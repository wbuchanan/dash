# Stata rules the plan must implement — documentation research

Generated 2026-09-25 for the WP-28 plan (22 GAPS2 gaps). Context7 was not
available; every rule below is read from Stata's own installed files.

**Sources and how they are cited**

- `$BASE` = `/Applications/StataNow/ado/base/` (StataNow, help files dated up
  to 27may2026). Help files are SMCL text; `file:line` numbers are the raw
  file lines. Note: scheme files live in `$BASE/s/`, not `$BASE/style/`
  (`style/` holds `*.style` files).
- The four PDF manuals were converted with `pdftotext -layout` into the
  scratchpad (`p.txt`, `u.txt`, `d.txt`, `g.txt` from
  `/Applications/StataNow/docs/{p,u,d,g}.pdf`); citations to them give the
  text-dump line and, where visible, the printed page.
- Repository files are cited by path from the repo root.
- Nothing was run in Stata. Rules that the documentation leaves open are
  marked **PROBE** (must be measured by a cert script / `extract_*_truth.do`).
- WebFetch fallback (`https://www.stata.com/help.cgi?r(109)` etc.) was tried
  for the return-code wording: the site answers "help for r(109) not found",
  so the [P] error PDF was used instead.

---

## 1. numlist grammar ([U] 11.1.8, help numlist, [P] numlist)

Forms (`$BASE/n/numlist.sthlp:28-65`, identical table in `u.txt:2533-2567`,
[U] p.58):

| Form | Meaning | Line |
|---|---|---|
| `2` | one number | :28 |
| `1 2 3` / `3 2 1` | listed, order kept | :29-30 |
| `.5 1 1.5`, `1 3 -2.17 5.12` | any reals, any order | :31-32 |
| `1/3`, `3/1`, `5/8` | integer step of 1 in the stated direction | :34-36 |
| `-8/-5`, `-5/-8`, `-1/2` | negatives and descending allowed | :37-39 |
| `1 2 to 4`, `4 3 to 1`, `10 15 to 30` | step = second − first, run to the limit | :41-43 |
| `1 2:4`, `4 3:1`, `10 15:30` | `:` is a synonym of ` to ` | :45-47 |
| `1(1)3`, `1(2)9`, `9(-2)1`, `-1(.5)2.5` | first(step)last; negative and non-integer steps | :49-53 |
| `1(2)10` | "the same five numbers: 1, 3, 5, 7, 9" — stops at the last value ≤ limit | :51 |
| `1[1]3` … `-1[.5]2.5` | `[step]` ≡ `(step)` | :55-59 |
| `1 2 3/5 8(2)12` | forms mix freely | :61 |
| `1,2,3/5,8(2)12` | commas as separators | :62 |

- Comma rule: "You may use commas when a numlist appears inside the
  parentheses of an option, but you may not use commas in other cases"
  (`numlist.sthlp:67-71`). Axis-label numlists are inside option parentheses,
  so `xlabel(1,2,3)` is legal — but the comma also introduces sub-options
  (`axis_label_options.sthlp:54,845`), so the parser must decide which comma
  starts `, suboptions`. **PROBE** how twoway reads `xlabel(1,2,3, grid)`.
- The `#(#)#` rule "says to label the first number specified, increment by the
  second number, and keep labeling, as long as the result is less than or
  equal to the last number specified" (`$BASE/a/axis_label_options.sthlp:952-955`).
- Whitespace: the documented examples put spaces around `to` (`1 2 to 4`) and
  none around `:` (`1 2:4`) or inside `a(b)c`, `a[b]c`, `a/b`. Nothing states
  whether `1 (1) 3` or `1 / 3` is one element or three. **PROBE**.
- Limits: `numlist` accepts at most 1600 elements (`$BASE/n/nlist.sthlp:85-87`);
  missing values are refused unless `missingokay` (`:78-79`).

Error messages ([P] error, `p.txt:9609-9615`, printed p.196; examples
`p.txt:19653-19691`, [P] numlist p.421):

| rc | message |
|---|---|
| 121 | `invalid numlist` |
| 122 | `invalid numlist has too few elements` |
| 123 | `invalid numlist has too many elements` |
| 124 | `invalid numlist has elements out of order` |
| 125 | `invalid numlist has elements outside of allowed range` |
| 126 | `invalid numlist has noninteger elements` |
| 127 | `invalid numlist has missing values` |

Documented examples: `numlist "3 5 . 28 -3(2)5"` → r(127) (`p.txt:19674-19676`);
`"5.3 1.0234 3 6:18 -2.0033 5.3/7.3", integer` → r(126); `"3/6 -4 -1 to 5",
range(>=1)` → r(125). Which of these codes `graph` raises for a bad label
numlist (e.g. a zero step `1(0)5`) is not documented — **PROBE**.

Histogram's own numlists: `BINs(numlist max=1 >0 integer)`,
`Width(numlist max=1 >0)`, `START(numlist max=1)`
(`$BASE/t/twoway__histogram_gen.ado:9-11`), so `bin(2.5)` is r(126) and
`width(0)` r(125), by `syntax`.

---

## 2. axis_label_options (`$BASE/a/axis_label_options.sthlp`)

Option names and minimum abbreviations (`:32-39`): `{y|x|t|z}lab:el()`,
`ti:ck()`, `mlab:el()`, `mti:ck()`. They are *merged-explicit* (`:42-44`).

Grammar (`:50-58`, repeated `:834-838`):

```
[rule] [numlist ["label" [numlist ["label" [...]]]]] [, suboptions]
```
"Either rule or numlist must be specified, and both may be specified" (`:57-58`).

Rules (`:60-81`, `:901-922`):

