# UltraPlan Summary — WP-28: close the 22 GAPS2 gaps

## What we're building

Not a feature. A closing of the distance between what `dash` draws and what `twoway` draws.
`dash` accepts `twoway` syntax and renders an interactive HTML dashboard through two renderers in
`dash_render.py`: the saved offline page (JavaScript) and the `bokeh serve` app (Python). The
25 September 2026 audit (`GAPS2.md`, at commit `91d97be`) measured 122 places where the two
disagree with Stata or with each other. This package closes the 22 that hurt most or share one
cause: **fifteen where the page silently draws different numbers, text, colours or rows from
twoway and returns success** (B1, B2, B3, B5, B6, B7, C2, D1, E1, E2, F1, G1, K2, X1, X2), and
seven where a documented capability fails visibly or drifts (E3, E14, G2, G3, G5, G6, G16).

Every fix lands as a failing regression test, then the fix, then a closed BUGS.md entry, in one
commit per gap on `s3-bugs`; truth comes from Stata itself through measured fixtures; the exit
is the existing WP-27 release gate with no open S1 or S2 defect.

## The findings that justify the effort

1. **Axis labels are misread.** `xlabel(1 "2019" 2 "2020" 3 "2021")` draws six unlabelled ticks;
   `10 20 to 40` loses 30; a second label line is lost. (B1, G16)
2. **Scales narrow or invert** where twoway only ever widens: `ylabel(0(20)100)` stops at the
   data maximum, `yscale(range(100))` inverts the axis, `range(20 30)` hides data. (B2)
3. **Textbox abbreviations are drawn as title text**: `title("T", c(red))` draws `c(red)`;
   `ytitle("Volume", axis(2))` titles the left axis; `xtitle("")` draws the variable name. (B3, B6, B7)
4. **Legend `order()` text lands on the wrong keys**, `label()` follows position instead of plot
   number, `-` rows are dropped. (B5)
5. **A histogram silently drops its largest observation** (nlsw88 ttl_exp `bin(27)`: 2245 of
   2246), in Python and in the page's own recount. (C2)
6. **A copied scheme with quoted RGB loses every colour** and draws #606060 with no warning. (D1)
7. **Formats are ignored**: KPI cards ignore `fmt()`, dates ignore the variable's `%t` format on
   every widget, tooltip, axis, label and CSV; a float 0.1 prints seventeen digits. (E1, E3, G6)
8. **Filters lie**: dropdowns rewrite `'01'` to `'1'` and drop the categories `'nan'`, `'None'`,
   `'NaT'`; after a sequence of moves an `exclude()`d card shows rows from a widget state that no
   longer exists. (X1, E2)
9. **`dash serve` reports success with no server running**, and the installer accepts Python and
   Bokeh versions on which every render fails. (F1, K2)
10. **Data handling**: an internal column overwrites a user's variable, string plot variables are
    accepted where twoway refuses them, Unicode names are refused, the data limit counts what the
    page never embeds. (G1, G2, G5, G3)
11. **The saved page and the served app still present the dashboard differently** (viewport,
    dimming, range-layer selection, the bs reflow). (E14)

None of these warns. Every one was reproduced by running the software.

## Scale

**22 gaps (15 S1, 4 S2, 3 S3) · 19 sections · 205 tasks · 4 batches · 32 commits** (21 gap commits, the slot wrapper, four shared components, six closeout steps). Three
review reports raised 111 findings (14 critical, 31 major, 65 minor, 1 compliant); fourteen
decisions (`review/DECISIONS.md` D1-D14) and eight refinement answers (Q24-Q31) settled them,
and every section file was rewritten to them in the fixer pass.

## The decisions that shaped the plan

1. **Sections are components, not severities** (Q2): one display-format writer with a
   JavaScript twin (E1/E3/G6), one textbox grammar (B3/B6/B7), one axis pipeline (B1/B2/G16), one
   filter rule (E2/X1), one launcher/floor fix (F1/K2). Fewest conflicts in `dash_render.py`,
   widest parallel batch.
2. **Truth comes from Stata, once** (Q14, Q31): a shared SVG helper (`scripts/svg_truth.py`,
   `test/cert_svg.do`) and per-family `extract_*_truth.do` scripts write fixtures both suites
   pin, each stamped with the Stata build and dash commit that measured it.
3. **Behaviour stays twoway-quiet** (Q22): an option dash now honours prints nothing; refusals
   are loud and use Stata's codes (r(109), r(110), r(198), r(134)).
