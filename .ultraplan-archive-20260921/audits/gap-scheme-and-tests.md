# `dash` audit — scheme pipeline and test coverage gaps

Repo: `/Users/billy/Desktop/Programs/StataPrograms/d/dash` @ `3948ce8` (branch `main`)
All line numbers verified against the working tree at audit time.

Method note: every claim below was executed, not read. Where a claim is a runtime
behaviour I ran `dash_render.py` against real inputs and recorded the output.
Where I could not determine something, it is marked **UNDETERMINED**.

---

# SECTION 1 — THE SCHEME PIPELINE

## 1.1 What `SchemeParser` parses

`SchemeParser` is `dash_render.py:687-1040`. The parse is generic
(`_parse_file`, `dash_render.py:808-852`: split on whitespace, `tokens[0]` =
category, `tokens[-1]` = value, middle tokens = subcategory), so the raw dict
holds whatever the file contains. But the only keys that ever become attributes
are the ones hard-requested in `_init_properties` (`dash_render.py:918-974`).

**108 distinct keys are requested. That is the complete set.**

| # keys | Key pattern | Requested at | Becomes |
|---|---|---|---|
| 1 | `color background` | 921 | `background_color` |
| 1 | `color plotregion` | 922 | `plotregion_color` |
| 1 | `color legend` | 923 | `legend_bg_color` |
| 1 | `color legend_line` | 924 | `legend_border_color` |
| 2 | `color major_grid`, `color grid` | 925-928 | `grid_color` |
| 1 | `color minor_grid` | 929 | `minor_grid_color` |
| 1 | `color heading` | 930 | `title_color` |
| 1 | `color axisline` | 931 | `axis_line_color` |
| 15 | `color p1`…`color p15` | 934-936 | `p_colors` |
| 15 | `color p1line`…`p15line` | 937-940 | `p_line_colors` |
| 15 | `color p1bar`…`p15bar` | 941-944 | `p_bar_colors` |
| 15 | `color p1mark`…`p15mark` | 945-948 | `p_mark_colors` |
| 15 | `symbol p1`…`symbol p15` | 951-953 | `p_symbols` |
| 15 | `linepattern p1line`…`p15line` | 956-958 | `p_line_patterns` |
| 1 | `linewidth p` | 961 | `default_line_width` |
| 1 | `linewidth major_grid` | 962 | `grid_line_width` |
| 1 | `intensity p` | 965 | `fill_alpha` |
| 1 | `intensity bar` | 966 | `bar_alpha` |
| 1 | `intensity area` | 967 | `area_alpha` |
| 1 | `gsize text` | 970 | `text_font_size` |
| 1 | `gsize heading` | 971 | `heading_font_size` |
| 1 | `gsize axis_title` | 972 | `axis_title_font_size` |
| 1 | `gsize tick_label` | 973 | `tick_label_font_size` |
| 1 | `gsize note` | 974 | `note_font_size` |

Value coercion helpers: `_color` 863, `_gsize` 873, `_intensity` 884,
`_lpattern` 893, `_lwidth` 897, `_symbol` 909.

## 1.2 What the rest of `dash_render.py` consumes

Exhaustive. `grep -n "scheme" dash_render.py` returns 83 hits; every hit that is
a *read* of the scheme object is below. There are exactly **three** consumer
entry points.

| Consumer | Call sites | Scheme attributes it touches |
|---|---|---|
| `SchemeParser.default_color()` (980) | 38 call sites in `GlyphMapper`: 1965, 2022, 2105, 2192, 2271, 2329, 2376, 2417, 2487, 2568, 2685, 2718, 2892, 2925, 3012, 3074, 3122, 3167, 3205, 3257, 3305, 3309, 3428, 3495, 3577, 3633, 3716, 3761, 3833, 3967, 4038, 4111 | `p_colors`, `p_line_colors`, `p_bar_colors` |
| `SchemeParser.apply_to_figure()` (1004) | **1 call site: 5661** (`DashRenderer._make_figure`) | `plotregion_color`, `background_color`, `axis_line_color`, `grid_color`, `grid_line_width`, `axis_title_font_size`, `tick_label_font_size` |
| `SchemeParser.css_block()` (1023) | 2 call sites: 6595 (`_render_bootstrap_html`), 7476 (`_assemble_layout`) | `background_color`, `title_color`, `heading_font_size`, `text_font_size`, `legend_bg_color` |

`self.scheme` is assigned at 5003/5005 (`DashRenderer.__init__`) and 1142/1144
(`GlyphMapper.__init__`). There are **no other reads of the scheme anywhere in
the file.**

## 1.3 THE GAP — parsed vs consumed

Verified by attribute-level grep (`grep -c "\battr\b" dash_render.py` on each).

