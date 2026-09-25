# Phase 23 — Scheme consumption I(a): text sizing and typography

**Purpose.** Task 11-04's `<action>` has a paragraph headed *"Text:"* — the scheme's
`text_font_size`, `title_color`, `heading_font_size` and `note_font_size` are supposed to
supply the **defaults** for marker labels, the figure title and the note, with S09's explicit
sub-options still winning on top. That paragraph did not land. Point labels are drawn at a
hardcoded `10px` in `GlyphMapper` and at a *different* hardcoded `9px` in eight hand-written
places in the emitted `bokeh serve` app; the figure `Title` is touched only when the user
passes `title()` sub-options, so on a plain `dash scatter mpg weight, scheme(s2color)` the
canvas title keeps Bokeh's `#444444` / `13px` while the scheme asks for `#1e2d53` / `14pt`;
the note is a hardcoded `11.0px` / `#555555` in both renderers and `note_font_size` has zero
consumers anywhere in the file. Underneath all of it sits a conversion bug: `SchemeParser._gsize`'s
numeric branch computes `max(6, int(val * 1.2))pt` where Stata's own style files make the
ratio `pt = val × 2.880`, so `economist`'s `gsize heading 6.0` — ~17pt in Stata — becomes 7pt
in dash, and that wrong value is **already live** in the `.db-title` CSS rule this task made
apply. This phase closes the typography half of 11-04 in both renderers, fixes the conversion
under it, removes a standalone/server split the auditor's own DONE clause introduced, repairs a
`try/except` in the served app that silently discards the scheme's legend chrome, and settles
the ledger of parsed-but-unconsumed keys that 11-04's `<done>` condition names.

---

## At a glance

| | |
|---|---|
| **Items** | 8 (numbered 1–8 below, exactly as handed over) |
| **Functional vs deliverable** | 7 functional · 1 deliverable |
| **Effort mix** | 7 × small · 1 × medium (item 4) · 0 large |
| **Renderers touched** | `both` on items 1, 2, 3, 4, 6, 7 · `server` only on item 5 · `n/a` on item 8 (a test) |
| **Ultraplan tasks discharged** | `11-04` — the *"Text:"* clause of its `<action>`, the typography half of its `<done>` ("No parsed scheme key is discarded, and the check is mechanical"), and the legend-label-size parity that the same task's legend clause created. Section **S11**. |
| **Not discharged here** | 11-04's subtitle/caption clauses and the `gsize body` / `gsize subheading` ground truth (Phase 24); its CSS-delivery, KPI-card, colour-mapping and alpha clauses and the Appendix B enumeration deliverable (Phase 25). 11-05 (scheme surface restriction) is untouched. |
| **Depends on** | Nothing hard at HEAD. `SchemeParser` already parses every key this phase consumes (`dash_render.py:1965`, `:2042-2047`, `:2086-2088`); `GlyphMapper` already holds a `scheme` reference; `ServerAppBuilder` already emits a `_SCHEME_CHROME` dict (`:12609-12623`) this phase extends. |
| **Unblocks** | **Phase 24** (subtitle/caption take the same `_TEXTBOX_DEFAULTS` path item 3 opens, and Phase 24 item 6 re-targets the key item 3 wires); **Phase 25** (its items 2, 8, 9 are the same two defects as items 8 and 5 here, seen from Appendix C). |
| **Source of items** | Items 1–6: REMAINING.md **Appendix B**, `11-04`. Items 7–8: REMAINING.md **Appendix C**, `11-04` (17 further items). Corroborated by Appendix A, `11-04 · PARTIAL`, and by the S11 row of the status table. |

---

## Why this phase exists

### The section status line (REMAINING.md, "Status by section")

> | 11 | Scheme consumption | 6 | **11-05 not done** ①, 6 partial ② | error not warning; Stata-side validation; retire `.scheme` path; help; scheme-driven **text sizing** (title, note, subtitle, mlabel) still ignored ② |

The emphasis is REMAINING.md's own. "Text sizing (title, note, subtitle, mlabel) still
ignored" is this phase, less the subtitle (Phase 24).

### What the audit measured (REMAINING.md, Appendix A — `11-04 · PARTIAL`)

Copied verbatim, because it is the proof:

> **The dead CSS is fixed and mechanically guarded.** `css_block()` now emits
> `.db-title`, `.db-subtitle` and `.db-kpi-card`, and each matches a class the
> HTML actually uses. The guard the task demanded exists:
> `test/test_scheme_consumption.py:265`
> `test_every_selector_matches_a_class_the_html_emits`, parameterised by layout.
>
> **Most keys are consumed, but through accessors, not attributes** — worth
> stating because an attribute-level grep makes them look dead. `default_color`
> has 38 external call sites and reads `p_colors`/`p_line_colors`/
> `p_bar_colors`/`p_lineplot_colors`; `default_marker_size` 6 and reads
> `marker_size`; `default_symbol` 2 (`p_symbols`); `default_line_pattern` 2
> (`p_lineplot_patterns`); `default_connect_pattern` 2 (`p_line_patterns`).
> Alphas, grid colours, legend chrome, axis and tick styling all resolve in both
> renderers.
>
> **Remaining:**
> 1. **`title_color` and `heading_font_size` never reach the figure title.** They
>    are read only by `css_block()`. Measured on `s2color`, which declares
>    `title_color='#1e2d53'` and `heading_font_size='14pt'`, while the rendered
>    figure title carries Bokeh's defaults `text_color='#444444'`,
>    `text_font_size='13px'`. The task names this explicitly: *"`title_color` and
>    `heading_font_size` reach the figure title, which today gets no colour, size
>    or alignment."* Still true of the canvas title.
> 2. **`note_font_size` has zero consumers.** Parsed at `dash_render.py:2047`
>    (`self.note_font_size = self._gsize("gsize note", "9pt")`), but the note
>    annotation at `:9867` hardcodes `{"size": 11.0, "color": "#555555"}`. The
>    colour is a hardcoded literal too, and belongs in the same fix.
> 3. `graphsize_x` / `graphsize_y` are consumed in the standalone renderer and
>    absent from the emitted app (S10 territory, but the key is a scheme key).

### The task's own wording (`.ultraplan/sections/section-11-scheme-consumption.md`, task `11-04`)

The clause this phase answers, quoted from the plan (line numbers in the plan are stale —
the file grew from ~10,455 to ~16,000 lines — so treat them as historical):

> Text: `text_font_size` replaces the mlabel `"10px"` (`:1860`); `title_color` and
> `heading_font_size` reach the figure title (`:5643-5644`), which today gets no colour,
> size or alignment; `note_font_size` reaches the note; the subtitle uses a real scheme
> value. S09 applied the explicit sub-options — this supplies their defaults.

`<done>`: *"No parsed scheme key is discarded, and the check is mechanical."*

### The four defects, at HEAD

**(a) Marker labels ignore the scheme, and the two renderers ignore it differently.**
`GlyphMapper._apply_mlabel_opts`, `dash_render.py:3344-3352` — confirmed unchanged at HEAD:

```python
        kwargs: dict[str, Any] = dict(
            x=xvar,
            y=yvar,
            text=text_col,
            source=source,
            text_font_size="10px",
            x_offset=4,
            y_offset=4,
        )
```

The explicit-option branch the item says must keep winning is six lines below
(`dash_render.py:3361-3366`):

```python
        if "mlabsize" in options:
            try:
                size_px = self.tr.translate_msize(options["mlabsize"])
                kwargs["text_font_size"] = f"{size_px}px"
            except ValueError:
                pass
```

The emitted server app writes its own label sets, at a different literal. `grep -n
"text_font_size='9px'" dash_render.py` returns **eight** sites, all inside `ServerAppBuilder`:

| line | emitted symbol |
|---:|---|
| 14452 | `_r_mlab_kw` |
| 14482 | `_r_mlab_kw` |
| 14500 | `_r_mlab_kw` |
| 14530 | `_r_mlab_kw` |
| 14550 | `_r_mlab_kw` |
| 14583 | `_r_mlab_kw` |
| 14653 | `_r_mlab_kw` |
| 14906 | `_mlab_kw2` |

