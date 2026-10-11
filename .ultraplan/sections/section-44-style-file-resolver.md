# Section 44: A general resolver over Stata's style files

> Part of: WP-31 · GAPS3 rows: E10 · Risk: red · Batch: 15 · Depends on: 40 · Blocks: -- · Tasks: 4, 1 commit · Case-id prefix: U44

## Overview

**What is wrong today.** GAPS3 E10 (GAPS3.md:189): "User and third-party `*.style` files on the ado-path are not read; 57 Stata style names outside the transcribed table draw default attributes with a note; a scheme cannot redefine a linestyle/areastyle because `linestyle`, `areastyle`, `markerstyle`, `seriesstyle`, `shadestyle` keys are never read (kept silently, by ruling). `c(adoarchive)` unhandled." Evidence dash_render.py:8115 `_STYLE_TABLE`, :8663-8711 (`_STYLE_KNOWN`, `_STYLE_DEFAULT`), :9424-9492 (`_parse_lines`). Task: "A general resolver over the 161 style files and the scheme's own class directives." Register P2.55 (user `*.style` files, textboxstyle and color files), P2.74 (the 57 names), P2.73 (`c(adoarchive)`).

At `6370ca4` `SchemeParser._STYLE_TABLE` (:8115-8661) is a hand transcription of a subset of the four option classes' style files (`seriesstyle`, `markerstyle`, `areastyle`, `linestyle`): rows `(attr, "scheme"|"literal", value)` with Stata's `#` kept in keys; `_STYLE_KNOWN` (:8663-8706) lists every file name of the four classes (28 + 28 + 29 + 76 = 161 -- the "161 style files"); `_style_kind` (:11103-11130) returns `"table"`, `"known"` (Stata's but not transcribed -> default attributes with twoway's note), `"p"` or `"unknown"`; `_style_resolve` (:11225-11260) walks the table rows through `_STYLE_ATTR` with hops bounded at depth 6; `_style_leaf` (:11310-11325) falls to `_STYLE_DEFAULT` for a non-table name. The scheme's class directives (`markerstyle p1`, `linestyle dots dot` ... s2color has 792 such lines, :626-646 for markerstyle) are parsed into `_props` as any other key and read by nothing (test_unread_scheme_directives.py pins "kept, no note"). `_resolve_path`/`_ado_candidates`/`_admit` (:9095-9230) find a SCHEME file as findfile does, with the size cap, regular-file and containment guards (`_MAX_SCHEME_BYTES` 1 MiB, :8953). `c(adoarchive)`: scheme.class:152-160 reads a scheme from `_stfilearchive` when `c(adoarchive)` is 1 (a compressed ado archive, used by some installs); dash never checks it.

**After this section**, both modes: every name of the four classes resolves by READING its `style/<class>-<name>.style` file from the ado-path (BASE's `style/` directory and any user `style/` directory, the same guards as scheme files), so the 57 untranscribed names (`fpall`, `sunflower`, `plotregion`, `refline`, ...) draw their file's attributes; a user's or a third-party package's `linestyle-mine.style` on the ado-path is drawn; a scheme's `linestyle p1 mine`, `areastyle p1 foo`, `markerstyle dots star`, `seriesstyle p1 line_circle` and `shadestyle` directives redefine which file a style name points at (Stata's `scheme.style` lookup, scheme.class:40-123); the transcribed table becomes a fallback used only when no file is found (so a tree without Stata still renders); `c(adoarchive)` is measured and either handled (the archive extracted through Stata at registration into the work directory) or documented as unsupported with the measured message.

**Why one section.** E10 is one row and one red L change to `SchemeParser`; it depends on S40 (batch 13) because the resolver hands `pattern` and `symbol` attributes to `translate_lpattern(value, width_px)` and `symbol_traits`.

**Test order and commit rule.** One cycle, one commit `(WP-31 E10)`: 44-01 measures and writes the red tests; 44-02 adds the file reader and resolver; 44-03 reads the scheme's class directives and handles adoarchive; 44-04 closes and commits.

### Section decisions (binding on the executor)