| rule | meaning | lines |
|---|---|---|
| `#N` (e.g. `#6`) | "approximately 6 nice values"; not taken literally — `#10` gave 7 and 8 labels (`:592-593`, `:928-939`) | :62-64 |
| `##N` | N−1 minor ticks between majors; allowed with `mlabel()`/`mtick()` only; needs evenly spaced majors, else "does not produce any minor ticks" (`:662-669`, `:942-949`) | :65-68 |
| `#(#)#` | exact range/step (`:69-71`, `:952-960`); minor ticks drop the intersection with major: `ylabel(1(1)10) ymtick(1(.5)10)` ≡ `ymtick(1.5(1)9.5)` (`:958-960`) | |
| `minmax` | min and max only | :72-74, :963-964 |
| `none` | no labels, no ticks | :75-77, :967-968 |
| `.` | skip the rule; only meaningful with `add`, otherwise ≡ `none` | :78-80, :971-972 |

Rule vs numlist: `ylabel(1(1)10)` is a *rule*; `ylabel(none 1(1)10)` is a
*numlist* — "Visually … there is no difference" (`:987-995`); numlists are for
unequal spacing or extra values, `ylabel(1(1)10 3.5 7.5)` (`:998-1006`).

Value/"text" pairs (`:1013-1022`, `:735-740`): `ylabel(10 20 30 "mean" 40 50)`
labels all five values and prints "mean" at 30. A text follows *one* numlist
element; the grammar shows exactly one `"label"` after each numlist. Whether
a second consecutive string (`xlabel(1 "a" "b")`) is a second line or a
syntax error is **not documented** here (multi-line by consecutive strings is
documented only for titles/legend labels, §4–§5) — **PROBE**.

Sub-options (`:107-156`; abbreviation = the part before the colon in `{cmdab:}`):

| option | min. abbrev | note |
|---|---|---|
| `axis(#)` | `ax` | 1 ≤ # ≤ 9 |
| `add` | — | merge values; "rule specifications always replace any existing rule" (`:236-243`) |
| `[no]ticks` | `no` prefix only | |
| `[no]labels` | `lab` | `nolabels` turns `ylabel()` into `ytick()` (`:255-266`) |
| `valuelabel` | `val` | see below |
| `format(%fmt)` | — | |
| `angle(anglestyle)` | — | |
| `alternate` | `alt` | offsets adjacent labels (`:329-341`) |
| `norescale` | — | see below |
| `tstyle()` | `tsty` | |
| `labelminlen(#)` | — | pads labels left to width # (`:367-369`) |
| `labgap()`, `labstyle()` | — | |
| `labsize()` | `labs` | |
| `labcolor()` | `labc` | |
| `tlength()` | `tl` | |
| `tposition(outside\|crossing\|inside)` | `tp`; values `o`/`c`/`i` | `:134-135`, `:385-389` |
| `tlstyle()` | `tlsty` | |
| `tlwidth()` | `tlw` | |
| `tlcolor()` | `tlc` | |
| `custom` | — | rendition options apply to this option's labels only (`:401-414`) |
| `[no]grid` | — | `ylabel` defaults to `grid`, others `nogrid`; scheme decides (`:417-428`) |
| `[no]gmin`, `[no]gmax` | — | neither is the default; graph decides (`:449-482`) |
| `gstyle()` | `gsty` | |
| `[no]gextend` | `gex` | |
| `glstyle()` | `glsty` | |
| `glwidth()` | `glw` | |
| `glcolor()` | `glc` | |
| `glpattern()` | `glp` | |

`valuelabel` (`:269-291`): "values should be mapped through the first y
variable's value label (y*() options) or the x variable's value label (x*()
options)"; `xlabel(1 2 3, valuelabel)` "would have the same effect as
`xlabel(1 "Low" 2 "Med" 3 "Hi")`". twoway does **not** use value labels
unless told to — the repo already pins this
(`test/test_help_claims_2.cscript:1018-1029`, HC2-41).

`format()` (`:294-321`): default "obtained from the variables specified with
the graph command, which for ylabel() … usually means the first y variable,
and for xlabel() … the x variable"; sub-options may be given without values,
`ylabel(,format(%9.2fc))` — "Note carefully the comma in front of format".
The tick-set object's own initial `label_format` is `"%8.0gc"`
(`$BASE/t/tickset_g.class:23`), overwritten from the variable.

**Rescaling — quoted** (`:344-350`; identical in `g.txt:21649-21652`):

> norescale specifies that the ticks or labels in the option be placed
> directly on the graph without rescaling the axis or associated plot region
> for the new values. By default, label options automatically rescale the
> axis and plot region to include the range of values in the new labels or
> ticks. norescale allows you to plot ticks or labels outside the normal
> bounds of an axis.

The default rule widens too: with `scatter mpg weight` "four values are
labeled on each axis because choosing five would have required widening the
scale too much" (`:557-568`), i.e. nice ticks may extend the axis, and the
tick chooser trades count against widening.

Repeated options (`:1029-1035`): without `add` "the rightmost of each is
honored"; with `add` values merge; "All suboptions are rightmost".

`t*()` options also accept a *datelist* and the rule `date(#)date`, e.g.
`tlabel(1999m1(1)1999m12)` on a `%tm` axis (`:87-102`, `:190-191`).

`zlabel()`, `ztick()`, `zmlabel()`, `zmtick()`: apply to the contour legend
axis and, "when you create a two-way plot and use colorvar_options … The
levels of this numeric variable will be presented on the z axis; thus, the
zlabel(), ztick(), zmlabel(), and zmtick() options can be used" (`:813-820`).
Grid sub-options have no effect on z axes (`:810-811`).

---

## 3. axis_scale_options (`$BASE/a/axis_scale_options.sthlp`)

Names: `ysc:ale()`, `xsc:ale()`, `tsc:ale()`, `zsc:ale()` (`:34-39`),
*merged-implicit* (`:41-43`); several `yscale()` combine and the rightmost
sub-option wins (`:279-295`).

Sub-options and abbreviations (`:47-77`): `ax:is(#)`, `[no]log`,
`[no]rev:erse`, `r:ange(numlist)`, `r:ange(datelist)` (tscale only), `off`/`on`,
`fill`, `alt`, `fex:tend`, `ex:tend`, `noex:tend`, `noli:ne`, `li:ne`,
`titleg:ap(size)`, `outerg:ap(size)`, `lsty:le()`, `lc:olor()`, `lw:idth()`,
`lp:attern()`.

