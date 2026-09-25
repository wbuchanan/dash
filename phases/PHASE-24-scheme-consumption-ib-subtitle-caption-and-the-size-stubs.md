# Phase 24 — Scheme consumption I(b): subtitle, caption and the size stubs

**Purpose.** Section 11's promise is that a translated scheme is *visible* — "As a Stata
user with `set scheme economist`, my dashboard is an Economist dashboard — colours,
symbols, line weights, fonts and backgrounds — without my passing any option." Phase 23
takes the text sizes that already have a parsed scheme key (mlabel, title, note) and
routes them onto models. This phase takes the ones that have **no key to route**, or
**no delivery path to route through**. Three of the six text names the section's own TDD
stub enumerates — subtitle, note, caption — are drawn today from hardcoded literals, and
two of them cannot be fixed inside `dash_render.py` at all, because the Stata style each
one derives from (`textboxstyle-subheading`, `textboxstyle-body`) reads scheme keys that
`SchemeParser` does not parse and that all fourteen translated `.scheme` files dropped on
purpose. Alongside that, the CSS block those same values feed reaches nothing in two of
the three places it is supposed to apply: `bokeh serve` never calls `css_block()` at all,
and in the auto layout the classed markup lives inside Bokeh `Div` models, which Bokeh 3
renders in a shadow root where a document-level rule cannot match. The phase closes with
the guard the section asked for — a rendered-model assertion over all six text names, per
renderer — so the clause stops being defended by a source-count proxy.

---

## At a glance

| | |
|---|---|
| **Items** | 9 (work items 1–9, exactly as assigned) |
| **Functional vs deliverable** | 8 functional · 1 deliverable (item 9) |
| **Effort mix** | 6 small · 3 medium · 0 large |
| **Renderers touched** | `both` 5 (items 1, 6, 7, 8, 9) · `server` 2 (items 2, 3) · `standalone` 2 (items 4, 5) |
| **Files at the centre** | `dash_render.py` (`SchemeParser._init_properties`, `DashRenderer._make_figure_body`, `DashRenderer._assemble_layout`, `GlyphMapper._apply_colorvar`, `ServerAppBuilder`), `schemes/*.scheme` (all 14), `test/test_scheme_consumption.py`, `test/test_server_scheme.py`, `test/test_scheme.py` |
| **Ultraplan task discharged** | **11-04** — "Consume the remaining discarded keys and fix the dead CSS" (section **S11**, Scheme consumption and fidelity) |
| **Which clauses of 11-04** | the `Text:` paragraph's *"`note_font_size` reaches the note; the subtitle uses a real scheme value"*; the `**The dead CSS.**` paragraph's *"Align them so the block applies"* on the server and auto-layout paths; the chrome half of the `Colour mapping:` paragraph (the continuous `ColorBar`); and the TDD stub *"Test: title, subtitle, axis-title, tick-label, note and caption sizes come from the scheme."* |
| **Shares 11-04 with** | Phase 23 (I(a) — text sizing and typography, 8 items) and Phase 25 (II — legend, colour mapping and CSS delivery, 15 items). 32 items total across the three. |
| **Depends on** | **Phase 23** (the `_gsize` numeric branch must be correct before any new `gsize` key is trusted; the note/`note_font_size` disposition collides — see Risks) · **Phase 03** (packaged install and scheme reachability: as installed, every scheme is inert, so none of this is visible to a real user until that lands) · **Phase 29** (S03 scheme ground truth — items 6 and 7 edit all 14 `.scheme` files) |
| **Unblocks** | **Phase 25** (shares the `css_block()` delivery surface and the `ColorBar` `add_layout` call) · **S11-06** (the by-eye Stata fidelity check cannot pass while the note is 11px and the subtitle 13px regardless of scheme) · **S16-06 / S16-07** release gates |

---

## Why this phase exists

Everything below is copied from `REMAINING.md` (the audit of all 89 tasks against
`ca5fe35`), with the source lines confirmed against `dash_render.py` at HEAD
(16,264 lines). A developer should not need to open `REMAINING.md` to work this phase.

### The section's own status line

> | # | Section | Tasks | Status | What is left |
> |---|---|---:|---|---|
> | 11 | Scheme consumption | 6 | **11-05 not done** ①, 6 partial ② | error not warning; Stata-side validation; retire `.scheme` path; help; scheme-driven **text sizing** (title, note, subtitle, mlabel) still ignored ② |

### What Appendix A measured for 11-04

> **The dead CSS is fixed and mechanically guarded.** `css_block()` now emits
> `.db-title`, `.db-subtitle` and `.db-kpi-card`, and each matches a class the
> HTML actually uses. The guard the task demanded exists:
> `test/test_scheme_consumption.py:265`
> `test_every_selector_matches_a_class_the_html_emits`, parameterised by layout.
>
> **Remaining:**
> 1. **`title_color` and `heading_font_size` never reach the figure title.** They
>    are read only by `css_block()`. Measured on `s2color`, which declares
>    `title_color='#1e2d53'` and `heading_font_size='14pt'`, while the rendered
>    figure title carries Bokeh's defaults `text_color='#444444'`,
>    `text_font_size='13px'`.
> 2. **`note_font_size` has zero consumers.** Parsed at `dash_render.py:2047`
>    (`self.note_font_size = self._gsize("gsize note", "9pt")`), but the note
>    annotation at `:9867` hardcodes `{"size": 11.0, "color": "#555555"}`. The
>    colour is a hardcoded literal too, and belongs in the same fix.

Item 1 of that list is Phase 23's. Item 2 is where this phase starts — and the
adversarial pass then showed that the prescribed fix (wire `note_font_size`) is
**wrong**, which is work item 6 below.

### The backlog arithmetic for this task

> | task | Appendix B | Appendix C | total |
> |---|---:|---:|---|
> | 11-04 Scheme keys and dead CSS | 15 | 17 | **32** |

### The literals, at HEAD

`DashRenderer._make_figure_body`, `dash_render.py:9866-9869` — the note and caption
defaults, confirmed in source:

```python
        _TEXTBOX_DEFAULTS = {
            "note":     {"size": 11.0, "color": "#555555", "y": 2.0},
            "caption":  {"size": 12.0, "color": "#555555", "y": -12.0},
        }
```

The comment two lines above records why the geometry is what it is — *"Measured in
Stata: the note is ring(4) and the caption ring(5), i.e. the caption sits BELOW the note,
and the note is the smaller of the two."* The geometry was measured. The **sizes and
colours were not**; they are four literals.

`dash_render.py:9893-9896` — the graph-level subtitle Label:

```python
                text_font_size=f"{_textbox_size(subtitle_opts, 13.0):g}px",
                text_color=_textbox_color(subtitle_opts, "#444444"),
```

`ServerAppBuilder` carries its own emitted copy of both. `dash_render.py:13931-13934`:

```python
            "        _TEXTBOX_DEFAULTS = {",
            "            'note':    {'size': 11.0, 'color': '#555555', 'y': 2.0},",
            "            'caption': {'size': 12.0, 'color': '#555555', 'y': -12.0},",
            "        }",
```

and `dash_render.py:13952-13953`:

```python
            "            fig.add_layout(_Label(x=0, y=0, x_units='screen', y_units='screen',",
            "                text=html.escape(_sub_txt), text_font_size='13px', text_color='#444444'), 'above')",
```

So six literals in two renderers, for three annotations, on every scheme.

