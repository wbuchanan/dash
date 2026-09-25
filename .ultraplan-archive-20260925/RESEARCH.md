# UltraPlan Research — Phase 01: per-plot qualifiers on computed layers

Three parallel investigations: the codebase, Bokeh 3.9 filtering semantics, and Stata's own
`if`/`in` ground truth. Everything below was measured at `187a786` on
`feature/batch4-interactive-layer`. Nothing in the repository was modified.

---

## 1. Codebase — where the qualifier lands and what it misses

### 1.1 The single qualifier site

`DashRenderer._make_figure_body`, `dash_render.py:9951-9998`. `source_for_plot = source`
(:9955) is **never reassigned** — the layer always draws from the graph's shared
`ColumnDataSource`; only `_plot_view` changes.

The mask built at :9979 is *exactly* the array a `mask=` kwarg would carry — one bool per
row of the source the mapper receives, already intersected with any facet view. It is in
scope at every dispatch call (:10027, :10031, :10036, :10063) as
`_plot_view.filter.booleans`.

Identity space: `_ROW_ID_COLUMN = "__dash_row__"` (:591), stamped by `_make_source` (:8506).
`_row_ids_for` (:8574-8592) returns **ordinal positions in `self.df`**.

### 1.2 The 14 computed mappers — a uniform result

**Machine-verified by AST walk: all 14 accept `view=None`, and the token `view` never
appears in any of their bodies.** All 14 build their own `ColumnDataSource`.

| method | `def` | reads data at | own CDS at | returns |
|---|---|---|---|---|
| `map_area` | 3592 | 3614, 3615 | 3630, 3652 | VArea renderer |
| `map_lfit` | 3821 | 3845, 3846 | 3853, 3865 | renderer |
| `map_qfit` | 3873 | 3895, 3896 | 3902, 3910 | renderer |
| `map_lfitci` | 3918 | 3942, 3943 | 3950, 3988 | `[line_r, band_r]` |
| `map_qfitci` | 3998 | 4023, 4024 | 4031, 4082 | `[line_r, band_r]` |
| `map_lowess` | 4091 | 4127, 4128 | 4134, 4141 | renderer |
| `map_lpoly` | 4272 | 4300, 4301 | 4306, 4333 | renderer |
| `map_lpolyci` | 4344 | 4366, 4367 | 4372, 4433 | `[line_r, band_r]` |
| `map_fpfit` | 4517 | 4543, 4544 | 4549, 4558 | renderer |
| `map_fpfitci` | 4569 | 4591, 4592 | 4597, 4625 | `[line_r, band_r]` |
| `map_histogram` | 4636 | `_extract_finite` :4666 | 4663, 4672 | Quad + agg tags |
| `map_kdensity` | 4806 | `_extract_finite` :4830 | 4836, 4860, 4892 | Line + agg tags |
| `map_mspline` | 5912 | 5942, 5943 | 5967, 5975 | `[r]` |
| `map_mband` | 5983 | 6011, 6012 | 6017, 6057 | `[r]` |

Twelve share one shape, e.g. `map_lfit`:

```python
 3845        x = np.array(source.data[xvar], dtype=float)
 3846        y = np.array(source.data[yvar], dtype=float)
 3847        # Drop NaN pairs
 3848        mask = ~(np.isnan(x) | np.isnan(y))
 3849        x, y = x[mask], y[mask]
```

**Minimal change for those twelve: a `row_mask=` kwarg ANDed into the existing NaN mask —
two inserted lines, no other body change.** The local is already named `mask`, so the
parameter must be `row_mask=` (or the local renamed).

Insertion points, per method: `map_lfit` after :3846 · `map_qfit` after :3896 ·
`map_lfitci` after :3943 (before `n = len(x)` at :3946, which feeds `df = n-2` and `se_fit`)
· `map_qfitci` after :4024 · `map_lowess` after :4128 · `map_lpoly` after :4301 ·
`map_lpolyci` after :4367 (also fixes the bootstrap at :4427-4430) · `map_fpfit` after :4544
· `map_fpfitci` after :4592 (plus `_bootstrap_ci` at :4620) · `map_mspline` after :5943
(before the `argsort` at :5949) · `map_mband` after :6012 · `map_area` after :3615.

Most of these become *correct by construction* once masked: `map_lowess`'s `frac=bw` is a
fraction of the sample; `_default_lpoly_bwidth` (:4157) derives bandwidth from the data;
`map_mband`'s band count `_mband_default_bands(len(x_clean))` (:6029) becomes
subset-relative — each matching what `twoway ... if` does.

**`map_histogram` and `map_kdensity` are the two exceptions.** `_extract_finite`
(:964-995) drops `None`/NaN internally and returns a **shorter array with no positional
correspondence**, so a mask cannot be applied after the call:

```python
  994    arr = np.array([v for v in col if v is not None], dtype=float)
  995    return arr[~np.isnan(arr)]
```