`range()` semantics:
- "specifies that the axis be expanded to include the numbers specified.
  Missing values, if specified, are ignored" (`:144-148`).
- Single value: `ysc(r(0))` extends 1–100 down to 0; `ysc(r(100))` extends
  0–99 up to 100; `ysc(r(0 100))` both (`:314-334`).
- "Specifying missing for a value leaves the current minimum or maximum
  unchanged; specifying a nonmissing value changes the range, but only if the
  specified value is outside the value that would otherwise have been chosen.
  range() never narrows the scale of an axis or causes data to be omitted from
  the plot" (`:336-341`). `xsc(r(10 50))` does not subset; use `if`
  (`:341-351`). [G-2] twoway scatter, `g.txt:18878` (p.416): "range() can
  widen, but never narrow, the extent of an axis."
- Any number of values may be listed (it is a numlist); each only widens.
  Order of values is irrelevant. **PROBE** `range(. 50)` (leading missing).

`log` (`:127-132`, `:359-388`): natural-log scale, "the axis is labeled in
natural units"; same picture as plotting `log(x)`. `reverse` (`:135-141`,
`:396-403`). `off`/`on` (`:157-161`): `off` removes "the axis line …, along
with all of its ticking, labeling, and titling" (`:412-418`); `fill` keeps the
space (`:164-166`). `alt` moves left→right or bottom→top (`:169-175`).
`noline` keeps ticks, labels and title (`:183-185`); ≡ `lstyle(noline)` ≡
`lstyle(none)` (`:440-446`). `noextend` = line spans only the axis range;
`extend` = across the plot region; `fextend` = also across its margins, "the
default with most schemes" (`:192-213`). `zscale()` acts like the others but
on the contour legend axis (`:453-459`).

---

## 4. Textbox, title and axis-title sub-options

### 4a. textbox_options (`$BASE/t/textbox_options.sthlp:41-78`)

| option (full) | min. abbrev | line | semantics |
|---|---|---|---|
| `tstyle(textboxstyle)` | `tsty` | :41 | overall style; default by context/scheme (`:126-149`) |
| `orientation(orientationstyle)` | `orient` | :43 | horizontal / vertical (bottom→top) / rvertical (top→bottom) (`:152-155`, `:332-355`) |
| `size(textsizestyle)` | `si` | :45 | |
| `color(colorstyle)` | `c` | :46 | text colour and opacity |
| `justification(left\|center\|right)` | `j` | :47 | horizontal placement of short lines in a multi-line box; irrelevant for one line (`:432-468`) |
| `alignment(baseline\|middle\|top)` | `al` | :49 | vertical |
| `margin(marginstyle)` | `m` | :51 | text→border; order top bottom left right (`:599-602`) |
| `linegap(size)` | — | :53 | |
| `width(size)`, `height(size)` | — | :54-57 | override computed box (`:609-649`; width is approximate, height never wrong) |
| `box` / `nobox` | — | :59 | border drawn; default usually `nobox` (`:211-218`) |
| `bcolor(colorstyle)` | `bc` | :60 | background **and** border; "matters only if box is also specified; otherwise, bcolor() is ignored" (`:221-229`, `:657-661`) |
| `fcolor(colorstyle)` | `fc` | :62 | background only, only with `box` (`:232-236`) |
| `lstyle(linestyle)` | `ls` | :63 | border line style |
| `lpattern(linepatternstyle)` | `lp` | :65 | forces `lalign` to center (`:261-262`) |
| `lwidth(linewidthstyle)` | `lw` | :67 | |
| `lcolor(colorstyle)` | `lc` | :69 | only with `box` (`:271-275`) |
| `lalign(linealignmentstyle)` | `la` | :70 | inside/outside/center |
| `bmargin(marginstyle)` | `bm` | :73 | border→containing box; used to nudge (`:579-602`) |
| `bexpand` | `bex` | :75 | expand in direction of text to the containing box (`:289-293`, `:653-655`) |
| `placement(compassdirstyle)` | `place` | :77 | override positioning; values `nw n ne w c e sw s se` (`:296-300`, `:692-781`) |

Not in the table: `nobexpand` (only `bexpand` is documented), `style()` (the
textbox word is `tstyle`; `style()` belongs to `legend()`/`region()`),
`axis(#)` and `position()/ring()/span` (these come from the *context*: title
or axis-title options, `:362-381`). `justification` does not centre the
title; `position()` does (`:432-434`).

Multi-line text: a textbox "is one or more lines of text" (`:322-327`);
`title("First line of title" "Second line", position(12) justification(left))`
(`:528-544`).

### 4b. title_options (`$BASE/t/title_options.sthlp`)

Names (`:28-36`): `ti:tle()`, `sub:title()`, `note()`, `cap:tion()`,
`t1:title()`, `t2:title()`, `b1:title()`, `b2:title()`, `l1:title()`,
`l2:title()`, `r1:title()`, `r2:title()` (the last eight twoway-only, `:41`,
and `position()` is not allowed with them, `:69`). *merged-explicit* (`:39`).

`tinfo` grammar (`:47-51`): `"string" ["string" [...]] [, suboptions]`;
strings may hold Unicode and SMCL (`:53-55`). Each string is a line
(`:296-314`); "You may have as many lines in your titles as you wish".

Sub-options (`:57-66`): `prefix`, `suffix`, `pos:ition(clockposstyle)`,
`ring(ringposstyle)`, `span`, plus every textbox option.

Repeated options (`:321-347`, `:411-415`): rightmost wins; `suffix` appends
its lines after the earlier text, `prefix` puts them before; earlier
options' *sub-options* (colour, position) are still merged. Examples `:74-79`.