| Scheme attribute | Parsed at | Consumed? | If not: hardcoded literal used instead |
|---|---|---|---|
| `p_colors` (15) | 934 | **YES** — `default_color` 992 | — |
| `p_line_colors` (15) | 937 | **YES** — `default_color` 991 | — |
| `p_bar_colors` (15) | 941 | **YES** — `default_color` 993 | — |
| `background_color` | 921 | **YES** — 1010, 1025 | — |
| `plotregion_color` | 922 | **YES** — 1009 | — |
| `grid_color` | 925 | **YES** — 1015 | — |
| `grid_line_width` | 962 | **YES** — 1016 | — |
| `axis_line_color` | 931 | **YES** — 1011-1012, 1019 | — |
| `axis_title_font_size` | 972 | **YES** — 1020 | — |
| `tick_label_font_size` | 973 | **YES** — 1021 | — |
| `title_color` | 930 | **YES** — 1026 (CSS chrome only) | — |
| `heading_font_size` | 971 | **YES** — 1027 (CSS chrome only) | — |
| `text_font_size` | 970 | partial — 1028 (CSS chrome only) | in-figure text: `text_font_size="10px"` **1860** |
| `legend_bg_color` | 923 | partial — 1029 (KPI card CSS only) | never applied to the Bokeh `Legend` object |
| **`p_symbols` (15)** | 951 | **NO** | `marker = "circle"` **1936** |
| **`p_line_patterns` (15)** | 956 | **NO** | `line_dash="solid"` **2330**; default `[]` elsewhere |
| **`p_mark_colors` (15)** | 945 | **NO** | never read at all — pure dead parse |
| **`default_line_width`** | 961 | **NO** | `line_width=1.5` **2023, 2125, 2272, 3206, 3260, 3264, 3267, 3306, 3310**; `line_width=2.0` **1291, 2330, 2377, 2424, 2497, 2569, 2686, 2728, 2893, 2935, 3075** |
| **`fill_alpha`** | 965 | **NO** | `alpha=0.7` **1974**; `fill_alpha=0.2` **1287, 2421, 2494, 2725, 2932** |
| **`bar_alpha`** | 966 | **NO** | `fill_alpha=0.8` **2199, 3014** |
| **`area_alpha`** | 967 | **NO** | `fill_alpha=0.8` **2199** |
| **`minor_grid_color`** | 929 | **NO** | minor grids are never configured |
| **`legend_border_color`** | 924 | **NO** | Bokeh default |
| **`note_font_size`** | 974 | **NO** | note/caption use CSS defaults |

**Summary: 10 of 24 attribute groups — 63 of 108 parsed keys — are parsed and
then discarded.** `default_symbol()` (996) and `default_line_pattern()` (1000)
are public API with **zero call sites** in the entire file; they exist only to be
unit-tested (see §2.4).

There is no marker-size scheme key at all: marker size is `size=8` at **1971,
3440, 3716, 3967** and `size=6`/`size=10` in the emitted server source.

## 1.4 Scheme entries that `SchemeParser` cannot see

### (a) In the five bundled files — near-zero gap, because the files were written to fit the parser

`schemes/s2color.scheme` self-documents this at line 2-6: *"dash bundled
approximation… Covers only properties that have a Bokeh equivalent."*

Each bundled file has exactly 114 parseable entries, of which exactly 5 are not
parsed — identical in all five files:

| Key | e.g. |
|---|---|
| `label` | `schemes/s2color.scheme:8` |
| `color foreground` | `schemes/s2color.scheme:14` |
| `linewidth minor_grid` | `schemes/s2color.scheme:137` |
| `gsize subheading` | `schemes/s2color.scheme:151` |
| `gsize body` | `schemes/s2color.scheme:155` |

Parser bug in passing: the tokenizer does not understand quoted values, so
`label "s2 color"` parses as key `label "s2` / value `color"`
(`dash_render.py:845-849`). Harmless today only because `label` is unused.

### (b) Against a REAL Stata scheme — the gap is 98.4%

This is the finding that matters. I ran dash's own `_parse_file` algorithm over
`/Applications/Stata 18.0/ado/base/s/scheme-s2color.scheme` (2,576 lines):

```
real scheme: 2050 parseable entries, 2048 distinct keys
  keys dash CAN see    :   33  (1.6%)
  keys dash CANNOT see : 2015 (98.4%)
```

Unseen keys by category (count): `linestyle` 272, `areastyle` 200,
`textboxstyle` 158, `seriesstyle` 136, `yesno` 127, `color` 105, `shadestyle` 99,
`markerstyle` 84, `gsize` 76, `labelstyle` 67, `alignstroke` 62, `margin` 57,
`special` 54, `linewidth` 46, `linepattern` 42, `symbolsize` 30, `intensity` 26,
`ticksetstyle` 23, `symbol` 22, `axisstyle` 22, `clockdir` 17,
`plotregionstyle` 17, `numstyle` 15, `relsize` 14, `numticks_g` 14,
`tickstyle` 12, `anglestyle` 11, `legendstyle` 3.

**Worse: 75 of the 108 keys dash asks for do not exist in real Stata schemes at
all.** dash invented its own naming. Real Stata carries the series cycle as
`markerstyle p1 p1` (line 646), `linestyle p1 p1` (967), `seriesstyle p1 p1`
(2304); dash looks for `color p1line`, `color p1bar`, `color p1mark`,
`symbol p1`, `linepattern p1line`, `intensity area` — none of which exist.

Verified runtime consequence of feeding dash a real Stata scheme:

```
SchemeParser("<real scheme-s2color.scheme> in CWD")
  p_colors[:5]        -> ['#1a476f','#90353b','#538d22','#e07f2c','#1b8a7a']  OK
  p_symbols[:5]       -> ['circle','circle','circle','circle','circle']       DEGRADED
  p_line_patterns[:5] -> [[], [], [], [], []]                                 DEGRADED
```

It does not raise. It silently falls back.

### (c) Stata 18+ default scheme `stcolor` — catastrophic silent failure

