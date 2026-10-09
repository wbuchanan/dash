# Section 34: Stata's scheme lookup along the ado-path (P1.25 part b, M7)

> Part of: WP-30 · Items: P1.25 part b (entry `P1.25b`; extra entry P1.25.6, added closed, A146) · Risk: yellow · Batch: 12 · Depends on: 06, 07, 30, 33 · Blocks: — · Tasks: 13, 1 commit · Case prefix: SP

## Review amendments

- Fixed (blocker): the truth block header was not S01's stub header. It now reads `* ==== S34 P1.25b: Stata's scheme lookup along the ado-path ====` (TR-01.6), the line `TestTheWp30TruthScript` checks.
- Fixed (major): the commit body's `BUGS.md:` line carried a placeholder. It now holds the Appendix B title verbatim.
- Fixed (major, security): `_admit` checked containment on the path, then `_parse_lines` opened it again, so a link swapped into the directory between the two steps would have been read. `_admit` now records the checked file's (device, inode), `_read_scheme_lines` refuses a mismatch after `fstat`, and the new test `test_a_swap_after_the_check_is_not_read` covers it (TR-34.6, TR-34.7, TR-34.20).
- Fixed (major, security): the ado-path JSON passed through `c_local` and the master_json lines unprotected, so a directory name holding a backtick or `$` would have been expanded again as a macro. The JSON now goes through `macval()` at every expansion, and Mata skips directories that hold a backtick, `$`, a quote or a control character (TR-34.14, TR-34.15).
- Fixed (minor): the Python name rule now refuses C1 controls too, matching the Stata gate's `\p{Cc}`.
- Fixed (minor): Q1 is now marked as a Maintainer question with a recommendation. S35's reviewer confirmed the hunks are disjoint.
- Rejected: refusing `scheme(nosuchthing)` and `scheme(my theme)` r(198) where twoway notes and draws s2color, as breaking M5. M5's item list does not include P1.25. P1.25.4 keeps the name guard under M7, and the unfound refusal is today's behaviour, which the help documents.
- Rejected: following links out of a directory as twoway does. M7's per-directory containment is binding, and this is kept as a documented difference.
- Checked: no batch-12 partner edits `SchemeParser._resolve_path`, `resolve_or_fallback`, `_include`, `_parse_lines`, `can_resolve`, `DashRenderer._scheme_for`/`_make_figure`/`__init__`, `ServerAppBuilder.__init__`, `_resolve_scheme_name`, or dash.ado's gate and writers. S36 edits only `style_bundle`, its table, the extractor and the generated files. In `_glyph_layer_lines`, S35's tuple anchors and S34's scheme block are disjoint. S34 adds no copy-list entry (R2).
- (cross-file pass) 34-13 verify: added the key-deletion check `grep -c '^    "P1.25b": "' test/test_tracking_documents.py` → 0 (S01 TR-01.10.1).
- The review pass applied both lenses.
- Ratification row 4 (ratification 06oct2026, CHANGED: no unread-directive note): Risk 5, Dependencies (S33), TR-34.13's per-graph builder bullet and `_dash_graph_scheme`, TR-34.16's S33 neighbour, Boundaries and the Test plan row no longer mention S33's read-recording, allow-list or note; an ado-path scheme's directives are retained like any other (S33's D-33d), with no note.
- `TestThirdPartySchemes::test_an_unread_allow_listed_key_is_noted_once[mode]` is replaced by `::test_an_ado_path_schemes_unread_directives_are_kept_silently[mode]` (retained in `_props` and the served dict, no note, both modes); the test count is unchanged (ratification 06oct2026).

## Overview

`scheme(NAME)` is looked for in two places only: dash's own `dash-<name>.scheme` translations and `NAME.scheme` in the working directory. Stata looks much further. `set scheme` and `twoway ..., scheme()` run `findfile scheme-NAME.scheme` and then `findfile NAME.scheme` (BASE/s/scheme.class:172-173). Each walks the whole ado-path: BASE, SITE, the working directory, PERSONAL, PLUS, OLDPLACE and any added directory, each with its first-letter subdirectory. GAPS2 X5 states the measured symptom: "A scheme on the ado-path is therefore refused with r(198) when named. When it is inherited through `c(scheme)`, s2color is drawn with a note." Research p1-25 re-measured it at `c96facd`:
- `dash scatter mpg weight, scheme(w30x)` with `scheme-w30x.scheme` in the working directory is refused r(198), and twoway draws it red.
- After `set scheme w30p` (a file in an `adopath +` directory), an unschemed dashboard is drawn s2color (`#eaf2f3`) with a warning, in both modes.
- An `#include` has the same limits.
- The refusal names no scheme.
- A working-directory `s1mono.scheme` overrides the shipped s1mono, which twoway never allows, because BASE comes first.
- The help's remedy, "copy the PLUS file into the working directory", fails: the copy is still named `scheme-NAME.scheme`.

After this section, dash finds a scheme it does not ship exactly as Stata finds it:
- `scheme-NAME.scheme`, then `NAME.scheme`, in each ado-path directory in Stata's order, each directory followed by its first-letter subdirectory;
- for `scheme()` on every entry point, for a graph's own `scheme()`, for the session's `c(scheme)` and for every `#include`;
- with the twenty-six shipped names first, as twoway's BASE is (M7, register P1.25.1, P1.25.3).

A theme name given to `scheme()` is the file of that name when Stata finds one (P1.25.5). Every file read is a scheme found by name, never by path. It passes per-directory realpath containment, is a regular file of at most 1,048,576 bytes, and is parsed as data. The refusal lists the twenty-six names and the six themes. The help states twoway's rule.

This section also carries the register's fold-in P1.25.6 (A80, IR-17, ratification item 28), with its own closed BUGS.md entry (A146). Each graph's own `scheme()` is resolved by one rule in both renderers, and the served app carries one property dict per distinct graph scheme. Today the served app draws every graph in the first graph's scheme, and both modes warn "a dashboard draws one scheme", which is false for the saved page. Measuring for this section found one more defect with the same root and code. A graph-level theme alias, `dash scatter mpg weight, scheme(mono)`, draws its figure in s2color (border `#eaf2f3`) on the saved page with a false "not found" note, while the served app draws s1mono (probe below). That defect is fixed under the P1.25.6 entry.

**Test order and commit rule (rule 7, D1, A146).** One entry (`P1.25b`) plus the extra closed entry P1.25.6 make one commit, `(WP-30 P1.25b)`.
- 34-01 and 34-02 write every regression test (pytest, the parity corpus, the area cscript and the truth block). They run them against the unmodified tree cut from `batch-12-base.txt` and save the failure text to `<scratch>/34-P1.25b-failure.txt`, P1.25.6's tests under their own heading. Neither commits.
- 34-03 adds the Stata truth fixture.
- 34-04 and 34-05 flip the pinned tests in place.
- 34-06 to 34-10 make the fix.
- 34-11 certifies it and 34-12 corrects the help.
- 34-13 closes `P1.25b`, appends P1.25.6 closed, replaces the CHANGELOG markers and commits once after one full run through the queue. No test-only commit exists.

## Risk: [yellow] — a widened file-read surface on CRITICAL/HIGH parse and render paths

**Why yellow.** The lookup reads files from every ado-path directory, a security surface (G9, PLAN K9). The edited symbols include `DashRenderer._scheme_for` and `DashRenderer._make_figure` (CRITICAL) and five `SchemeParser` methods (HIGH). Behaviour changes three ways:
- a working-directory file named like a shipped scheme stops overriding it;
- inherited schemes start being drawn;
- served per-graph schemes change (ratification item 28).

**Risk factors.**
1. **The read surface.** A hostile name could steer a path out of a directory: `..`, a separator, `:` or a link. A hostile file could be huge, a FIFO or full of directives.
2. **`_generate_app_source` is S35's in batch 12 (R12).** P1.25.6 needs four one-line edits in it (TR-34.13). This is an exception the orchestrator must grant at 12.0, or the section stops before task 34-08 (open question Q1).
3. **Pinned tests.** About 15 pinned tests across 7 files assert today's precedence, today's refusal text or today's inherited-scheme warning (Evidence E11).
4. **Copied class source.** `SchemeParser`'s source is copied into the served app. A new module-level name read by a class method would be a NameError on the served page (`TestTheServedAppDefinesEveryNameItReads`).
5. **Neighbours.** S30's colour reader must treat an ado-path file as a user file, and an ado-path file's directives must stay in the parsed scheme as any file's do (S33's D-33d; no unread-directive note exists, ratification row 4).

**Mitigation.**
- Every guard is enforced in Python, whatever the Stata gate says:
  - a name rule before any path is built;
  - realpath containment per directory;
  - `os.path.isfile` before open, then `fstat` after a non-blocking open;
  - a bounded read of at most `_MAX_SCHEME_BYTES + 1`;
  - the existing include depth and count bounds.
- Each guard has a hostile test (symlink, FIFO, directory, oversized, traversal, hostile directives, bounded `scheme_dirs`).
- New class-level names are class attributes. New imports inside methods are local imports.
- The served app keeps receiving properties, never paths: the builder pops `scheme_dirs` before the spec is embedded, and a test greps the page and the app for the directory names.
- The four template lines are one-line wraps, and S34 lands first in batch 12.

## Dependencies

- **Depends on:**
  - S06 (batch 2): the note channel. Every note here is a `dash…: `-prefixed `warnings.warn` inside `main()`, routed by `_dash_note_scope`; cscript needles count `(note:` through `_cs_notes`.
  - S07 (batch 3): the twenty-six shipped names in `_dash_shipped_schemes`, `_BUILTIN_NAMES` and `SHIPPED`, and its truth helpers `_s07_svg`, `_s07_page`, `_s07_app`.
  - S30 (batch 10): `SchemeParser._color`/`_color_alpha` read every Stata colour form through `OptionTranslator.stata_colour`.
  - S33 (batch 11): its regenerated shipped files and `SchemeParser` members are on S34's base. By ratification row 4 (06oct2026) S33 builds no read-recording and no unread-directive note: every parsed directive is retained in `_props`, unread ones included, and none is noted (S33's D-33d).
- **Blocks:** none.
- **Parallel batch:** S35 (date positions) and S36 (other style names).
- **Merge order:** S34 first, then S35, then S36. S34 regenerates nothing (A152).
- **Can run with them:** S34 edits `SchemeParser`'s lookup methods, `_resolve_scheme_name`, `_scheme_for`, `_make_figure`, `ServerAppBuilder.__init__`, the scheme block of `_glyph_layer_lines` and four template lines. S35 edits `_make_figure_body`, the finishers, `_on_axis` and the rest of the template. S36 edits only `SchemeParser.style_bundle` and its table.

## Evidence

Line numbers are `c96facd`'s. S01-S33 move them, so the quoted text and the symbols govern.

**E1. The Stata gate tries one name, in one directory** (dash.ado `_dash_validate_value`, scheme kind, :2423-2478).