4. **One commit per gap, never a red tree** (Q18, D1): the failing tests are written first, run
   against the unmodified tree, recorded, and committed together with the fix, the flipped tests
   and the closed BUGS.md entry; the CHANGELOG quotes the recorded old value (Q24).
5. **One new certification script** (Q28, D11): every twoway or Stata-value comparison joins
   `test/test_gaps2_truth.cscript`; everything else joins the existing script for its area, so
   the certification suite grows by at most about five minutes.
6. **C4/E4 are out** (Q3): the saved page still does not re-estimate fitted lines after a
   filter move; nothing is ported on that account. Third-party scheme files are out (Q30).

## Risk areas

- **[red] S04 Display-format writer core** — `%w.0g` has no documented algorithm; two twins must
  stay identical; the loaders start carrying `%g` formats, which flips pinned tests.
- **[red] S09 Serve launcher and version floor** — child-process plumbing inside Stata's
  embedded Python; three refusal sites; tests that required clamping are inverted.
- **[red] S12 Widgets, tooltips, axes, labels, CSV** — nine sites in both renderers; period
  sliders change the mask's column conversion; the tooltip field pattern is a security guard.
- **[red] S14 Axis labels and value labels** — a new tokenizer, numlist expansion in ado with a
  Python bound, and a hover column that must survive filter moves in both twins.
- **[red] S17 Filters** — the callback architecture changes in both modes under tests that pin
  today's wrong answers.
- **[red] S18 Axis scale extents** — the hull interacts with count ticks, log/date axes, the
  by() common scale and the saved-only range renderers.

## Structure

```
Batch 1  S01 tracking · S03 node runner · S02 SVG truth · S06 schemes · S07 names · S08 varlists/limit · S09 serve/floor · S10 parity     (disjoint files; run together)
Batch 2  S04 formats core (03) · S05 histogram (03) · S13 textbox (02) · S17 filters (03,07) · S16 colorvar (02) · S14 axis labels (02,07)
Batch 3  S18 extents (02,14) · S15 legend (02,13) · S11 KPI cards (04,17) · S12 widgets… (03,04,14,16,17)
Batch 4  S19 closeout
```

Merge order inside a batch is fixed (index.md step 1): S13 → S17 → S16 → S14 in batch 2 for the
functions they share; S18, S15, S11, S12 in batch 3. Every Stata run takes one of three slots
through `scripts/stata_slot.sh`.

## Places you can stop

| Stop after | What the user gets |
|---|---|
| **Batch 1** | The guards can prove closure; quoted scheme values are read (D1); `__dash` names refused and Unicode names accepted (G1, G5); string plot variables refused as twoway does and the data limit counts what the page embeds (G2, G3); `dash serve` fails loudly and the floor is honest (F1, K2); saved and served present alike (E14). Eight gaps. |
| **Batch 2** | Every histogram counts every observation (C2); textbox grammar, axis labels and value labels read as Stata reads them (B3, B6, B7, B1, G16); explicit colorvar forms (X2); filters mask each target by its own filters and compare numbers as numbers (E2, X1). Seventeen gaps. |
| **Batch 3** | KPI cards, widgets, tooltips, date axes, marker labels and the CSV write Stata's display formats (E1, E3, G6); legend order and labels (B5); axis extents are twoway's hull (B2). All 22. |
| **Batch 4** | The release: CHANGELOG, GAPS2 Tracked lines, WP-28 DONE, both suites, the certification suite, the gate from an installed package, the merge command reported. |

## How to execute

1. Create `scripts/stata_slot.sh` (index.md step 0).
2. Say: "Read `.ultraplan/sections/index.md` and execute batch 1" — one agent per section in
   its own worktree, each given its section file, `sections/BRIEF.md`, `DISCOVERY.md`,
   `RESEARCH.md`, `review/DECISIONS.md` and the research report it cites.
3. Merge each finished section with `patch -p1` from its worktree's diff in the batch's merge
   order; run the changed tests; after the batch, the full suite once and the cscripts the batch
   added; commit per gap.
4. Repeat for batches 2 and 3, then S19, which runs `make test`, `make test-dev`, `make cert`,
   `make gate`, regenerates the demo pages, and reports `git checkout main && git merge s3-bugs`
   without running it.

## How to update

Run `/ultraplan update` and describe what changed — only affected sections are regenerated.
