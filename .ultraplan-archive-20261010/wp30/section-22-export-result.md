# Section 22: r(filename) and the stale-graph note (P1.28 part a, M8)

> Part of: WP-30 · Items: P1.28a (entry `P1.28a`) · Risk: yellow · Batch: 8 · Depends on: 06, 12 (and 01's entry, key, markers and stub block; 03's floor) · Blocks: 54 · Tasks: 12, 1 commit · Case prefix: GE

## Review amendments

- Fixed (major): 22-12's verify grepped `"P1.28a"` in `test_tracking_documents.py` for 0, which never holds (`WP30_LISTS`/`WP30_SECTION` keep the key, TR-01.2); it now imports the module and checks `WP30_OPEN`.
- Fixed (major, batch 8): the stale-graph note lands first and fires whenever a Stata graph, a `nodraw` one included, is in memory; S23's NC-09/NC-10 draw `twoway …, nodraw` and then require no `(note:` line from dash. Boundaries now say the partners clear graph memory before their dash calls, and S23's cases were amended to do so.
- Marked clearly as a "Maintainer question" (with ratification item 16), with a recommendation: P1.28.3's "one line per dash command" is read as "per file-writing command".
- Checked: dash.ado anchors (:84-146, `_dash_render_immediate` :6432/:6826-6832, `_dash_build` :8072/:8243-8257, `_dash_limit` :2822, `_dash_browser_wanted` :5696, `_dash_kpi` :6892), S06's `_dash_note(before, value, after)` and S12's `_dash_saving_parse` interface (`_sv_*` locals, TR-12.4/12.6/12.7) match; EXP-06 (:128), TOK-04/SRV-19 and PV placement exist as stated; M5 (nothing newly refused), M6 (the note is for what dash draws differently) and M8 obeyed; no renderer or copy list touched.
- Checked (batch 8): S22 shares no function with S23 (which edits no dash.ado line) or S24; GE-20 and S23's NC-07/NC-08 both go between TOK-04 and SRV-19 of `test_serve_launch.cscript`, kept in merge order S22 then S23.
- Rejected: "`_dash_result`'s `capture` hides errors" (it guards only the note's `graph dir`; the path is set and returned outside it).
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:162 (P1.28) reads: "`graph export` after dash fails r(601), or silently exports a stale earlier graph. There is no `r(filename)` and no SVG backend (see Decisions)." Its sources are GAPS2-J7-a, J7-c, E10c, J7-b and E10b. These ids exist only in DROPIN; they follow the Plan steps of GAPS2 J7 (GAPS2.md:1742-1752) and E10 (:1205-1219), as the research critic established (`.ultraplan/wp30/research/p1-28.md`, Critic additions, correction 1): J7-a is the `graph export` companion, J7-b the SVG backend, J7-c the rclass `r(filename)`, E10b the SVG backend and E10c the scripted `dash export`. Re-measured at `c96facd` (Evidence E7):

- `dash scatter mpg weight` followed by `graph export d1.png` stops with `no Graph window open`, r(601).
- `twoway scatter price weight`, then `dash scatter mpg weight, saving(d2.html) replace`, then `graph export d2.svg` writes the **earlier twoway graph** (`>Price<` in the SVG, no `>Mileage (mpg)<`), rc 0, with nothing printed.
- `dash` is not rclass (dash.ado:84), so the helpers it calls leak their `r()` to the user: after the one-line form `r(fn)` holds `/Users/billy/…/dash/dash.ado`, the path of dash's own ado-file, which a do-file can take for the page dash wrote; after a registration `r(ceiling) r(default) r(value) r(global)`; after `dash build` `r(open) r(flag)`; after `dash build, server` and `dash clear` `r(fn)`; after `dash kpi` summarize's whole `r()` of the KPI variable.
- Measured beyond the item: `saving(d5.png)` writes `d5.png.html` with rc 0 and no note (`.svg` and `.pdf` alike).

**After this section.** Under M8 ("Document + SVG button") and the register's rulings P1.28.1-P1.28.8:

- `dash` is rclass. A command that writes a file stores its absolute path in `r(filename)`: the one-line form's page (or its temporary preview), `dash build`'s page and `dash build, server`'s `.py` app. A registration, `dash kpi`, `dash clear`, `dash serve` and a refused command store nothing, and no helper's `r()` reaches the user (P1.28.6, P1.28.8). `r(filename)` is copied by value, set after the write and the browser decision, and never holds the served key.
- A command that writes a file prints one note, through S06's channel, when Stata holds a graph in memory: `(note:  dash: graph export writes the graph in Stata's Graph window, not this dashboard; graphs in memory: Graph)` (P1.28.3, A93). With no graph in memory nothing is printed. dash never draws, drops or changes a Stata graph.
- `saving()` with a suffix `graph export` writes (`.png .svg .pdf .eps .ps .jpg .jpeg .tif .gif .emf .wmf`, any case) writes `.html` (`.py` with `server`) instead, with one note, on the one-line form and `dash build`, inside S12's `_dash_saving_parse` (P1.28.4, A94).
- The help gains a Stored results section and an Exporting text that says what `graph export` does after dash, that a do-file cannot write an image of a dashboard (that waits for the deferred platform package, M8), that dash has no SVG drawing mode (P1.28.2), and that printing prints the active tab only (P1.28.5).

This closes GAPS2-J7-c and the r(601)/stale-graph part of GAPS2-J7-a, and documents GAPS2-J7-b. The "Save as SVG" toolbar action (P1.28b) is S54's (batch 19). The scripted export (GAPS2-E10c) stays open, in the deferred platform package (M8, P1.34.6).

**Why one section.** Everything here sits on the path from `dash`'s dispatcher to the file written and back: the rclass dispatch, the writers' last statement, the result helper, and the `saving()` name the writers are handed. No drawing changes, so neither renderer, the served template, a JS callback nor a copy list is touched.

**Test order and commit rule (rule 7, D1).**

- **22-01 to 22-04** write every regression test (pytest structure and help tests, the fixture, the cscript cases in four scripts) and run them against the unmodified tree. 22-01 creates `<scratch>/22-P1.28a-failure.txt`; 22-03 and 22-04 append to it. None commits.
- **22-05 to 22-10** add the Mata functions and the image-suffix rule, make `dash` rclass with its result helper, set the result in the writers, register the units, sweep the note-counting scripts and update the help.
- **22-11** certifies through the slot; **22-12** closes the entry, runs the full suite once through the queue and makes the one commit, `(WP-30 P1.28a)`.

No test-only commit exists, and no commit is red.

## Risk: [yellow] — every command's r() changes, and a new note appears whenever a Stata graph is in memory

**Why.** `dash` is the entry point of every command (59 certification scripts call it); turning it rclass replaces `r()` after every route. The stale-graph note is a new line in any session that holds a Stata graph, which can move note counts in scripts that draw twoway graphs before a dash run. `_dash_saving_parse` is shared by the one-line form and `dash build`.

**Risk factors.**

1. A route that exits without posting the result: the twoway-prefixed route (S12's strip branch) exits before the dispatcher's own routes, so `dash twoway scatter …, saving(f.html)` would store nothing.
2. Macro re-expansion: `return local filename "$dash__rfile"` expands a `$` or backquote in the path a second time (critic c3: a global holding `a$b.html` with `$b`="ZZ" returned `aZZ.html`).
3. A stale path: a global left over from an interrupted command reaches a later registration's `r()`.
4. `return` semantics: an rclass program that errors after its own `return local` keeps it (critic C6b: `r(filename)=x.html`, rc 198).
5. Notes counted by existing cases: scripts that draw a twoway graph and then count `(note:` lines (S06's needles) see one more line.
6. Choosing the graph to name: `graph describe` names the current graph, which is not always what `graph export` writes (Stata truth G4, G5, G8).
7. `pathjoin()` rewrites a backslash to a slash on Unix and resolves `..` lexically (Stata truth J3, J5), so it would name a file dash did not write.
8. Tests that read `r()` straight after `dash`.

**Mitigation.**

1. Each writing route — the strip branch, `build` and the plain plot route — ends with `_dash_result` and `return add` before its `exit` or `end`; `test_every_writing_route_posts_the_result` pins all three, and GE-05 runs the prefixed form.
2. `_dash_result` reads the global with `st_global()` into a local and returns it with `` `"`macval(_rf)'"' `` (critic c4 Q5 measured this returns `a$b.html` literally); GE-09 pins it with `$b` set.
3. `_dash_plot` and `_dash_build` drop `dash__rfile` at entry, and `_dash_result` drops it when it reads it; GE-05 runs a registration straight after a write.
4. `_dash_result` runs only after the route returned without error, as the command's last statement; a refused command stores nothing (GE-08).
5. Task 22-09 runs every script that reads notes (the S06 list) after the fix and fixes a case only by drawing-state setup (`quietly graph drop _all` before the dash call), never by changing a count; a hit inside another section's truth block is reported, not edited (R1).
6. The note names the graphs `graph dir, memory` lists (up to five), never `graph describe`'s; its text says what `graph export` does rather than which graph it will write, so it is true in every measured state.
7. `_dash_abs_path` is a pure Mata function: absolute paths unchanged, otherwise the working directory, one separator and the path as written; GE-11 pins `a\b.html`, `../x.html` and the Windows forms.
8. Grep at `c96facd`: every `r(fn)`, `r(open)`, `r(flag)`, `r(ceiling)`, `r(value)` read in `test/*.cscript` follows a direct helper call (`_dash_find_render`, `_dash_dashboard_browser`, `_gos_opt`, `findfile`), never `dash` (Evidence E8).

## Dependencies

- **Depends on: 01.** The open BUGS.md entry `P1.28a` ("dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph") and its `WP30_OPEN` key; the markers `<!-- WP-30 P1.28a -->` at the end of `### New` and of `### Changed behaviour (may need your do-files changed)` (index "P1 coverage": "New; Changed behaviour"); S22's stub block in `test/test_wp30_truth.cscript` (`* ==== S22 P1.28a: … ====`), with `_w30_expect`/`_w30_done` and `` `w30_work' ``; the S22 anchors in `test/program_coverage_map.py` (end of `COVERAGE["dash.ado"]` and of `COVERAGE["dash_parse.mata"]`, A148).
- **Depends on: 03.** `version 19` opens every program; S22's new program declares it.
- **Depends on: 06.** Mata `_dash_note(before, value, after)` (S06 TR-06.7) prints `(note:  dash: …)` in text colour on the error channel, SMCL-escaped and capped at 4,000 characters; shown under `quietly`, hidden by `capture`. Both new notes use it.
- **Depends on: 12.** `_dash_saving_parse(s, ext)` (S12 TR-12.4) is the one `saving()` grammar of the one-line form and `dash build`, and the place S12 reserved for the image-suffix rule. S12's prefix strip is the route S22's dispatch must also cover (A154).
- **Blocks: 54.** S54 (batch 19) adds "Save as SVG" to every toolbar and a sentence to this section's Exporting text.
- **Ratification.** Item 16 (A93, A96) is pending: "The stale-graph note prints once per dash command, only when a Stata graph is in memory. `r(filename)` is an absolute path, and for previews it is transient." This section is written on that ruling; a strike re-plans TR-22.2 and TR-22.4 before batch 8's base is recorded.
- **Parallel batch: 8, merge order S22, S23, S24** (S22 lands first). S23 edits `_make_figure_body`, the build-time trial, `_dash_launch_app`'s relay and the served notes; S24 the scheme mappers, the extractor and the 26 scheme files. Neither edits `dash`, `_dash_result`, `_dash_render_immediate`'s or `_dash_build`'s last lines, `_dash_saving_parse` or the help paragraphs named here (Boundaries).

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash.sthlp 3,822; dash_parse.mata header :1-303). S03, S06 and S12 land before batch 8 and move lines; find each site by the quoted text at the batch-8 base.

### E1. The dispatcher has no class and exits route by route

dash.ado:84-85, 92, 120-146:

