# UltraPlan Research: dash -- close the drop-in audit (WP-33..WP-50)

> Generated: 2026-10-20 · Phase 2/6 · Inputs: `DISCOVERY.md` (Q1-Q58, binding), `review/DROPIN-AUDIT-19oct2026.md`.
> Three reports, each read at s3-bugs `090d928` (code unchanged since the audit's `7dced3a`):
> - [C] `research/codebase-mechanics.md` -- tracking, truth cscripts, tiers, gallery inside dash, per-package code map with anchors, dash-only words, suite speed, merge tooling.
> - [S] `research/stata-ground-truth.md` -- measured on this machine's StataNow 19.5 console: corpus, SVG export, zero observations (400 probes), ts operators (121 probes), dash-only words (69 forms), twoway__contour_gen, aspectratio, a(b)c.
> - [B] `research/bokeh-web.md` -- measured on Bokeh 3.8.0 and 3.9.0 in headless Chrome over DevTools: SVG export, verdict machinery, Firefox/WebKit, item-by-item capability check for P6-P10, P1-5, WebGL, SMCL runs, legend keys.
>
> Section files cite these by letter and heading. Probe do-files, logs and SVGs are in the session scratchpad (`r2/`, `r3/`), not the repository.

---

## 1. Scope and register

- **222 live items** in the 17 packages (224 printed; plat:PT-3 withdrawn by Q48, basic:PT-7 by Q50) [C §1.3]. Every item's first id is unique, so GAPS4.md keys rows by lead id; id grammar `(?:(?:plot|basic|stat|plat|syn|sil):)?[A-Z]{2,3}-\d{1,2}`. The audit's 22 "false today" help/README lines have no ids: fold each into its owning item, or give them `HR-1..HR-22` rows under P16 [C §1.3].
- **Tracking model** = WP-31's GAPS3 machinery generalised: `GAPS4_OPEN / GAPS4_WP / GAPS4_SECTION`, readers for Open / Closed / Documented / Partly / Withdrawn forms, per-WP closeout tests parametrised over `GAPS4_CLOSED_WPS`, release-guard allowance [C §1.4].
- **Traps:** audit ids (`AX-4`) match the cert case-id shape `_CASE_ID`, so truth-script case ids must use another shape (suggested `Q<wp><ss>-<k>`) [C §1.1]; the release guard needs an S1-S3 grade per open entry, so the audit's blocker/major/minor/cosmetic needs a mapping [C §1.3]; the existing natscale entry (BUGS.md:4139) overlaps P1 item 10 and P9's last item [C §1.2].
- **Truth cscripts cost cert time:** WP-30 + WP-31 scripts are already 1,023 of 2,127 cert seconds; each new `*`-row script loads ~26,000 lines per session in all three sessions. Create each WP's script in that WP's first section, not all in 33-01; count pins 69/51/69 move per script; `picks.sh`/`blockorder.py` name only WP-31's script and GAPS3.md [C §2.4, §8.2].

## 2. P13 corpus and gallery (WP-33)

- **Corpus:** 198 distinct help-file examples, 305 runnable g.pdf commands ([G-2] + [G-3]), 120 dash graph lines in `examples/` -- about **620** [S §1]. 18 datasets via `sysuse`; 3 via `webuse` (lifeexp2, lbw, nhanes2l). webuse works from batch, but Stata keeps no cache, so the harness keeps its own git-ignored copy [S §1d]. Multi-line `///` commands and `gr_example2` named blocks need a dedicated extractor [S §1a-1b].
- **twoway SVG:** `graph export x.svg` works in console batch and is **byte-identical** across sessions; grid lines are dash segments (the comparator merges them) [S §2]. Default stcolor graph is **7.5 x 4.5 in**; 5.5 x 4 is s2color's [S §2, B §0].
- **dash SVG:** works today with no new dependency: `Bokeh.index.find_one(model).export("svg").ctx.get_serialized_svg(true)` over DevTools on the saved page (dash's Save-as-SVG uses the same call). Legend keys, ColorBar strip and TeX come out as embedded PNGs; text is doubled; clipPath ids are random, so committed SVGs need normalising. A fixed size works for a lone figure (set width/height, clear min/max height and aspect ratio in-page); a by() grid needs dash's own fixed-size support (P1-5 / P10 fix) [B §1].
- **Verdicts:** geometry from the existing stdlib SVG readers (`scripts/svg_truth.py`, `svg_layer.py`, `svg_chrome.py`, `svg_text_runs.py`, `svg_scheme_visual.py`) against a BokehJS view dump (model: `test_default_axes_chrome.py`, `test_mode_parity._figure_profile`); image score = Chrome rasterises both SVGs, SSIM in numpy+scipy (matches scikit-image to 4 dp). **No new dependency** [B §2, C §3.3].
- **Gallery page inside dash:** dash today cannot embed raw SVG/HTML/images (the help promises no user markup), and one `dash build` draws one in-memory dataset; the corpus spans ~21 datasets [C §4.1-4.2]. `.gitignore` ignores `*.html` (`docs/gallery/*.html` needs a `!` rule) [C §3.1]. Q36's path/name scan is new (test_no_secrets checks key shapes and the e-mail only) [C §3.1].
- **Targets:** `make corpus` / `make gallery` beside `make truth`; the ~20-example guard as a block range in `test_wp33_truth.cscript` with a committed expected-verdict fixture [C §3.1].

## 3. Package findings that change the plan

- **P1 (WP-34).** ts operators: twoway allows them; all 121 probes agree between twoway and dash on rc and first line, matching the 18oct fixture -- D41's precondition is met [S §4]. Item 8 confirmed as the missing-end-row cause, with or without an operator (dash 1967q2..2002q2 vs twoway 1970q1..2000q1) [S §4]. Item 9: twoway prints `0`, dash holds 5.551e-17 / 1.11e-16 [S §8]. Item 5: cause reproduced; fix = figure width/height = the xsize/ysize box, clear min/max height and aspect ratio; no 0 px plot and no E-1023 in both versions [B §4.6, S §7].
- **P2 (WP-36).** Python discovery collides with two guards: `test_cscript_hygiene.py:472` forbids `capture python query`, and the standing rule (probe c(python_exec), never execute Python; `python query` can report "initialized" while a later `python:` fails). The whole harness (truth cscripts, cert_svg.do, `make test` via `scripts/stata_python_exec.sh`) reads c(python_exec) too [C §0.4, §5 P2]. WebGL: no per-renderer backend, so a figure with dashed lines must stay on canvas; dashed/dotted WebGL lines break up on the real GPU too; every browser test passes `--disable-gpu`, so none has drawn WebGL [B §4.7].
- **P6-P10 (WP-41..45).** Of 97 items, **0 are not supported** under the maintainer's definition: 70 yes, 27 yes-as-composite. Residuals worth a Differences sentence: mixed SMCL runs (composite labels), dates past the browser's Date range, custom legend key cells losing click-to-hide [B §4.8, §5, §6].
- **P11 (WP-35).** 42 dash-only words (38 shadow synonyms: 25 second-axis forms + 13 others; 3 extensions hover(), table, colpalette(); 1 noted-not-drawn bw()), plus 5 non-word forms and ~20 subcommand words; 11 rows had no twoway rc in any committed fixture -- now measured [C §6, S §5]. `scheme(unknown)`: twoway draws with a note, dash refuses [S §5].
- **P12 (WP-37) zero observations (400 probes).** twoway **draws an empty graph (rc 0)** for 34 of 40 types in every case (plot `if 0`, one empty plot among several, graph-wide `|| if 0`, an `in`/`if` selecting nothing, all-missing y); it refuses only lpoly/lpolyci r(2000) `no observations`, fpfit/fpfitci r(198) `observation numbers out of range` (after a note), mband/mspline r(198) `bands must be between 1 and 200`; by() with every panel empty is r(198) `nothing to graph` for every type; function/scatteri/pci/pcarrowi ignore `if 0`. dash already matches in 389/400; the 11 gaps are contour's r(7102) crash (7 cases) and by()+`if 0` on function/scatteri/pci/pcarrowi [S §3]. The single check fits right after `_dash_qual_gen` (dash.ado:11778 one-line; :13207 build/serve), before `_dash_do_render` [C §0.6].
- **P12 contour.** `twoway__contour_gen` replaces the dataset; 0.2 s on gridded sandstone (every help example), but on scattered points it grows about as n^4 (400 points: 143 s; 1,000 points: twoway's own draw unfinished after 12 min) -- the same cost twoway pays [S §6].

## 4. Browsers (Q32)

- Firefox: WebDriver BiDi over the tornado websocket client the tests already use, against the installed Firefox 157 -- measured working, no geckodriver/selenium [B §3.1].
- WebKit: Safari has no headless mode; Playwright for Python is the only headless WebKit on macOS (dev-only: ~43 MB wheel + ~180 MB WebKit download) [B §3.2-3.3].

## 5. Test-suite speed (WP-50)

- Inputs and untaken levers in [C §7]; levers already in place are listed so WP-50 does not re-propose them.

## 6. Conflicts between discovery and research

| # | Discovery answer | Research finding | Resolution |
|---|---|---|---|
| C1 | Q21-Q22 (D40): one Stata-side zero-observation check, copying twoway per measured case; r(2000) with the plot named | twoway draws an empty graph for 34 of 40 types and refuses only six types and the all-empty by() | **Copy twoway per case.** The single check (after `_dash_qual_gen`, before `_dash_do_render`) implements [S §3]'s table: draw the empty graph where twoway draws; refuse with twoway's rc and words where it refuses (lpoly/lpolyci r(2000) `no observations`; fpfit/fpfitci r(198) after twoway's note; mband/mspline r(198); all-empty by() r(198) `nothing to graph`, including function/scatteri/pci/pcarrowi); fix the contour crash. where dash refuses, twoway's words come first and a second line names the plot's number and type (Q22, kept as index M9); no help note is needed where dash matches. |
| C2 | Q57: twoway's default 5.5 x 4 in shape | the default stcolor graph is 7.5 x 4.5 in (5.5 x 4 is s2color's) | **Each example's own size**: dash rendered at the size twoway draws that example (its scheme's default, or its xsize()/ysize()). |
| C3 | Q26: twoway__contour_gen at registration | as slow as twoway on scattered data (n^4); fast on gridded data | **Grid or interp(none) only**: call `twoway__contour_gen` when the data is a full grid or `interp(none)` is given; scattered data above 1,000 points keeps the seeded subsample and its note. |
| C4 | Q16: one gallery page built with dash itself | dash cannot embed SVG/HTML/images and draws one dataset per build; the corpus needs ~21 datasets | **Add a dash image panel**: a new registered image/SVG item placed by tabs()/layout() like a KPI, and registered graphs keep their own frame so one `dash build` draws several datasets. The gallery is a genuine dash build. (New dash feature in WP-33; help, tests and security rules apply.) |
| C5 | D40 P2: use whichever Python Stata finds | the standing rule forbids `python query` as a probe and the harness reads c(python_exec) everywhere | **No pre-check**: when c(python_exec) is empty, dash and dash_setup skip their refusal and run the normal `python:` path so Stata picks its Python; Stata's own failure is surfaced with dash's advice. The harness (truth-cscript gates, cert_svg.do, `scripts/stata_python_exec.sh`) gets the same rule. No `python query` probe. |