The mask must be applied **at** :4666 / :4830 — either by adding an optional `mask=` to
`_extract_finite` or by zipping `source.data[yvar]` against the mask inline. Both also need
the agg-config change in §1.5, or the bars jump back to the full sample on the first widget
move. Note both put `options` **before** `xvar` in their signatures, and `_add_glyph`
already special-cases them at :10418-10419.

### 1.3 Raw-data mappers — and two defects the spec did not have

All ten raw mappers accept `view=` and **all ten actually use it**. But:

| mapper | glyph | draws from | connected topology? |
|---|---|---|---|
| `map_scatter` 3407 | Scatter 3477 | `plot_source` | no |
| `map_line` 3486 | Line 3549 | **`sorted_source`** (new CDS 3527) | **yes** |
| `map_connected` 3560 | Line + Scatter | delegates | **Line half yes** |
| `map_bar` 3660 | vbar 3739 | **`clean_source`** (new CDS 3691) | no |
| `map_spike` 3765 | segment 3812 | **`seg_source`** (new CDS 3801) | no |
| `map_dropline` 5211 | segment + scatter | **`dl_source`** (new CDS 5260) | no |
| `map_rline` 5106 | Line ×2 | `source` directly | **yes ×2** |
| `map_tsline` 5805 / `map_rconnected` 5147 / `map_dot` 5178 | delegate | — | tsline/rconnected yes |

Connected-topology glyphs Bokeh silently drops the filter on: `map_line`, `map_tsline`,
`map_rline`, the Line halves of `map_connected` and `map_rconnected`, and `map_area`'s
`fig.varea` (:3631).

> **NEW — D1. `map_line` attaches a positionally-invalid view.** :3526 does
> `dropna(...).sort_values(xvar)` and :3527 wraps the result in a new CDS; :3547-3548 then
> attach a `BooleanFilter` whose booleans were indexed against the *original, unsorted*
> source. Even if Bokeh honoured Line filters, the mask would select the **wrong rows**.
> `sorted_source` also carries only `{xvar, yvar, mlabel?}` (:3521-3524) — **no
> `__dash_row__`**. The chosen private-source fix must build identity in, not assume it.

> **NEW — D2. Private sources are invisible to the filter callback generally, not just to
> the qualifier.** `all_graph_sources` is built only from `self.sources` (:11882). So
> `sorted_source`, `clean_source`, `seg_source`, `dl_source` and every computed mapper's CDS
> are **never updated when a widget moves**. Only `map_scatter` (unjittered), `map_rline`
> and the histogram/kdensity agg path currently respond to filters at all. This is strictly
> larger than "computed layers ignore `view`" and bounds what Epic B can promise.

### 1.4 `jitter()` (item 9) — three blockers, not one

`_build_jitter_source` (:2521) copies **all** columns (:2559-2562), so `__dash_row__`
survives and row count/order are identical. At initial render the view is valid. After the
first widget move it is not: the callback shortens only sources in `all_graph_sources` and
rebuilds booleans to the kept-row count (:7167-7169), while the jittered CDS keeps every row.

Appending the jittered source to `all_graph_sources` (:11881-11887) is **necessary but not
sufficient**:

1. **`:11902` would raise `KeyError`** — `_snapshot_of` is keyed by `id()` and populated only
   from `self.sources` (:11835-11841); the comprehension is unguarded.
2. **The snapshot must be taken from the jittered CDS**, so kept rows retain their original
   offsets. There is no JS port of `_apply_jitter` (:2231), so offsets cannot be re-derived
   client-side.
3. **`_view_filter_args` resolves by object identity** (`ordered_sources.index(source)`,
   :8542) and all three `_register_view_filter` call sites register the *shared* source.

Related: `map_dropline` jitters inline at :5244-5248 into `dl_source`, whose column set
(:5250-5253) **omits `__dash_row__` entirely** — a `map_scatter` fix does not generalise.

### 1.5 Item 7 — the intersection loss is CONFIRMED, with the exact mechanism

`_register_view_filter` (:8509-8524) stores `(source, BooleanFilter, member_ids)`. The
`CDSView` itself is not stored. `self._view_filters` is **not initialised in `__init__`** —
created lazily at :8522-8523, never reset. Three call sites: :9991 (per-plot), :11399
(linked-graph qualifier), :11475 (linked `by()` panel).

The JS rebuild at :7164-7171:

```javascript
 7167    const kept = _kept_ids_by_src[_si] || [];
 7168    const member = new Set(vf.member_ids || []);
 7169    vf.filter.booleans = kept.map(id => member.has(id));
```

:7169 is a **total replacement**. It never reads the prior `booleans`, and no copy of the
render-time mask is stored anywhere — `member_ids` is the sole source of truth.

At :9987 `_mask` becomes `facet_mask AND qualifier_mask`, but :9992 registers
`self._row_ids_for(_pdf)` — the qualifier **alone**. On the first widget move the facet
AND-term is overwritten and the panel shows qualifier-passing rows from *every* facet.

