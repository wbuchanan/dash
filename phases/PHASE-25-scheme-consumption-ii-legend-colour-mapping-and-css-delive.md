# Phase 25 — Scheme consumption II — legend, colour mapping and CSS delivery

**Purpose.** Ultraplan task 11-04 ("Consume the remaining discarded keys and fix the dead
CSS") was audited as PARTIAL, and the part of it that this phase owns is the part that looks
finished from the source and is not finished in a browser. The scheme's legend chrome is
written into both renderers, and in `dash serve` it destroys itself on the first assignment
and silently drops everything after it. The colour key and the colour bar are pinned to the
`"right"` panel while `legend(position() ring())` is parsed and ignored, and `colorvar()`
has no branch at all in `ServerAppBuilder`. The scheme's stylesheet is emitted, is
mechanically guarded, and — in the Bootstrap layout, for any dashboard that contains a widget
— never reaches the browser, because the head is lifted out of Bokeh's own document with a
non-greedy regex and `bokeh-widgets.min.js` contains a literal `</head>` inside a JavaScript
string. The one rule in that stylesheet that has something to match, `.db-kpi-card`, is beaten
by an inline `style=` attribute on the card it names. This phase makes the legend, the colour
mapping and the CSS delivery real in both renderers, and replaces the three string-matching
guards that let all of this pass with behavioural ones that assert against a rendered model.

---

## At a glance

| | |
|---|---|
| **Items** | 15 (numbered 1–15 below; 7 from Appendix B, 8 from Appendix C) |
| **Functional vs deliverable** | 9 functional · 6 deliverable |
| **Effort mix** | 10 small · 4 medium · 1 large |
| **Renderers touched** | standalone 4 (items 1, 6, 12, 13) · server 5 (items 3, 8, 11, 14, 15) · both 5 (items 4, 5, 7, 9, 10) · n/a 1 (item 2) |
| **Ultraplan discharged** | Task **11-04**, section 11 (scheme consumption) — the legend, colour-mapping and dead-CSS clauses of its `<action>`, plus the mechanical half of its `<done>` |
| **Task-mates** | 11-04 carries **32** backlog items (15 Appendix B + 17 Appendix C). Phase 23 takes 8 (text sizing/typography), Phase 24 takes 9 (subtitle, caption, size stubs), **Phase 25 takes these 15** |
| **Depends on** | Phase 23 (owns the Appendix-B statement of the `_dash_style_legend` fix and the legend label-size parity split), Phase 24 (wires `css_block()` into the served dashboard and fixes the shadow-root Divs), Phases 5–7 (15-03 server unification — makes item 15 cheap rather than large) |
| **Unblocks** | Phase 30 (documentation/help reconciliation for S11), Phase 31 (release gates: 11-04 cannot be certified closed while its `<verify>` line — "Alphas, text sizes, legend styling and colour palettes all track the scheme; the CSS selector test passes" — is false in a browser) |
| **Primary files** | `dash_render.py` (both renderers), `test/test_scheme_consumption.py`, `test/test_server_scheme.py`, `test/test_server_legend.py`, `test/test_colorvar_legend.py`, `.ultraplan/CHANGELOG.md` |

---

## Why this phase exists

### 1. What the task asked for

From `.ultraplan/sections/section-11-scheme-consumption.md:152`, task `11-04`, the three
clauses this phase owns (the text-sizing clauses belong to Phases 23 and 24):

> **Legend:** `legend_bg_color` and `legend_border_color` (`:923-924`) currently have **zero
> consumers**, because with no `legend()` option nothing is styled at all (`:6004-6005`).
> Style the legend from the scheme unconditionally.
>
> **Colour mapping:** the discrete `colorvar` palette (`Category10_10`, `:1727-1730`) and the
> continuous one (`Viridis256`, `:1780-1781`) both ignore the scheme; use `scheme.p_colors`
> for discrete. Colorbar placement is hardcoded `"right"` (`:1769`, `:1797`) while
> `legend(position() ring())` is parsed and ignored — honour it.
>
> **The dead CSS.** `css_block()` (`:1026-1035`) emits `.dash-title`, `.dash-subtitle` and
> `.kpi-card`; the HTML emits `db-title`, `db-subtitle` and inline-styled KPI divs
> (`:6551`, `:6555`, `:6292-6300`). Align them so the block applies, and add a test
> asserting every selector `css_block()` emits matches a class the HTML actually uses.
> That test is what stops this recurring.
>
> `minor_grid_color` is also parsed and unread; wire it.
>
> `<verify>` Alphas, text sizes, legend styling and colour palettes all track the scheme; the
> CSS selector test passes.
> `<done>` No parsed scheme key is discarded, and the check is mechanical.

(The line numbers in that section file are stale — the file grew from ~10,455 to ~16,000
lines. Every line number below is the current one, taken from `REMAINING.md` or re-measured
at `ca5fe35`.)

### 2. What the audit measured — `REMAINING.md`, Appendix A

> ## 11-04 — Consume the remaining discarded keys and fix the dead CSS · PARTIAL
>
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

Appendix A's own three "Remaining" items for 11-04 — `title_color`/`heading_font_size` on the
figure title, `note_font_size` with zero consumers, and `graphsize_x`/`graphsize_y` missing
from the emitted app — are **Phase 23 and Phase 24 work**, listed here only so a reader of
this document knows they are covered elsewhere and not lost.

Appendix A closes its survey with:

> The exceptions are 05-04, which is `dash.ado` work that gates S07/S09/S10, and
> 11-04, which is three small standalone fixes.

The adversarial pass then found 17 more items on this one task, nine of which are in this
phase. "Three small standalone fixes" is the assessment this phase exists to correct:
`REMAINING.md`'s own backlog arithmetic is

> | task | Appendix B | Appendix C | total |
> |---|---:|---:|---:|
> | 11-04 Scheme keys and dead CSS | 15 | 17 | **32** |

### 3. Evidence — the served legend chrome self-destructs on every shipped scheme

`ServerAppBuilder` emits a scheme-chrome dict and a styling function into the generated
`bokeh serve` app. The dict is built at `dash_render.py:12618-12623`:

```python
    "legend_bg_color": sch.legend_bg_color,
    "legend_border_color": sch.legend_border_color,
    "legend_position": getattr(sch, "legend_position", "") or "",
    "legend_cols": getattr(sch, "legend_cols", 0) or 0,
```

and the consumer is the emitted string block at `dash_render.py:12653-12667`:

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

`legend_position` is parsed as a **Stata clock integer**, not a Bokeh anchor
(`dash_render.py:2086-2088`):

```python
        # Stata's clockdir is a numeric clock position (1-12), so expose it as
        # a number rather than the raw string — consumers compare it as one.
        self.legend_position: "int | None" = self._int(
            "clockdir legend_position", None)
        self.legend_cols: "int | None" = self._int("numstyle legend_cols", None)
```

`Legend.location` is a Bokeh enum (`top_left`, `center_right`, …) or an `(x, y)` tuple, so
assigning `3` raises `ValueError` inside the `try`, the bare `except` swallows it, and
`lg.ncols` on the **next line never executes**. From `REMAINING.md`, Appendix C:

> The emitted `_dash_style_legend` aborts halfway on every shipped scheme: it
> assigns the scheme's clock-position INT straight to `Legend.location`, Bokeh raises
> ValueError, and the bare `except` swallows it — so `lg.ncols` on the next line never
> executes. This sharpens the auditor's "legend_position/legend_cols have zero consumers": a
> consumer exists, it is reached, and it is silently self-destructing. … Any future scheme
> chrome appended to this block is equally unreachable.

and:

> legend_position and legend_cols are NOT unconsumed — the generated server app reads both
> and the read is broken.

The mapping the fix needs already exists in the standalone renderer, in
`DashRenderer._rebuild_legend` at `dash_render.py:9044-9056`:

```python
        # ---- Stata's clock positions -------------------------------
        # 12 o'clock is straight up, 3 is right, 6 is down, 9 is left.  The
        # measured placements group into the four sides; ring(0) keeps the
        # legend inside the plot region instead of in a side panel.
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

The standalone chrome loop immediately below it (`dash_render.py:9062-9068`) reads three
keys and has **never** read the two legend-placement keys at all:

```python
        for leg in fig.legend:
            if self.scheme.legend_bg_color:
                leg.background_fill_color = self.scheme.legend_bg_color
            if self.scheme.legend_border_color:
                leg.border_line_color = self.scheme.legend_border_color
            if self.scheme.text_font_size:
                leg.label_text_font_size = self.scheme.text_font_size
```

So the two renderers disagree twice over: one reads the placement keys and breaks, the other
does not read them; one sizes the label from `scheme.text_font_size`, the other from
`_c['tick_label_font_size']` (that second split is Phase 23's item 7, and is called out here
because the two fixes touch the same six lines).

### 4. Evidence — the served facet legend gets no chrome at all

From `REMAINING.md`, Appendix C:

> In server mode a by()-faceted figure's legend never receives the scheme chrome:
> `_dash_style_legend` is called only from the main (unfaceted) plot loop, while the facet
> loop builds its figure and its auto-legend and moves on. So one dashboard serves faceted
> panels with Bokeh-default legends and unfaceted panels with the scheme's — the clause
> 'style the legend from the scheme unconditionally' is unmet on the faceted path.

The paired call exists only in the main loop, at `dash_render.py:14955-14961`:

```python
"                _lg = Legend(items=_items, location='top_right')",
"                _lg.click_policy = 'hide'",
"                # twoway draws no legend for a single series; the standalone",
"                # renderer builds one and hides it, so both documents carry",
"                # the same models.",
"                _lg.visible = len(_items) > 1",
"                fig.add_layout(_lg)",
"                _dash_style_legend(_lg)",
```

The facet loop at `dash_render.py:15131-15214` builds `_fac_fig`, calls
`_dash_apply_scheme(_fac_fig)`, draws glyphs that pass `legend_label=`, stores
`figures[_fac_name] = _fac_fig` — and never styles the auto-legend Bokeh creates from those
labels.

### 5. Evidence — the colour key and the colour bar ignore `legend(position() ring())`

Both are added to the `"right"` panel unconditionally. Discrete key,
`dash_render.py:3240-3243`:

```python
            fig.add_layout(
                Legend(items=legend_items, title=html.escape(var_display),
                       name=_COLORVAR_LEGEND_NAME),
                "right",
            )
```

Continuous bar, `dash_render.py:3267-3271`:

```python
                fig.add_layout(
                    ColorBar(color_mapper=mapper, label_standoff=8,
                             width=12, location=(0, 0),
                             title=html.escape(var_display)),
                    "right",
                )
```

`GlyphMapper._apply_colorvar` never receives the graph's options —
`dash_render.py:2995-3001`:

```python
    def _apply_colorvar(
        self,
        fig: Any,
        renderer: Any,
        source: "ColumnDataSource",
        options: dict[str, str],
    ) -> None:
```

(`options` here is the **plot's** option dict — `colorvar()`, `colordiscrete`, `colpalette()`
— not the graph's `legend()`.) And the post-pass that *does* know the clock position
deliberately excludes the colour key, `dash_render.py:8990-8998`:

```python
        # when the colour key is the only legend would silently reinstate a
        # Bokeh-default legend on a themed plot region, which is a bug this
        # file already fixed once.
        _cv_legends = [l for l in fig.legend
                       if str(getattr(l, "name", "") or "")
                       == _COLORVAR_LEGEND_NAME]
        _plot_legends = [l for l in fig.legend if l not in _cv_legends]
```

with `_COLORVAR_LEGEND_NAME = "_dash_clegend"` at `dash_render.py:595`. From `REMAINING.md`,
Appendix B:

> Honour legend(position() ring()) for the colorvar colour key and the continuous ColorBar;
> both are hardcoded to the "right" panel. GlyphMapper._apply_colorvar does not receive
> graph_options, so this needs either a plumbing change or a post-pass in _rebuild_legend
> (which today deliberately filters _dash_clegend legends out of the clock-position move).

### 6. Evidence — the continuous ramp has no recorded disposition

The discrete path already takes the scheme (`dash_render.py:3192-3194`,
`if not palette_key and getattr(self.scheme, "p_colors", None): pal_list = list(self.scheme.p_colors)`).
The continuous path does not — `dash_render.py:3253-3254`:

```python
            pal_name = self._PALETTE_MAP.get(palette_key or "viridis", "Viridis256")
            palette  = getattr(_bk_palettes, pal_name, _bk_palettes.Viridis256)
```

From `REMAINING.md`, Appendix B:

> Decide and record what the continuous colorvar() ramp should be. The task names Viridis256
> as ignoring the scheme but prescribes a replacement only for the discrete case, and no
> Stata scheme declares a continuous ramp — so this needs a written disposition (keep Viridis
> as the documented default, or synthesise a ramp from p_colors) rather than a silent
> leave-as-is. *Where:* `dash_render.py:3253-3254 …`, `.ultraplan/CHANGELOG.md` (S11 section
> at :396-500, whose "Consumed now" table lists only the discrete palette)

### 7. Evidence — `colorvar()` has no branch in the server renderer

From `REMAINING.md`, Appendix C:

> colorvar() has no implementation whatsoever in ServerAppBuilder, so the task's whole
> 'colour mapping' clause — discrete palette from scheme.p_colors, continuous ramp,
> colour-key placement — is unmet in `dash serve`, and a served dashboard silently drops the
> option entirely (no mapper, no colour key, no colour bar). dash.ado parses and serializes
> it (dash.ado:564-565, :673, :865), so the key is written and never read on this path.

Confirmed at `ca5fe35`: the string `colorvar` occurs **0** times anywhere after
`dash_render.py:12265` (`class ServerAppBuilder`), while `dash.ado` writes it:

```
dash.ado:564:    if `"`cv'"' != "" & `"`colorvar'"' == "" local colorvar `"`cv'"'
dash.ado:673:    sreturn local colorvar         `"`colorvar'"'
dash.ado:865:                   blcolor bfcolor jitter jseed yaxis xaxis colorvar colpalette ///
```

This is the "written and never read" defect class the plan exists to remove, on the `dash
serve` path.

### 8. Evidence — residual alpha literals the task's sweep missed

From `REMAINING.md`, Appendix B:

> Residual alpha literals the task's sweep missed: map_rarea still fills at a hardcoded 0.5,
> and the server's by()-facet and total histogram paths fill at a hardcoded 0.6 instead of
> _SCHEME_BAR_ALPHA.

`dash_render.py:4947-4950`:

```python
        _varea_kwargs: dict = dict(x=xvar, y1=y1var, y2=y2var, source=source,
                                    fill_color=self.scheme.default_color(color_idx, "area"),
                                    fill_alpha=0.5,
                                    legend_label=y1var)
```

`dash_render.py:15157` (emitted facet histogram) and `:15258` (the `by(total)` twin):

```python
"                    _fac_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6, legend_label=_hvar)"
"                    _tot_fig.quad(top='top', bottom=0, left='left', right='right', source=_hsrc, fill_color=color, fill_alpha=0.6, legend_label=_hvar)"
```

The named constants they should use are emitted two lines apart at
`dash_render.py:12601-12602` (`_SCHEME_BAR_ALPHA = %r`, `_SCHEME_AREA_ALPHA = %r`), and the
sibling facet `area` branch at `:15151` already passes `fill_alpha=_SCHEME_AREA_ALPHA` — so
the histogram quad is the odd one out on its own line of the same chain. Standalone parallels:
`map_area` uses `fill_alpha=self.scheme.area_alpha` (`:3635`), the bar paths use
`self.scheme.bar_alpha` (`:3735`, `:4683`), and `map_scatter` uses `self.scheme.fill_alpha`
(`:3472`). Scheme defaults: `bar_alpha` and `area_alpha` are both
`self._intensity("intensity bar"/"intensity area", 0.8)` at `dash_render.py:2039-2040`.

### 9. Evidence — the entire `<style>` block is swallowed in the Bootstrap layout

From `REMAINING.md`, Appendix C (verbatim):

> The bs/Bootstrap layout emits a MALFORMED head whenever the dashboard contains any widget,
> and the entire <style> block carrying _DASH_GRID_CSS + the scheme's css_block() (plus the
> CSP and viewport metas) is swallowed as script text and never applied. Root cause: the head
> is lifted from bokeh's file_html() with a non-greedy regex, and bokeh-widgets.min.js
> contains a literal '</head>' inside a JS string, so the match cuts the head in the middle
> of that inline <script>. Fix the extraction (match to the LAST </head>, or use bokeh's own
> template/json_item instead of string surgery) and assert <script>/</script> balance in the
> emitted document. This is the task's central deliverable — 'align them so the block
> applies' — still not true in a browser, and the .db-kpi-card rule the task added can ONLY
> appear in a document that has a KPI card, i.e. exactly the document where the whole block
> is destroyed.

The extraction, `dash_render.py:10783-10786`:

```python
        _dummy_col = column(*all_models, sizing_mode="stretch_width")
        _dummy_html = file_html(_dummy_col, INLINE, title=title_text or "dash")
        _head_m = re.search(r"(?s)<head>(.*?)</head>", _dummy_html)
        _extracted_head = _head_m.group(1) if _head_m else ""
```

The consumer, `dash_render.py:10892-10902`:

```python
        html_str = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            f"{_extracted_head}\n"
            f"  {_CSP_META}\n"
            "  <style>\n"
            f"{_DASH_GRID_CSS}\n"
            f"{scheme_css_block}\n"
            "  </style>\n"
            "</head>\n"
```

Re-measured against the installed Bokeh at `ca5fe35`, confirming the root cause the auditor
named:

```
bokeh-widgets.min.js  378284 bytes  count of literal '</head>': 1
bokeh.min.js         1264808 bytes  count of literal '</head>': 0
```

So the defect is conditional on the widgets bundle being inlined — i.e. on the model tree
containing a widget — which is why a plain two-figure dashboard looks fine and a dashboard
with a filter `Select`, a header `Div` or a KPI card does not. `INLINE` resources are chosen
deliberately here ("`file_html()` with INLINE selects only the resource bundles needed by
this specific model tree (~1.5 MB vs ~3.5 MB from `render_js()`)", `dash_render.py:10779-10781`),
so the fix is in the extraction, not in the resource mode.

### 10. Evidence — the one rule that could bite is beaten by an inline style

`css_block()` emits, at `dash_render.py:2216-2219`:

```python
            f"  .db-title {{ color: {tc}; font-size: {hs}; }}\n"
            f"  .db-subtitle {{ color: {tc}; font-size: {ts}; }}\n"
            f"  .db-kpi-card {{ background-color: {lbg}; "
            f"border-color: {lbc}; }}\n"
```

and the card it names carries its own `style=` attribute, `dash_render.py:10484-10496`:

```python
        color    = _resolve_kpi_color(kpi_def.get("color", ""), "#212529")
        bgcolor  = _resolve_kpi_color(kpi_def.get("bgcolor", ""), "#f8f9fa")

        html_content = f"""
<div class="db-kpi-card" style="background:{bgcolor}; border-radius:8px;
            padding:20px; text-align:center; border:1px solid #dee2e6;
            min-width:160px; min-height:110px;">
```

An inline declaration beats a stylesheet rule, so `legend_bg_color` / `legend_border_color`
have no visible effect on a KPI card. From `REMAINING.md` (Appendix B, restated more sharply
in Appendix C):

> Make the .db-kpi-card rule actually apply. The class-name fix landed, but the KPI div
> carries inline `style="background:...; border:1px solid #dee2e6"`, and an inline
> declaration beats a stylesheet rule, so legend_bg_color / legend_border_color still have no
> visible effect on KPI cards. Either drop the unconditional inline background/border
> defaults (emit them only when the user passed bgcolor()) or move the scheme values into the
> inline style.

> The `.db-kpi-card` rule css_block() emits is overridden by the KPI div's inline style, so
> the selector test passes while the scheme value still does nothing. … The auditor named
> this in the report headline but it is absent from the itemised backlog, so it is not in
> REMAINING.md.

There are **three** copies of that markup, and they must not drift:

| site | what it is |
|---|---|
| `dash_render.py:10487-10496` | `DashRenderer._build_kpi_html` — the initial card |
| `dash_render.py:7328-7334` | the CustomJS that rebuilds the card text after a filter/brush |
| `dash_render.py:12976-12980` | the emitted `_dash_kpi_card` in `ServerAppBuilder` |

All three hardcode `border:1px solid #dee2e6` and default `background` `#f8f9fa`.

### 11. Evidence — the guards cannot see any of the above

**(a) The selector guard compares strings, not a DOM**, and it is satisfied by markup that the
browser never styles. `test/test_scheme_consumption.py:265-293`:

```python
    @pytest.mark.parametrize("layout", ["auto", "bs"])
    def test_every_selector_matches_a_class_the_html_emits(self, layout):
        ...
        block = dr.scheme.css_block()
        selectors = set(re.findall(r"\.([A-Za-z][\w-]*)\s*\{", block))
        assert selectors, "css_block() emits no class selectors at all"
        emitted = set(re.findall(r'class="([^"]*)"', out))
        emitted |= set(re.findall(r'class=\\+"([^"\\]+)\\+"', out))
        classes = {c for group in emitted for c in group.split()}
        missing = sorted(s for s in selectors if s not in classes)
```

A class string inside a `<script>` element that the browser parses as script text still
matches this regex. So does a class on a Div whose markup Bokeh 3 renders inside a shadow
root (Phase 24's item 4). And a rule beaten by an inline style matches it too.

**(b) The guard drives only `DashRenderer`.** The `_render` helper at
`test/test_scheme_consumption.py:60-90` constructs `DashRenderer(sp, dp, op)` and returns
`dr.render()`; nothing in the file builds a `ServerAppBuilder`. From `REMAINING.md`:

> Extend the CSS selector test to the server-emitted document. `_render()` in the test only
> drives DashRenderer, so the mechanical guard the task installed cannot see the server's
> markup at all.

> No test anywhere exercises the server half of 11-04. The alphas, minor_grid_color and
> legend chrome were landed in the emitted app with zero coverage, which is exactly how the
> 11pt/10pt legend split above survived.

**(c) The "no key is discarded" check is a hand-written list of 7 names and a source count.**
`test/test_scheme_consumption.py:462-476`:

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

From `REMAINING.md`:

> Replace the hand-written attribute list in test_the_key_is_read_somewhere with a real
> enumeration of everything _init_properties assigns, so the check is mechanical as the
> `<done>` demands. The current list covers 7 of 34 names and omits every key that is
> actually dead.

Re-measured at `ca5fe35`: `SchemeParser._init_properties` (`dash_render.py:1953`) assigns
exactly **34** attributes —

```
background_color plotregion_color legend_bg_color legend_border_color grid_color
minor_grid_color title_color axis_line_color p_colors p_line_colors p_bar_colors
p_mark_colors p_symbols p_lineplot_patterns p_line_patterns p_lineplot_colors
default_line_width grid_line_width fill_alpha bar_alpha area_alpha text_font_size
heading_font_size axis_title_font_size tick_label_font_size note_font_size
graphsize_x graphsize_y draw_major_hgrid draw_major_vgrid symbolsize marker_size
legend_position legend_cols
```

— and the parametrize list names 7 of them, none of which is one of the keys under
suspicion.

**(d) The constraint on how item 2 may be written.** `REMAINING.md` records a refutation that
an attribute-level enumeration would trip over:

> **11-04 · `graphsize_x` / `graphsize_y` are not dead** (refuted twice, independently). They
> are read by *string*, not by attribute — `getattr(self.scheme, "graphsize_x", None)` at
> `dash_render.py:9244-9245` inside `_resolve_aspect_ratio`, whose result becomes
> `fig_kwargs["aspect_ratio"]`. Measured on rendered figures: `stcolor` → 1.6667 (scheme
> 7.5/4.5), `economist` → 1.0 (2.2/2.2), `s2color` → 1.375 (5.5/4.0). An attribute-level
> count cannot see this, which is the methodological trap — and the one Appendix A's own
> enumeration fell into before being redone.

The companion Appendix C item that states this as a correction ("the enumerated replacement …
must NOT keep the current `code.count(f".{attr}") >= 2` heuristic … produces four false
failures") is **Phase 23's item 8**. Item 2 in this phase must be written to satisfy it.

---

## Epics

| Epic | Goal (one line) | Items |
|---|---|---|
| **25.A — Legend chrome, placement and the colour key** | Every legend in either renderer — plain, faceted, and the colorvar colour key/colour bar — carries the scheme's chrome and lands where `legend(position() ring())` says. | 1, 8, 9, 14 |
| **25.B — Colour mapping and fill fidelity** | `colorvar()` works in `dash serve`, the continuous ramp has a written disposition, and no glyph fills at a literal alpha where the scheme declares one. | 5, 6, 15 |
| **25.C — CSS delivery and mechanical guards** | The scheme's stylesheet survives the head splice, actually wins against the markup it styles, and is guarded by tests that assert against a rendered model in **both** renderers. | 2, 3, 4, 7, 10, 11, 12, 13 |

---

## User stories

### Epic 25.A — Legend chrome, placement and the colour key

**US-25.A1 — the `dash serve` operator.**
*As a `dash serve` operator, I want a served legend to carry the same background, border,
label size, placement and column count as the saved HTML, so that the dashboard I serve and
the dashboard I email are the same dashboard.*

- **Given** a spec whose scheme declares a legend clock position and a column count,
  **when** the emitted app styles a legend via `_dash_style_legend`,
  **then** the legend's `location` is the anchor the clock position maps to (not the raw
  integer), `ncols` is the scheme's column count, and no exception is raised or swallowed.
- **Given** a scheme whose clock position is unmappable or missing,
  **when** `_dash_style_legend` runs,
  **then** `ncols`, the background, the border and the label size are still applied — one bad
  value cannot discard the rest.
- **Given** the same spec rendered standalone and served,
  **when** the two legends are compared,
  **then** background, border colour, label font size, anchor and `ncols` agree.

**US-25.A2 — the dashboard viewer, faceted panels.**
*As a dashboard viewer looking at a `by()`-faceted served dashboard, I want every panel's
legend to look like every other panel's, so that the facets read as one figure.*

- **Given** a served spec with `by(foreign)` and two series,
  **when** the facet loop builds each `_fac_fig` and Bokeh creates its auto-legend,
  **then** that legend has been through `_dash_style_legend`, and its background/border/label
  size match the unfaceted figure's in the same document.
- **Given** a `by(..., total)` spec, **when** the `by(total)` panel is built, **then** the
  same is true of its legend.

**US-25.A3 — the Stata user pasting a `twoway` command with a colour key.**
*As a Stata user who wrote `scatter mpg weight, colorvar(rep78) legend(position(6) ring(1))`,
I want the colour key to move to the bottom like any other legend, so that the option I pasted
means what it means in Stata.*

- **Given** a graph with `colorvar()` and `legend(position(6))`,
  **when** the standalone renderer assembles the figure,
  **then** the `_dash_clegend` Legend is laid out below the plot, not in the right panel.
- **Given** `legend(position(3) ring(0))`,
  **when** the figure is assembled,
  **then** the colour key is inside the plot region at `center_right`, per `_CLOCK_INSIDE`.
- **Given** a continuous `colorvar()` with `legend(position(12))`,
  **when** the figure is assembled,
  **then** the `ColorBar` is in the `above` panel.
- **Given** no `legend()` option at all,
  **when** the figure is assembled,
  **then** the colour key and colour bar stay in the `"right"` panel — today's behaviour is
  the default, not a regression.

### Epic 25.B — Colour mapping and fill fidelity

**US-25.B1 — the `dash serve` operator, colour mapping.**
*As a `dash serve` operator, I want `colorvar()` to colour the served points and draw its key,
so that a served dashboard does not silently discard an option `dash.ado` accepted and
serialized.*

- **Given** a spec with `colorvar(rep78) colordiscrete`,
  **when** the emitted app builds the document,
  **then** the figure carries a `CategoricalColorMapper` whose palette intersects
  `scheme.p_colors`, and a Legend named `_dash_clegend`.
- **Given** a spec with a continuous `colorvar(price)`,
  **when** the emitted app builds the document,
  **then** the figure carries a `LinearColorMapper` and a `ColorBar`.
- **Given** a plot type other than `scatter` that supports `colorvar()` in standalone mode,
  **when** the same spec is served,
  **then** the served figure's colour treatment matches the standalone figure's.

**US-25.B2 — the package maintainer, ramp policy.**
*As a package maintainer, I want the continuous ramp decision written down, so that the next
auditor reads a disposition instead of finding a hardcoded `Viridis256` and reopening the
question.*

- **Given** the S11 section of `.ultraplan/CHANGELOG.md`,
  **when** a reader looks for the continuous `colorvar()` ramp,
  **then** they find a named decision (keep `Viridis256` as the documented default, or
  synthesise from `p_colors`), the reason, and the code line it governs.
- **Given** the shipped help,
  **when** a user looks up `colpalette()`,
  **then** the documented default for the continuous case matches
  `_PALETTE_MAP.get(palette_key or "viridis", "Viridis256")`.

**US-25.B3 — the dashboard viewer, fills.**
*As a dashboard viewer, I want a range-area band and a faceted histogram to use the scheme's
fill intensity, so that one figure is not lighter than its neighbour for no reason.*

- **Given** a scheme whose `area_alpha` is 0.8, **when** `rarea` is drawn, **then** the
  `VArea` glyph's `fill_alpha` is 0.8, not 0.5.
- **Given** a served `by()` histogram, **when** the facet quad is drawn, **then** its
  `fill_alpha` is `_SCHEME_BAR_ALPHA`, not 0.6 — and the same for the `by(total)` panel.

### Epic 25.C — CSS delivery and mechanical guards

**US-25.C1 — the dashboard viewer, page chrome.**
*As a dashboard viewer opening a saved `layout(bs)` dashboard that has a filter and a KPI, I
want the scheme's colours and the grid CSS to actually apply, so that the file looks like the
scheme I chose.*

- **Given** a `layout(bs)` spec with a KPI and a filter widget,
  **when** the HTML is written,
  **then** the document's `<script>`/`</script>` tags are balanced and the `<style>` element
  containing `css_block()` is a real element in `<head>`, not text inside a script.
- **Given** the same document, **when** it is parsed, **then** the scheme's
  `background_color` reaches `body`.

**US-25.C2 — the Stata user, KPI cards.**
*As a Stata user who set `scheme(economist)`, I want my KPI cards to take the scheme's card
background and border, while `bgcolor()` on a specific KPI still wins, so that precedence
works the way every other scheme value works.*

- **Given** a scheme with `legend_bg_color` and `legend_border_color` and a KPI with no
  `bgcolor()`, **when** the card is rendered, **then** the card's computed background and
  border colour are the scheme's.
- **Given** a KPI with an explicit `bgcolor(red)`, **when** the card is rendered, **then**
  that colour wins over the scheme's.
- **Given** a filter that changes the KPI value, **when** the CustomJS rebuilds the card,
  **then** the card keeps the same background and border it had before the rebuild.
- **Given** the same KPI served by `dash serve`, **when** the card is built by
  `_dash_kpi_card`, **then** it matches the standalone card.

**US-25.C3 — the package maintainer, guards.**
*As a package maintainer, I want the 11-04 guards to fail when the behaviour breaks rather
than when a string moves, so that "no parsed scheme key is discarded, and the check is
mechanical" is a fact and not a slogan.*

- **Given** `SchemeParser._init_properties`,
  **when** the key-consumption test runs,
  **then** it enumerates all 34 assigned attributes mechanically — no hand-written list — and
  counts string-literal reads (`getattr(..., "name")`, `_SCHEME_CHROME['name']`) as
  consumption.
- **Given** the emitted server document,
  **when** the CSS guard runs,
  **then** it asserts the server's markup as well as the standalone's.
- **Given** the three alphas, `minor_grid_color` and the server legend chrome,
  **when** the guards run,
  **then** each is asserted against a rendered Bokeh model, not against a source count.

---

## Business requirements

| ID | Requirement | Testable as |
|---|---|---|
| **BR-25.1** | A legend styled by the scheme in `dash serve` receives every chrome value the scheme declares; no single unusable value may discard the others. | Build and exec an app on each shipped scheme; assert background, border, label size, anchor and `ncols` on a real `Legend`. |
| **BR-25.2** | The standalone and served renderers produce legends whose chrome and placement agree for the same spec. | Parity assertion in `test/test_mode_parity.py` / `test/test_server_legend.py`. |
| **BR-25.3** | `legend(position() ring())` governs the placement of the `colorvar()` colour key and the continuous colour bar exactly as it governs a plot legend; with no `legend()` option both keep the `"right"` panel. | Render with `position(6)`, `position(3) ring(0)`, `position(12)`, and with no option; assert the layout panel/anchor each time. |
| **BR-25.4** | Every legend in a served document is styled, including the `by()` and `by(total)` facet panels. | Serve a faceted spec; assert chrome on every `Legend` reachable from the document roots. |
| **BR-25.5** | `colorvar()` produces the same colour mapping, colour key and colour bar under `dash serve` as it does standalone, or is reported as unsupported — it may not be silently dropped. | Build both documents from one spec; compare mapper class, palette and key/bar presence. |
| **BR-25.6** | The continuous `colorvar()` ramp has a recorded, dated disposition in `.ultraplan/CHANGELOG.md`, and the help matches the code. | `test/test_help_conformance.py` assertion plus a CHANGELOG entry. |
| **BR-25.7** | No glyph fill alpha is a literal where the scheme declares the value: `rarea` takes the scheme's area intensity, faceted and total histograms take the scheme's bar intensity. | Rendered-model assertions in both renderers. |
| **BR-25.8** | Every saved dashboard is a well-formed HTML document: balanced `<script>` elements, and the `<style>` element carrying `_DASH_GRID_CSS` + `css_block()` present in `<head>` as an element. | Structural assertions over the emitted text for both layouts, with and without widgets. |
| **BR-25.9** | The scheme's card background and border reach a KPI card in all three emitters (initial render, CustomJS rebuild, served app), with an explicit `bgcolor()` still winning. | Three assertions, one per emitter, plus a precedence case. |
| **BR-25.10** | The "no parsed key is discarded" check enumerates `SchemeParser._init_properties` mechanically, covers all 34 attributes, and recognises string-literal reads. | Introspection-driven parametrize; a new key added to `_init_properties` with no consumer must fail the suite. |
| **BR-25.11** | Every scheme-consumption guard that exists for `DashRenderer` has a `ServerAppBuilder` arm. | Test-file structure: a `_render_server()` helper used by the same test bodies. |
| **BR-25.12** | Each behaviour fixed in this phase has a regression test that fails before the fix and passes after (CLAUDE.md rule 8), and each new or changed function has a unit test (rule 4). | The test plan below, with the named mutation for each test. |

---

## Technical requirements

### Epic 25.A — Legend chrome, placement and the colour key

**TR-25.1 — Translate the clock position in the emitted `_dash_style_legend`.**
In `ServerAppBuilder` (`dash_render.py:12653-12667`), the emitted function must map
`_SCHEME_CHROME['legend_position']` (a Stata clock **integer**, 1–12, parsed at
`dash_render.py:2086-2088`) through a side/anchor table before assignment. Emit the same two
tables the standalone renderer uses at `dash_render.py:9044-9056` — `_CLOCK_SIDE`
(`11,12,1 → above`; `2,3,4 → right`; `5,6,7 → below`; `8,9,10 → left`) and `_CLOCK_INSIDE`
(`11 → top_left`, `12 → top_center`, `1,2 → top_right`, `3 → center_right`,
`4,5 → bottom_right`, `6 → bottom_center`, `7,8 → bottom_left`, `9 → center_left`,
`10 → top_left`) — as module-level constants in the generated app so the two renderers cannot
drift. A scheme carries no `ring()`, so the scheme default uses the **side** table (the panel
form), leaving `_CLOCK_INSIDE` for an explicit `legend(ring(0))`.

**TR-25.2 — Split the try so one bad value cannot discard the rest.**
Each assignment in `_dash_style_legend` gets its own guarded statement (or the function
applies values through a small helper that catches per key). The `except` must name the
specific exceptions, and must not remain a blanket wrapper around the whole body. `lg.ncols =
int(_c['legend_cols'])` must execute whether or not the location assignment succeeded. Emit a
one-line comment recording why (a swallowed `ValueError` on `Legend.location` is what made
`legend_cols` look unconsumed).

**TR-25.3 — Give the standalone chrome loop the two placement keys.**
`DashRenderer._rebuild_legend` (`dash_render.py:9062-9068`) currently applies
`legend_bg_color`, `legend_border_color` and `text_font_size`. Add the scheme's
`legend_position` (through `_CLOCK_SIDE`, already in scope at `:9044`) and `legend_cols` as
**defaults applied before** the user's `legend()` parsing at `dash_render.py:9070+`
(`m_pos = re.search(r"\b(?:position|pos)\s*\(\s*(\d+)\s*\)", ...)`), so an explicit
`legend(position())`/`legend(cols())` still wins — the same precedence the existing chrome
comment states ("applied BEFORE the user's `legend()` options so an explicit size() still
wins").

**TR-25.4 — Style the faceted legends in server mode.**
In the emitted facet loop (`dash_render.py:15131-15214`) and its `by(total)` twin, after the
facet figure's glyphs are drawn and Bokeh's auto-legend exists, call `_dash_style_legend` on
it — mirroring the main loop's pair at `dash_render.py:14955-14961`
(`fig.add_layout(_lg)` / `_dash_style_legend(_lg)`). Where the facet path relies on Bokeh's
implicit legend (built from `legend_label=` kwargs), reach it through `_fac_fig.legend` rather
than a local name. If Phases 6–7 have already routed the facet loops through
`_expand_by_groups` / `GlyphMapper`, apply this at the single unified site instead of the two
copies, and say so in the commit message.

**TR-25.5 — Honour `legend(position() ring())` for the colour key and the colour bar.**
Two viable mechanisms; pick one and record it:

1. **Plumbing.** Extend `GlyphMapper._apply_colorvar` (`dash_render.py:2995-3001`) with an
   optional `graph_opts` parameter and pass the graph's option dict from the call site in
   `map_scatter` (`dash_render.py:3480`). Placement is then computed where the `Legend` and
   `ColorBar` are constructed (`:3240-3243`, `:3267-3271`).
2. **Post-pass.** In `DashRenderer._rebuild_legend`, keep the existing `_dash_clegend`
   exclusion for the *item rebuild* (`dash_render.py:8990-8998` — the comment there explains
   why: rebuilding items when the colour key is the only legend reinstates a Bokeh-default
   legend on a themed plot region) but add an explicit **move** pass for
   `_cv_legends` and for any `ColorBar` on the figure, using the same clock tables.

Either way: the default with no `legend()` option remains `"right"`; `ring(0)` uses
`_CLOCK_INSIDE` for the Legend; a `ColorBar` has no inside-anchor form, so `ring(0)` on a
continuous key falls back to the side panel and the behaviour is documented. `ColorBar`'s
`location=(0, 0)` argument at `:3269` is an offset within its panel and must not be confused
with the panel choice.

### Epic 25.B — Colour mapping and fill fidelity

**TR-25.6 — `rarea` takes the scheme's area intensity.**
`GlyphMapper.map_rarea` (`dash_render.py:4947-4950`) passes `fill_alpha=0.5`. Replace with
`self.scheme.area_alpha` — the key `map_area` already uses at `dash_render.py:3635`, parsed as
`self._intensity("intensity area", 0.8)` at `:2040` — unless the maintainer records a reason
to use `fill_alpha`/`bar_alpha` instead; whichever is chosen, the standalone value and the
emitted app's constant must be the same key. An explicit `fintensity()`/`fcolor()` option must
still win.

**TR-25.7 — Faceted and total histograms take `_SCHEME_BAR_ALPHA`.**
The emitted quads at `dash_render.py:15157` (facet) and `:15258` (`by(total)`) hardcode
`fill_alpha=0.6`. Replace with `_SCHEME_BAR_ALPHA`, emitted at `dash_render.py:12601`
(`"_SCHEME_BAR_ALPHA = %r" % (sch.bar_alpha,)`), matching the sibling `area` branch at
`:15151` which already passes `_SCHEME_AREA_ALPHA`. Note for the implementer: the same two
emitted lines pass no `line_color` at all, which is a separate faceted-divergence item owned
by Phase 6/7 — do not silently fold that fix in here without saying so.

**TR-25.8 — Record the continuous-ramp disposition.**
`dash_render.py:3253-3254` resolves `pal_name = self._PALETTE_MAP.get(palette_key or
"viridis", "Viridis256")`. `_PALETTE_MAP` (`dash_render.py:2971-2992`) offers 21 keys —
`viridis magma inferno plasma cividis turbo blues greens reds greys oranges purples spectral
rdylgn rdbu category10 category20 set1 set2 set3 paired`. No shipped `.scheme` file declares a
continuous ramp, so there is nothing to consume; the deliverable is a written decision in the
S11 section of `.ultraplan/CHANGELOG.md` (`:396-500`, whose "Consumed now" table currently
lists only the discrete palette), naming the code line it governs, plus a help sentence for
`colpalette()`. If the decision is to synthesise from `p_colors`, it must state the
interpolation and the number of steps; if it is to keep `Viridis256`, it must say why a
perceptually uniform ramp is preferred to a categorical cycle for a continuous variable.

**TR-25.9 — Implement `colorvar()` in `ServerAppBuilder`.**
`colorvar` occurs 0 times after `dash_render.py:12265`. `dash.ado` writes the key
(`dash.ado:564-565`, `:673`, `:865`), so the spec carries it. The emitted app already contains
the implementation: `ServerAppBuilder` copies `OptionTranslator`, `SchemeParser` and
`GlyphMapper` **by `inspect.getsource`** (`dash_render.py:12408-12409`) and instantiates
`_DASH_MAPPER = GlyphMapper(scheme=_DASH_SCHEME)` at `:12432`, so `_apply_colorvar` and
`_PALETTE_MAP` are *defined* in the generated app. Requirements:

1. Measure first: `_apply_colorvar` is reached from `GlyphMapper.map_scatter`
   (`dash_render.py:3480`), and the emitted scatter branch delegates to
   `_DASH_MAPPER.map_scatter` at `dash_render.py:14090`. Build a served document from a
   `colorvar()` spec and record what it actually draws today (mapper? key? bar? colour
   column present in the `ColumnDataSource`?). Put the measurement in the commit message.
   Whatever it shows, the item's substance stands: there is no colorvar branch, no
   non-scatter path, no faceted path and no test.
2. Every plot type that supports `colorvar()` standalone must behave the same served —
   which, for all but `scatter`, means it arrives with the 15-03 delegation (Phases 5–7).
3. The served colour key must be named `_dash_clegend` (`dash_render.py:595`) so the
   placement work in TR-25.5 and the legend-rebuild exclusion apply identically in both
   renderers.
4. The served data payload must carry the colour variable's column; if it does not, that is
   part of this item, not a separate one.

### Epic 25.C — CSS delivery and mechanical guards

**TR-25.10 — Fix the head extraction.**
`dash_render.py:10785` uses `re.search(r"(?s)<head>(.*?)</head>", _dummy_html)`. The inlined
`bokeh-widgets.min.js` contains one literal `</head>` inside a JS string (measured:
`bokeh-widgets.min.js` 378,283 bytes, 1 occurrence; `bokeh.min.js` 1,264,807 bytes, 0
occurrences), so the non-greedy match truncates the head mid-`<script>`. Acceptable fixes, in
order of preference:

1. Use Bokeh's own machinery — `json_item()` or a Jinja template passed to `file_html()` — and
   stop doing string surgery on a generated document.
2. Match to the **last** `</head>` (greedy `(?s)<head>(.*)</head>`, or `rfind`), which is
   correct because the real head close is the last one before `<body>`.

Whichever is chosen, `_extracted_head` must be validated before use: balanced
`<script>`/`</script>` within the extracted text, and a non-empty result (today
`_head_m` failing yields `""` silently). The consumer at `dash_render.py:10892-10902` — which
appends `_CSP_META`, `_DASH_GRID_CSS` and `scheme_css_block` — needs no change once the head
is whole, but the CSP meta must still precede the inline `<style>`.

**TR-25.11 — Make `.db-kpi-card` win, in all three emitters.**
`css_block()` emits `.db-kpi-card { background-color: {lbg}; border-color: {lbc}; }` at
`dash_render.py:2218-2219`, where `lbg`/`lbc` are the scheme's `legend_bg_color` /
`legend_border_color`. The three markup sites are `dash_render.py:10487-10496`
(`DashRenderer._build_kpi_html`), `dash_render.py:7328-7334` (the CustomJS rebuild) and
`dash_render.py:12976-12980` (the emitted `_dash_kpi_card`). Required behaviour:

- With **no** `bgcolor()` on the KPI, the card must take the scheme's background and border —
  so the unconditional inline `background:{bgcolor}` / `border:1px solid #dee2e6` defaults
  must go, or become CSS custom properties the stylesheet rule can set.
- With an explicit `bgcolor()`, that value must win — emit it as a narrow inline property (or
  a custom-property override) rather than reinstating the blanket shorthand.
- The current defaults are `#f8f9fa` (background, via `_resolve_kpi_color(..., "#f8f9fa")` at
  `:10485`) and `#dee2e6` (border); whatever replaces them must keep those as the
  *no-scheme* fallback so an unthemed dashboard is unchanged.
- All three sites must be changed together and asserted together; the CustomJS rebuild must
  not reintroduce the inline background when a filter fires.
- Layout caveat: in `layout(auto)` the card markup is the text of a Bokeh `Div`, which Bokeh 3
  renders in a shadow root — Phase 24's item 4 attaches the scheme CSS to those Divs
  (`stylesheets=[InlineStyleSheet(css=...)]`). If that has not landed, the custom-property
  form of this fix is the one that works in both layouts.

**TR-25.12 — A mechanical key-consumption check.**
Replace `test_the_key_is_read_somewhere` (`test/test_scheme_consumption.py:462-476`). The
replacement must:

- enumerate the attributes `SchemeParser._init_properties` (`dash_render.py:1953`) assigns —
  by introspecting a constructed `SchemeParser` instance, or by parsing the method's AST for
  `self.<name> = ...` targets — so a new key added tomorrow is covered without editing the
  test (34 names today, listed in §11(c) above);
- **not** keep the `code.count(f".{attr}") >= 2` heuristic alone: per the Appendix C
  correction (Phase 23's item 8), that produces four false failures, because `graphsize_x`,
  `graphsize_y`, `legend_position` and `legend_cols` are read via
  `getattr(self.scheme, "name")` (`dash_render.py:9244-9245`) and via `_SCHEME_CHROME['name']`
  dict keys (`dash_render.py:12615-12623`, `:12683`). Count string-literal reads as
  consumption, or — better, and what the `<done>` really wants — assert behaviour: render or
  emit, then read the value back off the model.
- carry an explicit, commented allow-list for any key deliberately unconsumed, with the
  disposition and the phase that owns it, so "dead" is a decision rather than an oversight.

**TR-25.13 — Give the CSS guards a server arm.**
`test/test_scheme_consumption.py`'s `_render` helper (`:60-90`) builds only
`DashRenderer(sp, dp, op)`. Add a `_render_server()` sibling modelled on
`test/test_server_scheme.py:44-66`: write the spec and data, call
`dr.ServerAppBuilder(str(spec), str(data)).build(str(app))`, exec the module with
`importlib.util`, call `mod.make_document(Document())`, and return both the emitted app source
(for text assertions) and the built `Document` (for model assertions). Parameterise
`TestSchemeCssActuallyApplies` over renderer as it is already parameterised over layout. This
depends on Phase 24's `css_block()`-in-server work for the *selector* assertions; the
*structural* assertions (script balance, `<style>` survival) apply immediately.

**TR-25.14 — Behavioural assertions for the clauses only a source count covers.**
Add, against rendered models rather than file text:

| clause | standalone anchor | server anchor |
|---|---|---|
| `fill_alpha` | `map_scatter` at `dash_render.py:3472` (`alpha=self.scheme.fill_alpha`) | `_SCHEME_FILL_ALPHA` in the emitted app |
| `bar_alpha` | `:3735`, `:4683` | `_SCHEME_BAR_ALPHA` (`:12601`), incl. facet/total quads after TR-25.7 |
| `area_alpha` | `:3635`, plus `map_rarea` after TR-25.6 | `_SCHEME_AREA_ALPHA` (`:12602`), facet `varea` at `:15151` |
| `minor_grid_color` | `SchemeParser.apply_to_figure` at `dash_render.py:2185` (`grid.minor_grid_line_color = self.minor_grid_color`), reached via `fig.xgrid`/`fig.ygrid` | emitted `_dash_apply_scheme` at `dash_render.py:12669`, assignment at `:12683` |
| legend chrome | `_rebuild_legend` `:9062-9068` | `_dash_style_legend` `:12653-12667` |

**TR-25.15 — Structural guards on the emitted document.**
In `TestSchemeCssActuallyApplies`, for a spec that has **a KPI and a filter** (the case that
pulls in `bokeh-widgets.min.js`), and for both layouts:

- assert `<script>`/`</script>` balance across the whole document;
- assert the `<style>` element that contains a distinctive fragment of `css_block()` (e.g. the
  scheme's `legend_bg_color` literal) is inside `<head>` and is **not** nested inside a
  `<script>` element — a scan that tracks whether the offset falls between a `<script>` and
  its matching `</script>`;
- assert the header/KPI Divs carry a `stylesheets=` entry where Phase 24's Div fix requires
  one;
- keep the existing `test_the_style_elements_are_balanced_and_not_nested`
  (`test/test_scheme_consumption.py:244-262`) — the new assertions are additional, not a
  replacement.

A rendered-DOM arm (headless browser) is the ideal form of this guard; if the dependency is
not acceptable, the string-structure assertions above are the stated minimum in
`REMAINING.md`.

---

## Work items

Every item below is reproduced with the text, tags and *Where* it was handed over with.
`[kind · renderer · effort]`; **B** = Appendix B, **C** = Appendix C (the adversarial pass).
All 15 originate from ultraplan task **11-04**.

### Item 1 — Colour-key and colour-bar placement `[functional · standalone · medium]` (B)

> Honour legend(position() ring()) for the colorvar colour key and the continuous ColorBar;
> both are hardcoded to the "right" panel. GlyphMapper._apply_colorvar does not receive
> graph_options, so this needs either a plumbing change or a post-pass in _rebuild_legend
> (which today deliberately filters _dash_clegend legends out of the clock-position move).

**Where.** `dash_render.py:3240-3243`
(`fig.add_layout(Legend(items=legend_items, ..., name=_COLORVAR_LEGEND_NAME), "right")`),
`dash_render.py:3267-3271` (`fig.add_layout(ColorBar(...), "right")`),
`dash_render.py:2995-3001` (`GlyphMapper._apply_colorvar` signature — no graph_opts),
`dash_render.py:8996-8998` (`_plot_legends` filter in `DashRenderer._rebuild_legend`).
**Evidence.** §5 above. **Requirement.** TR-25.5. **Epic.** 25.A.

### Item 2 — Mechanical enumeration for the key-consumption test `[deliverable · n/a · small]` (B)

> Replace the hand-written attribute list in test_the_key_is_read_somewhere with a real
> enumeration of everything _init_properties assigns, so the check is mechanical as the
> <done> demands. The current list covers 7 of 34 names and omits every key that is actually
> dead.

**Where.** `test/test_scheme_consumption.py:462-476`
(`@pytest.mark.parametrize("attr", [...]); def test_the_key_is_read_somewhere`).
**Evidence.** §11(c) and §11(d) above — including the refutation that forbids a naive
attribute count. **Requirement.** TR-25.12. **Epic.** 25.C.

### Item 3 — Server arm for the CSS selector test `[deliverable · server · small]` (B)

> Extend the CSS selector test to the server-emitted document. `_render()` in the test only
> drives DashRenderer, so the mechanical guard the task installed cannot see the server's
> markup at all.

**Where.** `test/test_scheme_consumption.py:60-90` (`_render` helper) and `:242-296`
(`TestSchemeCssActuallyApplies`) — add a ServerAppBuilder arm.
**Evidence.** §11(b) above. **Requirement.** TR-25.13. **Epic.** 25.C.
**Note.** Its selector assertions depend on Phase 24's item 3 (`css_block()` is never called
in `dash serve`); the structural assertions do not.

### Item 4 — Make the `.db-kpi-card` rule apply `[functional · both · small]` (B)

> Make the .db-kpi-card rule actually apply. The class-name fix landed, but the KPI div
> carries inline `style="background:...; border:1px solid #dee2e6"`, and an inline
> declaration beats a stylesheet rule, so legend_bg_color / legend_border_color still have no
> visible effect on KPI cards. Either drop the unconditional inline background/border defaults
> (emit them only when the user passed bgcolor()) or move the scheme values into the inline
> style.

**Where.** `dash_render.py:10487-10490` (`_build_kpi_html`,
`<div class="db-kpi-card" style="background:{bgcolor}; ... border:1px solid #dee2e6;">`),
`dash_render.py:7328-7331` (the CustomJS rebuild), `dash_render.py:12976-12980` (the server's
`_dash_kpi_card`), rule emitted at `dash_render.py:2218-2219`.
**Evidence.** §10 above. **Requirement.** TR-25.11. **Epic.** 25.C.
**Note.** Item 10 is the Appendix C statement of the same defect; they are done together.

### Item 5 — Residual alpha literals `[functional · both · small]` (B)

> Residual alpha literals the task's sweep missed: map_rarea still fills at a hardcoded 0.5,
> and the server's by()-facet and total histogram paths fill at a hardcoded 0.6 instead of
> _SCHEME_BAR_ALPHA.

**Where.** `dash_render.py:4947-4950` (`GlyphMapper.map_rarea`, `fill_alpha=0.5`);
`dash_render.py:15157` and `15258` (emitted `_fac_fig.quad(... fill_alpha=0.6 ...)` and
`_tot_fig.quad(... fill_alpha=0.6 ...)`).
**Evidence.** §8 above. **Requirements.** TR-25.6, TR-25.7. **Epic.** 25.B.

### Item 6 — Disposition for the continuous `colorvar()` ramp `[deliverable · standalone · small]` (B)

> Decide and record what the continuous colorvar() ramp should be. The task names Viridis256
> as ignoring the scheme but prescribes a replacement only for the discrete case, and no Stata
> scheme declares a continuous ramp — so this needs a written disposition (keep Viridis as the
> documented default, or synthesise a ramp from p_colors) rather than a silent leave-as-is.

**Where.** `dash_render.py:3253-3254`
(`pal_name = self._PALETTE_MAP.get(palette_key or "viridis", "Viridis256")`),
`.ultraplan/CHANGELOG.md` (S11 section at `:396-500`, whose "Consumed now" table lists only
the discrete palette).
**Evidence.** §6 above. **Requirement.** TR-25.8. **Epic.** 25.B.

### Item 7 — Behavioural tests for the source-count-only clauses `[deliverable · both · small]` (B)

> Add behavioural tests for the clauses that only the source-count test covers: the three
> alphas reaching real glyphs, minor_grid_color reaching fig.xgrid/ygrid, and the server-side
> legend chrome. Today nothing asserts any of these against a rendered model.

**Where.** `test/test_scheme_consumption.py` (`TestNoParsedKeyIsDiscarded`, `:427-476`) — add
glyph-level and ServerAppBuilder assertions.
**Evidence.** §11(c) above; the anchors are tabulated in TR-25.14.
**Requirement.** TR-25.14. **Epic.** 25.C.

### Item 8 — The emitted `_dash_style_legend` aborts halfway `[functional · server · small]` (C)

> The emitted `_dash_style_legend` aborts halfway on every shipped scheme: it assigns the
> scheme's clock-position INT straight to `Legend.location`, Bokeh raises ValueError, and the
> bare `except` swallows it — so `lg.ncols` on the next line never executes. This sharpens the
> auditor's "legend_position/legend_cols have zero consumers": a consumer exists, it is
> reached, and it is silently self-destructing. Fix = map the clock int through a side/anchor
> table (the standalone `_CLOCK_SIDE`/`_CLOCK_INSIDE` maps at dash_render.py:9044-9056) before
> assigning, and split the try so one bad assignment cannot kill the rest. Any future scheme
> chrome appended to this block is equally unreachable.

**Where.** `dash_render.py:12653-12667` (the `_dash_style_legend` string block inside
`ServerAppBuilder`; location assignment at `:12662`, ncols at `:12664`, swallowing
`except (AttributeError, KeyError, TypeError, ValueError): pass` at `:12665-12666`). Call site:
emitted app `_dash_style_legend(_lg)`. Scheme values parsed at `dash_render.py:2086-2088`;
passed into `_SCHEME_CHROME` at `dash_render.py:12622-12623`.
**Evidence.** §3 above. **Requirements.** TR-25.1, TR-25.2. **Epic.** 25.A.
**Note.** Phase 23's item 5 is the Appendix B statement of this defect — see sequencing.

### Item 9 — `legend_position`/`legend_cols` are consumed, and the consumption is broken `[functional · both · small]` (C)

> legend_position and legend_cols are NOT unconsumed — the generated server app reads both and
> the read is broken. Fix the server's `_dash_style_legend`: map the scheme's integer clock
> position through the same `_CLOCK_SIDE`/`_CLOCK_INSIDE` tables `_rebuild_legend` uses
> (dash_render.py:9044-9056) instead of assigning the raw int to `lg.location`, and put the
> `ncols` assignment in its own try so a bad location no longer discards it. Then give the
> standalone `_rebuild_legend` the same scheme defaults, which it has never read at all.

**Where.** `dash_render.py:12622-12623` and `12661-12665` (ServerAppBuilder, emitted
`_dash_style_legend`); `dash_render.py:9062-9068` (`DashRenderer._rebuild_legend` chrome loop —
add the two keys here); clock tables to reuse at `dash_render.py:9044-9056`.
**Evidence.** §3 above. **Requirements.** TR-25.1, TR-25.2, TR-25.3. **Epic.** 25.A.

### Item 10 — The `.db-kpi-card` rule loses to the inline style `[functional · both · small]` (C)

> The `.db-kpi-card` rule css_block() emits is overridden by the KPI div's inline style, so
> the selector test passes while the scheme value still does nothing. Either drop the inline
> `background:`/`border:` shorthands from the KPI markup (keeping the per-KPI bgcolor()
> override as a narrower inline property or a CSS custom property), or have css_block() stop
> pretending to style the card. The auditor named this in the report headline but it is absent
> from the itemised backlog, so it is not in REMAINING.md.

**Where.** `dash_render.py:2218-2219` (css_block `.db-kpi-card` rule),
`dash_render.py:10487-10496` (KPI Div markup), `dash_render.py:7328-7334` (JS rebuild),
`dash_render.py:12976` (server copy).
**Evidence.** §10 above. **Requirement.** TR-25.11. **Epic.** 25.C.
**Note.** Same defect as item 4, stated from the adversarial pass; the two are one change set
with one shared regression test, and the "or have css_block() stop pretending" branch is a
real option that must be explicitly rejected in the commit message if the rule is kept.

### Item 11 — No test exercises the server half of 11-04 `[deliverable · server · medium]` (C)

> No test anywhere exercises the server half of 11-04. The alphas, minor_grid_color and legend
> chrome were landed in the emitted app with zero coverage, which is exactly how the 11pt/10pt
> legend split above survived. Add server-mode assertions (build an app with ServerAppBuilder,
> exec it, assert `_SCHEME_FILL_ALPHA`/`_SCHEME_CHROME` values and call `_dash_style_legend`
> on a real Legend) alongside the standalone ones in test/test_scheme_consumption.py.

**Where.** `test/test_scheme_consumption.py` (classes `TestNoParsedKeyIsDiscarded` at `:427`,
`TestSchemeCssActuallyApplies` at `:242`).
**Evidence.** §11(b) above. **Requirements.** TR-25.13, TR-25.14. **Epic.** 25.C.

### Item 12 — The Bootstrap head is malformed and swallows the `<style>` block `[functional · standalone · medium]` (C)

> The bs/Bootstrap layout emits a MALFORMED head whenever the dashboard contains any widget,
> and the entire <style> block carrying _DASH_GRID_CSS + the scheme's css_block() (plus the
> CSP and viewport metas) is swallowed as script text and never applied. Root cause: the head
> is lifted from bokeh's file_html() with a non-greedy regex, and bokeh-widgets.min.js
> contains a literal '</head>' inside a JS string, so the match cuts the head in the middle of
> that inline <script>. Fix the extraction (match to the LAST </head>, or use bokeh's own
> template/json_item instead of string surgery) and assert <script>/</script> balance in the
> emitted document. This is the task's central deliverable — 'align them so the block applies'
> — still not true in a browser, and the .db-kpi-card rule the task added can ONLY appear in a
> document that has a KPI card, i.e. exactly the document where the whole block is destroyed.

**Where.** `dash_render.py:10784-10786` (`_dummy_html = file_html(...)`,
`_head_m = re.search(...)`, `_extracted_head`) in `DashRenderer._assemble_layout`; consumed at
`dash_render.py:10896-10900` (`f"{_extracted_head}\n"`, `f"  {_CSP_META}\n"`,
`"  <style>\n"` + `_DASH_GRID_CSS` + `scheme_css_block`).
**Evidence.** §9 above, including the re-measured bundle counts.
**Requirement.** TR-25.10. **Epic.** 25.C.
**Security note.** `_CSP_META` is inside the swallowed region too, so this is also a
content-security-policy delivery defect, not only a cosmetic one (CLAUDE.md rule 1).

### Item 13 — The CSS guard cannot see either failure `[deliverable · standalone · medium]` (C)

> The mechanical CSS guard the task installed cannot see either failure above, because it only
> compares selector strings against class strings in the HTML source. Give it a rendered-DOM
> arm (or at minimum: assert the emitted document has balanced <script>/</script>, assert the
> <style> element containing the scheme block survives the head splice for a spec that has a
> KPI and a filter, and assert the header/KPI Divs carry a stylesheets= entry). Without this
> the task's own stated purpose — 'that test is what stops this recurring' — is unmet.

**Where.** `test/test_scheme_consumption.py:242-296` (`TestSchemeCssActuallyApplies`,
`_render` helper at `:60-90`).
**Evidence.** §11(a) above. **Requirement.** TR-25.15. **Epic.** 25.C.

### Item 14 — Faceted legends get no scheme chrome in server mode `[functional · server · small]` (C)

> In server mode a by()-faceted figure's legend never receives the scheme chrome:
> `_dash_style_legend` is called only from the main (unfaceted) plot loop, while the facet loop
> builds its figure and its auto-legend and moves on. So one dashboard serves faceted panels
> with Bokeh-default legends and unfaceted panels with the scheme's — the clause 'style the
> legend from the scheme unconditionally' is unmet on the faceted path.

**Where.** `dash_render.py:14955-14961` (the emitted `fig.add_layout(_lg)` /
`_dash_style_legend(_lg)` pair in `ServerAppBuilder`'s main plot loop) and
`dash_render.py:15131-15214` (the emitted facet loop: `_fac_fig = bokeh_figure(**_fac_kw)`,
`_dash_apply_scheme(_fac_fig)`, glyphs passing `legend_label=`,
`figures[_fac_name] = _fac_fig` — no legend styling).
**Evidence.** §4 above. **Requirement.** TR-25.4. **Epic.** 25.A.

### Item 15 — `colorvar()` is absent from `ServerAppBuilder` `[functional · server · large]` (C)

> colorvar() has no implementation whatsoever in ServerAppBuilder, so the task's whole 'colour
> mapping' clause — discrete palette from scheme.p_colors, continuous ramp, colour-key
> placement — is unmet in `dash serve`, and a served dashboard silently drops the option
> entirely (no mapper, no colour key, no colour bar). dash.ado parses and serializes it
> (dash.ado:564-565, :673, :865), so the key is written and never read on this path.

**Where.** `dash_render.py:12265` (class `ServerAppBuilder`) / `:12740`
(`_generate_app_source`) — no colorvar branch; compare `GlyphMapper._apply_colorvar` at
`dash_render.py:2995-3300`.
**Evidence.** §7 above. **Requirement.** TR-25.9. **Epic.** 25.B.
**Note.** This is the one `large` item in the phase and the one with a real dependency: after
Phases 5–7 land the `GlyphMapper` delegation, most plot types inherit `_apply_colorvar` for
free and this collapses toward `medium`.

---

## Test plan

Conventions used throughout: **rule 8** — for every defect, the regression test is written
**first** and must fail on the current tree; **rule 4** — every function added or changed gets
a unit test; **non-vacuity** — each test names the mutation that must kill it, and that
mutation is applied and reverted during development, with the observed failure pasted into the
commit message.

Test files in play (all exist today):
`test/test_scheme_consumption.py`, `test/test_server_scheme.py`, `test/test_server_legend.py`,
`test/test_colorvar_legend.py`, `test/test_server_kpi_card.py`, `test/test_kpi.py`,
`test/test_mode_parity.py`, `test/test_html_output.py`, `test/test_layout.py`,
`test/test_layout_facets.py`, and the certification scripts `test/test_server_build.cscript`,
`test/test_e2e_serve.cscript`, `test/test_e2e_kpi.cscript`, `test/test_conformance.cscript`.
The server-side helper to copy is `test/test_server_scheme.py:44-66` (`_build_doc` →
`ServerAppBuilder(...).build(app)` → `importlib.util` exec → `mod.make_document(Document())`),
plus its `_figures(doc)` walker at `:69-95`, which already handles the GridPlot
`(child, row, col)` tuple trap.

### Epic 25.A — Legend chrome, placement and the colour key

**Failing test first (items 8, 9).**
`test/test_server_legend.py::TestSchemeLegendChrome::test_the_scheme_column_count_survives_the_position`
— build a served app on a scheme that declares both `clockdir legend_position` and
`numstyle legend_cols`, exec it, build the document, find the `Legend`, assert
`lg.ncols == scheme.legend_cols` **and** `lg.location` is a valid Bokeh anchor string.
On the current tree this fails on `ncols` (the `ValueError` on the preceding line is
swallowed), which is exactly the reported defect.

**Unit tests.**

| Test | Asserts |
|---|---|
| `test_the_clock_position_maps_to_a_side` (parametrized over 1–12) | the emitted app's clock table gives the same side as `_CLOCK_SIDE` at `dash_render.py:9044-9056` |
| `test_an_unmappable_position_does_not_discard_the_rest` | with a junk `legend_position` in `_SCHEME_CHROME`, background/border/label-size/`ncols` are all still applied |
| `test_the_standalone_legend_takes_the_scheme_position` | `DashRenderer` places the legend per the scheme when no `legend()` option is given |
| `test_an_explicit_legend_position_beats_the_scheme` | `legend(position(6))` wins over the scheme's clockdir; same for `legend(cols(2))` vs `legend_cols` |
| `test_the_colour_key_moves_with_legend_position` (`test/test_colorvar_legend.py`) | the `_dash_clegend` Legend is in the `below` panel for `position(6)`; inside at `center_right` for `position(3) ring(0)` |
| `test_the_colour_bar_moves_with_legend_position` | the `ColorBar` is in the `above` panel for `position(12)` |
| `test_the_colour_key_defaults_to_the_right_panel` | with no `legend()` option, both stay `"right"` |
| `test_a_faceted_served_legend_carries_the_scheme_chrome` (`test/test_server_legend.py`) | every `Legend` reachable from the document roots of a `by(foreign)` served spec has the scheme background/border/label size — and the `by(..., total)` panel too |

**Integration / parity.**
`test/test_mode_parity.py` gains a legend-chrome comparison: one spec, both renderers, assert
background, border, label font size, anchor and `ncols` agree. `test/test_e2e_serve.cscript`
and `test/test_serve_options.cscript` build a served dashboard from Stata with an explicit
`scheme()` and assert rc 0 and the app text contains the clock table (set `$dash_nobrowser`
before any Stata run that builds a dashboard; run the cert suite with `arch -arm64` from
`test/`).

**Mutation proofs.**
Restore `lg.location = _c['legend_position']` → the `ncols` test dies. Re-merge the split
`try` into one → the unmappable-position test dies. Delete the new
`_dash_style_legend(_fac_lg)` call → the faceted test dies. Revert the colour-key move to the
unconditional `"right"` → the three placement tests die; leaving the `"right"` default in
place must **not** kill the default test.

### Epic 25.B — Colour mapping and fill fidelity

**Failing test first (item 15).**
`test/test_server_scheme.py::TestColorvarInServerMode::test_a_served_discrete_colorvar_builds_a_mapper`
— serve a spec with `colorvar(rep78) colordiscrete`, walk the document, assert a
`CategoricalColorMapper` exists and its palette intersects `dr.scheme.p_colors`, and that a
`Legend` named `_dash_clegend` is present. Record the pre-fix failure output verbatim in the
commit message (per TR-25.9 step 1, the measurement of what a served `colorvar()` scatter draws
today is part of this test's first run).

**Failing test first (item 5).**
`test/test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_area_alpha_reaches_the_rarea_band`
— render an `rarea` layer, find the `VArea` glyph, assert
`glyph.fill_alpha == dr.scheme.area_alpha` (0.8 on the shipped schemes). Fails today at 0.5.

**Unit tests.**

| Test | Asserts |
|---|---|
| `test_a_served_continuous_colorvar_builds_a_colorbar` | `LinearColorMapper` + `ColorBar` in the served document |
| `test_a_served_colorvar_is_not_silently_dropped` | if a plot type is unsupported served, the build emits the standard unsupported-option note — never silence (CLAUDE.md rule 2, and the plan's own "nothing is silently dropped" clause) |
| `test_the_served_discrete_palette_comes_from_the_scheme` | mirrors the standalone `test_the_discrete_colorvar_palette_comes_from_the_scheme` (`test/test_scheme_consumption.py:447-460`) |
| `test_the_faceted_histogram_uses_the_scheme_bar_alpha` (`test/test_server_scheme.py`) | served `by()` quad `fill_alpha == scheme.bar_alpha`; `by(total)` twin likewise |
| `test_an_explicit_intensity_option_beats_the_scheme` | `fintensity()`/equivalent still wins on `rarea` |
| `test_the_documented_continuous_ramp_matches_the_code` (`test/test_help_conformance.py`) | the help's stated default equals `_PALETTE_MAP.get("viridis")` (or the synthesised-ramp decision), so item 6's disposition cannot rot |

**Integration.** `test/test_every_plot_type_draws.py` gains a served `colorvar()` case for each
plot type that supports it standalone; `test/test_server_build.cscript` builds a served app
with `colorvar()` from Stata and asserts rc 0 with no unsupported-option note.

**Mutation proofs.**
Put `fill_alpha=0.5` back in `map_rarea` → the area-alpha test dies. Put `0.6` back in either
emitted quad → the facet/total tests die (write them as two tests so the `by(total)` twin
cannot be forgotten). Remove the served colorvar branch → the mapper tests die. Change the
documented ramp name in the help → the conformance test dies.

### Epic 25.C — CSS delivery and mechanical guards

**Failing test first (items 12, 13).**
`test/test_scheme_consumption.py::TestSchemeCssActuallyApplies::test_the_style_block_survives_the_head_splice`
— render `layout("bs")` with a title, a subtitle, a KPI **and** a filter (so the widgets
bundle is inlined), then assert (a) `<script>`/`</script>` are balanced, and (b) the offset of
the scheme's `legend_bg_color` literal inside the document does **not** fall between a
`<script>` and its matching `</script>`. Fails today, for the reason measured in §9.

**Failing test first (items 4, 10).**
`test/test_scheme_consumption.py::TestSchemeCssActuallyApplies::test_the_kpi_card_takes_the_scheme_background`
— render a KPI with no `bgcolor()` under `scheme(economist)` and assert the card's effective
background is `scheme.legend_bg_color` and its border `scheme.legend_border_color`, i.e. that
no inline `background:`/`border:` shorthand is present to beat the rule. Three arms: the
initial Div (`dash_render.py:10487`), the CustomJS rebuild string (`:7328`) and the served
`_dash_kpi_card` (`:12976`). Fails today on all three.

**Failing test first (item 2).**
`test/test_scheme_consumption.py::TestNoParsedKeyIsDiscarded::test_every_parsed_key_has_a_consumer`
— enumerate `_init_properties`' 34 assignments by introspection, then for each assert
consumption by attribute **or** by string literal, with a commented allow-list for deliberate
non-consumers. Run it on the current tree first and record which keys it reports; that list is
the phase's own inventory and must shrink to the allow-list by the end.

**Unit tests.**

| Test | Asserts |
|---|---|
| `test_the_extracted_head_is_well_formed` | `_extracted_head` has balanced `<script>` tags and is non-empty for a widget-bearing model tree |
| `test_the_head_extraction_survives_a_literal_close_tag` | a synthetic `file_html()` output containing `</head>` inside a script string still yields the full head (unit test on the extraction helper, so the guard does not depend on a particular Bokeh build) |
| `test_the_csp_meta_reaches_the_document` | `_CSP_META` is inside `<head>` as an element, not inside a script — the security half of item 12 |
| `test_an_explicit_kpi_bgcolor_still_wins` | `bgcolor(red)` overrides the scheme on all three emitters |
| `test_a_filter_rebuild_keeps_the_card_chrome` | the CustomJS-rebuilt card text carries the same background/border as the initial render |
| `test_the_minor_grid_colour_reaches_the_figure` | `fig.xgrid[0].minor_grid_line_color == scheme.minor_grid_color` standalone (`dash_render.py:2185`) and in the served document (`:12683`) |
| `test_the_three_alphas_reach_real_glyphs` | scatter `alpha == scheme.fill_alpha`, bar `fill_alpha == scheme.bar_alpha`, area `fill_alpha == scheme.area_alpha`, in both renderers |
| `test_the_server_document_carries_the_scheme_css` | server arm of the selector guard (gated on Phase 24 item 3) |

**Integration / cscript.**
`test/test_e2e_kpi.cscript` builds a KPI dashboard from Stata with `scheme(economist)` and
asserts the written HTML contains the scheme's card colour and no `#dee2e6` default;
`test/test_conformance.cscript` keeps the drop-in claim honest for the same command.
`test/test_layout.py` and `test/test_layout_facets.py` get the structural assertions applied to
their existing fixtures so a malformed head is caught wherever it appears.

**Mutation proofs.**
Revert the head regex to `(?s)<head>(.*?)</head>` → the splice test dies (and only that test,
which is how you know it is measuring the splice). Re-add `border:1px solid #dee2e6` to any one
of the three KPI emitters → that emitter's arm dies. Add a new attribute to
`_init_properties` with no reader → the enumeration test dies. Delete the
`minor_grid_line_color` assignment at `:2185` → the minor-grid test dies; delete its emitted
twin at `:12683` → the server arm dies. Point `_render_server` back at `DashRenderer` → the
server arms all pass trivially, which the reviewer should check by running exactly that
mutation once.

### Suite hygiene

- Run the Python suite before and after each change set; run the Stata certification suite with
  `arch -arm64` from `test/`, and treat a **skip as a skip, not a pass**.
- Set `$dash_nobrowser` before any Stata run that builds a dashboard.
- Per CLAUDE.md rule 5: pull local `main`, run the full suite including the new tests, fix and
  re-run until green, commit to the feature branch, and supply the merge command rather than
  committing to `main`.

---

## Definition of done

**Epic 25.A**

- [ ] The emitted `_dash_style_legend` maps the scheme's clock integer through a side/anchor
      table and never assigns a raw int to `Legend.location` (items 8, 9).
- [ ] The `try` is split so `ncols`, background, border and label size are applied
      independently; the `except` names its exceptions and cannot hide a real failure (items 8, 9).
- [ ] `DashRenderer._rebuild_legend` applies the scheme's `legend_position` and `legend_cols`
      as defaults, and an explicit `legend()` option still wins (item 9).
- [ ] Served `by()` and `by(total)` facet legends carry the scheme chrome (item 14).
- [ ] `legend(position() ring())` moves the `colorvar()` colour key and the continuous
      `ColorBar`; with no `legend()` option both stay in the `"right"` panel (item 1).
- [ ] A standalone/server parity assertion covers legend chrome and placement.

**Epic 25.B**

- [ ] `map_rarea` fills at the scheme's area intensity; the served facet and total histograms
      fill at `_SCHEME_BAR_ALPHA` (item 5).
- [ ] `colorvar()` in `dash serve` produces the mapper, the colour key and — for the
      continuous case — the colour bar, or reports itself unsupported; it is not silently
      dropped (item 15).
- [ ] The continuous-ramp decision is written into `.ultraplan/CHANGELOG.md`'s S11 section and
      the help agrees with `dash_render.py:3253-3254` (item 6).

**Epic 25.C**

- [ ] A `layout(bs)` dashboard containing a widget has balanced `<script>` elements, and its
      `<style>` block (with `_DASH_GRID_CSS`, `css_block()` and `_CSP_META` before it) is a
      real element in `<head>` (items 12, 13).
- [ ] The scheme's card background and border reach a KPI card in the initial render, after a
      CustomJS rebuild, and in the served app; `bgcolor()` still wins (items 4, 10).
- [ ] `test_the_key_is_read_somewhere` is replaced by a mechanical enumeration of all 34
      `_init_properties` attributes that counts string-literal reads and carries a commented
      allow-list (item 2).
- [ ] `test/test_scheme_consumption.py` has a `ServerAppBuilder` arm used by both the CSS class
      and the key-consumption tests (items 3, 11).
- [ ] The three alphas, `minor_grid_color` and the server legend chrome are asserted against
      rendered models, not source counts (item 7).

**Across the phase**

- [ ] Every fix has a regression test that was observed failing before the fix (rule 8), with
      the failure output in the commit message.
- [ ] Every test names its mutation, and the mutation was run and reverted (non-vacuity).
- [ ] No new hardcoded colour, size or alpha literal was introduced on any path this phase
      touched.
- [ ] Full Python suite green; Stata cert suite green under `arch -arm64` with no new skips.
- [ ] Committed to `feature/batch4-interactive-layer` (or a branch off it) with the merge
      command supplied; no commit mentions the assistant or the vendor (rule 7).

---

## Risks and sequencing notes

**1. Overlap with Phase 23 on the legend block — coordinate, do not duplicate.**
Phase 23's item 5 is the Appendix B statement of the same `_dash_style_legend` defect that
items 8 and 9 state from Appendix C, and its item 7 is the `text_font_size` vs
`tick_label_font_size` split in the very same six lines (`dash_render.py:12660` and `:9068`).
Whoever reaches `_dash_style_legend` first should land the clock mapping, the split `try` **and**
the label-size decision in one change, and the other phase then verifies rather than re-edits.
Items 9's second clause (the standalone `_rebuild_legend` defaults), item 14 (facets) and item 1
(the colour key) are this phase's alone regardless of ordering.

**2. Phase 24 gates two of the CSS assertions.**
Item 3's *selector* assertions have nothing to see until Phase 24 item 3 calls `css_block()` in
the served app; item 4/10's `layout(auto)` arm is affected by Phase 24 item 4 (Bokeh 3 renders
Div markup in a shadow root, so a document-level rule cannot reach it). Mitigation: implement
the KPI fix in its **CSS custom property / narrow inline property** form, which works whether or
not the Div carries a `stylesheets=` entry, and land the structural assertions (script balance,
`<style>` survival) first since they depend on nothing.

**3. Item 15 is cheap after Phases 5–7 and expensive before.**
`GlyphMapper` is copied into the app wholesale by `inspect.getsource`
(`dash_render.py:12408-12409`) and instantiated at `:12432`, and the scatter branch already
delegates (`:14090`), so `_apply_colorvar` is defined in the served app and reached for at least
one path. Every other plot type gets colorvar for free the moment 15-03's delegation lands.
Doing item 15 before then means hand-writing a colorvar branch per plot type — the exact
duplication 15-03 exists to delete. **Sequence item 15 after Phases 5–7**, and start it by
measuring what a served `colorvar()` scatter draws today (TR-25.9 step 1) so the commit message
records the true starting state rather than restating the audit.

**4. The head-splice fix touches the security envelope.**
`_CSP_META` sits in the same swallowed region as the stylesheet, so item 12 changes what policy
the browser actually enforces on every `layout(bs)` dashboard with a widget. Re-run
`test/test_html_output.py`'s XSS arms (`:486`, `:633`, `:939` — proven non-vacuous under
mutation per `REMAINING.md`) and `test/test_security_surface.py` after the change, and check
that a now-enforced CSP does not break the inline Bokeh bootstrap; if it does, that is a real
finding about the CSP, not a reason to re-break the head.

**5. Changing the KPI markup is a three-copy change.**
`dash_render.py:10487` (initial), `:7328` (CustomJS rebuild) and `:12976` (served) hold the same
card markup. Changing one and not the others produces a card that changes appearance when a
filter moves, or a served card that differs from the saved one. The regression test has three
arms for exactly this reason.

**6. `rarea`'s alpha key is a judgement call.**
`REMAINING.md` records the literal (`fill_alpha=0.5`) and the ultraplan `<action>` names three
alphas without assigning one to `rarea`. `map_area` uses `area_alpha` (`:3635`), which is the
obvious sibling, but the choice must be stated in the commit message so the next auditor reads
a decision rather than inferring one.

**7. Enumerating scheme keys will surface keys other phases own.**
Item 2's mechanical check will report `p_mark_colors` (11-03's "wire it or remove it") and
anything Phases 23/24 have not yet landed. Do **not** silence those with a blanket skip: the
allow-list entries must name the key, the disposition and the owning phase, so the check stays
honest while the other phases land.

**8. Bokeh version sensitivity.**
Two mechanisms here depend on Bokeh internals: the presence of a literal `</head>` inside
`bokeh-widgets.min.js` (measured: 1 occurrence at the pinned version) and shadow-root rendering
of `Div` markup. Write the head-extraction unit test against a **synthetic** document
containing that literal (TR-25.10) so the guard survives a Bokeh upgrade that removes the
literal, and prefer Bokeh's own template/`json_item` path if it is available, which removes the
dependency entirely.
