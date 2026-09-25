# PRD — `dash` as a true drop-in replacement for `twoway`

## 1. What we're building

`dash` already turns `twoway` syntax into interactive HTML dashboards. This project closes
the distance between what `dash` says it does and what it does.

Three things happen. First, every `twoway` command that works in Stata will work in `dash`
instead of stopping the user's do-file with an error. Second, every option `dash` accepts
will either take effect or say out loud that it cannot — nothing will be quietly thrown
away. Third, the values that decide how a chart looks and what it computes — how many
histogram bars, how wide a smoothing window, what colour the third line is, how tall the
plot is — will come from the user's command, from their data, and from their Stata colour
scheme, instead of being fixed numbers written into the source code.

The headline promise of the package is one sentence: *just replace `twoway` with `dash`*.
This project is what makes that sentence true.

## 2. The problem

`dash` currently fails its own promise in four distinct ways, and the four need different
fixes.

**It stops working do-files.** Of 59 ordinary `twoway` commands tested against live Stata,
**37 were rejected outright** with `r(198)`. Not exotic ones: `xsize()`, `ysize()`,
`text()`, `sort`, `horizontal`, `bin()`, `percent`, `level()`, `kernel()`, and the everyday
abbreviations `mlab()`, `msym()`, `xlab()`, `mcol()`, `lcol()`. A user who pastes their
own working `twoway` line has a better-than-even chance of an error message.

**It throws work away in silence.** `dash scatter mpg price weight` draws one series; the
same `twoway` command draws two. `layout(bs)` combined with `by()` deletes the faceted graph
from the dashboard entirely. `fa(0.4)` does nothing. `link(_all)` produces an unlinked
dashboard. `title("T", size(large))` accepts the size and drops it. None of these produce a
warning.

**Its numbers are not the user's numbers.** A histogram is always 10 bars, whether there are
74 observations or 2,246 — Stata's own answers for those two datasets are 8 and 33. Every
confidence band is 95%, whatever `c(level)` says and with no `level()` option to change it.
Every `twoway function` is drawn over x from 0 to 1. `kdensity` ignores the `bwidth()` the
user supplied and uses a different bandwidth rule again the moment a filter moves.

**It cannot be installed.** `dash.pkg` omits the `schemes/` directory, and the code path that
is supposed to recover from a missing scheme raises the same error a second time, uncaught.
Installed the advertised way, **every `dash` command ends in a Python traceback.**

## 3. Who it's for

Stata users who already know `twoway` and expect to keep knowing it. They paste existing
syntax from existing do-files. They are not reading the help file first — the whole pitch is
that they don't have to. Their tolerance for "you have to learn our dialect" is zero,
because a static `twoway` graph is always one word away.

A second, smaller audience matters for the scheme work: users who have set a house scheme
(`set scheme`, or one built with `brewscheme`) and expect their graphs to look like their
other graphs.

## 4. What it does

Grouped by the four failure classes above, in the order they should be fixed.

**Make it installable.** Ship the scheme files. Make the scheme fallback actually fall back.
Verify dependencies before use rather than declaring them in a manifest.

**Stop rejecting valid syntax.** Accept the full `twoway` option surface. Where an option
has a real HTML meaning, implement it. Where it has none, accept it and note that it was
ignored — never abort. Replace the fixed abbreviation lookup table with Stata's own
capitalisation-driven abbreviation, so every prefix a user might type works and none is
silently mapped to the wrong option.

**Stop discarding work silently.** Expand multi-variable plot specs into one series per
y-variable. Fix Bootstrap layout so faceted graphs survive it. Wire up the options that are
parsed and then dropped. Warn wherever a value genuinely cannot be honoured.

**Derive values instead of fixing them.** Statistical defaults come from the data and from
`c(level)`, matching Stata's documented rules. Visual defaults come from the user's active
scheme, read from Stata's own scheme library rather than from five hand-written
approximations. Formats, dates and labels come from the dataset.

**Prove it.** A conformance suite that runs real `twoway` commands through `dash` and asserts
they neither abort nor silently drop content, plus a regression test written before each fix.

## 5. How it should feel

Invisible. A user replaces one word and gets the chart they expected, in their own colours,
with their own axis titles and number formats — and then discovers they can hover, zoom and
brush it. Nothing about the experience should announce that a translation layer exists.

Where `dash` genuinely cannot do something — a `.gph` file, a printer option — it should say
so in one plain line and carry on, the way a well-behaved Stata command does.

## 6. What it connects to

- **Stata** — for data, for variable and value labels, for display formats, and for `c()`
  settings (`c(scheme)`, `c(level)`, `c(os)`). The display-format channel does not exist
  today and has to be built, because `jsonio` has no way to emit formats.
- **`jsonio`** — carries the data. Not modified by this project.
- **Stata's installed scheme library** — 26 files that `dash` currently cannot see.
- **Bokeh >= 3.0** — the rendering target.
- **Bootstrap** — inlined for `layout(bs)`; no CDN dependency.

## 7. What it does NOT do

- It does not modify `jsonio`.
- It does not aim for pixel-identical output to `twoway`. The target is *recognisably the
  same graph in the same scheme*, not a bitmap match.
- It does not add plot types Stata does not have.
- It does not implement options that are meaningless in a browser (`play()`, `nodraw`,
  `.gph` saving, print options). Those are accepted and reported as ignored.
- It does not redesign the architecture. The Stata-`syntax`-parses-everything decision stays.
- It is not the conference deck. That is a separate, downstream project.

## 8. How we'll know it works

1. A conformance suite of real `twoway` commands runs through `dash` with **zero** `r(198)`
   aborts and zero silently-dropped series or graphs.
2. `dash histogram` reproduces Stata's own bin count on at least three datasets of different
   sizes.
3. Confidence bands honour `level()` and `c(level)`.
4. A user with `set scheme economist` gets economist colours without passing any option.
5. `net install` from a clean directory produces a working command.
6. The full test suite passes, with a new regression test for every defect fixed.
7. No existing dashboard changes except where the change is the fix, and every such change is
   listed.

## 9. Business model

Not applicable. `dash` is a free Stata package.

## 10. Risks and concerns

- **`dash_render.py` is 10,455 lines with ~60 consecutive single-issue fix commits behind
  it.** The regression surface is the whole file. Baseline first, full suite after every
  change.
- **Scheme work is the big one.** Reading Stata's real scheme files means parsing a 2,588-line
  format with `#include` chains and a four-level `p#stub` resolution order. It is separable
  and should not block the parity work.
- **Some fixes change existing output.** Correct histogram bins will change every existing
  histogram. That is the point, but it needs to be a deliberate, announced change.
- **Server mode and standalone mode implement the same behaviours twice** and have already
  drifted. Fixing parity in one does not fix it in the other.
- **The environment is fragile.** `statsmodels` is currently broken here; Stata's Python and
  the test suite's Python are different interpreters; Stata must be forced to its arm64 slice
  for `dash build` to run at all on this machine.
