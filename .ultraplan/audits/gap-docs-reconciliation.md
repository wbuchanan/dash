# `dash` — Documentation vs. Behaviour Reconciliation

Scope: `dash.sthlp` (744 ln), `dash_setup.sthlp` (125 ln), `dash.ado` (1649 ln),
`dash_parse.mata` (1 abbreviation table), `dash_render.py` (10,455 ln),
`PLAN.md` / `BUGS.md` / `TODO.md`. There is **no `README`** in the repo.

Method: every syntax diagram and every option entry in the help was walked against the
corresponding `syntax` statement in `dash.ado` and against the option keys actually read
in `dash_render.py`. Every Table A row and the material Table B/D rows were **empirically
executed** against StataNow 19.5 (`/usr/local/bin/stata`) with `sysuse auto`; observed
return codes and byte-normalised HTML diffs are quoted inline.

Severity key: **BLOCKER** = user's do-file aborts · **SILENT** = wrong output, no error ·
**DOC-ONLY** = code is right, help is wrong.

Counts: **A = 17 · B = 14 (12 real + 2 starting points disproved) · C = 16 · D = 19 · E = 180+ sites**

---

## Starting points that turned out to be WRONG (stated up front, as required)

| Starting point | Verdict | Disproving code |
|---|---|---|
| `link(_all)` not implemented | **WRONG — it is implemented** | `dash_render.py:6855` `if "_all" in link_names: link_names = list(all_graph_names)`; also `:6983`, `:7842`, `:8382`. Executed: `dash build, link(_all)` → `rc=0`, linked source built. |
| `by()` combined with `link()` — "verify whether the code still forbids it" | **Code does NOT forbid it; the help is stale** | `dash_render.py:6873-6878` adds by-vars to the shared linked source; `:6991-6999` builds per-panel `CDSView(filter=BooleanFilter(...))` from `self._facet_masks`; `:7536-7620` is the whole by()+link() branch. Executed `dash build, link(s1 s2)` with `s1` faceted → `rc=0`. Moved to **Table D (D9)**. The `Raises: ValueError` docstring at `dash_render.py:6966-6968` is itself stale. |
| `timeout()` units mismatch | **ALREADY FIXED — no divergence** | `dash.sthlp:216-217` "minutes"; `dash.ado:1502-1505` "non-negative integer in minutes"; `dash_render.py:10392` "timeout in minutes"; `dash_render.py:10446` `_time.sleep(args.timeout * 60)`. Consistent end-to-end. |
| secondary-axis options (`ytitle2()` etc.) undocumented | **WRONG — they ARE documented** | `dash.sthlp:704-707` documents `ytitle2()`, `ylabel2()`, `yscale2(log)`, `xtitle2()`, `xlabel2()`, `xscale2(log)`; implemented at `dash_render.py:5733-5793`. (Placement is odd — buried inside the `xaxis()/yaxis()` entry of the *"Unsupported"* section — but it is documented.) |
| `jitter()` / `jseed()` / `msangle()` undocumented | **WRONG — they ARE documented** | `dash.sthlp:683-695`. Implemented at `dash_render.py:1177-1200` and `:1478-1490`. The real defect is *placement*: they sit under the heading "Unsupported Stata twoway options" (`dash.sthlp:666-673`), so a reader is told they are unsupported and then told how to use them. |
| multi-`filter()` mechanism undocumented | **PARTLY WRONG** | `dash.sthlp:325-327` explicitly says "Multiple `filter()` options may be specified on the same `dash build` call", and `:332-334` gives a two-filter example. The *Mata pre-extraction* (`dash.ado:1170`) and the `;` separator are internal details only. |
| `__all__` dropdown sentinel undocumented | **Correct, but it is an internal detail** | `dash_render.py:4732-4736` computes a collision-proof sentinel; the user only ever sees the label `"All"`, which `dash.sthlp:314` already documents correctly. **Not worth documenting.** |

---

# TABLE A — DOCUMENTED BUT NOT ACCEPTED (`syntax` rejects → do-file aborts)

Every row below was executed; the quoted `rc` and Stata error text are observed, not inferred.

