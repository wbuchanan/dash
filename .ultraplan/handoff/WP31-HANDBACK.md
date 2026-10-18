# WP-31 hand-back (closeout, 18oct2026)

WP-31 (close the GAPS3 drop-in gaps) is done on `s3-bugs`. Batches 0-20 landed sections S01-S60; S61 (this closeout) ran in the main checkout. The ROADMAP.md section "WP-31 · Close the GAPS3 drop-in gaps — DONE" has the full record.

## What landed

There are 143 WP-31 entries: 110 at the plan (DECISIONS A12) plus 33 added by D14-D36. Each is closed in BUGS.md or recorded as a residual. These are the entries by section (WP31_SECTION):

S02 C1; S03 C2 B5a; S04 C3; S05 C10a; S06 C10b C18 F4; S07 A5 A6 A7 A8; S08 A1 A2 A3 A4; S09 C10c; S10 F1a; S11 C4; S12 C5; S13 F1b; S14 C6 C7; S15 C8a A3d; S16 F1c; S17 C8b; S18 B5b; S19 F1d; S20 C9 A5b; S21 B1 B2 B3; S22 F1e C11b; S23 B4a; S24 D1; S25 F1f C6b; S26 B4b C8e; S27 D2 A3b; S28 F1g; S29 B4c B4d; S30 D3 D13 D2b; S31 D4 C13; S32 D5 E11 A3c C8d; S33 D6 D7 E6 D1c; S34 D8 C17 E3 C14 C15; S35 D9 C10e B5c D1b D6b; S36 D10 D3b; S37 D11; S38 D12; S39 D14 D16 D16b D4b D10b D11b; S40 E1 E2 E12; S41 E4 E5 E7 E8 E13 C4b C17b; S42 E9 D13b; S43 G1 G2 G3 G4 G5; S44 E10 C8c E11b D10c; S45 D15 D9b D1d; S46 C11 C12 C16 G6 G7 F5 C10d; S47 F2 F3 C18b; S48 H2t; S49 H2f; S50 H2k; S51 H2l; S52 H1; S53 H2x; S54 K6; S55 H3 H4 H7 G3c G3d; S56 J1 J2 E10b; S57 J3; S58 J4 J5 J6; S59 I2 I3 I4 I5 I7; S60 K2 K3 K4 H6 I6.

The GAPS3 rows came out as follows:
- **Closed:** 87.
- **Partly closed:** 7 (G3, H3, H6, I3, K2, K3, K4).
- **Outside WP-31:** H5, I1, K1 (handled as flips inside each section) and K5.

## The S61 commits

| Step | Commit | Subject |
|---|---|---|
| S61.1 | dac025b | Date every shipped file and the distribution date 18oct2026 (WP-31 S61.1) |
| S61.2 | 7e5c51a | Date the 0.1.0 release line and tidy the WP-31 lists (WP-31 S61.2) |
| S61.3 | fa1118b | Close WP-31's tracking: no entry, Tracked line or marker left open (WP-31 S61.3) |
| S61.4 | d705d3b | Fix the axe fetch race found by the WP-31 closeout gates (WP-31 S61.4) |
| S61.5 | 4547107 | Record WP-31 as done with its measurements and time its truth blocks (WP-31 S61.5) |
| S61.6 | (this file) | Hand back WP-31 (WP-31 S61.6) |

## Measurements

All gates ran on s3-bugs, 18oct2026, StataNow 19.5 MP on macOS arm64.

| Gate | Result | Time |
|---|---|---|
| Full pytest (`python3 -m pytest test/ -q`, 8 workers) | 27,473 passed, 8 skipped, 5 xfailed, 0 failed | 898 s |
| `make cert` (three sessions) | 69 of 69 scripts passed, no SKIP, verdict PASS | 804 s wall |
| `make gate` | 14 of 14 examples and 26 of 26 scheme pages clean; venv sessions clean; PASS | 105 s |
| axe-core over the 14 example pages the gate built | 14 passed, 0 violations | about 10 s |

- **make cert shards.** The scripts in each shard summed to 802 s, 640 s and 685 s.
- **axe run.** The first run had 12 passes and 2 errors. The errors came from a race when two workers fetched axe-core at the same time; S61.4 fixed it and added a regression test.
- **Whole batch-end run.** 1,807 s. The batch-20 run took 1,769 s.
- **Index.** GitNexus was re-indexed after the last step.