So the same `mlabel(make)` draws 10px labels in the HTML file and 9px labels under
`dash serve` — a parity split that exists before any scheme is considered.

**(b) The figure title is scheme-blind unless the user styles it by hand.**
`dash_render.py:9588-9596`, the only place a `Title` model is touched in `DashRenderer`:

```python
        # title() sub-options: applied to the Title model, since the text
        # itself went in via fig_kwargs.
        _t_text, _t_opts = _parse_textbox_opt(graph_opts.get("title", ""))
        if _t_text and _t_opts and fig.title is not None:
            if "size" in _t_opts:
                fig.title.text_font_size = (
                    f"{_textbox_size(_t_opts, 16.0):g}px")
            if "color" in _t_opts or "colour" in _t_opts:
                fig.title.text_color = _textbox_color(_t_opts, "#000000")
```

`_t_opts` is empty unless the user wrote `title("…", size(…) color(…))`, so with a plain
`title("Price")` — or no title at all — nothing in that block executes. `title_color` is
parsed at `dash_render.py:1965` (`self.title_color = self._color("color heading", "#000000")`)
and has exactly one reader: `css_block()` at `dash_render.py:2209`.

On the server side the measurement is starker. `awk 'NR>12265 && /fig\.title/' dash_render.py`
returns **nothing**: there is no `fig.title.*` assignment anywhere in the emitted-app source.
The figure is created at `dash_render.py:13840` with the text and nothing else:

```python
            "        _fig_kw = dict(",
            "            title=html.escape(go.get('title', '') or ''),",
```

**(c) The note is a literal in both renderers, and `note_font_size` has no consumer at all.**
`DashRenderer`, `dash_render.py:9866-9869`:

```python
        _TEXTBOX_DEFAULTS = {
            "note":     {"size": 11.0, "color": "#555555", "y": 2.0},
            "caption":  {"size": 12.0, "color": "#555555", "y": -12.0},
        }
```

and the same dict emitted into the server app at `dash_render.py:13931-13934`:

```python
            "        _TEXTBOX_DEFAULTS = {",
            "            'note':    {'size': 11.0, 'color': '#555555', 'y': 2.0},",
            "            'caption': {'size': 12.0, 'color': '#555555', 'y': -12.0},",
            "        }",
```

`self.note_font_size = self._gsize("gsize note", "9pt")` is parsed at `dash_render.py:2047`
and read nowhere.

**(d) The gsize conversion is wrong, and the wrong value is already on screen.**
`SchemeParser._gsize`, `dash_render.py:1844-1853`:

```python
    def _gsize(self, key: str, default: str = "10pt") -> str:
        raw = self._props.get(key, "").strip().lower()
        if raw in self._GSIZE_PT:
            return self._GSIZE_PT[raw]
        # Numeric value like "3.0" → assume Stata points → rough CSS approximation
        try:
            val = float(raw)
            return f"{max(6, int(val * 1.2))}pt"
        except (ValueError, TypeError):
            return default
```

REMAINING.md's measurement of what Stata means by those numbers (Appendix B, 11-04):

> Stata's gsize values are relative sizes (style/gsize-medium.style: val 3.8194 = 11pt;
> gsize-large.style: val 4.8611 = 14pt, i.e. pt = val x 2.880), but `_gsize` returns
> `max(6, int(val*1.2))pt`. economist declares `gsize heading 6.0`, which is ~17pt in Stata
> and 7pt in dash — and that wrong value is ALREADY live in the `.db-title` rule this task
> made apply.

Confirmed at HEAD: `schemes/economist.scheme:197` reads `gsize heading       6.0`, and it is
the **only** numeric `gsize` declaration in the shipped set —
`grep -h "^gsize" schemes/*.scheme | grep -cE "gsize +[a-z_]+ +[0-9]"` returns `1` across all
14 `.scheme` files. Every other declaration is a keyword resolved by the `_GSIZE_PT` table at
`dash_render.py:1638-1655`, which is not in question.

### The legend defects the same task's DONE clause left behind

REMAINING.md, Appendix C (11-04), first item — the swallowed exception:

> The emitted `_dash_style_legend` aborts halfway on every shipped scheme: it assigns the
> scheme's clock-position INT straight to `Legend.location`, Bokeh raises ValueError, and the
> bare `except` swallows it — so `lg.ncols` on the next line never executes. This sharpens the
> auditor's "legend_position/legend_cols have zero consumers": a consumer exists, it is
> reached, and it is silently self-destructing.

The emitted block, `dash_render.py:12653-12667`, verbatim at HEAD:

```python
            "def _dash_style_legend(lg):",
            "    # The scheme's legend chrome, so a served legend matches the",
            "    # one the standalone renderer draws.",
            "    _c = _SCHEME_CHROME",
            "    try:",
            "        lg.background_fill_color = _c['legend_bg_color']",
            "        lg.border_line_color = _c['legend_border_color']",
            "        lg.label_text_font_size = _c['tick_label_font_size']",
            "        if _c.get('legend_position'):",
            "            lg.location = _c['legend_position']",
            "        if _c.get('legend_cols'):",
            "            lg.ncols = int(_c['legend_cols'])",
            "    except (AttributeError, KeyError, TypeError, ValueError):",
            "        pass",
```

The values it reads are emitted at `dash_render.py:12622-12623`:

```python
                "legend_position": getattr(sch, "legend_position", "") or "",
                "legend_cols": getattr(sch, "legend_cols", 0) or 0,
```

and `SchemeParser` parses them as integers (`dash_render.py:2086-2088`):

```python
        self.legend_position: "int | None" = self._int(
            "clockdir legend_position", None)
        self.legend_cols: "int | None" = self._int("numstyle legend_cols", None)
```

Both are declared by the shipped schemes — `schemes/s2color.scheme:199-200` has
`clockdir legend_position  6` / `numstyle legend_cols  2`, `schemes/economist.scheme:213-214`
has `12` / `3` — so the `if _c.get(...)` guards are true and the ValueError fires on every
scheme that declares a position. Everything after the failing line, `ncols` included, is
discarded in silence.

REMAINING.md, Appendix C (11-04), third item — the parity split:

