# Phase 26 — Text fidelity I: canvas escaping

**Purpose.** Ultraplan task 09-07 established a single rule — *text that Bokeh draws as
a canvas glyph must carry the characters the user typed, and text that reaches the DOM
must be escaped exactly once, in one place.* The fix that landed applied that rule to
three strings in one renderer: the figure title and the two primary axis titles in
`DashRenderer`. Sixteen further sites across both renderers still call
`html.escape()` on text that never becomes HTML, so `title("R&D spend")` is correct but
`legend(label(1 "R&D"))`, a `by()` panel title, a `colorvar()` legend or colour-bar
title, a secondary-axis tick label, a filter dropdown option and *every* canvas string
in the emitted `bokeh serve` app still draw `R&amp;D` at the user. One site goes the
other way: the emitted app escapes the dashboard title once and then hands the escaped
copy to `doc.title`, which Bokeh's page template escapes again, so the browser tab reads
`Price &amp; Weight` under `dash serve` where `dash build` reads `Price & Weight`. This
phase finishes the clause everywhere, and replaces the three single-figure fidelity
tests with a net that covers every model property and both renderers — because the
reason this defect survived a "fixed" verdict is that nothing tested anything but
`fig.title.text`.

---

## At a glance

| | |
|---|---|
| **Work items** | 11 |
| **Functional / deliverable** | 10 functional · 1 deliverable |
| **Effort mix** | 11 small · 0 medium · 0 large |
| **Renderers touched** | standalone 4 · server 3 · both 4 |
| **Distinct escape sites to change** | 17 (16 canvas/widget over-escapes + 1 HTML double-escape) |
| **Ultraplan tasks discharged** | `09-07` — the escaping clause only (hover, the secondary-axis range and the `mlabel` test go to Phase 27) |
| **Sections touched** | S09 (task 09-07); `GlyphMapper` sites are shared with S15's emitted glyph layer |
| **Depends on** | — (no prerequisite phase) |
| **Unblocks** | Phase 27 — Text fidelity II: `hover()` and the secondary axis |
| **Files** | `dash_render.py` (one module, both renderers), `test/test_axis_options.py`, `test/test_mode_parity.py` |

