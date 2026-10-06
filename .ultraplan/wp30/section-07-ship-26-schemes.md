# Section 07: Ship the six StataCorp schemes (P1.25 part a)

> Part of: WP-30 · Items: P1.25 part a (entry P1.25a) · Risk: green · Batch: 3 · Depends on: 01 · Blocks: 15, 24, 34 · Tasks: 10, 1 commit · Case prefix: SX

## Review amendments

- Fixed (major): a count pin the red list missed. The six `{synopt}` rows move `test_help_conformance.py::TestTheParsersFoundSomething::test_the_entry_parser_cuts_the_help_into_entries` from 339 to 345 definition entries (measured on a scratch copy of dash.sthlp with six rows added; `_help_options` stays 149). 07-09 now flips it with its R10 comment, and 07-10 stages the file. It is an R10 combined pin: S08 and S09 edit help in the same batch.
- Fixed (major): the SX block wrote files outside `` `w30_work' `` (TR-01.10 item 4). Every page and SVG now goes under `` `w30_work' ``. SX-05 and SX-08 still need their child scheme files in the working directory, because both twoway's `findfile` and dash's pre-S34 lookup read only there. Each such file is checked absent before it is written (rule 1: never overwrite or trust a planted file) and erased in the same case, pass or fail.
- Fixed (minor): logs are captured with a named `log using …, text replace name(sx…)`, as test_wp29_truth.cscript does, so they cannot collide with the driver's log.
- Checked: the anchors (`_dash_shipped_schemes` dash.ado:1967-1971, `_BUILTIN_NAMES` dash_render.py:5704-5715, extractor `SCHEMES` :1957-1963, `main` :1964 with `--schemes` at :1971 and the unchecked join at :2215), the eight count pins and the `#include stcolor_meta` test (test_help_claims_8.py:978-998) at HEAD. All match.
- Checked: batch 3 shares no function. S08 and S09 name S07's symbols as S07's. `_shipped_base` (docstring only) is not edited by either.
- Rejected: "07-06 names more than three files". The six `dash-*.scheme` files and the fixture are the output of one extractor run, never hand-edited (R7); the task edits one source file.
- (cross-file pass) 07-10 verify: added the key-deletion check `grep -c '^    "P1.25a": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:146 (P1.25) reads: "Six StataCorp schemes, including meta and stcolor_mv, are refused r(198) where `twoway` draws them. An inherited `c(scheme)` that Stata found is drawn as s2color." The six are **meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv**. Stata's BASE/s holds 26 `scheme-*.scheme` files and dash ships 20. The extractor says so on purpose (scripts/extract_scheme_truth.py:1952-1954: "The internal ones ... are deliberately not translated").

Measured at `c96facd` on StataNow 19.5 (probe `p1.do`, quoted under Evidence):
- `twoway scatter mpg weight, yline(20) scheme(X)` gives rc 0 for each of the six.
- `dash scatter mpg weight, scheme(X)` gives r(198) for each, with `dash: scheme() must be a shipped scheme, a theme, or a .scheme file in the working directory (got: meta)`.
- After `set scheme stcolor_meta`, an unschemed dash graph is drawn as s2color (`border_fill_color #eaf2f3`) with the warning `dash: 'stcolor_meta' is not a known theme or scheme; it was inherited from the session (c(scheme)) ...`. This happens in both modes, by `scheme()` and by `session_scheme`.
- A user file's `#include stcolor_meta` is read as `#include s2color` with `(note: scheme stcolor_meta not found, using s2color)`.

**After this section** dash ships 26 translations. Each of the six resolves by name, as the inherited `c(scheme)` and through `#include`, in the saved page and the served app, before and after a filter move. Each is drawn as twoway draws it, measured on every surface dash already draws for the twenty:
- background and palette;
- stcolor_meta's and stgcolor_meta's solid `#c10534` `yline()`; stcolor_mv's and stgcolor_mv's solid black one;
- each scheme's graph proportions (stgcolor_meta 3.987 x 2.392);
- meta's 8pt tick labels and its legend at 4 o'clock;
- the ci band;
- the child-scheme tables of the S3 batch.

stcoloralias is drawn as stcolor. Its only directive of its own, `zyx2rule colorvar`, is not read, and twoway draws a `colorvar()` scatter identically under both (measured). The help says so.

**Why one section, and why first.** This is the six-scheme half of P1.25 (A138; register P1.25.2, ruling A79). It closes the six-refused sub-claim, which has no source id of its own, and the part of GAPS2-X5-c where the inherited `c(scheme)` is one of the six. The lookup along the ado-path (sub-claims a, c for every other scheme, d, e, f and g) is S34's under M7.