> Standalone/server parity split introduced by the legend-chrome clause the auditor marked
> DONE: the two renderers size the legend label from DIFFERENT scheme keys. `_rebuild_legend`
> uses `scheme.text_font_size`; the emitted `_dash_style_legend` uses
> `_c['tick_label_font_size']`. Pick one (Stata's key_label gsize is the honest source) and
> make both renderers use it.

Standalone, `dash_render.py:9062-9068` (inside `_rebuild_legend`, which starts at `:8956`):

```python
        for leg in fig.legend:
            if self.scheme.legend_bg_color:
                leg.background_fill_color = self.scheme.legend_bg_color
            if self.scheme.legend_border_color:
                leg.border_line_color = self.scheme.legend_border_color
            if self.scheme.text_font_size:
                leg.label_text_font_size = self.scheme.text_font_size
```

The clock tables the server fix needs are immediately above it, `dash_render.py:9044-9056`:

```python
        _CLOCK_SIDE = {
            11: "above", 12: "above", 1: "above",
            2: "right", 3: "right", 4: "right",
            5: "below", 6: "below", 7: "below",
            8: "left", 9: "left", 10: "left",
        }
        _CLOCK_INSIDE = {
            11: "top_left", 12: "top_center", 1: "top_right",
            2: "top_right", 3: "center_right", 4: "bottom_right",
            5: "bottom_right", 6: "bottom_center", 7: "bottom_left",
            8: "bottom_left", 9: "center_left", 10: "top_left",
        }
```

### The ledger the `<done>` asks for, and why the current check cannot close it

11-04's `<done>` is *"No parsed scheme key is discarded, and the check is mechanical."* The
check that exists, `test/test_scheme_consumption.py:463-478` at HEAD:

```python
    @pytest.mark.parametrize("attr", [
        "fill_alpha", "bar_alpha", "area_alpha", "minor_grid_color",
        "text_font_size", "title_color", "heading_font_size",
    ])
    def test_the_key_is_read_somewhere(self, attr):
        """A parsed key with no consumer is a key that does nothing."""
        sp = SchemeParser("s2color")
        if not hasattr(sp, attr):
            pytest.skip(f"SchemeParser does not parse {attr}")
        src = open(os.path.join(_HERE, "..", "dash_render.py")).read()
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        assert code.count(f".{attr}") >= 2, (
            f"scheme.{attr} is parsed and never read"
        )
```

Seven hand-written names out of 34, and a substring count as the proof. REMAINING.md,
Appendix C (11-04), records exactly why swapping the list for an enumeration is not enough:

> Correction to remaining item 7 as written: the enumerated replacement for
> `test_the_key_is_read_somewhere` must NOT keep the current `code.count(f".{attr}") >= 2`
> heuristic. Enumerating `_init_properties` while keeping that heuristic produces four false
> failures (graphsize_x, graphsize_y, legend_position, legend_cols are all read, via
> `getattr(self.scheme, "name")` and via `_SCHEME_CHROME[...]` dict keys). The mechanical
> check the `<done>` asks for has to count string-literal reads too — or, better, assert
> behaviour (render/emit and read the value back off the model).

And the refutation that shrank the dead list, REMAINING.md, Appendix C, "3 items were refuted":

> **11-04 · `graphsize_x` / `graphsize_y` are not dead** (refuted twice, independently). They
> are read by *string*, not by attribute — `getattr(self.scheme, "graphsize_x", None)` at
> `dash_render.py:9244-9245` inside `_resolve_aspect_ratio`, whose result becomes
> `fig_kwargs["aspect_ratio"]`. Measured on rendered figures: `stcolor` → 1.6667 (scheme
> 7.5/4.5), `economist` → 1.0 (2.2/2.2), `s2color` → 1.375 (5.5/4.0). An attribute-level count
> cannot see this, which is the methodological trap — and the one Appendix A's own enumeration
> fell into before being redone. The standalone half of Appendix A's item 3 stands: re-checked
> by string, `graphsize_x`, `graphsize_y` and `_resolve_aspect_ratio` all occur **0** times in
> the emitted app, so the scheme's graph size still does not reach `dash serve`.

Putting the three together gives the real ledger this phase has to close — see TR-23.12.

---

## Epics

| epic | goal | items |
|---|---|---|
| **E23.1 — Annotation typography: point labels and the note** | Marker-label and note text take their size from the scheme in both renderers, with explicit Stata options still winning, and the last hardcoded text literals in that path go. | 1, 3 |
| **E23.2 — The figure title and the size scale under it** | The canvas title takes the scheme's colour, size and alignment in both renderers — after the `gsize` numeric conversion that feeds it is corrected. | 2, 6 |
| **E23.3 — Legend typography, the dead-key ledger and a mechanical check that works** | Both renderers size legend labels from the same key, the server stops silently discarding the scheme's legend chrome, every parsed key is wired or removed by decision, and the `<done>` check asserts behaviour instead of counting substrings. | 4, 5, 7, 8 |

---

## User stories

### E23.1 — Annotation typography

**US-23.1.1** — *As a Stata user pasting a `twoway` command, I want `mlabel()` point labels to
take their size from the scheme I asked for, so that a labelled scatter looks like the rest of
my scheme's output instead of carrying a size nobody chose.*

- **Given** a dataset and `dash scatter mpg weight, mlabel(make) scheme(economist)`
- **When** I run `dash build`
- **Then** the `LabelSet` drawn for those labels carries the size derived from `economist`'s
  `gsize text`, not `10px`
- **And Given** the same command with `mlabsize(large)` added
- **When** I build
- **Then** the explicit size wins and the scheme default is not applied.

**US-23.1.2** — *As a `dash serve` operator, I want a served dashboard's point labels to be the
same size as the same dashboard's HTML file, so that I can show either one without explaining
the difference.*

- **Given** one spec built twice, once through `DashRenderer` and once through `ServerAppBuilder`
- **When** I read `text_font_size` off every `LabelSet` in each document
- **Then** the two sets of values are equal
- **And** neither contains the literals `10px` or `9px` unless the active scheme resolves to them.

**US-23.1.3** — *As a dashboard viewer, I want the note under a graph to be sized by the
dashboard's scheme, so that the note is legible in the scheme's own scale rather than at a
fixed 11px.*

- **Given** a graph built with `note("Source: 1978 Automobile Data")` under a scheme whose note
  size differs from 11px
- **When** the figure renders in either mode
- **Then** the note `Label`'s `text_font_size` comes from the scheme key the project has decided
  is authoritative for a note (see the Phase 24 caveat in Risks)
- **And** an explicit `note("…", size(…))` still overrides it.

### E23.2 — The figure title and the size scale

**US-23.2.1** — *As a Stata user, I want the graph title to be drawn in my scheme's heading
colour and size without my having to restate them, so that `scheme(s2color)` produces s2color's
title rather than Bokeh's.*

- **Given** `dash scatter mpg weight, title("Price and weight") scheme(s2color)`
- **When** the figure is built
- **Then** `fig.title.text_color` is `#1e2d53` and `fig.title.text_font_size` is the scheme's
  heading size — not `#444444` / `13px`
- **And Given** `title("Price and weight", size(20) color(red))`
- **When** the figure is built
- **Then** the explicit sub-options win, because the scheme is applied *before* the block at
  `dash_render.py:9588-9596`.

**US-23.2.2** — *As a `dash serve` operator, I want the served figure title styled from the
scheme too, so that the served dashboard is not the only place the scheme is ignored.*

- **Given** any spec with a title and a non-default scheme
- **When** the emitted app is executed and its document inspected
- **Then** the figure's `Title` carries the scheme's colour and size
- **And** the emitted `_dash_apply_scheme` is the single place that applies it, so a future
  chrome key lands once.

**US-23.2.3** — *As a package maintainer, I want a numeric `gsize` in a scheme file to convert
to points the way Stata's own style files do, so that a translated scheme is not quietly
one-half the size Stata draws.*

- **Given** `SchemeParser("economist")`, whose file declares `gsize heading 6.0`
- **When** `heading_font_size` is read
- **Then** it reflects Stata's measured ratio `pt = val × 2.880` (6.0 → ~17.3pt), not
  `max(6, int(6.0 × 1.2))pt` = 7pt
- **And Given** a keyword such as `medium` or `large`
- **When** it is read
- **Then** the `_GSIZE_PT` table still answers, unchanged.

### E23.3 — Legend typography, the ledger and the check

**US-23.3.1** — *As a `dash serve` operator, I want the scheme's legend columns and position to
actually reach the served legend, so that a two-column legend stays two columns instead of
being discarded by an exception nobody sees.*

- **Given** a served dashboard under `economist` (`legend_position 12`, `legend_cols 3`)
- **When** `_dash_style_legend` runs on a real `Legend`
- **Then** `ncols` is 3 and the location is a Bokeh-legal value mapped from the clock integer
- **And** no exception is swallowed: a genuine failure is reported, not passed over.

**US-23.3.2** — *As a package maintainer, I want both renderers to size legend labels from the
same scheme key, so that "the legend chrome is done" means the same thing in both modes.*

- **Given** one spec and one scheme
- **When** the legend label size is read from the standalone figure and from the served figure
- **Then** the two values are equal and both trace to the single key the project chose.

**US-23.3.3** — *As a package maintainer, I want every key `SchemeParser` parses to be wired to
something or deliberately removed, so that the scheme surface has no ornamental attributes.*

- **Given** the set of attributes `_init_properties` assigns
- **When** the ledger is reviewed
- **Then** each name is either consumed by a rendered model, or removed from the parser, or
  carries a written disposition naming the task that owns it
- **And** the decision for each is recorded in `.ultraplan/CHANGELOG.md`.

**US-23.3.4** — *As a package maintainer, I want the `<done>` check to fail when a key stops
being used, so that the guard is worth having.*

- **Given** the replacement for `test_the_key_is_read_somewhere`
- **When** a consumer of any covered key is deleted
- **Then** the check fails
- **And Given** a key read only via `getattr(self.scheme, "name")` or via a `_SCHEME_CHROME`
  string key
- **When** the check runs
- **Then** it passes — no false failure for `graphsize_x`, `graphsize_y`, `legend_position` or
  `legend_cols`.

---

## Business requirements

| id | requirement | how it is tested |
|---|---|---|
| **BR-23.1** | Marker-label text size, figure-title colour and size, and note text size are defaults supplied by the active scheme in **both** render modes. | Rendered-model assertions per renderer (TP-1.1, TP-1.3, TP-2.1, TP-2.2). |
| **BR-23.2** | An explicit Stata option (`mlabsize()`, `title(…, size() color())`, `note(…, size())`) always beats the scheme default. | Precedence tests per option (TP-1.2, TP-2.3). |
| **BR-23.3** | For any one piece of text, the standalone renderer and the emitted server app read the **same** scheme key and produce the same value for the same spec. | Cross-renderer equality tests (TP-1.4, TP-3.2). |
| **BR-23.4** | No key `SchemeParser._init_properties` assigns is left parsed-and-unconsumed. A removal is an acceptable outcome; an undecided key is not. | The ledger in TR-23.12 plus the behavioural check (TP-3.4). |
| **BR-23.5** | A numeric `gsize` value converts to points by Stata's measured ratio, and the keyword path is unchanged. | Parser unit tests (TP-2.4). |
| **BR-23.6** | Scheme chrome that cannot be applied fails loudly enough to be diagnosable; it is never discarded by a blanket `except … : pass`. | TP-3.1 plus a log assertion. |
| **BR-23.7** | The mechanical check 11-04's `<done>` demands asserts behaviour or counts *all* read forms; it never produces a false failure for a string-keyed read. | TP-3.4 and its mutation. |
| **BR-23.8** | Nothing in this phase changes the output of a build that names no scheme and no text option, beyond the corrections themselves; the default dashboard stays recognisable. | Conformance corpus (`test/test_conformance.cscript`) plus a golden-size check. |

---

## Technical requirements

Files: `dash_render.py` throughout (standalone `DashRenderer` and `GlyphMapper` below
`:12265`; emitted server source above it — everything after `class ServerAppBuilder` at
`dash_render.py:12265` is *source text for the generated app*, not code that runs in the
renderer). Test files: `test/test_scheme_consumption.py`, `test/test_server_scheme.py`.
Schemes: `schemes/*.scheme` (14 files).

**TR-23.1 — mlabel default, standalone.** In `GlyphMapper._apply_mlabel_opts`
(`dash_render.py:3344-3352`), replace the literal `text_font_size="10px"` with the scheme's
`text_font_size`. `GlyphMapper` already holds the scheme (it is constructed as
`GlyphMapper(scheme=…)`; the emitted app does the same at `dash_render.py:12432`,
`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)`), so no plumbing change is needed. The
`mlabsize` branch at `dash_render.py:3361-3366` must remain **after** the default so an explicit
size still wins; `mlabcolor` at `:3355-3359` is untouched by this phase.

**TR-23.2 — mlabel default, server.** The eight emitted literals at `dash_render.py:14452`,
`:14482`, `:14500`, `:14530`, `:14550`, `:14583`, `:14653` (`_r_mlab_kw`) and `:14906`
(`_mlab_kw2`) must read the scheme instead of `'9px'`. Route them through the emitted
`_SCHEME_CHROME` dict (TR-23.9) rather than interpolating the value at build time into eight
separate string literals, so a later scheme change lands in one place. `_mlab_kw2` at `:14906`
also carries `text_color='#333333'` with an override applied two lines later
(`_mlc2 = _resolve_color(opts.get('mlabcolor', ''))`); the colour is out of scope here, the size
is not.

**TR-23.3 — units.** `SchemeParser._gsize` returns **point** strings (`"10pt"`, from the
`_GSIZE_PT` table at `dash_render.py:1638-1655`); every literal being replaced is in **pixels**
(`"10px"`, `'9px'`, `11.0` px, `13px`). Bokeh accepts both, and they are not the same size
(16px ≈ 12pt). The wiring must make one explicit choice — pass the scheme's `pt` string through
unchanged, or convert `pt → px` once in a single named helper — and record it, in the code
comment and in `.ultraplan/CHANGELOG.md`. An unremarked unit switch here would silently resize
every labelled scatter in the corpus.

**TR-23.4 — figure title, standalone.** Apply `scheme.title_color` (parsed from `color heading`
at `dash_render.py:1965`) and `scheme.heading_font_size` (from `gsize heading`, `:2043`) to
`fig.title` **before** the `_t_text, _t_opts = _parse_textbox_opt(...)` block at
`dash_render.py:9588-9596`, so that block's explicit sub-options still overwrite them. The task
also names **alignment** (*"which today gets no colour, size or alignment"*); Bokeh's
`Title.align` is the target, and the chosen default must be stated rather than assumed.
`fig.title` may be `None` when no title text was given — the existing block already guards with
`fig.title is not None` and the new code must do the same.

**TR-23.5 — figure title, server.** There is no `fig.title.*` assignment anywhere after
`dash_render.py:12265` (measured: `awk 'NR>12265 && /fig\.title/'` → zero lines). The figure is
built at `:13840` with `title=html.escape(go.get('title', '') or '')`. Add the title styling to
the emitted `_dash_apply_scheme` (`dash_render.py:12670-12688`), which already ends with the
axis block:

```python
            "    for _ax in list(fig.xaxis) + list(fig.yaxis):",
            "        _ax.axis_line_color = _c['axis_line_color']",
            "        _ax.axis_label_text_font_size = _c['axis_title_font_size']",
            "        _ax.major_label_text_font_size = _c['tick_label_font_size']",
```

`_dash_apply_scheme` is the emitted app's single chrome entry point, and its own comment states
the ordering contract — *"applied before any explicit graph option, in the same order the
standalone renderer uses — so an explicit option still overrides the scheme in both modes"*
(`dash_render.py:12671-12673`). Keep that ordering.

**TR-23.6 — the note.** `_TEXTBOX_DEFAULTS` at `dash_render.py:9866-9869` (standalone) and the
emitted copy at `dash_render.py:13931-13934` must take the note's `size` from a scheme key
instead of `11.0`. Appendix A adds: *"The colour is a hardcoded literal too, and belongs in the
same fix"* — and no colour key exists for it today: `grep -n '"color note"\|color body\|note_color'
dash_render.py` returns nothing, so the colour half requires a key to be added to
`_init_properties` and to the 14 `.scheme` files (S03-shaped work; see Risks). The size half is
landable now against `note_font_size` (`dash_render.py:2047`). The `caption` entry in the same
dict is Phase 24's.

**TR-23.7 — `_gsize` numeric branch.** In `dash_render.py:1844-1853`, replace
`max(6, int(val * 1.2))` with Stata's measured ratio `pt = val × 2.880`
(`gsize-medium.style` val 3.8194 = 11pt; `gsize-large.style` val 4.8611 = 14pt). Keep a floor if
one is wanted, but state it; keep the keyword lookup (`self._GSIZE_PT`) and the
`except (ValueError, TypeError)` default path unchanged. Blast radius, measured: exactly **one**
numeric `gsize` declaration exists across the 14 shipped schemes —
`schemes/economist.scheme:197`, `gsize heading 6.0` — so today this changes `economist`'s
heading size (7pt → ~17.3pt) and nothing else, in both the `.db-title` CSS rule
(`dash_render.py:2211`) and, once TR-23.4 lands, the canvas title. A user-supplied scheme with
numeric sizes would be affected the same way.

**TR-23.8 — the server legend.** In the emitted `_dash_style_legend`
(`dash_render.py:12653-12667`):

1. Map `_c['legend_position']` (a clock integer, 1–12) through side/anchor tables equivalent to
   `_CLOCK_SIDE` / `_CLOCK_INSIDE` at `dash_render.py:9044-9056` before assigning anything to
   `lg.location` — or drop the assignment, which item 5 explicitly allows. The raw assignment at
   `:12662` is what raises.
2. Split the `try` so one failing assignment cannot discard the rest; `lg.ncols =
   int(_c['legend_cols'])` at `:12664` must execute independently.
3. Narrow the `except (AttributeError, KeyError, TypeError, ValueError): pass` at `:12665-12666`
   so a real failure is visible — log it through the app's existing logging rather than passing
   silently (CLAUDE.md rule 14). The served dashboard must still come up.

**TR-23.9 — the emitted chrome dict.** `_SCHEME_CHROME` is built at `dash_render.py:12609-12623`
and today carries `plotregion_color`, `background_color`, `axis_line_color`, `grid_color`,
`grid_line_width`, `minor_grid_color`, `draw_major_hgrid`, `draw_major_vgrid`,
`axis_title_font_size`, `tick_label_font_size`, `legend_bg_color`, `legend_border_color`,
`legend_position`, `legend_cols`. This phase adds the keys TR-23.2, TR-23.5 and TR-23.6 need —
`text_font_size`, `title_color`, `heading_font_size`, `note_font_size` — and every emitted
consumer reads them from that dict. Note the existing `or ""` / `or 0` fallbacks on the two
legend entries (`:12622-12623`): a scheme that declares neither key yields falsy values, which is
what the `if _c.get(...)` guards test.

**TR-23.10 — legend label size, one key.** `DashRenderer._rebuild_legend` sets
`leg.label_text_font_size = self.scheme.text_font_size` (`dash_render.py:9068`); the emitted
`_dash_style_legend` sets `lg.label_text_font_size = _c['tick_label_font_size']`
(`dash_render.py:12660`). Pick one key for both. REMAINING.md's recommendation is explicit —
*"Stata's `key_label` gsize is the honest source"* — so if that key is not parsed today, the
honest options are (a) parse `gsize key_label` into a new attribute and use it in both places,
or (b) converge on one existing key and record why. Either way the two lines must name the same
thing after this phase.

**TR-23.11 — scheme defaults for the standalone legend.** Appendix C's second 11-04 item notes
that `_rebuild_legend`'s chrome loop (`dash_render.py:9062-9068`) *"has never read"* the
scheme's `legend_position` / `legend_cols` at all. Item 5 is scoped to the server; the standalone
half is carried in Phase 25 (its item 9). When item 5 lands, leave the standalone loop in a state
Phase 25 can extend — i.e. put the clock mapping somewhere both renderers reach rather than
inlining a second copy.

**TR-23.12 — the ledger.** Item 4's text names six keys. REMAINING.md corrects that count twice,
and the corrections must be carried into the ledger rather than re-derived:

| key | parsed at | status after the audit's corrections | owner |
|---|---|---|---|
| `p_mark_colors` | `dash_render.py:1980` | no consumer | **11-03**'s "wire it or remove it" — it appears in no other phase's item list, so it is decided here |
| `note_font_size` | `dash_render.py:2047` | no consumer | **11-04** — item 3 wires it (see the Phase 24 caveat in Risks) |
| `graphsize_x` | `dash_render.py:2055` | **refuted — not dead.** Read by string at `dash_render.py:9244-9245` (`getattr(self.scheme, "graphsize_x", None)` in `_resolve_aspect_ratio`) → `fig_kwargs["aspect_ratio"]`. Measured: `stcolor` → 1.6667, `economist` → 1.0, `s2color` → 1.375 | standalone done; **0** occurrences in the emitted app (S10 / geometry) |
| `graphsize_y` | `dash_render.py:2056` | as above | as above |
| `legend_position` | `dash_render.py:2086-2087` | **read, and the read self-destructs** — consumed by the emitted `_dash_style_legend` (`:12662`), which raises and is swallowed | item 5 here; standalone half in Phase 25 |
| `legend_cols` | `dash_render.py:2088` | as above (`:12664`, never reached) | as above |

So the set with genuinely **zero** consumers is two names, not six: `p_mark_colors` and
`note_font_size`. Item 4 closes when each of the six has landed as a wiring or a recorded
removal, with the disposition written into `.ultraplan/CHANGELOG.md` (S11 section).

**TR-23.13 — the mechanical check.** `test/test_scheme_consumption.py:463-478` must stop being a
substring count. The replacement must satisfy both constraints REMAINING.md states: enumerate
what `_init_properties` assigns (not a hand-written list of 7 of 34 names), **and** not fail on
keys read via `getattr(self.scheme, "name")` or via `_SCHEME_CHROME[...]` string keys. The
preferred form named in the source is behavioural — *"render/emit and read the value back off the
model"*. Enumeration can be done by instantiating `SchemeParser("s2color")` and taking the
instance's attribute names, or by walking `_init_properties`' AST; either is mechanical. Any
attribute that no behavioural assertion can reach must appear on an explicit, commented
exemption list naming the task that owns it — an exemption list of one line per key is still
mechanical, a silent skip is not (`pytest.skip` on a missing attribute, as the current test does
at `:470-471`, hides exactly the failure the check exists for).

---

## Work items

All eight, numbered exactly as handed over. `kind · renderer · effort` in brackets; *Where* and
the evidence are as REMAINING.md records them.

---

### 1. Marker-label size from the scheme  [func · both · S]

> Make `scheme.text_font_size` the default size for `mlabel()` point labels.
> `GlyphMapper._apply_mlabel_opts` builds its `LabelSet` with a hardcoded `"10px"`; an explicit
> `mlabsize()` must still win (that branch already exists 6 lines below). The server's own
> mlabel branches use a different literal, `9px`, so fixing only one side also leaves a
> standalone/server parity split.

**Where.** `dash_render.py:3350` (`GlyphMapper._apply_mlabel_opts`, `text_font_size="10px"`);
server literals at `dash_render.py:14452, 14482, 14500, 14530, 14550, 14583, 14653`
(`_r_mlab_kw`, `text_font_size='9px'`) and `14906` (`_mlab_kw2`).

**Evidence.** REMAINING.md Appendix B, 11-04, item 1; the plan's own `<action>` text
(*"`text_font_size` replaces the mlabel `"10px"`"*). Confirmed at HEAD: the `10px` literal is the
only one of its kind in the renderer, and `grep -n "text_font_size='9px'"` returns the eight
server sites listed. **Requirements:** TR-23.1, TR-23.2, TR-23.3, TR-23.9.

---

### 2. Title colour, heading size and alignment  [func · both · S]

> Route `scheme.title_color` and `scheme.heading_font_size` onto the figure `Title` (and the
> alignment the task names). Today the `Title` model is only touched when the user passes
> `title()` sub-options; with no sub-options it keeps Bokeh's defaults. The server never touches
> `fig.title` at all.

**Where.** `dash_render.py:9588-9596` (DashRenderer figure build, the
`_t_text, _t_opts = _parse_textbox_opt(...)` block — apply the scheme before it so explicit
sub-options still win); server: no `fig.title.*` assignment exists after `dash_render.py:12265`,
figure created at `13840` with `title=html.escape(go.get('title',''))` only.

**Evidence.** REMAINING.md Appendix A, 11-04, remaining item 1 — measured on `s2color`:
declared `title_color='#1e2d53'`, `heading_font_size='14pt'`; rendered title `text_color='#444444'`,
`text_font_size='13px'`. `title_color` is parsed at `dash_render.py:1965` and read only by
`css_block()` at `:2209`. **Requirements:** TR-23.4, TR-23.5, TR-23.9. **Sequencing:** land item 6
first or together — otherwise `economist`'s 7pt heading goes onto the canvas as well as into the
CSS.

---

### 3. Note size from the scheme  [func · both · S]

> Make `scheme.note_font_size` the default size for the `note()` annotation. It currently has
> ZERO consumers anywhere in the file — the note `Label` uses a hardcoded `11.0px` default in
> both renderers.

**Where.** `dash_render.py:9867` (`_TEXTBOX_DEFAULTS = {"note": {"size": 11.0, ...}}` in
`DashRenderer`) and `dash_render.py:13932` (the same dict emitted into the server app).

**Evidence.** REMAINING.md Appendix A, 11-04, remaining item 2, and Appendix B, 11-04, item 3.
Parsed at `dash_render.py:2047`; both `_TEXTBOX_DEFAULTS` copies confirmed verbatim at HEAD.
**Requirements:** TR-23.6, TR-23.9, TR-23.12. **Caveat, carried from Appendix C and owned by
Phase 24:** `gsize note` is a dead key at Stata scheme level — see Risks R1. Wire the mechanism
here; the key it points at may be re-targeted by Phase 24 item 6.

---

### 4. Close the `<done>` condition on the discarded keys  [func · both · M]

> Close the task's `<done>` condition: 6 of the 34 keys `SchemeParser` parses still have zero
> consumers — `p_mark_colors`, `note_font_size`, `graphsize_x`, `graphsize_y`, `legend_position`,
> `legend_cols`. (`p_mark_colors` is 11-03's "wire it or remove it"; `graphsize_x`/`y` are marked
> in-code as S10's; `note_font_size` and the two legend keys are 11-04's.) Decide and land each,
> including the removals.

**Where.** `dash_render.py:1980` (`p_mark_colors`), `2047` (`note_font_size`), `2054-2056`
(`graphsize_x`/`graphsize_y`), `2086-2088` (`legend_position`, `legend_cols`) — all in
`SchemeParser._init_properties`.

**Evidence.** REMAINING.md Appendix B, 11-04, item 6 — which carries its own inline correction:
*"(**4**, not 6 — `graphsize_x`/`graphsize_y` were refuted, see Appendix C)"*. Items 5 and 7 below
narrow it further: the two legend keys **are** read, by a read that raises and is swallowed. The
resolved ledger is TR-23.12; the genuinely unconsumed set is `p_mark_colors` and `note_font_size`.
`p_mark_colors` appears in no other phase's item list, so its wire-or-remove decision is taken
here and recorded. **Requirements:** TR-23.12, and whichever of TR-23.6 / TR-23.8 the decisions
select.

---

### 5. The server's swallowed legend exception  [func · server · S]

> Fix the swallowed exception in the server's `_dash_style_legend`: it assigns Stata's clock
> integer to Bokeh's `Legend.location` enum, which raises inside the `try`, so `legend_cols` is
> never applied either. Map the clockdir through the same `_CLOCK_SIDE`/`_CLOCK_INSIDE` tables
> the standalone renderer uses (or drop the assignment), and narrow the except so a real failure
> is not hidden. Also align the label size: standalone uses `text_font_size`, the server uses
> `tick_label_font_size`.

**Where.** `dash_render.py:12657-12666` (emitted `_dash_style_legend`:
`lg.location = _c['legend_position']` at `12662`, `lg.ncols = int(_c['legend_cols'])` at `12664`,
`except (AttributeError, KeyError, TypeError, ValueError): pass` at `12665-12666`); values emitted
at `12622-12623`; standalone label size at `dash_render.py:9067-9068`.

**Evidence.** REMAINING.md Appendix B, 11-04, item 10, sharpened by Appendix C's first two 11-04
items: *"a consumer exists, it is reached, and it is silently self-destructing"*. Both shipped
schemes checked declare a position (`s2color` 6, `economist` 12), so the guard is true and the
assignment raises on every one of them. **Requirements:** TR-23.8, TR-23.10, TR-23.11.
**Overlap:** Phase 25 items 8 and 9 are the Appendix C statements of this same defect — whoever
lands first closes the other, and Phase 25 still owns the standalone half of the two legend keys.

---

### 6. The `_gsize` numeric branch  [func · both · S]

> Fix `SchemeParser._gsize`'s numeric branch before `heading_font_size` is wired to anything
> else. Stata's gsize values are relative sizes (`style/gsize-medium.style`: val 3.8194 = 11pt;
> `gsize-large.style`: val 4.8611 = 14pt, i.e. pt = val x 2.880), but `_gsize` returns
> `max(6, int(val*1.2))pt`. `economist` declares `gsize heading 6.0`, which is ~17pt in Stata and
> 7pt in dash — and that wrong value is ALREADY live in the `.db-title` rule this task made apply.

**Where.** `dash_render.py:1844-1853` (`SchemeParser._gsize`, the `float(raw)` branch at
`1849-1851`).

**Evidence.** REMAINING.md Appendix B, 11-04, item 12. Confirmed at HEAD: the branch is
unchanged, `schemes/economist.scheme:197` is `gsize heading       6.0`, and it is the only
numeric `gsize` in the shipped set. **Requirements:** TR-23.7. **Sequencing:** the item's own
first clause — *"before `heading_font_size` is wired to anything else"* — makes this a
prerequisite of item 2.

---

### 7. One key for the legend label size  [func · both · S]

> Standalone/server parity split introduced by the legend-chrome clause the auditor marked DONE:
> the two renderers size the legend label from DIFFERENT scheme keys. `_rebuild_legend` uses
> `scheme.text_font_size`; the emitted `_dash_style_legend` uses `_c['tick_label_font_size']`.
> Pick one (Stata's `key_label` gsize is the honest source) and make both renderers use it.

**Where.** `dash_render.py:9068` (`DashRenderer._rebuild_legend`); `dash_render.py:12660`
(`ServerAppBuilder`, emitted `_dash_style_legend`).

**Evidence.** REMAINING.md Appendix C, 11-04, third item. Both lines confirmed verbatim at HEAD.
**Requirements:** TR-23.10. Landing this with item 5 is natural — they edit adjacent lines of the
same emitted function.

---

### 8. The mechanical check must not be a substring count  [deli · n/a · S]

> Correction to remaining item 7 as written: the enumerated replacement for
> `test_the_key_is_read_somewhere` must NOT keep the current `code.count(f".{attr}") >= 2`
> heuristic. Enumerating `_init_properties` while keeping that heuristic produces four false
> failures (`graphsize_x`, `graphsize_y`, `legend_position`, `legend_cols` are all read, via
> `getattr(self.scheme, "name")` and via `_SCHEME_CHROME[...]` dict keys). The mechanical check
> the `<done>` asks for has to count string-literal reads too — or, better, assert behaviour
> (render/emit and read the value back off the model).

**Where.** `test/test_scheme_consumption.py:463-478`.

**Evidence.** REMAINING.md Appendix C, 11-04, seventh item. The current test is quoted in full in
*Why this phase exists*; at HEAD its parametrize list holds 7 names and its assertion is
`code.count(f".{attr}") >= 2` with comments stripped. **Requirements:** TR-23.13.
**Overlap:** Phase 25 item 2 is Appendix B's version of this deliverable (*"Replace the
hand-written attribute list … with a real enumeration"*). This item is the **constraint** that
enumeration must satisfy; land the constraint and the behavioural arm for this phase's keys here,
and hand the full enumeration to Phase 25 rather than writing a check that will need redoing.

---

## Test plan

Project rules that shape it: **rule 8** — every one of items 1, 2, 3, 5, 6 and 7 is a bug fix, so
each gets a regression test written *first*, shown to fail at HEAD, and shown to pass after;
**rule 4** — every function touched gets a unit test; **rule 20** — the three epics are
independent enough to run in parallel once item 6 has landed.

**Harnesses that already exist** (use them, do not build new ones):

- `test/test_scheme_consumption.py` — `_render(plots, *, scheme=…, theme=…, layout=…, kpis=…,
  title=…, subtitle=…)` at `:60-90` returns `(html, DashRenderer)`; `TestNoParsedKeyIsDiscarded`
  at `:427`; the selector guard `TestSchemeCssActuallyApplies` at `:242`.
- `test/test_server_scheme.py` — `_build_doc(tmp_path, build_options, plots=None)` at `:43`
  builds the app with `ServerAppBuilder`, `exec_module`s it and calls `mod.make_document(doc)`,
  returning a live Bokeh `Document`; `_figures(doc)` at `:69` walks GridPlot tuples correctly.
  This is the server arm every item below needs, and it makes "assert against a rendered model"
  cheap.

### Epic E23.1 — annotation typography (items 1, 3)

| id | test | file · new class/name | proves |
|---|---|---|---|
| **TP-1.1** | **Write first, must fail at HEAD.** `test_mlabel_size_comes_from_the_scheme`: render a scatter with `mlabel` under `economist`, pull every `LabelSet` off the figure, assert `text_font_size` equals the value derived from `scheme.text_font_size`. Fails today with `10px`. | `test/test_scheme_consumption.py`, new `TestSchemeTextSizes` | item 1, standalone |
| **TP-1.2** | `test_an_explicit_mlabsize_still_wins`: same spec plus `mlabsize(large)`; assert the translated explicit size, not the scheme's. | same | BR-23.2 |
| **TP-1.3** | **Write first, must fail at HEAD.** `test_the_served_mlabel_size_comes_from_the_scheme`: `_build_doc(...)` with `mlabel`, walk `fig.center` for `LabelSet`s, assert the scheme value. Fails today with `9px`. | `test/test_server_scheme.py`, new `TestSchemeTextSizes` | item 1, server |
| **TP-1.4** | `test_both_renderers_label_at_the_same_size`: one spec, both harnesses, assert the two `text_font_size` sets are equal. | `test/test_server_scheme.py` | BR-23.3 |
| **TP-1.5** | **Write first, must fail at HEAD.** `test_the_note_size_comes_from_the_scheme`: build with `note("…")` under a scheme whose note size ≠ 11px; assert the `Label`'s `text_font_size`. Standalone and server arms. | both test files | item 3 |
| **TP-1.6** | Unit: `GlyphMapper._apply_mlabel_opts` called directly with a stub scheme and (a) no options, (b) `mlabsize`, (c) `mlabcolor` only — assert the resolved kwargs dict. Rule 4 coverage for the changed function. | `test/test_scheme_consumption.py` | TR-23.1 |
| **TP-1.7** | Unit: `SchemeParser("s2color").note_font_size` and `SchemeParser("economist").note_font_size` return the values their files declare (`gsize note small` → the table's 8pt; `gsize note large` → 14pt). | `test/test_scheme_consumption.py` | TR-23.6 |

**Non-vacuity (mutation).** Put `text_font_size="10px"` back in `_apply_mlabel_opts` → TP-1.1,
TP-1.4 and TP-1.6 must fail. Put `'9px'` back in one of the eight emitted sites → TP-1.3 and
TP-1.4 must fail (this is the mutation that matters: it proves the test walks *all* label sets,
not just the first). Move the `mlabsize` branch above the default → TP-1.2 must fail. Restore
`'size': 11.0` in either `_TEXTBOX_DEFAULTS` copy → TP-1.5 must fail on that renderer only.

### Epic E23.2 — the figure title and the size scale (items 2, 6)

| id | test | file · new class/name | proves |
|---|---|---|---|
| **TP-2.1** | **Write first, must fail at HEAD.** `test_the_figure_title_takes_the_schemes_colour_and_size`: `_render(scheme="s2color", title="Price and weight")`, assert `fig.title.text_color == "#1e2d53"` and the size is the scheme's heading size. Fails today with `#444444` / `13px` — the exact pair Appendix A measured. | `test/test_scheme_consumption.py`, `TestSchemeTextSizes` | item 2, standalone |
| **TP-2.2** | **Write first, must fail at HEAD.** `test_the_served_title_takes_the_schemes_colour_and_size`: `_build_doc` with the same build options; assert on `figs[0].title`. Fails today because no `fig.title.*` assignment exists in the emitted app. | `test/test_server_scheme.py` | item 2, server |
| **TP-2.3** | `test_an_explicit_title_suboption_still_wins`: `title("t", size(20) color(red))` under `s2color`; assert the explicit values survive, in both renderers. | both | BR-23.2, TR-23.4 |
| **TP-2.4** | **Write first, must fail at HEAD.** `test_a_numeric_gsize_uses_statas_ratio`: `SchemeParser("economist").heading_font_size` reflects `6.0 × 2.880` (≈17.3pt) within the rounding the fix documents; and `test_a_keyword_gsize_is_unchanged` asserts `medium` → `11pt`, `large` → `14pt` from `_GSIZE_PT`. Fails today at `7pt`. | `test/test_scheme_consumption.py` | item 6 |
| **TP-2.5** | `test_the_db_title_rule_and_the_canvas_title_agree`: `css_block()`'s `.db-title` font-size and `fig.title.text_font_size` come from the same parsed value for the same scheme — the two consumers of `heading_font_size` cannot drift. | `test/test_scheme_consumption.py` | BR-23.1, TR-23.7 |
| **TP-2.6** | Unit: `_gsize` table-driven — keyword hit, numeric value, unparseable value (falls back to the passed default), empty key. Rule 4 coverage for the changed function. | `test/test_scheme_consumption.py` | TR-23.7 |

**Non-vacuity (mutation).** Restore `max(6, int(val * 1.2))` → TP-2.4 and TP-2.5 must fail.
Delete the scheme-application lines before `dash_render.py:9588` → TP-2.1 and TP-2.3's default
half must fail. Delete the title lines from the emitted `_dash_apply_scheme` → TP-2.2 must fail.
Move the scheme application *after* the `_t_opts` block → TP-2.3 must fail while TP-2.1 still
passes, which is the specific ordering regression TR-23.4 exists to prevent.

### Epic E23.3 — legend typography, the ledger, the check (items 4, 5, 7, 8)

| id | test | file · new class/name | proves |
|---|---|---|---|
| **TP-3.1** | **Write first, must fail at HEAD.** `test_the_served_legend_gets_the_schemes_columns`: build an app under `economist` (`legend_cols 3`), reach the emitted `_dash_style_legend` (via the module object `_build_doc` execs) and apply it to a real `Legend`; assert `ncols == 3`. Fails today because the location assignment raises first and the bare `except` eats it. | `test/test_server_scheme.py`, new `TestServerLegendChrome` | item 5 |
| **TP-3.2** | **Write first, must fail at HEAD.** `test_both_renderers_size_the_legend_label_from_the_same_key`: one spec, one scheme, assert `label_text_font_size` equal across the two documents. Fails today whenever `text_font_size != tick_label_font_size` — true of `s2color` (`medium` 11pt vs `medsmall` 10pt, `schemes/s2color.scheme:179,182`). | `test/test_server_scheme.py` | item 7 |
| **TP-3.3** | `test_a_clock_position_becomes_a_legal_bokeh_location`: parametrized over 1–12, assert each maps to a value Bokeh accepts, and that an out-of-range or missing value leaves the legend untouched without raising. | `test/test_server_scheme.py` | TR-23.8 |
| **TP-3.4** | **The replacement for `test_the_key_is_read_somewhere`** (`test/test_scheme_consumption.py:463-478`): enumerate the attributes `_init_properties` assigns; for each, either assert the value reaches a rendered model (standalone and/or server) or match it against a commented exemption list naming the owning task. No `code.count(".attr")`, no silent `pytest.skip`. | `test/test_scheme_consumption.py`, replacing the current test | item 8, BR-23.7 |
| **TP-3.5** | `test_no_parsed_key_is_unaccounted_for`: the union of (behaviourally asserted keys) and (the exemption list) equals the enumerated set — so adding a key to `_init_properties` without a consumer or a disposition fails the suite. | same | item 4, BR-23.4 |
| **TP-3.6** | `test_the_two_legend_keys_are_not_silently_dropped`: assert the string-keyed reads in `_SCHEME_CHROME` count as consumption, i.e. the new check does **not** flag `legend_position`, `legend_cols`, `graphsize_x`, `graphsize_y` — the four false failures Appendix C names. | same | item 8 |
| **TP-3.7** | Integration, Stata: a cscript that runs `dash scatter mpg weight, mlabel(make) title("t") note("n") scheme(economist)` then `dash build` and asserts rc 0, no scheme-fallback warning, and that the built HTML contains neither `10px` nor `9px` as a label size. Name: `test/test_scheme_text.cscript`, run with `arch -arm64` from `test/`. | new cscript | end-to-end, rule 4's E2E half |

**Non-vacuity (mutation).** Restore the single wide `try` in `_dash_style_legend` → TP-3.1 must
fail. Point `_dash_style_legend` back at `tick_label_font_size` (or `_rebuild_legend` back at
`text_font_size`, whichever item 7 does not choose) → TP-3.2 must fail. Add a throwaway
`self.unused_key = "x"` to `_init_properties` → TP-3.5 must fail; remove it again and the suite
must go green without any other edit. Delete one consumer of `text_font_size` → TP-3.4 must fail.
Re-introduce the `code.count(...)` heuristic alongside the enumeration → TP-3.6 must fail with the
four names Appendix C predicts, which is the proof that the correction in item 8 was necessary.

### Suite-level

- Full `pytest` run, and the certification suite from `test/` with `arch -arm64`. A skip is not a
  pass — skip counts must be accounted for, per the S01 runner rule.
- `test/test_conformance.cscript` and the parity corpus must stay green: item 1 changes the size
  of every marker label in the corpus and item 6 changes `economist`'s heading, so any golden
  expectation that encodes `10px`, `9px`, `13px` or `7pt` has to be updated deliberately, with the
  new value justified by the scheme file it comes from.
- `.ultraplan/CHANGELOG.md` S11 section records: the unit decision from TR-23.3, the alignment
  default from TR-23.4, the key chosen in TR-23.10, and each disposition in the TR-23.12 ledger.

---

## Definition of done

A reviewer can tick every line below.

**Behaviour**

- [ ] `mlabel()` labels take their size from `scheme.text_font_size` in `DashRenderer`, and the literal `"10px"` is gone from `dash_render.py:3350`.
- [ ] All eight emitted `'9px'` label sizes (`:14452, 14482, 14500, 14530, 14550, 14583, 14653, 14906`) read the scheme through `_SCHEME_CHROME`.
- [ ] `mlabsize()` still wins over the scheme, in both renderers.
- [ ] `fig.title` carries `scheme.title_color`, `scheme.heading_font_size` and the agreed alignment on a plain `title("…")` build — measured on `s2color` as `#1e2d53`, not `#444444`.
- [ ] The emitted app styles its figure title from the same values, inside `_dash_apply_scheme`.
- [ ] `title("…", size() color())` still overrides the scheme in both renderers.
- [ ] The note `Label` takes its size from a scheme key in both `_TEXTBOX_DEFAULTS` copies (`:9867`, `:13932`); the hardcoded `11.0` is gone.
- [ ] `_gsize`'s numeric branch converts by Stata's ratio; `SchemeParser("economist").heading_font_size` is no longer `7pt`; the `_GSIZE_PT` keyword path is unchanged.
- [ ] The emitted `_dash_style_legend` applies `ncols` on every shipped scheme, maps the clock integer to a legal Bokeh location (or drops the assignment by recorded decision), and no longer hides failures behind a blanket `except … : pass`.
- [ ] Both renderers size legend labels from **one** key, and the two lines (`:9068`, `:12660`) name it.

**Ledger and record**

- [ ] Each of the six keys in TR-23.12 is wired, removed, or carries a written disposition naming its owning task; `p_mark_colors` in particular has a decision, taken here.
- [ ] The pt/px decision (TR-23.3), the title alignment (TR-23.4) and the legend key (TR-23.10) are written into `.ultraplan/CHANGELOG.md`, S11 section.

**Tests**

- [ ] Every regression test named "write first" above was seen to fail at HEAD and pass after (rule 8), and the transcript of both states is in the commit message or the PR body.
- [ ] Each changed function has a unit test (rule 4): `_apply_mlabel_opts`, `_gsize`, the title-styling path, the note default path, `_dash_style_legend`.
- [ ] Every mutation listed under *Non-vacuity* was applied and killed the test it names.
- [ ] `test_the_key_is_read_somewhere` is replaced by an enumerated, behavioural check with an explicit exemption list; it produces **no** false failure for `graphsize_x`, `graphsize_y`, `legend_position`, `legend_cols`.
- [ ] `test/test_scheme_text.cscript` exists, runs under `arch -arm64` from `test/`, and passes.
- [ ] Full pytest and the full certification suite pass, with skip counts accounted for; the conformance and parity corpora are green and any updated golden value is justified against the scheme file it comes from.

---

## Risks and sequencing notes

**R1 — `gsize note` is a dead key at Stata level; item 3 wires a mechanism, not necessarily the
final key.** REMAINING.md, Appendix C (11-04), carried in full because it directly qualifies item
3:

> `gsize note` is a DEAD key at Stata scheme level — exactly the trap this file already documented
> for `draw_major_grid`. No style file reads `scheme note`; the note textbox is
> `textboxstyle-body`, which reads `gsize body` / `color body`. Wiring `SchemeParser.note_font_size`
> (from `gsize note`) to the note `Label`, as the remaining item prescribes, would draw economist's
> note at 14pt where Stata draws ~8.6pt. Parse `gsize body` (and `color body`) instead, and add
> those keys back to the 14 translated `.scheme` files, which dropped them on purpose.

That item is **Phase 24's item 6**, not this phase's. Confirmed at HEAD: `economist.scheme:200` is
`gsize note large` → 14pt via `_GSIZE_PT`, and no `.scheme` file carries a live `gsize body`
declaration (the only match, `economist.scheme:247`, is a comment listing keys that were dropped).
The safe order is: land item 3's **mechanism** (the note `Label` reads a scheme attribute instead
of `11.0`) here, and let Phase 24 re-point that attribute at `gsize body` once the key exists in
the 14 files. Do not close item 3 by asserting that 14pt is correct — it is not; assert only that
the literal is gone and that the scheme decides. The same caveat applies to the note **colour**:
no `color note` / `color body` key is parsed today, so the colour half of TR-23.6 cannot be landed
honestly before that S03-shaped work.