### Why two of them cannot be fixed in `dash_render.py` alone

Copied from Appendix C, 11-04:

> **[func · both · S]** `gsize note` is a DEAD key at Stata scheme level —
> exactly the trap this file already documented for `draw_major_grid`. No
> style file reads `scheme note`; the note textbox is textboxstyle-body, which
> reads `gsize body` / `color body`. Wiring SchemeParser.note_font_size (from
> `gsize note`) to the note Label, as the remaining item prescribes, would
> draw economist's note at 14pt where Stata draws ~8.6pt. Parse `gsize body`
> (and `color body`) instead, and add those keys back to the 14 translated
> .scheme files, which dropped them on purpose.

> **[func · both · S]** The graph-level subtitle clause cannot be closed
> inside dash_render.py at all: Stata's subtitle is textboxstyle-subheading,
> which reads `gsize subheading` and `color subheading`, and SchemeParser
> parses NEITHER — and the 14 translated .scheme files deliberately dropped
> both.

Confirmed at HEAD. `SchemeParser._init_properties`, `dash_render.py:2043-2047`:

```python
        self.text_font_size: str = self._gsize("gsize text", "10pt")
        self.heading_font_size: str = self._gsize("gsize heading", "13pt")
        self.axis_title_font_size: str = self._gsize("gsize axis_title", "10pt")
        self.tick_label_font_size: str = self._gsize("gsize tick_label", "10pt")
        self.note_font_size: str = self._gsize("gsize note", "9pt")
```

No `subheading`, no `body`. On the scheme-file side, a sweep of `schemes/`:

| key | files carrying it (of 14) |
|---|---:|
| `gsize note` | **14** |
| `gsize text` | **14** |
| `gsize body` | **0** (the single grep hit is a *comment* — `schemes/economist.scheme:247`) |
| `gsize subheading` | **0** (same comment) |
| `color subheading` | 0 |

And the comment itself, `schemes/economist.scheme:243-247`, states the intent plainly:

```
* Keys carried by the earlier approximation and dropped here because
* SchemeParser._init_properties() reads none of them, and inventing dash
* vocabulary is what this translation exists to stop:
*   color foreground, color grid (economist's grid colour is recorded above
*   under the key dash actually reads, "color major_grid"), linewidth
*   minor_grid, gsize subheading, gsize body.
```

That is the whole shape of the problem: the keys were dropped *because the parser did not
read them*, and the parser does not read them *because the schemes do not carry them*.
Breaking that loop is S03-shaped work, and it must happen before any renderer edit is
anything but invented.

The magnitude of the `gsize note` trap is measurable from the declared values and the
parser's own table (`SchemeParser._GSIZE_PT`, `dash_render.py:1638-1655`):

| scheme | declares | `_GSIZE_PT` → | what Stata draws (textboxstyle-body) |
|---|---|---|---|
| `economist` | `gsize note large` | **14pt** | ~8.6pt |
| the other 13 | `gsize note small` | 8pt | ~8.6pt |

Wiring `note_font_size` as Appendix A prescribes would therefore make `economist`'s note
*63% too large* and call it fidelity.

### Why the CSS never lands

`css_block()` at `dash_render.py:2213-2220` emits four rules:

```python
        return (
            f"  body {{ background-color: {bg}; }}\n"
            f"  .db-title {{ color: {tc}; font-size: {hs}; }}\n"
            f"  .db-subtitle {{ color: {tc}; font-size: {ts}; }}\n"
            f"  .db-kpi-card {{ background-color: {lbg}; "
            f"border-color: {lbc}; }}\n"
        )
```

`DashRenderer` calls it twice — the Bootstrap layout splices it into a `<style>` alongside
`_DASH_GRID_CSS` (`dash_render.py:10892-10902`) and the non-Bootstrap path replaces
`<head>` with `css_style_element()` (`dash_render.py:12132-12141`). `ServerAppBuilder`
calls it **zero** times. Appendix C:

> **[func · server · M]** css_block() is never called in `dash serve`: the
> generated app carries a verbatim copy of SchemeParser (css_block included)
> but no call site, and emits no `.db-title`/`.db-subtitle` markup, so the
> served dashboard chrome ignores the scheme entirely. Wire the scheme CSS
> into the server app's template (Bokeh `curdoc().template` / the Div that
> builds the header) the way DashRenderer does at 10899-10900 and 12136-12140.
> Headline-only in the auditor's report; not in REMAINING.md.

The served header, `dash_render.py:15929-15936`, is unclassed inline-styled markup:

```python
            '        if title_text:',
            '            _head += f\'<h2 style="font-family:sans-serif;margin-bottom:2px;">{title_text}</h2>\'',
            '        if subtitle_text:',
            '            _head += (f\'<div style="font-family:sans-serif;font-size:14px;\'',
            '                      f\'color:#666;margin-top:0;">{subtitle_text}</div>\')',
```

`font-size:14px; color:#666` — a literal, on every scheme, in the one place the dashboard
tells the user what it is. So `title_color`, `heading_font_size`, `text_font_size`,
`legend_bg_color` and `legend_border_color` are all inert in server mode.

And in standalone mode the class-name fix that Appendix A recorded as landed still does
not reach pixels in the auto layout:

> **[func · standalone · M]** In the auto layout the .db-title / .db-subtitle
> / .db-kpi-card markup is emitted INSIDE Bokeh Div models, which Bokeh 3
> renders in a shadow root, so the document-level scheme rules cannot match
> them. The class-name fix the task landed therefore still has no effect on
> the auto-layout header or on KPI cards in EITHER layout — only `body {
> background-color }` (light DOM) works.

Confirmed: `dash_render.py:12105-12122` builds the header as `Div(text='<h2
class="db-title" ...>')` / `Div(text='<p class="db-subtitle" ...>')`, and
`_build_kpi_html` at `dash_render.py:10486-10496` returns
`Div(text=...'<div class="db-kpi-card" style="background:{bgcolor}; ...">'...)`. The
classes are right. The rules cannot cross the shadow boundary to reach them.

This is exactly the failure mode the task's own test was meant to stop, and the test
cannot see it: `test_every_selector_matches_a_class_the_html_emits`
(`test/test_scheme_consumption.py:264-292`) compares *selector strings against class
strings in the HTML source*. Both sides of that comparison are correct today. The pixels
are not.

### And the colour bar has no chrome at all

> **[func · standalone · S]** The continuous colorvar() ColorBar takes no
> scheme chrome at all. Only its palette was considered; its background,
> border, tick-label size/colour and title size/colour are Bokeh defaults, so
> an economist or s2color dashboard draws a white colour bar with #444444 13px
> text over a themed plot region. Stata styles this through
> clegendstyle-default.style / textboxstyle-clegend.

`GlyphMapper._apply_colorvar`, `dash_render.py:3265-3272`, confirmed:

```python
            try:
                fig.add_layout(
                    ColorBar(color_mapper=mapper, label_standoff=8,
                             width=12, location=(0, 0),
                             title=html.escape(var_display)),
                    "right",
                )
```

Eight constructor arguments, none of them a scheme value.

### And the guard is a third of a guard

> **[deli · both · S]** The section's TDD stub for text sizes is only
> one-third delivered and only on one renderer: axis-title and tick-label
> sizes are asserted once, against DashRenderer, and nothing asserts them
> against the server's emitted `_dash_apply_scheme`; nothing at all asserts
> title, subtitle, note or caption sizes.