```stata
84  program define dash
85      version 16.0
92      _dash_require_mata
120     if "`_subcmd'" == "kpi" {
121         _dash_kpi `macval(_args)'
122         exit
123     }
124     if "`_subcmd'" == "build" {
125         _dash_build `macval(_args)'
126         exit
127     }
...
144     global dash__uv = string(_caller())
145     _dash_plot `macval(0)'
146 end
```

At batch 8, S03 has made :85 `version 19` and put its guard above :92, and S12 has put its prefix strip after `_dash_require_mata` (S12 TR-12.1). The strip's `"strip"` branch is a route of its own that exits before :120:

```stata
    if "`_pf_kind'" == "strip" {
        global dash__uv = string(_caller())
        _dash_plot `macval(0)'
        exit
    }
```

A154 orders the top of `dash`: S03's guard, the Mata guard, S25's dependency guard (batch 9), S12's strip, then S22's rclass dispatch.

### E2. Where the leaked r() comes from

- `_dash_xm_load` (dash.ado:4576-4583) runs `capture findfile dash.ado` and reads `r(fn)`; the last such `findfile` on the one-line route leaves `r(fn)` = dash.ado's path (critic correction 2).
- `_dash_limit, rclass` (dash.ado:2822): `r(ceiling) r(default) r(value) r(global)` after a registration.
- `_dash_browser_wanted, rclass` (dash.ado:5696-5704) and `_dash_dashboard_browser, rclass` (5739): `return scalar open = `open'` and `r(flag)`.
- `_dash_kpi` (6892): `quietly summarize `kpi_var' `macval(if)' `macval(in)'` (7112) leaves summarize's `r()`.

### E3. The one-line writer's last lines

dash.ado:6826-6832 (`_dash_render_immediate`, def 6432; called only from `_dash_plot` :5682):

```stata
6826        _dash_open_page, path(`"`saving_path'"')
6827    }
6828    else {
6829        // Shown as written: braces are legal in a file name (P20-07).
6830        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving_path"), "")
6831    }
6832 end
```

`saving_path` is the validated `saving()` path (relative as typed, `~/` expanded by `_dash_validate_path`'s `_dash_vpath`) or the preview path `r(path)` from `_dash_tmp_preview` (6796-6801), under `c(tmpdir)dash-<uid>/previews/`. S12 TR-12.3 adds the temporary-preview line inside the `else` branch; S22's statement goes after the whole `if`/`else`, directly above `end`.

### E4. `dash build`'s last lines

dash.ado:8243-8257 (`_dash_build`, def 8072; called only from `dash` :125):

```stata
8243        mata: _dash_say("txt", "dash: dashboard saved to ", st_local("saving"), "")
...
8250        _dash_dashboard_browser, `nobrowser'
8251        if r(open) {
8252            // The one opener, shared with the one-line form (see
8253            // _dash_open_page).
8254            _dash_open_page, path(`"`saving'"')
8255        }
8256    }
8257 end
```

The server branch (8228-8241) prints `dash build: server app written to …` and the `To launch:` lines. `saving` holds the validated `.html` or `.py` path.

### E5. The `saving()` name rule

At `c96facd` (dash.ado:6474-6489) the one-line route replaces `.gph` with a note and appends `.html` to everything else:

```stata
6481        local _gph = 0
6482        if regexm(lower(scalar(`P')), "\.gph$") {
6483            scalar `P' = substr(scalar(`P'), 1, strlen(scalar(`P')) - 4)
6484            local _gph = 1
6485        }
6486        if !regexm(lower(scalar(`P')), "\.html$") scalar `P' = scalar(`P') + ".html"
```

S12 replaces this with `_dash_saving_parse(s, ext)` in dash_parse.mata (after `_dash_path_badchar`, which closes at :630): "a case-insensitive `.gph` suffix is removed and `_sv_gph` set to "1"; "." + ext is appended unless the name ends in it case-insensitively. It sets the caller's locals by value: `_sv_file`, `_sv_replace`, `_sv_asis`, `_sv_gph`, `_sv_comma`. This is the place S22 adds its image-extension rule" (S12 TR-12.4). Its callers are `_dash_plot` (validation only, before anything is registered), `_dash_render_immediate` and `_dash_build` (with `ext` = `py` under `server`).

### E6. The help

- Jump list, dash.sthlp:3-21: no "Exporting" and no "Stored results" entry; no `{marker results}` exists.
- Description, :135-139: "{cmd:dash} accepts the same syntax as {helpb twoway} and produces an interactive HTML file instead of a static Stata graph window."
- Dashboard Options, :924-926: "required; path to the output HTML file (must end in {cmd:.html}; no {cmd:..} traversal allowed)" (S12 TR-12.12 rewrites it to "the file to write: {cmd:.html} is appended … and a {cmd:.gph} suffix is replaced, as on the one-line form; …").
- Exporting, :980-986:

```
980 {marker export}
981 {title:Exporting}
982
983 {pstd}
984 Every dashboard can save its figures as a PNG image, with the save button
985 on the toolbar (see {help dash##toolbar:The toolbar}).  With {cmd:csv} it
986 can also give you its data.
```

  The section runs to :1033 (the csv paragraphs); `{marker layout}` is :1034. Nothing in the help mentions `graph export`, `r()`, printing or an SVG drawing mode.

### E7. Measured (StataNow 19.5, console batch, Apple Silicon; this section's probes)

Each probe opened `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"` and `global dash_nobrowser 1` and ran as `scripts/stata_slot.sh <scratch>/s22 <scratch>/s22/pN.do`.

dash at `c96facd` (p6.do; before each command `quietly summarize price` seeds `r()`, and `_rshow` prints `st_dir("r()", "macro"|"numscalar", "*")`):

```
R0seed macros=[] scalars=[N sum_w mean Var sd min max sum] matrices=0
R1oneline macros=[fn] scalars=[] matrices=0          (saving(r1.html, replace))
R1oneline fn=[/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado]
R2preview macros=[fn] scalars=[] matrices=0          (no saving())
R3register macros=[global] scalars=[ceiling default value] matrices=0
R4kpi macros=[] scalars=[N sum_w mean Var sd min max sum] matrices=0
R5build macros=[flag] scalars=[open] matrices=0
R6server macros=[fn] scalars=[] matrices=0
R7 rc=102 / R7refused macros=[] scalars=[] matrices=0   (dash scatter mpg, saving(r7.html, replace))
R8clear macros=[fn] scalars=[] matrices=0
dash: dashboard saved to r9.png.html / R9 png.html rc=0  (saving(r9.png) replace)
dash: dashboard saved to r10.html / R10 export rc=0 / R10 svg Price=1 Mileage=0
```

twoway and `graph export` (p7.do, p2.do, p3.do):

```
T1  graph drop _all; graph export t1.png, replace       -> no Graph window open        rc=601
T2  twoway ...; graph export t2.svg, name(nosuch)      -> could not find Graph window  rc=693
C1  quietly summarize price; twoway scatter price weight -> macros=0 scalars=0  (twoway clears r())
T6  twoway scatter price weight, saving(t6.png, replace) -> file t6.png saved as .gph format;
    t6.png exists (rc 0), t6.png.gph and t6.gph do not (rc 601)
G0  nothing drawn:            list=[ ]          describe rc=198          export rc=601
G1  twoway ..., nodraw:       list=[Graph ]     describe rc=0 fn=[Graph] export rc=601
G2  twoway scatter price weight:  list=[Graph ] describe fn=[Graph]      export writes price
G3  then twoway ..., name(g2):    list=[Graph g2 ] describe fn=[g2]      export writes mpg (g2)
G4  then graph drop g2:           list=[Graph ] describe rc=198          export writes mpg (g2)
G5  then twoway ..., name(g3) nodraw: list=[Graph g3 ] describe fn=[g3]  export writes mpg (g2)
G7  set graphics off; twoway ...: list=[Graph ]                          export writes price
G8  graph close _all:             list=[Graph ] describe rc=198          export writes price
H1  draw; graph drop _all:        list=[ ]                               export rc=0 (writes it)
H4  twoway; dash ..., saving(); graph dir after dash: list=[Graph ]; export rc=0
timing: 20 x (graph dir, memory + graph describe) 0.005 s; 20 x translate @Graph to SVG 0.047 s
```

`graph export`'s suffixes (p2.do, `graph export "sfx.<s>", replace` after a drawn graph):

```
png svg pdf eps ps jpg  -> rc 0 ("file sfx.png written in PNG format", "... saved as SVG format", ...)
jpeg -> translator Graph2jpeg not found rc=111;   tif -> translator Graph2tif not found rc=111
gif emf wmf -> Stata for Unix cannot create gif files rc=198 (emf, wmf alike)
tiff pict gph html xyz -> output file suffix tiff not recognized rc=198
```

The eleven recognised suffixes are `gr_export.ado`'s `VerifySuffix` list (/Applications/StataNow/ado/base/g/gr_export.ado:514-524: png, tif, pdf, svg, ps, eps, wmf, emf, jpeg, jpg, gif), which compares the suffix as typed with lower-case words.

Return mechanics (p1.do and critic c1/c3/c4):

```
P1  rclass _o1: summarize price; _h1 (returns filename "abc.html"); return add
    -> r(filename) : "abc.html", r(mean)=.            (return add posts the helper's r())
P2  rclass _o2: local f ""; return local filename `"`macval(f)'"'  -> return list empty
P2b rclass _o3: _h2 (returns nothing); return add   -> return list empty
C5  an rclass outer program discards an inner helper's r()
C6  ... also when it errors;  C6b  but an rclass program that errors AFTER its own
    return local keeps it: r(filename)=[x.html], rc=198
Q1  return local filename "$dash__rfile" with the global a$b.html, $b="ZZ" -> aZZ.html
Q5  local f : copy global dash__rfile; return local filename `"`macval(f)'"' -> a$b.html
```

Graph memory and certification scripts (p4.do): `discard` empties graph memory (`D1 after discard list=[ ]`), and so does `cscript` (`D2 after cscript list=[ ]`, cscript.ado:28 runs `discard`) and `clear all` (D3). A case that needs a graph in memory draws it after its script's `cscript` line.

Mata path functions (p5.do):

```
J1 pathjoin("/w/d", "x.html")    -> /w/d/x.html
J2 pathjoin("/w/d", "./x.html")  -> /w/d/./x.html
J3 pathjoin("/w/d", "../x.html") -> /w/x.html          (resolves .. lexically)
J5 pathjoin("/w/d", "a\b.html")  -> /w/d/a/b.html      (rewrites a backslash on Unix)
J6 pathisabs on MacOSX: "C:\x.html" 0, "\x.html" 0, "\\srv\x.html" 0;  "~/x.html" 1
```

### E8. Existing tests

Pinned and flipped:

- `test/test_help_conformance.py::TestInternalLinksResolve::test_the_reference_scan_found_something` — `assert len(refs) == 75 and len(set(refs)) == 29` at `c96facd` (:968). S22 adds `dash##export` and `dash##results` references and the `results` marker; the value at the batch-8 base is re-derived on the worktree and written with `# <old> -> <new>: P1.28a …` (R10).

Kept (they call helpers directly, so their `r()` reads are unchanged): `test/test_bug_regressions.cscript` :436, :459 (`_dash_find_render`); `test_help_claims_4.cscript` :462, :499; `test_serve_browser.cscript` :91-92 (`_dash_dashboard_browser` after `dash … nodraw`), :130, :199-200; `test_serve_launch.cscript` :296, :468; `test_help_claims_8.cscript` :709, :780 (`findfile`); `test_graph_option_scope.cscript` :123 (`_gos_opt`). `test_help_claims_1.cscript` HC1-12 (:731-755, dash's `name()` leaves graph memory alone) holds: S22 only reads graph memory.

Program-body readers that must accept `program define dash, rclass` (measured regexes): `test_packaging.py:590` `program define %s\s*(,|$)`; `test_serve_options.py:50` `(?:,[ \t\w]*)?`; `test_abbreviations.py:67` `\b.*?$`; the `src.index("program define " + name)` readers (test_color_alias.py:140, test_help_claims_8.py:1264, test_help_conformance.py:344, test_option_validation.py:463) match a prefix.

No test pins `x.png.html` (`grep -rn 'png\.html\|svg\.html\|pdf\.html' test/` finds none). The GE prefix is unused (`grep -cE '(^|[^A-Za-z0-9_])GE-[0-9]' test/*.cscript test/*.py test/*.do` sums to 0).

### E9. Blast radius

`gitnexus impact <sym> -d upstream -r dash` returns `Target '<sym>' not found` for `dash`, `_dash_render_immediate`, `_dash_build` and `_dash_saving_parse` (Stata and Mata are not indexed): **UNKNOWN, unresolved**, confirmed by grep:

| Symbol | Callers (grep at `c96facd`) | Treat as |
|---|---|---|
| `dash` (dash.ado:84) | every user command; 59 certification scripts; every example | HIGH (entry point) |
| `_dash_plot` (5001) | `dash` :145 (and S12's strip branch) | HIGH (every plot command) |
| `_dash_render_immediate` (6432) | `_dash_plot` :5682 | MEDIUM |
| `_dash_build` (8072) | `dash` :125 | MEDIUM |
| `_dash_saving_parse` (S12, dash_parse.mata) | `_dash_plot`, `_dash_render_immediate`, `_dash_build` | MEDIUM |
| `_dash_require_mata` (dash.ado, `_needed` 237-255) | `dash` and every subcommand | MEDIUM (list-only edit) |

No `dash_render.py` symbol is edited, so no Python impact applies. `dash__rfile` is a new global name (`grep -c dash__rfile dash.ado test/*` prints 0 everywhere).

## User stories

- **US-22.1** As a twoway user, I want `dash …, saving(fig.html)` and `dash build, saving(dash.html)` to leave the file's path in `r(filename)`, so a do-file can copy, attach or open the page it just wrote.
- **US-22.2** As a twoway user running a do-file in batch, I want `r(filename)` after the one-line form without `saving()` to name the temporary preview page, so I can find it without reading the log.
- **US-22.3** As a twoway user, I want `return list` after any dash command to hold only what dash means to return, as after `twoway`, so I never take dash's own ado-file path for my page.
- **US-22.4** As a twoway user who also draws Stata graphs, I want to be told when `graph export` after dash would write my earlier Stata graph instead of the dashboard, so I do not ship the wrong figure.
- **US-22.5** As a twoway user, I want `saving(fig.png)` to say that it wrote `fig.html`, so I know dash wrote a page, not an image.
- **US-22.6** As a twoway user, I want the help to say what dash stores, how to get an image or a printout of a dashboard, and what it cannot do yet.

## Business requirements

- **BR-22.1** After a dash command that writes a file, `r(filename)` holds that file's absolute path: the path the "saved to" or "written to" line shows, joined to the working directory when it is relative, so it still names the file after a `cd`.
- **BR-22.2** After a registration, `dash kpi`, `dash clear`, `dash serve` or a command refused with an error, `r()` holds nothing. After any dash command, `r()` holds nothing but `r(filename)`.
- **BR-22.3** `r(filename)` is the path exactly as written: a `$` or a backquote in it stays literal, and it never holds the served dashboard's key or address.
- **BR-22.4** When Stata holds a graph in memory, a dash command that writes a file prints exactly one note in twoway's note form, saying that `graph export` writes the graph in Stata's Graph window and not the dashboard, and naming up to five of the graphs. With no graph in memory it prints none. Stata's graph memory is the same before and after.
- **BR-22.5** A `saving()` name ending in a suffix `graph export` writes (the eleven, in any case) writes `.html` (`.py` with `server`) instead, with one note naming the file written, on the one-line form and `dash build`. Any other name is written as before.
- **BR-22.6** `graph export` after dash, with no Stata graph, fails exactly as after nothing was drawn: r(601) "no Graph window open". dash makes no Stata graph.
- **BR-22.7** The help has a Stored results section and an Exporting text covering BR-22.1 to BR-22.6, the do-file image limit, the absence of an SVG drawing mode, and that printing prints the tab that is showing.
- **BR-22.8** The saved page and the served app are drawn exactly as before, before and after a filter move.

## Technical requirements

**TR-22.1 The rclass dispatch (`dash`, dash.ado:84).**

- The program line becomes `program define dash, rclass`. Nothing else at the top changes (A154: S03's guard, the Mata guard, S25's later guard and S12's strip keep their lines).
- Directly after S12's strip paragraph, and before the "Subcommand routing" comment block, insert this comment paragraph (no statements): dash is rclass so that, as after `twoway`, a command leaves nothing in `r()` but what it means to return (WP-30 P1.28a, M8): `r(filename)`, the absolute path of the file a command wrote, posted by `_dash_result` and `return add` at the end of each route that can write (the prefixed route above, `build`, and the plot route); `kpi`, `clear` and `serve` post nothing, and a refused command posts nothing because an rclass program that stops with an error leaves `r()` empty; `_dash_result` must run last, because an rclass program that errors after its own `return` keeps it (measured, critic C6b).
- Three routes gain two lines each, `_dash_result` then `return add`:
  - S12's `"strip"` branch, between `_dash_plot `macval(0)'` and `exit` (no other line of S12's paragraph changes);
  - the `build` route, between `_dash_build `macval(_args)'` and `exit`;
  - the plot route, after the final `_dash_plot `macval(0)'` and before `end`.
- The `kpi`, `clear` and `serve` routes are unchanged.

**TR-22.2 `_dash_result` (new; dash.ado, directly after `dash`'s `end` and before the `_dash_do_render` header comment).**

```stata
program define _dash_result, rclass
    version 19
    mata: st_local("_rf", st_global("dash__rfile"))
    capture macro drop dash__rfile
    if `: length local _rf' == 0 exit
    local _gn ""
    capture {
        quietly graph dir, memory
        mata: st_local("_gn", _dash_graph_names(st_global("r(list)"), 5))
    }
    if `: length local _gn' {
        mata: _dash_note("dash: graph export writes the graph in Stata's Graph window, not this dashboard; graphs in memory: ", st_local("_gn"), "")
    }
    return local filename `"`macval(_rf)'"'
end
```

- Header comment: what `r(filename)` is and who sets it (TR-22.3); why the global is read with `st_global()` and returned through `macval()` (Q1 and Q5 of Evidence E7); why the note names the graphs `graph dir, memory` lists and not `graph describe`'s current graph (G4, G5, G8); that it never draws, drops, displays or exports a graph (HC1-12); that the note is printed at most once per command because `_dash_result` runs once per route; that a dropped graph still shown in the console's Graph window is not in memory and gets no note (H1).
- `capture` around `graph dir` keeps a written page from ever being reported as a failure because of the note.

**TR-22.3 The writers set the result last; the routes clear it first.**

- `_dash_render_immediate`: directly above its `end` (after the `if "`open_browser'" == "1" … else …` block, E3), a comment line and `mata: st_global("dash__rfile", _dash_abs_path(st_local("saving_path"), c("pwd"), c("os")))`.
- `_dash_build`: directly above its `end` (after the server/HTML `if`/`else`, E4), the same with `st_local("saving")`.
- `_dash_plot` and `_dash_build`: directly after their `version 19` line, `capture macro drop dash__rfile` with a comment (a path from a command interrupted between its write and its result must never reach a later command's `r()`).
- The global is set and read only by Mata `st_global()`, never by `global` or `$`.

**TR-22.4 `_dash_abs_path(path, pwd, os)` (new; dash_parse.mata, directly after S12's block, before `_dash_check_utf8`).**

```mata
string scalar _dash_abs_path(string scalar path, string scalar pwd,
                             string scalar os) {
    string scalar c1, last, sep
    if (path == "") return("")
    c1 = substr(path, 1, 1)
    if (os == "Windows") {
        if (c1 == "/" | c1 == char(92)) return(path)
        if (strlen(path) >= 2 & substr(path, 2, 1) == ":" &
            ((c1 >= "A" & c1 <= "Z") | (c1 >= "a" & c1 <= "z"))) return(path)
        sep = char(92)
    }
    else {
        if (c1 == "/" | c1 == "~") return(path)
        sep = "/"
    }
    if (pwd == "") return(path)
    last = substr(pwd, -1, 1)
    if (last == "/" | last == char(92)) return(pwd + path)
    return(pwd + sep + path)
}
```

- Pure: no file-system access, no normalisation (no `.` or `..` resolution, no separator rewriting), so the result names exactly the file the renderer wrote relative to the same working directory. Linear in the lengths. Not `pathjoin()` (J3, J5).
- `os` is `c(os)`: `MacOSX`, `Unix` or `Windows`.

**TR-22.5 `_dash_graph_names(list, max)` (new; dash_parse.mata, directly after `_dash_abs_path`).**

```mata
string scalar _dash_graph_names(string scalar list, real scalar max) {
    string rowvector t
    t = tokens(list)
    if (cols(t) == 0) return("")
    if (cols(t) <= max) return(invtokens(t))
    return(invtokens(t[1..max]) + " and " + strofreal(cols(t) - max) + " more")
}
```

Graph names are Stata names; the output is at most `max` names of 32 characters plus the count. `_dash_note` SMCL-escapes it in any case.

**TR-22.6 The image-suffix rule (`_dash_saving_parse`, dash_parse.mata; its two writing callers).**

- In S12's name-mapping step, between the `.gph` rule and the `"." + ext` append: when no `.gph` was removed, for `k` in the literal row `("png", "svg", "pdf", "eps", "ps", "jpg", "jpeg", "tif", "gif", "emf", "wmf")`, if `strlower(substr(name, -(strlen(k) + 1), .)) == "." + k` and the stem left by removing it is not empty and does not end in `/` or `char(92)`, remove the suffix, set `img = k` (from the row, never the user's bytes) and stop. Then append `"." + ext` as S12 does. Set the caller's local `_sv_img` by value to `img` (`""` when none) on every call, beside S12's five locals.
- Comment: the eleven are `graph export`'s own (`gr_export.ado` `VerifySuffix`, measured E7); twoway's `saving(t6.png)` writes a `.gph` named `t6.png` (T6), dash writes HTML and says so (WP-30 P1.28a, A94); `.tiff` and other names `graph export` does not recognise are left alone; a name that would become empty or a bare folder keeps its suffix.
- `_dash_render_immediate`: directly after S12's `.gph` line (`if "`_sv_gph'" == "1"`), `if "`_sv_img'" != "" { mata: _dash_note("dash: saving() writes HTML, not a ." + st_local("_sv_img") + " image; using ", st_local("saving_path"), "") }`, after `_dash_validate_path` so the path shown is the validated one.
- `_dash_build`: directly after S12's `.gph` line, `if "`_sv_img'" != "" { mata: _dash_note("dash build: saving() writes " + (st_local("server") != "" ? "a server app" : "HTML") + ", not a ." + st_local("_sv_img") + " image; using ", st_local("saving"), "") }`, after the validator, so the path shown is the validated `.html` or `.py` one.
- `_dash_plot`'s validation call is unchanged and prints nothing for an image suffix: a named graph writes nothing.

**TR-22.7 Registries (X.5, A137, A148).**

- `_dash_require_mata`'s `_needed` (dash.ado:237-255, extended by S12): end S12's line with ` ///` and add the line `        _dash_abs_path _dash_graph_names`.
- dash_parse.mata header (:1-303): two Public API entries after S12's last entry, in the existing form:
  - `*!   _dash_abs_path(path, pwd, os)` / `*!       path when it is absolute on os, else pwd, one separator and path,` / `*!       with nothing normalised.` / `*!`
  - `*!   _dash_graph_names(list, max)` / `*!       The first max graph names of list, then "and N more".` / `*!`
- `test/program_coverage_map.py`, under the S22 anchors, alphabetical: `COVERAGE["dash.ado"]`: `"_dash_result": ("test_export.cscript:GE-09", "test_export.cscript:GE-01")`; `COVERAGE["dash_parse.mata"]`: `"_dash_abs_path": ("test_export.cscript:GE-11",)`, `"_dash_graph_names": ("test_export.cscript:GE-14",)`.
- `test/function_test_map.py`: none (no Python function). Served copy lists: none (index R2 row S22).

**TR-22.8 The help (`dash.sthlp`; R3 rows Syntax/Description, Dashboard Options, Exporting; the jump list, which no other WP-30 section edits).**

- Jump list: after `{viewerjumpto "Dashboard Options" "dash##dashboard_options"}{...}` (:8) add `{viewerjumpto "Exporting"         "dash##export"}{...}` and `{viewerjumpto "Stored results"    "dash##results"}{...}`.
- Description, after the paragraph :135-139, a new `{pstd}` paragraph: "A dashboard is not a Stata graph: {cmd:graph export}, {cmd:graph save}, {cmd:putdocx} and {cmd:dyndoc} do not see it.  {cmd:dash} stores the path of the file it wrote in {cmd:r(filename)}; see {help dash##export:Exporting} and {help dash##results:Stored results}."
- Dashboard Options, the `saving()` row as S12 left it: after the clause naming the replaced `.gph` suffix, add "and so is a suffix {cmd:graph export} writes ({cmd:.png}, {cmd:.svg}, {cmd:.pdf}, {cmd:.eps}, {cmd:.ps}, {cmd:.jpg}, {cmd:.jpeg}, {cmd:.tif}, {cmd:.gif}, {cmd:.emf}, {cmd:.wmf}), with a note".
- Exporting, three `{pstd}` paragraphs after :983-986 and before the csv paragraphs:

```
{pstd}
{ul:graph export.}  A dashboard is drawn in the browser, not in a Stata
Graph window, so {cmd:graph export} cannot write it: {cmd:graph export}
writes the graph displayed in a Graph window, and with none it stops with
"no Graph window open", {cmd:r(601)}.  If Stata holds an earlier graph,
{cmd:graph export} after {cmd:dash} writes that graph.  So that this is never
silent, a {cmd:dash} command that writes a file -- the one-line form and
{cmd:dash build} -- prints one note when Stata holds a graph in memory (the
graphs {cmd:graph dir, memory} lists), naming up to five of them:
{cmd:(note: dash: graph export writes the graph in Stata's Graph window, not this dashboard; graphs in memory: Graph)}.
{cmd:dash} never draws, drops or changes a Stata graph.  In batch, a graph
removed with {cmd:graph drop} can still be the one {cmd:graph export} writes;
it is no longer in memory, and no note is printed.

{pstd}
{ul:Images.}  The toolbar's save button writes the figures as a PNG image at
the screen's resolution.  A do-file cannot write an image of a dashboard:
that needs a web browser driven from Stata, which {cmd:dash} does not ship.
A do-file finds the page in {cmd:r(filename)} (see
{help dash##results:Stored results}).  {cmd:saving()} always writes HTML
({cmd:.py} with {cmd:server}): a name ending in a suffix {cmd:graph export}
writes -- {cmd:.png}, {cmd:.svg}, {cmd:.pdf}, {cmd:.eps}, {cmd:.ps},
{cmd:.jpg}, {cmd:.jpeg}, {cmd:.tif}, {cmd:.gif}, {cmd:.emf} or {cmd:.wmf}, in
any case -- has that suffix replaced, with a note, on the one-line form and
{cmd:dash build}: {cmd:saving(fig.png)} writes {cmd:fig.html}.
({cmd:twoway}'s {cmd:saving(fig.png)} writes a {cmd:.gph} file named
{cmd:fig.png}.)  The figures are drawn on an HTML canvas; {cmd:dash} has no
SVG drawing mode, because a figure drawn as SVG cannot be saved by the
toolbar's button.

{pstd}
{ul:Printing.}  Printing the page from the browser prints what the screen
shows: with {cmd:tabs()}, the tab that is showing and none of the others.
Print each tab in turn.
```

- Stored results, a new section directly after Exporting's last paragraph and before `{marker layout}` (:1034):

```
{marker results}{...}
{title:Stored results}

{pstd}
{cmd:dash} stores the following in {cmd:r()}:

{synoptset 16 tabbed}{...}
{p2col 5 16 20 2: Macros}{p_end}
{synopt:{cmd:r(filename)}}the file the command wrote, as an absolute path{p_end}

{pstd}
{cmd:r(filename)} is stored by the commands that write a file: the one-line
form with {cmd:saving()} (the page), the one-line form without it (the
preview page in {cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/previews/}),
{cmd:dash build} (the page) and {cmd:dash build, server} (the {cmd:.py} app).
It is the path the "saved to" line shows, joined to the working directory
when it is relative, so it still names the file after a {cmd:cd}.  A preview
is temporary: the newest five of a session are kept, and {cmd:dash clear}
removes the session's previews (see {help dash##tempfiles:Temporary files and privacy});
use {cmd:saving()} to keep a page.  Registering a graph or a KPI card,
{cmd:dash clear} and {cmd:dash serve} store nothing; {cmd:dash serve} writes
no file of yours, and the key in its address is never stored.  A command
that stops with an error stores nothing.  As after {cmd:twoway}, every
{cmd:dash} command replaces the {cmd:r()} results of the command before it.
```

- No `{cmd:. …}` example lines are added (the help-example runner executes those).

**TR-22.9 Both modes.** No change to `dash_render.py`, the served template, a JS callback, a copy list or a fixture the renderer reads. The saved page for `saving(x.png)` is the page `saving(x.html)` writes, and `dash build, server saving(x.png)` writes the app `saving(x.py)` writes (GE-16, GE-17 read both). `test/test_mode_parity.py` runs unchanged as the G3 guard (saved and served, before and after a filter move); no CORPUS case is added because nothing drawn changes. No JS twin applies.

**TR-22.10 Tests and fixture** (TDD test stubs; Stata truth): a new pytest file `test/test_export_result.py`; a new extractor `scripts/extract_graph_export_truth.do` and fixture `test/fixtures/graph_export_truth.json`; cases appended to `test/test_export.cscript` (GE-01..GE-15), `test/test_path_validation.cscript` (GE-16..GE-19), `test/test_serve_launch.cscript` (GE-20) and S22's block of `test/test_wp30_truth.cscript` (GE-21..GE-24).

**TR-22.11 Tracking.** BUGS.md entry `P1.28a` closed in place; its `WP30_OPEN` line deleted; both markers replaced in place (22-12).

**TR-22.12 Security (rule 1).** Threats named in the commit body:

- (a) Macro expansion of a path through `r(filename)`: read and returned by value (Mata `st_global`/`st_local`, `macval()`); GE-09 with `$b` defined.
- (b) Disclosure of the served key: `dash serve` posts nothing; GE-20 checks no `r()` macro or scalar exists after a stubbed serve.
- (c) A misleading result: `r(fn)` named dash.ado as if it were the page; gone (GE-01).
- (d) SMCL or control text through a note: both notes pass the path and the names as `_dash_note`'s value argument (SMCL-escaped, capped at 4,000 characters); the image word comes from a fixed row; graph names are Stata names, at most five.
- (e) Graph-memory side effects: `_dash_result` only reads `graph dir, memory`; GE-12 and HC1-12 pin memory unchanged.
- No shell, no `python`, no `eval`; nothing reaches HTML or JS; `_dash_abs_path` touches no file and is linear.

## Boundaries

- **S12's lines** (landed in batch 4): S22 adds two lines inside the strip's `"strip"` branch and the image rule inside `_dash_saving_parse`'s name mapping, as S12 reserved; it changes no other line of `_dash_strip_prefix`, `_dash_saving_split`, `_dash_seg_saving`, the display rule, the launch line, the `.gph` lines or S12's PV/SB/CF cases.
- **S06's channel**: used, not edited (`_dash_note`, `_dash_say`, the needles, the help paragraph).
- **Batch 8 partners.** S23 owns `_make_figure_body`, the build-time trial, `_dash_launch_app`'s relay, the served notes, NC-07..19 and `dash build, server`'s banner; S24 owns the scheme mappers, `extract_scheme_truth.py` and the 26 scheme files. S22 edits none of their functions or paragraphs. S22's stale-graph note lands first in this batch and prints on every file-writing command while a Stata graph (a `nodraw` one included) is in memory; S23's NC-07..NC-10 count notes and are written on worktrees without it, so they clear Stata's graphs (`quietly graph drop _all`) before their dash calls (S23 says so, review pass); S24's SK cases draw twoway graphs but count no notes. The merger's G8 run of the whole truth script is the check.
- **Later sections.** S25 (batch 9) inserts its dependency guard before S12's strip. S46 (batch 16) edits `_dash_serve` and the server banner. S54 (batch 19) owns "Save as SVG" (`_dash_name_save`, `_DASH_SVG_SAVE_JS`, the `_assert_nine_tools` flip, the toolbar help row) and adds its sentence to this section's Exporting "Images" paragraph. S58 owns every tracking document.
- **Not WP-30.** The print stylesheet and `beforeprint` JS, and the KPI cards and header in the PNG (P3.11, P1.28.5); the iframe note and the Jump To completeness (P3.4); a Chrome-driven `dash export` (the deferred platform package, M8, P1.34.6).
- **Rejected.** No `output_backend(svg)` (M8, P1.28.2: an SVG figure breaks the grid's PNG save). No `twoway` companion option (M8: no B4). No `graph describe`, `graph display`, `graph export` or `translate` call in shipped code.
- Differences from twoway (dash.sthlp:444-814) is not edited (R3 assigns it to S06, S11, S12, S18, S20).

## Stata truth

**Probes run for this plan** (scratch `<scratch>/s22`, quoted in Evidence E7): `p1.do` (return add, empty return), `p2.do` (graph-memory states, suffixes), `p3.do` (dropped graph, timings, graph memory after dash), `p4.do` (discard, cscript, clear all), `p5.do` (pathjoin, pathisabs), `p6.do` (r() after each subcommand at `c96facd`), `p7.do` (T1, T2, C1, T6). Each opened with `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"` and `global dash_nobrowser 1`, and ran as `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh <scratch>/s22 <scratch>/s22/pN.do`.

**The extractor** `scripts/extract_graph_export_truth.do` (new; 22-02):

1. Header comment: purpose (WP-30 section 22, P1.28a), output, the run line `DASH_REPO=<tree> <tree>/scripts/stata_slot.sh <scratch> <tree>/scripts/extract_graph_export_truth.do`, and the method below; it reads the commit from a file `shell` wrote and never uses `shell=True`.
2. `clear all`, `set more off`, `set linesize 255`, then S02's TR-02.9 root stanza with `<file>` = `extract_graph_export_truth.do` and `_zr_*` locals, then `global GX_REPO "`repo'"`, `global GX_OUT "${GX_REPO}/test/fixtures/graph_export_truth.json"`, `adopath ++ "`repo'/"`, `global dash_nobrowser 1`.
3. A work folder `` `c(tmpdir)'dash_gx_probe `` (`global GX_WORK`); the `c(python_exec)` check (exit 601 when empty); `quietly shell git -C "${GX_REPO}" rev-parse HEAD > "${GX_WORK}/git_head.txt"`; `GX_VERSION` = `c(stata_version)`, `GX_BORN` = `c(born_date)`, `GX_WHEN` = date and time, `GX_OS` = `c(os)`, `GX_MODE` = `c(mode)`.
4. A helper `_gx_run name : command` that opens `log using "${GX_WORK}/gx_<name>.log", text replace name(gx)`, runs `capture noisily <command>`, stores `_rc` in `global GX_rc_<name>`, and closes the log.
5. The cases, after `sysuse auto, clear`:
   - `no_graph`: `graph drop _all`; `graph export "${GX_WORK}/gx1.png", replace`.
   - `no_such_name`: `twoway scatter price weight`; `graph export "${GX_WORK}/gx2.svg", name(nosuch) replace`.
   - `nodraw_only`: `graph drop _all`; `twoway scatter price weight, nodraw`; `graph dir, memory`'s list into `GX_mem_nodraw`; `graph export "${GX_WORK}/gx3.svg", replace`.
   - `dropped`: `graph drop _all`; `twoway scatter price weight`; `graph drop _all`; the list into `GX_mem_dropped`; `graph export "${GX_WORK}/gx4.svg", replace`.
   - `return_after_twoway`: `quietly summarize price`; `twoway scatter price weight`; the counts of `st_dir("r()", "macro", "*")` and `st_dir("r()", "numscalar", "*")` into `GX_rmac`, `GX_rsca`.
   - `sfx_<s>` for `s` in `png svg pdf eps ps jpg jpeg tif gif emf wmf PNG tiff pict gph html xyz`: `graph export "${GX_WORK}/gx5.<s>", replace` (after a drawn graph).
   - `saving_png`: `twoway scatter price weight, saving("${GX_WORK}/gx6.png", replace)`; whether `gx6.png` exists (`GX_s6_named`) and whether `gx6.png.gph` exists (`GX_s6_appended`).
6. A python block (stdlib only; never calls Stata back) reads each case log, takes `first` = the first non-blank line after the echoed `capture noisily` command line that does not start with `> `, replaces the work folder's path with `<work>`, and writes the fixture (`json.dump(..., indent=1, sort_keys=True)` and a final newline). It erases the case logs, the exported files and `git_head.txt`.

**Fixture keys** (`test/fixtures/graph_export_truth.json`):

```
_meta:   stata_version, born_date, dash_commit, extracted, source, os, mode
cases:   no_graph {rc, first}, no_such_name {rc, first}, nodraw_only {rc, first, memory},
         dropped {rc, first, memory}, saving_png {rc, first, named_as_typed, gph_appended}
suffixes: {<s>: {rc, first}} for the 17 spellings above
return_after_twoway: {macros, scalars}
```

Expected from E7: `no_graph` 601 "no Graph window open"; `no_such_name` 693 "could not find Graph window"; `nodraw_only` 601 with memory `Graph`; `dropped` 0 with memory ``; `saving_png` 0, "file <work>/gx6.png saved as .gph format", named 1, appended 0; `return_after_twoway` 0 and 0; the suffixes as E7 lists, `PNG` measured by the extractor (VerifySuffix compares lower-case words, so r(198) "not recognized" is expected). A disagreement is reported, never patched (R7). `git add -f test/fixtures/graph_export_truth.json` (`.git/info/exclude:58` ignores `*.json`); `test/test_export_result.py` names it.

**The S22 truth block** (GE-21..GE-24, in S22's stub block of `test/test_wp30_truth.cscript`, helpers `_s22_*` directly above its header): run through the driver with `WP30_ONLY=S22`.

## TDD test stubs

Regression tests (each fails on the unmodified tree; the expected failure is given):

- Test: `dash` is declared rclass — `test/test_export_result.py::TestDashIsRclass::test_the_program_is_rclass` (fails: `program define dash` has no class).
- Test: the strip branch, the `build` route and the plot route each end with `_dash_result` then `return add` — `test/test_export_result.py::TestDashIsRclass::test_every_writing_route_posts_the_result` (fails: no `_dash_result`).
- Test: `dash` holds no `return local|scalar|matrix` of its own; `_dash_result` holds exactly one `return local filename`, reads `dash__rfile` through `st_global(`, and never contains `$dash__rfile` or `macval(global(` — `…::TestDashIsRclass::test_only_the_result_reaches_r` (fails: program missing).
- Test: `_dash_render_immediate`'s and `_dash_build`'s last statement sets `dash__rfile` through `_dash_abs_path(` — `…::TestTheWritersSetTheResultLast::test_render_immediate_sets_it_last`, `…::test_build_sets_it_last` (fail).
- Test: `_dash_plot` and `_dash_build` drop `dash__rfile` before anything else — `…::TestTheWritersSetTheResultLast::test_each_route_clears_it_first` (fails).
- Test: `_dash_result` reads `graph dir, memory`, calls `_dash_note(` once, and no dash.ado line outside comments runs `graph describe`, `graph display`, `graph drop`, `graph export` or `translate` as a command (AC-22.5's pattern) — `…::TestTheGraphExportNote::test_it_reads_graph_memory_and_uses_the_note_channel` (fails).
- Test: the literal suffix row in `_dash_saving_parse` equals the fixture's recognised suffixes — `…::TestTheImageSuffixes::test_the_row_is_the_suffixes_graph_export_recognises` (fails: no row).
- Test: `_dash_render_immediate` and `_dash_build` each read `_sv_img` and print through `_dash_note(` — `…::TestTheImageSuffixes::test_both_routes_note_a_replaced_suffix` (fails).
- Test: the help — `…::TestTheHelpStatesWhatDashReturns::test_stored_results_and_exporting_are_in_the_jump_list`, `::test_stored_results_lists_r_filename_per_route`, `::test_exporting_states_what_graph_export_does`, `::test_it_states_the_image_suffix_rule`, `::test_it_states_that_printing_prints_the_tab_showing`, `::test_it_states_there_is_no_svg_drawing_mode` (fail).
- **GE-01** (`test_export.cscript`) after `quietly summarize price`, `dash scatter mpg weight, saving(ge01.html, replace)` in a folder the case makes under `c(tmpdir)`: `r(filename)` equals `c(pwd) + "/ge01.html"`, the file exists, `st_dir("r()", "macro", "*")` is exactly `filename` and no scalar is left. Fails first: `r(filename)` empty, `r(fn)` = dash.ado's path.
- **GE-02** the one-line form with no `saving()`: `r(filename)` starts with `c(tmpdir)`, holds `/previews/dash-preview-`, ends `.html`, exists, and equals the path on the log's `dash: dashboard saved to` line. Fails first: empty.
- **GE-03** `dash build, saving(ge03.html) replace`: `r(filename)` absolute, exists; no `r(open)`, no `r(flag)`. Fails first.
- **GE-04** `dash build, saving(ge04.py) replace server`: `r(filename)` absolute `.py`, exists, holds `def make_document`; no `r(fn)`. Fails first.
- **GE-05** `dash twoway scatter mpg weight, saving(ge05.html, replace)` (S12's strip route) stores `r(filename)`; then a registration `dash scatter mpg weight, name(ge05)` straight after it stores nothing (no stale path, no `r(ceiling)`), and so does a registration carrying `saving(ge05b.html)` (named graphs write nothing). Fails first.
- **GE-06** `dash kpi mean(mpg), name(ge06) title("Mean mpg")` after `quietly summarize price`: no `r()` macro or scalar. Fails first: summarize's eight scalars.
- **GE-07** `dash clear`: no `r()`. Fails first: `r(fn)`.
- **GE-08** (guard) a refused `dash scatter mpg, saving(ge08.html, replace)` (r(102)) right after GE-01's successful write: `r()` empty.
- **GE-09** `_dash_result` unit: with `global b "ZZ"` and `mata: st_global("dash__rfile", "/x/a" + char(36) + "b.html")`, `_dash_result` returns `r(filename)` equal to `"/x/a" + char(36) + "b.html"` (compared in Mata) and leaves `dash__rfile` empty; with the global empty, `r()` is empty and no note is printed even with a graph in memory. Fails first: r(199) unrecognized command.
- **GE-10** from a subfolder `sub` of the case folder, `saving(../ge10.html, replace)`: `r(filename)` is `c(pwd) + "/../ge10.html"`; after `cd` back to the case folder, `confirm file` on the copied value succeeds. Fails first.
- **GE-11** `_dash_abs_path` unit cases: `("x.html", "/w", "MacOSX")` → `/w/x.html`; `("/a/x.html", "/w", "MacOSX")` unchanged; `("~/x.html", "/w", "Unix")` unchanged; `("a" + char(92) + "b.html", "/w", "MacOSX")` → `/w/a\b.html`; `("../x.html", "/w/d", "Unix")` → `/w/d/../x.html`; `("x", "/", "Unix")` → `/x`; `("", "/w", "MacOSX")` → `""`; Windows: `("C:\d\x.html", "C:\w", "Windows")`, `("\\srv\x.html", …)` and `("/x.html", …)` unchanged, `("x.html", "C:\w", "Windows")` → `C:\w\x.html`, `("x.html", "C:\", "Windows")` → `C:\x.html` (each backslash built with `char(92)`). Fails first: 3499 not found.
- **GE-12** `twoway scatter price weight` then `dash scatter mpg weight, saving(ge12.html, replace)` under a text log at linesize 255: `cert_log_has` counts exactly one line holding `(note:  dash: graph export writes the graph in Stata's Graph window, not this dashboard; graphs in memory: Graph)`; `graph dir, memory`'s list is `Graph` before and after. Fails first: count 0.
- **GE-13** with `graph drop _all` first, the one-line form, `dash build` and `dash build, server` print no `graph export writes` line; with a graph in memory, a registration, `dash kpi` and `dash clear` print none either. Partly a guard (no-graph half passes first); the registration half fails first only if dash printed it (it does not), so GE-13 is listed as a guard.
- **GE-14** graphs `Graph` and `g2` in memory (drawn in that order): `dash build, saving(ge14.html) replace` prints one note ending `graphs in memory: Graph g2)` and `dash build, saving(ge14.py) replace server` one; with seven graphs (`Graph g2 … g7`) the note ends `Graph g2 g3 g4 g5 and 2 more)`. Fails first.
- **GE-15** one note per command: a `dash build` of a `tabs()` dashboard with three graphs and a KPI, with a graph in memory, prints exactly one `graph export writes` line, and `quietly dash scatter …, saving(…)` still prints it (S06's channel). Fails first.
- **GE-16** (`test_path_validation.cscript`) for each `k` of `png svg pdf eps ps jpg jpeg tif gif emf wmf`: `dash scatter mpg weight, title(GE16) saving(ge16_<k>.<k>, replace)` writes `ge16_<k>.html` holding `GE16` and `<html`, writes no `ge16_<k>.<k>.html`, prints one `(note:  dash: saving() writes HTML, not a .<k> image; using ge16_<k>.html)`, and `r(filename)` ends `/ge16_<k>.html`; `saving(ge16u.SVG, replace)` writes `ge16u.html` with the note's word `.svg` (a distinct stem, because the Mac's file system ignores case). Fails first: `ge16_png.png.html`, no note.
- **GE-17** `dash build, saving(ge17.pdf) replace` writes `ge17.html` with `dash build: saving() writes HTML, not a .pdf image; using ge17.html`; `dash build, saving(ge17s.png) replace server` writes `ge17s.py` (holds `def make_document`) with `dash build: saving() writes a server app, not a .png image; using ge17s.py`. Fails first: `ge17.pdf.html`.
- **GE-18** unchanged names: `saving(ge18.tiff)` writes `ge18.tiff.html` with no image note; `saving(ge18.png.html)` writes that name; `saving(ge18.png.gph)` writes `ge18.png.html` with S12's `.gph` line only; `saving(.png)` writes `.png.html`. Guard for the first three; `.png` fails first only if S22 got the empty-stem rule wrong, so GE-18 is listed as a guard.
- **GE-19** `_dash_saving_parse` unit: `"a.JPEG"` with `html` sets `_sv_file` `a.html` and `_sv_img` `jpeg`; `"a.gph"` sets `_sv_img` `""`; `"a.html"`, `"a.tiff"` and `"dir/.png"` set `_sv_img` `""`; `"a.eps"` sets `eps`, `"a.ps"` sets `ps`; with `py`, `"a.svg"` gives `a.py`. Fails first: `_sv_img` never set.
- **GE-20** (`test_serve_launch.cscript`, before SRV-19) a stubbed `dash serve` (the SRV-17 stub renderer, written in the case's own `c(tmpdir)` folder, after a registration and a `dash build`) after `quietly summarize price`: rc 0 and no `r()` macro or scalar, so neither a path nor the key can be stored. Measured first; listed as a regression if `r()` is non-empty at the base, otherwise as a guard.
- **GE-21** (`test_wp30_truth.cscript`, S22) `graph drop _all`, the one-line form (preview and `saving()`), then `capture noisily graph export` to a `.png` in `` `w30_work' ``: rc and first line equal the fixture's `cases.no_graph`. Guard (holds first; pins that dash makes no Stata graph).
- **GE-22** for every fixture suffix spelling in lower case: `_dash_saving_parse("a." + s, "html")` sets `_sv_img` equal to `s` exactly when the fixture's `first` does not hold "not recognized". Fails first.
- **GE-23** the fixture's `return_after_twoway` is 0 macros and 0 scalars; after `quietly summarize price` and the one-line form, dash leaves 0 scalars and exactly one macro, `filename`. Fails first: `fn`.
- **GE-24** with `twoway scatter price weight` in memory, the one-line form prints the note once, and `graph export` afterwards writes an SVG holding `>Price<` and not `>Mileage (mpg)<`, rc 0: the stale export is now announced. Fails first: no note.

Guard tests (hold on the unmodified tree; listed so G1 does not expect them red):

- `test/test_export_result.py::TestTheGraphExportFixture::test_it_carries_the_stamp`, `::test_graph_export_without_a_graph_is_r601`, `::test_the_recognised_suffixes_are_graph_exports_eleven` (green once 22-02 wrote the fixture).
- GE-08, GE-13, GE-18, GE-21 (and GE-20 if its first run is green).

Pinned test to flip:

- `test/test_help_conformance.py::TestInternalLinksResolve::test_the_reference_scan_found_something` — the link and marker counts move by S22's references (re-derived, R10).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| rclass dispatch, routes, writers, note channel, suffix row, help | pytest `test/test_export_result.py` (structure and help) | `graph_export_truth.json` | n/a (Stata) |
| r() per subcommand, absolute path, stale-path, by-value | cscript GE-01..GE-11, through the driver | none | saved and server builds |
| Stale-graph note | cscript GE-09, GE-12..GE-15, GE-24 | none | saved and server builds |
| Image suffixes | cscript GE-16..GE-19, GE-22 | `graph_export_truth.json` | HTML and `.py` |
| Serve stores nothing | cscript GE-20 (stub renderer) | none | served route |
| twoway truth | cscript GE-21..GE-24 in S22's truth block | `graph_export_truth.json` | n/a |
| Drawing unchanged | `python3 -m pytest test/test_mode_parity.py -q -n0` (G3 guard, no CORPUS change) | none | yes, before and after a filter move |
| Note-count sweep | the scripts that read notes (22-09), through the driver | none | n/a |
| Registries | `test_program_coverage_map.py`, `test_file_headers.py`, `test_no_orphans.py`, `test_function_test_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_tracking_documents.py`, `test_fixtures_are_committed.py`, `test_cscript_hygiene.py` | none | n/a |
| Help kept | `test_help_conformance.py`, `test_help_claims_1.py`, `test_help_claims_2.py`, `test_help_examples.py`, `test_toolbar.py` | none | n/a |

**Acceptance criteria.**

- **AC-22.1** `python3 -m pytest test/test_export_result.py test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_toolbar.py -q -n0` reports 0 failed.
- **AC-22.2** Through the driver, `test_export.cscript` prints GE-01..GE-15 PASS and `test_export.cscript: ALL CHECKS PASSED`; `test_path_validation.cscript` prints GE-16..GE-19 PASS and its `ALL CHECKS PASSED`; `test_serve_launch.cscript` prints GE-20 PASS and `All dash serve option tests PASSED.`.
- **AC-22.3** `WP30_ONLY=S22` on `test_wp30_truth.cscript` prints GE-21..GE-24 PASS and `test_wp30_truth: ALL CHECKS PASSED`, no FAIL, no SKIP.
- **AC-22.4** Every script that reads notes (22-09's list) and `test_help_claims_1.cscript` (HC1-12) report no FAIL.
- **AC-22.5** Outside comment lines, dash.ado runs no `graph describe`, `graph display`, `graph drop`, `graph export` or `translate` command (`grep -v '^\s*//' dash.ado | grep -cE '^\s*((quietly|capture|noisily|cap|qui) +)*(graph +(describe|display|drop|export)|translate) '` prints 0, as at `c96facd`; the note's text, inside a `mata:` line, does not match), and names `dash__rfile` at exactly the six sites of TR-22.2 and TR-22.3 (`grep -v '^\s*//' dash.ado | grep -c dash__rfile` prints 6: the read and the drop in `_dash_result`, the two sets, the two clears).
- **AC-22.6** `python3 -m pytest test/test_mode_parity.py -q -n0` reports 0 failed with no CORPUS change.
- **AC-22.7** The full suite, run once through the queue in the worktree, has 0 failed (E6 for the known flaky tests).

## Tasks

**Commit boundary.** Tasks 22-01 to 22-12 form the one commit of entry P1.28a, subject `Store r(filename), stop leaking internal r(), and note when graph export would write an earlier graph (WP-30 P1.28a)`, made by 22-12 on `wp30-s22` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s22` (`$WT`) after one full run through the queue. The help (22-10) is part of that commit. The body:

1. opens with `<scratch>/22-P1.28a-failure.txt`;
2. gives the measured defects (Evidence E7: `r(fn)` = dash.ado's path, the leaked `r()` per route, the silent stale export, `saving(x.png)` → `x.png.html`);
3. says what changed and where, and names the threats of TR-22.12;
4. carries one line each: `Regression: test/test_export_result.py::<Class>::<test> -- failed at <batch-8 base sha> with <text>` for each failing pytest node; `Regression: test/<script>.cscript <CASE-ID> -- failed at <sha> with <text>` for each failing GE case; `Flipped: test/test_help_conformance.py::TestInternalLinksResolve::test_the_reference_scan_found_something -- <old> links to <old> markers was wrong because the help now links Exporting and Stored results and has a results marker`; a `Flipped:` line for each 22-09 setup change; `Fixture: test/fixtures/graph_export_truth.json (scripts/extract_graph_export_truth.do)`; `BUGS.md: "dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph" (closed)`.

Every command runs from `$WT`; `S=<scratch>/s22` (`mkdir -p "$S"`). A cscript runs only through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`), prefixed `WP30_ONLY=S22` for the truth script. No message, BUGS line, CHANGELOG line or help line names a tool or vendor (G7).

<task type="auto" id="22-01">
  <name>Write the failing structure and help tests</name>
  <files>test/test_export_result.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `<scratch>/batch-8-base.txt` and `git -C "$WT" branch --show-current` prints `wp30-s22`. Copy the S22 rows of `<scratch>/batch-8-impact.txt` into `$S/22-impact.txt` (every S22 symbol is UNKNOWN: confirm the Evidence E9 callers with `grep -n` at the base and record them as unresolved).
    Create `test/test_export_result.py` with the classes `TestDashIsRclass`, `TestTheWritersSetTheResultLast`, `TestTheGraphExportNote`, `TestTheImageSuffixes` and `TestTheHelpStatesWhatDashReturns` of "TDD test stubs", reading dash.ado, dash_parse.mata and dash.sthlp as text. Add a `_program_body(src, name)` helper that matches `^program define <name>(?:,[ \t\w]*)?\s*$` through the next `^end\s*$` and a `_mata_body(src, name)` helper for a Mata function; strip `//` comments before searching code. `test_the_row_is_the_suffixes_graph_export_recognises` reads `test/fixtures/graph_export_truth.json` and skips nothing: it fails while the fixture is absent.
    Run `python3 -m pytest test/test_export_result.py -q -n0 -p no:cacheprovider -rf > "$S/22-01-pytest.log" 2>&1`. Create `<scratch>/22-P1.28a-failure.txt` with the base sha, each failing node and its assertion line. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/22-01-pytest.log"` equals the number of tests in test/test_export_result.py (15); `test -s <scratch>/22-P1.28a-failure.txt`; `git -C "$WT" status --porcelain` lists only `?? test/test_export_result.py`.]]></verify>
  <done>The structure and help regression tests existed and were shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="22-02">
  <name>Extract the graph export truth fixture</name>
  <files>scripts/extract_graph_export_truth.do, test/fixtures/graph_export_truth.json, test/test_export_result.py</files>
  <action><![CDATA[
    Create `scripts/extract_graph_export_truth.do` exactly as "Stata truth" specifies: header, `clear all`/`set more off`/`set linesize 255`, S02's TR-02.9 root stanza copied from a converted extractor at the base (`scripts/extract_emptied_layer_truth.do`) with `<file>` = `extract_graph_export_truth.do`, `GX_REPO`/`GX_OUT`/`GX_WORK`, `adopath ++ "`repo'/"`, `global dash_nobrowser 1`, the stamp globals, `_gx_run`, the cases in the stated order, and the python block (stdlib only, no `shell=True`, the work path replaced by `<work>`, every case log, exported file and `git_head.txt` erased).
    Run it once: `DASH_REPO="$WT" /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$WT/scripts/extract_graph_export_truth.do"`. Check the fixture against Evidence E7 case by case; a disagreement is reported to the orchestrator, never patched.
    Add `TestTheGraphExportFixture` (the three guard tests of "TDD test stubs") to `test/test_export_result.py`. `git add -f` waits for 22-12.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/graph_export_truth.json'));print(sorted(d['_meta']), d['cases']['no_graph']['rc'], len(d['suffixes']), sorted(k for k,v in d['suffixes'].items() if 'not recognized' not in v['first']))"` prints the seven `_meta` keys, `601`, `17` and `['emf', 'eps', 'gif', 'jpeg', 'jpg', 'pdf', 'png', 'ps', 'svg', 'tif', 'wmf']`; `grep -cE '/Users/|/private/|/tmp/' test/fixtures/graph_export_truth.json` prints 0 (no machine path in the fixture); `python3 -m pytest test/test_export_result.py -q -n0 -k Fixture` reports 3 passed.]]></verify>
  <done>twoway's and graph export's measured answers were stored in a stamped fixture that guard tests read.</done>
</task>

<task type="auto" id="22-03">
  <name>Write the failing r() and note cases</name>
  <files>test/test_export.cscript</files>
  <action><![CDATA[
    Append GE-01..GE-15 to `test/test_export.cscript` as one contiguous run after EXP-06's last line and before `display "test_export.cscript: ALL CHECKS PASSED"`, exactly as "TDD test stubs" states, each ending `display "GE-nn PASS: …"`. Extend the header's WHY paragraph with one sentence: the script also certifies what dash returns (`r(filename)`) and the note about `graph export`.
    Rules for the cases: each writes only in a folder it creates under `c(tmpdir)` and erases at its end; GE-10 restores the working folder on every path (`capture noisily` around the `cd` block, then `cd` back); `r(filename)` is copied into a local by value (`mata: st_local("ge_rf", st_global("r(filename)"))`) before any other command, because `cert_log_has` and `cd` replace `r()`; `r()` contents are read with `st_dir("r()", "macro", "*")` and `st_dir("r()", "numscalar", "*")`; note lines are counted with `cert_log_has` on a text log opened at `set linesize 255`; graphs are drawn after the script's `cscript` line (cscript runs `discard`, which empties graph memory) and dropped with `graph drop _all` at each case's end; the script ends with `dash clear`.
    Run the driver for `test_export.cscript` on the unmodified tree; append the first failing case and its message to `<scratch>/22-P1.28a-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c 'EXP-0[1-6] PASS' "$S/run_test_export.log"` prints at least 6 (EXP cases unchanged); `grep -c 'GE-01 PASS' "$S/run_test_export.log"` prints 0 and the log shows GE-01's failure (`r(filename)` empty or `fn` left); `grep -c 'GE-' <scratch>/22-P1.28a-failure.txt` is at least 1.]]></verify>
  <done>The r(), absolute-path, by-value and stale-graph-note regression cases existed and were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="22-04">
  <name>Write the failing suffix, serve and truth cases</name>
  <files>test/test_path_validation.cscript, test/test_serve_launch.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Append GE-16..GE-19 to `test/test_path_validation.cscript` as one contiguous run after S12's last case (PV-44) and before its `ALL CHECKS PASSED` line; insert GE-20 into `test/test_serve_launch.cscript` directly after TOK-04's block (its `dash clear` after the TOK-04 PASS line) and before the SRV-19 banner, because SRV-19 replaces `_dash_find_render` and does not restore it (the script header, :41 and :46-55, places LC and TOK there for the same reason). GE-20 writes its own stub renderer (SRV-17's seven `file write` lines) in a folder it creates under `c(tmpdir)`, registers `dash scatter mpg weight, name(ge20)`, runs `dash build, saving(...) replace nobrowser` into that folder as SRV-17 does, puts the stub on the ado-path for the call only (`adopath ++`, then `adopath -` on every path), runs `quietly summarize price` and `capture noisily dash serve`, reads `r()` with `st_dir` before any other command, erases the folder and ends with `dash clear`. Add a header line after the TOK lines ("GE-20 (WP-30 P1.28a), after TOK-04 and before SRV-19: dash serve stores nothing in r()"). Update `test_path_validation.cscript`'s header case list too.
    In S22's stub block of `test/test_wp30_truth.cscript` (`grep -n '==== S22 P1.28a' test/test_wp30_truth.cscript`), write GE-21..GE-24 between its start and end display lines with `_w30_expect`/`_w30_done`; files only under `` `w30_work' ``, erased before the end line; the fixture is read by one-line `python:` calls of a helper `_s22_fx(key)` defined in a `python:` block directly above S22's header (it reads `fixtures/graph_export_truth.json`, the driver's working folder being `test/`, and sets locals through `sfi.Macro`; stdlib `json` only); `graph drop _all` and `dash clear` before the end line.
    Run the driver for the two area scripts and for `test_wp30_truth.cscript` with `WP30_ONLY=S22`; append each first failure to `<scratch>/22-P1.28a-failure.txt`, and record GE-20's first result (red: regression; green: guard) there.
  ]]></action>
  <verify><![CDATA[`grep -c 'GE-16 PASS' "$S/run_test_path_validation.log"` prints 0 and PV-35..PV-44 still PASS; `grep -c 'SRV-19 PASS' "$S/run_test_serve_launch.log"` prints 1; `grep -c 'GE-22 PASS' "$S/run_test_wp30_truth.log"` prints 0 and `grep -c 'GE-21 PASS' "$S/run_test_wp30_truth.log"` prints 1.]]></verify>
  <done>Every regression case of the section existed and had been shown failing on the unmodified tree, and the failure text was complete.</done>
</task>

<task type="auto" id="22-05">
  <name>Add the Mata path, name and suffix rules</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    Directly after S12's block (after `_dash_launch_warn`'s closing brace, before `_dash_check_utf8`), add `_dash_abs_path` and `_dash_graph_names` exactly as TR-22.4 and TR-22.5 give them, each under a comment block naming WP-30 P1.28a, the measured reason (E7 J3/J5 for the first; G4/G5/G8 for the second) and its linear bound; every backslash is `char(92)`.
    In S12's `_dash_saving_parse`, add the image-suffix rule of TR-22.6 between the `.gph` rule and the `"." + ext` append, with its comment, and set `_sv_img` by value on every call. Change no other line of S12's block.
    Add the two header entries of TR-22.7 after S12's last Public API entry.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_export_result.py -q -n0 -k "row_is_the_suffixes"` reports 1 passed; through the driver, `test_path_validation.cscript` prints GE-19 PASS (GE-16..GE-18 may still fail until 22-07) and PV-35..PV-44 PASS; `test_export.cscript` prints GE-11 PASS.]]></verify>
  <done>The absolute-path, graph-name and image-suffix rules existed in Mata as pure, tested functions.</done>
</task>

<task type="auto" id="22-06">
  <name>Make dash rclass with its result helper</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `dash` (find `^program define dash$`): change the program line to `program define dash, rclass`; insert the comment paragraph of TR-22.1 directly after S12's strip paragraph; add `_dash_result` and `return add` to the strip branch (between `_dash_plot `macval(0)'` and `exit`), to the `build` route (between `_dash_build `macval(_args)'` and `exit`) and after the final `_dash_plot `macval(0)'`. Change nothing else in `dash`.
    Add `_dash_result` exactly as TR-22.2 gives it, with its header comment, directly after `dash`'s `end` and before the `_dash_do_render` header comment.
    In `_dash_require_mata`, end S12's continuation line with ` ///` and add `        _dash_abs_path _dash_graph_names` (TR-22.7).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_export_result.py -q -n0 -k "TestDashIsRclass or graph_memory"` reports 0 failed; `python3 -m pytest test/test_file_headers.py test/test_packaging.py test/test_serve_options.py test/test_abbreviations.py -q -n0 -p no:cacheprovider` reports 0 failed; through the driver `test_export.cscript` prints GE-05..GE-09 PASS.]]></verify>
  <done>dash posted only its own result on every route, through one helper that reads the path by value and prints the stale-graph note.</done>
</task>

<task type="auto" id="22-07">
  <name>Set the result in the writers</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-22.3: the `mata: st_global("dash__rfile", _dash_abs_path(...))` statement with its comment directly above `end` in `_dash_render_immediate` (after the opener/saved-to `if`/`else`, below S12's preview line) and in `_dash_build` (after the server/HTML `if`/`else`); `capture macro drop dash__rfile` with its comment directly after `version 19` in `_dash_plot` and `_dash_build`.
    Apply TR-22.6's two caller notes: in `_dash_render_immediate` and in `_dash_build`, the `if "`_sv_img'" != ""` statement directly after S12's `.gph` line, through `_dash_note`, reading every value with `st_local`. Change no other line of these programs.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_export_result.py -q -n0` reports 0 failed except the help class (22-10); through the driver `test_export.cscript` prints GE-01..GE-15 PASS and `ALL CHECKS PASSED`, `test_path_validation.cscript` GE-16..GE-19 PASS, `test_serve_launch.cscript` GE-20 PASS, and `WP30_ONLY=S22` on `test_wp30_truth.cscript` GE-21..GE-24 PASS.]]></verify>
  <done>Every writing route stored the absolute path it wrote, cleared any stale one first, and noted a replaced image suffix.</done>
</task>

<task type="auto" id="22-08">
  <name>Register the new programs and functions</name>
  <files>test/program_coverage_map.py</files>
  <action><![CDATA[
    Under the `# WP-30 S22 (P1.28a): r(filename) and the stale-graph note (P1.28 part a, M8)` anchors, alphabetical, add the three entries of TR-22.7: `"_dash_result"` in `COVERAGE["dash.ado"]`; `"_dash_abs_path"` and `"_dash_graph_names"` in `COVERAGE["dash_parse.mata"]`. Edit no other entry.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_program_coverage_map.py test/test_no_orphans.py test/test_file_headers.py test/test_function_test_map.py test/test_statistical_helpers.py -q -n0 -p no:cacheprovider -k "coverage or orphan or header or function_test_map or CarriesEveryName"` reports 0 failed.]]></verify>
  <done>The coverage map named a certification case for every new program and Mata function.</done>
</task>

<task type="auto" id="22-09">
  <name>Sweep the scripts that count notes</name>
  <files>none</files>
  <action><![CDATA[
    List the scripts that read notes at the base: `grep -l '(note:' test/*.cscript > "$S/22-notes-scripts.txt"` (S06's needle files: test_custom_scheme, test_render_log_clean, test_render_locate, test_adversarial, test_wp29_truth, test_help_claims_8, and any later section's). Run each through the driver, and `test_wp30_truth.cscript` with `WP30_ONLY` unset; also `test_help_claims_1.cscript` (HC1-12).
    For each FAIL, read the case: if it fails only because the stale-graph note adds a line while a twoway graph from an earlier case is in memory, and the case is not inside another WP-30 section's truth block, insert `quietly graph drop _all` directly before that case's first dash call (a setup change; its counts and needles stay as written) and record a `Flipped:` line in `$S/22-flips.txt` ("<node> -- counted a note dash now prints when a Stata graph is in memory; the case now clears Stata's graphs before its dash call, its counts unchanged"). At most three files may change in this task; name them in `$S/22-flips.txt`.
    A failure inside another section's block of `test/test_wp30_truth.cscript`, a failure for any other reason, or a fourth file: stop and report to the orchestrator before editing (R1; index step 2, "a red result belongs to the section that owns the test").
  ]]></action>
  <verify><![CDATA[Every script listed in `$S/22-notes-scripts.txt`, `test_wp30_truth.cscript` (all blocks) and `test_help_claims_1.cscript` report no FAIL through the driver; `git -C "$WT" diff --name-only -- test/` lists at most three files beyond the section's own (named in `$S/22-flips.txt`). Expected at the base: no change needed.]]></verify>
  <done>No case anywhere counted the new note by accident, and any setup change was named with its reason.</done>
</task>

<task type="auto" id="22-10">
  <name>Update the help and its link count</name>
  <files>dash.sthlp, test/test_help_conformance.py</files>
  <action><![CDATA[
    Make the dash.sthlp edits of TR-22.8 in order: the two jump-list lines after the Dashboard Options entry; the Description paragraph after :135-139; the clause in the Dashboard Options `saving()` row as S12 left it; the three Exporting paragraphs after the first Exporting paragraph; the Stored results section before `{marker layout}`. Edit no other paragraph (R3); add no `{cmd:. …}` example line.
    Run `python3 -m pytest test/test_help_conformance.py -q -n0 -k reference_scan` to read the new counts, then flip `TestInternalLinksResolve::test_the_reference_scan_found_something`'s assertion to them, with the comment line `# <old> -> <new> links to <old> -> <new> markers: WP-30 P1.28a links Exporting and Stored results (jump list, Description, Stored results) and adds the results marker.` above the assertion, keeping the existing history comments (R10). Add its `Flipped:` line to `$S/22-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_export_result.py test/test_help_conformance.py test/test_help_claims_1.py test/test_help_claims_2.py test/test_help_examples.py test/test_toolbar.py -q -n0 -p no:cacheprovider` reports 0 failed; `grep -c '{marker results}' dash.sthlp` prints 1; `grep -c 'r(filename)' dash.sthlp` is at least 4.]]></verify>
  <done>The help documented what dash stores, what graph export does after dash, the image suffix rule, printing and the missing SVG drawing mode, and the link pin carried its new values with the reason.</done>
</task>

<task type="auto" id="22-11">
  <name>Certify the section through the slot</name>
  <files>none</files>
  <action><![CDATA[
    Through the driver, run `test_export.cscript`, `test_path_validation.cscript`, `test_serve_launch.cscript`, `test_wp30_truth.cscript` (`WP30_ONLY=S22`, then unset), `test_help_claims_1.cscript`, `test_bug_regressions.cscript`, `test_serve_browser.cscript`, `test_json_escaping.cscript` and `test_program_coverage.cscript`. Run `python3 -m pytest test/test_mode_parity.py -q -n0` (G3 guard) and `python3 -m pytest test/test_export_result.py test/test_program_coverage_map.py test/test_file_headers.py test/test_cscript_hygiene.py test/test_fixtures_are_committed.py -q -n0`.
    Check AC-22.5 with its two comment-stripping greps (0 and 6).
  ]]></action>
  <verify><![CDATA[AC-22.1 to AC-22.6 hold: every listed script ends with its ALL-PASSED line and no FAIL or SKIP; the pytest runs report 0 failed; `git -C "$WT" status --porcelain --ignored | grep -v '^!! .gitnexus'` lists only the section's files and `$S/22-flips.txt`'s.]]></verify>
  <done>Every test the section added or touched passed in Stata and in pytest, and the drawing guard stayed green.</done>
</task>

<task type="auto" id="22-12">
  <name>Close the entry and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Find the title as `WP30_OPEN["P1.28a"]`. Close that BUGS.md entry in place (`- [x]`) with the Resolution of Notes ("BUGS.md resolution"), naming only tests that exist. Delete the `"P1.28a": …` key line of `WP30_OPEN` in `test/test_tracking_documents.py`, and nothing else there (R5).
    Replace `<!-- WP-30 P1.28a -->` under `### New` and under `### Changed behaviour (may need your do-files changed)` in place with the two lines of Notes ("CHANGELOG lines"), each ending `(WP-30, P1.28a)` (R4).
    Run `python3 -m pytest test/test_tracking_documents.py -q -n0`. Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`), one full run `<scratch>/full_suite_queue.sh "$WT" <scratch>/22-full-1.log` waited for and read (E1, E6). Stage the section's files, with `git add -f test/fixtures/graph_export_truth.json`; check `git diff --cached --name-only` (G6: no CLAUDE.md, .gitignore, AGENTS.md, .gitnexus/, .ultraplan/wp30/, html or scratch file). Write the message to `$S/msg.txt` in the Commit boundary form, run G7 on it, confirm `git -C "$WT" branch --show-current` prints `wp30-s22`, commit with `git commit -F "$S/msg.txt"`, and run G7 on `git log -1 --format=%B`.
  ]]></action>
  <verify><![CDATA[`cd test && python3 -c "import test_tracking_documents as t; print('P1.28a' in t.WP30_OPEN, 'P1.28a' in t.WP30_LISTS)"` prints `False True` (`WP30_LISTS`/`WP30_SECTION` keep the key for good, TR-01.2); `grep -c '<!-- WP-30 P1.28a -->' CHANGELOG.md` prints 0; `grep -c '(WP-30, P1.28a)' CHANGELOG.md` prints 2; `<scratch>/22-full-1.log` ends `exit=0` with 0 failed; `grep -Eic 'claude|anthropic' "$S/msg.txt"` and the same on `git log -1 --format=%B` print 0; `git log -1 --format=%s` ends `(WP-30 P1.28a)`.]]></verify>
  <done>The entry was closed with its tests named, its markers replaced and its key deleted, and the one commit of P1.28a was made on wp30-s22 after a green full run.</done>
</task>

## Section completion criteria

- `dash` is rclass; after every command `r()` holds only `r(filename)` (an absolute path, by value) or nothing, on all routes: one-line with and without `saving()`, the twoway-prefixed form, registration, `dash kpi`, `dash build` (HTML and server), `dash clear`, `dash serve` and a refusal.
- With a Stata graph in memory, each file-writing command prints exactly one `(note:  dash: graph export writes …)` line naming up to five graphs; without one, none; graph memory unchanged.
- `saving()` with one of the eleven suffixes writes `.html`/`.py` with one note on both routes; other names unchanged.
- The help's jump list, Description, Dashboard Options row, Exporting and Stored results say so, including printing and the missing SVG drawing mode.
- GE-01..GE-24 pass; the 15 structure/help tests and 3 fixture guards pass; the link pin is flipped with its reason; the fixture is committed with its `_meta` stamp.
- No change to `dash_render.py`, the served template, JS, copy lists or `function_test_map.py`; `test_mode_parity.py` green.
- BUGS.md entry `P1.28a` closed, its `WP30_OPEN` key gone, both markers replaced; one commit `(WP-30 P1.28a)` on `wp30-s22` after a green full run.

## Notes

**Traps.**

- Never `return local filename "$dash__rfile"` or `` `macval(global(dash__rfile))' ``: Stata expands the value again (critic c3). Read with `st_global()`, return through `` `"`macval(_rf)'"' `` (c4 Q5).
- `return add` posts the most recent rclass call's `r()`; it must follow `_dash_result` directly, with nothing rclass between them.
- `_dash_result` runs only after the route's program returned: an rclass program that stops after its own `return` keeps it (C6b), so nothing may run after `return local` that can fail.
- `pathjoin()` rewrites `\` and resolves `..` (J3, J5); `_dash_abs_path` exists to avoid it. `pathisabs("~/x")` is 1 on Unix; `_dash_abs_path` agrees.
- `graph describe` names the current graph, which is not what `graph export` writes after `graph drop`, `graph close` or a `nodraw` draw (G4, G5, G8): name the `graph dir, memory` list only.
- A `nodraw`-only graph is in memory while `graph export` fails r(601) (G1): the note still prints, and its wording ("writes the graph in Stata's Graph window") stays true.
- `cscript` runs `discard`, which empties graph memory (p4.do): a case draws its graph after its script's `cscript` line.
- `cert_log_has`, `cert_file_has`, `cd`, `graph dir` and `confirm` replace `r()`: copy `r(filename)` first.
- Logs wrap long lines at the line size; count notes with `cert_log_has` (which joins wrapped lines) at `set linesize 255`.
- The image word in the note comes from the fixed row, never from the user's suffix bytes, so `.SVG` reads `.svg` in the note.
- S12's `_dash_plot` validation call of `_dash_saving_parse` sets `_sv_img` too; it is unused there, and no note may be printed on that route.

**Merge rules touched.**

- **R1** (cscripts): GE-01..GE-15 at the end of `test_export.cscript` and GE-16..GE-19 at the end of `test_path_validation.cscript`, each one contiguous run; GE-20 in `test_serve_launch.cscript` directly before SRV-19 (the one place a case that needs the real renderer locator can run there; the script's own ordering rule, header :41-55); GE-21..GE-24 only inside S22's block, `_s22_*` helpers directly above its header. S23 may also add relay cases to `test_serve_launch.cscript` in batch 8: S22 lands first, and the merger keeps both runs in merge order.
- **R2** (maps): `program_coverage_map.py` under S22's anchors only; no copy-list or `function_test_map.py` change.
- **R3** (help): jump list, Description, Dashboard Options `saving()` row, Exporting and Stored results only. S23 edits Server Mode and S24 Stata scheme support in the same batch.
- **R4** (CHANGELOG): the two `P1.28a` markers only, in place.
- **R5** (BUGS.md, `WP30_OPEN`): the `P1.28a` entry and key line only.
- **R6** (dash.ado, dash_parse.mata): every new program and function under `version 19`; A154's order kept (S22's statements below S12's strip; S25's guard goes above the strip in batch 9); the export-block paragraphs of `_dash_render_immediate` and `_dash_build` gain S22's last statement, separate from S12's grammar paragraph; the Mata header gains two entries in place.
- **R7** (fixtures): `graph_export_truth.json` is new, extractor-written, stamped, `git add -f`, never hand-patched.
- **R10** (combined pins): the help link count, re-derived on the worktree; the merger re-derives it after landing if S23 or S24 also moved it.

**Commit body line forms.** `Regression: test/test_export_result.py::<Class>::<test> -- failed at <batch-8 base sha> with <text>`; `Regression: test/<script>.cscript GE-nn -- failed at <sha> with <text>`; `Flipped: <node> -- <old expectation> was wrong because <why>`; `Fixture: test/fixtures/graph_export_truth.json (scripts/extract_graph_export_truth.do)`; `BUGS.md: "dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph" (closed)`.

**BUGS.md resolution** (22-12; `<ddmonyyyy>` is the commit date):

`  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.28a). dash is rclass and stores r(filename), the absolute path of the file a command wrote (the one-line form's page or temporary preview, dash build's page, dash build, server's .py app): _dash_render_immediate and _dash_build set it as their last statement through _dash_abs_path, and _dash_result posts it by value, with return add, on the plain, twoway-prefixed and build routes. A registration, dash kpi, dash clear, dash serve and a refused command store nothing, and no helper's r() (r(fn) naming dash.ado, r(open), r(flag), r(ceiling), summarize's results) reaches the user. A command that writes a file prints one note, through the note channel, when Stata holds a graph in memory: graph export writes the graph in Stata's Graph window, not the dashboard, naming up to five graphs (_dash_graph_names); dash never changes graph memory. saving() with a suffix graph export writes (.png .svg .pdf .eps .ps .jpg .jpeg .tif .gif .emf .wmf, any case) writes .html, or .py with server, with a note, on the one-line form and dash build (_dash_saving_parse). The saved page and the served app are drawn as before. The help gains Stored results and states what graph export does after dash, that printing prints the tab showing, and that there is no SVG drawing mode. Pinned by test/test_export_result.py::TestDashIsRclass::test_every_writing_route_posts_the_result, test/test_export_result.py::TestTheImageSuffixes::test_the_row_is_the_suffixes_graph_export_recognises, test/test_export.cscript GE-01, test/test_export.cscript GE-12, test/test_path_validation.cscript GE-16, test/test_serve_launch.cscript GE-20, test/test_wp30_truth.cscript GE-24; fixture test/fixtures/graph_export_truth.json. Residual, deferred (WP-30): a do-file export to an image (GAPS2-E10c) waits for the deferred platform package (M8); a graph removed with graph drop that the console's Graph window still shows is exported without a note.`

**CHANGELOG lines** (22-12):

Under `### New`:

```
- `dash` stores the file it wrote in `r(filename)`, as an absolute path:
  the one-line form's page (or its temporary preview), `dash build`'s
  page and `dash build, server`'s app. A command that writes a file notes
  once, when Stata holds a graph in memory, that `graph export` writes
  that graph and not the dashboard. The help gains Stored results and says
  what `graph export`, printing and the toolbar can and cannot do.
  (WP-30, P1.28a)
```

Under `### Changed behaviour (may need your do-files changed)`:

```
- `r()` after `dash` holds only `r(filename)`, and nothing after a
  registration, `dash kpi`, `dash clear`, `dash serve` or a refusal, as
  `twoway` clears `r()`. It used to hold dash's internal results, such as
  `r(fn)` naming dash.ado after the one-line form, `r(open)` and `r(flag)`
  after `dash build`, and `summarize`'s `r(mean)` after `dash kpi`.
  `saving(fig.png)`, or any suffix `graph export` writes, now writes
  fig.html with a note; the one-line form wrote fig.png.html silently and
  `dash build` refused it. (WP-30, P1.28a)
```

**Notes for the closeout** (S58; A145). Text this section hands over:

- **GAPS2.md J7** (its only WP-30 entry is P1.28a): `- **Tracked:** Closed in WP-30, BUGS.md "dash returns no r(filename), and graph export after dash fails r(601) or silently exports an earlier Stata graph", commit <sha>`. Plan dispositions to record beside it: step 1 (a `twoway` companion) not taken (M8, no B4); step 2 (`output_backend(svg)`) rejected because an SVG figure breaks the grid's PNG save (P1.28.2), the SVG need met by S54's toolbar action; step 3 (rclass `r(filename)`) done here, its iframe sentence left to P3.4 (J7-d); step 4 (print stylesheet) moved to P3.11 (P1.28.5), the help documenting "prints the tab showing"; step 5's byte-identical companion test is moot.
- **GAPS2.md E10**: Closed only when P1.28b (S54) has landed too (S01's map lists E10 under P1.28a and P1.28b). GAPS2-E10c (scripted export at a chosen size) stays open in the deferred platform package; E10a (KPI cards and header in the PNG) is P3.11's.
- **DROPIN-REMAINING.md P1.28**: part a closed by S22's commit (r(filename), the stale-graph note, image suffixes, the help); part b by S54's.
- **ROADMAP.md**: the deferred platform package carries P1.28 B3, a `dash export using file.png|pdf|svg` driven by a browser found on the machine, with `r(filename)` its output path (P1.34.6); P3.11 gains the `beforeprint` layout of every tab.
- **TWOWAY_COVERAGE_AUDIT.md**: the `saving()` row gains "a name ending in a `graph export` suffix: twoway writes a .gph under that name; dash writes .html with a note (WP-30 P1.28a)", and a `Stored results` row: "twoway stores nothing; dash stores r(filename) (WP-30 P1.28a)".
- **Maintainer question (put with ratification item 16, A151).** Register P1.28.3 says "one line per dash command, only when a graph is in memory"; this section prints the note only on the commands that write a dashboard file (the one-line form, `dash build`, `dash build, server`), so a registration, `dash kpi`, `dash clear` and `dash serve` print none. **Recommendation: ratify this reading.** A registration writes nothing a user could export, so a note there would repeat on every graph of a session that holds a Stata graph, and the file-writing command that follows prints it once anyway; `dash serve` writes no file of the user's. If the maintainer wants the broader reading, `_dash_result` is also called on the registration and serve routes (TR-22.1), still once per command.
