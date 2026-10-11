# Section 47: The function fallback's grammar, and the missing statistical truth

> Part of: WP-31 · GAPS3 rows: F2, F3 · Risk: yellow · Batch: 16 · Depends on: 01 · Blocks: -- · Tasks: 3, 2 commits · Case-id prefix: U47

## Overview

**What is wrong today.** GAPS3 F2 (GAPS3.md:209): "`function` points-free fallback evaluates 10 math names only; comparisons, `!`, `cond()`, n-ary `min/max`, `round`, `int`, `ln`, `normal`, `normalden`, `c(pi)`, missing codes need Stata (the Stata route covers them at build time)." The row's anchor "`_SAFE_FUNCS` ~11683" is stale: at 6370ca4 the whitelist is the tuple `funcs = ("sin", "cos", "tan", "exp", "log", "log10", "sqrt", "abs", "floor", "ceil")` in `_stata_fn_parse` (dash_render.py:42115-42116) and the `table` dict in `_stata_fn_eval` (:42287-42290); `map_function` (:20567) calls them for a spec without stored points. A hand-written spec with `y = cond(x > 2, 1, 0)` or `normal(x)` draws the layer empty with the note naming the refused function (WP-30 P1.22; `TestTheFallbackSaysWhatItNeeds`). GAPS3 F3 (:210): "Stata ground truth missing for weighted qfitci/fpfitci bands, stdf/stdr under `[fw=]`, the six kernels on lpolyci, pattern lengths, on-edge values." GAPS2 C12 (:781-793) lists the unmeasured items; GAPS2 :806 names the on-edge histogram cases ("x = 0(.1)1 with bin(10), 200 values rounded to hundredths with bin(20), the 21-value example with bin(27), nlsw88 ttl_exp with bin(27)"); GAPS2 :886 the pattern question ("Whether Stata scales pattern lengths with line width has not been measured"). `stat_truth.json`'s `unverified` key (3 entries: histogram bar heights, lpoly's ROT formula, mband's band-count formula) records what is not measured; `weighted` holds aw/fw for lfit, lfitci, qfit, fpfit, lpoly, lowess, kdensity, histogram only; `fitci_std` holds stdp/stdf/stdr unweighted only; `lpolyci_truth.json` holds the default kernel only.

**After this section** the fallback parses and evaluates, with Stata's semantics measured by `scripts/extract_function_expr_truth.do` (extended), the comparison operators `== != ~= > < >= <=`, the unary nots `!` and `~`, the binary `&` and `|`, `cond(x,a,b[,c])`, n-ary `min()`/`max()`, `round(x[,unit])`, `int()`, `trunc()`, `ln()`, `normal()`, `normalden(z[,sd]|x,mean,sd)`, `invnormal()`, `c(pi)`, and keeps the missing codes `.a`-`.z` distinct (so `.a == .` is 0 as in Stata). `test/fixtures/stat_truth.json` gains, through `scripts/extract_stat_truth.do`, the weighted qfitci/fpfitci/lpolyci bands under `[aw=]`/`[fw=]`/`[pw=]` where twoway accepts them, stdf/stdr under `[fw=]`, lpolyci's and lpoly's eight kernels at an explicit bandwidth, the lpoly default bandwidth for degree 2/3 and every kernel, histogram on-edge serset values, and `test/fixtures/line_width_truth.json` (or a new `pattern_length_truth.json`) gains the dash/dot stroke lengths at three line widths read from a twoway SVG export; each gains a pinning test and the `unverified` key shrinks to what remains.

**Why these rows share this section.** Both are "measure in Stata, then pin" work on the estimator and expression layer, both extend existing extract scripts and fixtures, and neither touches a hot function (R12). F2's twin is the parser pair; F3's twins are already written (the estimators) and need their missing truth.

**Test order and commit rule (rule 7, BRIEF).** Two cycles. F2: 47-01 extends the function-expression extractor, runs it, writes the failing tests, saves `<scratch>/47-01-failure.txt`; 47-02 extends the parser and evaluator, flips the pins and commits `(WP-31 F2)`. F3: 47-03 extends the stat extractor and the pattern probe, runs them, writes the pinning tests (red where the fixture now shows a divergence, otherwise guards named as such), fixes any divergence found in the estimator that owns it only if it is a one-line constant (else files a residual BUGS.md entry), and commits `(WP-31 F3)`.

### Section decisions (binding on the executor)

- **D-47a. Grammar extension** of `_stata_fn_parse` (D-47a is Stata's operator precedence from `[U] 13.2.1`, each level measured by the extractor's probes):
  ```
  expr := or ;  or := and ('|' and)* ;  and := cmp ('&' cmp)*
  cmp  := sum (CMPOP sum)*            CMPOP in == != ~= > < >= <=  (left to right: 1 < 2 < 3 is (1<2)<3)
  sum, diff, prod, quot as today;  neg := '-'* pow ;  pow := notatom ('^' expo)* ;  notatom := ('!' | '~')* atom
  atom := NUMBER | MISSING | 'x' | '_pi' | 'c(pi)' | FUNC '(' args ')' | '(' or ')'
  args := or (',' or)*
  ```
  [U] 13.2.1 ranks `!` above `^` and unary `-` below `^` (REVIEW-4 R4-31): `!x^2` is `(!x)^2`, `-x^2` is `-(x^2)`, `-!x` is `-(!x)`. `!-x` is admitted only if the probe shows Stata accepts it (then `notatom` gains the alternative `'!' '-' notatom`, read as `!(-x)`); the fixture wins and 47-02 never "corrects" it. The probes `!x^2`, `(!x)^2`, `-x^2`, `-!x`, `!-x`, `2 < x < 4`, `x == 2 == 1`, `1 | 0 & 0` (expected 1: `&` binds tighter) pin the levels. Tokens: `==`, `!=`, `~=`, `>=`, `<=`, `>`, `<`, `&`, `|`, `,`, `!`, `~`; `c(pi)` is one token (the letters `c`, `(`, `pi`, `)` with no blanks -- `c( pi )` is refused as twoway refuses it, measured).