**R2 — item 6 before item 2.** Item 6's own wording is *"before `heading_font_size` is wired to
anything else"*. Wiring the title first would put `economist`'s 7pt on the canvas as well as in
the CSS, and would make TP-2.1's expected value wrong twice over.

**R3 — points and pixels are not the same size.** Every literal being replaced is `px`; every
scheme value is `pt`. TR-23.3 makes the choice explicit and testable; skipping it is how this fix
silently shrinks or grows every labelled scatter in the conformance corpus.

**R4 — the server's copy of `GlyphMapper` cuts both ways.** `ServerAppBuilder` copies
`OptionTranslator`, `SchemeParser` and `GlyphMapper` into the emitted app with
`inspect.getsource` (`dash_render.py:12408-12409`) and constructs `_DASH_MAPPER` at `:12432`. So
item 1's standalone edit reaches `dash serve` **only through branches that delegate** — at the
time of the audit exactly one did (`_DASH_MAPPER.map_scatter` at `dash_render.py:14090`; REMAINING.md
15-03, remaining item 1). The eight hand-written `9px` sites are the other branches, which is why
item 1 names them. If Phase 05/07 (the dispatch collapse) lands before this phase, some of those
eight sites will no longer exist — **re-grep `text_font_size='9px'` before editing** rather than
trusting the line numbers here, and fix whatever remains.

