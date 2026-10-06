# Section 26: function: closed by disposition (P1.22 under M12)

> Part of: WP-30 · Items: P1.22 (entry `P1.22`; GAPS2-A6-a, A6-b, GAPS2-C5-a, C5-b, C5-c, C5-d, C5-e, C5-f, AUDIT-53, all closed by disposition under M12) · Risk: green · Batch: 9 (merge order S25, S26, S27) · Depends on: 06, 23 · Blocks: — · Tasks: 10, 1 commit · Case prefix: FN

## Review amendments

- Fixed (major, executability): `$S` was the shared WP-30 scratch root, so S26's driver files, logs and `STATATMP` (`run_test_wp30_truth.log`, `run_test_parser.log`, …) shared names with its batch partners running at the same time. `$X` is now the root (batch base, impact and ratified records, queue script, the failure file at `<scratch>/26-P1.22-failure.txt` as index step 1 names it) and `$S` is `$X/s26`.
- Fixed (minor): the `unknown name` raise is at dash_render.py:28788, not :28789; FN-02..05's insertion point names the second `macro drop lb_pfail` (:2854).
- Checked at `c96facd`: `map_function` :14854 with the empty returns at :14916/:14926/:14930, `_stata_fn_parse` :28693 (raises :28779, :28788), `_dash_report_empty_layer` :28331 and its calls :28405-28408, `_mark_silent` :10735 / `_masked_index` :10757, the copy list :33126-33137, `_dash_fn_spec_tail`'s two notes (dash_parse.mata:4253, :4264), dash.sthlp:413-418, C-03's needle (test_conformance.cscript:425, control :230), `_fx_serset`/`_fx_stored`/`_fx_plots_saved`/`_fx_plots_served` in test_wp29_truth.cscript, `_p1a_logrun` and `cert_helpers.do` in test_parser.cscript: all as quoted. WP-29's truth script already runs a `python:` block inside its gated block, so FN-01's form is runnable.
- Checked: S23's `_dash_note_empty_layer(gname, index, ptype, rows, renderers, layer_rows=None)` leaves the function branch to S26 (section-23 TR, :405), so TR-26.6 and its unit test fit S23's signature.
- Checked: batch 9. S26 edits `_stata_fn_parse`, `map_function`, two new `GlyphMapper` methods, the two empty-layer helpers, `_dash_fn_spec_tail` and dash.sthlp:413-418; S25 and S27 edit none of them, and S26 edits no copy list, `_generate_app_source` or finisher. Tracking forms (title, key, `### Fixed in WP-30` marker, stub header, subject) match section-01.
- Rejected: "the note should be refused or silent under M6". M6 covers what twoway draws in silence; twoway never meets a spec without points, and M12 rules a note.
- The review pass applied both lenses.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:133 (P1.22) reads: "`function` evaluates only 10 functions. `normalden`, `normal`, `ln`, `_pi`, `c(pi)`, comparisons, `cond`, `min`, `max`, `round`, `int`, `scalar()` and `_b[]` all draw nothing." Its WP-29 note: "P0.6 (commit 96aa267) evaluates every function layer of a Stata-built spec with Stata's own generator (stored points), which closes these sources there; the points-free fallback still knows ten functions". Measured at `c96facd` (research `.ultraplan/wp30/research/p1-22.md` §2, re-measured for this file, Evidence E5):

- Every graph `dash` registers draws Stata's own points: all 16 expressions of research M1 (the 13 the item names plus `s*x`, `invlogit(x)` and `sin(x)`) give stored points equal (`==` on doubles) to `twoway function`'s serset, and both modes draw them.
- A spec that carries no points (one written by hand, or a registry whose `$dash_fpts_<name>` was removed) reaches the ten-function fallback. Anything else draws an empty layer with one bare note: `dash: graph 'nd' plot 1 (function) drew nothing.` The note names neither the cause nor the remedy, in either mode, and `dash build, server` printed nothing at all before S23.
- When the stored points are not dash's, Stata prints `dash: the function points stored for graph 'ng' are not dash's; that layer is drawn from its expression.` That promises a draw the fallback cannot make for any function that only Stata evaluates, and the renderer then reports the bare "drew nothing.".
- The help (dash.sthlp:413-418) already says that for anything outside the ten "a note names it". No note names anything.

**What is true after this section.** Maintainer decision M12 is binding: "The ten-function points-free fallback stays; anything else it meets gets a 'needs Stata's points' note; P1.22 is recorded closed by WP-29 P0.6 plus that note." After this section:

- A function layer the fallback cannot draw still draws nothing, and it gives one neutral note in both modes. The note says the layer needs the points Stata computes when `dash` registers the graph, lists what the fallback evaluates, and names the first function (`normalden()`) or bare name (`pi`) it refused, or says the expression cannot be read. Stored points that cannot be read get the same note, naming that cause.
- The note reaches Stata from a saved build through S06's channel, and from `dash build, server` through S23's trial render.
- The Stata note for points that are not dash's stops promising a draw. It says the points are not used and how to store Stata's.
- The help states the rule.
- The disposition's premise, that every registered graph draws twoway's points, is pinned against twoway's serset for the 13 expressions the item names (FN-01).

The fallback's grammar (`_stata_fn_parse`/`_stata_fn_eval`) is not extended (register P1.22.1: option B is a candidate P2 item), and no extractor or fixture is added.

**Why one section.** P1.22 is one item, closed by one disposition and one note. Everything it edits is one path: the parser's refusal, `map_function`'s empty returns, the empty-layer note both modes run, the Stata tail note and the help paragraph.

**Test order and commit rule.** The section makes one commit, `(WP-30 P1.22)`.
- 26-01 writes every regression test (pytest, the parity case, FN-02..FN-05). It runs them against the unmodified worktree at `batch-9-base`, saves the failure text to `$X/26-P1.22-failure.txt` and never commits.
- 26-02 fills the S26 truth block with the guard FN-01, which passes at the base, and records it as a guard.
- 26-03 to 26-09 make the fix, flip the four pinned expectations, register the two new methods and rewrite the help.
- 26-10 closes the entry, replaces the marker, deletes the `WP30_OPEN` key, runs the full suite once and commits.

No test-only commit exists, and no commit is red.

## Risk: [green] — a note's wording and one Stata note change; nothing is drawn differently

**Why green.** No glyph, coordinate, colour or page byte changes in either mode. Only the text of one note (which gains a reason) and of one Stata note changes. The edited symbols are all LOW in impact (E9). The HIGH `ServerAppBuilder._glyph_layer_lines` is not edited: the two new names are `GlyphMapper` static methods, which travel with the class.

**Risk factors.**
1. Four tests pin the bare note's exact text: three pytest nodes and C-03 of `test_conformance.cscript` (E8).
2. `map_function` is edited later by S35, S40, S45 and S49, after S24 and S19 edited it earlier. A later edit could drop the mark from an empty return.
3. The served note reaches Stata only through S23 (batch 8). If S23's trial or relay changes shape, FN-03 changes with it.
4. The note is about 330 characters long, so Stata wraps it in a log. A raw-byte needle can miss it.
5. `_stata_fn_parse` is copied verbatim into the served app, and eight test files call it. Its error text must not change, because tests match on it.
6. The note echoes a name taken from a spec, which is user input.

**Mitigation.**
1. Each pin is flipped in place with a `Flipped:` line (R9). The relational guards that count one note stay green, unedited (E8).
2. The mark composes with any `_empty()`: it is applied to what `_empty()` returns. TR-26.4 and Notes trap 3 tell later sections to keep it, and a test per path pins it in both modes (R1-R4 of the stubs).
3. FN-03 reads the served build's log in Stata, whatever S23's mechanism. The pytest served tests exec the generated app's `make_document`, which S23 does not change.
4. Every log needle goes through `cert_log_has`, which rejoins wrapped lines.
5. Only an attribute is added to the raised `ValueError`. `str(exc)` is unchanged and `TestTheParser` stays green.
6. Only a name that is ASCII, starts with a letter or `_` and holds only letters, digits and `_` is echoed, cut at 32 characters. Nothing else from the spec is echoed. The note goes only to Stata, through S06's SMCL-escaping emitter, and never into the page (TR-26.12).

**Prototype (measured 03oct2026 on a scratch copy of `c96facd` with TR-26.1-TR-26.7 and the parity case applied).**
- `test_function_expr.py`, `test_empty_layer_report.py`, `test_immediate_dashboards.py`, `test_server_layer_defects.py`, `test_layer_reports.py`, `test_server_function_security.py`, `test_function_test_map.py` and the two served-name guards gave `7 failed, 789 passed`. The seven are exactly the planned flips (two in `test_empty_layer_report.py`, four ids of `test_with_data_or_none`) and `test_every_function_has_an_entry` (the two methods not yet mapped).
- `test_mode_parity.py`, `test_security_surface.py`, `test_glyphs.py`, `test_phase4_plots.py`, `test_resource_limits.py`, `test_help_claims_7.py`, `test_help_claims_8.py` and `test_pipeline_integration.py`, run with `-k "function or Function or empty or Empty or drew"`, gave `529 passed`.
- The new parity case gave `11 passed`. Use `-k needing`, a single word: a two-word `-k` under xdist ended in an INTERNALERROR.

## Dependencies

- **Depends on: 06, 23.**
  - S06 (batch 2) gives the note channel. A `warnings.warn("dash: …")` raised inside `main()` prints once as `(note:  dash: …)` through `_dash_emit_note`, SMCL-escaped and at most 4,000 characters, and Mata `_dash_note` replaces `_dash_say("txt", …)` in `_dash_fn_spec_tail` (S06 E3 rows 10-11).
  - S23 (batch 8) makes the served app's notes reach Stata. `dash build, server` runs a trial render whose notes are re-issued in the building process (IR-10, A83). `dash serve` relays the child's notes with its first session (until S46). It also gives `_dash_note_empty_layer` S23's M6 argument (`layer_rows`).
  - S26 adds no channel code of its own. Register P1.22.2 says a renderer note only; P1.22.5 says after P1.26-A, using `_dash_emit_note`.
- **Blocks:** none.
- **Parallel batch: 9.** Merge order S25, S26, S27 (index "Batch 9").
- **Can run with:** S25 and S27. Neither edits `map_function`, `_stata_fn_parse`, the empty-layer note helpers, `_dash_fn_spec_tail`, `test_function_expr.py`, `test_parser.cscript` or dash.sthlp:413-418 (Boundaries).

## Evidence

All anchors are at `c96facd` (dash_render.py 37,689 lines, dash.ado 8,487, dash_parse.mata 6,093, dash.sthlp 3,822). Batches 2-8 move them, so every executor step finds its site by the quoted text, never by number.

### E1. The disposition's premise: every registered graph draws Stata's points

`_dash_fn_points` (dash.ado:5973-6024, called at :5360) runs `twoway__function_gen` at registration and stores `{"x0":…,"dx":…,"y":[…]}` in `$dash_fpts_<name>`. `_dash_fn_spec_tail` (dash_parse.mata:4240) writes the points into the spec, and `_dash_attach_function_points` (dash_render.py:3191) moves them onto each plot in both renderers. `map_function` then draws them without parsing the expression.

Research M1 (`m1b.do`, StataNow 19.5). For each expression: `sysuse auto`, `regress mpg weight`, `scalar s = 2`, `twoway function y = <e>, range(..) n(5) nodraw`, then the serset, then `dash function y = <e>, range(..) n(5) name(gk)` and `$dash_fpts_gk`. Output:

```
 1 normalden(x)            twoway rc=0 dash rc=0 n=5 equal=True
 2 normal(x)               twoway rc=0 dash rc=0 n=5 equal=True
 3 ln(x)                   twoway rc=0 dash rc=0 n=5 equal=True
 4 _pi*x                   ... equal=True
 5 c(pi)*x                 ... equal=True
 6 (x>1)*x                 ... equal=True
 7 cond(x>1,x,0)           ... equal=True
 8 min(x,1)                ... equal=True
 9 max(x,1)                ... equal=True
