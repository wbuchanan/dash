# WP-29 S15 — 15-06 approval package (02oct2026)

Detail: 15-05-gaps2.tsv / 15-05-gaps2-drafts.md (GAPS2), 15-05-other-sources.tsv / 15-05-other-drafts.md (REMAINING, AUDIT, DROPIN, GAPS.md), wp29-residual-filings.md, wp29-invariants.tsv / 15-05-agents-draft.md. Every test node cited collects.

## 1. GAPS2 classification (24 ids: 11 FULL, 9 PARTLY incl. C4, 3 ANNOTATE, G1 no edit)
- FULL (ROADMAP field, GAPS2 order): A1 (b0d170d), A6+C5 (96aa267), A9+C1,C13 (758cf59), B4 (ab53f25), C7+A10 (e32be3a), F2 (ece0752), F4+H2 (c595259), H7 (4d74922), I2 (cbeef4e), I3 (7f5c8f5; with fd51038), X3 (fd51038).
- PARTLY: A4 (only sort(varlist) closed), A13+C10 (open: fit/lowess/lpoly/mband, pc and immediate keys, mixed y title, y1/y2), B12+G15 (open: horizontal/vertical, recast, connect, cmissing), B15 (axes 3-9, yaxis(1 2)), B16 (rows/holes/i*axes/title/legend in by()), B22 (numlists, lc/lp/lw abbreviations, lstyle/style, noextend), C12, F9, C4.
- ANNOTATE (WP-28 prefix kept): E1 (KPI-spread residual closed, P0.20), G16 (hover-only residual closed; x/y not in hover() still numbered), G3 (counting rule, P0.10). G1: untouched by WP-29.
- Contested — please rule:
  a. A6 FULL: every Gap bullet has a test, but Appendix C made FULL depend on range(varname)/droplines()/horizontal, which are still refused/ignored. Recommend FULL (Gap rule), those filed as P2.7/P2.14 notes.
  b. C12: Appendix C/S11 credit only C12-e; P0.9 tests also pin aw/fw lpolyci bands. Recommend PARTLY crediting both.
  c. F9: S08 credits bullet c only; P0.12a also closed d. Recommend PARTLY (c, d closed; a, b, e open).
  d. I3: S08 note said PARTLY (pre-S13); S13 and Appendix C say FULL. Recommend FULL, D.1 "; with" form.
  e. F2 names ece0752 only (one commit per Tracked line, R15-2).

## 2. C4
Recommend D.4 (a): "Partly closed in WP-29 (P0.17, commit b242b99): stale cue …; open by decision (M3): no re-estimate on the saved page". Alternative (b) keeps the WP-28 deferral with a WP-29 clause. (S12 also lists bins/grid P2.24 and Q22; D.4 text omits them — add "; no build-time note (Q22)"?)

## 3. Other tracking documents
- REMAINING: 14 tags (7 closed, 7 partly). REM-08-05-M3 not located.
- AUDIT: 24 tags + dated line; :116 left untagged (its claim is still true).
- DROPIN: 20 P0 annotations, 5 §4 decisions (M1-M4), 22 notes on P1/P2/P3 items.
- GAPS.md: L10 and E1 paragraphs, plus two more sentences WP-29 made false: A4 (lpoly bandwidth/bootstrap "stay as they were") and F3 (sort(varlist) "Unsupported"). Approve all four?

## 4. Residual filings (all to DROPIN, none as BUGS.md entries; none graded P1)
New P2.30-P2.40: S02 join-order edge cases; S04 by() evaluated once + y-form message; S05 fractional periods floored; S06 hover() inside+after comma; S07 colorvar refusals/keys; S08 private-files/lifecycle (shared non-sticky tmpdir, leftover folders, 0.25 s KILL window, F2 erase timing, previews/Windows pruning); S11 SD-10, D1-D8; S12 lpoly own-if on five domestic rows draws empty line (unchecked vs twoway); S13 key residuals 2-8 (incl. SIGTERM leaves link folder, bokeh serve needs --allow-websocket-origin, first session refused); S14 embedded-rows (computed-layer rows, served .py/data on disk, $dash_max_cells, served brush mapper-copy index, size notes); S09 OQ4/OQ6.
Notes on existing items: P1.3, 4, 8, 9, 15, 16, 17, 18, 22, 23, 26, 30, 34; P2.2, 7, 14, 18, 21, 24, 28; P3.2, 12.
Not filed: csv embeds every row (contract), hand-run .py (documented), no saved-page refit (M3).
Also for the record: S10 by() 100-panel settle 7.98 s (bound 30 s accepted), S11 1e-4 tier / 1e-6·var(y) / ~2e-151 pwidth band rulings, S08 GUI Break via patched pollstd only, Linux/Windows unmeasured.
Ratification-introduced divergences: S05 kept date axis (documented divergence, not residual).

## 5. Invariants: 20 AGENTS.md paragraphs
Join order; variable labels; function points; Stata units; hover export; a view's own rows; colour key; private files + verified launch; parent watch; Break r(1); setup's children (run_child); by() sharing; build-time served notes; lpoly port + lpvar key; copied helpers read no computed constant (guard tests check callees/defined names, not "non-literal" directly — accept?); saved stale cue; empty layer style; served redraw widths; per-launch key; embedded rows.

## 6. Recorded exceptions (maintainer ruled)
CHANGELOG 39 lines accepted; E2 exceptions cd210ea, 529875d; K3: one renamed test (help_claims_2) whose Flipped line names the class, not the old name.