`c(scheme)` on this machine is `stcolor` (Stata's default since v18). dash ships
no `stcolor`.

```
SchemeParser("stcolor")
  -> ValueError: dash: scheme 'stcolor' not found.
     Built-in schemes: economist, s1color, s1mono, s2color, sj.
```

`DashRenderer.__init__:5003-5005` catches this and silently substitutes
`s2color`. So `dash …, scheme(stcolor)` renders s2color with no warning.

If the user instead copies Stata's real `scheme-stcolor.scheme` into the CWD:

```
SchemeParser("real_stcolor.scheme")
  p_colors[:4] -> ['#000000','#000000','#000000','#000000']
```

**Every series renders black.** Cause: real `stcolor` defines `color p1 stc1`
(a colour *alias*, resolved through `stcoloralias`). `translate_mcolor("stc1")`
raises, and `_color()` at 863-871 swallows it and returns its `default`
argument — which for `p_colors` (934-936) is the bare `"#000000"`. The dashboard
is monochrome and nothing is reported.

Note also `scheme-stcolor.scheme:3` is `#include s2color`. dash's include
resolution (`_resolve_path`, 745-803) has no notion of Stata's ado path, so
`s2color` resolves to **dash's own bundled approximation**, not Stata's file.

## 1.5 The series cycle — VERIFIED, and the answer differs by output mode

**Standalone HTML: the colour cycle WORKS.**
`DashRenderer._make_figure` loops `for pi, plot in enumerate(plots):` at
**5915** and threads `color_idx=pi` into every dispatch: 5931, 5938, 5943, 5948,
5971. `default_color` (980-994) does `idx = index % 15`. So
`dash (scatter y1 x) (scatter y2 x) (scatter y3 x)` yields navy / maroon /
forest-green.

**But only the colour cycles.** All three series get:
- the same marker — `marker = "circle"`, **1936** (`p_symbols` never consulted)
- the same line dash — **2330** / Bokeh default (`p_line_patterns` never consulted)
- the same marker size — `size=8`, **1971**
- the same line width — 1.5/2.0 literals (`default_line_width` never consulted)
- the same alpha — `alpha=0.7`, **1974**

In Stata's `s2color`, p1/p2/p3 are circle/diamond/square with distinct line
patterns. In dash they are three identically-shaped, identically-sized markers
that differ only in hue. This breaks greyscale printing and colour-blind
readability, both of which Stata's scheme design specifically provides for.

**Bokeh Server mode (`server` option): the colour cycle DOES NOT WORK AT ALL.**

`ServerAppBuilder` (7738-10333) emits `for pi, plot in enumerate(plots):` at
**8670**, and then at **8678**:

```python
"            color = '#1f77b4'",
```

`pi` is used **only** as a dict key for `agg_sources[(gname, pi)]` (8787, 8799,
8814, 8846, 8858, 8876, 8894, 8906, 8917, 9031, 9057, 9396, 9408, 9424, 9449).
It is never used for styling. Same literal at **9680** and **9778** for the
faceted and total-panel paths.

So in server mode `dash (scatter y1 x) (scatter y2 x) (scatter y3 x)` renders
**all three series in identical Matplotlib blue `#1f77b4`** — which is not even
a Stata colour.

Confirming the scope: `grep -n "scheme" dash_render.py | awk -F: '$1>7738'`
returns **zero hits**. `ServerAppBuilder` ignores the scheme completely — no
`apply_to_figure`, no `css_block`, no palette. Server output is not just
different from standalone output; it is unthemed.

## 1.6 Does `dash` consult Stata's active scheme? NO.

`grep -n "c(scheme)" dash.ado` → **no matches**. There is no `c(scheme)`,
`creturn`, or `set scheme` read anywhere in `dash.ado`, `dash_setup.ado`, or
`dash_parse.mata`.

`scheme` appears in `dash.ado` only as an option to be captured and forwarded:
declared at 239 and 319, returned at 264 (`sreturn local scheme`) and 388
(`sreturn local g_scheme`), and listed in the option passthroughs at 512, 675,
768, 782, 809. `dash_parse.mata:242-243` maps the abbreviation `sch` → `scheme`.

Consequence: a user who has `set scheme stcolor` (or anything) in their
`profile.do` gets s2color from `dash` regardless, with no message. This is a
direct violation of the drop-in-replacement premise.

## 1.7 `dash.pkg` does NOT ship `schemes/` — the package is broken on `net install`

`dash.pkg` declares six files (`dash.pkg:22-27`):

```
f dash.ado
f dash.sthlp
f dash_setup.ado
f dash_setup.sthlp
f dash_parse.mata
f dash_render.py
```

No `schemes/` directory, no `.scheme` files. Stata's `net install` copies only
declared files.

**Traced failure path (executed, not inferred).** I staged exactly those six
files into a clean directory and ran from a CWD with no `.scheme` files:

1. `SchemeParser._SCHEMES_DIR` (**702**) = `os.path.dirname(os.path.abspath(__file__)) + "/schemes"` → `<PLUS>/d/schemes`, which does not exist.
2. `DashRenderer.__init__:5003` → `SchemeParser("s2color")`.
3. `_resolve_path` (745) builds one candidate, `<PLUS>/d/schemes/s2color.scheme`; `os.path.isfile` is False; falls through to **797-802** and raises:
   `ValueError: dash: scheme 's2color' not found. Built-in schemes: economist, s1color, s1mono, s2color, sj.`
4. `DashRenderer.__init__:5004-5005` catches `(ValueError, OSError)` and retries — **with the identical expression `SchemeParser("s2color")`**. It raises again, uncaught.
5. `GlyphMapper.__init__:1141-1142` has the same unguarded construction and fails identically.

Observed output from the staged install:

```
SchemeParser('s2color')  -> ValueError : dash: scheme 's2color' not found...
RENDERER FALLBACK ALSO RAISES -> ValueError : dash: scheme 's2color' not found...
GlyphMapper() (dash_render.py:1142) -> ValueError : dash: scheme 's2color' not found...
```

**`dash` is 100% non-functional after `net install`.** Every invocation aborts
before any rendering, on the default code path, with no scheme option supplied.
The error message is also actively misleading: it advertises `s2color` as a
built-in while `s2color` is precisely what failed to load.

The existing tests cannot catch this: every test runs from the repo, where
`schemes/` sits next to `dash_render.py`.

## 1.8 Answers to the follow-up questions

**Q1 — Can `SchemeParser` ever locate Stata's own installed scheme files?**
No. `_resolve_path` (745-803) admits exactly two roots: `_SCHEMES_DIR` (702,
fixed to the directory of `dash_render.py`) and `os.getcwd()` (752, 763). Both
the abspath check (768-776) and the realpath/symlink check (777-795) actively
*reject* anything outside those two roots, so even a symlink to
`/Applications/Stata/ado/base/s/` is refused. The only way in is a physical copy
into the CWD.

Could it, given the existing `#include` support? Yes, cheaply — the machinery is
already there. `_parse_file` (808) already recurses through parents with a
circular-include guard (819-821). What is missing is (a) an allowed root derived
from Stata's ado path, which `dash.ado` can pass down since it already forwards
`scheme` (264/388) and could equally forward `c(sysdir_base)`, and (b) key names
that match real Stata. Both are additive. The security model would need a third
allowed root rather than a relaxation of the existing checks.

**Q2 — Is Stata's `p#stub → pstub → p# → p` resolution implemented?**
Only one of the four levels, and even that is a coincidence of dash's own key
naming.

| Stata level | dash equivalent | Implemented? |
|---|---|---|
| `p#stub` (e.g. `color p1line`) | `_color(f"color p{i}line", …)` 937-940 | yes (dash's own invented key) |
| ↓ fallback to `pstub` (`color pline`) | — | **no** |
| ↓ fallback to `p#` (`color p1`) | the `default=` arg at 938, 942, 946 | yes, one level only |
| ↓ fallback to `p` (`color p`) | — | **no** |

Real `scheme-s2color.scheme` populates the bare-`p` level explicitly —
`color p gs6` (423), `symbol p circle` (521), `linepattern p solid` (593),
`symbolsize p medium` (268), `linewidth p 1193`, `intensity p 1294`. dash reads
only `linewidth p` (961) and `intensity p` (965) and ignores the rest, so the
final fallback rung that Stata relies on to keep unspecified styles coherent is
absent. `default_color` (980-994) is a flat `index % 15` table lookup with a
plot-type switch; there is no chain.

**Q3 — Which real-scheme categories does dash recognise today?**

| Category | Present in real s2color | dash parses it? | Detail |
|---|---|---|---|
| `graphsize` | yes — `graphsize 5`/`x 5.5`/`y 4` (31-33) | **NO** | canonical figure size; dash has no width/height at all (§2.5) |
| `numstyle` | yes — 15 keys incl. `legend_rows`, `legend_cols` (37-40) | **NO** | legend geometry falls back to Bokeh |
| `gsize` | yes — 76 keys | **partial: 5 of 76** | only `text`, `heading`, `axis_title`, `tick_label`, `note` (970-974) |
| `margin` | yes — 57 keys | **NO** | no plot/graph region margin control |
| `linepattern` | yes — 42 keys incl. `linepattern p solid` (593) | **parses 15, consumes 0** | `p_line_patterns` 956 is dead (§1.3) |
| `symbol` | yes — 22 keys incl. `symbol p circle` (521) | **parses 15, consumes 0** | `p_symbols` 951 is dead; real keys are `markerstyle p# p#` anyway |
| `symbolsize` | yes — 30 keys (268 etc.) | **NO** | marker size hardcoded `size=8` (1971) |
| `yesno` | yes — 127 keys | **NO** | every boolean toggle (grid on/off, axis alternation, margin adjustment) invisible |
| `clockdir` | yes — 17 keys incl. `legend_position` | **NO** | legend placement comes only from the explicit `legend()` option |
| `compass`/`compass2dir` | yes — 15 `compass2dir` keys | **NO** | label anchoring |
| `relsize` | yes — 14 keys (bar gaps, box fences) | **NO** | bar spacing hardcoded |
| `axisstyle` | yes — 22 keys | **NO** | — |
| `gridstyle` | not a category; nearest is `gridringstyle` (14) | **NO** | dash reads only `color major_grid`/`grid` (925) and `linewidth major_grid` (962) |

Recognised categories in total: `color` (33 of 105 real keys), `gsize` (5 of 76),
`linewidth` (2 of 46), `intensity` (2 of 26), plus `symbol`/`linepattern` which
are parsed but discarded.

**Q4 — Quantified approximation gap.**

| Measure | Value |
|---|---|
| Directives in real `scheme-s2color.scheme` | 2,050 (2,048 distinct keys, 2,576 lines) |
| Keys `SchemeParser` requests | 108 |
| Requested keys that exist in the real scheme | 33 |
| **Real directives dash can read** | **33 / 2,048 = 1.6%** |
| **Real directives dash can read *and act on*** | **~23 / 2,048 ≈ 1.1%** (the 15 `symbol p#` are read then discarded, and `color p#mark`/`linepattern` do not exist under those names) |
| Requested keys that are dash inventions absent from real Stata | 75 / 108 = 69% |
| Bundled approximation size vs real | ~144 lines vs 2,576 = 5.6% |
| Stata schemes on this machine | 26 |
| Of which dash ships an approximation | 5 (and not the v18+ default `stcolor`) |

---

# SECTION 2 — TEST COVERAGE GAPS

Suite size: **1,494 pytest tests** across 20 `.py` files (~24,600 lines), 11
`.cscript` files (1,798 lines), 16 `.do` files (421 lines).

**Current state: the suite is RED.** `python3 -m pytest test/ -q` →
**14 failed, 1480 passed** (33s). All 14 are `ModuleNotFoundError` from the
unguarded `from statsmodels.nonparametric.smoothers_lowess import lowess` at
`dash_render.py:2547` (statsmodels is uninstallable here — missing `packaging`).
Failing: `test_glyphs.py` TestMapLowess / TestLowessConstantX /
TestEdgeCasesEmptyData / TestLegendLabelCoverage,
`test_html_output.py::TestLowessHtmlOutput`, `TestColorRenderingAllPlotTypes`,
`test_pipeline_integration.py::TestLowessBasicFunctionality`, `TestEdgeCaseData`.
This violates CLAUDE.md rule 5. Separately, that import has no guard, so a
Stata user missing statsmodels gets a raw Python traceback rather than a
diagnostic.

## 2.1 Function-level coverage map

DIRECT = test references the name as code. MENTION = name appears only in
comments/docstrings. NONE = string absent from `test/`.

### Glyph mappers — `GlyphMapper.map_*` (38): **38/38 DIRECT.** Best-covered area of the codebase.
`map_scatter` 1914, `map_line` 1988, `map_connected` 2034, `map_area` 2065,
`map_bar` 2131, `map_spike` 2229, `map_lfit` 2285, `map_qfit` 2335,
`map_lfitci` 2382, `map_qfitci` 2456, `map_lowess` 2525, `map_lpoly` 2628,
`map_lpolyci` 2691, `map_fpfit` 2843, `map_fpfitci` 2898, `map_histogram` 2967,
`map_kdensity` 3033, `map_rarea` 3094, `map_rbar` 3132, `map_rspike` 3177,
`map_rcap` 3215, `map_rline` 3280, `map_rconnected` 3321, `map_dot` 3352,
`map_dropline` 3385, `map_rcapsym` 3451, `map_scatteri` 3530, `map_pcspike` 3598,
`map_pci` 3642, `map_pcscatter` 3674, `map_pcarrow` 3724, `map_pcbarrow` 3796,
`map_tsline` 3869, `map_tsrline` 3896, `map_rscatter` 3925, `map_mspline` 3975,
`map_mband` 4044, `map_function` 4117.
Thinnest: `map_pcscatter` (1 call site in tests), `map_pci`/`map_rscatter`/
`map_connected` (2 each).

### Option translators — `OptionTranslator` (7): **7/7 DIRECT.**
`parse_color_alpha` 482, `translate_mcolor` 525, `translate_msymbol` 580,
`translate_msize` 606, `translate_lcolor` 632, `translate_lwidth` 637,
`translate_lpattern` 662 — all covered in `test_options.py` /
`test_html_verification.py`.

### Scheme parser — `SchemeParser` (15): **8 of 15 have ZERO references.**

| Function | line | status |
|---|---|---|
| `__init__` 734 / `default_color` 980 / `default_symbol` 996 / `default_line_pattern` 1000 / `apply_to_figure` 1004 / `css_block` 1023 | | DIRECT |
| `_resolve_path` | 745 | referenced only via `inspect.getsource` text assertion, `test_scheme.py:500`; **never invoked with a path** |
| `_parse_file` | 808 | **NONE** — `#include` recursion + circular-include guard untested |
| `_color` 863, `_gsize` 873, `_intensity` 884, `_lpattern` 893, `_lwidth` 897, `_symbol` 909, `_init_properties` 918 | | **NONE** |

The entire value-coercion layer — exactly where the `stc1` → `#000000`
silent-black failure of §1.4(c) originates — has no unit test.

### Layout engines — `DashRenderer`
DIRECT: `_compute_grid` 6767 (`test_layout.py:103`), `_pad_grid_children` 6802
(:161), `_is_bootstrap_layout` 6308 (:321), `_auto_bs_layout` 6320 (:340),
`_parse_bs_layout` 6367 (:369).
**NONE: `_assemble_layout` 7345** (the primary layout assembler),
`_parse_tabs_option` 6661, `_build_tabs_widget` 6703.
MENTION-only: `_render_bootstrap_html` 6441, `_make_figure` 5593,
`_add_glyph` 6142, `_add_pc_glyph` 6231.

### Filter / KPI builders
`FilterBuilder`: `build_dropdown` 4650, `build_slider` 4777, `build_range` 4833
all DIRECT. **`_safe` 4645 — NONE.** That is the HTML/JS escaping helper used at
4687, 4739, 4795, 4851; it is the XSS chokepoint for every filter widget and has
no direct test (CLAUDE.md rules 16 and 18).
KPI: `_compute_kpi_stat` 5102, `_format_kpi_value` 5186, `_make_kpi_div` 6276
DIRECT. **NONE: `_compute_kpi_stat_on_df` 5140, `_build_kpi_html` 7075,
`_parse_fmt` 7068.**

### `ServerAppBuilder` (4): **4/4 DIRECT** — `__init__` 7764, `build` 7779,
`_embed_data` 7798 (1 call site), `_generate_app_source` 7810. 448 tests in
`test_server.py`. But note these overwhelmingly assert on the *generated source
text*, not on rendered output (see §2.5).

### Full list of 28 zero-reference functions
Module: `_parse_scale_opt` 203, `_extract_region_color` 246,
`_extract_region_lcolor` 255, `_extract_region_lwidth` 261.
SchemeParser: `_parse_file` 808, `_color` 863, `_gsize` 873, `_intensity` 884,
`_lpattern` 893, `_lwidth` 897, `_symbol` 909, `_init_properties` 918.
GlyphMapper: `_build_jitter_source` 1161, `_hover_tool` 1210, `_render_ci_band`
1255, `_bootstrap_ci` 1298, `_apply_fill_opts` 1488, `_predict_fp2` 2831.
FilterBuilder: `_safe` 4645.
DashRenderer: `_load_data` 5051, `_compute_kpi_stat_on_df` 5140, `_axis_label`
5543, `_parse_tabs_option` 6661, `_build_tabs_widget` 6703, `_to_serialisable`
7055, `_parse_fmt` 7068, `_build_kpi_html` 7075, `_assemble_layout` 7345.

**False positive to be aware of:** `DashRenderer._make_source` (5226) looks
covered — 20 grep hits — but every one is an unrelated *test-local* helper of
the same name (`test_jitter.py:41`, `test_filters.py:1040`). It is untested.
Similarly `_collect_graph_vars` 4936 has only `hasattr`/`callable` existence
assertions (`test_pipeline_integration.py:591-594`), never an invocation.

11 nested closures are unreachable for unit testing as written, including
`_validate_expr_node` 4161 (the AST allow-list that gates user `if` expressions —
security-critical) and `_parse_refline` 5834.

## 2.2 Features from `dash.sthlp` with no test

| Feature | Documented at | Status |
|---|---|---|
| **Tabbed layout** | `dash.sthlp` layout section | **ZERO tests.** The string `tabs` does not appear in any file under `test/` — `.py`, `.cscript`, `.do`. `_parse_tabs_option` 6661, `_build_tabs_widget` 6703, and the `tabs_widget`/`__tabs__` branches at 6449, 6503-6505, 6579-6581, 7373-7378 are entirely unexercised. |
| `nobrowser` | `dash.sthlp:96, 215` | no test reference |
| `timeout()` | `dash.sthlp:216-217` | only the BUG-49 unit-consistency string checks (`test_server.py` TestTimeoutUnitConsistency); no behavioural test |
| `connect()` | `dash.sthlp:675` | no test reference |
| `colpalette()` | `dash_render.py:1564` | one file only (`test_html_verification.py`) |
| `xsize()` / `ysize()` | **not documented, not implemented** | `grep xsize\|ysize` across `dash.ado`, `dash.sthlp`, `dash_parse.mata`, `dash_render.py` → zero hits |
| **Date/time axes** | not documented | **not implemented** (see §2.5) |
| `scheme()` | `dash.sthlp:79, 709-716` | documented as "fully supported"; see §1 — the claim at :714 that "the scheme controls… marker color cycles" is accurate only for colour |

Note `dash.sthlp:161-162` states *"`scheme()` is fully supported"*. Given §1.3
(63 of 108 keys discarded), §1.5 (server mode unthemed), §1.6 (active scheme
ignored) and §1.7 (not shipped), that sentence is not defensible.

## 2.3 `.cscript` end-to-end coverage

`test/run_all_cscripts.do` runs **9 of 11** cscripts (lines 44, 63, 82, 101, 120,
139, 158, 178, 198).

| cscript | In suite? | Reaches Python? | Evidence |
|---|---|---|---|
| `test_e2e_single.cscript` | yes (:101) | **HTML** | `:45` `dash scatter … saving()`; `:48-49` `confirm file` + `assert _rc==0`; `:63-78` asserts bokeh markers in the file |
| `test_e2e_multi.cscript` | yes (:120) | **HTML** | `:50` `dash build, saving() layout(2 2)`; `:53-54` confirm; `:84-86`, `:108` content asserts |
| `test_e2e_filters.cscript` | yes (:139) | **HTML** | `:49` build; `:53-54` confirm; `:73`, `:91-92` content asserts |
| `test_e2e_kpi.cscript` | yes (:158) | **HTML** | `:54` build; `:56-57` confirm; `:72`, `:95-96` content asserts |
| `test_tokenizer.cscript` | yes (:44) | **no** — Mata only | `:18` `do ../dash_parse.mata`; only `mata: _dash_split_segs(...)` asserts |
| `test_parser.cscript` | yes (:63) | **no** — parse only | Its own docstring `:12` says *"no jsonio/render required"*. Its single non-`clear` `dash` call `:178` passes `name(u3)`, which routes to `_dash_register_graph` (`dash.ado:840-842`) instead of `_dash_render_immediate` (`dash.ado:844`). Nothing renders. |
| `test_jsonio.cscript` | yes (:82) | **no** | no `dash` command at all; exercises the third-party `jsonio` only; `:167-168` confirms a JSON file, not HTML |
| `test_ado_loads.cscript` | yes (:178) | **no** | load-time program-existence asserts |
| `test_mata_autoload.cscript` | yes (:198) | **no** | Mata autoload only |
| **`test_adversarial.cscript`** | **NO — orphan** | HTML + server `.py` | 311 lines, ~14 security asserts: `:58` XSS build → `:78` `assert found_raw_xss==0`; `:218` server build → `:237` no raw `<script>`; `:255-268` compiles the generated app. **The only Stata-side coverage of XSS, path traversal and `_dash_validate_path` — and it is not in the suite.** |
| **`test_e2e_serve.cscript`** | **NO — orphan** | server `.py` only | 305 lines, ~15 asserts; `:269-286` imports the generated module and calls `make_document`, asserting `len(_doc.roots) > 0` — the deepest Python execution in the Stata suite. Not in the suite. |

So: **4 of 9 suite members touch Python end to end; 5 of 9 are parse-only.** The
two richest cscripts are excluded.

The 16 `.do` files are debugging scratchpads, not tests — **zero `assert`
statements across all of them** (verified by grep). `test_r_trace*.do`,
`test_build_s3*.do`, `test_if_expr*.do`, `test_equalop.do`, `test_r_char*.do`,
`diag_cwd.do` only `display`/`type`.

There is **no CI config, no pytest.ini/pyproject/tox, and no shell runner**
anywhere in the repo, and no single command runs both halves of the suite.

## 2.4 Landmines — tests that must change when bugs are fixed

Ranked by how badly they will mislead an implementer.

**L1 — `test_scheme.py:404-415`, `test_real_stata_scheme_via_cwd_copy`.** The one
test that feeds dash a real Stata scheme. It asserts exactly one thing —
`assert sp.p_colors[0] == "#1a476f"` (:414) — which is the single property that
survives. It does not assert `p_symbols`, `p_line_patterns`, fonts, widths or
intensities, all of which I showed silently degrade (§1.4b). It is a green test
that actively conceals a 98.4% gap. It is also hardcoded to
`/Applications/Stata 15/…` (:406) and `pytest.skip`s on any other machine (:408).

**L2 — `test_scheme.py:194-203`.** `test_default_symbol_returns_string`,
`test_default_symbol_wraps_modulo_15`, `test_default_line_pattern_returns_list`
all pass — while `default_symbol` (996) and `default_line_pattern` (1000) have
**zero call sites in `dash_render.py`**. Likewise the `fill_alpha`/`bar_alpha`/
`area_alpha` tests around `test_scheme.py:209+`. These are vacuous-green tests
for dead API: they make §1.3 invisible to the suite.

**L3 — `test_server.py:6990, 7014, 7065, 7119, 7711`** (and `:7715`):
`if not renderer.filter_callbacks: pytest.skip("No filter callbacks built (nothing to test)")`.
The skip condition *is* one of the regressions the test exists to catch. If
callback generation breaks entirely, these report skipped, not failed.

**L4 — `test_kpi.py:276` and `:287`:** `assert kpi_info is None or kpi_info == "filter"` /
`== "brush"`. `kpi_info` comes from `._kpi_update_modes.get(..., None)` (:275),
so total non-registration passes. Tautologies for P2-43/P2-44.

**L5 — `test_linking.py:207-214`, `test_single_link_group_enforced`.** The `try:`
body calls `_setup_sources()` and then contains only comments; `except
ValueError: pass`. **No assertion on either branch — the test cannot fail.** The
comment at :203-206 concedes the behaviour is "implementation-dependent".

**L6 — `test_glyphs.py:1796`:** `assert len(fig.renderers) >= 0  # just verifies no exception`.
Always true. Encodes "`mlabwidth` is accepted and does nothing" (matching
`dash_render.py:1905` `options.get("mlabwidth")  # consumed; no-op`).

**L7 — `test_filters.py:588-604`.** Docstring :591-595 explicitly says it
"documents the pre-fix failure mode"; :600 asserts the *symptom*
(`len(r.filter_widgets) == 0`). It will keep passing after a correct fix.

**L8 — `test_server.py:2216-2251`.** Three unsafe-`if_expr` tests whose assertion
(`:2225`, `:2238`, `:2250`) is a disjunction accepting **either** the full
unfiltered dataset **or** an empty one. Two opposite security outcomes both pass.

**L9 — ~22 "silently ignored" tests** that lock in no-diagnostic behaviour for
malformed user input, e.g. `test_jitter.py:177-183` (`jitter()` is a no-op on
line plots), `test_graph_options.py:368-374` (a typo'd axis tick is dropped
silently), `test_glyphs.py:841-846` (a typo'd `mlabel` variable produces no
label and no warning), `test_html_verification.py:473-481` (`colorvar` on a
missing column silently produces no colour bar). Each is a deliberate
design decision encoded as a test; each will need renegotiating if `dash` is to
report bad options the way Stata does.

**L10 — Stata-side silent skips scored as PASS.** All 15 dependency guards use
`display as error "SKIP: …"` then `exit 0` (`test_e2e_single.cscript:18-19,
28-29`; `test_e2e_multi` :18-19, :28-29; `test_e2e_filters` :18-19, :28-29;
`test_e2e_kpi` :18-19, :28-29; `test_jsonio` :18-19; `test_e2e_serve` :19-20,
:29-30, :40-41; `test_adversarial` :20-21, :30-31, :40-41). `run_all_cscripts.do`
only inspects `_rc` (:46-48, :65-67, …), so an `exit 0` skip is counted as a
pass. Its `n_skip` counter is initialised at **:36** and **never incremented**,
so **:216** always prints "0 skipped". On a machine without jsonio/Python/bokeh
the runner prints ALL TESTS PASSED having executed no assertions.

No `pytest.mark.skip`, `xfail`, `skipif`, `@unittest.skip`, `TODO`, `FIXME` or
`known issue` markers exist anywhere in `test/`. Other `pytest.skip` sites:
`test_scheme.py:431, :450` (need `/etc/hosts`), `test_server.py:4547` (POSIX-only).

## 2.5 Regression coverage for the five named areas

| Area | Covered? | Evidence |
|---|---|---|
| **Date/time axes** | **NO — and there is nothing to regress.** | Zero date support in the codebase: no `DatetimeTickFormatter`, no `x_axis_type="datetime"`, no `%td`/`%tc` handling anywhere in `dash_render.py`. `map_tsline` (3869) is a pass-through — `:3894` `return self.map_line(...)` — so a Stata date variable renders as a raw integer axis (e.g. 22000 instead of 01jan2020). `test_phase4_plots.py:262` tests `map_tsline` but only that a line renderer is produced; it never asserts axis type or tick formatting. No test would fail if date support were added *or* if the numeric fallback broke. |
| **Figure sizing** | **NO.** | There is no sizing to test. `_make_figure` sets only `sizing_mode="stretch_width"` (**5648**) — no `width`, no `height`, no `frame_width`. `aspectratio()` (5628-5631, 5652) is the sole size control and has 3 tests, one of which (`test_graph_options.py:144-147`) only asserts `fig is not None`. `xsize()`/`ysize()` do not exist. The scheme's `graphsize 5 / x 5.5 / y 4` is unparsed. No test asserts any figure dimension. |
| **Scheme consumption** | **NO — worse, existing tests mask the gap.** | `test_scheme.py` (78 tests) tests `SchemeParser` in isolation; `test_scheme_integration.py` (11 tests) checks only that `apply_to_figure` set a background (`:154-175`) and that CSS differs between schemes (`:183-196`). No test asserts a glyph's marker symbol, line dash, line width, alpha or marker size came from the scheme. The 8 private coercion methods are untested (§2.1). L1 and L2 above make the dead-attribute gap look covered. |
| **Series colour cycle** | **PARTIAL — the central case is untested.** | Only `test_scheme.py:175-190` (unit-level `default_color` modulo behaviour) and `test_phase4_plots.py:398` (`expected_color = gm.scheme.default_color(0, "line")` — index 0 only). **No test anywhere renders 3 overlaid series and asserts 3 distinct colours.** Nothing would catch a regression to a constant colour in standalone mode — and nothing catches the existing constant-colour bug in server mode. `grep -rn "1f77b4" test/` → **zero hits**. |
| **Server-vs-standalone parity** | **NO.** | `test_server.py` has 448 tests but they assert on *generated source text* and on `make_document()` structure; none compares server output against standalone output for the same spec. There is no parity test of any kind. This is exactly why the §1.5 defect (server hardcodes `#1f77b4`, ignores the scheme entirely) has gone unnoticed despite the largest test file in the repo. |

---

# FINDINGS RANKED BY SEVERITY

| # | Sev | Finding | Cite |
|---|---|---|---|
| 1 | **CRITICAL** | `dash.pkg` omits `schemes/`; after `net install` every invocation raises `ValueError` and nothing renders. The `except` handler at 5004-5005 re-calls the expression that just failed, so the fallback cannot work. Verified by staging the six declared files. | `dash.pkg:22-27`; `dash_render.py:702, 797-802, 5003-5005, 1141-1142` |
| 2 | **HIGH** | Server mode ignores the scheme completely and hardcodes `'#1f77b4'`; all overlaid series render identical. `grep "scheme"` over lines >7738 → zero hits. | `dash_render.py:8678, 9680, 9778`; `ServerAppBuilder` 7738-10333 |
| 3 | **HIGH** | A real Stata scheme silently degrades rather than erroring; Stata 18+ default `stcolor` renders **every series black** because `color p1 stc1` fails `translate_mcolor` and `_color` returns its `"#000000"` default. | `dash_render.py:863-871, 934-936`; verified at runtime |
| 4 | **HIGH** | `dash` never reads `c(scheme)`. `set scheme` is ignored with no message; hardcoded default `s2color` is Stata's pre-v18 default. | `dash.ado` (no `c(scheme)` match); `dash_render.py:4982-5001` |
| 5 | **HIGH** | 63 of 108 parsed scheme keys are discarded — symbols, line patterns, line widths, all intensities, marker colours, minor grid, legend border, note size. `default_symbol`/`default_line_pattern` have zero call sites. Series differ only in hue. | `dash_render.py:945, 951, 956, 961, 965-967, 996, 1000, 1936, 1971, 1974, 2023` |
| 6 | **HIGH** | Suite is currently RED: 14 failures from an unguarded `statsmodels` import. Violates CLAUDE.md rule 5; also surfaces a raw traceback to Stata users. | `dash_render.py:2547`; pytest run |
| 7 | **HIGH** | `test_adversarial.cscript` (311 lines, the only Stata-side XSS/path-traversal coverage) and `test_e2e_serve.cscript` (305 lines) are **not in `run_all_cscripts.do`**. Violates CLAUDE.md rule 18. | `run_all_cscripts.do:44-198` |
| 8 | **HIGH** | Stata dependency guards `exit 0`, which the runner scores as PASS; `n_skip` is never incremented so it always reports "0 skipped". A machine without jsonio/Python/bokeh prints ALL TESTS PASSED with zero assertions executed. | `run_all_cscripts.do:36, 46-48, 216`; 15 guard sites |
| 9 | **MEDIUM** | `FilterBuilder._safe` — the HTML/JS escaping chokepoint for every widget — has zero direct tests. So does `_validate_expr_node` (AST allow-list for user `if` expressions). Violates CLAUDE.md rules 16 and 18. | `dash_render.py:4645, 4161` |
| 10 | **MEDIUM** | No date/time axis support at all; `map_tsline` is a pass-through to `map_line`. Stata dates render as integers. No test would catch it either way. | `dash_render.py:3869, 3894` |
| 11 | **MEDIUM** | No figure sizing of any kind: `sizing_mode="stretch_width"` only, no `xsize()`/`ysize()`, scheme `graphsize` unparsed. Zero dimension assertions in the suite. | `dash_render.py:5648` |
| 12 | **MEDIUM** | Tabbed layout feature has **zero** tests — the string `tabs` is absent from all of `test/`. | `dash_render.py:6661, 6703, 6449, 6503-6505, 7373-7378` |
| 13 | **MEDIUM** | No server-vs-standalone parity test exists despite 448 server tests; this is why #2 was missed. | §2.5 |
| 14 | **MEDIUM** | No test renders 3 series and asserts 3 distinct colours — the central drop-in-replacement claim is unverified. | §2.5 |
| 15 | **MEDIUM** | Landmine tests L1–L9: vacuous greens (`test_linking.py:207-214` has no assertion at all), tautologies (`test_kpi.py:276, 287`), skips that fire on the regression (`test_server.py:6990` +4), symptom-asserting tests (`test_filters.py:600`), and a security test accepting two opposite outcomes (`test_server.py:2225, 2238, 2250`). | §2.4 |
| 16 | **MEDIUM** | 28 functions have zero test references, including the whole `SchemeParser` coercion layer (8) and `_assemble_layout`. `DashRenderer._make_source` looks covered but all 20 hits are same-named test helpers. | §2.1 |
| 17 | **LOW** | `dash.sthlp:161-162` claims `scheme()` is "fully supported"; unsupportable given #2–#5. | `dash.sthlp:161-162, 709-716` |
| 18 | **LOW** | `SchemeParser` tokenizer cannot handle quoted values: `label "s2 color"` → key `label "s2`. Harmless only because `label` is unused. | `dash_render.py:845-849` |
| 19 | **LOW** | No CI config, no pytest config, no runner that executes both the pytest and cscript halves. | repo-wide grep |
| 20 | **LOW** | 16 `.do` files in `test/` contain zero assertions — debugging scratchpads checked in as tests. | §2.3 |

## Explicitly UNDETERMINED

- Whether `run_all_cscripts.do` passes on this machine. I did not invoke Stata; all cscript claims are from reading the files, not from execution.
- Whether the 14 lowess failures also occur in the maintainer's environment. The cause here is a broken local `statsmodels`/`packaging` install, which is environmental; the *absence of an import guard* at `dash_render.py:2547` is not.
- Stata's exact runtime `p#stub` resolution semantics are taken from the comment block at `scheme-s2color.scheme:6-13`, not from Stata source.