- **D-47b. Values.** Missing codes stay distinct through the tree: a constant node is `("c", value, code)` where `code` is `""` for a number, `"."` or `".a"`..`".z"` for a missing; the evaluator carries two arrays, `v` (float, NaN where missing) and `m` (int8 code: 0 none, 1 `.`, 2-27 `.a`-`.z`). Arithmetic: any missing operand gives `.` (code 1) -- Stata: "missing values in arithmetic yield `.`" ([U] 13.10: `.a + 1` is `.`); comparisons never yield missing: `.` and `.a` compare as numbers above every number with `. < .a < .b < ... < .z`; `==` between different codes is 0. `!v`: 1 if `v == 0` else 0 (missing is nonzero: 0). `a & b`: 0 if either is 0, else 1 (a missing operand is nonzero: `. & 1` is 1); `a | b`: 1 if either nonzero. `cond(c, a, b, d)`: `a` where `c` is nonzero and not missing, `b` where `c == 0`, `d` where `c` is missing (default `a` when `d` is absent -- [FN] `cond()`: "c if x is missing; default a"). `min()`/`max()`: over the non-missing arguments; `.` only when all are missing. `round(x)` = half away from zero (`floor(|x| + .5) * sign`); `round(x, u)` = `u * round(x/u)` with `u` missing or 0 -> `round(x)`? No: `round(x, 0)` is `x`? Measured. `int(x)` = `trunc(x)` toward zero. `ln` = `log`. `normal(z)` = `0.5 * erfc(-z / sqrt(2))` through `np.vectorize(math.erfc)`; `invnormal(p)` through a vectorised Acklam-with-Newton refinement (or `_t_ppf`'s inverse machinery if it exposes a normal inverse) to 1e-12; `normalden(z)`, `normalden(z, sd)`, `normalden(x, m, sd)`. Every result that is not finite is `.` (today's `m()` rule). The extractor measures each rule at the points the fixture lists; where Stata disagrees with the rule written here the fixture wins and the rule in code is corrected before the commit.
- **D-47c. Tails.** `normal()` at `z <= -37.5` returns 0 and at `z >= 8.3` returns 1 in Stata (to be measured at -40 -38 -37.5 -37 -20 -8.3 -8 0 8 8.3 9 40); dash's twin is compared at 1e-12 absolute everywhere and at 1e-12 relative where both exceed 1e-300, and clamps exactly where Stata does (fixture `function.normal_tails`).
- **D-47d. Names refused** stay refused with the note (`exc.dash_refused`): `pi`, `e`, `**`, `%`, `//`, and every other function name; twoway's own refusals are measured and the list `test_the_note_lists_exactly_what_the_fallback_knows` pins is extended.
- **D-47e. F3 fixture scope.** Added to stat_truth.json by extending scripts/extract_stat_truth.do (a LAYER 12 block before the trailing python block): `weighted_ci` (qfitci, fpfitci, lpolyci under aw and fw on the four datasets, pw for qfitci/fpfitci; fpfitci refuses stdf/stdr and `range()` -- `fpfitci_parse:21-36`), `fitci_std_fw` (lfitci/qfitci × stdf/stdr × fw), `kernels` (kdensity, lpoly, lpolyci at `bwidth(<fixed>)` for all eight kernels on auto and nlsw88: curve points), `lpoly_default_bwidth` (degree 0..3 × eight kernels on auto: `r(bwidth)`), `histogram_edge` extended with the four GAPS2:806 cases as drawn serset bar heights. Pattern lengths: a new `scripts/extract_pattern_length_truth.do` exporting `twoway line mpg weight, lpattern(dash|dot|dash_dot|shortdash|longdash) lwidth(thin|medium|thick)` to SVG (`graph export .svg`) and reading each path's `stroke-dasharray` and `stroke-width` into `test/fixtures/pattern_length_truth.json`; the pinning test compares dash's `line_dash` arrays (through `OptionTranslator.translate_lpattern`) to the measured ratio (dash length / stroke width) and files the divergence as a residual if dash's constants differ (fixing them is S40's area, batch 13, which landed; a constant change here is allowed only if S40's tests stay green).
- **D-47f. The `unverified` key** is rewritten by the extractor (never by hand): the lpoly ROT and mband entries stay; the histogram entry is removed once the on-edge bar heights are enumerated.

## Risk: [yellow] -- a grammar change in a security-sensitive parser, and extractor runs of several minutes

**Why.** `_stata_fn_parse`/`_stata_fn_eval` are the one place user text is interpreted without Stata (`TestNoEval` pins that no text reaches `eval`/`compile`); `_FN_EXPR_MAX_NEST` and the n-ary folds keep the recursion bounded; the new `args` list and the new operators must keep both.