**R5 — line numbers drift, evidence does not.** Every line number in this document was confirmed
against `dash_render.py` at `feature/batch4-interactive-layer` (`187a786`). The file is ~16,000
lines and any edit in this phase moves later numbers. Re-locate by symbol (`_apply_mlabel_opts`,
`_TEXTBOX_DEFAULTS`, `_dash_style_legend`, `_dash_apply_scheme`, `_gsize`, `_SCHEME_CHROME`),
not by number.

**R6 — narrowing the swallowed `except` can surface failures that were previously invisible.**
That is the point, but a served dashboard must not stop coming up because of a chrome failure.
TR-23.8 requires the failure to be logged and the app to survive; a test that asserts the document
still builds when one chrome value is nonsense belongs with TP-3.3.

**R7 — overlapping items across phases.** Three overlaps, all deliberate, all recorded above so
neither phase silently re-does the other's work: item 5 here ↔ Phase 25 items 8 and 9 (the same
`_dash_style_legend` defect from Appendix B and Appendix C); item 8 here ↔ Phase 25 item 2 (this
is the constraint on that enumeration); item 3 here ↔ Phase 24 item 6 (the key the note should
read). Item 4's ledger cannot be *ticked* until Phase 24 and Phase 25 have taken their halves of
the legend and note decisions — but the two genuinely unconsumed keys (`p_mark_colors`,
`note_font_size`) are decided here, and nothing else in the index claims `p_mark_colors`.

**R8 — suggested internal order.** (1) item 6, alone, with TP-2.4/TP-2.6 — it is a parser change
with one measured consequence. (2) items 2 and 7 with 5 — they touch the same two emitted
functions. (3) items 1 and 3 — the annotation literals, standalone then server. (4) items 8 and 4
last: the check and the ledger are the closing argument, and writing them first would mean writing
them against a moving target.