10 round(x)                ... equal=True
11 int(x-1)                ... equal=True
12 scalar(s)*x             ... equal=True
13 s*x                     ... equal=True
14 _b[_cons]+_b[weight]*x  ... equal=True
15 invlogit(x)             ... equal=True
16 sin(x)                  ... equal=True
```

The critic's `c1.do` also drew the one-line form, a mixed `(scatter …)(function …)`, a one-line `by(foreign)` and a named two-function graph saved and served (via `make_document`), each at Stata's values. `ado/base/t/twoway__function_gen.ado` is byte-identical in Stata 14-19.5 (research §3). Already pinned:
- `test/fixtures/function_expr_truth.json` holds `c(pi)*x`, `normalden(x)`, `ln(x)`, `(x>1)*x` and `max(x,1)` (`_meta`: `stata_version` 19.5, `born_date` 12 Aug 2026, `extracted` 1 Oct 2026, `dash_commit` e77651e…), and `TestAgainstTheFixture::test_every_stored_probe` draws them in both modes;
- `test_wp29_truth.cscript` FX-20..FX-24 pin twenty grammar expressions.

`normal`, `cond`, `min`, `round`, `int`, `scalar()` and `_b[]` are pinned nowhere. FN-01 pins all 13 the item names.

### E2. Where the fallback draws an empty layer (dash_render.py, `GlyphMapper.map_function`, 14854-14949)

```python
14913        if points is not None:
14914            got = _dash_function_points(points)
14915            if got is None:
14916                return _empty()
14917            x_arr, y_arr = got
14918        else:
14919            if len(text) > _MAX_EXPR_CHARS:
14920                warnings.warn(  ... "the layer is drawn empty." ...)
14926                return _empty()
14927            try:
14928                tree = _stata_fn_parse(text)
14929            except ValueError:
14930                return _empty()
```

There are four empty returns:
- **:14916** stored points that cannot be read (critic case H; `test_conformance.cscript`'s `ctl` control is one);
- **:14926** an expression over 5,000 characters, which already has its own note (left as it is);
- **:14930** a refusal by the fallback's parser (the item);
- **:14938** an evaluation error. It is unreachable in practice: `n` is capped at 10,000 by `_dash_function_args` (:28627), and the tree holds only known nodes. Left as it is.

The parser's refusals carry no name (dash_render.py:28729, :28777-28789):

```python
28729    funcs = ("sin", "cos", "tan", "exp", "log", "log10", "sqrt", "abs",
28730             "floor", "ceil")
 ...
28777            if j < n and text[j] == "(":
28778                if name not in funcs:
28779                    raise ValueError("unknown function")
 ...
28786            elif name == "_pi":
28787                toks.append(("c", math.pi))
28788            else:
28789                raise ValueError("unknown name")
```

The tokenizer reads left to right, so the first refusal decides. Measured with a scratch copy that adds the name to the error (03oct2026, `proto.py`):

```
'normalden(x)'     'unknown function'              ('function', 'normalden')
'c(pi)*x'          'unknown function'              ('function', 'c')
'cond(x>1,x,0)'    'unknown function'              ('function', 'cond')
'scalar(s)*x'      'unknown function'              ('function', 'scalar')
's*x'              'unknown name'                  ('name', 's')
'_b[_cons]+...'    'unknown name'                  ('name', '_b')
'pi*x'             'unknown name'                  ('name', 'pi')
'sin (x)'          'unknown name'                  ('name', 'sin')
"__import__('os')" 'unknown function'              ('function', '__import__')
'(x>1)*x'          'character not in the grammar'  None
'x^'               'expression ends early'         None
'ｓｉｎ(x)'          'function expressions are ASCII' None
'2x'               'malformed number'              None
'1>normalden(x)'   'character not in the grammar'  None
```

So a note that says "X is evaluated only by Stata" would be false for `pi`, `e`, `PI`, `E` and `sin (x)`, which twoway refuses (r(111)). The critic's finding (p1-22.md "Critic additions" 1) is binding as register P1.22.3: the note is neutral. It says what the fallback knows and names the one it met.

### E3. The note today (dash_render.py:28331-28408)

```python
28331 def _dash_report_empty_layer(gname, index, ptype, rows=None):
 ...
28342    where = f"graph {gname!r} plot {index}" if gname else f"plot {index}"
28343    tail = f" from {rows:,} observations" if rows is not None else ""
28344    warnings.warn(
28345        f"dash: {where} ({ptype}) drew nothing{tail}.",
28346        UserWarning, stacklevel=2,
28347    )
 ...
28400    # A layer twoway draws empty in silence ... (GlyphMapper._mark_silent)
28402    if any(getattr(_r, "_dash_silent", False) is True
28403           for _r in renderers or ()):
28404        return
28405    if pt == "function":
28406        _dash_report_empty_layer(gname, index, ptype)
28407    elif rows:
28408        _dash_report_empty_layer(gname, index, ptype, rows)
```

Both modes call `_dash_note_empty_layer` after each layer. The saved call is in `DashRenderer._make_figure_body` (dash_render.py:30643, CRITICAL, not edited here). The served call is the generated line at :35405 (`_dash_note_empty_layer(gname, pi + 1, ptype, len(g_df), …)`). The mapper-mark pattern this section reuses is `GlyphMapper._mark_unfit` (:10693) and `_mark_silent` (:10735): a private attribute on the renderer object, never serialised, read by `_dash_note_empty_layer`. The docstring of `_mark_silent` says: "A static method, so the served app, which copies GlyphMapper by source, carries it."

### E4. The Stata note that promises a draw (dash_parse.mata:4251-4266)

```
4251        if (txt == "") {}
4252        else if (_dash_fn_points_ok(txt)) out = q + q + ":" + txt
4253        else _dash_say("txt", "dash: the function points stored for graph '",
4254                       "", "' are not dash's; that layer is drawn from its expression.")
 ...
