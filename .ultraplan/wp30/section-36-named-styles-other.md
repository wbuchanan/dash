# Section 36: Other style names (P1.14 part b)

> Part of: WP-30 · Items: P1.14 part b (entry `P1.14b`) · Risk: yellow · Batch: 12 · Depends on: 32 · Blocks: — · Tasks: 17, 1 commit · Case prefix: OS

## Review amendments

- Blocker: the shipped files carry no style-name (hop) keys (`markerstyle ci`, `areastyle p3bar`, … are absent from every `dash-*.scheme`), so TR-36.7's hop read would have fallen to the class default for every table name. TR-36.6/36.7 now read a hop from `_props` when declared, else take the chain step that names a style (D-36h, E10), and `test_the_style_name_hops_are_identity` pins that rule against Stata for all 26 schemes.
- Major: four shipped-file pins S36's regeneration turns red were missing from E12: `TestTheShippedFiles::test_the_directive_count_is_what_the_help_says` (S24's rename of `test_80_to_140_directives`), `::test_every_colour_is_rrggbb` (`color pieline none`, `color fpspacer none`), `::test_some_uncarried_directives_govern_what_dash_draws_its_own_way_in_dash` (`color refline`), and `::test_no_directive_for_what_dash_does_not_draw` (26 tick/pie/dot/matrix line keys). Each is now flipped in 36-16 with the help's "What the shipped files are" paragraph.
- Major: a `none` colour value had no spelling (`_color_token` returns None). TR-36.14 now writes Stata's `none` token, and TR-36.7 reads it as not drawn.
- Major (M1, measured q7, E9.7): twoway notes `dstyle(bogus)`, `dlstyle(bogus)` and `bmlinestyle(bogus)`. `_style_plan` now asks `style_bundle` for those three keys for the note only (D-36i).
- Major (M1, measured q6, E9.6): twoway draws `lstyle("refline")` as refline, silently. `style_bundle` now unwraps one pair of double quotes (D-36j), and TR-36.20 no longer expects a note for it.
- Major: `PLOT_VALUES` used `dot` and `pcbarrow`, but the test's `_render` builds one y/x layer. All three rows now use `scatter`, which twoway accepts (E9.7).
- Major: 36-05's second run wrote "up to date" to stderr, so the verify could never count it. The task now captures `2>&1`.
- Minor: M5 is now settled by measurement (E9.6, E9.7): twoway refuses no style name, hostile ones included. `bm()` is r(198) in twoway and stays named, as D-32d keeps `pst()`.
- Minor: D-36g now uses scheme.class's words. The memo re-emits a recorded D-36g note on a hit. New tests: a graph's own scheme reaching a style (S34's served swap), `dstyle(bogus)`'s note, and the H grid of hostile names.
- Minor: the truth-block skeleton is written out. The Resolution's fixture clause now follows TR-01.10. The closeout notes name every P1.14 shared id, and the wrong "B11-c is not P1.14's" reading is struck.
- Rejected: changing the D-36c disposition. The maintainer question stays as written.
- Rejected: "S36 collides with S34 in `test_help_claims_8.py`". S34 edits `TestWhatAnIncludeResolvesTo` and `TestAnInstalledTree…`, and S36 edits only `TestTheShippedFiles`, so the hunks differ.
- (cross-file pass) 36-17 verify: added the key-deletion check `grep -c '^    "P1.14b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- (cross-file pass) 36-17 verify: added the subject check `git -C $WT log -1 --format=%s` ends `(WP-30 P1.14b)` (S01 Appendix A/TR-01.10.7).
- The review pass applied both lenses.
- Ratification row 4 (ratification 06oct2026, CHANGED: no unread-directive note): the S33 boundary no longer names a committed list of noted keys or read-recording; `TestAUserScheme::test_no_unread_key_note` is reworded as the guard `test_unread_directives_stay_and_print_nothing` (directive retained in `_props`, no note); the test count is unchanged.
- Ratification row 27 (ratification 06oct2026, "Fix in WP-30"): the residual "brushed and muted copies" is removed; those copies follow S08's brushed-copy sync (ratification row 27), and no P2 item is filed for them.

**Binding readings applied in this file** (decisions.md M1, M5, M6; decision-register P1.14.1, P1.14.3, P1.14.4, P1.14.5, P1.14.9, X.1, X.2, X.5; index A138, A145, A146, A148, A152, IR-14, R1-R12):
- **P1.14.1 part B, IR-14.** Every name of Stata 19.5's 76 `linestyle-*.style` files resolves. The other three option classes resolve the manifest's curated names: `ci`, `ci2`, `histogram`, `foreground`, `background`, `none` and the `p#line`, `p#bar`, `p#area`, `p#box`, `p#dot` and `p#arrow` forms. A form resolves only in the classes that have a style file for it (E7). `grid`, `major_grid`, `minor_grid`, `refline`, `p#other` and `p#mark` exist as line styles only. The general resolver for all 161 files stays a residual (manifest item-14 residual).
- **P1.14.3 (M1).** A name Stata does not know draws twoway's default attributes for its class, with twoway's note. The defaults were measured over all 26 schemes (E9.3): seriesstyle and markerstyle use p1, linestyle uses `foreground`, and areastyle uses `background`. "Once per layer" is read through S06's channel, which prints a given note text once per command (S06 TR-06.3, the `said` set). Two layers with the same bad name therefore print one line, as twoway's identical lines would read.
- **P1.14.5, P1.14.9 (A47, A51).** `dstyle()`, `dlstyle()` and `bmlinestyle()` are declared, serialised, split per y and dropped under `p()`. They stay named as not drawn until P2.9 (dot rows) and P2.8 (back lines). This takes S32's open Q1 (`bmlinestyle()`, register P1.14.9 and PLAN BR-30.14).
- **M5.** Nothing is newly refused, because twoway refuses no style name. That was measured for hostile names too (E9.6: `../x`, `{bf:x}`, `p3;x`, 33- to 200-character names, `ｐ３` all rc 0 with the note) and for the three new options (E9.7). `ds()` is twoway's `dsymbol()`, which dash does not declare, so it stays named as typed. `bm()`, which twoway refuses r(198) as an unknown option, stays named, as D-32d keeps `pst()` (P2.21). **M6.** twoway notes an unknown name even on a layer that does not draw the option's role (`scatter, lstyle(bogus)`, E9.4), so dash notes it too. S32's `TestOtherNames::test_unused_option_is_silent` is flipped (E12).
- **A152.** S36 is batch 12's only scheme regenerator. It lands last, after S34 and S35.
- **R12.** S36 edits none of the one-editor symbols: `_make_figure_body`, `_generate_app_source`, `_build_sources_and_figures`, `_build_filter_widgets` and the four appliers.

**Section decisions (this file).**
- **D-36a — a table transcribed from 19.5, resolved at render time.** `SchemeParser._STYLE_TABLE` holds each style file's `set` lines for the names S36 resolves, and nothing else. `style_bundle` follows those lines through the scheme's keys at render time, along Stata's own `scheme.class` chain (E8). A user scheme that `#include`s a shipped scheme and overrides `color refline` therefore reaches `lstyle(refline)`, as in Stata. The shipped files carry only the leaf keys the chain *declares* (E10: 119-137 new directives per file). No resolved bundle is ever written into a scheme file.
- **D-36b — a seriesstyle is not three same-named role styles.** `pstyle(p3bar)` is markerstyle p3, linestyle p3 (through `p#connect`) and areastyle p3bar. `mstyle(p3bar)` is unknown (E7, E9.2). S32's plan asks `style_bundle(<role class>, <pstyle value>)` (S32 TR-32.7). So S36 changes the bundle classes of the `pstyle` and `p` rows of `GlyphMapper._STYLE_FACTORS` to `series.marker`, `series.line` and `series.area`, which only `style_bundle` interprets. For p1-p15 the answers equal S32's own bundles, so S32's tests stay green. This is the one change S36 makes in S32's plan. It goes beyond the manifest note "edits only style_bundle…", and it is flagged to the orchestrator (Notes).
- **D-36c — Stata-known names outside the table.** Fifty-seven Stata-known style files lie outside the curated table: seriesstyle `fpall`, `dendrogram`, `matrix`, `p#pie` …; markerstyle `sunflower`, `star`, `refmarker` …; areastyle `plotregion`, `outline`, `legend` … (E7). They draw their class's default attributes. They are named in dash's words, `named style fpall of class seriesstyle is not drawn by dash; default attributes used`, because twoway's "not found" would be false for them. This follows M5: a valid twoway value dash cannot draw is named. It is open question 1 for the maintainer.
- **D-36d — all notes come from one place.** `SchemeParser._style_note` emits both texts through `_dash_warn_once`, keyed `("named-style", <Stata class>, <shown name>)`, and S06's channel prints them. S32's interim note (`_style_unresolved`, `_STYLE_UNREAD_NOTE`, the plan's `unresolved` list) can no longer be reached, because `style_bundle` returns a bundle for every non-blank name. S36 retires it, as S32 anticipated ("For later sections: S36 … `_style_unresolved` and `_STYLE_UNREAD_NOTE` may then be retired").
- **D-36e — the ci types.** `_ci_pstyle` gains a fourth answer, `("named", name)`, for a table seriesstyle other than ci, ci2 and p#. `_ci_band_style` then takes its base from `style_bundle("series.area", name)`, and `_ci_line_restyle` takes its line from `style_bundle("series.line", name)`. An unknown or not-drawn name keeps today's p1 drawing. Its note becomes `_style_note`'s.
- **D-36f — the label and dots roles are not resolved.** A seriesstyle also sets `label`, `dots`, `connect` and `connect_missings` (E7). S36 resolves marker, line and area only. Labels are P2.12's (`mlabstyle()`, a labelstyle sibling) and dots are P2.9's, and `connect()` is S40's. The extractor records the label colour, so the closeout can file any difference it shows (Notes for the closeout).
- **D-36g — a missing leaf key in a user scheme.** A user scheme that defines no key the chain reads (for example a scheme with no `#include` and no `color refline`) draws s2color's value for that key, taken from `_FALLBACK_PROPS`. It is noted once in scheme.class's words (E8, :205) with what dash draws: `dash: color refline not found in scheme, default attributes used -- s2color's value`. twoway's own value for this case is unmeasured, so dash names the value it draws. This applies to leaf keys only, because hops follow D-36h.
- **D-36h — a hop absent from the scheme is the chain step that names a style.** The shipped files carry no style-name keys (`grep -cE '^(markerstyle|linestyle|areastyle|shadestyle) ' dash-s2color.scheme` prints 0 at `c96facd`). Writing them would add about 364 lines per file (E10). Instead, a hop (`set marker scheme ci`, `set line scheme p#connect`) walks scheme.class's chain. At each step it takes the `_props` value when the scheme declares one (so a user scheme that maps a hop is followed). Otherwise it takes the step itself when that names a style of the hop's class (a table name, a `_STYLE_KNOWN` name or p1-p15). The first hit wins: `linestyle p3connect` → `p3`, `markerstyle ci` → `ci`. E10 measured that every hop the table reaches in the 26 schemes declares exactly that value. `test_the_style_name_hops_are_identity` pins the rule against Stata's chain for every scheme, and no note is printed for a hop.
- **D-36i — the three undrawn options are still noted as twoway notes them** (E9.7). `dstyle(bogus)` prints twoway's markerstyle note, and `dlstyle(bogus)` and `bmlinestyle(bogus)` print its linestyle note. `_style_plan` therefore asks `self.scheme.style_bundle("marker"|"line", value)` for those keys for its note only, before its early return, and uses no bundle. A table name stays silent.
- **D-36j — one pair of double quotes is unwrapped** (E9.6: twoway draws `lstyle("refline")` as refline, with no note). `style_bundle` strips one enclosing `"…"` (or compound `` `"…"' ``) after S32's strip and passes the unwrapped name on, to S32's p# path too. Nothing else is unwrapped.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:104 (P1.14) reads: "`pstyle()` works only on the four CI fits. `lstyle`, `mstyle`, `mlstyle`, `astyle`, `alstyle`, `bstyle` and `dstyle` are not read." S32 (batch 11) makes p1-p15 work for every style option. Its interim rule (D-32b) leaves every other name noted and undrawn: `dash: lstyle(refline): only the named styles p1-p15 are drawn; this layer keeps its own style.` S01's open entry for this part reads: "the named-style options read no Stata style name outside p1-p15 (ci, ci2, histogram, foreground, background, grid, refline, none, and the p#line, p#bar, p#area and p#mark suffixes), an unknown name is not noted as twoway notes it, and `dstyle()` is not declared."

Measured at `c96facd` (research d1.do, re-run as E11): `dash line mpg weight, lstyle(refline)` draws p1's line, `#1a476f` under s2color. twoway draws `45 109 102` (#2d6d66) at width .3. `dash dot mpg weight, dstyle(p3)` writes no key and prints `ignoring unsupported option(s): dstyle()`. twoway (E9) draws `area mpg weight, astyle(bogus)` filled and outlined in the scheme's background colour (#eaf2f3 under s2color). `line …, lstyle(bogus)` comes out black at width .2, `pstyle(bogus)` on any plot comes out p1, and each prints `(note:  named style bogus not found in class CLASS, default attributes used)`.

**After this section,** in both modes and before and after any filter move:
- `pstyle()`, `p()`, `lstyle()`, `clstyle()`, `mstyle()`, `mlstyle()`, `astyle()`, `alstyle()`, `bstyle()` and `blstyle()` draw every name of Stata's 76 line styles and the curated names of the series, marker and area classes, as twoway draws them, under each of the 26 shipped schemes and under a user scheme that includes one of them.
- `pstyle(ci)`/`pstyle(ci2)` work on scatter, line, area, bar and every other type, and `pstyle(histogram)` and the `p#bar`-type names work on the ci fits' band and line.
- A name Stata does not know draws twoway's default attributes and prints twoway's note once. A name Stata knows outside the table draws the same defaults and is named (D-36c).
- `dstyle()`, `dlstyle()` and `bmlinestyle()` (with `dst`, `dl`/`dls`, `bml`) reach the spec and are named as not drawn.

**Why one section.** This is P1.14's name table (A138: "P1.14 A/B: S32/S36"). It reuses S32's resolver entry point (`style_bundle`), plan and appliers unchanged in every body, and adds the transcription it reads: the extractor, the 26 files, `_FALLBACK_PROPS` and the table. Batch 12's partners touch none of these (S34: the scheme path functions; S35: axes).

**Test order and commit rule (rule 7, D1).** One cycle, one commit `(WP-30 P1.14b)`:
- **36-01** writes the regression tests with twoway's literal values (E9) and runs them against the unmodified batch-12 base. It saves `<scratch>/36-P1.14b-failure.txt` and never commits.
- **36-02 and 36-03** write the Stata-truth extractor and its fixture-driven tests, run those tests at the base, and append their failures to the same file.
- **36-04 to 36-16** fix, regenerate, flip the pinned tests, register, fill the truth block and update the help.
- **36-17** closes the entry and makes the commit.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — a 26-file regeneration, three HIGH ci methods, one data row of S32's plan, and every dashboard that names a non-p style changes its look

**Why.** The regeneration adds about 120 directives (and as many provenance lines) to each of 26 generated files and `scheme_truth.json`. The resolver runs inside the CRITICAL appliers' first step (S32's `_style_restyle`), so a wrong bundle reaches every glyph that names a style. `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle` are HIGH (2/1/4 direct callers, 4/3/4 processes; E13). Users' drawings change wherever they named a non-p style. Those names were ignored before.

**Risk factors.**
1. The table must equal the 19.5 style files exactly. A mistyped key silently draws the wrong colour.
2. A style-name hop (`set marker scheme ci` → `markerstyle ci ci`) could map to another name in some scheme. E10 measured that none does for any table name in any of the 26 schemes. A future scheme could differ.
3. The served app rebuilds the parser with `SchemeParser.__new__` and `_init_properties()` (dash_render.py:33450-33459), so state built in `__init__` does not exist there.
4. A hostile name could grow a memo without bound or be formatted into a `_props` key.
5. The Stata extractor is slow: 0.87 s per single-layer `twoway … nodraw` (E9.5).
6. `_FALLBACK_PROPS` grows by about 119 entries that must equal s2color's.

**Mitigation.**
1. The table is held equal to `scheme_truth.json` `_meta.style_files`, which the extractor transcribes from the style files (TR-36.14). `style_bundle` is held equal to Stata's graph object for every recorded name (TR-36.15, about 4,700 records).
2. `test_the_style_name_hops_are_identity` asserts that D-36h's rule gives, for every hop in every shipped scheme, the value Stata's chain declares. `_style_resolve` reads each hop from `_props` first, so a user scheme that maps a hop is followed.
3. The memo is created lazily on `self.__dict__`. A served-mode test builds the app and draws a named style (TestBothModes).
4. Names are matched against fixed sets and one regex, never formatted into a key. Memo keys are table names or a per-class default. An adversarial test checks keys and time (TR-36.20).
5. The extractor batches 25 layers per call, 2.5 s each (E9.5), for about 11 minutes once.
6. `TestTheFallback::test_every_table_name_matches_s2color`.

## Dependencies

- **Depends on: 32.** S32 provides `SchemeParser.style_bundle(cls, name)` (TR-32.6) with its three bundle shapes, `GlyphMapper._STYLE_FACTORS`/`_style_plan`/`_style_options`/`_style_value`/`_style_restyle`/`_style_unresolved` (TR-32.7), the appliers' first step (TR-32.8), the ten mappers (TR-32.9), the ci integration (TR-32.11), the declarations and `_dash_p_drops` (TR-32.5, D-32a), `named_style_truth.json` with its U rows, and `test/test_named_styles.py`. Earlier sections S32 itself builds on: S06 (`_dash_emit_note`, the `(note:  …)` channel), S07 (26 schemes), S08/S13 (size and width ladders: `translate_msize`, `translate_lwidth`), S11 (`_dash_stylelist_keys()`), S15/S24 (`color histogram`, `color histogram_line`, `intensity histogram`, `linewidth histogram`) and S30 (colour grammar in `_color_alpha`).
- **Blocks:** none in the manifest. S38 (batch 13, `plotregion(style())`/`lstyle()`) and S39 (batch 14, `xline(, lstyle())`) call `style_bundle("area"|"line", name)` and get S36's names without editing it. S43 (batch 15) composes `*#` with a named style's base through `_style_value`.
- **Parallel batch: 12**, with merge order S34, S35, S36. S36 lands last as the batch's regenerator (A152).
- **Can run with:** S34 and S35. Neither edits the extractor, a scheme file, `scheme_truth.json`, `_FALLBACK_PROPS`, `style_bundle`, `_STYLE_FACTORS` or the ci methods. S34 edits `SchemeParser._resolve_path`, `resolve_or_fallback` and `_include`, which are different methods of the same class. Its hunks are distinct. Both S34 and S36 add a paragraph to dash.sthlp's scheme support section, and the paragraphs are different (R3).

## Evidence

Anchors are at `c96facd` unless marked "at the base". Sections 01-35 move them, so every task locates code by the quoted text and the function name.

### E1. The parser: fallback properties and the served rebuild

`SchemeParser._FALLBACK_PROPS` (dash_render.py:5728-5824) mirrors s2color, held so by `test_scheme_fallback_provenance.py::TestTheFallbackMirrorsS2color::test_every_style_attribute_matches` (:87). Its last block is the ci keys:

```python
5811        # A ci fit's band and its ci line style, at s2color's values
5812        # (scheme-s2color.scheme 352-358, 560-561, 1208-1211, 1272).
5813        "color ci_area":          "#c0c0c0",
5818        "color ci_line":          "#808080",
5821        "color ci2_area":         "#e5daa5",
5823        "linewidth ci2_area":     "medium",
5824    }
```

`fallback()` (5827) is `cls.__new__(cls)`, `inst._props = dict(cls._FALLBACK_PROPS)`, then `_init_properties()`. The served app does the same from the property dict (33446-33459):

```python
33447            "_SCHEME_PROPS = %r" % (dict(getattr(self.scheme, "_props", {})),),
33454            "    _s = SchemeParser.__new__(SchemeParser)",
33455            "    _s._props = dict(_SCHEME_PROPS)",
33457            "    _s.is_fallback = _DASH_SCHEME_IS_FALLBACK",
33458            "    _s._init_properties()",
```

So any key the shipped file carries reaches the served app, and nothing `__init__` builds does. The three classes are copied by source (33436: `for _cls in (OptionTranslator, SchemeParser, GlyphMapper):`). Class constants and methods therefore need no copy-list entry (R2 row "S24, S30, S32, S33, S34, S36": none). `_parse_lines` stores a two-token line as a class default under the bare class name (`props[tokens[0]] = tokens[1]`, 6382-6383), and every other line under `"<class> <key>"`.

### E2. The readers the resolver uses

- `_color_alpha(key, …)` (6491) gives `(hex, opacity)`.
- `_first_present(keys)` (6519).
- `_stub_color_alpha(i, stub)` (6527-6541) walks `color p<stub>` and `color p<i><stub>` over `p_colors[i-1]`:

  ```python
  6537        val = (self.p_colors[i - 1], self.p_alphas[i - 1])
  6538        for key in (f"color p{stub}", f"color p{i}{stub}"):
  6539            if self._props.get(key, "").strip():
  6540                val = self._color_alpha(key, *val)
  ```

- `_intensity(key, default)` (6577), `_lpattern_chain(keys)` (6605), `_symbol(key, default)` (6797, through `OptionTranslator.translate_msymbol`), `_markersize_px(keyword)` (7248) and `_plot_lwidth_of(key)` (7317).
- `OptionTranslator._INVISIBLE_SYMBOLS = frozenset({"i", "none", "invisible"})` (5247). `msymbol(none)` sets `fill_alpha` and `line_alpha` to 0 (8773-8777), and S32's `_style_restyle` does the same for a `None` colour (TR-32.7).

S08, S13, S16, S24 and S30 change some of these in place. 36-01 records their names at the base (`$S/36-interface.txt`).

### E3. The bundle shapes S36 must return (S32 TR-32.6, from the existing dicts)

- area: `p_other_band_styles[i]` (7120-7139) and `ci_band_styles[w]` (7078-7112), with keys `fill, fill_alpha, intensity, line, line_alpha, line_width, line_dash`:

  ```python
  7133            self.p_other_band_styles.append({
  7134                "fill": _fc, "fill_alpha": _fa,
  7135                "intensity": (self._intensity(_ik, self.fill_alpha) if _ik
  7137                "line": _oc, "line_alpha": _oa,
  ```

- line: `ci_line_styles[w]` (7099-7105), with keys `line, line_alpha, line_width, line_dash`.
- marker (S32 TR-32.6): `fill, fill_alpha, line, line_alpha, line_width, symbol, size`.

### E4. The only non-p names read today: the ci types

`GlyphMapper._ci_pstyle` (8262-8291), with `_CI_PSTYLE_NAMED = frozenset({"ci", "ci2"})` (8258):

```python
8280        if s in self._CI_PSTYLE_NAMED:
8281            return s, None
8282        if s in self._CI_PSTYLE_P:
8283            return "p", self._CI_PSTYLE_P[s]
8284        _shown = _dash_display(s)
8285        _dash_warn_once(
8286            ("ci-pstyle", _shown),
8287            f"dash: pstyle({_shown}): named style not found; default "
8288            f"attributes used -- p1's, as twoway draws them.",
```

`_ci_band_style` (8307) takes `p_other_band_styles[pi % 15]` or `ci_band_styles["ci"|"ci2"]`. `_ci_line_restyle` (8448) branches on the same answer. After S32 (TR-32.11), `_ci_pstyle` reads `p` before `pstyle` and names the option it read. Its sets and its note are otherwise unchanged at the base.

### E5. The note helpers

`_dash_warn_once(key, message)` (15363-15368) de-duplicates per render, and `_dash_reset_notes` clears the set at the top of `render()` and of the served `make_document`. `_dash_display(text, limit=80)` (26383) echoes printable characters only, 80 at most. Both are in the served app: `_dash_warn_once` through `_shared_stat_lines` (33536-33540, beside `"_DASH_NOTED = set()"` at 33534), and `_dash_display` on the functions tuple (33384). After S06, a `dash: `-prefixed warning raised inside `main()` reaches Stata as `(note:  dash: …)`, and each distinct text is printed once per command (S06 TR-06.3).

### E6. dash.ado and Mata at `c96facd`

- The plot syntax (dash.ado:924-990) declares `MSTyle(string)`, `LStyle(string)` and `MLStyle(string)` (951-952). It declares no `DSTyle`, `DLstyle` or `BMLinestyle`, so `dst()`, `dl()` and `bml()` fall into `*` and are named as typed.
- The pending lines (1074, 1082-1085) are of the form `` if `: length local mstyle' local _dash_pending `"`_dash_pending' mstyle"' ``.
- The sreturn block (1181, 1202-1204) has `sreturn local mstyle : copy local mstyle`.
- `_dash_plot_opts_to_json`'s key list (3144-3156) ends `lineopts fitopts color mlwidth mstyle lstyle mlstyle mlpattern`. Each key is read by value through `mata: st_local("val", st_global("s(" + st_local("key") + ")"))` (3163).
- `_dash_rep_cat` (dash_parse.mata:4664-4687) returns "R" (the last copy wins) for any key it does not list. twoway declares the three new options `rightmost` (twoway_yxview_parse.class:631, 729, 740), so no Mata change is needed for repeats.
- At the base, S11's `_dash_stylelist_keys()` (dash_parse.mata, after `_dash_rep_toks`) and S32's `_dash_p_drops` local (in `_dash_plot_opts_to_json`) are where a style key joins the per-y split and the `p()` drop (S32 "For later sections: S36 … adds `dstyle dlstyle` to the declarations, the sreturn block, the JSON key list, `_dash_stylelist_keys()` and `_dash_p_drops`").

### E7. Stata's style files (StataNow 19.5, `/Applications/StataNow/ado/base/style/`)

Counts: seriesstyle 28, markerstyle 28, areastyle 29, linestyle 76 (161), and shadestyle 29. Each file is a list of `set <attr> scheme <key>` or `set <attr> <literal>` lines:

```
linestyle-refline.style   set width scheme refline / set color scheme refline / set pattern scheme refline
linestyle-none.style      set width scheme foreground / set color none / set pattern solid
linestyle-p#line.style    set width scheme p#lineplot / set color scheme p#lineplot / set pattern scheme p#lineplot
markerstyle-ci.style      set symbol scheme ci / set size scheme ci / set fillcolor scheme ci_symbol / set linestyle scheme ci
markerstyle-none.style    set symbol none / set size scheme symbol / set fillcolor scheme symbol / set linestyle scheme symbol
areastyle-ci.style        set linestyle scheme ci_area / set shadestyle scheme ci
areastyle-none.style      set linestyle none / set shadestyle none
shadestyle-histogram.style set color scheme histogram / set intensity scheme histogram
seriesstyle-p#bar.style   set marker scheme p# / set line scheme p#connect / set area scheme p#bar / set label scheme p#bar / set dots scheme dots
seriesstyle-ci.style      set marker scheme ci / set line scheme ci / set area scheme ci / set label scheme / set dots scheme dots
```

The curated names that exist, per class (measured with `ls`, s36-probe/chain.py):
- seriesstyle: `ci ci2 histogram p#line p#bar p#area p#box p#dot p#arrow` (93 names with # = 1-15);
- markerstyle: `ci ci2 histogram none p#box p#dot p#arrow` (49);
- areastyle: `background ci ci2 foreground histogram none p#area p#bar p#box` (51);
- linestyle: all 76 files, which is 64 plain names and 12 templates (`p# p#area p#arrow p#arrowline p#bar p#box p#boxmark p#dotmark p#line p#mark p#other p#solid`). That is 244 names, of which S32 owns the 15 `p#`.

Stata-known but outside the table (D-36c):
- seriesstyle (18): `dendrogram editor fpall fpallarrow fpallci fpci fpciarrow fpcumul fpes fpesinside fpgrp fpgrparrow fpgrpci fpgrps ilabel line_circle matrix p#pie`;
- markerstyle (20): `dots ed_arrow editor fpall fpallarrow fpallci fpci fpciarrow fpcumul fpes fpesinside fpgrp fpgrparrow fpgrpci fpgrps ilabel matrix refmarker star sunflower`;
- areastyle (19): `boxed_bg clegend_inner clegend_outer clegend_preg dendrogram dotchart fpall fpciarea fpgraph fpgrp fpspacer legend matrix_plotregion outline p#pie plotregion sunflower sunflowerdb sunflowerlb`.

### E8. Stata's key lookup (`/Applications/StataNow/ado/base/s/scheme.class`, :72-125)

```
if bsubstr("`id'", 1, 1) != "p" {          /* handle normal case */
        local stl `.`class'.`id''          ... if "`id'" == "" use `.`class'._default'
}
else {                                     /* handle p#stub */
        ... p`num'`stub'  ->  p`stub'  ->  p`num'  ->  p  ->  `id'
}
di in smcl "{txt}{p 0 8} (note:  `._mapcl `class'' `id' {txt}not found in scheme, default attributes used){p_end}"
```

A non-p key has no class-default fallback unless it is empty. The extractor's `linked()` (scripts/extract_scheme_truth.py:864-907) does fall back to the class default (`tok = r.settings.get((cls, ""))`). S36's new extractor code follows scheme.class instead, and records any key that does not resolve as `unresolvable` (E10 found none).

### E9. twoway truth (StataNow 19.5, graph object `.Graph.plotregion1.plotK.style.*`)

Probes q1-q5 are in `<scratch>/s36-probe/`, quoted here (E11 of the index: never the only evidence). Each was run as `scripts/stata_slot.sh <scratch>/s36-probe <scratch>/s36-probe/qN.do` and reads with research `pst_prog.do`.

**E9.1 Named non-p names (q1).**

```
s2color  line lstyle(refline)     lc=45 109 102  lw=.3 lp=solid
stcolor  line lstyle(refline)     lc=0 0 0       lw=.3 lp=solid
stcolor  line lstyle(major_grid)  lc=240 240 240 lw=.3 lp=dash
stcolor  line lstyle(minor_grid)  lc=80 80 80    lw=.2 lp=dot
s2color  line lstyle(xyline)      lc=193 5 52    lw=.3 lp=solid
stcolor  scatter pstyle(ci)       mf=160 160 160 msz=1.52778 lc=160 160 160 lw=.3 af=224 224 224 ai=100
s2color  scatter pstyle(ci)       mf=128 128 128 lc=128 128 128 af=192 192 192 ai=100
stcolor  line pstyle(ci2)         mf=239 237 216 ml=160 160 160 lc=160 160 160 af=247 244 228
stcolor  scatter mstyle(histogram) mf=26 133 255 ml=95 170 255 mlw=.15 msz=1.94444
s2color  scatter mstyle(histogram) mf=202 194 126 ml=215 210 158 msz=1.94444
s2color  area astyle(background)  af=234 242 243 ai=100 al=234 242 243 alw=.2
stcolor  area astyle(p3bar)       af=0 191 127 ai=80 al=0 191 127 alw=.2
s2color  scatter pstyle(p3bar)    mf=85 117 47 lc=85 117 47 af=85 117 47 alw=.2
stcolor  scatter pstyle(fpall)    rc 0, no note, msz=11            (Stata-known, outside the table)
stcolor  scatter dstyle(p3)       df=0 191 127 (dots only; marker unchanged), rc 0, no note
stcolor  scatter dlstyle(p3)      rc 0, no note
```

**E9.2 Names twoway does not know (q1).** Each case prints the note and draws the defaults:

```
(note:  named style p0 not found in class seriesstyle, default attributes used)      pstyle(p0)
(note:  named style p03 not found in class seriesstyle, default attributes used)     pstyle(p03)
(note:  named style p16line not found in class linestyle, default attributes used)   (twice) lstyle(p16line): 0 0 0 .2 solid
(note:  named style p16box not found in class markerstyle, default attributes used)  mstyle(p16box)
(note:  named style foreground not found in class markerstyle, default attributes used)
(note:  named style p3other not found in class seriesstyle, default attributes used)
(note:  named style p3mark not found in class seriesstyle, default attributes used)
(note:  named style foreground not found in class seriesstyle, default attributes used)
```

**E9.3 Default attributes are a class's fixed style, not the layer's (q2, q3).** These were read on plot 2:
- stcolor `pstyle(bogus)` gives p1 everywhere (mf 26 133 255).
- `mstyle(bogus)` gives p1's marker (mf 26 133 255), with the line kept at p2 (212 17 89).
- `lstyle(bogus)` gives 0 0 0, .2, solid.
- `astyle(bogus)` gives a 255 255 255 fill at 100 with an outline of 255 255 255 at .2.
- `mlstyle(bogus)` gives a 0 0 0 outline at .2.
- `alstyle(bogus)` gives an outline of 0 0 0 at .2.

Over all 26 Stata schemes (q3), `lstyle(bogus)` equals `lstyle(foreground)` (s1rcolor `255 255 255/.2/solid`, every other scheme `0 0 0/.2/solid`). `astyle(bogus)` equals `astyle(background)` (s2color `234 242 243/100`, economist `198 211 223/100`, s2manual/s2mono/sj `240 240 240/100`, s1rcolor `0 0 0/100`, the st* family `255 255 255/100`).

`none` (q2, `.color.stylename`):
- `mstyle(none)` gives `ms=none`;
- `astyle(none)` gives `afc=none|alc=none`;
- `lstyle(none)` gives `lc=none`.

Research t4's SVGs: `lstyle(none)` has stroke-opacity 0, `mstyle(none)` draws no marker, and `astyle(bogus)` is `fill:#FFFFFF;stroke:#FFFFFF`.

**E9.4 Note count (q1).**

```
twoway (line mpg weight, lstyle(bogus)) (line price weight, lstyle(bogus))   -> 4 identical linestyle notes
twoway scatter mpg weight, lstyle(bogus) mstyle(bogus)                        -> 1 markerstyle note, 2 linestyle notes
```

twoway notes `lstyle(bogus)` on a scatter, whose line role is not drawn.

**E9.5 Cost (q4, q5).** `forvalues i = 1/100 { quietly twoway line mpg weight, lstyle(refline) nodraw }` took `86.54` s. Four 25-layer calls `(line mpg weight in 1/2, lstyle(<n>)) …` took `9.97` s, and each plot k reads its own style (q5: plot 1 `refline` is `45 109 102|.3|solid`, plot 22 `plotregion` is `255 255 255|.2|solid`). Under sttrans, `.color.opacity` reads `20` (q4).

**E9.6 Hostile names (q6, stcolor, run for this review; `scripts/stata_slot.sh <scratch>/s36-probe <scratch>/s36-probe/q6.do`).** Every case had rc 0:

```
line lstyle(../x)      (note:  named style .. / x not found in class linestyle, default attributes used)   x2
line lstyle({bf:x})    (note:  named style x not found in class linestyle, ...)                           (SMCL rendered)
line lstyle(p3;x)      (note:  named style p3 ; x not found in class linestyle, ...)
line lstyle("refline") no note (drawn as refline)
line lstyle(REFLINE)   (note:  named style REFLINE not found in class linestyle, ...)
line lstyle(ｐ３), lstyle(x.y), lstyle(3), 33-, 40- and 200-character names: the note, rc 0
scatter pstyle(../x)   (note:  named style ../x not found in class seriesstyle, ...)
scatter pstyle(p3+)    (note:  named style p3+ not found in class seriesstyle, ...)
```

dash echoes `{bf:x}` literally (escaped through S06), not rendered. That is the security rule, and it is a documented difference of display only.

**E9.7 The three undrawn options (q7, stcolor, run for this review).**

```
scatter mpg turn weight, dstyle(p3 p4)   rc 0  dots plot1 0 191 127, plot2 255 212 0   (a per-y list)
scatter mpg turn weight, dlstyle(p3 p4)  rc 0  dots line plot1 0 191 127, plot2 255 212 0
scatter mpg weight, dst(p3) / dl(p3) / dls(p3) / bml(p3)   rc 0, no note
scatter mpg weight, ds(p3)               rc 0  (note:  named style p3 not found in class symbol, ...)   (dsymbol)
scatter mpg weight, bm(p3)               option bm() not allowed  r(198)
scatter mpg weight, dstyle(bogus)        rc 0  (note:  named style bogus not found in class markerstyle, default attributes used)
scatter mpg weight, dlstyle(bogus)       rc 0  (note:  named style bogus not found in class linestyle, default attributes used)
scatter mpg weight, bmlinestyle(bogus)   rc 0  (note:  named style bogus not found in class linestyle, default attributes used)
```

### E10. What the chain reads (s36-probe/chain.py and chain2.py, a scheme.class-faithful resolver over the extractor's `SchemeResolver`)

- Across the 26 schemes, the table's names reach 271 distinct leaf keys (`color`, `linewidth`, `linepattern`, `symbol`, `symbolsize`, `intensity`).
- The keys a scheme declares that its shipped dash file lacks at `c96facd` number 119 (s2color, sj), 120 (17 schemes) and 137 (economist).
- For s2color they include `color refline`, `linewidth refline`, `linepattern refline`, `color ci_symbol`, `symbol ci`, `symbolsize ci`, `color histogram_line`, `symbolsize histogram`, `linewidth foreground`, `linepattern grid`, `linewidth medium` and `symbolsize parrow`. S24 adds four histogram keys, so S36's count at the base is lower by them.
- "non-identity style-name keys reached:" is empty. Every hop (`markerstyle ci`, `linestyle ci_area`, `areastyle p3bar`, `shadestyle histogram` and so on) has a value equal to the chain step that declares it, in all 26 schemes. `linestyle p3connect` is declared at its `p3` step as `p3`. Meanwhile 163-166 other style-name keys per scheme do not (`linestyle axis axisline`, `shadestyle p foreground`, and others). None is unresolvable.
- Re-measured for this review (chain3/chain5.py, same resolver):
  - The chains declare 364 hop keys per scheme, all absent from the shipped files, hence D-36h.
  - The leaf keys reached include 26 that `test_no_directive_for_what_dash_does_not_draw`'s pattern bans. They are the line styles `tick`, `minortick`, `pie`, `dot*` and `matrix*`: `color tick`, `linewidth minortick`, `linepattern pie`, `color dots`, `linewidth matrix_plotregion` and others.
  - `color pieline` and `color fpspacer` are Stata's `none` in all 26 schemes.

### E11. dash at `c96facd` (research d1.do and py1.py, both modes identical)

```
dash line mpg weight, lstyle(p3)  -> dash: ignoring unsupported option(s): lstyle()   options {"lstyle":"p3"}
dash dot mpg weight, dstyle(p3)   -> dash: ignoring unsupported option(s): dstyle()   options {}
line lstyle(p3)                   -> Line #1a476f solid (unchanged from the base)
lfitci pstyle(p3)                 -> VArea #779159, Patch #55752f, Line #55752f   (the ci pstyle works)
```

Re-measured for this file at `c96facd` with `GlyphMapper(scheme=SchemeParser("s2color")).map_line(figure(), ColumnDataSource({"y":[1,2,3],"x":[1,2,3]}), "y", "x", {"lstyle": "refline"})`, which printed `lstyle(refline) at HEAD: #1a476f` (p1's line; twoway draws #2d6d66). At the base (after S32), `lstyle(refline)` prints D-32b's interim note and keeps the layer's p1. 36-01 re-measures this in both modes and saves it as the failure text.

### E12. Tests that pin today's behaviour (flipped in place with a `Flipped:` line, never deleted; re-measured by 36-01 at the base)

| Test | Today | After S36 |
|---|---|---|
| `test/test_named_styles.py::TestOtherNames::test_noted_once_and_drawn_as_the_layer[saved]`, `[served]` (S32) | `lstyle(refline)`: D-32b note, p1 line | refline's line (s2color #2d6d66, .3, solid), no note |
| `test/test_named_styles.py::TestOtherNames::test_unused_option_is_silent[saved]`, `[served]` (S32) | `scatter, lstyle(bogus)` silent | twoway's linestyle note once (E9.4, M6 does not apply) |
| `test/test_named_styles.py::TestAdversarial::test_hostile_names_are_noted_shortened_and_inert[*]` (S32) | D-32b text | `_style_note`'s text; still ≤ 80 printable characters of name, inert |
| `test/test_named_styles.py` tests naming `_style_unresolved`/`_STYLE_UNREAD_NOTE` (36-01 lists them) | interim path | retired with the path (D-36d); `function_test_map.py`'s key deleted |
| `test/test_ci_band_style.py::TestAdversarial::test_a_hostile_pstyle_is_named_once_and_shortened` (:421-433) | filters warnings on `"pstyle" in msg` | filters on `"named style" in msg` |
| `test/test_ci_band_options.cscript` CB-04 (S32's flipped form) | `al(red)`: the interim style note | twoway's `named style red not found in class linestyle` note |
| `test/test_unsupported_report_is_true.py:240` plot pending (S32 left 44) | the base value | +3 (dstyle, dlstyle, bmlinestyle) |
| `test/test_unsupported_report_is_true.py:607` declared plot (S32 left 175) | the base value | +3 |
| `test/test_help_claims_8.cscript` HC8-07 `p_opts`/`p_names` (:392-393) | the pending list | gains `dstyle(p3) dlstyle(p3) bmlinestyle(p3)` |
| `test/test_help_claims_8.py::TestTheShippedFiles::test_the_directive_count_is_what_the_help_says` (S24's rename of `test_80_to_140_directives`, :1014 at `c96facd`; bounds as S33 left them) | the base's bounds and help numbers | bounds re-derived from the regenerated 26 (min/max rounded outward to ten), the help's "What the shipped files are" numbers with them (R10) |
| `test/test_help_claims_8.py::TestTheShippedFiles::test_every_colour_is_rrggbb[*]` (:1056) | only economist's `color plotregion_line` may be `none` | also `color pieline` and `color fpspacer`, which Stata declares `none` in all 26 (E10) |
| `test/test_help_claims_8.py::TestTheShippedFiles::test_some_uncarried_directives_govern_what_dash_draws_its_own_way_in_dash[saved]`, `[served]` (:1083) | `"color refline" not in keys` | `"color refline" in keys` (lstyle(refline) draws it); the xline half unchanged |
| `test/test_help_claims_8.py::TestTheShippedFiles::test_no_directive_for_what_dash_does_not_draw` (:1104) | no key matches the bar/box/pie/dot/matrix/margin/tick pattern | the pattern applies outside the `Named styles (WP-30 S36)` group; inside it the 26 line-style keys of E10 are allowed, because `lstyle(tick)` and the rest draw them |
| `test/test_unsupported_report_is_true.py` `PLOT_VALUES` | no rows | `dstyle`, `dlstyle`, `bmlinestyle` on `scatter` (`_render` builds one y/x layer, so `dot`/`pcbarrow` cannot be used) |

Guards (green before and after):
- `test/test_ci_band_style.py::TestAdversarial::test_a_pstyle_dash_does_not_know_is_p1` (:411): `p0`, `p03`, `P3`, `p16`, `ci3` and `{safe}` stay unknown and draw p1 (E9.2);
- `test/test_scheme_fidelity.py::test_regenerating_a_shipped_file_is_a_no_op`, `::test_a_shipped_file_carries_each_directive_once`, `::test_every_fixture_key_has_provenance`, `::test_shipped_file_carries_one_provenance_line_per_directive`;
- `test/test_scheme_fallback_provenance.py::TestTheFallbackMirrorsS2color::test_every_style_attribute_matches`;
- S32's `TestStyleBundle::test_against_stata`, `TestTheEmptyPlanIsInert`, `TestAfterAFilterMove::test_no_page_script_writes_a_style`.

### E13. GitNexus impact (CLI, `-r dash`, at `c96facd`; re-run at the batch-12 base in step 12.0)

| Symbol | Risk | Note |
|---|---|---|
| `GlyphMapper._ci_pstyle` | HIGH (2 direct, 4 processes) | warn before editing |
| `GlyphMapper._ci_band_style` | HIGH (1 direct, 3 processes) | warn |
| `GlyphMapper._ci_line_restyle` | HIGH (4 direct, 4 processes) | warn |
| `SchemeParser` (class) | LOW (4 direct) | |
| `SchemeParser._init_properties` | LOW (1 direct; the served `__new__` path is invisible to the index) | not edited |
| `expected_directives`, `extract` (scripts/extract_scheme_truth.py) | LOW | the second needs `--file`-disambiguation (two `extract` symbols) |
| `SchemeParser.style_bundle`, `GlyphMapper._style_plan`, `_style_restyle`, `_STYLE_FACTORS` | new in S32, run at the base | expected LOW/HIGH; report any HIGH |
| `_dash_parse_plot_opts`, `_dash_plot_opts_to_json` (dash.ado), `_dash_stylelist_keys` (Mata) | UNKNOWN (not indexed) | `grep -n` at the base, recorded unresolved |

## User stories

- **US-36.1** As a twoway user, I want `lstyle(refline)`, `lstyle(grid)`, `lstyle(foreground)`, `lstyle(xyline)` and every other Stata line style name to draw my lines in the scheme's colour, width and pattern, so that a do-file written for twoway looks the same.
- **US-36.2** As a twoway user, I want `pstyle(ci)`, `pstyle(ci2)` and `pstyle(histogram)` to work on any plot, and on the ci fits too, so that I can style a layer like a confidence band or a histogram.
- **US-36.3** As a twoway user, I want the series and area forms `p3bar`, `p3line`, `p3area`, `p3box`, `p3dot` and `p3arrow`, and `astyle(background)`, `astyle(foreground)` and `none`, to draw as in twoway.
- **US-36.4** As a twoway user who mistypes a style name, I want twoway's default attributes and twoway's note, so that I see the same picture and the same hint to fix it.
- **US-36.5** As a twoway user, I want `dstyle()`, `dlstyle()` and `bmlinestyle()` in a copied command to be accepted, kept and named as not drawn, never silently lost.
- **US-36.6** As a dashboard publisher with my own scheme, I want `#include s2color` plus `color refline red` to reach `lstyle(refline)` as it does in Stata.
- **US-36.7** As a dashboard publisher, I want any text in a style name to stay inert data: never a file path, never markup, never a crash.

## Business requirements

- **BR-36.1** Every name of Stata 19.5's 76 line styles, given to `lstyle()`, `clstyle()`, `mlstyle()`, `alstyle()` or `blstyle()`, draws the colour, width, pattern and opacity twoway draws under each of the 26 shipped schemes.
- **BR-36.2** `pstyle()`/`p()` with `ci`, `ci2`, `histogram`, `p#line`, `p#bar`, `p#area`, `p#box`, `p#dot` or `p#arrow`, `mstyle()` with `ci`, `ci2`, `histogram`, `none`, `p#box`, `p#dot` or `p#arrow`, and `astyle()`/`bstyle()` with `background`, `foreground`, `ci`, `ci2`, `histogram`, `none`, `p#area`, `p#bar` or `p#box` draw each role (marker, line, area fill and outline) as twoway does, on every type S32 styles, the ci fits included.
- **BR-36.3** A name twoway does not know draws twoway's default attributes for the option's class (seriesstyle and markerstyle: p1; linestyle: the scheme's foreground line; areastyle: the scheme's background area). The command prints `(note:  dash: named style NAME not found in class CLASS, default attributes used)` once.
- **BR-36.4** A name twoway knows but dash does not draw draws the same defaults and is named once as not drawn.
- **BR-36.5** `dstyle()`, `dlstyle()`, `bmlinestyle()` and their abbreviations `dst()`, `dl()`/`dls()` and `bml()` are accepted, kept in the spec per y, dropped under `p()` as twoway drops them, and named as not drawn.
- **BR-36.6** The saved page and the served app draw the same, before and after a filter move, and so do a scheme included by a user scheme and the fallback scheme.
- **BR-36.7** No style name, however hostile, changes anything but which built-in style is drawn and the shortened, escaped name in the note.

## Technical requirements

- **TR-36.1 `SchemeParser._STYLE_TABLE`** (new class constant, directly after `_FALLBACK_PROPS`).
  - Form: `{"<stata class>": {"<file name>": (("<attr>", "scheme"|"literal", "<key or token>"), …)}}`. File names keep the `#` template (`"p#bar"`), and keys keep `#` (`"p#connect"`).
  - Contents, transcribed from 19.5 (E7):
    - seriesstyle: the 9 curated files, attrs `marker line area`;
    - markerstyle: the 7, attrs `symbol size fillcolor linestyle`;
    - areastyle: the 9, attrs `linestyle shadestyle`;
    - shadestyle: the hops those areastyles reach, attrs `color intensity`;
    - linestyle: all 76 except `p#` (S32's), attrs `width color pattern`.
  - Other attrs (`label`, `dots`, `connect`, `align`, `angle`, `back*`, `fill`) are not transcribed (D-36f).
  - Written from the extractor's `_meta.style_files` (TR-36.14) with a one-off print, and held equal to it by `TestTheStyleTable::test_it_is_19_5s_files`.
- **TR-36.2 `SchemeParser._STYLE_KNOWN`**: `{"seriesstyle": frozenset(28 file names), "markerstyle": …(28), "areastyle": …(29), "linestyle": …(76)}`, from `_meta.style_known`.
- **TR-36.3 `SchemeParser._STYLE_DEFAULT = {"seriesstyle": "p1", "markerstyle": "p1", "linestyle": "foreground", "areastyle": "background"}`.** Its comment cites E9.3. `TestDefaultAttributes` pins it against the fixture's U grid for all 26 schemes.
- **TR-36.4 Bundle-class tokens.** `_STYLE_CLASS = {"marker": "markerstyle", "line": "linestyle", "area": "areastyle", "series.marker": "seriesstyle", "series.line": "seriesstyle", "series.area": "seriesstyle"}`. A `series.*` token returns the named seriesstyle's role, resolved through its `marker`, `line` or `area` attr.
- **TR-36.5 `SchemeParser._style_kind(self, stata_class, name) -> str`.**
  - `s = str(name).strip(" \t")`, as S32 strips. `""` is `"blank"`, and `len(s) > 64` is `"unknown"` before any regex.
  - `re.fullmatch(r"p(?:[1-9]|1[0-5])", s)` is `"p"`, which is S32's path.
  - `m = re.fullmatch(r"p([1-9]|1[0-5])([a-z]+)", s)` with `"p#" + m[2]` in the class's table is `"table"`. A literal in the table is `"table"`.
  - In `_STYLE_KNOWN` (literally, or as `p#<suffix>` with a valid number) is `"known"`. Anything else is `"unknown"`.
  - The match is case-sensitive, as Stata's is. `p0`, `p03`, `p16line` and `P3` are unknown (E9.2).
- **TR-36.6 `SchemeParser._style_leaf(self, leaf_class, key, hop=False) -> "str | None"`** returns the raw value of `"<leaf_class> <key>"` along scheme.class's chain (E8):
  - a key starting `p`: `p<num><stub>`, `p<stub>`, `p<num>`, `p`, then the key itself;
  - any other key: exact;
  - `""`: the bare class key (E1).
  - `key` comes only from the table with `#` replaced by the validated number (1-15). No user text is ever formatted into a `_props` key.
  - **Leaf** (`hop=False`): if no step is present, it returns `_FALLBACK_PROPS`' value for the same lookup and notes D-36g's text once.
  - **Hop** (`hop=True`, `leaf_class` a style class: `markerstyle`, `linestyle`, `areastyle` or `shadestyle`; D-36h): at each step it returns the `_props` value if the scheme declares one. Otherwise it returns the step itself if `_style_kind(leaf_class, step)` is `"p"`, `"table"` or `"known"` (shadestyle: a `_STYLE_TABLE["shadestyle"]` name). It never notes. If no step qualifies, it returns None and the attr takes its class default (TR-36.7).
- **TR-36.7 `SchemeParser._style_resolve(self, stata_class, file, num, depth=0) -> dict`** builds the canonical form:
  - line `{color, alpha, width, dash}`;
  - marker `{symbol, size, fill, fill_alpha, line}`;
  - area `{fill, fill_alpha, intensity, line}`;
  - series `{marker, line, area}`.

  Rules:
  - A leaf converts through the E2 readers: colour to `_color_alpha`, linewidth to the S13 reader `_plot_lwidth_of` uses, linepattern to `_lpattern_chain`, symbol to `_symbol`, symbolsize to `_markersize_px`, intensity to `_intensity`.
  - A `none` colour is `None`, whether it is a literal in the style file or the scheme's value (`color pieline none`, `color fpspacer none`; E10). A literal `none` symbol is drawn as `msymbol(none)` (E2).
  - A style-name attr (`marker`, `line`, `area`, `linestyle`, `shadestyle`) takes a literal token as the style's name directly, and reads a `scheme` value with `_style_leaf(<sub class>, key, hop=True)` (D-36h):
    - `none` means that part is not drawn (colours `None`);
    - a p1-p15 name is S32's bundle, `self.style_bundle(<role>, name)`;
    - a table name recurses;
    - anything else is that class's default (TR-36.3).
  - Depth is capped at 6, which is ample for the deepest chain, series → area → shade.
- **TR-36.8 `SchemeParser._style_shape(self, cls, resolved) -> dict`** maps the canonical form to S32's shapes (E3) exactly:
  - line: `line`, `line_alpha`, `line_width`, `line_dash`;
  - area: `fill`, `fill_alpha`, `intensity`, `line`, `line_alpha`, `line_width`, `line_dash`;
  - marker: `fill`, `fill_alpha`, `line`, `line_alpha`, `line_width`, `symbol`, `size`.

  A hollow symbol keeps `fill_alpha` 0.0 as S32's does. `TestTheShapes::test_each_class_has_p1s_keys` asserts `set(style_bundle(cls, "ci")) == set(style_bundle(cls, "p1"))`.
- **TR-36.9 `style_bundle(self, cls, name)` extended** (S32's method; its p# body is unchanged).
  0. Strip as S32 strips, then unwrap one enclosing `"…"` or `` `"…"' `` (D-36j). Every later step, S32's p# path included, gets the unwrapped name.
  1. An unknown `cls` token returns None, and so does kind `"blank"`.
  2. Kind `"p"`: a `series.<role>` token returns `style_bundle(<role>, name)`, which is S32's p# path.
  3. Kind `"table"`: resolve, shape, and return a new dict.
  4. Kinds `"known"` and `"unknown"`: call `_style_note`, then return the class default's bundle. For `series.*`, that is p1's role bundle.

  The memo is `self.__dict__.setdefault("_style_memo", {})`, keyed `(cls, canonical name)` for table names and `(cls, "<default>")` for defaults. It is never keyed by user text, so it holds at most one entry per table name and bundle-class token (about 650). A copy is returned, never the memo's dict. An entry also keeps the D-36g notes its resolution raised, as `(key, text)` pairs, and a hit re-emits them through `_dash_warn_once`. A later render, or a served session, reusing the parser therefore still prints them.
- **TR-36.10 `SchemeParser._style_note(self, stata_class, name, kind)`** calls `_dash_warn_once(("named-style", stata_class, shown), text)`, where `shown = _dash_display(name)`. The texts are `f"dash: named style {shown} not found in class {stata_class}, default attributes used"` (unknown) and `f"dash: named style {shown} of class {stata_class} is not drawn by dash; default attributes used"` (known). S06's channel prints each once per command as `(note:  dash: …)`.
- **TR-36.11 `_FALLBACK_PROPS`.** Append a block after S24's histogram keys, headed `# Named styles (WP-30 S36): every key the style table reads, at s2color's values (scheme-s2color.scheme; scheme_truth.json "named_style_directives")`. It holds every directive of dash-s2color.scheme's S36 group, value for value.
- **TR-36.12 S32's plan (D-36b, D-36d).**
  - `GlyphMapper._STYLE_FACTORS`: the `pstyle` and `p` rows map `marker→series.marker`, `mline→series.marker`, `line→series.line`, `area→series.area` and `aline→series.area`. No other row and no function body of the plan changes, except the retirement below.
  - Retire `_style_unresolved`, `_STYLE_UNREAD_NOTE`, the plan's `"unresolved"` list and `_style_restyle`'s loop over it. `_style_plan` still skips a key whose bundle is None (blank or a bad class).
  - D-36i: a new class constant `_STYLE_NOTE_ONLY = (("dstyle", "marker"), ("dlstyle", "line"), ("bmlinestyle", "line"))`. `_style_plan`'s first statements, before its early return, call `self.scheme.style_bundle(cls, value)` for each non-blank one and discard the result. Only the note survives. No role, factor or bundle comes from these keys.
- **TR-36.13 The ci types (D-36e).**
  - `_ci_pstyle`: after its ci/ci2 and p# branches, `k = self.scheme._style_kind("seriesstyle", s)`. A `"table"` kind returns `("named", s)`. Otherwise it calls `self.scheme._style_note("seriesstyle", s, k)` and returns `("p", 0)`. Its old note text and `"ci-pstyle"` key are deleted.
  - `_ci_band_style`: `ps == "named"` gives `st = dict(sch.style_bundle("series.area", name))`.
  - `_ci_line_restyle`: `"named"` restyles from `style_bundle("series.line", name)`, in its `p` branch's form.
- **TR-36.14 The scheme extractor** (`scripts/extract_scheme_truth.py`).
  - Add the constants `NAMED_STYLE_CLASSES` and `NAMED_STYLE_CURATED` (E7's lists, linestyle as "every file").
  - Add `style_table(r)`, which transcribes the table's files plus the shadestyle hops into `{class: {file: [[attr, kind, value], …]}}`.
  - Add `style_known(r)` (`{class: sorted file names}` for the four option classes).
  - Add `named_style_directives(r, provenance, sources)`, a scheme.class-faithful walk (E8, not `linked()`'s class default). It collects every `(class, key)` the scheme *declares* along each table name's chain and returns `{"<class> <key>": value}`. Values are spelled as the existing groups spell them:
    - a colour goes through the resolver to `_color_token(hex, opacity)` (`#rrggbb` or `#rrggbb%NN`, as `color p11 #2d6d66` at dash-s2color.scheme:59);
    - a `none` colour, for which `_color_token` returns None, is written as Stata's token `none` and never skipped (`color pieline`, `color fpspacer`; E10);
    - any other value is written as Stata's own token (`medium`, `solid`, `circle`).

    Only leaf classes are written (`color`, `linewidth`, `linepattern`, `symbol`, `symbolsize`, `intensity`). No hop key is written (D-36h). Hops go to `_meta.style_hops` instead (`{scheme: {"<class> <key>": declared value}}`), which `test_the_style_name_hops_are_identity` compares with D-36h's rule. Each entry gets `sources["named_style_directives.<class> <key>"]` and a transcribed provenance entry naming the file and line. A key no step resolves goes to `unresolvable`.
  - `extract()` stores it as `"named_style_directives"`. `main()` writes `_meta.style_files`, `_meta.style_known` and `_meta.style_hops`.
  - `expected_directives` gains a last group, `"Named styles (WP-30 S36): the keys Stata's style files read for the named styles dash draws"`, of those directives in sorted order, skipping any key an earlier group carries.
  - A second run is a no-op.
- **TR-36.15 The Stata truth extractor** (`scripts/extract_style_name_truth.do`; see "Stata truth").
- **TR-36.16 dash.ado and dash_parse.mata** (BR-36.5).
  - Declare `DSTyle()`, `DLstyle()` and `BMLinestyle()` in the form S32 declares `MSTyle()` at the base (`grep -n 'MSTyle(' dash.ado`), after S32's last named-style declaration.
  - Add a pending line for each, `` if `: length local dstyle' local _dash_pending `"`_dash_pending' dstyle"' ``, under a comment citing P2.9/P2.8.
  - Add `sreturn local dstyle : copy local dstyle` (and the other two) beside `mlstyle`.
  - Add `dstyle dlstyle bmlinestyle` to `_dash_plot_opts_to_json`'s key list after S32's style keys, and to `_dash_p_drops` with a comment ("p() sets the whole seriesstyle, dots and marker back line included; twoway_yxview_parse.class:631, 729, 740").
  - Append the three names to `_dash_stylelist_keys()`'s returned string in dash_parse.mata. Its header entry is unchanged.
  - Every program edited keeps `version 19`.
- **TR-36.17 Both modes.**
  - No copy-list change (R2 row S36). The table, the methods and the memo travel with `SchemeParser`. The keys travel in `_SCHEME_PROPS`. `_dash_warn_once` and `_dash_display` are already served (E5).
  - No JS twin. No page script writes a style (S32's guard `test_no_page_script_writes_a_style`).
  - A saved computed layer keeps its named style on the stale cue, because `_dash_stale_glyph` (1130) clones the styled glyph.
- **TR-36.18 Registries (X.5, A148).**
  - Under `# WP-30 S36 (P1.14b): Other style names (P1.14 part b)` in `test/function_test_map.py`, in alphabetical order: `SchemeParser._style_kind`, `SchemeParser._style_leaf`, `SchemeParser._style_note`, `SchemeParser._style_resolve` and `SchemeParser._style_shape`, each naming its `test/test_style_names.py` node.
  - Delete S32's `GlyphMapper._style_unresolved` key.
  - `program_coverage_map.py` is unchanged, because no program or Mata function is added.
- **TR-36.19 Pins (R10).**
  - `test_unsupported_report_is_true.py`: :240 and :607 each gain 3 from their base values, with the comment `# <old> -> <new>: P1.14b dstyle dlstyle bmlinestyle declared and named`. R10's table lists S36 for :607 only. The orchestrator is asked to add S36 (12) to the :240 row (Notes). No batch-12 partner moves :240, and the merge log says so.
  - `PLOT_VALUES` gains `"dstyle": ("p3", "p5", "scatter")`, `"dlstyle": ("p3", "p5", "scatter")` and `"bmlinestyle": ("p3", "p5", "scatter")`. `_render` (:202) builds one `yvar`/`xvar` layer, so a pc type cannot be drawn there, and twoway accepts all three on scatter (E9.7).
  - The help's Unsupported section moves with them (R10, `test_help_conformance.py::TestTheUnsupportedSectionIsTrue`).
- **TR-36.20 Security (rule 1).**
  - Names are data: matched against fixed sets and one anchored regex, never a path, never formatted into a key, never `eval`'d.
  - Shown only through `_dash_display`, then S06's SMCL escape.
  - Memo bounded (TR-36.9).
  - `TestAdversarial` covers `../x`, `p3;rm -rf`, `{bf:x}`, `"\x00"`, `"x"*10000`, `"ｐ３"`, `"p٣"`, `"REFLINE"`, `"refline\n"`, `'""refline""'` and `'"refline'`. Each must be inert and noted, with the note holding at most 80 printable characters of name.
  - `'"refline"'` (one pair of quotes) draws refline with no note, as twoway does (D-36j, E9.6).
  - 10,000 distinct names finish in under 1 s, add no memo entry, and read only table keys (a `_props` spy).
  - Twoway refuses none of these names (E9.6), so dash refuses none (M5).
- **TR-36.21 Help** (R3, A155).
  - In "Stata scheme support", insert a `{phang2}{ul:Named styles.}` paragraph after `{ul:Series.}`. It lists the names each option class takes (E7), the default attributes and the two notes, D-36c's not-drawn names, and that a user scheme's keys reach them.
  - In "Stata scheme support", update `{ul:What the shipped files are.}` (R3, owned by no batch-12 partner):
    - the directive bounds become those 36-16 measures (R10, the pin `test_the_directive_count_is_what_the_help_says`);
    - the carried keys gain "the keys Stata's style files read for the named styles, `color refline` among them";
    - "Most of the directives dash does not carry govern what it does not draw: … dot and matrix charts, margins and tick geometry" gains "(the line styles of those names, such as `tick` and `pie`, are carried for `lstyle()`)".
  - In "Unsupported Stata twoway options", add `{phang2}{ul:Dot and marker back-line styles.}`: `{opt dstyle(markerstyle)}`, `{opt dlstyle(linestyle)}` and `{opt bmlinestyle(linestyle)}` are kept and named; dash does not draw dot rows (P2.9) or marker back lines (P2.8).
  - No help line names a tool or vendor.

## Boundaries

- **S32's** functions keep their bodies:
  - `_style_plan`, `_style_options`, `_style_value` and `_style_restyle` change only by the retirement and `_style_plan`'s note-only calls (TR-36.12, D-36i);
  - the three appliers, the ten mappers, `_dash_plot_style_indices`, `_dash_p_drops`' existing keys, `p()` handling and per-y splitting are untouched;
  - S36 adds keys only.
- **S34** (batch 12): `SchemeParser._resolve_path`, `resolve_or_fallback`, `_include`, `DashRenderer._scheme_for`, `_dash_scheme_dirs`, the ado-path lookup, and the scheme-support "remedy" paragraph. S36 reads no path.
- **S35** (batch 12): every date-axis function, `_make_figure_body`, `_build_sources_and_figures`, the template, the finishers.
- **S33** (batch 11): `_apply_mlabel_opts` and the marker-label and colour-key defaults. By ratification row 4 (06oct2026) S33 keeps no list of noted keys and no read-recording: every parsed directive is retained in `_props`, unread ones included, and none is noted (S33's D-33d). A key S36's table starts reading is already there; S36 has nothing of S33's to update. `TestAUserScheme::test_unread_directives_stay_and_print_nothing` checks it.
- **Later:**
  - S38 and S39 call `style_bundle` and never edit it;
  - S43 composes `*#` through `_style_value`;
  - S45's `recast()` changes the role table, not the names.
- **Residuals** (not drawn, still named):
  - dot rows (`dstyle`, `dlstyle`; P2.9);
  - marker back lines and arrowheads (`bmlinestyle`, `mstyle()` on pc arrows; P2.8);
  - area and rarea outlines of a named style (P2.12);
  - the label role of a seriesstyle (P2.12);
  - the 57 names of D-36c and the general 161-file resolver (manifest item-14 residual).

  Brushed-away and muted copies are not a residual: they follow S08's brushed-copy sync (ratification row 27), which carries a glyph's styled properties to its nonselection and muted copies.
- **Not touched:** the tracking documents (A145), `rejected_options.json`, `abbrev_truth.json`, `_make_figure_body`, `_generate_app_source`, and every copy list.

## Stata truth

**New extractor** `scripts/extract_style_name_truth.do` writes the **new fixture** `test/fixtures/style_name_truth.json` (`git add -f`, `.git/info/exclude:58`).
- It copies S02's path-free form (R7): root `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else `exit 601` with "set DASH_REPO to the dash repository".
- It opens `adopath ++ "<root>/"`, `global dash_nobrowser 1`, `version 19`, `set graphics off`, `set more off`, `local entry_scheme "`c(scheme)'"`. It exits 601 when `c(python_exec)` is empty.
- The D12 stamp is `_meta`: `stata_version`, `born_date`, `dash_commit` (`shell git -C "<root>" rev-parse HEAD > <tempfile>`, `file read`, reaching python through `Macro.getLocal`), `extracted` (`c(current_date)`), `source` and `seconds` (the timer).
- Run once, from the worktree. It takes about 11 minutes (E9.5):

  ```
  mkdir -p "$S/truth"
  DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/truth" "$WT/scripts/extract_style_name_truth.do"
  git -C $WT add -f test/fixtures/style_name_truth.json
  ```

  The log is `$S/truth/extract_style_name_truth.log`. No other section runs it (R7).

**Method.**
- Data: `sysuse auto, clear`. The schemes are Stata's 26, listed literally (E9.3's list).
- Program `_os_read k`: for plot `k`, read into one `|` record:
  - marker: `mf mfop mfs ml mlop mls mlw ms msz`;
  - line: `lc lop lcs lw lp`;
  - area: `af afop afs ai al alop als alw alp`;
  - label: `labc`.

  Each comes from `` `.Graph.plotregion1.plot`k'.style.<…>.rgb' ``, `.opacity`, `.stylename` (the `*s` fields, for `none`), `.val` or `.stylename`. The python block collapses blanks in rgb.
- Program `_os_batch id scheme opt type names`: one `capture noisily twoway (<type> mpg weight in 1/2, <opt>(<n1>)) (… <n2>) … , nodraw legend(off) scheme(<scheme>)` of at most 25 layers. The types are `pstyle`/`mstyle` on `scatter`, `lstyle` on `line` and `astyle` on `area`. It records `_rc` and reads every plot. A layer whose name is unknown would print notes, so the U grid runs one name per call instead.
- Notes: each call runs under `log using <tmp>, text replace` and records the `(note:  …)` lines.

**Grids** (record id `GRID|SCHEME|OPTION|NAME`):
- **N (names).**
  - stcolor, s2color, s1mono and s1rcolor: every table name of every class (E7). That is 93 seriesstyle on `pstyle`, 49 on `mstyle`, 51 on `astyle` and 229 on `lstyle`, for 422 records each.
  - The other 22 schemes: the plain names, plus the p1, p3 and p15 instances of each template, for about 149 records each.
- **U (unknown and default; one name per call, on plot 2 after a plain plot 1).**
  - Names `bogus P3 p16 p0 p03 Ci` and a 40-character name, under every option.
  - Plus `p16line p3other p3mark foreground` under `pstyle` and `mstyle`, and `p16box` under `mstyle`, on all 26 schemes.
  - Records the notes.
- **K (known, not drawn; stcolor).** `pstyle(fpall)`, `pstyle(dendrogram)`, `mstyle(sunflower)`, `mstyle(star)`, `astyle(plotregion)` and `astyle(outline)`: rc, notes (none expected) and roles.
- **C (ci types; stcolor, s2color).** `lfitci mpg weight`, `lpolyci mpg weight` and `qfitci mpg weight` with `pstyle(histogram)`, `pstyle(p3bar)`, `pstyle(p3line)`, `pstyle(ci2)` and `pstyle(bogus)`: band (area) and line.
- **T (pstyle(ci)/ci2 on types; stcolor, s2color).** `scatter line connected area bar rarea spike rcap dropline` with `pstyle(ci)` and `pstyle(ci2)`, using each type's variables as in S32's R grid.
- **Q (note counts; stcolor).** E9.4's two commands, plus `(scatter mpg weight, lstyle(bogus)) (scatter price weight, lstyle(bogus))`.
- **D (declared, not drawn; stcolor).** These record rc and notes:
  - `scatter, dstyle(p3)`, `dst(p3)`, `dlstyle(p3)`, `dl(p3)` and `dls(p3)`;
  - `pcbarrow mpg weight price length in 1/5, bmlinestyle(p3)` and `bml(p3)`;
  - `scatter, dstyle(bogus)`, `dlstyle(bogus)` and `bmlinestyle(bogus)`, whose notes are E9.7's;
  - `scatter mpg turn weight, dstyle(p3 p4)`, reading each plot's `.style.dots`;
  - `scatter, bm(p3)`, which is r(198).
- **H (hostile names; stcolor, one per call).** `lstyle` on line and `pstyle` on scatter, with `../x`, `{bf:x}`, `p3;x`, `"refline"`, `REFLINE`, `x.y`, `3` and a 200-character name: rc and notes (E9.6).
- **S (SVG; stcolor).** `line, lstyle(none)`, `scatter, mstyle(none)`, `area, astyle(none)`, `area, astyle(bogus)` and `line, lstyle(refline)`, each exported and read by S32's `scripts/svg_truth.py` (by path).

**Fixture keys.**

```
{"_meta": {"stata_version", "born_date", "dash_commit", "extracted", "source": "scripts/extract_style_name_truth.do", "seconds"},
 "schemes": [26 names],
 "records": {"N|stcolor|lstyle|refline": {"rc": 0, "plot": 1, "type": "line",
              "marker": {"fill", "fill_opacity", "fill_none", "line", "line_opacity", "line_none", "line_width", "symbol", "size"},
              "line":   {"color", "opacity", "none", "width", "pattern"},
              "area":   {"fill", "fill_opacity", "fill_none", "intensity", "line", "line_opacity", "line_none", "line_width", "line_pattern"},
              "label_color"}},
 "notes": {"<record id>": ["(note:  named style … )", …]},
 "svg": {"S|stcolor|lstyle|none": {"strokes": [[hex, n]], "fills": [[hex, n]]}}}
```

Colours are lower-case `#rrggbb`. Widths and sizes are Stata's numbers. A difference from E9 is investigated and reported, never patched (R7).

**Truth block** (`test/test_wp30_truth.cscript`, S36's stub, TR-01.6/TR-01.10 form). The cases go between the start and end display lines, which stay the block's first and last statements:

```stata
* ==== S36 P1.14b: Other style names ====
local only : env WP30_ONLY
if inlist("`only'", "", "S36") {
    display as text "S36 start " c(current_date) " " c(current_time)
    * OS-01 .. OS-06 here
    display as text "S36 end " c(current_date) " " c(current_time)
}
* ==== end S36 ====
```

- The helpers `_s36_page`, `_s36_app` and `_s36_case` copy S32's `_s32_*` pattern. They sit directly above S36's header, outside every gate, and declare `version 19`. They compare the layer's stroke, fill, symbol and dash in the saved page, the served document, and the served document after a `filter(price, type(range))` move, against twoway's graph object on the same command.

| Case | Check |
|---|---|
| OS-01 | s2color `line mpg weight, sort lstyle(refline)`: dash's Line is `#2d6d66`, at the width `translate_lwidth(".3")` gives, solid, saved = served = after move = twoway |
| OS-02 | stcolor `scatter mpg weight, pstyle(ci)`: marker fill `#a0a0a0`, size ratio to the default 1.52778/1.04166 within 1%, both modes |
| OS-03 | s2color `area mpg weight, sort astyle(bogus)`: fill `#eaf2f3`; the log holds `(note:  dash: named style bogus not found in class areastyle, default attributes used)` once; twoway's log holds its own note |
| OS-04 | stcolor `scatter mpg weight, pstyle(fpall)`: rc 0, drawn as p1, the log holds D-36c's note once, twoway's none |
| OS-05 | stcolor `lfitci mpg weight, pstyle(histogram)`: band fill and line equal twoway's C record, both modes |
| OS-06 | `dash dot mpg weight, dstyle(p3) dlstyle(p3)` and `dash pcbarrow mpg weight price length in 1/5, bmlinestyle(p3)`: `dash_json_<g>` holds the three keys by value; the note names `dstyle() dlstyle()` and `bmlinestyle()` |

`test/test_abbreviations.cscript` gains **OS-07**: `dst(p3)`, `dl(p3)`, `dls(p3)` and `bml(p3)` land on `dstyle`/`dlstyle`/`bmlinestyle` in `dash_json_<g>`, and the note names them by full name. It is one contiguous run after the file's last case (R1). Before first use, `grep -E '(^|[^A-Za-z0-9_])OS-[0-9]' test/*.cscript test/*.py test/*.do` prints nothing.

## TDD test stubs

### Regression tests written by 36-01 (fail at the base; literal values from E9)

In `test/test_style_names.py` (new). The module docstring cites research p1-14 §2.3-2.4, E9 and the register rows. Helpers: `_figure(mode, tmp_path, plots, scheme)` in `test_ci_band_style.py`'s form (:361), `_glyphs(fig)`, `_px_w(stata)` = `OptionTranslator.translate_lwidth(str(stata))`, and `_notes(callable)` counting `dash: named style` texts.
- Test: `TestTheTableNames::test_s2color_lstyle_refline[saved|served]`: Line `#2d6d66`, `_px_w(.3)`, `[]` dash.
- Test: `TestTheTableNames::test_stcolor_major_grid_is_dashed[saved|served]`: `#f0f0f0`, dash pattern of `dash`.
- Test: `TestTheTableNames::test_stcolor_minor_grid_is_dotted[saved|served]`: `#505050`, `_px_w(.2)`, dot.
- Test: `TestPstyleCi::test_stcolor_scatter[saved|served]`: fill `#a0a0a0`, size ratio 1.52778/1.04166.
- Test: `TestPstyleCi::test_s2color_line_ci2[saved|served]`: Line `#808080` (ci_line).
- Test: `TestSeriesForms::test_s2color_scatter_p3bar[saved|served]`: marker `#55752f`.
- Test: `TestSeriesForms::test_stcolor_area_astyle_p3bar[saved|served]`: fill `#00bf7f` at intensity 0.8 through S16's blend; outline `_px_w(.2)`.
- Test: `TestMarkerForms::test_stcolor_mstyle_histogram[saved|served]`: fill `#1a85ff`, line `#5faaff` at `_px_w(.15)`, size ratio 1.94444/1.04166.
- Test: `TestAreaForms::test_s2color_astyle_background[saved|served]`: fill `#eaf2f3`.
- Test: `TestNone::test_lstyle_none_draws_no_line[saved|served]`, `::test_mstyle_none_draws_no_marker`, `::test_astyle_none_draws_nothing`: alphas 0.
- Test: `TestUnknown::test_lstyle_bogus_is_the_foreground_line[saved|served]`: stcolor, plot 2, `#000000`, `_px_w(.2)`, solid.
- Test: `TestUnknown::test_s1rcolor_lstyle_bogus_is_white`.
- Test: `TestUnknown::test_astyle_bogus_is_the_background[saved|served]`: s2color `#eaf2f3`, economist `#c6d3df`.
- Test: `TestUnknown::test_pstyle_bogus_on_plot_2_is_p1[saved|served]`: stcolor `#1a85ff`.
- Test: `TestUnknown::test_mstyle_bogus_on_plot_2_is_p1s_marker`: marker `#1a85ff`, line kept `#d41159`.
- Test: `TestUnknown::test_p0_p03_p16line_p3other_are_unknown`: the kinds via `_style_kind`.
- Test: `TestTheNote::test_twoways_words_once`: `area, astyle(bogus)` gives exactly one `dash: named style bogus not found in class areastyle, default attributes used`.
- Test: `TestTheNote::test_two_layers_print_one_line` (E9.4 via S06).
- Test: `TestTheNote::test_a_table_name_is_silent`.
- Test: `TestTheNote::test_unused_role_is_noted` (E9.4).
- Test: `TestTheNote::test_known_not_drawn_is_named`: `pstyle(fpall)` gives D-36c's text and draws p1.
- Test: `TestTheNote::test_dstyle_bogus_is_noted` (E9.7, D-36i): `scatter, dstyle(bogus)` gives exactly one `dash: named style bogus not found in class markerstyle, default attributes used`. `dlstyle(bogus)` and `bmlinestyle(bogus)` give the linestyle text. `dstyle(p3)` gives no such note, and the drawing is unchanged.
- Test: `TestAdversarial::test_one_pair_of_quotes_is_unwrapped[saved|served]` (D-36j): `lstyle("refline")` draws `#2d6d66` with no note.
- Test: `TestAfterAFilterMove::test_a_graphs_own_scheme_reaches_the_style[saved|served]`: a dashboard in s2color with one graph `scheme(stcolor)` and `line, lstyle(refline)` draws `#000000` (E9.1) before and after `_move_price`, through S34's `_dash_under_graph_scheme` in the served app.
- Test: `TestCiTypes::test_lfitci_pstyle_p3bar_band_is_p3bar[saved|served]`: the band equals `style_bundle("series.area","p3bar")`; the C grid pins the values in 36-03.
- Test: `TestAUserScheme::test_a_child_override_reaches_lstyle_refline`: `#include s2color` plus `color refline red` gives `#ff0000`.
- Test: `TestAUserScheme::test_unread_directives_stay_and_print_nothing` (guard; S33's D-33d, ratification row 4): a user scheme `#include s2color` plus `color refline red` and `clockdir p 9`, drawn with `line, lstyle(refline)`, keeps `clockdir p` → `9` in `_props` and records no `dash scheme:` warning.
- Test: `TestAUserScheme::test_a_missing_key_takes_s2colors_value` (D-36g text once).
- Test: `TestTheFallback::test_every_table_name_matches_s2color`: not None and equal, for every class and table name.
- Test: `TestTheShapes::test_each_class_has_p1s_keys`.
- Test: `TestAdversarial::test_hostile_names_are_inert_and_noted[name]` (TR-36.20).
- Test: `TestAdversarial::test_ten_thousand_names_are_bounded`.
- Test: `TestAdversarial::test_no_props_key_comes_from_user_text`.
- Test: `TestAfterAFilterMove::test_served_style_survives_a_move` (`lstyle(refline)`, `_move_price` of test_keyword_names.py:339).
- Test: `TestAfterAFilterMove::test_saved_stale_cue_keeps_the_style` (`lfit, lstyle(refline)` muted glyph `#2d6d66`).

### Added by 36-03 (fixture-driven; fail at the base unless marked guard)

- Test: `TestTheFixture::test_meta_is_stamped` (guard).
- Test: `TestTheFixture::test_every_scheme_is_recorded` (guard; equals `SchemeParser._BUILTIN_NAMES`).
- Test: `TestAgainstStata::test_each_scheme[scheme]` (26 nodes): every N record. `style_bundle` for the option's class equals the record through `translate_lwidth`, `translate_msize`, `translate_lpattern`, `translate_msymbol`, rgb to hex, and `*_none` to `None`. The diffs are collected and listed.
- Test: `TestDefaultAttributes::test_each_scheme[scheme]`: every U record equals `_STYLE_DEFAULT`'s bundle, and every U and Q note list is the expected text.
- Test: `TestKnownNotDrawn::test_each_k_record`: K records are rc 0 with no twoway note, and dash draws the default with D-36c's note.
- Test: `TestCiTypes::test_each_c_record[mode]` and `TestPstyleCi::test_each_t_record[mode]`.
- Test: `TestSvg::test_none_forms`.
- Test: `TestDeclaredNotDrawn::test_each_d_record`: every D record has its rc (`bm()` 198, the rest 0) and its notes; dash's spec and notes agree for the rc-0 ones.
- Test: `TestHostileNames::test_each_h_record`: every H record is rc 0. dash draws the same default (or refline, for `"refline"`) and notes each name, escaped and shortened (E9.6).
- Test: `TestS32sOtherNameRows::test_each_u_row`: every U row of S32's `named_style_truth.json` (132) now matches.
- Test: `TestTheStyleTable::test_it_is_19_5s_files` (against `scheme_truth.json` `_meta.style_files`).
- Test: `TestTheStyleTable::test_every_linestyle_file_is_read` (76).
- Test: `TestTheStyleTable::test_known_lists_match` (`_meta.style_known`).

### In `test/test_scheme_fidelity.py` (36-04)

- Test: `test_the_style_table_is_transcribed`: `_meta.style_files` holds 76 linestyle files and the curated ones.
- Test: `test_the_named_style_directives_are_carried[name]` (26).
- Test: `test_the_style_name_hops_are_identity[name]` (26; E10, D-36h). For every `_meta.style_hops` entry of the scheme, `SchemeParser(name)._style_leaf(cls, key, hop=True)` equals the declared value, and that value is a style the runtime resolves (S32's p# or a table name). It also asserts that no shipped file carries a hop key.
- Test: `test_the_named_style_walk_follows_scheme_class`: `color refline` absent with a bare `color` class default is unresolvable, not the default (E8).

### Parity and flips

- `test/test_mode_parity.py` `CORPUS` gains `s36_lstyle_refline` (`line mpg weight, sort lstyle(refline)`), `s36_pstyle_ci` (`scatter, pstyle(ci)`), `s36_astyle_bogus` (`area, sort astyle(bogus)`, with its own `_MUST_WARN` entry) and `s36_mstyle_histogram`.
- The flips are E12's table.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Table equals 19.5's files | pytest `TestTheStyleTable`, `test_scheme_fidelity.py` | `scheme_truth.json` `_meta` | n/a |
| Every table name against twoway, 26 schemes | pytest `TestAgainstStata` | `style_name_truth.json` N | saved units; modes by TestBothModes classes |
| Default attributes and notes | pytest `TestDefaultAttributes`, `TestTheNote`; cscript OS-03, OS-04 | U, Q, K | yes |
| ci types | pytest `TestCiTypes`; cscript OS-05 | C | yes |
| pstyle(ci) on types | pytest `TestPstyleCi`; cscript OS-02 | T | yes |
| Regeneration | pytest `test_scheme_fidelity.py` (no-op, once, provenance) | `scheme_truth.json` | n/a |
| Fallback | pytest `TestTheFallback` | — | served rebuild through `_SCHEME_PROPS` |
| User scheme | pytest `TestAUserScheme` | tmp scheme | yes |
| Declared, not drawn | pytest `test_unsupported_report_is_true.py`; cscript OS-06, OS-07, HC8-07 | D | spec |
| Hostile names, quotes, undrawn options' notes | pytest `TestHostileNames`, `TestDeclaredNotDrawn`, `TestTheNote::test_dstyle_bogus_is_noted`, `TestAdversarial::test_one_pair_of_quotes_is_unwrapped` | H, D | yes |
| Shipped-file pins | pytest `test_help_claims_8.py::TestTheShippedFiles` (four flips, E12) | `scheme_truth.json` | n/a |
| Hop rule | pytest `test_scheme_fidelity.py::test_the_style_name_hops_are_identity` | `_meta.style_hops` | n/a |
| After a move | pytest `TestAfterAFilterMove`; cscript OS-01 | — | saved stale cue and served move |
| Parity | pytest `test_mode_parity.py` | CORPUS | yes |
| Security | pytest `TestAdversarial` | — | yes |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `TestTheServedAppCarriesEveryName`, `TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |

**Acceptance criteria.**
- **AC-36.1** Every `TestAgainstStata` node passes. Each of the 26 schemes' N records equals `style_bundle`, with no record excluded.
- **AC-36.2** Every U record draws `_STYLE_DEFAULT`'s bundle, and the note is printed once per distinct (class, name) per command, in twoway's words prefixed `dash:`. OS-03 prints PASS.
- **AC-36.3** The K names draw the defaults with D-36c's note. OS-04 prints PASS.
- **AC-36.4** The ci and T records pass in both modes. OS-02 and OS-05 print PASS.
- **AC-36.5** The 26 regenerated files and `scheme_truth.json` keep every pre-existing directive and record. Each file gains only its S36 group and provenance lines, and a second run prints `up to date` 26 times.
- **AC-36.6** `dstyle`, `dlstyle` and `bmlinestyle` and their abbreviations reach the spec and are named. OS-06, OS-07 and HC8-07 print PASS.
- **AC-36.7** Saved, served and after-move drawings agree (G3), and `TestAfterAFilterMove` passes.
- **AC-36.8** `TestAdversarial` and `TestHostileNames` pass, with 10,000 names in under 1 s and no memo growth. No style name is refused, as none is in twoway (E9.6).
- **AC-36.9** The full suite runs green once through the queue. G4, G5 and G7 pass.

## Tasks

**Commit boundary.** Tasks 36-01 to 36-17 form the one commit of entry `P1.14b`, subject `Draw Stata's other style names and twoway's default attributes (WP-30 P1.14b)`.
- It is made by 36-17 on `wp30-s36` in the worktree `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s36` (`$WT`), after one full run through the queue.
- `$S` is `<scratch>/s36`, where `<scratch>` is the orchestrator's WP-30 scratch directory (index "Deltas"). Every command runs from `$WT` unless it names the main checkout.
- The body:
  1. opens with `<scratch>/36-P1.14b-failure.txt`;
  2. then the measured defect (E9, E11) and what changed, where, in both modes;
  3. then one line each:
     - `Regression: test/test_style_names.py::<Class>::<test> -- failed at <batch-12 base sha> with <text>`, one per regression class;
     - `Flipped: <node> -- <old expectation> was wrong because <why>`, for every E12 row and every line of `$S/36-flips.txt`;
     - `Fixture: test/fixtures/style_name_truth.json (scripts/extract_style_name_truth.do)`;
     - `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
     - `BUGS.md: "Style names other than p1-p15, such as ci, histogram, refline and p1bar, are not read by pstyle() and the other style options" (closed)`;
     - a `Scope:` line naming D-36b's `_STYLE_FACTORS` rows and D-36e's three ci methods;
     - a `Rebaselined:` line only if the single-y digest moved (R10). It should not, because no corpus case names a style.

No subject, body, BUGS line, CHANGELOG line or help line names a tool or vendor (G7). `grep -Eic 'claude|anthropic'` prints 0 on the message file before committing and on `git log -1 --format=%B` after. Never stage `CLAUDE.md`, `.gitignore`, `AGENTS.md`, `.ultraplan/` or any `*.html` (E7, G6).

<task type="auto" id="36-01">
  <name>Write the failing style-name regression tests</name>
  <files>test/test_style_names.py</files>
  <action><![CDATA[
    Run `mkdir -p "$S"`. Check that `git -C $WT rev-parse HEAD` equals `<scratch>/batch-12-base.txt` and that `git -C $WT branch --show-current` prints `wp30-s36`; otherwise stop. Read `<scratch>/batch-12-impact.txt` and confirm it records E13's HIGH warnings for `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle` with approval; for any of `SchemeParser.style_bundle`, `GlyphMapper._style_plan`, `_style_restyle` missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout (never in $WT), append it and report any HIGH/CRITICAL before editing. Record S32's interface in `$S/36-interface.txt` from `grep -nE 'def style_bundle|_STYLE_FACTORS|def _style_plan|def _style_restyle|def _style_unresolved|_STYLE_UNREAD_NOTE|def _ci_pstyle' $WT/dash_render.py`, `grep -n '_dash_p_drops\|MSTyle(' $WT/dash.ado`, `grep -n '_dash_stylelist_keys' $WT/dash_parse.mata`, `grep -n 'histogram_line\|def _dash_emit_note' $WT/dash_render.py` and `test -f $WT/test/fixtures/named_style_truth.json`; if `style_bundle(self, cls, name)` or `_STYLE_FACTORS` is missing, or `_style_plan` does not call `style_bundle` with the bundle class from `_STYLE_FACTORS`, stop and report (S32 owns them). Create test/test_style_names.py with every test of "Regression tests written by 36-01", exactly those class and test names, the helpers named there, expectations as E9's literal values (widths and sizes compared through `OptionTranslator.translate_lwidth`/`translate_msize`, never pixel literals). Run `python3 -m pytest test/test_style_names.py -q -n0 -p no:cacheprovider -rf > "$S/36-01.log" 2>&1`. Write `<scratch>/36-P1.14b-failure.txt` with the base sha, then each FAILED line with its first assertion text, then the guard tests (E12's guards) run green: `python3 -m pytest test/test_ci_band_style.py -q -n0 -p no:cacheprovider -k test_a_pstyle_dash_does_not_know_is_p1`. Do not touch dash_render.py, and do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/36-01.log"` prints at least 40; `grep -E '^FAILED.*TestPstyleCi::test_stcolor_scatter' "$S/36-01.log"` prints a line; `test -s <scratch>/36-P1.14b-failure.txt`; `test -s "$S/36-interface.txt"`.]]></verify>
  <done>Every 36-01 regression test existed with twoway's literal values and failed on the unmodified base, the guards passed, S32's interface was recorded, and the failure text was saved.</done>
</task>

<task type="auto" id="36-02">
  <name>Write and run the style-name truth extractor</name>
  <files>scripts/extract_style_name_truth.do, test/fixtures/style_name_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_style_name_truth.do exactly as "Stata truth" specifies: S02's path-free root, the opening lines, `version 19`, the python_exec gate, `_os_read`, `_os_batch` (at most 25 layers per call; the U grid one name per call on plot 2), the N, U, K, C, T, Q, D and S grids with the 26 scheme names written literally, notes captured from a text log, SVGs read through `scripts/svg_truth.py` imported by path, and the `_meta` stamp. The python block uses `sfi.Macro.getLocal`, never `shell=True`, writes a backtick as `\x60`, writes `indent=2, sort_keys=True` to `<root>/test/fixtures/style_name_truth.json`, prints `style_name_truth: wrote <N> records in <s> s`, erases every SVG and restores `entry_scheme`. Run it with `DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S/truth" "$WT/scripts/extract_style_name_truth.do"`, then `git -C $WT add -f test/fixtures/style_name_truth.json`. Compare its N|s2color|lstyle|refline, N|stcolor|pstyle|ci, U|s1rcolor|lstyle|bogus and Q records with E9 and stop and report on any difference.
  ]]></action>
  <verify><![CDATA[`grep -E '^style_name_truth: wrote [0-9]+ records' "$S/truth/extract_style_name_truth.log"` prints one line with at least 4500 records; `python3 -c "import json;d=json.load(open('$WT/test/fixtures/style_name_truth.json'));r=d['records'];print(r['N|s2color|lstyle|refline']['line']['color'],len(d['schemes']),sorted(d['_meta']))"` prints `#2d6d66 26` and a list holding `born_date`, `dash_commit`, `extracted`, `stata_version`.]]></verify>
  <done>The extractor measured every table name, the defaults, the notes, the ci and type grids and the declared options from Stata 19.5, and the stamped fixture was staged.</done>
</task>

<task type="auto" id="36-03">
  <name>Add the fixture-driven style tests</name>
  <files>test/test_style_names.py</files>
  <action><![CDATA[
    Append every class of "Added by 36-03" to test/test_style_names.py, with those names, reading `test/fixtures/style_name_truth.json`, S32's `test/fixtures/named_style_truth.json` (U rows only) and `test/fixtures/scheme_truth.json` `_meta`. Per-scheme nodes collect every mismatching record id with its two values into one assertion message. A missing fixture key fails, never skips. Run `python3 -m pytest test/test_style_names.py -q -n 6 -p no:cacheprovider -rf > "$S/36-03.log" 2>&1` on the still unmodified renderer and append its FAILED lines (one per node, first assertion text) to `<scratch>/36-P1.14b-failure.txt` under a heading `fixture-driven (36-03)`.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED.*TestAgainstStata::test_each_scheme' "$S/36-03.log"` prints 26; `grep -E '^FAILED.*TestTheFixture' "$S/36-03.log"` prints nothing.]]></verify>
  <done>The fixture-driven tests existed and failed on the unmodified base for every scheme, and their failures were appended to the failure text.</done>
</task>

<task type="auto" id="36-04">
  <name>Teach the scheme extractor the style table</name>
  <files>scripts/extract_scheme_truth.py, test/test_scheme_fidelity.py</files>
  <action><![CDATA[
    Make TR-36.14 in scripts/extract_scheme_truth.py: the two constants after `SCHEMES`, `style_table(r)`, `style_known(r)` and `named_style_directives(r, provenance, sources)` (a scheme.class walk, E8: p-keys through `p<num><stub>`, `p<stub>`, `p<num>`, `p`, the key; other keys exact; `""` the class default; a hop value read with the same walk), the `extract()` key `named_style_directives` with its sources and provenance (kind `transcribed`, the declaring file and line), `main()`'s `_meta.style_files` and `_meta.style_known`, and the last `expected_directives` group with the exact heading text of TR-36.14, sorted, skipping keys an earlier group carries. Do not change `linked()`. Add the four `test_scheme_fidelity.py` tests of "In test/test_scheme_fidelity.py (36-04)". Do not regenerate yet.
  ]]></action>
  <verify><![CDATA[`python3 -c "import sys;sys.path.insert(0,'scripts');import extract_scheme_truth as x;r=x.SchemeResolver(x.DEFAULT_STATA_BASE);r.load('s2color');p,s={},{};d=x.named_style_directives(r,p,s);print(d['color refline'],len(d)>=100,len(x.style_table(r)['linestyle']))"` prints `#2d6d66 True 75` (s2color's `color refline emerald`, scheme-s2color.scheme:402, spelled as the files spell colours; 75 = 76 files less S32's p#); `python3 -m pytest test/test_scheme_fidelity.py -q -n0 -p no:cacheprovider -k walk_follows_scheme_class` passes.]]></verify>
  <done>The extractor transcribed the style table and the keys each scheme declares along Stata's chain, with provenance, without changing any existing group.</done>
</task>

<task type="auto" id="36-05">
  <name>Regenerate the shipped schemes and fixture</name>
  <files>dash-*.scheme, test/fixtures/scheme_truth.json</files>
  <action><![CDATA[
    Save `git -C $WT show HEAD:test/fixtures/scheme_truth.json > "$S/scheme_truth.before.json"`. Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json` from $WT; it updates all 26 `dash-<name>.scheme` and the fixture. Run it a second time with `> "$S/36-regen2.log" 2>&1` (the extractor writes `up to date` to stderr). Check with a short python script that every pre-existing scheme record and `_meta` key of the before file is unchanged except `generated_utc`, `_meta.style_files`/`_meta.style_known`/`_meta.style_hops` (new) and each scheme's new `named_style_directives` with its `sources`/`provenance` entries; and with `git -C $WT diff --stat -- 'dash-*.scheme'` that only additions occur (no `-` line other than a rewritten provenance block). Never edit a generated file by hand (R7); a mismatch is reported. Run `python3 -m pytest test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k TestTheShippedFiles -rf > "$S/36-05-shipped.log" 2>&1` and list each red node in `$S/36-flips.txt` for 36-16 (E12 expects the four TestTheShippedFiles rows; any other red node is reported).
  ]]></action>
  <verify><![CDATA[`grep -c 'up to date' "$S/36-regen2.log"` prints 26; `python3 -m pytest test/test_scheme_fidelity.py -q -n 6 -p no:cacheprovider` passes; `grep -c '^color refline' dash-s2color.scheme` prints 1.]]></verify>
  <done>All 26 shipped schemes and scheme_truth.json carried the keys the named styles read, every earlier directive and record was unchanged, and a second run changed nothing.</done>
</task>

<task type="auto" id="36-06">
  <name>Add the style table to SchemeParser</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Directly after `_FALLBACK_PROPS`'s closing brace, add `_STYLE_TABLE`, `_STYLE_KNOWN`, `_STYLE_DEFAULT` and `_STYLE_CLASS` per TR-36.1 to TR-36.4, written from the regenerated fixture's `_meta.style_files`/`_meta.style_known` by a one-off print into `$S/table.py` that you then paste (never generated at import time). Each constant has a comment citing E7, E9.3 and the security rule (names are matched, never used as paths or keys). Run `python3 -m pytest test/test_style_names.py -q -n0 -p no:cacheprovider -k TestTheStyleTable`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_style_names.py -q -n0 -p no:cacheprovider -k TestTheStyleTable` passes; `python3 -c "import dash_render as d;print(len(d.SchemeParser._STYLE_KNOWN['linestyle']),d.SchemeParser._STYLE_DEFAULT['areastyle'])"` prints `76 background`.]]></verify>
  <done>SchemeParser carried 19.5's style table, the known names and the measured defaults, equal to the extractor's transcription.</done>
</task>

<task type="auto" id="36-07">
  <name>Resolve the other names in style_bundle</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Add `SchemeParser._style_kind`, `_style_leaf`, `_style_resolve`, `_style_shape` and `_style_note` directly after S32's `style_bundle`, exactly as TR-36.5 to TR-36.10 define them, and extend `style_bundle` per TR-36.9 without changing its p# body: new cls tokens through `_STYLE_CLASS`, the kinds, the lazily created memo on `self.__dict__`, copies returned. No nested defs, no new module-level names, nothing in `__init__` or `_init_properties`. Each docstring cites E7, E8 and E9 and the register rows P1.14.1/P1.14.3. Run `python3 -m pytest test/test_style_names.py -q -n 6 -p no:cacheprovider -k "TheTableNames or SeriesForms or MarkerForms or AreaForms or None or Unknown or TheShapes or Adversarial or AgainstStata or DefaultAttributes"`.
  ]]></action>
  <verify><![CDATA[That pytest run passes; `python3 -c "import dash_render as d;s=d.SchemeParser('s2color');b=s.style_bundle('line','refline');print(b['line'],s.style_bundle('line','p3')==d.SchemeParser('s2color').style_bundle('series.line','p3'))"` prints `#2d6d66 True`.]]></verify>
  <done>style_bundle drew every table name through Stata's chain, the default attributes for any other name, and S32's p# bundles unchanged.</done>
</task>

<task type="auto" id="36-08">
  <name>Extend the fallback properties</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Append TR-36.11's block to `_FALLBACK_PROPS`, after S24's histogram keys, holding every directive of dash-s2color.scheme's `Named styles (WP-30 S36)` group with the same value (generate the lines with a one-off script reading that group into `$S/fallback.txt`, then paste). Run `python3 -m pytest test/test_style_names.py test/test_scheme_fallback_provenance.py -q -n0 -p no:cacheprovider -k "Fallback"`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_style_names.py test/test_scheme_fallback_provenance.py -q -n0 -p no:cacheprovider -k Fallback` passes.]]></verify>
  <done>The fallback scheme drew every named style exactly as the shipped s2color does.</done>
</task>

<task type="auto" id="36-09">
  <name>Route pstyle and the ci fits through series styles</name>
  <files>dash_render.py, test/test_named_styles.py, test/test_ci_band_style.py</files>
  <action><![CDATA[
    Report E13's HIGH ratings for `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle` before editing (already approved at 12.0). Make TR-36.12 in GlyphMapper: change only the `pstyle` and `p` rows of `_STYLE_FACTORS` to the `series.*` classes; delete `_style_unresolved`, `_STYLE_UNREAD_NOTE`, the plan's `unresolved` list and `_style_restyle`'s loop over it; add `_STYLE_NOTE_ONLY` and `_style_plan`'s note-only calls before its early return (TR-36.12, D-36i). Make TR-36.13 in `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle`. Flip in place, each with a comment `# Flipped (WP-30 P1.14b): <old> was wrong because <why>` and a line in `$S/36-flips.txt`: S32's `TestOtherNames::test_noted_once_and_drawn_as_the_layer`, `::test_unused_option_is_silent`, `TestAdversarial::test_hostile_names_are_noted_shortened_and_inert` and every test 36-01 listed that names the retired path, and `test_ci_band_style.py::TestAdversarial::test_a_hostile_pstyle_is_named_once_and_shortened`'s filter to `"named style"`. Run `python3 -m pytest test/test_named_styles.py test/test_ci_band_style.py test/test_style_names.py -q -n 6 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That pytest run passes; `grep -nE '_style_unresolved|_STYLE_UNREAD_NOTE|"ci-pstyle"' dash_render.py` prints nothing.]]></verify>
  <done>pstyle and p() resolved each role through its seriesstyle, the ci fits drew the table's series styles, the interim note was retired, and the pinned tests were flipped with reasons.</done>
</task>

<task type="auto" id="36-10">
  <name>Declare dstyle, dlstyle and bmlinestyle</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Make TR-36.16. Before editing, re-read S32's declarations, pending lines, sreturn lines, JSON key list and `_dash_p_drops` at the base and place each new item right after S32's last named-style item in the same form; `grep -n 'BMLinestyle\|DSTyle\|DLstyle' dash.ado` must print nothing first (if S32 already declared one, skip it and say so in `$S/36-flips.txt`). Append ` dstyle dlstyle bmlinestyle` to `_dash_stylelist_keys()`'s string in dash_parse.mata. Run the parser script through the driver (36-12 runs the abbreviation script): `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_parser.cscript > "$S/run_test_parser.do"` and `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_parser.do"`.
  ]]></action>
  <verify><![CDATA[`grep -cE 'DSTyle\(|DLstyle\(|BMLinestyle\(' dash.ado` prints 3; `grep -c 'sreturn local dstyle\|sreturn local dlstyle\|sreturn local bmlinestyle' dash.ado` prints 3; `$S/run_test_parser.log` holds no `FAIL` and ends with its ALL-CHECKS line.]]></verify>
  <done>dash accepted dstyle(), dlstyle() and bmlinestyle() with twoway's minimums, kept them per y in the spec, dropped them under p(), and named them as not drawn.</done>
</task>

<task type="auto" id="36-11">
  <name>Flip the pending and declared pins</name>
  <files>test/test_unsupported_report_is_true.py</files>
  <action><![CDATA[
    Make TR-36.19: measure `len(_plot_pending())` and `len(_declared_plot())` at the base, set the pins at :240 and :607 to base + 3 with the R10 comment, and add the three `PLOT_VALUES` rows (match the variables of the file's existing pcbarrow or pc row for `bmlinestyle`). Add one line per pin to `$S/36-flips.txt`. Run the file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_unsupported_report_is_true.py -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>The pending and declared counts and the test values named the three new options, each with its reason.</done>
</task>

<task type="auto" id="36-12">
  <name>Flip the cscript pins and add OS-07</name>
  <files>test/test_help_claims_8.cscript, test/test_abbreviations.cscript, test/test_ci_band_options.cscript</files>
  <action><![CDATA[
    Run `grep -E '(^|[^A-Za-z0-9_])OS-[0-9]' test/*.cscript test/*.py test/*.do` and confirm nothing but S36's own new lines print. In test_help_claims_8.cscript HC8-07 add `dstyle(p3) dlstyle(p3) bmlinestyle(p3)` to `p_opts` and `dstyle dlstyle bmlinestyle` to `p_names` in sorted place. In test_abbreviations.cscript append OS-07 ("Stata truth") as one contiguous run after the last case, reading `dash_json_<g>` by value. In test_ci_band_options.cscript CB-04, if it matches S32's interim text, change the expected note to `named style red not found in class linestyle, default attributes used` and rewrite its PASS text. Add a line per flip to `$S/36-flips.txt`. Run each script through the driver (index "The cscript driver").
  ]]></action>
  <verify><![CDATA[`$S/run_test_help_claims_8.log`, `$S/run_test_abbreviations.log` and `$S/run_test_ci_band_options.log` show HC8-07, OS-07 and CB-04 PASS and no FAIL.]]></verify>
  <done>The certification scripts named the three new options, checked their abbreviations against twoway's, and expected twoway's words for an unknown line style.</done>
</task>

<task type="auto" id="36-13">
  <name>Register the new SchemeParser methods</name>
  <files>test/function_test_map.py</files>
  <action><![CDATA[
    Under `# WP-30 S36 (P1.14b): Other style names (P1.14 part b)` add TR-36.18's five keys in alphabetical order, each naming a `test/test_style_names.py` node that fails when that method's body is skipped (check each with a scratch copy: replace the body with `return None` or `pass`, run the node, restore). Delete the `GlyphMapper._style_unresolved` key under S32's anchor. Run the registry tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n 6 -p no:cacheprovider` passes.]]></verify>
  <done>Every new method named a test that fails without it, the retired method left the map, and the served-name guards stayed green.</done>
</task>

<task type="auto" id="36-14">
  <name>Add parity cases and check both modes</name>
  <files>test/test_mode_parity.py</files>
  <action><![CDATA[
    Append the four CORPUS cases of "Parity and flips" at the end of `CORPUS`, and `s36_astyle_bogus`'s `_MUST_WARN` entry (needle `named style bogus not found in class areastyle`), never editing `ALLOWED` (R8). Run the parity file and the both-mode and after-move classes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_mode_parity.py -q -n 6 -p no:cacheprovider` passes; `python3 -m pytest test/test_style_names.py -q -n 6 -p no:cacheprovider -k "saved or served or AfterAFilterMove"` passes.]]></verify>
  <done>The saved page and the served app drew the four named-style cases alike, before and after a filter move.</done>
</task>

<task type="auto" id="36-15">
  <name>Fill the S36 truth block</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Write `_s36_page`, `_s36_app` and `_s36_case` directly above S36's header, outside every gate, each declaring `version 19`, copying S32's `_s32_*` pattern. Write OS-01 to OS-06 of "Stata truth" between S36's start and end display lines through `_w30_expect`/`_w30_done`. Files go only under `` `w30_work' `` and are erased before the end line; python helpers pass values through `Macro.setLocal`, never inline user text into Python source, never use shell=True. Run `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_truth.do"` and `WP30_ONLY=S36 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_truth.do"`.
  ]]></action>
  <verify><![CDATA[`grep -cE '^OS-0[1-6] PASS' "$S/run_truth.log"` prints 6; `grep -c 'FAIL' "$S/run_truth.log"` prints 0; the log ends with `ALL CHECKS PASSED`; `python3 -m pytest test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>Six Stata-truth cases compared dash's drawing and notes with twoway's on the same commands, in both modes and after a move, and passed.</done>
</task>

<task type="auto" id="36-16">
  <name>Document the style names in the help and flip the shipped-file pins</name>
  <files>dash.sthlp, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Make TR-36.21: insert the `{phang2}{ul:Named styles.}` paragraph after the `{ul:Series.}` paragraph of "Stata scheme support" (locate by text); update `{ul:What the shipped files are.}` as TR-36.21 says; add the `{phang2}{ul:Dot and marker back-line styles.}` paragraph in "Unsupported Stata twoway options", after the paragraph S32 left for named styles. Quote the notes in the `(note:  dash: …)` form. Name no tool or vendor.
    Flip in place the four `TestTheShippedFiles` rows of E12 in test/test_help_claims_8.py, each with `# Flipped (WP-30 P1.14b): <old> was wrong because <why>` and a line in `$S/36-flips.txt`: measure the min and max directive counts over the 26 regenerated files with the test's own counter, write the bounds rounded outward to ten with `# <old> -> <new>: P1.14b named-style keys` (R10) and the same numbers in the help; add `color pieline` and `color fpspacer` to `test_every_colour_is_rrggbb`'s `none` exception (any scheme); assert `"color refline" in keys` in `..._in_dash` and rewrite its docstring; restrict `test_no_directive_for_what_dash_does_not_draw`'s pattern to directives outside the `Named styles (WP-30 S36)` group (read the group's keys from each scheme's `named_style_directives` in test/fixtures/scheme_truth.json, never a hand list) and assert the group's matches are exactly E10's 26 line-style keys or a subset per scheme. Run the help tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py -q -n 6 -p no:cacheprovider` passes; `grep -c 'named style .* not found in class' dash.sthlp` prints at least 1; `grep -c 'Flipped (WP-30 P1.14b)' test/test_help_claims_8.py` prints at least 4.]]></verify>
  <done>The help listed the style names each option takes, the default attributes and both notes, the shipped files' new bounds and carried keys, and named the three kept-but-undrawn options; the four shipped-file pins were flipped with reasons.</done>
</task>

<task type="auto" id="36-17">
  <name>Close the entry and commit P1.14b</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Close the BUGS.md entry titled `Style names other than p1-p15, such as ci, histogram, refline and p1bar, are not read by pstyle() and the other style options` in place (`- [x]`) with the Resolution of Notes. Delete only its `"P1.14b"` line from `WP30_OPEN` (R5). Replace `<!-- WP-30 P1.14b -->` in place with the CHANGELOG line of Notes (R4). Run the changed test files; run every cscript this section touched through the driver; run `git -C $WT merge --no-edit main` (expect `Already up to date.`); run one full suite through the queue, `<scratch>/full_suite_queue.sh $WT <scratch>/36-full-1.log`, in the background and wait for its `exit=` line (E1; E6 for flaky tests). Check `git -C $WT diff --cached --name-only` holds only this section's files (G6), write the message per the commit boundary to `$S/msg.txt`, run G7, confirm the branch, and `git commit -F "$S/msg.txt"`; run G7 on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`grep -c '^exit=0' <scratch>/36-full-1.log` prints 1 and the log shows 0 failed; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes; `grep -c 'WP-30 P1.14b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.14b": "' test/test_tracking_documents.py` prints 0; `git -C $WT log -1 --format=%s` ends `(WP-30 P1.14b)`; `git -C $WT log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The P1.14b entry, its key and its marker were closed in place, the full suite ran green once, and the one commit was made on wp30-s36.</done>
</task>

## Section completion criteria

- One commit on `wp30-s36`, ending `(WP-30 P1.14b)`, holding:
  - `dash_render.py`, `dash.ado`, `dash_parse.mata` and `dash.sthlp`;
  - `scripts/extract_scheme_truth.py` and `scripts/extract_style_name_truth.do`;
  - the 26 `dash-*.scheme` files, `test/fixtures/scheme_truth.json` and `test/fixtures/style_name_truth.json`;
  - `test/test_style_names.py`, `test/test_scheme_fidelity.py`, `test/test_named_styles.py`, `test/test_ci_band_style.py`, `test/test_unsupported_report_is_true.py`, `test/test_help_claims_8.py`, `test/test_mode_parity.py` and `test/function_test_map.py`;
  - the four cscripts (`test_wp30_truth`, `test_help_claims_8`, `test_abbreviations`, `test_ci_band_options`);
  - `BUGS.md`, `CHANGELOG.md` and `test/test_tracking_documents.py`.
- AC-36.1 to AC-36.9 hold. Every 36-01 and 36-03 test passes, and every E12 flip carries its reason.
- `style_name_truth.json` is new, stamped and staged with `git add -f`. `scheme_truth.json` and the 26 files are regenerated, never hand-edited, and a second run is a no-op.
- No copy-list change, no `_make_figure_body`/`_generate_app_source` edit, and nothing of S34's or S35's touched (G6, `detect-changes` at landing).

## Notes

**Traps for the executor.**
- **The served rebuild skips `__init__`** (E1). Create the memo lazily on `self.__dict__`, and never in `__init__`. A served test catches a miss, but only when a named style is present.
- **Never format user text into a key.** `_style_leaf` builds keys only from `_STYLE_TABLE` strings, with `#` replaced by the validated number. The `_props` spy test enforces this.
- **Two different chains.** The existing `linked()` falls back to the class default and S36's walk does not (E8). Do not route S36's walk through `linked()`, and do not "fix" `linked()`: its groups are other sections' records.
- **`.rgb` has runs of blanks** (`26    133    255`, q1 in E9). The extractor collapses them before hex conversion.
- **A `none` colour reads `0 0 0` from `.rgb`.** Use the `.stylename` reads (`*_none`) to decide "not drawn" (E9.3).
- **Unknown names in a 25-layer call** print notes for every layer. The U grid runs one name per call, so notes stay attributable.
- **Regeneration lands last** in batch 12 (A152). A conflict in a generated file means re-running the extractor on the merged tree, never a hand merge (R7).
- **The single-y digest** (`_SINGLE_Y_BASELINE_SHA256`) should not move: no corpus case names a style, and the empty plan is byte-identical (S32 TR-32.16a). If it moves, stop and report.

**Merge rules touched.**
- R1: the truth block, helpers above S36's header, OS-07 appended once.
- R2: no copy-list change; the registries run after landing.
- R3: two help paragraphs, scheme support (S34 edits another) and Unsupported.
- R4: one marker.
- R5: one entry and one key.
- R6: no new option key shared with S34 or S35, and `version 19` kept.
- R7: two fixtures, one new extractor, a regeneration.
- R8: four CORPUS cases and one `_MUST_WARN` entry.
- R9: E12's flips.
- R10: :240 and :607.
- R12: none of the one-editor symbols.

**For the orchestrator (not the maintainer).**
- D-36b, D-36d and D-36e edit S32's GlyphMapper code beyond the manifest note "edits only style_bundle, its table, the extractor and generated files":
  - the `pstyle`/`p` rows of `_STYLE_FACTORS`;
  - the retirement S32 itself offers;
  - `_style_plan`'s note-only calls for `dstyle`/`dlstyle`/`bmlinestyle` (D-36i, measured E9.7);
  - `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle`.

  The first is unavoidable, because a seriesstyle's roles name different styles (E7). No batch-12 partner edits any of them. Add S36's three HIGH ci methods to index 12.0's expected list.
- S36 takes S32's Q1 (`bmlinestyle()`), so the closeout need not file it.
- **Cross-file (index.md):**
  - R10's `test_unsupported_report_is_true.py:240` row should list S36 (12), which moves it +3.
  - R3's "Unsupported Stata twoway options" row should list S36 (12), for its `{ul:Dot and marker back-line styles.}` paragraph.
  - R10's movers of `test_help_claims_8.py::TestTheShippedFiles::test_the_directive_count_is_what_the_help_says` (S24's rename) should include S36 (12), which also flips three sibling pins (E12).
  - 12.0's expected HIGH list should add `_ci_pstyle`, `_ci_band_style` and `_ci_line_restyle`.
- **Partners' descriptions:** S34 ("Can run with") and S35 (Boundaries) describe S36 as editing only `style_bundle` and its table. S36 also edits `_STYLE_FACTORS`, `_style_plan`, `_style_restyle` (retirement), the three ci methods, dash.ado's plot declarations, sreturn and JSON key list, Mata `_dash_stylelist_keys`, and `TestTheShippedFiles`. None of these is a partner's symbol, so they collide nowhere. The descriptions are incomplete, not wrong in effect.

**BUGS.md Resolution (36-17):**

`- Resolution: Fixed <ddmonyyyy> (WP-30, P1.14b). Stata's other style names are drawn as twoway draws them: every name of Stata's 76 line styles (refline, grid, major_grid, minor_grid, foreground, background, xyline, none, p#line, p#bar and the rest), and for the series, marker and area classes ci, ci2, histogram, foreground, background, none and the p#line, p#bar, p#area, p#box, p#dot and p#arrow forms. SchemeParser.style_bundle follows a table transcribed from Stata 19.5's style files through the scheme's own keys along Stata's p#stub chain (_STYLE_TABLE, _style_resolve, _style_leaf), so a user scheme that includes a shipped one reaches them. scripts/extract_scheme_truth.py and the 26 shipped files carry the keys they read, and _FALLBACK_PROPS carries s2color's. pstyle() and p() resolve each role through its series style (GlyphMapper._STYLE_FACTORS), pstyle(ci) and ci2 work on every type, and the ci fits draw the table's series styles (_ci_pstyle, _ci_band_style, _ci_line_restyle). A name Stata does not know draws twoway's default attributes (series and marker p1, line foreground, area background) with twoway's note, and a Stata name outside the table draws the same defaults with a note saying it is not drawn. dstyle(), dlstyle() and bmlinestyle() are accepted with twoway's abbreviations, kept per y and named as not drawn. The saved page and the served app draw the same, before and after a filter move. Pinned by test/test_style_names.py::TestTheTableNames::test_s2color_lstyle_refline, test/test_style_names.py::TestPstyleCi::test_stcolor_scatter, test/test_style_names.py::TestUnknown::test_astyle_bogus_is_the_background, test/test_style_names.py::TestTheNote::test_twoways_words_once, test/test_style_names.py::TestAgainstStata::test_each_scheme, test/test_style_names.py::TestDefaultAttributes::test_each_scheme, test/test_style_names.py::TestCiTypes::test_each_c_record, test/test_style_names.py::TestAfterAFilterMove::test_served_style_survives_a_move, test/test_style_names.py::TestAdversarial::test_hostile_names_are_inert_and_noted, test/test_wp30_truth.cscript OS-01, test/test_abbreviations.cscript OS-07; fixture test/fixtures/style_name_truth.json; fixture test/fixtures/scheme_truth.json. Residual, deferred (WP-30): drawing dstyle() and dlstyle() is P2.9's and bmlinestyle() P2.8's; the label role of a series style and the outline of a named style on area and rarea are P2.12's; 57 Stata names outside the table (fpall, sunflower, plotregion and others) and a resolver for all 161 style files are filed by the closeout.`

**CHANGELOG line (36-17, replaces `<!-- WP-30 P1.14b -->` in "Results that change"):**

`- The style options take Stata's other style names and draw them as twoway does: every one of Stata's 76 line styles (lstyle(refline), lstyle(grid), lstyle(xyline), lstyle(none) …), and ci, ci2, histogram, foreground, background, none and the p#line, p#bar, p#area, p#box, p#dot and p#arrow series forms. line mpg weight, lstyle(refline) under s2color was drawn in p1's #1a476f and is now #2d6d66, and pstyle(ci) now works on any plot. A name Stata does not know now draws twoway's default attributes with twoway's note, where the layer kept its own style: area mpg weight, astyle(bogus) is filled in the scheme's background colour (#eaf2f3 under s2color) and lstyle(bogus) is drawn as a thin black line. dstyle(), dlstyle() and bmlinestyle() are accepted and kept, and still named as not drawn (WP-30, P1.14b)`

**Notes for the closeout (A145; S58 writes them).**
- **GAPS2.md B11** (also D6): closed only when P1.14a and P1.14b are both closed (index S58.2: B11 is carried by P1.14a and P1.14b). Its Tracked line names both commits, and `(WP-30, GAPS2-B11)` is appended to both Resolutions. The manifest's B11-c is this section's (the non-p names). The heading's other words (`mlpattern`, `colorlist`, `coloruseplegend`) belong to no P1.14 part; S58 checks them against the entries that carry them and leaves open what none closes.
- **P1.14's shared ids, recorded closed when P1.14a and P1.14b are both closed:** REM-§2-S09-lstyle, REM-§2-S09-mstyle, REM-§2-S09-areastyle, REM-S09-73-namedstyles, REM-05-04-S09-g, GAPS2-B11-a/b/c, GAPS2-D6, AUDIT-29 and AUDIT-30 (research p1-14 line 3).
- **REMAINING.md:** `dstyle`, `dlstyle` and `bmlinestyle` in the S09 style lists (:133-140, :149, :448-452, :818-821, :892-893) become "accepted, kept, named (P2.9/P2.8)", and the other-name words are drawn.
- **TWOWAY_COVERAGE_AUDIT.md (AUDIT-30):**
  - the rows at :112, :114 and :116 lose "named style coverage remains incomplete", keeping the D-36c names;
  - the ignored list at :169 keeps `dstyle`, `dlstyle` and `bmlinestyle` only if the audit lists them.
- **DROPIN-REMAINING.md P1.14:** closed by P1.14a and P1.14b.
- **test/fixtures/rejected_options.json:** the pstyle/lstyle/mstyle/astyle/bstyle rows are honoured for every table name. The dstyle/dlstyle/bmlinestyle rows (if present) keep "named".
- **Residuals to file:**
  - P2.9 (drawing `dstyle()`/`dlstyle()`);
  - P2.8 (`bmlinestyle()` and arrowheads);
  - P2.12 (the label role of a series style, and outlines on area/rarea);
  - a new P2 row for D-36c's 57 Stata-known names and the general 161-file resolver (manifest item-14 residual), citing E7's lists;
  - any label-colour difference the extractor's `label_color` field shows under `pstyle(ci)`/`histogram`.

**Open question for the maintainer.**
1. D-36c: the 57 Stata-known names outside the curated table (seriesstyle `fpall` …, markerstyle `sunflower` …, areastyle `plotregion`, `outline`, `legend` …) are drawn in their class's default attributes and named as not drawn. The table-driven resolver could carry them now, at about 30-60 more keys per shipped file. That is decided against here because the manifest keeps "the general 161-file resolver" as a residual. Ratify, or strike to include them.

**Line numbers.** Every number above is at `c96facd` unless marked "at the base". Sections 01-35 move them, so each task locates code by the quoted text and by function name.
