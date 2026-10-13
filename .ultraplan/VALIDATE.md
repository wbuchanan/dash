# Traceability Matrix -- WP-31

> Generated: 2026-10-13 | Phase 5/6 - VALIDATE (final, after the three fixer passes)
> Requirements: DISCOVERY.md Q1-Q40, RESEARCH.md C1-C4, review/DECISIONS.md D1-D8, and GAPS3.md's in-scope rows (section 4.A-4.K less I1/K5, section 5, section 6). Tasks: the XML tasks of sections/section-NN-*.md (task counts are those of the files after the Phase 4 fixer passes; `python3 scripts/..` is not used -- counts come from the files).

## Summary
- Total requirements from discovery and decisions: 52 (Q1-Q40 counted as 40, C1-C4, D1-D8)
- GAPS3 rows in scope: 110 entries (S01 Appendix A; A4/A12 split ids)
- Total tasks in plan: 249 across 61 section files, 116 commits (header, XML and manifest counts agree for every file; see §Mechanical validation)
- Requirements fully covered: 50
- Requirements partially covered: 2 (Q2 and Q29 are scope exclusions honoured by having no task; listed as "excluded by choice")
- Requirements excluded (user choice): Q2 platform package, Q29 module split, Q31 no LICENSE
- Tasks added beyond requirements (approved): S01 tracking foundation and S61 closeout (process, from M13/M2); the register corrections (GAPS3 §6)

## Requirement-to-Section Mapping

| # | Requirement | PRD section | Plan sections | Status |
|---|---|---|---|---|
| Q1 | Scope: twoway-facing rows, docs, tests, packaging basics, accessibility, dashboard extensions | 4, 7 | S02-S60 | Covered |
| Q2 | Platform package deferred | 7 | none | Excluded (user choice) |
| Q3 | Done = every row closed with BUGS entry + pinning test; full suite, cert, gate green | 8 | S01, every fix section's closing task, S61 | Covered |
| Q4/C1/D4 | contour/contourline: Python+JS interpolation, cap 1,000, subsample fallback, cue | 4, 7, 10 | S23, S26, S29 | Covered |
| Q5 | sunflower/matamatrix refused by name | 4, 7 | S21 | Covered |
| Q6 | Batch order: S1 → refused values → named options → fidelity → docs/tests | PLAN | index.md batches 1-20 | Covered |
| Q7-Q9 | Agents in worktrees, three in parallel, 2-3 sections per batch | PLAN | index.md batch table, A2 | Covered |
| Q10 | Optimise for the pasting twoway user | 3 | all fix sections | Covered |
| Q11/C3 | No new dependency | 6, 7 | (constraint; S23 uses numpy only) | Covered |
| Q12 | Stata truth from committed extract scripts | 6, 8 | every section's "Stata truth" + S60 generators | Covered |
| Q13 | Both twins + parity entry for new computed work | 8 | S10-S29, S48, S50, S51 | Covered |
| Q14 | Tracking in GAPS3.md | 8 | S01 | Covered |
| Q15 | Refuse like twoway per option × type | 4 | S04 (+S05, S06, S08, S39) | Covered |
| Q16 | Flip pinned tests, never delete | 8, 10 | BRIEF R9; every section's flips | Covered |
| Q17 | Measure first; scheme files RGB/RGBA only | 7, 8 | every section's measurement-first task; S41/S44 scope | Covered |
| Q18/M8 | Visible cue where the saved page cannot match | 5 | S11, S23/S26, S28, S52 | Covered |
| Q19 | Section runs its own tests; full suite at batch end | PLAN | BRIEF, index G1/G2 | Covered |
| Q20/C2 | 2 s / 100k-row bound; contour exempt | 8 | S10-S29 timing guards; S23 exempt | Covered |
| Q21 | No guard weakened | 7 | BRIEF security rule; S52-S55 | Covered |
| Q22 | Residuals as open BUGS entries + Tracked lines | 8 | BRIEF; S61 | Covered |
| Q23 | One truth cscript + pytest per item | 8 | S01 (script), every section | Covered |
| Q24 | Tracking foundation first | PLAN | S01 | Covered |
| Q25 | Shared glyph layer, never template-only | PLAN | BRIEF R2; index A7 | Covered |
| Q26 | Pending list + help + coverage audit updated in the same commit | 4 | every option section's closing task | Covered |
| Q27 | Eleven estimators ported to JS | 4 | S10, S13, S16, S19, S22, S25, S28 | Covered |
| Q28 | Abbreviation superset refused | 4 | S08 | Covered |
| Q29 | No module split | 7 | none | Excluded (user choice) |
| Q30 | Match scheme-driven layout where Bokeh can; else document | 5 | S24, S27, S30-S33, S36-S41 | Covered |
| Q31 | No LICENSE | 9 | none | Excluded (user choice) |
| Q32 | GitHub distribution now; README + dash.pkg lines | 9 | S59 | Covered |
| Q33 | Version 0.1.0, date moves at closeout | 9 | S59 (pins), S61 | Covered |
| Q34 | Accessibility deliverables | 4 | S54 | Covered |
| Q35 | Five extension groups | 4 | S48, S49, S50, S51, S53 | Covered |
| Q36 | Message style | 5 | BRIEF refusals rule; S04 | Covered |
| Q37 | Minor-tick labels as a LabelSet | 4 | S24 | Covered |
| Q38-Q40/D6 | Data table: per graph (and by() grid), toggle, drawn rows, formats/labels, virtual scroll, sort, cap+note | 4 | S48 | Covered |
| D1 | Custom arrowheads | 4 | S02 | Covered |
| D2 | mlabel minimum `mlab`, mla()=mlalign | 4 | S08, S34 | Covered |
| D3 | estopts layers frozen both modes | 5 | S11 | Covered |
| D5 | tabs() unknown name refused | 4 | S39 | Covered |
| D7 | BUGS preambles rewritten | 4 | S58 | Covered |
| D8 | Release label dropped | 9 | S61 | Covered |
| GAPS3 4.A-4.K rows | one entry each | 4 | index.md manifest (row → section), S01 Appendix A | Covered |
| GAPS3 §5 half-finished code | pending lists, unwired helpers, xfails | 4 | S02-S46 (each names the helper it wires) | Covered |
| GAPS3 §6 register corrections | data edits | 4 | S01 (A6) | Covered |