4261            txt = st_global("dash_fpts_" + nm[i])
4262            if (txt == "") continue
4263            if (!_dash_fn_points_ok(txt)) {
4264                _dash_say("txt", "dash: the function points stored for graph '",
4265                          nm[i], "' are not dash's; that layer is drawn from its expression.")
```

S06 (batch 2) changes both `_dash_say("txt", ` to `_dash_note(` with the same arguments. The comment above (4235-4237) repeats the promise: "the renderers then draw that layer from its expression". FX-08 (`test/test_parser.cscript:2674-2687`) pins only the substring `are not dash's`, and FX-11 (:2728-2752) pins its absence for an empty one-line scalar. Both stay green. Register P1.22.4: reword the tail in this section.

### E5. Measured at `c96facd`, both modes

Python (`m4.py`, `test_function_expr._draw`, no points except where noted):

```
saved  'normalden(x)'      0 ["dash: graph 'g1' plot 1 (function) drew nothing."]
saved  'pi*x'              0 ["dash: graph 'g1' plot 1 (function) drew nothing."]
saved  'x>1'               0 ["dash: graph 'g1' plot 1 (function) drew nothing."]
saved  'sin (x)'           0 ["dash: graph 'g1' plot 1 (function) drew nothing."]
saved  'x' pts {x0,dx}     0 ["dash: graph 'g1' plot 1 (function) drew nothing."]
saved  'sin(x)'            3 []
served (the same six lines, identical)
```

Stata (`p1.do` through `scripts/stata_slot.sh`, StataNow 19.5, `set linesize 255`):

```
* A: dash function y = normalden(x), range(-3 3) n(7) name(nd); macro drop dash_fpts_nd; dash build, saving("p1a.html") replace
.../dash_render.py:28406: UserWarning: dash: graph 'nd' plot 1 (function) drew nothing.
A rc=0
* B: ... name(ng); global dash_fpts_ng {"1":"abc"}; dash build, saving("p1b.html") replace
dash: the function points stored for graph 'ng' are not dash's; that layer is drawn from its expression.
.../dash_render.py:28406: UserWarning: dash: graph 'ng' plot 1 (function) drew nothing.
B rc=0
* C: ... name(ns); macro drop dash_fpts_ns; dash build, saving("p1c.py") server replace
C rc=0                       (no note at all: P1.26 F5a, S23's)
* D: dash function y = sin(x), range(0 2) n(5) name(sn); macro drop dash_fpts_sn; dash build, saving("p1d.html") replace
D rc=0                       (no note: the fallback draws sin)
```

After a filter move. Saved: no `CustomJS` takes the function source as an argument (0 found, scratch `move.py`; pinned for stored points by `TestStoredPoints::test_the_points_survive_a_filter_move`), so a move cannot change it. Served: after firing the `foreign` dropdown, the function source still has 0 rows, and the move raised no warning:

```
served after move: sources 1 rows [0] move notes: []
```

### E6. The served app

These are already on the functions tuple of `_glyph_layer_lines` and copied by name: `"_dash_function_points",` (dash_render.py:33126), `"_stata_fn_parse", "_stata_fn_eval",` (33127), `"_dash_layer_drew_anything",` (33135), `"_dash_report_empty_layer",` (33136) and `"_dash_note_empty_layer",` (33137). `GlyphMapper` is copied whole by the class loop (:33436, `for _cls in (OptionTranslator, SchemeParser, GlyphMapper):`). So the edits of TR-26.1-TR-26.6 reach the served app with no copy-list change:
- the parser and the two note helpers are edited in place;
- `_mark_needs_points` and `_needs_points_why` are `GlyphMapper` static methods that read no module-level name.

Index R2's row S26 ("+ any helper after `"_dash_function_points",` (33126)") is therefore used for nothing. If an executor finds it must add a module-level helper after all, it stops, runs `gitnexus impact _glyph_layer_lines -d upstream -r dash` (HIGH at `c96facd`), warns, and adds the name after `"_dash_function_points",` (manifest note).

### E7. The help (dash.sthlp:413-418)

```
413 panel; only random draws differ.  A dashboard spec written by hand without
414 the points is drawn by {cmd:dash} itself, with the same operators and
415 missing values, {cmd:x}, {cmd:_pi} and ten functions -- {cmd:sin},
416 {cmd:cos}, {cmd:tan}, {cmd:exp}, {cmd:log}, {cmd:log10}, {cmd:sqrt},
417 {cmd:abs}, {cmd:floor} and {cmd:ceil}; anything else draws that layer
418 empty, and a note names it.
```

No test reads this paragraph (`grep -rln "ul:Functions\|{cmd:ceil}\|cmd:log10" test/` finds nothing). dash.sthlp:511-516 makes setting registry macros by hand unsupported. :413 documents how a hand-written spec is drawn, and the renderer has a `--spec/--data/--output/--mode` command line (dash_render.py:36675). So the disposition reads "a hand-written spec is drawn by the documented ten-function fallback" (register P1.22.1), not "unsupported".

### E8. The tests that pin today's behaviour

Flipped in task 26-07, never deleted:

| Node | Pins at `c96facd` | Why it flips |
|---|---|---|
| `test/test_empty_layer_report.py::TestALayerThatDrawsNothingIsNamed::test_a_function_whose_expression_is_rejected_is_reported` (:105-117) | `== ["dash: graph 'g1' plot 2 (function) drew nothing."]` for `__import__('os')` | The note now says why: `__import__() is not one of them`. |
| `test/test_empty_layer_report.py::TestALayerThatDrawsNothingIsNamed::test_a_rejected_function_is_reported_when_no_row_is_selected` (:119-130) | the same text under `if_expr y > 1000` | The same reason. |
| `test/test_immediate_dashboards.py::TestARejectedExpressionIsStillReported::test_with_data_or_none` (:381-390; 4 ids, mode × data) | `== ["dash: graph 'a1' plot 1 (function) drew nothing."]` | The same reason. |
| `test/test_conformance.cscript` C-03 (needle at :425; control comment at :204-217; control set at :230) | `cert_log_has … needle("dash: graph 'ctl' plot 1 (function) drew nothing.")`, count 1 | The `ctl` control is a points object with no y value (case H). Its note now ends `…, and the points this spec carries for it cannot be read.`, so the needle with the bare period no longer matches. |

Guards that must stay green unedited, since they count notes or use substrings:
- `test/test_function_expr.py`:
  - `TestHostilePoints::test_bad_points_draw_nothing` (one `drew nothing` note per hostile object);
  - `TestStataGrammarFallback::test_what_twoway_refuses_draws_nothing`;
  - `TestAgainstTheFixture::test_every_fallback_probe`;
  - `TestTheParserIsBounded::test_nesting_is_capped`;
  - `TestTheParser::test_refusals` and `::test_ascii_names_only` (they need `ValueError` only);
  - `TestStoredPoints::test_the_points_survive_a_filter_move` and `::test_null_points_draw_silently`;
  - `TestNoEval::test_the_mapper_cannot_evaluate_python`.
- `test/test_immediate_dashboards.py::TestTheReportHelpers::test_a_function_is_reported_whatever_the_data` and `::test_the_words`. They call the helpers with no mark, so the bare form is unchanged.
- `test/test_server_layer_defects.py::TestALayerThatDrewNothingSaysSoInBothModes::test_a_rejected_function_expression_is_reported`, `::test_the_report_names_the_layer_that_failed` and `::test_no_type_is_reported_empty_in_only_one_mode` (saved equals served).
- `test/test_layer_reports.py::TestASmootherTwowayDrawsInSilenceIsSilent::test_mark_silent_marks_each_renderer`.
- `test/test_parser.cscript` FX-08 and FX-11; `test/test_wp29_truth.cscript` FX-20..FX-24.
- `scripts/release_verdict.py:50` keeps the substring `"drew nothing"`.

### E9. Blast radius (`gitnexus impact <symbol> -d upstream -r dash`, index at `c96facd`)

| Symbol | Risk | Note |
|---|---|---|
| `GlyphMapper.map_function` | LOW (3; processes `_build_sources_and_figures`, `_make_figure_body`) | Copied into the served app with its class. |
| `GlyphMapper` (two methods added) | LOW (6; the `scripts/fncov` and `regen_*` scripts) | Nothing outside them reads the class. |
| `_dash_note_empty_layer` | LOW (3; 2 processes) | Called by both renderers. |
| `_dash_report_empty_layer` | LOW (3; 1 process) | grep: called only by `_dash_note_empty_layer` (:28406, :28408) and by tests. |
| `_stata_fn_parse` | LOW (3; `_make_figure_body`) | A text copy in the served app; 8 test files call it. Treat it as yellow: `str(exc)` must not change. |
| `ServerAppBuilder._glyph_layer_lines` | HIGH (4; `main`, `_generate_app_source`, `scripts/fncov` mains) | **Not edited** (E6). |
| `_dash_fn_spec_tail` (Mata) | UNKNOWN (Mata is not indexed) | grep: called at dash.ado:6782 and :8062 only, and declared at :249. Recorded as unresolved, never as low. |

No CRITICAL symbol is edited: `_make_figure_body` and `_generate_app_source` are untouched.

## User stories

- **US-26.1** As a twoway user who opens a dashboard spec written by hand, I want a function layer dash cannot draw to tell me why and what would draw it, naming the function, instead of an empty plot and a bare "drew nothing". (US-30.19)
- **US-26.2** As a dashboard publisher, I want the same note from the saved page and from the served app, and from `dash build, server` in my Stata log, so the two modes cannot disagree about an empty layer.
- **US-26.3** As a twoway user, I want dash's notes never to promise a draw that will not happen, such as "that layer is drawn from its expression" for `normalden(x)`.
- **US-26.4** As the maintainer, I want P1.22 recorded closed by WP-29 P0.6 plus this note (M12), with the premise pinned against twoway, so the item does not stay open over a fallback kept by design.

## Business requirements

- **BR-26.1** Every function layer of a graph registered in Stata draws twoway's own points in both modes, before and after a filter move, for every expression the item names (WP-29 P0.6, unchanged; pinned here).
- **BR-26.2** A function layer without Stata's points that the fallback cannot evaluate draws nothing and gives exactly one note, in both modes. The note:
  - says the layer needs the points Stata computes when dash registers the graph;
  - lists what dash evaluates without them;
  - names the first function (as `name()`) or bare name it met, or says the expression cannot be read.
  It is true for every input, including `pi`, `e`, `PI`, `E` and `sin (x)` (register P1.22.3).
- **BR-26.3** Stored points that cannot be read draw nothing and give one note that names that cause.
- **BR-26.4** The note reaches Stata from a saved build and from `dash build, server`, once each, and the build ends rc 0.
- **BR-26.5** A layer the fallback can draw (the ten functions, `x`, `_pi`, numbers, operators), an expression missing everywhere, and stored points all stay silent, as today.
- **BR-26.6** The Stata note for stored points that are not dash's says they are not used and how to store Stata's. It no longer says the layer is drawn from its expression.
- **BR-26.7** The help states the fallback's rule and the note, and no longer says a note names something it did not name.
- **BR-26.8** Nothing from the spec reaches the page through this path, and the only spec text the note echoes is a plain name of at most 32 characters.

## Technical requirements

- **TR-26.1 `_stata_fn_parse` carries the refused name** (dash_render.py:28693; the raises at :28779 and :28788). Replace `raise ValueError("unknown function")` with:

  ```python
                    exc = ValueError("unknown function")
                    exc.dash_refused = ("function", name)
                    raise exc
  ```

  and `raise ValueError("unknown name")` with the same three lines for `("name", name)`, at that branch's indentation.
  - Add one sentence to the docstring's `Raises:`: "A refusal at a name carries it as ``exc.dash_refused``, ``("function" | "name", <name>)``, for the empty layer's note (WP-30 P1.22)."
  - No message text, token or grammar rule changes (manifest: "no change to the _stata_fn_parse/_stata_fn_eval grammar").
  - The function stays self-contained (the served copy is verbatim).
  - `_stata_fn_eval` is not edited.
- **TR-26.2 `GlyphMapper._mark_needs_points(renderers, why)`** (new `@staticmethod`, directly after `_mark_silent` and before `_masked_index`, dash_render.py:10756). Its body is `_mark_silent`'s loop, setting `_r._dash_needs_points = str(why)` inside `try/except (AttributeError, TypeError): pass`, and it returns `renderers`. The docstring says: a function layer drawn empty for want of Stata's points; a private attribute of the Python object, never serialised; read by `_dash_note_empty_layer` in both modes; a static method so the served app, which copies `GlyphMapper` by source, carries it (WP-30 P1.22).
- **TR-26.3 `GlyphMapper._needs_points_why(exc=None) -> str`** (new `@staticmethod`, directly after TR-26.2). It reads no module-level name and imports nothing. It returns, exactly:
  - `exc is None` (stored points that cannot be read): `"it needs the points Stata computes for it when dash registers the graph, and the points this spec carries for it cannot be read"`.
  - Otherwise: `"it needs the points Stata computes for it when dash registers the graph, and this spec carries none; without them dash evaluates only x, _pi, numbers, + - * / ^ and sin(), cos(), tan(), exp(), log(), log10(), sqrt(), abs(), floor() and ceil(), and " + tail`, where the tail is:
    - `"<shown>() is not one of them"` when `exc.dash_refused` is `("function", name)`;
    - `"the name <shown> is not one of them"` when it is `("name", name)`;
    - `"the expression cannot be read with them"` for anything else.
  - **The name check.** `got = getattr(exc, "dash_refused", None)`. The name is used only if all of these hold: `got` is a `tuple` of length 2; `got[0] in ("function", "name")`; `got[1]` is a non-empty `str`; `got[1].isascii()`; `got[1][0].isalpha() or got[1][0] == "_"`; and `all(c.isalnum() or c == "_" for c in got[1])`. Otherwise the expression tail is used.
  - `<shown>` is the name when it has at most 32 characters, else its first 32 characters followed by `...`.
  - No nested `def` and no lambda, so that `function_test_map.py` gains only two keys.
- **TR-26.4 `map_function`'s two empty returns** (E2).
  - :14915-14916 becomes `return self._mark_needs_points(_empty(), self._needs_points_why())`.
  - :14929-14930 becomes `except ValueError as exc:` / `return self._mark_needs_points(_empty(), self._needs_points_why(exc))`.
  - The `_MAX_EXPR_CHARS` return (:14926) and the evaluation-error return (:14938) are unchanged. The first already has its own note, and the mark must not add a third (critic 3); the second is unreachable (E2).
  - In the docstring, replace "A points object that is not valid (``_dash_function_points``) draws the layer empty, and the caller notes it." and "Anything else … draws the layer empty." with sentences saying that the layer is drawn empty and marked (`_mark_needs_points`) with the reason `_needs_points_why` words, which `_dash_note_empty_layer` gives in both modes (WP-30 P1.22).
  - A later section that adds an empty return to `map_function` for want of points marks it the same way.
- **TR-26.5 `_dash_report_empty_layer(gname, index, ptype, rows=None, why="")`** (:28331). Before the `warnings.warn`, add `reason = f": {why}" if why else ""`. The message becomes `f"dash: {where} ({ptype}) drew nothing{tail}{reason}."`. With `why` empty the text is byte-identical to today's (pinned by `TestTheReportHelpers::test_the_words`). Add one docstring sentence for *why*.
- **TR-26.6 `_dash_note_empty_layer`'s function branch** (:28405-28406, after S23's edits). It becomes:

  ```python
      if pt == "function":
          why = ""
          for _r in renderers or ():
              _w = getattr(_r, "_dash_needs_points", "")
              if isinstance(_w, str) and 0 < len(_w) <= 1000:
                  why = _w
                  break
          _dash_report_empty_layer(gname, index, ptype, why=why)
  ```

  - A mark on any other type is never read, and a mark that is not a `str` of 1-1,000 characters is ignored.
  - In the docstring's function bullet, add: "drawn empty for want of Stata's points, it says why (``GlyphMapper._mark_needs_points``, WP-30 P1.22)".
  - Every other branch, S23's `layer_rows` handling included, is unchanged.
- **TR-26.7 The Stata note** (dash_parse.mata, `_dash_fn_spec_tail`, E4; after S06 the two calls are `_dash_note(…)`). In both calls, replace the third argument `"' are not dash's; that layer is drawn from its expression."` with `"' are not dash's and are not used; run the graph's dash command again to store Stata's points."`.
  - The remedy is true here: the graph is in dash's registry, so Stata already evaluated it once.
  - In the comment at 4235-4237, replace "is skipped with a note; the renderers then draw that layer from its expression" with "is skipped with a note; the renderers then draw that layer as a spec without points, and name what they cannot evaluate (WP-30 P1.22)".
  - The header index (dash_parse.mata:95-100: "skipped with a note") stays true and is not edited. No new Mata function, so there is no `_needed` entry.
- **TR-26.8 Both modes, before and after a filter move.**
  - Saved: the mark and the note are made at build. No `CustomJS` reads the function source, so a move changes neither (guard G2).
  - Served: `make_document` runs the same `map_function` and `_dash_note_empty_layer`. A move leaves the layer empty and raises nothing (E5; guard G2).
  - No JS twin: no page script computes or reports a function layer.
  - Copy lists: no entry added or moved (E6).
- **TR-26.9 Maps.** Under the anchor `# WP-30 S26 (P1.22): function: closed by disposition (P1.22 under M12)` in `test/function_test_map.py` `FUNCTIONS`, in alphabetical order:
  - `'GlyphMapper._mark_needs_points': 'test/test_function_expr.py::TestTheNeedsPointsMark::test_mark_needs_points_marks_each_renderer'`;
  - `'GlyphMapper._needs_points_why': 'test/test_function_expr.py::TestTheNeedsPointsMark::test_the_why_of_each_refusal'`.

  `program_coverage_map.py` is not edited: no new program, and `_dash_fn_spec_tail`'s entry (:518-519, FX-10 and FX-08) still covers it.
- **TR-26.10 Help** (dash.sthlp:413-418, R3 row "Plot types (S26: :413-418)"). Replace everything from "A dashboard spec written by hand without" through "empty, and a note names it." with this text, keeping line 413's opening "panel; only random draws differ.  ":

  ```
  panel; only random draws differ.  A dashboard spec written by hand, which
  carries no points, is drawn by {cmd:dash} itself, with the same operators
  and missing values, {cmd:x}, {cmd:_pi} and ten functions -- {cmd:sin},
  {cmd:cos}, {cmd:tan}, {cmd:exp}, {cmd:log}, {cmd:log10}, {cmd:sqrt},
  {cmd:abs}, {cmd:floor} and {cmd:ceil}.  Any other function, name or form
  draws that layer empty, saved or served, with one note: the layer needs
  the points Stata computes when {cmd:dash} registers the graph, and the
  note names the first function or name it uses that {cmd:dash} cannot
  evaluate ({cmd:normalden()}, {cmd:pi}), or says that the expression
  cannot be read.  Stored points that cannot be read get the same note.
  Registering the graph with {cmd:dash} computes its points in Stata, or
  refuses the expression as {cmd:twoway} does.
  ```

  No other paragraph is edited (A155). S27 edits a different paragraph of "Plot types".
- **TR-26.11 Parity** (`test/test_mode_parity.py`, R8).
  - Append to the end of `CORPUS` (before its closing `]`, :1798 at `c96facd`, after any earlier section's cases): `_case("function without points needing Stata (WP-30 P1.22)", [_sc(), plot_for("function", {"range": "0 2", "n": "3"}, expr="normalden(x)")])`.
  - Append to the end of `_MUST_WARN` (before its `}`, :1931) the entry `"function without points needing Stata (WP-30 P1.22)": "dash: graph 'g1' plot 2 (function) drew nothing: it needs the points Stata computes for it when dash registers the graph"`, with the comment `# WP-30 P1.22: the fallback names what it needs, in both modes.`
  - `ALLOWED` is not edited, and no existing `_MUST_WARN` entry is edited.
- **TR-26.12 Security (rule 1).**
  - The note echoes only a name that passes TR-26.3's check, cut at 32 characters. The expression itself is never echoed by this path.
  - The note goes to Stata through S06's `_dash_emit_note` (SMCL-escaped, controls replaced, at most 4,000 characters). It never reaches HTML or JS: the mark is a private Python attribute, never serialised (guard G3).
  - `_dash_note_empty_layer` accepts only a `str` mark of at most 1,000 characters.
  - No `eval`, `compile` or `exec` (guard G4 and `TestNoEval`), and no `shell=True`.
  - The Stata note's graph name comes from dash's own registry and passes through S06's `_dash_note`, which SMCL-escapes it, as today.
- **TR-26.13 How the note reaches Stata** (no code here).
  - Saved build: raised inside `main()`, printed by S06's `_dash_note_scope` as `(note:  dash: graph '…' plot … (function) drew nothing: …)`.
  - `dash build, server`: S23's trial render re-issues it once.
  - `dash serve`: S23's relay, with the first session until S46 (IR-10).
  - Tests count it by substrings, never by its `(note:` wrapper (S06 hand-off).

## Boundaries

- **Not edited:**
  - `_stata_fn_parse`'s grammar, its messages and its token rules;
  - `_stata_fn_eval`, `_dash_function_points`, `_dash_function_args` and `_dash_attach_function_points`;
  - `_dash_fn_points` and every other dash.ado program;
  - `_dash_fn_points_ok`;
  - the `_MAX_EXPR_CHARS` note;
  - `DashRenderer._make_figure_body` (CRITICAL) and `ServerAppBuilder._generate_app_source`/`_glyph_layer_lines` (HIGH);
  - `_dash_emit_note`, `_dash_note_scope` and Mata `_dash_note` (S06's);
  - S23's trial, app hook, relay and `layer_rows` handling;
  - `function_expr_truth.json` and `scripts/extract_function_truth.do`.
- **Excluded by M12 and the register:**
  - extending the fallback to Stata's data-free language (research option B; manifest residual item 22, a candidate P2 item);
  - removing the fallback (option C);
  - a Stata-side note for a dropped `$dash_fpts_<name>` (register P1.22.2: renderer note only).
- **Batch partners (batch 9).**
  - S25 owns `_dash_dep_fail`, `_DASH_MIN_PYTHON`, the generated header in `_generate_app_source`, `_dash_require_deps` and its calls in `dash`, `_dash_xm_load` and `_dash_do_render`, dash_setup's first Python call, `test_env_guards.cscript`, the setup scripts and the Dependencies help.
  - S27 owns `_dash_finish_auto_bases`, `_dash_finish_count_ticks`, S21's `_dash_refinish_axes` and `_DASH_AXIS_FINISH_JS`, `_dash_units_to_axis`, the bar, area, spike and dropline default base, and its own Plot types paragraph.
  - S26 touches none of these.
- **Later sections that edit `map_function`:**
  - S35 (batch 12: `range()` in date units);
  - S40 (14: `_dash_join_glyph`, function bridging);
  - S45 (16: derived-type tails under `recast()`);
  - S49 (17: `horizontal`).

  Each keeps `_mark_needs_points` on the two empty returns of TR-26.4. Earlier: S19 (batch 7, the legend key) and S24 (batch 8, alpha at construction).
- **Residuals named, not closed here** (register P1.22.1):
  - `range(varname)` (P2.14);
  - `droplines()`/`base()` on function (P2.7);
  - `horizontal` on function (P1.9, S49/S55);
  - by() evaluated once per graph where twoway evaluates per panel (P2.31).
- **Tracking documents** (GAPS2.md, DROPIN-REMAINING.md, ROADMAP.md, TWOWAY_COVERAGE_AUDIT.md, AGENTS.md) are S58's (A145). Their text is in Notes.

## Stata truth

**No new extractor or fixture** (manifest: "No extractor"). The twoway truth this section rests on is:
- research M1 (E1), quoted with its command;
- the existing `test/fixtures/function_expr_truth.json`, read unchanged (`_meta`: `stata_version` 19.5, `born_date` 12 Aug 2026, `extracted` 1 Oct 2026, `dash_commit` e77651e…; `TestTheFixture::test_meta_keys` pins the four keys);
- the live comparison FN-01 below.

No `git add -f` is needed: no `*.json` is added.

**Probes run for this file** (03oct2026, `scripts/stata_slot.sh <scratch>/s26probe <scratch>/s26probe/p1.do`; the do-file opens with `adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"` and `global dash_nobrowser 1`). The commands and output are in E5. The same do-file run against the prototype copy (`p1p.do`, `adopath ++` the prototype) printed:

```
.../dash_render.py:28447: UserWarning: dash: graph 'nd' plot 1 (function) drew nothing: it needs the points Stata computes
A rc=0
dash: the function points stored for graph 'ng' are not dash's and are not used; run the graph's dash command again to store Stata's points.
.../dash_render.py:28447: UserWarning: dash: graph 'ng' plot 1 (function) drew nothing: it needs the points Stata computes
B rc=0
C rc=0
D rc=0
```

The first and third lines wrap at linesize 255. This is why every check counts with `cert_log_has`. The `UserWarning` form is pre-S06; at the batch-9 base it prints as `(note:  dash: …)`.

### FN-01: the disposition's premise (guard; `test/test_wp30_truth.cscript`, S26's block)

The helpers go directly above S26's header (R1, TR-01.10 item 4), each declaring `version 19`. They are copies of `test_wp29_truth.cscript`'s `_fx_serset` and `_fx_stored`, in the form those have at the batch-9 base, renamed:

```stata
capture program drop _s26_serset
program define _s26_serset
    version 19
    preserve
    serset set `.Graph.plotregion1.plot1.serset.id'
    serset use, clear
    mata: st_matrix("s26_sy", st_data(., 1)')
    restore
end
capture program drop _s26_stored
program define _s26_stored
    version 19
    args name
    mata: _s = st_global("dash_fpts_" + st_local("name")); _a = strpos(_s, `""y":["') + 5; _t = substr(_s, _a, strpos(substr(_s, _a, .), "]") - 1); _v = tokens(_t, ","); _v = select(_v, _v :!= ","); st_matrix("s26_dy", strtoreal(_v))
end
```

The cases sit between S26's own `display as text "S26 start …"` and `"S26 end …"` lines, under the gate `if inlist("`only'", "", "S26") {`:

```stata
    // FN-01: the thirteen expressions DROPIN P1.22 names are drawn from
    // Stata's points: stored == twoway's serset, and the saved page and the
    // served app draw them.
    sysuse auto, clear
    quietly regress mpg weight
    scalar s26s = 2
    dash clear
    local s26_list `" "normalden(x)" "normal(x)" "ln(x)" "_pi*x" "c(pi)*x" "(x>1)*x" "cond(x>1,x,0)" "min(x,1)" "max(x,1)" "round(x)" "int(x-1)" "scalar(s26s)*x" "_b[_cons]+_b[weight]*x" "'
    local k 0
    local s26_names ""
    foreach e of local s26_list {
        local ++k
        quietly twoway function y = `e', range(0.1 2) n(5) nodraw
        _s26_serset
        matrix s26_want_`k' = s26_sy
        capture noisily dash function y = `e', range(0.1 2) n(5) name(fn01_`k') title("fn01_`k'")
        _w30_expect FN-01 "(_rc == 0)" `"dash function y = `e' r(`=_rc')"'
        _s26_stored fn01_`k'
        mata: st_local("s26_eq", strofreal(st_matrix("s26_dy") == st_matrix("s26_sy")))
        _w30_expect FN-01 "(`s26_eq' == 1)" `"`e': stored y differs from twoway's serset"'
        local s26_names `s26_names' fn01_`k'
    }
    local s26_html "`w30_work'/s26.html"
    local s26_app  "`w30_work'/s26_app.py"
    quietly dash build, saving("`s26_html'") replace nobrowser
    quietly dash build, saving("`s26_app'") server replace
    global s26_names "`s26_names'"
    global s26_html "`s26_html'"
    global s26_app "`s26_app'"
    python:
    ... _s26_plots_saved(path) and _s26_plots_served(path): byte-for-byte copies of
        test_wp29_truth.cscript's _fx_plots_saved / _fx_plots_served as they stand
        at the batch-9 base (S23 may have adapted the served one), renamed;
    ... for each name fn01_k in _M.getGlobal("s26_names").split(): in each mode take the
        plot titled fn01_k, its renderer whose data_source holds "x_fn", the y_fn values
        ordered by x_fn, and compare with _X.get("s26_want_" + k)[0] (missing as NaN;
        equal means same length and every pair equal or both NaN); collect
        "<mode>:<name>:<first four y>" for each difference;
    ... _M.setGlobal("s26_bad", " ".join(bad))
end
    _w30_expect FN-01 `"("${s26_bad}" == "")"' `"drawn points differ: ${s26_bad}"'
    _w30_done FN-01 "thirteen expressions: stored, saved and served points are twoway's serset"
    dash clear
    capture erase "`s26_html'"
    capture erase "`s26_app'"
    macro drop s26_names s26_html s26_app s26_bad
    capture scalar drop s26s
```

Python reads Stata values only through `Macro.getGlobal` and `Matrix.get`, never through a macro inside a Python string (hygiene). There is no `capture python:` probe, so no hygiene pin moves.

### FN-02..FN-05: the note reaches Stata (`test/test_parser.cscript`, one contiguous run at the end of its last case block)

The run goes after LB-43's second `macro drop lb_pfail` (:2854 at `c96facd`, outside its `if`) and before `capture erase "`c(tmpdir)'dash_p1a_run.log"`. It uses the script's `_p1a_logrun` (linesize 255) and `cert_log_has`, which rejoins wrapped lines. The header comment (lines 1-6) gains `*!        FN-02 through FN-05 (a function layer without Stata's points, WP-30 P1.22)`. Each case is `assert` style, as FX-08 is. Removing `$dash_fpts_<name>` by hand is the one Stata route into the fallback (research M2), and a comment says so (dash.sthlp:511-516).

```stata
// ================================================================
// FN-02..FN-05 (WP-30 P1.22) -- a function layer without Stata's points
// says what it needs, saved and served, and stored points that are not
// dash's are said to be unused.  Dropping $dash_fpts_<name> is the one
// route from Stata into the points-free fallback.
// ================================================================
sysuse auto, clear
dash clear
dash function y = normalden(x), range(-3 3) n(7) name(fn02)
macro drop dash_fpts_fn02
local h02 "`c(tmpdir)'dash_fn02.html"
capture erase "`h02'"
_p1a_logrun `"dash build, saving("`h02'") replace"'
assert r(rc) == 0
local lg02 "`r(log)'"
cert_log_has "`lg02'", needle("drew nothing: it needs the points Stata computes for it when dash registers the graph")
assert r(count) == 1
cert_log_has "`lg02'", needle("normalden() is not one of them")
assert r(count) == 1
capture erase "`h02'"
display "FN-02 PASS: a saved build names normalden() as what the fallback cannot evaluate, once, rc 0"

local a03 "`c(tmpdir)'dash_fn03.py"
capture erase "`a03'"
_p1a_logrun `"dash build, saving("`a03'") server replace"'
assert r(rc) == 0
local lg03 "`r(log)'"
cert_log_has "`lg03'", needle("drew nothing: it needs the points Stata computes for it when dash registers the graph")
assert r(count) == 1
cert_log_has "`lg03'", needle("normalden() is not one of them")
assert r(count) == 1
capture erase "`a03'"
dash clear
display "FN-03 PASS: dash build, server prints the same note once, rc 0"

dash function y = normalden(x), range(-3 3) n(7) name(fn04)
mata: st_global("dash_fpts_fn04", `"{"1":"abc"}"')
local h04 "`c(tmpdir)'dash_fn04.html"
capture erase "`h04'"
_p1a_logrun `"dash build, saving("`h04'") replace"'
assert r(rc) == 0
local lg04 "`r(log)'"
cert_log_has "`lg04'", needle("are not dash's and are not used; run the graph's dash command again to store Stata's points.")
assert r(count) == 1
cert_log_has "`lg04'", needle("drawn from its expression")
assert r(count) == 0
cert_log_has "`lg04'", needle("normalden() is not one of them")
assert r(count) == 1
capture erase "`h04'"
dash clear
display "FN-04 PASS: points that are not dash's are said to be unused, and the layer's note names normalden()"

dash function y = sin(x), range(0 2) n(5) name(fn05)
macro drop dash_fpts_fn05
local h05 "`c(tmpdir)'dash_fn05.html"
capture erase "`h05'"
_p1a_logrun `"dash build, saving("`h05'") replace"'
assert r(rc) == 0
cert_log_has "`r(log)'", needle("drew nothing")
assert r(count) == 0
capture erase "`h05'"
dash clear
display "FN-05 PASS: a function the fallback knows draws without a note"
```

At the batch-9 base:
- FN-02 fails at its second `cert_log_has` (count 0): the bare note has no reason.
- FN-03 fails the same way, because S23 prints the bare note there.
- FN-04 fails at its first needle (the old wording).
- FN-05 passes (a guard).

### Running them

Through the driver ("The cscript driver"; `<repo>` is `$WT`):

```sh
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_wp30_truth.cscript > "$S/run_test_wp30_truth.do"
WP30_ONLY=S26 /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_wp30_truth.do"   # log: $S/run_test_wp30_truth.log
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_parser.cscript > "$S/run_test_parser.do"
/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_parser.do"                      # log: $S/run_test_parser.log
printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" test_conformance.cscript > "$S/run_test_conformance.do"
/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh "$S" "$S/run_test_conformance.do"                 # log: $S/run_test_conformance.log
```

A section never runs `run_all_cscripts.do` or `make cert`. After each run, `~/.stata19/console/stata19.rc` must still hold `python_exec`. A run that ends in `SKIP` or r(222) is not a pass.

## TDD test stubs

`test/test_function_expr.py` gains four classes at its end, after `TestNoEval`, and three module-level constants beside `_REFUSED`:
- `_NEEDS_STATA_FUNCS = {"normalden(x)": "normalden", "normal(x)": "normal", "ln(x)": "ln", "c(pi)*x": "c", "cond(x>1,x,0)": "cond", "min(x,1)": "min", "max(x,1)": "max", "round(x)": "round", "int(x-1)": "int", "scalar(s)*x": "scalar", "invlogit(x)": "invlogit", "__import__('os')": "__import__"}`;
- `_NEEDS_STATA_NAMES = {"pi*x": "pi", "e*x": "e", "PI": "PI", "E": "E", "s*x": "s", "_b[_cons]+_b[weight]*x": "_b", "sin (x)": "sin"}`;
- `_NO_NAME = ["x>1", "(x>1)*x", "x^", "sin(x,1)", "2x", "ｓｉｎ(x)", "1>normalden(x)", "x**2"]`.

Also `_HEAD = "dash: graph 'g1' plot 1 (function) drew nothing: it needs the points Stata computes for it when dash registers the graph"` and `_KNOWS = "without them dash evaluates only x, _pi, numbers, + - * / ^ and sin(), cos(), tan(), exp(), log(), log10(), sqrt(), abs(), floor() and ceil()"`. The module docstring gains a paragraph: P1.22 is closed by disposition (M12), and the fallback names what it needs.

### Regression tests (written by 26-01; each fails at `batch-9-base`)

- Test: `test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_a_function_it_does_not_know_is_named` — `@pytest.mark.parametrize("mode", MODES)` on the class, `expr` over `sorted(_NEEDS_STATA_FUNCS)`. `_draw(mode, expr)`: `len(y) == 0`; `_empty_notes(warns)` is one note, equal to `_HEAD + ", and this spec carries none; " + _KNOWS + ", and " + name + "() is not one of them."`. Fails at base: the one note is `"dash: graph 'g1' plot 1 (function) drew nothing."`.
- Test: `…::TestTheFallbackSaysWhatItNeeds::test_a_name_it_does_not_know_is_named_as_a_name` — over `_NEEDS_STATA_NAMES`. The one note ends `", and the name " + name + " is not one of them."`, and for `sin (x)` it does not hold `"sin() is not one of them"`. Fails at base as above.
- Test: `…::TestTheFallbackSaysWhatItNeeds::test_other_forms_name_nothing` — over `_NO_NAME`. The one note ends `", and the expression cannot be read with them."` and holds no `" is not one of them"`. Fails at base.
- Test: `…::TestTheFallbackSaysWhatItNeeds::test_points_that_cannot_be_read_say_so` — `case` over `sorted(_HOSTILE)` (the existing table). `_draw(mode, "x", points=points, raw=raw)` draws nothing and gives one note equal to `_HEAD + ", and the points this spec carries for it cannot be read."`. Fails at base.
- Test: `…::TestTheFallbackSaysWhatItNeeds::test_the_echoed_name_is_capped` — `"a" * 4000 + "(x)"` gives one note holding `"a" * 32 + "...() is not one of them."` and not `"a" * 33`. `"b" * 40 + "*x"` holds `"the name " + "b" * 32 + "... is not one of them."`. Fails at base.
- Test: `test/test_function_expr.py::TestTheNeedsPointsMark::test_the_parser_names_what_it_refused` — `_parse("normalden(x)")` raises a `ValueError` whose `str()` is `"unknown function"` and whose `dash_refused == ("function", "normalden")`. `"pi*x"` gives `"unknown name"` and `("name", "pi")`. `"ln(x)+normalden(x)"` gives `("function", "ln")` (the first refusal). `"x>1"` raises with `getattr(exc, "dash_refused", None) is None`. Fails at base: `assert None == ('function', 'normalden')`.
- Test: `…::TestTheNeedsPointsMark::test_mark_needs_points_marks_each_renderer` — modelled on `test_layer_reports.py:696`. With `f = figure()` and `a, b = f.line(x=[], y=[]), f.line(x=[], y=[])`: `_mark_needs_points(a, "W") is a`; `_mark_needs_points([a, b], "W")` returns the list and sets `a._dash_needs_points == b._dash_needs_points == "W"`; `_mark_needs_points([object()], "W")` raises nothing. Fails at base: `AttributeError: type object 'GlyphMapper' has no attribute '_mark_needs_points'`.
- Test: `…::TestTheNeedsPointsMark::test_the_why_of_each_refusal` — `why = dr.GlyphMapper._needs_points_why`:
  - `why()` is the points text;
  - `why(ValueError("x"))` ends with the expression tail;
  - for crafted `ValueError`s with `dash_refused` set: `("function", "normalden")` ends `"normalden() is not one of them"`; `("name", "pi")` ends `"the name pi is not one of them"`; `("function", "a" * 40)` ends `"a" * 32 + "...() is not one of them"`;
  - each hostile value gives the expression tail and its text appears nowhere in the result: `("function", "{bf:x}")`, `("function", "é")`, `("function", "")`, `("name", "9x")`, `("call", "x")`, `["function", "x"]`, `("function", 5)`, `("function", "a b")`.

  Fails at base: `AttributeError`.
- Test: `…::TestTheNeedsPointsMark::test_the_note_lists_exactly_what_the_fallback_knows` — `ast.parse(textwrap.dedent(inspect.getsource(dr._stata_fn_parse)))`. The `Assign` to `funcs` gives the tuple of ten names. `re.findall(r"(\w+)\(\)", why(ValueError("x")))[:10] == list(funcs)`, and the text holds `"x, _pi, numbers, + - * / ^"`. Fails at base: `AttributeError`.
- Test: `test/test_function_expr.py::TestTheReasonedReport::test_a_reason_follows_drew_nothing` — under `warnings.catch_warnings(record=True)` and `simplefilter("always")`:
  - `dr._dash_report_empty_layer("g1", 3, "function", why="it needs x")` gives `["dash: graph 'g1' plot 3 (function) drew nothing: it needs x."]`;
  - `why=""` gives the bare form.

  Fails at base: `TypeError: _dash_report_empty_layer() got an unexpected keyword argument 'why'`.
- Test: `…::TestTheReasonedReport::test_the_function_branch_reads_the_mark` — `r = figure().line(x=[], y=[])`:
  - with `r._dash_needs_points = "W"`, `dr._dash_note_empty_layer("g1", 2, "function", 0, [r])` gives `["dash: graph 'g1' plot 2 (function) drew nothing: W."]`;
  - unmarked, it gives the bare `"… drew nothing."`;
  - the same marked renderer as `"scatter"` with rows 6 gives `"… (scatter) drew nothing from 6 observations."` (the mark is ignored);
  - a mark of `5` or of `"x" * 1001` gives the bare form.

  Fails at base: the marked call gives the bare form.
- Test: `test/test_function_expr.py::TestTheHelp::test_the_fallback_rule_is_stated` — read dash.sthlp. Take the text from `{ul:Functions.}` to the second `{pstd}` after it, remove `{cmd:` and `}`, and collapse whitespace. It holds `"carries no points"`, `"needs the points Stata computes when dash registers the graph"`, `"names the first function or name it uses that dash cannot evaluate"`, `"Stored points that cannot be read get the same note"` and `"Registering the graph with dash computes its points in Stata"`, and not `"a note names it"`. Fails at base.
- Test: `test/test_mode_parity.py::TestTheTwoModesAgree::test_same_warnings[function without points needing Stata (WP-30 P1.22)]` (TR-26.11). Fails at base: `neither mode reported "dash: graph 'g1' plot 2 (function) drew nothing: it needs the points …"`.
- Test: `test/test_parser.cscript` FN-02, FN-03 and FN-04 ("Stata truth"). Each fails at base at the needle named there.

### Guard tests (green at the base and after; listed apart, G1)

- Test: `test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_a_function_it_knows_draws_silently` — over `["sin(x)", "_pi*x", "x^2", "log10(x+1)"]`: three values drawn, no `_empty_notes`.
- Test: `…::TestTheFallbackSaysWhatItNeeds::test_a_filter_move_changes_nothing`. The spec is `mp._spec([_fn_plot("normalden(x)"), mp._sc()], build_options={"filter": "foreign, type(dropdown)"})`.
  - Saved: no `CustomJS` argument is the function source (the loop of `TestStoredPoints::test_the_points_survive_a_filter_move`).
  - Served: `mp._fire` the Select to "Foreign" under `catch_warnings(record=True)`. The function source still has 0 rows, and no warning was recorded.
- Test: `test/test_function_expr.py::TestTheNeedsPointsMark::test_the_mark_is_never_serialised` — in mode, render `normalden(x)` with no points. Saved: `file_html(r._last_layout_root.document, CDN)`. Served: `file_html(mod._dash_test_doc, CDN)`. The text holds neither `"_dash_needs_points"` nor `"it needs the points"`.
- Test: `test/test_function_expr.py::TestTheNeedsPointsMark::test_the_new_code_evaluates_nothing` — `TestNoEval`'s pattern finds no `eval(`, `compile(` or `exec(` in `inspect.getsource` of the two new methods. At base it skips: `pytest.skip` when the methods are absent, so it is recorded as not run, never as a pass.
- Test: `test/test_mode_parity.py::TestTheTwoModesAgree` (all ids but `test_same_warnings`) `[function without points needing Stata (WP-30 P1.22)]`.
- Test: `test/test_wp30_truth.cscript` FN-01 and `test/test_parser.cscript` FN-05.

### Pinned tests flipped (26-07; E8)

- `test/test_empty_layer_report.py::TestALayerThatDrawsNothingIsNamed::test_a_function_whose_expression_is_rejected_is_reported`
- `test/test_empty_layer_report.py::TestALayerThatDrawsNothingIsNamed::test_a_rejected_function_is_reported_when_no_row_is_selected`
- `test/test_immediate_dashboards.py::TestARejectedExpressionIsStillReported::test_with_data_or_none`
- `test/test_conformance.cscript` C-03

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| The fallback names the function, the name or the expression | pytest `TestTheFallbackSaysWhatItNeeds` (3 tests, 27 cases × 2 modes) | inline specs | yes |
| Stored points that cannot be read say so | pytest `test_points_that_cannot_be_read_say_so` (13 × 2) | `_HOSTILE` | yes |
| The echo is a plain name, at most 32 characters | pytest `test_the_echoed_name_is_capped`, `test_the_why_of_each_refusal` | inline | yes / unit |
| The parser carries the name; its messages are unchanged | pytest `test_the_parser_names_what_it_refused`; `TestTheParser` (unchanged) | — | unit |
| The note lists exactly the fallback's ten functions | pytest `test_the_note_lists_exactly_what_the_fallback_knows` (ast of `_stata_fn_parse`) | — | unit |
| The report helpers word it, and read only a valid mark | pytest `TestTheReasonedReport` | — | unit (both modes call them) |
| What the fallback knows stays silent | pytest `test_a_function_it_knows_draws_silently`; `TestStataGrammarFallback`, `TestAgainstTheFixture` (unchanged) | `function_expr_truth.json` | yes |
| After a filter move | pytest `test_a_filter_move_changes_nothing`; `TestStoredPoints::test_the_points_survive_a_filter_move` | inline | yes |
| Nothing reaches the page | pytest `test_the_mark_is_never_serialised`, `test_the_new_code_evaluates_nothing`, `TestNoEval` | — | yes |
| Saved equals served, and the note is made | pytest `test_mode_parity.py -k needing` (G3) | CORPUS | yes |
| The note reaches Stata, saved and `dash build, server` | cscript `test_parser.cscript` FN-02, FN-03 | — | yes |
| The Stata note stops promising a draw | cscript FN-04; FX-08, FX-11 (unchanged) | — | n/a |
| A known function stays silent in Stata | cscript FN-05 | — | saved |
| The premise: 13 expressions draw twoway's points | cscript `test_wp30_truth.cscript` FN-01 | live serset | yes |
| The flipped pins | pytest the three nodes; cscript `test_conformance.cscript` C-03 | — | yes |
| Help | pytest `TestTheHelp` | dash.sthlp | n/a |
| Registries and served guards (G4) | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`, `test_cscript_hygiene.py`, `test_tracking_documents.py` | — | — |
| Full suite | the queue script, once (E1; task 26-10) | — | — |

**Acceptance criteria.**
- **AC-26.1** For each of the 12 functions in `_NEEDS_STATA_FUNCS`, a spec without points draws an empty function layer and exactly one note, `…drew nothing: it needs the points Stata computes for it when dash registers the graph, and this spec carries none; without them dash evaluates only x, _pi, numbers, + - * / ^ and sin(), …, floor() and ceil(), and <name>() is not one of them.`, identical in the saved page and the served app.
- **AC-26.2** `pi*x`, `e*x`, `PI`, `E`, `s*x`, `_b[_cons]+_b[weight]*x` and `sin (x)` name `the name <n>`. The eight forms of `_NO_NAME` say `the expression cannot be read with them`. No note echoes more than 32 characters of a name or any other text of the expression.
- **AC-26.3** All 13 hostile points objects give the one note ending `the points this spec carries for it cannot be read.`
- **AC-26.4** FN-02 and FN-03 print the note exactly once in Stata's log for a saved build and for `dash build, server`, with rc 0. FN-04 prints `are not dash's and are not used; run the graph's dash command again to store Stata's points.` once and `drawn from its expression` never. FN-05 prints no `drew nothing`.
- **AC-26.5** FN-01 prints `FN-01 PASS`: the 13 expressions' stored, saved and served points equal twoway's serset.
- **AC-26.6** After a filter move, both modes keep the layer empty and add no note. No page holds the mark or the note.
- **AC-26.7** `TestTheParser`, `TestStataGrammarFallback`, `TestAgainstTheFixture`, `TestHostilePoints` and the `test_server_layer_defects.py` guards pass unedited. The four pins are flipped in place, each with a `Flipped:` line.
- **AC-26.8** dash.sthlp:413-418 states the rule (TR-26.10), and `awk 'length > 79' dash.sthlp | grep -c "carries no points"` prints 0.
- **AC-26.9** Entry `P1.22` is closed in place with its Resolution, its `WP30_OPEN` key is gone, and its one `<!-- WP-30 P1.22 -->` marker is replaced by the line of Notes. `test_tracking_documents.py` is green.
- **AC-26.10** The full suite is green once in the worktree (E6 for the four known flaky tests). The commit holds exactly the 14 files of 26-10.

## Tasks

**Commit boundary.** All ten tasks form the one commit of entry `P1.22`, made by task 26-10 on `wp30-s26` with the subject `Name what a function layer without Stata's points needs (WP-30 P1.22)`.
- `$X` is `/private/tmp/claude-501/-Users-billy-Desktop-Programs-StataPrograms-d-dash/55d6df3b-6200-4eb1-99b7-fa28b88519a2/scratchpad/wp30` (the orchestrator's `<scratch>`: the batch base, impact record, ratified record, queue script and the failure file live there), and `$S` is `$X/s26` (`mkdir -p "$S"`), this section's own directory for driver files, logs and Stata's `STATATMP`, so S25 and S27, running at the same time, never share a driver or log name.
- `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s26`.
- Every command runs with `git -C "$WT"` or with `$WT` paths, never in the main checkout.
- pytest runs from `$WT` (`cd "$WT" && python3 -m pytest …`).

<task type="auto" id="26-01">
  <name>Write the failing tests and record them</name>
  <files>test/test_function_expr.py, test/test_mode_parity.py, test/test_parser.cscript</files>
  <action><![CDATA[
    Check that `git -C "$WT" rev-parse HEAD` equals `cat "$X/batch-9-base.txt"` and that `git -C "$WT" branch --show-current` prints `wp30-s26`; stop otherwise. Read `$X/batch-9-impact.txt`, `$X/wp30-ratified.txt` (rows 13 and 14 bind S06's note form and S23's `dash build, server` trial; stop and report if either is struck), and S23's landed form of `_dash_note_empty_layer`, `_dash_report_empty_layer` and the served trial (`grep -n "def _dash_note_empty_layer\|def _dash_report_empty_layer\|_DASH_TRIAL" "$WT/dash_render.py"`). In `test/test_function_expr.py`:
    - add `import textwrap` and `from bokeh.embed import file_html`, `from bokeh.resources import CDN`, `from bokeh.plotting import figure`;
    - add `_NEEDS_STATA_FUNCS`, `_NEEDS_STATA_NAMES`, `_NO_NAME`, `_HEAD` and `_KNOWS` after `_REFUSED`;
    - append classes `TestTheFallbackSaysWhatItNeeds` (mode-parametrized), `TestTheNeedsPointsMark`, `TestTheReasonedReport` and `TestTheHelp` with every stub of "TDD test stubs" (regression and guard), referencing the new names as `dr.GlyphMapper._mark_needs_points` and `dr.GlyphMapper._needs_points_why` so that they fail with AttributeError now.

    In `test/test_mode_parity.py` append the CORPUS case and the `_MUST_WARN` entry of TR-26.11, at the ends of both, after any earlier section's entries. In `test/test_parser.cscript` add the FN-02..FN-05 run and the header line of "Stata truth". Run `python3 -m pytest test/test_function_expr.py -q -n0 -p no:cacheprovider -rf -k "TestTheFallbackSaysWhatItNeeds or TestTheNeedsPointsMark or TestTheReasonedReport or TestTheHelp" > "$S/26-new.log" 2>&1` and `python3 -m pytest test/test_mode_parity.py -q -n 4 -p no:cacheprovider -rf -k needing >> "$S/26-new.log" 2>&1`, then `test_parser.cscript` through the driver ("Stata truth", Running them). Write `$X/26-P1.22-failure.txt`, cutting every path to its last component (Notes trap 7):
    - the base sha;
    - one `FAILED …` line with its first `E ` line for each regression test;
    - the first failing `assert` of `run_test_parser.log` (FN-02);
    - a `Guards (pass at base):` list of the guard tests that passed, and the skip of `test_the_new_code_evaluates_nothing`.

    Because `test_parser.cscript` stops at FN-02's assert, run FN-03 and FN-04 alone too: copy the script's preamble up to `_p1a_logrun`'s `end`, then each case, into `$S/26-fn03.do` and `$S/26-fn04.do`, and record their first failing assert. Do not commit, and do not edit `dash_render.py` or `dash_parse.mata`.
  ]]></action>
  <verify><![CDATA[`grep -c '^FAILED' "$S/26-new.log"` is at least 60 (27 named cases × 2 modes, 13 hostile × 2, and the unit, help and parity tests). `grep -c 'PASSED\| passed' "$S/26-new.log"` shows the guards passing. `grep -n 'FN-02\|assertion is false' "$S/run_test_parser.log"` shows FN-02 failing at its normalden needle. `test -s "$X/26-P1.22-failure.txt"`. `grep -Eic 'claude|anthropic' "$X/26-P1.22-failure.txt"` prints 0. `git -C "$WT" diff --name-only -- dash_render.py dash_parse.mata` prints nothing.]]></verify>
  <done>Every regression test of P1.22 was shown failing on the unmodified tree, the guards were shown passing, and the failure text was saved for the commit body.</done>
</task>

<task type="auto" id="26-02">
  <name>Fill the truth block with FN-01</name>
  <files>test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    Directly above the line `* ==== S26 P1.22: function: closed by disposition ====` add the helpers `_s26_serset` and `_s26_stored` of "Stata truth". Between S26's own `display as text "S26 start …"` and `"S26 end …"` lines (they stay the block's first and last statements, R1) add FN-01 as given there. Copy `_fx_plots_saved` and `_fx_plots_served` from `test/test_wp29_truth.cscript` in the worktree, byte for byte, renamed `_s26_…`, and write the comparison loop the stub describes. Write files only under `` `w30_work' ``, and erase them before the end line. Run the S26 block alone through the driver (`WP30_ONLY=S26`). FN-01 is a guard: it passes on this unmodified tree. Append `Guard FN-01 PASS at base` to `$X/26-P1.22-failure.txt`.
  ]]></action>
  <verify><![CDATA[`grep -c "FN-01 PASS" "$S/run_test_wp30_truth.log"` prints 1; `grep -c "test_wp30_truth: ALL CHECKS PASSED" "$S/run_test_wp30_truth.log"` prints 1; `grep -c "FN-01 FAIL\|^r(" "$S/run_test_wp30_truth.log"` prints 0; `python3 -m pytest test/test_cscript_hygiene.py -q -n 4 -p no:cacheprovider` passes.]]></verify>
  <done>The truth block showed that the thirteen expressions the item names are stored, saved and served at twoway's serset, which is the premise of the disposition.</done>
</task>

<task type="auto" id="26-03">
  <name>Carry the refused name on parser errors</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `_stata_fn_parse`, find `raise ValueError("unknown function")` and `raise ValueError("unknown name")` by their text (dash_render.py:28779 and :28788 at `c96facd`) and replace each with the three lines of TR-26.1, which set `exc.dash_refused` to `("function", name)` or `("name", name)`. Add the docstring sentence of TR-26.1. Change no message, token rule or other line. `_stata_fn_parse` is LOW (E9), and it is copied verbatim into the served app (E6), so its text must stay self-contained.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_function_expr.py::TestTheNeedsPointsMark::test_the_parser_names_what_it_refused" "test/test_function_expr.py::TestTheParser" "test/test_function_expr.py::TestTheParserIsBounded" "test/test_function_expr.py::TestNoEval" -q -n0 -p no:cacheprovider` passes.]]></verify>
  <done>A refusal at a name carried that name on the ValueError while its message stayed as it was.</done>
</task>

<task type="auto" id="26-04">
  <name>Mark the empty layer with its reason</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    In `GlyphMapper`, directly after `_mark_silent` and before `_masked_index` (dash_render.py:10756 at `c96facd`), add `_mark_needs_points` (TR-26.2) and `_needs_points_why` (TR-26.3). Each is a `@staticmethod` with a docstring giving what it does and why: M12, register P1.22.3, critic 1, and the served copy by class source. Neither reads a module-level name or nests a def. In `map_function`, replace the two empty returns of TR-26.4, found by text, and update its docstring as TR-26.4 says. Leave the `_MAX_EXPR_CHARS` return and the evaluation-error return as they are. Do not touch `_glyph_layer_lines`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_function_expr.py::TestTheNeedsPointsMark" -q -n0 -p no:cacheprovider` passes (all six). `python3 -c "import sys; sys.path.insert(0,'$WT'); import dash_render as d; print(d.GlyphMapper._needs_points_why().endswith('carries for it cannot be read'))"` prints `True`.]]></verify>
  <done>An empty function layer was marked with the reason the fallback could not draw it, in a form the served app carries with GlyphMapper.</done>
</task>

<task type="auto" id="26-05">
  <name>Give the reason after drew nothing</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-26.5 to `_dash_report_empty_layer` (the `why=""` keyword and `reason`) and TR-26.6 to the function branch of `_dash_note_empty_layer`. Both are found by text. Keep S23's `layer_rows` handling and every other branch as S23 left them, and update both docstrings. Both are LOW (E9) and already on the served copy list (dash_render.py:33136-33137 at `c96facd`), so no list changes.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_expr.py -q -n 4 -p no:cacheprovider` passes, all new tests included; `python3 -m pytest test/test_mode_parity.py -q -n 4 -p no:cacheprovider -k needing` passes (11 ids); `python3 -m pytest "test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName" "test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads" "test/test_server_layer_defects.py::TestALayerThatDrewNothingSaysSoInBothModes" "test/test_immediate_dashboards.py::TestTheReportHelpers" test/test_layer_reports.py -q -n 4 -p no:cacheprovider` passes.]]></verify>
  <done>Both modes gave one note saying why an empty function layer drew nothing, and every layer the fallback can draw stayed silent.</done>
</task>

<task type="auto" id="26-06">
  <name>Stop the Stata note promising a draw</name>
  <files>dash_parse.mata</files>
  <action><![CDATA[
    In `_dash_fn_spec_tail` (dash_parse.mata:4240 at `c96facd`), replace the third argument of both `_dash_note(` calls (S06's form of the `_dash_say("txt", ` calls at :4253 and :4264), `"' are not dash's; that layer is drawn from its expression."`, with `"' are not dash's and are not used; run the graph's dash command again to store Stata's points."`. Rewrite the comment of TR-26.7. Edit no other line, and leave the header index (95-100) as it is. `_dash_fn_spec_tail` is UNKNOWN to GitNexus. grep confirms its callers are dash.ado:6782 and :8062 at `c96facd`; record that as unresolved in `$S/26-impact-notes.txt`. Then run `test_parser.cscript` through the driver.
  ]]></action>
  <verify><![CDATA[`grep -c "that layer is drawn from its expression" "$WT/dash_parse.mata"` prints 0; `grep -c "are not used; run the graph's dash command again" "$WT/dash_parse.mata"` prints 2; `grep -c "FN-0[2-5] PASS\|FX-08 PASS\|FX-11 PASS" "$S/run_test_parser.log"` prints 6; `tail -3 "$S/run_test_parser.log"` shows `All syntax-based parser tests PASSED.`]]></verify>
  <done>The Stata note for stored points that are not dash's said they are unused and how to store Stata's, and every parser case passed.</done>
</task>

<task type="auto" id="26-07">
  <name>Flip the pinned note texts</name>
  <files>test/test_empty_layer_report.py, test/test_immediate_dashboards.py, test/test_conformance.cscript</files>
  <action><![CDATA[
    Flip the four pins of E8 in place. Delete no test and no parametrisation.

    In `test/test_empty_layer_report.py`, change the expected list in `test_a_function_whose_expression_is_rejected_is_reported` and in `test_a_rejected_function_is_reported_when_no_row_is_selected` so that each asserts exactly one report, starting `"dash: graph 'g1' plot 2 (function) drew nothing: it needs the points Stata computes"` and ending `"__import__() is not one of them."`. Add the sentence `Flipped (WP-30 P1.22): the note now says why the fallback drew nothing.` to each docstring, and to the module docstring's description of the function form.

    In `test/test_immediate_dashboards.py`, change `TestARejectedExpressionIsStillReported::test_with_data_or_none` the same way, for graph `'a1'` plot 1.

    In `test/test_conformance.cscript`:
    - C-03's needle (:425) becomes `"dash: graph 'ctl' plot 1 (function) drew nothing: it needs the points Stata computes for it when dash registers the graph, and the points this spec carries for it cannot be read."`;
    - the control comment (:204-217) quotes that text and says why (WP-30 P1.22);
    - bump its `*! Version:` line.

    Write one `Flipped:` line per pin, in the index R9 form, to `$S/26-flips.txt`. Then run `test_conformance.cscript` through the driver.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_empty_layer_report.py test/test_immediate_dashboards.py -q -n 4 -p no:cacheprovider` passes; `grep -c "C-03 PASS" "$S/run_test_conformance.log"` prints 1; `grep -c '^Flipped:' "$S/26-flips.txt"` prints 4.]]></verify>
  <done>The four tests that pinned the bare note were flipped in place, each with its reason, and pass on the new note.</done>
</task>

<task type="auto" id="26-08">
  <name>Map the two new methods</name>
  <files>test/function_test_map.py</files>
  <action><![CDATA[
    Under the anchor `# WP-30 S26 (P1.22): function: closed by disposition (P1.22 under M12)` in `FUNCTIONS`, add the two entries of TR-26.9 in alphabetical order. Edit no other anchor or entry. `program_coverage_map.py` is not edited (TR-26.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n 4 -p no:cacheprovider` passes.]]></verify>
  <done>The two new GlyphMapper methods were mapped to the unit tests that run them.</done>
</task>

<task type="auto" id="26-09">
  <name>State the rule in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    In dash.sthlp, find the sentence that begins "A dashboard spec written by hand without" (413 at `c96facd`) and ends "empty, and a note names it." (418). Replace it, keeping the opening "panel; only random draws differ.  " of its first line, with the text of TR-26.10. Lines are at most 74 characters, as in the paragraph around it. Edit no other paragraph (A155, R3).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_function_expr.py::TestTheHelp" test/test_help_conformance.py -q -n 4 -p no:cacheprovider` passes; `awk 'length > 79' "$WT/dash.sthlp" | grep -c "carries no points\|registers the graph, and the"` prints 0.]]></verify>
  <done>The help said how a spec without points is drawn, what note an empty layer gives, and how registering the graph draws or refuses it.</done>
</task>

<task type="auto" id="26-10">
  <name>Close the entry and make the commit</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.22"]`. In BUGS.md:
    - close that entry in place (`- [x]`);
    - replace its Resolution line with the text of "Notes: BUGS.md Resolution", today's date in `ddmonyyyy`;
    - leave its File Names, Description and Suggested fix as written.

    Delete the `"P1.22"` key line of `WP30_OPEN` in `test/test_tracking_documents.py`. In CHANGELOG.md, replace the one `<!-- WP-30 P1.22 -->` (under `### Fixed in WP-30`) in place with the line of "Notes: CHANGELOG line", quoting the old note from `$X/26-P1.22-failure.txt`.

    Run `python3 -m pytest test/test_tracking_documents.py test/test_cscript_hygiene.py -q -n0 -p no:cacheprovider`. Run `git -C "$WT" merge --no-edit main`, expecting `Already up to date.` (stop and report if main moved). Launch one full run, `"$X/full_suite_queue.sh" "$WT" "$S/26-full-1.log"`, in the background, and wait for its `exit=` line, reading the log and never relaunching it (E1; E6 for the four known flaky tests).

    Stage exactly these 14 files and check that `git -C "$WT" diff --cached --name-only` lists them and nothing else (G6): `dash_render.py dash_parse.mata dash.sthlp BUGS.md CHANGELOG.md test/test_function_expr.py test/test_mode_parity.py test/test_parser.cscript test/test_wp30_truth.cscript test/test_empty_layer_report.py test/test_immediate_dashboards.py test/test_conformance.cscript test/function_test_map.py test/test_tracking_documents.py`.

    Write the message to `$S/26-message.txt` in the form of "Notes: commit message". Check that `grep -Eic 'claude|anthropic' "$S/26-message.txt"` prints 0, confirm the branch prints `wp30-s26`, commit with `git -C "$WT" commit -F "$S/26-message.txt"`, and check the committed message the same way. Report the sha, the message, and the expected detect-changes symbols (Notes) to the merger.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/26-full-1.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.22 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.22": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.22)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `git -C "$WT" show --name-only --format= HEAD | wc -l` prints 14.]]></verify>
  <done>Entry P1.22 was closed by disposition, naming tests that exist, its marker was replaced in place, and one green commit on wp30-s26 was ready for the merger.</done>
</task>

## Section completion criteria

- A function layer without Stata's points that the fallback cannot evaluate draws nothing and gives one note naming what it needs and the function, name or expression it met. Stored points that cannot be read say so. Both hold in both modes, before and after a filter move (pytest; parity `-k needing`).
- The note reaches Stata from a saved build and from `dash build, server`, once each, rc 0 (FN-02, FN-03). The Stata note for points that are not dash's no longer promises a draw (FN-04). A known function stays silent (FN-05).
- The premise of the disposition holds: the 13 expressions are stored, saved and served at twoway's serset (FN-01).
- `GlyphMapper._mark_needs_points` and `GlyphMapper._needs_points_why` exist and are mapped. `_stata_fn_parse`'s messages and grammar are unchanged. No copy list, CRITICAL symbol, fixture or extractor changed.
- The four pins are flipped in place, each with its reason, and no test is deleted.
- dash.sthlp:413-418 states the rule.
- One green commit `(WP-30 P1.22)` exists on `wp30-s26`. Its body opens with the failure text and carries the `Regression:`, `Flipped:` and `BUGS.md:` lines. The entry is closed, the key is deleted and the marker is replaced. Exactly the 14 files are changed.

## Notes

**Traps for the executor.**
1. **Find by text.** Batches 2-8 moved every anchor. S06 added helpers above dash_render.py:15342, so `_dash_note_empty_layer` and everything below it moved. S24 edited `map_function`, and S23 edited `_dash_note_empty_layer`. Every TR names its site by quoted text.
2. **S23's shape decides two things.**
   - If S23 changed how the served `make_document` raises warnings (for example a process-wide hook installed when the app module loads), `test_function_expr._render`'s served branch must still record them. Read S23's landed tests and, if needed, record through S23's own served-note helper. Do not edit S23's code.
   - FN-03 relies on S23's `dash build, server` trial (IR-10, ratification row 14). If row 14 was struck, re-plan FN-03 against what S23 landed before 26-01.
3. **Later editors of `map_function`** (S35, S40, S45, S49) must keep `self._mark_needs_points(…, self._needs_points_why(…))` on the two empty returns of TR-26.4. Say so in the method's docstring, and in the hand-off below.
4. **`str(exc)` is a contract.** Eight test files call `_stata_fn_parse` and some match its message. Only the attribute is added.
5. **xdist and `-k`.** A two-word `-k` on `test_mode_parity.py` under `-n` ended in an INTERNALERROR in the prototype. Use `-k needing`.
6. **Wrapped log lines.** The note is about 330 characters. Use `cert_log_has` (it rejoins `> ` continuations), never `cert_file_has`, for every note needle.
7. **G7 and scratch paths.** pytest and Stata print absolute paths, and the scratch path holds a word G7 forbids. Cut every path in `26-P1.22-failure.txt`, `26-flips.txt` and the message to its last component before G7 runs.
8. **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`. A cscript then skips (r(222)), and a skip is not a pass. Check the file after each driver run.
9. **Not a full run.** Iterate with the files of each verify line. The one full run is 26-10's, through the queue.

**Merge rules for the shared files.**
- R1: S26's own block of `test_wp30_truth.cscript` and its helpers directly above its header. FN-02..FN-05 form one contiguous run at the end of `test_parser.cscript`'s last case block (no batch-9 partner appends there). The in-place flip of `test_conformance.cscript` C-03 only.
- R2: no copy-list change (E6). Two map entries under S26's anchor.
- R3/A155: dash.sthlp:413-418 only. S27 edits a different "Plot types" paragraph, and S25 edits Dependencies.
- R4: the one `P1.22` marker under `### Fixed in WP-30`.
- R5: the `P1.22` entry and key only. Its neighbours `P1.21b` and `P1.23a` are not batch-9 entries.
- R6: `_dash_fn_spec_tail` edited in place, with no new Mata function.
- R8: one CORPUS case and one new `_MUST_WARN` entry for that case, appended after earlier sections'. S27 may append after S26's; the merger keeps both. `ALLOWED` is untouched.
- R9: the four flips of E8.
- R10: no pin moves. The single-y page is unchanged, since no function is on it.
- R11: S26 touches no finisher (S27's).
- R12: S26 edits none of the one-editor symbols.
- R13: impact at the base, and `detect-changes` at landing.

**Landing (merger).** `gitnexus detect-changes --scope all --repo dash` after `git apply` lists only:
- `_stata_fn_parse`, `GlyphMapper.map_function`, `GlyphMapper._mark_needs_points` (new), `GlyphMapper._needs_points_why` (new), `_dash_report_empty_layer` and `_dash_note_empty_layer`;
- test symbols of the 14 files.

Mata is not indexed. No HIGH or CRITICAL symbol is touched, so batch 9's expected HIGH for S26 (`_glyph_layer_lines`, "only if it adds a helper") does not arise.

**Commit message** (`$S/26-message.txt`). Subject: `Name what a function layer without Stata's points needs (WP-30 P1.22)`. The body, in order:
1. the contents of `$X/26-P1.22-failure.txt`;
2. the measured defect (E5: the bare note in both modes, nothing from `dash build, server` before S23, and the Stata note's false promise);
3. the disposition: M12; WP-29 P0.6 draws every registered graph from Stata's points, FN-01; the fallback keeps its ten functions by design;
4. what changed and where (TR-26.1-TR-26.7, both modes, no copy-list change);
5. the threat considered: an echoed name is checked and cut at 32 characters, and the note never reaches the page;
6. one line each:
   - `Regression: test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_a_function_it_does_not_know_is_named -- failed at <batch-9 base sha> with <text>`, and likewise for every regression test of "TDD test stubs", with the cscript cases written `test/test_parser.cscript FN-02` … `FN-04`;
   - the four `Flipped:` lines of `$S/26-flips.txt`, for example `Flipped: test/test_empty_layer_report.py::TestALayerThatDrawsNothingIsNamed::test_a_function_whose_expression_is_rejected_is_reported -- the bare "drew nothing." was wrong because the note now says why the fallback drew nothing (WP-30 P1.22, M12)`;
   - `BUGS.md: "The points-free function fallback knows ten functions and draws any other in silence" (closed)`.

There is no `Fixture:` line, and no tool or vendor name appears anywhere (G7).

**BUGS.md Resolution** (one line, in place):

```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.22). Closed by disposition under maintainer decision M12: every function layer of a graph registered in Stata is drawn from the points Stata computes with twoway's own generator (WP-29 P0.6), in the saved page and the served app, before and after a filter move, and the thirteen expressions the item names are pinned against twoway's serset; the points-free fallback, which only a spec without points reaches (one written by hand, or a registry whose points were removed or are not dash's), keeps its ten functions by design. What was left was its silence: such a layer reported only that it drew nothing. Now _stata_fn_parse's refusal carries the function or name it refused (exc.dash_refused, messages unchanged), GlyphMapper.map_function marks the empty layer with the reason (GlyphMapper._mark_needs_points, GlyphMapper._needs_points_why), stored points that cannot be read included, and _dash_note_empty_layer gives one note in both modes -- "drew nothing: it needs the points Stata computes for it when dash registers the graph, and this spec carries none; without them dash evaluates only x, _pi, numbers, + - * / ^ and the ten functions, and normalden() is not one of them" -- naming the function, the bare name (the name pi) or neither (the expression cannot be read with them), with at most 32 characters of a name echoed; the served app carries it inside GlyphMapper, and dash build, server prints it through its trial render. _dash_fn_spec_tail's note for stored points that are not dash's says they are not used and how to store Stata's, where it promised that the layer is drawn from its expression. Pinned by test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_a_function_it_does_not_know_is_named, test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_a_name_it_does_not_know_is_named_as_a_name, test/test_function_expr.py::TestTheFallbackSaysWhatItNeeds::test_points_that_cannot_be_read_say_so, test/test_function_expr.py::TestTheNeedsPointsMark::test_the_why_of_each_refusal, test/test_function_expr.py::TestTheReasonedReport::test_the_function_branch_reads_the_mark, test/test_parser.cscript FN-02, test/test_parser.cscript FN-03, test/test_parser.cscript FN-04, test/test_wp30_truth.cscript FN-01. Residual, deferred (WP-30): extending the fallback beyond its ten functions (research option B, a candidate P2 item); range(varname), droplines() and horizontal on function (P2.14, P2.7, P1.9); under by() the function is evaluated once per graph where twoway evaluates it per panel (P2.31).
```

**CHANGELOG line** (it replaces `<!-- WP-30 P1.22 -->` under `### Fixed in WP-30`; `<old>` is FN-02's bare note as the failure text shows it, `(note:  dash: graph 'g' plot 1 (function) drew nothing.)` at the batch-9 base). Code goes in backticks, since CHANGELOG.md is Markdown:

```
- A `function` layer drawn without Stata's points -- from a dashboard spec written by hand, or a graph whose stored points were removed, cannot be read or are not dash's -- that uses a function or name dash does not evaluate itself (`normalden(x)`, `c(pi)*x`, `cond()`, `min()`, `round()`, `scalar()`, `_b[]`, `pi`) still draws nothing, but now says why, saved and served, and in the log of `dash build, server`: `(note:  dash: graph 'g' plot 1 (function) drew nothing: it needs the points Stata computes for it when dash registers the graph, and this spec carries none; without them dash evaluates only x, _pi, numbers, + - * / ^ and sin(), cos(), tan(), exp(), log(), log10(), sqrt(), abs(), floor() and ceil(), and normalden() is not one of them.)`, where it printed only `<old>`; and the note for stored points that are not dash's no longer says the layer "is drawn from its expression". Every function layer of a graph registered in Stata is drawn from twoway's own points, as since WP-29. (WP-30, P1.22)
```

**Hand-offs to later sections.**
- **S35, S40, S45 and S49** (they edit `map_function`): keep the mark on both empty returns (trap 3). A new empty return caused by missing or unreadable points is marked the same way. An empty return for any other cause is not.
- **S46** (`dash serve`'s warm-up): once the child's first render happens before the server listens, `dash serve` prints this note at launch. No S26 change is needed.

**Notes for the closeout (S58; A145).**
- **DROPIN-REMAINING.md:133 (P1.22):** "Closed by disposition (M12): WP-29 P0.6 (96aa267) draws every registered graph's `function` from Stata's points; the points-free fallback keeps its ten functions and, since <S26 sha> (WP-30 P1.22), names what it needs in both modes. Residuals: `range(varname)` (P2.14), `droplines()` (P2.7), `horizontal` (P1.9, S49/S55), by() per-panel evaluation (P2.31), extending the fallback (option B, a candidate P2 item)." This satisfies the WP-29 closeout rule (wp29 section-15:882) that P1.22's closed annotation names those residuals.
- **GAPS2.md A6** (its Tracked line at GAPS2.md:228; C5 at :719 and :757 is tracked through it): replace the deferred clause "the points-free fallback for hand-written specs knows ten functions" with "the points-free fallback for hand-written specs keeps its ten functions by design and names what it needs (WP-30 P1.22, commit <S26 sha>)". Keep the by(), `range(varname)`, `droplines()` and `horizontal` residuals. A6-a, A6-b and C5-a..C5-f are closed by disposition, so `(WP-30, GAPS2-A6)` is appended to the Resolution when S58 marks A6 closed (the Tracked-line rules of `test/test_tracking_documents.py`, :1076, :1112, :1152, :1199).
- **TWOWAY_COVERAGE_AUDIT.md:99 (AUDIT-53, `function`):** "unevaluated expressions draw nothing with a note" becomes "every registered function is evaluated by Stata (WP-29 P0.6); a spec without points is drawn by a ten-function fallback whose note names what it needs (WP-30 P1.22)".
- **ROADMAP.md, the WP-30 entry:** BR-30.22 as written. A candidate P2 row "Extend the points-free function fallback (research option B: comparisons, `!`, `cond`, n-ary `min`/`max`, `round`, `int`, `ln`, `normal`, `normalden`, `c(pi)`, missing codes; tolerance 1e-12 in the normal tails)" from manifest residual item 22.
- **AGENTS.md invariant** (E7): "A function layer drawn empty for want of Stata's points carries `GlyphMapper._mark_needs_points`'s mark, and `_dash_note_empty_layer` words the reason; every edit of `map_function` keeps it."
- **No REM id** is cited by P1.22. REMAINING.md and GAPS.md are not touched for it.

**Open question for the maintainer:** none. The register settles the note's wording (P1.22.3, neutral), the Stata note's rewording (P1.22.4), renderer-only notes (P1.22.2) and the ordering after S23 (P1.22.5). This file adds three architect-level choices within those rulings:
- the name travels on the `ValueError` (critic 2's preferred form), so `_glyph_layer_lines` is not edited;
- stored points that cannot be read are folded into the same note: the same root cause and the same code (critic 3 H; the register's fold rule), at the cost of flipping C-03;
- the Stata note's remedy "run the graph's dash command again" is used only where a registered graph exists.