## Residuals (D-61.b)

Each residual is an open BUGS.md entry graded S3 (WP-31) whose Resolution reads "Not fixed: deferred at WP-31's closeout because ...". Each also has a GAPS3 Tracked line in the Partly form.

| GAPS3 | BUGS.md title | Why deferred |
|---|---|---|
| H6 | Found by the move-parity extension: axes of degenerate or emptied layers after a move | The H6 follow-up ran out of time after fixing the outline, bins and grid causes |
| H6 | Parity guard: the surfaces it does not compare | S60's tasks named no other surface |
| K2 | A renderer without its source file cannot write a served app | D-60e: the missing fallback is documented, not built |
| K3 | Truth fixtures awaiting regeneration | A full `make truth` run (117 scripts) did not fit S60 |
| K4 | Harness guards | S60 closed only the process-leak clause |
| H3 | Served build on the event loop | D-55a: no section owned the make_document restructuring |
| G3 (G3b) | The data file embeds numbers as JSON text (about 0.5 GB per million values) | Stays open past WP-31 (D36) |
| I3 | dash_setup installs by version, not by hash | Hash pinning stays deferred (D38) |

The GAPS3 H6 Partly line now names both H6 entries.

These are the remaining residuals:
- **The five-minute suite target (CLAUDE.md rule 11).** It is not met: pytest takes 898 s and cert takes 804 s.
  - pytest is held up by served-mode probes that each run on a single worker. The largest are:
    - test_size_units.py TestStataRatios: 212 s and 192 s
    - test_bare_intensity.py: 93 s
    - test_by_text.py: three probes of 66-67 s
    - test_added_text.py: 62 s
    - test_intensity_blend.py: 59 s
    - test_by_axes_keys.py: 40 s each
  - cert is held up by test_wp30_truth.cscript (567 s) and test_wp31_truth.cscript (456 s).
- **Expected by the index:**
  - legend text before its symbol (M17)
  - contour above the cap (D4)
  - the platform package (I1)
  - the module split (K5)
  - the H5 design residuals

## Ratified

Pending: the maintainer has not answered task 61-06's checkpoint yet. These items were put to the maintainer:
1. The D-61.b conversions above.
2. The ROADMAP `**GAPS3 closed:**` field has no reader (D-61.d). The choice is to add a reader or accept it as text.
3. The open ratification items from the sections' Notes. DECISIONS.md does not rule on them:
   - **S01:** D-01.g.
   - **S08:** A3's `_SHORTER_THAN_TWOWAY` and D-08.b.
   - **S09 to S20:**
     - S09: D-09.a and D-09.b.
     - S10: D-10.c and D-10.f.
     - S11: D-11e.
     - S12: D-12a and D-12e.
     - S13: D-13.a and D-13.c.
     - S14: D-14a.
     - S15: D-15a and D-15f.
     - S17: D-17a-d.
     - S18: D-18a, c and d.
     - S19: D-19.a-c.
     - S20: D-20a and D-20b.
   - **S22 to S38:**
     - S22: D-22.a and D-22.b.
     - S25: D-25.a and D-25.b.
     - S28: D-28.c.
     - S29: D-29a.
     - S30: D-30.c and D-30.e.
     - S31: D-31.a and D-31.d.
     - S33: D-33.a, b and i.
     - S34: D-34.c and D-34.d.
     - S35: D-35.b.
     - S36: D-36.a, b, c, i, j and k.
     - S37: D-37.a, b, d and e.
     - S38: D-38.c.
   - **S39 to S46:**
     - S39: D-39.b-d.
     - S40: D-40a, f, g and h.
     - S41: D-41b, c and f.
     - S43: D-43f.
     - S44: D-44e.
     - S45: D-45b.
     - S46: D-46b and D-46d.
   - **S48 to S60:**
     - S48: D-48a.
     - S49: D-49a, b and d.
     - S50: D-50a and D-50b.
     - S51: D-51a and D-51d.
     - S52: D-52.d's last clause.
     - S53: D-53b, d and e.
     - S54: D-54a-d.
     - S55: D-55a and D-55b.
     - S56: D-56.c.
     - S60: D-60a, b, e, g and h.

   A change the maintainer asks for will be a new commit `(WP-31 S61.5b)`.

## Merge (reported, not run)

git checkout main && git merge --ff-only s3-bugs