All eleven items are **small**. This is a wide, shallow phase: seventeen one- to
five-line edits plus one real test-suite build-out. It is a good first phase for a new
contributor and a good candidate to run in parallel with the server-unification wave,
with the caveat in [Risks and sequencing notes](#risks-and-sequencing-notes).

---

## Why this phase exists

### What `REMAINING.md` records as fixed

From the main body, §"09-07 — HTML escaping, hover, secondary-axis range, mlabel on
lines · PARTIAL":

> Three of the five defects are fixed outright; `hover()` was decided but left
> inert, and the secondary-axis work is half done:
>
> - **Double escaping — fixed in both layouts.** Worth recording how this was
>   checked, because the naive check reads the wrong way round: in `layout(auto)`
>   the title lives in a Bokeh `Div` inside `docs_json`, which the embedding
>   escapes a second time, so the raw HTML shows `Price &amp;amp; Weight` and
>   looks doubly escaped. Decoding the embedding layer gives the Div's real text,
>   `Price &amp; Weight&#x27;s end`, which a browser renders as
>   `Price & Weight's end`. `layout(bs)` writes it directly, escaped once.
>   Both are correct.
> - **Canvas text — fixed in `DashRenderer`.** `title("R&D spend")` → figure
>   title `'R&D spend'`; `xtitle("W&L")` → axis label `'W&L'`. No escaping on
>   canvas glyphs. (Not fixed in the server renderer — see below.)

That verdict is true of exactly three strings. The in-file comment that records the fix
(`dash_render.py:9514-9519`) states the reasoning this phase generalises:

```python
        # "R&amp;D spend".  _axis_label() never escaped the variable labels it
        # returns and was already correct -- that is the evidence that the
        # escaping here was the bug rather than the protection.  Everything
        # that genuinely reaches the DOM is still escaped.
        x_label = raw_xtitle if raw_xtitle else self._axis_label(xvar)
        y_label = raw_ytitle if raw_ytitle else self._axis_label(yvar)
```

### What `REMAINING.md` records as still broken

Same section, "Remaining", items 2 and 3:

> 2. **Canvas text is still escaped in the server renderer.** The 09-07 fix was
>    applied to `DashRenderer` only; `ServerAppBuilder` still `html.escape()`s
>    the figure title, both axis labels, the subtitle `Label` and the facet
>    title, so `title("R&D spend")` draws `R&amp;D spend` under `dash serve`.
> 3. **Legend text is still escaped in both renderers** — the same defect class
>    as the titles, left behind: `legend(label(N "..."))` overrides and the
>    colour-key labels reach a canvas but are HTML-escaped on the way.

The adversarial pass (Appendix C) then found that both of those understate the
problem. From Appendix C, 09-07:

> **[func · both · S]** Canvas text is STILL html.escape()d at six more sites
> that the 09-07 fix never touched — the fix only removed the escape from the
> figure title and the two primary axis titles. `legend(label(1 "R&D"))`,
> by()-facet panel titles, the colorvar legend/colorbar title, and
> secondary-axis tick labels all still draw HTML entities on the canvas.

> **[func · standalone · S]** Facet/`by()` titles are still HTML-escaped in
> the STANDALONE renderer. `DashRenderer._facet_label` escapes the Stata value
> label it returns, and that string becomes the facet figure's canvas title —
> the identical defect 09-07 fixed for `title()`/`xtitle()`/`ytitle()`. The
> auditor (and REMAINING.md) reported the facet-title escape only for
> `ServerAppBuilder` (:15096/:15116) and declared canvas text "fixed in
> DashRenderer".

> **[func · server · S]** ServerAppBuilder's canvas escaping is broader than
> the five lines the auditor enumerated — a developer who fixes only the
> figure title, the two axis labels, the subtitle Label and `_fac_title` will
> leave three more mangled sites: the facet VALUE label (the part that
> actually carries user text), the LegendItem labels built from the emitted
> legend rebuild, and the emitted `legend(label(N "..."))` override.

> **[func · server · S]** The emitted server app double-escapes the
> browser-tab title: `title_text` is built with `html.escape()` once and then
> used BOTH for the header `<h2>` Div (correct) and for `doc.title` (wrong) —
> Bokeh's page template escapes `doc.title` again. Under `dash serve` the tab
> reads `Price &amp; Weight` where `dash build` reads `Price & Weight`.

> **[func · both · S]** Filter dropdown option labels are double-escaped in
> BOTH renderers, so a value label containing `&`, `<` or an apostrophe reads
> as `R&amp;D cars` in the filter widget. Bokeh builds widget DOM with
> `createTextNode`, which is exactly the reasoning the file already records
> for the widget TITLE at :7662 — the same reasoning was never applied to the
> option labels two lines above it.

### The complete site inventory

Every line below was re-read at `dash_render.py` HEAD on this branch while writing this
document; all seventeen still exist, exactly as `REMAINING.md` cites them.

| # | Site | Line | Renderer | What the user sees today |
|---:|---|---|---|---|
| 1 | `DashRenderer._facet_label` → `parts.append(html.escape(label))` | `:8917` | standalone | `by()` panel title draws `R&amp;D` |
| 2 | `GlyphMapper._apply_colorvar` → `Legend(..., title=html.escape(var_display))` | `:3240` | both¹ | categorical colour-key title |
| 3 | `GlyphMapper._apply_colorvar` → `ColorBar(..., title=html.escape(var_display))` | `:3269` | both¹ | continuous colour-bar title |
| 4 | `_make_figure_body` → `text = html.escape(m.group(2))` for `legend(label(N "…"))` | `:10165` | standalone | legend entry text |
| 5 | secondary **y** tick labels → `_safe2 = {str(k): html.escape(str(v)) …}` | `:9703` | standalone | `ylabel2(1 "R&D")` draws `R&amp;D` |
| 6 | secondary **x** tick labels → same construct for `_x2_ax` | `:9738` | standalone | `xlabel2(…)` same |
| 7 | primary axis: escaped `CustomJSTickFormatter` map beside an **unescaped** `major_label_overrides` | `:9152-9158` | standalone | latent — overrides win, escaped copy is dead |
| 8 | `FilterBuilder._safe` applied to dropdown **option** labels | `:7660` (`_safe` at `:7566-7568`) | standalone | `R&amp;D cars` in the `Select` |
| 9 | emitted `x_label = html.escape(raw_xt) …` / `y_label` | `:13834`, `:13835` | server | axis titles |
| 10 | emitted `title=html.escape(go.get('title', '') or '')` in `_fig_kw` | `:13840` | server | figure title |
| 11 | emitted subtitle `_Label(… text=html.escape(_sub_txt) …)` | `:13953` | server | subtitle |
| 12 | emitted `_fac_title = html.escape(go.get('title', '') or '')` | `:15116` | server | facet figure base title |
| 13 | emitted `_fac_parts.append(html.escape(_vl.get(…)))` | `:15096` | server | facet **value** label — the part carrying user text |
| 14 | emitted `LegendItem(label={'value': html.escape(_lbl)}, …)` | `:14951` | server | legend entries |
| 15 | emitted `_lt = html.escape(_lm.group(2))` for `legend(label(N "…"))` | `:14987` | server | legend override text |
| 16 | emitted filter option labels `(str(v), html.escape(str(vlabels.get(…))))` | `:15392` | server | `Select` options |
| 17 | emitted `title_text = html.escape(bo.get('title','') or '')`, then used for the `<h2>` **and** `doc.title` | `:13717`, consumed `:15932`/`:15935` (correct) and `:15940` (wrong) | server | browser tab reads `Price &amp; Weight` |

¹ `GlyphMapper` is copied into the emitted app verbatim by
`ServerAppBuilder._glyph_layer_lines` (`dash_render.py:12315`, spliced at `:12987`), so
sites 2 and 3 are carried by **both** renderers from a single source line.

Sites 1–16 are over-escapes: text that never reaches the DOM. Site 17 is the opposite —
a genuine double-escape of HTML text, and the one site in this phase where the escape
must be *kept* and *moved*, not deleted.

### The in-file precedents that define "correct"

Three places in the same file already do the right thing, and each is the model for a
group of sites:

- **Canvas glyph, no escape** — `dash_render.py:9518-9519` (`x_label`/`y_label`) and
  `:9541` (`title=_parse_textbox_opt(...)`), the 09-07 fix itself. Also
  `dash_render.py:13944`, the *emitted* note/caption `_Label(... text=_ann_txt ...)`,
  which is already unescaped and is the in-file precedent **inside**
  `ServerAppBuilder._generate_app_source` (`:12740`).
- **Widget DOM, no escape** — the comment at `dash_render.py:7662-7668`, two lines below
  the defect at `:7660`:

  ```python
        # NOT html.escape'd.  Bokeh renders a widget title as text and
        # escapes it itself, so escaping here escaped it twice:
        # label(R&D spend) displayed as "R&amp;D spend" on a dropdown while
        # the two slider paths, which do not escape, showed it correctly.
        # Same shape as the figure-title double-escape this file already
        # fixed.  Measured: the raw payload reaches the document in neither
        # path.
  ```

  The reasoning was applied to the widget **title** and never to the **options** two
  lines above it.
- **Page title, raw** — the standalone passes the **raw** `title_text` to `file_html`
  (`dash_render.py:12130`, with the explanatory comment above it, and the Bootstrap
  path's own `title_text` at `:12174`). That is the shape site 17 must adopt.

### Why the escaped tick-label map is dead code rather than a visible bug

Site 7 is the one item in this phase with no user-visible symptom today:

```python
        elif mode == "explicit" and spec["ticks"]:
            axis_obj.ticker = FixedTicker(ticks=spec["ticks"])
            if spec["labels"]:
                safe = {str(k): html.escape(str(v))
                        for k, v in spec["labels"].items()}
                axis_obj.formatter = CustomJSTickFormatter(
                    code=f"const m = {json.dumps(safe)}; "
                         "return m[String(tick)] || String(tick);")
                axis_obj.major_label_overrides = {
                    float(k): v for k, v in spec["labels"].items()}
```

BokehJS's `compute_labels` lets `major_label_overrides` win, so the unescaped copy is
what is drawn. `REMAINING.md` records the same construct a second time, under 09-02,
with a second reason it never fires: the map is keyed with Python's `str(float)`
(`"2000.0"`) while the JS looks up `String(tick)` (`"2000"` for an integral tick), *"so
the lookup always misses"*. Two independent reasons the escaped copy is invisible — and
both of them disappear the moment someone fixes the keying or removes the overrides.
That is the whole argument for fixing it now, in the same commit as its visible
siblings.

### Why the test suite did not catch any of this

Appendix C, 09-07, the deliverable item:

> **[deli · both · S]** Test-suite gap for the canvas-text clause: the only
> fidelity tests are `test_canvas_text_is_not_html_escaped`,
> `test_axis_titles_are_not_html_escaped` and
> `test_an_apostrophe_survives_on_the_canvas`, all of which read
> `fig.title.text` / `fig.xaxis[0].axis_label` of a single unfaceted figure.
> Nothing asserts fidelity for a `by()` panel title, a colorvar
> legend/colorbar title, a `legend(label())` override, primary or secondary
> explicit tick labels, a filter widget's option labels, or ANY canvas string
> produced by ServerAppBuilder.

Confirmed at `test/test_axis_options.py:446-459`:

```python
    def test_canvas_text_is_not_html_escaped(self):
        """Bokeh draws a title as a canvas glyph, not as HTML."""
        fig, _ = _fig_with_gopts(_SCATTER, {"title": "R&D spend"})
        assert str(fig.title.text) == "R&D spend", fig.title.text

    def test_axis_titles_are_not_html_escaped(self):
        fig, _ = _fig_with_gopts(
            _SCATTER, {"xtitle": "R&D spend", "ytitle": "Profit & loss"})
        assert str(fig.xaxis[0].axis_label) == "R&D spend"
        assert str(fig.yaxis[0].axis_label) == "Profit & loss"

    def test_an_apostrophe_survives_on_the_canvas(self):
        fig, _ = _fig_with_gopts(_SCATTER, {"title": "Ford's mileage"})
        assert str(fig.title.text) == "Ford's mileage"
```

Three tests, three model properties, one unfaceted standalone figure. The tests are
exactly as wide as the fix was, which is why the fix looked complete.

### What must **not** regress — the security boundary

Appendix C also records a refutation that constrains this phase. One item in Appendix B
was struck because the test it asked for already exists:

> - **09-07 · the adversarial canvas-text test already exists.** Three live
>   tests drive `graph_options` (canvas) rather than `build_options` (HTML
>   header): `test_html_output.py` `TestXssInHtmlOutput::test_script_tag_in_title_is_escaped`
>   (:486), `TestGraphOptionsInHtml::test_title_xss_not_in_html_unescaped`
>   (:633) and `TestAdversarialPlotOptions::test_xss_in_note_option_escaped`
>   (:939). Proven non-vacuous by mutation — appending the raw graph title to
>   the assembled HTML makes them fail.

Those three tests are the guard rail for this phase. Removing `html.escape` from a
canvas glyph is safe because Bokeh serialises model properties into `docs_json` as
JSON and renders them into a canvas, never into markup — but "safe because" is a claim,
and `test/test_html_output.py:485`, `:632` and `:936` are the measurement. **They must
stay green through every commit in this phase.** No item here touches a string that
reaches the DOM, with the single exception of site 17, where the escape is preserved and
relocated rather than deleted.

---

## Epics

| Epic | Goal | Items |
|---|---|---|
| **26-A — Standalone canvas glyphs** | Extend the 09-07 canvas rule to every remaining glyph in `DashRenderer`: facet titles, legend overrides, secondary-axis ticks, and the latent primary-axis map. | 3, 5, 6, 8 |
| **26-B — The emitted app's canvas text and its tab title** | Apply the same rule inside `ServerAppBuilder._generate_app_source`, and stop double-escaping `doc.title`. | 1, 7, 9 |
| **26-C — Shared sites and the fidelity net** | Fix the sites both renderers share (`GlyphMapper` colour-key titles, filter option labels), and build the parametrised + parity test suite that makes this class of defect impossible to declare fixed prematurely. | 2, 4, 10, 11 |

Epics 26-A and 26-B are independent and may run concurrently. 26-C's fixes are
independent of both; 26-C's **tests** are the acceptance gate for all three and are
written first (rule 8).

---

## User stories

### Epic 26-A — Standalone canvas glyphs

**US-26-A1 — Faceted panel titles.**
*As a Stata user pasting a `twoway` command, I want `by(make)` panel titles to show the
value label exactly as my data spells it, so that a label containing `&`, `<` or an
apostrophe reads as text and not as an HTML entity.*

- **Given** a dataset whose `by()` variable has the value label `R&D cars`
- **When** I run `dash scatter mpg weight, by(origin)` and `dash build`
- **Then** the faceted figure's `fig.title.text` ends in `R&D cars`, not `R&amp;D cars`
- **And** the base title and the `—` separator are unchanged
  (`fig.title.text = f"{orig_title} — {label}" if orig_title else label`,
  `dash_render.py:11487-11488` — `REMAINING.md` cites this consumer as `:11463`;
  verified at HEAD it is `:11488`)

**US-26-A2 — Legend label overrides.**
*As a Stata user, I want `legend(label(1 "R&D"))` to put `R&D` in the legend, so that
the override I typed is the text drawn.*

- **Given** `dash (scatter mpg weight) (scatter mpg length), legend(label(1 "R&D") label(2 "P&L"))`
- **When** the standalone HTML is built
- **Then** the legend item labels are exactly `R&D` and `P&L`

**US-26-A3 — Secondary-axis tick labels.**
*As a Stata user drawing a dual-axis graph, I want `ylabel2(1 "R&D")` to label the
right-hand axis `R&D`, so that the secondary axis behaves like the primary one.*

- **Given** a `yaxis(2)` layer with `ylabel2(1 "R&D" 2 "P&L")`
- **When** the figure is rendered
- **Then** the tick at 1 reads `R&D`
- **And** the secondary axis carries a `major_label_overrides` mapping with the raw
  text, matching the primary-axis path at `:9152-9161`

**US-26-A4 — No dead escaped copy on the primary axis.**
*As a package maintainer, I want the primary axis's `CustomJSTickFormatter` map and its
`major_label_overrides` to hold the same strings, so that whoever changes the keying or
drops the overrides does not silently reintroduce `R&amp;D`.*

- **Given** `xlabel(2000 "low" 4000 "R&D")`
- **When** `_apply_axis_spec` runs
- **Then** the JSON embedded in the formatter's JS and `major_label_overrides` contain
  byte-identical label values

### Epic 26-B — The emitted app's canvas text and its tab title

**US-26-B1 — Server canvas text matches build.**
*As a `dash serve` operator, I want the served dashboard to draw the same title, axis
titles, subtitle and facet titles as `dash build` writes, so that "serve" and "build" are
two deliveries of one dashboard and not two dashboards.*

- **Given** `dash scatter mpg weight, title("R&D spend") subtitle("Q1 & Q2") xtitle("W&L")`
- **When** the emitted app module is executed and `make_document` builds the document
- **Then** the figure title, both axis labels, the subtitle `Label` and any facet title
  contain `&`, never `&amp;`
- **And** the same strings compare equal to the standalone renderer's

**US-26-B2 — Server facet value labels and legends.**
*As a `dash serve` operator, I want the served facet value labels and legend entries to
carry the raw user text, so that the fix does not stop at the four lines the audit first
enumerated.*

- **Given** a served `by()` dashboard whose value label is `R&D cars` and whose legend
  uses `legend(label(1 "P&L"))`
- **When** the document is built
- **Then** the facet title contains `R&D cars` and the `LegendItem` label value is `P&L`

**US-26-B3 — The browser tab.**
*As a dashboard viewer, I want the browser tab to read `Price & Weight`, so that the tab
does not advertise a bug before the page finishes loading.*

- **Given** `dash build, title("Price & Weight")` and the same spec served
- **When** I compare the `<title>` of the built HTML with `doc.title` of the served app
- **Then** both are `Price & Weight`
- **And** the served page's header `<h2>` still contains `Price &amp; Weight` in its
  `Div.text` markup (escaped exactly once, because that string *is* HTML)

### Epic 26-C — Shared sites and the fidelity net

**US-26-C1 — Colour-key titles.**
*As a Stata user, I want `colorvar(rd_spend)` to title its legend or colour bar with the
variable's label as written, so that the colour key reads like the rest of the chart.*

- **Given** a variable whose Stata label is `R&D spend`, used as `colorvar()`
- **When** the graph renders in either mode
- **Then** the `Legend.title` (categorical) or `ColorBar.title` (continuous) is
  `R&D spend`

**US-26-C2 — Filter dropdown options.**
*As a dashboard viewer, I want the filter dropdown to list `R&D cars`, so that the
widget reads the way the data does.*

- **Given** a `filter()` on a variable with the value label `R&D cars`
- **When** the dropdown is built in either mode
- **Then** the `Select.options` entry is `R&D cars`
- **And** the widget **title** is still unescaped, as `:7662-7668` already requires

**US-26-C3 — A test net wide enough to hold the rule.**
*As a package maintainer, I want one parametrised test over every canvas and widget
string property in both renderers, so that no future "fixed" verdict can rest on three
assertions about one unfaceted figure.*

- **Given** a fixture string containing `&`, `<`, `>` and `'`
- **When** the parametrised fidelity test runs over facet titles, colour-key titles,
  legend overrides, primary and secondary tick labels and filter option labels, in both
  renderers
- **Then** every property equals the fixture string exactly
- **And** the mode-parity case asserts the standalone and server values are equal to
  each other as well as to the fixture

---

## Business requirements

| ID | Requirement | How it is verified |
|---|---|---|
| **BR-26.1** | Any text a user supplies that Bokeh renders as a **canvas glyph** is drawn with the characters the user typed. No HTML entity substitution occurs on that path. | Parametrised fidelity test over all canvas properties (both renderers) |
| **BR-26.2** | Any text that reaches the **DOM** is HTML-escaped exactly once, at the single point of interpolation into markup. | `test/test_html_output.py:485`, `:632`, `:936` stay green; site-17 header assertion |
| **BR-26.3** | `dash build` and `dash serve` produce the **same** user-visible strings for the same spec. A difference in escaping between the two modes is a defect. | `test/test_mode_parity.py` fidelity case |
| **BR-26.4** | The browser tab title under `dash serve` equals the `<title>` of the built HTML for the same `title()`. | Parity assertion on `doc.title` vs the built document title |
| **BR-26.5** | Widget text (`Select` options and titles) is passed to Bokeh unescaped, because Bokeh builds widget DOM with `createTextNode`. | Filter-widget fidelity case, both renderers |
| **BR-26.6** | No code path retains a "shadow" escaped copy of a string whose unescaped twin is what actually renders. Where two structures describe the same labels, they hold identical values. | Site-7 equality assertion between the formatter map and `major_label_overrides` |
| **BR-26.7** | Removing an escape never widens the XSS surface: the raw payload of a `graph_options` string must still not appear unescaped in the assembled HTML. | The three existing adversarial tests, re-run and re-proved non-vacuous by mutation |
| **BR-26.8** | Every fix in this phase is preceded by a test that fails on the current tree and passes after the change (CLAUDE.md rule 8). | Commit order; the failing-first list in the test plan |

---

## Technical requirements

All line numbers are current as of `ca5fe35` on `feature/batch4-interactive-layer` and
were re-read while writing this document. `ServerAppBuilder` begins at
`dash_render.py:12265`; everything after it that is a quoted string literal is **emitted
app source**, so an edit there changes a Python string that must remain valid Python
when written out.

### TR-26.1 — Facet titles, standalone (item 5, item 8 clause 1)

`DashRenderer._facet_label` builds the panel label and escapes it:

```python
            label = vlabels.get(str_val) or vlabels.get(int_str) or str_val
            parts.append(html.escape(label))
        return " / ".join(parts)
```

Remove `html.escape` at `dash_render.py:8917` so `parts.append(label)`. The return value
is consumed at `dash_render.py:11487-11488` as

```python
                        orig_title = fig.title.text if fig.title else ""
                        fig.title.text = f"{orig_title} — {label}" if orig_title else label
```

— a canvas glyph. (`REMAINING.md` cites this consumer as `:11463`; re-read at HEAD the
assignment is at `:11488`. The escape site itself, `:8917`, is exactly where
`REMAINING.md` puts it.) Apply the treatment used at `:9518-9519`. The `" / "` join for
multi-variable `by()` is unchanged.

### TR-26.2 — Legend `label(N "…")` overrides, standalone (item 4, item 8 clause 4)

`dash_render.py:10165`, inside `DashRenderer._make_figure_body` (`:9495`):

```python
                    text = html.escape(m.group(2))
```

Drop the escape: `text = m.group(2)`. The value becomes a `LegendItem` label, which
Bokeh draws on the canvas.

### TR-26.3 — Secondary-axis explicit tick labels, standalone (item 6, item 8 clause 5)

`dash_render.py:9703` (`_y2_ax`) and `:9738` (`_x2_ax`) both build:

```python
                        _safe2 = {str(k): html.escape(str(v)) for k, v in _labels2.items()}
```

Unlike the primary axis there is **no** `major_label_overrides` fallback, so the escaped
map is what BokehJS draws: `ylabel2(1 "R&D")` renders `R&amp;D`. Two admissible fixes,
in preference order:

1. **Preferred** — mirror the primary axis at `:9152-9161`: stop escaping *and* set
   `major_label_overrides` on the secondary axis object with the raw values. This makes
   the two axis paths structurally identical, which matters for the axis-grammar phases.
2. **Minimum** — drop `html.escape` from `_safe2` only.

Either way the raw text must be what is drawn. Note that the `str(float)`-vs-`String(tick)`
keying defect `REMAINING.md` records for the primary map under 09-02 applies to these
maps too; fixing the keying is **out of scope for this phase** and belongs to the axis
phases — do not let it block this change, and do not silently fix half of it.

### TR-26.4 — The latent primary-axis disagreement, standalone (item 3, item 8 clause 6)

`dash_render.py:9152-9158` inside `_apply_axis_spec` (`:9112`) builds `safe` at
`:9152-9153` with `html.escape(str(v))` for the `CustomJSTickFormatter` (`:9154-9156`),
then at `:9157-9158` builds `major_label_overrides` with the unescaped `v`.
`major_label_overrides` wins in BokehJS, so today the escaped copy is dead. Remove the `html.escape` from the `safe`
comprehension so both structures carry the same strings. `REMAINING.md` notes the
server's equivalent at `:14019` already passes `_labs` **unescaped** — the emitted side
is the correct precedent here, and after this change both sides agree.

### TR-26.5 — Colour-key titles, shared by both renderers (item 2 clause 2–3, item 4, item 8 clauses 2–3)

`GlyphMapper._apply_colorvar` (`dash_render.py:2995`) at:

- `:3240` — `Legend(items=legend_items, title=html.escape(var_display), …)`
- `:3269` — `ColorBar(…, title=html.escape(var_display)), "right")`

Both are canvas glyphs. Remove both escapes. Because
`ServerAppBuilder._glyph_layer_lines` (`dash_render.py:12315`, spliced into the app at
`:12987`) copies `GlyphMapper` into the emitted app **verbatim**, these two edits fix
both renderers from one source line — and the test net must assert that for both, or the
copy mechanism is untested.

### TR-26.6 — Filter dropdown option labels, both renderers (item 10)

Standalone: `FilterBuilder._safe` is defined at `dash_render.py:7566-7568` as
`html.escape(str(value), quote=True)` and applied to **option** labels at `:7660`:

```python
            options.append((rv, FilterBuilder._safe(_resolve_label(rv))))
```

Two lines later, `:7662-7668` documents why this is wrong for widget text and applies the
correct treatment to the widget **title**. Stop escaping the option labels; keep
`FilterBuilder._safe` for any caller that genuinely emits markup, or remove the helper if
this was its last such use — check callers before deleting.

Server: the same construct is emitted at `dash_render.py:15392`:

```python
"                (str(v), html.escape(str(vlabels.get(str(int(v)) if isinstance(v, float) and v == int(v) else str(v), v))))",
```

Remove the `html.escape(...)` wrapper, keeping the `str(...)` coercion and the
float/int key-resolution logic exactly as they are.

### TR-26.7 — Emitted canvas text (item 1, item 9)

All inside `ServerAppBuilder._generate_app_source` (`dash_render.py:12740`). Remove
`html.escape` from the emitted expression at each of:

| Line | Emitted source | Draws |
|---|---|---|
| `:13834` | `x_label = html.escape(raw_xt) if raw_xt else var_labels.get(xv, xv)` | x axis title |
| `:13835` | same for `y_label` | y axis title |
| `:13840` | `title=html.escape(go.get('title', '') or ''),` in `_fig_kw` | figure title |
| `:13953` | `_Label(… text=html.escape(_sub_txt), text_font_size='13px', text_color='#444444'), 'above')` | subtitle |
| `:15096` | `_fac_parts.append(html.escape(_vl.get(_sv) or _vl.get(_iv) or _sv))` | facet **value** label |
| `:15116` | `_fac_title = html.escape(go.get('title', '') or '')` | facet base title |
| `:14951` | `_items.append(LegendItem(label={'value': html.escape(_lbl)},` | legend entries |
| `:14987` | `_lt = html.escape(_lm.group(2))` | legend `label(N "…")` override |

Preserve the `or ''` guards, the `_vl.get(...) or ...` fallback chain and the
`text_font_size`/`text_color` keyword arguments verbatim — only the escape call is
removed. The in-file precedent for the correct emitted form is `dash_render.py:13944`,
the note/caption `_Label(... text=_ann_txt ...)`, which is already unescaped.

After the edits, `html.escape` must remain in the emitted region **only** where the
emitted string is interpolated into markup — i.e. the header `<h2>`/`<div>` path of
TR-26.8. A grep for `html.escape` after `:12265` is the review check.

### TR-26.8 — The double-escaped tab title (item 7)

`dash_render.py:13717` emits:

```python
"    title_text = html.escape(bo.get('title', '') or '')",
```

That single escaped local is then used in two places (`dash_render.py:15930-15940`):

```python
            '        if title_text:',
            '            _head += f\'<h2 style="font-family:sans-serif;margin-bottom:2px;">{title_text}</h2>\'',
            ...
            "        title_div = Div(text=_head, sizing_mode='stretch_width')",
            ...
            "    doc.title = title_text or 'dash'",
```

`:15932`/`:15935` are **correct** — that string is interpolated into markup. `:15940` is
**wrong** — Bokeh's page template escapes `doc.title` again, so the tab reads
`Price &amp; Weight`.

Fix: emit two locals. Keep the raw title (e.g. `title_raw = bo.get('title', '') or ''`)
and derive the escaped one at, or immediately before, the `<h2>`/`<div>` interpolation
sites. Assign the **raw** string to `doc.title`. The same split applies to
`subtitle_text`, which is interpolated into the header `<div>` at `:15934-15935` — it has
no `doc.title` consumer, so it stays escaped, but the naming must make the distinction
obvious to the next reader.

The standalone precedent is `dash_render.py:12130`:

```python
        html_str = file_html(layout_root, INLINE, title=title_text or "dash")
```

— the **raw** title, with the comment above it explaining the earlier double escape; and
the Bootstrap path's own `title_text` at `:12174`, which splices into an existing
`<head>` itself.

### TR-26.9 — The test net (item 11)

`test/test_axis_options.py::TestTitleTextFidelity` (`:420-459`) is the natural home. It
currently holds three canvas assertions (`:446`, `:451`, `:457`) plus three
sub-option/style tests. Extend it to a parametrised suite over `(property, builder)`
pairs covering, for **both** renderers:

| Property under test | Standalone reader | Server reader |
|---|---|---|
| facet panel title | `fig.title.text` of a `by()` panel | same, from the served document |
| colorvar `Legend.title` | `Legend` model on the figure | same |
| colorvar `ColorBar.title` | `ColorBar` model | same |
| `legend(label(N "…"))` override | `LegendItem.label['value']` | same |
| primary explicit tick labels | `axis.major_label_overrides` **and** the JSON inside `axis.formatter.code` | `axis.formatter.code` map |
| secondary explicit tick labels | `_y2_ax` / `_x2_ax` formatter and overrides | n/a (no secondary axis in server mode — Phase 27) |
| filter `Select.options` | `Select` model in the layout | same |
| document/tab title | built HTML `<title>` | `doc.title` |

For the server side, reuse the harness shape already proven at
`test/test_server_legend.py:48-76` — `_figs(tmp_path, plots, graph_options, server=True)`
writes the spec and data JSON, calls
`dr.ServerAppBuilder(str(spec), str(data)).build(str(ap))`, imports the emitted module,
calls `mod.make_document(doc)` and selects the figures out of the `Document`. Selecting
non-figure models (`Legend`, `ColorBar`, `Select`, `Label`) from the same `Document` is
the only extension needed.

The parity case belongs in `test/test_mode_parity.py`, alongside
`TestTheTwoModesAgree` (`:289`) and its existing `test_same_figure_chrome` (`:337`) and
`test_same_annotations` (`:320`) cases. It must assert **equality between the two modes**,
not merely that each is unescaped — that is what catches a future fix applied to one
renderer only, which is the exact failure mode that produced this phase.

The fixture string should exercise all four characters `html.escape(..., quote=True)`
touches: `&`, `<`, `>` and `'` — e.g. `R&D <'q1'> spend`.

---

## Work items

Every item below is reproduced from the phase assignment with its original numbering,
kind, renderer and effort tag. Nothing is merged or summarised.

### 1. Remove `html.escape()` from the canvas text emitted by `ServerAppBuilder`
`[func · server · S]` · origin `09-07` · Appendix B

Remove `html.escape()` from the canvas text emitted by ServerAppBuilder: the figure
title, both axis labels, the subtitle Label and the facet title. The 09-07 fix was
applied to DashRenderer only.

*Where:* `dash_render.py:13834`, `:13835` (x_label/y_label), `:13840` (`_fig_kw title=`),
`:13953` (subtitle `_Label text=`), `:15116` (`_fac_title`) — all inside
`ServerAppBuilder._generate_app_source` (`dash_render.py:12740`). Note `:13944`
(note/caption `_ann_txt`) is already correct and is the in-file precedent.

### 2. Canvas text is still HTML-escaped in the legend in BOTH renderers
`[func · both · S]` · origin `09-07` · Appendix B

Canvas text is still HTML-escaped in the legend in BOTH renderers — the same class of
defect 09-07 fixed for titles, left behind. `legend(label(N "..."))` overrides, the
colorvar Legend title and the ColorBar title are Bokeh canvas glyphs.

*Where:* `dash_render.py:10165` (`text = html.escape(m.group(2))` for `label(N "text")`
overrides, in `_make_figure_body` `:9495`); `:3240` and `:3269`
(`Legend(... title=html.escape(var_display))` and
`ColorBar(... title=html.escape(var_display))` in `_apply_colorvar` `:2995`); server
equivalents at `:14951` (`LegendItem(label={'value': html.escape(_lbl)}`) and `:14987`
(`_lt = html.escape(_lm.group(2))`).

### 3. Latent: the primary-axis formatter map and its overrides disagree
`[func · standalone · S]` · origin `09-07` · Appendix B

Latent: the `CustomJSTickFormatter` map built for explicit axis tick labels escapes the
label text while the parallel `major_label_overrides` does not — the two disagree, and
only the overrides path is currently user-visible.

*Where:* `dash_render.py:9152-9158` in `_apply_axis_spec` (`:9112`) —
`safe = {str(k): html.escape(str(v)) ...}` feeding `CustomJSTickFormatter`, immediately
followed by `major_label_overrides = {float(k): v ...}` with the unescaped value. The
server's equivalent at `:14019` already passes `_labs` unescaped.

### 4. Canvas text is STILL `html.escape()`d at six more sites
`[func · both · S]` · origin `09-07` · Appendix C

Canvas text is STILL `html.escape()`d at six more sites that the 09-07 fix never touched
— the fix only removed the escape from the figure title and the two primary axis titles.
`legend(label(1 "R&D"))`, `by()`-facet panel titles, the colorvar legend/colorbar title,
and secondary-axis tick labels all still draw HTML entities on the canvas.

*Where:* `dash_render.py:10165` (`DashRenderer._make_figure_body`, legend
`label(N "...")` overrides) and its server twin `dash_render.py:14987`
(`_lt = html.escape(_lm.group(2))`); `dash_render.py:8917` (`DashRenderer._facet_label`,
`parts.append(html.escape(label))`) and its server twin `:15096`
(`_fac_parts.append(html.escape(...))`); `dash_render.py:3240` and `:3269`
(`GlyphMapper._apply_colorvar`, `Legend(title=html.escape(var_display))` /
`ColorBar(title=html.escape(var_display))`) — `GlyphMapper` is copied into the emitted
app verbatim by `ServerAppBuilder._glyph_layer_lines`, so both renderers carry these two;
`dash_render.py:9703` and `:9738` (secondary-axis `ylabel2()`/`xlabel2()`
`CustomJSTickFormatter`, escaped with NO `major_label_overrides` fallback). The in-file
precedent for the correct treatment is `dash_render.py:9518-9519` and `:9541`, which
09-07 already fixed.

### 5. Facet/`by()` titles are still HTML-escaped in the STANDALONE renderer
`[func · standalone · S]` · origin `09-07` · Appendix C

Facet/`by()` titles are still HTML-escaped in the STANDALONE renderer.
`DashRenderer._facet_label` escapes the Stata value label it returns, and that string
becomes the facet figure's canvas title — the identical defect 09-07 fixed for
`title()`/`xtitle()`/`ytitle()`. The auditor (and REMAINING.md) reported the facet-title
escape only for `ServerAppBuilder` (`:15096`/`:15116`) and declared canvas text "fixed in
DashRenderer". Fix: drop `html.escape` at `dash_render.py:8917` the same way `:9518-9519`
were fixed.

*Where:* `dash_render.py:8917` (`DashRenderer._facet_label`); compare the in-file
precedent at `:9517-9519` and `:9541`.

### 6. `ylabel2()`/`xlabel2()` custom tick labels are escaped with no fallback
`[func · standalone · S]` · origin `09-07` · Appendix C

`ylabel2()`/`xlabel2()` custom tick labels are HTML-escaped into the
`CustomJSTickFormatter` and, unlike the primary axis, get NO `major_label_overrides` to
mask it — so `ylabel2(1 "R&D")` draws `R&amp;D` on the secondary axis. Fix: either stop
escaping at `dash_render.py:9703`/`:9738`, or set `major_label_overrides` with the raw
text the way the primary-axis path at `:9152-9161` does.

*Where:* `dash_render.py:9703` (`_safe2` for `_y2_ax.formatter`), `:9738` (same for
`_x2_ax`); correct precedent at `:9152-9161` (`safe` + `axis_obj.major_label_overrides`).

### 7. The emitted server app double-escapes the browser-tab title
`[func · server · S]` · origin `09-07` · Appendix C

The emitted server app double-escapes the browser-tab title: `title_text` is built with
`html.escape()` once and then used BOTH for the header `<h2>` Div (correct) and for
`doc.title` (wrong) — Bokeh's page template escapes `doc.title` again. Under `dash serve`
the tab reads `Price &amp; Weight` where `dash build` reads `Price & Weight`. This is the
same 09-07 "escape once, in one place" clause, still open in server mode. Fix: keep the
raw title in a separate local, escape only at the `<h2>`/`<div>` interpolation sites, and
assign the raw string to `doc.title` (mirroring the standalone, which passes the RAW
`title_text` to `file_html`).

*Where:* `dash_render.py:13717` and `:15940` (emitted lines inside
`ServerAppBuilder._generate_app_source`, `:12740`); header consumers at `:15932`/`:15935`;
standalone precedent at `:12130` + `:12174`.

### 8. DashRenderer still escapes five more pieces of canvas text
`[func · standalone · S]` · origin `09-07` · Appendix C

The canvas-escaping fix was applied to the figure title and the two axis titles only;
DashRenderer still `html.escape()`s five more pieces of canvas text. Every one is a Bokeh
glyph, not HTML: (1) `by()` panel titles via `_facet_label`; (2) the categorical colorvar
Legend title; (3) the continuous colorvar ColorBar title; (4) `legend(label(N "..."))`
overrides; (5) the secondary-axis explicit tick labels. A sixth site is inconsistent
rather than visibly wrong: the primary axis sets an ESCAPED `CustomJSTickFormatter` map
and an UNESCAPED `major_label_overrides` for the same ticks — BokehJS's `compute_labels`
lets the override win, so the escaped copy is dead code that will bite whoever removes
the overrides.

*Where:* `dash_render.py:8917` (`_facet_label`, consumed at `:11463`
`fig.title.text = f"{orig_title} — {label}"`); `:3240`
(`Legend(..., title=html.escape(var_display))`); `:3269`
(`ColorBar(..., title=html.escape(var_display))`); `:10165` (legend `label()` override);
`:9703` and `:9738` (secondary y/x explicit tick labels); `:9152-9158` (primary axis:
escaped formatter vs unescaped `major_label_overrides`).

### 9. ServerAppBuilder's canvas escaping is broader than five lines
`[func · server · S]` · origin `09-07` · Appendix C

ServerAppBuilder's canvas escaping is broader than the five lines the auditor enumerated
— a developer who fixes only the figure title, the two axis labels, the subtitle Label
and `_fac_title` will leave three more mangled sites: the facet VALUE label (the part
that actually carries user text), the LegendItem labels built from the emitted legend
rebuild, and the emitted `legend(label(N "..."))` override.

*Where:* `dash_render.py`, inside `ServerAppBuilder._generate_app_source` (`:12740`):
`:15096` `_fac_parts.append(html.escape(_vl.get(...)))`; `:14951`
`LegendItem(label={'value': html.escape(_lbl)}, ...)`; `:14987`
`_lt = html.escape(_lm.group(2))`.

### 10. Filter dropdown option labels are double-escaped in BOTH renderers
`[func · both · S]` · origin `09-07` · Appendix C

Filter dropdown option labels are double-escaped in BOTH renderers, so a value label
containing `&`, `<` or an apostrophe reads as `R&amp;D cars` in the filter widget. Bokeh
builds widget DOM with `createTextNode`, which is exactly the reasoning the file already
records for the widget TITLE at `:7662` — the same reasoning was never applied to the
option labels two lines above it.

*Where:* `dash_render.py`: `FilterBuilder._safe` (`:7566-7568`) applied to option labels
at `:7660` (`options.append((rv, FilterBuilder._safe(_resolve_label(rv))))`); the in-file
precedent explaining why this is wrong is the comment at `:7662-7668`. Server equivalent:
`:15392` inside `_generate_app_source`.

### 11. Test-suite gap for the canvas-text clause
`[deli · both · S]` · origin `09-07` · Appendix C

Test-suite gap for the canvas-text clause: the only fidelity tests are
`test_canvas_text_is_not_html_escaped`, `test_axis_titles_are_not_html_escaped` and
`test_an_apostrophe_survives_on_the_canvas`, all of which read `fig.title.text` /
`fig.xaxis[0].axis_label` of a single unfaceted figure. Nothing asserts fidelity for a
`by()` panel title, a colorvar legend/colorbar title, a `legend(label())` override,
primary or secondary explicit tick labels, a filter widget's option labels, or ANY canvas
string produced by ServerAppBuilder. Add a parametrised test over those model properties,
plus a mode-parity case (`test/test_mode_parity.py`) asserting standalone and server
agree on the same `&`-bearing strings.

*Where:* `test/test_axis_options.py::TestTitleTextFidelity` (`:420-459`) — the natural
home; `test/test_mode_parity.py` for the standalone-vs-server parity case.

---

## Test plan

CLAUDE.md rule 8 governs the order: **the failing test is written and committed before
the fix.** Rule 4 governs the breadth: every function this phase touches gets a unit
test. Item 11 is the deliverable that discharges both, so in practice 26-C's test work
comes first and 26-A/26-B turn its red cases green.

### Shared fixture

One string for every case: `R&D <'q1'> spend` — it exercises all four characters
`html.escape(..., quote=True)` substitutes (`&`, `<`, `>`, `'`). Assertions compare for
**exact equality** with that string, never `"&amp;" not in text`; an absence assertion
passes on an empty string and is how this class of bug hides.

### Epic 26-A — Standalone canvas glyphs (items 3, 5, 6, 8)

**Write first (must fail on the current tree):**

| Test | File | Fails today because |
|---|---|---|
| `test_facet_panel_titles_are_not_html_escaped` | `test/test_axis_options.py::TestTitleTextFidelity` | `:8917` escapes the value label; the panel title reads `R&amp;D …` |
| `test_legend_label_override_is_not_html_escaped` | same | `:10165` escapes the override text |
| `test_secondary_axis_tick_labels_are_not_html_escaped` | same | `:9703`/`:9738` escape into the formatter with no override fallback |
| `test_primary_tick_formatter_and_overrides_carry_the_same_text` | same | `:9152-9153` escapes the formatter map while `:9157-9158` does not |

**Unit tests (rule 4), on the functions changed:**

- `DashRenderer._facet_label` (`:8917`) — call it directly with a `vlabels` dict holding
  the fixture string; assert the return value and the `" / "` join for a two-variable
  `by()`. Assert the `str_val` / `int_str` lookup order is unchanged by passing a float
  value `1.0` against an `int_str` key.
- `DashRenderer._apply_axis_spec` (`:9112`) — assert `FixedTicker.ticks`,
  `major_label_overrides` and the JSON embedded in `formatter.code` all hold the fixture
  string, and that the `spec["format"]` fallback at `:9160-9162` still fires for a spec
  with no labels.

**Integration:** one `by()` + `legend(label())` + `ylabel2()` figure built through
`_fig_with_gopts` and asserted end to end, so the four fixes are proved to compose.

**Non-vacuity by mutation** — each test must die when the fix is reverted:

| Test | Mutation that must kill it |
|---|---|
| facet title | restore `html.escape(label)` at `:8917` |
| legend override | restore `html.escape(m.group(2))` at `:10165` |
| secondary ticks | restore `html.escape` in `_safe2`, **and separately** delete the new `major_label_overrides` assignment — both must fail it, or the test only covers one of the two admissible fixes |
| formatter/override equality | restore `html.escape` in the `safe` comprehension at `:9152` |

### Epic 26-B — Emitted app canvas text and the tab title (items 1, 7, 9)

**Write first (must fail on the current tree):**

| Test | File | Fails today because |
|---|---|---|
| `test_server_canvas_text_is_not_html_escaped` (parametrised over figure title, x/y axis labels, subtitle) | `test/test_axis_options.py` (server harness) | `:13834`, `:13835`, `:13840`, `:13953` |
| `test_server_facet_titles_are_not_html_escaped` (base title **and** value label) | same | `:15116` and `:15096` |
| `test_server_legend_text_is_not_html_escaped` | `test/test_server_legend.py` | `:14951` and `:14987` |
| `test_the_served_tab_title_is_escaped_once` | `test/test_mode_parity.py` | `:13717` + `:15940`; `doc.title` reads `Price &amp; Weight` |

**Harness:** reuse the shape at `test/test_server_legend.py:48-76` —
`ServerAppBuilder(...).build(path)`, import the emitted module, `mod.make_document(doc)`,
then select the models out of the `Document`. Extend the selection beyond `figure` to
`Legend`, `LegendItem`, `Label`, `ColorBar` and `Select`.

**Unit test (rule 4) on the generator itself:** a source-level guard that
`html.escape` appears after `dash_render.py:12265` **only** on lines that interpolate into
markup — i.e. the header `<h2>`/`<div>` path. Implemented as a scan of
`ServerAppBuilder(...)._generate_app_source(port)`, asserting an explicit allow-list of
occurrences with a stated reason for each. `test/test_mode_parity.py` already uses this
pattern: `TestTheAllowanceListIsExplicit::test_every_allowance_states_a_reason` (`:389`).
This is the ratchet that stops the next emitted string from arriving pre-escaped.

**Non-vacuity by mutation:**

| Test | Mutation that must kill it |
|---|---|
| server canvas text | restore `html.escape` at any one of `:13834`, `:13840`, `:13953` — run the mutation once per site, since a parametrised test can pass on the strength of its other parameters |
| server facet | restore `html.escape` at `:15096` **only** (not `:15116`) — this is the site the original audit missed, so the test must be sensitive to it alone |
| tab title | assign the escaped local back to `doc.title` at `:15940` |
| allow-list guard | add a gratuitous `html.escape` to any emitted canvas line |

**Header must not regress:** the same tab-title test asserts the header `Div.text` still
contains `&amp;` — escaped exactly once — so the fix cannot be "delete the escape
everywhere".

### Epic 26-C — Shared sites and the fidelity net (items 2, 4, 10, 11)

**Write first (must fail on the current tree):**

| Test | File | Fails today because |
|---|---|---|
| `test_colorvar_legend_title_is_not_html_escaped` (categorical) | `test/test_axis_options.py::TestTitleTextFidelity` | `:3240` |
| `test_colorvar_colorbar_title_is_not_html_escaped` (continuous) | same | `:3269` |
| the same two, run against the **server** document | same, server harness | `GlyphMapper` is copied verbatim, so both fail from one source line — and the test proves the copy carries the fix |
| `test_filter_option_labels_are_not_html_escaped` (both modes) | `test/test_axis_options.py` + server harness | `:7660` and `:15392` |
| `test_filter_widget_title_is_still_unescaped` | same | guard: must pass **before and after**, protecting the `:7662-7668` fix from collateral damage |
| `test_the_two_modes_agree_on_canvas_text` (parametrised) | `test/test_mode_parity.py::TestTheTwoModesAgree` | any single-renderer fix leaves the pair unequal |

**Unit tests (rule 4):**

- `GlyphMapper._apply_colorvar` (`:2995`) — called directly for a categorical and a
  continuous `colorvar`, asserting `Legend.title` and `ColorBar.title`.
- `FilterBuilder._safe` (`:7566-7568`) — if the helper survives the change, a test
  pinning what it is still *for*; if its last caller is removed, a test asserting the
  symbol is gone, so the dead helper cannot quietly return.

**Regression boundary, re-proved:** `test/test_html_output.py:485`
(`test_script_tag_in_title_is_escaped`), `:632`
(`test_title_xss_not_in_html_unescaped`) and `:936`
(`test_xss_in_note_option_escaped`) must stay green. `REMAINING.md` records that these
were proven non-vacuous by mutation — *"appending the raw graph title to the assembled
HTML makes them fail"* — so re-run that mutation once at the end of the phase and record
the result. This is the evidence that removing sixteen escapes did not widen the XSS
surface.

**Optional end-to-end (cscript):** a Stata-level case in `test/`, following
`test/test_e2e_single.cscript`'s shape, that builds a dashboard with a `&` in
`title()`, a `by()` on a variable whose value label contains `&`, and a `filter()` on the
same variable, then greps the written HTML for the decoded text. It is optional because
the pytest net already covers the model properties; it is valuable because it is the only
test in this phase that runs through the real Stata path. Run the suite per
`project_stata_cert_suite`: `arch -arm64` from `test/`, and remember a skip is not a pass.

---

## Definition of done

A reviewer can tick every line below.

**Code**

- [ ] `dash_render.py:8917` — `_facet_label` returns the raw value label (item 5, 8)
- [ ] `dash_render.py:10165` — legend `label(N "…")` override unescaped (item 2, 4, 8)
- [ ] `dash_render.py:3240` — colorvar `Legend.title` unescaped (item 2, 4, 8)
- [ ] `dash_render.py:3269` — colorvar `ColorBar.title` unescaped (item 2, 4, 8)
- [ ] `dash_render.py:9703` and `:9738` — secondary-axis tick labels unescaped, with
      `major_label_overrides` set from the raw text (item 6, 8)
- [ ] `dash_render.py:9152-9158` — formatter map and `major_label_overrides` carry
      identical strings (item 3, 8)
- [ ] `dash_render.py:7660` — filter option labels unescaped; `:7662-7668` widget-title
      behaviour unchanged (item 10)
- [ ] `dash_render.py:13834`, `:13835`, `:13840`, `:13953`, `:15116` — emitted canvas
      text unescaped (item 1)
- [ ] `dash_render.py:15096`, `:14951`, `:14987` — emitted facet value label, LegendItem
      labels and legend override unescaped (item 9)
- [ ] `dash_render.py:15392` — emitted filter option labels unescaped (item 10)
- [ ] `dash_render.py:13717`/`:15940` — raw title reaches `doc.title`; the escaped copy is
      built at the `<h2>`/`<div>` sites only (item 7)
- [ ] `grep -n "html.escape" dash_render.py` after line `12265` returns only lines on the
      markup-interpolation path, each covered by the allow-list guard

**Tests**

- [ ] Every test in the plan was committed **red** before its fix and is green after
      (rule 8), with the failing run recorded in the commit message
- [ ] `TestTitleTextFidelity` is parametrised over every property in the TR-26.9 table,
      for both renderers
- [ ] `test/test_mode_parity.py` asserts standalone and server produce **equal** strings
      for the fixture, including `doc.title` vs the built `<title>`
- [ ] Each mutation in the "must kill it" columns was applied and observed to fail the
      named test; the results are recorded
- [ ] `test/test_html_output.py:485`, `:632`, `:936` are green, and the
      raw-title-into-HTML mutation still kills them
- [ ] The emitted-source allow-list guard exists and states a reason per allowed
      occurrence
- [ ] Full suite green (pytest + the Stata cert suite, `arch -arm64` from `test/`) before
      any commit, per CLAUDE.md rule 5

**Behaviour, spot-checked by hand**

- [ ] `dash scatter mpg weight, title("R&D spend") by(foreign) legend(label(1 "P&L"))`
      then `dash build` — every string on the canvas reads with `&`
- [ ] The same spec under `dash serve` — identical canvas text, and the browser tab reads
      `R&D spend`
- [ ] A `filter()` dropdown on a variable with an `&`-bearing value label lists the raw
      text

---

## Risks and sequencing notes

**1. The server-unification phases will rewrite some of these lines.** Items 1 and 9
touch emitted source inside `ServerAppBuilder._generate_app_source` — specifically the
per-plot legend rebuild (`:14951`, `:14987`) and the facet loop (`:15096`, `:15116`).
`REMAINING.md` records under 15-03 that the facet loops *"were never unified"* and that
`_expand_by_groups` occurs 3× in `DashRenderer` and **0×** in the emitted app; Phases
05–08 exist to replace exactly that code. If those phases land after this one, an escape
can return in the rewritten loop. **Mitigation:** the emitted-source allow-list guard
(TR-26.9 / Epic 26-B) and the mode-parity case are ratchets, not one-time assertions —
they fail on any new escaped canvas string regardless of which phase introduces it. Land
the guard early and treat it as a merge gate for Phases 05–08.

**2. Items 2, 4, 8 and 10 overlap by design.** Four items name `:3240`, `:3269`, `:10165`
and the secondary-axis sites, because three independent audit lenses found the same
lines. A developer should fix each **site** once and tick every item that names it. The
site inventory table in *Why this phase exists* is the working list; the work items are
the provenance. Do not open four commits for one line.

**3. `GlyphMapper` is shared, so one edit changes two renderers.**
`ServerAppBuilder._glyph_layer_lines` (`:12315`) copies the class verbatim into the
emitted app. Fixing `:3240`/`:3269` fixes both modes at once — which is good, and is also
why the test net must assert the property in **both** documents. A test that only checks
the standalone would pass while proving nothing about the copy mechanism.

**4. The secondary-axis tick fix has two admissible shapes.** TR-26.3 prefers mirroring
the primary axis (unescape **and** add `major_label_overrides`) over the minimum fix
(unescape only). The preferred shape is more work now and less work in Phases 14–16,
which have to reconcile the primary and secondary axis paths anyway. Whichever is chosen,
the test must be sensitive to both halves — see the mutation table.

**5. Do not fix the tick-map keying here.** `REMAINING.md` records under 09-02 that the
`CustomJSTickFormatter` map is keyed `"2000.0"` while the JS looks up `"2000"`, so the
lookup always misses. That is a separate defect in a separate phase. Fixing the escaping
without the keying is safe (the overrides already win on the primary axis); fixing the
keying without the escaping would make the escaped map **user-visible for the first
time**, which is a good reason to land this phase first.

**6. Security review is cheap here but must be explicit.** Sixteen sites — seventeen
`html.escape()` calls, since site 9 in the inventory covers both `:13834` and `:13835` —
are being deleted. The argument that this is safe is architectural — Bokeh serialises model
properties into `docs_json` and draws them on a canvas — but the *evidence* is the three
adversarial tests at `test/test_html_output.py:485`, `:632`, `:936`, plus the new widget
cases. The reviewer should ask for the mutation result, not the argument. Per CLAUDE.md
rule 13, this phase is also a natural moment to grep for any *other* place a user string
reaches markup without an escape; anything found belongs in a new item, not a silent fix.

**7. No dependency, high leverage.** This phase depends on nothing and is listed in the
index as unblocking Phase 27 (*Text fidelity II — `hover()` and the secondary axis*).
Eleven small items, one file, no Stata-side change: it is the cheapest phase in the plan
that closes a user-visible correctness gap, and it is a good first phase for a
contributor learning the two-renderer structure, because doing it requires reading both.