**Decisions applied.**
- M1: each of the six is drawn with its own look, as twoway draws it.
- M6: the six, by name or inherited, print nothing, as twoway prints nothing.
- M5: no new refusal; a refusal twoway does not make is removed. That is a capability, so its CHANGELOG line goes under `### New` (A147: S07's `WP30_LISTS` row is New).
- M7: S34's.
- Register P1.25.2 (A79): ship translations and measure the six in Stata for the twenty-scheme tables.

S07 is the first scheme regenerator (A152). Every later regeneration covers 26 files: S15, S21, S24, S30, S33, S36, S47, S50, S53 and S56. The scheme count is one combined pin (R10: `EXPECTED_SCHEMES`, `_BUILTIN_NAMES`, `_dash_shipped_schemes`, dash.pkg, the help's "twenty") moved once, here.

**Test order and commit rule (rule 7, D1).** There is one cycle and one commit, `(WP-30 P1.25a)`.
- **07-01** writes the new regression module and runs it against the unmodified tree. It saves `<scratch>/07-P1.25a-failure.txt` and never commits.
- **07-02 to 07-05** flip the pinned counts and tables in place, append the parity guards and write the `SX` truth block. Each runs red-first where the test asserts new behaviour, and appends its red lines to the failure file.
- **07-06 and 07-07** make the fix.
- **07-08** certifies it, and **07-09** writes the help.
- **07-10** closes the entry and makes the one commit after one full run.

No test-only commit exists, and no commit is red.

## Risk: [green] — data-only additions through a verified generator, plus one list grown in five places that one test already holds equal

**Why green.**
- No drawing code changes. The renderer already resolves any name in `_BUILTIN_NAMES` to `dash-<name>.scheme` (`SchemeParser._resolve_path`, dash_render.py:6069-6186). dash.ado's gate already accepts any name in `_dash_schemes`.
- The extractor writes the six files with its existing writer. A dry run at `c96facd` created all six with `unresolvable: []` and left all twenty existing files "up to date".
- The extractor is a Python file reader of Stata's own scheme and style files. It never runs Stata.

**Risk factors.**
1. Count pins in tests the research did not list. Mitigation: the scheme test files were run on a simulated tree (Evidence, "Measured red list"). 07-03 to 07-05 flip every pin found, and the full run in 07-10 is the backstop.
2. A regeneration that changes an existing record. Mitigation: 07-06 compares every pre-existing scheme record and every existing `dash-*.scheme` byte for byte against `git show HEAD:...`. Only `_meta.generated_utc` and `_meta.provenance` may differ (measured: the provenance sentence's stale "schemes/<name>.scheme" becomes "dash-<name>.scheme").
3. meta is the first shipped scheme with `yesno draw_minor_hgrid/draw_minor_vgrid yes`.
   - Today's `SchemeParser.apply_to_figure` (dash_render.py:7401-7414) then colours Bokeh's minor grid (#505050, 0.2 px, four lines per major interval).
   - twoway draws a minor grid only at minor ticks. It draws none by default (`p1_meta.svg` has no #505050 line), and dash's `xmtick()`/`ymtick()` are pending (dash.ado:809-814).
   - Mitigation: a guard test pins today's drawing and names its owner. S15 (P1.2a, "no minor ticks unless asked", BR-30.2) removes it, and a "For S15" note says how. S07 does not edit `apply_to_figure` (S15's, batch 5).
4. Line widths of the six (meta's `linewidth p thin`) follow dash's existing ladder, as for the twenty. They are S13's (P1.12b) and are not certified here.

## Dependencies

- **Depends on: 01.** S01 provides:
  - the open BUGS.md entry `WP30_OPEN["P1.25a"]`;
  - the marker `<!-- WP-30 P1.25a -->` at the end of CHANGELOG.md `### New`;
  - the stub block `* ==== S07 P1.25a: … ====` in `test/test_wp30_truth.cscript`, with its `WP30_ONLY` gate and the `_w30_expect`/`_w30_done` tally helpers (WP-29's `_w29_` form; use whatever names S01's scaffold defines).
  - It also depends on S03 (batch 1; every program reads `version 19`) and S06 (batch 2; notes print as `(note: …)`, and the cscript needles count note text). Neither is a declared dependency: both landed earlier.
- **Blocks: 15, 24, 34.**
  - S15 and S24 regenerate 26 files and extend the extractor on top of S07's `SCHEMES`.
  - S34 walks the ado-path with the shipped names first (P1.25.3), so the six must be shipped names.
- **Parallel batch: 3**, merge order S07, S08, S09. S07 lands first (A152: no partner touches the extractor, a scheme file or `scheme_truth.json`).
- **Can run with:** S08 and S09.
  - S08 edits `OptionTranslator` size helpers, the four appliers, `_textbox_size`, `_mlabel_gap_px`, `_dash_validate_value`'s size rules and CHANGELOG.md:522.
  - S09 edits `DashRenderer._build_sources_and_figures` and adds `_dash_finish_graph_text`.
  - S07 edits `_dash_shipped_schemes` (a different program from `_dash_validate_value`), the `_BUILTIN_NAMES` frozenset, `SCHEMES` and `main` in the extractor, and data files.
  - The only shared files are dash.ado (distinct programs), dash_render.py (distinct hunks), CHANGELOG.md (distinct markers), BUGS.md (distinct entries) and `test_tracking_documents.py` (distinct `WP30_OPEN` lines). R4 and R5 apply.
  - S08 and S09 move the single-y page digest (R10). S07 does not: the default scheme's page is unchanged.

## Evidence

Anchors are at `c96facd` (dash_render.py 37,689 lines; dash.ado 8,487). Batches 0-2 land before S07's base, so line numbers may drift by tens of lines. The symbols are authoritative.

### The one list, in five places

`dash.ado:1967-1971`, `_dash_shipped_schemes`, between the sentinels `// BEGIN shipped schemes (WP-17)` / `// END …` that `test_scheme_resolution.py::_ado_block` reads:

```stata
1967 program define _dash_shipped_schemes
1968     version 16.0
1969     c_local _dash_schemes "economist s1color s1manual s1mono s1rcolor s2color s2color8 s2gcolor s2gmanual s2manual s2mono sj stcolor stcolor_alt stgcolor stgcolor_alt stmono1 stmono2 stsj sttrans"
1970     c_local _dash_themes  "default clean mono dark economist sj"
1971 end
```

S03 makes line 1968 read `version 19`. Its readers, confirmed by grep because Stata programs are not indexed:
- dash.ado:2436 (`_dash_validate_value`, kind `scheme`, whose refusal text is at :2477);
- dash.ado:7448 (`theme()` in `_dash_prepare_spec`);
- `test/test_custom_scheme.cscript` CS-12 (:467-488);
- `test_scheme_resolution.py::TestTheShippedListIsOneList::test_dash_ado_agrees`.

The comment above the program (:1956) says "the twenty scheme translations".

`dash_render.py:5697-5717`, `SchemeParser._BUILTIN_NAMES`. It is a class attribute, so it travels to the served app with the class source (R2: no copy-list entry):

```python
5697    # The twenty translated StataCorp schemes dash ships.  Each is a
5698    # faithful translation of the same-named Stata scheme, generated from
5699    # test/fixtures/scheme_truth.json by scripts/extract_scheme_truth.py.
5704    _BUILTIN_NAMES: frozenset[str] = frozenset({
5706        "stcolor", "stcolor_alt", "stgcolor", "stgcolor_alt", "stmono1",
5707        "stmono2", "stsj", "sttrans",
5714        "economist", "sj",
5715    })
```

Readers (grep; GitNexus gives `UNKNOWN` with "No callers resolved" for this property, confirmed by text search):
- `resolve_or_fallback`'s message (:5867);
- `_shipped_base` (:6006-6015, docstring "one of the twenty shipped names");
- `_resolve_path`'s error text (:6180);
- `_resolve_scheme_name` (:19773, :19781, :19794);
- nine test files: `test_help_claims_8`, `test_installed_layout`, `test_scheme_consumption`, `test_scheme_fidelity`, `test_scheme_linewidth`, `test_scheme_rendered_output`, `test_scheme_resolution`, `test_theme_aliases`, `test_ci_band_style` (through the fixture).

`scripts/extract_scheme_truth.py:1952-1963`:

```python
1952 # The twenty user-selectable schemes StataCorp ships.  The internal ones
1953 # (meta, stcolor_meta, stgcolor_meta, stcolor_mv, stgcolor_mv, stcoloralias)
1954 # are deliberately not translated.  SchemeParser._BUILTIN_NAMES,
1957 SCHEMES = [
1958     "stcolor", "stcolor_alt", "stgcolor", "stmono1", "stmono2", "stsj",
1962     "s2manual", "s1manual", "s2gmanual", "s2color8", "sttrans", "stgcolor_alt",
1963 ]
```

`main` (:1966-2230) takes `--schemes nargs="*"`. Each name reaches `doc[s] = extract(base, s)` (:2204) and `os.path.join(args.schemes_dir, f"dash-{s}.scheme")` (:2215) unchecked, so a name like `../x` would write outside the schemes directory. This is a development script, but S07 touches it, and rule 1 applies (TR-07.2).

`dash.pkg:34-53` lists `f dash-economist.scheme` … `f dash-sttrans.scheme` (20 lines). `scripts/release_gate.do:99-116` builds one page per `dash-*.scheme` in the package root, so `make gate` (S58.5) covers the six with no edit.

### Why nothing else needs to change for the six to draw

`_resolve_scheme_name` (dash_render.py:19771-19800) warns only when the name is in neither `_THEME_SCHEME_MAP` nor `_BUILTIN_NAMES` and `can_resolve` fails:

```python
19771    _lower = _raw_name.lower()
19772    if (_raw_name and _lower not in _THEME_SCHEME_MAP
19773            and _lower not in SchemeParser._BUILTIN_NAMES
19774            and not SchemeParser.can_resolve(_raw_name)):
19775        warnings.warn(
19776            f"dash: {_raw_name!r} is not a known theme or scheme; it was "
```

`SchemeParser._resolve_path` (:6069-6110) reads a shipped name, bare or with `.scheme`, from `dash-<name>.scheme` beside the renderer. The working directory is still tried first (S34 flips that order). `#include` goes through `_resolve_cached` and then `_resolve_path`, so an `#include stcolor_meta` resolves once stcolor_meta is shipped.

The served app resolves the scheme at build time in Stata's process (`ServerAppBuilder.__init__`, :32829-32832) and embeds a property dict (`_DASH_SCHEME`, :33446-33479). A filter move never re-reads a scheme. The saved page's scripts never write `border_fill_color`, `background_fill_color` or `aspect_ratio`: `grep -n '\.border_fill_color *=\|\.background_fill_color *=\|\.aspect_ratio *='` finds only Python build-time lines (:7381-7382, :30342-30378) and generated-app Python (:35227-35256).

### The six in Stata (BASE/s, StataNow 19.5), non-comment lines

```
meta          #include s2color; clockdir legend_position 4; numstyle legend_cols 1; gsize … small (tick_label small);
              linewidth p thin; anglestyle vertical_tick horizontal; yesno draw_major/minor_[hv]grid yes …
stcolor_meta  #include stcolor;      label "stcolor_meta";  color xyline cranberry; linepattern xyline solid
stcolor_mv    #include stcolor_alt;  label "stcolor_mv";    linepattern xyline solid
stcoloralias  #include stcolor;      label "stcoloralt";    zyx2rule colorvar intensity; zyx2rule colorvar hue
stgcolor_meta #include stcolor_meta; label "stgcolor_meta"; graphsize x 3.987; graphsize y 2.392
stgcolor_mv   #include stgcolor_alt; label "stgcolor_mv";   linepattern xyline solid
```

### twoway truth, measured 03oct2026 (probe `p1.do`, run as `scripts/stata_slot.sh <scratch>/s07/probe <scratch>/s07/probe/p1.do`)

`twoway scatter mpg weight, yline(20) scheme(X)`, `graph export` to SVG, read with `scripts/svg_truth.py`. `bg` is the first `<rect>` fill, `marker` the marker fill, `yline` the full-width horizontal line(s) at y = 20, and `tick` the tick-label font size in SVG units. Output lines:

```
VERSION 19.5 born 12 Aug 2026
TWRC meta = 0            DASHRC meta = 198   (and 198 for each of the other five; 0 for stcolor, s2color, stcolor_alt, stgcolor_alt)
SVG meta          wh 5.500in x 4.000in  bg #eaf2f3 markers {#1a476f: 74}  yline #c10534 solid   tick 79.94
SVG stcolor_meta  wh 7.500in x 4.500in  bg #ffffff markers {#1a85ff: 74}  yline #c10534 solid   tick 112.56
SVG stcolor_mv    wh 6.000in x 4.000in  bg #ffffff markers {#1a85ff: 74}  yline #000000 solid   tick 100.04
SVG stcoloralias  wh 7.500in x 4.500in  bg #ffffff markers {#1a85ff: 74}  yline #000000 dashed  tick 112.56
SVG stgcolor_meta wh 3.987in x 2.392in  bg #ffffff markers {#1a85ff: 74}  yline #c10534 solid   tick 59.84
SVG stgcolor_mv   wh 3.588in x 2.392in  bg #ffffff markers {#1a85ff: 74}  yline #000000 solid   tick 59.81
SVG stcolor       wh 7.500in x 4.500in  bg #ffffff                         yline #000000 dashed  tick 112.56
SVG s2color       wh 5.500in x 4.000in  bg #eaf2f3 markers {#1a476f: 74}  yline #c10534 solid   tick 99.99
CV stcolor      4 ['#0000ff', '#00ffaa', '#aaff00', '#ff0000']     (twoway scatter mpg weight, colorvar(price))
CV stcoloralias 4 ['#0000ff', '#00ffaa', '#aaff00', '#ff0000']
```

meta's tick labels are 79.94/99.99 = 0.7995 of s2color's, at the same 5.5 x 4in. That is `gsize tick_label small` (8pt) against medsmall (10pt). meta also draws its major x and y grids thinner (5.76 against 8.64 SVG units) and no minor grid line.

The graph-object probes over the six (the S3 batch's tables in `test_scheme_consumption.py`), one child file per case in the working directory, read with `` local v "`.Graph.plotregion1.plot1.style.<path>'" ``:

```
#include S / color p1 red / linepattern p1 dash   (all six): scatter marker fill and outline 255 0 0; bar fill and outline 255 0 0;
                                                     connected line 255 0 0, dash; line 255 0 0, dash   -> no "kept" row applies
#include S / symbol p diamond      (all six): plot1 diamond, plot2 diamond                              -> not in _DECLARE_P_HASH
#include S / symbolsize p huge     (all six): plot1 4.8611, plot2 4.8611                                -> as the nineteen, not s1manual
#include S alone, marker size:     meta 1.52778 (s2color's medium); the other five 1.04166 (stcolor's small)
twoway lfitci mpg weight, scheme(S): band fill/outline rgb, fit line rgb
  meta          192 192 192 / 192 192 192, fit 26 71 111, fit width .2 (s2color .3)
  the other five 224 224 224 / 224 224 224, fit 26 133 255, fit width .3
```

### dash at the fix, measured on a scratch tree

The tree was `git archive c96facd`, plus the six names in `SCHEMES`, `_BUILTIN_NAMES`, `_dash_schemes` and dash.pkg, plus the extractor run. Probe `p2.py`, through `test_scheme_resolution._draw` and the parity spec:

```
DRAW <each of the six> {standalone,served} {scheme,session_scheme}  name=<itself> fb=False warn=0
stgcolor_meta  aspect 1.6668060200668897  span [('#c10534', [], 1.5)]  tick 10pt     (3.987/2.392)
stgcolor_mv    aspect 1.5                 span [('#000000', [], 1.5)]  tick 10pt
stcolor_meta   aspect 1.6666666666666667  span [('#c10534', [], 1.5)]  tick 10pt
stcolor_mv     aspect 1.5                 span [('#000000', [], 1.5)]  tick 10pt
meta           aspect 1.375               span [('#c10534', [], 1.5)]  tick 8pt
stcolor        aspect 1.6666666666666667  span [('#000000', [8, 4], 1.5)] tick 10pt   (control)
s2color        aspect 1.375               span [('#c10534', [], 1.5)]  tick 10pt     (control)
ALIASDIFF ['name']          (every SchemeParser attribute of stcoloralias equals stcolor's but .name)
meta grids: xgrid/ygrid #eaf2f3, minor #505050 at 0.2 px on both (twoway: no minor grid)
```

The same values hold in both modes (each row was printed for standalone and served alike). At `c96facd` every one of these is `name=s2color border=#eaf2f3` plus the warning, in both modes.

### The regeneration, dry run at `c96facd`

```
python3 scripts/extract_scheme_truth.py --out <scratch>/s07/ext/scheme_truth.json --schemes-dir <scratch>/s07/ext --schemes <the 26>
wrote …/scheme_truth.json (26 schemes)
…/dash-<each of the twenty>.scheme: up to date
…/dash-<each of the six>.scheme: created
```

- `cmp` of the twenty files against the repository's: identical.
- The fixture's twenty records: equal.
- `_meta`: only `generated_utc` and `provenance` differ. The latter's last sentence now names `dash-<name>.scheme`, not the stale `schemes/<name>.scheme`, a leftover of commit 357c368.
- Each of the six has `unresolvable: []`. Include chains:

```
meta          ['s2color', 'meta']                                          graphsize 5.5 x 4    xyline #c10534  legend 4
stcolor_meta  ['s2color', 'stcolor', 'stcolor_meta']                       7.5 x 4.5            #c10534        3
stcolor_mv    ['s2color', 'stcolor', 'stcolor_alt', 'stcolor_mv']          6 x 4                #000000        6
stcoloralias  ['s2color', 'stcolor', 'stcoloralias']                       7.5 x 4.5            #000000        3
stgcolor_meta ['s2color', 'stcolor', 'stcolor_meta', 'stgcolor_meta']      3.987 x 2.392        #c10534        3
stgcolor_mv   ['s2color', 'stcolor', 'stcolor_alt', 'stgcolor_alt', 'stgcolor_mv']  3.588 x 2.392  #000000  6
```

The six files hold no `#include` line (296 lines each, every colour `#rrggbb`). The grid flags are `draw_major_hgrid`/`draw_major_vgrid` yes/yes for all six, and `draw_minor_*` yes/yes for meta only.

### Measured red list (simulated fix, scheme test files)

On the simulated tree (fix applied, no test edited), 109 test files were run. These are every `test/test_*.py` that mentions "scheme", plus test_packaging and test_installed_layout:

```
python3 -m pytest -q -n 4 -p no:cacheprovider -rf <109 files>
```

The result was `19 failed, 18457 passed, 60 skipped, 3 xfailed` in 18:34 (03oct2026). The 19 red nodes are the pins the fix makes wrong. Each is flipped in place under R9, and no other node is touched:

```
test_scheme_resolution.py::TestTheShippedListIsOneList::test_the_parser_ships_the_twenty      SHIPPED is 20; len == 20
test_scheme_resolution.py::TestTheShippedListIsOneList::test_the_extractor_agrees              SHIPPED is 20
test_scheme_resolution.py::TestTheShippedListIsOneList::test_dash_ado_agrees                   SHIPPED is 20
test_scheme_resolution.py::TestAnUnresolvableNameIsReportedOnce::* (8 nodes: nosuchthing, nosuchtheme, session,
    file that does not exist, traversal, graph level, build level [standalone], [served])       the warning's
    "Schemes: …" list now has 26 names; _assert_unknown_warning reads SHIPPED
test_scheme_fidelity.py::test_fixture_is_present_and_complete                                 EXPECTED_SCHEMES is 20
test_scheme_fidelity.py::test_extractor_schemes_list_is_the_twenty                            EXPECTED_SCHEMES; == 20
test_scheme_grids.py::TestTheTruthTableIsTheFixture::test_the_table_covers_every_scheme_in_the_fixture   _GRID_TRUTH; == 20
test_scheme_consumption.py::TestAChildPHashReachesWhatStatasChainReaches::test_the_twenty_are_the_ones_measured        == 20
test_scheme_consumption.py::TestAChildSymbolReachesWhatStatasChainReaches::test_the_nine_are_a_subset_of_the_twenty    == 20
test_packaging.py::test_the_root_holds_exactly_the_twenty_dash_files_the_manifest_ships        == 20
test_help_claims_8.py::TestAnInstalledTreeLooksOnlyForItsOwnTwenty::test_all_twenty_and_nothing_else   == 20
test_help_claims_8.py::TestWhatAnIncludeResolvesTo::test_an_include_that_resolves_to_nothing_stands_s2color_in
    `#include stcolor_meta` now resolves (no note); re-pointed to `w26nosuch`
```

Thirteen of the 19 turn green through two shared constants alone: `SHIPPED` (11 nodes) and `EXPECTED_SCHEMES` (2 nodes). Their own text is unchanged, and each gets one `Flipped:` line naming the constant and its readers. All `test_scheme_consumption.py`, `test_scheme_linewidth.py`, `test_scheme_rendered_output.py` and `test_scheme_fidelity.py` per-scheme parametrizations passed for the six with no edit. `test_installed_layout.py` and `test_ci_band_style.py` passed.

**The flips are sufficient (measured on the same tree, 03oct2026).**
- With `SHIPPED` and `EXPECTED_SCHEMES` grown and the two count pins at 26: `test_scheme_fidelity.py test_scheme_resolution.py` gave `618 passed`. This includes `test_scheme_fidelity.py`'s per-scheme fidelity tests, which then run on the six.
- With the `_GRID_TRUTH` rows, the consumption, packaging and installed-tree pins at 26 and the include re-pointed to `w26nosuch`: `test_scheme_grids.py test_scheme_consumption.py test_packaging.py test_help_claims_8.py test_installed_layout.py` gave `947 passed, 1 skipped`.
- The parity guards of TR-07.9 were checked at `c96facd` through `test_mode_parity._render_pair`: for `scheme(meta)` with `yline(20)` and for `session_scheme` stcolor_meta, the saved and served warnings were equal (one each) and the trees equal.

One more pin moves with the help, not the fix, so the scheme-file run above could not see it (found by the review, measured 06oct2026 on a scratch copy of dash.sthlp with the six `{synopt}` rows added): `test_help_conformance.py::TestTheParsersFoundSomething::test_the_entry_parser_cuts_the_help_into_entries` goes from 339 to 345 definition entries, while `test_the_help_parser_finds_the_whole_surface` stays 149. 07-09 flips it.

These count pins pass at the fix without edit, but their text says "twenty", so 07-03/07-04 update the docstrings or comments:
- `test_scheme_fidelity.py:1-13, :556, :589, :658-663`;
- `test_scheme_consumption.py:1053, :1456-1470, :1697-1710, :1799-1809`;
- `test_ci_band_style.py:11, :184-188` (fixture-derived `len(_SCHEMES) == 20` stays: the fixture has no generator, see TR-07.8);
- `test_adversarial_matrix.py:1432`;
- `test_installed_layout.py:74`.

Area cscripts not run by pytest:
- `test/test_custom_scheme.cscript:51-52, :474`: CS-12 `nsh == 20`.
- `test/test_render_locate.cscript:385`: LOC-13 `loc13nsch == 20`, the count of `dash-*.scheme` a real `net install` files in PLUS/d.

### Blast radius (E4; the batch-3 base impact file records it)

| Symbol | File | Result |
|---|---|---|
| `SchemeParser._BUILTIN_NAMES` | dash_render.py | `UNKNOWN` ("No callers resolved"). Confirmed by grep: 3 renderer methods plus `_resolve_scheme_name`, and 9 test files (above). Unresolved, not low. |
| `SCHEMES` | scripts/extract_scheme_truth.py | ambiguous (4 same-named variables), each `UNKNOWN`. Grep: `test_scheme_fidelity._extractor`, `test_scheme_resolution._extractor_schemes`. |
| `main` (extractor) | scripts/extract_scheme_truth.py | not indexed under that file (`main` is ambiguous). Grep: called only by `__main__` and the new test. |
| `_dash_shipped_schemes` | dash.ado | Stata, not indexed (`UNKNOWN`). Grep: dash.ado:2436, :7448; CS-12; `test_dash_ado_agrees`. |

No HIGH or CRITICAL symbol is edited.

### Tests that pin today's behaviour (flip in place, never delete)

See "Measured red list" for the full set with nodes. Per file:
- `test_scheme_resolution.py`: `SHIPPED` (:55-61, 20 names) and `TestTheShippedListIsOneList::test_the_parser_ships_the_twenty` (`len(SHIPPED) == 20`, :447).
- `test_scheme_fidelity.py`: `EXPECTED_SCHEMES` (:116-125, with the "deliberately not here" comment) and `test_extractor_schemes_list_is_the_twenty` (:1061-1067, `== 20`).
- `test_packaging.py::test_the_root_holds_exactly_the_twenty_dash_files_the_manifest_ships` (:348-356, `== 20`).
- `test_scheme_consumption.py`:
  - `TestAChildPHashReachesWhatStatasChainReaches::test_the_twenty_are_the_ones_measured` (:1503-1507);
  - `TestAChildSymbolReachesWhatStatasChainReaches::test_the_nine_are_a_subset_of_the_twenty` (:1732-1734).
- `test_scheme_grids.py`: `_GRID_TRUTH` (:58-84) and `TestTheTruthTableIsTheFixture::test_the_table_covers_every_scheme_in_the_fixture` (:94-101, `== 20`).
- `test_help_claims_8.py`:
  - `TestWhatAnIncludeResolvesTo::test_an_include_that_resolves_to_nothing_stands_s2color_in` (:978-998) uses `#include stcolor_meta` as the name that resolves nowhere. It is re-pointed to `w26nosuch`, the name its own docstring says was measured. BUGS.md cites this node, so it keeps its name.
  - `TestAnInstalledTreeLooksOnlyForItsOwnTwenty::test_all_twenty_and_nothing_else` (:1121-1147, `== 20`).
- cscripts: `test_custom_scheme.cscript` CS-12 (:474) and `test_render_locate.cscript` LOC-13 (:385).

Every flipped node keeps its name: one of them is cited by BUGS.md, and R9 flips in place. The count moves get R10's trailing comment `# 20 -> 26: P1.25a ships the six StataCorp schemes`.

## User stories

- **US-07.1** As a twoway user, I want `scheme(meta)`, `scheme(stcolor_mv)` and the other four internal StataCorp schemes to draw as twoway draws them, so a do-file that names one works with `dash` in front of it.
- **US-07.2** As a twoway user whose session is `set scheme stcolor_meta`, I want an unschemed dashboard drawn in that scheme with no warning, so it matches my other graphs.
- **US-07.3** As a scheme author, I want `#include stcolor_meta` in my own `.scheme` file to resolve as it does in Stata, so my scheme is drawn on its real parent.
- **US-07.4** As a dashboard publisher, I want the saved page and the served app to draw the six identically, before and after a filter move, so what I test is what my readers see.
- **US-07.5** As a reader of the help, I want the list of shipped schemes to name all 26, and stcoloralias's one difference stated, so I know what dash draws.

## Business requirements

- **BR-07.1** Each of the six (meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta, stgcolor_mv) is accepted by `scheme()` on `dash <plot>`, `dash build`, `dash build, server` and `_dash_serve_spec`, in any case and with or without `.scheme`, with rc 0 and no note.
- **BR-07.2** An inherited `c(scheme)` that is one of the six is drawn with no note.
- **BR-07.3** Each is drawn, in both modes and before and after a filter move, with twoway's measured background, first-series colour, `yline()` colour and solidity, graph proportions and tick-label size relative to s2color (meta), and its legend position, ci band colours and child-scheme behaviour (`color p1`, `symbol p`, `symbolsize p`).
- **BR-07.4** stcoloralias draws exactly what stcolor draws, and the help says that its `zyx2rule colorvar` is not read and that twoway's `colorvar()` scatter is identical under both.
- **BR-07.5** `#include` of one of the six in a user scheme file resolves to it with no note.
- **BR-07.6** dash ships 26 scheme files, installed to PLUS/d, and every place that names the count or the list (help, package manifest, renderer, ado, extractor, tests) says 26.
- **BR-07.7** Nothing that dash drew before changes. The twenty translations, the fixture's twenty records and the default page are byte-identical, apart from the fixture's `generated_utc` and its provenance sentence.

## Technical requirements

- **TR-07.1 The extractor's list.**
  - In `scripts/extract_scheme_truth.py`, append after the WP-17 line of `SCHEMES` (:1962): the comment `# WP-30 P1.25a: StataCorp's six internal schemes, measured in twoway` and the six names in the order meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta, stgcolor_mv.
  - Rewrite the comment at :1952-1956. It now reads "The twenty-six schemes StataCorp ships in BASE/s, every one of them" and names the four copies `test_scheme_resolution.py` holds equal.
- **TR-07.2 The extractor refuses a name that is not a scheme token.**
  - In `main`, directly after `args = ap.parse_args(argv)`, every `args.schemes` entry must match `^[a-z0-9_]{1,32}$` (module constant `_SCHEME_TOKEN_RE`).
  - Otherwise, before any read or write, write `error: --schemes takes scheme names (a-z, 0-9, _; at most 32), got: <repr(name)[:80]>` to stderr and return 2. Nothing is created under `--out` or `--schemes-dir`.
  - Stata's 26 names all match. This closes a path-escape surface (`../x` → `os.path.join(schemes_dir, "dash-../x.scheme")`) on a script every later regenerator runs.
- **TR-07.3 Regenerate, never hand-edit (R7).**
  - From the worktree root run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json`. The defaults are `--stata-base /Applications/StataNow/ado/base` and `--schemes-dir` the repository root.
  - It creates `dash-meta.scheme`, `dash-stcolor_meta.scheme`, `dash-stcolor_mv.scheme`, `dash-stcoloralias.scheme`, `dash-stgcolor_meta.scheme` and `dash-stgcolor_mv.scheme`, and rewrites the fixture with 26 records.
  - The twenty existing files must report "up to date". Any other report stops the task.
- **TR-07.4 The renderer's list.**
  - In `SchemeParser._BUILTIN_NAMES` (dash_render.py:5704-5715), add a group after `"economist", "sj",`: the comment `# StataCorp's internal schemes (WP-30 P1.25a); stcoloralias draws as stcolor` and the six names.
  - Rewrite the comment above it (:5697-5703) and `_shipped_base`'s docstring (:6007) from "twenty" to "twenty-six".
  - No copy-list entry: the frozenset is a class attribute and travels with `inspect.getsource(SchemeParser)` (R2 row S07). No function is added, so `function_test_map.py` is unchanged.
- **TR-07.5 dash.ado's list.**
  - In `_dash_shipped_schemes` (dash.ado:1969), append ` meta stcolor_meta stcolor_mv stcoloralias stgcolor_meta stgcolor_mv` inside the `_dash_schemes` string, lower case, each once.
  - Change the comment at :1956 to "twenty-six".
  - Edit nothing in `_dash_validate_value` (S08 edits its size rules in this batch; the scheme-kind code there is S34's) and nothing else in the program. No new program, so `program_coverage_map.py` is unchanged.
- **TR-07.6 dash.pkg.** Add `f dash-meta.scheme`, `f dash-stcolor_meta.scheme`, `f dash-stcolor_mv.scheme`, `f dash-stcoloralias.scheme`, `f dash-stgcolor_meta.scheme` and `f dash-stgcolor_mv.scheme` after `f dash-sttrans.scheme` (:53). The Distribution-Date stays (S58.6).
- **TR-07.7 Both modes and the move.**
  - No renderer code changes. The tests of TR-07.9 prove both modes and the move: the saved renderer (`DashRenderer`) and the served app (`ServerAppBuilder` + `make_document`) draw the same scheme properties, and a served dropdown move (`test_served_linked_views._fire`) leaves `border_fill_color`, `background_fill_color`, `aspect_ratio`, the `Span` colour and dash, and the tick-label size unchanged.
  - The saved page has no script that writes them (Evidence).
  - No JS twin is needed: the scheme is build-time state in both modes.
- **TR-07.8 Stata truth for the twenty-scheme tables (register P1.25.2).**
  - The `SX` block (Stata truth below) measures the six against twoway's graph object and SVG in the same run as dash's pages. That covers the S3-batch tables and the ci band, so the pytest tables can extend to 26 with honest docstrings.
  - `test/fixtures/ci_band_style_truth.json` has no committed generator and covers 20 schemes. It is not hand-patched. `test_ci_band_style.py`'s module docstring and `test_the_fixture_covers_every_scheme_and_type` docstring say the six are certified by `SX-06` and `test_twenty_six_schemes.py::TestTheSixDrawWhatTwowayDraws::test_the_ci_band_is_statas`. The fixture-derived `len(_SCHEMES) == 20` stays true and unflipped.
- **TR-07.9 Tests.**
  - New: `test/test_twenty_six_schemes.py` ("TDD test stubs").
  - Flips: the "Measured red list".
  - Parity guards appended to `test/test_mode_parity.py` `CORPUS` (one `_case` per scheme, `yline` on) and `MOVE_CORPUS` (`stcolor_meta` and `stgcolor_mv` with `_MOVES[0]`) (R8; `ALLOWED` and `_MUST_WARN` untouched).
- **TR-07.10 Help (R3: Stata scheme support 3291-3600, S07's own lines).** In dash.sthlp:
  - **:3300** "twenty" → "twenty-six". Add six `{synopt}` rows after `{synopt:{cmd:sj}}{p_end}` (:3331):
    - `meta`: "{cmd:s2color} with smaller text (8-point tick labels where {cmd:s2color} has 10), thinner plot lines, a one-column legend at 4 o'clock, and grids on both axes";
    - `stcolor_meta`: "{cmd:stcolor} with a solid cranberry {cmd:xline()}/{cmd:yline()}";
    - `stcolor_mv`: "{cmd:stcolor_alt} with solid reference lines";
    - `stcoloralias`: "{cmd:stcolor} with {cmd:zyx2rule colorvar hue}, a directive {cmd:dash} does not read: it is drawn as {cmd:stcolor}, which is also what {cmd:twoway} draws for a {cmd:colorvar()} scatter under it";
    - `stgcolor_meta`: "{cmd:stcolor_meta} at 3.987 by 2.392 inches";
    - `stgcolor_mv`: "{cmd:stgcolor_alt} with solid reference lines".
  - **:3493** delete ", or one of StataCorp's internal ones such as {cmd:stcolor_meta}". The sentence keeps "a third-party scheme" (S34 rewrites the rest).
  - **:3501, :3505** "twenty" → "twenty-six".
  - **:3511** delete "one of StataCorp's internal schemes, such as {cmd:stcolor_meta}, ".
  - **:3573, :3575, :3578** "twenty" → "twenty-six" (three times).
  - No other paragraph: the remedy (:3461-3465) and the precedence sentence (:3582-3583) are S34's.
- **TR-07.11 Security (rule 1).**
  - The six files are data: no `#include`, every colour `#rrggbb[ %NN]`, no path character in any value, parsed by `SchemeParser` and never executed.
  - Scheme names are fixed tokens. They reach the served app only as `_DASH_SCHEME["name"]`, written by the builder through `repr`.
  - The extractor refuses non-tokens (TR-07.2).
  - `test_twenty_six_schemes.py::TestTheSixAreData` pins all three. No `shell=True`, no `eval` of user text, and no new HTML or JS sink.

## Boundaries

- **S08 (batch 3)** owns sizes: `resolve_size`, `translate_msize`, `_textbox_size`, `_mlabel_gap_px`, the four appliers, `_dash_validate_value`'s size rules and CHANGELOG.md:522. S07 certifies meta's tick labels only as dash draws them today (8pt against 10pt). If S08 changes the unit, the ratio test still holds: it compares meta with s2color.
- **S09 (batch 3)** owns `_build_sources_and_figures` and the text pass. S07 touches neither.
- **S34 (batch 12)** owns everything else in P1.25:
  - `scheme-NAME.scheme` and the ado-path walk;
  - the findfile gate in `_dash_validate_value`;
  - the refusal's list of names (sub-claim e);
  - the shipped-first precedence over a working-directory file (f; `test_scheme_resolution.py:827`, dash.sthlp:3458/:3582);
  - the help's copy remedy (g);
  - theme-alias shadowing (P1.25.5);
  - per-graph served schemes (P1.25.6);
  - CS-10 and CS-16..22.

  S07 does not touch `_resolve_path`, `can_resolve`, `_resolve_scheme_name`, `_include`, `_resolve_cached` or `_dash_validate_value`.
- **S15 (batch 5)** owns scheme chrome, tick angle (`anglestyle vertical_tick`, which makes meta's y labels horizontal), minor ticks and meta's minor grid (Notes). It also owns `apply_to_figure`/`apply_to_axis` and the next regeneration.
- **S13 (batch 5)** owns line widths (meta's `linewidth p thin`, the grid widths).
- **S24, S30, S33, S36, S47, S50, S53, S56** extend the extractor and regenerate all 26. S07 adds no scheme key.
- **Tracking documents** (GAPS2 Tracked lines, DROPIN, REMAINING, TWOWAY_COVERAGE_AUDIT.md:144 "20 shipped translations", ROADMAP, AGENTS.md) are S58's (A145). See "Notes for the closeout".
- Not touched: `ci_band_style_truth.json` (no generator; TR-07.8), `test_fixtures_are_committed.py`, the runner and the hygiene pins (R1), and any served copy list.

## Stata truth

No new fixture and no new extractor. `test/fixtures/scheme_truth.json` is regenerated by its existing Python extractor, which reads Stata's own files and never runs Stata.
- Its `_meta` stamp is the extractor's own: `stata_version` "StataNow 19.5 (MP), born 12 Aug 2026", `generated_utc`, `scheme_dir`, `style_dir` and the rest. These existing keys stay (R7).
- D12's `dash_commit`/`extracted` belong to do-file extractors and are not added to this one.
- The fixture is tracked, so `git add -f test/fixtures/scheme_truth.json` stages it (`.git/info/exclude:58` ignores `*.json`).
- Its test is `test_scheme_fidelity.py::test_fixture_is_present_and_complete`.

The twoway comparison lives in the `SX` block of `test/test_wp30_truth.cscript`, between S01's `display as text "S07 start …"` and `"S07 end …"` lines. Its helpers sit directly above `* ==== S07 P1.25a: … ====`.

**Run it** through the driver (index "The cscript driver"):

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s07/run_test_wp30_truth.do
WP30_ONLY=S07 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s07 <scratch>/s07/run_test_wp30_truth.do
# log: <scratch>/s07/run_test_wp30_truth.log
```

**Helpers** (python, defined at the top level above the S07 header, where braces are safe; every argument crosses through `sfi.Macro.getGlobal`, every answer goes back through `Macro.setGlobal`; no macro text is pasted into Python source; no `shell=True`):

| Helper | Reads | Sets |
|---|---|---|
| `_s07_svg()` | `S07_SVG` (with `yline(20)`), `S07_SVG0` (same graph, no yline) | `S07_TW` = `bg;marker;ylc;segs;w;h;tick` (fields joined by `;`). `bg` is the first `<rect>` fill. `marker` is the most frequent `svg_marker_fills` colour. `ylc`/`segs` are the stroke and segment count of the `hlines` present in `S07_SVG` and absent from `S07_SVG0` (same stroke, width and y); `segs == 1` is solid. `w`/`h` come from `<svg width height>` in inches. `tick` is the most frequent text size. |
| `_s07_page()` | `S07_PAGE` (a saved page) | `S07_D` = `border;plot;fill;span;dash;aspect;tick`, read from the page's embedded JSON models (the WP-29 `_s03_models` method, renamed). Fields: the first `Plot`'s `border_fill_color`/`background_fill_color`; the first `Scatter` glyph's `fill_color`; the first `Span`'s `line_color` and `line_dash` (`solid` when empty); `aspect_ratio` to 4 decimals; the first `LinearAxis`'s `major_label_text_font_size`. |
| `_s07_app()` | `S07_APP` (a served `app.py`), `S07_MOVE` (a dropdown variable) | `S07_S` (the same summary from `make_document(Document())`), then fires the `Select` whose `_dash_var` is `S07_MOVE` to its second option. It sets `S07_FIRED` and `S07_SAME_AFTER` (1 if the summary is unchanged). |
| `_s07_child()` | `S07_CHILD` (a scheme name in the working directory) | `S07_DC` = dash's `SchemeParser(name)` `default_color(0, kind)` for the kinds scatter, bar, connected and line, `default_connect_pattern(0)`, `default_line_pattern(0)`, `p_symbols[0:2]` and `default_marker_size(0)` and `(1)`, joined by `;`. It imports `dash_render` from `os.path.abspath("..")` as WP-29's S04 block does. |
| `_s07_ci()` | `S07_SCH` | `S07_DCI` = `fill;outline;fit` hex of `GlyphMapper(scheme=SchemeParser(name)).map_lfitci` on a 40-row frame (the `test_ci_band_style._draw` method); `error` when `SchemeParser` raises (an unshipped name at the base). |
| `_s07_rgb()` | `S07_GOB` (a `.Graph` colour as `r g b [%a]`) | `S07_HEX` = `#rrggbb` (`%02x` per channel), so every colour comparison is hex against hex. |

`_s07_child()` also records `S07_DCW`, the number of warnings containing `not found, using s2color` raised while parsing, so an `#include` of an unshipped parent shows. A `program define _s07_gob` (Stata, `version 19`, above the header) reads one `.Graph` member into `$S07_GOB` in the `local v "`.Graph.<path>'"` form (cert_svg.do's trap note: assign to a local first, in its own statement).

**Cases** (each `sysuse auto, clear` first unless stated). Every dash page, served app, SVG and log is written under the scaffold's work directory: a `saving(sx1.html)` below means `` saving("`w30_work'/sx1.html") ``. Pages are built under `capture noisily`. Their log is captured with a named `` log using "`w30_work'/sxk.log", text replace name(sxk) `` and read with `cert_log_has`. The note needles are `is not a known theme or scheme` and `not found, using s2color`, which match in the `(note: …)` channel S06 left.

**Files in the working directory (SX-05, SX-08 only).** A child scheme file must sit in the working directory (`test/`), because twoway's `findfile` and dash's lookup before S34 read only there and the ado-path. This is the one exception to TR-01.10's work-directory rule. Before writing each such file, the case runs `capture confirm new file <name>`; a non-zero rc fails the case and writes nothing (rule 1: a planted file is never overwritten or read). Each file is erased in the same case, after the comparison, whether it passed or failed.

| Id | What | twoway side | dash side | PASS when |
|---|---|---|---|---|
| SX-01 | The refusal is gone | `twoway scatter mpg weight, scheme(S)` rc, for the six lower-case names | for S in the six, plus `META` and `meta.scheme` (dash-only spellings; twoway's case rule is platform-dependent, M4): `dash scatter mpg weight, scheme(S) name(sx1)` rc; `dash build, scheme(S) saving(sx1.html) replace nobrowser` rc; `_dash_serve_spec` as CS-13 calls it, rc | every rc 0 on both sides; no note needle in the log. At `c96facd`: dash rc 198 |
| SX-02 | Drawn as twoway, saved | per S, `twoway scatter mpg weight, yline(20) scheme(S)` → SVG, and the same without `yline` → SVG0; `_s07_svg` | `dash scatter mpg weight, yline(20) scheme(S) saving(sx2_S.html)`; `_s07_page` | bg = border; marker = fill; ylc = span; `segs == 1` iff dash `solid`; `abs(w/h - aspect) < 0.0005`; for meta only, `tick_meta/tick_s2color` within 0.01 of dash's `8pt/10pt`. Controls stcolor (dashed `[8, 4]`) and s2color run the same way |
| SX-03 | Served, and after a move | — | `dash build, server saving(sx3_S.py) replace nobrowser filter(foreign, type(dropdown))` after registering SX-02's graph; `_s07_app` with `S07_MOVE foreign` | `S07_S == S07_D` of SX-02; `S07_FIRED == 1`; `S07_SAME_AFTER == 1` |
| SX-04 | Inherited `c(scheme)` | `set scheme S`; `twoway scatter mpg weight, yline(20)` → SVG; `_s07_svg` | `set scheme S`; `dash scatter mpg weight, yline(20) saving(sx4_S.html)` with no `scheme()`; `_s07_page` | the SX-02 equalities; rc 0; no note needle. Restore the entry `c(scheme)` (saved in a local before the case) at the end |
| SX-05 | The twenty-scheme tables over the six | per S, write `scheme-sx5red_S.scheme` (`#include S`, `color p1 red`, `linepattern p1 dash`), `scheme-sx5sp_S.scheme` (`symbol p diamond`), `scheme-sx5zp_S.scheme` (`symbolsize p huge`); `twoway scatter`, `bar`, `connected` and `line` of `y1 x`, `scheme(…) nodraw`, on `set obs 11`; `_s07_gob` reads marker fillcolor, `area.shadestyle.color`, `line.color`, `line.pattern`, `marker.symbol`, `marker.size` | the same three files written also as `sx5red_S.scheme` etc. (dash reads the bare name in the working directory until S34); `_s07_child` | marker, bar, connected and line colour 255 0 0 / `#ff0000`; connected and line pattern `dash` / dash's `translate_lpattern("dash")`; both symbols `diamond`; both sizes twoway `4.8611`, dash `_markersize_px("huge")`; `S07_DCW == 0` (at `c96facd` the `#include S` notes "not found", so the case is red there) |
| SX-06 | ci band | per S, `twoway lfitci mpg weight, scheme(S) nodraw`; `_s07_gob` reads `plot1.style.area.shadestyle.color.rgb`, `…linestyle.color.rgb`, `plot2.style.line.color.rgb` | `_s07_ci` | fill, outline and fit hex equal. Widths are S13's and not compared |
| SX-07 | stcoloralias is stcolor | `twoway scatter mpg weight, colorvar(price) scheme(stcolor)` and `scheme(stcoloralias)` → SVGs; `svg_marker_fills` sets | the same `dash scatter …, colorvar(price) scheme(…)` pages; the `Scatter`'s colour mapper palette and the first `Plot`'s colours via `_s07_page` | twoway's two fill sets equal; dash's two summaries and palettes equal. twoway's hue ramp and dash's continuous map are not compared with each other (DISCOVERY Q5/X2, documented) |
| SX-08 | `#include` of one of the six | `sx8.scheme` = `#include stcolor_meta` / `color background red` in the working directory; `twoway scatter mpg weight, yline(20) scheme(sx8)` → SVG (twoway finds `sx8.scheme` by its second `findfile`) | `dash scatter mpg weight, yline(20) scheme(sx8) saving(sx8.html)`; `_s07_page`; log | twoway bg `#ff0000`, marker `#1a85ff`, ylc `#c10534`, solid; dash border `#ff0000`, fill `#1a85ff`, span `#c10534` solid; no `not found, using s2color` in the log |

Each case ends with `_w30_done SX-0k "<what>"`, which prints `SX-0k PASS`. No case prints SKIP. The block erases its files and `graph drop`s its graphs. The script's header comment list of blocks gains `S07  P1.25a the six StataCorp schemes against twoway (SX-01..SX-08)`.

## TDD test stubs

### Regression tests, `test/test_twenty_six_schemes.py` (new; red at `c96facd` unless marked guard)

Module setup:
- `SIX = ("meta", "stcolor_meta", "stcolor_mv", "stcoloralias", "stgcolor_meta", "stgcolor_mv")` and `MODES = ("standalone", "served")`.
- `_TWOWAY`: the measured table of Evidence, keyed by scheme: `bg`, `marker`, `yline` (hex, solid), `graphsize`, `tick`. The docstring quotes the `p1.do` command and date.
- `_CHAINS`: the include chains of Evidence.
- `_draw`, `_spec`, `MODES` imported from `test_scheme_resolution`; `tp` is `test_mode_parity`; `_fire` comes from `test_served_linked_views`.
- Specs use `plot_for("scatter")` with `{"yline": "20"}`. A served move spec adds `filter="foreign, type(dropdown)"`.

- Test: `test/test_twenty_six_schemes.py::TestTheSixAreShipped::test_each_has_its_dash_file[S]`. `dash-S.scheme` exists in the root. Base: `AssertionError … dash-meta.scheme`.
- Test: `::TestTheSixAreShipped::test_the_parser_ships_twenty_six`. `len(_BUILTIN_NAMES) == 26` and `set(SIX) <= _BUILTIN_NAMES`. Base: `assert 20 == 26`.
- Test: `::TestTheSixAreShipped::test_each_parses_from_its_file_without_a_word[S]`. `SchemeParser(S)` has `is_fallback False` and `name == S`, with no warning. Base: ValueError.
- Test: `::TestTheSixAreShipped::test_the_manifest_ships_each[S]`. dash.pkg has `f dash-S.scheme`.
- Test: `::TestTheSixAreShipped::test_dash_ado_and_the_extractor_list_each`.
- Test: `::TestTheFixtureCoversTheSix::test_each_is_extracted_with_nothing_unresolvable[S]` and `::test_each_chain_is_statas[S]` (`include_chain == _CHAINS[S]`).
- Test: `::TestTheFixtureCoversTheSix::test_the_shipped_file_draws_the_fixture[S]`. `p_colors`, `background_color`, `graphsize_x/y` and `xyline_color` of `SchemeParser(S)` equal the fixture.
- Test: `::TestTheSixResolveInBothModes::test_by_build_scheme[S-mode]`, `::test_by_graph_scheme[S-mode]`. `scheme.name == S`, no warning, and `fig.border_fill_color == _TWOWAY[S]["bg"]`. Base: `assert 's2color' == 'meta'`.
- Test: `::TestTheSixResolveInBothModes::test_unchanged_after_a_filter_move[S]`. Served: the `(border, plot, Span colour and dash, aspect, tick size)` summary is equal before and after `_fire(doc, "foreign", "Foreign")`. Saved: the summary of the page equals the served "before" one.
- Test: `::TestTheInheritedSchemeIsOneOfTheSix::test_the_session_scheme_resolves[S]`. `_resolve_scheme_name({"session_scheme": S})` returns `S` with zero warnings. Base: `'s2color'` plus one warning.
- Test: `::TestTheInheritedSchemeIsOneOfTheSix::test_the_session_scheme_is_drawn[S-mode]`.
- Test: `::TestTheSixDrawWhatTwowayDraws::test_the_background_and_first_series[S-mode]`.
- Test: `::TestTheSixDrawWhatTwowayDraws::test_the_yline_is_the_schemes[S-mode]`, over SIX plus the controls stcolor and s2color. The `Span` `line_color == _TWOWAY[S]["yline"][0]`, and `line_dash == []` iff solid.
- Test: `::TestTheSixDrawWhatTwowayDraws::test_the_proportions_are_the_graphsize[S-mode]`. `fig.aspect_ratio == pytest.approx(x / y, abs=1e-9)`.
- Test: `::TestTheSixDrawWhatTwowayDraws::test_metas_tick_labels_are_twoways_ratio[mode]`. Under meta and under s2color, `float(size[:-2])` of the y axis's `major_label_text_font_size`; the ratio is within 0.01 of 79.94/99.99.
- Test: `::TestTheSixDrawWhatTwowayDraws::test_metas_legend_sits_at_4_oclock[mode]`. `d.scheme.legend_position == 4` in both modes (the saved renderer's `SchemeParser`; the served module's `_DASH_SCHEME`, also a `SchemeParser`, measured on the scratch tree).
- Test: `::TestTheSixDrawWhatTwowayDraws::test_the_ci_band_is_statas[S]`, by `test_ci_band_style._draw("lfitci", S, {})`. The band `VArea` fill, the outline `Patch` line and the fit `Line` colour are meta `#c0c0c0`/`#c0c0c0`/`#1a476f` and the other five `#e0e0e0`/`#e0e0e0`/`#1a85ff`.
- Test: `::TestStcoloraliasIsDrawnAsStcolor::test_every_parsed_property_but_the_name_is_stcolors`. `{k for k in vars(a) if vars(a)[k] != vars(b).get(k)} == {"name"}`.
- Test: `::TestStcoloraliasIsDrawnAsStcolor::test_a_colorvar_scatter_matches_stcolor[mode]`. Under `colorvar(price)` (the `test_colorvar_*` spec form), `d.scheme.name == "stcoloralias"` with no warning (red at base), and the colour mapper's palette, low and high equal stcolor's. dash's continuous map is scheme-independent (viridis under both, measured at `c96facd`), so the equality guards against a future `zyx2rule` reader, not against twoway's hue ramp (DISCOVERY Q5/X2's documented difference).
- Test: `::TestStcoloraliasIsDrawnAsStcolor::test_the_help_says_so`. dash.sthlp, whitespace-collapsed, holds `{cmd:zyx2rule colorvar hue}` and "drawn as {cmd:stcolor}".
- Test: `::TestAnIncludeOfOneOfTheSixResolves::test_include_stcolor_meta_without_a_note`. In a tmp working directory, `sx8.scheme` holds `#include stcolor_meta\ncolor background #ff0000\n`. `SchemeParser("sx8")` gives background `#ff0000`, `p_colors[0] #1a85ff` and `xyline_color #c10534`, and no warning contains "not found". Base: the note is present and the p1 colour is `#1a476f`.
- Test: `::TestTheSixAreData::test_every_shipped_file_is_flat_and_hex[all 26]`.
  - No line starts with `#include`.
  - Every `color` directive value matches `^#[0-9a-f]{6}( %\d{1,3})?$|^none$`.
  - No directive value holds `/`, `\`, `..`, a quote other than a `label` line's own pair, or a control character.
- Test: `::TestTheSixAreData::test_every_listed_name_is_a_plain_token`. Each name in `_BUILTIN_NAMES`, `_dash_schemes` and `SCHEMES` matches `^[a-z0-9_]{1,32}$`.
- Test: `::TestTheSixAreData::test_the_extractor_refuses_a_name_that_is_not_a_token`.
  - For `../x`, `a/b`, `x y`, `""`, `"a"*33` and `S2COLOR`, `mod.main(["--out", str(tmp/"o.json"), "--schemes-dir", str(tmp/"d"), "--schemes", bad])` returns 2.
  - Neither `o.json` nor any file under `tmp/"d"` exists.
  - Base: no return 2 (the run proceeds or raises).
- Test (guard; red at base only because meta is not shipped): `::TestMetasMinorGridIsHandedOn::test_dash_still_draws_metas_minor_grid`.
  - Both grids' `minor_grid_line_color == "#505050"` in both modes.
  - The docstring says that twoway draws no minor grid under meta (no minor ticks by default; `p1_meta.svg`). It also says that S15 (P1.2a) flips this test when it removes Bokeh's default minor positions, and that the flip is S15's, not S07's.

### Flips (in place; R9/R10 comments; red at base after the edit where they assert new counts)

- `test/test_scheme_resolution.py`:
  - `SHIPPED` gains the six; its comment says "twenty-six: … plus StataCorp's six internal schemes (WP-30 P1.25a)".
  - `TestTheShippedListIsOneList::test_the_parser_ships_the_twenty` asserts `len(SHIPPED) == 26` (R10 comment).
  - Every node parametrized on `SHIPPED` (`test_every_shipped_name_has_a_file`, `TestEveryShippedSchemeResolves::*`, `TestCanResolve::test_every_shipped_scheme_is_true`, the `_assert_unknown_warning` users) grows by itself.
- `test/test_scheme_fidelity.py`:
  - `EXPECTED_SCHEMES` gains the six, under the comment `# WP-30 P1.25a: StataCorp's six internal schemes`; the "deliberately not here" comment is deleted.
  - `test_extractor_schemes_list_is_the_twenty` asserts `== 26`.
  - The docstrings at :1-13, :589 and :663 say twenty-six.
- `test/test_packaging.py::test_the_root_holds_exactly_the_twenty_dash_files_the_manifest_ships` asserts `== 26`.
- `test/test_scheme_consumption.py`:
  - `test_the_twenty_are_the_ones_measured` and `test_the_nine_are_a_subset_of_the_twenty` assert `== 26`.
  - Each of the three class docstrings gains: "Measured 03oct2026 over StataCorp's six internal schemes (WP-30 S07, test_wp30_truth.cscript SX-05): every one follows the not-kept rows: red markers, bars, connected and line, dashed; both symbols diamond; both sizes 4.8611 (huge)."
  - "nineteen schemes" → "twenty-five schemes" (:1805).
- `test/test_scheme_grids.py`:
  - `_GRID_TRUTH` gains `"meta": (True, True)` and `(True, True)` for the other five, under a comment naming their chains and meta's own `yesno draw_major_hgrid yes`.
  - `test_the_table_covers_every_scheme_in_the_fixture` asserts `== 26`.
- `test/test_help_claims_8.py`:
  - `test_an_include_that_resolves_to_nothing_stands_s2color_in`: `stcolor_meta` → `w26nosuch` in the file text and the needle.
  - `test_all_twenty_and_nothing_else` asserts `== 26`, and the class docstring says twenty-six.
- `test/test_custom_scheme.cscript`: the CS-12 header lines :51-52 say twenty-six, and :474 reads `(`nsh' == 26)` with "(expected 26)".
- `test/test_render_locate.cscript`: `assert `loc13nsch' == 26` (:385), with a comment line above it.
- `test/test_help_conformance.py::TestTheParsersFoundSomething::test_the_entry_parser_cuts_the_help_into_entries`: `len(defs) == 345` (339 + the six `{synopt}` rows; 07-09, with the help).

### Guards appended (green at base and after)

- `test/test_mode_parity.py`:
  - `CORPUS` gains `_case("scatter with yline, <S>", [_sc()], {"scheme": S}, {"yline": "20"})` for each of the six, and `_case("scatter, session scheme stcolor_meta", [_sc()], {"session_scheme": "stcolor_meta"})`.
  - `MOVE_CORPUS` gains `_move_case("scatter with yline under stcolor_meta, dropdown", _MOVES[0], [_sc()], {"yline": "20"}, bo={"scheme": "stcolor_meta"})` and the same for stgcolor_mv.
  - At base both modes draw s2color plus the same warning, so these pass before and after (G3).
- `test/test_ci_band_style.py`: docstrings only (TR-07.8).
- `test/test_adversarial_matrix.py`: the :1432 docstring says twenty-six.

### Mutation table (each must turn a named test red)

| Mutation | Red test |
|---|---|
| Drop one of the six from `_BUILTIN_NAMES` | `TestTheShippedListIsOneList::test_the_parser_ships_the_twenty`, `TestTheSixResolveInBothModes::test_by_build_scheme[…]` |
| Drop one from `_dash_schemes` | `TestTheShippedListIsOneList::test_dash_ado_agrees`, SX-01 |
| Delete `dash-stgcolor_meta.scheme` | `TestTheSixAreShipped::test_each_has_its_dash_file[stgcolor_meta]`, `test_pkg_manifest_lists_every_runtime_file` |
| Hand-edit a colour in `dash-meta.scheme` | `TestTheFixtureCoversTheSix::test_the_shipped_file_draws_the_fixture[meta]`, `test_regenerating_a_shipped_file_is_a_no_op` |
| Remove the extractor's token check | `TestTheSixAreData::test_the_extractor_refuses_a_name_that_is_not_a_token` |
| Add a `zyx2rule` read that changes stcoloralias | `TestStcoloraliasIsDrawnAsStcolor::test_every_parsed_property_but_the_name_is_stcolors` |

## Test plan

| What | How | Fixture / truth | Both modes? |
|---|---|---|---|
| The six are shipped, listed once, parse silently | pytest `test_twenty_six_schemes.py::TestTheSixAreShipped`, `TestTheShippedListIsOneList` | `scheme_truth.json` | n/a (parser) |
| Fixture records and chains | pytest `TestTheFixtureCoversTheSix`, `test_scheme_fidelity.py` (all) | `scheme_truth.json` | n/a |
| Resolution by build, graph and session | pytest `TestTheSixResolveInBothModes`, `TestTheInheritedSchemeIsOneOfTheSix`, `test_scheme_resolution.py::TestEveryShippedSchemeResolves` | — | yes |
| After a filter move | pytest `test_unchanged_after_a_filter_move`; `test_mode_parity.py` MOVE_CORPUS; cscript SX-03 | — | yes (saved = served before; served before = after) |
| Drawn as twoway | pytest `TestTheSixDrawWhatTwowayDraws` (measured constants); cscript SX-02, SX-04, SX-06 | twoway SVG and `.Graph` in the same run | yes |
| Child-scheme tables | pytest `test_scheme_consumption.py`, `test_scheme_linewidth.py`, `test_scheme_rendered_output.py` (parametrized on 26); cscript SX-05 | `.Graph` | parser |
| stcoloralias | pytest `TestStcoloraliasIsDrawnAsStcolor`; cscript SX-07 | twoway SVG | yes |
| `#include` of the six | pytest `TestAnIncludeOfOneOfTheSixResolves`; cscript SX-08 | twoway SVG | parser + saved |
| Refusal lifted, every entry point | cscript SX-01, CS-12 | — | saved + `_dash_serve_spec` |
| Install | cscript LOC-13 (`net install` into scratch PLUS); pytest `test_installed_layout.py`, `test_help_claims_8.py::TestAnInstalledTreeLooksOnlyForItsOwnTwenty` | — | n/a |
| Parity | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3) | — | yes |
| Security | pytest `TestTheSixAreData` | — | n/a |

**Acceptance criteria**

- **AC-07.1** `dash scatter mpg weight, scheme(S)`, `dash build, scheme(S)` and `_dash_serve_spec … scheme(S)` give rc 0 and no note for each of the six (SX-01). CS-12 builds 26 names.
- **AC-07.2** After `set scheme S`, an unschemed dashboard is S, with no note, in both modes (SX-04, `test_the_session_scheme_resolves`).
- **AC-07.3** Each of the six's background, first-series colour, `yline` colour and solidity and proportions equal twoway's in the saved page and the served app. meta's tick-label ratio is within 0.01 of twoway's (SX-02, SX-03, `TestTheSixDrawWhatTwowayDraws`).
- **AC-07.4** The served summary is unchanged by a dropdown move (SX-03, `test_unchanged_after_a_filter_move`, MOVE_CORPUS).
- **AC-07.5** SX-05 and SX-06 PASS for all six. `test_scheme_consumption.py` passes at 26.
- **AC-07.6** stcoloralias equals stcolor in every parsed property but `name`. twoway's `colorvar()` fills are equal under both (SX-07). The help says so.
- **AC-07.7** `#include stcolor_meta` resolves with no note (SX-08, `test_include_stcolor_meta_without_a_note`).
- **AC-07.8** `git diff --stat` on the twenty existing `dash-*.scheme` is empty. The fixture's twenty records are equal to HEAD's. `_meta` differs in `generated_utc` and `provenance` only.
- **AC-07.9** `grep -c twenty` over S07's help lines (:3300, :3501, :3505, :3573, :3575, :3578) prints 0, and the six `{synopt}` rows exist.
- **AC-07.10** The extractor returns 2 and writes nothing for a non-token name.
- **AC-07.11** The full suite is green once in the worktree. The `SX` block prints 8 PASS and no FAIL or SKIP. CS-12 and LOC-13 PASS.

## Tasks

**Commit boundary.** Tasks 07-01 to 07-10 form the one P1.25a commit. Its subject is `Ship StataCorp's six remaining schemes, twenty-six in all (WP-30 P1.25a)`, made by 07-10 on `wp30-s07` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s07`, after one full run through the queue.
- The body opens with `<scratch>/07-P1.25a-failure.txt`, then gives the measured defect and what changed where.
- It then carries one line each of:
  - `Regression: test/test_twenty_six_schemes.py::<Class>::<test> -- failed at <batch-3 base sha> with <text>`;
  - `Flipped: <node> -- <old expectation> was wrong because dash now ships StataCorp's six internal schemes (measured in twoway, SX-01..SX-08)` (one per flip, from `<scratch>/s07/07-flips.txt`);
  - `Fixture: test/fixtures/scheme_truth.json (scripts/extract_scheme_truth.py)`;
  - `BUGS.md: "<title>" (closed)`.

Every command runs from `$WT`. `<scratch>` is the WP-30 scratch directory the orchestrator hands over. No body, BUGS or CHANGELOG line names a tool or vendor (G7).

<task type="auto" id="07-01">
  <name>Write the failing six-scheme tests</name>
  <files>test/test_twenty_six_schemes.py</files>
  <action><![CDATA[
    First check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-3-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s07`. Run `mkdir -p <scratch>/s07` and confirm that `<scratch>/batch-3-impact.txt` holds the four rows of Evidence "Blast radius" (`_BUILTIN_NAMES`, `SCHEMES`, the extractor's `main`, `_dash_shipped_schemes`, each UNKNOWN with its grep). If a row is missing, run `gitnexus impact <symbol> -d upstream -r dash` in the main checkout plus the grep, and append it. Create `test/test_twenty_six_schemes.py` with exactly the classes, tests, module constants and imports of "TDD test stubs / Regression tests". The module docstring quotes the defect (r(198) for the six; s2color plus the warning when inherited, both modes), the `p1.do` command and date, and the twoway table. Do not touch any other file. Run `python3 -m pytest test/test_twenty_six_schemes.py -q -n0 -p no:cacheprovider -rf > <scratch>/s07/07-01.log 2>&1` and write `<scratch>/07-P1.25a-failure.txt`: the base sha, each failing node with its one-line reason, and the guard tests that passed. Do not commit, and do not weaken a test to pass.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s07/07-01.log` is at least 40, `grep -c "assert 's2color' == 'meta'\|dash-meta.scheme\|ValueError" <scratch>/s07/07-01.log` is at least 3, and `test -s <scratch>/07-P1.25a-failure.txt`.]]></verify>
  <done>Every regression test of the section existed and was shown failing on the unmodified tree, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="07-02">
  <name>Flip the one-list pins to twenty-six</name>
  <files>test/test_scheme_resolution.py, test/test_scheme_fidelity.py, test/test_packaging.py</files>
  <action><![CDATA[
    Make the flips of "TDD test stubs / Flips" for these three files, in place, keeping every node's name. `SHIPPED` and `EXPECTED_SCHEMES` gain the six; `test_the_parser_ships_the_twenty`, `test_extractor_schemes_list_is_the_twenty` and `test_the_root_holds_exactly_the_twenty_dash_files_the_manifest_ships` assert 26, each with the trailing comment `# 20 -> 26: P1.25a ships the six StataCorp schemes`. Update the docstrings and comments that say twenty (:55, test_scheme_fidelity.py:1-13, :116-118, :589, :663). For each flipped node append one line `Flipped: <node> -- len == 20 was wrong because dash now ships StataCorp's six internal schemes` to `<scratch>/s07/07-flips.txt`. Run the three files on the unmodified renderer and append their red nodes, under the heading `Pinned counts, red at base after the flip`, to `<scratch>/07-P1.25a-failure.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_scheme_resolution.py test/test_scheme_fidelity.py test/test_packaging.py -q -p no:cacheprovider -rf` fails exactly in: the nodes parametrized on one of the six, the three `TestTheShippedListIsOneList` nodes, the eight `TestAnUnresolvableNameIsReportedOnce` nodes, `test_fixture_is_present_and_complete`, `test_extractor_schemes_list_is_the_twenty` and the packaging pin; `grep -c "^Flipped:" <scratch>/s07/07-flips.txt` is at least 3.]]></verify>
  <done>The one-list pins asserted twenty-six names, kept their node names, and their flips were recorded with the reason.</done>
</task>

<task type="auto" id="07-03">
  <name>Extend the measured scheme tables</name>
  <files>test/test_scheme_consumption.py, test/test_scheme_grids.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    In test_scheme_consumption.py:
    - flip `test_the_twenty_are_the_ones_measured` (:1504) and `test_the_nine_are_a_subset_of_the_twenty` (:1733) to `== 26`, with the R10 comment;
    - add the "Measured 03oct2026 over StataCorp's six internal schemes" sentence of "TDD test stubs / Flips" to the docstrings of TestAChildPHashReachesWhatStatasChainReaches, TestAChildSymbolReachesWhatStatasChainReaches and TestAChildSymbolsizeReachesWhatStatasChainReaches;
    - change "nineteen schemes" to "twenty-five schemes" there.

    In test_scheme_grids.py, add the six `_GRID_TRUTH` rows (all `(True, True)`) after `"stgcolor_alt"`, with a comment that names their chains and meta's own `yesno draw_major_hgrid yes`, and flip :101 to `== 26`.

    In test_help_claims_8.py:
    - in `test_an_include_that_resolves_to_nothing_stands_s2color_in`, replace `stcolor_meta` with `w26nosuch` in the written file and in the note needle (two places);
    - flip `test_all_twenty_and_nothing_else` (:1129) to `== 26` and its class docstring to twenty-six.

    Append one `Flipped:` line per node to `<scratch>/s07/07-flips.txt`; the re-point's reason is "stcolor_meta is now shipped, so it no longer resolves to nothing". Run the three files on the unmodified renderer and append the red nodes to the failure file.
  ]]></action>
  <verify><![CDATA[`grep -c '"meta":' test/test_scheme_grids.py` prints 1; `grep -c "include stcolor_meta" test/test_help_claims_8.py` prints 0; `python3 -m pytest test/test_help_claims_8.py -q -n0 -p no:cacheprovider -k resolves_to_nothing` passes on the unmodified renderer.]]></verify>
  <done>The S3-batch tables, the grid table and the installed-tree test covered twenty-six schemes with the six's measured behaviour, and the include example pointed at a name that resolves nowhere.</done>
</task>

<task type="auto" id="07-04">
  <name>Append the parity guards and notes</name>
  <files>test/test_mode_parity.py, test/test_ci_band_style.py, test/test_adversarial_matrix.py</files>
  <action><![CDATA[
    Append the seven `CORPUS` cases and the two `MOVE_CORPUS` cases of "TDD test stubs / Guards appended" at the end of each list (R8), under the comment `# WP-30 P1.25a: StataCorp's six internal schemes`. Do not edit `ALLOWED` or `_MUST_WARN`.

    In test_ci_band_style.py, add to the module docstring and to `test_the_fixture_covers_every_scheme_and_type`'s docstring (none today) one sentence each: "ci_band_style_truth.json has no generator and covers the twenty schemes measured 24sep2026; StataCorp's six internal schemes are certified against twoway's graph object by test_wp30_truth.cscript SX-06 and test_twenty_six_schemes.py::TestTheSixDrawWhatTwowayDraws::test_the_ci_band_is_statas." Leave `len(_SCHEMES) == 20` unchanged.

    In test_adversarial_matrix.py, change :1432 "twenty" to "twenty-six". Run `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "stcolor_meta or stgcolor_mv or meta or stcolor_mv or stcoloralias"` on the unmodified renderer.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed (both modes draw s2color plus the same warning at base: the cases are guards); `grep -c "WP-30 P1.25a" test/test_mode_parity.py` prints 2.]]></verify>
  <done>The parity corpus held the six in both modes and after a move, and the ci band test said where the six are certified.</done>
</task>

<task type="auto" id="07-05">
  <name>Write the SX truth block red</name>
  <files>test/test_wp30_truth.cscript, test/test_custom_scheme.cscript, test/test_render_locate.cscript</files>
  <action><![CDATA[
    In test_wp30_truth.cscript, add the helpers of "Stata truth / Helpers" directly above `* ==== S07 P1.25a:` (python at top level; `_s07_gob` as a Stata program opening `version 19`). Write SX-01 to SX-08 of the cases table between S01's `S07 start` and `S07 end` lines, each ending `_w30_done SX-0k "<what>"`, and add the block line to the header comment.
    - No Python line inside the gate holds a brace.
    - Every file goes under the scaffold's work directory.
    - The entry `c(scheme)` is restored at the end.

    In test_custom_scheme.cscript, flip CS-12's header (:51-52) and :474 to 26. In test_render_locate.cscript, flip :385 to `loc13nsch == 26`, with a `// 20 -> 26: P1.25a` comment line above it. Record both in `<scratch>/s07/07-flips.txt`. Run the driver with `WP30_ONLY=S07` on the unmodified renderer and append the `SX-0k FAIL` lines to `<scratch>/07-P1.25a-failure.txt`. All eight are expected red: SX-05 through its no-note check (`#include S` notes "not found") and SX-06 because `_s07_ci` reports `error` for an unshipped name.
  ]]></action>
  <verify><![CDATA[`grep -c "SX-0[1-8] FAIL" <scratch>/s07/run_test_wp30_truth.log` prints 8; `grep -c "^r(9[0-9][0-9]);\|SKIP" <scratch>/s07/run_test_wp30_truth.log` prints 0 (the block ran to its end); `grep -c "nsh' == 26" test/test_custom_scheme.cscript` prints 1.]]></verify>
  <done>Stata's own drawing of the six was compared with dash's in one block that failed on the unmodified tree, and the area scripts' count pins expected twenty-six.</done>
</task>

<task type="auto" id="07-06">
  <name>Add the six to the extractor and regenerate</name>
  <files>scripts/extract_scheme_truth.py, test/fixtures/scheme_truth.json, dash-*.scheme</files>
  <action><![CDATA[
    Make TR-07.1 and TR-07.2 in scripts/extract_scheme_truth.py (`_SCHEME_TOKEN_RE = re.compile(r"^[a-z0-9_]{1,32}$")` beside `SCHEMES`; the check in `main` before `base = args.stata_base`). Run `python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json 2> <scratch>/s07/07-regen.log`. The log must show "created" for the six and "up to date" for the twenty; anything else stops the task, and nothing is hand-edited (R7).

    Check:
    - `git diff --quiet -- $(git ls-files 'dash-*.scheme')` (the twenty unchanged);
    - with `git show HEAD:test/fixtures/scheme_truth.json > <scratch>/s07/old.json`, a python comparison that every key of old.json other than `_meta` is equal in the new file, and that `_meta` differs only in `generated_utc` and `provenance`.

    Then `git add -f test/fixtures/scheme_truth.json` and `git add dash-meta.scheme dash-stcolor_meta.scheme dash-stcolor_mv.scheme dash-stcoloralias.scheme dash-stgcolor_meta.scheme dash-stgcolor_mv.scheme`.
  ]]></action>
  <verify><![CDATA[`grep -c ": created" <scratch>/s07/07-regen.log` prints 6 and `grep -c "up to date" <scratch>/s07/07-regen.log` prints 20; `ls dash-*.scheme | wc -l` prints 26; `python3 -m pytest test/test_twenty_six_schemes.py -q -n0 -p no:cacheprovider -k "Fixture or extractor_refuses or flat_and_hex"` passes.]]></verify>
  <done>The extractor listed and refused names safely, the six translations were generated from Stata's own files, and the fixture covered twenty-six schemes with the twenty earlier records unchanged.</done>
</task>

<task type="auto" id="07-07">
  <name>Grow the shipped list in three places</name>
  <files>dash_render.py, dash.ado, dash.pkg</files>
  <action><![CDATA[
    Make TR-07.4 (`_BUILTIN_NAMES`, its comment at :5697-5703, `_shipped_base`'s docstring at :6007), TR-07.5 (`_dash_shipped_schemes`'s `_dash_schemes` string and the comment at :1956, nothing else in dash.ado) and TR-07.6 (six `f dash-<name>.scheme` lines after `f dash-sttrans.scheme`). Do not edit `_resolve_path`, `can_resolve`, `_resolve_scheme_name`, `_include` or `_dash_validate_value` (S34's). Run `python3 -m pytest test/test_twenty_six_schemes.py test/test_scheme_resolution.py test/test_scheme_fidelity.py test/test_packaging.py test/test_installed_layout.py -q -p no:cacheprovider` and `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[Both runs report 0 failed; `grep -o "stgcolor_mv" dash.ado | wc -l` prints 1; `grep -c "^f dash-.*\.scheme" dash.pkg` prints 26.]]></verify>
  <done>dash.ado, the renderer and the package manifest named the same twenty-six schemes, and every regression test passed.</done>
</task>

<task type="auto" id="07-08">
  <name>Certify against Stata in both modes</name>
  <files>none</files>
  <action><![CDATA[
    Run every file changed in 07-01 to 07-07, plus test_scheme_linewidth.py, test_scheme_rendered_output.py, test_theme_aliases.py and test_ci_band_style.py: `python3 -m pytest <those files> -q -p no:cacheprovider`. Then G3: `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider`. Then three cscripts through the driver, each with its own `run_<script>.do` under `<scratch>/s07`:
    - `test_wp30_truth.cscript` with `WP30_ONLY=S07`;
    - `test_custom_scheme.cscript`;
    - `test_render_locate.cscript`.

    A red result is diagnosed against the measured values of Evidence. A failure in a file this section did not list is a pin the red list missed: flip it in place with a `Flipped:` line, never by deleting it. Afterwards check that `~/.stata19/console/stata19.rc` still holds `python_exec` (a SKIP is not a pass).
  ]]></action>
  <verify><![CDATA[Both pytest runs report 0 failed; `grep -c "SX-0[1-8] PASS" <scratch>/s07/run_test_wp30_truth.log` prints 8 and `grep -c " FAIL\|SKIP" <scratch>/s07/run_test_wp30_truth.log` prints 0; `grep -c "CS-12 PASS" <scratch>/s07/run_test_custom_scheme.log` prints 1; `grep -c "LOC-13 PASS" <scratch>/s07/run_test_render_locate.log` prints 1.]]></verify>
  <done>Stata certified that the six are accepted on every entry point and drawn as twoway draws them in the saved page and the served app, before and after a move, and every scheme test passed at twenty-six.</done>
</task>

<task type="auto" id="07-09">
  <name>Name the twenty-six schemes in the help</name>
  <files>dash.sthlp, test/test_help_conformance.py</files>
  <action><![CDATA[
    Make TR-07.10's edits only: :3300 and the six `{synopt}` rows after `{cmd:sj}`, the clauses at :3493 and :3511, and "twenty" → "twenty-six" at :3501, :3505, :3573, :3575 and :3578. Do not touch :3458, :3461-3465 or :3582-3583 (S34's) or the Grids paragraph (S15's).

    The six rows add six definition entries. Flip `test/test_help_conformance.py::TestTheParsersFoundSomething::test_the_entry_parser_cuts_the_help_into_entries` in place: `len(defs) == 339` and its message become 345, with the trailing comment `# 339 -> 345: P1.25a the six scheme rows`, and the comment block gains one sentence naming them. Measure the value on the worktree first; if S08 or S09 already moved it, write the measured value (R10). Append its `Flipped:` line to `<scratch>/s07/07-flips.txt`. Then run `python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py test/test_twenty_six_schemes.py -q -p no:cacheprovider -k "help or Help or include"` and every `test/test_help_claims_*.py` file that quotes the scheme-support lines (`grep -l "translations\|stcolor_meta" test/test_help_claims_*.py`).
  ]]></action>
  <verify><![CDATA[Those runs report 0 failed; `sed -n '3290,3600p' dash.sthlp | grep -c "twenty "` prints 1 (only :3312's "twenty percent"); `grep -c "zyx2rule colorvar hue" dash.sthlp` prints 1; `grep -c "339 -> 345: P1.25a" test/test_help_conformance.py` prints 1.]]></verify>
  <done>The help listed all twenty-six shipped schemes, described the six, and said that stcoloralias is drawn as stcolor because its zyx2rule is not read.</done>
</task>

<task type="auto" id="07-10">
  <name>Close P1.25a and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. Find the title as `WP30_OPEN["P1.25a"]`. In BUGS.md, close that entry in place (`- [x]`) and replace its Resolution with:

    `- Resolution: Fixed <ddmonyyyy> (WP-30, P1.25a). scripts/extract_scheme_truth.py lists StataCorp's six internal schemes (meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta, stgcolor_mv) and refuses a name that is not a plain token; the six dash-<name>.scheme files were generated and test/fixtures/scheme_truth.json regenerated with the twenty earlier records unchanged; dash.ado's _dash_shipped_schemes, SchemeParser._BUILTIN_NAMES and dash.pkg name the same twenty-six, so scheme(), an inherited c(scheme) and an #include of the six resolve and are drawn as twoway draws them in both renderers, before and after a filter move. stcoloralias is drawn as stcolor: its zyx2rule colorvar is not read, and twoway's colorvar() scatter is identical under both. Pinned by test/test_twenty_six_schemes.py::TestTheSixResolveInBothModes::test_by_build_scheme, test/test_twenty_six_schemes.py::TestTheInheritedSchemeIsOneOfTheSix::test_the_session_scheme_resolves, test/test_twenty_six_schemes.py::TestTheSixDrawWhatTwowayDraws::test_the_yline_is_the_schemes, test/test_wp30_truth.cscript SX-01; fixture test/fixtures/scheme_truth.json. Residual, deferred (WP-30): scheme-NAME.scheme on the ado-path, third-party and PLUS schemes, the refusal's list of names and the working-directory precedence are P1.25b (section 34); meta's draw_minor_hgrid/draw_minor_vgrid yes draws Bokeh's minor grid where twoway draws none until P1.2a (section 15) removes Bokeh's default minor ticks.`

    2. Delete the `"P1.25a"` key line from `WP30_OPEN`.

    3. In CHANGELOG.md, replace `<!-- WP-30 P1.25a -->` in place with:

    `- Six more StataCorp schemes, twenty-six in all: meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv. scheme(meta) and the others were refused r(198), and a session set to one of them (set scheme stcolor_meta) was drawn as s2color with a warning; each is now drawn as twoway draws it in both modes (stcolor_meta's solid #c10534 yline(), stgcolor_meta's 3.987 x 2.392 proportions, meta's 8-point tick labels and legend at 4 o'clock), and an #include of one of them in a scheme file of yours resolves. stcoloralias is drawn as stcolor: its zyx2rule colorvar is not read, and twoway draws a colorvar() scatter the same under both. (WP-30, P1.25a)`

    4. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`, then `git -C $WT merge --no-edit main` (expect `Already up to date.`), then one full run: `<scratch>/full_suite_queue.sh $WT <scratch>/07-full-1.log`, launched in the background and waited for on its `exit=` line (E1, E6).

    5. Stage only these files:
    - `dash_render.py dash.ado dash.pkg dash.sthlp BUGS.md CHANGELOG.md scripts/extract_scheme_truth.py`;
    - the six new scheme files;
    - `test/test_twenty_six_schemes.py test/test_scheme_resolution.py test/test_scheme_fidelity.py test/test_packaging.py test/test_scheme_consumption.py test/test_scheme_grids.py test/test_help_claims_8.py test/test_mode_parity.py test/test_ci_band_style.py test/test_adversarial_matrix.py test/test_help_conformance.py test/test_tracking_documents.py`;
    - `test/test_wp30_truth.cscript test/test_custom_scheme.cscript test/test_render_locate.cscript`;
    - any file 07-08 flipped;
    - `git add -f test/fixtures/scheme_truth.json`.

    Check `git diff --cached --name-only` against that list (G6; never CLAUDE.md, .gitignore, AGENTS.md or .ultraplan/). Write the message to `<scratch>/s07/msg.txt` in the boundary's form, run G7 (`grep -Eic 'claude|anthropic'` prints 0) before and after `git commit -F <scratch>/s07/msg.txt`, and report the sha and message to the orchestrator.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/07-full-1.log` prints `exit=0` and the pytest summary line above it names no `failed` or `error`; `git log -1 --format=%s` ends `(WP-30 P1.25a)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.25a -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.25a": "' test/test_tracking_documents.py` prints 0; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.25a was closed in BUGS.md naming tests that exist, its key was removed from WP30_OPEN, its CHANGELOG marker became the measured New line, and one green commit on wp30-s07 was ready for the merger.</done>
</task>

## Section completion criteria

- Each of meta, stcolor_meta, stcolor_mv, stcoloralias, stgcolor_meta and stgcolor_mv:
  - is accepted with rc 0 and no note on every scheme entry point and as the inherited `c(scheme)`;
  - resolves through `#include`;
  - is drawn as twoway draws it, on every surface measured in SX-02 to SX-08, in the saved page and the served app, before and after a filter move.
- stcoloralias draws exactly what stcolor draws, and the help says why.
- 26 `dash-*.scheme` files exist and are listed in dash.pkg. `scheme_truth.json` has 26 records, the twenty earlier ones unchanged, and the twenty earlier files byte-identical.
- One list of 26 in `_dash_shipped_schemes`, `_BUILTIN_NAMES`, `SCHEMES`, `EXPECTED_SCHEMES` and `SHIPPED`, held equal by `TestTheShippedListIsOneList`.
- The extractor refuses a non-token name before any write.
- `test_wp30_truth.cscript` prints SX-01..SX-08 PASS under `WP30_ONLY=S07`. CS-12 and LOC-13 PASS at 26.
- One green commit `(WP-30 P1.25a)` on `wp30-s07`, with its failure text, `Regression:`/`Flipped:`/`Fixture:`/`BUGS.md:` lines and no AI reference.
- The BUGS.md entry is closed in place, the `WP30_OPEN` key is deleted, and the CHANGELOG marker is replaced. No other entry, key, marker, copy list, map, runner or hygiene pin is touched.

## Notes

- **No renderer logic changes, on purpose.** The six resolve because the list grows. If a test fails in `_resolve_path`, `_include` or `_resolve_scheme_name`, the fix is in the data or the list, never in those functions (S34's). If it cannot be, stop and report.
- **The regenerated `_meta.provenance` sentence** changes from "schemes/<name>.scheme" to "dash-<name>.scheme". The extractor already carries the corrected text, and the fixture has been stale since commit 357c368. Name it in the commit body, so the merger does not read it as a hand edit.
- **Regenerations later in WP-30 cover 26 files** (A152). S07's `SCHEMES` order is append-only. A later regenerator never reorders it, because `scheme_truth.json`'s key order follows it and a reorder would rewrite every record's position.
- **Session scheme in the cscript.** cscript sessions run `set scheme s2color8`. SX-04 saves `c(scheme)` in a local first and restores it after each case, so later blocks keep their session.
- **python_exec hazard** (project memory). Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then exits 222, and a SKIP is not a pass. Re-check the file after 07-05 and 07-08.
- **Python inside the gated block holds no brace.** Stata scans a skipped block's braces, so the helpers sit above the header.
- **Shared files (R1-R10).**
  - **R1:** the S07 block only, with helpers above its header. Area cases CS-12 and LOC-13 are flipped in place; no runner or hygiene-pin edit.
  - **R2:** no copy-list or map change; the constant travels with its class.
  - **R3:** S07's help lines only.
  - **R4:** the one `### New` marker.
  - **R5:** the one entry and its key line.
  - **R6:** `_dash_shipped_schemes` only; its `version` line is S03's.
  - **R7:** the extractor run, never a hand patch. A conflict in a generated file is resolved by re-running the extractor on the merged tree.
  - **R8:** `CORPUS`/`MOVE_CORPUS` appended only.
  - **R9:** flips in place.
  - **R10:** the scheme-count pin moves 20 → 26 here, in every place that table lists.
- **For S15 (batch 5).** meta is the one shipped scheme with `yesno draw_minor_hgrid/draw_minor_vgrid yes`.
  - `SchemeParser.apply_to_figure` (dash_render.py:7401-7414) colours `minor_grid_line_color` from those flags. Bokeh's default ticker then draws four #505050 minor grid lines per interval on both axes, 0.2 px.
  - twoway draws a minor grid only at minor ticks, which it draws only under `xmtick()`/`xmlabel()` (both pending in dash). Measured: `p1_meta.svg` has no #505050 line.
  - "No minor ticks unless asked" must therefore remove the minor positions (a ticker with no minor ticks), not only hide the tick marks, or must gate the scheme's minor grid on minor ticks.
  - `test_twenty_six_schemes.py::TestMetasMinorGridIsHandedOn::test_dash_still_draws_metas_minor_grid` pins today's drawing. S15 flips it with a `Flipped:` line.
  - S15's `anglestyle vertical_tick` key makes meta's y labels horizontal (its `anglestyle vertical_tick horizontal`) through the regeneration S15 already runs.
- **For S34 (batch 12).**
  - The six are shipped names from S07 on, so P1.25.3's shipped-first precedence covers them.
  - The refusal's list (sub-claim e) is 26 names.
  - `test_scheme_resolution.py`'s `SHIPPED` is 26 and `_assert_unknown_warning` pins the warning's list through it.
  - CS-10 still names `zzdashtest`.
- **For S08 (same batch).** `TestTheSixDrawWhatTwowayDraws::test_metas_tick_labels_are_twoways_ratio` compares meta with s2color, so a unit change that scales both keeps it green. A change that breaks the ratio is a defect.
- **Commit body line forms** are BRIEF's, with WP-30 ids. `failed at` is `batch-3-base.txt`'s sha.
- **Notes for the closeout (S58).**
  - **DROPIN P1.25:** sub-claim b (six StataCorp schemes refused) is closed by P1.25a, with commit `<sha>`. Sub-claim c is closed for the six; the rest of c, and a, d (except `#include` of the six), e, f and g, stay with P1.25b.
  - **GAPS2-X5-c:** partly closed by P1.25a. The Tracked line names that an inherited `c(scheme)` that is one of StataCorp's six internal schemes is drawn. Third-party, PERSONAL and ado-path schemes remain for P1.25b. Append `(WP-30, GAPS2-X5-c)` to the Resolution only when S58 marks X5-c closed after S34.
  - **TWOWAY_COVERAGE_AUDIT.md:144:** "20 shipped translations" becomes "26 shipped translations".
  - **ROADMAP:** the WP-30 entry lists P1.25a and its commit. The residual "stcoloralias's `zyx2rule` (drawn as stcolor)" (manifest residual, item 25) is filed as documented, not open, because twoway's `colorvar()` scatter is identical (SX-07).
  - **AGENTS.md invariant** (E7): "the shipped scheme list is one list of twenty-six in dash.ado `_dash_shipped_schemes`, `SchemeParser._BUILTIN_NAMES`, the extractor's `SCHEMES`, dash.pkg and dash.sthlp, held equal by `test_scheme_resolution.py::TestTheShippedListIsOneList`; scheme files are generated, never hand-edited".
- **Line numbers** are `c96facd`'s. S01-S06 (batches 0-2) touch dash.ado's top guards, note sites and `version` lines, and dash_render.py's `__main__` and page assembly. Symbols are authoritative, and the six-line excerpts above are the text to find.