```stata
2460:         if !`hit' & scalar(`T') != "" {
2463:             local unsafe = strpos(scalar(`T'), "/") | ///
2464:                            strpos(scalar(`T'), char(92)) | ///
2465:                            strpos(scalar(`T'), "..") | ///
2466:                            strpos(scalar(`T'), char(34))
2467:             if !`unsafe' {
2468:                 if substr(scalar(`L'), -7, .) == ".scheme" {
2469:                     capture confirm file `"`macval(tv)'"'
2472:                     capture confirm file `"`macval(tv)'.scheme"'
2477:         if !`hit' local bad "a shipped scheme, a theme, or a .scheme file in the working directory"
```

The refusal is printed at :2511-2513 as `_dash_say("err", "`prefix': `opt'() must be `bad' (got: ", value, ")`extra'")`, followed by `exit 198`. `tv` is the trimmed value (:2164) and `extra` starts `""` (:2174). Callers:
- build and serve, through `_dash_prepare_spec` (:7454-7457);
- every graph-level `scheme()`, through the option table's `scheme=scheme` rule (:2085).

The list lives in `_dash_shipped_schemes` (:1967-1971). Its header comment (:1956-1966) says PLUS is "deliberately not ... looked for".

**E2. The spec carries no ado-path.** `_dash_render_immediate` (:6765-6769) and `_dash_prepare_spec` (:8002-8006, :8049) write `"session_scheme"` and nothing about directories:

```stata
6765:     local _dash_sess_scheme = c(scheme)
6766:     _dash_json_str `"`_dash_sess_scheme'"' _sess_scheme_esc
6769:     local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "", "session_scheme": "`_sess_scheme_esc'", "level": ...
```

**E3. The renderer puts the working directory first and never tries `scheme-NAME.scheme`** (dash_render.py `SchemeParser._resolve_path`, :6069-6187):

```python
6074:         search_dirs = list(self._SCHEME_SEARCH_DIRS)
6075:         shipped = self._shipped_base(name)
6087:             candidates = [os.path.abspath(os.path.join(os.getcwd(), name))]
6100:             candidates = [os.path.abspath(
6101:                 os.path.join(os.getcwd(), name + ".scheme"))]
6110:         if shipped is not None:
6111:             candidates += [
6112:                 os.path.abspath(os.path.join(d, self._shipped_file(shipped)))
```

The working-directory candidate comes before the shipped `dash-<name>.scheme` (flips sub-claim f). The not-found text (:6181-6187) ends "place a .scheme file in the current working directory and pass its filename". `_resolve_path` reads only class state. `can_resolve` (:6038-6067) calls it on a bare `__new__` instance.

**E4. No size or file-type bound on the read** (`_parse_lines`, :6318-6337):

```python
6331:         props: dict[str, str] = {}
6332:         try:
6333:             with open(path, encoding="utf-8", errors="replace") as fh:
6334:                 lines = fh.readlines()
6335:         except OSError as exc:
6336:             raise ValueError(f"dash: cannot read scheme file '{path}': {exc}") from exc
```

`open` is the module-level name. `test_security_surface.py::TestSchemeFileContainment._open_spy` patches `dr.open`, so a new reader must keep calling `open(...)`.

**E5. `#include` resolves as `scheme()` does** (`_include`, :6389-6440, through `_resolve_cached` :6448-6460 and then `_resolve_path`). Its note clause (:6418-6420) says "it resolves outside the working directory and dash's shipped dash-<name>.scheme files, which dash does not read". Bounds: `_MAX_SCHEME_INCLUDE_DEPTH = 32` (:5637) and `_MAX_SCHEME_INCLUDES = 256` (:5643).

**E6. The dashboard's name, the false warning and the theme map** (`_resolve_scheme_name`, :19678-19810; `_THEME_SCHEME_MAP`, :19663-19675):

```python
19727:     if len({_s for _n, _s in _graph_schemes}) > 1:
19731:         warnings.warn(
19732:             f"dash: a dashboard draws one scheme; using "
19733:             f"{_graph_scheme!r} from the first graph and ignoring "
19772:     if (_raw_name and _lower not in _THEME_SCHEME_MAP
19773:             and _lower not in SchemeParser._BUILTIN_NAMES
19774:             and not SchemeParser.can_resolve(_raw_name)):
19775:         warnings.warn(
19776:             f"dash: {_raw_name!r} is not a known theme or scheme; it was "
```

`session_scheme` goes through `_THEME_SCHEME_MAP` like an explicit name (critic G1). The inherited text at :19776-19781 is pinned by `_assert_unknown_warning` (test_scheme_resolution.py:311-318), which is kept.

**E7. The saved page swaps a graph's scheme without the dashboard's rule** (`DashRenderer._make_figure`, :30158-30196; `_scheme_for`, :30139-30156):

```python
30183:         _gscheme = str(graph_opts.get("scheme", "") or "").strip()
30184:         if _gscheme:
30185:             _saved_scheme, _saved_mapper = self.scheme, self.mapper.scheme
30186:             self.scheme = self._scheme_for(
30187:                 _gscheme, f"graph {graph_opts.get('name', '') or '(unnamed)'}")
30154:             sch = SchemeParser.resolve_or_fallback(key, context)
```

A theme name here goes to `resolve_or_fallback` as a file name. Probe, 03oct2026, through `test_scheme_resolution._draw` from a scratch working directory. Printed: mode, `d.scheme.name`, `fig.background_fill_color`, `fig.border_fill_color`, warnings.

```
{'scheme': 'mono'} standalone s1mono #ffffff #eaf2f3 ["dash: scheme 'mono' was not found for graph g1; using s2color. Supported schemes: economis…"]
{'scheme': 'mono'} served     s1mono #ffffff #ffffff []
```

**E8. The served app carries one scheme.**
- `ServerAppBuilder.__init__` (:32786-32833) embeds the spec as text at :32817 (`self._spec_str = json.dumps(self.spec)`, base64-written into the app at :33911). It then resolves one scheme at :32829-32832.
- `_glyph_layer_lines` (def :32834) emits `_SCHEME_PROPS`, `_dash_build_scheme()`, `_DASH_SCHEME` and `_DASH_MAPPER` (:33440-33481). The class sources are copied at :33436-33438.
- The template (`_generate_app_source`, def :33915) builds each figure in `make_document.<locals>._dash_figure_for` (:35095). It is called at :35562, :35584-35585 and :35646-35647. Inside it, `_DASH_SCHEME.apply_to_figure(fig)` is at :35203.
- A moved layer is redrawn through `_dash_redraw_for` (:35039), which ends `return _redraw` (:35093).
- Critic G2 (p1-25.md "Critic additions") measured `g1 scheme(s1mono)` with `g2 scheme(s1rcolor)`:
  - saved figures `#ffffff` / `#000000`;
  - served `#ffffff` / `#ffffff`;
  - both modes warn that a dashboard draws one scheme.

**E9. Stata's rule, measured** (StataNow 19.5; research p1-25 §3 t1-t4, critic c1-c7, and this section's probes p1-p7 under `<scratch>/s34probe/`).
- `findfile` walks directory by directory. Each directory is followed by its subdirectory named by the file name's first character, as written. p1.do, `mata: pathsearchlist("scheme-w34o.scheme")'`, lists `…/dash/scheme-w34o.scheme`, `…/dash/s/scheme-w34o.scheme`, `/Applications/StataNow/ado/base/scheme-w34o.scheme`, `…/base/s/…` and so on, in `c(adopath)` order.
- `pathsearchlist("9w34n.scheme")` uses `9/`, `pathsearchlist("_w34u.scheme")` uses `_/` and `pathsearchlist("W34M.scheme")` uses `W/` (p2.do).
- Order:
  - an earlier directory's letter subdirectory beats a later directory: `dA/s/scheme-w34o.scheme` (red) wins over `dB/scheme-w34o.scheme` (blue);
  - a directory beats its own subdirectory: `dA/scheme-w34p.scheme` wins over `dA/s/scheme-w34p.scheme`;
  - SITE's subdirectory beats the working directory (p5.do: `sysdir set SITE …/site` is rc 0, and `findfile scheme-w34s.scheme` returns `site/s/scheme-w34s.scheme` over `./scheme-w34s.scheme`).
- Form-major order. p2.do: with `w34q.scheme` (blue) in the working directory and `scheme-w34q.scheme` (red) in a later `adopath +` directory, `twoway scatter mpg weight, scheme(w34q)` draws `#FF0000`. HEAD's `dash scatter …, scheme(w34q)` draws `#0000ff` (rc 0).
- Links. p2.do: a `scheme-w34y.scheme` symlinked to a file outside its directory is drawn by twoway (`#FF0000`), and `set scheme w34y` is rc 0. dash will not follow it, which is a documented difference.
- Names (p6/p7):
  - twoway finds `scheme-a+b.scheme`, `scheme-.x.scheme`, `scheme--x.scheme` and `scheme-x.y.scheme` (all `#FF0000`);
  - for `scheme(my theme)` it notes `(note: scheme my theme not found, using s2color)` although `scheme-my theme.scheme` exists;
  - `set scheme` refuses `.x`, `-x` and `x.y` ("invalid name", r(198)), and reads `a+b` and `my theme` as their first word (r(111)).
- A scheme file holding only `color background red` makes twoway fail (`option seriesid() not allowed`, r(198)). Every test file therefore starts `#include s2color`.
- Shadowing: a working-directory `scheme-s1mono.scheme` and `s1mono.scheme` both lose to BASE's s1mono (`fill:#FFFFFF`, markers `#606060`; research t1/t3).
- `scheme(nosuchthing)` gives twoway's `(note: scheme nosuchthing not found, using s2color)` and rc 0, and `set scheme nosuchthing` gives r(111).
- `c(adopath)` reads `` `"…/dash/"';BASE;SITE;.;PERSONAL;PLUS;OLDPLACE ``. `mata: pathsubsysdir(pathlist(c("adopath")))` returns the expanded row vector, with `.` and `~/ado/` as written.
- On this machine, PLUS/s holds 129 third-party `scheme-*.scheme` files, all parsed by `SchemeParser`. The largest is 106,413 bytes and BASE's largest is 72,668, so 1,048,576 bytes is ten times the largest.

**E10. Name-rule probe (p3/p4).** `ustrregexm` (ICU) and Python `re` agree on `\s` and Unicode word characters for `grün`, `a b`, `.x`, `x.y`, `w30-h`, `_GRSTYLE_`, `-x`, `a+b`, `x.SCHEME`, `9x` and `a/b`. The deny-list rule of TR-34.2 is the one used: it accepts what twoway finds and refuses only what M7 and P1.25.4 name.

**E11. Tests that pin today's behaviour** (each is flipped in place, never deleted, with a `Flipped:` line; R9):

| Node | Pins | After |
|---|---|---|
| `test/test_scheme_resolution.py::TestTheShippedFilesAreDashNameDotDash::test_a_scheme_file_in_the_working_directory_still_wins` (:827, both kinds) | the cwd `s2color.scheme` wins | the shipped `dash-s2color.scheme` wins; `mytheme` still resolves from the cwd |
| `test/test_installed_layout.py::TestTheInstalledLookupDoesNotWidenWhatElseIsReadable::test_the_cwd_still_wins_over_the_install` (:359, INST-08) | same | same |
| `test/test_installed_layout.py::TestTheInstalledLookupDoesNotWidenWhatElseIsReadable::test_a_cwd_symlink_named_after_a_builtin_cannot_reach_the_install` (:292, INST-05) | `ValueError` "symlink" for `s2color.scheme` | returns the install's `d/dash-s2color.scheme`; the link is never opened (`_open_spy`-style check) |
| `test/test_installed_layout.py::TestTheHelpStatesTheInstalledLayout::test_the_help_says_where_an_install_puts_them_and_why_they_are_named_so` (:526, INST-18) | phrase "{cmd:set scheme} looks only for {cmd:scheme-}{it:name}{cmd:.scheme}, so it never reads them" | the corrected phrase of TR-34.19 |
| `test/test_help_claims_8.py::TestWhatAnIncludeResolvesTo::test_the_working_directory_first` (:953) | `#include s2color` reads the cwd `s2color.scheme` | reads the translation |
| `test/test_help_claims_8.py::TestWhatAnIncludeResolvesTo::test_never_statas_own_prefixed_file` (:967) | `#include zzinc` ignores `scheme-zzinc.scheme` | reads it (`#ff00ff`) |
| `test/test_help_claims_8.py::TestAnInstalledTreeLooksOnlyForItsOwnTwenty::test_all_twenty_and_nothing_else` (:1123; S07 grows it to 26) | `can_resolve("zzthird")` False only | also `can_resolve("zzthird", ado_dirs=(root,))` True |
| `test/test_immediate_scheme.py::TestGraphLevelScheme::test_the_first_graphs_scheme_wins_and_the_conflict_is_reported` (:87) | `pytest.warns(UserWarning, match="scheme")` | no such warning; dashboard `economist`, each figure its own |
| `test/test_custom_scheme.cscript` CS-06, CS-07, CS-09, CS-13 | needle "scheme() must be a shipped scheme" | needle "scheme() must be one of economist, meta," |
| `test/test_custom_scheme.cscript` CS-10 | `set scheme zzdashtest`: one note, s2color | no note; the file's own `#2a3b4c` background drawn |
| `test/test_help_claims_8.cscript` HC8-08 | the old refusal, word for word | the new refusal, word for word |
| `test/test_help_claims_8.cscript` HC8-10 | inherited `zzdashtest`: one warning | no note; drawn |
| `test/test_render_log_clean.cscript` check 5 | control: inherited `zzdashrlc` (`#include s2color`) warns once | control file holds `#include zzdashrlcnone`: one `(note: scheme zzdashrlcnone not found, using s2color)` |

Guards that must stay green unchanged:
- `test/test_scheme.py::TestSecurity` (`test_path_traversal_raises` matches "outside allowed"; the BUG_51 tests match "symlink");
- `test/test_security_surface.py::TestSchemeFileContainment` (all five; its search dir is still searched when no `scheme_dirs` is given, TR-34.5);
- `test/test_installed_layout.py` INST-04, -06, -07, -16 ("Built-in schemes");
- `test/test_scheme_resolution.py::TestAnUnresolvableNameIsReportedOnce` (all eight; the inherited text is unchanged), `::TestCanResolve`, `::TestTheShippedFilesAreDashNameDotDash::test_a_stray_name_dot_scheme_beside_the_renderer_is_not_read` and `::test_a_missing_dash_file_falls_back_rather_than_reading_a_stray`;
- `test/test_immediate_scheme.py`'s include-note tests (one parse per name, TR-34.13);
- `test/test_help_claims_8.cscript` HC8-12 and HC8-13.

The research's red list is re-measured, not trusted (R9): 34-11 runs every scheme test file.

**E12. Blast radius** (`gitnexus impact <sym> -d upstream -r dash`, 03oct2026):

| Symbol | Risk | Note |
|---|---|---|
| `SchemeParser._resolve_path` | HIGH (4) | warn |
| `SchemeParser.resolve_or_fallback` | HIGH (6) | warn |
| `SchemeParser._include` | HIGH (3) | warn |
| `SchemeParser._parse_lines` | HIGH (3) | warn |
| `SchemeParser.can_resolve` | LOW (3) | |
| `_resolve_scheme_name` (`-f dash_render.py`) | LOW (2) | |
| `DashRenderer._scheme_for` | **CRITICAL** (5; scripts/regen_* callers) | warn |
| `DashRenderer._make_figure` | **CRITICAL** (8; render, `_build_sources_and_figures`, regen scripts) | warn; not in the index's 12.0 list, so 12.0 runs it |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4) | warn |
| `ServerAppBuilder._generate_app_source` | HIGH (5) | warn; R12 exception, Q1 |
| `SchemeParser.__init__`, `DashRenderer.__init__`, `ServerAppBuilder.__init__` | UNKNOWN (`__init__` ambiguous) | grep: SchemeParser built at :5844-5870, :7957, :30154, :32830 |
| `_dash_validate_value`, `_dash_prepare_spec`, `_dash_render_immediate` | UNKNOWN (Stata) | grep: 9, 7 and 3 call sites |

## User stories

- **US-34.1** As a twoway user, I want `scheme(plotplain)` and any scheme I installed (PLUS, PERSONAL, SITE, an `adopath` directory, the working directory) found under Stata's own `scheme-NAME.scheme` name, so a dashboard looks like my graphs.
- **US-34.2** As a twoway user whose session has `set scheme` to such a scheme, I want an unschemed dashboard drawn in it, without a warning.
- **US-34.3** As a scheme author, I want my file's `#include` resolved exactly as Stata resolves it.
- **US-34.4** As a twoway user, I want a stray `s2color.scheme` in my working directory not to change what `scheme(s2color)` draws, as it does not in twoway.
- **US-34.5** As a twoway user who mistypes a name, I want the refusal to list the names that exist.
- **US-34.6** As a dashboard publisher, I want a dashboard whose graphs name different schemes served exactly as the saved page draws it, before and after a filter move, without a false warning.
- **US-34.7** As a dashboard publisher, I want a scheme file never run as code, never read through a link out of its directory, never read when it is huge or not a regular file, and my directory names never written into the page or the app.

## Business requirements

- **BR-34.1** A scheme dash does not ship is found as twoway finds it: `scheme-NAME.scheme` across the whole ado-path in Stata's order, then `NAME.scheme` across it, each directory followed by its first-letter subdirectory. Every measured placement of `scheme_lookup_truth.json` resolves to the file `findfile` returns, except LK-16 (shipped first) and LK-19 (a link out of its directory).
- **BR-34.2** BR-34.1 holds for `scheme()` on `dash` *plottype*, a registered graph, a layer's parentheses, `dash build`, `dash serve`, the session's `c(scheme)` and every `#include`.
- **BR-34.3** The twenty-six shipped names, bare or with `.scheme` in any case, always draw dash's translation, whatever file of that name sits anywhere on the ado-path.
- **BR-34.4** `scheme()` given a theme name (`default`, `clean`, `mono`, `dark`) draws the scheme file of that name when Stata finds one, and the theme otherwise. An inherited `c(scheme)` is always looked up as a file. `theme()` is always the alias.
- **BR-34.5** A name with a blank, a control character, `/`, `\`, `:`, `..`, a double quote, a backtick or `$`, or longer than 87 characters, is refused r(198) on every entry point, before any file is looked for. An unfound name is refused r(198). The refusal lists the twenty-six names and the six themes.
- **BR-34.6** A file is read only if it is a regular file of at most 1,048,576 bytes whose real path lies inside the ado-path directory it was found under. A file refused this way, when named, inherited or `#include`d, draws s2color with one note saying why, and rc is 0.
- **BR-34.7** A scheme file is parsed as data. Nothing in it is executed, evaluated or run by Python or Stata, and its text reaches the page only through the colour, size and style readers.
- **BR-34.8** Each graph's own `scheme()` draws that graph in that scheme, in the saved page and the served app, before and after a filter move. No "a dashboard draws one scheme" warning is printed. The page chrome and KPI cards take the dashboard's scheme (build `scheme()`, `theme()`, the first graph's, `c(scheme)`, in that order).
- **BR-34.9** The ado-path directories never appear in the saved page or the served `app.py`.
- **BR-34.10** The help states twoway's rule, the shipped-first precedence, the theme-name rule, the four safety differences (no paths, links not followed, the size cap, `dash-` names in the working directory only) and the refusal's text. It no longer offers the copy-into-the-working-directory remedy.

## Technical requirements

**SchemeParser (dash_render.py, class at :5646). Every new name is a class attribute or method, so it travels into the served app with the class. The index R2 row for S34 lists no copy-list entry.**

- **TR-34.1 Class constants**, after `_INTENSITY` (:5970-5975):
  - `_MAX_SCHEME_BYTES: int = 1_048_576`;
  - `_MAX_SCHEME_NAME_CHARS: int = 87` (an 80-character name plus `.scheme`);
  - `_SCHEME_NAME_BAD`, with a comment citing M7, P1.25.4 and the p6/p7 measurements. It matches any whitespace, any C0 or C1 control character or DEL, `/`, a backslash, `:`, a double quote, a backtick or `$` (C1, U+0080-U+009F, so the Python rule refuses at least what the Stata gate's `\p{Cc}` refuses):

    ```python
    _SCHEME_NAME_BAD = re.compile("[\\s\\x00-\\x1f\\x7f-\\x9f/\\\\:\"\x60$]")
    ```

  Rewrite the `_BUILTIN_NAMES` comment's "(WP-17)" sentence to say a name dash does not ship is found along the ado-path (WP-30 P1.25b).
- **TR-34.2 `_scheme_name_ok(cls, name) -> bool`** (new classmethod). True iff `0 < len(name) <= cls._MAX_SCHEME_NAME_CHARS`, `".." not in name` and `cls._SCHEME_NAME_BAD.search(name) is None`.
- **TR-34.3 `__init__(self, scheme_name="s2color", ado_dirs=())`** (:5977).
  - Set `self._ado_dirs = tuple(ado_dirs or ())` before `_resolve_path`.
  - A user file's `name` is its base name less `.scheme`, and less a leading `scheme-` in any case. A file `scheme-w34x.scheme` is `w34x`, the name `c(scheme)` shows (critic G4).
  - A shipped name keeps today's rule.
- **TR-34.4 `_resolve_path(self, name)`** (:6069), rewritten in this order:
  1. `name = (name or "").strip()`. If `_shipped_base(name)` is not None, return `self._shipped_path(name, shipped)`. That is a new method holding today's shipped branch unchanged: the `dash-<name>.scheme` candidates in `_SCHEME_SEARCH_DIRS`, the abspath and realpath containment loop, and the installed-letter-directory last resort with its "resolves outside … was not read. Reinstall dash." warning. It has no working-directory candidate (flips sub-claim f).
  2. If `not self._scheme_name_ok(name)`, raise `ValueError(f"dash scheme: path '{safe}' resolves outside allowed directories: a scheme is named, never given as a path (no blank, quote, slash, backslash, colon or '..').")`, where `safe = self._safe_name(name)`. The phrase "outside allowed" keeps `test_scheme.py::TestSecurity::test_path_traversal_raises` and `_include`'s clause.
  3. For `(root, path)` in `self._ado_candidates(name)`, the first `path` for which `os.path.exists(path)` is true decides: `return self._admit(root, path, safe)`. `_admit` raises for a refused file, and the walk does not go on, because findfile's first hit is twoway's file.
  4. Otherwise raise `ValueError(f"dash: scheme '{safe}' not found. Built-in schemes: {', '.join(sorted(self._BUILTIN_NAMES))}. A scheme of your own is found as Stata finds it: scheme-NAME.scheme, then NAME.scheme, in a directory on the ado-path.")`. INST-16 matches "Built-in schemes".
- **TR-34.5 `_ado_candidates(self, name) -> list[tuple[str, str]]`** (new):
  - `low = name.lower()`.
  - Directories:
    - `(os.getcwd(),)` when `low.startswith("dash-")` (today's rule: dash's own file names are the user's working-directory files, help "Why they are named");
    - otherwise `self._ado_dirs`;
    - when that is empty (a spec built without dash.ado, or a test), `(os.getcwd(),) + tuple(self._SCHEME_SEARCH_DIRS)`, today's set.
  - Forms:
    - `(name,)` when `low.endswith(".scheme")`;
    - `(name + ".scheme",)` for a `dash-` name;
    - else `("scheme-" + name + ".scheme", name + ".scheme")`.
  - Return `[(d, p) for f in forms for d in dirs for p in (os.path.join(d, f), os.path.join(d, f[0], f))]`, which is Stata's form-major, directory-then-subdirectory order (E9). The subdirectory is the first character as written.
- **TR-34.6 `_admit(self, root, path, safe) -> str`** (new).
  - `real_root = os.path.realpath(root)`, `real = os.path.realpath(path)` and `base = self._safe_name(os.path.basename(path))`.
  - If not `real.startswith(real_root + os.sep)`, raise `ValueError(f"dash scheme: '{base}' for scheme '{safe}' resolves via symlink outside allowed directories (the directory it was found in); it was not read.")`.
  - If not `os.path.isfile(real)`, raise `"… is not a regular file; it was not read."`.
  - If `os.path.getsize(real) > self._MAX_SCHEME_BYTES`, raise `"… is larger than 1,048,576 bytes; it was not read."`.
  - Otherwise record the checked file's identity, `self._admitted[path] = (st.st_dev, st.st_ino)` from one `os.stat(real)` taken after the checks (the dict is made with `getattr(self, "_admitted", None)` or `{}`, so a `__new__` probe works), and return `path`. No message names a directory (privacy, S06's no-path rule).
  - The identity closes the check-then-open race: a link or file swapped into the directory between `_admit` and the read (TR-34.7) is caught, never read.
- **TR-34.7 `_read_scheme_lines(cls, path) -> list[str]`** (new classmethod), used by `_parse_lines` in place of :6332-6336.
  - Read with `open(path, "rb", opener=lambda p, fl: os.open(p, fl | getattr(os, "O_NONBLOCK", 0)))`. It is the module-level `open`, so the security spy still sees it, and it is a lambda, so it is not a map key.
  - Signature `_read_scheme_lines(cls, path, expect=None)`; `_parse_lines` passes `expect=getattr(self, "_admitted", {}).get(path)`.
  - Inside: `import stat as _stat` (a local import, because the app does not import `stat`), `st = os.fstat(fh.fileno())`, refuse `not _stat.S_ISREG(st.st_mode)`. When `expect` is given, refuse `(st.st_dev, st.st_ino) != expect` with "… changed after it was checked; it was not read.". Then `data = fh.read(cls._MAX_SCHEME_BYTES + 1)`. Refuse `len(data) > cls._MAX_SCHEME_BYTES` with the TR-34.6 words.
  - Keep `except OSError as exc: raise ValueError(f"dash: cannot read scheme file '{path}': {exc}") from exc`.
  - Return `data.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")`, which gives the same lines and line numbers as `readlines()` with universal newlines.
- **TR-34.8 Lookup entry points.**
  - `can_resolve(cls, name, ado_dirs=())` returns `not cls.unresolved_reason(name, ado_dirs)`. Keep its docstring and widen it to the walk.
  - `unresolved_reason(cls, name, ado_dirs=())` is new. It is `""` when `_resolve_path` succeeds on a `__new__` probe with `_ado_dirs` set, under `warnings.catch_warnings()` with `simplefilter("ignore")`. Otherwise it is `str(exc)`, or `"no name"` for an empty name.
  - `resolve_or_fallback(cls, name, context, ado_dirs=())` builds `cls(candidate, ado_dirs=ado_dirs)` for both candidates. When the first fails with a message containing `"it was not read"`, its warning reads `f"dash: scheme {candidate!r} was not read for {context}; using s2color. ({exc})"`. Otherwise today's text is kept.
- **TR-34.9 `_include`** (:6418-6420): `where` becomes `"; a scheme is named, never given as a path"` when the reason contains `"outside allowed directories:"`, `"; it was not read"` when the reason contains `"it was not read"`, and `""` otherwise. `_resolve_cached` is unchanged and uses `self._ado_dirs` through `_resolve_path`, so `#include` follows the same walk (sub-claim d).

**One naming rule for both renderers (module level, builder-side only; neither is copied, because the served app receives properties).**

- **TR-34.10** Directly above `_resolve_scheme_name` (:19678), after `_THEME_SCHEME_MAP`:
  - `_DASH_MAX_SCHEME_DIRS = 64`.
  - `_dash_scheme_dirs_of(build_options) -> tuple[str, ...]`. It reads, never pops, `build_options.get("scheme_dirs")`. It keeps at most `_DASH_MAX_SCHEME_DIRS` entries that are `str`, 1-4096 characters, with no character below `\x20` or `\x7f`. It expands `~` only for `"~"` or a `"~/"` prefix (`os.path.expanduser`). It requires `os.path.isabs` and `os.path.isdir`, takes `os.path.realpath`, drops duplicates and keeps order. Anything else, including a non-list, gives `()`. It never raises.
  - `_dash_scheme_choice(raw, source, scheme_dirs=()) -> str`, with `source` one of `"scheme"`, `"theme"`, `"graph"`, `"session"`:
    - a shipped base (case-insensitive, with or without `.scheme`) gives the lower-case base;
    - a `_THEME_SCHEME_MAP` key gives the alias for `"theme"`, the raw name for `"session"` (P1.25.5), and for `"scheme"`/`"graph"` the raw name when `SchemeParser.can_resolve(raw, ado_dirs=scheme_dirs)` and the alias otherwise;
    - anything else gives `raw`.
- **TR-34.11 `_resolve_scheme_name(master_spec, scheme_dirs=None)`.**
  - `dirs = _dash_scheme_dirs_of(bo) if scheme_dirs is None else tuple(scheme_dirs)`.
  - Delete the one-scheme warning (:19727-19737, P1.25.6). The first graph's scheme is still the dashboard's.
  - Pick `(source, value)` by today's precedence: scheme, theme, graph, session. `choice = _dash_scheme_choice(value, source, dirs)`.
  - If `choice` is non-empty, not a shipped name, and `reason = SchemeParser.unresolved_reason(choice, dirs)` is non-empty:
    - warn today's inherited text (E6) when `"it was not read"` is not in `reason`;
    - otherwise warn `f"dash: {value!r} was found but not read ({reason.split(': ', 1)[-1]}); using s2color."`;
    - return `"s2color"`.
  - Return `choice or "s2color"`.
- **TR-34.12 Saved renderer** (`DashRenderer`).
  - In `__init__`, after `_build_opts` is read (:29155), set `self._scheme_dirs = _dash_scheme_dirs_of(_build_opts)` and `_build_opts.pop("scheme_dirs", None)`, then call `_resolve_scheme_name(self.master_spec, self._scheme_dirs)` (:29162).
  - In `_scheme_for` (:30154), call `SchemeParser.resolve_or_fallback(key, context, ado_dirs=getattr(self, "_scheme_dirs", ()))`.
  - In `_make_figure`, replace `self._scheme_for(_gscheme, …)` (:30186-30187) with `self._scheme_for(_dash_scheme_choice(_gscheme, "graph", getattr(self, "_scheme_dirs", ())), …)`, the same context string. Nothing else in `_make_figure` changes. `_make_figure_body` is S35's (R12).
- **TR-34.13 Served builder** (`ServerAppBuilder`).
  - In `__init__`, right after the spec is loaded (:32794), set `self._scheme_dirs = _dash_scheme_dirs_of(self.spec.get("build_options", {}))` and pop `"scheme_dirs"` from `self.spec["build_options"]`. This happens before `_spec_str` (:32817), so no directory name is embedded (BR-34.9).
  - :32829 passes `self._scheme_dirs`, and :32830 passes `ado_dirs=self._scheme_dirs`. Then call the new `self._resolve_graph_schemes()`.
  - `_resolve_graph_schemes(self)`:
    - For each graph dict with a non-empty stripped `graph_options["scheme"]` (`graph_options` only, as `_make_figure` reads), compute `choice = _dash_scheme_choice(raw, "graph", self._scheme_dirs)`.
    - Look the parser up in a cache seeded `{self.scheme_requested: self.scheme}`, so a graph naming the dashboard's scheme parses nothing and notes nothing again (`test_immediate_scheme.py` include-note tests). On a miss, build it with `SchemeParser.resolve_or_fallback(choice, f"graph {go.get('name', '') or '(unnamed)'}", ado_dirs=self._scheme_dirs)`.
    - Store `self.graph_schemes[raw] = parser` only when `parser is not self.scheme`.
    - A graph's own parser keeps every directive its file sets, unread ones included, in `_props` (S33's D-33d), so `_GRAPH_SCHEME_PROPS` below carries them; nothing is noted for them (ratification row 4).
  - In `_glyph_layer_lines`, after `"_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)",` (:33479), emit the following, with one blank line between items:
    - `_GRAPH_SCHEME_PROPS = %r` of `{raw: {"name": s.name, "is_fallback": bool(s.is_fallback), "props": dict(s._props)} for raw, s in sorted(getattr(self, "graph_schemes", {}).items())}`;
    - `_DASH_GRAPH_SCHEMES = {}`;
    - `def _dash_graph_scheme(raw):`, which returns the cached parser rebuilt exactly as `_dash_build_scheme()` builds one (`SchemeParser.__new__`, `_props`, `name`, `is_fallback`, then `_init_properties()`; S33 adds nothing there), or None for a name not in the dict;
    - `def _dash_under_graph_scheme(g, fn, *args, **kwargs):`. It declares `global _DASH_SCHEME` and reads `(g or {}).get('graph_options')` as a dict. If `_dash_graph_scheme(...)` is None it returns `fn(*args, **kwargs)`. Otherwise it saves `(_DASH_SCHEME, _DASH_MAPPER.scheme)`, sets both to the graph's parser, calls `fn` and restores both in `finally`. That is the saved `_make_figure` swap (E7).

    Every emitted line is a Python literal written by `%r`, or fixed text. No user text is pasted into code.
  - In `_generate_app_source`, four one-line edits (the R12 exception, Q1). No other template line changes:
    - :35562 → `"            figures[gname] = _dash_under_graph_scheme(g, _dash_figure_for, g, gname, g_df)",`;
    - :35584 → `"            figures[gname] = _dash_under_graph_scheme(g, _dash_figure_for, g, gname, work_df,",` (its next line is kept);
    - :35646 → `"            figures[_fname] = _dash_under_graph_scheme(_g_pan, _dash_figure_for,",` (the next line `_g_pan, _fname, _gdf, _fac_label=_label, _rescale=_brs)` is kept);
    - :35093 → `"        return lambda frame: _dash_under_graph_scheme(g, _redraw, frame)",`. A redraw after a move then runs under the graph's scheme.

**Stata side.**

- **TR-34.14 dash.ado.**
  - **New program `_dash_scheme_dirs`.** Place it after `// END shipped schemes (WP-17)` (:1972), outside the sentinels that `test_scheme_resolution._ado_block` reads, with a header comment citing scheme.class:172-173 and M7. It opens `version 19`, runs `mata: st_local("j", _dash_scheme_dirs_json())` and returns `c_local _dash_sdirs `"`macval(j)'"'`. Every later expansion of `_dash_sdirs` (the two writers' master_json lines) is written `` `macval(_dash_sdirs)' ``, so no directory text is re-expanded as a macro (the rule of `_dash_validate_value`'s header).
  - **Writers.** `_dash_render_immediate` (after :6766) and `_dash_prepare_spec` (after :8006) call `_dash_scheme_dirs`. Each master_json line gains `"scheme_dirs": `_dash_sdirs', ` (:6769) and `"scheme_dirs":`_dash_sdirs',` (:8049) directly after the `session_scheme` pair. These are S34's own export-block paragraphs (R6); S42 adds `ts` keys to the same lines in batch 15.
  - **The gate** (:2423-2478). Keep the shipped and theme hit tests. When neither hits:
    - `named` = `!ustrregexm(scalar(`T'), "[\s\p{Cc}]")` and none of `/`, `char(92)`, `:`, `..`, `char(34)`, `char(96)`, `char(36)` by `strpos`, and `ustrlen(scalar(`T')) <= 87`;
    - if named, a name whose lower case starts `dash-` is checked by `confirm file` in the working directory, as written when it ends `.scheme`, else with `.scheme`;
    - a name ending `.scheme` is checked by `capture findfile `"`macval(tv)'"'`;
    - any other name is checked by `capture findfile `"scheme-`macval(tv)'.scheme"'` and, if that fails, `capture findfile `"`macval(tv)'.scheme"'`;
    - rc 0 is a hit.
  - **The refusal.** On no hit, build `_sn` from `: list sort _dash_schemes` and `_tn` from `: list sort _dash_themes`, each with `" "` replaced by `", "`, and set `local bad "one of `_sn'; a theme (`_tn'); or a scheme Stata finds along the ado-path as scheme-NAME.scheme or NAME.scheme"`. If not named, also set `local extra ". A scheme is named, never given as a path: a name holding a blank, a quote, a slash or backslash, a colon or .. is not looked for"`. Rewrite the branch's WP-17 comment for the new rule.
  - **Comments.** Rewrite `_dash_shipped_schemes`'s header (:1956-1966: no PLUS refusal, no copy remedy), the option-table note (:2012-2016) and :7439-7444's comment. No other dash.ado line changes.
- **TR-34.15 dash_parse.mata.**
  - **New `string scalar _dash_scheme_dirs_json()`**, placed directly after `_dash_json_str_args()` (:382-404, before the `_dash_text_args` comment), with a comment block in the file's style:
    - `d = pathsubsysdir(pathlist(c("adopath")))` (a row vector);
    - for each entry up to 64: skip an empty entry; skip an entry holding a backtick, `$`, a double quote or a control character (dash never passes such a directory through a macro; documented beside the link rule); map `"."` to `c("pwd")`; keep an entry starting `~` as written; join any other relative entry to `c("pwd")` with `pathjoin`;
    - write each as `char(34) + _json_escape(p) + char(34)`, joined by `,` inside `[ ]`.
  - Add `_dash_scheme_dirs_json()` to the header index (:1-303) in its section.
  - Add `_dash_scheme_dirs_json` to dash.ado's `_needed` list (:237-255) after `_dash_json_str_args` (X.5).

**Notes, neighbours, maps, copy lists.**

- **TR-34.16** Every note in this section is a `warnings.warn("dash…: …", UserWarning)` raised in `main()`. S06's `_dash_note_scope` prints it once as `(note: …)`. Tests count notes with S06's helpers: `_cs_notes` in cscripts, `_assert_unknown_warning` and message lists in pytest.
  - **S30.** A third-party colour form in an ado-path file goes through the same `SchemeParser._color`/`_color_alpha` as any user file. TestThirdPartySchemes asserts equality with `OptionTranslator.stata_colour` on the same text.
  - **S33.** An ado-path file's directives (any directory, either form, PLUS included) are retained in `_props` like any other file's, unread ones included, and no note is raised for them (S33's D-33d; ratification row 4, 06oct2026). `_read_scheme_lines` changes how a file is opened and read, not what `_parse_lines` stores. TestThirdPartySchemes asserts the retention and the silence.
- **TR-34.17 Maps (A148, X.5)**, under S34's anchors, alphabetical.
  - `test/function_test_map.py` (S34 anchor after `'main'`):

    | Key | Test |
    |---|---|
    | `'SchemeParser._admit'` | `…::TestTheGuards::test_a_link_out_of_its_directory_is_not_read` |
    | `'SchemeParser._ado_candidates'` | `…::TestTheWalkIsStatas::test_each_measured_placement` |
    | `'SchemeParser._read_scheme_lines'` | `…::TestTheGuards::test_the_read_stops_at_the_cap` |
    | `'SchemeParser._scheme_name_ok'` | `…::TestTheNameRule::test_the_parser_reads_the_name_rule` |
    | `'SchemeParser._shipped_path'` | `…::TestShippedNamesComeFirst::test_a_working_directory_file_never_replaces_a_shipped_scheme` |
    | `'SchemeParser.unresolved_reason'` | `…::TestTheGuards::test_a_session_scheme_refused_by_a_guard_says_why` |
    | `'ServerAppBuilder._resolve_graph_schemes'` | `…::TestPerGraphSchemes::test_each_graph_is_drawn_in_its_own_scheme` |
    | `'_dash_scheme_choice'` | `…::TestThemeNamesAndFiles::test_an_explicit_alias_loses_to_a_file` |
    | `'_dash_scheme_dirs_of'` | `…::TestTheGuards::test_scheme_dirs_input_is_bounded` |
    | `'app:_dash_graph_scheme'` | `…::TestPerGraphSchemes::test_each_graph_is_drawn_in_its_own_scheme` |
    | `'app:_dash_under_graph_scheme'` | `…::TestPerGraphSchemes::test_the_served_move_keeps_each_graphs_scheme` |

    Every `…` is `test/test_scheme_lookup.py`. The existing keys of the edited functions stay as they are.
  - `test/program_coverage_map.py`:
    - `COVERAGE["dash.ado"]`: `"_dash_scheme_dirs": ("test_custom_scheme.cscript:SP-04", "test_wp30_truth.cscript:SP-18"),`;
    - `COVERAGE["dash_parse.mata"]`: `"_dash_scheme_dirs_json": ("test_wp30_truth.cscript:SP-18", "test_custom_scheme.cscript:SP-04"),`.
- **TR-34.18 Served copy lists (R2).** No entry is added to either `_glyph_layer_lines` tuple or to `_shared_stat_lines`. The new SchemeParser methods and constants travel with the class (:33436). `_dash_graph_scheme` and `_dash_under_graph_scheme` are generated text in the scheme block, like `_dash_build_scheme`. `_dash_scheme_dirs_of`, `_dash_scheme_choice` and `_resolve_graph_schemes` run only in the builder. G4 is run to show that the app reads no undefined global. No JavaScript twin exists or is needed: the saved page resolves schemes at build, and its filter JS never touches them.
- **TR-34.19 Help (R3: S34's paragraphs of "Stata scheme support", plus the one scheme sentence at dash.sthlp:703-707, which no batch-12 partner owns).** The SMCL is in task 34-12.
- **TR-34.20 Security (rule 1, G9; the commit body names the threats: path traversal, link escape, resource exhaustion, code execution, disclosure).**
  - The name rule runs before any path is joined, in Stata (`ustrregexm` and `strpos` on a scalar, never a macro-expanded value) and again in Python.
  - Containment is checked against each directory's realpath, and a refused first hit stops the walk.
  - Only regular files are read: `isfile` before open, then a non-blocking open and `fstat`, so a FIFO swapped in never blocks. The opened file's device and inode must equal the ones `_admit` checked, so a link swapped in after the check is never read (`test_a_swap_after_the_check_is_not_read`). The read is at most 1,048,577 bytes.
  - The include bounds (32 deep, 256 lines, 10 notes) are kept.
  - `scheme_dirs` is bounded: 64 entries, 4096 characters, no control characters, absolute existing directories.
  - Notes echo names through `_safe_name` (80 printable characters) and never print a directory.
  - No `eval`, `exec`, `subprocess` or `shell=True`, and dash.ado never `do`es, `run`s or `include`s a scheme path.
  - The directories are popped before the served spec is embedded.

## Boundaries

- **S35 (batch 12)** owns `_make_figure_body`, `_build_sources_and_figures`, the finishers and every other `_generate_app_source` line. S34 edits only the four lines of TR-34.13 and lands first. If S35's base for those four lines differs from the quoted text at 12.1, S34 stops and reports.
- **S36 (batch 12)** owns `SchemeParser.style_bundle`, its table, `_FALLBACK_PROPS`, the extractor and the regeneration of the 26 files. S34 touches none of them and its own dash.sthlp paragraphs only.
- **S30 (earlier batch)** owns the colour reader, and S33's D-33d records that every parsed directive is retained. S34 only asserts their behaviour on ado-path files (TR-34.16).
- **S06** owns the note channel and its needles. S07 owns the 26-name list and the six translations. S34 changes neither list.
- **S42 (batch 15)** adds `ts` keys on the same master_json lines, and S57 (batch 20) moves the served recompute to a worker. S57 must serialise `_dash_under_graph_scheme`'s module-state swap with its worker, as it must `_DASH_MAPPER.colorvar_domain` today (Notes).
- **Kept as documented differences:**
  - a path in `scheme()` is refused (P1.25.4);
  - `scheme(NAME.scheme)` still reads a file of that name, where twoway notes "not found";
  - a `dash-` name is read only from the working directory;
  - links out of a directory are not followed.
- **Out of scope:**
  - Windows and Linux path and case rules (M4);
  - the `c(adoarchive)` branch of scheme.class (UNCLEAR);
  - third-party `color-*.style` and `*.style` lookups (P1.25.7, filed in P2.55);
  - Stata 14-18.5 (M2).
- **Tracking documents** (GAPS2 Tracked lines, DROPIN, REMAINING, TWOWAY_COVERAGE_AUDIT, ROADMAP, AGENTS.md) are S58's (A145). See "Notes for the closeout".

## Stata truth

**1. New extractor and fixture.** `scripts/extract_scheme_lookup_truth.do` writes `test/fixtures/scheme_lookup_truth.json`.

The do-file:
- copies S02's root selection: `DASH_REPO`, else `c(pwd)` when it holds `dash.ado` and `test/run_all_cscripts.do`, else r(601);
- runs `adopath ++ "<root>/"` and then `global dash_nobrowser 1` as its first two statements after the root is known (E5);
- runs only twoway, never dash.

It saves `c(sysdir_site)`, `c(sysdir_personal)`, `c(sysdir_plus)`, `c(sysdir_oldplace)` and `c(pwd)`, and restores all five at the end, including after a failed case (each case under `capture noisily`). It works in a fresh `tempfile`-named directory under `c(tmpdir)`.

File contents:
- R is `#include s2color` + `color background red` + `color p1 green`;
- B is the same with `blue`;
- every name is used once per session, because Stata caches a loaded scheme (HC8-13's note).

Per case, it creates the case root and `cwd/`, `cd`s there, writes the files and applies the setup. It then records:
- `twoway scatter mpg weight, scheme(NAME) name(lk, replace)` rc;
- the first `<rect>` fill and the first circle fill of `graph export <case>.svg`, upper-case hex as Stata writes it;
- any `(note: …)` line from a `log using` around the twoway call;
- `capture set scheme NAME` rc (then `set scheme s2color`);
- `findfile` of `scheme-NAME.scheme`, else `NAME.scheme`: `r(fn)` made relative to the case root (`./x` becomes `cwd/x`; a BASE hit becomes `BASE/s/<file>`; `""` when none);
- the ado-path as Stata lists it after the setup, with sysdir codewords kept, the repo written `REPO` and case-root directories relative.

Cases:

| Key | Files (case-root relative) | Setup | NAME |
|---|---|---|---|
| lk01 | `cwd/scheme-lk01.scheme` R | — | lk01 |
| lk02 | `cwd/lk02.scheme` B | — | lk02 |
| lk03 | `cwd/scheme-lk03.scheme` R, `cwd/lk03.scheme` B | — | lk03 |
| lk04 | `cwd/lk04.scheme` B, `add/scheme-lk04.scheme` R | `adopath + add` | lk04 |
| lk05 | `add/s/scheme-lk05.scheme` R | `adopath + add` | lk05 |
| lk06 | `add/l/lk06.scheme` R | `adopath + add` | lk06 |
| lk07 | `add/9/9lk07.scheme` R | `adopath + add` | 9lk07 |
| lk08 | `add/_/_lk08_.scheme` R | `adopath + add` | _lk08_ |
| lk09 | `add/s/scheme-lk09.scheme` R, `addb/scheme-lk09.scheme` B | `adopath + add`, `adopath + addb` | lk09 |
| lk10 | `add/scheme-lk10.scheme` R, `add/s/scheme-lk10.scheme` B | `adopath + add` | lk10 |
| lk11 | `site/s/scheme-lk11.scheme` R, `cwd/scheme-lk11.scheme` B | `sysdir set SITE site` | lk11 |
| lk12 | `personal/scheme-lk12.scheme` R | `sysdir set PERSONAL personal` | lk12 |
| lk13 | `plus/s/scheme-lk13.scheme` R | `sysdir set PLUS plus` | lk13 |
| lk14 | `oldplace/scheme-lk14.scheme` R | `sysdir set OLDPLACE oldplace` | lk14 |
| lk15 | `cwd/rel/scheme-lk15.scheme` R | `adopath + rel` (relative) | lk15 |
| lk16 | `cwd/scheme-s1mono.scheme` R, `cwd/s1mono.scheme` R | — | s1mono |
| lk17 | `cwd/lk17.scheme` (`#include lk17p` / `color p1 green`), `add/scheme-lk17p.scheme` R | `adopath + add` | lk17 |
| lk18 | `add/scheme-mono.scheme` R | `adopath + add` | mono |
| lk19 | `add/scheme-lk19.scheme`, a symlink (`shell ln -s`, with the case root's path) to `outside/x.scheme` R | `adopath + add` | lk19 |
| lk20 | — | — | lk20none |
| lk21 | `cwd/scheme-lk2-1.scheme` R | — | lk2-1 |
| lk22 | `cwd/scheme-lk.22.scheme` R | — | lk.22 |

- A python block at the end writes the JSON through `sfi.Macro.getGlobal`. It never calls Stata, never uses `shell=True` and writes a backtick as `\x60`.
- `_meta` holds `stata_version` (`c(stata_version)` with `c(edition_real)`), `born_date` (`c(born_date)`), `dash_commit` (`git -C <root> rev-parse HEAD` written to a file by `shell`, read by Python) and `extracted` (date and time).
- Each record holds `files`, `setup`, `name`, `adopath`, `twoway_rc`, `twoway_bg`, `twoway_marker`, `note`, `set_scheme_rc` and `findfile_rel`.
- Stage it with `git add -f test/fixtures/scheme_lookup_truth.json`. `TestTheWalkIsStatas::test_the_fixture_is_stamped` names it, and `test_fixtures_are_committed.py` is not edited (R7).

Run (from the worktree `$WT`):

```sh
mkdir -p <scratch>/s34/ext
DASH_REPO=$WT /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s34/ext $WT/scripts/extract_scheme_lookup_truth.do
# log: <scratch>/s34/ext/extract_scheme_lookup_truth.log
```

Expected, from E9:
- lk01, lk03, lk04, lk05, lk06, lk07, lk08, lk09, lk10, lk11, lk12, lk13, lk14, lk15, lk17, lk18, lk19, lk21 and lk22: `twoway_bg` `#FF0000`;
- lk02: `#0000FF`;
- lk16: `#FFFFFF` with `findfile_rel` `BASE/s/scheme-s1mono.scheme`;
- lk20: the s2color background, the note `(note: scheme lk20none not found, using s2color)` and `set_scheme_rc` 111.

Any other value stops the task and is reported. It is not edited into the fixture.

**2. Truth block** `S34` in `test/test_wp30_truth.cscript`, between S01's `S34 start`/`S34 end` lines (R1). Header: S01's stub header, unchanged: `* ==== S34 P1.25b: Stata's scheme lookup along the ado-path ====` (the manifest name without its trailing parenthesis, TR-01.6; `TestTheWp30TruthScript` reads it). Each case compares a live twoway SVG with the dash page or app in the same session:
- S07's top-level helpers `_s07_svg`, `_s07_page` and `_s07_app` are reused;
- a new python helper `_s34_figs` and Stata helper `_s34_where` sit directly above S34's header;
- files are written only under `` `w30_work' `` and erased before the end line;
- `c(scheme)`, `sysdir` and `adopath` are saved before each case and restored after it.

`_s34_figs()` reads `S34_PAGE` (a saved page) or `S34_APP` (a served `app.py`). It sets `S34_BG`, each `Plot`'s `border_fill_color` in document order joined by `;`, read from the page's embedded models the way `_s07_page` reads them, or from `make_document(Document())`. For the app it then fires the `Select` whose `_dash_var` is `S34_MOVE` to its second option and sets `S34_BG_AFTER` and `S34_FIRED`.

`_s34_where` (Stata, `version 19`):
- runs `findfile` as the gate does and keeps `r(fn)`;
- runs `_dash_scheme_dirs`;
- calls a python helper that imports `dash_render` from `os.path.abspath("..")`, makes a `SchemeParser.__new__` probe with `_ado_dirs = dr._dash_scheme_dirs_of({"scheme_dirs": json.loads(<dirs>)})` and sets `S34_SAME` to 1 when `realpath(probe._resolve_path(name)) == realpath(r(fn))`.

Values cross only through `sfi.Macro` globals.

| Id | Placement | twoway side | dash side | PASS when |
|---|---|---|---|---|
| SP-10 | `scheme-sp10.scheme` R in the working directory | `scheme(sp10)` SVG | `dash scatter …, scheme(sp10)` page; `dash build, scheme(sp10)` page; `dash build, server filter(foreign, type(dropdown))` app with `S34_MOVE foreign` | bg `#ff0000` and marker `#008000` everywhere; app unchanged after the move; 0 notes |
| SP-11 | `sp11.scheme` B in cwd, `scheme-sp11.scheme` R in an `adopath +` dir | SVG | page | both `#ff0000` (form-major) |
| SP-12 | `site/s/scheme-sp12.scheme` R (`sysdir set SITE`), `scheme-sp12.scheme` B in cwd | SVG | page | both `#ff0000` |
| SP-13 | `scheme-s1mono.scheme` R and `s1mono.scheme` R in cwd | `scheme(s1mono)` SVG | page | twoway `#FFFFFF`; dash `#ffffff`, the shipped s1mono |
| SP-14 | `plus/s/scheme-sp14.scheme` R (`sysdir set PLUS`); `set scheme sp14` | unschemed SVG | unschemed `dash build` page and served app | all `#ff0000`; 0 notes |
| SP-15 | `sp15.scheme` (`#include sp15p`, `color p1 green`) in cwd, `scheme-sp15p.scheme` R in an added dir | SVG | page | bg `#ff0000`, marker `#008000`; 0 `not found` notes |
| SP-16 | `scheme-mono.scheme` R in an added dir; `set scheme mono`; then the dir is removed from the path | inherited SVG | inherited page; `scheme(mono)` page; after removal, `scheme(mono)` page | `#ff0000`, `#ff0000`, `#ff0000`, then `#ffffff` (s1mono alias) |
| SP-17 | registered g1 `scheme(s1mono)` and g2 `scheme(s1rcolor)` | each graph's SVG bg | `dash build` page; `dash build, server filter(foreign, type(dropdown))` app | twoway g1 `#FFFFFF` and g2 its s1rcolor background; saved `S34_BG` equals served `S34_BG` equals served `S34_BG_AFTER`, each equal to twoway's; no "draws one scheme" text in the log |
| SP-18 | the lk01-lk15, lk17, lk21 and lk22 placements recreated | `findfile` | `_s34_where` | `S34_SAME == 1` for each |

Each case ends `_w30_done SP-1k "<what>"`. No case prints SKIP.

**3. Area cases** in `test/test_custom_scheme.cscript`. Refusals, notes and return codes go after S33's last case block and before "Restore the session" (R1). They use the script's `_cs_run`/`_cs_expect`/`_cs_notes`/`_cs_page` helpers.

| Id | What | PASS when |
|---|---|---|
| SP-01 | `scheme(nosuchthing)` on `dash scatter`, `dash build` and `_dash_serve_spec` | rc 198 each; the log holds `scheme() must be one of economist, meta, s1color,` and `a theme (clean, dark, default, economist, mono, sj); or a scheme Stata finds along the ado-path as scheme-NAME.scheme or NAME.scheme (got: nosuchthing)` |
| SP-02 | `scheme(sub/x)` (with `sub/scheme-x.scheme` present), `scheme(a:b)` and `scheme(my theme)` (with `scheme-my theme.scheme` present) | rc 198 each, with `is not looked for`; no Traceback |
| SP-03 | `scheme-sp03.scheme` (`#include s2color`, `color background #3c4d5e`) in cwd; `scheme(sp03)` on scatter, build and `_dash_serve_spec` | rc 0 each; 0 notes; the page carries `#3c4d5e` |
| SP-04 | `sysdir set PERSONAL <cs_dir>/personal` holding `scheme-_SP04_.scheme` (grstyle's layout, `#4d5e6f`); `set scheme _SP04_`; unschemed build | rc 0; 0 notes; `#4d5e6f` |
| SP-05 | `sysdir set PLUS <cs_dir>/plus` holding `s/scheme-sp05.scheme` (`#5e6f70`); `scheme(sp05)` and then `set scheme sp05` with an unschemed build | rc 0 each; 0 notes; `#5e6f70` |
| SP-06 | `scheme-sp06.scheme` in an added dir, a symlink made with `shell ln -s` (both paths quoted) to `<cs_dir>/out/x.scheme` | `scheme(sp06)` rc 0; one note with `was not read`; page `#1e2d53` (s2color) |
| SP-07 | `scheme-sp07.scheme` of 1,048,577 bytes (`#include s2color`, then `*` comment lines) in cwd | rc 0; one note with `larger than 1,048,576 bytes`; page s2color |
| SP-08 | `scheme(dash-s2color)` with no working-directory file (the dash dir is on the path) | rc 198 (guard: `dash-` names stay working-directory only) |

Each case restores `sysdir`, `adopath` and `c(scheme)`. The script's file list at its end gains the new files.

**Run** (index "The cscript driver"):

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > <scratch>/s34/run_test_wp30_truth.do
WP30_ONLY=S34 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s34 <scratch>/s34/run_test_wp30_truth.do
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_custom_scheme.cscript > <scratch>/s34/run_test_custom_scheme.do
/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s34 <scratch>/s34/run_test_custom_scheme.do
```

The same driver form runs `test_help_claims_8.cscript` and `test_render_log_clean.cscript`.

## TDD test stubs

**Regression tests, failing at `batch-12-base`** (`test/test_scheme_lookup.py`, new):
- Fixtures are a `tmp_path` ado-path (`base/`, `site/`, `cwd/`, `personal/`, `plus/`, `oldplace/`, `add/`) and a spec helper that writes `build_options["scheme_dirs"]`.
- Rendering goes through `test_scheme_resolution._draw` in both modes.
- R/B file contents are as in "Stata truth".
- Notes are read from the recorded warnings.

**P1.25b:**
- Test: `test/test_scheme_lookup.py::TestStatasFileName::test_a_prefixed_file_is_found_in_both_modes[standalone|served]`. `scheme-w34x.scheme` R in `add/` and `scheme_dirs` set, named by build `scheme()`: `border_fill_color == "#ff0000"`, no warning. At base: s2color plus the inherited warning.
- Test: `…::TestStatasFileName::test_a_graph_level_name_is_found[mode]`, the same through `graph_options["scheme"]`.
- Test: `…::TestStatasFileName::test_the_session_scheme_is_found[mode]`, the same through `session_scheme`.
- Test: `…::TestStatasFileName::test_the_name_is_statas_not_the_file_name`. `SchemeParser("w34x", ado_dirs=…).name == "w34x"`.
- Test: `…::TestTheWalkIsStatas::test_the_fixture_is_stamped`. The fixture exists, with `_meta`'s four keys and 22 records.
- Test: `…::TestTheWalkIsStatas::test_each_measured_placement[lk01..lk22]`. Each record is recreated (REPO and BASE map to empty directories; `.` is the chdir'd `cwd`; a relative entry joins `cwd`) and the resolved realpath equals `findfile_rel`'s. lk16 resolves to `dash-s1mono.scheme`, lk19 raises `ValueError` matching "symlink", and lk20 raises "not found". For red or blue files `background_color` equals `twoway_bg.lower()`, and for lk17 `p_colors[0]` equals `twoway_marker.lower()`.
- Test: `…::TestShippedNamesComeFirst::test_a_working_directory_file_never_replaces_a_shipped_scheme[s2color.scheme|scheme-s2color.scheme|S2COLOR.scheme]`. The resolved basename is `dash-s2color.scheme`, with and without `scheme_dirs`, and the page border is s2color's in both modes.
- Test: `…::TestIncludeWalksTheAdoPath::test_an_include_of_a_prefixed_file[mode]`. `cwd/mine.scheme` holds `#include w34p` and `add/scheme-w34p.scheme` R: red, no note.
- Test: `…::TestThemeNamesAndFiles::test_an_inherited_theme_named_file_is_the_file[mode]`. `session_scheme "mono"` with `add/scheme-mono.scheme` R: red, no note. At base: s1mono, silent (critic G1).
- Test: `…::TestThemeNamesAndFiles::test_an_explicit_alias_loses_to_a_file[mode]`. Build `scheme(mono)` with the file: red.
- Test: `…::TestTheGuards::test_a_link_out_of_its_directory_is_not_read`. `add/scheme-w34y.scheme` links to `outside/x.scheme`: `SchemeParser("w34y", ado_dirs=…)` raises "symlink", and the `_open_spy` record is empty.
- Test: `…::TestTheGuards::test_a_file_over_the_cap_is_not_read`. A file of 1,048,577 bytes on the path raises "larger than".
- Test: `…::TestTheGuards::test_the_read_stops_at_the_cap`. A spy on `fh.read` sizes, with the file grown after the `_admit` check through a patched `os.path.getsize`: no read exceeds `_MAX_SCHEME_BYTES + 1`, and `ValueError`.
- Test: `…::TestTheGuards::test_a_swap_after_the_check_is_not_read`. With `os.path.getsize` patched to replace `add/scheme-w34s.scheme` by a link to `outside/x.scheme` after `_admit`'s containment check, `SchemeParser("w34s", ado_dirs=…)` raises "changed after it was checked" and `outside/x.scheme` is never parsed.
- Test: `…::TestTheGuards::test_a_fifo_is_not_opened`. `os.mkfifo(add/scheme-w34f.scheme)` raises "not a regular file" within 2 s.
- Test: `…::TestTheGuards::test_a_directory_named_like_a_scheme_is_not_read`. "not a regular file".
- Test: `…::TestTheGuards::test_scheme_dirs_input_is_bounded`. `_dash_scheme_dirs_of` on a non-list, 1,000 entries, a 5,000-character string, `"a\x00b"`, a relative path, a missing directory, a file, `"~"`, and the same directory twice: returns at most 64 realpaths, the valid ones only, in order, and never raises.
- Test: `…::TestTheGuards::test_the_directories_never_reach_the_page_or_the_app`. A `scheme_dirs` directory named `zz_s34_dirmark`: the saved page and the served `app.py` text do not contain it. At base the served app embeds it.
- Test: `…::TestTheGuards::test_a_session_scheme_refused_by_a_guard_says_why`. A session `w34y` (link out) gives one warning with "was found but not read" and s2color.
- Test: `…::TestTheNameRule::test_the_parser_reads_the_name_rule`:

  | Accepted | Refused |
  |---|---|
  | `w30x`, `w30-h`, `_GRSTYLE_`, `9x`, `a+b`, `.x`, `-x`, `x.y`, `grün`, `x.SCHEME` | `a b`, `a/b`, `a\b`, `a:b`, `..`, `a..b`, `a"b`, `` a`b ``, `a$b`, `"\x01"`, an 88-character name, `""` |

- Test: `…::TestTheRefusalNamesTheSchemes::test_the_help_shows_the_new_refusal`. dash.sthlp holds `dash build: scheme() must be one of ` followed by `", ".join(sorted(_BUILTIN_NAMES))`, then `; a theme (clean, dark, default, economist, mono, sj); or a scheme Stata finds along the ado-path as scheme-NAME.scheme or NAME.scheme (got: nosuchthing)`.
- Test: `…::TestThirdPartySchemes::test_a_plus_layout_is_found`. `plus/s/scheme-w34t.scheme` holds `#include s2mono` and `color p2 "0 114 178"`. It resolves, and `p_colors[1]` equals `OptionTranslator.stata_colour("0 114 178")`'s hex.
- Test: `…::TestThirdPartySchemes::test_an_ado_path_schemes_unread_directives_are_kept_silently[mode]`. `plus/s/scheme-w34u.scheme` holds `#include s2color`, `clockdir p 9` and `textboxstyle tick heading`. It resolves; the parser's `_props` holds both directives with their values, and so does the served app's property dict for it; no `dash scheme:` warning is recorded in either mode (S33's D-33d, ratification row 4). Red at the base only because the PLUS file is not found there.
- Test: `…::TestTheWalkStaysFast::test_256_unresolvable_includes_over_64_dirs`. It completes in under 2 s, with at most 11 include notes.

**P1.25.6 (saved first under its own heading in the failure file):**
- Test: `…::TestPerGraphSchemes::test_each_graph_is_drawn_in_its_own_scheme[mode]`. g1 `scheme(s1mono)`, g2 `scheme(s1rcolor)`: the figures' `border_fill_color` are `[s1mono's, s1rcolor's]` in both modes. At base the served app gives `[s1mono's, s1mono's]`.
- Test: `…::TestPerGraphSchemes::test_no_one_scheme_warning[mode]`. No message contains "draws one scheme".
- Test: `…::TestPerGraphSchemes::test_the_served_move_keeps_each_graphs_scheme`. After a dropdown move in the app (the `test_mode_parity._served_after_move` harness), g2's glyph colours equal the saved page's.
- Test: `…::TestPerGraphSchemes::test_one_parse_per_name_served`. Three graphs naming `b2inc` (an include-nowhere user file): each note once in the served build.
- Test: `…::TestThemeNamesAndFiles::test_a_graph_level_alias_is_the_alias_in_both_modes[mode]`. A graph-level `scheme(mono)` with no file: the figure border is s1mono's and there is no note. At base the saved page is s2color plus a note.
- Parity: `test/test_mode_parity.py` `CORPUS` gains, under `# WP-30 P1.25b: scheme lookup and each graph's own scheme`:
  - `_case("two graphs, two schemes", graphs=[("g1", [_sc()], {"scheme": "s1mono"}), ("g2", [_sc()], {"scheme": "s1rcolor"})])`;
  - `_case("graph-level theme alias mono", [_sc()], go={"scheme": "mono"})`.
- `MOVE_CORPUS` gains `_move_case("two graphs, two schemes, dropdown", _MOVES[0], graphs=[…the same…])`.
- At base, `TestTheTwoModesAgree::test_same_chrome`/`test_same_warnings` and `TestAFilterMoveAgrees::test_same_glyphs_after_the_move` fail for them.

**Guards (green at base, kept green):** E11's guard list, plus:
- `…::TestThemeNamesAndFiles::test_an_explicit_alias_without_a_file_is_the_alias[mode]`;
- `…::TestIncludeWalksTheAdoPath::test_an_include_nowhere_still_notes_once[mode]`;
- `…::TestTheGuards::test_hostile_directives_are_data`:
  - a scheme file of `#delimit ;`, `program define x`, `shell rm -rf /`, `` `=exec("1")' ``, `python: import os`, `<script>alert(1)</script>` as a colour, `color background "</style><script>"`, 10,000 `x` tokens and NUL bytes;
  - with `subprocess.Popen`, `os.system`, `builtins.exec` and `builtins.eval` patched to raise, it parses and renders in both modes;
  - neither page nor app contains `<script>alert`;
- `…::TestTheGuards::test_hostile_include_names_read_nothing_outside`: `#include ../../outside/x`, `#include /etc/hosts`, `#include a:b`, `#include add/..`; the `_open_spy` record is empty and each is noted once;
- `…::TestTheGuards::test_a_link_inside_its_directory_is_read`.

**Flips** (E11, each recorded as `Flipped: <node> -- <old expectation> was wrong because <why>` in `<scratch>/s34/34-flips.txt`). The reasons:
- precedence: "twoway draws BASE's scheme first, so a file named like a shipped scheme never replaces it (research t1/t3, M7, P1.25.3)";
- prefixed include: "Stata's setscheme tries scheme-NAME.scheme first (scheme.class:172-173)";
- PLUS: "M7 reads the whole ado-path";
- refusal text: "the refusal now lists the twenty-six names and the themes (REM-§3-e)";
- inherited scheme: "a scheme Stata found is now found by dash (GAPS2-X5-c)";
- one-scheme warning: "each graph is drawn in its own scheme in both modes (P1.25.6, A80)";
- INST-05: "a shipped name never consults the working directory, so the link is never opened";
- INST-18: "set scheme also tries NAME.scheme (measured), so the help's phrase was wrong";
- log-clean control: "an inherited scheme Stata found no longer notes; the control is now an #include that resolves nowhere".

## Test plan

| What | How | Fixture / truth | Both modes? |
|---|---|---|---|
| `scheme-NAME.scheme` on every entry point and inherited | pytest `TestStatasFileName`; cscript SP-03, SP-10, SP-14 | twoway SVG in the same session | yes, plus served after a move (SP-10) |
| Stata's walk order, letter subdirectories, SITE/PERSONAL/PLUS/OLDPLACE, relative entries | pytest `TestTheWalkIsStatas` over the fixture; cscript SP-11, SP-12, SP-18 | `scheme_lookup_truth.json`; live `findfile` | parser (resolution precedes both modes) |
| Shipped first | pytest `TestShippedNamesComeFirst`; flips of :827 and INST-08; SP-13 | twoway SVG | yes |
| `#include` on the walk | pytest `TestIncludeWalksTheAdoPath`; SP-15 | twoway SVG | yes |
| Theme names | pytest `TestThemeNamesAndFiles`; SP-16; parity "graph-level theme alias mono" | twoway SVG | yes |
| Per-graph schemes (P1.25.6) | pytest `TestPerGraphSchemes`; parity CORPUS and MOVE_CORPUS; SP-17 | twoway per-graph SVG | yes, before and after a move |
| Refusal text and name rule | pytest `TestTheNameRule`, `TestTheRefusalNamesTheSchemes`; SP-01, SP-02, CS-06/07/09/13, HC8-08, OV-144/145 | — | Stata gate (both routes) |
| Guards (link, size, FIFO, directory, hostile text, hostile includes, bounded dirs, no directory in output) | pytest `TestTheGuards`, `TestTheWalkStaysFast`; `test_scheme.py::TestSecurity`; `test_security_surface.py::TestSchemeFileContainment`; SP-06, SP-07 | — | yes (page and app grep) |
| Third-party forms, retained directives and silence (S30; S33's D-33d) | pytest `TestThirdPartySchemes`; SP-05 | — | yes |
| Registries | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |

**Acceptance criteria.**
- **AC-34.1** `scheme(w34x)` with `scheme-w34x.scheme` anywhere on the ado-path draws it with rc 0 and no note, on `dash` *plottype*, `dash build` and `_dash_serve_spec`, in the page and the served app, before and after a dropdown move (SP-03, SP-10, `TestStatasFileName`).
- **AC-34.2** For each of the 22 fixture placements, dash resolves the file `findfile` returns (SP-18, `test_each_measured_placement`). The two documented exceptions are lk16 (shipped) and lk19 (link).
- **AC-34.3** After `set scheme` of a PERSONAL, PLUS or ado-path scheme, an unschemed dashboard draws it with 0 notes (SP-04, SP-05, SP-14, CS-10 flipped, HC8-10 flipped).
- **AC-34.4** A working-directory `s2color.scheme` or `scheme-s1mono.scheme` changes nothing dash draws (SP-13, `TestShippedNamesComeFirst`).
- **AC-34.5** The refusal is r(198) and reads, word for word, the SP-01 text on all three routes. A path-like name adds the `is not looked for` sentence (SP-02).
- **AC-34.6** A linked-out, oversized, FIFO or directory candidate is never opened or read past 1,048,577 bytes. It draws s2color with one note and rc 0 (SP-06, SP-07, `TestTheGuards`).
- **AC-34.7** Two graphs with two schemes draw identically in the saved page and the served app, before and after a move, equal to twoway's per-graph backgrounds, with no "draws one scheme" text (SP-17, CORPUS/MOVE_CORPUS). A graph-level `scheme(mono)` draws s1mono in both modes.
- **AC-34.8** No `scheme_dirs` entry appears in a saved page or an `app.py`.
- **AC-34.9** G3 (`test_mode_parity.py`), G4 and the registries are green. `SP-0[1-8] PASS` and `SP-1[0-8] PASS` appear 17 times in total, with no FAIL or SKIP.
- **AC-34.10** The full suite is green once in the worktree (E1, E6).

## Tasks

**Commit boundary.** Tasks 34-01 to 34-13 form the one P1.25b commit, made by 34-13 on `wp30-s34` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s34` after one full run through the queue. Its subject is `Find schemes along Stata's ado-path as twoway does (WP-30 P1.25b)`.
- The body opens with `<scratch>/34-P1.25b-failure.txt`.
- It then gives the measured defects and what changed where, in both renderers.
- It names the threats closed (path traversal, link escape, resource exhaustion through size or FIFO, code execution from scheme text, disclosure of directory names; G9).
- It then carries one line each of:
  - `Regression: test/test_scheme_lookup.py::<Class>::<test> -- failed at <batch-12-base sha> with <text>` (P1.25.6's tests first);
  - `Flipped: <node> -- …` (from `<scratch>/s34/34-flips.txt`);
  - `Fixture: test/fixtures/scheme_lookup_truth.json (scripts/extract_scheme_lookup_truth.do)`;
  - `BUGS.md: "scheme(NAME) is looked for in two places only, never along Stata's ado-path or under Stata's scheme-NAME.scheme file name, and its refusal does not list the valid names" (closed)` (section-01's Appendix B title, verbatim);
  - `BUGS.md: "A graph's own scheme() was drawn differently on the saved page and in the served app" (added closed)`.
- G7 holds throughout. Every command runs from `$WT`.

<task type="auto" id="34-01">
  <name>Write the failing pytest regression tests</name>
  <files>test/test_scheme_lookup.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Check the cut: `git -C $WT rev-parse HEAD` equals `cat <scratch>/batch-12-base.txt`, and `git -C $WT branch --show-current` prints `wp30-s34`. Check that `<scratch>/batch-12-impact.txt` holds every row of Evidence E12 and records the maintainer's approval of the four `_generate_app_source` lines (Q1). If that approval is absent, stop and report. Run `mkdir -p <scratch>/s34`.

    Create `test/test_scheme_lookup.py` with every class and test of "TDD test stubs", the module docstring quoting E7, E8 and E9's measurements, and the helpers named there. Append the two CORPUS cases and the MOVE_CORPUS case at the end of their lists in test_mode_parity.py under `# WP-30 P1.25b: scheme lookup and each graph's own scheme` (R8; `ALLOWED` and `_MUST_WARN` are not edited).

    Run `python3 -m pytest test/test_scheme_lookup.py -q -n0 -p no:cacheprovider -rf > <scratch>/s34/34-01.log 2>&1`, then `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "two_schemes or theme_alias or two graphs" -rf >> <scratch>/s34/34-01.log 2>&1`. Write `<scratch>/34-P1.25b-failure.txt` with the base sha, P1.25.6's failing nodes under the heading `P1.25.6`, then P1.25b's, each with its one-line reason, then the guard tests that passed. Do not commit, and do not weaken a test to pass.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s34/34-01.log` is at least 30; `grep -c "TypeError\|AttributeError\|ValueError\|assert" <scratch>/s34/34-01.log` is at least 10; `grep -c "^P1.25.6" <scratch>/34-P1.25b-failure.txt` prints 1; `git -C $WT status --porcelain` lists only the two test files.]]></verify>
  <done>Every pytest regression test of the section existed and was shown failing on the unmodified tree, with P1.25.6's failures saved first.</done>
</task>

<task type="auto" id="34-02">
  <name>Write the cscript cases red</name>
  <files>test/test_wp30_truth.cscript, test/test_custom_scheme.cscript</files>
  <action><![CDATA[
    Confirm with `grep -n "def _s07_page\|def _s07_svg\|def _s07_app" test/test_wp30_truth.cscript` that S07's helpers exist at the base; if any is missing, stop and report. In test_wp30_truth.cscript, add `_s34_figs` (python, top level) and `_s34_where` (Stata, `version 19`) directly above `* ==== S34 P1.25b:` and write SP-10 to SP-18 of "Stata truth 2" between S01's `S34 start` and `S34 end` lines; add the block to the script's header list. No Python line inside the gate holds a brace; every file goes under `` `w30_work' ``; `c(scheme)`, `sysdir` and `adopath` are restored after each case.

    In test_custom_scheme.cscript:
    - append SP-01 to SP-08 of "Stata truth 3" after the last case block before "Restore the session", and add their files to the erase list and their rows to the header comment;
    - flip CS-06, CS-07, CS-09 and CS-13's needle to `scheme() must be one of economist, meta,`;
    - flip CS-10: add `file write `fh' "color background #2a3b4c" _n` after the `#include s2color` line of scheme-zzdashtest.scheme (:211-213), then `_cs_notes CS-10 "`lg'" 0` and `_cs_page CS-10 "b.html" "#2a3b4c" 1`, and rewrite its header line and `_cs_done` text.

    Append each flip to `<scratch>/s34/34-flips.txt`. Run both scripts through the driver ("Stata truth", Run; WP30_ONLY=S34 for the truth script) and append every `FAIL` line to `<scratch>/34-P1.25b-failure.txt` under `cscript`.
  ]]></action>
  <verify><![CDATA[`grep -o "SP-1[0-8] FAIL" <scratch>/s34/run_test_wp30_truth.log | sort -u | wc -l` prints 9 (at base every case is red: SP-13 because HEAD reads the cwd `s1mono.scheme` first, SP-18 because `_dash_scheme_dirs` does not exist); `grep -o "SP-0[1-7] FAIL\|CS-0[679] FAIL\|CS-1[03] FAIL" <scratch>/s34/run_test_custom_scheme.log | sort -u | wc -l` prints 12; `grep -c "SP-08 PASS" <scratch>/s34/run_test_custom_scheme.log` prints 1; `grep -c "SKIP" <scratch>/s34/run_test_wp30_truth.log` prints 0.]]></verify>
  <done>Stata's own drawing was compared with dash's for every placement in one truth block, the refusals and guard notes were checked in the area script, and both failed on the unmodified tree as recorded.</done>
</task>

<task type="auto" id="34-03">
  <name>Measure Stata's lookup into a fixture</name>
  <files>scripts/extract_scheme_lookup_truth.do, test/fixtures/scheme_lookup_truth.json</files>
  <action><![CDATA[
    Create scripts/extract_scheme_lookup_truth.do as "Stata truth 1" specifies: S02's root selection copied from an extractor S02 converted, then `adopath ++ "<root>/"` and `global dash_nobrowser 1`, the 22 cases, the saved and restored sysdir paths and pwd, and a python block that writes the fixture with the D12 `_meta` stamp (no shell=True; the commit read from the file `shell git … > <work>/git_head.txt` wrote). Run it through the slot (Run line). Compare the log's per-case values with "Expected"; a mismatch stops the task and is reported, never edited. Then `git add -f test/fixtures/scheme_lookup_truth.json` and `git add scripts/extract_scheme_lookup_truth.do`. Run `python3 -m pytest test/test_scheme_lookup.py -q -n0 -p no:cacheprovider -k fixture_is_stamped`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/scheme_lookup_truth.json'));print(len([k for k in d if k!='_meta']), sorted(d['_meta']))"` prints `22 ['born_date', 'dash_commit', 'extracted', 'stata_version']`; `python3 -c "import json;d=json.load(open('test/fixtures/scheme_lookup_truth.json'));print(d['lk04']['twoway_bg'], d['lk16']['findfile_rel'], d['lk20']['set_scheme_rc'])"` prints `#FF0000 BASE/s/scheme-s1mono.scheme 111`; the stamped test passes.]]></verify>
  <done>twoway's lookup over 22 placements was measured in Stata and committed as a stamped fixture that the walk tests read.</done>
</task>

<task type="auto" id="34-04">
  <name>Flip the precedence and include pins</name>
  <files>test/test_scheme_resolution.py, test/test_installed_layout.py, test/test_help_claims_8.py</files>
  <action><![CDATA[
    Flip in place, keeping each node's name. For each, append a `Flipped:` line with E11's reason to `<scratch>/s34/34-flips.txt`.
    - test_scheme_resolution.py:827 `test_a_scheme_file_in_the_working_directory_still_wins`: `s2color` resolves to the staged `dash-s2color.scheme`; `mytheme` (both spellings) still resolves to the cwd file. Rewrite the docstring and add a comment naming P1.25b.
    - test_installed_layout.py INST-08 `test_the_cwd_still_wins_over_the_install`: the shipped file wins. INST-05 `test_a_cwd_symlink_named_after_a_builtin_cannot_reach_the_install`: `_resolve_path("s2color.scheme")` returns `root/d/dash-s2color.scheme` (realpath), and a spy on `module.open` records no read of the link's target. INST-18: replace the `set scheme` phrase with TR-34.19's corrected phrase. Also rewrite `test_the_help_never_offers_set_scheme_dash`'s docstring ("tries scheme-NAME.scheme first"), keeping its asserts.
    - test_help_claims_8.py `TestWhatAnIncludeResolvesTo`: `test_the_working_directory_first` asserts the translation's background, and `test_never_statas_own_prefixed_file` asserts `#ff00ff`. Rewrite the class docstring to the new rule. `test_all_twenty_and_nothing_else` keeps its asserts and adds `assert mod.SchemeParser.can_resolve("zzthird", ado_dirs=(str(root),))`.

    Run the three files on the unmodified renderer and append their red nodes to the failure file under `Pinned, red at base after the flip`.
  ]]></action>
  <verify><![CDATA[`grep -c "^Flipped:" <scratch>/s34/34-flips.txt` is at least 12 (34-02's five plus these seven); `python3 -m pytest test/test_scheme_resolution.py test/test_installed_layout.py test/test_help_claims_8.py -q -p no:cacheprovider -rf` fails in exactly the flipped nodes.]]></verify>
  <done>The pins of today's working-directory precedence, include rule and PLUS refusal asserted the new rule and kept their names, with each flip recorded.</done>
</task>

<task type="auto" id="34-05">
  <name>Flip the warning and log pins</name>
  <files>test/test_immediate_scheme.py, test/test_help_claims_8.cscript, test/test_render_log_clean.cscript</files>
  <action><![CDATA[
    - test_immediate_scheme.py:87 `test_the_first_graphs_scheme_wins_and_the_conflict_is_reported`: record warnings with `warnings.catch_warnings(record=True)` and assert none contains "draws one scheme". Then assert `r.scheme.name == "economist"`, and that `r.figures`' two figures carry economist's and s1mono's `border_fill_color` respectively. Rewrite the docstring (P1.25.6).
    - test_help_claims_8.cscript HC8-08: the scheme needle becomes the full SP-01 build refusal for `nosuchthing`. HC8-10: after `set scheme zzdashtest`, 0 notes and `#1e2d53` present (the file includes s2color); rewrite its header line (:38-39) to "an inherited session scheme Stata found: rc 0, no note, drawn".
    - test_render_log_clean.cscript check 5: write `#include zzdashrlcnone` instead of `#include s2color` (:176) and keep `nctl == 1`, now the include note. Rewrite the comment (:156-167) to say so.

    Append a `Flipped:` line for each to `<scratch>/s34/34-flips.txt`. Run test_immediate_scheme.py on the unmodified renderer and both cscripts through the driver, and append their red results to the failure file.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_immediate_scheme.py -q -n0 -p no:cacheprovider -k conflict` fails at base; `grep -c "HC8-08 FAIL\|HC8-10 FAIL" <scratch>/s34/run_test_help_claims_8.log` prints 2 at base; `grep -c "zzdashrlcnone" test/test_render_log_clean.cscript` is at least 1.]]></verify>
  <done>The pins of the one-scheme warning, the old refusal words and the inherited-scheme control asserted the new behaviour, each flip recorded with its reason.</done>
</task>

<task type="auto" id="34-06">
  <name>Walk the ado-path in SchemeParser</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Before editing, run `gitnexus impact _resolve_path -d upstream -r dash` (and for resolve_or_fallback, _include, _parse_lines, can_resolve) in the main checkout if 12.0's record lacks them, and report any HIGH. Make TR-34.1 to TR-34.9 in `SchemeParser`:
    - the three class constants;
    - `_scheme_name_ok`, `_shipped_path`, `_ado_candidates`, `_admit`, `_read_scheme_lines` and `unresolved_reason`;
    - `__init__`'s `ado_dirs` and name rule;
    - the rewritten `_resolve_path`;
    - `_parse_lines`' read through `_read_scheme_lines`;
    - `can_resolve`/`resolve_or_fallback`'s `ado_dirs`;
    - `_include`'s clause.

    No module-level name is read by a method. `stat` is a local import, and the opener is a lambda. Run `python3 -m pytest test/test_scheme_lookup.py -q -n0 -p no:cacheprovider -k "Walk or Guards or NameRule or Include or Shipped or ThirdParty or Fast"` and `python3 -m pytest test/test_scheme.py test/test_security_surface.py test/test_installed_layout.py -q -p no:cacheprovider -k "Security or Containment or Installed or INST"`.
  ]]></action>
  <verify><![CDATA[Both runs report 0 failed except `TestTheGuards::test_the_directories_never_reach_the_page_or_the_app` and `test_a_session_scheme_refused_by_a_guard_says_why` (34-07/34-08); `python3 -c "import dash_render as d;print(d.SchemeParser._MAX_SCHEME_BYTES, d.SchemeParser._scheme_name_ok('a b'), d.SchemeParser._scheme_name_ok('a+b'))"` prints `1048576 False True`.]]></verify>
  <done>SchemeParser found a scheme it does not ship as Stata's findfile does, shipped names first, and read only named, contained, regular files under the size cap.</done>
</task>

<task type="auto" id="34-07">
  <name>Resolve names by one rule in both renderers</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-34.10 (`_DASH_MAX_SCHEME_DIRS`, `_dash_scheme_dirs_of`, `_dash_scheme_choice`, above `_resolve_scheme_name`), TR-34.11 (`_resolve_scheme_name`'s `scheme_dirs` argument, the one-scheme warning deleted, the choice, the found-but-not-read text) and TR-34.12 (DashRenderer `__init__` reads and pops `scheme_dirs`; `_scheme_for` passes `ado_dirs`; `_make_figure`'s one call goes through `_dash_scheme_choice(…, "graph", …)`). `_make_figure` and `_scheme_for` are CRITICAL: confirm the 12.0 approval names them. Edit nothing else in `_make_figure` and nothing in `_make_figure_body`. Run `python3 -m pytest test/test_scheme_lookup.py test/test_scheme_resolution.py test/test_immediate_scheme.py test/test_theme_aliases.py test/test_server_scheme.py -q -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[That run reports 0 failed except the served-only nodes of `TestPerGraphSchemes` and `test_the_directories_never_reach_the_page_or_the_app`; `grep -c "draws one scheme" dash_render.py` prints 0.]]></verify>
  <done>The dashboard's scheme, a graph's own scheme and an inherited c(scheme) were named by one rule that walks the ado-path, theme names lost to a file of that name, and the false one-scheme warning was gone.</done>
</task>

<task type="auto" id="34-08">
  <name>Carry each graph's scheme into the app</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Make TR-34.13:
    - in `ServerAppBuilder.__init__`, read and pop `scheme_dirs` before `_spec_str`, pass the directories, and call the new `_resolve_graph_schemes`;
    - in `_glyph_layer_lines`, add the emitted `_GRAPH_SCHEME_PROPS`, `_DASH_GRAPH_SCHEMES`, `_dash_graph_scheme` and `_dash_under_graph_scheme` after `_DASH_MAPPER`;
    - in `_generate_app_source`, change exactly the four lines quoted in TR-34.13.

    Before editing, check that each of those four lines still reads as quoted at this tree. If one differs, stop and report (R12). Run:
    - `python3 -m pytest test/test_scheme_lookup.py test/test_mode_parity.py test/test_server_facets.py test/test_immediate_scheme.py -q -p no:cacheprovider`;
    - `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0 -p no:cacheprovider`.
  ]]></action>
  <verify><![CDATA[Both runs report 0 failed; `git -C $WT diff -U0 dash_render.py | grep -c "^+.*_dash_under_graph_scheme(.*_dash_figure_for\|^+.*lambda frame: _dash_under_graph_scheme"` prints 4.]]></verify>
  <done>The served app drew each graph in its own scheme, from property dicts written at build time, before and after a filter move, and no directory name reached the app.</done>
</task>

<task type="auto" id="34-09">
  <name>Gate and pass the ado-path from Stata</name>
  <files>dash.ado, dash_parse.mata</files>
  <action><![CDATA[
    Make TR-34.14 in dash.ado:
    - the new `_dash_scheme_dirs` program after the END sentinel;
    - the two writers' calls and `scheme_dirs` keys;
    - the gate's name rule, findfile pair, `dash-` rule, refusal list and `extra` sentence;
    - the rewritten comments;
    - `_dash_scheme_dirs_json` in `_needed`.

    Make TR-34.15 in dash_parse.mata: `_dash_scheme_dirs_json()` after `_dash_json_str_args()`, and its header-index entry. Every new program opens `version 19`. Run `python3 -m pytest test/test_option_validation.py test/test_security_surface.py test/test_scheme_resolution.py -q -p no:cacheprovider -k "scheme or master or ado"`, then the area script and the truth block through the driver.
  ]]></action>
  <verify><![CDATA[`grep -c "SP-0[1-8] PASS" <scratch>/s34/run_test_custom_scheme.log` prints 8 and its log ends `ALL CHECKS PASSED`; `grep -c "SP-1[0-8] PASS" <scratch>/s34/run_test_wp30_truth.log` prints 9 and `grep -c " FAIL\|SKIP" <scratch>/s34/run_test_wp30_truth.log` prints 0; `grep -c '"scheme_dirs"' dash.ado` prints 2.]]></verify>
  <done>dash.ado accepted a scheme Stata finds by name, refused paths and unknown names with the full list, and wrote the ado-path into every spec it builds.</done>
</task>

<task type="auto" id="34-10">
  <name>Register the new names in the maps</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[Add TR-34.17's eleven `function_test_map.py` keys under the S34 anchor `# WP-30 S34 (P1.25b): …`, and the two `program_coverage_map.py` entries under S34's anchors in `COVERAGE["dash.ado"]` and `COVERAGE["dash_parse.mata"]`, each alphabetical. Run `python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py test/test_no_orphans.py -q -n0 -p no:cacheprovider`.]]></action>
  <verify><![CDATA[That run reports 0 failed; `grep -c "test_scheme_lookup.py" test/function_test_map.py` prints 11.]]></verify>
  <done>Every new function, method, Stata program and Mata function named the test that exercises it.</done>
</task>

<task type="auto" id="34-11">
  <name>Certify in both modes against Stata</name>
  <files>none</files>
  <action><![CDATA[
    Run every scheme test file:
    - `python3 -m pytest test/test_scheme_lookup.py test/test_scheme.py test/test_scheme_resolution.py test/test_scheme_fidelity.py test/test_scheme_consumption.py test/test_scheme_linewidth.py test/test_scheme_rendered_output.py test/test_scheme_fallback_provenance.py test/test_scheme_layer_alpha.py test/test_twenty_six_schemes.py test/test_installed_layout.py test/test_immediate_scheme.py test/test_theme_aliases.py test/test_server_scheme.py test/test_help_claims_8.py test/test_security_surface.py -q -p no:cacheprovider` (omit a name `ls` does not find at this tree);
    - G3: `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider`;
    - G4 and the registry tests of R2.

    Then run these cscripts through the driver: test_wp30_truth (WP30_ONLY=S34), test_custom_scheme, test_help_claims_8, test_render_log_clean, test_option_validation and test_render_locate. A failure in a file this section did not list is a pin E11 missed. Flip it in place with a `Flipped:` line; never delete it. Afterwards check that `~/.stata19/console/stata19.rc` still holds `python_exec` (a SKIP is not a pass).
  ]]></action>
  <verify><![CDATA[Every pytest run reports 0 failed; every cscript log ends with its `ALL CHECKS PASSED` line; `grep -c "SKIP" <scratch>/s34/run_*.log | grep -v ":0"` prints nothing.]]></verify>
  <done>The lookup, the guards and the per-graph schemes were certified against twoway and in both modes, before and after a move, with every scheme test green.</done>
</task>

<task type="auto" id="34-12">
  <name>Correct the scheme help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Edit only these paragraphs (R3), keyed by their text, because line numbers moved in earlier batches:
    1. **:703-707** ("A scheme name: {cmd:scheme()} must be …") becomes: `{cmd:scheme()} must be a shipped scheme, a {cmd:theme()} name or a scheme Stata finds along the ado-path, {cmd:scheme-}{it:name}{cmd:.scheme} or {it:name}{cmd:.scheme}, wherever it is written`. Keep the link.
    2. **The intro** ("{cmd:scheme()} applies a named Stata graph scheme to the whole dashboard.") gains: `A {cmd:scheme()} written on one graph draws that graph in it, in the saved page and the served app alike; the page and the KPI cards take the dashboard's scheme ({cmd:dash build}'s {cmd:scheme()}, then {cmd:theme()}, then the first graph's, then {cmd:c(scheme)}).`
    3. **"A scheme of your own."** Replace its first five sentences and its PLUS/copy sentences ("A scheme another package installed into {cmd:PLUS} is not read … Copy the file into the working directory instead.") with the rule of BR-34.1 to BR-34.4:
       - `scheme-`/`NAME.scheme` in each directory of the ado-path in turn ({cmd:BASE}, {cmd:SITE}, the working directory, {cmd:PERSONAL}, {cmd:PLUS}, {cmd:OLDPLACE}, directories added with {cmd:adopath}), each with its first-letter subdirectory, as {cmd:findfile} looks;
       - every entry point and {cmd:c(scheme)};
       - the twenty-six shipped names first, as Stata's own are in {cmd:BASE}, so a working-directory {cmd:s2color.scheme} or {cmd:scheme-s2color.scheme} replaces nothing;
       - a {cmd:theme()} name given to {cmd:scheme()} is a file of that name when Stata finds one;
       - and the four safety differences: a name, never a path (`a blank, a quote, a slash or backslash, a colon or {cmd:..}` is refused, where {cmd:twoway} follows a relative path); a regular file of at most 1,048,576 bytes inside the directory it was found in, so a link out of it is not followed; a {cmd:dash-} name read only from the working directory; read as data, never run.

       Then add: `A file refused this way is named in a note and {cmd:s2color} is drawn.` Keep the sentences on tokenising, unreadable lines and quoted values.
    4. **"A name that resolves to nothing is refused."**
       - The example line becomes the SP-01 build refusal for `nosuchthing`.
       - "neither a shipped scheme, one of the theme() aliases nor a .scheme file in the working directory" becomes "neither a shipped scheme, a {cmd:theme()} name nor a scheme Stata finds".
       - The session sentence becomes: `The session's own {cmd:c(scheme)}, inherited when you name none, is looked up the same way, so a scheme {cmd:set scheme} accepted is drawn; it is never refused, and when {cmd:dash} cannot read it -- a file the rules above refuse -- a note says why and {cmd:s2color} is drawn.`
    5. **"What a scheme file of yours may include."** The resolution sentence becomes: `an {cmd:#include} is resolved as {cmd:scheme()} itself is -- one of the twenty-six translations, or {cmd:scheme-}{it:name}{cmd:.scheme} then {it:name}{cmd:.scheme} along the ado-path`. The "resolves to neither" list becomes `(a scheme nowhere on the ado-path, or a path)`.
    6. **"Where the shipped schemes live after an install."**
       - "and for nothing else … stays unread" becomes `; a name it does not ship is looked for along the ado-path as Stata looks for it, so another package's file in the same directory is read only when you name it`.
       - The last sentence becomes: `A {cmd:.scheme} file in the working directory no longer wins over the shipped one of the same name, as it never does in {cmd:twoway}.`
    7. **"Why they are named …"** The `set scheme` sentence becomes: `{cmd:set scheme} {it:name} finds Stata's own {cmd:scheme-}{it:name}{cmd:.scheme} in {cmd:BASE} first, so it never reads them`. This is the phrase INST-18 now pins.

    Run `python3 -m pytest test/test_help_conformance.py test/test_help_claims_8.py test/test_installed_layout.py test/test_scheme_lookup.py -q -p no:cacheprovider -k "help or Help or INST or Refusal"` and every `test/test_help_claims_*.py` that quotes these paragraphs (`grep -l "working directory\|scheme-" test/test_help_claims_*.py`).
  ]]></action>
  <verify><![CDATA[Those runs report 0 failed; `grep -c "Copy the file into the working directory" dash.sthlp` prints 0; `grep -c "still wins over the" dash.sthlp` prints 0; `grep -c "along the ado-path" dash.sthlp` is at least 4.]]></verify>
  <done>The help stated twoway's lookup rule, the shipped-first precedence, the theme-name rule, the four safety differences and the new refusal, and the failing copy remedy was gone.</done>
</task>

<task type="auto" id="34-13">
  <name>Close P1.25b and commit it</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    1. **BUGS.md.** Close `WP30_OPEN["P1.25b"]`'s entry in place (`- [x]`) and replace its Resolution with Notes "BUGS P1.25b". Append at the end of BUGS.md, after one blank line, the closed entry of Notes "BUGS P1.25.6" (A146; no `"` in the title; the file ends with one newline).
    2. **test_tracking_documents.py.** Delete the `"P1.25b"` key line from `WP30_OPEN`. In `WP30_LISTS`, change `"P1.25b"`'s lists to add `"Changed behaviour"` (R4), in the row's existing order form.
    3. **CHANGELOG.md.** Replace `<!-- WP-30 P1.25b -->` in the WP-30 group of `### Results that change` with Notes "CHANGELOG Results" (two lines), and in `### Security` with Notes "CHANGELOG Security". Add Notes "CHANGELOG Changed" at the end of `### Changed behaviour (may need your do-files changed)`, in entry order: after the last P1.24-or-earlier line or marker and before the first P1.26-or-later one.
    4. **Checks.** Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Then run `git -C $WT merge --no-edit main` (expect `Already up to date.`). Then run one full suite: `<scratch>/full_suite_queue.sh $WT <scratch>/34-full-1.log` in the background, waiting for its `exit=` line (E1, E6).
    5. **Staging.** Stage only:
       - `dash_render.py dash.ado dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md scripts/extract_scheme_lookup_truth.do`;
       - the test files of 34-01 to 34-10 and any 34-11 flip;
       - `git add -f test/fixtures/scheme_lookup_truth.json`.

       Check `git diff --cached --name-only` against that list (G6; never CLAUDE.md, .gitignore, AGENTS.md or .ultraplan/).
    6. **Commit.** Write `<scratch>/s34/msg.txt` in the boundary's form. Run G7 before and after `git commit -F <scratch>/s34/msg.txt`. Confirm `git -C $WT branch --show-current` prints `wp30-s34`, and report the sha.
  ]]></action>
  <verify><![CDATA[`tail -1 <scratch>/34-full-1.log` prints `exit=0` with no `failed` or `error` in the summary above it; `git log -1 --format=%s` ends `(WP-30 P1.25b)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.25b -->' CHANGELOG.md` prints 0; `grep -c '^    "P1.25b": "' test/test_tracking_documents.py` prints 0; `grep -c "(WP-30, P1.25b)" CHANGELOG.md` prints 4; `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>P1.25b was closed and P1.25.6 appended closed in BUGS.md naming tests that exist, the key was removed, the CHANGELOG markers became measured lines in three lists, and one green commit on wp30-s34 was ready for the merger.</done>
</task>

## Section completion criteria

- A scheme dash does not ship, named or inherited or `#include`d, resolves to the file Stata's `findfile` returns over the 22 measured placements (two documented exceptions) and is drawn as twoway draws it, in the saved page and the served app, before and after a filter move.
- The twenty-six shipped names always draw dash's translation. A theme name given to `scheme()` is a file of that name when Stata finds one.
- Paths and unsafe names are refused r(198) before any lookup. Refused files (link out, oversized, FIFO, directory) are never opened or over-read, and draw s2color with one note. Scheme text is never run, and directory names never reach the page or the app.
- The refusal lists the twenty-six names and the six themes, word for word as the help shows.
- Two graphs with two schemes draw identically in both modes, with no "draws one scheme" warning, and a graph-level `scheme(mono)` draws s1mono in both modes.
- `scheme_lookup_truth.json` is committed and stamped. The S34 truth block prints SP-10..SP-18 PASS, and test_custom_scheme prints SP-01..SP-08 PASS and CS-06/07/09/10/13 PASS.
- One green commit `(WP-30 P1.25b)` on `wp30-s34`, with its failure text, `Regression:`/`Flipped:`/`Fixture:`/`BUGS.md:` lines and the threats named.
- P1.25b closed in place and its key deleted. P1.25.6 appended closed. Four `(WP-30, P1.25b)` CHANGELOG lines in three lists, with `WP30_LISTS` updated.

## Notes

- **Maintainer question (Q1, the R12 exception).** TR-34.13's four `_generate_app_source` lines are the only template edits. S35 is batch 12's template editor. **Recommendation: grant the exception at 12.0.** The four lines (:35093, :35562, :35584, :35646) are disjoint from every S35 template hunk (section-35 names its hunks and says it will not touch these four), S34 lands first, and each edit is a one-line wrap. The orchestrator records the maintainer's approval in `<scratch>/batch-12-impact.txt` at 12.0, and 34-01 stops if it is absent. If the exception is refused, P1.25.6's served half moves to batch 13's template editor (S38), which then owns TR-34.13's emitted names, the four lines and the P1.25.6 entry. S34 then keeps the rest, and its `TestPerGraphSchemes` served nodes and the two-schemes parity cases move with it.
- **Shared mutable state.** `_dash_under_graph_scheme` swaps the module globals `_DASH_SCHEME` and `_DASH_MAPPER.scheme` for one synchronous call, exactly as `_dash_figure_for` already sets `_DASH_MAPPER.z_options` and `colorvar_domain`. Today every call runs on the Bokeh IO loop. **For S57 (batch 20):** the recompute worker must hold the same lock around `_dash_under_graph_scheme(g, _redraw, frame)` as around any other `_DASH_MAPPER` mutation. Name this in S57's thread-safety test.
- **Messages kept for tests.**
  - "outside allowed" is in the name-rule error (`test_scheme.py::TestSecurity::test_path_traversal_raises`, `_include`'s clause).
  - "symlink" is in the link error (BUG-51 tests, `TestSchemeFileContainment`).
  - "Built-in schemes" is in the not-found error (INST-16).
  - The inherited-warning text is unchanged (`_assert_unknown_warning`, HC8-10's old needle is flipped).
- **The no-dirs fallback.** A spec without `scheme_dirs` (pytest, scripts/regen_*, a hand-built spec) walks the working directory and `_SCHEME_SEARCH_DIRS`, today's set, under both file names. That is why `TestSchemeFileContainment`'s search-dir cases stay unchanged. dash.ado always writes `scheme_dirs`, so a real build walks Stata's path only.
- **Stata caches a loaded scheme by name** for the session (HC8-13). Every case name in the extractor, the truth block and the area script is used once per session.
- **python_exec hazard** (project memory). Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. A truth script then exits 222, and a SKIP is not a pass. Check it after 34-02, 34-09 and 34-11.
- **Python inside a gated cscript block holds no brace.** Helpers sit above S34's header (R1).
- **Shared files.**
  - **R1:** the S34 block, area cases appended after S33's, and in-place flips only.
  - **R2:** no copy-list change, and map entries under S34's anchors.
  - **R3:** S34's scheme-support paragraphs and :703-707 only. S36 edits other scheme-support paragraphs in this batch.
  - **R4:** S34's markers, plus one added "Changed behaviour" line and its `WP30_LISTS` row.
  - **R5:** the one key line and the appended P1.25.6 entry.
  - **R6:** S34's export-block lines and the scheme branch.
  - **R7:** a new stamped fixture from a new extractor, never hand-edited.
  - **R8:** CORPUS and MOVE_CORPUS appended only.
  - **R9:** flips in place.
  - **R12:** the Q1 exception.
- **Commit-body line forms** are BRIEF's, with WP-30 ids. "failed at" is `batch-12-base.txt`'s sha.

**BUGS P1.25b** (the Resolution line, replacing the open one):

`  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.25b). A scheme dash does not ship is found as twoway finds it: SchemeParser._resolve_path walks the ado-path dash.ado writes as build_options.scheme_dirs (_dash_scheme_dirs, Mata _dash_scheme_dirs_json), scheme-NAME.scheme then NAME.scheme in each directory and its first-letter subdirectory (_ado_candidates), with the twenty-six shipped names first (_shipped_path), for scheme(), a graph's own scheme(), the session's c(scheme) and every #include, in both renderers (_resolve_scheme_name, _dash_scheme_choice, DashRenderer._scheme_for, ServerAppBuilder). A theme name given to scheme() is a file of that name when Stata finds one. dash.ado's gate refuses a path or unsafe name and an unfound one r(198), listing the twenty-six names and the six themes. A file is read only when it is a regular file of at most 1,048,576 bytes inside the directory it was found in (_admit, _read_scheme_lines); otherwise a note names why and s2color is drawn. Scheme files are parsed as data and the directories never reach the page or the app. Pinned by test/test_scheme_lookup.py::TestStatasFileName::test_a_prefixed_file_is_found_in_both_modes, test/test_scheme_lookup.py::TestTheWalkIsStatas::test_each_measured_placement, test/test_scheme_lookup.py::TestShippedNamesComeFirst::test_a_working_directory_file_never_replaces_a_shipped_scheme, test/test_scheme_lookup.py::TestTheGuards::test_a_link_out_of_its_directory_is_not_read, test/test_custom_scheme.cscript SP-01, test/test_wp30_truth.cscript SP-18; fixture test/fixtures/scheme_lookup_truth.json. Residual, deferred (WP-30): Windows and Linux path and case rules (M4); the c(adoarchive) branch of scheme.class is unmeasured; third-party color-*.style files are not looked up (P2.55); scheme(NAME.scheme), dash- names read only from the working directory, refused paths and unfollowed links are documented differences.`

**BUGS P1.25.6** (appended closed):

```
- [x] Title: A graph's own scheme() was drawn differently on the saved page and in the served app
  - File Names and Line Numbers: dash_render.py at c96facd: _resolve_scheme_name (19678; the one-scheme warning at 19727-19737), DashRenderer._make_figure (30158; the swap at 30183-30195), ServerAppBuilder.__init__ (32786), ServerAppBuilder._glyph_layer_lines (32834; the scheme block at 33440-33481), ServerAppBuilder._generate_app_source (33915; _dash_figure_for at 35095, _dash_redraw_for at 35039)
  - Description: Register P1.25.6 (A80), measured 03oct2026 at c96facd. Two registered graphs with scheme(s1mono) and scheme(s1rcolor) were drawn #ffffff and #000000 on the saved page and #ffffff and #ffffff in the served app, and both modes warned that a dashboard draws one scheme and ignored the second graph, which was false for the saved page. A graph-level theme name, dash scatter mpg weight, scheme(mono), was drawn in s2color (border #eaf2f3) with the note that scheme mono was not found on the saved page, and in s1mono with no note when served.
  - Suggested fix: WP-30 section 34 (Stata's scheme lookup along the ado-path): name each graph's scheme by the dashboard's rule in both renderers and give the served app one property dict per distinct graph scheme, swapped per figure and per redraw.
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.25b). Each graph's scheme() is named by _dash_scheme_choice in both renderers, so a theme name is the theme (or a file of that name Stata finds); ServerAppBuilder._resolve_graph_schemes writes one property dict per distinct graph scheme, and the app's _dash_under_graph_scheme swaps it in for each figure and each redraw after a filter move, as DashRenderer._make_figure does; the one-scheme warning is gone from both modes. Pinned by test/test_scheme_lookup.py::TestPerGraphSchemes::test_each_graph_is_drawn_in_its_own_scheme, test/test_scheme_lookup.py::TestPerGraphSchemes::test_the_served_move_keeps_each_graphs_scheme, test/test_scheme_lookup.py::TestThemeNamesAndFiles::test_a_graph_level_alias_is_the_alias_in_both_modes, test/test_wp30_truth.cscript SP-17.
```

**CHANGELOG Results** (two lines, replacing the Results marker):

`- scheme(), a scheme named on one graph and the session's c(scheme) are found as Stata finds them: scheme-NAME.scheme, then NAME.scheme, in each directory of the ado-path in turn (BASE, SITE, the working directory, PERSONAL, PLUS, OLDPLACE and directories added with adopath, each with its first-letter subdirectory), and a scheme file's #include the same way. dash scatter mpg weight, scheme(w30x) with scheme-w30x.scheme in the working directory was refused r(198), and after set scheme of a PLUS, PERSONAL or third-party scheme an unschemed dashboard was drawn in s2color with a warning; each is now drawn in that scheme. A file in the working directory named like one of the twenty-six shipped schemes (s2color.scheme, scheme-s1mono.scheme) no longer replaces the shipped scheme, as in twoway; scheme(mono) and the other theme names draw a scheme file of that name when Stata finds one; and the refusal of a name Stata does not find lists the twenty-six schemes and the six themes. (WP-30, P1.25b)`

`- A dashboard whose graphs name different schemes is served with each graph in its own scheme, as the saved page draws it: served, scheme(s1rcolor) on the second graph drew it white in the first graph's s1mono. The warning that a dashboard draws one scheme is gone from both modes, and a graph's scheme(mono) draws s1mono on the saved page where it drew s2color with a note. (WP-30, P1.25b)`

**CHANGELOG Security** (replacing the Security marker):

`- Schemes are looked up by name only. A scheme() holding a blank, a quote, a slash or backslash, a colon or .. is refused r(198) before any file is looked for, and such an #include is read as s2color with Stata's note. A scheme file found along the ado-path is read only if it is a regular file of at most 1,048,576 bytes whose real path lies inside the directory it was found in, so a link out of that directory is not followed; otherwise a note says why and s2color is drawn. Scheme files are read as data and never run, and the ado-path directories are read at build time and never written into the saved page or the served app. (WP-30, P1.25b)`

**CHANGELOG Changed** (added to Changed behaviour):

`- scheme() takes a scheme's name as Stata finds its file: a name holding a blank, a control character, a colon, a backtick or a dollar sign, or longer than 87 characters, such as scheme(my theme), was looked for as a file in the working directory and is now refused r(198) with the list of schemes; twoway does not find such a name either. Rename the file, for example to scheme-mytheme.scheme. (WP-30, P1.25b)`

**Notes for the closeout (S58).**
- **DROPIN-REMAINING.md P1.25.** Sub-claims a (`scheme-NAME.scheme`), c (an inherited `c(scheme)` drawn as s2color, for every scheme Stata finds), d (`#include`) and e (the error lists the names) are closed by P1.25b, commit `<sha>`. Also closed: the measured f (working-directory override reversed) and g (the copy remedy). Sub-claim b and the six-scheme half of c were closed by P1.25a. The "Third-party and PLUS schemes (DISCOVERY Q30)" decision of §4 is answered by M7 and closed by P1.25b.
- **GAPS2 X5.** The Tracked lines of X5-a, X5-c and X5-d become Closed, citing P1.25a (X5-c's six-scheme half) and P1.25b. X5-b (PLUS refused by design) becomes Closed by M7 and P1.25b. Append `(WP-30, GAPS2-X5-a)`, `(WP-30, GAPS2-X5-c)` and `(WP-30, GAPS2-X5-d)` to P1.25b's Resolution, and `(WP-30, GAPS2-X5-c)` to P1.25a's.
- **REMAINING.md §3.** Rows e (an error naming the set) and f (help matches code) are closed by P1.25b. The ".scheme file path retired" row is answered differently, by M7: files are found along the ado-path under name, containment, regular-file and size guards.
- **TWOWAY_COVERAGE_AUDIT.md:144.** The Schemes row becomes "Session `c(scheme)`, 26 shipped translations, any scheme Stata finds along the ado-path (`scheme-NAME.scheme`, `NAME.scheme`), theme aliases". Drop "third-party PLUS schemes are not discovered automatically". AUDIT-74 is closed.
- **ROADMAP.**
  - The WP-30 entry lists P1.25b and the added P1.25.6 entry with the commit.
  - Residuals: Windows and Linux path and case rules for the walk (the deferred platform package, M4); scheme.class's `c(adoarchive)` branch (unmeasured); third-party `color-*.style` and other `*.style` files (P2.55, P1.25.7). The help claims fidelity for third-party schemes only as measured.
  - Documented differences, not open: `scheme(NAME.scheme)`, `dash-` names read only from the working directory, refused paths, links not followed.
- **AGENTS.md invariant** (E7): "a scheme is found by name along the ado-path dash.ado writes as build_options.scheme_dirs, shipped names first; a file is read only when it is a regular file of at most 1,048,576 bytes inside the directory it was found in; scheme files are data and the directories never reach a page or an app".
- **Ratification item 28 (A80)** is implemented here. If it was struck, Q1's fallback text applies, and P1.25.6 reopens as a P2 residual instead of being added closed.
