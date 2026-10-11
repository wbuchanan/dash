# Section 04: `function` evaluated by Stata

> Part of: WP-29 · P0: P0.6 (GAPS2-A6-d, GAPS2-C5-g, GAPS2-A6-c) · Risk: yellow · Batch: 1 · Depends on: 01 · Blocks: — · Tasks: 17, 1 commit (P0.6) · Case prefix: FX · Effort: L (DROPIN-REMAINING.md:42 scoped it S; see A12)

## Review amendments (binding; they override any conflicting text below)

This section carries unit u06 ("sound with amendments"). Every amendment is applied as follows.

| Id | Amendment | Where it is applied |
|---|---|---|
| A1 | Write each point with `%24.17g`, not `%21.0g`; put the leading `0` back on `.` and `-.`; add exponent-form probes. | TR-04.3 (`_dash_json_number17`); fixture probes `x/3` over `range(0 0.00001)` and `1/x` over `range(0 1e-5) n(7)`; measured below (Evidence E7). |
| A2 | Evaluate after the segment loop and after the `by()` variables are checked, before the graph-level options. | TR-04.2. Measured G1-G8 and N7 are quoted in Evidence E3. |
| A3 | `by()` evaluates once per panel in twoway. Either port that or document it as a tested residual. | The residual route is taken (decision S4-D4). It is pinned by FX-24, stated in the help and recorded in the BUGS.md Resolution. |
| A4 | Never let points overflow a macro. Prefer keeping points out of macros. | Preferred route taken (S4-D3): one global `dash_fpts_<name>` per graph, written to the spec file in Mata, attached by the renderers. Per-graph `c(macrolen)` check refuses r(134) before anything is set. Build-time readers never see points. |
| A5 | The "session-state QUIRK" is false: a varless dataset is reset to `_N == 0`. | Removed everywhere. FX-04 pins `_N` parity on varless data (measured M3 below: `tw N=0`, `proto N=0`). |
| A6 | With `_N >= n` the data are marked changed, as twoway marks them. | FX-04 parity test; stated in help and CHANGELOG. |
| A7 | Refuse raw text with a top-level comma before building the generator's command line; never pass `generate(..., replace)`. | TR-04.2 (`_dash_comma_pos`, quote- and paren-aware). FX-06 builds the text directly. |
| A8 | Break under `capture` is rc 1: re-raise, no echo. | TR-04.2; FX-06 simulates it with an in-memory stub of `twoway__function_gen`. |
| A9 | A served spy on `dash_render._floats_only` sees nothing. | Every served spy is set on the generated app module's own copy (`mod._stata_fn_parse`), and the "never evaluated" tests put an unevaluable expression beside valid points in both modes. |
| A10 | Bound the fallback's total depth, not only parentheses; keep the parser self-contained or copy its helpers. | Chains are folded iteratively (n-ary nodes), nesting is capped at 40 (Stata refuses 50, measured), and both functions are self-contained module functions in the served copy list. |
| A11 | Hostile points: `10**400`, NaN, Infinity, `1e400`. | TR-04.6 `_dash_function_points` converts inside `try/except (OverflowError, TypeError, ValueError)` and refuses non-finite x0/dx/y. `n(1)` is still refused by dash, so `dx` is never missing. |
| A12 | Effort is L, not S. | Header line. |

**Missed sites from the review (all handled).** These are: `dash.ado:4170/4175/4179/4820/5131/5137/5869` (points no longer travel in those macros), `5200/6949/6957/7068/7283` (the build-time readers never see points), the `_needed` list `dash.ado:232-245`, the header `dash_parse.mata:78-93`, the segment loop `4730-4821`, `_dash_by_panels` (not used: S4-D4), the facet call sites (unchanged: one point set per layer), the served copy tuple, `test_conformance.cscript` C-03, `test_json_escaping.cscript` JSE-47 and `test_qualifier_literals.cscript` QL-20.

**Design decisions of this section beyond the reviewed design.** Each is grounded in a measurement quoted under Evidence.

| Id | Decision | Why (evidence) |
|---|---|---|
| S4-D1 | The Python fallback (specs without points) is a **tree interpreter** (`_stata_fn_parse` + `_stata_fn_eval`), not an `ast` tree handed to `compile`/`eval`. `_stata_expr_to_python`, `_floats_only` and the in-method AST validator are deleted. | Stata propagates a missing value through every operation. `(0^-1)^0+x`, `1/(1/0)+x`, `exp(-exp(1000))+x` and `x^.` are missing at every x (E5, m2). numpy's operators heal them: `1/inf = 0`, `exp(-inf) = 0`, `inf**0 = 1`, `1**nan = 1`. The interpreter maps every intermediate non-finite value to missing. It also removes the last `eval()` of spec text from both renderers (rule 1). |
| S4-D2 | `_dash_fn_refuse` is retired, together with its two Mata helpers `_dash_fn_names` and `_dash_fn_space_call`, which `test_no_orphans.py` would otherwise flag. | The generator returns twoway's rc for every case it handled, with the RNG untouched (M7). twoway prints one line, `error in expression:  nosuch(x)` (M13), not dash's extra `unknown function` line. A pre-check of all layers would refuse `(function y=runiform()) (function y=nosuch(x))` before the first layer draws, where twoway advances the RNG first (N7: `rc=133 rngchanged=1`). |
| S4-D3 | Points are stored per graph in `$dash_fpts_<name>` (10 + 22 = 32 characters) and written to the spec as a top-level `"function_points"` member. Both renderers move them onto their plots at load (`_dash_attach_function_points`). | This is A4's preferred option. The `dash_json_<name>` readers and the build-time concatenation keep their current size. |
| S4-D4 | `by()`: evaluated once, drawn in every panel. Residual, pinned and documented. | Deterministic expressions, including data references, are identical across twoway's panels (M2: both sersets `0 17 44`). Only an RNG expression differs. Matching panel order between Stata and both renderers' facet builders is out of this section's reach. |
| S4-D5 | The generator gets the **typed** `range()` when it is two plain numbers. Otherwise it gets dash's normalised numlist. | `numlist "0.123456789012345678 1e-7 ..."` gives `.1234567890123 1.00000000e-07` (M10): 13 digits. The generator given the typed text gives `0.12345678901234568` (A7 in m4c). |
| S4-D6 | `_dash_fn_points` sets `._Gr_Global.callerver` to the user's version, as `graph.ado:9-23` does before every graph. | `twoway__function_gen.ado:227-235` evaluates under `version callerver:` when `_Gr_Global` exists, else under its own `version 8`. A stale value left by an earlier graph is read otherwise (M6: `callerver now=13` after a `version 13:` graph). |
| S4-D7 | The size refusal is r(134), dash's limit code (`_dash_plot_cap_refuse`, `_dash_byte_cap`). The research's r(920) is not used. | BRIEF "Refusals use Stata's codes: r(134) limits". |
| S4-D8 | Case ids are `FX-nn`. Refusals go in `test/test_parser.cscript` (R1 table), truth in `test/test_wp29_truth.cscript` block S04 (index A3). There is no `P1A-85` and no `U06` block. | index.md manifest and A3. |
| S4-D9 | Files beyond the manifest's list: `test/test_json_escaping.cscript` (JSE-47 flip), `test/test_conformance.cscript` (C-03 control), `test/test_security_surface.py` (`2*pi*x` and the eval spy), `test/test_mode_parity.py` (CORPUS, R6), `test/test_qualifier_literals.cscript` (QL-20 re-run only, no edit expected). `test/test_fixtures_are_committed.py` needs no edit; it is run as a guard. | Measured pins (Evidence E10). |

## Overview

**What is wrong today.** DROPIN-REMAINING.md:42, P0.6, says `function` evaluates `^` right to left and accepts `pi` and `e`. `2^3^x` at x=2 draws 512 where Stata gives 64, and `pi*x` draws where `twoway` refuses it with r(111). The audit understated it. dash never asks Stata. `map_function` (dash_render.py:12431-12630) rewrites `^` to Python's `**` character by character (`_stata_expr_to_python`, :13752-13782) and `eval`s the result. The Stata grammar is lost in three ways:

- `**` is right-associative, and it binds a sign after it to the whole tail;
- `/` and `*`, and `-` and `+`, are grouped Python's way;
- Python's names and operators are let through: `pi`, `e`, `**`, `%`, `//`, a leading `+`, and NFKC-folded full-width names.

Measured at HEAD (E2):

- `2^3^x` → `2 8 512`;
- `0.1*3/0.3` → `1.0000000000000002`;
- `1e16+1-2` → `9999999999999998`;
- `pi*x`, `e*x`, `x**2`, `x%2`, `+x`, `x//1` and `ｓｉｎ(x)` draw;
- `_pi*x`, `normalden(x)`, `ln(x)`, `_b[]` and scalars draw nothing.

The served app runs the same mapper and redraws the same wrong values after every filter move.

**What will be true after.** A function layer's points are Stata's own:

- At registration, `dash` runs `twoway__function_gen` (the generator `twoway function` itself calls), with twoway's range, `n()` and caller version. The evaluation happens at twoway's point in the command: after every plot and the `by()` variables are checked, before the graph options.
- It refuses exactly what twoway refuses, with twoway's return code and its one-line message.
- It stores the points (`x0`, `dx` and every y written `%24.17g`, a missing value `null`) beside the graph.
- Both renderers draw those numbers and never evaluate the expression.
- The points are fixed, as twoway's drawing is fixed when its command runs. They are identical saved and served, and before and after any filter move.
- A spec written by hand without points is drawn by a small Stata-grammar interpreter with Stata's missing-value rules, so `2^3^x` is 64 there too.

**Why one section.** P0.6 is one code path with two halves. Stata decides the points (`dash.ado`, `dash_parse.mata`) and the renderers draw them (`dash_render.py`, both modes). Neither half is correct alone.

**Test order (rule 7) and commit rule (D1).**
- Tasks 04-03..04-05 write the fixture and every regression test, and run them against the batch-1 base (`<scratch>/batch-1-base.txt`).
- They save the failure text to `<scratch>/04-P0.6-failure.txt` and commit nothing.
- 04-06..04-10 make them green, 04-11..04-14 flip the pinned tests, 04-15 certifies in Stata, and 04-16 updates the help.
- 04-17 closes the BUGS.md entry in place, replaces the two CHANGELOG markers, deletes the `WP29_OPEN["P0.6"]` key, runs the full suite once and makes the section's **one** commit. Its subject ends `(WP-29 P0.6)` and its body opens with the saved failure text.

## Risk: [yellow] — a Stata-side evaluation inserted into every function command, a new registry global, and a rewritten evaluator in both renderers

**Why yellow.** The behaviour is fully specified by measurement, and the renderer change is contained. But four kinds of shared code change: the command flow of `_dash_plot` (every graph command), the registry, the spec writers, and the load path of both renderers.

**Risk factors.**
1. Validation order inside `_dash_plot` changes: `by()` is checked first, then functions are evaluated, then the other graph options. A wrong placement changes the rc of mixed refusals.
2. RNG side effects are new: registering `runiform()` now advances the stream, as twoway does.
3. Macro-length limits: `st_global` truncates silently past `c(macrolen)` (645,200; measured c2), and a `local` concatenation past it is an uncapturable r(920).
4. About 25 existing tests pin the old evaluator or its instruments: `_floats_only` spies, `node.keywords` and `_SAFE_NAMES` source pins, and `pi`/`**` expressions.
5. Shared files: `_dash_process_segment` (S02 `sort()`), `_dash_plot` (S06 hover export later in the file), the spec writers (S08 private writer, merged after S04), and `dash_render.py` dispatch (S02).

**Mitigation.**
1. G1-G8, M8 and N7 are re-asserted live against twoway in FX-02.
2. FX-03 and FX-22 compare `c(rngstate)` with twoway's.
3. Points never travel in macros. A per-graph `strlen` check runs before `st_global`, and a dashboard check runs against the bytes limit. FX-07 asserts refusals and unchanged registry globals.
4. Each pin is flipped with a `Flipped:` line and re-pointed to the new acceptance point (`_stata_fn_eval`), never deleted (R7).
5. R1-R4 merge rules. Only the function branch and the post-loop block are edited in `dash.ado`, and only the two `master_json` writes plus one Mata call are edited in the writers.

## Dependencies

- **Depends on:** S01. It opens the BUGS.md entry for P0.6, places `<!-- WP-29 P0.6 -->` in `### Results that change` and `### Changed behaviour`, adds `WP29_OPEN["P0.6"]`, and creates `test/test_wp29_truth.cscript` with the marker line.
- **Blocks:** none in the manifest. Interface notes for later sections:
  - S12 (P0.17 stale cue) must treat `function` as never stale: its points do not depend on the rows.
  - S14 (embed rows) reads no data for a function layer.
  - S08 rewrites the two spec writers after this section and must keep the Mata tail call (TR-04.4).
- **Parallel batch:** 1. Merge order `S01, S09, S03, S02, S04, S06, S07, S05, S08`.
- **Why:** batch 1 needs only S01's tracking scaffold. No other section touches `map_function`, the function branch, the `function_points` transport or `_dash_fn_*`.

## Evidence

All Stata runs are StataNow 19.5 MP through `scripts/stata_slot.sh <dir> <file>.do` with `dash_nobrowser=1`. Values are read with `serset set \`.Graph.plotregion1.plot1.serset.id''` then `serset use`. Python probes import `dash_render` at `7421d3d`.

