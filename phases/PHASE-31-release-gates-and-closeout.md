# Phase 31 — Release gates and closeout

**Purpose.** This is the phase where "done" is declared, and project rule 2 makes that
declaration binding. Ultraplan task **16-07** is one of only two NOT_DONE tasks in the
whole 89-task plan, and it is NOT_DONE for a structural reason rather than a technical
one: it is gated on everything else. The work here is therefore not to build anything.
It is to *verify* — to run the six release gates and read their output honestly, to
re-run S10's responsive procedure at 375px, 768px and 1440px because responsiveness is
the conference abstract's headline claim and this is the last chance to check it, to
reconcile `BUGS.md`'s 73 closed entries against the CHANGELOG's defect list so every
defect this programme fixed is recorded with its resolution and the regression test that
guards it, to rewrite `TODO.md` and `PLAN.md` so they no longer describe a roadmap this
work has overtaken, and then to report the merge command for
`feature/batch4-interactive-layer` **without running it** (rule 6). Nothing in this phase
is allowed to start until Phases 01–30 have landed, and nothing in this phase may be
reported complete on the strength of a plausible assumption — every gate result in this
document must be a number someone read off a log.

---

## At a glance

| | |
|---|---|
| **Work items** | 4 |
| **Functional / deliverable** | 0 functional · 4 deliverable. This phase changes no user-visible behaviour by design; if it does, something it found needed fixing and rule 8 applies to that fix. |
| **Effort mix** | 3 small · 1 medium (the medium is item 2, the `BUGS.md` ↔ CHANGELOG reconciliation across 73 entries and 100+ defects) |
| **Renderers touched** | standalone (`DashRenderer`) ×1 — item 1 renders and *looks at* a dashboard, it does not modify the renderer · n/a ×3 (`BUGS.md`, `TODO.md`, `.ultraplan/PLAN.md`, git) |
| **Ultraplan tasks discharged** | **16-07** in full (close-out and the six gates — one of the two NOT_DONE tasks in the plan); the responsive half of **16-06** (*"Verify the responsive claim at 375px, 768px and 1440px using S10's procedure, since it is the abstract's headline and this is the last chance to check it"*). The `net install` half of 16-06 is Phase 03's. |
| **Sections closed** | **S16** — `0 DONE / 6 PARTIAL / 1 NOT_DONE` at the audit. This phase takes 16-07 to DONE and closes the section, and with it the plan. |
| **Depends on** | **Everything — Phases 01–30.** Gate 5 (`clean net install runs every example`) fails at HEAD on the packaging defect **Phase 03** fixes. Gate 4 (parity corpus) is only meaningful once **Phase 08** widens the corpus from 17 to 36 plot types. Gate 3 (conformance) depends on Phases 01–02 and 17–22. Item 2 cannot be reconciled until every phase that fixes a defect has written its `BUGS.md` entry. |
| **Unblocks** | Nothing. This is the last phase; what follows it is the user running the merge command. |
| **Source in `REMAINING.md`** | §7 *Release closeout* (`:271-292`), *Gates still to pass (S16-07)* (`:335-346`), the status table row 16 (`:315`), *Suggested order* step 6 (`:333`), and the final tally (`:348-375`) |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. Where a measurement was taken
from the repository rather than from `REMAINING.md`, it is labelled as such and the
command that produced it is shown. Nothing here is modelled.

### The closeout list, verbatim

> ## 7. Release closeout  [S16-06, S16-07]
>
> - **`net install` + run every example** — the gate S16-06 names. Item 1 above
>   means it does not pass today.
> - **Responsive verification at 375/768/1440px** — S10's procedure, re-run
>   against the current build.
> - **`BUGS.md`** holds 73 entries, all `[x]`. S16-07 asks for every defect this
>   plan fixed to be recorded; the count needs reconciling against the
>   CHANGELOG's defect list.
> - **`TODO.md` / `PLAN.md`** last touched at `5f857fc`; S16-07 asks that they no
>   longer describe an overtaken roadmap.
> - **Merge command** to be reported, not run (project rule 6).

The first of those five bullets is **Phase 03's** work, not this phase's — it is the
`net install` cscript and the scheme search paths. It appears here because this phase
*checks* it as gate 5. The other four bullets are items 1–4 below.

### The six gates, verbatim

> ## Gates still to pass (S16-07)
>
> full pytest · full certification suite with honest skips · conformance corpus
> (zero `r(198)`, zero dropped series, zero dropped graphs) · parity corpus ·
> clean `net install` runs every example · adversarial suite.
>
> At HEAD the first four pass (3,498 passed / 37 skipped; 25/25 cscripts);
> the fifth fails on §1.

Read that carefully, because it is the shape of this phase's risk. `REMAINING.md` records
the state of **five** of the six gates. It says nothing about the sixth. The adversarial
suite's state is therefore *unknown*, not *passing*, and TR-31.8 below says what to do
about that.

### 16-07's own text, from the plan

From `.ultraplan/sections/section-16-docs-conformance-release.md`, task `16-07`
(*files:* `BUGS.md`, `TODO.md`, `.ultraplan/CHANGELOG.md`, `.ultraplan/STATE.md`):

> Record every defect this plan fixed in `BUGS.md` in the existing style, each with its
> resolution and the regression test that guards it. The audit found 100+ distinct
> defects; they belong in the file that already tracks 51.
>
> Finalise `.ultraplan/CHANGELOG.md` as the migration document 16-02 links to.
>
> Update `TODO.md` and `PLAN.md` so they no longer describe a roadmap that has been
> overtaken.
>
> Final verification, and project rule 2 applies literally here — do not report completion
> until all of it passes:
> - full pytest suite green
> - full certification suite green, with honest skip counts
> - conformance corpus: zero `r(198)`, zero dropped series, zero dropped graphs
> - parity corpus: no undocumented divergence
> - clean `net install` runs every example
> - adversarial suite clean
>
> Then report the merge command for the feature branch. **Do not run it** (rule 6).
>
> *verify:* All six verification gates pass; `BUGS.md` and the CHANGELOG are complete;
> the merge command is reported, not executed.
> *done:* `dash` works as advertised, every claim is backed by a test, and the branch is
> ready for the user to merge.

Note the phrase *"the file that already tracks 51"*. It tracked 51 when the plan was
written. **It tracks 73 now** — the plan's own statement of the work is 22 entries stale,
which is a small demonstration of exactly the drift item 2 exists to close.

### Where S16 stands

From the status table (`REMAINING.md:315`):

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 16 | Help, conformance, release | 7 | 16-01..05 done ③ | 16-06, 16-07 gated on §1 |

Source ③ is **the CHANGELOG — self-reported**, not measured. That matters: the adversarial
pass never re-checked S16 (*"S11, S12, S15 and S16 had no DONE claim left to refute"*), so
16-01..05 carry the weakest evidence grade in the whole audit. This phase does not
re-audit them, but it must not treat them as proven either.

From the final tally (`REMAINING.md:348-375`):

