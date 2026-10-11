# WP-30 plan status (06oct2026)

Done:
- Research (35 notes), decisions M1-M12, decision register, manifest (58 sections, 22 batches), index.md, PLAN.md, section files 01-58.
- Review-and-fix pass of all 57 section files (S31-S36 on 04oct2026; S01-S30 and S37-S57 on 06oct2026, groups g01-g09; notes in `review-notes/`), and the cross-file pass on the section files.
- Whole-plan consistency pass (06oct2026): every review-note fix addressed to index.md, manifest.json, PLAN.md, decision-register.md and open-questions.md applied; index.md checked against the section headers (batch, depends on, blocks, case-id prefix: all agree), merge orders and truth-block order; R2/R3/R9/R10 tables, A139 exceptions, A147 (84 markers, 34/5/7/24/4/10), A152 (S37 added), A153, the batch k.0 expected HIGH/CRITICAL lists and step 0a's P-1 precondition updated; open-questions.md rewritten as a status list.
- Section 58 (closeout) written 06oct2026 (21 tasks); checked by its writer only (consolidated review budget), not by a separate reviewer.
- **Ratified 06oct2026.** The maintainer answered all 44 rows of index.md "Decisions for maintainer ratification": 35 as recommended; rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED; row 29 answered otherwise than recommended. The answers are applied to the section files (each records them under "(ratification 06oct2026)" in its Review amendments), decision-register.md, manifest.json, PLAN.md, index.md and open-questions.md (every question resolved). No row is pending or struck.

Executed (09oct2026):
- Row 29's `_ROOT_ALSO` change committed as 2da4783 (WP-30 P-1); the plan committed as bd05776 (WP-30 S00).
- Batches 0-21 landed on `wp30-p1` (S01-S58), merged into main at af9676f. The closeout's record is ROADMAP.md's WP-30 entry (DONE, "Done, measured (09oct2026)").
- Follow-up branch `wp30-followup` closes the gaps a post-merge audit found (S12, S22, S27/S44, S46, S47, S48 and four stale records).

Remaining: none in this plan. Deferred work is filed as DROPIN-REMAINING.md P2.42-P2.92 and the platform package in ROADMAP.md.