**Risk factors.**
1. A comparison chain or `cond()` list of 50,000 elements recursing: `args` must be a loop, nesting counted on `(` only.
2. Two missing arrays double the evaluator's memory: 300 points × 2, trivial; but `np.vectorize(math.erfc)` on a hand-written 10⁶-point grid (n() is bounded at 10,000 by the rules, `n=int,2,10000`) is fine.
3. The stat extractor runs twoway hundreds of times (`weighted_ci` on nlsw88 N=2246 with lpolyci: seconds each); a run of 10-20 minutes in one Stata slot.
4. Pattern lengths read from SVG: Stata's SVG `stroke-dasharray` may be absent (patterns rendered as paths); then the probe reads the `.gph`'s linepattern style and the help's documented ratios instead and the fixture says so.
5. `test_function_expr.py::TestTheFixture` and `test_statistical_truth.py` pin fixture `_meta` and key counts; regenerated fixtures change `extracted` and counts.

**Mitigation.**
1. `args` is a `while` loop like `chain`; `TestTheParserIsBounded::test_long_argument_lists_do_not_recurse` (red) pins it.
2. Guard: the fallback's grid is `n()`-bounded already.
3. Run the extractor once in 47-03 with the slot wrapper; record its wall time in the commit body; it is not a test.
4. The probe handles both forms; `pattern_length_truth.json` records `source: "svg stroke-dasharray"` or `"linepattern style"`.
5. Counts pinned with `_meta.counts` move with `# old -> new: WP-31 F3` comments (R10).

## Dependencies

- **Depends on: 01** (entries F2, F3, markers, Tracked lines).
- **Blocks:** none.
- **Parallel batch: 16**, merge order S47, S48, S49. **Can run with S48 and S49**: S48 edits `_dash_layout_cell` and adds DataTable code; S49 edits `FilterBuilder`; S47 edits `_stata_fn_parse`, `_stata_fn_eval`, `map_function`'s docstring, two extract scripts and fixtures, none of the hot functions.

## Evidence

All anchors at `6370ca4`.

### The fallback

`_stata_fn_parse` (dash_render.py:42075-42263): tokens `c`, `x`, `f`, `o` over `+-*/^()`; `funcs` tuple :42115-42116; the grammar docstring :42079-42087; `atom()` :42189-42205 (depth counted on `(`/call, `_FN_EXPR_MAX_NEST` = 40, :11693); `chain()` folds :42233-42238. `_stata_fn_eval` (:42266-42318): `table` :42287-42290; `m(v)` :42295; `pow` with NaN rule :42308-42314. `map_function` (:20567-20686): docstring names the ten functions and "Anything else -- `pi`, `e`, `**`, a leading `+`, any other name -- draws the layer empty, marked"; the fallback runs only when `points is None` (:20639). `_dash_fn_points` (dash.ado:8315) is the Stata route (`twoway__function_gen`), which covers every Stata function at build: the fallback matters for hand-written specs and for the served app's `_dash_memo_wrap`-free redraw of a spec without points.

### Tests pinning today's grammar (flip, never delete)

- test/test_function_expr.py `TestStataGrammarFallback::test_what_twoway_refuses_draws_nothing[expr]` (:518): its parametrised list includes names the extension now draws? Check each `expr`: `pi`, `e`, `**`, `%`, `//`, `+x`, `x^`, `2x`, `sin (x)`, `sin(x,1)` -- all stay refused (D-47d); `sin(x,1)` stays refused (one argument). No flip expected; `TestTheParser::test_refusals` (:681) and `TestTheNeedsPointsMark::test_the_note_lists_exactly_what_the_fallback_knows` (:816) enumerate the known functions: flipped to the new list. `TestTheHelp::test_the_fallback_rule_is_stated` (:872) reads the `{ul:Functions.}` paragraph: its sentences stay; a sentence naming the grammar is added.
- function_test_map.py:722-735 names `_stata_fn_parse.<locals>.*` and `_stata_fn_eval.<locals>.*`; new locals (`level_or`, `level_and`, `level_cmp`, `args`) need entries.
- test_statistical_truth.py / test_help_claims_6.py:880-918 (pweight bands at first and last grid rows) -- extended, not flipped.
- test_kernel_flags.py: "six of the eight kernels, which are checked only against formulas test_kernel_flags.py writes itself" (GAPS2 C12): after F3 its formula oracles are replaced by fixture values where the fixture has them (flip the oracle source, keep the nodes).

### The fixtures on disk

`test/fixtures/stat_truth.json` (`_meta.counts`: weighted_probes 55, fitci_std_probes 24, lpoly_probes 16 ...; `unverified` 3 entries); `test/fixtures/lpolyci_truth.json` (`cases`, `datasets`, `divergences`, `no_df`, `serset`; one kernel); `test/fixtures/function_expr_truth.json` (test_function_expr.py:58; `TestAgainstTheFixture::test_every_stored_probe`/`test_every_fallback_probe`); `test/fixtures/line_width_truth.json`.

## User stories

- **US-47.1** As a developer writing a spec by hand (or serving a page whose points were not stored), I want `function y = cond(x > 2, normal(x), 0)` drawn as Stata would draw it.
- **US-47.2** As a maintainer, I want every weighted band, kernel and edge case pinned to Stata's own numbers so that an estimator cannot drift unnoticed.

## Business requirements

- **BR-47.1** The fallback evaluates the listed operators and functions with Stata's missing-value and precedence rules, measured.
- **BR-47.2** What the fallback does not know is still named in the note; no text reaches `eval`.
- **BR-47.3** stat_truth.json holds Stata's values for weighted qfitci/fpfitci/lpolyci bands, stdf/stdr under fw, eight kernels, default bandwidths by degree and kernel, on-edge histogram bars; a fixture holds Stata's pattern lengths; tests pin each; `unverified` shrinks.

## Technical requirements

