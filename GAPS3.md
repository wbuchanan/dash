# GAPS3 -- what dash still lacks to be a drop-in `twoway`

*Audit of 10 October 2026 at HEAD `1a78bb9` (`main`, 09oct2026), on branch
`s3-bugs` after a fast-forward to `main`, with every mention of heatmap removed
from the codebase (section 8). Successor to `GAPS.md` (21sep2026) and
`GAPS2.md` (25sep2026). Read with `.ultraplan/handoff/DROPIN-REMAINING.md`,
whose P2/P3 numbering this document keeps.*

## 1. Verdict

dash parses the full `twoway` grammar, draws 40 of the 45 documented plot
types in both the saved page and the served app from one glyph layer, and
honours most of the common options. It is not yet a drop-in replacement. What
remains falls into six kinds:

1. **Five plot types are not drawn**: `contour`, `contourline`, `rpcap`,
   `rpspike` (refused by name) and `sunflower` and `matamatrix()` (fall to the
   generic "unrecognised plot type" message).
2. **About 70 accepted `twoway` options are named in a note and not drawn**
   (the `_dash_pending` lists in dash.ado hold 67 entries; a further ~25
   undeclared names reach the generic note), and a handful are dropped with no
   note at all (section 4, items marked S1).
3. **Values `twoway` accepts are refused** (`range(varname)`, `degree()` above
   3, lowess `bwidth()` above 1, `yaxis(1 2)`, axes 3-9, weight expressions,
   several variables in one `mlabel()` element).
4. **Picture fidelity**: arrowheads, `dot` rows, minor ticks, edge titles,
   textbox placement, legend geometry, `scale()`/`fxsize()`/`fysize()`, the
   marker-symbol remainder, line-pattern formulas, date `#N` ticks.
5. **The offline page does not refit** computed layers after a filter move
   (by decision WP-29 M3; it shows a stale cue instead); the second axis and
   emptied `by()` panels do not follow a move in either mode.
6. **Platform**: only Apple-silicon macOS, StataNow 19.5, Python 3.11-3.13,
   bokeh 3.8-3.9 and headless Chrome have ever been run; Linux, Windows, Intel
   macOS, GUI Stata and a scripted image export are a deferred package.

Nothing here is silently wrong in common use any more: the S1 items below are
edge cases. The user-visible cost of the rest is a note instead of a drawing.

## 2. Repository state (findings about the audit itself)

- **The branch was stale.** `s3-bugs` sat at `357c368` (30sep2026), 196
  commits behind `main`, with zero commits of its own; `main` carried WP-29 and
  WP-30, which closed 43 GAPS2 gaps and partly closed 19 more. The first pass
  of this audit measured the stale tree; every finding was then re-verified on
  `main`'s tree, which `s3-bugs` now equals (`git merge --ff-only main`).
- **The authoritative residual register already exists**:
  `.ultraplan/handoff/DROPIN-REMAINING.md` §3, P2.1-P2.92 and P3.1-P3.12
  (P0 and P1 are all closed). Every P2/P3 item was re-verified against the
  code (section 4); 86 are still open as written, 7 are partly closed or need
  their text narrowed, 2 are closed now (section 6).
- **GAPS2.md** at HEAD: 22 closed in WP-28, 11 in WP-29, 32 in WP-30; 4 partly
  closed in WP-29, 15 partly in WP-30; 38 still open, all of which map onto
  P2/P3 rows below.
- **BUGS.md**: 3 open entries, all S3 (A11 "drew nothing" note kept by decision
  M6; refusal-order wording; `kernel()` on a type without a kernel written to
  the spec without a note).
- **ROADMAP.md WP-30** defers "the platform package (P1.34.6)" (section 4.I).
- The local `.git/info/exclude` hides `.ultraplan/handoff/*.log` and `*.txt`,
  so the working tree looks current when it is not; check
  `git log HEAD..main` before any audit.

## 3. Method

Twelve read-only agents, one per area, each given the register text for its
slice and Stata's own help and ado files (`/Applications/StataNow/ado/base`)
as ground truth, verified every open register item against the current code
with file:line evidence and then walked the twoway surface independently for
gaps no register names. A first pass on the stale tree was discarded except
where it found items the second pass confirmed. No Stata was run for the
audit itself; where a claim about `twoway`'s behaviour needs Stata it says
"unverified". Line numbers are at `1a78bb9` with the heatmap edits applied
(dash.ado 11,039 lines; dash_parse.mata 9,789; dash_render.py 52,280;
dash.sthlp 5,207).

Severity: **S1** silently wrong output; **S2** a documented or `twoway`
capability that does not work, but fails visibly (refused, or named in a
note); **S3** fidelity, hygiene, coverage or documentation drift. **NEW**
marks a gap no register held before this audit.

## 4. Gaps by area

Each row: what is missing, where in the code it is decided, and the task that
closes it (with the test that must pin it). "Register" names the P2/P3 or
GAPS2 row that already tracks it.

### 4.A Command syntax

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| A1 | `dash twoway` with nothing after it is refused r(198) "empty plot specification"; twoway draws an empty graph. | S3 | P2.56 | dash.ado:118-125 prefix strip; dash_parse.mata `_dash_split_segs` | Draw an empty figure (axes only) for the bare prefix; cscript. |
| A2 | Plot-type abbreviations are a superset of twoway's (`lfi qfi ar ba sp low lpo fp kde dr tsl tsrl msp` accepted; twoway refuses them) and the help lists only twoway's eight. | S3 NEW | -- | dash_parse.mata:1688-1730; dash.sthlp:302-333 | Either refuse the extras with twoway's "not a twoway plot type" r(198), or document the superset. Pin with test_parser.cscript. |
| A3 | Option-abbreviation minimums have no live pin: test/fixtures/abbrev_truth.json is marked "PRE-FIX RECORD" and test_abbreviations.py asserts the stale counts (7 mismaps, 2 unresolved). | S3 NEW | -- | test/test_abbreviations.py:41-53, :255 | Regenerate the fixture from StataNow and pin every minimum both ways. |
| A4 | `mla()` binds to dash's `mlabel()` (minimum `ml`) where twoway's `mla` is `mlalign()`; `scatter y x, mla(center)` is refused as a bad variable. | S2 NEW | -- | dash.ado:1170; marker_options.sthlp `{cmdab:mla:lign}` | Declare `MLAlign()` so the longer minimum wins; cscript with both spellings. |
| A5 | Weight expressions `[aw=price+1]` and `[aw=L.x]` refused; twoway takes an expression. | S2 | P2.14 (G17) | dash.ado:5402-5425 | Evaluate the expression into a `__dash` column at registration (the `_dash_tsop_gen` route); pin values against `summarize [aw=]`. |
| A6 | Option varlists with operators: `mlabel(L.make)`, `colorvar(L.mpg)`, `by(L.foreign)` are refused r(198); twoway r(111)/r(101) or draws. | S3 | P2.78 | dash.ado:3471-3479 | Route option varlists through `_dash_tsop_gen` where twoway draws; copy twoway's rc where it refuses. |
| A7 | `hover()` written inside a layer's parentheses and again after the comma keeps only the rightmost list. | S3 | P2.33 | dash.ado:1085, :1571 | Merge the two lists; pin. |
| A8 | Date literals in y-options (`ylabel(2000m1)`) accepted; twoway r(198). | S3 | P2.83 | dash.ado:7546-7563 (x options only) | Extend the refusal loop to y options. |

Confirmed working on this tree (no gap): `(a) (b)`, `a || b`, `(a) || b`,
`a || (b)`, `a ||, opts`, `(a) (b), opts (c)`, trailing `||`, the `twoway`,
`tw`, `graph twoway`, `gr tw` prefixes, multiple y variables, per-plot and
global `if`/`in`, `[aw fw pw iw]`, time-series operators in plot varlists
(`_dash_tsop_gen`, dash.ado:6543-6590), wildcards, compound quotes, macros,
`#delimit`, the `c(macrolen)` guard.