| | DONE | PARTIAL | NOT DONE |
|---|---:|---:|---:|
| **89 tasks** | **19** | **68** | **2** |

| S09 | S10 | S11 | S12 | S13 | S14 | S15 | S16 |
|---|---|---|---|---|---|---|---|
| 0/7/0 | 0/4/0 | 0/6/0 | 0/5/0 | 2/4/0 | 1/4/0 | 0/4/0 | 0/6/**1** |

> The two NOT_DONE are 02-04 (the packaged-install
> cscript) and 16-07 (close-out, which is gated on everything else).

And the suggested order's last step (`REMAINING.md:333`):

> 6. **S16-06 / S16-07.** The six gates, then the merge command.

### The responsive claim, and what it last measured

Item 1 is not a fresh procedure; it is a re-run of one that exists and has a recorded
result to compare against. `test/test_geometry_visual.md` is S10-01's deliverable, and its
opening paragraph states the reason this phase does not get to skip it:

> Structural tests cannot tell you whether a dashboard *looks* right. Section 10
> is the section most likely to be reported done on the strength of an assertion
> about a model property, so this procedure exists and is meant to be followed,
> not skipped.

The exemplar it builds is `examples/geometry_responsive.do` — *"four KPI cards, a
deliberately wide panel (`xsize(10) ysize(2)`), a square one (`aspectratio(1)`), one at
the scheme's own proportions, and a faceted graph."*

The last recorded run, from the same file, is the comparison target:

| width | horizontal scroll | KPI cells | wide panel | other graphs |
|---|---|---|---|---|
| 1440 | none | 4 across, 358×130 | 1432×283 (ratio 5.06) | 2 across, 716×560 |
| 768 | none | 2 across, 380×130 | 760×149 | 2 across, 380×364 |
| 375 | none | 1 across, 367×130 | 367×160 | 1 across, full width |

> The aspect ratio is honoured between `_MIN_FIGURE_HEIGHT` and
> `_MAX_FIGURE_HEIGHT`. Outside that band it yields, so one square panel cannot
> fill a whole screen and a 10×2in panel on a phone does not collapse to a
> 73px sliver.

Measured in the repository at the time of writing: `_MAX_FIGURE_HEIGHT = 560`
(`dash_render.py:131`) and `_MIN_FIGURE_HEIGHT = 160` (`dash_render.py:132`). The `716×560`
cell at 1440px and the `367×160` wide panel at 375px are those two clamps being hit, which
is how you tell the table above is a real measurement rather than a model.

The procedure also records why check 2 exists at all:

> 2. **`window.innerWidth` matches the device width.** If it reports 980 at a
>    375px device, the viewport meta tag has gone missing and a phone is
>    rendering the page zoomed out. This was a real defect, found this way.

The viewport tag lives at `dash_render.py:667`
(`<meta name="viewport" content="width=device-width, initial-scale=1">`) and
`test/test_geometry.py` already guards it — but only structurally. Twenty-nine phases of
layout, scheme, geometry and facet work sit between that measurement and this one.

### The two documents that describe an overtaken roadmap

Measured in the repository at the time of writing:

```
$ wc -l TODO.md .ultraplan/PLAN.md
     786 TODO.md
     216 .ultraplan/PLAN.md

$ grep -c "^- \[x\]" TODO.md   ->  555
$ grep -c "^- \[ \]" TODO.md   ->    0
$ grep -c "^- \[~\]" TODO.md   ->    0
```

`TODO.md`'s own legend is `Status: [ ] not started | [~] in progress | [x] complete`, and
**every one of its 555 items is `[x]`**. A reader opening the repository today is told the
work is finished, while the audit behind these phase documents carries **249 remaining
work items** and **68 PARTIAL / 2 NOT_DONE** of 89 tasks. That gap is item 3.

`REMAINING.md` records both files as last touched at `5f857fc`. Measured:

```
$ git log --oneline -1 -- TODO.md            -> 5f857fc  Record what this pass fixed, and what it did not
$ git log --oneline -1 -- .ultraplan/PLAN.md -> 681bcf5  Add the batch 1 plan artifacts and measured baseline
```

`TODO.md` matches. `.ultraplan/PLAN.md` is **staler still** — it has not been touched since
the batch-1 plan artifacts went in. This does not contradict `REMAINING.md`; it sharpens it
in the same direction.

`PLAN.md` is also the file that carries binding decision 1, which `REMAINING.md` §3 shows
is still violated at HEAD (`PLAN.md:36-37`):

> 1. **Schemes are translated, not parsed from Stata.** … `scheme()` is
>    **restricted** to the translated set with a clear error naming the supported names —
>    never a silent fallback to black or to `s2color`.

So `PLAN.md` is not merely stale prose. It states a contract that Phase 04's S11-05 work
makes true; item 3 must not rewrite that sentence into a description of whatever the code
happens to do, or the decision stops binding anything.

### The ledger to reconcile

Measured in the repository at the time of writing:

```
$ grep -c "\[x\]" BUGS.md   ->  73
$ grep -c "\[ \]" BUGS.md   ->   0
$ wc -l BUGS.md             -> 438
```

The existing style — which item 2 must preserve, because "in the existing style" is 16-07's
own wording — is five fields per entry. A real entry, quoted in full so the shape is not in
doubt:

```
- [x] Title: Server-mode function `n` option allows unbounded point counts
  - File Names and Line Numbers: dash_render.py (8851-8853, 8872)
  - Description: Generated server code parses `opts['n']` directly into `n_pts` and uses
    it in `np.linspace(x_lo, x_hi, n_pts)` with no upper bound. …
  - Suggested fix: Clamp `n_pts` to a safe range (for example `2..10000`) …
  - Resolution: Fixed. Changed the `n_pts` parse … 3 regression tests added in
    `test/test_server.py` class `TestServerFunctionNClamp` (BUG-FE-2a through BUG-FE-2c).
    All 1222 tests pass.
```

Two things to carry forward from that. First, the `Resolution:` field **already names the
test file and the test class** — so 16-07's "with its resolution and the regression test
that guards it" is satisfiable mechanically, and therefore testable mechanically (TR-31.9).
Second, `All 1222 tests pass` is a point-in-time count baked into prose; the suite is at
3,498 today. Do not "fix" those historical counts — they are a record of when the entry was
written, and rewriting them would be falsifying the ledger.

### The advisory in §7 — owned elsewhere, checked here

> ### Advisory, outside the plan
>
> `dash.pkg` carries its version only as prose (`d Version: 1.0.0 25mar2026`).
> There is no `v` line and no `d Distribution-Date:` line, so `adoupdate` can
> never detect an update, and the stated date is six months stale. The manifest
> itself is complete — all 20 declared files exist and nothing shippable is
> missing.

This is **Phase 03 item 4**, not a work item here (`phases/PHASE-03-packaged-install-and-scheme-reachability.md:660`).
It is quoted because a release that ships a manifest whose stated date is six months stale
is not a release anyone should sign off, and the Definition of Done below therefore checks
it. Measured at the time of writing: `dash.pkg:21` still reads `d Version: 1.0.0  25mar2026`.

### The branch this ends on

`REMAINING.md`'s header records the branch as *"`feature/batch4-interactive-layer`, 61
commits ahead of `main`, tree clean"* at `ca5fe35`. Measured at the time of writing:
`git rev-list --count main..HEAD` → **62**, on `feature/batch4-interactive-layer`, and 29
more phases of work will land on top of it before item 4 runs.

---

## Epics

Four items, three epics. They are separated because they fail differently: a gate fails by
measurement, a document fails by drift, and a handoff fails by being executed when it
should have been reported.

| Epic | Goal | Items |
|---|---|---:|
| **E31.1 — Gate verification** | Run all six release gates against the finished branch, and re-run S10's responsive procedure at 375/768/1440px so the abstract's headline claim is checked by eye rather than by assertion. | 1 |
| **E31.2 — The written record** | Make `BUGS.md`, `.ultraplan/CHANGELOG.md`, `TODO.md` and `.ultraplan/PLAN.md` describe the code that exists, with every defect recorded against the test that guards it. | 2, 3 |
| **E31.3 — The handoff** | Report the merge command for the feature branch once, and only once, all six gates have passed — and do not run it. | 4 |

---

## User stories

### E31.1 — Gate verification

**US-31.1.1** — *As a **dashboard viewer** opening a `dash` dashboard on a phone, I want the
whole dashboard usable at 375px with no horizontal scrolling, so that the claim that made me
open it on a phone is true.*

- **Given** `examples/geometry_responsive.do` built against the finished branch and served
  over HTTP (a `file://` page will not load with the CSP meta tag in place),
  **when** the page is viewed at 375px, 768px and 1440px,
  **then** `document.documentElement.scrollWidth` equals `window.innerWidth` at every width.
- **Given** the same page at an emulated 375px device,
  **when** `window.innerWidth` is read,
  **then** it reports 375 and not 980 — 980 means the viewport meta tag
  (`dash_render.py:667`) has gone missing again and a phone is rendering zoomed out.
- **Given** the wide panel (`xsize(10) ysize(2)`) and the square panel (`aspectratio(1)`) in
  the same dashboard,
  **when** their boxes are measured at each width,
  **then** the wide one is wide and short, the square one is square, and neither has a large
  empty band below its content.
- **Given** the faceted graph in the same dashboard,
  **when** its panels are measured,
  **then** they are sized consistently with the unfaceted panels.
- **Given** the measurement table recorded in `test/test_geometry_visual.md`,
  **when** the new run's numbers are compared against it,
  **then** every difference is explained in writing by a change this programme made, or it
  is a defect and rule 8 applies.

**US-31.1.2** — *As a **package maintainer**, I want the six gates run and their raw counts
recorded, so that "finished" is a number I can re-derive rather than a claim I have to
trust.*

- **Given** the finished branch,
  **when** the full pytest suite is run,
  **then** it is green, and the skip count is recorded and every skip has a named reason.
- **Given** the certification suite run through `test/run_all_cscripts.do` under `arch -arm64`,
  **when** the log is read,
  **then** every script reports `[ PASS]`, the totals line accounts for every script on
  disk, and **a skip is not counted as a pass**.
- **Given** the conformance corpus,
  **when** `test/test_conformance.cscript` runs,
  **then** it reports zero `r(198)`, zero dropped series and zero dropped graphs.
- **Given** the parity corpus,
  **when** `test/test_mode_parity.py` runs,
  **then** there is no divergence outside the documented `ALLOWED` set at
  `test/test_mode_parity.py:55`, and the corpus covers all 36 server `ptype` branches rather
  than the 17 it covered at the audit.
- **Given** a clean directory and a real `net install`,
  **when** all 12 `examples/*.do` are run from it,
  **then** every one returns rc 0 **and none emits the scheme-fallback warning**.
- **Given** the adversarial suite,
  **when** it is run,
  **then** no case gains unauthorised access, and the suite that was run is named
  explicitly rather than assumed.

**US-31.1.3** — *As a **`dash serve` operator**, I want the parity gate to mean what it says,
so that a dashboard I serve draws what the same spec drew standalone.*

- **Given** a spec using `function`, `pci` or `fpfitci` — the three drifts `REMAINING.md` §4
  measured, of which two drew **nothing** in server mode,
  **when** the parity corpus runs against the finished branch,
  **then** each draws the same layer set in both renderers, or the difference is in
  `ALLOWED` with a written reason.

### E31.2 — The written record

**US-31.2.1** — *As a **package maintainer** triaging a new report, I want every defect this
programme fixed recorded in `BUGS.md` with the test that guards it, so that I can tell in one
grep whether a symptom is new or a regression.*

- **Given** `BUGS.md` after reconciliation,
  **when** each entry is read,
  **then** it carries Title, File Names and Line Numbers, Description, Suggested fix and
  Resolution, and the Resolution names at least one test file or test class that exists on
  disk.
- **Given** the CHANGELOG's defect sections,
  **when** they are cross-checked against `BUGS.md`,
  **then** every defect the CHANGELOG claims fixed has a `BUGS.md` entry, and every
  `BUGS.md` entry closed during this programme is reflected in the CHANGELOG.
- **Given** an entry whose regression test was never written,
  **when** reconciliation runs,
  **then** it fails, and the missing test is written before the entry is marked `[x]`
  (rule 8) — reconciliation is never satisfied by editing the ledger to match reality.

**US-31.2.2** — *As a **Stata user pasting a `twoway` command**, I want the repository's own
roadmap documents to describe what `dash` does today, so that I am not told a feature is
complete when the audit says otherwise.*

- **Given** `TODO.md` at 555 items all `[x]`,
  **when** it is rewritten,
  **then** it reflects the post-audit state — what this programme delivered, and what
  remains — and no item claims completion that a gate has not demonstrated.
- **Given** `.ultraplan/PLAN.md`, last touched at `681bcf5`,
  **when** it is updated,
  **then** the section index, the dependency graph and the four binding decisions match the
  delivered shape, and **decision 1's wording at `PLAN.md:36-37` still states the
  restriction** rather than being softened to match old behaviour.
- **Given** a reader who opens the repository cold,
  **when** they read `TODO.md`, `PLAN.md` and `REMAINING.md` together,
  **then** the three do not contradict each other about what is finished.

### E31.3 — The handoff

**US-31.3.1** — *As a **package maintainer**, I want the merge command reported and not run,
so that the decision to move this onto `main` stays mine.*

- **Given** all six gates passing and the record reconciled,
  **when** the phase reports completion,
  **then** it prints the exact merge command for `feature/batch4-interactive-layer` and the
  branch is still unmerged.
- **Given** any gate not passing,
  **when** completion is considered,
  **then** it is not reported, and the failing gate is named with its output (rule 2).
- **Given** the commits this programme produced,
  **when** their messages are read,
  **then** none mentions Claude or Anthropic (rule 7), and none was made directly on `main`
  (rule 6).

---

## Business requirements

| ID | Requirement | How it is verified |
|---|---|---|
| **BR-31.1** | A `dash` dashboard is usable at 375px, 768px and 1440px with no horizontal scroll at any width. | S10 procedure re-run; probe output recorded in `test/test_geometry_visual.md` |
| **BR-31.2** | The responsive result is recorded as a measurement, against a named build, so the next person has something to compare against. | New measurement table in `test/test_geometry_visual.md`, stamped with the commit it was built from |
| **BR-31.3** | All six release gates pass, and each gate's result is a count read from a log rather than an assertion. | Gate log excerpts recorded in `.ultraplan/STATE.md` |
| **BR-31.4** | A skip is never reported as a pass, in either suite. | Skip counts recorded per gate; `test/test_cscript_hygiene.py` green |
| **BR-31.5** | Every defect this programme fixed is recorded in `BUGS.md` in the existing five-field style, with its resolution and the regression test that guards it. | `test/test_release_closeout.py::TestBugsLedger` |
| **BR-31.6** | `BUGS.md` and `.ultraplan/CHANGELOG.md` agree about what was fixed. | `test/test_release_closeout.py::TestChangelogReconciliation` |
| **BR-31.7** | No `BUGS.md` entry is closed on the strength of a regression test that does not exist. | Ledger test resolves every named test path/class against disk |
| **BR-31.8** | `TODO.md` and `.ultraplan/PLAN.md` describe the delivered system, not the superseded roadmap. | `test/test_release_closeout.py::TestRoadmapCurrency`; review |
| **BR-31.9** | Binding decision 1 survives the `PLAN.md` rewrite with its restriction intact. | Currency test asserts the decision text still requires an error, not a fallback |
| **BR-31.10** | The merge command is reported; the branch is not merged and `main` carries no commit from this programme. | DoD check; `git branch --contains` inspection at review time |
| **BR-31.11** | Completion is not reported while any gate fails (rule 2). | Review of the closeout report against the six recorded gate results |
| **BR-31.12** | Running the gates opens no browser window on the user's desktop. | `global dash_nobrowser 1` set before every Stata run that builds a dashboard |

---

## Technical requirements

### TR-31.1 — The responsive procedure, exactly as S10 wrote it

*File:* `test/test_geometry_visual.md` (the procedure), `examples/geometry_responsive.do`
(the exemplar).

Build:

```bash
mkdir -p /tmp/dash-visual && cd /tmp/dash-visual && cat > run.do <<'DO'
clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "<repo>"
cd /tmp/dash-visual
do "<repo>/examples/geometry_responsive.do"
exit, clear STATA
DO
arch -arm64 /usr/local/bin/stata-mp -b do run.do
```

Serve it — *"A browser will not load a `file://` dashboard with the CSP meta tag in place"*:

```bash
cd /tmp/dash-visual && python3 -m http.server 8771 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8771/geometry_responsive.html` at **375px**, **768px** and
**1440px** and run the six checks the procedure lists: no horizontal scroll; `innerWidth`
matches the device width; no overlapping cells and no dead band under a short wide panel;
the wide panel wide and short and the square one square; faceted panels sized like
unfaceted ones; the whole dashboard usable on a phone.

The two probes, copied from the procedure:

```js
JSON.stringify({
  vw: window.innerWidth,
  docW: document.documentElement.scrollWidth,
  hscroll: document.documentElement.scrollWidth > window.innerWidth + 1,
})
```

```js
[...document.querySelectorAll('div[class*="db-col-12"]')]
  .map(d => [d.className, Math.round(d.getBoundingClientRect().width),
                          Math.round(d.getBoundingClientRect().height)])
```

**`global dash_nobrowser 1` must be set in `run.do` before the build** (BR-31.12) — the
build step must not open windows; the serving step is where the page is looked at.

### TR-31.2 — Record the new measurement, do not overwrite the old one silently

*File:* `test/test_geometry_visual.md`, section *"What was measured when this procedure was
last run"*.

Append the new table beside the prior one, each labelled with the commit it was built from
and the active scheme (the recorded run used *"the `stcolor`-family default scheme"*). Any
row that differs from the prior run must carry a one-line reason naming the phase that
changed it. A difference with no reason is a defect, and rule 8 applies before it is
explained away.

Expected clamps, unchanged unless a phase deliberately changed them:
`_MIN_FIGURE_HEIGHT = 160` (`dash_render.py:132`), `_MAX_FIGURE_HEIGHT = 560`
(`dash_render.py:131`). The recorded `716×560` at 1440px and `367×160` at 375px are those
two constants.

### TR-31.3 — Gate 1: full pytest

Baseline to beat, from `REMAINING.md:341-342`: **3,498 passed / 37 skipped** at HEAD, with
the first four gates passing. The finished branch will be higher — 29 phases add tests —
so the requirement is *green with the skip count recorded and each skip reasoned*, not a
fixed number. Run from the repository root. Record: passed, failed, skipped, errors,
warnings, and the pytest version.

### TR-31.4 — Gate 2: the certification suite, with honest skips

*Command* (project memory records the arm64 requirement, and the runner's own header
explains it — a long run was observed launching the x86_64 slice, after which the arm64
`libpython3.13.dylib` cannot load and every Python-dependent script fails for a reason that
has nothing to do with `dash`):

```bash
cd test && arch -arm64 /usr/local/bin/stata-mp -b do run_all_cscripts.do
```

Then read `test/run_all_cscripts.log` and grep `^\[ (PASS|FAIL|SKIP)\]` and `^  Results`.

At the audit: **25/25 cscripts**, and `ls test/*.cscript | wc -l` returns 25 at the time of
writing. Phase 03 adds `test/test_netinstall.cscript`, so the finished branch should report
**26/26** — and the totals line must account for every `.cscript` on disk. A script that is
on disk but not invoked by the runner is the exact failure mode `REMAINING.md`'s S01 row
still lists (*"runner skip-accounting regression test"*, Phase 29). **A skip is not a pass.**

`test/run_all_cscripts.do` already sets `$dash_nobrowser`.

### TR-31.5 — Gate 3: the conformance corpus

*File:* `test/test_conformance.cscript`. Required result: **zero `r(198)`, zero dropped
series, zero dropped graphs.**

Known limitation to state in the record rather than discover later: `REMAINING.md` §4
measured that *"`test_conformance.cscript`'s 'every layer drew something' assertion runs in
**standalone mode only**, which is precisely why the two server-mode layers that draw
nothing are invisible to it."* Gate 3 alone therefore cannot prove server-mode drawing;
gate 4 is what covers that. If Phase 08 widened this assertion to both modes, say so in the
record; if it did not, gate 3's scope is standalone and the record must not overstate it.

### TR-31.6 — Gate 4: the parity corpus

*File:* `test/test_mode_parity.py`; the documented-divergence set is `ALLOWED` at
`test/test_mode_parity.py:55`, whose header reads *"Differences that are CORRECT, with the
reason. Anything not listed here is a failure."*

At the audit the corpus was **32 cases over 17 distinct plot types against 36 server `ptype`
branches — 19 types unguarded**: `fpfit` `fpfitci` `function` `lfitci` `lowess` `pcbarrow`
`pci` `pcspike` `qfit` `qfitci` `rarea` `rbar` `rcap` `rconnected` `rline` `rscatter`
`rspike` `tsline` `tsrline`. It also *"never constructs a spec with `by()`, KPIs,
`filter()`, `link()` or `tabs()` — grep for each of those keys in the corpus returns 0."*

Five of the 19 had already drifted, measured by building both renderers' figures from the
same spec and diffing every glyph property:

| type | standalone | server | consequence |
|---|---|---|---|
| **`fpfitci`** | `VArea`(α .2) + `Line` | `Line` only | **the confidence band is missing in server mode** |
| **`function`** | `Line` | *nothing* | **server-mode `function` draws no layer** |
| **`pci`** | `Segment` | *nothing* | **server-mode `pci` draws no layer** |
| `lowess` | `#1f77b4`, width 1 | `#1a476f`, width 1.5 | **standalone `lowess` ignores the scheme** (matplotlib's default blue) |
| `rscatter` | marker size 8.0 | marker size 6 | two default size tables |

Gate 4 passes when the corpus covers **all 36** types plus `by()`, KPI, `filter()`, `link()`
and `tabs()` specs (Phase 08's work), and every remaining divergence is in `ALLOWED` with a
written reason. **A green parity run over 17 types is not gate 4** — it is the state the
audit already found and called insufficient.

### TR-31.7 — Gate 5: a clean `net install` runs every example

*File:* `test/test_netinstall.cscript` — delivered by **Phase 03**, items 2 and 3. It
replaces `test/test_packaging.py:stage_package (:89-123)`, which `REMAINING.md` §1
characterises as *"a `shutil` model of `net install` — 'no network, no Stata'"* modelling
only `flat` and `as-declared`, neither of which is Stata's real layout.

Pass criteria: a real `net install` into a clean directory, only that directory on the
adopath, **all 12** `examples/*.do` run with rc 0, and **zero** occurrences of either
fallback warning:

```
UserWarning: dash: scheme 's1color' was not found ... using s2color
UserWarning: dash: no scheme file could be resolved for the dashboard
```

At the audit all 12 examples ran with rc 0 *and all 12 emitted the fallback warning* — rc 0
alone is not this gate.

### TR-31.8 — Gate 6: the adversarial suite, whose state is unrecorded

*Files:* `test/test_adversarial.cscript` exists on disk and is one of the 25 scripts the
runner invokes. Task 16-05 named **two** files: `test/test_adversarial.cscript` **and**
`test/test_adversarial_py.py`. Measured at the time of writing, `ls test/ | grep -i adversar`
returns only `test_adversarial.cscript` and `test_adversarial.log` — **the Python half is
not on disk**. `REMAINING.md` marks 16-01..05 done from source ③ (the CHANGELOG,
self-reported) and records nothing about gate 6's state.

Therefore: before reporting gate 6, establish by inspection which suite exists and what it
covers, against project rule 18 (*three adversarial cases per API endpoint and/or user input,
targeting auth bypass, injection and resource exhaustion*). If the Python half is genuinely
absent, gate 6 is not passed by running the half that exists — write the missing cases or
record the gap explicitly as an open item. Do not report the gate green on a file count.

The resource-exhaustion cases have a specific target list from `REMAINING.md` §6 (Phase 04's
work): the `_MAX_IPS` eviction structure (*"One machine cycling 10,000 forwarded keys took
300 sessions inside a 60-second window against a nominal 60"*), the uncapped dropdown filter
(*"200,001 options on 200,000 observations"*), and the absent `by()` group cap.

### TR-31.9 — `BUGS.md` schema and the reconciliation rule

*Files:* `BUGS.md` (438 lines, 73 entries, all `[x]`), `.ultraplan/CHANGELOG.md` (1,195
lines; defect content lives under headings such as `### Bugs fixed`, `### The headline
defect`, `### Four product defects the unmasked suite found`, `### Six tests that certified
nothing`).

Required entry shape, unchanged from the existing style:

```
- [x] Title: <one line>
  - File Names and Line Numbers: <file> (<line ranges>)
  - Description: <what was wrong and why it is a defect>
  - Suggested fix: <what was proposed>
  - Resolution: Fixed. <what changed>. <N> regression tests added in `test/<file>.py`
    class `<TestClass>`.
```

Reconciliation rules, in priority order:

1. **Never edit the ledger to match reality.** If an entry claims a regression test that
   does not exist, write the test (rule 8), then keep the entry.
2. Every defect fixed by Phases 01–30 gets an entry. The programme's phase documents each
   end with a DoD line requiring exactly this, so the reconciliation is a join, not an
   archaeology exercise.
3. Historical `All <N> tests pass` counts inside old `Resolution:` fields are records of
   when they were written. Leave them.
4. The CHANGELOG stays the migration document 16-02 links to; entries added here must not
   break links into it.

### TR-31.10 — `TODO.md` and `PLAN.md`

*Files:* `TODO.md` (786 lines, 555 `[x]`, 0 `[ ]`, last touched `5f857fc`),
`.ultraplan/PLAN.md` (216 lines, last touched `681bcf5`).

`TODO.md` must stop asserting 100% completion of a roadmap the audit contradicted. The
minimum honest rewrite: keep the delivered items, mark anything a gate did not demonstrate
with `[ ]` or `[~]` per the file's own legend, and point forward to `REMAINING.md` and
`phases/PHASE-00-INDEX.md` for the post-audit scope.

`PLAN.md` must match the delivered shape in three places: the section index (*"16 sections,
89 tasks, 6 batches"*), the dependency graph (batches 1–6, `S01…S16`), and the four binding
decisions. **Decision 1 at `PLAN.md:36-37` keeps its restriction** — `scheme()` restricted
to the translated set *"with a clear error naming the supported names — never a silent
fallback to black or to `s2color`"*. `REMAINING.md` §3 measured that violated at HEAD; Phase
04 makes it true; this phase must not paper over the gap by weakening the sentence.

### TR-31.11 — The merge command

Project rule 6: commit to the local branch, report the merge command, never commit directly
to `main`. Rule 7: no reference to Claude or Anthropic in commit messages.

The command to report, not run — current branch `feature/batch4-interactive-layer`:

```
git checkout main && git merge --no-ff feature/batch4-interactive-layer
```

Report it only after the six gate results are recorded and all six are green. Alongside it,
report the branch state at that moment (`git rev-list --count main..HEAD`; 62 at the time of
writing) so the reviewer knows what they are about to merge.

### TR-31.12 — Where the gate results are recorded

*File:* `.ultraplan/STATE.md` — one of 16-07's four named files. It already carries a
`## Session History` table; add a closeout section listing the six gates by name with, for
each, the command run, the raw counts, and the date. `test/test_release_closeout.py` asserts
all six gate names are present with a result, which is what stops "all gates pass" from
being a sentence nobody has to back up.

---

## Work items

All four items, numbered as handed over.

### 1 — Re-run the responsive verification at three widths

`[deli · standalone · small]`

> Re-run the responsive verification at 375px, 768px and 1440px using S10's procedure,
> against the current build. It is the abstract's headline claim and the last chance to
> check it.

*Where:* `examples/geometry_responsive.do`, `test/test_geometry_visual.md` (the procedure and
the recorded measurement), `test/test_geometry.py` (the structural half), `dash_render.py:667`
(viewport meta), `dash_render.py:131-132` (`_MAX_FIGURE_HEIGHT = 560`,
`_MIN_FIGURE_HEIGHT = 160`).

*Evidence:* `REMAINING.md` §7 — *"**Responsive verification at 375/768/1440px** — S10's
procedure, re-run against the current build."* S16-06's own text: *"Verify the responsive
claim at 375px, 768px and 1440px using S10's procedure, since it is the abstract's headline
and this is the last chance to check it."* S10's risk line: *"visual rather than logical,
which makes it the section most likely to be reported 'done' on the basis of a structural
assertion. It is not done until someone has looked at it at three viewport widths."* The
prior measurement to compare against is the three-row table above. The `innerWidth == 980`
check exists because the missing viewport tag *"was a real defect, found this way."*

*Requirements:* TR-31.1, TR-31.2; BR-31.1, BR-31.2, BR-31.12.

### 2 — Reconcile `BUGS.md` against the CHANGELOG's defect list

`[deli · n/a · medium]`

> Reconcile `BUGS.md` against the CHANGELOG's defect list. It holds 73 entries, all `[x]`;
> S16-07 asks that every defect this plan fixed be recorded there with its resolution and
> the regression test that guards it.

*Where:* `BUGS.md` (438 lines, 73 entries, `grep -c "\[ \]" BUGS.md` → 0),
`.ultraplan/CHANGELOG.md` (1,195 lines).

*Evidence:* `REMAINING.md` §7 — *"**`BUGS.md`** holds 73 entries, all `[x]`. S16-07 asks for
every defect this plan fixed to be recorded; the count needs reconciling against the
CHANGELOG's defect list."* 16-07's text: *"Record every defect this plan fixed in `BUGS.md`
in the existing style, each with its resolution and the regression test that guards it. The
audit found 100+ distinct defects; they belong in the file that already tracks 51."* The
file tracks 73 now, so the plan's own statement of this task is 22 entries stale. The
existing style already names the guarding test inside `Resolution:` (see the `BUG-FE-2a`
entry quoted above), which is what makes the reconciliation mechanically checkable.

*Requirements:* TR-31.9; BR-31.5, BR-31.6, BR-31.7.

### 3 — Update `TODO.md` and `PLAN.md`

`[deli · n/a · small]`

> Update `TODO.md` and `PLAN.md` so they no longer describe a roadmap this work has
> overtaken. Both were last touched at `5f857fc`.

*Where:* `TODO.md`, `.ultraplan/PLAN.md` (binding decisions at `:36-37`, section index at
`:45-46`, dependency graph at `:49-77`).

*Evidence:* `REMAINING.md` §7 — *"**`TODO.md` / `PLAN.md`** last touched at `5f857fc`; S16-07
asks that they no longer describe an overtaken roadmap."* Measured: `TODO.md` is 786 lines
with **555 `[x]` and 0 `[ ]`**, against its own legend `[ ] not started | [~] in progress |
[x] complete` — a repository that tells a reader everything is finished while the audit
carries 249 remaining work items and 68 PARTIAL / 2 NOT_DONE tasks. `git log -1 --
.ultraplan/PLAN.md` returns `681bcf5`, older than the `5f857fc` `REMAINING.md` records, so
`PLAN.md` is staler still. `PLAN.md:36-37` also carries binding decision 1, which
`REMAINING.md` §3 measured violated at HEAD.

*Requirements:* TR-31.10; BR-31.8, BR-31.9.

### 4 — Report the merge command once all six gates pass

`[deli · n/a · small]`

> Report the merge command for the feature branch once all six gates pass. Do not run it
> (project rule 6).

*Where:* git; the closeout report; `.ultraplan/STATE.md` for the gate results.

*Evidence:* `REMAINING.md` §7 — *"**Merge command** to be reported, not run (project rule
6)."* Gate state at the audit: *"At HEAD the first four pass (3,498 passed / 37 skipped;
25/25 cscripts); the fifth fails on §1."* The sixth is unrecorded (TR-31.8). 16-07's verify
clause: *"All six verification gates pass; `BUGS.md` and the CHANGELOG are complete; the
merge command is reported, not executed."* Branch measured at the time of writing:
`feature/batch4-interactive-layer`, 62 commits ahead of `main` (`REMAINING.md` header
records 61 at `ca5fe35`).

*Requirements:* TR-31.11, TR-31.12; BR-31.3, BR-31.10, BR-31.11.

---

## Test plan

This phase's items are deliverables, so most of its "tests" are the gates themselves. That
is not an excuse to skip rule 8 or rule 4: the two document items are mechanically checkable
and get a real pytest file, the gate results get a check that stops them being asserted
without evidence, and anything the gates *find* is a bug that needs a failing-first
regression test like any other.

**New file:** `test/test_release_closeout.py`, with three classes —
`TestBugsLedger`, `TestChangelogReconciliation`, `TestRoadmapCurrency` — plus
`TestGateRecord`. Existing files touched: `test/test_geometry_visual.md` (the recorded
measurement), `.ultraplan/STATE.md` (the gate record), `test/run_all_cscripts.do` (script
registry only, if Phase 03's script is not already registered).

### E31.1 — Gate verification

**The failing test to write first (rule 8).** Before touching anything, run
`test/test_geometry.py`'s viewport class and the two `test_geometry_visual.md` probes
against the finished branch and **read the output**. If any of the six visual checks fails,
that failure is the failing-first test: write the structural assertion that captures it into
`test/test_geometry.py` (e.g. a cell-height or grid-span assertion mirroring the observed
defect), watch it fail, fix, watch it pass. A visual defect that is fixed without first
being pinned by an assertion will come back — that is what the S10 risk line says.

**Unit tests (rule 4).** Existing, and all must be green:

| file | what it covers |
|---|---|
| `test/test_geometry.py` | `xsize()`/`ysize()` ratios, scheme `graphsize`, `aspectratio()` precedence, responsive sizing mode, `lg`/`md` breakpoints, cell height from span, KPI row maximum as a named constant, and the viewport-meta class (`test_the_document_declares_a_viewport`, `test_it_is_declared_exactly_once`, `test_the_csp_meta_is_still_present`) |
| `test/test_mode_parity.py` | standalone vs server glyph properties; `ALLOWED` at `:55` is the only permitted divergence |
| `test/test_cscript_hygiene.py` | the suite's own honesty — a skip must not read as a pass |

**Integration / cscript coverage.** The six gates, in order, each with its counts recorded
in `.ultraplan/STATE.md`: full pytest · `test/run_all_cscripts.do` under `arch -arm64`
(26/26 expected once Phase 03's script is registered) · `test/test_conformance.cscript` ·
`test/test_mode_parity.py` over all 36 types · `test/test_netinstall.cscript` (Phase 03) ·
the adversarial suite (`test/test_adversarial.cscript`, plus the Python half if it exists —
TR-31.8).

**Proving each test non-vacuous (mutation).**

| mutation | test that must die |
|---|---|
| Delete the `<meta name="viewport">` emission at `dash_render.py:667` | `test/test_geometry.py::test_the_document_declares_a_viewport` (and the 375px probe reports `innerWidth` 980) |
| Emit the viewport meta twice | `test_it_is_declared_exactly_once` |
| Set `_MIN_FIGURE_HEIGHT = 0` (`dash_render.py:132`) | the 375px wide-panel row no longer reproduces `367×160`; the procedure's check 4 catches the collapsed sliver |
| Set `_MAX_FIGURE_HEIGHT = 10000` (`dash_render.py:131`) | the 1440px `716×560` row no longer reproduces; check 3 catches the dead band |
| Add a bogus key to `ALLOWED` (`test/test_mode_parity.py:55`) covering a real divergence | the parity gate stops failing on a difference it should fail on — so review `ALLOWED` diffs as code, and assert its size is unchanged unless a phase documented a new entry |
| Point `test_netinstall.cscript`'s adopath at the repo instead of the install dir | gate 5 passes vacuously — the cscript must assert the install directory is the *only* entry |

### E31.2 — The written record

**The failing test to write first (rule 8).** Write `test/test_release_closeout.py` against
the **current** `BUGS.md`, `CHANGELOG.md` and `TODO.md` and run it before editing any of
them. `TestRoadmapCurrency` must fail immediately on today's `TODO.md` (555 `[x]`, 0 `[ ]`,
last touched `5f857fc`) and on today's `PLAN.md` (`681bcf5`). `TestBugsLedger` must fail on
any entry whose `Resolution:` names a test that does not resolve on disk. Reading those
failures *is* the work list for items 2 and 3 — exactly as 16-01's text says the help
conformance failures were the work list for 16-02.

**Unit tests (rule 4).** In `test/test_release_closeout.py`:

| test | assertion |
|---|---|
| `TestBugsLedger::test_every_entry_is_closed` | no `- [ ]` or `- [~]` entries remain |
| `TestBugsLedger::test_every_entry_has_all_five_fields` | Title, File Names and Line Numbers, Description, Suggested fix, Resolution — all present, in order |
| `TestBugsLedger::test_every_resolution_names_a_test_that_exists` | each `Resolution:` names at least one `test/…` path (and, where given, a class) that resolves on disk |
| `TestBugsLedger::test_entry_count_is_recorded_and_monotone` | the count only grows; a shrink means an entry was deleted rather than reconciled |
| `TestChangelogReconciliation::test_every_changelog_defect_has_a_bugs_entry` | defect headings in `.ultraplan/CHANGELOG.md` map to `BUGS.md` titles |
| `TestChangelogReconciliation::test_changelog_links_still_resolve` | the migration document 16-02 links into is not broken by the additions |
| `TestRoadmapCurrency::test_todo_is_not_uniformly_complete` | `TODO.md` does not consist of 100% `[x]` while `REMAINING.md` lists open work |
| `TestRoadmapCurrency::test_todo_and_plan_are_newer_than_the_audit` | both files' last-touched commits are at or after the audit commit |
| `TestRoadmapCurrency::test_binding_decision_one_still_restricts` | `PLAN.md` still contains *"never a silent fallback"* and the word *restricted* for `scheme()` |

**Integration coverage.** None of these need Stata. They run in the full pytest gate, which
means the record is re-checked on every future run rather than only at release.

**Proving each test non-vacuous (mutation).**

| mutation | test that must die |
|---|---|
| Flip one `BUGS.md` entry from `[x]` to `[ ]` | `test_every_entry_is_closed` |
| Delete the `Resolution:` line from one entry | `test_every_entry_has_all_five_fields` |
| Change one `Resolution:` to name `test/test_nonexistent.py` | `test_every_resolution_names_a_test_that_exists` |
| Delete a `BUGS.md` entry | `test_entry_count_is_recorded_and_monotone` |
| Add a `### Bugs fixed` block to the CHANGELOG with no ledger counterpart | `test_every_changelog_defect_has_a_bugs_entry` |
| `git checkout 5f857fc -- TODO.md` | `test_todo_is_not_uniformly_complete` **and** `test_todo_and_plan_are_newer_than_the_audit` |
| Rewrite `PLAN.md:36-37` to say `scheme()` "falls back to `s2color`" | `test_binding_decision_one_still_restricts` |

### E31.3 — The handoff

**The failing test to write first (rule 8).** `TestGateRecord::test_all_six_gates_are_recorded`
against today's `.ultraplan/STATE.md`, which records none of them. It must fail before the
gates are run and pass only once each of the six has a named command and a raw count beside
it.

**Unit tests (rule 4).**

| test | assertion |
|---|---|
| `TestGateRecord::test_all_six_gates_are_recorded` | all six gate names appear in `.ultraplan/STATE.md` with a result line |
| `TestGateRecord::test_no_gate_result_is_blank_or_pending` | no recorded gate reads `TBD`, `pending`, `n/a` or empty |
| `TestGateRecord::test_skip_counts_are_present_where_a_suite_can_skip` | the pytest and cscript gates each record a skip count, because "green" without one is the failure mode S01 already caught |

**Integration coverage.** The merge command itself is reported, never executed, so its
coverage is the DoD checklist plus a reviewer running `git branch --contains` to confirm
`main` carries nothing from this branch. This is stated rather than automated on purpose:
a test that merges to check that merging works would violate the rule it is testing.

**Proving each test non-vacuous (mutation).**

| mutation | test that must die |
|---|---|
| Remove the parity gate's row from `.ultraplan/STATE.md` | `test_all_six_gates_are_recorded` |
| Set the adversarial gate's result to `TBD` | `test_no_gate_result_is_blank_or_pending` |
| Delete the skip count from the certification gate's row | `test_skip_counts_are_present_where_a_suite_can_skip` |

---

## Definition of done

- [ ] `test/test_release_closeout.py` was written **first**, run against the unmodified
      `BUGS.md`, `CHANGELOG.md`, `TODO.md`, `PLAN.md` and `STATE.md`, and its failures read
      and recorded before any of those files were edited (rule 8).
- [ ] The S10 procedure (`test/test_geometry_visual.md`) was run against a build of the
      finished branch, at 375px, 768px and 1440px, by looking at it — not by asserting.
- [ ] `global dash_nobrowser 1` was set before every Stata run in this phase; no browser
      window opened on the user's desktop.
- [ ] All six visual checks pass at all three widths: no horizontal scroll; `innerWidth`
      equals the device width (not 980); no overlapping cells and no dead band; the wide
      panel wide and short and the square one square; faceted panels sized like unfaceted
      ones; usable on a phone.
- [ ] A new measurement table is recorded in `test/test_geometry_visual.md`, stamped with
      the commit and scheme, beside the prior one; every difference from the prior table
      carries a one-line reason naming the phase that caused it.
- [ ] **Gate 1** — full pytest green; passed/failed/skipped/errors recorded; every skip has
      a named reason.
- [ ] **Gate 2** — certification suite green under `arch -arm64` via
      `test/run_all_cscripts.do`; the totals line accounts for every `.cscript` on disk
      (26/26 with Phase 03's script registered); no skip counted as a pass.
- [ ] **Gate 3** — `test/test_conformance.cscript`: zero `r(198)`, zero dropped series, zero
      dropped graphs; the record states whether its "every layer drew something" assertion
      now runs in both modes or standalone only.
- [ ] **Gate 4** — `test/test_mode_parity.py` covers all 36 server `ptype` branches plus
      `by()`, KPI, `filter()`, `link()` and `tabs()` specs; every divergence is in `ALLOWED`
      (`:55`) with a written reason; the five measured drifts (`fpfitci`, `function`, `pci`,
      `lowess`, `rscatter`) are each either fixed or documented.
- [ ] **Gate 5** — `test/test_netinstall.cscript` performs a real `net install`, runs all 12
      examples with rc 0, and emits **zero** scheme-fallback warnings.
- [ ] **Gate 6** — the adversarial suite is named explicitly, its coverage checked against
      rule 18, and its result recorded; if `test/test_adversarial_py.py` is still absent, that
      is stated as a gap rather than passed over.
- [ ] All six gate results are written into `.ultraplan/STATE.md` with the command that
      produced each and its raw counts; `TestGateRecord` is green.
- [ ] `BUGS.md` carries an entry for every defect Phases 01–30 fixed, in the existing
      five-field style, each `Resolution:` naming a regression test that exists on disk; no
      entry was deleted or downgraded to make the reconciliation pass.
- [ ] `.ultraplan/CHANGELOG.md` is finalised as the migration document 16-02 links to, and
      agrees with `BUGS.md` about what was fixed.
- [ ] `TODO.md` no longer reads as a uniformly complete roadmap, and points forward to
      `REMAINING.md` and `phases/PHASE-00-INDEX.md`.
- [ ] `.ultraplan/PLAN.md` matches the delivered section index, dependency graph and
      decisions, **with decision 1's restriction at `:36-37` intact**.
- [ ] `REMAINING.md` is unmodified (it is the source of record for this whole programme).
- [ ] Phase 03's advisory is closed: `dash.pkg` carries a `v` line and a real
      `d Distribution-Date:`, and the stated version is not six months stale at release.
- [ ] Every mutation in the test plan was applied and the named test observed to fail, then
      reverted.
- [ ] Commits are on `feature/batch4-interactive-layer`, none on `main` (rule 6), and no
      message mentions Claude or Anthropic (rule 7).
- [ ] The merge command is **reported, not run**, together with the branch state
      (`git rev-list --count main..HEAD`), and only after all six gates are green (rule 2).

---

## Risks and sequencing notes

**This phase cannot start early, and that is its main scheduling risk.** Every other phase
can be worked in parallel with something; this one is a join on all thirty. The mitigation
is that its inputs accumulate as the programme runs: each phase's DoD already requires a
`BUGS.md` entry in the existing style, so item 2 is a join rather than archaeology — *if*
those DoD lines were honoured. If they were not, item 2's medium estimate is wrong by a
wide margin. Check `BUGS.md`'s entry count at the end of each wave; it should be climbing.

**Risk: this is the phase most likely to be reported done on an assumption.** `REMAINING.md`
records four gates passing, one failing and one unmentioned. The tempting move is to treat
"the first four pass" as still true at the end of thirty phases of change. It will not be —
29 phases add tests, change defaults, widen corpora and rewrite emitted app source. Every
gate is re-run from scratch here, and its counts are recorded. Project rule 2 is quoted in
16-07 for exactly this reason: *"do not report completion until all of it passes."*

**Risk: gate 6's state is unknown, not good.** `REMAINING.md` says nothing about the
adversarial suite, S16's DONE claims come from the CHANGELOG's self-report (source ③), and
the adversarial pass never re-checked S16 because there was nothing left to refute there.
Measured here: the Python half 16-05 named is not on disk. Budget for writing adversarial
cases in this phase, not merely running them.

**Risk: the parity gate can be passed vacuously.** A green `test_mode_parity.py` over 17 of
36 plot types is exactly the state the audit found and called insufficient — and
`REMAINING.md` notes a related trap at `:2939-2940`: *"kdensity IS in the parity corpus and
the guard is green, because the guard never compares data."* Gate 4 is not "the parity file
is green"; it is "the parity file is green **and** covers the surface". Review `ALLOWED`
additions as code. An entry added to `ALLOWED` to make a gate pass is a defect wearing a
comment.

**Risk: the responsive check is subjective and the temptation is to automate it away.** S10
explicitly allows automation (*"If the built-in browser can drive this, automate the three
widths and capture what is rendered; if not, the written procedure is the deliverable and
it must be followed"*), and automating the two probes is worth doing. But checks 3–6 — dead
bands, overlap, panel proportions, phone usability — are judgements. Automate the two
numeric probes, look at the other four.

**Risk: reconciliation drifting into falsification.** The failure mode for item 2 is
adjusting `BUGS.md` until the test passes. TR-31.9 rule 1 exists to name it in advance: if
an entry claims a regression test that does not exist, the test gets written. The ledger is
the assertion; the code is what has to move.

**Sequencing inside the phase.** Item 3 (documents) can be drafted while the gates run —
it depends on the audit, not on the gate results. Item 2 must wait for the last phase's
`BUGS.md` entries to land. Item 1 must run against the *final* build, so it comes after the
last merge into the feature branch, not before. Item 4 is strictly last and is a single
sentence of output.

**Sequencing out.** Nothing follows this phase inside the programme. What follows is the
user deciding whether to run the merge command — which is the whole reason rule 6 says to
report it rather than run it.

**Effort honesty.** Three small items and one medium, but the *elapsed* cost is dominated by
running six suites, one of which needs Stata under `arch -arm64` and one of which needs a
real `net install` into a clean directory, plus a browser session at three widths. The risk
is not that the work is hard; it is that it is tedious in exactly the way that invites
someone to assert a result instead of measuring one. Every claim in this phase's output
should be traceable to a log line.