Defaults: justification — `title`, `subtitle`, `t/b/l/r#title` centred;
`note`, `caption` left (`:540-547`); rings (`:86-108`, `:452-462`): plot 0,
`t1/b1/l1/r1` 1, `t2..` 2, legend 3 (table) — but the prose says legend
`ring(4)` (`:488`, `legend_options.sthlp:856-857`); note 4, caption 5,
subtitle 6, title 7. `position(0)` = centre of the plot region in ring 0;
in ring 0 clock 1/2, 4/5, 7/8, 10/11 coincide (`:501-508`). `span` widens the
placement area to the whole graph (`:570-597`); `box bexpand` stretches the
box to the plot-region width (`:627-655`).

### 4c. axis_title_options (`$BASE/a/axis_title_options.sthlp`)

Names (`:33-38`): `yti:tle()`, `xti:tle()`, `tti:tle()` ("a synonym for
xtitle()", `:91`), `zti:tle()`; *merged-explicit* (`:41`). Grammar (`:48-49`):
`"string" ["string" [...]] [, suboptions]`; sub-options `axis(#)` (1–9),
`prefix`, `suffix`, textbox options (`:57-62`).

Default title: "the corresponding variable's variable label or, if it does not
have a label, using its name" (`:158-159`); `lfit` labels y "Fitted values"
regardless (`:168-172`); several variables on one axis → no axis title,
a legend instead (`:175-184`).

Multi-line: `ytitle("First line" "Second line")`,
`xtitle("First line" "Second line" "Third line")` (`:210-215`).

Suppression — quoted (`:218-228`):

> To eliminate an axis title, specify {y|x}title("").
> To eliminate the title on a second, third, ..., axis, specify
> {y|x}title("", axis(#)).

Repeated: rightmost wins (`:235-236`); `xtitle("in days", suffix)` gives
"analysis time" / "in days" on two lines; `prefix` reverses (`:244-264`).
`ztitle()` is documented for contour only (`:281-287`) although `zlabel()`
is documented for colorvar (§2); **PROBE** whether `ztitle()` draws on the
colorvar key.

---

## 5. legend_options (`$BASE/l/legend_options.sthlp`)

Names: `leg:end()`, `pleg:end()`, `cleg:end()` (`:26-31`), *merged-implicit*
(`:34-35`).

Grammars:
- `orderinfo` (`:104-111`): `{#|-} ["text" ["text" ...]]` repeated. "A dash
  specifies that text be inserted into the legend" (`:231-234`);
  `order(1 - "Predicted" 2 3)` adds a text-only line; `order(1 - " "
  "Predicted" 2 3)` adds a blank line then the text — "we typed " " and not
  "". Typing "" would insert nothing" (`:254-267`); `order(1 "Observed 1992"
  ...)` overrides key 1's text, "It is considered better style, however, to use
  the label() suboption" (`:270-275`). `order(1 2 3)` with four keys drops
  key 4 (`:225-227`).
- `labelinfo` (`:113-119`): `# "text" ["text" ...]`; `label(1 "Observed"
  "1992-1993")` is two lines; one key per `label()`, repeat for more
  (`:278-289`).
- `lastlabel()` (`:292-314`): "the last label to be applied and overrides any
  text specified in order() or label() … If the text for a key is modified by
  the order() suboption, you cannot change the label with the label()
  suboption, but you can with lastlabel()"; `lastlabel()` indexes by the key
  position **on the graph** after `order()` (`:305-309`).

Precedence: `order(# "text")` beats `label(# "text")`; `lastlabel()` beats
both; `label()` on an `order()`-relabelled key is ignored.

Default key text: "obtained from the variable's variable label … If the
variable has no variable label, the variable's name is used" (`:818-820`);
`lfit` keys read "Fitted values" (`axis_title_options.sthlp:183-184`). The
legend is shown only when more than one symbol is drawn; `legend(on)` forces,
`legend(off)` suppresses (`:698-703`, `:779-811`). `all` makes a key per plot
even with repeated styles (`:346-364`).

Layout (`:56-62`, `:394-506`): `c:ols(#)`, `r:ows(#)` (alternatives; default
`cols(2)`), `[no]colf:irst` (default `nocolfirst`), `[no]textf:irst`
(default `notextfirst`: symbol then text), `stac:k` (symbol above text),
`rowg:ap()` (default 1.4), `colg:ap()` (4.9), `symp:lacement()` (center),
`keyg:ap()` (2), `symy:size()`, `symx:size()` (13), `textw:idth()`,
`forces:ize`, `bm:argin()`, `hol:es(numlist)` (`:317-343`), `sty:le()`,
`reg:ion(roptions)` with `sty:le`, `c:olor`, `fc:olor`, `ls:tyle`,
`lc:olor`, `lw:idth`, `lp:attern`, `la:lign`, `m:argin` (`:126-145`).
Location: `off|on`, `pos:ition()`, `ring()`, `bplace:ment()`, `span`,
`at(#)` (`:84-95`); default `position(3) ring(4)` (`:856-857`). With `by()`,
*contents* go outside `by()` and *location* inside it (`:960-990`).

---

## 6. colorvar_options (`$BASE/c/colorvar_options.sthlp`; table in `$BASE/c/colorvar_optstbl.ihlp`)

Continuous default (`:73-80`): colorvar "must be numeric. The range of values
for colorvar will be divided into levels, formed by equally spaced values …
The number of levels is determined by the major ticks on the z axis.
Additionally, if colorvar contains missing values, these missing values will
form a separate category and will be included in the graph in the color
gray." No numeric default is stated; the z axis is an axis, so "approximately
five" nice values (`axis_label_options.sthlp:557`) — **PROBE** the count.

`colordiscrete` (`:92`) "treats colorvar as a discrete variable."

`colorcuts(numlist)` / `colorlevels(#)` (`:95-98`): "may not be combined. If
neither option is specified, the values used for the major ticks on the z axis
are used as cuts." `colorcuts()`/`colorlevels()` are exact; `zlabel()` is
approximate (`:101-108`).

`colorcuts(numlist)` (`:111-116`): values "will be sorted, and the levels
determined as follows: (-infinity,n_1], (n_1, n_2], …, (n_{k-1}, n_k],
(n_k, infinity). Any values below the minimum for colorvar are ignored; if all
values are below the minimum, the minimum value will be used as the cut."
With `colordiscrete` (`:119-121`): "the values in numlist will be the levels.
Any values that are not included in these levels will be grouped with missing
values and displayed in gray."

`colorlevels(#)` (`:124-128`): "creates # - 1 equally spaced cuts between the
minimum and maximum of colorvar … n_1, …, n_k, where k = # - 1", same
half-open intervals. With `colordiscrete` (`:131-134`) the levels are
n_1..n_k, others gray; "rarely specified".

`colorvarminmax` (`:137-140`): modifier of `colorcuts()`/`colorlevels()`;
"the minimum and maximum of colorvar be included in the list of cuts. The
major ticks on the z axis will also be updated to include the minimum and
maximum values."

`colorrule([crule] [%# [*#]])` (`:143-159`): crule ∈ `hue` (default), `chue`,
`phue` (p1–p15 then hue), `int:ensity`, `lin:ear` (`:28-41`); `%#` opacity
and `*#` intensity modify it, e.g. `colorrule(hue %40 *2)`.
`colorstart()`, `colorend()` (`:162-167`); `colorlist()` (`:170-175`, quote
RGB/CMYK/HSV/hex/`red*.3`). `colorfillonly` (`:178-185`),
`colorformissing(colorstyle)` (default gray, `:188-190`), `colorkeysrange`
(`:193-194`), `coloruseplegend` requires `colordiscrete` (`:197-200`).

Parser abbreviations from twoway's own class
(`$BASE/t/twoway_yxview_parse.class:146-148,186-200`): `COLORVar`,
`COLORSTart`, `COLOREnd`, `COLORLEVels`, `COLORVARMINMax`, `COLORRule`,
`COLORLIst`, `COLORFORMISSing`, `COLOROTHERLABel` (undocumented). The class
enforces `confirm numeric variable `colorvar'` (`:220`).

`zlabel()` etc.: §2 (`axis_label_options.sthlp:813-820`); `zscale()`:
`axis_scale_options.sthlp:453-459` (documented for contour only); `ztitle()`:
§4c.

---

## 7. twoway histogram binning (`$BASE/t/twoway__histogram_gen.ado`)

Syntax (`:6-17`): `varname(numeric) [fw] [if] [in]`, `DISCrete`,
`BINs(numlist max=1 >0 integer)`, `Width(numlist max=1 >0)`,
`START(numlist max=1)`, `DENsity FRACtion FREQuency PERCENT`.

Exclusions (`:27-51`): `discrete`+`bins()` → "options discrete and bins() may
not be combined" r(198); `bins()`+`width()` → "options bins() and width() may
not be combined" r(198); two height types → "options `type' may not be
combined" r(198); none → `density`.

Range (`:73-100`): `sum … meanonly` with weights; N = r(N) (weighted);
min/max from the data; `if min == max & width == "" → width 1`.

`start()` (`:102-116`): error when `min < start & reldif(min,start) > 1e-5`:

> option start() may not be larger than minimum of `v'   (r(198))

(so a start a hair above the minimum is tolerated by relative 1e-5); in the
continuous case `min = start`; in the discrete case the minimum is **not**
moved (`:109-111`) — start "does nothing more than add white space to the
left side of the graph" (`$BASE/h/histogram.sthlp:187-188`,
`$BASE/t/twoway_histogram.sthlp:133-134`). Help wording: "start(#), if
specified, must be less than or equal to m, or else an error will be issued"
(`histogram.sthlp:154-155`; `twoway_histogram.sthlp:137-138,175-176`).

Continuous bins (`:119-143`):
- no `width()`, no `bin()`: `bin = int(min(sqrt(N), 10*log(N)/log(10)))`,
  then `max(1, bin)`; `h = (max-min)/bin` (`:122-130`). Help:
  `k = min(sqrt(N), 10*ln(N)/ln(10))` (`histogram.sthlp:135-142`,
  `twoway_histogram.sthlp:154-161`). Note `int()` truncates.
- `width()`: `h = width`; `bin = ceil((max-min)/h)`, `max(1, bin)` (`:132-136`).

Discrete (`:144-164`): `h` = smallest positive difference between sorted
values (1 if none) unless `width()`; `min = min - h/2`;
`bin = int((max-min)/h + .5)`.

Returned (`:166-185`): `area` (frequency `N*h`, fraction `h`, percent
`100*h`, density 1), `max = min + h*bin`, `min`, `start`, `width`, `bin`, `N`,
`type`.

Bin index and the fold (`:200-203`):
```
gen `midbin' = floor((`v'-`min')/`h') if `touse'
replace `midbin' = 0 if `touse' & `midbin' < 0
replace `midbin' = `bin'-1 if `touse' & `midbin' == `bin'
```
A value exactly at (or floating above) the last edge — including every value
equal to the maximum — is folded into the last bin; values below `min` (only
possible via the 1e-5 start tolerance) into the first.

Heights (`:206-231`): `tabulate midbin [fw], matcell matrow` → only **non-empty**
bins are emitted (`obins = r(r)`, `:211`; `n_x` returned `:248`); centre
`x = min + h/2 + h*index` (`:212`); density `count/(N*h)`, fraction
`count/N`, percent `100*count/N`, frequency `count`. With a user `start()`
an extra observation with `x = start` and missing height is appended
(`:232-235`) so the axis reaches `start`. The x variable takes `v`'s display
format and label (`:220-221`); the y label is "Density"/"Fraction"/
"Frequency"/"Percent" (`:79-81`, `:244-245`) — the default y title.

---

## 8. Display formats ([D] format, [U] 12.5.1, [D] Datetime display formats)

### 8a. Numeric (`$BASE/f/format.sthlp`)

Syntax table (`:55-83`): `%w.dg`, `%w.df`, `%w.de` (right-justified), `%21x`,
`%16H`, `%16L`, `%8H`, `%8L`, `%w.dgc`, `%w.dfc`, `%0w.df` (leading zeros),
`%-w.dg`/`f`/`e`/`gc`/`fc` (left-justified). Comma decimal: "You may
substitute comma (,) for period (.) in any of the above formats … In
%9,2fc, 1000.03 is 1.000,03" (`:84-88`; also `set dp comma`). `%~ws` centres,
"for use with display only" (`:136-140`, `:461-467`). Defaults by type:
byte/int `%8.0g`, long `%12.0g`, float `%9.0g`, double `%10.0g`, str# `%#s`,
strL `%9s` (`:159-166`).

[U] 12.5.1 (`u.txt:4729-4805`, p.104-105): order is `%` `[-]` `[0]` `w` `.`
`d` `{e|f|g}` `[c]`; "d must be less than w"; `c` not allowed with `e`;
leading-zero `0` honoured only with `f` (`:4742`). "%w.dg … The 4 means to
display approximately four significant digits … 3.14159265 in %9.4g … 3.142,
31.4159265 as 31.42, 314.159265 as 314.2, and 3141.59265 as 3142. The format
is not exactly a significant digit format because 31415.9265 is displayed as
31416, not as 3.142e+04" (`:4790-4794`). `f` "switches to g whenever a number
is too large to be displayed in the specified f format" (`:4797-4798`). `e`
needs `w ≥ d+7` (`:4803-4805`; format.sthlp `:343-345` says d+8 for 3-digit
exponents).

`%g` ([D] format `:292-325`; `d.txt:13132-13152`, p.299): d=0 lets Stata
choose the decimals; d≠0 caps them; "it will switch to a %e format if the
number is too large or too small". Documented examples: `%12.0g`: 5.139 →
`5.139`; 5231371222.139 → `5231371222`; 52313712223.139 → `5.23137e+10`;
0.0000029394 → `2.93940e-06`. `%9.0g` (`:475-480`, `u.txt:4746-4749`):
12345, 37.916, 3567890, .9165, 1.414214, 1000, 10,000,000 → `1.00e+07`.

**Derived width rule (not stated verbatim anywhere; consistent with every
documented example; must be pinned by the display fixture):** `%w.0g` shows
at most `w-2` significant digits in fixed notation (9→7: `1.414214`,
`3567890`; 12→10: `5231371222`); a value needing more, or one whose fixed
form would not fit `w-1` characters (`0.0000029394` is 12 wide), switches to
exponent form with a `w-6`-digit mantissa padded with trailing zeros
(`1.00e+07` for w=9; `5.23137e+10`, `2.93940e-06` for w=12). Trailing zeros
of a fixed-form value are dropped (`.9165`, no leading 0).

`%f` (`:225-249`): fixed decimals, d=0 drops the point. `%fc` (`:256-285`)
inserts thousands separators, width counts them. `%gc` = `%g` with commas
(`:332-334`). `%e` (`:341-357`). `%21x` (`:364-383`) and `%16H`/`%16L`/
`%8H`/`%8L` (`:390-429`) are hexadecimal / IEEE byte dumps (the plan refuses
them, Q6). Invalid formats are r(120) "invalid %format" (`p.txt:9603`).

### 8b. Dates (`$BASE/d/datetime_display_formats.sthlp`)

Format heads (`:27-39`): `%tc`, `%tC`, `%td`, `%tw`, `%tm`, `%tq`, `%th`,
`%ty` (+ `%tg` generic, `%tb` business, `format.sthlp:103,119`), each with
optional *details*. Codes (`:45-106`): `CC`/`cc` century−1, `YY`/`yy`
2-digit year, `JJJ`/`jjj` day of year, `Mon`/`Month`/`mon`/`month`, `NN`/`nn`
month number, `DD`/`dd`, `DAYNAME`/`Dayname`/`Day`/`Da`/`day`/`da`, `h` half,
`q` quarter, `WW`/`ww` week, `HH` 00-23, `Hh` 00-12, `hH` 0-23, `hh` 0-12,
`MM`/`mm`, `SS`/`ss` (00-60, leap seconds), `.s`, `.ss`, `.sss`, `am`,
`a.m.`, `AM`, `A.M.`, literal `.` `,` `:` `-` `_`(space) `/` `\`, `!c`
(any character), `+` separator that "displays nothing" (`:105-110`).

Default pictures (`:113-127`; `d.txt:7003-7012`, p.161):

| head | implied picture | typical text |
|---|---|---|
| `%tC` | `%tCDDmonCCYY_HH:MM:SS` | 20jan2010 15:15:30 |
| `%tc` | `%tcDDmonCCYY_HH:MM:SS` | 20jan2010 15:15:30 (`:160-161`) |
| `%td` | `%tdDDmonCCYY` | 20jan2010 |
| `%tw` | `%twCCYY!www` | 1960w1 (`d.txt:4853`) |
| `%tm` | `%tmCCYY!mnn` | 1960m1 (`d.txt:4854`), i.e. 2000m10 |
| `%tq` | `%tqCCYY!qq` | 1960q1 |
| `%th` | `%thCCYY!hh` | 1960h1 |
| `%ty` | `%tyCCYY` | 1998 (year itself, not an offset — `scripts/extract_date_truth.do:34-35`) |

Fractional seconds are omitted by default; `%tcDDmonCCYY_HH:MM:SS.sss` shows
them (`:259-266`). Times are **truncated, not rounded** (`:272-287`).
Worked pictures (`:219-243`): `%tdCCYY.NN.DD` → 2010.01.20;
`%tdMonth_dd,_CCYY` → January 20, 2010; `%tdnn/dd/YY` → 1/20/10;
`%tcCCYY.NN.DD_HH:MM`; `%tcMonth_dd,_CCYY_hh:MM_am` → January 20, 2010 3:15 pm;
`%tcDay_Mon_DD_HH:MM:SS_CCYY` → Wed Jan 20 15:15:30 2010. `%tdCCYY-NN-DD` uses
the `-` hyphen code (`:99`). The repo already records verbatim `display`
output for every epoch plus ISO pictures in `test/fixtures/date_truth.json`
via `scripts/extract_date_truth.do:19-40,115-133`; the new numeric-format
fixture should follow that script's shape.

---

## 9. Scheme file grammar ([G-4] scheme files, colorstyle, shipped schemes)

Entry grammar (`$BASE/s/scheme_files.sthlp:86-100`): each line is
`styletype element style`, e.g. `symbolsize matrix medium`; "the first word
… specifies the styletype, or attribute affected; the second word is the
graph element …; and the third word is the style". Values with more than one
token must be quoted: `color axis_title "255 0 0"` — "the RGB values and any
style using more than one token or word must be enclosed in quotes"
(`:121-130`). `#include schemename` must precede other entries (`:54-72`).
Comments: "comments can only be entered as entire lines and the lines must
begin with a "*"" (`:322-324`); `*! version …` is a comment (`:303`,
`:324-326`). Extra spaces inside an RGB string are ignored
(`"  0 255   0"`, `:343-350`). s2color has "over 1,700 entries" (`:392`).
File name `scheme-<name>.scheme` (`:45-51`).