Confirmed: `test/test_scheme.py:291-296` is `test_sets_axis_label_font_size`, which drives
`SchemeParser.apply_to_figure` directly; `test/test_server_scheme.py` has
`TestSchemeColour`, `TestSchemeChrome` (plot-region colour and grid on/off),
`TestPrecedenceIsSharedWithStandalone` and `TestSchemeMarkersAndDashes` — and **no
font-size arm at all**. The only 11-04 size check in
`test/test_scheme_consumption.py` is the source-count proxy at `:462-476`:

```python
    @pytest.mark.parametrize("attr", [
        "fill_alpha", "bar_alpha", "area_alpha", "minor_grid_color",
        "text_font_size", "title_color", "heading_font_size",
    ])
    def test_the_key_is_read_somewhere(self, attr):
        ...
        assert code.count(f".{attr}") >= 2, (
            f"scheme.{attr} is parsed and never read"
        )
```

Seven names of thirty-four, counted in the *source text*, never read back off a model.

---

## Epics

| Epic | Goal (one line) | Items |
|---|---|---|
| **E24.1 — The textbox vocabulary** | Give the subtitle, note and caption a real, Stata-sourced scheme key in both renderers, adding the keys to the parser and to all 14 `.scheme` files first. | 1, 6, 7, 8 |
| **E24.2 — Delivering the CSS where it is actually rendered** | Make `css_block()`'s values reach pixels in `dash serve` and inside Bokeh 3's shadow DOM, not just match a class name in a string comparison. | 2, 3, 4 |
| **E24.3 — Colour-bar chrome and the six-name guard** | Chrome the continuous `ColorBar` from the scheme, and replace the source-count proxy with a rendered-model assertion over all six text names, per renderer. | 5, 9 |

---

## User stories

### E24.1 — The textbox vocabulary

> **As a Stata user pasting a `twoway` command**, I want `note()`, `caption()` and
> `subtitle()` to be drawn at my scheme's sizes and colours, so that the dashboard's
> annotations look like the graph Stata would have drawn from the same command.

- **Given** `set scheme economist` and a command carrying `note("Source: FRED")`,
  **when** I run `dash build`, **then** the note Label's `text_font_size` equals the size
  `economist.scheme` declares under `gsize body` (≈8.6pt, i.e. the `textboxstyle-body`
  size), **and not** `11px`, **and not** the 14pt that `gsize note large` would have given.
- **Given** the same command, **when** I compare the standalone HTML and the
  `dash serve` app, **then** the note, caption and subtitle carry identical sizes and
  colours in both.
- **Given** `subtitle("Q3", size(large) color(navy))`, **when** I render,
  **then** the explicit sub-options still win over the scheme default — the scheme
  supplies the *default* argument to `_textbox_size` / `_textbox_color`, it does not
  replace the parsed override.
- **Given** any of the 14 translated schemes, **when** `SchemeParser` loads it,
  **then** `subheading_font_size`, `subheading_color`, `body_font_size` and `body_color`
  all resolve from a key the file actually carries, with no fallback warning raised.

> **As a package maintainer**, I want a scheme key that Stata itself never reads to be
> *removed or documented as inert* rather than wired, so that we do not ship a fidelity
> claim we cannot substantiate.

- **Given** `gsize note`, which all 14 files carry and no Stata style file reads,
  **when** the disposition lands, **then** either `note_font_size` is retired from
  `_init_properties` or it is annotated in-code and in the CHANGELOG as parsed-and-inert
  with the reason, **and** the note's size comes from `gsize body`.
- **Given** `schemes/economist.scheme:243-247`, which records `gsize subheading` and
  `gsize body` as deliberately dropped, **when** those keys are added back,
  **then** that comment is corrected in the same commit so the file does not contradict
  itself.

### E24.2 — Delivering the CSS where it is actually rendered

> **As a `dash serve` operator**, I want the served dashboard's title and subtitle to
> carry my scheme's colour and sizes, so that the served view and the exported HTML of the
> same spec are the same dashboard.

- **Given** `dash serve, scheme(s2color)` with a dashboard title, **when** the document
  is built, **then** the header markup carries `class="db-title"` / `class="db-subtitle"`
  rather than `style="font-family:sans-serif;font-size:14px;color:#666"`, **and** the
  document delivers `SchemeParser.css_block()` so those classes resolve to
  `title_color` (`#1e2d53` on `s2color`) and `heading_font_size` (`14pt`).
- **Given** the same app, **when** I inspect the served page's body background,
  **then** it is the scheme's `background_color`, as in standalone.

> **As a dashboard viewer**, I want the header and KPI cards to look themed, so that the
> dashboard reads as one design rather than a themed plot area inside default chrome.

- **Given** `layout(auto)` and `scheme(economist)`, **when** the page renders in a
  browser, **then** the `db-title` Div's computed colour is the scheme's `title_color` —
  achieved by attaching the scheme CSS to the Div
  (`stylesheets=[InlineStyleSheet(css=...)]`) or by folding the values into the inline
  style, because a document-level rule cannot reach into Bokeh 3's shadow root.
- **Given** a spec with a KPI card in either layout, **when** it renders, **then** the
  card's background and border come from `legend_bg_color` / `legend_border_color`.

### E24.3 — Colour-bar chrome and the six-name guard

> **As a Stata user pasting a `twoway` command with `colorvar()`**, I want the continuous
> colour bar to be part of the themed graph, so that a dark or tinted scheme does not draw
> a white bar with default-grey text over a themed plot region.

- **Given** `scatter mpg weight, colorvar(length)` under `economist`, **when** the figure
  renders, **then** the `ColorBar`'s `background_fill_color` is the scheme's
  `plotregion_color`, its `major_label_text_font_size` is `tick_label_font_size`, and its
  `title_text_font_size` / `title_text_color` are `text_font_size` / `title_color`.

> **As a package maintainer**, I want all six scheme-driven text names asserted against a
> rendered model in both renderers, so that the clause has a guard instead of a
> `code.count(".attr") >= 2` proxy.

- **Given** a rendered `DashRenderer` figure and an executed `ServerAppBuilder` document
  for the same spec, **when** the size guard runs, **then** it asserts title, subtitle,
  axis-title, tick-label, note and caption sizes against the scheme, in both, and fails
  if any one of the twelve assertions is reverted to a literal.

---

## Business requirements

| ID | Requirement | How it is testable |
|---|---|---|
| **BR-24.1** | Every graph-level textbox `dash` draws — title, subtitle, axis title, tick label, note, caption — takes its size and colour from the active scheme when the user passes no sub-option. | Rendered-model assertion per name per renderer (item 9). |
| **BR-24.2** | A scheme value used by `dash` must correspond to a key Stata itself reads for that element. No key is wired on the strength of its *name*. | `gsize note` is not the note's source; `gsize body` is. Reviewed against Stata's `textboxstyle-body` / `textboxstyle-subheading` / `clegendstyle-default`. |
| **BR-24.3** | An explicit Stata sub-option always overrides the scheme default, in both renderers. | `subtitle("x", size(large))`, `note("x", size(vsmall))`, `caption("x", color(red))` each beat the scheme. |
| **BR-24.4** | Standalone and server render the same textbox sizes and colours for the same spec and scheme. | Parity assertion over the six names, both renderers, same spec. |
| **BR-24.5** | The scheme's dashboard chrome (title colour, heading and text size, card background and border, page background) is visible in `dash serve`, not only in the exported HTML. | Server-mode document assertion: classed markup present **and** the CSS delivered. |
| **BR-24.6** | The scheme's dashboard chrome is visible in the `layout(auto)` header and on KPI cards in **both** layouts — i.e. it survives Bokeh 3's shadow DOM. | A check that does not rely on string matching of class names alone (rendered-DOM arm, or `stylesheets=`/inline-value assertion). |
| **BR-24.7** | A continuous `colorvar()` colour bar is chromed by the scheme. | `ColorBar` model attributes read back after render. |
| **BR-24.8** | All 14 translated schemes carry the keys the renderer now reads, with values taken from Stata's style files — not invented, not interpolated. | Sweep test over `schemes/*.scheme`: every key `_init_properties` reads is present in every file, or its documented default is explicitly justified. |
| **BR-24.9** | Any scheme key that remains parsed but unread is documented as such, in code and in the CHANGELOG, with the reason. | `gsize note` disposition recorded; no silent dead key. |