- **TR-47.1 tokens.** In `_stata_fn_parse`'s tokenizer (:42122-42180): before the `if ch in "+-*/^()"` line add two-character operators: `if text[i:i+2] in ("==", "!=", "~=", ">=", "<="): toks.append(("o", text[i:i+2])); i += 2; continue`; then single `><&|,!~` join the one-character `o` set. `c(pi)`: in the name branch, when `name == "c"` and `text[j:j+4] == "(pi)"`: `toks.append(("c", math.pi, "")); i = j + 4; continue` (any other `c(` is the refused function `c`). Constants carry the code: `("c", float, "")` for numbers, `("c", nan, ".")`/`("c", nan, ".a")` for missings (:42138-42146 set the code from the letter).
- **TR-47.2 grammar.** Replace `level_sum` as the top: add
  ```python
  def level_cmp():
      node = level_sum()
      while peek() is not None and peek()[0] == "o" and peek()[1] in ("==", "!=", "~=", ">", "<", ">=", "<="):
          op = peek()[1]; pos[0] += 1
          node = ("cmp", "!=" if op == "~=" else op, node, level_sum())
      return node
  def level_and():  return chain("&", level_cmp)
  def level_or():   return chain("|", level_and)
  ```
  `level_neg`: `while is_op(peek(), "-")`: toggles `odd`, then calls `level_pow()` (so `-x^2` is `("neg", ("pow", x, 2))`); `level_pow`: `node = level_not(); while is_op(peek(), "^"): ...` as today's `pow` but over `level_not`; `level_not`: `while is_op(peek(), "!") or is_op(peek(), "~")`: appends a `("not", ...)` wrapper in order and then calls `atom()` (so `!x^2` is `("pow", ("not", x), 2)` and `-!x` is `("neg", ("not", x))`); `!-x` is a parse error unless the fixture shows rc 0 for the probe, in which case `level_not` admits `-` after `!` as `("not", ("neg", level_not()))`. `atom()` for a call: parse `args` as a loop `nodes = [level_or()]; while is_op(peek(), ","): pos[0] += 1; nodes.append(level_or())`, then `("call", name, nodes)` (today's single-node call becomes a one-element list; the arity table below refuses the wrong count with `ValueError("wrong number of arguments")`, `dash_refused = ("function", name)`). `tree = level_or()`. `funcs` becomes the arity table `{"sin": (1,1), ..., "ceil": (1,1), "ln": (1,1), "int": (1,1), "trunc": (1,1), "round": (1,2), "min": (1, None), "max": (1, None), "cond": (3, 4), "normal": (1,1), "normalden": (1,3), "invnormal": (1,1)}` (`None` = any number ≥ min). The docstring's grammar (:42079-42087) is rewritten to D-47a.
- **TR-47.3 evaluator.** `_stata_fn_eval(tree, x)` keeps its signature and return (a float array, NaN where missing); internally `ev(node)` returns `(v, m)`: `v` float array, `m` int8 code array. Rules (D-47b):
  ```python
  CODES = {".": 1, **{"." + ch: i + 2 for i, ch in enumerate("abcdefghijklmnopqrstuvwxyz")}}
  def miss(v, m):                 # arithmetic result: any missing -> "."
      bad = ~np.isfinite(v) | (m != 0)
      return np.where(bad, np.nan, v), np.where(bad, 1, 0).astype(np.int8)
  # cmp: compare on the two keys (m, v), never on a float surrogate (1e308 * (1 + m)
  # overflows to inf and makes every missing code equal, REVIEW-4 R4-09):
  #   gt = (ma > mb) | ((ma == mb) & (va > vb))
  #   lt = (ma < mb) | ((ma == mb) & (va < vb))
  #   eq = (ma == mb) & ((ma != 0) | (va == vb))      # .a == .a is 1, .a == . is 0
  #   ne = ~eq; ge = gt | eq; le = lt | eq            # 0/1 float, m = 0 (never missing)
  # (a number has m == 0 and sorts below every missing code because every code is > 0)
  # not: r = (v == 0) & (m == 0) -> 1.0 else 0.0
  # fold "&": acc = all operands nonzero-or-missing -> 1 else 0;  "|": any
  # cond(c,a,b[,d]): np.where(mc != 0, d-or-a, np.where(vc != 0, a, b)) with the chosen branch's m
  # min/max: over operands with m == 0; all missing -> (nan, 1)
  # round(x[,u]): r = np.sign(x)*np.floor(np.abs(x) + 0.5); with u: u*round(x/u), u missing or 0 -> round(x) [measured]
  # int/trunc: np.trunc; ln: np.log; normal: 0.5*erfc(-z/sqrt(2)) vectorised, clamped per D-47c
  # normalden(z) = exp(-z^2/2)/sqrt(2 pi); (z, sd) = normalden(z/sd)/sd; (x, m, sd) = normalden((x-m)/sd)/sd
  # invnormal(p): missing outside (0,1); Acklam rational approximation + one Newton step on normal()
  ```
  Every arithmetic result passes `miss`; `pow`'s NaN rule stays. The returned array is `v` (callers unchanged). The `table` dict maps names to callables taking the list of `(v, m)` pairs.