### 4.B Plot types

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| B1 | `rpcap`, `rpspike` refused by name r(198) with advice. | S2 | P2.17 (A5) | dash.ado:4880-4906; dash_parse.mata:1806 | Parse as the 4-variable family twoway_y3xview_parse assigns; draw `map_rcap`/`map_rspike` plus the point marker; both modes; cscript against the .gph serset. |
| B2 | `sunflower` falls to the generic "unrecognised plot type"; absent from the help's Not-drawn list. | S2 | P2.17 (A5) | dash.ado:4904; grep 0 | Short term: refuse by name with advice and list it in the help. Long term: port twoway__sunflower_gen.ado (petals as segments). |
| B3 | `matamatrix()` is read as a varlist and refused r(101)/r(111). | S2 | P2.17 (A5) | grep 0 | Refuse by name now; later read the matrix columns by value into reserved export columns. |
| B4 | `contour`, `contourline` refused by name. | S2 | P2.17 (A5) | dash.ado:4891-4893 | Call `twoway__contour_gen` under preserve at registration, export the polygons as literal records, draw with patches/multi_line, note the layer is static under filters. |
| B5 | `dot` is drawn as a plain scatter: no dot rows; `dotextend()`, `ndots()`, `dsymbol dcolor dfcolor dsize dlcolor dlwidth dlalign` undeclared (generic note), `dstyle()`/`dlstyle()` pending; `base()` on dot written to the spec and never read; `recast()` on dot dropped with no note. | S2 (recast part S1 unverified) | P2.9 (A14) | dash_render.py:18910-18937 `map_dot`; dash.ado:2575 | Draw the dot rows (twoway's dot geometry), declare and draw the d-options, note or honour `recast()`; measure twoway `dot, recast(line)` first. |

### 4.C Type-specific options

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| C1 | pcarrow/pcbarrow/pcarrowi: head `msize() mcolor() mfcolor() mlcolor() mlwidth()` are declared, written to the spec and **silently** not read; heads are fixed `OpenHead(size=10)`; pcbarrow's `NormalHead` has no `fill_color` so its heads fill black; `mangle()`, `barbsize()`, `headlabel` undeclared (generic note); a row missing only its second point is dropped whole. test_phase4_plots.py P4-18/P4-20 pin the black heads. | S1 | P2.8 (A2, B27) | dash_render.py:19683-19861, :19660-19662 | Size and colour the heads from the marker options and the scheme; fill pcbarrow's heads with the line colour; declare mangle/barbsize/headlabel; keep a one-point row as a marker; rewrite P4-18/P4-20. |
| C2 | `rbar ..., msize()` (the bar width twoway then uses with `mwidth`) is written and **silently** unread; `mwidth` is named. | S1 NEW | P2.7 names mwidth only | dash_render.py:18512-18650 `map_rbar` | Read `msize()` with `mwidth` on rbar; or name both. |
| C3 | Options twoway refuses on a type are dropped in silence: `kernel() n() level() bwidth() bands() range() base()` are written to every spec with no applicability table; only fpfit/fpfitci warn. BUGS.md open entry. | S1 | P2.21 (A12) | dash.ado:4448-4449; :2987-3010 rules have no type list | Add a per-type applicability column to `_dash_option_rules`; refuse with twoway's words (decision M5). |
| C4 | Fit options `atobs`, `estcmd()`, `estopts()` (incl. fpfit `estopts(degree())`), `predopts()`, `ciplot()`, `fitplot()`, `nofit` named, not drawn. | S2 | P2.6 (A4) | dash_parse.mata:6261-6276; grep 0 for est* | Honour `nofit`/`ciplot()`/`fitplot()` (style only, S); run `estcmd()/estopts()/predopts()` through Stata at build time and embed (M); `atobs` as a grid rule. |
| C5 | kdensity `area()`, `boundary`; histogram `gap()`; function `droplines()`, `base()`; area `nodropbase`; bar `baroffset()` named, not drawn. | S2 | P2.7 (A4) | dash_parse.mata:6263-6298; dash.sthlp:3075-3077 | Draw each (all have a direct Bokeh form). |
| C6 | `cmissing(n)` on area/rarea and on estimator-generated missing points (lowess, lpoly, lpolyci, fpfit, fpfitci, lfitci, qfitci, mband, mspline); `connect()` other than direct on rarea: named, not drawn. | S2 | P2.42, P2.43 | dash.ado:2712, :2775-2776 | Split the patch/band at missing points as twoway does. |
| C7 | `recast()` histogram to a range type or unknown name named; `recast()` on pci/pcarrowi named; twoway draws them. | S3 | P2.44, P2.79 | dash.ado:2616-2635, :2577-2581 | Extend `_dash_recast_opt`. |
| C8 | `colorvar()` drawn on 4 types only (scatter connected rconnected dot); `jitter()` named on rscatter rcapsym pcscatter pccapsym; `colorlist()`, `coloruseplegend` pending (`_use_plegend` read into a dead variable); `colorstart() colorend() colorformissing() colorfillonly colorkeysrange colorrule() clegend() plegend() pcycle()` undeclared, generic note; dash's own `colormissing()` is not Stata's `colorformissing()` spelling; `colorvar(i.var)` r(111). | S2 | P2.10, P2.16 (A8, B11, X2) | dash.ado:2205, :2218-2225, :1330-1331; dash_render.py:13734 | Route every glyph through `_apply_colorvar`; alias `colorformissing()`; declare and draw the remainder; jitter the four types. |
| C9 | Weighted scatter markers are not sized by `[aw]`. | S2 | P2.16 (G18) | dash_render.py:14944-14973 | Scale marker area by weight as twoway does; pin against twoway's .gph marker sizes. |
| C10 | Values twoway accepts are refused: `range(varname)` and `range(# .)`, `degree()` above 3 (ROT constants for 4-7 exist but are unreachable), `n(1)`, `bwidth(0)`, lowess `bwidth()` above 1 (twoway uses .8), one `mlabel()` element naming several variables, scatteri `2/2`, `level()` bounds applied to every CI type (and `level(5)` drawn on lfitci where twoway bounds 10-99.99), `yaxis(1 2)`, axes 3-9. | S2 | P2.14, P2.15 (A15) | dash.ado:2995-3003, :3150-3158, :3484-3487 | Relax each rule to twoway's bound; draw axes 3-9 with Bokeh extra ranges; cscript each against twoway's rc. |
| C11 | lpoly edges: gaussian weights below 1e-14 counted toward the two-observation rule (3 vs 23 points), round-off cases D1-D5, `pwidth(0)` and `pwidth(+800)` rc differences; lpoly with its own `if` on five rows draws an empty line (twoway unmeasured). | S3 | P2.36, P2.37 | dash_render.py:16960-17180 | Measure, then match or document. |
| C12 | `function` under `by()` evaluated once, twoway once per panel; a malformed y-form echoed as typed. | S3 | P2.31 | dash.ado:8280-8394 | Evaluate per panel. |
| C13 | histogram-only graph draws a legend; twoway draws none. | S3 | P2.51 | dash_render.py:28514 | Exempt histogram-only graphs. |
| C14 | `rscatter y y2 x, mlabel(y)` draws; twoway r(102). | S3 | P2.75 | dash.ado:3712-3760 | Count mlabel variables toward the range check. |
| C15 | Bar marker labels default to 3 o'clock; twoway's bar default is 12. | S3 | P2.91 | dash_render.py:14360 | Per-type default clock. |
| C16 | A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted. | S3 | P2.90 | dash_render.py:17994-18004, :1913-1930 | Tag the recast renderer for the recount. |
| C17 | `mlabprefix()`/`mlabsuffix()` (StataNow) and `lalign()` at plot level are undeclared: generic note, absent from the help's Unsupported list. `headlabel` is accepted-and-named on pcspike/pcscatter/pci/pcarrowi where only pcarrow/pccapsym take it (twoway unverified). | S3 NEW | -- | dash.ado:1137-1250; dash_parse.mata:6277 | Declare and draw prefix/suffix; declare `lalign()`; measure headlabel's type set. |
| C18 | Immediate forms: `scatteri` `2/2` numlist refused where twoway divides. | S3 | P2.14 | dash_parse.mata:1166 | Evaluate the division. |

Drawn and verified on this tree: barwidth/base on bar and rbar, histogram's
nine options, kdensity's kernel/bwidth/n/range, lowess's five, lpoly's four
with Stata's rule-of-thumb bandwidth per kernel and degree, lpolyci's analytic
band with pwidth/var, mband/mspline bands/n, lfit/qfit range/n, the ci bands'
level/stdp/stdf/stdr and fitarea options, `horizontal` on every type twoway
turns, connect/cmissing on line types, x/yvarformat on function, sort and
sort(varlist), the immediates' clock positions and labels.

### 4.D Graph-level options

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| D1 | `xmtick ymtick xmlabel ymlabel tmtick tmlabel` (and the `*2` forms) pending, never read by the renderer. Bokeh has no labelled minor ticks. | S2 | P2.2 (B10, D16-b) | dash.ado:1025-1037; grep 0 in renderer | Draw minor ticks as Bokeh minor ticks; draw minor labels as a second LabelSet along the axis (partial by Bokeh). |
| D2 | `t1title`..`r2title`, `title2`, `subtitle2` pending; the latter two are twoway refusals, not options. | S2 | P2.3 (B19, B28) | dash.ado:1016-1035; dash_render.py:36868-36871 | Draw the eight edge titles as Title/Label objects on each side; refuse `title2()`/`subtitle2()` with twoway's r(198). |
| D3 | Textbox sub-options on titles (`position ring span justification alignment orientation box bexpand margin bmargin tstyle fcolor lcolor lwidth lpattern lstyle bcolor width height linegap placement`) named; `_dash_textbox_place` exists but is wired only to scheme clocks. | S2 | P2.4 (D17-e) | dash_render.py:37117 `_DASH_TEXTBOX_HONOURED`, :37246 | Wire user `position()`/`ring()` through `_dash_textbox_place`; draw box/margin/justification on a Div or Label. |
| D4 | Legend: `holes colfirst textfirst stack symxsize symysize symplacement keygap rowgap colgap textwidth forcesize region() bplacement() span title() subtitle() note() caption() bmargin() nobox color()` named; scheme `cols` dropped when `position()` given; corner clocks centred on a side; `pos(0)` goes top-right; `ring(0)` alone leaves Bokeh's top_right (help promises "inside the plot region"); `legend(label(1))` with no text dropped silently; key size fixed; keys with the same text and style not merged. | S2 | P2.5, P2.50, P2.59 (B17, B26, D16-e) | dash_render.py:37094, :37105, :28394-28425, :28059-28063, :28325-28327, :28514 | Implement the geometry sub-options on Bokeh Legend; a clock table for corners and `pos(0)`; `ring(0)` default clock; blank key for `label(#)`; merge identical keys. |
| D5 | `scale()`, `fxsize()`, `fysize()`, `xoverhangs`, `yoverhangs` pending, never read; `aspectratio()` shapes the figure not the plot region, loses to `xsize/ysize`, and `aspectratio(#, placement())` is refused as "not a positive number". | S2 | P2.13 (B30, B33, D14) | dash.ado:1028-1048, :3047, :3166-3190; dash_render.py:21362-21366, :43721 | Apply `scale()` to every size; honour fxsize/fysize in the grid; compute the plot-region ratio from the frame; accept placement. |
| D6 | Axis sub-options `labgap labstyle tstyle gstyle alternate altgap gmin gmax gextend custom tlstyle tlwidth tlcolor tlpattern glwidth glcolor glpattern labjustification labalignment` named; `##5` read as `#5`; `minmax` over all layers unverified; label forms twoway refuses drawn anyway. | S2 | P2.20, P2.61 (B21) | dash_render.py:36969-36976, :30267 | Draw the stylable ones (gap, colours, widths, patterns, alternate); `##N` minor rule; refuse twoway's refusals. |
| D7 | Axis-scale look: `fill outergap() extend noextend fextend lstyle atanh logit log1m` named; two `yscale(alt)` toggle back in twoway; `gsize axis_title_gap` unread; `zlabel()/zscale()` look words named. | S3 | P2.72 (B23) | dash_render.py:31980, :36922-36945 | Draw extend/fextend/outergap; toggle alt. |
| D8 | `yvarlabel()`/`xvarlabel()` (real twoway options, advanced_options.sthlp) undeclared: generic note, not drawn, not in the help. | S2 NEW | -- | dash.ado:933-975, :1167-1210; test/fixtures/rejected_options.json:2300-2314 | Declare and use as axis title and legend key text. |
| D9 | Secondary axis: the y2/x2 range is built once and never follows a filter move in either mode; the first-used axis is not drawn left/bottom; `horizontal` with `yaxis(2)` titles no x axis. | S2 | P2.23, P2.52 (E6) | dash_render.py:31764, :31723-33579; no y2 in `_DASH_AXIS_FINISH_JS`/`_FILTER_JS` | Recompute extra ranges in the move callback (JS and served); first-used side rule. |
| D10 | `by()`: overall `graphregion()/plotregion()` and `regions` named; `legend(ring(0))` drawn beside the array; overall legend not clickable; `by_alternate_*` axes; panel margin uses f(panels) not `iscale()`; `subtitleformat()`, shrink options, other bystyles named; panel-label box restyling (`subtitle(, fcolor() lcolor() nobox)`) named; a one-panel `by()` with an empty value label drawn without chrome; panels emptied by a filter stay drawn. | S3 | P2.69, P2.77, P2.81, P2.84, P2.89, P2.24 (B16, B31) | dash_render.py:26095-26135 grammar, :38451 | Apply the stage-3 grammar rows; hide emptied panels after a move. |
| D11 | Region: `graphregion(margin())` not exact; graphregion `i*` options, `intensity() iintensity() shadestyle() ishadestyle() marginonly` named; margin forms `L+10`, three- and five-value, `allsides-ms` not parsed; s1color's unfilled plot region filled white. | S3 | P2.53, P2.76, P2.80, P2.92 (B18) | dash_render.py:6504-6710 | Parse every marginstyle form; draw intensity/shade; honour `shadestyle plotregion none`. |
| D12 | Reference lines: an out-of-range `xline()/yline()` is clipped to the frame (Bokeh Span); twoway draws it outside [corrected WP-31 D12: twoway draws it only where its position falls on the canvas, the graph-region margin strip; a farther one is off the canvas or written at a wrapped coordinate]; an asymmetric extended end stays at the last frame on zoom-out. | S3 | P2.54, P2.82 (B22) | dash_render.py:39139 | Draw with a Segment in screen units beyond the frame. |
| D13 | Added text: `tstyle()` and the other textbox sub-options named; `$name` in drawn labels not macro-expanded. | S3 | P2.85, P2.58 (B20) | dash.ado:7829-7889; dash_render.py:37323 | Route `tstyle()` through `SchemeParser.textbox_style`; expand globals at registration. |
| D14 | `tabs()` drops unregistered names silently (layout() now names them); served `layout(s1:1,1 s2:1,1)` overwrites the cell silently; no per-tab `layout()`. | S3 | P2.1 (E15) | dash_render.py:36001, :50709-50712 | Name unknown tab members; refuse same-cell collisions in Mata; per-tab layout. |
| D15 | Date `#N` ticks on %td-%th agree with `_tsnatscale` on 52-98% of ranges; three natscale misses on auto (strict xfails); `xtick(#N)`/`xlabel(minmax)` held after a move; margin a build-time fraction. | S3 | P2.19, P2.65 (B24, B25) | test/test_date_axis_ticks.py:62; test/test_natscale.py:64-78; test/test_by_scales.py:426 | Fit more measured ranges or embed Stata's ticks at build time; re-place after a move. |
| D16 | `legend(po(9) top)` names `top` first; `title("T", prefix suffix)` prints no "option prefix ignored" line; values nested in `legend(region())`/`legend(title())` unchecked. | S3 | P2.59 | dash.ado:2860-2884; dash_parse.mata:8206-8219 | Match twoway's order and message. |

Verified drawn on this tree: titles with size/color/prefix/suffix, axis labels
with Stata's numlist and quoted forms and abbreviations, `axis(#)` routing on
every family, label/tick/scale/line options with Stata's abbreviations
(test_subopt_abbrev.py), `xline()` numlists and styles, `text()/ttext()`,
`by()` with common scales, rows/cols/total/missing/holes/compact/iscale,
region colours and lines, `xsize/ysize`, `name()`, `saving(, replace asis)`,
`nodraw`, `play()` named, the t-axis family folded onto x, `yvarformat()`.

### 4.E Styles, grammars and schemes

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| E1 | Symbols: `arrow`, `arrowf`, `A`, `a`, `\|` refused (noted, scheme symbol drawn); `pipe` drawn as a horizontal dash (twoway's is vertical); `point`/`p` at full 8 px; `V` as a filled inverted triangle; lower-case shorthands `o d s t x v` at full size; `star asterisk hexagon dot` accepted where twoway refuses. | S2 | P2.11 (D5) | dash_render.py:6932-6987, :6921-6930, :7536-7559 | Add an arrow marker (Bokeh `Arrow` glyph or a custom marker), vertical pipe, 1 px point, hollow V, the small factor for shorthands; refuse the non-Stata names. |
| E2 | Line patterns: formula strings (`-.`, `--..`, `_`, `#`) refused in options and schemes (solid drawn); `-_-` drawn as dash_dot; dot geometry `[2,4]` vs Stata `.1 .7`, shortdash `[4,4]` vs `.8 .7`, tight_dot `[1,2]` vs `.1 .4`, vshortdash `[3,3]` vs `.5 .7`; `mlpattern()` pending (never read). | S2 | P2.12 (D4) | dash_render.py:7633-7651, :7253-7281, :7261, :9786-9803; dash.ado:1343 | Parse the formula grammar into dash arrays scaled by line width; copy the style files' ratios; draw `mlpattern()` on marker outlines. |
| E3 | `msangle(anglestyle name)` noted and drawn at 0 degrees although `_DASH_ANGLESTYLES` exists; `mlalign()`, `mwidth`, `mlabstyle()` undeclared (generic note). | S2 | P2.12 | dash_render.py:13465-13475, :6379 | Use `_dash_anglestyle_degrees`; declare the three. |
| E4 | Stylelist edges: glued `=` forms (`red=blue`, `red=`) and `(red)` reach the renderer as one unknown element (twoway r(198) for `(red)`); an unknown `msymbol()` element draws the p# symbol (twoway: circle, unverified). | S3 | P2.60 (D8) | dash_parse.mata:5302-5361, :5393 | Tokenise `=` inside elements; refuse `(red)`. |
| E5 | Colours: a comma colour inside a structured sub-option (`title(, color("1,2,3"))`, region, `xline(, lcolor())`, `ylabel(, labcolor())`) noted and drawn black where twoway refuses r(198); `navy*52` clamp and `color foreground bg` cycle UNCLEAR; `mcolor("red",blue)` unverified. | S3 | P2.71 (D7) | dash_render.py:7412-7421, :7469, :7509-7510, :12603 | Read comma RGB in every context; refuse where twoway does. |
| E6 | Line-width edges: `*#` multiplies before the 0.3 pt floor; 10,000-unit bound; `tlwidth()/glwidth()` named not drawn. | S3 | P2.61 | dash_render.py:7161, :7180, :7245 | Apply the floor after the multiply; draw tick/grid widths. |
| E7 | pstyle(p#) CI band under a scheme intensity above full is clamped to full (`_intensity` default clamp=True); histogram passes clamp=False. | S3 | P2.62 | dash_render.py:10746-10750 vs :10732 | Pass clamp=False on the band reader. |
| E8 | rarea and rbar outlines: twoway strokes them (rarea `#1A476F` 17.28 under s2color); dash draws none unless colour options are given. | S3 | P2.66 | dash_render.py:18494-18513, :18588 | Stroke from the scheme's area line style. |
| E9 | Inline SMCL style runs (`{bf:}` on part of a text) and raised text with no Unicode form drawn in the text's own style; `{hline} {space} {dup} {cmd:} {hi:} {ccl} {center:}` and links drawn as typed. | S3 | P2.70, P2.47 (D3) | dash_render.py:34473-34481, :33876-34123 | Split a text into runs and draw as several Label objects, or document the limit. |
| E10 | User and third-party `*.style` files on the ado-path are not read; 57 Stata style names outside the transcribed table draw default attributes with a note; a scheme cannot redefine a linestyle/areastyle because `linestyle`, `areastyle`, `markerstyle`, `seriesstyle`, `shadestyle` keys are never read (kept silently, by ruling). `c(adoarchive)` unhandled. | S3 | P2.55, P2.74, P2.73 (D10) | dash_render.py:8115 `_STYLE_TABLE`, :8663-8711, :9424-9492 | A general resolver over the 161 style files and the scheme's own class directives. |
| E11 | Sizes are relative to a 4-inch reference and `scale()` is pending (see D5). | S2 | P2.13 (D14) | dash_render.py:7098, :7221, :11450 | With D5. |
| E12 | Case folding: `translate_msymbol` and `translate_lpattern` lower-case names (`CIRCLE`, `Dash` drawn); Stata style names are case-sensitive (measured for anglestyle). `_INTENSITY["max"]` 9999.99 vs the style file's 999999 (no visible effect). | S3 NEW | -- | dash_render.py:7550-7553, :7645, :8952 | Measure twoway; match. |
| E13 | Shipped scheme keys the renderer never references (`color plabel`, `color pline`, `color plineplot`, `linewidth p#solid`, `linewidth parea`); `_SIZE_MAP` kept and serialised into the served app though nothing reads it; `_GSIZE_NUMERIC_PT_PER_UNIT` duplicates `PT_PER_RS`; scheme `%NN` opacity on histogram unverified though the help promises every layer. | S3 NEW | -- | dash_render.py:6992-7007, :48084, :8899, :7015, :17911-18060 | Drop the dead map and constant; verify histogram opacity with a test. |

Verified on this tree (no gap): all 26 Stata schemes have a `dash-<name>.scheme`
and resolve first; user schemes found along the ado-path as `scheme-NAME.scheme`
or `NAME.scheme` with name/size guards; an inherited `c(scheme)`; 92 colour
names, RGB, hex, CMYK, HSV, `*#`, `%#`, `bg/fg`, `none`; 12 line widths with
units; 13 marker sizes with units; 21 text sizes; anglestyle names on
mlabangle and axis `angle()`; clock positions; `fintensity()` blended opaquely;
scheme hollow and small symbols; `lwidth(none)`; `mlabtextstyle()`;
pstyle/lstyle/mstyle/mlstyle; stylelists across y variables with `.`, `=`,
`..`, `...`; textsize keywords on titles through the text ladder.

### 4.F Statistical fidelity

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| F1 | The saved page recomputes only histogram and kdensity after a filter move; lfit, qfit, lfitci, qfitci, fpfit, fpfitci, lowess, lpoly, lpolyci, mband, mspline show a stale cue (decision WP-29 M3). The served app refits everything. | S2 (by decision) | C4 deferred, P2.39 | dash_render.py:1884-1932, :46229; `_dash_agg_config` set only at :18012, :18381 | Decide: port each estimator to JavaScript (XL) or keep the cue. |
| F2 | `function` points-free fallback evaluates 10 math names only; comparisons, `!`, `cond()`, n-ary `min/max`, `round`, `int`, `ln`, `normal`, `normalden`, `c(pi)`, missing codes need Stata (the Stata route covers them at build time). | S3 | P2.68 (A6/C5) | dash_render.py:~11683 `_SAFE_FUNCS`, :20567 | Extend the fallback (research option B). |
| F3 | Stata ground truth missing for weighted qfitci/fpfitci bands, stdf/stdr under `[fw=]`, the six kernels on lpolyci, pattern lengths, on-edge values. | S3 | P3.7 (C12) | test/fixtures/stat_truth.json keys | Extract and pin. |
| F4 | `_LPOLY_ROT_CONSTANTS` holds degree 4-7 rows that are unreachable under `degree=int,0,3`. | S3 | with C10 | dash_render.py:486 | Accept degree 4-7 with C10. |
| F5 | `map_qfitci` docstring still describes a 500-resample bootstrap; the code is analytic (bootstrap only on LinAlgError). The header comment at :364-381 narrates fpfitci's former bootstrap. `_dash_fold_typed`'s comment says line types are always joined in x order (false since WP-29). | S3 NEW | -- | dash_render.py:16560-16563, :16627-16632, :364-381; dash.ado:2229-2234 | Fix the three comments. |

Verified: lfit/qfit WLS; lfitci/qfitci/fpfitci analytic stdp/stdf/stdr with
twoway's weight rules; lowess per lowess.ado; lpoly per lpoly.ado with the
ported rule of thumb (`_LPOLY_ROT_CONSTANTS`) and analytic lpolyci band with
pwidth/var; mband/mspline bands rule; kdensity form and n default; histogram
floor-and-clamp rule (C2, C14 closed); function evaluated by Stata
(`twoway__function_gen`); line join in data order with `sort`/`sort(varlist)`
honoured.

### 4.G Data handling

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| G1 | Extended missing `.a`-`.z` merged into one null in by(, missing) panels, marker labels, filters, tooltips. | S2 | P2.18 (G12) | dash_render.py:2495-2497; dash_parse.mata:2161 | Carry the missing code through export and the label writer. |
| G2 | `set dp comma` never read; `%tC` converted without leap seconds (up to 27 s); `graph set` font faces not read. | S3 | P2.22 (J1, G7) | grep `c(dp)` 0; dash_render.py:534, :658, :33988 | Read `c(dp)`; embed Stata's leap-second table; read `graph set`. |
| G3 | Working columns are generated in the user's data (r(900) possible at `c(maxvar)`); user variables named `x`, `y`, `top`, `count`, `density` shadowed in `hover()`/`mlabel()`; numbers embedded as JSON text (~0.5 GB per million values); strL check loops per observation; a faceted computed-only graph counted in full; `$dash_max_cells` counts every exported row. | S3 | P2.28, P2.39 (G1, G3, G14) | dash.ado:6543-6590, :4262-4273; dash_render.py:1772-1792, :12387-12430, :43028-43034 | Reserve names by prefix in the renderer's derived keys; binary/base64 arrays; count planned rows. |
| G4 | Carried columns (`hover()`, `mlabel`, row id) upcast to dtype=object and handed to Bokeh as Python lists; bokeh 3.8 validates item by item (7.5 of 7.7 s on a million-row line). | S3 | P2.41 | dash_render.py:12420-12424 | Keep numeric carried columns as arrays. |
| G5 | One ~33 KB format-writer model per distinct tick format and per (fmt, kind) tooltip. | S3 | P2.45 | dash_render.py:27945 | Share one writer per page. |
| G6 | Fractional %t values floored on load (twoway unmeasured); join-order edge cases (rarea one bound missing, tied sort keys, connected markers under sort). | S3 | P2.32, P2.30 | dash_render.py:612-620, :16187-16210 | Measure; match. |
| G7 | `%d`/`%tb` axis formats drawn `%9.0g` with a note; `xvarformat(bogus)` noted (twoway: "bogus not found"). | S3 | P2.63 | grep `%tb` 0 | Write business dates; copy twoway's error. |

### 4.H Interactivity, served mode and saved/served parity

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| H1 | A box or lasso selection on bars or histograms drives nothing; concurrent brushes are not intersected on the saved page (served intersects); saved-page JS errors fail silently (no `window.onerror`, the only catches swallow); saved sliders fire on every drag step (served uses `value_throttled`). | S3 | P2.25 (E5, E11, E12) | dash_render.py:35259, :25467-25476, :25624/:25688/:25753, :50063 | Translate a bin/bar selection to rows; intersect; an error banner; `value_throttled` on the saved page. |
| H2 | Dashboard extensions: KPI cards take no weights and lack kurtosis/semean/range; no multi-select filter, "(missing)" option, slider direction or reset button; one link group; brush cannot act as a filter; no print stylesheet; PNG/SVG omit KPI cards, title, filters and tab strip. | S3 | P3.11, P2.48 (E7, E9, E10, E13, J7) | dash.ado:9318, :9350; dash_render.py:35539, :35340-35364 | Product decisions; none is twoway parity. |
| H3 | Served app: `make_document` builds on the event loop (1.6-4.6 s at 100-200k rows; no per-session memory bound, 64-150 MB per session at 200k rows by decision); library `catch_warnings` can swap filters; a brush made while a move waits is cleared; the bundle ships bokeh-mathjax (1.79 MB per session) though dash no longer uses it. | S3 | P2.57, P2.86, P2.48 (F3) | dash_render.py:48895-48950, :4967-4985 | Build off-loop; drop the mathjax component from the served resources. |
| H4 | Environment: `BOKEH_RESOURCES=cdn` blanks the served page silently; `BOKEH_MINIFIED/DEV` change the saved page silently; `/health` reports only ok/timestamp; the browser-launch return code is captured and never read. | S3 | P2.26 (I1, K4) | dash_render.py:48376-48396, :50985-51007; dash.ado:8166-8167 | Reject or report each variable; deeper health; read `_op_rc`. |
| H5 | Served key residuals: unthrottled per-refusal WARNING under a hand-run app; under `bokeh serve` only Gate B; keyless websocket may inflate 262,144 bytes; self-made link limits; link folder outlives SIGKILL; private-file residuals in shared `c(tmpdir)`, the 0.25 s crash window, the five kept preview pages; CSP keeps `script-src 'unsafe-eval'` and `style-src 'unsafe-inline'` (blocked on Bokeh). | S3 | P2.35, P2.38, P2.87 | dash_render.py:5301, :5848, :2883, :2997, :3196, :4622-4623 | Documented design residuals; revisit when Bokeh allows a nonce in the header. |
| H6 | Parity guard limits: after a move only glyphs, labels, arrowheads and KPI cards are compared; the move oracle is the saved renderer re-run with an `if`, not the saved page's JS; no brush, multi-move, bs under 992 px, second-axis range after a slider move, runtime notes, PNG/SVG/CSV bytes, ado-path schemes, launched-process behaviour; test_mode_parity.py runs only in the batch tier. | S3 NEW (partly GAPS2 K) | -- | test/test_mode_parity.py:111-155, :2802, :3247-3298 | Extend the move profile to axes/ranges/legend/chrome; add a slider-on-yaxis(2) entry; add a saved-JS move oracle. |
| H7 | Session hygiene: four unprefixed Mata functions (`_json_escape`, `_is_utf8`, `_expand_plottype_str`, `_first_comma_pos`) dropped by name on repair; `sys.argv` overwritten and never restored; `_dash_xm`, `_dash_render_ns`, `_dash_priv_argv` left in `__main__`. | S3 | P2.27 (X7) | dash_parse.mata:555, :769, :1688, :2498; dash.ado:524-528, :665, :669-681, :10997 | Prefix; save and restore argv; delete the names. |

Verified: every capability documented in dash.sthlp's dashboard sections is
implemented in both the saved page and the served app (two independent walks;
no documented option, limit, default or message found unimplemented, none
implemented but undocumented); dash.pkg lists exactly the 33 shipped files;
`net install` layout works from PLUS/d and PLUS/py; dash_setup prints a remedy
and returns r(198) on every unmet requirement, including PEP 668 and no-pip
Pythons.

### 4.I Installation, packaging and platform

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| I1 | The platform package: Linux, Windows (`/e`, cmd.exe `%`/`!` expansion, `Scripts\python.exe` venvs), Intel macOS and GUI Stata never run; Stata 16-18.5 refused and never certified, Stata 19.0/BE/SE declared and not measured; no scripted image export (`dash export using file.png|pdf|svg`); Python 3.10 and older, Windows 3.11 patch levels without the os.mkdir 0o700 fix; Firefox/Safari CSP runs; bokeh 3.10 unverified (ceiling <3.10). | S2 | ROADMAP WP-30 P1.34.6; P2.88 | dash.ado:85-89 `version 19`; :319; dash_setup.ado:589; Makefile:13; `_DASH_BOKEH_CEIL` dash_render.py:218-220 | Run the certification suite on each platform; parametrise the runners; the export companion needs a headless browser dependency decision. |
| I2 | No README, no LICENSE, dash.pkg has no Author/KW lines, no `net install` instruction in the help, Author section titled "Also see", Jump To lists 19 of 32 sections. | S3 | P2.29, P3.4 (J8) | `ls README* LICENSE*` empty; dash.pkg; dash.sthlp:3-21, :5203-5204 | Write them. |
| I3 | A failed dash_setup leaves already-installed packages in place and does not say what it installed; no hash-pinned installs; the served child is `sys.executable` (Homebrew's base Python under a venv link) working only through Stata's exported `PYTHONPATH`; `Unmet:` lists warnings when a failure also occurred; a `dash_setup_lib.py` or `bokeh.py` in the working directory is found first. | S3 | P2.29, P2.40, P2.88 (H8) | dash_setup.ado:91-92, :827; dash_render.py:51842 | Record installs and offer the uninstall line; pin hashes. |
| I4 | `_dash_dep_versions()` (dash_render.py:189) is computed and returned but printed nowhere except through Stata's call at dash.ado:6139, so a hand-run renderer or app with a sub-floor numpy/pandas is silent; Python below 3.7 dies at the parser. | S3 | P2.67 | dash_render.py:189-210, :51346; dash.ado:6139 | Print the note from the renderer's and the app's `__main__`; accept the SyntaxError. |
| I5 | Version headers disagree: dash_render.py `Version: 1.0.0 25mar2026`; dash.ado:1, :13, :6638 and dash_parse.mata:1 say `v2.0`; test_pkg_metadata.py pins only the `*! Version:` lines. | S3 (dash.ado/mata part NEW) | P3.3 (H4f, J8-h) | dash_render.py:60; dash.ado:1, :13, :6638; test/test_pkg_metadata.py:50-57 | Renumber; extend the pin to every file and header. |
| I7 | The renderer bytecode is still cached under PLUS/py: the guard added for dash_setup_lib does not cover the renderer load, and `ado uninstall` leaves `__pycache__` behind. | S3 | P2.29 (H10) | dash.ado:6118-6133 unguarded vs :6296-6299 | Wrap the renderer load in the same `dont_write_bytecode` guard; pin with test_installed_layout.py. |
| I6 | No secret scan; no CI; no ruff/pyflakes/bandit in the Makefile (the renderer has 51 findings); `.claude/hooks/*` that CLAUDE.md relies on are git-ignored; `*.log` excluded only locally so a fresh clone shows test/run_all_cscripts.log as untracked. | S3 | P3.9 (I9, K5-d) | Makefile:24-92; .gitignore; .git/info/exclude:130 | Add a CI workflow, a lint target, a secrets test; track the hooks or document them. |

### 4.J Documentation and register drift

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| J1 | dash.sthlp:4972-4975 says every supplied option "is named in that command's note, so nothing is dropped in silence"; contradicted by C1, C2, C3. The Unsupported section (:4968-5137) omits every name that reaches the generic note (atobs, ciplot, fitplot, nofit, boundary, headlabel, mwidth, baroffset, nodropbase, clegend, plegend, pcycle, the six colorvar names, gap(), droplines(), mangle(), barbsize(), ndots(), dotextend(), the d-options, estcmd/estopts/predopts, mlabprefix/mlabsuffix, mlalign, mlabstyle, lalign, yvarlabel/xvarlabel) because test_help_conformance.py reads only the pending blocks. | S3 | P3.2 (A4-r, B14-g) | dash.sthlp; test/test_help_conformance.py:353-360 | Generate the list from the pending blocks plus `_dash_rep_und_tab` plus the catch-all probes; pin both ways. |
| J2 | Help inconsistencies: Syntax line 88 shows filter `type()` as required; the %tw-%ty period-slider sentence sits in the dropdown paragraph (:1731-1734); `legend(ring(0))` "inside the plot region" (:3545) vs Bokeh's top_right; `msangle` documented as degrees only; dash.sthlp:572 "Four plot types are not drawn" omits sunflower/matamatrix; `dot` listed among types drawn as twoway describes (:236-260); "logs each refusal once a minute per limit, so a flood cannot flood the log" (:2262-2263): the per-minute rate constants exist (dash_render.py:48132-48135) but no once-a-minute gate on the refusal log line was found (unverified); no iframe sentence; no overlay/`link()` qualifier example; no %tC/log-precedence paragraph. | S3 | P3.4, P3.2 | dash.sthlp | Fix each sentence with its test. |
| J3 | Examples: 10 of 40 plot types unused (bar, scatteri, pci, pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline, fpfit); no example uses `dash serve`, weights or `csv`; feature_tour.do's header names serve/pci it does not contain and says "thirty-eight plot types"; test_examples_run.cscript:13-16 claims the examples exercise every plot type; no coverage test. | S3 | P3.5 (J10) | examples/*.do; test/test_examples_run.cscript:13-16 | Add a plot-types tour and a serve example; a coverage test. |
| J4 | Stale tracking text: GAPS.md:42-76 lists 8 closed gaps as current; ROADMAP.md:4194 "19 remain open, all S3" vs 3; 62 closed BUGS.md entries open with "Resolution: Not fixed"; DROPIN P3.10 and GAPS2 K10 give the renderer as 32k/27.7k lines (52,280 now); TWOWAY_COVERAGE_AUDIT.md:169 lists horizontal/vertical/pstyle/lstyle/mstyle/mlstyle/recast/text/mlabvposition/mlabtextstyle/cmissing/connect as inert (all drawn now) and :95 still describes lpolyci as a bootstrap in its body; GAPS2 anchors A8, B27, A2 point at old line numbers; test/test_geometry_visual.md:6, :20; stale "all 20" built-ins comment test/test_scheme_fidelity.py:996; docstrings describing removed xfails in test_scheme_consumption.py:1108-1113, test_scheme_visual_truth.py:66-74, test_mode_parity.py:2341, test_filters.py:1612-1622; test_glyphs.py:1352 "Missing unit tests" header over tests that exist; dangling references to `.ultraplan/BASELINE.md` (test_varlist_expansion.py:240), `.ultraplan/CHANGELOG.md` (REMAINING.md, BUGS.md:245), `.ultraplan/phases/PHASE-12`, `examples/plot_types_tour.do`, `scripts/extract_format_locale_truth.do` (GAPS2.md). | S3 | P3.3 (K11) | as cited | One reconciliation pass; extend test_tracking_documents.py to the counts. |
| J5 | Served-app text: emitted header "Launch with: bokeh serve", ServerAppBuilder docstrings (:46428, :46440), dead `title_safe` (:47868), `_SIZE_MAP` emitted into the app (:48084). | S3 | P3.3 (F9) | dash_render.py | Fix. |
| J6 | REMAINING.md and phases/ (31 phases) are superseded by ROADMAP.md and DROPIN-REMAINING.md but still in the tree with 68 PARTIAL markers and unchecked definitions of done; ROADMAP's WP-01..WP-11 headings lack the "DONE" suffix the tracking test reads although each carries a DONE blockquote. | S3 | -- NEW | REMAINING.md:353-365; phases/; ROADMAP.md:88-1106 | Mark the two documents historical (or delete them) and add the suffixes. |

### 4.K Tests and engineering

| ID | Gap | Sev | Register | Evidence | Task |
|---|---|---|---|---|---|
| K1 | Tests that pin the non-twoway behaviour a fix must replace: test_phase4_plots.py P4-18/P4-20 (black pcbarrow heads), test_glyphs.py TestMapDot (dot = scatter), test_pipeline_integration.py EC-03/04/05 ("drew nothing" notes, by decision), test_parser.cscript:728-737 (scatteri `2/2` refused), test_server_build_options.py:152 (Python-side layout fallback). | S3 | -- NEW | as cited | Flip with the fix, never delete. |
| K2 | Stata end-to-end gaps: served layer-output assertions, computed layers on %t variables served, the serve start line in the log, a served build from an installed tree, per-type `by()` parity as a cscript, an `inspect.getsource` fallback. | S3 | P3.6 | test/ | Add. |
| K3 | Truth fixtures: 16 fixtures with no committed generator; 9 carry absolute paths; no `make truth`; no metadata guard; visual truth covers 4 of 26 schemes with no histogram render. | S3 | P3.7 (K3) | scripts/, test/fixtures/ | Add generators and a target. |
| K4 | Harness: the server fixture leaks a process when `__enter__` fails (test_server_serves.py:123-142); no AST count of the generated app's dispatch; scheme-key enumeration hand-written; no CSS-guard served arm; tracking-document counts unchecked; strict xfails test_natscale.py:76 and test_by_scales.py:426 (known divergences). | S3 | P3.8 | as cited | Fix the leak; add the guards. |
| K5 | Code structure: dash_render.py is one 52,280-line module, ~3,343 lines of the served app emitted as string literals, `_gopts_of` defined four times, facet orchestration duplicated, no shared case table between the JS and Python statistics. | S3 | P3.10 (K10) | dash_render.py:44397, :44692, :46014, :50627 | A split into modules shipped under PLUS/py (packaging change) or a generated single file. |
| K6 | Accessibility (one `aria-live` region, no alt text) and English-only interface. | S3 | P3.12 | dash_render.py:1906 | Scope decision. |

## 5. Partially finished work

Code that exists but is not wired through, in the order a developer would hit it:

- **Pending-option lists**, dash.ado:1010-1050 (graph) and :1283-1370 (plot): 67
  entries written to the spec and never read by the renderer: `b1title b2title
  l1title l2title r1title r2title t1title t2title title2 subtitle2 fxsize
  fysize scale xmlabel xmtick ymlabel ymtick tmlabel tmtick xoverhangs
  yoverhangs play filter link` (graph) and `at blabel ciopts cmissing colorlist
  coloruseplegend connect fitopts lineopts mlabwidth mlpattern dstyle dlstyle
  bmlinestyle acolor alcolor alwidth alpattern sort` (plot; the last five
  drawn on some types). Each is named by the note and pinned by
  test_unsupported_report_is_true.py, so none is a silent drop.
- **Undeclared names that reach the generic note** (`_dash_rep_und_tab`,
  dash_parse.mata:6256-6320, plus catch-all): atobs, ciplot, fitplot, fit/nofit,
  boundary, headlabel, mwidth, baroffset, dropbase/nodropbase, colorend,
  colorstart, colorformissing, colorrule, colorfillonly, colorkeysrange,
  colorkeysreverse, colorotherlabel, colorallowmultiple, clegend, plegend,
  pcycle, smoothplot, estcmd, estopts, predopts, area(), gap(), droplines(),
  mangle(), barbsize(), ndots(), dotextend(), the d-options, mlabprefix(),
  mlabsuffix(), mlalign(), mlabstyle(), lalign(), yvarlabel(), xvarlabel().
- **Helpers present but not wired**: `_dash_textbox_place` (dash_render.py:37246,
  scheme clocks only); `_dash_anglestyle_degrees` (:6386, not used by msangle);
  `_LPOLY_ROT_CONSTANTS` degree 4-7 rows (:486); `_bootstrap_ci` (:13081, only a
  LinAlgError fallback); `_use_plegend` (:13734, dead variable);
  `_DASH_BY_GRAMMAR` stage-3 rows (:26127-26134, parsed, never applied);
  `_DASH_TITLE_SUBOPT_TABLE` and `_DASH_AXTITLE` (:36947-36960, read for
  refusals only); `_dash_at_opts` parses tstyle/width/height to list them
  (dash.ado:7829-7889); `_dash_agg_config` set by two layer types only
  (:18012, :18381); `numeric_formats` threaded to the mapper and consumed only
  for mlabel (:1139-1193, :12226, :14234); `_SIZE_MAP` (:6992-7007) read by
  nothing yet emitted into the app (:48084); `_GSIZE_NUMERIC_PT_PER_UNIT`
  (:8899) beside `PT_PER_RS` (:7015).
- **Options declared and written but unread on some types**: `msize mcolor
  mfcolor mlcolor mlwidth` on pcarrow/pcbarrow heads; `msize` and `barwidth`
  logic on rbar (`msize` unread); `base()` on dot and function.
- **Strict xfails**: test/test_natscale.py:76 (three natscale ranges),
  test/test_by_scales.py:426 (`style(rescale) noyrescale` x count).
- **Deferred by decision**: the saved-page refit (WP-29 M3); the "drew nothing"
  note where twoway is silent (WP-30 M6, BUGS.md:2559); the 80 MB per-session
  bound removed 09oct2026; `bin()` ≤ 1000 and `n()` ≤ 10,000 as resource
  limits; unread scheme class directives kept silently (ruling in
  test_unread_scheme_directives.py).
- **The platform package** (section 4.I, I1).
- **This audit's own uncommitted change**: the heatmap removal (section 8),
  17 files, on the working tree of `s3-bugs`.

## 6. Register corrections (text that no longer matches the code)

- **Closed now, mark closed**: P3.1 (`scripts/regen_option_surface.py` is
  retired by a hard `sys.exit`, :17); GAPS2 C14 (histogram edge rule,
  test_histogram_edge_rule.py); GAPS2 G4 (ts operators, `_dash_tsop_gen`).
- **Half closed, keep open**: GAPS2 H10 / P2.29's `.pyc` leg: the
  dash_setup_lib load is guarded (`sys.dont_write_bytecode` at
  dash.ado:6296-6299, dash_setup.ado:1080-1083; `PYTHONDONTWRITEBYTECODE=1`
  in dash_setup_lib.py:43) but the renderer load at dash.ado:6118-6133
  (`spec_from_file_location` + `exec_module`) is not, so the 1.2 MB
  `dash_render` bytecode is still written under PLUS/py (see I7).
- **Narrow the text**: P2.1 (unknown `layout()` names are refused now, dash_parse.mata:1650-1668;
  only the served same-cell collision and `tabs()` stay silent); P2.29 (dash.pkg
  does state "Requires: Stata 19 or later" and a version; the `.pyc` leg is
  closed; README/LICENSE/Author/KW/rollback remain); P2.48 (the saved page ships
  no mathjax, three tests assert it; the served bundle still does); P2.25 (a
  brushed histogram is drawn at full intensity, not dimmed: dash.sthlp:4418;
  "drives nothing" stands); P2.12 (`lwidth(none)` and `mlabtextstyle` closed);
  P2.14 (`msize(1e400)` and per-series `mlabel(make rep78)` closed; one element
  naming several variables remains); P3.9 (dev dependencies now declared in
  test/requirements-*.txt; CI, lint, bandit, secrets remain).
- **Residuals no register names** (from two sweeps of BUGS.md's closed
  entries): the registry globals a do-file can set by hand (BUGS.md:524,
  documented design); no test runs an interpreter or bokeh below the floor
  (:2640); `csv` embeds every row (:2786, documented); no build-time note for
  frozen fits on the saved page (:2828, DISCOVERY Q22); the manual GUI Break
  check (:2804, implicit in the platform package); on the one-line route a
  `hover()`-only variable is not exported, so its value labels cannot show
  (G16's residual); a layer that drew nothing has no legend key, so `order()`
  naming its number draws nothing where twoway draws the key (B5's residual);
  twoway's common `by()` scale includes fit lines, outer-axes-only display
  (B16) and `yrescale`/two `style()` are accepted where twoway refuses them
  (P0.2's residual); no y title when layers differ, and the y1/y2 range titles
  (P0.3/P0.4's residual); the second axis's default title (P0.5's residual);
  hsv, CMYK and `colour*#` values inside a scheme file (D1's residual;
  `_colour_cmyk`/`_colour_hsv` exist at dash_render.py:7354/:7372 for options,
  the scheme path is unverified). Each needs a P2 row.
- **GAPS2 rows whose "new" status should point here**: A2, A5, A8, A11, A12,
  A14, A15, B10, B19, B24, B28, B30, B33, C14 (closed), D4, D14, E5, E6, E7,
  E9, E11, E12, E13, E15, G7, G12, G17, G18, H8, H10 (closed), I1, I9, J1, J10,
  K4, K10, K11, X7.

## 7. Decisions still open

1. **Saved-page refit** (F1): port the estimators to JavaScript, or keep the
   stale cue. Everything else about offline filtering is done.
2. **Options twoway refuses on a type** (C3): refuse like twoway (decision M5
   says yes for new code) -- the sweep over the existing rules table is the
   remaining work.
3. **Plot-type abbreviation superset** (A2): refuse or document.
4. **Unbinned `colorvar()`**: dash maps continuously, twoway bins at the
   z-axis ticks (documented; DISCOVERY Q5).
5. **Dashboard extensions** (H2) and accessibility/localisation (K6): scope.
6. **The platform package** (I1): which platforms before 0.1.0 ships.

## 8. Heatmap removed from scope

`heatmap` is no longer a name dash knows. Before this audit it was one of
five twoway plot types refused by name with advice; it now falls to the same
generic "unrecognised plot type" message as any other word, and nothing in the
repository plans, documents, tests or mentions it. Changed (17 files, 74
insertions, 91 deletions): dash.ado (the advice branch and comment),
dash_parse.mata (`_dash_undrawn_plottype` now four names), dash.sthlp
("Four twoway plot types are not drawn", and the Differences count),
test/test_parser.cscript (P1A-59 and the Mata helper asserts),
test/test_help_claims_1.py and .cscript, test/test_help_plot_types.py,
GAPS.md, GAPS2.md (A5 retitled "Five twoway plot types"), ROADMAP.md,
CHANGELOG.md, BUGS.md, TWOWAY_COVERAGE_AUDIT.md,
.ultraplan/handoff/DROPIN-REMAINING.md (P2.17 bullet dropped),
.ultraplan/wp30/manifest.json, .ultraplan/wp30/section-03-stata-19-floor.md,
.ultraplan/wp30/research/p1-35.md. `git grep -i heatmap` is empty. Verified:
test_parser.cscript (P1A-59 PASS, all parser tests passed) and
test_help_claims_1.cscript (HC1-19 PASS, all checks passed) under the console
binary; test_help_plot_types.py, test_help_claims_1.py,
test_tracking_documents.py, test_packaging.py, test_help_conformance.py: 266
passed. Untracked, git-excluded certification logs under `.ultraplan/handoff/`
still contain the word from earlier runs; they are regenerated by `make cert`.

## 9. Tracking

One line per WP-31 entry (.ultraplan/sections/index.md, A4), rewritten in place by the entry's closing commit; test/test_tracking_documents.py::TestWp31Tracking reads exactly these forms:
`Open (WP-31 section NN).`, `Closed in WP-31, BUGS.md "<title>", commit <sha>.`, or
`Partly closed in WP-31 (section NN, commit <sha>): <what is closed>; open: <what remains> (BUGS.md "<residual title>").`
A closing commit writes `commit pending`; the merger's step k.3b replaces it with the landed sha on s3-bugs (DECISIONS A11).

- **A1 Tracked:** Closed in WP-31, BUGS.md "dash twoway with nothing after it is refused r(198) where twoway draws an empty graph", commit 4b1be95.
- **A2 Tracked:** Closed in WP-31, BUGS.md "Plot-type abbreviations are a superset of twoway's eight and the help lists only twoway's", commit 9319ed5.
- **A3 Tracked:** Closed in WP-31, BUGS.md "Option-abbreviation minimums have no live pin and test/fixtures/abbrev_truth.json is a pre-fix record whose stale counts test_abbreviations.py asserts", commit c956f42.
- **A3b Tracked:** Closed in WP-31, BUGS.md "The *2title options and name() take spellings shorter than twoway's minimum (b, l, r, t and nam)", commit d840eda.
- **A3c Tracked:** Closed in WP-31, BUGS.md "aspectratio() takes asp, shorter than twoway's minimum", commit 2c66ba1.
- **A3d Tracked:** Closed in WP-31, BUGS.md "jitter() takes jit, shorter than twoway's minimum", commit 9665bca.
- **A4 Tracked:** Closed in WP-31, BUGS.md "mla() binds to mlabel() where twoway's mla is mlalign(), so mla(center) is refused as a bad variable", commit 3380e3d.
- **A5 Tracked:** Closed in WP-31, BUGS.md "Weight expressions such as [aw=price+1] and [aw=L.x] are refused where twoway takes an expression", commit 59f0f24.
- **A5b Tracked:** Closed in WP-31, BUGS.md "A weight expression that is zero on every row registers without the note twoway prints that its fit could not be computed", commit 4dc41d1.
- **A6 Tracked:** Closed in WP-31, BUGS.md "Option varlists with time-series operators (mlabel(L.make), colorvar(L.mpg), by(L.foreign)) are refused r(198) where twoway draws or refuses with another code", commit 79c9f79.
- **A7 Tracked:** Closed in WP-31, BUGS.md "hover() written inside a layer's parentheses and again after the comma keeps only the rightmost list", commit ec00ad8.
- **A8 Tracked:** Closed in WP-31, BUGS.md "Date literals in y options such as ylabel(2000m1) are accepted where twoway refuses r(198)", commit e07f97e.
- **B1 Tracked:** Closed in WP-31, BUGS.md "rpcap and rpspike are refused by name", commit 6aea1e5.
- **B2 Tracked:** Closed in WP-31, BUGS.md "sunflower falls to the generic unrecognised-plot-type message and is absent from the help's Not-drawn list", commit eae52c8.
- **B3 Tracked:** Closed in WP-31, BUGS.md "matamatrix() is read as a varlist and refused r(101) or r(111)", commit ff82353.
- **B4a Tracked:** Closed in WP-31, BUGS.md "contour and contourline are refused by name (the interpolation, grid rule, cap and truth extractor)", commit 8e78c4d.
- **B4b Tracked:** Closed in WP-31, BUGS.md "contour and contourline are refused by name (the type registration, options, colour rules, colour key and both modes)", commit b89f2a4.
- **B4c Tracked:** Closed in WP-31, BUGS.md "contour and contourline are refused by name (the JavaScript twin)", commit 4456ce9.
- **B4d Tracked:** Closed in WP-31, BUGS.md "After a filter move the served contour colour bar keeps the build's cuts while the bands are recomputed", commit 62890cf.
- **B5a Tracked:** Closed in WP-31, BUGS.md "base() on dot is written to the spec and never read, and recast() on dot is dropped with no note (the base and recast parts)", commit 9f74f15.
- **B5b Tracked:** Closed in WP-31, BUGS.md "dot is drawn as a plain scatter with no dot rows, and dotextend(), ndots() and the d-options are undeclared or pending (the dot rows and d-options)", commit 5e0a387.
- **B5c Tracked:** Closed in WP-31, BUGS.md "dot rows on the saved page keep the build's axis span after a filter move", commit c9e3a97.
- **C1 Tracked:** Closed in WP-31, BUGS.md "pcarrow, pcbarrow and pcarrowi heads ignore msize(), mcolor(), mfcolor(), mlcolor() and mlwidth() in silence, pcbarrow heads fill black, mangle(), barbsize() and headlabel are undeclared, and a row missing its second point is dropped", commit c0c5139.
- **C2 Tracked:** Closed in WP-31, BUGS.md "rbar msize() is written and silently unread where twoway uses it as the bar width with mwidth", commit 7fe438e.
- **C3 Tracked:** Closed in WP-31, BUGS.md "Options twoway refuses on a type (kernel() n() level() bwidth() bands() range() base()) are written to every spec and dropped in silence", commit 8cd5310.
- **C4 Tracked:** Closed in WP-31, BUGS.md "Fit options atobs, estcmd(), estopts(), predopts(), ciplot(), fitplot() and nofit are named and not drawn", commit 660be06.
- **C4b Tracked:** Closed in WP-31, BUGS.md "fitplot() and ciplot() lines and bands are drawn in the layer's own colour with twoway's colours for those views unmeasured", commit 368e38a.
- **C5 Tracked:** Closed in WP-31, BUGS.md "kdensity area() and boundary, histogram gap(), function droplines() and base(), area nodropbase and bar baroffset() are named and not drawn", commit c44d542.
- **C6 Tracked:** Closed in WP-31, BUGS.md "cmissing(n) on area, rarea and estimator-generated missing points and connect() other than direct on rarea are named and not drawn", commit b2af9fc.
- **C6b Tracked:** Closed in WP-31, BUGS.md "mband and mspline over data with missing y draw fewer vertices than twoway", commit 6dd0c80.
- **C7 Tracked:** Closed in WP-31, BUGS.md "recast() of a histogram to a range type or an unknown name and recast() on pci and pcarrowi are named where twoway draws them", commit 44761fa.
- **C8a Tracked:** Closed in WP-31, BUGS.md "colorvar() is drawn on four plot types only and jitter() is named on rscatter, rcapsym, pcscatter and pccapsym (the coverage and jitter parts)", commit 46698dd.
- **C8b Tracked:** Closed in WP-31, BUGS.md "colorlist() and coloruseplegend are pending, colorstart(), colorend(), colorformissing(), colorfillonly, colorkeysrange, colorrule(), clegend(), plegend() and pcycle() are undeclared, and dash's colormissing() is not Stata's colorformissing() spelling (the option remainder)", commit 17d85ec.
- **C8c Tracked:** Closed in WP-31, BUGS.md "A user-supplied scheme's colorvar() default colour rule falls back to s2color's", commit 9e80c0d.
- **C8d Tracked:** Closed in WP-31, BUGS.md "pcycle() refuses a fraction where twoway draws it on a graph of few series", commit 4f9c3e4.
- **C8e Tracked:** Closed in WP-31, BUGS.md "colorkeysreverse on a colorvar() colour bar is named, not drawn", commit 59fcd19.
- **C9 Tracked:** Closed in WP-31, BUGS.md "Weighted scatter markers are not sized by [aw]", commit 5895120.
- **C10a Tracked:** Closed in WP-31, BUGS.md "range(varname), range(# .), bwidth(0), lowess bwidth() above 1, n(1) and per-type level() bounds are refused where twoway accepts them (the bounds that are a rules-table edit)", commit c7c1b2b.
- **C10b Tracked:** Closed in WP-31, BUGS.md "degree() above 3, several variables in one mlabel() element, scatteri 2/2 and yaxis(1 2) are refused where twoway accepts them (the values needing new parsing)", commit a8b39ef.
- **C10c Tracked:** Closed in WP-31, BUGS.md "Axes 3 to 9 are refused where twoway draws them (the axes part)", commit 85c8cef.
- **C10d Tracked:** Closed in WP-31, BUGS.md "kdensity range() naming a string or all-missing variable draws over the data's span where twoway draws an empty curve", commit 844e1cf.
- **C10e Tracked:** Closed in WP-31, BUGS.md "Axes 3 to 9 on a date variable are labelled in Stata numbers, and t-options with axis(3) to axis(9) are left as typed", commit 78df376.
- **C11 Tracked:** Closed in WP-31, BUGS.md "lpoly edge cases: tiny gaussian weights counted toward the two-observation rule, round-off cases, pwidth(0) and pwidth(+800) rc differences, and an empty line under a five-row if", commit 1108a12.
- **C11b Tracked:** Closed in WP-31, BUGS.md "lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app", commit 3df7686.
- **C12 Tracked:** Closed in WP-31, BUGS.md "function under by() is evaluated once where twoway evaluates once per panel, and a malformed y form is echoed as typed", commit 10be1b6.
- **C13 Tracked:** Closed in WP-31, BUGS.md "A histogram-only graph draws a legend where twoway draws none", commit 26b5060.
- **C14 Tracked:** Closed in WP-31, BUGS.md "rscatter y y2 x, mlabel(y) draws where twoway refuses r(102)", commit 52b3d18.
- **C15 Tracked:** Closed in WP-31, BUGS.md "Bar marker labels default to 3 o'clock where twoway's bar default is 12", commit d5556ea.
- **C16 Tracked:** Closed in WP-31, BUGS.md "A recast kdensity or histogram is marked stale after a move where the un-recast one is recounted", commit 3c33dd5.
- **C17 Tracked:** Closed in WP-31, BUGS.md "mlabprefix(), mlabsuffix() and plot-level lalign() are undeclared and headlabel is accepted on types twoway may not take it on", commit 7f73bbe.
- **C17b Tracked:** Closed in WP-31, BUGS.md "lal() is read as dash's lalpha() where twoway reads it as lalign()", commit 90ca733.
- **C18 Tracked:** Closed in WP-31, BUGS.md "scatteri refuses a 2/2 numlist element where twoway divides", commit 034fc0b.
- **C18b Tracked:** Closed in WP-31, BUGS.md "An immediate coordinate written as a hexadecimal literal such as 1.0X+3ff is refused where twoway takes it", commit 59b4ee2.
- **D1 Tracked:** Closed in WP-31, BUGS.md "xmtick, ymtick, xmlabel, ymlabel, tmtick and tmlabel and their *2 forms are pending and never read", commit 4db3719.
- **D1b Tracked:** Closed in WP-31, BUGS.md "Minor labels on a far-side axis stay where the build put them after a move, and minor ticks on axes 3 to 9 are named, not drawn", commit 0862bf7.
- **D1c Tracked:** Closed in WP-31, BUGS.md "A minor-label format() is not kept after a move, axis-2 minor-label angle() is unbounded, and an evenly spaced typed list is drawn as a rule", commit fc92e8d.
- **D1d Tracked:** Closed in WP-31, BUGS.md "An outer axis's ##N minor labels after a move are capped at its build's label pool", commit 20ee5f0.
- **D2 Tracked:** Closed in WP-31, BUGS.md "t1title to r2title are pending and title2 and subtitle2 are named where twoway refuses them", commit 2c6a68a.
- **D2b Tracked:** Closed in WP-31, BUGS.md "Edge titles name position(), ring(), span and orientation() where twoway draws them", commit 5a36059.
- **D3 Tracked:** Closed in WP-31, BUGS.md "Textbox sub-options on titles are named and _dash_textbox_place is wired to scheme clocks only", commit 0dfb5b6.
- **D3b Tracked:** Closed in WP-31, BUGS.md "subtitle() position() and ring() on a by() panel's label row are named, not drawn", commit ceccb04.
- **D4 Tracked:** Closed in WP-31, BUGS.md "Legend geometry sub-options are named, corner clocks are centred, pos(0) and ring(0) land at Bokeh's top_right, label(#) with no text is dropped, and identical keys are not merged", commit c2e27c0.
- **D4b Tracked:** Closed in WP-31, BUGS.md "Legend stacked, symplacement(), colgap() and the legend's own subtitle(), note() and caption() are named, not drawn", commit c7df7e1.
- **D5 Tracked:** Closed in WP-31, BUGS.md "scale(), fxsize(), fysize() and the overhangs are never read, and aspectratio() shapes the figure, loses to xsize/ysize and refuses placement()", commit 831e4f0.
- **D6 Tracked:** Closed in WP-31, BUGS.md "Axis label and tick style sub-options are named, ##5 is read as #5, and label forms twoway refuses are drawn", commit 2c2ad89.
- **D6b Tracked:** Closed in WP-31, BUGS.md "alternate on an axis(2) to axis(9) label option is named, not drawn", commit c6efd39.
- **D7 Tracked:** Closed in WP-31, BUGS.md "Axis-scale look options fill, outergap(), extend, fextend and lstyle are named and two yscale(alt) do not toggle back", commit 8768cac.
- **D8 Tracked:** Closed in WP-31, BUGS.md "yvarlabel() and xvarlabel() are undeclared, noted and absent from the help", commit 6cc4f83.
- **D9 Tracked:** Closed in WP-31, BUGS.md "The y2 and x2 range is built once and never follows a filter move, the first-used axis is not drawn left or bottom, and horizontal with yaxis(2) titles no x axis", commit c8a5e9a.
- **D9b Tracked:** Closed in WP-31, BUGS.md "With three or more axes the outer axes keep dash's number order, and text(..., yaxis(#)) is not renumbered with its axis", commit c685d0d.
- **D10 Tracked:** Closed in WP-31, BUGS.md "by() sub-options of its stage-3 grammar are named, overall legend placement and interaction differ, panel margins ignore iscale(), and panels emptied by a filter stay drawn", commit af3273a.
- **D10b Tracked:** Closed in WP-31, BUGS.md "by()'s shrink, overallshrink, region margins, array outline and the econ, stata7, combine and rescale bystyles are named, not drawn", commit 90d8a51.
- **D10c Tracked:** Closed in WP-31, BUGS.md "The econ and stata7 bystyles are named and the combine and rescale bystyles draw only their scales", commit f91707a.
- **D11 Tracked:** Closed in WP-31, BUGS.md "graphregion margins are inexact, the intensity and shade options are named, several marginstyle forms are not parsed, and s1color's unfilled plot region is filled white", commit a8ae5a6.
- **D11b Tracked:** Closed in WP-31, BUGS.md "margin(l+1e400) draws zeros with a note where twoway draws a medium margin", commit 880accb.
- **D12 Tracked:** Closed in WP-31, BUGS.md "An out-of-range xline() or yline() is clipped to the frame and an unextended end stays put after a zoom", commit 397d1a3.
- **D13 Tracked:** Closed in WP-31, BUGS.md "Added text ignores tstyle() and the textbox sub-options and does not expand a global macro in a drawn label", commit 86e627a.
- **D13b Tracked:** Closed in WP-31, BUGS.md "Global macros in title(), subtitle(), note() and caption() are drawn literally where twoway expands them", commit 47e2f82.
- **D14 Tracked:** Closed in WP-31, BUGS.md "tabs() drops unregistered names silently, the served layout() overwrites a cell silently, and there is no per-tab layout()", commit bb9f4a9.
- **D15 Tracked:** Closed in WP-31, BUGS.md "Date #N ticks agree with _tsnatscale on 52 to 98 percent of ranges, xtick(#N) and xlabel(minmax) are held after a move, and the margin is a build-time fraction", commit 023caab.
- **D16 Tracked:** Closed in WP-31, BUGS.md "legend(po(9) top) names top first, title(T, prefix suffix) prints no ignored line, and values nested in legend(region()) are unchecked", commit 398149e.
- **D16b Tracked:** Closed in WP-31, BUGS.md "A bare quoted string after the comma is named in the note where twoway refuses it as quotes unbalanced", commit 78f2ba0.
- **E1 Tracked:** Closed in WP-31, BUGS.md "Marker symbols arrow, arrowf, A, a and pipe are refused, pipe is horizontal, point is 8 px, V is filled, shorthands are full size and non-Stata names are accepted", commit ab33ff3.
- **E2 Tracked:** Closed in WP-31, BUGS.md "Line-pattern formula strings are refused, named pattern geometry differs from Stata's and mlpattern() is pending", commit 947c9ca.
- **E3 Tracked:** Closed in WP-31, BUGS.md "msangle(anglestyle name) is drawn at 0 degrees and mlalign(), mwidth and mlabstyle() are undeclared", commit 8adad05.
- **E4 Tracked:** Closed in WP-31, BUGS.md "Glued = stylelist forms and a parenthesised element reach the renderer as one unknown element", commit 0e81c30.
- **E5 Tracked:** Closed in WP-31, BUGS.md "A comma colour inside a structured sub-option is drawn black where twoway refuses r(198)", commit 3576ec2.
- **E6 Tracked:** Closed in WP-31, BUGS.md "Line-width *# multiplies before the 0.3 pt floor and tlwidth() and glwidth() are named not drawn", commit db38355.
- **E7 Tracked:** Closed in WP-31, BUGS.md "A pstyle(p#) CI band under a scheme intensity above full is clamped to full", commit 5bc828a.
- **E8 Tracked:** Closed in WP-31, BUGS.md "rarea and rbar outlines are not stroked where twoway strokes them from the scheme", commit 1a2c566.
- **E9 Tracked:** Closed in WP-31, BUGS.md "Inline SMCL style runs and raised text with no Unicode form are drawn in the text's own style, and hline, space, dup, cmd, hi, ccl, center and links are drawn as typed", commit 7c630e7.
- **E10 Tracked:** Partly closed in WP-31 (section 44, commit dda6868): the four classes, shadestyle, user files, class directives on named and default styles, adoarchive, rows embedded at registration; open: textboxstyle and color-*.style files (BUGS.md "textboxstyle and color-*.style files on the ado-path are not read").
- **E10b Tracked:** Open (WP-31 section 56).
- **E11 Tracked:** Closed in WP-31, BUGS.md "Sizes are relative to a 4-inch reference and scale() is pending", commit 0d9af7a.
- **E11b Tracked:** Closed in WP-31, BUGS.md "A scheme's #-pt gsizes convert at 4 inches when the scheme's smaller graphsize side is not 4 inches", commit dc4c0ec.
- **E12 Tracked:** Closed in WP-31, BUGS.md "translate_msymbol and translate_lpattern lower-case names where Stata style names are case-sensitive", commit 947c9ca.
- **E13 Tracked:** Closed in WP-31, BUGS.md "_SIZE_MAP and _GSIZE_NUMERIC_PT_PER_UNIT are dead but kept and serialised, and histogram scheme opacity is unverified", commit e1e0207.
- **F1a Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit lfit and qfit after a filter move (the JS prelude and the lfit and qfit twins)", commit 76547f8.
- **F1b Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit lfitci and qfitci after a filter move (the lfitci and qfitci twins)", commit 55ee2e5.
- **F1c Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit lowess after a filter move (the lowess twin)", commit 3e5823c.
- **F1d Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit lpoly after a filter move (the lpoly twin)", commit bbc640a.
- **F1e Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit lpolyci after a filter move (the lpolyci twin)", commit 2b9ce0a.
- **F1f Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit mband and mspline after a filter move (the mband and mspline twins)", commit 54554e2.
- **F1g Tracked:** Closed in WP-31, BUGS.md "The saved page does not refit fpfit and fpfitci after a filter move (the fpfit and fpfitci twins)", commit b9488d3.
F1 (all parts): closed in WP-31 sections 10, 13, 16, 19, 22, 25, 28; residual: the lpoly/lpolyci exact-fit bandwidth, where the saved page keeps the build and marks the layer (BUGS.md "lpoly's default bandwidth on an exactly fitted y differs between the saved page and the served app", C11b)
- **F2 Tracked:** Closed in WP-31, BUGS.md "The function points-free fallback evaluates ten math names only", commit 5075645.
- **F3 Tracked:** Closed in WP-31, BUGS.md "Stata ground truth is missing for weighted qfitci and fpfitci bands, stdf and stdr under fw, the six kernels on lpolyci, pattern lengths and on-edge values", commit 0e97169.
- **F4 Tracked:** Closed in WP-31, BUGS.md "_LPOLY_ROT_CONSTANTS holds degree 4-7 rows that are unreachable under the degree 0-3 rule", commit 8f8fdf7.
- **F5 Tracked:** Closed in WP-31, BUGS.md "The map_qfitci docstring, the module header and the _dash_fold_typed comment describe code that no longer exists", commit 1918fc4.
- **G1 Tracked:** Closed in WP-31, BUGS.md "Extended missing .a to .z are merged into one null in by(, missing) panels, marker labels, filters and tooltips", commit 17d01bc.
- **G2 Tracked:** Closed in WP-31, BUGS.md "set dp comma is never read, %tC is converted without leap seconds and graph set font faces are not read", commit becb59c.
- **G3 Tracked:** Partly closed in WP-31 (section 43, commit 1a2df3d): shadowing and the planned count; open: the binary data file and the strL loop (BUGS.md "The data file embeds numbers as JSON text (about 0.5 GB per million values)" and "The strL binary check reads every observation one at a time"), and the working columns in the user's data (BUGS.md "Qualifier and working columns are generated in the user's data (r(900) possible at c(maxvar))").
- **G3c Tracked:** Open (WP-31 section 55).
- **G3d Tracked:** Open (WP-31 section 55).
- **G4 Tracked:** Closed in WP-31, BUGS.md "Carried hover, mlabel and row-id columns are upcast to object and handed to Bokeh as Python lists", commit fb6bdad.
- **G5 Tracked:** Closed in WP-31, BUGS.md "One format-writer model is emitted per distinct tick format and per tooltip kind", commit fb0d5ae.
- **G6 Tracked:** Closed in WP-31, BUGS.md "Fractional %t values are floored on load and join-order edge cases differ", commit 8b367e7.
- **G7 Tracked:** Closed in WP-31, BUGS.md "%d and %tb axis formats are drawn %9.0g with a note and xvarformat(bogus) is noted where twoway refuses", commit 75f0f12.
- **H1 Tracked:** Closed in WP-31, BUGS.md "Saved-page JavaScript errors fail silently and saved sliders fire on every drag step", commit ec5fe79.
- **H2f Tracked:** Closed in WP-31, BUGS.md "Filters lack a multi-select dropdown, a (missing) option, a slider direction and a reset button (the filter widgets)", commit e7c500a.
- **H2k Tracked:** Closed in WP-31, BUGS.md "KPI cards take no weights and lack kurtosis, semean and range (the KPI statistics)", commit d1076a8.
- **H2l Tracked:** Closed in WP-31, BUGS.md "One link group only, brush cannot act as a filter, a brush on bars or histograms drives nothing and concurrent brushes are not intersected (the link groups and brush)", commit 01d9b3f.
- **H2t Tracked:** Closed in WP-31, BUGS.md "No per-graph data table shows the rows a graph draws (the data table)", commit 30edbb3.
- **H2x Tracked:** Closed in WP-31, BUGS.md "No print stylesheet, and PNG and SVG export omit KPI cards, title, filters and the tab strip (the export and print parts)", commit pending.
- **H3 Tracked:** Partly closed in WP-31 (section 55, commit pending): the served bundle no longer ships the bokeh-mathjax component; open: the build on the event loop, catch_warnings swapping filters and a brush made during a move being cleared (BUGS.md "Served build on the event loop").
- **H4 Tracked:** Closed in WP-31, BUGS.md "BOKEH_RESOURCES=cdn blanks the served page silently, BOKEH_MINIFIED and BOKEH_DEV change the saved page silently, /health reports only ok, and the browser-launch return code is never read", commit pending.
- **H6 Tracked:** Open (WP-31 section 60).
- **H7 Tracked:** Open (WP-31 section 55).
- **I2 Tracked:** Open (WP-31 section 59).
- **I3 Tracked:** Open (WP-31 section 59).
- **I4 Tracked:** Open (WP-31 section 59).
- **I5 Tracked:** Open (WP-31 section 59).
- **I6 Tracked:** Open (WP-31 section 60).
- **I7 Tracked:** Open (WP-31 section 59).
- **J1 Tracked:** Open (WP-31 section 56).
- **J2 Tracked:** Open (WP-31 section 56).
- **J3 Tracked:** Open (WP-31 section 57).
- **J4 Tracked:** Open (WP-31 section 58).
- **J5 Tracked:** Open (WP-31 section 58).
- **J6 Tracked:** Open (WP-31 section 58).
- **K2 Tracked:** Open (WP-31 section 60).
- **K3 Tracked:** Open (WP-31 section 60).
- **K4 Tracked:** Open (WP-31 section 60).
- **K6 Tracked:** Closed in WP-31, BUGS.md "One aria-live region, no alt text and English-only interface", commit pending.