---

## Technical requirements

### E24.1 — The textbox vocabulary (items 1, 6, 7, 8)

- **TR-24.1** Add four attributes to `SchemeParser._init_properties`, in the font-size
  block at `dash_render.py:2043-2047` and the colour block above it:
  `subheading_font_size = self._gsize("gsize subheading", <default>)`,
  `subheading_color = self._color("color subheading", <default>)`,
  `body_font_size = self._gsize("gsize body", <default>)`,
  `body_color = self._color("color body", <default>)`.
  Defaults must be the Stata-measured fallbacks, not the current literals: the note is
  drawn by `textboxstyle-body`, so the pre-existing `#555555` / 11.0px pair is the
  *legacy* value, not the *correct* one.
- **TR-24.2** Add `gsize subheading`, `color subheading`, `gsize body` and `color body`
  to **all 14** files in `schemes/` (`economist`, `s1color`, `s1mono`, `s1rcolor`,
  `s2color`, `s2gcolor`, `s2mono`, `sj`, `stcolor`, `stcolor_alt`, `stgcolor`,
  `stmono1`, `stmono2`, `stsj`), with values read out of Stata's own style files.
  Correct `schemes/economist.scheme:243-247`, which currently records these keys as
  deliberately dropped — that comment becomes false the moment the keys land.
- **TR-24.3** Standalone note/caption: change the two defaults in `_TEXTBOX_DEFAULTS`
  (`dash_render.py:9866-9869`) from `{"size": 11.0, "color": "#555555"}` and
  `{"size": 12.0, "color": "#555555"}` to the scheme's `body_font_size` / `body_color`.
  The `y` geometry (`2.0` for the note, `-12.0` for the caption) is **measured** — note
  is `ring(4)`, caption `ring(5)` — and must not change. `_gsize` returns a `pt` string
  (`"8pt"`), while the Label consumer formats a float as px
  (`f"{_textbox_size(ann_opts, d['size']):g}px"`), so the conversion point must be
  explicit and shared, not duplicated per call site.
- **TR-24.4** Standalone subtitle: replace the `13.0` and `"#444444"` default arguments
  at `dash_render.py:9893-9896` with `subheading_font_size` / `subheading_color`. The
  override branch is untouched: `_textbox_size(subtitle_opts, default)` and
  `_textbox_color(subtitle_opts, default)` already give the explicit sub-option
  precedence, so only the *default argument* changes — this is what keeps BR-24.3 true
  for free.
- **TR-24.5** Server: the emitted app reads its scheme through the `_SCHEME_CHROME`
  literal that `ServerAppBuilder` writes at `dash_render.py:12609-12624`. That dict today
  carries `plotregion_color`, `background_color`, `axis_line_color`, `grid_color`,
  `grid_line_width`, `minor_grid_color`, `draw_major_hgrid`, `draw_major_vgrid`,
  `axis_title_font_size`, `tick_label_font_size`, `legend_bg_color`,
  `legend_border_color`, `legend_position`, `legend_cols` — and **no** text/title/note/
  caption/subtitle entry. Add `body_font_size`, `body_color`, `subheading_font_size`,
  `subheading_color` (plus `text_font_size`, `title_color`, `heading_font_size` if
  Phase 23 has not already), then read them in the emitted `_TEXTBOX_DEFAULTS`
  (`dash_render.py:13931-13934`) and the emitted subtitle Label
  (`dash_render.py:13952-13953`) in place of `'11.0'`/`'12.0'`/`'#555555'`/`'13px'`/
  `'#444444'`.
- **TR-24.6** Disposition for `note_font_size` (`dash_render.py:2047`,
  `self.note_font_size = self._gsize("gsize note", "9pt")`): it is **not** the note's
  source. Either retire the attribute or keep it with an in-code comment naming
  `textboxstyle-body` as the real source, and record the decision in
  `.ultraplan/CHANGELOG.md`. This directly contradicts the Appendix A prescription and
  Phase 23's item 3 — see Risks.
