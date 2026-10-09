# Visual verification procedure — layout and geometry

Structural tests cannot tell you whether a dashboard *looks* right. Section 10
is the section most likely to be reported done on the strength of an assertion
about a model property, so this procedure exists and is meant to be followed,
not skipped.

**Run this whenever you change anything that affects layout or figure size.**

## Build the dashboard

```bash
mkdir -p /tmp/dash-visual && cd /tmp/dash-visual && cat > run.do <<'DO'
clear all
adopath ++ "<repo>"
cd /tmp/dash-visual
do "<repo>/examples/geometry_responsive.do"
exit, clear STATA
DO
sh <repo>/scripts/stata_batch.sh -b do run.do
```

`examples/geometry_responsive.do` is the exemplar: four KPI cards, a deliberately
wide panel (`xsize(10) ysize(2)`), a square one (`aspectratio(1)`), one at the
scheme's own proportions, and a faceted graph.

## Serve it

A browser will not load a `file://` dashboard with the CSP meta tag in place,
so serve it:

```bash
cd /tmp/dash-visual && python3 -m http.server 8771 --bind 127.0.0.1
```

## Look at it at three widths

Open `http://127.0.0.1:8771/geometry_responsive.html` at **375px**, **768px**
and **1440px**.

At each width, check:

1. **No horizontal scroll.** `document.documentElement.scrollWidth` must equal
   `window.innerWidth`.
2. **`window.innerWidth` matches the device width.** If it reports 980 at a
   375px device, the viewport meta tag has gone missing and a phone is
   rendering the page zoomed out. This was a real defect, found this way.
3. **No cell overlaps another**, and no cell has a large empty band below its
   content. Dead space under a short wide panel means a min-height is being
   forced on a cell that does not need one.
4. **The wide panel is wide and short**; the square one is square. The
   proportions are the point of the section.
5. **Faceted panels are sized like unfaceted ones** — they inherit the same
   ratio.
6. **The whole dashboard is usable on a phone.** That is the specific claim the
   conference abstract makes.

A one-line probe for points 1 and 2, in the browser console:

```js
JSON.stringify({
  vw: window.innerWidth,
  docW: document.documentElement.scrollWidth,
  hscroll: document.documentElement.scrollWidth > window.innerWidth + 1,
})
```

And for point 3, the emitted grid cells and their measured boxes:

```js
[...document.querySelectorAll('div[class*="db-col-12"]')]
  .map(d => [d.className, Math.round(d.getBoundingClientRect().width),
                          Math.round(d.getBoundingClientRect().height)])
```

## What was measured when this procedure was last run

Recorded so a later run has something to compare against. Built from
`examples/geometry_responsive.do`, with the `stcolor`-family default scheme.

| width | horizontal scroll | KPI cells | wide panel | other graphs |
|---|---|---|---|---|
| 1440 | none | 4 across, 358×130 | 1432×283 (ratio 5.06) | 2 across, 716×560 |
| 768 | none | 2 across, 380×130 | 760×149 | 2 across, 380×364 |
| 375 | none | 1 across, 367×130 | 367×160 | 1 across, full width |

The aspect ratio is honoured between `_MIN_FIGURE_HEIGHT` and
`_MAX_FIGURE_HEIGHT`. Outside that band it yields, so one square panel cannot
fill a whole screen and a 10×2in panel on a phone does not collapse to a
73px sliver.
