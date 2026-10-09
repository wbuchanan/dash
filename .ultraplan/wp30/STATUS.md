# WP-30 plan status (06oct2026)

Done:
- Research (35 notes), decisions M1-M12, decision register, manifest (58 sections, 22 batches), index.md, PLAN.md, section files 01-58.
- Review-and-fix pass of all 57 section files (S31-S36 on 04oct2026; S01-S30 and S37-S57 on 06oct2026, groups g01-g09; notes in `review-notes/`), and the cross-file pass on the section files.
- Whole-plan consistency pass (06oct2026): every review-note fix addressed to index.md, manifest.json, PLAN.md, decision-register.md and open-questions.md applied; index.md checked against the section headers (batch, depends on, blocks, case-id prefix: all agree), merge orders and truth-block order; R2/R3/R9/R10 tables, A139 exceptions, A147 (84 markers, 34/5/7/24/4/10), A152 (S37 added), A153, the batch k.0 expected HIGH/CRITICAL lists and step 0a's P-1 precondition updated; open-questions.md rewritten as a status list.
- Section 58 (closeout) written 06oct2026 (21 tasks); checked by its writer only (consolidated review budget), not by a separate reviewer.
- **Ratified 06oct2026.** The maintainer answered all 44 rows of index.md "Decisions for maintainer ratification": 35 as recommended; rows 4, 8, 12, 22, 25, 27, 32 and 36 CHANGED; row 29 answered otherwise than recommended. The answers are applied to the section files (each records them under "(ratification 06oct2026)" in its Review amendments), decision-register.md, manifest.json, PLAN.md, index.md and open-questions.md (every question resolved). No row is pending or struck.

Remaining:
1. Row 29: the one-line `test/test_packaging.py::_ROOT_ALSO` change (naming `PhilSchummSuggestion.md`) is in the working tree, uncommitted. Run the full suite once (`python3 -m pytest test/ -q`), then commit that change on `wp30-p1` in a commit of its own, before step 0a (index step 0a.4).
2. Commit `.ultraplan/wp30/` on `wp30-p1` (index step 0a: `git add -f` for manifest.json; G0 green), after step 0g writes the queue script.