## Gap Resolution Log
| # | Gap Type | Description | Resolution | Date |
|---|---|---|---|---|
| 1 | Missing requirement | A3 (abbreviation fixture pin) had no section | Added to S08 (index) and to S01's entry table (A12) | 2026-10-10 |
| 2 | Missing requirement | by() graphs had no data table (Q38 "per graph") | D6: one table under the grid with a panel column (S48) | 2026-10-10 |
| 3 | Missing requirement | G3's working-columns clause and D10's bystyles had no task | Residuals G3d (S43) and D-36.k (S36) opened | 2026-10-10 |
| 4 | Missing requirement | G3 axe check on example pages had no task | S61-04 runs axe over the example pages (A30) | 2026-10-10 |
| 5 | Scope creep | S51 claimed an H1b entry | Dropped; H1 stays with S52 (A21) | 2026-10-10 |
| 6 | Scope creep | S32's `inner_width` CustomJS (could never fire) | Replaced by Python frame sizing (A16) | 2026-10-10 |
| 7 | Scope creep | S38's Span/Arrow dual path | One Arrow path (A17) | 2026-10-10 |
| 8 | Excluded | Q2 platform package, Q29 module split, Q31 LICENSE | No tasks; residual list in index.md | 2026-10-10 |

## Review findings resolution

| Review | Sections | Finding rows | Resolved by |
|---|---|---|---|
| REVIEW-1 | S01-S09 | 28 | D1, D2, A11, A12, A32, A33 and the per-finding edits; fixer pass 1 (verified 2026-10-13) |
| REVIEW-2 | S10-S29 | 34 | A19-A23, D3, D4; fixer pass 2 (S13, S16, S26, S28 edited; the rest verified) |
| REVIEW-3, 3b, 3c, 3d, 3e | S30-S46 | 12 + 20 + 19 + 23 + 27 | A15-A18, A24-A27, A31, A34, D2, D5; fixer pass 3 (verified 2026-10-13) |
| REVIEW-4 | S47-S61 | 38 | A21, A23, A28-A30, D6-D8; fixer pass 4 (verified 2026-10-13) |

