# Web research: Bokeh 3.8/3.9, ECMAScript/Python number text, PEPs, formats, server ports, headless Chrome

> Written 2026-09-25 for the WP-28 plan (`.ultraplan/DISCOVERY.md`). Every claim carries its source
> URL. "Measured" means run on this machine today: macOS (Darwin 25.5), Homebrew Python 3.14.5 with
> Bokeh 3.9.0 / numpy 2.4.3 / pandas 3.0.1 / tornado 6.5.5, Stata-linked `/opt/anaconda3/bin/python3`
> 3.13.9 with Bokeh 3.8.0 / numpy 2.3.5 / pandas 2.3.3, node v24.13.1 (ICU 78.2, full-icu),
> Google Chrome 153.0.8010.54, StataMP (batch). Bokeh sources were read at the `3.9.0` git tag
> (`https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/...`) and compared with `3.8.0` where noted.
> "Latest" docs at docs.bokeh.org are now **3.10.0 (Aug 2026)**, which requires Python >= 3.12; do not
> cite `en/latest` as if it were 3.9.

---

## 1. Bokeh

### 1a. `LegendItem` with a label but no renderers

**Answer: allowed, and BokehJS draws it as a text-only row (label with an empty glyph cell).**
No placeholder glyph is needed.

- Python side: `LegendItem.renderers = List(Instance(GlyphRenderer))` (default empty list); the only
  validations are `NON_MATCHING_DATA_SOURCES_ON_LEGEND_ITEM_RENDERERS` and `BAD_COLUMN_NAME`, both
  conditional on the label being a *field*. A *value* label with `renderers=[]` raises no error or
  warning. `LegendItem.__init__` converts a plain `str` label to `value(label)`:
  `if isinstance(self.label, str): self.label = value(self.label)`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/annotations/legends.py
- BokehJS: `LegendItem.get_labels_list_from_label_prop()` returns `[value]` for a value label
  regardless of renderers (`if (isValue(this.label)) { const {value} = this.label; return value != null ? [value] : [] }`);
  only a *field* label with no renderers yields the text `"No source found"`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/annotations/legend_item.ts
- `LegendView._render_items()` creates one entry per label (`glyph` canvas layer + `label_el`);
  the glyph is painted by `for (const renderer of item.renderers) view?.draw_legend(...)`, which
  simply runs zero times, and `_draw_legend_items` still draws the label text. There is no
  `renderers.length == 0` filter anywhere in legend.ts. `is_visible` only requires
  `items.length != 0 && some(items, item => item.visible)`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/annotations/legend.ts
- Version caveat: the DOM/HTML legend (`_render_items`, `legend_css`) arrived in **3.7.0** (present in
  3.7.0/3.8.0/3.9.0 legend.ts; absent in 3.6.0 and earlier). The pre-3.7 canvas legend has the same
  semantics (entries from `get_labels_list_from_label_prop`, glyph loop over `item.renderers`,
  text painted unconditionally, legend.ts 3.6.0 lines 123-129 and 428-435).
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.6.0/bokehjs/src/lib/models/annotations/legend.ts ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.7.0/bokehjs/src/lib/models/annotations/legend.ts
- Click policy: `is_active` for `"hide"` is `every(item.renderers, r => r.visible)`; `every([])` is
  true, so a label-only row never renders "inactive" and clicking it toggles nothing (legend.ts
  lines 594-604). A label-only row can still be clicked (a `LegendItemClick` event fires).
- A label-only item is the accepted way to get a text-only line; `visible=False` on a renderer does
  **not** remove it from the legend (the user guide hides *items* with `p.legend.items[1].visible = False`,
  and "If all items in a legend are invisible, the entire legend will be hidden").
  Source: https://docs.bokeh.org/en/latest/docs/user_guide/basic/annotations.html