- **TR-24.7** Do not change `html.escape(_sub_txt)` at `dash_render.py:13953`. Escaping
  canvas text is a live defect in the same statement (the standalone renderer's own
  comment at `:13927-13929` records the symptom — *"a note reading `R&D' came out
  `R&amp;D'"*), but it is **Phase 26** (Text fidelity I — canvas escaping) territory.
  Touch the two style arguments only, and do not propagate the escape into any new code
  path this phase adds.

### E24.2 — CSS delivery (items 2, 3, 4)

- **TR-24.8** Server markup: in the emitted header block at
  `dash_render.py:15929-15936`, replace the inline-styled `<h2 style="font-family:
  sans-serif;margin-bottom:2px;">` and `<div style="font-family:sans-serif;font-size:
  14px;color:#666;margin-top:0;">` with `class="db-title"` / `class="db-subtitle"`
  markup, matching the classes `css_block()` styles at `dash_render.py:2215-2217`.
- **TR-24.9** Server delivery: add a `css_block()` call site to the generated app. The
  class source is already present verbatim — `ServerAppBuilder` at
  `dash_render.py:12265+` emits the whole `SchemeParser`, `css_block()` included, and
  never calls it. Two mechanisms are acceptable, and the choice must be recorded:
  (a) a Bokeh document template (`curdoc().template`) carrying
  `<style>{css_block()}</style>`, mirroring `DashRenderer`'s splice at
  `dash_render.py:10892-10902`; or (b) `InlineStyleSheet` on the header `Div`. Note that
  (b) alone does **not** satisfy `body { background-color: … }`, which needs a light-DOM
  home — so a server-side document template is the safer primary.
- **TR-24.10** Shadow DOM, standalone: the auto-layout header `Div`s at
  `dash_render.py:12105-12122` and the KPI `Div` at `dash_render.py:10486-10496` must
  either carry `stylesheets=[InlineStyleSheet(css=self.scheme.css_block())]` or fold the
  scheme values into the inline `style` they already write. Bokeh 3 renders `Div` content
  in a shadow root, so the document-level rules at `dash_render.py:2215-2219` cannot match
  them; today only the light-DOM `body { background-color }` rule works.
- **TR-24.11** KPI interaction: the KPI markup writes
  `style="background:{bgcolor}; … border:1px solid #dee2e6;"` at
  `dash_render.py:10487-10490`. An inline declaration beats a stylesheet rule, so
  `.db-kpi-card { background-color; border-color }` is overridden even once the shadow
  boundary is crossed. Phase 25 owns the inline-vs-rule decision (its items 4 and 10);
  this phase must not land a `stylesheets=` change that makes the Phase 25 item look
  fixed while the inline style still wins. Coordinate or sequence — see Risks.
- **TR-24.12** Both delivery changes must preserve the invariants the existing guard
  already holds: `<style>` elements stay balanced and unnested
  (`test_the_style_elements_are_balanced_and_not_nested`,
  `test/test_scheme_consumption.py:244-262`), and `css_block()` continues to return a bare
  block with `css_style_element()` supplying the wrapper — the non-Bootstrap path at
  `dash_render.py:12136-12140` depends on that split.

### E24.3 — Colour bar and the guard (items 5, 9)

- **TR-24.13** `GlyphMapper._apply_colorvar`, `dash_render.py:3265-3272`: add to the
  `ColorBar(...)` constructor `background_fill_color=` the scheme's `plotregion_color`
  (falling back to `background_color`), `major_label_text_font_size=` `tick_label_font_size`,
  `title_text_font_size=` `text_font_size`, `title_text_color=` `title_color`. Keep the
  existing `except (ValueError, TypeError, KeyError)` → `warnings.warn("dash: color bar
  skipped — …")` path; new keyword arguments must not turn a skipped colour bar into a
  raised exception. Stata's source for this chrome is
  `clegendstyle-default.style` / `textboxstyle-clegend`.
- **TR-24.14** The `ColorBar` placement (`"right"`, hardcoded at `:3272`) is **Phase 25's**
  item 1, not this phase's. Add chrome at the same call site without changing the panel.
- **TR-24.15** The size guard asserts **six names × two renderers = twelve** facts,
  against models, not source text:
  standalone via `DashRenderer` (`fig.title.text_font_size`, the subtitle `Label`, the
  note `Label`, the caption `Label`, `fig.xaxis.axis_label_text_font_size`,
  `fig.xaxis.major_label_text_font_size`); server via an executed
  `ServerAppBuilder` document (`_dash_apply_scheme`, emitted at
  `dash_render.py:12669-12690`, supplies the axis and tick sizes; the emitted
  `_TEXTBOX_DEFAULTS` and subtitle Label supply the rest).
- **TR-24.16** The guard must not be built on the existing `code.count(f".{attr}") >= 2`
  heuristic at `test/test_scheme_consumption.py:462-476`. `REMAINING.md` records why —
  Appendix C, 11-04: *"Enumerating `_init_properties` while keeping that heuristic
  produces four false failures (graphsize_x, graphsize_y, legend_position, legend_cols are
  all read, via `getattr(self.scheme, "name")` and via `_SCHEME_CHROME[...]` dict keys)."*
  The generalised replacement is Phase 23's item 8 and Phase 25's item 2; this phase's
  item 9 supplies the **behavioural** arm those two depend on.

---

## Work items

Every item below is reproduced from the phase assignment, numbered exactly as given.
Tags are `[kind · renderer · effort]`.

---

**1. `[functional · both · small]` — Give the per-figure subtitle annotation a real scheme
value instead of the hardcoded 13.0px / #444444 default.**

(The DASHBOARD subtitle is already scheme-driven through `.db-subtitle` in `css_block`;
this is the graph-level `subtitle()` Label.)

*Where:* `dash_render.py:9893-9896` (`text_font_size=f"{_textbox_size(subtitle_opts,
13.0):g}px"`, `text_color=_textbox_color(subtitle_opts, "#444444")`); server at
`dash_render.py:13953` (`text_font_size='13px', text_color='#444444'`).

*Evidence:* Appendix B, 11-04. The task's `<action>` says *"the subtitle uses a real scheme
value"*. Both renderers draw it from a literal. Confirmed at HEAD; the server line also
shows `html.escape(_sub_txt)` (Phase 26's, per TR-24.7). **Blocked on item 7** — there is
no key to read until `subheading` is parsed and declared.

---

**2. `[functional · server · medium]` — Make `css_block()` reach the served dashboard.**

The generated `bokeh serve` app carries the whole `SchemeParser` class source (so
`css_block` is DEFINED there) but never calls it, and its dashboard title/subtitle are
unclassed inline-styled markup, so `title_color`, `heading_font_size`, `text_font_size`,
`legend_bg_color` and `legend_border_color` are all inert in server mode.

*Where:* `dash_render.py:15929-15936` (the emitted `_head += f'<h2
style="font-family:sans-serif;margin-bottom:2px;">…'` / `<div
style="font-family:sans-serif;font-size:14px;color:#666;…">` block in `ServerAppBuilder`)
— needs the `db-title`/`db-subtitle` classes plus a `Document.add_root`/template hook that
emits `self.scheme.css_block()`.

*Evidence:* Appendix B, 11-04. Confirmed at HEAD: the emitted block writes
`font-size:14px; color:#666` unconditionally, and `grep` finds no `css_block` call inside
`ServerAppBuilder`.

---

**3. `[functional · server · medium]` — `css_block()` is never called in `dash serve`.**

The generated app carries a verbatim copy of `SchemeParser` (`css_block` included) but no
call site, and emits no `.db-title`/`.db-subtitle` markup, so the served dashboard chrome
ignores the scheme entirely. Wire the scheme CSS into the server app's template (Bokeh
`curdoc().template` / the Div that builds the header) the way `DashRenderer` does at
`10899-10900` and `12136-12140`. Headline-only in the auditor's report; not in
`REMAINING.md`.

*Where:* `dash_render.py:12265+` (`ServerAppBuilder` — no `css_block` call), compare
`dash_render.py:10892-10902` and `12132-12141`.

*Evidence:* Appendix C, 11-04. This is the adversarial pass's independent statement of
item 2's gap, and it adds two things item 2 does not carry: the explicit standalone call
sites to mirror (`10892-10902` splices `_DASH_GRID_CSS + css_block()` into a `<style>`;
`12132-12141` replaces `<head>` with `css_style_element()`), and the fact that the gap was
headline-only in the auditor's report. Land items 2 and 3 as one change; keep both
numbers in the commit body so the audit trail closes on both.

---

**4. `[functional · standalone · medium]` — In the auto layout the `.db-title` /
`.db-subtitle` / `.db-kpi-card` markup is emitted INSIDE Bokeh Div models, which Bokeh 3
renders in a shadow root, so the document-level scheme rules cannot match them.**

The class-name fix the task landed therefore still has no effect on the auto-layout header
or on KPI cards in EITHER layout — only `body { background-color }` (light DOM) works. Fix
by attaching the scheme CSS to those Divs
(`stylesheets=[InlineStyleSheet(css=self.scheme.css_block())]`) or by folding the scheme
values into the inline style the Div already carries.

*Where:* `dash_render.py:12105-12122` (the two `Div(text='<h2 class="db-title" …>')` /
`Div(text='<p class="db-subtitle" …>')` header items in `DashRenderer._assemble_layout`'s
auto branch); `dash_render.py:10486-10490` (`_build_kpi_html`, the `<div
class="db-kpi-card" …>` that becomes a Div in both layouts); `dash_render.py:2214-2220`
(`css_block`).

*Evidence:* Appendix C, 11-04. Confirmed at HEAD in all three places. This is why
`test_every_selector_matches_a_class_the_html_emits` passes on a dashboard whose header is
unstyled: the test compares strings, and both strings are correct.

---

**5. `[functional · standalone · small]` — The continuous `colorvar()` ColorBar takes no
scheme chrome at all.**

Only its palette was considered; its background, border, tick-label size/colour and title
size/colour are Bokeh defaults, so an economist or s2color dashboard draws a white colour
bar with `#444444` 13px text over a themed plot region. Stata styles this through
`clegendstyle-default.style` / `textboxstyle-clegend`. Set `background_fill_color` from
`plotregion_color` (or `background_color`), `major_label_text_font_size` from
`tick_label_font_size`, and `title_text_font_size`/`title_text_color` from
`text_font_size`/`title_color`, in the same place the ColorBar is built.

*Where:* `dash_render.py:3266-3272` (`GlyphMapper._apply_colorvar`,
`fig.add_layout(ColorBar(color_mapper=mapper, label_standoff=8, width=12, location=(0,0),
title=html.escape(var_display)), "right")`).

*Evidence:* Appendix C, 11-04. Confirmed verbatim at HEAD.

---

**6. `[functional · both · small]` — `gsize note` is a DEAD key at Stata scheme level** —
exactly the trap this file already documented for `draw_major_grid`.

No style file reads `scheme note`; the note textbox is `textboxstyle-body`, which reads
`gsize body` / `color body`. Wiring `SchemeParser.note_font_size` (from `gsize note`) to
the note Label, as the remaining item prescribes, would draw economist's note at 14pt where
Stata draws ~8.6pt. Parse `gsize body` (and `color body`) instead, and add those keys back
to the 14 translated `.scheme` files, which dropped them on purpose.

*Where:* `dash_render.py:2047` (`self.note_font_size = self._gsize("gsize note", "9pt")`);
`schemes/*.scheme` (all 14 carry `gsize note`, none carries `gsize body`);
`dash_render.py:9867` and `:13932` (the `_TEXTBOX_DEFAULTS` note entry in each renderer).

*Evidence:* Appendix C, 11-04. Confirmed: 14/14 files carry `gsize note`
(`economist` = `large`, the other 13 = `small`); 0/14 carry `gsize body`; `_GSIZE_PT`
(`dash_render.py:1638-1655`) maps `large → "14pt"`, `small → "8pt"`. **This item
overrides Appendix A's own remaining-item 2 and Phase 23's item 3.**

---

**7. `[functional · both · small]` — The graph-level subtitle clause cannot be closed
inside `dash_render.py` at all.**

Stata's subtitle is `textboxstyle-subheading`, which reads `gsize subheading` and `color
subheading`, and `SchemeParser` parses NEITHER — and the 14 translated `.scheme` files
deliberately dropped both. So the remaining item "give the subtitle a real scheme value"
needs S03-shaped work first (add the keys to `schemes/*.scheme`, add
`subheading_font_size` / `subheading_color` to `_init_properties`) before any renderer edit
can be correct rather than invented.

*Where:* `dash_render.py:2040-2048` (`SchemeParser._init_properties` font-size block — no
`subheading` attribute); `schemes/*.scheme` (all 14); `dash_render.py:9893-9896` and
`:13952-13953` (the subtitle Label in each renderer).

*Evidence:* Appendix C, 11-04. Confirmed: the font-size block at `:2043-2047` parses
`text`, `heading`, `axis_title`, `tick_label`, `note` and nothing else;
`grep subheading schemes/` returns one hit and it is the comment at
`schemes/economist.scheme:247` recording the drop. **This item gates item 1.**

---

**8. `[functional · both · small]` — The section's TDD stub names CAPTION explicitly and
the caption is untouched.**

The stub reads *"title, subtitle, axis-title, tick-label, note and caption sizes come from
the scheme"*; both renderers draw the caption at a hardcoded 12.0px / `#555555` with no
scheme key parsed. Like the note, its Stata source is `gsize body` / `color body` via
`textboxstyle-body`.

*Where:* `dash_render.py:9866-9869` (`_TEXTBOX_DEFAULTS` in
`DashRenderer._make_figure_body`) and `dash_render.py:13931-13934` (the emitted copy in
`ServerAppBuilder`).

*Evidence:* Appendix C, 11-04, and `.ultraplan/sections/section-11-scheme-consumption.md:67`
(the stub itself). Confirmed verbatim at HEAD in both renderers. Shares its scheme key
with item 6, so the two land together.

---

**9. `[deliverable · both · small]` — The section's TDD stub for text sizes is only
one-third delivered and only on one renderer.**

Axis-title and tick-label sizes are asserted once, against `DashRenderer`, and nothing
asserts them against the server's emitted `_dash_apply_scheme`; nothing at all asserts
title, subtitle, note or caption sizes. Add a rendered-model test per renderer covering all
six names, so the clause has a guard rather than a source-count proxy.

*Where:* `test/test_scheme_consumption.py` (`TestNoParsedKeyIsDiscarded`, `:427-481` —
natural home), `test/test_server_scheme.py` (needs an axis/tick font-size arm),
`test/test_scheme.py:290-300`.

*Evidence:* Appendix C, 11-04. Confirmed: `test/test_scheme.py:291-296` is
`test_sets_axis_label_font_size` (the single axis-title assertion, driving
`apply_to_figure` directly); `test/test_server_scheme.py` has no font-size assertion in any
of its four classes; the only size check in `test_scheme_consumption.py` is the
`code.count(f".{attr}") >= 2` proxy at `:462-476`, parameterised over 7 of 34 names.

---

## Test plan

The suite is `pytest` for the Python renderers and `.cscript` certification scripts for the
Stata surface (run with `arch -arm64` from `test/`, via `test/run_all_cscripts.do`). Rule 4
(every function unit-tested) and rule 8 (every bug fix preceded by a regression test that
fails first) both bind. At HEAD the baseline is **3,498 passed / 37 skipped; 25/25
cscripts** — that is the number the phase must not regress.

### E24.1 — The textbox vocabulary (items 1, 6, 7, 8)

**Write first (must fail at HEAD).**

| Test | File | Fails at HEAD because |
|---|---|---|
| `test_the_note_size_comes_from_gsize_body` | `test/test_scheme_consumption.py` (`TestNoParsedKeyIsDiscarded`) | the note Label reads `11px` on every scheme |
| `test_the_caption_size_comes_from_gsize_body` | same | the caption Label reads `12px` on every scheme |
| `test_the_subtitle_size_and_colour_come_from_gsize_subheading` | same | the subtitle Label reads `13px` / `#444444` on every scheme |
| `test_gsize_note_is_not_the_notes_source` | `test/test_scheme_fidelity.py` | asserts the negative: under `economist` the note is **not** 14pt. Pins item 6's refutation so a future "helpful" wiring of `note_font_size` fails loudly |
| `test_every_scheme_declares_the_keys_the_parser_reads` | `test/test_scheme_fidelity.py` | 0 of 14 files carry `gsize body` / `gsize subheading` |
| server arms of the three size tests | `test/test_server_scheme.py` (new `TestSchemeTextBoxes`, built on the existing `_build_doc` helper at `:43-68` and `_figures` at `:71-96`) | `_SCHEME_CHROME` carries no textbox key and the emitted Labels are literals |

**Unit tests (rule 4).** In `test/test_scheme_coercion.py`, one direct test per new
accessor path: `_gsize("gsize subheading", …)` and `_gsize("gsize body", …)` on a file
that declares the key, on a file that does not (default path), and on a malformed value
(the silent-`#000000` failure path `test_scheme_coercion.py` already exists to pin, for
`_color("color body")` / `_color("color subheading")`). Assert the unresolvable-token
**warning** is raised and names the token and the scheme, per 11-01's rule.

**Integration / cscript.** `test/test_e2e_single.cscript` gains a `dash build,
scheme(economist)` case carrying `title() subtitle() note() caption()` and asserts the
rendered HTML contains the scheme's sizes; `test/test_e2e_serve.cscript` gains the same
spec through `dash serve` and asserts the generated app source carries the scheme values
rather than `11.0` / `12.0` / `'13px'`.

**Precedence (BR-24.3).** `test_an_explicit_subtitle_size_still_wins`,
`test_an_explicit_note_colour_still_wins` — both renderers. These must pass *before and
after*; they are the regression fence around the default-argument change.

**Non-vacuity by mutation.**

| Break this | Test that must die |
|---|---|
| revert `d["size"]` for `"note"` to the literal `11.0` | `test_the_note_size_comes_from_gsize_body` (both renderers) |
| point the note at `note_font_size` instead of `body_font_size` | `test_gsize_note_is_not_the_notes_source` (this is the *whole point* of that test) |
| delete `gsize body` from one `.scheme` file | `test_every_scheme_declares_the_keys_the_parser_reads` |
| swap the scheme default into the override slot (`_textbox_size(subtitle_opts, …)` → ignore `subtitle_opts`) | `test_an_explicit_subtitle_size_still_wins` |
| drop the four new keys from `_SCHEME_CHROME` | the `test_server_scheme.py` arms |

### E24.2 — CSS delivery (items 2, 3, 4)

**Write first (must fail at HEAD).**

| Test | File | Fails at HEAD because |
|---|---|---|
| `test_the_served_header_carries_the_scheme_classes` | `test/test_server_scheme.py` | the emitted header is `style="…font-size:14px;color:#666"` with no class |
| `test_the_served_document_delivers_the_scheme_css` | `test/test_server_scheme.py` | `css_block()` has no call site in `ServerAppBuilder`; assert the built document (or its template) contains the scheme's `title_color` and `heading_font_size` |
| `test_the_served_body_background_is_the_scheme_background` | `test/test_server_scheme.py` | no `body { background-color }` reaches the served page |
| `test_the_header_divs_carry_the_scheme_stylesheet` | `test/test_scheme_consumption.py` (`TestSchemeCssActuallyApplies`) | the auto-layout header `Div`s at `:12105-12122` have no `stylesheets=` and no scheme value in their inline style |
| `test_the_kpi_card_div_carries_the_scheme_stylesheet` | same | `_build_kpi_html` returns a `Div` with neither |

The `_render` helper at `test/test_scheme_consumption.py:60-90` already takes
`title=`, `subtitle=`, `kpis=` and `layout=`, so the standalone arms need no new
scaffolding; the server arms build on `_build_doc`.

**Guard the existing invariants.** `test_the_style_elements_are_balanced_and_not_nested`
(`:244-262`) and `test_every_selector_matches_a_class_the_html_emits` (`:264-292`) must
still pass, parameterised over both layouts. If the delivery change moves `css_block()`
into a `stylesheets=` entry, the selector test's premise changes — extend it rather than
weaken it.

**Non-vacuity by mutation.**

| Break this | Test that must die |
|---|---|
| remove `class="db-title"` from the emitted server header | `test_the_served_header_carries_the_scheme_classes` |
| delete the new `css_block()` call in the server template | `test_the_served_document_delivers_the_scheme_css` and `test_the_served_body_background_…` |
| drop `stylesheets=` from the header `Div` | `test_the_header_divs_carry_the_scheme_stylesheet` |
| wrap `css_block()` in a second `<style>` | `test_the_style_elements_are_balanced_and_not_nested` |

**Known limit, to state in the test docstring.** A `stylesheets=`/inline assertion is a
*proxy for* the rendered DOM, not the DOM itself. The full rendered-DOM arm is Phase 25's
item 13; this phase's tests must say so in the docstring rather than imply coverage they
do not have (rule 2).

### E24.3 — Colour bar and the six-name guard (items 5, 9)

**Write first (must fail at HEAD).**

| Test | File | Fails at HEAD because |
|---|---|---|
| `test_the_colorbar_takes_the_scheme_chrome` | `test/test_scheme_consumption.py` | the `ColorBar` at `:3266-3272` is constructed with five arguments, none of them a scheme value; assert `background_fill_color`, `major_label_text_font_size`, `title_text_font_size`, `title_text_color` off the model |
| `test_a_failing_colorbar_still_warns_and_does_not_raise` | same | regression fence on the `except (ValueError, TypeError, KeyError)` → `warnings.warn` path, so new kwargs cannot turn a skip into a crash |
| `test_all_six_text_sizes_come_from_the_scheme[standalone]` | `test/test_scheme_consumption.py` (`TestNoParsedKeyIsDiscarded`, `:427-481`) | four of the six names are literals |
| `test_all_six_text_sizes_come_from_the_scheme[server]` | `test/test_server_scheme.py` | nothing in that file asserts a font size at all |

The six-name guard is parameterised over `("title", "subtitle", "axis_title",
"tick_label", "note", "caption")` × `("standalone", "server")` — twelve assertions, each
read back off a Bokeh model, none read out of the source text.

**Non-vacuity by mutation.**

| Break this | Test that must die |
|---|---|
| revert any one of the six standalone consumers to its literal | exactly one parameterisation of the standalone guard (prove it is *one*, not all twelve — a guard that dies wholesale is testing the fixture, not the value) |
| revert the corresponding server consumer | exactly one parameterisation of the server guard |
| drop `background_fill_color` from the `ColorBar` | `test_the_colorbar_takes_the_scheme_chrome` |
| replace `warnings.warn` with `raise` in `_apply_colorvar` | `test_a_failing_colorbar_still_warns_and_does_not_raise` |

**What this guard deliberately does not do.** It does not replace the
`code.count(f".{attr}") >= 2` proxy at `:462-476`. That replacement is Phase 23's item 8
and Phase 25's item 2, and `REMAINING.md` records why it must not be a naive enumeration:
four keys (`graphsize_x`, `graphsize_y`, `legend_position`, `legend_cols`) are read by
**string**, not by attribute, and a mechanical attribute count reports them as dead. This
phase supplies the behavioural arm those two build on.

---

## Definition of done

A reviewer can tick every line below.

**Parser and schemes**
- [ ] `SchemeParser._init_properties` parses `gsize subheading`, `color subheading`,
      `gsize body`, `color body`, with defaults taken from Stata, not from the previous
      literals.
- [ ] All 14 files in `schemes/` declare the four new keys, with values sourced from
      Stata's style files and recorded as such in each file's provenance comment.
- [ ] `schemes/economist.scheme:243-247` no longer lists `gsize subheading` / `gsize body`
      as deliberately dropped.
- [ ] The `gsize note` / `note_font_size` disposition is landed **and** recorded in
      `.ultraplan/CHANGELOG.md`: either retired, or kept with an in-code comment naming
      `textboxstyle-body` as the real source.

**Renderers**
- [ ] Standalone note, caption and subtitle read `body_font_size` / `body_color` and
      `subheading_font_size` / `subheading_color` (`dash_render.py:9866-9869`, `:9893-9896`).
- [ ] The emitted server copies read the same values through `_SCHEME_CHROME`
      (`dash_render.py:12609-12624`, `:13931-13934`, `:13952-13953`).
- [ ] An explicit `size()` / `color()` sub-option still wins in both renderers.
- [ ] The note's `y=2.0` / caption's `y=-12.0` measured geometry is unchanged.
- [ ] The served header carries `db-title` / `db-subtitle` classes
      (`dash_render.py:15929-15936`).
- [ ] The served document delivers `css_block()`, including a light-DOM home for
      `body { background-color }`.
- [ ] The auto-layout header `Div`s and the KPI `Div` carry the scheme CSS across the
      shadow boundary (`stylesheets=` or folded inline values).
- [ ] The continuous `ColorBar` carries `background_fill_color`,
      `major_label_text_font_size`, `title_text_font_size` and `title_text_color` from the
      scheme; its panel is still `"right"` (Phase 25 owns placement).
- [ ] `html.escape(_sub_txt)` at `dash_render.py:13953` is untouched (Phase 26 owns it).

**Tests**
- [ ] Every test named in the test plan exists, and each was demonstrated to **fail before
      the fix and pass after** (rule 8).
- [ ] Every new `SchemeParser` accessor has a direct unit test, including its failure path
      (rule 4).
- [ ] Each mutation in the three mutation tables was applied, the named test died, and the
      mutation was reverted.
- [ ] The six-name × two-renderer guard is twelve independent parameterisations; breaking
      one consumer kills exactly one.
- [ ] `test_the_style_elements_are_balanced_and_not_nested` and
      `test_every_selector_matches_a_class_the_html_emits` still pass for both layouts.
- [ ] Full `pytest` green at or above the 3,498-passed baseline; 25/25 cscripts, with no
      new skips (a skip is not a pass).
- [ ] The tests' docstrings state honestly what they do **not** cover — specifically that
      a `stylesheets=` assertion is not a rendered-DOM check.

**Process**
- [ ] Pulled from local `main`, full suite run and green before commit (rule 5).
- [ ] Single-issue commits on `feature/batch4-interactive-layer`; the merge command into
      local `main` is provided, not run (rule 6).
- [ ] Commit messages describe the change only (rule 7).
- [ ] Items 1–9 are each referenced by number in a commit body, so the audit trail closes
      on all nine — including the pair 2/3, which land together.

---

## Risks and sequencing notes

**1. Item 6 contradicts Phase 23's item 3, and Appendix A's own prescription.** Phase 23
item 3 reads *"Make `scheme.note_font_size` the default size for the `note()`
annotation"*; item 6 here proves that would draw `economist`'s note at 14pt where Stata
draws ~8.6pt. These two cannot both land. **Resolution: item 6 wins, and the two phases
must agree before either touches `dash_render.py:9867`.** If Phase 23 lands first, this
phase's first act is to re-point the note at `body_font_size` and delete the wiring, with
the regression test `test_gsize_note_is_not_the_notes_source` in front of it. This is the
single highest-risk interaction in the phase; treat it as a hard coordination point, not a
merge conflict to resolve in the editor.

**2. `_gsize`'s numeric branch is wrong, and this phase adds two new `_gsize` callers.**
From `REMAINING.md`, Appendix B, 11-04:

> Stata's gsize values are relative sizes (`style/gsize-medium.style`: val 3.8194 = 11pt;
> `gsize-large.style`: val 4.8611 = 14pt, i.e. pt = val × 2.880), but `_gsize` returns
> `max(6, int(val*1.2))pt`. economist declares `gsize heading 6.0`, which is ~17pt in Stata
> and 7pt in dash.

Confirmed at `dash_render.py:1844-1853`. If any of the fourteen schemes declares
`gsize subheading` or `gsize body` **numerically** rather than as a keyword, this phase
inherits that bug on two new elements. Phase 23's item 6 fixes it. **Sequence Phase 23's
`_gsize` fix before TR-24.2's scheme-file edits**, or restrict the new declarations to
keywords and say so in the scheme files.

**3. Items 6 and 7 are S03 work landing late.** They edit all 14 translated `.scheme`
files, which are the artefact Phase 29 (S03 ground truth) and S11-06 (the by-eye Stata
comparison) both verify. Do not land a value that has not been read out of a Stata style
file; "inventing dash vocabulary is what this translation exists to stop" is the schemes'
own stated contract. Where a value genuinely cannot be sourced, record the gap in the file
rather than guessing (project rule 2).

**4. Item 4 and Phase 25's KPI items overlap on the same markup.** Phase 25 items 4 and 10
own the inline-`style`-beats-stylesheet problem on `.db-kpi-card`
(`dash_render.py:10487-10490`, `:7328-7334`, `:12976`). Attaching a stylesheet to the KPI
`Div` here without resolving the inline `background:` / `border:` shorthand would make the
selector test *look* satisfied while the scheme value still does nothing — the exact
failure mode this task already shipped once. **Either land item 4's KPI half together with
Phase 25's items 4/10, or scope item 4 to the header `Div`s only and hand the KPI `Div` to
Phase 25 explicitly in the commit body.**

**5. Item 5 shares a call site with Phase 25's item 1.** Both edit the
`fig.add_layout(ColorBar(...), "right")` statement at `dash_render.py:3266-3272` — this
phase adds chrome arguments, Phase 25 changes the panel from the hardcoded `"right"` to
`legend(position() ring())`. Small, but a guaranteed textual conflict. Land chrome first
(it is `small`); placement is `medium` and needs a plumbing change
(`_apply_colorvar` does not receive `graph_options`).

**6. Nothing in this phase is visible to a real user until Phase 03 lands.** From the
audit's first blocker: *"A real `net install` produces a package whose schemes are all
unreachable. Every scheme in the package — the whole of S03 and the first binding decision
— is inert as installed."* Stata routes `f schemes/economist.scheme` to `<dir>/e/…`, while
`SchemeParser` searches two paths relative to `dash_render.py`. A perfectly wired
`gsize body` on an unreachable scheme file changes nothing for an installed user. Say so in
the CHANGELOG entry rather than claiming a fidelity improvement the installed package does
not deliver.

**7. Do not build the new guard on an attribute count.** The `graphsize_x`/`graphsize_y`
refutation is the standing warning: they were listed as dead and are read by string
(`getattr(self.scheme, "graphsize_x", None)` at `dash_render.py:9244-9245`, feeding
`fig_kwargs["aspect_ratio"]`; measured on rendered figures as `stcolor` → 1.6667,
`economist` → 1.0, `s2color` → 1.375). An attribute-level count cannot see that, *"which
is the methodological trap — and the one Appendix A's own enumeration fell into before
being redone."* Item 9's guard reads values off rendered models for exactly this reason.

**8. Escaping is adjacent and must not be swept in.** `dash_render.py:13953` escapes
canvas text (`text=html.escape(_sub_txt)`), which the standalone renderer's own comment at
`:13927-13929` already identifies as wrong for a Bokeh `Label`. It sits in the literal this
phase replaces. Change the two style arguments; leave the escape to Phase 26, and note in
the commit body that it was seen and deliberately left.

**Suggested order within the phase:** 7 → 6 → 8 → 1 (E24.1, keys before consumers, note
and caption before subtitle since they share a key) → 9's standalone arm → 2 + 3 (one
change) → 4 (header `Div`s; KPI half per note 4) → 5 → 9's server arm.