- **TR-47.4 maps and tests.** function_test_map.py entries for the new locals (`_stata_fn_parse.<locals>.level_or`, `level_and`, `level_cmp`, `level_pow`, `level_not`, `args` if factored; `_stata_fn_eval.<locals>.miss`, `cmp`, and each function callable if they are locals -- prefer one dict of lambdas named `_FN_TABLE` at module scope with an entry). `TestTheNeedsPointsMark::test_the_note_lists_exactly_what_the_fallback_knows` flipped to the new list. The help's `{ul:Functions.}` paragraph gains one sentence naming the operators and functions the fallback knows.
- **TR-47.5 the extractor (F2).** Extend `scripts/extract_function_expr_truth.do` (the script test_function_expr.py:14 names) with a `fallback_grammar` section: for each probe expression run `twoway function y = <expr>, range(-3 3) n(13) nodraw` via `twoway__function_gen` (as `_dash_fn_points` does) and record the 13 y values (`%20.17g`) or the rc and message. Probes: `x > 1`, `x >= 1`, `x == 1`, `x != 1`, `x ~= 1`, `!x`, `~x`, `!x^2`, `(!x)^2`, `-x^2`, `-!x`, `!-x`, `2 < x < 4`, `x == 2 == 1`, `1 | 0 & 0`, `x & .`, `. | 0`, `!.`, `. == .`, `.a == .`, `.a < .b`, `. > 1e300`, `cond(x > 0, 1, 2)`, `cond(., 1, 2)`, `cond(., 1, 2, 3)`, `min(x, 1, .)`, `max(., .)`, `min(.)`, `round(x)`, `round(-2.5)`, `round(2.5)`, `round(x, .5)`, `round(x, 0)`, `round(x, .)`, `int(-2.7)`, `trunc(2.7)`, `ln(x)`, `ln(0)`, `normal(x)`, `normal(-40)`, `normal(-38)`, `normal(-37.5)`, `normal(-37)`, `normal(-20)`, `normal(-8.3)`, `normal(8)`, `normal(8.3)`, `normal(9)`, `normal(40)`, `normalden(x)`, `normalden(x, 2)`, `normalden(x, 1, 2)`, `invnormal(.975)`, `invnormal(0)`, `invnormal(1)`, `c(pi)`, `c( pi )`, `c(e)`, `.a + 1`, `.a * 0`, `sin(x, 1)`, `cond(x)`, `min()`, `round(x, 1, 2)`.
- **TR-47.6 the extractor (F3).** Extend `scripts/extract_stat_truth.do` with LAYER 12 (D-47e) using its existing `zq_n`/`zq_s`/`zq_curve` recorders (:428-460 pattern) and the serset method (:26-33): sections `weighted_ci`, `fitci_std_fw`, `kernels`, `lpoly_default_bwidth`, and the four `histogram_edge` cases of GAPS2:806 with bar heights from the drawn serset; rewrite the `unverified` dict in the python block (drop the histogram entry, keep the two others, add none). Create `scripts/extract_pattern_length_truth.do` per D-47e writing `test/fixtures/pattern_length_truth.json` with `_meta`.
- **TR-47.7 pinning tests (F3).** `test/test_statistical_truth.py` (existing file; add classes): `TestWeightedCiBands::test_each[ds-type-weight]` comparing `map_qfitci`/`map_fpfitci`/`map_lpolyci` bands at the sampled grid rows (rtol 1e-6, the fixture's float precision note); `TestFitciStdUnderFw::test_each[ds-type-std]`; `TestEightKernels::test_each[cmd-kernel]` (kdensity/lpoly/lpolyci curves at the fixed bandwidth, rtol 1e-6); `TestLpolyDefaultBandwidth::test_each[degree-kernel]` against `GlyphMapper._default_lpoly_bwidth` (rtol 1e-9); `TestHistogramOnEdge::test_each[case]` bar by bar in Python and through `run_filter_js_block("histogram", ...)` under node (GAPS2:806 step 3). `test/test_pattern_lengths.py` (new): `TestPatternLengths::test_ratio_to_width[pattern-width]` comparing `translate_lpattern`'s `line_dash` scaled by the width to the fixture's ratio within 10%; a divergence is recorded as `pytest.xfail(reason="WP-31 F3 residual: <measured>")` in the same commit and a residual BUGS.md entry is opened (M12). test_kernel_flags.py's formula oracles for the six kernels are replaced by fixture reads (flip in place, R9). `test_fixtures_are_committed.py` requires the new fixture to be named: `test_pattern_lengths.py` names it.

## Boundaries

- Do not edit `map_function`'s logic (only its docstring's function list), `_dash_fn_points`, the Stata route, `_FILTER_JS` (no JS twin exists for the function fallback: the saved page draws stored points, WP-29 P0.6), the estimators (except a one-line constant under D-47e's rule), S40's pattern translators beyond a constant.
- Do not change `_FN_EXPR_MAX_NEST`, `_MAX_EXPR_CHARS`; do not add `eval`/`compile`; `TestNoEval` stays green.
- Do not hand-edit a fixture (R7); the `unverified` key is written by the extractor.

## Stata truth

- `scripts/extract_function_expr_truth.do` extended (TR-47.5) -> `test/fixtures/function_expr_truth.json` regenerated whole (`_meta` restamped; keys `fallback_grammar.<probe>` with `y` (13 values), `rc`, `msg`). Run: `DASH_REPO=<wt> scripts/stata_slot.sh <scratch>/s47 <wt>/scripts/extract_function_expr_truth.do`.
- `scripts/extract_stat_truth.do` extended (TR-47.6) -> `test/fixtures/stat_truth.json` regenerated whole; `_meta.counts` gains `weighted_ci_probes`, `fitci_std_fw_probes`, `kernel_probes`, `lpoly_default_bwidth_probes`; `histogram_edge_probes` 7 -> 11; `unverified` 3 -> 2. Run as its header says (:11); expect 10-20 minutes.
- `scripts/extract_pattern_length_truth.do` (new) -> `test/fixtures/pattern_length_truth.json`.
- All three `git add -f`; named by test_function_expr.py (existing), test_statistical_truth.py (existing) and test_pattern_lengths.py (new).

Truth block `* ==== S47 F2: function fallback grammar ====` in `test/test_wp31_truth.cscript`:
- **U47-1** for each `fallback_grammar` probe with rc 0: a `python:` helper evaluates `dr._stata_fn_eval(dr._stata_fn_parse(expr), x)` on `range(-3 3) n(13)` and compares to the fixture's `y` (missing both sides, else `isclose(rtol=1e-12, atol=1e-12)`); `normal_tails` probes exact at the clamps.
- **U47-2** for each probe with rc != 0: `_stata_fn_parse` raises `ValueError` (`dash_refused` set where a name is involved).
- **U47-3** `dash function y = cond(x > 1, normal(x), 0), range(-3 3) name(u473)` registers with stored points (the Stata route) and a hand-written spec without points, rendered by `_dash_serve_spec`'s helper in both modes, draws the same 300 y values as the stored ones (rtol 1e-12).
- Block `* ==== S47 F3: statistical truth extended ====`:
- **U47-4** `twoway qfitci mpg weight [aw=price]` and dash's served/saved band at the fixture's sampled grid rows agree (rtol 1e-6) -- the live comparison beside the fixture (the serset read in the block as the extractor reads it).
- **U47-5** `twoway lfitci mpg weight [fw=rep78], stdf` band vs dash (rtol 1e-6).
- **U47-6** `twoway lpolyci mpg weight, kernel(cosine) bwidth(300)` smooth and band vs dash (rtol 1e-6).
- **U47-7** `twoway histogram x, bin(10)` on `x = 0(.1)1` (11 values): bar heights equal the serset's (every value on an edge).

## TDD test stubs

### Regression tests (red at 6370ca4 unless marked)

- `test/test_function_expr.py`:
  - Test: each of `x > 1`, `!x`, `cond(x>0,1,2)`, `min(x,1,.)`, `round(-2.5)`, `int(-2.7)`, `ln(x)`, `normal(x)`, `normalden(x,1,2)`, `invnormal(.975)`, `c(pi)` parses and equals the fixture -- `TestExtendedGrammar::test_against_the_fixture[probe]` (red: ValueError unknown function/character).
  - Test: precedence probes (`!x^2`, `-x^2`, `-!x`, `2 < x < 4`, `1 | 0 & 0`) equal the fixture -- `TestExtendedGrammar::test_precedence[probe]` (red).
  - Test: missing codes stay distinct (`.a == .` is 0, `.a < .b` is 1, `.a + 1` is `.`) -- `TestMissingCodes::test_each` (red).
  - Test: `normal()` clamps where Stata does and agrees at 1e-12 -- `TestNormalTails::test_each_point` (red).
  - Test: a 50,000-argument `max(...)` and a 50,000-term `&` chain parse without recursion -- `TestTheParserIsBounded::test_long_argument_lists_do_not_recurse` (red: args not supported).
  - Test: wrong arity (`sin(x,1)`, `cond(x)`, `round(x,1,2)`, `min()`) is refused with `dash_refused=("function", name)` -- `TestTheParser::test_arity` (red).
  - Test: `c( pi )` and `c(e)` are refused -- `TestTheParser::test_c_pi_token` (red).
  - Test: no text reaches eval (existing `TestNoEval`, guard).
  - Flip: `TestTheNeedsPointsMark::test_the_note_lists_exactly_what_the_fallback_knows` and `TestTheParser::test_refusals` to the new list.
- `test/test_statistical_truth.py`: TR-47.7's five classes (red until the fixture exists; after 47-03's extraction they are green guards unless a divergence appears, in which case the divergence is the row's finding).
- `test/test_pattern_lengths.py` (new): `TestPatternLengths::test_ratio_to_width[pattern-width]`; `TestTheFixture::test_meta`.
- test_kernel_flags.py: oracle flipped to fixture reads for the six kernels.

### cscript cases: U47-1..U47-3 (F2 block), U47-4..U47-7 (F3 block).

### Combined pins (R10): stat_truth `_meta.counts` pins in test_statistical_truth.py move with `# old -> new: WP-31 F3`; function_expr_truth probe counts likewise `WP-31 F2`.

### Parity corpus: `_case("function cond", [plot_for("function", {"range": "-3 3"}) | {"expr": "cond(x > 1, normal(x), 0)"}])` -- a function spec without points draws alike in both modes (the fallback is shared code).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| grammar and semantics | pytest TestExtendedGrammar/TestMissingCodes/TestNormalTails; cscript U47-1,2 | function_expr_truth.json | n/a (shared) |
| bounded parser, no eval | pytest TestTheParserIsBounded, TestNoEval | -- | n/a |
| both modes draw the fallback alike | parity case; cscript U47-3 | -- | yes |
| weighted bands, stdf/stdr fw, kernels, bandwidths, edges | pytest test_statistical_truth.py; cscript U47-4..7 | stat_truth.json | saved (mappers) |
| pattern lengths | pytest test_pattern_lengths.py | pattern_length_truth.json | n/a |

Acceptance: **AC-47.1** every rc-0 probe agrees at 1e-12; every refused probe raises; **AC-47.2** parser bounded, no eval; **AC-47.3** the five F3 classes green or their divergences filed; **AC-47.4** `unverified` holds two entries; **AC-47.5** two green commits.

## Tasks

**Commit boundary.** 47-01 + 47-02 = `Evaluate Stata's comparisons, cond(), min/max, round, normal and c(pi) in the function fallback (WP-31 F2)`; 47-03 = `Pin weighted bands, stdf/stdr, eight kernels, edge bars and pattern lengths to Stata (WP-31 F3)`.

<task type="auto" id="47-01">
  <name>Measure the grammar and write failing tests</name>
  <files>scripts/extract_function_expr_truth.do, test/fixtures/function_expr_truth.json, test/test_function_expr.py</files>
  <action><![CDATA[Extend scripts/extract_function_expr_truth.do with the `fallback_grammar` section (TR-47.5: every probe through `twoway__function_gen y = <expr>, range(-3 3) x(x) n(13) generate(fy fx)` under `capture noisily`, y values at %20.17g, rc and the error line), regenerate test/fixtures/function_expr_truth.json whole with the slot wrapper, and confirm the existing `TestAgainstTheFixture` still passes (the old keys are unchanged in meaning). Add the stubs under "TDD test stubs" to test/test_function_expr.py (new classes; flips of `test_the_note_lists_exactly_what_the_fallback_knows` and `test_refusals` to the D-47a list with their reasons). Run `python3 -m pytest test/test_function_expr.py -q -n0 -p no:cacheprovider 2>&1 | tee <scratch>/47-01-failure.txt` against the unmodified renderer; append the S47 F2 block (U47-1..U47-3) to test_wp31_truth.cscript and run it red through the driver. Do not commit.]]></action>
  <verify><![CDATA[`grep -c "unknown function\|unknown name\|character not in the grammar\|FAILED" <scratch>/47-01-failure.txt` is at least 8; `python3 -c "import json;d=json.load(open('test/fixtures/function_expr_truth.json'));g=d['fallback_grammar'];print(len(g), g['normal(-40)']['y'][0], g['cond(., 1, 2)']['y'][0])"` prints a count of at least 60 and the two Stata values (expected 0 and 1).]]></verify>
  <done>Stata's answers for every grammar probe were measured and the extended-grammar tests failed against the unmodified parser, with the failure text saved.</done>
</task>

<task type="auto" id="47-02">
  <name>Extend the parser and evaluator, commit F2</name>
  <files>dash_render.py, test/function_test_map.py, dash.sthlp</files>
  <action><![CDATA[Make TR-47.1, TR-47.2 and TR-47.3 in `_stata_fn_parse` and `_stata_fn_eval` (dash_render.py:42075-42318), rewriting both docstrings and `map_function`'s function list sentence (:20589-20600); correct any rule the fixture contradicts (D-47b: the fixture wins) and say so in the docstring. Add TR-47.4's function_test_map.py entries. dash.sthlp `{ul:Functions.}` paragraph: add `A spec without stored points is evaluated by dash's own reader of Stata's grammar: + - * / ^, the comparisons == != ~= > < >= <=, ! and ~, & and |, cond(), min(), max(), round(), int(), trunc(), ln(), log(), log10(), exp(), sqrt(), abs(), floor(), ceil(), sin(), cos(), tan(), normal(), normalden(), invnormal(), _pi and c(pi), with Stata's missing values (.a to .z kept apart); anything else is named in the note.` Run test_function_expr.py, test_function_test_map.py, test_help_conformance.py, `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "function"` (append the parity case first), test_adversarial.py, test_resource_limits.py, and the F2 block through the driver. Close BUGS.md "F2", rewrite the F2 Tracked line to the Closed form with `commit pending` (DECISIONS A11; the merger's step k.3b writes the sha), replace `<!-- WP-31 F2 -->` under `### Fixed in WP-31` with `- A function layer whose spec carries no stored points is drawn for comparisons, ! and ~, & and |, cond(), n-ary min()/max(), round(), int(), trunc(), ln(), normal(), normalden(), invnormal() and c(pi), with Stata's missing-value rules; it was drawn empty with a note. (WP-31, F2)`. Stage dash_render.py dash.sthlp scripts/extract_function_expr_truth.do test/test_function_expr.py test/function_test_map.py test/test_mode_parity.py test/test_wp31_truth.cscript BUGS.md GAPS3.md CHANGELOG.md and `git add -f test/fixtures/function_expr_truth.json`; commit with BRIEF's body forms.]]></action>
  <verify><![CDATA[Every run reports 0 failed; `grep -c "U47-[1-3] PASS" <scratch>/s47/run_test_wp31_truth.log` prints 3; `python3 -c "import dash_render as dr,numpy as np;print(dr._stata_fn_eval(dr._stata_fn_parse('cond(x > 1, normal(x), c(pi))'), np.array([0.0, 2.0])))"` prints `[3.14159265 0.97724987]`; `grep -c "eval(\|compile(" <(sed -n 42075,42500p dash_render.py)` prints 0; `git log -1 --format=%s` ends `(WP-31 F2)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The function fallback read Stata's comparison, logical and function grammar with its missing-value rules, agreed with twoway on every probe, stayed bounded and eval-free, and F2 was committed green.</done>
</task>

<task type="auto" id="47-03">
  <name>Extract and pin the missing statistical truth, commit F3</name>
  <files>scripts/extract_stat_truth.do, scripts/extract_pattern_length_truth.do, test/test_statistical_truth.py</files>
  <action><![CDATA[Write TR-47.7's test classes in test/test_statistical_truth.py and the new test/test_pattern_lengths.py first; run them (red: fixture keys missing), save <scratch>/47-03-failure.txt. Make TR-47.6: LAYER 12 in scripts/extract_stat_truth.do (sections weighted_ci, fitci_std_fw, kernels, lpoly_default_bwidth, four more histogram_edge cases; `unverified` rewritten in its python block) and create scripts/extract_pattern_length_truth.do (SVG export of 5 patterns x 3 widths, `stroke-dasharray`/`stroke-width` read in a python block; fall back to the linepattern style record with `source` saying so). Run both through the slot wrapper (`DASH_REPO=$WT scripts/stata_slot.sh <scratch>/s47 ...`; record the stat extractor's wall time). Run test_statistical_truth.py, test_pattern_lengths.py, test_kernel_flags.py (its six oracles flipped to fixture reads), test_help_claims_6.py, test_lpolyci_band.py, `test/test_statistical_helpers.py -k FilterJavaScript`, test_fixtures_are_committed.py; append the S47 F3 block (U47-4..U47-7) and run it through the driver. A divergence an estimator shows against the new truth: if it is a one-line constant, fix it with its own failing test in this commit; otherwise mark the node `xfail(reason="WP-31 F3 residual: ...")`, open a residual BUGS.md entry in the open form graded S3 and name it in the F3 Tracked line (Partly closed form). Close BUGS.md "F3" (or Partly), rewrite the Tracked line with `commit pending` (A11), replace `<!-- WP-31 F3 -->` under `### Fixed in WP-31` with `- Stata's values for weighted qfitci, fpfitci and lpolyci bands, stdf/stdr under fweights, all eight kernels, lpoly's default bandwidth by degree and kernel, histogram bars on bin edges and line pattern lengths are recorded and pinned. (WP-31, F3)`. Stage the two scripts, the tests, BUGS.md GAPS3.md CHANGELOG.md and `git add -f test/fixtures/stat_truth.json test/fixtures/pattern_length_truth.json`; commit with BRIEF's body forms (the extractor's wall time after the measured defect).]]></action>
  <verify><![CDATA[Every run reports 0 failed (xfails allowed only with a `WP-31 F3 residual` reason); `python3 -c "import json;d=json.load(open('test/fixtures/stat_truth.json'));print(len(d['unverified']), sorted(k for k in d if k in ('weighted_ci','fitci_std_fw','kernels','lpoly_default_bwidth')), d['_meta']['counts']['histogram_edge_probes'])"` prints `2 ['fitci_std_fw', 'kernels', 'lpoly_default_bwidth', 'weighted_ci'] 11`; `grep -c "U47-[4-7] PASS" <scratch>/s47/run_test_wp31_truth.log` prints 4; `git log -1 --format=%s` ends `(WP-31 F3)`; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>The statistical truth fixture held Stata's weighted bands, fw standard errors, eight kernels, default bandwidths, edge bars and pattern lengths, every estimator was pinned to them or its divergence filed, and F3 was committed green.</done>
</task>

## Section completion criteria

- The fallback parses D-47a's grammar with D-47b's semantics, agrees with twoway on every rc-0 probe at 1e-12, refuses every rc-198 probe with the note, recurses only into parentheses, reaches no eval.
- stat_truth.json gains the four sections and the on-edge cases, `unverified` has two entries; pattern_length_truth.json exists; every item pinned (or filed as a residual with an xfail).
- U47-1..U47-7 PASS; two green commits; F2 closed, F3 closed or partly with a named residual.

## Notes

- **The GAPS3 anchor `_SAFE_FUNCS`** does not exist; the executor edits `funcs` in `_stata_fn_parse` and `table` in `_stata_fn_eval` and records the correction in the F2 commit body ("GAPS3 F2's anchor named `_SAFE_FUNCS`; the whitelist is `_stata_fn_parse.funcs`").
- **Comparisons are 0/1 floats**, never missing; `cmp` nodes compare the (m, v) key pair (TR-47.3) so `. > 1e300` is 1, `.a < .b` is 1 and `.a == .` is 0 (measured by the probes; if Stata's ordering of codes differs, the fixture decides and `CODES` is reordered). No float surrogate: `1e308 * 2` is `inf`.
- **`c(pi)` vs `_pi`:** both are `math.pi`; `c(pi)` is one token only when written without blanks.
- **The served app** copies `_stata_fn_parse`/`_stata_fn_eval` by name (they are on the functions tuple already: check with `grep -n '"_stata_fn_parse",' dash_render.py`; if absent, add both after `_dash_reference_lines`'s block -- after S26's last entry `_dash_is_horizontal_opts` -- and say so in Notes to the merger). `math` is imported at module scope already.
- **Fixture precision note** (stat_truth `_meta.precision`): serset values are float32; compare bands with rtol 1e-6.
- **Extractor time**: the stat extractor is the longest in the repo (2948 lines); LAYER 12 adds nlsw88 lpolyci runs; run it once, in a slot, never in a test.
- **python_exec hazard** (project memory): check `~/.stata19/console/stata19.rc` after each extractor and driver run.
- **Shared files (R1-R13).** R1: two S47 blocks (F2 and F3, consecutive). R2: no new module function unless `_FN_TABLE` is factored out (then one constant after S26's `_DASH_CONTOUR_CAP_NOTE`). R3: the `{ul:Functions.}` paragraph. R4: two markers. R5: two entries (plus a residual if filed). R7: three fixtures regenerated whole, `git add -f`. R8: one parity case. R9: the two function_expr flips, test_kernel_flags' oracle flip. R10: fixture count pins. R12: none of the hot functions edited.
- **Commit-body line forms** are BRIEF's; `failed at` is the batch-16 base sha. Tracked lines are written with `commit pending` (DECISIONS A11); no amend.
- **A14.** 47-01 appends only the F2 block; 47-03 appends the F3 block when it closes F3 (one truth block per row, appended by the row's closing task).