| # | Documented | Doc cite | Code reality | Observed | Rank |
|---|---|---|---|---|---|
| **A1** | `scheme(`*schemename*`)` on `dash build` | `dash.sthlp:79` (syntax diagram) + `dash.sthlp:709-717` (full option entry) + `dash.sthlp:161-162` ("`scheme()` is fully supported") | `dash.ado:1174-1185` — the `dash build` syntax block accepts only `SAVing TItle SUBtitle LAYout LINK THEME REPLACE SERVER TABS FILTERPOSition`. No `SCHEME`. | `option scheme() not allowed`, `rc=198` | **BLOCKER** |
| **A2** | `name(`*identifier*`[, replace]`)` | `dash.sthlp:54` (syntax diagram); "Use name(`name`, replace) to overwrite" is even printed by `dash.ado:880-881` | `dash.ado:857-862` validates the whole `name()` payload against `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$`, so `"a1, replace"` fails before the `replace_flag` regex at `dash.ado:866-869` is ever consulted. The replace feature is **dead code**. | `dash: invalid graph name 'a1, replace'.` `rc=198` | **BLOCKER** |
| **A3** | `mlac(`*color*`)` | `dash.sthlp:537` `{cmdab:mlac:olor}` | `dash_parse.mata:186` maps `mlc`→`mlabcolor`. `mlac` is not in the exact-match table and is not a Stata min-abbrev of the lowercase `mlabcolor(string)` at `dash.ado:331`. | `option mlac() not allowed`, `rc=198` (`mlc`/`mlabcolor` → `rc=0`) | **BLOCKER** |
| **A4** | `mlas(`*size*`)` | `dash.sthlp:538` `{cmdab:mlas:ize}` | `dash_parse.mata:187` maps `mls`→`mlabsize`. | `option mlas() not allowed`, `rc=198` | **BLOCKER** |
| **A5** | `mlap(#)` | `dash.sthlp:540` `{cmdab:mlap:osition}` | `dash_parse.mata:188` maps `mlp`→`mlabposition`. | `option mlap() not allowed`, `rc=198` | **BLOCKER** |
| **A6** | `mlag(#)` | `dash.sthlp:543` `{cmdab:mlag:ap}` | `dash_parse.mata:189` maps `mlg`→`mlabgap`. | `option mlag() not allowed`, `rc=198` | **BLOCKER** |
| **A7** | `xli(#)` | `dash.sthlp:642` `{cmdab:xli:ne}` | `dash_parse.mata:220` maps `xl`→`xline`. | `option xli() not allowed`, `rc=198` (`xl(3000)` → `rc=0`) | **BLOCKER** |
| **A8** | `yli(#)` | `dash.sthlp:643` `{cmdab:yli:ne}` | `dash_parse.mata:221` maps `yl`→`yline`. | `option yli() not allowed`, `rc=198` | **BLOCKER** |
| **A9** | `no(`*string*`)` for `note()` | `dash.sthlp:644` `{cmdab:no:te}` | `dash_parse.mata:213` maps only the *full* `note`→`note`; nothing shorter. | `option no() not allowed`, `rc=198` | **BLOCKER** |
| **A10** | `xlab(...)` | `dash.sthlp:639` `{cmdab:xlab:el}` — **self-contradictory with `dash.sthlp:637` `{cmdab:xla:bel}`** | `dash_parse.mata:211` maps `xla`→`xlabel` only. | `option xlab() not allowed`, `rc=198` (`xla(...)` → `rc=0`) | **BLOCKER** |
| **A11** | `nam(`*id*`)` on `dash kpi` | `dash.sthlp:61` `{cmdab:nam:e}` (KPI syntax diagram) | `dash.ado:1065` declares `name(string)` in **lowercase**, so Stata permits no abbreviation. (The graph path gets `nam`→`name` from `dash_parse.mata:216`, but `dash kpi` never goes through Mata.) | `option name() required`, `rc=198` | **BLOCKER** |
| **A12** | `upd(`*mode*`)` on `dash kpi` | `dash.sthlp:66` and `dash.sthlp:388` `{cmdab:upd:ate}` | `dash.ado:1070` declares `UPDATE(string)` — all-caps means the full word is required. | `option upd() not allowed`, `rc=198` | **BLOCKER** |
| **A13** | `play()` — "will produce a warning and the option will be ignored" | `dash.sthlp:157-160` | Not present in `_dash_parse_plot_opts` (`dash.ado:293-326`) or `_dash_parse_graph_opts` (`dash.ado:230-246`). | `option play() not allowed`, `rc=198` | **BLOCKER** |
| **A14** | `nodraw` — same claim; plus `dash.sthlp:719-721` | `dash.sthlp:157-160`, `:719-721` | Same as A13. | `option nodraw not allowed`, `rc=198` | **BLOCKER** |
| **A15** | **Any** unrecognised `twoway` option — "No error is produced for unknown options, so existing Stata graph commands copy-pasted into `dash` will still run" | `dash.sthlp:669-673` | `dash.ado:293-326` is a closed `syntax` list. Nothing falls through. | `ttitle(x)`→`rc=198`; `xsize(5) ysize(3)`→`rc=198`; `sort`→`rc=198` | **BLOCKER** (the single most damaging doc claim — it invites copy-paste that always aborts) |
| **A16** | `histogram`'s `bin(#)` | `histogram` is a supported plot type (`dash.sthlp:30`, `:463`, `:553`) and `dash.sthlp:125-127` promises "`dash` accepts the same syntax as `twoway`" | `dash_render.py:2985` and `:3001` **read** `options["bin"]`, but `bin` is absent from `dash.ado:293-326`. Also `width` (`dash_render.py:2176`) and `percent` are unreachable. | `option bin() not allowed`, `rc=198`; `width()`→`rc=198`; `percent`→`rc=198` | **BLOCKER** |
| **A17** | `function y=`*exp* | `dash.ado:560` advertises `function` in the supported-plot-type error message; `dash.ado:628-631` contains dedicated code to strip the `y=` prefix | `dash.ado:453-459` `_dash_parse_varpart_any` uses `syntax anything(name=vals)`, which rejects a leading `=` before the strip at `:630` can run. | `=exp not allowed`, `rc=101` (`dash function x^2` → `rc=0`) | **BLOCKER** |

---

# TABLE B — DOCUMENTED / ACCEPTED BUT NOT IMPLEMENTED

| # | Option | Doc cite | `dash.ado` accepts at | Renderer reality | Evidence | Rank |
|---|---|---|---|---|---|---|
| **B1** | `layout(`*name*`:`*row*`,`*col* ...`)` explicit placement | `dash.sthlp:272-275`; also `PLAN.md:97` | `dash.ado:1226` (regex accepts `name:r,c`), emitted at `:1433` | `dash_render.py:6767-6800` `_compute_grid` handles **only** `"auto"` and a 2-token `"N M"`; a 3-token placement string takes the `# Fallback: auto` branch at `:6797-6800`. `_assemble_layout` (`:7389-7440`) then fills cells in plain registry order — there is no placement map anywhere in the file. | `layout(s1:1,1 s2:1,2 k1:2,1)` → `rc=0`; output HTML **byte-identical** (after UUID normalisation) to `layout(auto)` | **SILENT** |
| **B2** | graph-level `scheme(`*schemename*`)` | `dash.sthlp:709-717`; `dash.sthlp:161-162` "fully supported" | `dash.ado:239`, `:319`, `:512`, `:676` — emitted into `graph_options` | `dash_render.py:4991-4995` reads `scheme` **only** from `build_options`; the only other `graph_options` key read near it is `hover` (`:4940`). And `dash.ado` **never writes** a `build_options["scheme"]` key — see `dash.ado:1433` (build) and `dash.ado:974` (immediate, hard-codes `{"layout":"1 1","theme":"default"}`). So `scheme()` is dead on every path. | `scheme(economist)` output = 1 226 985 B, identical to no-scheme; `theme(economist)` = 1 227 019 B | **SILENT** |
| **B3** | `falpha()` / `fa()` | Covered only by the blanket `dash.sthlp:125-127` twoway-compatibility promise | `dash.ado:303`, `:348`, `:479`; `dash_parse.mata:198` (`fa`), `:206` (`fal`) | **Zero** occurrences of `falpha` in `dash_render.py`. Value is serialised into the spec JSON and never read. | `grep -c falpha dash_render.py` → 0 | **SILENT** |
| **B4** | `mlcolor()` (marker outline colour) | `dash.sthlp:125-127` blanket promise | `dash.ado:297`, `:331`, `:477` | **Zero** occurrences of `mlcolor` in `dash_render.py`. (Marker outlines are driven by `lcolor` at `dash_render.py:1448`.) | `grep -c mlcolor dash_render.py` → 0 | **SILENT** |
| **B5** | `mlabwidth()` / `mlw()` | `dash.sthlp:125-127` blanket promise | `dash.ado:297`, `:339`; `dash_parse.mata:190` | `dash_render.py:1905` — `options.get("mlabwidth")  # consumed; no-op` | source comment | **SILENT** |
| **B6** | `coloruseplegend` | *Not documented at all* — accepted but dead on both sides | `dash.ado:307`, `:360`, `:481` | `dash_render.py:1590` — `_use_plegend = bool(options.get("coloruseplegend"))  # noqa: F841` — assigned, never used | source | **SILENT** |
| **B7** | `theme(dark)` | `dash.sthlp:248` | `dash.ado:1181` (`THEME(string)`, unvalidated) | `_THEME_SCHEME_MAP` at `dash_render.py:4983-4989` = `{default, clean, mono, economist, sj}`. `"dark"` passes through unmapped (`:5000`) → `SchemeParser("dark")` → `ValueError` at `:797-802` → **swallowed** at `:5005-5007` → `s2color`. | `theme(dark)` output **byte-identical** to `theme(default)` (both 1 547 869 B); `theme(mono)` differs (1 547 809 B) | **SILENT** |
| **B8** | KPI `update(brush)` in standalone HTML | `dash.sthlp:399-400`, `:402-403`, and the comparison table `dash.sthlp:424` | `dash.ado:1093-1097` validates `filter|brush|both` | Brush→KPI wiring exists **only** in the generated server app: `dash_render.py:10204-10232` (`shared_source.selected.on_change('indices', ...)`). In standalone there is no `selected.on_change` / `selected.js_on_change` anywhere. `self._kpi_update_modes` (`:5030`) is declared and **never read**. Worse: `update(brush)` also fails the `kupdate in ("filter","both")` test at `:6886-6891` and `:7273`, so the card is excluded from the filter refresh too — it is **completely static**. | code + grep | **SILENT** |
| **B9** | `dash kpi` `[if]` / `[in]` | `dash.sthlp:59`, `:347` (both syntax diagrams show `{ifin}`) | `dash.ado:1063` accepts; `:1102-1119` computes the statistic **with** the qualifier | The KPI JSON written at `dash.ado:1421` carries **no** `if_expr`/`in_expr` key, and `dash_render.py:7121-7131` **discards** the Stata-computed value and recomputes via `_compute_kpi_stat` (`:5140`), which reads `self._df[varname].dropna()` — the **full** dataset. `grep "kpi.*if_expr"` → 0 hits. | `dash kpi mean(mpg) if foreign==1` → Stata reports **24.7727**; the rendered card `kpi_val_kif` shows **21.2972972972973**, identical to the unqualified card | **SILENT** (silently wrong numbers on a KPI card) |
| **B10** | custom `.scheme` file "in the current working directory … specify its base name without the extension" | `dash.sthlp:711-713` | n/a (reached only via `theme()`, see B2) | `dash_render.py:747` — `is_file_ref = name.endswith(".scheme") or os.sep in name or "/" in name`. Only a **file ref** searches CWD (`:751-754`); a bare base name is looked up **solely** in the bundled `schemes/` dir (`:756-760`). The renderer's own error text at `:800-801` says "place a .scheme file in the current working directory and **pass its filename**" — directly contradicting the help. | `mycustom.scheme` in CWD: `theme(mycustom)` → 1 226 985 B (= default, ignored); `theme(mycustom.scheme)` → 1 227 019 B (works) | **SILENT** |
| **B11** | `dash serve` honouring the dashboard you just described | `dash.sthlp:200-205`; example `dash.sthlp:484-490` builds with `filter(foreign, type(dropdown))` then runs `dash serve` under the comment *"or launch live server (filter recomputes aggregates)"* | `dash.ado:1488` accepts only `PORT NOBROWSER TIMEOUT` | `dash.ado:1603` hard-codes `"build_options":{"layout":"auto","link":"","filter":"","theme":"default","title":"","subtitle":"","registry":"..."}` — no `filter`, no `link`, no `layout`, no `theme`, and `tabs`/`filter_position` are omitted entirely. **`dash serve` can never render a filter widget**, so the entire "Bokeh Server" column of the comparison table (`dash.sthlp:420-423`) is unreachable from `dash serve`. | `dash.ado:1603` | **SILENT** (feature is documented as the headline benefit of server mode and does not exist on that path) |
| **B12** | `layout()` in **server** mode | implied by `dash.sthlp:249-251` + the server-mode section | `dash.ado:1433` emits it | `dash_render.py:7832` assigns `layout_opt` and it is **never referenced** in the generated source; the emitted grid is always auto (`:10243-10250`). | source | **SILENT** |
| **B13** | `theme()`/`scheme()` in **server** mode | same | `dash.ado:1433` emits `theme` | `dash_render.py:7835` assigns `theme_opt` and it is **never referenced**. Server dashboards always use hard-coded defaults. | source | **SILENT** |
| **B14** | `tabs()` in **server** mode | (undocumented option, see C1) | `dash.ado:1433` emits `tabs` | `build_options["tabs"]` is never read anywhere in `ServerAppBuilder`. | grep | **SILENT** |

---

# TABLE C — IMPLEMENTED BUT NOT DOCUMENTED

| # | Feature | Code | Doc status | Stable & worth documenting? |
|---|---|---|---|---|
| **C1** | `tabs(`*Title*`: n1 n2 / *Title2*`: n3`)` | `dash.ado:1183`; `dash_render.py:6673-6712` (`_parse_tabs_option`), `:6714-6760` (`_build_tabs_widget`), wired at `:7371-7377` | Absent from `dash.sthlp` entirely | **Yes — stable, user-facing.** Must document the hard dependency: `dash_render.py:7372` gates it on `_is_bootstrap_layout(layout_opt)`, so `tabs()` without `layout(bs…)` is a silent no-op (see E). |
| **C2** | `filterposition(top|left)` | `dash.ado:1184`, validated `:1234-1238`; `dash_render.py:7366-7369`, sidebar rendering in `_render_bootstrap_html` | Absent | **Yes — stable.** (Error message misspells the option — see D6.) |
| **C3** | `layout(bs)` and `layout(bs: `*name*`=`*N*` … / … )` | `dash.ado:1227` (`regexm(lower("`layout'"), "^bs")`) and the error text at `:1228` mentions it; `dash_render.py:6308-6318` (`_is_bootstrap_layout`), `:6320-6364` (`_auto_bs_layout`), `:6367-6437` (`_parse_bs_layout`), `:6437+` (`_render_bootstrap_html`) | `dash.sthlp:263-275` documents only `auto`, `N M`, and the (non-functional) `name:row,col` | **Yes — highest-value omission.** It is the only layout that supports tabs, `filterposition(left)`, and per-item 12-column spans. Grammar: `bs`, or `bs: name=N name=N / name=N`, spans clamped to 1–12, unlisted items appended full-width (`:6434-6436`). |
| **C4** | `theme(mono)`, `theme(economist)`, `theme(sj)` | `dash_render.py:4983-4989` | `dash.sthlp:248` lists only `default, clean, dark` — and `dark` does not exist (B7) | **Yes.** |
| **C5** | `theme(`*file*`.scheme)` — the *actual* custom-scheme entry point | `dash_render.py:745-760` | `dash.sthlp:711-713` gives the wrong option (`scheme()`) and the wrong form (base name) | **Yes** — replaces the incorrect instructions. |
| **C6** | `colorvar()`, `colpalette()`, `colordiscrete` | `dash.ado:306-307`; `dash_render.py:1560-1830` (`_apply_colorvar`) | Absent from `dash.sthlp` | **Yes — substantial working feature** (continuous + discrete mapping, value-label-aware legends, colour bar). |
| **C7** | `colorcuts()`, `colornlevels()`, `colormissing()` | `dash.ado:308`; `dash_render.py:1591`, `:1622-1633` | Absent | **Yes**, document with C6. |
| **C8** | `jitter()`, `jseed()`, `msangle()` | `dash_render.py:1177-1200`, `:1478-1490` | **Documented (`dash.sthlp:683-695`) — but under the heading "Unsupported Stata twoway options"** | **Relocate**, don't re-write. Same for `xaxis()/yaxis()` + the `*2()` family at `:701-707` and `scheme()` at `:709-717`. |
| **C9** | `bgcolor()`, `plotbgcolor()` graph options | `dash.ado:241`, `:321`; `dash_render.py:5666-5680` | Mentioned only in passing at `dash.sthlp:716` ("`bgcolor()`, `plotbgcolor()`, etc."); no entry in the Region Styling section (`:590-622`) | **Yes.** |
| **C10** | `legend(on)` / `legend(ring)` keywords | `dash_render.py:6007-6013` (`loc_map`) | `dash.sthlp:649` documents `on`; `ring` is undocumented | `ring` is a `top_right` alias — low value, optional. |
| **C11** | Plot types with no help entry: `dot`, `dropline`, `rcapsym`, `rscatter`, `rconnected`, `tsline`, `tsrline`, `mspline`, `mband`, `scatteri`, `pci`, `pcscatter`, `pcspike`, `pcarrow`, `pcbarrow`, `lpolyci`, `function` | dispatch tables at `dash_render.py:6167-6206` and `:6258-6264`; advertised only in the error string at `dash.ado:551-556` | The help's `{vieweralsosee}` block (`dash.sthlp:16-33`) lists 15 types and omits all of the above | **Yes** — at minimum a supported-plot-type table. (`function` is currently broken — A17.) |
| **C12** | `dash build` (non-server) **always** opens a browser | `dash.ado:1474-1477` — unconditional `shell open` / `start` / `xdg-open` | Undocumented, and inconsistent with the immediate path (`dash.ado:1007-1015`), which opens **only** when `saving()` was omitted | **Yes** — document it, or add a `nobrowser` option to `dash build`. |
| **C13** | `__all__` dropdown sentinel | `dash_render.py:4732-4736`, `:4417`, `:7258` | Undocumented | **No — internal detail.** The user-visible behaviour ("All" removes the filter) is already correct at `dash.sthlp:314`. |
| **C14** | `;` as a multi-filter separator | `dash.ado:1330` (`subinstr ";" → "||"`), `dash_render.py:5398` ("legacy server-mode compatibility") | Undocumented | **No — legacy internal detail.** Multiple `filter()` options are the documented, supported form (`dash.sthlp:325-327`). |
| **C15** | Mata multi-`filter()` pre-extraction | `dash.ado:1163-1172` (`_dash_extract_filters`) | Undocumented | **No — implementation detail**, though it explains why `filter()` is the *only* repeatable option. |
| **C16** | Renderer-only options with **no Stata entry point** (dead features) | `hover()` `dash_render.py:4940`,`:6060-6087` · `xrange()`/`yrange()` `:5799`,`:5809` · `bin()` `:2985`,`:3001` · `color()` `:2109`,`:2204` · `n()`/`range()` for `function` `:5953-5963` · filter sub-option `label()` `:7186` (never populated by `_parse_filter_raw`, `:5390-5413`) | Undocumented; all `rc=198` if typed (verified for `hover`, `xrange`, `bin`, `color`) | **Not documentable until wired into `dash.ado`.** `bin()` is the urgent one (A16). |

---

# TABLE D — DOCUMENTED WITH WRONG VALUES / DEFAULTS / RANGES / GUARANTEES

| # | Help claim | Doc cite | Code reality | Evidence | Rank |
|---|---|---|---|---|---|
| **D1** | `theme()` values are `default, clean, dark` | `dash.sthlp:247-248` | `dash_render.py:4983-4989`: `{"default":"s2color","clean":"s1color","mono":"s1mono","economist":"economist","sj":"sj"}`. `dark` is **not a key**; `mono`/`economist`/`sj` are undocumented. | `theme(dark)` HTML byte-identical to `theme(default)` | **SILENT** |
| **D2** | `degree()` is `0 = Nadaraya–Watson (default), 1 = local linear, 2 = local quadratic` | `dash.sthlp:566-568` | `dash_render.py:2673` and `:2740`: `degree = max(0, min(3, int(options.get("degree","0"))))` — **0–3**, and out-of-range values are silently clamped, non-numeric silently → 0. | `degree(3)` → `rc=0`, renders | **DOC-ONLY** (under-documented) + **SILENT** (clamp) |
| **D3** | Comparison table: *Brush/lasso KPI update — **Standalone: Yes*** | `dash.sthlp:424` | False. No brush→KPI wiring exists outside the generated server app (`dash_render.py:10204-10232`). See B8. | grep: no `selected.on_change`/`js_on_change` in the standalone path | **DOC-ONLY / SILENT** |
| **D4** | Comparison table: *Histogram recompute on filter — **Standalone: No*** | `dash.sthlp:422` | **Help understates the product.** The standalone JS filter callback **does** recompute histogram bin counts (`dash_render.py:4566-4596`) and kdensity curves (`:4598-4630`), driven by `agg_source_registry` (`:5021-5027`, populated `:7700-7709`, tagged `:3026-3030` / `:3083-3087`). | source | **DOC-ONLY** |
| **D4b** | Comparison table: *Fit-line recompute — Standalone: No* | `dash.sthlp:423` | **Correct.** Only `histogram` and `kdensity` carry `_dash_agg_config` (`:3027`, `:3084`); `lfit/qfit/lowess/lpoly/fpfit` do not. | source | — (verified accurate) |
| **D5** | `dash build, server` "**do not block**" / "**does not block or open a browser**" / "(non-blocking)" | `dash.sthlp:82`, `:249-251`, `:492` | **False.** `dash.ado:1461-1467` passes `--mode server`; `dash_render.py:10408` `if args.mode == "server":` then `_sp.Popen(["python","-m","bokeh","serve", …])` (`:10420-10427`), starts a `webbrowser.open` daemon thread because `_dash_do_render` (`dash.ado:142`) never passes `--no-browser` (`:10436-10441`), and **blocks** on `_proc.wait()` (`:10452-10455`). The reassuring `"To launch: bokeh serve …"` message (`dash.ado:1470-1471`) prints only *after* the server has already exited. | Stata log shows `_cmd: ['…python3','-m','bokeh','serve','app_srv.py','--port','5006','--allow-websocket-origin','localhost:5006']` and `_bt: <Thread(Thread-1 (_open_browser), started daemon …)>`; `bokeh serve app_srv.py` run standalone blocks indefinitely | **BLOCKER** (do-file hangs until Ctrl+C) |
| **D6** | `filterposition()` error text names `filter_position()` | n/a | `dash.ado:1236`: `"dash build: filter_position() must be 'top' (default) or 'left' (sidebar)."` — but the option is `FILTERPOSition()` (`dash.ado:1184`). The name printed is not a valid option. | `filterposition(bottom)` → that exact message, `rc=198` | **DOC-ONLY** (message bug) |
| **D7** | Custom scheme: "place a Stata-format `.scheme` file in the current working directory and specify its **base name without the extension**" | `dash.sthlp:711-713` | Wrong on both counts — wrong option (`scheme()` is dead, B2; the live one is `theme()`) and wrong form (a bare base name never searches CWD, `dash_render.py:747-760`). | see B10 evidence | **SILENT** |
| **D8** | `by()` "cannot be combined with `link()`" | `dash.sthlp:517` | False — fully supported. `dash_render.py:6873-6878`, `:6991-6999`, `:7536-7620`, `self._facet_masks` (`:5036`). No guard exists in `dash.ado` either. The stale `Raises: ValueError` docstring at `dash_render.py:6966-6968` should also be removed. | `dash build, link(s1 s2)` with faceted `s1` → `rc=0` | **DOC-ONLY** |
| **D9** | "No error is produced for unknown options … copy-pasted `twoway` commands will still run" | `dash.sthlp:669-673` | False — see A15. | `ttitle()`, `xsize()`, `sort` → `rc=198` | **BLOCKER** |
| **D10** | `play()`/`nodraw` "will produce a warning and the option will be ignored" | `dash.sthlp:157-160` | False — hard `rc=198`. See A13/A14. | observed | **BLOCKER** |
| **D11** | `dcount` = "number of distinct values" | `dash.sthlp:361`; also `PLAN.md:91` ("computed via `codebook`") | `dash.ado:1110-1113` runs `quietly codebook`; **`codebook` returns nothing in `r()`** (verified: `r(unique)` and `r(N_unique)` are both `.`). `$dash_kpi_*_val` and the console message are therefore always missing. The rendered card is saved only because `dash_render.py:7127` recomputes via `col.nunique()` (`:5148`). | `dash kpi dcount(mpg)` → `dash: KPI 'k6' registered (dcount(mpg) = .)`; `return list` after `codebook mpg` is empty | **SILENT** |
| **D12** | `dash clear` "Drops all `$dash_*` global macros" | `dash.sthlp:222-223` | `dash.ado:1050-1051` drops `dash_graph_registry` and `_dash_*` — note the **leading underscore**, a different namespace. The per-graph globals are only dropped by the registry-driven loop (`:1028-1048`), so any orphan survives. | after `dash clear`, `macro list` still shows `dash_spec_orphan` / `dash_json_orphan` | **DOC-ONLY** |
| **D13** | Server comparison table: *Deployment — `bokeh serve app.py`* | `dash.sthlp:425`, `:434-438`; `dash.ado:1470-1471` | Misleading given D5: `dash build, server` has already started a server on 5006 and opened a browser before printing this advice. | see D5 | **DOC-ONLY** |
| **D14** | `port()` range 1024–65535, default 5006 | `dash.sthlp:213-214` | Enforced correctly for `dash serve` (`dash.ado:1493-1501`; observed `port(80)` → `rc=198`). But `dash_render.py:10417` *also* silently clamps, and for `dash build, server` the port is **never user-settable** — it is always argparse's default 5006 (`dash_render.py:10384-10386`), which the help does not say. | `port(80)` → `dash serve: port() must be between 1024 and 65535` | **DOC-ONLY** |
| **D15** | `bwidth()` "default is 0.5; valid range 0.01–1.0" (for `lpoly`/`lpolyci`) | `dash.sthlp:563-565` | Correct for `lpoly` (`dash_render.py:2666-2668`) and `lpolyci` (`:2734-2735`) — but the clamp is silent. `lowess` also accepts `bwidth` (`dash.ado:364`) and parses it at `dash_render.py:2560` with **no clamp and no `try`** → `bwidth(wide)` raises an uncaught `ValueError` that surfaces as a `RuntimeError` from `:7696`. `kdensity` has its own separate bandwidth path. The help documents one behaviour for three different implementations. | source | **DOC-ONLY** + **SILENT** |
| **D16** | `dash_setup` "Verifies that Python 3.8+ is available" | `dash_setup.sthlp:34` | `dash_setup.ado:23-33` only checks `capture python query` returns 0 and prints `sys.version`. **No version comparison is performed.** On Python 3.6 it prints `Python ............. OK (version 3.6.x)`. | source | **DOC-ONLY** |
| **D17** | `dash_setup` "verifies that the installed bokeh version is 3.0 or later, which guarantees Tornado availability" | `dash_setup.sthlp:81-83` | The version gate at `dash_setup.ado:105-122` is **non-fatal** — it prints `(below minimum 3.0)` and continues, then `:154` declares `"dash_setup complete. All dependencies are satisfied."` | source | **DOC-ONLY** |
| **D18** | `dash_setup` checks list (3 steps) | `dash_setup.sthlp:32-39` | Omits the `packaging` package, which `dash_setup.ado:36-60` silently pip-installs first. | source | **DOC-ONLY** (minor) |
| **D19** | `PLAN.md` examples | `PLAN.md:43`, `:91`, `:97` | `dash (histogram mpg, bin(20))` → `rc=198` (A16); "`dcount` … computed via `codebook`" → always missing (D11); "Explicit placement also supported: `layout(s1:1,1 s2:1,2 k1:2,1)`" → silently ignored (B1). | observed | **BLOCKER / SILENT** |

---

# TABLE E — SILENT FAILURES IN `dash_render.py`

## E.0 — The complete WARNED set (ground truth)

`warnings.warn` appears at exactly **6 sites in the live render path** plus **4 sites inside
generated server-app source strings**. `warnings` is always imported lazily at the call site.
There is **no** `print()`/stderr diagnostic anywhere in the option-parsing surface (the only
`print`s are the server banner at `:10316-10318` and the `bokeh serve` launch failure at `:10428`).
**Everything else in this table is UNWARNED.**

| Line | Function | Message |
|---|---|---|
| `dash_render.py:1234` | `GlyphMapper._check_vars` | variable(s) not found in data source; skipping glyph |
| `dash_render.py:1801` | `_apply_colorvar` | color bar skipped — `{exc}` |
| `dash_render.py:5297` | `_apply_graph_filter` | `if_expr` filter skipped — invalid syntax |
| `dash_render.py:5312` | `_apply_graph_filter` | `if_expr` filter skipped — `{qexc}` |
| `dash_render.py:7204` | `_build_filter_widgets` | filter type `slider` requires numeric data |
| `dash_render.py:7220` | `_build_filter_widgets` | filter type `range` requires numeric data |
| `dash_render.py:9942, 9953, 9972, 9983` | emitted server code | server-mode equivalents of the two filter-type guards + two "no finite values" guards |

## E.1 — Highest-impact unwarned sites (the ones that change numbers or delete content)

| # | Site | User typed | Silently happened | Fix |
|---|---|---|---|---|
| **E1** | `dash_render.py:5005-5007` | `theme(dark)`, `theme(clen)`, `scheme(nope)` | `SchemeParser` raises an **already-written, already-formatted** error listing every built-in scheme (`:797-802`) — caught and thrown away; renders `s2color` | `warnings.warn(str(exc))` — one line recovers full diagnostics. **Top priority.** |
| **E2** | `dash_render.py:6223-6229`, `:6266` | an unrecognised plot type reaching `_add_glyph` | `dispatch.get(pt)` → `None` → **the entire plot layer vanishes**, no message, no exception | `warnings.warn` + ideally a Stata-side `display as error` |
| **E3** | `dash_render.py:7121-7131` (+ `dash.ado:1421`) | `dash kpi mean(x) if foreign==1` | The qualifier is **dropped from the spec entirely**; the card shows the unqualified statistic (see B9) | Stata-side: emit `if_expr`/`in_expr` in the KPI JSON; renderer: apply before `_compute_kpi_stat` |
| **E4** | `dash_render.py:6797-6800` | `layout(s1:1,1 s2:1,2)` | Placement discarded, auto grid used | `warnings.warn` now; implement placement later |
| **E5** | `dash_render.py:7372` | `tabs(A: s1 / B: s2)` **without** `layout(bs)` | `tabs()` is a total no-op | Stata-side `display as error` in `_dash_build` is the right fix (fail fast) |
| **E6** | `dash_render.py:7832`, `:7835`, and absent tabs read | `layout()`, `theme()`, `tabs()` with `, server` | Dead options; standalone and server diverge silently | `warnings.warn` per dropped option |
| **E7** | `dash_render.py:1852` | `mlabel(makee)` (typo) | **All** marker labels dropped | shared `_warn_bad_opt()` |
| **E8** | `dash_render.py:1571`, `:1575` | `colorvar(mpgg)` / `colorvar(my-var)` | **Entire colour mapping dropped**, plot renders monochrome | `warnings.warn` |
| **E9** | `dash_render.py:4211`, `:4243` | `function(sin(x` / eval error | Curve dropped; an **empty red line** is still drawn so the legend advertises an expression that isn't plotted. Server mode (`:9503`, bare `except Exception: pass`) draws nothing at all | `warnings.warn`; unify standalone/server |
| **E10** | `dash_render.py:5277-5279` | `in 5/2`, `in abc` | `in` qualifier silently ignored (regex fails, no `else`) — note the sibling `if_expr` path **does** warn at `:5297`/`:5312` | mirror the `if_expr` warn |
| **E11** | `dash_render.py:5457-5459`, `:5448` | `by(foriegn)` (typo) / `by(my$var)` | **No faceting at all** — one combined graph | `warnings.warn` |
| **E12** | `dash_render.py:5408`, `:5412` + `:7231-7232` | `filter(my-var, …)`, `filter(foreign, type(dropdwn))` | Widget never created. Inconsistent: the numeric-type mismatch right next door **does** warn (`:7204`/`:7220`) | `warnings.warn`; better, validate `type()` in `_dash_build` |
| **E13** | `dash_render.py:5401` | `filter(my__var, …)` or a variable literally named `open`/`eval`/`exec` | `_UNSAFE_F` (`:5390-5394`) matches `__` and `\bopen\b` etc. → **whole filter dropped** | tighten the regex to the *spec*, not the varname; warn on rejection |
| **E14** | `dash_render.py:7174-7175` | `filter(pricee, …)`, or a filter var absent from the chosen `fsource` | Widget silently dropped | `warnings.warn` |
| **E15** | `dash_render.py:6428` / `:6698-6700` | `layout(bs: kpi_one=4)` / `tabs(A: s22)` with a name typo | Unknown name dropped from the row/tab; element reappears as a stray full-width row (`:6434-6436`), or the tab vanishes | validate names in `_dash_build` against `$dash_graph_registry` |
| **E16** | `dash_render.py:6855`/`:6983`, `:7512` | `link(s1 s99)` | Unknown name never matches → silently unlinked. **Note:** `dash.ado:1242-1251` *does* validate `link()` names, so this is only reachable via a hand-written spec. | low priority |
| **E17** | `dash_render.py:7273` | `update(brsh)` (typo) | Fails both `("filter","both")` and `("brush","both")` → the KPI becomes completely static | `dash.ado:1094-1097` already validates — good; renderer should still warn |
| **E18** | `dash_render.py:7292-7295` vs `:6289` | `color(0 0 128)` on a KPI | `_sanitize_css_color` (`:4356`) rejects Stata RGB triplets → `#212529`, **but only inside the filter callback**; the initial card uses `html.escape` only. The card **changes colour the first time a filter fires.** | route both through the same translator |
| **E19** | `dash_render.py:5891`, `:5584-5589` | `xlabel(0 5 ten 15)` / `xlabel(low mid high)` | Bad tokens dropped; if all are bad the whole `xlabel()` is ignored (docstring even says "Invalid tokens are silently dropped") | warn per dropped token |
| **E20** | `dash_render.py:6029`, `:6015-6024` | `legend(label(1 First))` (unquoted) / `legend(topleft)` | Override or placement silently dropped | warn |
| **E21** | `dash_render.py:5720-5724`, `:5921-5923` | `yaxis(3)` | Only `"2"` is recognised; the layer silently lands on the **primary** axis | warn or reject |
| **E22** | `dash_render.py:5686`/`:5709` | `plotregion(bcolor(red))` (wrong sub-option) | Regex misses → sub-option vanishes | warn on unrecognised region sub-options |
| **E23** | `dash_render.py:5246` | any plot/hover/colorvar variable absent from the dataset | Column silently omitted from the CDS (docstring: "Missing columns are silently skipped"). `_check_vars` (`:1234`) covers x/y/y2 but **not** `hover`/`colorvar`. | extend `_check_vars` coverage |

## E.2 — Silent clamps of user numeric options (all UNWARNED)

| Site | Option | Clamp |
|---|---|---|
| `dash_render.py:1190` | `jitter(500)` | → 100 |
| `dash_render.py:1517` | `fintensity(250)` | → 1.0 |
| `dash_render.py:1623` | `colornlevels(1)` | → 2 |
| `dash_render.py:2666-2667`, `:2734` | `bwidth(5)` / `bwidth(0)` | → 1.0 / 0.01 |
| `dash_render.py:2673`, `:2740` | `degree(9)` | → 3 (see D2) |
| `dash_render.py:3001-3002` | `bin(99999)` / `bin(0)` | → 1000 / 1 |
| `dash_render.py:6421` | `layout(bs: k1=99)` / `k1=0` | → 12 / 1 |
| `dash_render.py:6793` | `layout(0 0)` | → 1×1 |
| `dash_render.py:9466-9469` (emitted) | `n(99999)` for `function` | → 10000 |
| `dash_render.py:10417` | `--port 80` / `--port 99999` | → 1024 / 65535 |

A single "value clamped to *N*" note at each site is cheap and high-signal.

## E.3 — Silent fallbacks in colour / size / pattern translation

`OptionTranslator.translate_*` raise well-worded `ValueError`s (`:573`, `:599`, `:626`, `:656`, `:677`) —
**every caller swallows them**. The diagnostic text is written and then thrown away.

**Nineteen `except …: pass` blocks** cluster in `_apply_line_opts` / `_apply_marker_opts` /
`_apply_fill_opts` (`dash_render.py:1361-1521`): `lcolor` `:1361`, `lwidth` `:1366`, `lpattern` `:1371`,
`lalpha` `:1377`+`:1379`, `marker` `:1404`, `mcolor` `:1417`, `msymbol` `:1422`, `msize` `:1427`,
`mfcolor` `:1438`, outline `lcolor` `:1448`, outline `lwidth` `:1454`, `malpha` `:1461`+`:1466`,
`lalpha` `:1472`+`:1474`, `msangle` `:1485`, `fcolor` `:1507`, `fintensity` `:1517`/`:1520`.
Note `lalpha(150)`/`malpha(200)` fail a bare range test with **no `else`** — silently ignored.

Marker-label family: `mlabcolor` `:1868`, `mlabsize` `:1875`, `mlabposition` `:1888`/`:1890`,
`mlabgap` `:1898`, `mlabwidth` `:1905` (deliberate no-op, B5).

Palette: `colpalette(viridus)` → `Category10_10` (`:1727`/`:1729`) or `Viridis256` (`:1780-1781`);
`colormissing()` passed **raw** to Bokeh with no Stata→hex translation (`:1591`).

Per-plot-type repeats: `map_scatter` `:1940`, `map_bar` `:2181`/`:2189`/`:2209`/`:2215`/`:2220`,
`map_area` `:2097`, `map_spike` `:2261`, `map_dropline` `:3434`, `map_rcapsym` `:3501`,
`map_scatteri` `:3563`/`:3571`/`:3583`, `map_pcarrow` `:3767`, `map_pcbarrow` `:3839`.

Graph level: `aspectratio` `:5632`, `bgcolor` `:5670`, `plotbgcolor` `:5677`,
`plotregion(color/lcolor/lwidth)` `:5690`/`:5696`/`:5702`, `graphregion(color)` `:5713`,
`xscale/yscale` unknown tokens `:213`, axis `angle()` `:242`,
`xrange`/`yrange` `:5802`/`:5806`/`:5811`/`:5816`, `xline`/`yline` per-value `:5847`/`:5854`,
`hover` var typo `:6087`, `legend(cols/rows)` `:6048`/`:6055`.

Scheme-file parsing (user-supplied `.scheme`): bad `#include` `:843`, malformed line `:849`,
bad colour `:870` → `#000000`, bad `gsize` `:881` → `10pt`, `intensity` clamp/fallback `:889-890`,
`linewidth` `:903-907` → 1.5, `symbol` `:915` → `circle`.

KPI formatting: `fmt(%q)` → raw float (`:5205`), comma grouping dropped (`:5217`),
`_parse_fmt` returns `(0, False)` for `%9.2e`/`%tc` (`:7070-7073`) so the **JS-refreshed value
uses 0 decimals and diverges from the initially rendered value**; unknown `stat` → `"—"`
or blank with the descriptive `ValueError` discarded (`:7118`, `:7130`).

## E.4 — Standalone ↔ server divergences (silent, and each a correctness trap)

| Site | Divergence |
|---|---|
| `dash_render.py:8688` | emitted `_lw_map.get(...)` has **no numeric passthrough** — `lwidth(3)` silently becomes 1.5; standalone honours it |
| `dash_render.py:8733` | emitted marker map is a **12-entry subset** of the standalone `_MARKER_MAP` — many valid Stata symbols silently become `circle` |
| `dash_render.py:8736`, `:8998`, `:9016` | emitted `_sz_map` is a reduced 9-entry map — e.g. `msize(vvsmall)` → 8 |
| `dash_render.py:8561` | emitted `plotregion(lwidth())` tries `float()` only — keyword widths (`thin`) work standalone, dropped in server |
| `dash_render.py:8810-8811` | `bin(abc)` → **20** in server, but an uncaught `ValueError`→`RuntimeError` in standalone (`:3001`) |
| `dash_render.py:8489`, `:8491` | emitted `if`-expression failures use a **bare `except Exception: pass`** — server does **not** warn, unlike `:5297`/`:5312` |
| `dash_render.py:9577` | emitted `_cols_m` for `by(, cols())` is computed and **never used** — server ignores facet column counts |
| `dash_render.py:9527` | emitted `mlabsize(13)` (numeric) unchanged — keywords only |
| `dash_render.py:2560` vs `:2667` | `lowess` `bwidth()` has **no clamp and no `try`** (hard `RuntimeError`), while `lpoly` silently clamps — inconsistent for the same option name (see D15) |
| `dash_render.py:3420-3422`, `:3586-3587` | `map_dropline`/`map_scatteri` raise **uncaught** `ValueError`→`RuntimeError` on bad `jitter()`/`jseed()`/`msize()`/`msymbol()`, while `map_scatter` (`:1183`, `:1197`, `:1427`) silently ignores the identical input |

## E.5 — Deliberately excluded as unreachable by user option values

`:1340` (`_bootstrap_ci` degenerate resample), `:2623` (`polyfit` fallback), `:2815`/`:2825-2826`
(`_fit_fp2` power search) — numeric-algorithm interior, data-driven not option-driven.
`:816`/`:829` (circular-include guard, blank/comment scheme lines).
`:4411`/`:4418` and the other `_FILTER_JS` `continue`s — documented defensive guards over
structures built 1:1 upstream. `:7019`/`:7041`/`:7680`/`:7696` **re-raise** as `RuntimeError` —
loud, not silent.

---

# Recommended fix ordering

1. **Abbreviation table (A3–A10, A12)** — reconcile `dash_parse.mata:177-250` with the `{cmdab:}`
   markup in `dash.sthlp`, or change the help to the abbreviations the code actually implements.
   Ten one-line additions to `_expand_optkey` fix nine of them; `upd` needs `UPDate` in `dash.ado:1070`.
2. **A1 `scheme()` on `dash build`** and **A2 `name(id, replace)`** — both are advertised in syntax
   diagrams and both abort. A2 additionally resurrects a feature whose implementation already exists.
3. **A15 / D9** — either make unknown options fall through (an `*` catch-all in `syntax`) or delete the
   claim from `dash.sthlp:669-673`. As written, the help invites a failure mode it promises cannot happen.
4. **A16 `bin()`**, **A13/A14 `play()`/`nodraw`**, **A17 `function y=`** — three missing entries in
   `_dash_parse_plot_opts` and one `syntax` fix in `_dash_parse_varpart_any`.
5. **D5** — `dash build, server` must not launch/block. Pass `--no-browser` and gate the
   `if args.mode == "server"` launch block on a new `--serve` flag set only by `_dash_serve`.
6. **B9 KPI `[if]`/`[in]`** and **D11 `dcount`** — both produce *silently wrong numbers*, the worst class.
   `dcount` needs `quietly levelsof`/`inspect` instead of `codebook`.
7. **B11 `dash serve` build options** — pass the real `build_options` at `dash.ado:1603` instead of the
   hard-coded stub, or document that `dash serve` is registry-only.
8. **B1/B7/B10/D1/D7** — decide per item: implement `layout(name:r,c)` and `theme(dark)`, or correct
   the help. Custom-scheme instructions (D7) must be rewritten regardless.
9. **E1 + a shared `_warn_bad_opt(key, value, exc)` helper** — one helper wired into the 19 `pass`
   blocks at `dash_render.py:1361-1521` plus `:5005` covers the bulk of the silent surface in one change.
10. **Document C1–C3, C6, C7, C9, C11, C12** — `tabs()`, `filterposition()`, `layout(bs…)`, the
    `colorvar()` family, `bgcolor()`/`plotbgcolor()`, the full plot-type list, and the auto-open-browser
    behaviour of `dash build`. Relocate C8's entries out of the "Unsupported" section.