**Fix shape:** register the ids the *combined* mask selects —
`[r for r, keep in zip(_ids, _mask) if keep]` — instead of `self._row_ids_for(_pdf)`.

> **NEW — D3.** The length guard at :9986 silently skips the intersection when
> `len(_prev_bools) != len(_mask)` — no warning, and `except Exception` (:9993) does not
> catch it because nothing raises. Lengths coincide today only because `linked_source`
> (:11379) is built without `df=`; any shortened source loses the facet restriction **at
> initial render too**.

### 1.6 Item 10 — the KPI path is a working precedent to copy

Only two producers of `_dash_agg_config` exist: :4695 (histogram) and :4905 (kdensity).
Both attach plain Python attributes to the `GlyphRenderer`. Both mappers' early-outs
(:4662-4665, :4835-4837, :4859-4861) return **untagged** renderers.

Registry at :12203-12210 (inside `render()`, not `_assemble_layout`); wiring at :11905-11914.
The `_FILTER_JS` agg loop (:7390-7399) selects rows **by column name only** — no graph id,
no source index, no row-id list — and reads the already-filtered `new_data` (:7097-7104).

`_kpi_callback_config` (:11613, :11620-11621) and `dash_apply_kpis` (:7215-7225) already do
exactly the needed thing with `has_qual` / `qual_ids` and a JS `Set`. **Copy that shape.**

Three insertion points: **(a)** config build :4695-4703 and :4905-4913 — the ids must arrive
from `_make_figure_body`, where `self._row_ids_for(_pdf)` is already computed at :9992;
**(b)** serialization needs **no change** (`dict(...)` shallow-copies, `_row_ids_for` already
returns `int`); **(c)** JS between :7397 and :7399, where `ROW_ID` is already in scope
(:7115). Preserve the tri-state: `None` = unrestricted, `[]` = blank the layer.

> **Residual gap (out of scope, record it):** even with (a)-(c) the recompute still draws
> from `new_data`, the **primary** source. An aggregate on an unlinked graph with a different
> frame is already recomputed from the wrong row universe today.

### 1.7 The server renderer — 43 call sites, and no row identity

15 `_compute_*` helpers are emitted (plus `_compute_lpoly_fit`, copied by
`inspect.getsource` at :12520, so grep does not find it). **None takes a mask or row-id
list** — the only restriction channel is the first positional `df`.

**43 aggregate call sites would need a row restriction** (46 counting the three
`_compute_kpi` sites):

| path | loop at | frame passed | sites |
|---|---|---|---|
| main plot loop | :14030 | `g_df` | 15 |
| `by()` facet ladder | :15136 | `_fac_gdf` | 7 |
| `by(total)` twin | :15236 | `work_df` | 7 |
| filter callback | :15583 | `agg_fdf` | 14 |

> **NEW — D4. Server mode has no row-identity carrier.** `_ROW_ID_COLUMN` is emitted as a
> bare constant but **no emitted code ever writes `__dash_row__` into a ColumnDataSource**.
> The app uses a plain `'index'` column, and only on `shared_source` (:13751). A row-id-list
> approach has no carrier in server mode — **a mask over `df.index` is the only thing
> available today.** This changes the shape of the eventual Epic C implementation.

> **NEW — D5. The per-plot data is present in the payload; the emitted code never reads it.**
> `dash.ado:1240`/`:1244` emit `if_expr`/`in_expr` on **every** plot segment, and those reach
> `_SPEC_B64`. But `plot.get('if_expr')` **does not occur anywhere** in the emitted app —
> every read is graph-scoped (:13812, :13819, `_graph_qualifiers` :15007). Separately,
> `dash.ado:1496` promotes the qualifier to graph level **only when `n_segs == 1`**, with a
> comment at :1485 stating the consequence outright: *"per-plot qualifiers are not read in
> build/server flows."* So **single-layer commands work in server mode today; multi-layer
> ones silently ignore the qualifier.**

Pre-existing inconsistency Epic C would extend: facet/total agg entries (15155ff, 15256ff)
**omit the `'opts'` key**, so `agg.get('opts') or {}` at 15605ff silently degrades to `{}`
for faceted layers.

### 1.8 `_apply_graph_filter` and `_stata_if_to_pandas` — failure modes

`_apply_graph_filter` (:8603-8666) is **spec-shaped, not scope-shaped** — it reads only
`if_expr`/`in_expr` from whatever dict it is given, and **subsets** (`df.iloc` :8632,
`df.query` :8654); it never returns a mask. It copies the whole frame at :8623 on every call.

> **NEW — D6. `in_expr` silently ignores most legal Stata.** :8628 uses
> `^(\d+)/(\d+)$` with no `else` branch, so `in 1/l`, `in f/20`, `in -10/-1`, `in 10` and
> `1 / 10` are accepted and **discarded without a warning**. The generated-script paths
> re-implement the same regex (:13814-13818, :15047-15051), so the gaps are identical there.