Colour value grammar (`$BASE/c/colorstyle.sthlp:144-165`): `"# # #"` RGB
(`"255 255 255"`), `"# # # #"` CMYK (`"0 0 255 0"`), `"hsv # # #"`
(`"hsv 0 0 1"`), `"#RRGGBB"` (`"#FF0000"`), `colorstyle*#` intensity,
`colorstyle%#` opacity 0–100, bare `*#` / `%#` adjust the default colour;
named colours (`:128-142`, `none`, `background`/`bg`, `foreground`/`fg`).
Opacity examples `green%50`, `"0 255 0%50"`, `%30` (`:221-240`); intensity
`green*.8`, `purple*1.5`, `"0 255 255*1.2"`, `"hsv 240 1 1*.5"`, no space
before `*` (`:246-258`).

Five example lines from shipped schemes:
1. `$BASE/s/scheme-sttrans.scheme:44` — `color p1  "26 71 111 %20"` (quoted RGB with a space-separated `%20` opacity; `:43` `color p  "26 71 111 %20"`, `:45` `color p2  "204 102 119 %20"`, `:46` `color p3  "221 204 119 %20"`)
2. `$BASE/s/scheme-economist.scheme:154` — `color dot_area       "218 231 253"`
3. `$BASE/s/scheme-s2color.scheme:430` — `color p1      navy` (`:431` `color p2      maroon`, `:432` `color p3      forest_green`)
4. `$BASE/s/scheme-s2color.scheme:1268` — `intensity foreground inten100` (`:1267` `intensity            full`, `:1272` `intensity ci_area    full`)
5. `$BASE/s/scheme-s2color.scheme:1-23` — comment block (`* s2 scheme family …`, `*!  version 1.5.2   23feb2024`); `:25-45` non-colour entries `sequence 1210`, `label "s2 color"`, `system naturally_white 1`, `graphsize x 5.5`, `numstyle legend_cols 2`, `numstyle pcycle 15`.