### E1. twoway's grammar (u06 truth5/8/13, confirmed by the review)

At x = 0 1 2:

| Expression | twoway | Expression | twoway |
|---|---|---|---|
| `2^3^x` | 1 8 64 | `-2^2` | -4 |
| `2^-1^2` | .25 | `-x^2` | 0 -1 -4 |
| `x^2^-1` | . 1 .25 | `x*-2^2` | 0 -4 -8 |
| `-x^-x^-1` | -1 -1 -4 | `3-2^2` | -1 |
| `2^-x^2` | 1 .25 .0625 | `- -x`, `--x` | 0 1 2 |
| `-2^-2^-2` | -16 | `0.1*3/0.3` | 1 |
| `2^-2^-1` | 4 | `1e16+1-2` | 1e16 |
| `x^-1^-1` | . 1 2 | `1+0.1-0.7` | .40000000000000002 |
| `2^+1` | 2 | `10-2-3`, `100/10/5` | 5, 2 |

So `^` is left-associative, and a sign after `^` takes one operand. Unary minus binds looser than `^`. `/` binds tighter than `*`, and binary `-` tighter than `+` ([U] 13.2.5). A leading `+` is refused everywhere except after `^`.

### E2. dash at HEAD (Python probe, `GlyphMapper().map_function(figure(), e, (0.0, 2.0), 3, {})`)

```
'2^3^x'      [2.0, 8.0, 512.0]
'2^-1^2'     [0.5, 0.5, 0.5]
'0.1*3/0.3'  [1.0000000000000002, ...]
'1e16+1-2'   [9999999999999998.0, ...]
'pi*x'       [0.0, 3.141592653589793, 6.283185307179586]
'e*x'        [0.0, 2.718281828459045, 5.43656365691809]
'x**2' [0,1,4]   'x%2' [0,1,0]   '+x' [0,1,2]   'x//1' [0,1,2]
'ｓｉｎ(x)'  [0.0, 0.8414709848078965, 0.9092974268256817]
'_pi*x' []   'x^.' []
```

A Stata-built spec carries `{"type":"function","expr":"2^3^x","options":{"n":"3","range":"0 2"},...}`, and `dash build, server` gives `y_fn 2 8 512` (u06 dashnow). After a foreign-dropdown move, served `_redraw` re-runs `map_function` and draws `2 8 512` again. On the saved page the function's ColumnDataSource is referenced by no CustomJS (u06 probe_move).

### E3. Refusals, codes and the order of checks (m1, m2, g1)

```
M13 nosuch(x) -> "error in expression:  nosuch(x)" rc=133
    pi*x -> 111   x**2 -> 198   x%2 -> 198   +x -> 198   x^ -> 111   2^^x -> 198
N8  twoway function nosuch(x)  -> "error in expression: nosuch(x)" (one blank)
N9  twoway function y=nosuch(x) -> "error in expression: nosuch(x)" (one blank)
N11 2x -> 198    N12 sin(x,1) -> 198    N10 2/-x -> 0    N13 1.8X+01*x -> 0
N1  x + 5000 unknown calls -> 133    N2 x + 5000 '+ sin(x)' -> 130    N3 x + 5000 '+ (x)' -> 130
N4  x + 500 '+ sin(x)' -> 0          P2 700 '+x' -> 0, 800 '+x' -> 130
P1  40 nested parentheses -> 0       N6 50 nested -> 198      P5 50 nested sin() -> 198
```

The message is `error in expression: ` followed by the text after the `=` exactly as typed (two blanks for `y = e`, one for `y=e` or no `y =`).

Order of checks (g1, m1, m2):

```
G1 (function y=runiform()) (scatter nosuch weight)            rc=111 rng_changed=0
G2 (function y=runiform()), badopt                            rc=198 rng_changed=1
G3 (function y=runiform()), xlabel(foo)                       rc=198 rng_changed=1
G4 (function y=x**2) (scatter nosuch weight)                  rc=111
G5 (function y=x**2) (scatter mpg weight, badopt)             rc=198 ('option badopt not allowed')
G7 (function y=x**2) (scatter mpg weight), by(nosuchv)        rc=111
G8 (function y=runiform()) (scatter mpg weight), by(nosuchv)  rc=111 rng_changed=0
M8b function y=nosuch(x), badopt                              rc=198
M8c function y=nosuch(x), n(0)                                rc=198
N7  (function y=runiform(), range(0 2) n(3)) (function y=nosuch(x))  rc=133 rngchanged=1
M7  generator alone: y=runiform()+nosuch(x) rc=133 rngchanged=0; y=runiform()+pi*x rc=111 rngchanged=0
```

So twoway checks every plot's varlist and options and the `by()` variables first. Then it evaluates the layers in order. Then it checks the graph options. dash today refuses M8b and M8c with r(133) at segment time (`_dash_fn_refuse`, dash.ado:3545), which is the wrong code.

### E4. What the generator does (twoway__function_gen.ado, read)

- `syntax anything(... equalok) [if], Range(string asis) Xis(name) [N() GENerate() DROPlines() ...]`, followed by the `y =` parse with `gettoken` (lines 7-60).
- `if _N < n set obs n` without its own preserve (line 208). The caller preserves, as `twoway_function_parse.class` `log_create_serset` does with `.func_preserve`.
- `x = r(min) + r(delta)*(_n-1)` (lines 214-217), then `version callerver: GenData double y = <exp> in 1/n` when `_Gr_Global` exists (lines 227-235). `graph.ado:9-23` sets `._Gr_Global.callerver = string(_caller())` on every graph.
- The program is `sortpreserve`. twoway's serset is then sorted by x (`log_create_serset`: `.sersetname.sort x`), so `range(2 0)` is drawn over 0 1 2 (M16: generator `min=2 delta=-1 ys=4 1 0`, twoway's serset `xs=0 1 2 ys=0 1 4`; the same polyline).

The prototype program (`if _N < n preserve`; `tempvar fy fx`; `capture twoway__function_gen <raw>, range(lo hi) x(x) n(n) generate(fy fx)`) matched twoway on 27/27 probes (u06 proto). Further measurements:

```
M2  by(foreign), y = mpg*x: both panel sersets 0 17 44   (data rows 1-3, not per panel)
J1  by(foreign) runiform() n(3) consumes 6 draws; J2 by(foreign,total) -> three sersets = draws 1-3, 4-6, 7-9
M3  clear; set obs 5; twoway function y=x -> N=0 k=0; prototype -> N=0 k=0
K1  sysuse auto; twoway function, n(3)  -> changed=1, sortedby=foreign; K2 prototype changed=1
K3/K4 n(300) > _N: changed=0 for both
M5  y = max(x,1): prototype = twoway = 1 1 2; injected "y = x, range(5 6)" -> rc=198
Q4  twoway__function_gen y = x, generate(mpg weight, replace) range() x(x) n(3) generate(a b)
    -> "option generate() not allowed" rc=198, mpg kept
Q1  twoway function y = strlen(`"ab"')*x -> rc 0     Q2 y = strlen("'x") -> rc 198
M6  after `version 13: twoway function`, callerver=13; prototype under user version 19 gives
    twoway-19's values .13387664401253263 .13640703636619722 .45121490384453822 (RNG follows
    the user version); `version 13: twoway` gives .13698407844640315 ...
M11 global FXG 3; `twoway function y = \$FXG*x` -> 0 3 6; prototype with "y = \$FXG*x" -> 0 3 6
    (one expansion, inside the generator, in both)
```

### E5. Missing-value propagation (m2): why the fallback is an interpreter (S4-D1)

```
x^.                 -> . . .      (numpy: 1**nan = 1 at x=1)
(0^-1)^0 + x        -> . . .      (numpy: inf**0 = 1)
1/(1/0) + x         -> . . .      (numpy: 1/inf = 0)
exp(-exp(1000)) + x -> . . .      (numpy: exp(-inf) = 0)
2--x -> 2 3 4
```

### E6. Limits (m1, m6, c1, c2)

```
M9  macrolen=645200 cmdlen=645216 maxvar=5000;  L2 set maxvar 20000 -> macrolen=2580200
c2  mata st_global() of an 800,000-character string truncates to 645,200 (silent)
c1  capture noisily local b "`a'`a'`a'" with 900K characters aborts the do-file (r(920), uncapturable)
A5  10,000 points of sin(x)/x over range(-100 100): generator + %24.17g writer 0.031 s,
    217,287 characters (about 21.7 a point)
```

### E7. The writer's number format (e1, m4)

`%21.0g` drops digits in exponent form. `3.3333333333333e-301`, `-6.66666666666667e-08` and `-1.46666666666667e+70` read back as other doubles. `%24.17g` reads back exactly. Prototype output (m4, parsed back in Python):

```
A1 x/3, range(0 0.00001) n(3): {"x0":0,"dx":5.0000000000000004e-06,"y":[0,1.6666666666666669e-06,3.3333333333333337e-06]}
A2 1/x, range(0 1e-5) n(7):    {"x0":0,"dx":1.6666666666666669e-06,"y":[null,599999.99999999988,...,99999.999999999985]}
A7 x, range(0 0.123456789012345678) n(3): y[2] = 0.12345678901234568 = x0 + 2*dx in numpy
M1 %24.17g writes .5 and -.5 (leading zero needed), 0 as 0, 1e21 as 1.00000000000000000e+21; . .a .z as . .a .z
A4 Mata fopen(path, "a") + fwrite appends: {"graphs":[]  +  ,"function_points":{}}  ->  {"graphs":[],"function_points":{}}
```

The review checked that `x0 + dx*np.arange(n)` equals twoway's x bit for bit on 10 ranges, n from 3 to 10000 (u06-review d1). `np.linspace` sets the last point to `stop` and is not twoway's rule.

### E8. The current code (anchors at `7421d3d`)

- **dash.ado function branch,** `_dash_process_segment` 3521-3546. Mata strips `name =` (3525). The no-expression refusals follow (3535-3542), then `_dash_fn_refuse \`"\`macval(expr)'"'` (3545). The JSON is `"expr":"<escaped>"` (4124-4127).
- **Options in the segment:** `_dash_parse_plot_opts` (3923), `_dash_opts_repeats` (3938), `_dash_validate_opts` (3956). The rules are `n=int,2,10000` and `range=numlist,2,2` (dash.ado:1901-1905); numlist normalisation is at 2161-2186.
- **Segment loop,** `_dash_plot` 4730-4821. The per-segment resets are at 4736-4745, the call at 4755, the plot count at 4780, and `macro drop dash__gq_if dash__gq_in dash__g_by` at 4823. The graph rules follow (`_dash_option_rules` 4848, loop 4849-4858; `by=byvarlist` is the fifth rule, dash.ado:1946-1951), then `_dash_check_legend` (4863), then the `by()` panel answer (4868-5015). That answer skips any graph holding a literal or function layer (`_by_lit`, 4893-4898).
- **Routing:** `_dash_register_graph \`_rg_name' \`_rg_json' \`_rg_spec'` (5162); `_dash_render_immediate \`"\`graph_json'"'` (5165).
- **`_dash_fn_refuse`:** comment block 5421-5456, program 5457-5501.
- **`_dash_register_graph`:** 5740-5884. It drops the old item (`_dash_drop_item`, 5858-5864) and stores the two globals (5866-5869).
- **`_dash_render_immediate`:** `args json_spec` (5892), `master_json` (6138), writer (6143-6145).
- **`_dash_clear`:** sweeps `dash_spec_* dash_json_* dash_opts_* dash_kpi_*` (6218-6221).
- **`_dash_prepare_spec`:** the graph loop (7152-7176), `master_json` (7281), writer (7286-7288).
- **`_dash_require_mata` `_needed`:** 232-245 (`_dash_fn_names _dash_fn_space_call` at 242). `program define dash` calls `_dash_plot \`macval(0)'` at 140.
- **dash_parse.mata:** header entries 80-83 and 90-93. `_dash_json_number` (%21.0g) is at 1414-1427, `_first_comma_pos`/`_dash_comma_pos` at 1744-1784 (quote- and compound-quote-aware), `_dash_item_globals` at 3837-3860 (the exact list `dash_json_`, `dash_spec_`, `dash_kpi_` and the KPI fields), `_dash_fn_names` at 3944-3995 and `_dash_fn_space_call` at 5161-5268.
- **dash_render.py:**
  - `_MAX_EXPR_CHARS = 5000` (5571); `_floats_only` (5574-5596).
  - `GlyphMapper.map_function` (12431-12630): `_SAFE_NAMES = {"x","pi","e"}` (12476), `_OP_NODES` with Mod, FloorDiv, BitXor, BitOr, BitAnd, UAdd (12515-12519), `expr = _stata_expr_to_python(expr)` (12544), `np.linspace` (12568), `eval` (12597), `legend_label=expr[:40]` (12626).
  - `_stata_expr_to_python` (13752-13782); `_IF_EXPR_MAX_DEPTH = 300` (14192).
  - `_dash_layer_drew_anything` (24527) counts an all-NaN line as drawn. `_dash_note_empty_layer` (24576-24635) reports an empty function layer whatever the data.
  - `_dash_function_args` (24792-24818).
  - `DashRenderer.__init__` (24981; spec load and `_dash_cap_spec` 25006-25023). Saved call: `_make_figure_body` 26263-26271.
  - `ServerAppBuilder.__init__` (28268; 28275-28286).
  - Copy lists: constants tuple 28362-28497 (`"_MAX_EXPR_CHARS"` 28365); functions tuple 28535-28829 (`"_floats_only"` 28562, `"_dash_function_args"` 28575); `_shared_stat_lines` tuple ending `_stata_if_to_pandas, _stata_expr_to_python):` (28981).
  - Served template: `_dash_draw_layer` function branch (30188-30191), `_redraw` (30285-30302).