> **NEW — D7. Missing-as-`+∞` is a silent wrong answer.** `mpg>20` with `mpg=[10, NaN, 30]`
> returns only `30` under pandas; **Stata includes missing**. Nothing compensates. It
> validates, executes, returns the wrong rows, and warns about nothing.

Everything else in `_stata_if_to_pandas` (:6852-6929) fails **open**: a rejected qualifier
warns and returns the **unfiltered** frame (:8646-8651, :8661-8664, :9993-9998) — it draws
*more* data, not less. Verified-rejected inputs include `_n`/`_N`, extended missing `.a`-`.z`
(which mangles to `(rep78 != rep78)a` before failing to parse), nested `inlist`, any other
Stata function, and `^`.

No injection path was found by inspection: `_validate_if_expr` (:6932-6967) runs **after**
translation and before `df.query(..., engine="python")`; `@` is hard-rejected (:6954);
`_IF_EXPR_ALLOWED_NODES` omits `Call`, `Attribute`, `Subscript`, `Lambda` and all arithmetic.
That is a code-reading assessment, not a proof.

### 1.9 Two findings that widen the phase

> **F-A. The same defect already bites `by()` + `link()` with no per-plot qualifier at all.**
> At :11465-11470 a **linked** `by()` graph gives every panel the same `shared_src_render`
> and differentiates them only by `panel_view_r`. Since computed mappers ignore `view`,
> **every facet panel draws an identical lfit/kdensity/histogram computed from all rows.**
> An **unlinked** `by()` graph (:11481) gets a genuinely pre-subset source per panel and is
> correct. So **adding `link()` silently changes a computed layer's values.** The same
> applies to a linked graph-level qualifier (:11502-11505).

> **F-B. Existing coverage is scatter-only and structurally cannot catch this.**
> `test/test_per_plot_qualifier_linking.py` (163 lines, 7 tests) contains no reference to
> `lfit`, `kdensity` or `histogram`. The helper `_visible_count`
> (`test/test_varlist_expansion.py:101`) reads `renderer.view.filter.booleans` — it will
> report a *computed* layer as fully visible regardless. Assertions on computed layers must
> compare the fit source's **values** against an independently computed subsample fit.

---

## 2. Bokeh 3.9 filtering semantics

Measured against bokeh 3.9.0 in a **real browser with an instrumented
`CanvasRenderingContext2D`**, so every claim is what BokehJS *drew*, not what it was asked to
draw. Scripts under `scratchpad/bokeh-research/`.

### 2.1 E-1024 is narrower than its message, and it is not a refusal

```python
@error(CDSVIEW_FILTERS_WITH_CONNECTED)
def _check_cdsview_filters_with_connected(self):
    if isinstance(self.glyph, ConnectedXYGlyph) and not isinstance(self.view.filter, AllIndices):
```

`ConnectedXYGlyph` has **exactly two subclasses in 3.9: `Line` and `Patch`.** Not `VArea`,
not `HArea`, not `Step`, not `MultiLine`, not `Patches`. And it is an *error-level validation
issue*, not a refusal: `file_html()` succeeds, the `BooleanFilter` serialises unchanged,
nothing raises.

**This matters directly: `map_area` draws `fig.varea`, which is NOT affected.** `area` can
keep its `CDSView`.

### 2.2 What actually gets drawn — and why "the full line is drawn" is wrong

`GlyphRendererView.set_data` subsets the glyph arrays to the view, but `_paint` then passes
`all_indices.ones()` — **full-source-space** positions — into those **subset-space** arrays.
`sx[6]` is `undefined`, and `LineView`'s `gap(i) = i - iprev != 1` test fires on every
non-adjacent pair, turning `lineTo` into `moveTo`.

So the outcome is **filter-shape dependent** (10 rows, 5 kept):

| kept positions | Line result | Patch result |
|---|---|---|
| `[0,1,2,3,4]` contiguous prefix | **all 5 — correct, by accident** | correct |
| `[3,4,5,6,7]` middle run | **2 of 5** | 2 of 5 |
| `[0,2,4,6,8]` alternating | **nothing drawn** | 3 of 5 |
| `[5,6,7,8,9]` suffix | **nothing drawn** | **nothing drawn** |