Tally: 201 finding rows, 7 critical, 70 major, 118 minor, the remainder "no finding" rows.
Every critical and major finding maps to a DECISIONS.md ruling or a section edit; the fixer
reports (kept in this session's transcript) list the lines changed per file. Items REVIEW-4
listed only as minors (R4-27 generator split, R4-28 ubuntu CI runner, R4-29 fixture-meta guard
location) were applied as the review's stated defaults; S60 grew from 4 to 8 tasks so that
every `<files>` stays at three paths (A13).

## Deliberately excluded or deferred

| Row / item | Why | Where recorded |
|---|---|---|
| I1 platform package (Linux, Windows, Intel macOS, Stata 16-18.5, scripted export) | Maintainer: deferred (Q2) | PRD §7, index.md residual list |
| K5 module split of dash_render.py | Maintainer: no split (Q29) | PRD §7, index.md residual list |
| H5 served-key and private-file design residuals | GAPS3 calls them design residuals; documented, no code change | index.md row coverage check; S55 Notes |
| K1 tests pinning the non-twoway behaviour | Not a section: each fix section flips its own pins with a `Flipped:` line (BRIEF R9) | index.md row coverage check; S01 D-01.a |
| LICENSE | Maintainer: do not write one (Q31) | PRD §9 |
| Version bump | Maintainer: 0.1.0, only the date moves (Q33) | S59 pins, S61.1 |
| New Python dependency | Maintainer: none (Q11/C3); numpy and plain JS only | S23, S29 |
| Scheme colour spaces beyond RGB/RGBA | Maintainer: not needed (Q17) | BRIEF rule; S41, S44 scope |
| Contour timing bound | Maintainer: exempt (C2) | S23 TR, index M-list |
| Residuals opened by sections (D6b textstyle/tickstyle/gridstyle in S33/S44, D-36.k bystyles, G3d working columns in S43) | Narrowed by decision; stay open graded S3 with a Tracked "Partly closed" line | S33, S36, S43, S44; S61.3 converts any leftover |

## Mechanical validation (run 2026-10-13 after the fixer passes; read-only)

| Check | Command (repo root) | Result |
|---|---|---|
| XML tasks parse, ids sequential, five fields present, `<files>` ≤ 3, type auto/checkpoint | `python3 <scratch>/xmlcheck.py .ultraplan/sections/section-*.md` | 61 × `ok`; 249 tasks |
| Header `Tasks: n, k commits` = XML count = manifest column | python over the 61 headers and index.md | 0 mismatches; 249 tasks, 116 commits |
| Every row-closing section writes the A11 form | `grep -c "commit pending" section-*.md` | non-zero in all 61 (S01 as the reader's forms) |
| No commit-then-amend routine | `grep -n amend section-*.md` | only negations ("no amend", "never `git commit --amend`") |
| No `commit <sha>` placeholder in a task | `grep -n 'commit <sha>'` | only S01's post-k.3b reader forms and S34's negative verify clause |
| A12: 110 entries, no `109` | `grep -n '\b109\b'` | only anchors (`:1109`, `:10936`) and `r(109)` |
| Every GAPS3 row id named by a section header or recorded as excluded | python over GAPS3.md row ids and the 61 headers | 94 of 98 in headers; H5, I1, K1, K5 as in the table above |
| No row claimed by two sections | manifest row column | split ids only (B4a-c, B5a/b, C8a/b, C10a-c, F1a-g, H2f/k/l/t/x), each in one section |
| Risk and effort tallies | manifest columns | 11 red / 36 yellow / 14 green; 12 S / 41 M / 8 L (index.md:13 agrees) |
| Batch dependencies point backwards | header `Depends on` vs batch numbers | no forward dependency; the one same-batch dependency (06 on 05) has its order recorded in the batch-2 cell (A32); merge orders 50→51→52 and 14→15 are owner-table orderings, not header dependencies |

## Validation result

The plan covers every requirement from DISCOVERY Q1-Q40, RESEARCH C1-C4 and DECISIONS D1-D8,
and every in-scope GAPS3 row, with the exclusions above recorded where an executor will read
them. The 61 section files pass the mechanical checks. Ready for Phase 6 OUTPUT.