### E9. GitNexus

`mcp__gitnexus__list_repos` lists only `TYME` and `PhotoShootPlannerPro`; dash is not indexed. Task 04-01 runs `gitnexus analyze` and the mandatory impact queries.

Interim grep-based blast radius:

| Symbol | Callers |
|---|---|
| `map_function` | 2 (`_make_figure_body`, served `_dash_draw_layer`, which `_redraw` and the per-panel builder reuse) |
| `_stata_expr_to_python` | 1, plus the copy tuple |
| `_floats_only` | 1, plus the copy list and 3 test instruments |
| `DashRenderer.__init__`, `ServerAppBuilder.__init__` | every build (HIGH expected) |
| `_dash_process_segment` | 1 (`_dash_plot`) |
| `_dash_plot` | 1 (`dash`), but every graph command (HIGH expected) |
| `_dash_register_graph`, `_dash_render_immediate` | 1 each |
| `_dash_prepare_spec` | 2 (`dash build` 7414, `dash serve` 7571) |
| `_dash_item_globals` | 1 (`_dash_drop_item`) |
| `_dash_fn_refuse`, `_dash_fn_names`, `_dash_fn_space_call` | 1 each |

### E10. Tests that pin today's behaviour (flip, never delete; R7)

| Test (file::Class::test) | Pins | Flip |
|---|---|---|
| test_phase4_plots.py::TestMapFunction::test_function_y_values_correct_for_constant (:556-563) | `pi` drawn as π | `_pi`, plus a `pi` draws nothing assertion |
| test_phase4_plots.py::TestMapFunction::test_function_pi_constant_accessible (:768-775) | `sin(pi * x)` | `sin(_pi * x)` |
| test_phase4_plots.py::TestMapFunction::test_function_e_constant_accessible (:777-784) | `e * x` | `exp(1) * x` |
| test_phase4_plots.py::TestMapFunction `evaluated` fixture (:673-685) and ::test_the_eval_spy_sees_an_accepted_expression (:687-693) | spy on `dr.eval` | spy on `dash_render._stata_fn_eval` |
| test_statistical_defaults.py::TestFunctionOperatorAndDomain::test_double_star_still_works (:95-100) | `x**2` drawn | draws nothing |
| test_statistical_defaults.py::TestFunctionOperatorAndDomain::test_caret_translation_does_not_loosen_the_whitelist (:102-140) | spy on `_floats_only` | spy on `_stata_fn_eval` |
| test_server.py::TestServerFunctionExpressionOperators::test_function_power_does_not_raise (:4806) | `x ** 2` | `x^2` with drawn values asserted |
| test_server.py::TestServerFunctionExpressionOperators::test_function_complex_expr_does_not_raise (:4822) | `sin(x) + x**2 - 1` | `sin(x) + x^2 - 1` |
| test_server.py::TestServerFunctionExpressionOperators::test_function_unsafe_name_guard_in_source (:4830) | `_SAFE_NAMES`, "Unsafe name" in source | `_stata_fn_parse` and its refusal text in source |
| test_server.py::TestServerFunctionExpressionOperators::test_function_unsafe_call_guard_in_source (:4847) | `_SAFE_FUNCS`, "Disallowed function call" in source | the function-name table and its refusal text in source |
| test_server.py helper `_exec_function_app` (:4677-4710) | wraps `app_mod._floats_only` | wraps `app_mod._stata_fn_eval` |
| test_server.py::TestServerFunctionConstantExpressions::test_constant_pi_renders_glyph (:5103) | `pi` | `_pi` |
| test_server_function_security.py `_ValidatorVerdict` / `_build_and_run` / `_standalone` (:71-145) | `_floats_only` | `_stata_fn_eval` |
| test_server_function_security.py::TestAKeywordArgumentCannotExecute::test_the_emitted_validator_names_keywords (:217-237) | `node.keywords` in source | renamed `test_the_emitted_mapper_cannot_evaluate_python`: no `eval(`/`compile(` in `map_function`, `_stata_fn_parse`, `_stata_fn_eval`; parser present in `GlyphMapper` app source |
| test_server_function_security.py::TestOrdinaryFunctionPlotsStillWork::test_a_plain_expression_still_draws[2*pi*x] (:243-247) | `2*pi*x` | `2*_pi*x` |
| test_security_surface.py::TestTheFunctionExpressionWhitelist::_draw_with_eval_spy (:367-386) | spy on `dr.eval` | spy on `dr._stata_fn_eval` |
| test_security_surface.py::TestTheFunctionExpressionWhitelist::test_ordinary_expressions_still_draw[2*pi*x] (:504) | `2*pi*x` | `2*_pi*x`; `9^9^9^9` stays all-missing |
| test_resource_limits.py::TestTheServedAppHasTheSameBounds::test_the_served_evaluator_does_not_compute_integer_powers (:295-337) | `**` towers all missing | `^` forms; `x^9^9^9` and `x*9^9^9` over (1,2) are finite (u06 truth7: 4.44e70 at 1.25); `9^9^9^9`, `2^10000000`, `2^200000` stay missing; control `x^2` |
| test_adversarial_matrix.py::TestFunctionExpressionEncodings::test_a_folded_spelling_of_an_allowed_function_still_draws (:1380-1384) | full-width `sin` drawn | renamed `test_a_folded_spelling_is_refused_as_twoway_refuses_it`: draws nothing (twoway r(133), u06 truth7) |
| test_parser.cscript P1A-77 (:1461-1550) | 5000 unknown calls rc 133 (stays: N1); `unknown function ` line in log; 5000 `+ sin(x)` rc 0 | line absent (twoway prints one line); `+ sin(x)` chain is twoway's live rc (130, N2); `_dash_fn_names` scanner asserts removed with the function |
| test_parser.cscript P1A-78 (:1553-1648) | 5000 `+ (x)` rc 0 | twoway's live rc (130, N3); `_dash_fn_space_call` scanner asserts removed with the function |
| test_json_escaping.cscript JSE-47 (:2176-2185) | `function y = strlen("'x")` rc 0, stored | rc 198 as twoway (Q2), not registered |
| test_conformance.cscript C-03 control `ctl` (:203-226, 422-432) | `normal(x)` drawn empty with the note | `normal(x)` now draws; the control is a registered `function y = x` whose `$dash_fpts_ctl` is set by hand to a malformed object, drawn empty with the same note |
| test_qualifier_literals.cscript QL-20 `da5` (:724) | first error line vs twoway | re-run only (the qualifier is checked in-segment, before evaluation); no edit expected |
| function_test_map.py entries `GlyphMapper.map_function.<locals>._validate_expr_node` (:189), `_floats_only` (:573), `_stata_expr_to_python` (:600) | deleted units | removed; new units added |
| program_coverage_map.py entries `_dash_fn_refuse` (:229-230), `_dash_fn_names` (:464), `_dash_fn_space_call` (:466) | deleted units | removed; new units added |

## User stories

- **US-04.1** As a twoway user, I want `dash function y = 2^3^x` to draw 1 8 64 at x = 0 1 2, as `twoway function` does, so a pasted do-file draws the same curve.
- **US-04.2** As a twoway user, I want any expression twoway accepts (`normalden(x)`, `ln(x)`, `_pi`, `_b[weight]*x`, a scalar, a variable) to draw twoway's points, and any expression twoway refuses (`pi*x`, `x**2`, `+x`) to be refused with twoway's message and code.
- **US-04.3** As a dashboard reader, I want a function curve to stay exactly where Stata put it in the saved page and the served app, before and after every filter move.
- **US-04.4** As an analyst who sets a seed, I want `dash function y = runiform()` to draw twoway's values and leave the random-number stream where twoway leaves it.
- **US-04.5** As the maintainer, I want the renderers to draw only validated numbers for Stata-built specs and never `eval` spec text, so a function layer cannot run code.

## Business requirements

- **BR-04.1** For every expression, range and `n()` twoway accepts, the points dash draws equal twoway's serset values. y is equal in value (NaN where twoway has missing), and x equals twoway's x as a set, in generator order. This holds in the saved page and the served app, before and after any filter move.
- **BR-04.2** For every expression twoway refuses, dash refuses with twoway's return code and the line `error in expression: <the text after =>`, capped at 200 characters and shown as typed. The refusal comes at twoway's point in the command (after plot and `by()` variable checks, before graph options). Nothing is registered.
- **BR-04.3** After registering a function graph, `c(rngstate)`, `_N`, `c(changed)`, the sort order and every user variable (including one named `x`) equal what `twoway function` leaves. A Break during evaluation ends the command with r(1) and leaves the data as they were.
- **BR-04.4** A registered graph whose function points exceed one Stata macro (`c(macrolen)`) is refused with r(134), naming `n()` and `c(macrolen)`, before any registry global changes. A dashboard whose points exceed the bytes limit is refused at build with r(134), naming `dash_max_bytes`. No point is ever silently truncated.
- **BR-04.5** A spec without points (written by hand) is drawn with Stata's operator rules and missing-value rules for `x`, `_pi`, numbers, `+ - * / ^` and ten functions. Anything else draws nothing, with the existing "drew nothing" note. No spec text is passed to `eval` or `compile`.
- **BR-04.6** The help, BUGS.md and CHANGELOG state every behaviour change: grammar, refusals, fixed points, RNG, `c(changed)`, the macro limit, and the `by()` residual.

## Technical requirements

**TR-04.1 Segment capture (`_dash_process_segment`, dash.ado).**
- In the function branch (3521-3546), before the `regexr` line, add `mata: st_local("_fn_raw", strtrim(st_global("s(vals)")))`. Keep the no-expression refusals. Delete the `_dash_fn_refuse` call and its comment (3543-3545).
- In the options block, right after `_dash_opts_repeats` (3938) and before `_dash_fold_bw`/`_dash_validate_opts`, add `if "\`ptype'" == "function" mata: st_local("_fn_rtyped", st_global("s(range)"))`.
- After the options block, for `function` only, set the generator's range:
  - `_fn_lo`/`_fn_hi` are the two words of `_fn_rtyped` when it has exactly two words and `capture confirm number` succeeds on each (S4-D5);
  - otherwise the two words of the validated `s(range)`;
  - otherwise `0` and `1`.
  - `_fn_n` is `s(n)` or `300`.