- **D-44a. The file reader is the scheme reader's twin.** `SchemeParser._style_file_rows(stata_class, file)` finds `f"{stata_class}-{file}.style"` in each ado-path directory's `style/` subdirectory (U44-02 measures findfile's order: `findfile linestyle-refline.style` returns BASE/style; a user file placed in PERSONAL/style and in PERSONAL root tells which is found), with `_admit`'s guards (regular file, contained, under `_MAX_SCHEME_BYTES`), reads at most 200 lines of at most 400 bytes, and keeps only lines of the form `set <attr> <kind> <value>` where `<kind>` is `scheme` (-> `("scheme", value)`) or absent (-> `("literal", value)`); `sequence`, `label` and comment lines are skipped. The result is memoised per parser instance (dict keyed by `(class, file)`), bounded at 400 entries. A `#` in the file name stays `#` (the p-number is substituted by `_style_resolve` as today).
- **D-44b. Lookup order: scheme directive, then file, then table, then default.** `_style_rows(stata_class, name, num)`: (1) if the scheme declares `"<class> <name>"` (a class directive, `_props` key e.g. `"linestyle p1"` or the bare `"linestyle"` default when the directive's second token is absent, read through Stata's p#stub -> pstub -> p# -> p chain of `_props` keys), the directive's VALUE is the file name to read; (2) else the file `<class>-<name>.style`; (3) else `_STYLE_TABLE[class][name]`; (4) else `_STYLE_DEFAULT`. `_style_kind` gains `"file"` and `"directive"`; `"known"` disappears (every known name has a file). `_STYLE_KNOWN` stays as the set a user name is matched against before any path is built (rule 1: a style name is never used as a path unless it is in the known set OR it passes the scheme name rule `_scheme_name_ok` and the file exists on the walk).
- **D-44c. Which classes are read from files.** The four option classes plus `shadestyle` (the fill side of an areastyle: `set color`, `set intensity`, `set pattern`) and `anglestyle`/`symbolsize`/`linewidth`/`linepattern`/`symbol` leaf classes where a style file's attribute hops to them (today's `_style_leaf` reads leaf values from `_props`; a leaf FILE such as `linewidth-thick.style` `set val 0.8` is already in `_LWIDTH_RS`; the resolver reads a leaf file only for a name not in dash's tables, through the same reader). textboxstyle and color files (P2.55) are out: their readers are the textbox (S30) and colour (`_SCOLOR`) tables; listed as a residual in the hand-back (M12) with an open BUGS entry `E10b`.
- **D-44d. The scheme's class directives redefine, never add attributes.** `linestyle p1 mine` makes p1's line style the file `linestyle-mine.style`; `shadestyle p1 foo` the fill side. Directives whose value is not a file on the walk and not a table name keep today's silent-keep ruling (test_unread_scheme_directives.py stays green for them) and are noted once as twoway notes them ("named style ... not found") only when a drawn element asks for them -- U44-04 measures twoway's text for a scheme `linestyle p1 nosuch`.
- **D-44e. `c(adoarchive)` is measured, then branched.** U44-05 records `c(adoarchive)` on this machine and, if 1, what `_stfilearchive find linestyle-refline.style` returns. If the archive is in use, dash.ado extracts the needed style files at registration (`_stfilearchive extract` into the work directory) and passes that directory first in `ado_dirs`; if 0 (expected on this install), dash.ado writes `c(adoarchive)` into build_options and the renderer, seeing 1 with no extracted directory, notes once "style files inside a compressed ado archive are not read" and falls to the table -- documented in the help with the measured text (M17).

## Risk: [red] -- every styled element in every scheme goes through a new resolver that reads files

**Why.** `style_bundle` is called for every p# cycle entry, every `pstyle()`/`lstyle()`/`mstyle()`/`astyle()`/`mlstyle()`/`alstyle()`/`blstyle()`/`clstyle()` option and every CI band; a file read replaces a table lookup on a hot path; rule 1 (a user-typed name must never become a path without the known-set or name-rule check); the served app copies `SchemeParser` by source and has its own `ado_dirs` (template :48700 region passes the spec's ado dirs).

**Risk factors.** 1. Per-render file reads (161 files x 15 p-numbers): memoisation must make it one read per file. 2. A hostile style file (huge, symlinked, outside the tree, with a `set` value that is a path) -- the scheme guards apply; values are style NAMES matched against sets, never paths. 3. Table-vs-file disagreement where the transcription was wrong: a visible change pinned by test_style_names.py. 4. The served app's `ado_dirs` differ from the saved renderer's if dash.ado passes them differently. 5. Reading the 792 class directives of s2color changes nothing unless a directive's value differs from the file default -- but the shipped `dash-*.scheme` files were generated WITHOUT those directives (absent per research §11); Stata's `scheme-s2color.scheme` `markerstyle dots dots` and its 791 siblings would only matter for a user scheme that `#include`s Stata's own files (dash reads dash's copies).

**Mitigation.** 1. `TestTheReaderIsMemoised::test_one_read_per_file` (monkeypatch `open` count). 2. `TestHostileStyleFiles` (symlink, 2 MiB, path-like value, 10,000 lines) all refused or cut, no exception, no path built from a name. 3. 44-01's simulated-fix red list; every flip reasoned from the file text quoted in the docstring. 4. `TestBothModesReadTheSameFile`. 5. `TestADirectiveRedefinesAStyle` with a tmp scheme.

## Dependencies

- **Depends on: 40** (`translate_lpattern(value, width_px)`, `symbol_traits`, `_LPATTERN_MAP` keys = file names).
- **Blocks: none.**
- **Parallel batch: 15**, merge order S44, S45, S46. **Can run with S45 and S46**: S45 edits the tick model, `_dash_refinish_axes`, `_DASH_AXIS_FINISH_JS` and dash.ado's axis probe; S46 edits lpoly, function points, the recast tagging and `_FILTER_JS`'s histogram/kdensity branches. None touches `SchemeParser`, `style_bundle` or the style tables. S44 edits dash.ado only for D-44e's build-option line (no shared program with S45/S46: S45 edits `_dash_plot`'s axis block, S46 `_dash_fn_points` -- S44's line goes beside `dp` in the build-options writer, which S43 edited in batch 14).

## Evidence

### The tables and the resolver

```python
8115    _STYLE_TABLE: "dict[str, dict[str, tuple]]" = {
8116        "seriesstyle": {
8117            "ci": (
8118                ("marker", "scheme", "ci"),
...
8663    _STYLE_KNOWN: "dict[str, frozenset]" = {
8664        "seriesstyle": frozenset((
...
8708    _STYLE_DEFAULT: "dict[str, str]" = {
8709        "seriesstyle": "p1", "markerstyle": "p1",
8710        "linestyle": "foreground", "areastyle": "background"}
11103    _STYLE_P_RE = re.compile(r"p([1-9]|1[0-5])([a-z_]*)")
11105    def _style_kind(self, stata_class: str, name: Any) -> str:
11106        """What *name* is in Stata class *stata_class*: ``"blank"``,
11107        ``"p"`` (p1-p15, S32's bundles), ``"table"`` (a name of
11108        ``_STYLE_TABLE``), ``"known"`` (a Stata style file outside the
11109        table, D-36c) or ``"unknown"``.
11233        rows = self._STYLE_TABLE[stata_class][file]
11234        attrs = self._STYLE_ATTR[stata_class]
11320            name = self._STYLE_DEFAULT.get(sub, "p1")
```
`style_bundle(cls, name)` docstring :11040-11060; `_style_leaf` :11310; the fallback at :11390-11402. Fixtures: `test/fixtures/style_name_truth.json` (test_style_names.py:41; `_meta.style_files`/`style_known` at :654-662 hold the file list the table was transcribed from) and `scheme_truth.json`.

### The style files (B = /Applications/StataNow/ado/base)

913 files in `B/style/`; the four classes: linestyle 76, areastyle 29, markerstyle 28, seriesstyle 28 (= 161). Forms:

```
--- markerstyle-p#.style          --- linestyle-p#area.style
sequence 4001                     sequence 4401
set symbol     scheme p#          set width    scheme p#area
set size       scheme p#          set color    scheme p#arealine
set fillcolor  scheme p#markfill  set pattern  scheme p#area
set linestyle  scheme p#mark      set align    scheme p#area
set angle      scheme p#mark
...
--- areastyle-p#area.style        --- linestyle-refline.style
set linestyle   scheme p#area     set width    scheme refline
set shadestyle  scheme p#area     set color    scheme refline
                                  set pattern  scheme refline
--- markerstyle-refmarker.style: `set angle scheme` (two tokens: the class default)
--- anglestyle-stdarrow.style: `set val 28.64` (a leaf literal)
```
Every line is `set <attr> [scheme] <value>` with `sequence`/`label` headers; a two-token `set angle scheme` means the class default (as `_parse_lines` treats a two-token scheme line, :9432-9434).

### Stata's lookup

`B/s/scheme.class:40-123` (`style` program): `scheme p#stub` tries `p#stub`, `pstub`, `p#`, `p`, then the bare id; not found -> `(note: <class> <id> not found in scheme, default attributes used)`. The class directives of `scheme-s2color.scheme` (:626-646 markerstyle; 792 lines over the five classes) give each named style its FILE. `c(adoarchive)` branch: scheme.class:152-160 (`_stfilearchive find scheme-<name>.scheme` then `extract`).

### Tests pinning today's behaviour

- test_style_names.py::TestKinds (:172, asserts `"known"` for the 57 names), ::TestUnknown (:147), ::TestTheNote (:186, the note for a known-but-untranscribed name), ::TestTheFallback (:317), ::TestTheTableNames (:89; the table equals `_meta.style_files` -- after S44 the table is a fallback and the test pins the FILE set instead).
- test_unread_scheme_directives.py::TestUnreadDirectivesAreRetained (:73), ::TestNoNoteForUnreadDirectives (:126), ::TestTheHelpSaysTheyAreKept (:161): the five class directives leave the "unread" set; the help sentence changes.
- test_scheme_lookup.py::TestTheGuards (:350): extended to style files, not flipped.

## User stories

- US-44.1 As a Stata user, I want `lstyle(refline)`, `pstyle(fpall)`, `mstyle(sunflower)` and every other Stata style name drawn with its file's attributes, as twoway draws them.
- US-44.2 As a package author, I want my `linestyle-mine.style` on the ado-path to be drawn when a do-file says `lstyle(mine)`.
- US-44.3 As a scheme author, I want `linestyle p1 mine` in my scheme to redefine p1's line.
- US-44.4 As a maintainer, I want no user-typed name ever to become a file path.

## Business requirements

- BR-44.1 Every name of the 161 files draws its file's attribute chain in both modes; the 57 "default attributes" notes disappear.
- BR-44.2 A user style file on the ado-path (in the directory findfile searches, measured) is read with the scheme guards; a hostile file is refused or cut without an exception.
- BR-44.3 A scheme's `linestyle`/`areastyle`/`markerstyle`/`seriesstyle`/`shadestyle` directive redefines the named style; an unresolvable directive keeps today's silent-keep rule until drawn, then twoway's measured note.
- BR-44.4 `c(adoarchive)` is handled or documented per the measurement.
- BR-44.5 A tree without Stata's files (CI) still renders through the table fallback.
- BR-44.6 Build time: reading the files adds under 50 ms per render on this machine (`test_estimator_cost.py`-style bound in test_style_files.py, marked `slow`).

## Technical requirements

- TR-44.1 `SchemeParser._STYLE_FILE_CLASSES = ("seriesstyle", "markerstyle", "areastyle", "linestyle", "shadestyle")`; `_STYLE_FILE_MAX_LINES = 200`, `_STYLE_FILE_MAX_LINE_BYTES = 400`, `_STYLE_FILE_MEMO_MAX = 400` class constants after `_MAX_SCHEME_NAME_CHARS` (:8956).
- TR-44.2 `SchemeParser._style_dirs()`: `[os.path.join(d, "style") for d in (self._ado_dirs or default dirs)]` in `_ado_candidates`' order (plus the measured extra form if findfile also looks in `d` itself); `_style_file_path(stata_class, file)`: the first existing path, admitted by `_admit(root, path, safe)` (reused as is); None when none.
- TR-44.3 `_style_file_rows(stata_class, file) -> tuple | None`: read through `_read_scheme_lines`'s bounded reader (reuse it; it takes a path and the caps), parse `set` lines per D-44a into `(attr, kind, value)` with `attr`, `value` matched by `^[A-Za-z_][A-Za-z0-9_#]{0,40}$` (else the line is skipped and the file noted once); memoised in `self._style_memo`.
- TR-44.4 `_style_rows(stata_class, name, num) -> tuple`: D-44b order; a directive key is `f"{stata_class} {name}"` through the p-chain helper `_first_present` (:10746 region already used for `intensity p#bar` chains); its value is a file name checked against `_STYLE_KNOWN[stata_class] | <names found on the walk>` and the name rule before `_style_file_rows`.
- TR-44.5 `_style_resolve` (:11225) reads `rows = self._style_rows(stata_class, file, num)` in place of the table lookup; `_style_kind` returns `"file"` for a name with a file and `"table"` only when no file exists; `_style_leaf`'s default path unchanged. `shadestyle` rows (`color`, `intensity`, `pattern`) are read by the existing shadestyle shaper (:11325 region) from the file instead of the table.
- TR-44.6 Leaf hops to `anglestyle`/`symbolsize`/`linewidth`/`linepattern`/`symbol` names outside dash's tables read `<class>-<name>.style`'s `set val`/`set pattern` through the same reader (D-44c) and convert with `OptionTranslator.resolve_size`/`translate_lpattern(value, width_px)`/`symbol_traits`.
- TR-44.7 dash.ado: `"adoarchive":"`c(adoarchive)'"` into build_options (beside `dp`); D-44e's extraction program `_dash_style_archive` (version 19) only if the measurement says the archive is in use on any supported install -- else the one build-option line and the renderer's note.
- TR-44.8 Both renderers: all members of `SchemeParser` (copied by source); no copy-list entry; the served template passes `ado_dirs` already (confirm at :48700 region; the test pins both modes read the same file). function_test_map.py: `SchemeParser._style_dirs`, `._style_file_path`, `._style_file_rows`, `._style_rows`. program_coverage_map.py: `_dash_style_archive` if added (`test_wp31_truth.cscript:U44-05`).
- TR-44.9 Tests and docs: test_style_names.py's `_meta.style_files` pin becomes the FILE set (regenerated fixture through `scripts/extract_style_name_truth.do` -- re-run, never hand-patched, R7); test_unread_scheme_directives.py's unread set drops the five classes; dash.sthlp scheme paragraph: "the five class directives are read; a style name is looked up in your ado-path's `style/` directories as Stata looks it up; `c(adoarchive)` ..."; TWOWAY_COVERAGE_AUDIT.md:112/:114/:116 ("named style coverage remains incomplete") gain `[WP-31 E10: corrected -- every Stata style file read]`.


### Reference TR-44.A: the untranscribed names at 6370ca4 (key-set difference `_STYLE_KNOWN` minus `_STYLE_TABLE`, computed 10oct2026; 61 names, of which the four `p#` entries are S32's bundles -> GAPS3's 57)

- seriesstyle (19): dendrogram editor fpall fpallarrow fpallci fpci fpciarrow fpcumul fpes fpesinside fpgrp fpgrparrow fpgrpci fpgrps ilabel line_circle matrix p#pie (+ p#)
- markerstyle (21): dots ed_arrow editor fpall fpallarrow fpallci fpci fpciarrow fpcumul fpes fpesinside fpgrp fpgrparrow fpgrpci fpgrps ilabel matrix refmarker star sunflower (+ p#)
- areastyle (20): boxed_bg clegend_inner clegend_outer clegend_preg dendrogram dotchart fpall fpciarea fpgraph fpgrp fpspacer legend matrix_plotregion outline p#pie plotregion sunflower sunflowerdb sunflowerlb (+ p#)
- linestyle (1): p# only (75 of 76 transcribed)

The extractor lists them by this rule at run time (import `dash_render` in its python block), so the fixture holds whatever the batch-15 base has.

### Reference TR-44.B: attribute chains the resolver must reproduce (read from the files; the test compares the drawn element with the fixture, these rows show the executor the shape)

| name (class) | file rows | chain |
|---|---|---|
| refline (linestyle) | `width scheme refline`, `color scheme refline`, `pattern scheme refline`, `align scheme refline` | `linewidth refline` -> s2color value (or `linewidth` default), `color refline`, `linepattern refline` |
| refmarker (markerstyle) | `symbol scheme refmarker`, `size scheme refmarker`, `fillcolor scheme refmarker`, `linestyle scheme refmarker`, `angle scheme` (class default), `backsymbol scheme none` ... | `symbol refmarker`, `symbolsize refmarker`, `color refmarker`, linestyle hop to the FILE `linestyle-refmarker.style` |
| fpall (seriesstyle) | `marker scheme fpall`, `line scheme fpall`, `area scheme fpall`, `label ...` | each a hop to `markerstyle-fpall.style`, `linestyle-fpall.style`, `areastyle-fpall.style` |
| p#area (areastyle) | `linestyle scheme p#area`, `shadestyle scheme p#area` | `linestyle-p#area.style` (width p#area -> p, color p#arealine -> p#, pattern p#area), `shadestyle-p#area.style` |
| plotregion (areastyle) | `linestyle scheme plotregion`, `shadestyle scheme plotregion` | the plot region's own line and shade |

`_STYLE_ATTR` (the attribute -> sub-class map used by `_style_resolve`, :11234) already names `linestyle`/`shadestyle`/`marker`/`line`/`area` hops; a hop whose target FILE exists is read through `_style_file_rows`; a hop to a leaf class (`symbol`, `symbolsize`, `linewidth`, `linepattern`, `color`, `intensity`, `anglestyle`) reads `_props` through the p-chain as today.

### Reference TR-44.C: the reader and the lookup (TR-44.3, TR-44.4)

```python
    _STYLE_SET_RE = re.compile(
        r"^\s*set\s+([A-Za-z_][A-Za-z0-9_]{0,40})(?:\s+(scheme))?(?:\s+([A-Za-z_][A-Za-z0-9_#]{0,40}))?\s*$")

    def _style_file_rows(self, stata_class, file):
        """Rows ``(attr, kind, value)`` of style/<class>-<file>.style on the
        walk, or None.  Memoised; bounded; the scheme reader's guards."""
        key = (stata_class, file)
        memo = self.__dict__.setdefault("_style_memo", {})
        if key in memo:
            return memo[key]
        rows = None
        path = self._style_file_path(stata_class, file)
        if path is not None:
            rows = []
            for line in self._read_scheme_lines(path, self._STYLE_FILE_MAX_LINES,
                                                self._STYLE_FILE_MAX_LINE_BYTES):
                m = self._STYLE_SET_RE.match(line)
                if m is None:
                    continue
                attr, is_scheme, val = m.group(1), m.group(2), m.group(3)
                if is_scheme:
                    rows.append((attr, "scheme", val if val is not None else ""))
                elif val is not None:
                    rows.append((attr, "literal", val))
            rows = tuple(rows)
        if len(memo) < self._STYLE_FILE_MEMO_MAX:
            memo[key] = rows
        return rows

    def _style_rows(self, stata_class, file, num):
        """D-44b: a scheme class directive, then the style file, then the
        transcribed table, then None (the caller falls to the default)."""
        directive = self._first_present(tuple(
            f"{stata_class} {k}" for k in self._p_chain(file, num)))
        if directive:
            target = self._props.get(directive, "").strip()
            if target and target != file and self._style_name_ok(stata_class, target):
                rows = self._style_file_rows(stata_class, target)
                if rows is not None:
                    return rows
                if target in self._STYLE_TABLE.get(stata_class, {}):
                    return self._STYLE_TABLE[stata_class][target]
        rows = self._style_file_rows(stata_class, file)
        if rows is not None:
            return rows
        return self._STYLE_TABLE.get(stata_class, {}).get(file)
```
`_style_name_ok(stata_class, name)`: `name in self._STYLE_KNOWN[stata_class] or (self._scheme_name_ok(name) and len(name) <= 64)`; `_p_chain(file, num)`: for `p#stub` the four keys `p<num><stub>`, `p<stub>`, `p<num>`, `p` (scheme.class:40-52), else `(file,)`. `_read_scheme_lines(path, max_lines, max_bytes)`: if the existing reader takes no caps, add two keyword arguments defaulting to today's limits.

### Verbatim TR-44.D

- function_test_map.py entries: `"SchemeParser._style_dirs": "test/test_style_files.py::TestTheWalk::test_order_is_findfiles"`, `"SchemeParser._style_file_path": "...::TestTheWalk::test_user_root_vs_style_dir"`, `"SchemeParser._style_file_rows": "...::TestTheReaderIsMemoised::test_one_read_per_file"`, `"SchemeParser._style_rows": "...::TestDirectives::test_redefines[saved]"`.
- dash.sthlp scheme paragraph sentence: `A style name -- {cmd:lstyle(refline)}, {cmd:pstyle(fpall)}, your own {cmd:lstyle(mine)} -- is looked up as Stata looks it up: a {cmd:linestyle}, {cmd:areastyle}, {cmd:markerstyle}, {cmd:seriesstyle} or {cmd:shadestyle} directive in the scheme first, then the {cmd:style/<class>-<name>.style} file in your ado-path's style directories, with the same size and location checks as a scheme file.` plus the adoarchive sentence per D-44e.
- CHANGELOG Results line: `- 57 Stata style names (fpall, refline, plotregion, sunflower, ...) drew default attributes with a note; they draw their style file's attributes, and a scheme's class directives and your own *.style files are read (WP-31, E10)`.
- BUGS.md E10b open form: `- [ ] Title: textboxstyle and color-*.style files on the ado-path are not read` / `File Names and Line Numbers: dash_render.py _dash_textbox (S30), _SCOLOR colour table` / `Description: GAPS3.md E10 (P2.55), re-verified at 6370ca4: ...` / `Suggested fix: extend SchemeParser._style_file_rows to the textboxstyle and color classes with readers for their attributes` / `Resolution: Not fixed because WP-31 section 44 read the four option classes and shadestyle only. Graded S3 (WP-31): a user textbox or colour style falls to a note and the default.`

## Boundaries

- No textboxstyle or color-*.style reading (D-44c; residual `E10b`).
- No change to `translate_lpattern`/`symbol_traits` (S40's) or to `_apply_*` appliers.
- No CMYK/HSV (M7); the scheme `_parse_lines` grammar unchanged.
- No new dependency; no `shell=True`; no path from a user name without the known-set or name-rule check.

## Stata truth

Script `scripts/extract_style_files_truth.do` -> `test/fixtures/style_files_truth.json`.

| Key | Probe | Recorded |
|---|---|---|
| `find.<class>-<name>` for 6 names (linestyle-refline, markerstyle-refmarker, areastyle-plotregion, seriesstyle-fpall, shadestyle-p#area? no: `shadestyle-foreground`, linestyle-p#area as `linestyle-p#area`) | `findfile <file>` | the path returned |
| `find.user_root`, `find.user_style` | write `linestyle-u44a.style` into `c(sysdir_personal)` root and `linestyle-u44b.style` into `c(sysdir_personal)style/`; `findfile` each | found or not; path |
| `draw.<name>` for the 57 untranscribed names (from `_STYLE_KNOWN` minus `_STYLE_TABLE` keys, listed in the do-file by class with the option that takes the class: `lstyle()`, `mstyle()`, `astyle()`, `pstyle()`) | `scatter mpg weight, <opt>(<name>)` (area names on `area mpg weight, sort`) + SVG | rc, note text, the element's stroke/fill/width/pattern/symbol |
| `user.lstyle` | `linestyle-u44b.style` with `set width thick`, `set color red`, `set pattern dash`; `line mpg weight, lstyle(u44b)` | stroke colour, width, dasharray |
| `scheme.redefine` | `scheme-u44.scheme`: `#include s2color`, `linestyle p1 u44b`; `line mpg weight, scheme(u44)` | stroke |
| `scheme.redefine_missing` | `linestyle p1 nosuch`; `line mpg weight, scheme(u44m)` | rc, note text |
| `adoarchive.value`, `adoarchive.find` | `c(adoarchive)`; if 1, `_stfilearchive find linestyle-refline.style` | values |
| `all.files` | `dir "`c(sysdir_base)'style/*.style"` listed by class | the 161 names (and the whole 913 for the record) |

Truth block `* ==== S44 E10: Style file resolver ====`: U44-01 fixture stamped, 161 names; U44-02 findfile order equals dash's `_style_dirs()` order (python helper prints `_style_file_path` for the six files); U44-03 for each of the 57 names dash's drawn attributes in both modes equal `draw.*` (within 0.05 px for widths; colours exact; dash arrays per S40's unit); U44-04 `scheme.redefine` and `scheme.redefine_missing`: dash's drawing and note equal twoway's (note text through `cert_log_has`); U44-05 adoarchive per D-44e; U44-06 a hostile `linestyle-u44x.style` (a symlink to /etc/hosts; a 2 MiB file) is refused with dash's one note and the default drawn, rc 0.

## TDD test stubs

### `test/test_style_files.py` (new)

- Test: fixture stamped, 161 names -- `TestTheFixture::test_meta`, `::test_161` (guard).
- Test: `_style_dirs()` order equals findfile's -- `TestTheWalk::test_order_is_findfiles`, `::test_user_root_vs_style_dir` (red: AttributeError).
- Test: every one of the 57 names draws the fixture's attributes in both modes -- `TestEveryKnownNameDraws::test_name[mode-class-name]` (red: default attributes).
- Test: a tmp ado dir with `linestyle-mine.style` is drawn through `lstyle(mine)` in both modes -- `TestUserFiles::test_drawn[mode]` (red).
- Test: hostile files: symlink out, 2 MiB, 10,000 lines, a value `../../x`, a name `a/b` -- refused/cut, one note, no exception, no path built (monkeypatch `os.path.exists` to record every path asked for and assert each is under a walk directory) -- `TestHostileStyleFiles::test_*` (red/guard).
- Test: one read per file per parser -- `TestTheReaderIsMemoised::test_one_read_per_file` (red).
- Test: a scheme `linestyle p1 mine` redefines p1; `linestyle p1 nosuch` keeps p1 and notes once when drawn -- `TestDirectives::test_redefines[mode]`, `::test_missing_notes_as_twoway[mode]` (red).
- Test: `shadestyle p1 foo` redefines the fill side -- `::test_shadestyle[mode]` (red).
- Test: with no Stata files on the walk (tmp empty ado dir), the table fallback renders p1-p15 and `ci` as today -- `TestTheFallback::test_table_when_no_files` (guard).
- Test: both modes read the same file (served `ado_dirs` equal saved) -- `TestBothModesReadTheSameFile::test_paths` (red).
- Test: build time bound -- `TestCost::test_under_50ms_per_render` (slow; red if memoisation missing).
- Test: adoarchive branch -- `TestAdoArchive::test_measured_branch` (red).

### Flips

test_style_names.py::TestKinds (`"known"` -> `"file"`), ::TestTheNote (no note for a file name), ::TestTheTableNames (pins the file set), ::TestTheFallback (table only without files); test_unread_scheme_directives.py (the five classes leave the set; help sentence). Reasons: "Stata's style files are read (E10)".

### cscript: U44-01..U44-06. Parity: `CORPUS` "lstyle(refline)", "pstyle(fpall)", "scheme with linestyle p1 redefined".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Walk order | pytest + U44-02 | style_files_truth.json | n/a |
| 57 names | pytest + U44-03 | same | yes |
| User files, hostile files | pytest + U44-06 | -- | yes |
| Directives | pytest + U44-04 | same | yes |
| adoarchive | U44-05 + pytest | same | n/a |
| Fallback, cost, memo | pytest | -- | n/a |

AC-44.1 every fixture name drawn; AC-44.2 guards hold; AC-44.3 directives redefine; AC-44.4 adoarchive branch recorded; AC-44.5 fallback renders; AC-44.6 one green commit.

## Tasks

**Commit boundary.** 44-01..44-04 form the one E10 commit, subject `Resolve every Stata style name through its style file and the scheme's class directives (WP-31 E10)`. `$WT=<worktrees>/wp31-s44`.

<task type="auto" id="44-01">
  <name>Measure findfile and the 57 names, write failing tests</name>
  <files>scripts/extract_style_files_truth.do, test/fixtures/style_files_truth.json, test/test_style_files.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s44 at the batch-15 base; S40 is in it: `grep -c "def lpattern_formula" dash_render.py` prints 1). Create the extractor from the table (head as scripts/extract_style_name_truth.do, which already lists the style files; the 57 names computed in the do-file's python block as `_STYLE_KNOWN - _STYLE_TABLE keys` read from dash_render.py by import; user files written under `c(sysdir_personal)` and erased at the end; `_meta` five keys). Run through the slot; `git add -f` the fixture. Create test/test_style_files.py with the stub classes (every attribute expectation from the fixture). Run it `-q -n0 -p no:cacheprovider -rf > <scratch>/s44/44-01.log`; write `<scratch>/44-01-failure.txt`. Write U44-01..U44-06 in the S44 block; run (`WP31_ONLY=S44`); append FAIL lines. Simulated fix (TR-44.1..TR-44.6 on a scratch copy): run test_style_names.py, test_unread_scheme_directives.py, test_scheme_consumption.py, test_scheme_lookup.py -> `<scratch>/s44/44-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/style_files_truth.json'));print(sorted(d['_meta']), len(d['all.files']['linestyle'])+len(d['all.files']['areastyle'])+len(d['all.files']['markerstyle'])+len(d['all.files']['seriesstyle']), sum(k.startswith('draw.') for k in d))"` prints the five keys, 161 and 57; `grep -c FAILED <scratch>/s44/44-01.log` is at least 60; `test -s <scratch>/44-01-failure.txt`.]]></verify>
  <done>findfile's order, every untranscribed name's drawn attributes, the user-file and directive behaviours and the adoarchive state were recorded, and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="44-02">
  <name>Read style files with the scheme guards</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-44.1 to TR-44.3, TR-44.5 (file before table; `"file"` kind) and TR-44.6, with `_style_dirs()`'s order taken from `find.*` (D-44a). Add the four function_test_map.py entries. Run test_style_files.py (TestTheWalk, TestEveryKnownNameDraws, TestUserFiles, TestHostileStyleFiles, TestTheReaderIsMemoised, TestTheFallback, TestBothModesReadTheSameFile, TestCost green; TestDirectives, TestAdoArchive still red), test_scheme_lookup.py::TestTheGuards, test_csp.py, test_function_test_map.py, and U44-02/03/06 through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_style_files.py -k "not Directives and not AdoArchive" test/test_scheme_lookup.py test/test_function_test_map.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U44-0[236] PASS" <scratch>/s44/run_test_wp31_truth.log` prints 3.]]></verify>
  <done>Every Stata style name of the four classes and every user style file on the walk is read with the scheme guards, memoised, in both modes, with the table as the file-less fallback.</done>
</task>

<task type="auto" id="44-03">
  <name>Read the scheme's class directives and the adoarchive branch</name>
  <files>dash_render.py, dash.ado, test/test_unread_scheme_directives.py</files>
  <action><![CDATA[
    Apply TR-44.4 (directive before file; the p-chain through `_first_present`) and TR-44.7 per `adoarchive.*` (D-44e). Flip test_unread_scheme_directives.py's set and help sentence pins and the test_style_names.py nodes of 44-flips.txt in place. Run test_style_files.py whole, test_unread_scheme_directives.py, test_style_names.py, test_scheme_consumption.py, test_program_coverage_map.py (if a program was added), and U44-04/05.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_style_files.py test/test_unread_scheme_directives.py test/test_style_names.py test/test_scheme_consumption.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U44-0[45] PASS" <scratch>/s44/run_test_wp31_truth.log` prints 2.]]></verify>
  <done>A scheme's linestyle, areastyle, markerstyle, seriesstyle and shadestyle directives redefine the named styles as Stata's lookup does, and c(adoarchive) is handled or documented per the measurement.</done>
</task>

<task type="auto" id="44-04">
  <name>Regenerate the style-name fixture, document, close E10 and commit</name>
  <files>dash.sthlp, BUGS.md, GAPS3.md</files>
  <action><![CDATA[
    Re-run scripts/extract_style_name_truth.do through the slot so `_meta.style_files` is the file set (R7; `git add -f`); apply TR-44.9's help and audit edits; open the residual entry `E10b` (textboxstyle/color files; BRIEF's open form, Graded S3) in BUGS.md; close E10's entry (Resolution names D-44b and the residual), rewrite `E10 Tracked` as "Partly closed in WP-31 (section 44, commit <sha>): the four classes, shadestyle, user files, directives, adoarchive; open: textboxstyle and color-*.style files (BUGS.md "<E10b title>")"; replace the E10 marker (Results line: "57 Stata style names: default attributes with a note -> their file's attributes"). Run test_style_files.py, test_style_names.py, test_help_conformance.py, test_tracking_documents.py, test_fixtures_are_committed.py, test_mode_parity.py -k "lstyle or pstyle", and the S44 block once more. Commit `(WP-31 E10)`; grep the message for tooling names (0). Write `<scratch>/s44/handback.txt` (sha; D-44c's residual and D-44e's branch for ratification; the measured findfile order).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_style_files.py test/test_style_names.py test/test_help_conformance.py test/test_tracking_documents.py test/test_fixtures_are_committed.py -q -p no:cacheprovider` ends 0 failed; `grep -c FAIL <scratch>/s44/run_test_wp31_truth.log` prints 0; `git log -1 --format=%s` ends `(WP-31 E10)`; `grep -c '^- \*\*E10 Tracked:\*\* Partly closed' GAPS3.md` prints 1; `test -s <scratch>/s44/handback.txt`.]]></verify>
  <done>The style-name fixture pins the file set, the help and audit describe the resolver, E10 is closed with its one named residual, and the commit landed green.</done>
</task>

## Section completion criteria

- The 57 names and user files draw their files' attributes in both modes; hostile files refused; one read per file; directives redefine; adoarchive measured and branched; fallback intact.
- One green commit; BUGS.md E10 closed, E10b open (Graded); Tracked line "Partly closed"; marker; two fixtures stamped and named.

## Notes

- **Rule 1 path:** the only strings that become paths are `f"{stata_class}-{file}.style"` where `stata_class` is from `_STYLE_FILE_CLASSES` and `file` passed `_STYLE_KNOWN` or `_scheme_name_ok` (no blank, quote, slash, backslash, colon, `..`); `_admit` then checks containment and size.
- **Renderer order:** `SchemeParser.__init__` receives `ado_dirs` in both modes (saved from the spec; served from the template's spec read) -- `_style_dirs()` must read `self._ado_dirs` lazily, after `__init__` set it (:8976).
- **Copy lists (R2):** none (class members). **R6:** `version 19`; `_needed` untouched (no Mata). **R3:** the scheme paragraph and the style-name sentences only. **R4/R5:** one marker, one closed entry plus one opened. **R7:** two fixtures. **R8:** corpus appended. **R9:** flips. **R12:** no hot function.
- **For S56 (help reconciliation):** the Differences count may change by one (the 57-name note is gone; the textboxstyle/color residual stays).
- **python_exec hazard** as S40.
- **Decisions for ratification:** D-44c (textboxstyle/color files deferred as E10b), D-44e's branch.