**A `CDSView` filter on a `Line` is correct only when the kept rows are a contiguous prefix
`0..k-1`.** Every other shape silently under-draws or draws nothing. Corroborated by
[bokeh#7070](https://github.com/bokeh/bokeh/issues/7070) (open since 2017) and maintainer
bryevdv in [bokeh#9388](https://github.com/bokeh/bokeh/issues/9388#issuecomment-552147658):
*"I'm not actually sure that CDSView together with lines can be considered supported."*

The [Filtering data](https://docs.bokeh.org/en/3.9.0/docs/user_guide/basic/data.html#filtering-data)
user guide never mentions the restriction; the correct warning in the `GlyphRenderer.view`
docstring uses `.. note:` with one colon (malformed reST) and has never rendered. Trust the
measurement.

### 2.3 Head-to-head — the decisive table

12 rows, layer must draw `g=="A"` = rows `[0,1,2]` and `[6,7,8]` — **two contiguous runs**,
which is what a real group filter looks like. Correct answer: 2 subpaths, 6 points.

| approach | drawn | linked selection | `source.data` swap reaches it | hover |
|---|---|---|---|---|
| `CDSView` + `BooleanFilter` | **1 subpath, 3 pts — rows 6,7,8 silently lost** | yes | yes (filter goes stale) | correct |
| **(b) NaN in a per-layer column** | **2 subpaths, 6 pts ✓** | **yes, automatic** | **yes** | NaN rows unhittable |
| (a) private pre-filtered source | 1 subpath, 6 pts — **connects straight across the gap** | **no** | **no** | private-space |
| (c) `multi_line` per run | 2 subpaths, 6 pts ✓ | **no** — row identity gone | **no** | no row identity |

Confirmed by screenshot and by canvas trace. Rewriting `shared.data` changed the NaN line
correctly and left the private-source line and the `multi_line` **byte-for-byte unchanged** —
the callback never reached them.

> **NEW — B1. Stale-filter hazard.** After a callback grew a source 10 → 12 rows, the
> `BooleanFilter` still held **10** booleans. No error, no warning; the two new rows were
> simply invisible. **Any callback that rewrites a shared source must also rewrite every
> `BooleanFilter.booleans` to the new length.**

### 2.4 NaN semantics — breaks reliably, and is excluded from auto-ranging

`y = [1, 2, NaN, 4, 5]` drew two subpaths breaking exactly at the NaN. `LineView._paint`
tests `!isFinite(sx_i + sy_i)` — **screen** coordinates, so anything mapping to non-finite
(e.g. ≤ 0 on a log axis) also breaks the line.

| y column | measured `y_range` |
|---|---|
| `[100,101,102,103,104]` | 99.8 → 104.2 |
| `[100,101,102,103,` **NaN** `]` | 99.85 → **103.15** — NaN ignored entirely |
| `[100,101,102,103,` **0.0** `]` | **-5.15** → 108.15 — the 0 stretches the range |

So a NaN row neither draws nor stretches the range. The docs warn about the third row
directly: *"Do not use the native Python `None` object, because this will be evaluated as 0"*.
Box-select over NaN rows returns `[]`; over real rows returns source-space indices.

Two consequences to design around: **one NaN column per layer** (NaN'ing a shared `y` would
break every other glyph reading it — two `line` layers over one source using `yA`/`yB` each
drew their own correct subset), and **NaN cannot draw isolated points** — a run of length 1
has nothing to connect to, so pair the line with a `scatter` on the same NaN column.

### 2.5 Private sources lose everything, measured

Setting `shared.selected.indices = [2,4,6]` faded the shared-source scatter to
`rgba(31,119,180,0.1)` while the private-source scatter stayed `#1f77b4` — **completely
unaffected**. Same for `inspected`. Bokeh provides no index-remapping helper; the documented
pattern is a hand-written `selected.js_on_change` with an explicit `src_row` column, which is
**one-directional**, asynchronous, and must be re-run whenever either source's rows change.

`source.selected.indices` is **always source space**, never view space — so two glyphs with
*different* `CDSView`s over the *same* source interoperate correctly.

### 2.6 `LabelSet` has no `view` at all — use the `text` glyph

```
LabelSet has a 'view' property:  False
DataAnnotation's own properties: ['source']
LabelSet(view=...) -> AttributeError: unexpected attribute 'view' to LabelSet
```

No annotation inherits a view. A `LabelSet` over a 10-row source drew all ten strings.

**`figure.text(...)` is a real `GlyphRenderer`, accepts `view=`, is not a `ConnectedXYGlyph`,
and was measured to filter correctly** — it drew exactly `P0, P2, P4, P6, P8` for a view
keeping `[0,2,4,6,8]`, while keeping the shared source and linked selection. And **if the
layer already has a NaN column, a `text` glyph plotted against it subsets itself for free.**

### 2.7 Colour over a subset

| mapper | measured metrics | verdict |
|---|---|---|
| `LinearColorMapper()` auto | `0 → 9` | **ignores the view — full column** |
| **`domain=[(renderer,"c")]`** | **`0 → 4`** | **respects the view ✓** |
| explicit `low`/`high` | `0 → 4` | hand-computed |

**`linear_cmap` can never auto-range** — `low` and `high` are *required positional*
arguments. Only `LinearColorMapper(palette=...)` auto-ranges, and only `domain` follows a
view. `ColorBar` has no range of its own, so fixing the mapper fixes the bar.

---

## 3. Stata ground truth

StataNow 19.5 MP (arm64), `sysuse auto` (N=74; foreign==1: 22, foreign==0: 52). Nothing was
inferred from a picture: every claim is backed by the **serset** each `twoway` layer builds,
loaded with `serset dir` / `serset set k` / `serset use, clear`. Fitted lines were recovered
by regressing a serset's own points on each other.

> **Method caveat that matters for the test.** Sersets store `float`, so coefficients
> recovered *from a graph* agree with `regress` doubles only to ~1e-8 relative. That is a
> storage artifact of the graph object, not of Stata's estimation. **Test assertions must use
> the `regress` doubles below, not serset-recovered values.**

### 3.1 The ground-truth numbers (full precision)

| quantity | `if foreign==1` | full sample |
|---|---|---|
| N | **22** | **74** |
| slope `_b[weight]` | **-.010425957587798849** | **-.0060086868119993289** |
| intercept `_b[_cons]` | **48.918297231743246** | **39.440283530717977** |
| slope, `%21x` | `-1.55a3456f3dfbfX-007` | `-1.89c9095975231X-008` |
| intercept, `%21x` | `+1.8758ac3812c1bX+005` | `+1.3b85b35f2b358X+005` |
| se(slope) | .0024941691063949203 | .00051787817670857252 |
| r2 | .46628963289838132 | .65153125290875114 |
| x-range of the drawn segment | **[1760, 3420]** | [1760, 4840] |

Companions: `foreign==0` N=52 slope -.0059750835105182119 · `in 1/60` N=60 slope
-.0056974654861187985 · `foreign==1 & weight>2500` N=6 slope -.0093656523981433745 ·
`foreign==1 in 1/60` N=8 slope -.0096564106174751828.

> ⚠️ **Trap for the test author.** `auto.dta` ships sorted domestic-first; foreign cars start
> at observation 53. So `in 1/20` contains **zero** foreign cars and
> `regress mpg weight if foreign==1 in 1/20` is `r(2000)`. Use `in 1/60` (N=8) for any
> intersection test.

### 3.2 Per-layer semantics — confirmed numerically, not assumed

`lfit` emits exactly 3 points (xmin, mid, xmax of *its own* estimation sample).

| command | layer 1 serset | `lfit` slope | equals `regress` on |
|---|---|---|---|
| `(scatter) (lfit)` | 74 obs | -.0060086866 | full sample |
| **`(scatter) (lfit … if foreign==1)`** | **74 obs** | **-.0104259571** | `if foreign==1` |
| `(scatter) (lfit) if foreign==1` | 22 obs | -.0104259571 | `if foreign==1` |
| `(scatter … if foreign==0) (lfit … if foreign==1)` | 52 obs | -.0104259571 | each its own |
| `(scatter) (lfit … if weight>2500) if foreign==1` | 22 obs | -.0093656528 | the **intersection**, N=6 |
| `(scatter) (lfit … if foreign==1) in 1/60` | 60 obs | -.0096564116 | intersection, N=8 |
| `(scatter) (lfit … in 1/60) if foreign==1` | 22 obs | -.0096564116 | intersection, N=8 |

1. **A per-layer qualifier restricts only its own layer** — the scatter still holds all 74
   rows while the fit is the 22-row foreign regression.
2. **Command-level restricts every layer**, including layers with no qualifier of their own.
3. **Both ⇒ logical AND**, and the last two rows are identical, so **order does not matter**.
4. **`in` is absolute dataset observation numbers, never re-indexed into an outer
   subsample**, and it is sort-order dependent. The decisive case: if `in 1/60` were
   re-indexed within the 22 command-level rows it would select all 22 and give -.01042; it
   gives -.00965 instead.
5. The **axes** span the union across layers; only the **fitted segment** shrinks to its own
   sample's x-range.

> **NEW — S1. `||` syntax binds a trailing `if` to the LAST PLOT, not the command.**
> `twoway scatter … if foreign==1 || lfit …` gives a 22-obs scatter and a **full-sample**
> fit. Command-level scope in bar syntax requires the explicit empty final segment
> `|| if exp`. This is a real parsing hazard and needs its own test — `dash.ado:1496`
> promotes a qualifier to graph level when `n_segs == 1`, which is a different rule.

### 3.3 Degenerate subsets — **Stata is not uniform, and this contradicts decision Q8**

`twoway (<type> … if _n==1)` — one observation:

| types | message | rc | effect |
|---|---|---|---|
| `lfit` `lfitci` `lpoly` `lpolyci` `kdensity` | `insufficient observations` | **2001** | **whole graph aborts — no graph at all** |
| `qfit` `qfitci` `fpfit` `fpfitci` | `could not fit model` | **0** | all-missing serset, nothing drawn |
| `lowess` `mband` `mspline` `histogram` and every raw type | *(none)* | **0** | 1-obs serset, drawn |

Zero observations (`if foreign==99`):

| types | rc | effect |
|---|---|---|
| `lfit` `lfitci` `qfit` `qfitci` `lowess` `scatter` `line` | **0** | empty serset; other layers draw normally |
| `histogram` | 0 | 1-obs serset |
| `kdensity` | 0 | **75-obs serset** (degenerate) |
| `lpoly` `lpolyci` | **2000** | whole graph aborts |
| `fpfit` | **198** | whole graph aborts |
| `mband` `mspline` | **198** | whole graph aborts |

`twoway (scatter mpg weight) (lfit mpg weight if make=="Honda Civic")` → **rc 2001, and the
scatter is not drawn either** — `graph describe` reports *graph not found*.

**Root cause** (read from `/Applications/StataNow/ado/base/t/twoway__lfit_serset.ado`,
described not reproduced): both `lfit` and `qfit` wrap the internal `regress` in `capture`,
but `lfit`/`lfitci` **re-raise any rc other than 2000**, so rc 2001 propagates and kills the
graph, while `qfit`/`qfitci` re-raise nothing. The asymmetry is deliberate in the code but
undocumented — arbitrary rather than principled.

Boundary: exactly 2 observations is rc 0 for every fitted type. Constant x is rc 0.

### 3.4 `scatteri` / `pci` / `function` — validated, then discarded

**The sharpest finding for implementers.** All three accept a qualifier, **evaluate it**, and
then ignore it:

| probe | `scatteri` | `pci` | `function` | `scatter` (contrast) |
|---|---|---|---|---|
| `if nosuchvar==1` | rc **111** | rc **111** | rc **111** | rc 111 |
| `in 900/901` | rc **198** | rc **198** | rc **198** | rc 198 |
| valid `if foreign==1` | rc 0, **output byte-identical** | rc 0, **identical** | rc 0, **identical** | rc 0, restricted |

So dash must still **validate** the qualifier on these three — a bad variable name or an
out-of-range `in` is a genuine error — while **ignoring it semantically**. Also: `function`
defaults to **range 0-1** and does not inherit companion plots' x-range.

### 3.5 Marker labels — decision Q15 confirmed

`(scatter mpg weight if foreign==1, mlabel(make))`: serset N 74 → **22**, non-blank `make`
74 → **22**. The label column is carried into the serset already subset; there is no separate
filtering step.

### 3.6 `by()` × per-layer qualifier — strict intersection, confirmed per panel

`(scatter mpg weight) (lfit mpg weight if foreign==1), by(rep78)`:

| panel | scatter | lfit | recovered slope | `regress … if rep78==k & foreign==1` |
|---|---|---|---|---|
| 1 | 2 obs (all panel rows) | **0 obs** | — | N=0 |
| 2 | 8 obs | **0 obs** | — | N=0 |
| 3 | 30 obs | 3 pts | -.015476189 | N=3, **-.0154761904761905** |
| 4 | 18 obs | 3 pts | -.005500296 | N=9, **-.0055002961792872** |
| 5 | 11 obs | 3 pts | -.019698354 | N=9, **-.0196983546617916** |

**Each panel's fit equals `regress … if <panel> & <layer>` exactly**, the scatter keeps all
its panel's rows, and **empty-intersection panels are kept and rendered**.

> **NEW — S2, the biggest surprise. `by()` swallows a fatal rc and silently deletes the
> panel.** The same 1-observation case that aborts an ordinary graph with rc 2001 returns
> **rc 0** under `by()` — the message `insufficient observations` still prints, the graph is
> built, and the offending **panel disappears from the layout entirely**, taking its
> perfectly valid scatter layer with it. SVG export confirms the panel label is gone.
> The researcher flagged this as ambiguous rather than resolving it: printing a fatal-looking
> error, returning success and deleting a panel is hard to read as intentional design.

> **Ambiguity left open — `kdensity`'s third serset column.** The serset carries density,
> grid, **and the raw source variable**. Density and grid honour the qualifier (grid min
> 12 → 14) but the third column still holds all 74 `mpg` values. Whether it feeds anything
> visible could not be determined from outside. It only bites if dash's `kdensity` is ever
> compared against a serset dump rather than against the drawn curve.

---

## 4. Conflicts with the discovery decisions, and how they were resolved

Research contradicted three discovery decisions and raised four new ones. All seven were put
back to the user; none was resolved unilaterally.

### 4.1 SUPERSEDED — Q3, connected-topology glyphs

**Was:** private pre-filtered `ColumnDataSource` with a `link()` guard test.
**Now:** **a per-layer NaN column on the shared source.**

The measurement decided it. A private source draws the line **straight across the excluded
gap** — the qualifier is honoured in the data and lied about in the picture — and it loses
linked selection and callback reach entirely. The NaN column draws the correct gapped
topology, keeps both, and sidesteps E-1024 because no `CDSView` filter is set.

Consequences for the plan:
- `map_area` **drops out of this item**: `VArea` is not a `ConnectedXYGlyph`, so `area` keeps
  its `CDSView`. The affected set is `map_line`, `map_tsline`, `map_rline` and the Line halves
  of `map_connected` / `map_rconnected`.
- The `link()` guard test Q3 mandated is **no longer needed for its original purpose** — the
  layer stays inside `link()`. It is replaced by a test asserting the gapped topology and one
  asserting linked selection still reaches the layer.
- **D1 is dissolved, not fixed.** `map_line`'s positionally-invalid view stops mattering
  because no view is attached; the NaN column is written before the sort, so it travels with
  the row.
- New requirement: **one NaN column per layer** (NaN'ing a shared `y` breaks every other glyph
  reading it), and **a paired `scatter` on the same NaN column** so isolated single rows are
  visible at all — a run of length 1 has nothing to connect to.

### 4.2 SUPERSEDED — item 8, marker labels

**Was:** mask the `LabelSet`.
**Now:** **replace it with a filterable `figure.text(...)` glyph.**

`LabelSet` has no `view` property in Bokeh 3.9 and no annotation inherits one, so it cannot be
filtered at all. `figure.text(...)` is a real `GlyphRenderer`, accepts `view=`, and was
measured drawing exactly the kept rows while keeping the shared source. Where the layer
already carries a NaN column, the `text` glyph subsets itself for free.

Consequence: this changes which Bokeh model carries marker labels, so every existing `mlabel`
assertion needs re-baselining. That is a plan task, not a side effect.

### 4.3 REFINED — item 8, colour range

`LinearColorMapper` auto-ranging **ignores the view** (measured 0→9 where the subset is 0→4),
and `linear_cmap` can never auto-range because `low`/`high` are required positional arguments.
**Resolution: `LinearColorMapper(palette=...)` with `domain=[(renderer, column)]`** — the only
mechanism measured to follow a `CDSView`. `ColorBar` has no range of its own, so fixing the
mapper fixes the bar. The mapper must be built *after* the renderer exists.

### 4.4 UPHELD — Q8, degenerate subsets

Stata is **not uniform**: `lfit`/`lfitci`/`lpoly`/`lpolyci`/`kdensity` at 1 observation return
rc 2001 and **abort the whole graph**, taking the companion scatter with them, while
`qfit`/`fpfit` return rc 0 and draw nothing; at 0 observations the split differs again. The
root cause is `lfit` re-raising any rc other than 2000 while `qfit` re-raises nothing —
deliberate in the code, undocumented, and arbitrary rather than principled.

**Resolution: keep the uniform graceful policy and document the divergence.** Every layer type
warns and draws nothing. Losing an entire dashboard because one layer's qualifier matched one
row is a worse outcome than a missing layer.

### 4.5 REFINED — Q6, inline/analytic layers

Stata **evaluates** the qualifier on `scatteri`/`pci`/`function` — rc 111 for a bad variable
name, rc 198 for an out-of-range `in` — and then **silently discards it**.

**Resolution: validate like Stata, then warn instead of staying silent.** A typo is still an
error; a valid-but-inapplicable qualifier gets the named warning rather than Stata's silence.
A deliberate, documented divergence, on the grounds that silently dropping a user's `if` is
the exact pattern this project exists to remove.

### 4.6 NEW — S1, `||` bar-syntax binding

In `||` syntax a trailing `if` binds to the **last plot**, not the command:
`twoway scatter mpg weight if foreign==1 || lfit mpg weight` gives a 22-obs scatter and a
**full-sample** fit. Command-level scope requires the explicit empty final segment `|| if exp`.
`dash.ado:1496` promotes on a different rule (`n_segs == 1`).

**Resolution: probe dash's behaviour against the Stata table first, then decide.** If dash
already matches, pin it with a regression test; if it diverges, fix it here, because qualifier
scoping is precisely this phase's subject.

### 4.7 NEW — S2, `by()` swallowing a fatal rc

Under `by()`, a layer whose qualifier leaves too few rows prints `insufficient observations`,
returns **rc 0**, and Stata silently **deletes the entire panel** — including its valid scatter
layer.

**Resolution: do not reproduce it.** Keep the panel, warn, draw the failing layer empty —
consistent with 4.4.

### 4.8 Findings carried forward but out of scope

Recorded here so the plan can cite them and a later phase can pick them up:

- **D2** — private sources are invisible to the filter callback *generally*
  (`clean_source`, `seg_source`, `dl_source`, every computed mapper's CDS). Bounds what Epic B
  can promise; the NaN decision reduces but does not eliminate it.
- **D6** — `in_expr` silently discards `in 1/l`, `in f/20`, `in -10/-1`, `in 10`, `1 / 10`.
- **D7** — `mpg>20` excludes missing where **Stata includes it**. A silent wrong answer in the
  qualifier translator itself, affecting graph-level qualifiers too.
- **B1** — a callback that grows a source leaves `BooleanFilter.booleans` at the old length,
  silently hiding the new rows.
- **F-A** — a **linked** `by()` graph already draws an identical computed layer in every panel
  with no qualifier involved; the `row_mask` fix closes it, but it is its own user-visible bug
  deserving its own test and changelog line.
- The emitted app's facet/total agg entries omit the `'opts'` key, so `agg.get('opts') or {}`
  degrades silently for faceted layers.
- `kdensity`'s third serset column holds unrestricted values in Stata; unresolved, and only
  bites if dash is ever compared against a serset dump rather than the drawn curve.