- Return all of these with `c_local _seg_fnraw_out : copy local _fn_raw`, `c_local _seg_fnlo_out`, `c_local _seg_fnhi_out` and `c_local _seg_fnn_out`. The JSON keeps `"expr":"<escaped>"` unchanged (test_parser.cscript:463's `strpos` still holds).

**TR-04.2 Evaluation (`_dash_plot` and the new `_dash_fn_points`, dash.ado).**

In `program define dash`, directly before `_dash_plot \`macval(0)'` (140), add `global dash__uv = string(_caller())`.

In `_dash_plot`:
- Before the segment loop, set `local _fn_m 0`. Add `_seg_fnraw_out _seg_fnlo_out _seg_fnhi_out _seg_fnn_out` to the per-segment resets (4736-4745).
- After the plot-count line (4780), when `"\`_pt_k'" == "function"`, increment `_fn_m` and keep `_fn_k_\`_fn_m'` = `\`_dash_nplots'` (the layer's 1-based place in the plots array) and the four values by `: copy local`.
- Replace the graph-rule loop at 4848-4858 with three steps:
  1. the `by` rule alone (the same body, for `_vopt == "by"`);
  2. the function evaluation: `tempname _fp_sc _fx_raw`, `mata: st_strscalar(st_local("_fp_sc"), "")`, then for each `m` set `_fx_raw` from `_fn_raw_m` and call `_dash_fn_points \`_fx_raw' \`_fn_lo_m' \`_fn_hi_m' \`_fn_n_m' \`_fn_k_m' \`_fp_sc'`; if the scalar is non-empty, wrap it `{ ... }`; then `macro drop dash__uv`;
  3. every other graph rule (`if "\`_vopt'" == "by" continue`).

Program `_dash_fn_points raw_sc lo hi n k obj_sc` (version 16.0; placed where `_dash_fn_refuse` stood):
1. Read the raw text by value from `raw_sc`. Compute the echo text in Mata: the text after `^([A-Za-z_][A-Za-z0-9_]*)?[ \t]*=` when it matches, else the raw text; longer than 200 characters → the first 197 + `...`.
2. `mata: _dash_comma_pos(st_local("_fx_raw"), "_fx_cpos")`. If the position is not 0, print `_dash_say("err", "error in expression: ", <echo>, "")` and `exit 198` (A7).
3. `if "\`._Gr_Global.isa'" == "" ._Gr_Global = .global_g.new`, then `._Gr_Global.callerver = "\`uv'"`, where `uv` is `$dash__uv`, or `string(c(version))` when that is empty (S4-D6).
4. `if _N < \`n' preserve`, then `tempvar fy fx`, then `capture twoway__function_gen \`macval(_fx_raw)', range(\`lo' \`hi') x(x) n(\`n') generate(\`fy' \`fx')`.
5. On rc 1, `exit 1` with no echo (A8). On any other rc, echo through `_dash_say` and `exit` with that rc.
6. On success, append `"<k>":` + `_dash_fn_points_json("\`fy'", \`n', r(min), r(delta))` to `obj_sc` (comma-separated), in Mata, by value.

The expression reaches a command line only through `macval()`, and its single expansion is the generator's own (M11). Graph-level options never reach the generator.

**TR-04.3 Mata (dash_parse.mata).**
- `string colvector _dash_json_number17(real colvector v)`, beside `_dash_json_number` (1414):
  - `strtrim(strofreal(v, "%24.17g"))`;
  - missing (`v >= .`) → `null`;
  - `0` → `0`;
  - leading `.` → `0.`;
  - leading `-.` → `-0.`.
- `string scalar _dash_fn_points_json(string scalar yvar, real scalar n, real scalar x0, real scalar dx)` returns `{"x0":<x0>,"dx":<dx>,"y":[<y1>,...,<yn>]}` built from `st_data((1, n), yvar)`, joined with `invtokens(..., ",")`.
- `void _dash_fn_spec_tail(string scalar path, string scalar names, string scalar sc)`:
  - With `sc != ""`, the single entry is `"":` + `st_strscalar(sc)`.
  - Otherwise there is one entry `"<name>":` + `st_global("dash_fpts_" + name)` for each word of `names` whose global is non-empty.
  - An entry is written only when its text starts with `{`, ends with `}`, and every byte is one of `0-9 . + - e E n u l x d y " : , { } [ ]` (an `ascii()` lookup). A failing entry is skipped, and `_dash_say("txt", "dash: the function points stored for graph '", name, "' are not dash's; that layer is drawn from its expression.")` is printed.
  - Append, with `fopen(path, "a")` and `fwrite`, either `,"function_points":{<entries>}}`, or `}` when there are none.
- Delete `_dash_fn_names` (3944-3995) and `_dash_fn_space_call` (5161-5268) and their header entries (80-83, 90-93).
- Add header entries for `_dash_fn_points_json` and `_dash_fn_spec_tail` (they are dash.ado's calls). `_dash_json_number17` is internal and has no header entry.
- `_dash_item_globals` (3837): add `"dash_fpts_" + nm` to `own`.

**TR-04.4 Registry and spec writers (dash.ado).**
- `_dash_register_graph` takes a fourth scalar `fp_sc` (routing 5162 passes `\`_fp_sc'`).
  - Right after the name checks and before `_dash_graph_cap`/`_dash_drop_item`: if `strlen(st_strscalar(fp_sc)) > c(macrolen)`, display `dash: graph '<name>' holds <N> characters of function points, more than the <c(macrolen)> one Stata macro holds.`, then `      Use a smaller n(), put the function layers in separate graphs, or raise c(macrolen) with set maxvar.`, and `exit 134` (S4-D7). Read `c(macrolen)` live.
  - After the two existing `st_global` lines, set `dash_fpts_<name>` from the scalar when it is non-empty, else `capture macro drop dash_fpts_<name>`.
- `_dash_render_immediate`:
  - `args json_spec fp_sc` (routing 5165 passes `\`"\`graph_json'"' \`_fp_sc'`).
  - `master_json` (6138) loses its final `}`.
  - After `file close` (6145): `mata: _dash_fn_spec_tail(st_local("spec_json_path"), "", st_local("fp_sc"))`.
- `_dash_prepare_spec`:
  - In the graph loop (7152-7176), collect `_fp_names` (graph names only).
  - Before the writer, sum `strlen(st_global("dash_fpts_" + name))` over `_fp_names`. If the sum exceeds `_dash_limit, name(bytes)`'s `r(value)`, refuse r(134) in `_dash_byte_cap`'s words: `dash: this dashboard would embed <N> characters of function points, more than the <limit> dash embeds.` and `Use a smaller n(), or set global dash_max_bytes to a higher value (at most <ceiling>).` (formatted with `_dash_count_fmt`).
  - `master_json` (7281) loses its final `}`. After `file close` (7288): `mata: _dash_fn_spec_tail(st_local("specpath"), st_local("_fp_names"), "")`.
- `_dash_clear` (6218-6221): add `capture macro drop dash_fpts_*`.
- `_needed` (232-245): remove `_dash_fn_names _dash_fn_space_call`; add `_dash_fn_points_json _dash_fn_spec_tail`.

**TR-04.5 Spec transport, both renderers (dash_render.py).**

New module function `_dash_attach_function_points(spec) -> dict`:
- It returns a copy, never mutating its input, with `"function_points"` removed.
- For each graph dict, take the name `str((g.get("graph_options") or {}).get("name") or g.get("name") or "")`, first occurrence only. Take its table `spec["function_points"].get(name)` (a dict).
- For each key matching `^[0-9]{1,4}$` (ASCII digits only), with `1 <= k <= len(plots)` and `plots[k-1]` a dict whose `type` lower-cased is `function`, set `plots[k-1] = dict(plots[k-1], points=value)`.
- Anything else is ignored. Values are not validated here (TR-04.6 does that at draw).

Call it first, before `_dash_cap_spec`, in `DashRenderer.__init__` (after the spec load at 25007) and `ServerAppBuilder.__init__` (after 28276). The served app therefore embeds plots that already carry `points`. The helper is builder-side only and is not in the served copy lists.

**TR-04.6 Drawing stored points.**

New module function `_dash_function_points(points, n_cap=10000) -> "tuple[np.ndarray, np.ndarray] | None"`:
- `points` must be a dict.
- `x0` and `dx` must be `int`/`float`, not `bool`.
- `y` must be a list of 1..`n_cap` entries, checked by `len()` before any conversion. Each entry is `None`, or an `int`/`float` that is not a `bool`.
- Convert inside `try/except (OverflowError, TypeError, ValueError)`: `float(x0)`, `float(dx)`, `np.array([np.nan if v is None else float(v) for v in y])`.
- Return None when x0, dx or any non-None y is not finite (NaN, Infinity, 1e400, `10**400`).
- Return `x = x0 + dx * np.arange(n, dtype=float)`, or None if any x is not finite, together with `y`.

`GlyphMapper.map_function(..., color_idx=0, points=None)`:
- When `points is not None`, draw `_dash_function_points(points)`, or the empty source when it returns None. The expression is never parsed and never evaluated.
- `_make_figure_body` (26270) passes `points=plot.get("points")`. The served `_dash_draw_layer` function branch (30190) passes `points=plot.get('points')`, which also serves `_redraw` and every panel.
- `legend_label` stays the user's text `str(expr)[:40]`.
- An all-null `y` draws a NaN line in silence (`_dash_layer_drew_anything` is True), as twoway is silent. An invalid object draws the empty source, and `_dash_note_empty_layer` gives the existing note.
- Served copy: add `"_dash_function_points"` after `"_dash_function_args"` in the functions tuple (28575; R2).

**TR-04.7 Fallback evaluator (specs without points).**

Delete `_stata_expr_to_python` (13752-13782) and `_floats_only` (5574-5596), together with their copy-list entries (28981 and 28562) and the in-method `_SAFE_NAMES`/`_SAFE_FUNCS`/`_validate_expr_node`/`_OP_NODES`/`compile`/`eval`. Add three module-level items.

`_FN_EXPR_MAX_NEST = 40` goes in the constants tuple after `"_MAX_EXPR_CHARS"` (28365). Stata draws 40 nested parentheses and refuses 50 (P1, N6).

`_stata_fn_parse(text) -> tuple` parses by the measured grammar (E1). Any refusal is `ValueError`.

Grammar:

```
sum  := diff ('+' diff)*        diff := prod ('-' prod)*
prod := quot ('*' quot)*        quot := neg ('/' neg)*
neg  := '-'* pow                pow  := atom ('^' expo)*
expo := ('-' | '+')* atom       atom := NUMBER | MISSING | 'x' | '_pi' | FUNC '(' sum ')' | '(' sum ')'
```

Tokens:
- ASCII only (`text.isascii()`; NUL and non-ASCII refused).
- Blanks and tabs separate tokens.
- NUMBER is `digits[.digits][e[+-]digits]`, `.digits[...]` or `digits.`.
- MISSING is `.` or `.a`-`.z` not followed by a name character, and evaluates to NaN.
- Names are `[A-Za-z_][A-Za-z0-9_]*`. The only bare names are `x` and `_pi`. FUNC is one of `sin cos tan exp log log10 sqrt abs floor ceil`, written directly before `(` with no blank.

Refused: `pi`, `e`, `**`, `%`, `//`, `+x`, `x^`, `2x`, `sin (x)`, `sin(x,1)`, quotes, hex literals, comparisons and logic, any other name, and nesting deeper than `_FN_EXPR_MAX_NEST`.

Tree shape:
- Sign runs are counted (odd parity → `("neg", node)`).
- Chains become n-ary `("fold", op, [nodes])`, with a single operand collapsed to itself.
- `^` becomes `("pow", base, [(odd, node), ...])`.
- Constants are `("c", value)`; `x` is `("x",)`; calls are `("call", name, node)`.
- Recursion happens only at parentheses and calls, so depth is at most about 6 × 40 frames.

`_stata_fn_eval(tree, x) -> np.ndarray` evaluates under `np.errstate(all="ignore")`. Let `m(v) = where(isfinite(v), v, nan)`.
- Every fold step and call result passes through `m`.
- `^` is `where(isnan(a) | isnan(b), nan, m(np.power(a, b)))`, left to right, with each exponent's sign applied to it alone.
- Constants broadcast to `x.shape`. The function table is a local dict.
- Both functions are self-contained and import only `numpy`/`math`, which the app has. Add `"_stata_fn_parse"` and `"_stata_fn_eval"` after `"_dash_function_points"` in the functions tuple.

The `map_function` fallback path:
- If `len(text) > _MAX_EXPR_CHARS`, warn as today (the reason text loses "recursive"; it keeps "over the") and draw empty.
- Otherwise `tree = _stata_fn_parse(text)` (`ValueError` → empty source).
- The grid is `x = lo + dx*np.arange(n)` with `dx = (hi - lo)/(n - 1)`, twoway's rule (E7), not `np.linspace`.
- `y = _stata_fn_eval(tree, x)`. Keep the `if y_arr.ndim == 0` broadcast line (test_server.py:5124 pins it).

**TR-04.8 Registries.**
- `test/function_test_map.py`: remove `GlyphMapper.map_function.<locals>._validate_expr_node`, `_floats_only` and `_stata_expr_to_python`. Add `_dash_attach_function_points`, `_dash_function_points`, `_stata_fn_parse` and `_stata_fn_eval`, mapped to their `test_function_expr.py` tests. Point `GlyphMapper.map_function` (:188) at `TestStoredPoints::test_the_points_are_drawn_not_the_expression`. All in alphabetical place.
- `test/program_coverage_map.py`: remove `_dash_fn_refuse`, `_dash_fn_names` and `_dash_fn_space_call`. Add these entries:
  - `_dash_fn_points`: `("test_parser.cscript:FX-01", "test_wp29_truth.cscript:FX-20")`;
  - `_dash_fn_points_json`, `_dash_json_number17` and `_dash_fn_spec_tail`: `("test_parser.cscript:FX-10",)`, a direct Mata call case;
  - `_dash_item_globals`: add `test_parser.cscript:FX-08` to its existing tuple.

**TR-04.9 Security (rule 1).**
- **No new trust boundary.** The expression runs in Stata's generator with the one expansion twoway gives it (M11).
- **No eval of spec text.** Neither renderer evaluates spec text: Stata-built specs carry numbers only, validated twice (Mata character check on write, `_dash_function_points` on draw), and the fallback is an ASCII interpreter.
- **No generator-option injection.** It is refused (A7). The generator's own `syntax` also refuses a repeated `generate()` (Q4).
- **Inert echoes.** Echoes go through `_dash_say` (SMCL inert) and are capped at 200 characters.
- **No silent truncation.** Every size is bounded: n ≤ 10000, one graph ≤ `c(macrolen)`, the dashboard ≤ `dash_max_bytes`, text ≤ 5000 characters, nesting ≤ 40.
- **Break.** It is re-raised and the data are restored (preserve and tempvars).
- **`._Gr_Global.callerver`.** It is set exactly as every `graph` command sets it.

## Boundaries

- Do not touch:
  - `range(varname)` (still refused, dash.sthlp:1990-1994), `droplines()`, `horizontal` or `base()` on `function` (DROPIN P2/P3);
  - legend text ("Fitted values" for function is P1 legend text);
  - a date axis under function x (DROPIN P1 line 135; S05 owns date units).
- Do not port per-panel evaluation (S4-D4). Do not change `_dash_by_panels`, the facet builders or `_expand_by_groups`.
- Do not edit `_dash_json_number` (scatteri/pci values are stored as floats by twoway; `%21.0g` suffices there).
- Do not touch S02's `sort()` validation in the plot-option parse, S06's export path (dash.ado:5981-6060), or S08's private writer. S08 lands after this section and keeps the `_dash_fn_spec_tail` call.
- Do not add Stata functions to the fallback (P1.22's business; Stata-built specs no longer need them).
- Do not edit `ROADMAP.md`, `GAPS2.md`, `REMAINING.md`, `TWOWAY_COVERAGE_AUDIT.md`, `DROPIN-REMAINING.md`, `AGENTS.md`, `test/run_all_cscripts.do` or `test/test_cscript_hygiene.py` (A5, R1).
- Do not edit `ALLOWED` or `_MUST_WARN` in `test_mode_parity.py` (R6).
- No new `.cscript` file.

## Stata truth

**Fixture.** Create `scripts/extract_function_truth.do`, which writes `test/fixtures/function_expr_truth.json` (D12, R5). It is modelled on `scripts/extract_text_truth.do`.

Setup:
- The header comment states WHY, the probe method and the run line.
- `clear all`, `set more off`, `set linesize 200`.
- `global ZF_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"` (point it at the worktree while running there, and restore it before committing). `global ZF_OUT "${ZF_REPO}/test/fixtures/function_expr_truth.json"`.
- The provenance stamp is copied from extract_text_truth.do:81-95: `shell git -C ... rev-parse HEAD`, read back from a file, checked as 40 hex characters.
- The do-file runs under `version 19`.

Each probe is a do-file line `zf <id> <n> "<lo hi>" <expression text>`, run on `clear`. It records one tab-separated line per probe through Mata `fput` (never `file write` of user text). The program `zf`:
1. `capture twoway function <text>, range(<lo hi>) n(<n>) nodraw` → `rc`.
2. On rc 0, read the serset as above → `serset_x` and `serset_y` (each `%24.17g`, `.` → `null`).
3. On rc 0, run `preserve`/`tempvar`/`twoway__function_gen <text>, range(<lo hi>) x(x) n(<n>) generate(fy fx)` → `x0` = r(min), `dx` = r(delta), `gen_y` (generator order).

One trailing `python:` block reads the record file and writes `{"_meta": {stata_version, born_date, extracted, dash_commit, method}, "probes": [{id, expr, range, n, rc, x0, dx, gen_y, serset_x, serset_y}]}`. It never calls back into Stata, never uses `shell=True`, and writes a backtick as `\x60`.

Probes, all data-free (data-variable, RNG and estimation probes are live in cscripts):
- **Power and sign:** `2^3^x`, `(2^3)^x`, `2^(3^x)`, `2^3^2`, `x^x^x`, `x^2^-1`, `x^2^0.5`, `x^3^0.5`, `x^-1^-1`, `2^-1`, `2^-x`, `2^-1^2`, `2^-x^2`, `-2^-2^-2`, `2^-2^-1`, `2^+1`, `2^ - x`.
- **Unary:** `-2^2`, `-x^2`, `(-x)^2`, `-(-x)^2`, `-x^x`, `-x^-2`, `-x^-x^-1`, `- -x`, `--x`, `2*-x`, `x*-2^2`, `3-2^2`, `2^x*3`, `2*x^3`, `2--x`, `2/-x`.
- **Precedence:** `0.1*3/0.3`, `1e16+1-2`, `1+0.1-0.7`, `1e16+1+1`, `0.1*0.7*0.3`, `10-2-3`, `100/10/5`, `x/2*3`, `x-1+2`.
- **Missing:** `0^0`, `0^-1`, `(-8)^(1/3)`, `(-2)^x`, `.`, `x^.`, `(0^-1)^0+x`, `1/(1/0)+x`, `exp(-exp(1000))+x`.
- **Literals:** `1e3*x`, `.5*x`, `5.*x`.
- **Functions:** `sqrt(x-1)`, `log(x)`, `log10(x)`, `exp(x)`, `sin(x)`, `cos(x)`, `tan(x)`, `abs(-x)`, `floor(x/2)`, `ceil(x/2)`.
- **Outside the fallback:** `_pi*x`, `c(pi)*x`, `normalden(x)`, `ln(x)`, `1.8X+01*x`, `(x>1)*x`, `max(x,1)`.
- **Over range(1 2) n(5):** `9^9^9^9`, `x^9^9^9`, `x*9^9^9`, `2^10000000`, `2^200000`.
- **Grids:**
  - `x+1` range(0 1) n(300);
  - `x` range(-3.7 11.2) n(301);
  - `x/3` range(0 0.00001) n(3);
  - `1/x` range(0 1e-5) n(7);
  - `x` range(0 0.123456789012345678) n(3);
  - `x^2` range(2 0) n(3);
  - `sin(x)/x` range(-100 100) n(10000).
- **Refusals (rc only):** `pi*x`, `e*x`, `pi`, `e`, `PI`, `E`, `x**2`, `x%2`, `x//1`, `+x`, `2*+x`, `(+x)`, `x^`, `2^^x`, `ｓｉｎ(x)`, `2x`, `sin(x,1)`, `sin (x)`, `nosuch(x)`, `strlen("'x")`, `x` followed by 600 copies of `+ sin(x)`, and an 800-term `x+x+...` chain. The last two are built in the do-file.

Unless noted, each probe is written as `y = <e>` with range(0 2) n(3).

Run:

```
mkdir -p <scratch>
dash_nobrowser=1 scripts/stata_slot.sh <scratch> scripts/extract_function_truth.do
git add -f test/fixtures/function_expr_truth.json
```

**Live truth (cscript).** The block `* ==== S04 P0.6: function points are twoway's ====` goes in `test/test_wp29_truth.cscript`, above `* ==== append new blocks above this line ====`. It is gated by `local only : env WP29_ONLY` and `if inlist("\`only'", "", "S04")`, with start and end time lines, and ends with `* ==== end S04 ====`. Cases FX-20..FX-24 are listed under TDD.

Run it through the index's two-line driver:

```
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "<repo>" "<repo>" "test_wp29_truth.cscript" > <scratch>/run_test_wp29_truth.do
dash_nobrowser=1 WP29_ONLY=S04 scripts/stata_slot.sh <scratch> <scratch>/run_test_wp29_truth.do
```

Read the log; never relaunch to check. A SKIP is not a pass.

## TDD test stubs

All pytest tests below are in **`test/test_function_expr.py`** (new; task 04-04) unless noted.

- `mode` is parametrised `["saved", "served"]` through `test_mode_parity`'s `_spec`, `_standalone` and `_served` (import the module as `mp`). The function source is the ColumnDataSource whose data has `x_fn`.
- After-move cases fire the first Select with `mp._fire`, copying the filter and move of an existing `test_same_glyphs_after_the_move` case (test_mode_parity.py:2229).
- New tests that assert label text pass `var_labels` explicitly (index A7).

Every stub below marked "FAILS" fails at the batch-1 base, and its text goes in `<scratch>/04-P0.6-failure.txt`. "Guard" stubs pass at the base and are listed separately in the commit body.

**Regression tests (fail at base):**
- `TestStoredPoints::test_the_points_are_drawn_not_the_expression[mode]`: plot `{"type":"function","expr":"nosuch(x)","options":{"range":"0 2","n":"3"},"points":{"x0":0,"dx":1,"y":[1,8,64]}}` draws x `0 1 2`, y `1 8 64`. FAILS (empty).
- `TestStoredPoints::test_points_travel_beside_the_graphs[mode]`: plot expr `2^3^x` and no `points`; top-level `"function_points": {"g1": {"1": {"x0":0,"dx":1,"y":[1,8,64]}}}` draws `1 8 64`. FAILS (`2 8 512`).
- `TestStoredPoints::test_the_points_survive_a_filter_move[served]`: after a foreign move the function source still holds `1 8 64`. FAILS (`2 8 512`).
- `TestStoredPoints::test_null_points_draw_silently[mode]`: expr `nosuch(x)`, `y` `[null,null,null]` draws 3 NaN y and no "drew nothing" warning. FAILS (empty plus note).
- `TestStoredPoints::test_an_unevaluable_expression_beside_points_is_never_parsed[mode]` (A9): expr `__import__('os').system('true')` with valid points draws the points. A spy on `_stata_fn_parse` counts 0 calls (saved: `dash_render._stata_fn_parse`; served: the app module's copy, through a builder like `test_server_function_security._build_and_run`). FAILS.
- `TestHostilePoints::test_bad_points_draw_nothing[case][mode]`, expr `x`. The cases are `y` a string, `y` with `True`, `y` a dict, nested list, 10001 values, a `NaN`, `Infinity`, `1e400`, `10**400` as a JSON integer, `dx` = Infinity, no `x0`, `x0` = `True`, points a list. Each draws the empty source and exactly one "drew nothing" note, and raises nothing. FAILS (draws `x`).
- `TestAttach::test_the_transport` (unit): attaches by name and 1-based key and removes the top-level member. It does not mutate its input, ignores keys `0`, `4` (3 plots), `01x`, `١`, a non-function plot and a non-dict table, and takes the first graph of a repeated name. FAILS (AttributeError).
- `TestFunctionPoints::test_valid_and_invalid` (unit, `_dash_function_points`). FAILS.
- `TestStataGrammarFallback::test_caret_is_left_associative[mode]`: `2^3^x` → `1 8 64`. FAILS.
- `TestStataGrammarFallback::test_a_sign_after_caret_takes_one_operand[expr][mode]`: the E1 values for `2^-1^2`, `x^2^-1`, `-x^-x^-1`, `2^-x^2`, `-2^-2^-2`, `2^-2^-1`, `x^-1^-1`, `2^+1`. FAILS.
- `TestStataGrammarFallback::test_division_binds_tighter_than_multiplication[mode]`: `0.1*3/0.3` `== 1.0` exactly. FAILS.
- `TestStataGrammarFallback::test_subtraction_binds_tighter_than_addition[mode]`: `1e16+1-2 == 1e16` and `1+0.1-0.7 == 0.40000000000000002`, exactly. FAILS.
- `TestStataGrammarFallback::test_what_twoway_refuses_draws_nothing[expr][mode]`: `pi*x`, `e*x`, `pi`, `e`, `PI`, `E`, `x**2`, `x%2`, `x//1`, `+x`, `2*+x`, `(+x)`, `x^`, `2^^x`, `ｓｉｎ(x)`, `2x`, `sin(x,1)`, `sin (x)` each draw empty with one note. FAILS for those drawn at base.
- `TestStataGrammarFallback::test_underscore_pi_is_statas_pi[mode]`: `_pi*x` → `0, π, 2π`. FAILS.
- `TestStataGrammarFallback::test_missing_propagates_as_in_stata[expr][mode]`: `x^.`, `.`, `(0^-1)^0+x`, `1/(1/0)+x`, `exp(-exp(1000))+x` draw all-NaN, silent. FAILS.
- `TestAgainstTheFixture::test_every_stored_probe[mode]`: for each rc-0 probe, points `{x0, dx, gen_y}` draw `y == gen_y` (NaN-equal) and `sorted(x) == serset_x`. FAILS (points ignored).
- `TestAgainstTheFixture::test_every_fallback_probe[mode]`, for each probe:
  - if `_stata_fn_parse` accepts it, assert `rc == 0` (the fallback never accepts what twoway refuses), and the drawn y equals `gen_y`;
    - exactly for probes whose text holds no `^` and no function;
    - otherwise `np.testing.assert_allclose(rtol=1e-15, atol=0)`, NaN-equal;
  - if it refuses, the probe is either rc ≠ 0 or in `_FALLBACK_UNSUPPORTED` (`c(pi)*x`, `normalden(x)`, `ln(x)`, `1.8X+01*x`, `(x>1)*x`, `max(x,1)`), and it draws empty with one note.
  - FAILS.
- `TestTheParser::test_power_nests_left`, `::test_sign_binds_one_atom`, `::test_precedence_levels`, `::test_ascii_names_only`, `::test_numbers_and_missing` (tree shapes) and `::test_refusals` (ValueError list). FAILS (AttributeError).
- `TestTheParserIsBounded::test_long_chains_do_not_recurse`: a 2,400-term `x+x+...` (4,799 characters) evaluates in under 1 s with no RecursionError. `'-'*4999 + 'x'` gives `-x`. FAILS.
- `TestTheParserIsBounded::test_nesting_is_capped`: 40 nested parentheses draw, 41 draw empty with a note. FAILS.
- `TestNoEval::test_the_mapper_cannot_evaluate_python`: no `eval(` and no `compile(` in `inspect.getsource` of `GlyphMapper.map_function`, `_stata_fn_parse` and `_stata_fn_eval`. FAILS.

**Guards (pass at base; kept):**
- `TestStoredPoints::test_the_points_survive_a_filter_move[saved]`: the function source's id appears in no `CustomJS.args` value of the rendered document.
- `TestStoredPoints::test_x_is_rebuilt_exactly`: for each rc-0 probe, `float(x0) + float(dx)*np.arange(n)` sorted equals `serset_x` as floats.
- `TestTheFixture::test_meta_keys`: `_meta` has `stata_version`, `born_date`, `dash_commit`, `extracted`.
- `TestStataGrammarFallback::test_unary_minus_binds_looser_than_caret[mode]`: `-2^2`, `-x^2`, `3-2^2`, `x*-2^2`, `2--x`, `2/-x`.

**cscript, `test/test_parser.cscript`** (appended as one run after the last case block; each case prints `FX-nn PASS`; the cases fail at base where marked):

- **FX-01 refusals.** For each of `pi*x`, `e*x`, `pi`, `e`, `PI`, `E`, `x**2`, `x%2`, `x//1`, `+x`, `2*+x`, `(+x)`, `x^`, `2^^x`, `ｓｉｎ(x)`, `2x`, `sin(x,1)`, `sin (x)`, `nosuch(x)` and `x` followed by 600 copies of `+ sin(x)`, run `capture twoway function y = <e>, range(0 2) nodraw`. Then `_p1a_logrun dash function y = <e>, range(0 2) name(fx01)`. dash's rc equals twoway's (read live), the registry is empty, and the log holds `error in expression: ` exactly once. The same holds for `(function y = x**2) (scatter mpg weight)` and `scatter mpg weight || function y = pi*x`. FAILS (rc 0 for most).
- **FX-02 order.** G1-G8, M8b, M8c and N7 (E3). dash's rc equals twoway's, and `c(rngstate)` after dash equals twoway's after the same command from the same seed. FAILS (M8b and M8c give 133; G2, G3 and N7 do not move the RNG).
- **FX-03 RNG.** `set seed 42`, `twoway function y=runiform(), nodraw`, `s1 = c(rngstate)`; `set seed 42`, `dash function y=runiform(), name(fx03)` gives `c(rngstate) == s1`. FAILS.
- **FX-04 data.** Each of the following matches twoway's state after the same command:
  - On auto (`_N >= n`) and on `clear; set obs 2` (`_N < n`): `datasignature`, `_N`, `c(changed)` and `: sortedby` after registration and after a refused one. (K1-K4: `c(changed)` is 1 for `_N >= n`, 0 otherwise.)
  - A user variable `x` (`gen x = 99`) is unchanged.
  - `clear; set obs 5` (no variables) gives `_N == 0` after both (M3).
  - With a variable `pi` in memory, `function y = pi*x` registers rc 0, as twoway draws it.
  - FAILS (`c(changed)` and the varless `_N`).
- **FX-05 echo.** `function y = nosuch(x) + {bf:BOLD}` is refused r(133) and the log holds `{bf:BOLD}` as typed. The first error line equals twoway's for `y = nosuch(x)`, `y=nosuch(x)` and `nosuch(x)` (N8/N9; two blanks versus one). A 5000-call expression shows its first 197 characters of the text after `=`, then `...`, and r(133). FAILS (extra line; rc for the `+ sin(x)` form).
- **FX-06 hostile.**
  - (a) A string scalar holding `y = x, generate(mpg weight, replace)` handed to `_dash_fn_points` directly is r(198); `mpg` and `weight` exist after.
  - (b) Break: `capture program drop twoway__function_gen` and define an in-memory stub that does `exit 1`. `dash function y = x, name(fx06)` is then rc 1, no `error in expression` is in the log, data signature and `_N` are unchanged, and nothing is registered. Drop the stub afterwards.
  - FAILS ((a): `_dash_fn_points` does not exist; (b): rc 0 at base).
- **FX-07 size.**
  - Four layers of `y = sin(x)/x, range(-100 100) n(10000)` in one graph, `name(fx07)`, are r(134). The log names `n()` and the value of `c(macrolen)`. `dash_graph_registry` is unchanged and there is no `$dash_fpts_fx07`.
  - The same four layers in the one-line form, `saving(<tmp>.html) replace`, are rc 0 (no macro is involved).
  - One such layer, `name(fx07b)`, registers and builds saved and served rc 0.
  - With `clear`, a function n(300) registered, and `global dash_max_bytes 1000`, `dash build` is r(134) naming `dash_max_bytes` (then reset the global).
  - FAILS.
- **FX-08 registry.**
  - `$dash_fpts_fx08` exists after `dash function y = x, name(fx08)`.
  - It is gone after `dash scatter mpg weight, name(fx08, replace)`, after a KPI replacing a function graph, and after `dash clear`.
  - A non-function graph never sets one.
  - A hand-set `$dash_fpts_g` holding `}],"graphs":[` is skipped at build with dash's note, and the page builds.
  - FAILS.
- **FX-09 expansion and version.**
  - `global FXG 3` with `dash function y = \$FXG*x, range(0 2) n(3)` stores y `0,3,6` (M11).
  - `version 17: dash function y = x, name(fx09)` leaves `._Gr_Global.callerver == "17"`.
  - FAILS.
- **FX-10 Mata units.** `_dash_json_number17((0, -0, .5, -.5, 1/3, ., .a, 1e21)')` gives `0, 0, 0.5, -0.5, 0.33333333333333331, null, null, 1.00000000000000000e+21`. `_dash_fn_points_json` on a 3-row tempvar gives the exact text. `_dash_fn_spec_tail` on a tempfile holding `{"a":1` gives `{"a":1}` with no entries, and `{"a":1,"function_points":{"":{...}}}` with a scalar. FAILS (functions absent).

**cscript truth, `test/test_wp29_truth.cscript` block S04:**

- **FX-20 battery.** For 20 fixture expressions (E1's table), the following must equal twoway's: `dash function y=<e>, range(0 2) n(3) name(fxK)`; `$dash_fpts_fxK`'s y, parsed in Mata (`strtoreal` of the tokens between `"y":[` and `]`, `null` → `.`), against twoway's serset y, exactly; and `x0`/`dx` against `twoway__function_gen`'s `r(min)`/`r(delta)`. Then `dash build, saving()` and `dash build, server`: a `python:` block executes the app's `make_document` and reads the function source. Those values equal the serset values, passed in as a Stata matrix. FAILS.
- **FX-21 Stata-only.** Each of `regress mpg weight` with `y=_b[_cons]+_b[weight]*x, range(1760 4840)`; `scalar s=2` with `y=s*normalden(x)`; `y=ln(x), range(0.5 2)`; `y=c(pi)*x`; and, with a variable `educ = 7` in memory, `y = educ*x` has points equal to twoway's serset, and builds saved and served with drawn points. FAILS.
- **FX-22 version.** `version 13: set seed 1` followed by `version 13: dash function y=runiform(), n(3) name(fx22)` gives points equal to the `version 13: twoway` serset (kiss32), and the same `c(rngstate)`. FAILS.
- **FX-23 descending and precision.** `range(2 0)`: dash stores `x0=2 dx=-1 y=4,1,0`, and the drawn polyline equals twoway's (M16). `range(0 0.123456789012345678)`: y[3] `== 0.12345678901234568` (S4-D5). FAILS.
- **FX-24 by() residual.** `set seed 1` and `dash function y=runiform(), range(0 2) n(3) by(foreign, total) name(fx24)` gives points equal to twoway's first panel serset (draws 1-3). `c(rngstate)` equals the state after 3 draws, where twoway's is after 9 (J2). This pins the documented residual. FAILS (no points at base).

**Mutation table:**

| Break this | Test that must die |
|---|---|
| fold `^` right to left in `_stata_fn_parse` | `test_caret_is_left_associative`, `test_every_fallback_probe` |
| drop the `isnan` check in `^` | `test_missing_propagates_as_in_stata[x^.]` |
| `%21.0g` in `_dash_json_number17` | `test_every_stored_probe` via FX-20 (`x/3` probe), FX-10 |
| evaluate before the `by` rule | FX-02 (G8 RNG moved) |
| evaluate after all graph rules | FX-02 (G3 RNG not moved) |
| keep a pre-check of every layer | FX-02 (N7) |
| skip `preserve` when `_N < n` | FX-04 (`_N` grows) |
| no `macro drop dash_fpts_<name>` on replace | FX-08 |
| check `c(macrolen)` after `st_global` | FX-07 (truncated global) |
| `points=` not passed in the served branch | `test_the_points_survive_a_filter_move[served]` |
| attach after `_dash_cap_spec` with 0-based keys | `TestAttach::test_the_transport` |
| `np.linspace` in the fallback grid | `test_every_fallback_probe` on `x` over range(-3.7 11.2) n(301) |

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Stored points drawn and never evaluated | pytest | none | yes |
| Transport through `function_points` | pytest | none | yes |
| Points after a filter move | pytest (served fire; saved CustomJS scan) | none | yes |
| Hostile points | pytest | none | yes |
| Fallback grammar, refusals, missing rules, bounds | pytest | none | yes |
| Every fixture probe, stored and fallback | pytest | function_expr_truth.json | yes |
| No `eval`/`compile` in the mapper | pytest | none | n/a |
| Refusal codes and messages vs twoway, live | test_parser.cscript FX-01, FX-05 | none (Stata) | n/a |
| Check order and RNG vs twoway, live | FX-02, FX-03 | none | n/a |
| Data integrity, Break, injection | FX-04, FX-06 | none | n/a |
| Size refusals, registry hygiene, writer | FX-07, FX-08, FX-10 | none | yes (FX-07 builds both) |
| Points equal twoway's serset, built pages | test_wp29_truth.cscript FX-20..FX-24 | none (Stata computes) | yes |
| Parity guard | test_mode_parity.py CORPUS: "function with stored points" (`2^3^x` with points `1 8 64`) and "function points under by()" | none | yes |
| Pins flipped | the files of E10 | — | yes |

**Acceptance criteria:**
- **AC-04.1** `python3 -m pytest test/test_function_expr.py test/test_phase4_plots.py test/test_statistical_defaults.py test/test_server.py test/test_server_function_security.py test/test_security_surface.py test/test_resource_limits.py test/test_adversarial_matrix.py test/test_mode_parity.py test/test_function_test_map.py test/test_program_coverage_map.py test/test_file_headers.py test/test_no_orphans.py test/test_fixtures_are_committed.py test/test_statistical_helpers.py -q` passes with no new skips.
- **AC-04.2** The S04 block of `test_wp29_truth.cscript` prints `FX-20 PASS`..`FX-24 PASS` under `WP29_ONLY=S04`. `test_parser.cscript` prints `FX-01 PASS`..`FX-10 PASS` and keeps every earlier PASS. JSE-47, C-03 and QL-20 pass.
- **AC-04.3** `grep -c "_stata_expr_to_python\|_floats_only\|_dash_fn_refuse\|_dash_fn_names\|_dash_fn_space_call" dash_render.py dash.ado dash_parse.mata` prints 0 for each file.
- **AC-04.4** For P0.6:
  - BUGS.md's P0.6 entry is `- [x]` with `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.6). ...`;
  - `grep -c '<!-- WP-29 P0.6 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-29, P0.6)' CHANGELOG.md` prints 2;
  - `WP29_OPEN` has no `"P0.6"` key;
  - `python3 -m pytest test/test_tracking_documents.py -q` passes.

## Tasks

**Commit boundary.**
- One commit (P0.6) holds tasks 04-03 to 04-17. Its subject is `Evaluate function layers with Stata's own generator (WP-29 P0.6)`.
- 04-17 makes it on branch `wp29-s04` in `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp29-s04`, after the section's one full pytest run there.
- The body opens with `<scratch>/04-P0.6-failure.txt`. It then carries:
  - one `Regression: test/<file>::<Class>::<test> -- failed at <batch-1-base sha> with <text>` line per regression test;
  - `Guard:` lines for the guard tests;
  - the `Flipped:` lines from `<scratch>/04-flips.txt`;
  - `Fixture: test/fixtures/function_expr_truth.json (scripts/extract_function_truth.do)`;
  - `Security:` lines naming each threat closed (G9);
  - `BUGS.md: "<the P0.6 title S01 wrote>" (closed)`.
- No AI reference anywhere.
- Every Stata run is `scripts/stata_slot.sh <scratch> <file>.do` with `dash_nobrowser=1`, and every cscript goes through the two-line driver.
- `<scratch>` is this section's scratch directory outside the repository, for example `/private/tmp/dash-s04`. `<repo>` in the driver is the worktree root.

<task type="auto" id="04-01">
  <name>Index the tree and measure impact</name>
  <files>none</files>
  <action><![CDATA[
    In the worktree root run `gitnexus analyze` (dash is not indexed: `list_repos` shows only TYME and PhotoShootPlannerPro) and note the repo name it reports. Run `gitnexus_impact({target, direction: "upstream", repo})` for `map_function`, `_stata_expr_to_python`, `_floats_only`, `_make_figure_body`, `_generate_app_source`, `DashRenderer.__init__` (file_path dash_render.py, kind Method) and `ServerAppBuilder.__init__`. For the Stata and Mata units the index may not parse (`_dash_plot`, `_dash_process_segment`, `_dash_register_graph`, `_dash_render_immediate`, `_dash_prepare_spec`, `_dash_clear`, `_dash_item_globals`, `_dash_fn_refuse`, `_dash_fn_names`, `_dash_fn_space_call`), record `grep -n "\b<name>\b" dash.ado dash_parse.mata` callers instead (Evidence E9 lists them). Write every result (direct callers, processes, risk) to `<scratch>/04-impact.txt`.
  ]]></action>
  <verify><![CDATA[`<scratch>/04-impact.txt` exists and holds one block per symbol with a risk level or a grep count; `grep -c "risk" <scratch>/04-impact.txt` is at least 7.]]></verify>
  <done>The blast radius of every symbol this section edits was recorded before any edit.</done>
</task>

<task type="checkpoint" id="04-02">
  <name>Approve any HIGH impact before editing</name>
  <files>none</files>
  <action><![CDATA[
    If `<scratch>/04-impact.txt` shows HIGH or CRITICAL for any symbol (expected for `DashRenderer.__init__`, `ServerAppBuilder.__init__` and, by grep, `_dash_plot`), report the list to the maintainer with this section's mitigation (TR-04.5: one call added before `_dash_cap_spec`; TR-04.2: one block replaces the graph-rule loop) and wait for approval. With none, record "no HIGH/CRITICAL" in the file and continue.
  ]]></action>
  <verify><![CDATA[The maintainer's approval (or the "no HIGH/CRITICAL" line) is recorded in `<scratch>/04-impact.txt`.]]></verify>
  <done>Every HIGH or CRITICAL blast radius was reported and approved before editing.</done>
</task>

<task type="auto" id="04-03">
  <name>Extract twoway's function truth</name>
  <files>scripts/extract_function_truth.do, test/fixtures/function_expr_truth.json</files>
  <action><![CDATA[
    Create `scripts/extract_function_truth.do` exactly as "Stata truth" specifies: header, `global ZF_REPO` pointed at the worktree for this run, the D12 stamp copied from `scripts/extract_text_truth.do:81-95`, the `zf` program (twoway `capture`, serset read through `.Graph.plotregion1.plot1.serset.id`, a direct `twoway__function_gen` under `preserve` with tempvars for `x0`/`dx`/`gen_y`, every number `%24.17g` with missing as `null`, records written by Mata `fput`), every probe listed, and one trailing `python:` block that writes `test/fixtures/function_expr_truth.json` (`json.dump(..., indent=2, sort_keys=True)`). Run it with `dash_nobrowser=1 scripts/stata_slot.sh <scratch> scripts/extract_function_truth.do`, read the log, restore `ZF_REPO` to the main checkout path, and `git add -f test/fixtures/function_expr_truth.json`.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/function_expr_truth.json'));p={q['expr']:q for q in d['probes']};print(sorted(d['_meta']));print(p['y = 2^3^x']['gen_y'], p['y = pi*x']['rc'], p['y = x**2']['rc'], p['y = ｓｉｎ(x)']['rc'])"` prints `['born_date', 'dash_commit', 'extracted', 'method', 'stata_version']` and `['1', '8', '64'] 111 198 133`; `git ls-files test/fixtures/function_expr_truth.json` prints the path.]]></verify>
  <done>twoway's points, generator parameters and return codes for every probe were written to a stamped fixture and staged with git add -f.</done>
</task>

<task type="auto" id="04-04">
  <name>Write the failing Python tests</name>
  <files>test/test_function_expr.py</files>
  <action><![CDATA[
    Create `test/test_function_expr.py` with every pytest test of "TDD test stubs" under exactly those class and test names, using `test_mode_parity` (`_spec`, `_standalone`, `_served`, `_fire`) for both modes, `pytest.fail` (never skip) when the fixture is missing, and `_FALLBACK_UNSUPPORTED` as a module set. Where a unit under test does not exist yet, reach it as `getattr(dash_render, "<name>")` inside the test so collection never errors. Run `python3 -m pytest test/test_function_expr.py -q -n0 -p no:cacheprovider` on the unmodified tree. Do not commit. Save the run's failure lines to `<scratch>/04-P0.6-failure.txt`, including `[2.0, 8.0, 512.0]` for `2^3^x` and the drawn `pi*x`. Write the guard tests' names to `<scratch>/04-guards.txt`.
  ]]></action>
  <verify><![CDATA[The run reports failures for every stub marked FAILS and passes only the four guards; `grep -c "512" <scratch>/04-P0.6-failure.txt` is at least 1; no collection error.]]></verify>
  <done>Every Python regression test of P0.6 existed and failed for its recorded reason at the batch base, with nothing committed.</done>
</task>

<task type="auto" id="04-05">
  <name>Write the failing cscript cases</name>
  <files>test/test_parser.cscript, test/test_wp29_truth.cscript</files>
  <action><![CDATA[
    Append FX-01..FX-10 to `test/test_parser.cscript` as one contiguous run after its last case block (R1), each case built on the script's `_p1a_logrun`, comparing with twoway live in the same session state and displaying `FX-nn PASS`. Append the S04 block (FX-20..FX-24) above `* ==== append new blocks above this line ====` in `test/test_wp29_truth.cscript`, gated on `WP29_ONLY`. Run both through the two-line driver (`WP29_ONLY=S04` for the truth script) against the unmodified tree and append each failing case's first error line to `<scratch>/04-P0.6-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c "FX-[0-9]* PASS" <scratch>/run_test_parser.log` is less than 10 and every earlier P1A case still prints PASS up to the first FX failure; `<scratch>/04-P0.6-failure.txt` names FX-01 and FX-20.]]></verify>
  <done>Every Stata-side regression case of P0.6 existed and failed at the batch base, with its failure recorded.</done>
</task>

<task type="auto" id="04-06">
  <name>Add the Mata points writer</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    In `dash_parse.mata` add `_dash_json_number17` beside `_dash_json_number` (1414), and `_dash_fn_points_json` and `_dash_fn_spec_tail` where `_dash_fn_names` stands (3944), exactly as TR-04.3 specifies, each with a comment stating its rule and the measurement it rests on (E7). Add `"dash_fpts_" + nm` to `_dash_item_globals` (3837) and update its comment. Add the two header entries in the Public API list (lines 20-260) and the two names to `_needed` in `dash.ado` (232-245). Add the three units to `test/program_coverage_map.py` (TR-04.8).
  ]]></action>
  <verify><![CDATA[FX-10 prints `FX-10 PASS` through the driver; `python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py -q -n0` passes.]]></verify>
  <done>Mata wrote a function layer's points in a form that reads back to the same doubles and appended them to a spec file.</done>
</task>

<task type="auto" id="04-07">
  <name>Evaluate each layer with the generator</name>
  <files>dash.ado, dash_parse.mata, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-04.1 in `_dash_process_segment` and TR-04.2 in `program define dash` (140) and `_dash_plot` (the resets 4736-4745, the capture after 4780, and the three-step replacement of 4848-4858). Write `_dash_fn_points` where `_dash_fn_refuse` stands (5421-5501), and delete `_dash_fn_refuse` and its comment block. Delete `_dash_fn_names` (3944-3995) and `_dash_fn_space_call` (5161-5268) from `dash_parse.mata`, with their header entries and their `_needed` words. Remove their three entries from `test/program_coverage_map.py` and add `_dash_fn_points` (TR-04.8).
  ]]></action>
  <verify><![CDATA[Through the driver, FX-01 to FX-06 print PASS; `python3 -m pytest test/test_no_orphans.py test/test_file_headers.py test/test_program_coverage_map.py -q -n0` passes.]]></verify>
  <done>Every function layer was evaluated by twoway's generator at twoway's point in the command, refusing exactly as twoway refuses and leaving RNG and data as twoway leaves them.</done>
</task>

<task type="auto" id="04-08">
  <name>Store and write the points</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-04.4. Give `_dash_register_graph` its fourth scalar argument, with the `c(macrolen)` refusal before `_dash_graph_cap` and the set-or-drop of `dash_fpts_<name>` after the existing two globals. Give `_dash_render_immediate` `args json_spec fp_sc` and route both calls (5162, 5165) with `_fp_sc`. In both writers (6138/6143-6145 and 7281/7286-7288) remove the final `}` of `master_json` and call `_dash_fn_spec_tail` after `file close`. Add the points-size check against the bytes limit in `_dash_prepare_spec`, and `capture macro drop dash_fpts_*` in `_dash_clear`.
  ]]></action>
  <verify><![CDATA[Through the driver, FX-07, FX-08, FX-09 and FX-10 print PASS, and FX-20's registry half (stored y equal to twoway's serset) passes; its build half waits for 04-09.]]></verify>
  <done>Each registered graph's points lived in one bounded global and reached the spec file beside the graphs, never through a macro concatenation.</done>
</task>

<task type="auto" id="04-09">
  <name>Draw stored points in both renderers</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Add `_dash_attach_function_points` (TR-04.5) and call it first in `DashRenderer.__init__` (after 25007) and `ServerAppBuilder.__init__` (after 28276), before `_dash_cap_spec`. Add `_dash_function_points` (TR-04.6) and the `points=None` keyword to `GlyphMapper.map_function`, drawing the points and never touching the expression when they are given. Pass `points=plot.get("points")` at `_make_figure_body` (26270) and in the served template's function branch (30190). Insert `"_dash_function_points"` after `"_dash_function_args"` in the functions tuple (28575). Add both helpers to `test/function_test_map.py` and point `GlyphMapper.map_function` at `TestStoredPoints::test_the_points_are_drawn_not_the_expression`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_expr.py -q -n0 -k "TestStoredPoints or TestHostilePoints or TestAttach or TestFunctionPoints or test_every_stored_probe"` passes; `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" -q -n0` passes.]]></verify>
  <done>Both renderers drew a function layer's stored points exactly, before and after a filter move, and drew a bad points object as an empty, noted layer.</done>
</task>

<task type="auto" id="04-10">
  <name>Replace the fallback with Stata's grammar</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-04.7. Delete `_stata_expr_to_python` (13752-13782) and `_floats_only` (5574-5596), their entries in the `_shared_stat_lines` tuple (28981) and the functions tuple (28562), and the in-method validator, name tables, `compile` and `eval` of `map_function`. Add `_FN_EXPR_MAX_NEST` after `"_MAX_EXPR_CHARS"` in the constants tuple (28365), and `_stata_fn_parse` and `_stata_fn_eval` after `"_dash_function_points"` in the functions tuple. Use twoway's grid rule in the fallback, keep the `ndim == 0` broadcast and the over-length warning ("over the"), and rewrite the docstring to describe `points=` and the fallback's grammar and names (no `pi`, no `e`). Update `test/function_test_map.py` (TR-04.8).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_expr.py -q -n0` passes completely; `grep -c "_stata_expr_to_python\|_floats_only" dash_render.py` prints 0; `python3 -m pytest test/test_function_test_map.py -q -n0` passes.]]></verify>
  <done>A spec without points was drawn by Stata's operator and missing-value rules, and no spec text reached eval or compile in either renderer.</done>
</task>

<task type="auto" id="04-11">
  <name>Flip the pinned mapper and server tests</name>
  <files>test/test_phase4_plots.py, test/test_statistical_defaults.py, test/test_server.py</files>
  <action><![CDATA[
    Flip, with a comment naming WP-29 P0.6 and the measured twoway value, every pin of E10 in these three files: the `pi`, `sin(pi * x)` and `e * x` tests; the `evaluated` fixture re-pointed to `dash_render._stata_fn_eval`; `test_double_star_still_works` (now draws nothing); the `_floats_only` spy in `test_caret_translation_does_not_loosen_the_whitelist`; and the `x ** 2`, complex-expression, source-guard, `_exec_function_app` spy and `pi` constant tests in `test_server.py`. Assert drawn values where a test only counted renderers. Record one `Flipped: <node> -- <old expectation> was wrong because <why>` line per flipped assertion in `<scratch>/04-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_phase4_plots.py test/test_statistical_defaults.py test/test_server.py -q` passes; `python3 -m pytest --collect-only -q test/test_phase4_plots.py test/test_statistical_defaults.py test/test_server.py | tail -1` reports no fewer tests than at the batch base.]]></verify>
  <done>Every mapper and server test that pinned Python's grammar pinned twoway's, re-pointed to the new acceptance point, with no test deleted.</done>
</task>

<task type="auto" id="04-12">
  <name>Flip the security instruments</name>
  <files>test/test_server_function_security.py, test/test_security_surface.py, test/test_adversarial_matrix.py</files>
  <action><![CDATA[
    Re-point `_ValidatorVerdict`, `_build_and_run` and `_standalone` from `_floats_only` to `_stata_fn_eval` (the app module's own copy when served). Rename and flip `test_the_emitted_validator_names_keywords` to `test_the_emitted_mapper_cannot_evaluate_python` (E10). Change `2*pi*x` to `2*_pi*x` in both files. Re-point `_draw_with_eval_spy` to `dr._stata_fn_eval`. Rename and flip the full-width `sin` test to `test_a_folded_spelling_is_refused_as_twoway_refuses_it`. Add each to `<scratch>/04-flips.txt` with its old node id.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_server_function_security.py test/test_security_surface.py test/test_adversarial_matrix.py -q` passes, and `test_the_verdict_count_sees_an_accepted_expression` still asserts exactly one accepted expression in both modes.]]></verify>
  <done>Every security test kept its assertion against the new evaluator, and its positive controls still proved the instruments live.</done>
</task>

<task type="auto" id="04-13">
  <name>Flip the resource pin and add parity cases</name>
  <files>test/test_resource_limits.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Rewrite the towers of `test_the_served_evaluator_does_not_compute_integer_powers` in Stata's `^`. `x^9^9^9` and `x*9^9^9` over (1,2) are now asserted finite and equal to the fixture's `gen_y`, while `9^9^9^9`, `2^10000000` and `2^200000` stay all missing under 5 s; the control becomes `x^2`. Record the flip. Append two CORPUS cases to `test/test_mode_parity.py`: "function with stored points" (`2^3^x`, points `1 8 64`) and "function points under by()". Leave `ALLOWED` and `_MUST_WARN` untouched (R6).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_resource_limits.py test/test_mode_parity.py -q` passes, including `test_same_glyphs_after_the_move` for the new cases.]]></verify>
  <done>The resource pin asserted Stata's left-associative overflow, and the parity guard covered stored points in both modes and after a move.</done>
</task>

<task type="auto" id="04-14">
  <name>Flip the pinned cscript cases</name>
  <files>test/test_parser.cscript, test/test_json_escaping.cscript, test/test_conformance.cscript</files>
  <action><![CDATA[
    In P1A-77, assert that the `unknown function ` line is absent, assert twoway's live rc for the 5000-term `+ sin(x)` expression, re-measure the 197-character needle on the text after `=`, and remove the `_dash_fn_names` scanner asserts (the function is gone). In P1A-78, assert twoway's live rc for the 5000-term `+ (x)` expression and remove the `_dash_fn_space_call` asserts. Flip JSE-47's `jg_q5` to twoway's rc 198 with `jg47f` not registered. Replace the C-03 control `ctl` with a registered `dash function y = x, range(0 10) name(ctl)` followed by `mata: st_global("dash_fpts_ctl", `"{"1":{"x0":0,"dx":1,"y":"bad"}}"')`, so the page reports `dash: graph 'ctl' plot 1 (function) drew nothing.`, and update its comment. Record every flip in `<scratch>/04-flips.txt`.
  ]]></action>
  <verify><![CDATA[Through the driver, the logs of `test_parser.cscript`, `test_json_escaping.cscript` and `test_conformance.cscript` each contain no ` FAIL` and no `^r([0-9]*);`, and print P1A-77, P1A-78, JSE-47 and C-03 PASS.]]></verify>
  <done>The certification cases that pinned the old evaluator asserted twoway's codes and messages, and C-03 still proved the empty-layer report reaches the log.</done>
</task>

<task type="auto" id="04-15">
  <name>Certify every area script in Stata</name>
  <files>test/test_wp29_truth.cscript</files>
  <action><![CDATA[
    Run through the driver, one at a time and reading each log: `test_wp29_truth.cscript` (`WP29_ONLY=S04`), `test_parser.cscript`, `test_json_escaping.cscript`, `test_conformance.cscript`, `test_qualifier_literals.cscript`, `test_registry_collision.cscript`, `test_clear_registry.cscript`, `test_program_coverage.cscript`, `test_env_guards.cscript`, `test_caller_version.cscript`, `test_help_claims_2.cscript`, `test_help_claims_6.cscript`, `test_varlist_expansion.cscript`, `test_option_validation.cscript`, `test_resource_limits.cscript` and `test_abbreviations.cscript`. Fix the code, not a test, for any red case outside E10's list. Only the S04 block may be edited here.
  ]]></action>
  <verify><![CDATA[`grep -c "FX-2[0-4] PASS" <scratch>/run_test_wp29_truth.log` prints 5; every listed log has no ` FAIL`, no `^r([0-9]*);` and no `SKIP`, and `c(python_exec)` was set (a SKIP is not a pass).]]></verify>
  <done>Stata itself certified that dash's stored and drawn points equal twoway's, and every certification script touching function, the registry or the spec writer stayed green.</done>
</task>

<task type="auto" id="04-16">
  <name>Rewrite the help for function</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Replace the Functions paragraph (338-347) with two paragraphs. The first states that Stata evaluates the expression with twoway's generator at registration and that twoway's grammar applies, giving twoway's refusals with codes. The second states that the points are fixed (data, estimates and filter moves do not move them), that `runiform()` advances the stream and the data are marked changed when they have at least `n()` observations, that `by()` evaluates once (twoway once per panel; only random draws differ), and that a hand-written spec without points is evaluated by dash with the listed operators and ten functions, drawing anything else empty with a note. Add `{cmd:$dash_fpts_}{it:name}` to the globals sentence (424) and the `dash clear` list (809). Add to the `n()` entry (1972-1976) that one graph's function points must fit in `c(macrolen)` characters (645,200 by default; `set maxvar` raises it), or the graph is refused with r(134). Grep `test/test_help_claims_*.py` and `test/test_help_claims_*.cscript` for any sentence you changed and update the pins.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_help_claims_1.py test/test_help_claims_6.py test/test_help_conformance.py -q` passes; `grep -c "does not evaluate draws nothing" dash.sthlp` prints 0; `grep -c "dash_fpts_" dash.sthlp` prints 2.]]></verify>
  <done>The help described what function draws and refuses, when its points are fixed, the RNG and data side effects, the by() residual and the size limit.</done>
</task>

<task type="auto" id="04-17">
  <name>Close P0.6 and commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    In BUGS.md close S01's P0.6 entry in place: `- [ ]` becomes `- [x]`, and the Resolution reads `- Resolution: Fixed <ddmonyyyy> (WP-29, P0.6). function layers are evaluated at registration by twoway__function_gen (dash.ado _dash_fn_points, after the plot and by() checks, before the graph options); their points are stored in $dash_fpts_<name>, written beside the graphs by _dash_fn_spec_tail, and drawn by both renderers without evaluating the expression (_dash_attach_function_points, _dash_function_points); a spec without points is drawn by _stata_fn_parse/_stata_fn_eval with Stata's grammar and missing rules. Pinned by test/test_function_expr.py::TestStataGrammarFallback::test_caret_is_left_associative, ::TestStoredPoints::test_the_points_are_drawn_not_the_expression, ::TestAgainstTheFixture::test_every_stored_probe, test/test_parser.cscript FX-01, test/test_wp29_truth.cscript FX-20; fixture test/fixtures/function_expr_truth.json. Residual, deferred (WP-29): by() evaluates once where twoway evaluates once per panel (FX-24); the points-free fallback knows ten functions; a malformed y-form is echoed as typed rather than as twoway's token.`
    Replace the `<!-- WP-29 P0.6 -->` marker in `### Results that change` with one line: `dash function y = 2^3^x, range(0 2) n(3)` drew 2 8 512, now 1 8 64; `2^-1^2` .5, now .25; `0.1*3/0.3` 1.0000000000000002, now 1; `1e16+1-2` 9999999999999998, now 1e16; `normalden(x)`, `ln(x)`, `_pi*x`, `_b[]` and scalars drew nothing, now twoway's points (WP-29, P0.6). Replace the marker in `### Changed behaviour` with one line: `pi`, `e`, `x**2`, `x%2`, `x//1`, a leading `+` and full-width names are refused with twoway's r(111), r(198) and r(133), and a too-long expression with r(130); registering a function evaluates it once, so a later data or estimate change does not move it, `runiform()` advances the random-number stream, data with at least n() observations are marked changed, and a graph whose points exceed c(macrolen) is refused r(134) (WP-29, P0.6). Delete the `"P0.6"` line from `WP29_OPEN` in `test/test_tracking_documents.py`. Then:
    1. Run `python3 -m pytest test/ -q` once in the worktree. A pin E10 missed is flipped in its file, with a `Flipped:` line, before continuing.
    2. Run the S04 truth block once more through the driver.
    3. Run `gitnexus_detect_changes()` and `git diff --cached --name-only`. Only this section's files may appear: never `CLAUDE.md`, `.gitignore`, scratch or `*.html`.
    4. Grep the three tracking files and the message for `claude|anthropic`.
    5. Commit once with the subject and body of "Commit boundary".
  ]]></action>
  <verify><![CDATA[The full suite's tail shows 0 failed and no new skips; `python3 -m pytest test/test_tracking_documents.py -q -n0` passes; `grep -c '<!-- WP-29 P0.6 -->' CHANGELOG.md` prints 0; `grep -c '(WP-29, P0.6)' CHANGELOG.md BUGS.md` prints `CHANGELOG.md:2` and `BUGS.md:1`; `git log -1 --format=%s | grep -c '(WP-29 P0.6)$'` prints 1; `git log -1 --format=%B | grep -ci 'claude\|anthropic'` prints 0.]]></verify>
  <done>P0.6 was closed in BUGS.md and CHANGELOG with its tests named, its allowance removed, and one green commit on wp29-s04 carried the whole section.</done>
</task>

## Section completion criteria

- Every function expression twoway accepts draws twoway's serset values in both modes, before and after a filter move. Every one twoway refuses is refused with twoway's rc and line at twoway's point in the command. The S04 truth block proves it from Stata (FX-20..FX-24).
- `c(rngstate)`, `_N`, `c(changed)`, the sort order and user variables after registration equal twoway's (FX-02..FX-04). Break returns r(1) with the data intact (FX-06).
- No point travels in a macro concatenation. One graph's points are refused past `c(macrolen)`, and a dashboard's past `dash_max_bytes`, with r(134), before any global changes (FX-07).
- Neither renderer passes spec text to `eval` or `compile` (`TestNoEval`). `_stata_expr_to_python`, `_floats_only`, `_dash_fn_refuse`, `_dash_fn_names` and `_dash_fn_space_call` are gone, with their map entries.
- One commit on `wp29-s04` with subject ending `(WP-29 P0.6)`, carrying the failing tests, the fix, the flips (each a `Flipped:` line), the fixture and the closed entry. No test-only commit exists. The full suite and every touched cscript were green.

## Notes

- **The fixture's x order.** twoway's serset is sorted by x and the generator's order is not (descending ranges). Compare `sorted(x)` with `serset_x`, and `y` in generator order with `gen_y`. Never compare generator y with serset y for `range(2 0)`.
- **Equality.** Compare floats with `==` and NaN-equal. `-0` is written `0` and compares equal. Stored points are exact. The fallback's `^`, `log10` and transcendental functions may differ from Stata's by about 1 ulp (u06 truth14: Stata's `2^0.5` is 1.414213562373095), hence `rtol=1e-15` there and only there.
- **Data-variable and RNG probes are never in the fixture.** Their answer depends on the data in memory and the seed. FX-04, FX-21 and FX-22 compare them live with twoway in the same state.
- **The varless-data "quirk" is not a quirk (A5).** twoway's tempvar drop leaves no variables, so `_N` becomes 0. dash does the same by construction, and FX-04 pins it.
- **A registry built by hand.** A function graph whose `$dash_fpts_<name>` was dropped by hand, or registered by an older dash, is drawn by the fallback from its stored expression. A global whose characters are not dash's is skipped with a note (FX-08).
- **Version.** `$dash__uv` is set at every `dash` entry and dropped after evaluation. An error exit may leave it set; it is overwritten by the next command and is not in `_dash_clear`'s sweep by design.
- **Shared files (R1-R4).**
  - R1: FX cases go in `test_parser.cscript` as one contiguous run, and the S04 block goes in `test_wp29_truth.cscript` in section order. Neither the runner nor the hygiene pins are edited.
  - R2: `_dash_function_points`, `_stata_fn_parse` and `_stata_fn_eval` go after `"_dash_function_args"`, and `_FN_EXPR_MAX_NEST` after `"_MAX_EXPR_CHARS"`. `_floats_only` and `_stata_expr_to_python` are removed. Both maps are kept in alphabetical place.
  - R3: dash.sthlp regions 338-347, 424, 809 and 1972-1976 only. Only the two P0.6 markers. The P0.6 entry is closed in place.
  - R4: the function-layer collection in `_dash_plot` is this section's (index R4). S02's `sort()` validation and S06's export code are not touched.
  - S08 lands after this section and keeps `_dash_fn_spec_tail` after its private writer closes the spec.
- **Commit body line forms:**
  - `Regression: test/test_function_expr.py::<Class>::<test> -- failed at <sha> with <text>`
  - `Regression: test/test_parser.cscript FX-nn -- failed at <sha> with <first error line>`
  - `Guard: <node> -- passed at <sha>`
  - `Flipped: <node> -- <old expectation> was wrong because <twoway's measured value>`
  - `Fixture: test/fixtures/function_expr_truth.json (scripts/extract_function_truth.do)`
  - `Security:` one line each for: no eval of spec text in either renderer; no generator-option injection; numbers-only points checked on write and on draw; no silent truncation (r(134)).
  - `BUGS.md: "<title>" (closed)`.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. The truth script then skips. A SKIP is not a pass: check `c(python_exec)` before trusting it.
- **Notes for the closeout (S15; A5 of index.md).**
  - GAPS2-A6-d, GAPS2-C5-g and GAPS2-A6-c are closed by this commit.
  - P1.22's sources (GAPS2-A6-a, A6-b, C5-a..f, AUDIT-53) are closed for Stata-built specs by the stored points. S15 decides FULLY versus PARTLY, since the points-free fallback still knows ten functions.
  - GAPS2-A6's plan item "the RNG state is unchanged" is superseded by measurement: twoway advances it, and so does dash.
  - Residuals to list:
    - per-panel evaluation under `by()`;
    - `range(varname)`, `droplines()` and `horizontal` on `function` (still refused or ignored);
    - function x on a date axis (DROPIN P1 line 135);
    - message text for malformed `y` forms.
  - AGENTS.md invariant: "a function layer's points are Stata's (`$dash_fpts_<name>`, spec `function_points`); a renderer never evaluates an expression that has points" (`test_function_expr.py::TestStoredPoints::test_an_unevaluable_expression_beside_points_is_never_parsed`).
- **Line numbers** are `7421d3d`'s. Batch-1 merges ahead of S04 (S01, S09, S03, S02) shift them. Symbols are authoritative.