Also `$BASE/s/scheme-stcolor.scheme:47` `color p1   stc1` (named palette
entries) and `$BASE/s/scheme-s2color.scheme:78` `special fpfmt_es  `"%6.2f"'`
(compound-quoted values exist). No shipped scheme uses CMYK, `hsv` or `*#`
inside a `color` entry; sttrans is the only one with `%NN`, and it writes the
opacity **after a space** inside the quotes, whereas the colorstyle help shows
`"0 255 0%50"` without one — both must parse. p# resolution order is
`p#stub`, `pstub`, `p#`, `p` (`scheme-s2color.scheme:6-17`).

---

## 10. `start()` restriction text

- `$BASE/h/histogram.sthlp:145-155`: "start(#) specifies the theoretical
  minimum of varname. The default is start(m), where m is the observed minimum
  value … start(#), if specified, must be less than or equal to m, or else an
  error will be issued." Discrete: `:180-192` "does nothing more than add
  white space to the left side of the graph … must be less than or equal to
  m, or an error will be issued."
- `$BASE/t/twoway_histogram.sthlp:124-138` (discrete), `:164-176` (continuous):
  same wording.
- The error actually raised: `option start() may not be larger than minimum
  of <var>`, r(198), with the 1e-5 relative tolerance
  (`twoway__histogram_gen.ado:102-107`).

---

## 11. The `.Graph` object and exported SVG

`.Graph` members the repo already reads after `twoway … [, nodraw]`:
- `.Graph.subtitle.text[1]` (`test/test_graph_option_scope.cscript:152`)
- `.Graph.graphs.arrnels`, `.Graph.graphs[k].plotregion1.plot1.serset.id`
  then `serset set`/`serset use` (`test/test_qualifier_in_stata.cscript:770-780`)
- `.Graph.plotregion1.plot1.style.area.linestyle.color.rgb` → "255 0 0"
  (`test/test_ci_band_options.cscript:262-266`)
- `.Graph.plotregion1.plot1.base` (`test/test_help_claims_6.cscript:672-673`)

Axis extents. There is no stored member named `range_min`; that name is only
an argument of `transform.rescale` (`$BASE/t/transform.class:92-104`,
`$BASE/g/gditransform.class:16-47`). The extents live in the plotregion's
scale objects: `axis.class` reads `.plotregion.yscale.min` / `.max`
(`$BASE/a/axis.class:179-183`), and `scale.class` holds `min`, `max`
("permanent"), `curmin`, `curmax` ("temporary"), `reverse`, `transform`
(`$BASE/s/scale.class:19-27`; `addmin`/`addmax`/`addcur` at `:265-298`).
Tick sets hold the rule range `min`, `max`, `delta`, the explicit `ticks`
array, `label_format` and `_tmin`/`_tmax` (`$BASE/t/tickset_g.class:20-33`);
`set_ticks` widens a degenerate range to ±1 (`:246-252`) and pushes the tick
range into the scale with `.scale.addcur` (`:250`). Candidate paths for a cert
script: `.Graph.plotregion1.yscale.min`, `.max`, `.curmin`, `.curmax`;
`.Graph.yaxis1.major.min`, `.max`, `.delta`, `.ticks[i]`;
`classutil describe .Graph.plotregion1.yscale` / `classutil describe
.Graph.yaxis1.major` list them (`$BASE/c/classutil.sthlp:38-44,91-97`, option
`recurse` `:117-129`). **PROBE** which of `min`/`curmin` equals the drawn
extent and whether they are populated without drawing (`nodraw`);
`scripts/extract_axis_truth.do:20-56` records that a saved `.gph` stores only
the *request* (`.xaxis1.major.suggest_ticks 10`), which is why that script
recovers the range by inverting the SVG.

Exported SVG (`graph export f.svg[, as(svg)]`, `$BASE/g/graph_export.sthlp:62`;
options in `$BASE/s/svg_options.sthlp:24-45`). What twoway writes, as the
repo has measured (`scripts/extract_axis_truth.do:44-56`): the plotregion is a
solid-fill `<rect>` before its border; each tick a short black `<line>` at a
plotregion edge; each tick label a `<text>` whose x (x axis) or y (y axis) is
at the tick; gridlines dashed multi-segment `<line>` groups; the legend in its
own `<rect>` with keys as `<text>` elements **without** `text-anchor`;
titles/labels are `<text>` with `font-size:NNpx` in `style`
(`test/test_help_claims_8.cscript:229-236`); marker/line colours appear as
`stroke:#RRGGBB` / fill (`test/test_twoway_option_parity.cscript:842`
counts `stroke:#FF0000`); sttrans's `%20` becomes `fill-opacity 0.20` and
`stroke-opacity 0.20` (`GAPS2.md:1059`, `dash_render.py:4110-4111`); text is
matched raw as `>Domestic<`/`>1</text>` (`test_help_claims_2.cscript:1023-1029`,
`_ztp_count` `test_twoway_option_parity.cscript:649-653,745`). Caveats for a
shared SVG text reader: `nbsp(on)` is the default, so runs of spaces in a
string are written as U+00A0 (`svg_options.sthlp:128-137`) — normalise before
comparing; `pre(off)` default; `version(on)` writes the Stata version
(`:32`); `ignorefont(off)` writes `font-family` (`:102-106`); subscripts use
`dy` not `baseline-shift` (`:93-99`). No `.svg` is checked into the repo
(`find` returned none); the desktop SVGs found are unrelated to Stata.

---

## 12. Return codes and wording

[P] error table (`p.txt`, printed p.196):
- `109. type mismatch` — "you attempted to combine a string and numeric
  subexpression in a logically impossible way" (`:9573-9575`). The specific
  message `syntax varlist(numeric)` prints for a string variable ("string
  variables not allowed in varlist; <var> is a string variable") is **not in
  any local help or PDF** (grep of p/u/d/g dumps and `$BASE/**/*.sthlp` found
  nothing) — it is emitted by the built-in `syntax`; **measure it** in the G2
  cscript. Parsers: twoway's y/x view uses
  `varlist(min=2 numeric ts default=none)` when `.varcheck` is set, else
  `[varlist(numeric ts default=none)]` (`$BASE/t/twoway_yxview_parse.class:119-124`;
  `ts` allows time-series operators, `p.txt:26527`); `histogram.ado:5`,
  `twoway__histogram_gen.ado:6` and `kdensity.ado:10,34` use
  `varname(numeric)`; colorvar uses `confirm numeric variable`
  (`twoway_yxview_parse.class:220`).
- `110. ___ already defined` — "A variable or a value label has already been
  defined, and you attempted to redefine it. This occurs most often with
  generate" (`:9577-9581`); ado wording `variable {bf:x} already defined`
  (`$BASE/r/reshape.ado:1224`), `x already defined` (`reshape_10.ado:817`).
- `111. ___ not found` / `no variables defined` / `variables out of order` /
  `ambiguous abbreviation` (`:9585-9598`).
- `120. invalid %format` (`:9603`).
- `121`–`127` numlist (§1).
- `198. invalid syntax` with variants `option ___ incorrectly specified`,
  `option ___ not allowed`, `___ invalid`, `range invalid`, `invalid obs no`,
  `invalid filename`, `invalid varname`, `invalid name`, `multiple by's not
  allowed`, `___ found where number expected`, `on or off required`
  (`:9713-9724`); "produced by syntax and other parsing commands when there is
  a syntax error in the use of the command itself" (`:9711-9712`). Histogram
  examples: "options bins() and width() may not be combined",
  "option generate() incorrectly specified" (`twoway__histogram_gen.ado:34-37,272-273`).
- `103. too many variables specified` (`:9547`) — what twoway gives when a
  third variable (e.g. `mlabel`'s) reaches `mspline`/`mband`
  (`test/test_twoway_option_parity.cscript:670-674`).

---

## Open items the plan must probe in Stata (collected)

1. numlist: spaces inside `a(b)c` / `a/b`; commas vs the sub-option comma;
   which rc a bad rule in `xlabel()` raises.
2. `xlabel(1 "a" "b")`: second line or error.
3. `range(. 50)` and repeated/unsorted `range()` values.
4. `.Graph.plotregion1.yscale.{min,max,curmin,curmax}` vs the drawn extent,
   with and without `nodraw`.
5. Default number of colorvar levels (z-axis nice ticks) and whether
   `ztitle()`/`zscale()` act on the colorvar key.
6. Exact `syntax varlist(numeric)` string-variable wording (r(109)).
7. The `%w.0g` significant-digit rule derived in §8a, over a Stata `display`
   fixture including negatives, `%w.dg` d>0, `%gc` with commas, `%9,2fc`,
   `%0w.df`, `%-w.dg`.