- Renaming after construction: `LegendItem.label` is a `NullStringSpec`; **a plain string assigned
  after `__init__` is a field name, not a value** ("By default, string values are interpreted as
  fields, but you can use the |value| function": `m.title = value("foo") # value`, `m.title = "foo" # field`).
  Use `item.label = value("text")` (or `dict(value="text")`).
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/core/property/dataspec.py

### 1b. `Axis.major_label_overrides` with a `FixedTicker`

- Property: `major_label_overrides = Dict(Either(Float, String), TextLike, default={})`,
  "Provide explicit tick label values for specific tick locations that override normal formatting."
  Identical in 3.8.0 and 3.9.0.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/axes.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.8.0/src/bokeh/models/axes.py
- Keys must equal the tick *numbers*. BokehJS builds `_major_label_views` as a `Map` keyed by the
  deserialised key and looks labels up with `_major_label_views.get(ticks[i])` in `compute_labels`
  (axis.ts lines 126-129 and 545-556): a `Map.get` with a number key. The JS type is
  `Mapping(Or(Str, Float), Or(Str, Ref(BaseText)))`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/axes/axis.ts
- **Int vs float keys are equivalent in Bokeh 3.x**: Python dicts are serialised as
  `{"type":"map","entries":[[encode(key), encode(val)], ...]}` (`Serializer._encode_dict`), and the JS
  deserialiser rebuilds a `Map` (`case "map": return this._decode_map(...)`), so `1` and `1.0` both
  become the JS number `1` and match tick `1`. A *string* key `"1"` never matches a numeric tick.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/core/serialization.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/core/serialization/deserializer.ts
  The old bug "major_label_overrides are not applied if the overrides are float but the original
  labels are int" (#11930, Bokeh 2.4, string comparison `'1' != '1.0'`) does not apply to the 3.x
  map transport; the safe habit remains to key with the exact numbers you give `FixedTicker(ticks=...)`
  (non-integer ticks must match to the bit, so generate keys and ticks from the same list).
  Source: https://github.com/bokeh/bokeh/issues/11930
- Secondary axis: it is the same `Axis` property, so it works on a `LinearAxis(y_range_name=...)`
  added with `p.add_layout(..., "right")` (the twin-axes recipe: named ranges in `extra_y_ranges`,
  `y_range_name` on the glyph, `LinearAxis` via `add_layout`).
  Source: https://docs.bokeh.org/en/latest/docs/user_guide/basic/axes.html
- Multi-line: string overrides are parsed by `parse_delimited_string` and rendered as a `TextBox`,
  whose `_size()`/`nlines` split on `"\n"` (`const lines = this.text.split("\n")`), and
  `infer_text_height()` switches to `"ascent_descent"` when the text contains `"\n"` — so
  `"1\nQ1"` renders as two lines. Caveat: `parse_delimited_string` treats `$$...$$`, `\[...\]` and
  `\(...\)` as LaTeX delimiters, so a label containing `$$` is drawn as MathText.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/core/graphics.ts ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/text/utils.ts

### 1c. `CustomJSTickFormatter`

- Properties: `args` ("A mapping of names to Python objects ... made available to the formatter's
  code snippet as named parameters") and `code` ("A snippet of JavaScript code that reformats a
  single tick to the desired format"). Variables in scope: `tick` (the unformatted tick value),
  `ticks` (array of all ticks the ticker positioned), `index` (position of `tick` in `ticks`), plus
  the `args` names. The doc example keeps state on `this`:
  `this.precision = this.precision || (ticks.length > 5 ? 1 : 2); return Math.floor(tick) + " + " + (tick % 1).toFixed(this.precision);`
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/formatters.py
- BokehJS builds `new Function("tick", "index", "ticks", ...argNames, code)` and calls it per tick,
  coercing the return with a template string (`${func(...)}`), with a fresh `this` cache per
  `doFormat` call.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/formatters/customjs_tick_formatter.ts
- User-guide form: `p.yaxis.formatter = CustomJSTickFormatter(code="""return Math.floor(tick) + " + " + (tick % 1).toFixed(2)""")`.
  Source: https://docs.bokeh.org/en/latest/docs/user_guide/styling/plots.html
- Replacing a `DatetimeTickFormatter`: assign the same way to the datetime axis
  (`p.xaxis.formatter = CustomJSTickFormatter(...)`, or `p.xaxis[0].formatter`). `tick` is then
  **floating-point milliseconds since the Unix epoch**, because Bokeh converts every datetime to
  that unit (`convert_datetime_type`: "Convert any recognized date, time, or datetime value to
  floating point milliseconds since epoch"; `convert_datetime_array` likewise).
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/util/serialization.py
  `DatetimeAxis` defaults to `DatetimeTickFormatter`, whose per-resolution strings
  (`microseconds`="%fus", `milliseconds`="%3Nms", `seconds`="%Ss", `minsec`, `minutes`, `hourmin`,
  `hours`, `days`="%m/%d", `months`="%m/%Y", `years`="%Y") follow strftime plus Bokeh extensions;
  a custom formatter loses the resolution switching and must implement its own.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/formatters.py

### 1d. `CustomJSHover`

- `code`: "A snippet of JavaScript code to transform a single value. The variable `value` will
  contain the untransformed value ... Additionally, the variable `special_vars` will be available"
  with `x`, `y`, `sx`, `sy`, `data_x`, `data_y`, `indices`, `name` (and `segment_index` for multi
  glyphs). "The value of the format passed in the tooltip specification is available as the
  `format` variable. The snippet will be made into the body of a function and therefore requires a
  return statement." `args`: names to Bokeh models exposed as parameters.
- Wiring: `HoverTool(tooltips=[('lat', '@y{custom}')], formatters={'@y': lat_custom})` — the
  `formatters` keys are the `@field`/`$var` names, the values are `"numeral" | "datetime" | "printf"`
  or a `CustomJSHover` instance (`formatters = Dict(String, Either(Enum(TooltipFieldFormatter), Instance(CustomJSHover)))`),
  and whatever is inside `{...}` on the tooltip becomes `format` in the snippet (`{custom}` is
  just a conventional value). Default scheme when none is given: `"numeral"`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/tools.py
- Datetime columns reach `value` as epoch milliseconds (see 1c). Version note: 3.8.0 added
  `filters`, `sorters` and limits to `HoverTool` (not needed here).
  Source: https://docs.bokeh.org/en/3.8.0/docs/releases.html

### 1e. Slider `format`

- `AbstractSlider.format = Either(String, Instance(TickFormatter))` (already so in 3.0.0).
  Defaults: `Slider`/`RangeSlider` `"0[.]00"`, `DateSlider`/`DateRangeSlider` `"%d %b %Y"`,
  `DatetimeRangeSlider` `"%d %b %Y %H:%M:%S"`. `RangeSlider.value = Required(Tuple(Float, Float))`,
  `DateRangeSlider.value = Required(Tuple(Datetime, Datetime))`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/widgets/sliders.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.0.0/src/bokeh/models/widgets/sliders.py
- **A `RangeSlider` can carry a `CustomJSTickFormatter`.** BokehJS: `RangeSliderView._formatter`
  is `isString(format) ? numbro.format(value, format) : format.compute(value)`; `DateRangeSliderView`
  is `isString(format) ? datetime(value, format) : format.compute(value)`. `TickFormatter.compute(tick)`
  is `this.doFormat([tick], {loc: 0})[0]`, so inside a `CustomJSTickFormatter` used on a slider
  `ticks` is a one-element array and `index` is 0. The title shows `start.map(v => this.pretty(v)).join(" .. ")`
  and tooltips use the same `pretty`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/widgets/sliders/range_slider.ts ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/widgets/sliders/date_range_slider.ts ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/formatters/tick_formatter.ts ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/widgets/sliders/abstract_slider.ts
- String formats: numeric sliders use numbro syntax, date sliders use Bokeh's `tz`/strftime-style
  syntax (`datetime(value, format)`); a date slider given a numbro string, or vice versa, is wrong.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/core/util/templating.ts

### 1f. `Select` option values

- **Values need not be strings since Bokeh 3.4.0.** 3.9.0:
  `Options = List(Either(String, Tuple(AnyRef, String)))`, `OptionsGroups = Dict(String, Options)`,
  `Select.options = Either(Options, OptionsGroups)`, `Select.value = AnyRef(default="")`; help:
  "a list of tuples, each of the form (value, label), where value can be of any type, not
  necessarily a string." 3.4.0 had `Tuple(Any, String)` / `value = Any`; 3.3.0 was
  `Tuple(String, String)` / `value = String`. `MultiSelect` and `MultiChoice` remain string-only.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/widgets/inputs.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.4.0/src/bokeh/models/widgets/inputs.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.3.0/src/bokeh/models/widgets/inputs.py
- How BokehJS does it: `<option value=label>` elements are built from the *labels*; a
  `_known_values: Map<Value, Label>` maps each original value to its label; on change the selected
  label is looked up back to the original value (`[..._known_values].find(([_, label]) => selected_label == label)`),
  and `_update_value` sets `input_el.value = _known_values.get(value)`. Consequences: (1) numeric
  values round-trip as JS numbers, so a `CustomJS` can compare `select.value === col[i]` without
  parsing; (2) **labels must be unique** — a duplicate label resolves to the first value;
  (3) a value with no matching label leaves the widget with `selectedIndex = -1`.
  Source: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/widgets/select.ts
- So the "string value plus parallel mapping" workaround is unnecessary on 3.4+; on Bokeh < 3.4 it
  would be required. The declared floor (1h) is 3.8, so numeric values may be used directly.

### 1g. Ranges: `Range1d`, `bounds`, `DataRange1d`

- `Range1d`: "A fixed, closed range [start, end]"; `bounds`: "The bounds that the range is
  allowed to go to. Typically used to prevent the user from panning/zooming/etc away from the
  data. If set to 'auto', the bounds will be computed to the start and end of the Range."
  `min_interval`/`max_interval` limit zoom. User guide: `p.y_range = Range1d(0, 15, bounds=(0, None))`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/ranges.py ,
  https://docs.bokeh.org/en/latest/docs/user_guide/basic/axes.html
- A `Range1d` narrower than the data does not "hide" data in the model sense: glyphs are painted
  and then clipped to the frame — `PlotCanvasView._paint_levels` does `ctx.rect(...clip_box.args); ctx.clip()`
  around each render level — so points outside the range are simply not visible, and panning
  reveals them unless `bounds` forbid it. (Very distant coordinates may also fail to draw on some
  browsers, a canvas limitation noted in the `Line` glyph reference with issue #11498.)
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/plots/plot_canvas.ts ,
  https://docs.bokeh.org/en/3.5.0/docs/reference/models/glyphs/line.html
- `DataRange1d`: "By default, the `start` and `end` of the range automatically assume min and max
  values of the data for associated renderers"; `renderers`: "An explicit list of renderers to
  autorange against. If unset, defaults to all renderers on a plot"; `only_visible`: "If True,
  renderers that are not visible will be excluded from automatic bounds computations" (default
  **False**, so invisible renderers still count); `range_padding` (default 0.1, percent or
  absolute via `range_padding_units`); `bounds` default None, `'auto'` = the computed start/end.
  In BokehJS `start`/`end` given at construction are captured as `_initial_start`/`_initial_end`
  (`isNaN(this.start) ? null : this.start`) and then **pin that side** of the computed range
  (`if (this._initial_start != null) start = this._initial_start`), while the other side keeps
  auto-fitting; the visibility filter is `r.visible || !this.only_visible`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/ranges.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/ranges/data_range1d.ts
- Idiomatic "hull of the data plus extra values": two options. (a) Python-side `Range1d` from the
  numbers you already know (`Range1d(start=min(data_min, extra...), end=max(...))`, add your own
  padding) — deterministic, pinned, testable without a browser, and what a Stata axis fixture
  compares best against. (b) Keep `DataRange1d` and add the extra values as a renderer that is in
  the range's `renderers` (or all renderers) — an invisible `scatter(visible=False)` still counts
  because `only_visible` defaults to False. A `DataRange1d(start=x)` fixes only that side.
  Bokeh's docs do not name one of these as canonical; (a) is the one that survives `only_visible`
  and legend-hide interactions unchanged.

### 1h. Minimum Python per Bokeh release, `CustomJSTicker`, numpy/pandas floors

PyPI metadata (`requires_python`, `requires_dist`, first-file upload date) per release:

| Bokeh | requires_python | classifiers | numpy | pandas | tornado | first upload |
|---|---|---|---|---|---|---|
| 3.0.0 | >=3.8 | 3.8-3.10 | >=1.11.3 | >=1.2 | >=5.1 | 2022-10-31 |
| 3.1.0 | >=3.8 | 3.8-3.11 | >=1.16 | >=1.2 | >=5.1 | 2023-03-10 |
| 3.2.0 | >=3.9 | 3.9-3.11 | >=1.16 | >=1.2 | >=5.1 | 2023-06-21 |
| 3.3.0 | >=3.9 | 3.9-3.12 | >=1.16 | >=1.2 | >=5.1 | 2023-10-10 |
| 3.4.0 | >=3.9 | 3.9-3.12 | >=1.16 | >=1.2 | >=6.2 | 2024-03-14 |
| 3.5.0 | >=3.10 | 3.10-3.12 | >=1.16 | >=1.2 | >=6.2 | 2024-07-04 |
| 3.6.0 | >=3.10 | 3.10-3.12 | >=1.16 | >=1.2 | >=6.2 | 2024-09-26 |
| 3.7.0 | >=3.10 | 3.10-3.13 | >=1.16 | >=1.2 (+narwhals>=1.13) | >=6.2 | 2025-03-12 |
| 3.8.0 | >=3.10 | 3.10-3.13 | >=1.16 | >=1.2 (+narwhals>=1.13) | >=6.2 | 2025-08-29 |
| 3.9.0 | >=3.10 | 3.10-3.14 | >=1.16 | **not required** (narwhals>=1.13) | >=6.2 | 2026-03-11 |
| 3.9.1 | >=3.10 | | | | | 2026-06-04 |
| 3.10.0 | **>=3.12** | 3.12-3.14 | >=1.16 | extra `pandas>=2.0` | >=6.2 | 2026-08-18 |

Sources: https://pypi.org/pypi/bokeh/3.0.0/json , https://pypi.org/pypi/bokeh/3.1.0/json ,
https://pypi.org/pypi/bokeh/3.2.0/json , https://pypi.org/pypi/bokeh/3.3.0/json ,
https://pypi.org/pypi/bokeh/3.4.0/json , https://pypi.org/pypi/bokeh/3.5.0/json ,
https://pypi.org/pypi/bokeh/3.6.0/json , https://pypi.org/pypi/bokeh/3.7.0/json ,
https://pypi.org/pypi/bokeh/3.8.0/json , https://pypi.org/pypi/bokeh/3.9.0/json ,
https://pypi.org/pypi/bokeh/3.9.1/json , https://pypi.org/pypi/bokeh/3.10.0/json ;
`pyproject.toml` at tags 3.8.0 (`requires-python = ">=3.10"`, `pandas >=1.2`) and 3.9.0 (no pandas):
https://raw.githubusercontent.com/bokeh/bokeh/3.8.0/pyproject.toml ,
https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/pyproject.toml

- Release notes confirm the steps: 3.2.0 "Official support for Python 3.8 was removed";
  3.5.0 "Dropped support for Python 3.9"; 3.9.0 "Added support for Python 3.14", "Added support for
  Pandas 3", "Removed `pandas` as a required dependency"; 3.10.0 "requires Python 3.12 or newer".
  Sources: https://docs.bokeh.org/en/latest/docs/releases.html , https://docs.bokeh.org/en/3.9.0/docs/releases.html
- `CustomJSTicker` first appeared in **3.6.0** ("Added support for `CustomJSTicker` callback",
  PR 13988); `class CustomJSTicker` is absent from `tickers.py` at tag 3.5.0 and present at 3.6.0.
  Sources: https://docs.bokeh.org/en/3.6.0/docs/releases.html ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.5.0/src/bokeh/models/tickers.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.6.0/src/bokeh/models/tickers.py
- numpy/pandas floors for 3.8 and 3.9: Bokeh declares only `numpy >=1.16`; pandas `>=1.2` (3.8) and
  nothing (3.9, where pandas becomes optional through narwhals; "Added support for Pandas 3" is a
  3.9.0 note, so **pandas 3 with Bokeh 3.8 is untested by Bokeh**). dash imports pandas itself,
  so the plan must declare pandas independently of Bokeh.
- K2 floor as measured today (DISCOVERY Q8 wants the tested versions): the two suite interpreters
  are Stata's linked `/opt/anaconda3/bin/python3` = **Python 3.13.9, Bokeh 3.8.0, numpy 2.3.5,
  pandas 2.3.3** and Homebrew `python3` = **Python 3.14.5, Bokeh 3.9.0, numpy 2.4.3, pandas 3.0.1**
  (`ROADMAP.md` WP-25 records the same pair). `dash_setup.ado` still says 3.8 (`_dash_pymin` returns
  "3.8", `min_bokeh "3.0"`), and Python 3.8/3.9 binaries exist on this machine only as bare
  interpreters. Both Bokeh floors above 3.4 mean numeric `Select` values (1f) are safe.

### 1i. Reordering / renaming legend items; separators

- `Legend.items` is an ordinary `List(Instance(LegendItem))` property ("This can be specified
  explicitly ... But as a convenience, can also be given more compactly as a list of tuples");
  order in the list is display order. Reassign (`legend.items = [...]`) or mutate in place:
  Bokeh wraps list properties in `PropertyValueList`, whose `__setitem__`, `append`, `insert`,
  `reverse`, `sort`, `__delitem__`, `__iadd__` are `@notify_owner`-decorated, so in-place
  `legend.items.reverse()`/`.sort(key=...)` also trigger a document change.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/models/annotations/legends.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/core/property/wrappers.py
  Maintainer statement (2017): "Their order in this list is the order they appear visually in the
  legend. You can re-order this .items list to be in whatever order you like."
  Source: https://discourse.bokeh.org/t/legend-ordering/2224
- Rename: `item.label = value("new text")` (a bare string after construction is a *field*, 1a).
- Separators/section headers: **no such model**. Every entry is a grid cell (`ncols`/`nrows`
  layout in legend.ts); the nearest tools are a label-only `LegendItem` (1a) as a header row,
  `Legend.title` (`Nullable(TextLike)`) for one heading, or several `Legend` annotations added with
  `add_layout`. No open Bokeh issue proposes separators (searches returned only ordering and
  visibility issues, e.g. #1358, #7672).
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/bokehjs/src/lib/models/annotations/legend.ts ,
  https://github.com/bokeh/bokeh/issues/1358

---

## 2. Number-to-text thresholds: ECMAScript vs Python

- ECMAScript `Number::toString` (ES2015 §7.1.12.1, unchanged in the current spec §6.1.6.1.20):
  with `n, k, s` such that `10^(k-1) <= s < 10^k` and `s × 10^(n-k)` is the value: "If k ≤ n ≤ 21"
  → integer digits plus `n−k` zeros; "If 0 < n ≤ 21" → fixed with a decimal point; "If −6 < n ≤ 0"
  → `0.` followed by `−n` zeros and the digits; otherwise exponential `d.ddde±x` with `abs(n−1)`
  as the exponent (no leading zeros). Hence decimal notation for `1e-6 <= |x| < 1e21`.
  Source: https://262.ecma-international.org/6.0/#sec-tostring-applied-to-the-number-type
  (current text: https://tc39.es/ecma262/#sec-numeric-types-number-tostring)
- MDN states it plainly: "Scientific notation is used if radix is 10 and the number's magnitude
  (ignoring sign) is greater than or equal to 10^21 or less than 10^-6."
  Source: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Number/toString
- Measured (node v24.13.1): `1e20 → "100000000000000000000"`, `1e21 → "1e+21"`,
  `1e-6 → "0.000001"`, `1e-7 → "1e-7"`, `1e16 → "10000000000000000"`,
  `12345678901234567890 → "12345678901234567000"`. Note the JS exponent has no zero padding
  (`1e-7`, `1e+21`) whereas Python pads to two digits (`1e-07`).
- Python `repr(float)`/`str(float)` (same since 3.2): CPython `format_float_short`, format code
  `'r'`: `if (decpt <= -4 || decpt > 16) use_exp = 1;` with the comment "convert to exponential
  format at 1e16. We used to convert at 1e17 ...". For `'g'`: `if (decpt <= -4 || decpt > (add_dot_0_if_integer ? precision-1 : precision)) use_exp = 1;`.
  So repr is fixed for `1e-4 <= |x| < 1e16`, exponent otherwise.
  Source: https://raw.githubusercontent.com/python/cpython/main/Python/pystrtod.c
- Measured (Python 3.14.5): `repr(1e15) = '1000000000000000.0'`, `repr(9999999999999998.0) = '9999999999999998.0'`,
  `repr(1e16) = '1e+16'`, `repr(0.0001) = '0.0001'`, `repr(9e-05) = '9e-05'`.
- Python's documented `'g'` rule (format spec): with `exp` from `'e'` formatting at precision
  `p-1`, "if m <= exp < p, where m is -4 for floats ... the number is formatted with presentation
  type 'f' ... Otherwise ... 'e' ... insignificant trailing zeros are removed"; the `None` type
  (what `str()` uses) "switches to the scientific notation when exp >= p - 1" with p "as large as
  needed to represent the given value faithfully".
  Source: https://docs.python.org/3/library/string.html#format-specification-mini-language
- Consequence for the shared Python/JavaScript format writer: neither `String(x)` nor `str(x)`
  can be the fallback path — the two twins disagree between `1e-6..1e-4` and `1e16..1e21`, and on
  exponent padding. Both twins must format explicitly (fixed digits or a hand-written `%e`).

---

## 3. Python annotations: PEP 563 / 585 / 604

- PEP 585 (`list[int]`, `dict[str, int]`, `tuple[int, ...]`, `type[X]`) is implemented in
  **3.9**; before that evaluating them raises `TypeError: 'type' object is not subscriptable`.
  Source: https://peps.python.org/pep-0585/
- PEP 604 (`X | Y`) is implemented in **3.10**; before that `TypeError: unsupported operand
  type(s) for |: 'type' and 'type'` (and `... and 'NoneType'` for `int | None`).
  Source: https://peps.python.org/pep-0604/
- Because annotations are evaluated at definition time without the future import, these errors
  fire **at import** of the module (when the `def`/class body/annotated assignment executes).
  With `from __future__ import annotations` (PEP 563, available since 3.7) they are stored as
  strings and not evaluated; `typing.get_type_hints()` on them still fails on the old interpreter.
  PEP 563 is "Superseded" by PEP 649/749 (Python 3.14 defers evaluation by default), but the
  future import remains supported in 3.14.
  Sources: https://peps.python.org/pep-0563/ , https://docs.python.org/3/whatsnew/3.14.html
- Placement: "A future statement must appear near the top of the module. The only lines that can
  appear before a future statement are: the module docstring (if any), comments, blank lines, and
  other future statements." `annotations` is the only feature that still needs it.
  Source: https://docs.python.org/3/reference/simple_stmts.html#future-statements
- Measured on this machine (`/usr/local/bin/python3.8` 3.8.16, `python3.9` 3.9.16, `python3.10`
  3.10.10, anaconda 3.13.9): on 3.8 `def f(x: list[int])` raises TypeError and `int | None` raises
  TypeError; on 3.9 `list[int]` is fine but `int | None` raises; on 3.10+ both fine; on all four,
  `import os` followed by the future import raises `SyntaxError: from __future__ imports must occur
  at the beginning of the file`, while docstring + comment before it is accepted; with the future
  import both syntaxes import cleanly on 3.8 and 3.9 (but `typing.get_type_hints` then raises the
  same TypeErrors there).

---

## 4. `%g`-style formatting, Stata's `%w.dg`, thousands separators with a comma decimal

- No stdlib function reproduces Stata's width-driven `%w.dg`. Python's `'g'` is
  precision-driven (`'{:.{p}g}'` → p significant digits, exponent when `exp < -4` or `exp >= p`,
  trailing zeros stripped); there is no "fit the width" mode, and `'{:9g}'` only pads.
  Source: https://docs.python.org/3/library/string.html#format-specification-mini-language
- Stata's rule (help format): "%g differs from %f in that (1) it decides how many digits to
  display to the right of the decimal point, and (2) it will switch to a %e format if the number
  is too large or too small"; "%w.dgc is %w.dg, with commas"; "You may substitute comma (,) for
  period (.) in any of the above formats to make comma the decimal point", e.g. `%9,2fc` shows
  1000.03 as `1.000,03`.
  Source: https://www.stata.com/help.cgi?format
- Measured in StataMP batch today (`display %9.0g x` etc.), for the fixture designer:

  | value | %9.0g | %10.0gc | %9,0g | %12.0g | %9.2f | %10.3e |
  |---|---|---|---|---|---|---|
  | 3.14159265358979 | `3.141593` | `3.1415927` | `3,141593` | `3.141592654` | `3.14` | `3.142e+00` |
  | 123456789 | `1.23e+08` | `1.235e+08` | `1,23e+08` | `123456789` | | |
  | 1234567 | `1234567` | `1234567` | | | | |
  | 12345678 | `1.23e+07` | `12345678` | `1,23e+07` | | | |
  | 1234567.891 | `1234568` | `1234567.9` | | | | |
  | -123456.789 | `-123456.8` | `-123,456.8` | `-123456,8` | | | |
  | 0.0001 | `.0001` | `.0001` | `,0001` | | | |
  | 0.000012345 | `.0000123` | `.00001234` | `,0000123` | | | |
  | 1e-7 | `1.00e-07` | `1.000e-07` | `1,00e-07` | | | |
  | 1e16 | `1.00e+16` | `1.000e+16` | `1,00e+16` | | | |
  | 1000.03 | `1000.03` | `1,000.03` | `1000,03` | | | |

  Observed pattern (measured, not documented): `%w.0g` shows at most `w-2` significant digits
  (7 for width 9, 8 for width 10, 10 for width 12), drops the leading `0` before the decimal point,
  switches to `d.dde±xx` with `w-7` mantissa decimals when the integer part needs more than `w-2`
  digits or the value would show too few significant digits (`1e-7` → `1.00e-07` although
  `.0000001` fits), and `%w.dg` with `d>0` keeps `d` decimals (`%12,2gc` 1234567.891 → `1.234.568`).
  Python's closest single call, `'{:.{w-2}g}'`, matches the plain cases (`'{:.7g}'.format(1234567.891) = '1234568'`)
  but not the exponent form (`'{:.7g}'.format(123456789) = '1.234568e+08'` vs Stata `1.23e+08`),
  the dropped leading zero (`0.0001` vs `.0001`), or the small-number switch; the writer must be
  hand-coded and pinned by the Stata fixture the plan already calls for.
- Thousands separator with a European comma decimal, Python: format with `','` grouping then swap
  the two characters in one pass — `format(1234567.891, ',.2f').translate(str.maketrans(',.', '.,'))`
  → `'1.234.567,89'` (measured). `str.translate` maps "each character ... through the given
  translation table" in a single pass, so the swap cannot collide (unlike two `replace` calls).
  The `'n'` presentation type and `locale.format_string` need `setlocale`, which "is not
  thread-safe on most systems", "affects the entire program", and depends on the locale being
  installed (`locale.Error` otherwise) — unsuitable for a library.
  Sources: https://docs.python.org/3/library/stdtypes.html#str.translate ,
  https://docs.python.org/3/library/locale.html
- JavaScript: the same explicit approach — `x.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",")`
  then swap — keeps the two twins byte-identical. `Intl.NumberFormat("de-DE")` gives
  `1.234.567,89` and needs no network (ICU data ships with the engine), but (1) output is
  implementation-dependent — "implementations may not always be up to date", unknown locales are
  "ignored ... eventually falling back to the system's locale"; (2) separators are locale
  characters, e.g. `fr-FR` yields `1 234 567,89` with U+202F (measured); (3) Node built with
  `small-icu` has English data only ("Prints either 'M01' or 'January' on small-icu"), although
  official binaries are `full-icu` (measured: node v24 `hasFullICU true`). `formatToParts()`
  exposes `group`/`decimal` parts if Intl is used.
  Sources: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl ,
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat ,
  https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl/NumberFormat/formatToParts ,
  https://nodejs.org/api/intl.html

---

## 5. Bokeh server: port in use, pre-checks, readiness

- `bokeh serve` wraps `Server(...)` construction in `report_server_init_errors`, which on
  `OSError` with `errno.EADDRINUSE` logs **`Cannot start Bokeh server, port {port} is already in use`**
  at CRITICAL (to stderr through logging), `EADDRNOTAVAIL` → `Cannot start Bokeh server, address
  '{address}' not available`, anything else → `Cannot start Bokeh server [{ERRNO_NAME}]: {strerror}`,
  and then **`sys.exit(1)`**. Startup logs `Bokeh app running at: {url}`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/command/util.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/command/subcommands/serve.py
- A bare `Server(...)` (what dash's generated app does) has no such handler: `Server.__init__`
  calls `bind_sockets(opts.address, opts.port)` → `tornado.netutil.bind_sockets(port=port or 0, address=address)`,
  and the `OSError` propagates (sockets already created are closed in the `except Exception:` block).
  With `address=None` Tornado binds every interface; port 0 asks the OS for a free port and the
  chosen port is read back from `getsockname()`.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/server/server.py ,
  https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/server/util.py ,
  https://www.tornadoweb.org/en/stable/netutil.html
- errno values: `EADDRINUSE` = **48** on macOS/XNU, **98** on Linux; Python surfaces it as
  `OSError: [Errno 48] Address already in use`, and an uncaught exception ends the interpreter
  with exit status 1 (measured).
  Sources: https://raw.githubusercontent.com/apple-oss-distributions/xnu/main/bsd/sys/errno.h ,
  https://raw.githubusercontent.com/torvalds/linux/master/include/uapi/asm-generic/errno.h ,
  https://docs.python.org/3/library/socket.html
- **Measured (Bokeh 3.9.0, tornado 6.5.5, macOS)** with a listening "holder" socket:
  - holder on `127.0.0.1:P`: `Server(port=P, address="127.0.0.1")` and `address="localhost"` →
    rc 1, `OSError: [Errno 48] Address already in use`; `bokeh serve --address 127.0.0.1 --port P`
    → rc 1, `Cannot start Bokeh server, port P is already in use`; **but** `Server(port=P)` with the
    default (all-interfaces) address and plain `bokeh serve --port P` **start successfully**,
    whether or not the holder set `SO_REUSEADDR` (BSD allows a wildcard bind beside a specific
    one when the new socket sets `SO_REUSEADDR`, which Tornado does).
  - holder on `0.0.0.0:P`: the wildcard binds fail (rc 1) and the loopback binds succeed.
  So the F1 cscript must hold the socket on the **same address the app binds**. dash's generated
  app maps `--address None` to `'127.0.0.1'` (`_kw = {'address': address or '127.0.0.1'}`,
  dash_render.py ~27320), so a holder bound to `127.0.0.1` is the right fixture there; a Linux CI
  box behaves the same for the specific-address case but Linux rejects wildcard-beside-specific,
  so do not rely on the macOS-only "no conflict" cases.
- Pre-launch bind test: `socket.socket().bind(("127.0.0.1", port))` raises `OSError` errno
  `EADDRINUSE` when held (measured; `bind` "Raises ... OSError" per the socket docs; `create_server`
  sets `SO_REUSEADDR` on POSIX). It is inherently racy (TOCTOU) and still misses the wildcard
  cases above, so the child's exit status and stderr must remain the authority; a bind test only
  gives a friendlier early message.
  Source: https://docs.python.org/3/library/socket.html
- Readiness: Bokeh documents no readiness endpoint; the practical signal is HTTP. Per-app routes
  are `/?` (DocHandler), `/ws`, `/metadata`, `/autoload.js`; `bokeh serve` also serves an index at
  `/` unless `--disable-index`. Measured: after `Bokeh app running at: http://localhost:N/cli_app`
  appears (0.32 s after launch), the first `GET` of the app URL and of `/metadata` both return 200.
  dash's own launcher registers `/health` through `Server(extra_patterns=[('/health', _HealthHandler)])`
  (dash_render.py ~27353), which `bokeh serve` cannot add, so polling `/health` works only for the
  self-serving launcher; poll the app root or `/metadata` for a `bokeh serve`-launched app.
  Sources: https://raw.githubusercontent.com/bokeh/bokeh/3.9.0/src/bokeh/server/urls.py ,
  https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html
- `--port`: `type=int`, default 5006; "passing 0 as the port number allows the system to select an
  arbitrary port, with the actual port number logged at startup". Bokeh itself does no range
  validation, so the "outside 1024-65535 is refused" rule in DISCOVERY Q12 must be dash's own
  (the generated app currently *clamps*: `_port = max(1024, min(int(_a.port), 65535))`).
  Source: https://docs.bokeh.org/en/latest/docs/reference/command/subcommands/serve.html

---

## 6. Headless Chrome for layout tests

- Since Chrome 112 headless "creates, but doesn't display, any platform windows" (the unified
  "new" headless); "Since Chrome 132.0.6793.0 the old Headless mode is only available as a
  standalone binary named `chrome-headless-shell`". Chromium's README: "As of M132, headless shell
  functionality is no longer part of the Chrome binary, so --headless=old has no effect"; "As of
  M118, precompiled headless_shell binaries are available ... via Chrome for Testing".
  `IsHeadlessMode()` is simply `command_line.HasSwitch(switches::kHeadless)`, so `--headless`,
  `--headless=new` (the repo's current spelling) are equivalent today and `--headless=old` is inert.
  Sources: https://developer.chrome.com/docs/chromium/headless ,
  https://chromium.googlesource.com/chromium/src/+/main/headless/README.md ,
  https://raw.githubusercontent.com/chromium/chromium/main/chrome/browser/headless/headless_mode_util.cc
- The command switches used by `test/responsive_probe.py` still exist in the new headless command
  handler (Chromium `main`): `--dump-dom` "Print the serialized DOM (doctype +
  document.documentElement.outerHTML) to stdout"; `--screenshot` "Save a screenshot of the loaded
  page" (default `screenshot.png`); `--print-to-pdf` (default `output.pdf`); `--timeout` "Issues a
  stop after the specified number of milliseconds"; `--virtual-time-budget` (virtual time is
  fast-forwarded until the budget is exhausted, letting timers fire); `--default-background-color`;
  `--window-size=w,h` "Headless Chrome users historically use this to specify expected screenshot size".
  Sources: https://raw.githubusercontent.com/chromium/chromium/main/components/headless/command_handler/headless_command_switches.cc ,
  https://raw.githubusercontent.com/chromium/chromium/main/components/headless/command_handler/headless_command_handler.cc
- The 2017 "Getting started with Headless Chrome" article documents the same invocations
  (`--headless --disable-gpu --dump-dom URL`, `--screenshot --window-size=1280,1696`) and now
  carries a banner that it predates the new implementation; `--disable-gpu` was a Windows-only need.
  Source: https://developer.chrome.com/blog/headless-chrome
- `--dump-dom` serialises the DOM only; computed layout (`getBoundingClientRect`, computed styles)
  is not in it. The repo's approach — a host page whose script measures the dashboard and writes
  the numbers into the DOM before `--virtual-time-budget` expires, then `--dump-dom` — remains the
  Playwright-free way to read layout; nothing in the M112-M153 changes removes it. Local Chrome is
  153.0.8010.54 (measured).
