# Phase 29 — Test debt and scheme ground truth

**Purpose.** Section 03 translated fourteen StataCorp schemes and got them exactly right:
an independent re-derivation compared **1,610 properties across the 14 files and found 0
disagreements**. But the adversarial pass overturned two of S03's DONE claims for the same
reason — the *record* is narrower than the work. The ground-truth fixture the translations
are written from stops short of five properties TR-03.3 names by name (`color foreground`,
`color text`, `color tick_label`, `color body`, `color subheading`), so those properties
exist nowhere in `dash`: not in `scripts/extract_scheme_truth.py`, not in
`test/fixtures/scheme_truth.json`, not in any of the 14 `schemes/*.scheme` files, and not in
`SchemeParser._init_properties`. Every downstream phase that wants to draw a subtitle, a
note or a caption from the scheme is therefore blocked on ground truth that has never been
extracted — `REMAINING.md` says so outright: that work *"needs S03-shaped work first … before
any renderer edit can be correct rather than invented."* And separately, the one behaviour
change 03-04 did make — two marker slots moved toward Stata — is recorded in no changelog at
all. This phase has no user-visible behaviour change of its own. It is the ground-truth and
record-keeping phase that makes Phases 23, 24 and 25 possible and honest, and it closes the
two paperwork gaps that hold S03 at 1 DONE / 4 PARTIAL.

---

## At a glance

| | |
|---|---|
| **Work items** | 2 |
| **Functional / deliverable** | 0 functional · 2 deliverable |
| **Effort mix** | 1 small · 1 medium |
| **Renderers touched** | **None.** Both items are `n/a` on the renderer axis: item 1 touches the extraction script, the JSON fixture and the 14 translated `.scheme` files; item 2 touches `.ultraplan/CHANGELOG.md`. No line of `DashRenderer` or `ServerAppBuilder` changes in this phase — that is deliberate, and it is what keeps the phase mergeable in parallel with everything else. |
| **Ultraplan tasks discharged** | **03-03** (*"Author the nine new translations and deepen the five existing ones"*) and **03-04** (*"Extend SchemeParser's vocabulary to the properties the translations now carry"*) — the two S03 DONE claims the adversarial pass overturned. Completes the unmet half of **TR-03.3** and extends **03-01**'s ground-truth extraction. |
| **Sections advanced** | **S03 — Scheme translation.** Final tally at HEAD: `1 DONE / 4 PARTIAL / 0 NOT DONE` over 5 tasks. This phase is what lets 03-03 and 03-04 return to DONE. |
| **Depends on** | Nothing. No upstream phase, no code dependency, no merge conflict with any other phase's files. Runnable immediately. |
| **Unblocks** | **Phase 23** (Scheme consumption I(a) — text sizing and typography), **Phase 24** (Scheme consumption I(b) — subtitle, caption and the size stubs) and **Phase 25** (Scheme consumption II). The `gsize body` / `color body` / `gsize subheading` / `color subheading` keys are the ground truth those phases consume; without them their work is invention rather than translation. Also feeds **Phase 31** (release closeout), which reconciles the changelog. |

---

## Why this phase exists

Everything in this section is copied from `REMAINING.md`. Where a line was re-confirmed
against the tree while this document was written, that is said explicitly and the command is
given.

### The two overturned claims

`REMAINING.md`, *"17 DONE claims the adversarial pass overturned"* — *"All to PARTIAL; 10
small, 5 medium, 1 large, 1 cosmetic."* Two of the seventeen rows are S03's, and they are
this phase:

| task | what the refutation found |
|---|---|
| 03-03 | 14 translations independently re-derived exact (1,610 properties, 0 disagreements); `color foreground`/`text`/`tick_label` still absent from the fixture |
| 03-04 | cosmetic — two marker slots moved *toward* Stata; record-keeping only |

03-04 is the single **cosmetic** row in that table of seventeen.

### The section status, both before and after the adversarial pass

From the *"Status by section"* table:

| # | Section | Tasks | Status | What is left |
|---|---|---:|---|---|
| 03 | Scheme translation | 5 | 3 done, 2 partial ② | `color foreground`; all 14 inert once installed ① |

And from *"Final tally, after the adversarial pass"*, S03 reads `1/4/0` —
DONE / PARTIAL / NOT DONE. The arithmetic between the two tables is exactly these two
items: the deep audit called S03 *3 done, 2 partial*; the adversarial pass overturned 03-03
and 03-04, leaving `1 DONE / 4 PARTIAL / 0 NOT DONE`.

`REMAINING.md` is explicit that this is not half-built work:

> **Read PARTIAL carefully — it is not "half-built".** In most cases the audit found the
> defect the task was written against genuinely fixed and proven load-bearing by mutation,
> with a *secondary* deliverable missing: a cscript the TDD stubs named, a CHANGELOG entry,
> a help sentence, a no-caller test.

S03 is that case twice over. The translations are right. The record is short.

### What TR-03.3 actually asked for

The plan's own technical requirement, from `.ultraplan/sections/section-03-scheme-translation.md`:

> - TR-03.3 Property coverage per file must include, at minimum: the `p1`-`p15` cycle for
>   colour, **marker symbol, marker size, line pattern and line width**; background, plot
>   region and grid colours; foreground and axis-line colours; title, subtitle, axis-title,
>   tick-label, note and caption text sizes and colours; legend background, border and
>   position; fill/bar/area alpha; and **graph size** (`graphsize x`, `graphsize y`), which is
>   what S10 uses for figure geometry.

Three clauses of that requirement are unmet: **foreground** colour, **subtitle** size and
colour, and the text **colours** for tick labels and body text. Everything else in the
sentence landed.

### The measurement that shows how narrow the gap is

Re-confirmed while writing this document. The fidelity harness states its own unit count at
`test/test_scheme_fidelity.py:237`:

```python
#: Total property units per scheme: 6 lists x 15 + 25 scalars = 115.
```

14 schemes × 115 units = **1,610** — the exact number in the 03-03 refutation, and the
denominator of "0 disagreements". So the translations are 1,610/1,610 faithful against a
fixture that never asked about the five properties in question.

The fixture's own colour scalars, `scripts/extract_scheme_truth.py:517-539`:

```python
"background_color": color_of("background_color", ["background"]),
"plotregion_color": color_of("plotregion_color", ["plotregion"]),
"legend_bg_color":  color_of("legend_bg_color", ["legend"]),
"legend_border_color": color_of("legend_border_color", ["legend_line"]),
"grid_color":       color_of("grid_color", ["major_grid", "grid"]),
"minor_grid_color": color_of("minor_grid_color", ["minor_grid"]),
...
"title_color":      color_of("title_color", ["heading"]),
"axis_line_color":  color_of("axis_line_color", ["axisline"]),
```

Eight colour scalars. No `foreground`, no `text`, no `tick_label`, no `body`, no
`subheading`. The `gsize` family at `:555-564` is `text`, `heading`, `axis_title`,
`tick_label`, `note` — no `body`, no `subheading`.

Confirmed against the generated fixture at HEAD:

```
$ python3 -c "import json; d=json.load(open('test/fixtures/scheme_truth.json')); \
             print(sorted(d['stcolor']))"
39 keys — foreground_color ABSENT, text_color ABSENT, tick_label_color ABSENT,
           body_color ABSENT, body_size ABSENT,
           subheading_color ABSENT, subheading_size ABSENT
```

And confirmed against the 14 translated files:

```
$ grep -l "color foreground" schemes/*.scheme   -> 1   (a comment in economist.scheme, not a directive)
$ grep -l "color text"       schemes/*.scheme   -> 0
$ grep -l "color tick_label" schemes/*.scheme   -> 0
$ grep -l "color body"       schemes/*.scheme   -> 0
$ grep -l "gsize subheading" schemes/*.scheme   -> 1   (the same comment)
```

The single hit is `schemes/economist.scheme:241-247`, which records the omission as a
deliberate decision:

```
* Keys carried by the earlier approximation and dropped here because
* SchemeParser._init_properties() reads none of them, and inventing dash
* vocabulary is what this translation exists to stop:
*   color foreground, color grid (economist's grid colour is recorded above
*   under the key dash actually reads, "color major_grid"), linewidth
*   minor_grid, gsize subheading, gsize body.
```

That was the right call *at the time* — a key with no ground truth behind it is a guess. This
phase removes the reason for the omission by extracting the ground truth first.

### Why it matters downstream — `REMAINING.md` says so in its own words

From Appendix C, the 11-04 list:

> - **[func · both · S]** The graph-level subtitle clause cannot be closed inside
>   dash_render.py at all: Stata's subtitle is textboxstyle-subheading, which reads
>   `gsize subheading` and `color subheading`, and SchemeParser parses NEITHER — and the 14
>   translated .scheme files deliberately dropped both. So the remaining item 'give the
>   subtitle a real scheme value' needs S03-shaped work first (add the keys to
>   schemes/*.scheme, add `subheading_font_size` / `subheading_color` to _init_properties)
>   before any renderer edit can be correct rather than invented.     *Where:*
>   `dash_render.py:2040-2048 (SchemeParser._init_properties font-size block — no subheading
>   attribute); schemes/*.scheme (all 14); dash_render.py:9893-9896 and :13952-13953 (the
>   subtitle Label in each ren`

And the note, immediately above it:

> - **[func · both · S]** `gsize note` is a DEAD key at Stata scheme level — exactly the trap
>   this file already documented for `draw_major_grid`. No style file reads `scheme note`;
>   the note textbox is textboxstyle-body, which reads `gsize body` / `color body`. Wiring
>   SchemeParser.note_font_size (from `gsize note`) to the note Label, as the remaining item
>   prescribes, would draw economist's note at 14pt where Stata draws ~8.6pt. Parse
>   `gsize body` (and `color body`) instead, and add those keys back to the 14 translated
>   .scheme files, which dropped them on purpose.     *Where:*
>   `dash_render.py:2047 (`self.note_font_size = self._gsize("gsize note", "9pt")`);
>   schemes/*.scheme (all 14 carry `gsize note`, none carries `gsize body`);
>   dash_render.py:9867 and :13932 (the `_TEXTBOX_D`

And the caption:

> - **[func · both · S]** The section's TDD stub names CAPTION explicitly ('title, subtitle,
>   axis-title, tick-label, note and caption sizes come from the scheme') and the caption is
>   untouched: both renderers draw it at a hardcoded 12.0px / #555555 with no scheme key
>   parsed. Like the note, its Stata source is `gsize body` / `color body` via
>   textboxstyle-body. *Where:* `dash_render.py:9866-9869 (`_TEXTBOX_DEFAULTS` in
>   DashRenderer._make_figure_body) and dash_render.py:13931-13934 (the emitted copy in
>   ServerAppBuilder)`

Three separate downstream items — subtitle, note, caption — all wait on the same two
`gsize`/`color` pairs. That is the whole argument for doing this phase early and cheaply.

The **14pt vs ~8.6pt** figure checks out exactly, and the check is worth recording because it
shows the extraction is the load-bearing part. `economist` declares `gsize note large` and
`gsize body 3.0`; the fixture resolves `large` to relative `4.8611`
(`test/fixtures/scheme_truth.json`, `economist.note_size`), and
`SchemeParser._GSIZE_PT["large"]` is `"14pt"` (`dash_render.py:1638-1655`). Scaling by the
relative ratio: 14 × (3.0 / 4.8611) = **8.64pt**. The note is nearly 40% too large if drawn
from `gsize note`.

### The scheme that makes the omission visible

`s1rcolor` is the reverse-video scheme. Its fixture entry gives
`background_color #000000`, `plotregion_color #000000`, `title_color #ffffff`,
`axis_line_color #ffffff`. Reading Stata's own `scheme-s1rcolor.scheme` (the same file the
extractor already parses, under `_meta.scheme_dir`), all five omitted keys are declared
`white`:

```
color foreground  white
color text             white
color body             white
color subheading       white
color tick_label       white
```

Nothing in `dash` carries any of those five values today — not the fixture, not the
`.scheme` file, not `SchemeParser`. So the only text colour a `dash` figure can use for a
caption under `s1rcolor` is the hardcoded `#555555` in `_TEXTBOX_DEFAULTS`
(`dash_render.py:9866-9869`), against a `#000000` plot region. That is the concrete shape of
the gap, and it is why "foreground and axis-line colours" sits in TR-03.3 as one clause: the
axis-line half landed, the foreground half did not.

### Every one of the 14 can supply these values

Confirmed by reading Stata's scheme files directly — the same files
`scripts/extract_scheme_truth.py` already walks, with the same `#include` chain and
last-write-wins rule it already implements:

| scheme | declares the keys directly | resolves through |
|---|---|---|
| `s2color` | all 7 (`color foreground/text/tick_label/body/subheading`, `gsize body/subheading`) | — (root of every chain) |
| `s2mono`, `s1color`, `s1rcolor` | the 5 colours | `#include s2color` for the 2 gsizes |
| `s1mono` | `color foreground` | `#include s1color` → `s2color` |
| `economist` | `color foreground`, `gsize body`, `gsize subheading` | `#include s2color` |
| `stcolor`, `stcolor_alt`, `stgcolor`, `stmono1`, `stmono2`, `stsj`, `s2gcolor`, `sj` | none directly | `#include` chains that all terminate at `s2color` |

Every chain reaches a declaration, so all 14 will resolve and none should add an entry to
its `unresolvable` list. There is no "honest gap" to declare here — which is exactly why the
omission is closable rather than merely documentable.

### Item 2's evidence: the marker slots

`REMAINING.md`'s row is one line — *"cosmetic — two marker slots moved toward Stata;
`s2color` really does declare `smdiamond`/`smtriangle`"* — and the change it refers to is
still in the tree, at `dash_render.py:1195-1202`:

```python
# Remaining symbol-<name>.style entries from Stata's style library.
# The mono schemes (s1mono, s2mono, sj, stmono1/2, stsj) cycle through
# smdiamond and smtriangle, which previously raised out of SchemeParser
# and made a faithful translation of those schemes unparseable.
"smdiamond":          "diamond",
"smdiamond_hollow":   "diamond",
"smtriangle":         "triangle",
"smtriangle_hollow":  "triangle",
```

The two slots are `p12` and `p14`. Confirmed present, verbatim, in six translated schemes:

| scheme | `symbol p12` | `symbol p14` |
|---|---|---|
| `schemes/s1mono.scheme` | `:145` `smdiamond` | `:147` `smtriangle` |
| `schemes/s2mono.scheme` | `:153` `smdiamond` | `:155` `smtriangle` |
| `schemes/sj.scheme` | `:172` `smdiamond` | `:174` `smtriangle` |
| `schemes/stmono1.scheme` | `:126` `smdiamond` | `:128` `smtriangle` |
| `schemes/stmono2.scheme` | `:165` `smdiamond` | `:167` `smtriangle` |
| `schemes/stsj.scheme` | `:153` `smdiamond` | `:155` `smtriangle` |

Before the change, `SchemeParser._symbol()` swallowed the `ValueError` from
`OptionTranslator.translate_msymbol()` and substituted a circle for both; after it, they draw
as a diamond and a triangle. On a monochrome print scheme, where series are distinguished by
symbol rather than by colour, two of fifteen series stopped being indistinguishable from the
rest. That is a picture a user has already seen changing, and `.ultraplan/CHANGELOG.md`'s own
opening contract is:

> Every entry here changes a number or a picture a user has already seen. Each one records
> the value before, the value after, and the evidence.

Re-confirmed at HEAD: `.ultraplan/CHANGELOG.md` is 1,195 lines with twelve `##` sections —
`S07`, `S08`, `S09`, `S10`, `S11`, certification suite, colour fidelity, `tabs()`/`by()`,
the audit, `S14`, `S15`, `S16`. **There is no S03 section and `grep -n "03-0"` returns
nothing.** This is the same class of gap `REMAINING.md` flags for S06 in the status table
(*"**no S06 entry in CHANGELOG** ②"*).

---

## Epics

| epic | goal | items |
|---|---|---|
| **E29.1 — Ground truth for the five omitted properties** | Extract `color foreground`, `color text`, `color tick_label`, `color body` and `color subheading` (plus `gsize body` and `gsize subheading`) from Stata, record them in the fixture, carry them into all 14 translated `.scheme` files, and extend the fidelity harness so they are gated rather than merely present. Closes the unmet third of TR-03.3 and unblocks Phases 23–25. | 1 |
| **E29.2 — Record the marker-slot change** | Give `.ultraplan/CHANGELOG.md` its missing S03 entry, recording the two marker slots that moved toward Stata with the before value, the after value and the evidence, in the form the changelog's own preamble requires. | 2 |

---

## User stories

### E29.1 — Ground truth for the five omitted properties

**US-29.1.1** — *As a package maintainer, I want every property TR-03.3 names to exist in
`scheme_truth.json` with its Stata provenance recorded, so that a later phase wiring the
subtitle or the note to the scheme is translating a measured value rather than inventing
one.*

- **Given** `scripts/extract_scheme_truth.py` has been re-run against Stata's own scheme and
  style tree,
  **when** `test/fixtures/scheme_truth.json` is read,
  **then** every one of the 14 scheme entries carries `foreground_color`, `text_color`,
  `tick_label_color`, `body_color`, `subheading_color`, `body_size` and `subheading_size`,
  **and** each has an entry in that scheme's `sources` map naming the exact
  `"<class> <key>"` directive Stata resolved through.
- **Given** the same regenerated fixture,
  **when** each scheme's `unresolvable` list is inspected,
  **then** it is still empty for all 14 — no new property was added that Stata could not
  answer (every `#include` chain terminates at `s2color`, which declares all seven).
- **Given** the regenerated fixture,
  **when** `_meta` is inspected,
  **then** `generated_by`, `generated_utc`, `stata_version`, `scheme_dir` and `style_dir` are
  all updated by the script, not by hand — `_meta.do_not_hand_edit` says
  *"Regenerate it by re-running scripts/extract_scheme_truth.py; do not hand-edit."*

**US-29.1.2** — *As a package maintainer, I want the fidelity harness to check the new
properties, so that "the fixture knows about them" cannot be mistaken for "the translations
carry them".*

- **Given** the seven new properties are in the fixture but **not** yet in the `.scheme`
  files,
  **when** `pytest test/test_scheme_fidelity.py` runs,
  **then** `test_scheme_property_fidelity` fails for all 14 schemes with
  `NOT SUPPLIED by the .scheme file` lines naming each missing directive.
- **Given** the same state,
  **when** `test_scheme_coverage` runs,
  **then** it **passes** — 115 faithful of 122 units is 0.943, above `COVERAGE_THRESHOLD`
  (0.90) — which is why the fidelity test, not the coverage test, is this phase's gate. This
  must be observed, not assumed.
- **Given** the `.scheme` files then carry the seven directives,
  **when** the harness runs again,
  **then** all 14 schemes are faithful on all 122 units: 14 × 122 = **1,708 properties, 0
  disagreements**, the successor to the 1,610 figure in the 03-03 refutation.

**US-29.1.3** — *As a Stata user with `set scheme s1rcolor`, I want the reverse-video
scheme's white text colours to be part of what `dash` ships, so that when the renderer learns
to use them my captions and tick labels are not dark grey on a black background.*

- **Given** the regenerated fixture,
  **when** `s1rcolor` is read,
  **then** `foreground_color`, `text_color`, `tick_label_color`, `body_color` and
  `subheading_color` are all `#ffffff`, matching the `white` Stata's own
  `scheme-s1rcolor.scheme` declares.
- **Given** `schemes/s1rcolor.scheme`,
  **when** it is read,
  **then** it carries those five as resolved `#rrggbb` directives, per the file-header rule
  every translation already states (*"Every colour below is written as a RESOLVED #rrggbb
  value, not as a Stata colour name"*).
- *(Out of scope here, stated so the boundary is explicit: making a rendered figure use these
  values is Phases 23–25. This phase makes the values exist.)*

**US-29.1.4** — *As a package maintainer, I want the per-file "HONEST GAPS" headers to stop
claiming these keys were dropped, so that the files do not document a decision that has been
reversed.*

- **Given** `schemes/economist.scheme:241-247` currently lists `color foreground`,
  `gsize subheading` and `gsize body` as deliberately dropped,
  **when** those directives are added to the file,
  **then** the header is rewritten to state what is now carried and why, and no header in any
  of the 14 files claims a key is absent that the file now declares.
- **Given** the precedent already set by `schemes/stgcolor.scheme:33-38` and
  `schemes/stmono2.scheme:31-35` for `yesno draw_major_hgrid`,
  **when** a reviewer asks why a directive `SchemeParser` does not yet read is present,
  **then** the header gives the same three-part answer: the directive name comes from the
  fixture's own `sources` map, it parses into `SchemeParser._props`, and
  `test_scheme_fidelity.py` checks it by that name.

### E29.2 — Record the marker-slot change

**US-29.2.1** — *As a `dash` user who built the same monochrome dashboard before and after
this branch, I want the changelog to tell me why two of my series changed shape, so that I do
not have to diff the source to find out.*

- **Given** `.ultraplan/CHANGELOG.md`,
  **when** it is read,
  **then** it contains an `S03` section recording that `symbol p12` (`smdiamond`) and
  `symbol p14` (`smtriangle`) previously rendered as circles and now render as a diamond and
  a triangle.
- **Given** that entry,
  **when** it is checked against the changelog's own contract (*"records the value before,
  the value after, and the evidence"*),
  **then** it names the before value, the after value, the six affected schemes and the
  source location (`dash_render.py:1195-1202`).
- **Given** that entry,
  **when** its scope claim is checked,
  **then** it states which schemes are affected as **measured**, not as assumed — the
  `REMAINING.md` row names `s2color`, and the directives are in the six mono translations
  (`s1mono`, `s2mono`, `sj`, `stmono1`, `stmono2`, `stsj`). The entry must be written from a
  re-measurement, because an entry that misattributes its own scope is worse than no entry.

**US-29.2.2** — *As a package maintainer closing out S16-07, I want S03 to have a changelog
section like every other behaviour-changing section, so that the release notes are assembled
from one complete record rather than from twelve sections plus a gap.*

- **Given** the twelve existing `##` sections in `.ultraplan/CHANGELOG.md`,
  **when** S03's section is added,
  **then** it follows the same shape as `## S11 — the renderer now consumes the translated
  schemes`: a heading, a short statement of the change, and a table or list carrying
  before/after/evidence.
- **Given** Phase 31's closeout,
  **when** the changelog is reconciled against the 89 tasks,
  **then** S03 is no longer an unexplained absence.

---

## Business requirements

| id | requirement | how it is tested |
|---|---|---|
| **BR-29.1** | Every property named in TR-03.3 has ground truth extracted from Stata and recorded in `test/fixtures/scheme_truth.json` for all 14 schemes. | `test_fixture_is_present_and_complete` extended to assert the new keys; new per-property presence test |
| **BR-29.2** | No value in the fixture is hand-written. Everything is produced by re-running `scripts/extract_scheme_truth.py`, and `_meta` records the run. | fixture-provenance test asserting `_meta.generated_by` and a regeneration check |
| **BR-29.3** | Every one of the 14 translated `.scheme` files declares the new directives, with colours as resolved `#rrggbb` and sizes as the Stata style name or literal the fixture records. | `test_scheme_property_fidelity` over the extended property set |
| **BR-29.4** | Faithful coverage after the extension is 122/122 per scheme — 1,708 properties across the 14, 0 disagreements. | `test_scheme_coverage` plus the fidelity test; the count is asserted, not narrated |
| **BR-29.5** | The extension cannot silently lower the bar: adding properties to the fixture without adding them to the `.scheme` files must fail a test that was **seen** to fail. | rule 8 failing-test-first step in the test plan; mutation table |
| **BR-29.6** | No rendered output changes in this phase. A figure built at HEAD and a figure built after this phase are byte-identical for every scheme. | render-stability test over all 14 schemes |
| **BR-29.7** | No `.scheme` file header claims a key is omitted that the file now declares. | header-consistency test over `schemes/*.scheme` |
| **BR-29.8** | `.ultraplan/CHANGELOG.md` records the marker-slot change with before value, after value, affected schemes and evidence. | changelog-structure test; manual review against the changelog preamble |
| **BR-29.9** | The changelog entry's scope claim is measured, not assumed. | the measurement is reproduced in the test plan and its output pasted into the entry |
| **BR-29.10** | Every claim this phase adds has a test that fails without it (project rule 8), and every new helper function has a unit test (project rule 4). | Definition of done |

---

## Technical requirements

### TR-29.1 — Extend the extractor's colour scalars

*File:* `scripts/extract_scheme_truth.py`, the `out = {...}` dict at `:495`, colour block at
`:517-539`, using the existing `color_of(out_key, keys)` helper defined at `:404`.

Add five entries alongside the eight that exist:

| fixture key | directive chain | note |
|---|---|---|
| `foreground_color` | `["foreground"]` | TR-03.3's *"foreground and axis-line colours"* — the axis-line half is already `axis_line_color` at `:539` |
| `text_color` | `["text"]` | the generic text colour; `color textbox`, `color text_option*` are **different keys** and are not this |
| `tick_label_color` | `["tick_label"]` | pairs with the existing `tick_label_size` at `:561` |
| `body_color` | `["body"]` | textboxstyle-body — the source of the **note** and **caption** colours |
| `subheading_color` | `["subheading"]` | textboxstyle-subheading — the source of the **subtitle** colour |

`color_of` already appends to `unresolvable` and writes `sources[out_key]` when a key is
absent, so no new failure handling is needed. `c.resolve()` already handles the
`background`/`foreground` self-references at `:269-271`:

```python
elif low in ("foreground", "fg"):
    return self.resolve(self.r.get("color", "foreground"), _depth + 1)
```

That path must not recurse when resolving `color foreground` itself — confirm with the
depth guard (`MAX_INCLUDE_DEPTH = 32`, `:66`) and cover it with a unit test (TR-29.9).

### TR-29.2 — Extend the extractor's `gsize` scalars

*File:* same, the `gsize` block at `:555-564`, using `scalar(...)` + `resolve_sized(r, "gsize", t)`.

| fixture key | directive | why |
|---|---|---|
| `body_size` | `gsize body` | `gsize note` is a **dead key at Stata scheme level** — no style file reads `scheme note`; the note textbox is textboxstyle-body |
| `subheading_size` | `gsize subheading` | the subtitle's real source; `SchemeParser` parses neither it nor `color subheading` |

`resolve_sized` (`:310-331`) already returns `{"name", "value", "sztype"}` and already
handles both spellings the schemes use — a literal (`economist` writes `gsize body 3.0`) and
a style name (`s2color` writes `gsize body medsmall`). Both forms must survive into the
fixture unchanged; the `name` field is what the fidelity harness compares
(`STYLE_NAME_SCALARS`, `:205-215`, compares the **declared style name**, not the resolved
value).

Do **not** remove `note_size`. It stays as the record of what the scheme declares; the
decision that the *note* should be drawn from `body_size` belongs to Phase 23/24, and
removing the key here would delete evidence they need.

### TR-29.3 — Regenerate, never hand-edit, the fixture

*File:* `test/fixtures/scheme_truth.json` (6,248 lines at HEAD).

```
$ python3 scripts/extract_scheme_truth.py --out test/fixtures/scheme_truth.json
```

`_meta.do_not_hand_edit` states the rule:

> This file is GENERATED ground truth extracted from Stata's own scheme and style files.
> Regenerate it by re-running scripts/extract_scheme_truth.py; do not hand-edit.

`_meta` at HEAD records `generated_utc 2026-09-19T17:42:59Z`,
`stata_version "StataNow 19.5 (MP), born 12 Aug 2026"`,
`scheme_dir /Applications/StataNow/ado/base/s`,
`style_dir /Applications/StataNow/ado/base/style`. The regeneration updates
`generated_utc`; the rest must be unchanged, and a diff that changes any **existing**
property value is a red flag that must be explained before the commit, not after.

**Expected diff shape:** 14 entries × 7 new keys = 98 new property values, 98 new `sources`
entries, one changed `generated_utc`, and **nothing else**. If the diff touches
`p_colors`, `p_symbols`, `graphsize_*` or any other existing key, stop: the Stata install has
changed underneath the fixture and that is a separate finding.

### TR-29.4 — Carry the directives into all 14 `.scheme` files

*Files:* `schemes/*.scheme` — `stcolor`, `stcolor_alt`, `stgcolor`, `stmono1`, `stmono2`,
`stsj`, `s2color`, `s2mono`, `s2gcolor`, `s1color`, `s1mono`, `s1rcolor`, `economist`, `sj`.

Directive spellings, matching the fixture's `sources` map exactly:

```
color foreground   #rrggbb
color text         #rrggbb
color tick_label   #rrggbb
color body         #rrggbb
color subheading   #rrggbb
gsize body         <style name or literal, as the fixture's .name field records it>
gsize subheading   <style name or literal, as the fixture's .name field records it>
```

Colours are written **resolved**, per the rule every file header already states:

> Every colour below is written as a RESOLVED #rrggbb value, not as a Stata colour name.
> dash's OptionTranslator._COLOR_MAP knows only 72 names, and SchemeParser._color() silently
> returns #000000 for a name it cannot resolve, so hex is the only self-contained
> representation.

Sizes are written as the **declared name** (`medsmall`, `medium`, `3.0`), because
`STYLE_NAME_SCALARS` compares names and because `SchemeParser._gsize` (`dash_render.py:1844-1853`)
resolves both forms itself.

### TR-29.5 — The admissibility rule for a directive the parser does not yet read

This is the question `schemes/economist.scheme:241-247` answered "no" to, and the precedent
that answers it "yes" is already in the tree, at `schemes/stgcolor.scheme:33-38`:

> Two directives are recorded that SchemeParser._init_properties() does not yet expose as
> attributes -- "yesno draw_major_hgrid" and "yesno draw_major_grid". They are not invented
> dash keys: they are the exact directive names the fixture's own sources map records, they
> parse into SchemeParser._props, and test_scheme_fidelity.py checks for them by those names.
> The attributes that consume them land in section 11.

and `schemes/stmono2.scheme:31-35`:

> They are inert until dash learns to consume them.

**The rule, stated once for this phase:** a directive is admissible in a translated
`.scheme` file if and only if (a) it is a real Stata directive name, (b) the fixture's
`sources` map for that scheme names it, and (c) `test_scheme_fidelity.py` checks it. All
seven new directives satisfy all three once TR-29.1, TR-29.2 and TR-29.6 land — which is the
reason the three must land in that order and in one commit.

### TR-29.6 — Extend the fidelity harness, and pick the right comparison group

*File:* `test/test_scheme_fidelity.py`.

This is the requirement with a trap in it, and it comes straight out of `evaluate_scheme`
(`:366-484`):

| group | line | compares | needs a `SchemeParser` attribute? |
|---|---|---|---|
| `COLOR_SCALARS` | `:168-177` | `attr(sp, prop)` — a **parser attribute** | **Yes.** `faithful = supplied and colors_close(expected, actual)`; with no attribute, `actual` is `MISSING` and `faithful` is `False` |
| `STYLE_NAME_SCALARS` | `:205-215` | `declared(sp, chain)` — the token in `SchemeParser._props` | **No** |
| `YESNO_SCALARS` | `:217-224` | `declared(sp, chain)` | **No** |

Consequences, which the implementer must not discover the hard way:

1. **`body_size` and `subheading_size` go straight into `STYLE_NAME_SCALARS`** and will pass
   with no change to `dash_render.py` at all — exactly like `draw_major_hgrid` does today.
2. **The five colours cannot go into `COLOR_SCALARS`** without `SchemeParser` growing
   `foreground_color`, `text_color`, `tick_label_color`, `body_color` and `subheading_color`
   attributes — and adding parser attributes is **Phase 23/24's** work, not this phase's
   (the work-item's `files` field is the extractor, the fixture and `schemes/*.scheme`; it
   does not name `dash_render.py`). Add them instead to a **new declared-token group**, e.g.
   `DECLARED_COLOR_SCALARS`, evaluated like `YESNO_SCALARS` but compared with
   `colors_close(expected, declared(sp, chain))` so the hex is compared as a colour within
   `COLOR_CHANNEL_TOL` (2 per channel, `:107`) rather than as a string.
3. When Phase 23/24 adds the parser attributes, those five entries move from
   `DECLARED_COLOR_SCALARS` to `COLOR_SCALARS` and the assertion strengthens from "the file
   declares the right colour" to "the parser exposes the right colour". Leave a comment
   saying so, in the style of the existing note at `:104-113`.

Update the unit-count comment at `:237`:

```python
#: Total property units per scheme: 6 lists x 15 + 25 scalars = 115.
```

to the new arithmetic: **6 lists × 15 + 32 scalars = 122**, and 14 × 122 = **1,708**.

### TR-29.7 — Do not touch `COVERAGE_THRESHOLD`, and know why it cannot be the gate

*File:* `test/test_scheme_fidelity.py:104`.

```python
COVERAGE_THRESHOLD = 0.90
```

The constant's own comment forbids lowering it (*"It must never be lowered to accommodate a
translation that fell short; that would turn the harness into a rubber stamp"*). It must also
not be **raised** as part of this phase without a measurement, per the same comment
(*"re-measure what they actually achieve and reset this constant to that floor —
deliberately, in a commit that says so"*).

The arithmetic that matters: at HEAD every scheme is 115/115 faithful. Add seven properties
to the fixture and not to the `.scheme` files, and each scheme is 115/122 = **0.9426**, which
is **above** 0.90. `test_scheme_coverage` would pass. The test that catches the omission is
`test_scheme_property_fidelity` (`:596-612`), which fails on *any* non-faithful property and
prints `NOT SUPPLIED by the .scheme file (Stata: ...)` for each. That is this phase's gate,
and the failing-test-first step in the test plan must be run against `test_scheme_property_fidelity`,
not against the coverage test.

### TR-29.8 — Rewrite the affected file headers

*Files:* `schemes/economist.scheme:236-247` (the `HONEST GAPS` block that lists
`color foreground`, `gsize subheading` and `gsize body` as dropped) and any other header
whose omission list names a key the file now carries.

The headers to model the rewrite on are `schemes/stgcolor.scheme:30-38` and
`schemes/stmono2.scheme:26-35`, quoted in TR-29.5. Each rewritten header states: the
directive is real Stata vocabulary, the fixture's `sources` map names it, it parses into
`SchemeParser._props`, `test_scheme_fidelity.py` checks it, and the attribute that consumes
it lands in a later section.

Separately, and cheaply, three headers carry stale statements about the marker symbols that
`dash_render.py:1199-1202` has since learned — they belong with item 2's record-keeping and
are listed under TR-29.13.

### TR-29.9 — Unit tests for the extractor's new paths (project rule 4)

*File:* `test/test_scheme_extractor.py` if one exists for these helpers, otherwise the nearest
existing home; the harness-side assertions go in `test/test_scheme_fidelity.py`.

Functions touched and therefore requiring a unit test:

| function | location | what the test pins |
|---|---|---|
| `color_of` | `scripts/extract_scheme_truth.py:404-413` | returns the resolved hex and writes `sources[out_key]`; appends to `unresolvable` and returns `None` when no key in the chain is set |
| `SchemeResolver.resolve` foreground branch | `:269-271` | `color foreground` resolves without infinite recursion; a chain longer than `MAX_INCLUDE_DEPTH` (32) is stopped |
| `resolve_sized` | `:310-331` | a literal (`3.0`) yields `{"name": "3.0", "value": 3.0, "sztype": "relative"}`; a style name (`medsmall`) indirects into `style/gsize-medsmall.style` and carries its `sztype` |
| `_as_number` | `:300-306` | `"3.0"` → `3.0` (float), `"3"` → `3` (int), a name → `None` — the discriminator between the two `resolve_sized` branches |

### TR-29.10 — Prove nothing rendered changed (BR-29.6)

*File:* `test/test_scheme.py` or `test/test_scheme_consumption.py`, whichever already owns
rendered-model assertions.

Because `SchemeParser._init_properties` (`dash_render.py:1953-2060`) reads none of the seven
new directives, adding them to the `.scheme` files must be inert. Prove it rather than assume
it: for each of the 14 schemes, render the same minimal figure before and after and assert
the outputs are identical. `_parse_file` populates `_props` with every directive it sees, so
the new keys *are* parsed — they simply have no consumer. An unexpected difference means a
directive name collided with one the parser already reads, which is the one way this phase
could break a picture.

### TR-29.11 — Header-consistency test (BR-29.7)

A test over `schemes/*.scheme` that, for each file, extracts the directive names mentioned in
its comment blocks as "dropped"/"omitted"/"not carried" and asserts none of them appears as a
live directive in the same file. This is what stops `economist.scheme`'s header from
contradicting its own body after TR-29.4, and it generalises: the next translation deepening
cannot leave a stale omission note behind.

### TR-29.12 — The S03 changelog entry

*File:* `.ultraplan/CHANGELOG.md` — 1,195 lines, twelve `##` sections at HEAD, none for S03.
Insert `## S03 — scheme translation` **before** `## S07` so the sections stay in section
order.

The entry must carry, in the table form the file already uses:

| slot | content |
|---|---|
| **what changed** | two marker slots in the monochrome schemes |
| **before** | `symbol p12 smdiamond` and `symbol p14 smtriangle` rendered as **circle** — `OptionTranslator.translate_msymbol` raised `ValueError` and `SchemeParser._symbol` swallowed it |
| **after** | `smdiamond` → Bokeh `diamond`, `smtriangle` → Bokeh `triangle` (`smdiamond_hollow` and `smtriangle_hollow` map alongside them) |
| **where** | `dash_render.py:1195-1202` |
| **affected schemes** | as measured — the files declaring `symbol p12 smdiamond` / `symbol p14 smtriangle`; see TR-29.14 |
| **evidence** | the grep output from TR-29.14, and the `REMAINING.md` refutation row |

Keep it short. `REMAINING.md` classes this as *cosmetic — record-keeping only*, and the
entry should be proportionate: a heading and a table, not an essay.

### TR-29.13 — Stale marker-symbol comments (record-keeping, same item)

Three translated schemes still tell a reader that `dash` cannot translate these symbols,
which `dash_render.py:1199-1202` has made false:

| file | line | text |
|---|---|---|
| `schemes/sj.scheme` | `:155-157` | *"OptionTranslator.translate_msymbol() does not know them today — SchemeParser._symbol() swallows the ValueError and substitutes a circle for p12 and p14"* |
| `schemes/stmono2.scheme` | `:150-152` | *"dash's translate_msymbol() does not yet know smdiamond or smtriangle and falls back to a circle for those two"* |
| `schemes/s1mono.scheme` | `:39-41` | *"…and the marker symbols smdiamond and smtriangle are not yet in OptionTranslator's tables"* |

Correcting these three comments is the same record-keeping act as the changelog entry and
belongs to item 2. Note that `s1mono.scheme:36-41` also names eight **line-pattern** names
(`vshortdash`, `tight_dot`, `dash_dot_dot`, `longdash_shortdash`, `dash_3dot`,
`longdash_dot_dot`, `shortdash_dot_dot`, `longdash_3dot`) in the same sentence; whether those
are still untranslatable is a **separate** question this phase does not answer. Edit only the
marker-symbol clause, and leave the line-pattern clause exactly as it stands unless a
measurement says otherwise. Splitting the sentence rather than deleting it is the honest edit.

### TR-29.14 — The measurement the changelog entry must be written from

`REMAINING.md`'s row names `s2color`. Before writing the entry, re-run the measurement and
paste its output into the commit message:

```
$ grep -n "symbol p12\|symbol p14" schemes/*.scheme
$ grep -n "smdiamond\|smtriangle" dash_render.py
```

At the time this document was written those returned `smdiamond`/`smtriangle` in
`s1mono`, `s2mono`, `sj`, `stmono1`, `stmono2` and `stsj`, and `circle` for `p12`/`p14` in
the eight colour schemes including `s2color`. The changelog entry states what the
measurement shows. If the measurement and the `REMAINING.md` row disagree about which scheme
is involved, the entry says what was measured and notes the discrepancy — it does not quietly
restate the audit, and it does not quietly contradict it. `REMAINING.md` is the source of
record and is not edited (project rule 2 applies to both halves of that sentence).

---

## Work items

Both items, numbered exactly as handed over.

### 1 — Extend the extractor and the fixture with the TR-03.3 properties the 14 translations omit

`[deli · n/a · medium]`

> Extend `scripts/extract_scheme_truth.py` and `test/fixtures/scheme_truth.json` with the
> TR-03.3 properties the 14 translations omit — at minimum `color foreground`, `color text`,
> `color tick_label`, `color body`/`color subheading`.

*Where:* `scripts/extract_scheme_truth.py` (colour block `:517-539`, `gsize` block
`:555-564`, `color_of` helper `:404`, `resolve_sized` `:310`),
`test/fixtures/scheme_truth.json` (all 14 entries plus `_meta`), `schemes/*.scheme` (all 14),
and the harness `test/test_scheme_fidelity.py` (`COLOR_SCALARS` `:168`, `STYLE_NAME_SCALARS`
`:205`, unit-count comment `:237`).

*Origin:* S03, main body of `REMAINING.md`.

*Evidence:* The 03-03 refutation row — *"14 translations independently re-derived exact
(1,610 properties, 0 disagreements); `color foreground`/`text`/`tick_label` still absent from
the fixture"* — and the status-table row for section 03, *"3 done, 2 partial ② | `color
foreground`; all 14 inert once installed ①"*. TR-03.3 names *"foreground and axis-line
colours"* and *"title, subtitle, axis-title, tick-label, note and caption text sizes and
colours"*; the axis-line, title, axis-title, tick-label and note **sizes** landed, the
foreground colour, the text/tick-label/body colours and the subtitle size and colour did not.
Appendix C ties three downstream items to exactly this gap: the subtitle clause *"needs
S03-shaped work first (add the keys to schemes/\*.scheme, add `subheading_font_size` /
`subheading_color` to _init_properties) before any renderer edit can be correct rather than
invented"*; `gsize note` is *"a DEAD key at Stata scheme level"* whose real source is
`gsize body`/`color body`, and wiring the note from it *"would draw economist's note at 14pt
where Stata draws ~8.6pt"*; and the caption is *"untouched: both renderers draw it at a
hardcoded 12.0px / #555555 with no scheme key parsed"*.
Confirmed against the tree at HEAD: the fixture's `stcolor` entry has 39 keys and none of the
seven; `grep -l "color text" schemes/*.scheme` returns 0 files; `SchemeParser._init_properties`
(`dash_render.py:1953-2060`) declares no attribute for any of them. Confirmed against Stata's
own scheme tree: all seven are declared in `scheme-s2color.scheme`, which every one of the 14
`#include` chains terminates at, so all 14 can supply a real value and none needs an honest
gap.
*Requirements:* TR-29.1, TR-29.2, TR-29.3, TR-29.4, TR-29.5, TR-29.6, TR-29.7, TR-29.8,
TR-29.9, TR-29.10, TR-29.11. *Business:* BR-29.1 … BR-29.7, BR-29.10.

### 2 — Record the 03-04 marker-slot change

`[deli · n/a · small]`

> Record the 03-04 marker-slot change (two slots moved toward Stata — `s2color` really does
> declare `smdiamond`/`smtriangle`). Cosmetic, record-keeping only.

*Where:* `.ultraplan/CHANGELOG.md` (new `## S03` section, inserted before `## S07` at `:11`);
evidence at `dash_render.py:1195-1202`; the stale headers at `schemes/sj.scheme:155-157`,
`schemes/stmono2.scheme:150-152`, `schemes/s1mono.scheme:39-41`.

*Origin:* S03, main body of `REMAINING.md`.

*Evidence:* The 03-04 refutation row — *"cosmetic — two marker slots moved toward Stata;
record-keeping only"* — the single **cosmetic** entry among the seventeen overturned DONE
claims (*"10 small, 5 medium, 1 large, 1 cosmetic"*). The changelog's own contract requires
it: *"Every entry here changes a number or a picture a user has already seen. Each one
records the value before, the value after, and the evidence."* Confirmed at HEAD:
`.ultraplan/CHANGELOG.md` has twelve `##` sections (S07, S08, S09, S10, S11, certification
suite, colour fidelity, `tabs()`/`by()`, the audit, S14, S15, S16) and **no S03 section**;
`grep -n "03-0" .ultraplan/CHANGELOG.md` returns nothing. This is the same class of gap the
status table flags for S06 (*"no S06 entry in CHANGELOG ②"*). The change itself is live at
`dash_render.py:1199-1202`, with the in-code rationale at `:1195-1198`: *"The mono schemes
(s1mono, s2mono, sj, stmono1/2, stsj) cycle through smdiamond and smtriangle, which
previously raised out of SchemeParser and made a faithful translation of those schemes
unparseable."*
*Requirements:* TR-29.12, TR-29.13, TR-29.14. *Business:* BR-29.8, BR-29.9, BR-29.10.

---

## Test plan

Project rule 8: the regression test comes first and must be **seen** to fail before the
change. Project rule 4: every function gets a unit test. Project rule 2 has particular force
in this phase — both items are about the record being honest, so a test that has not been
watched to fail has not been shown to work.

Run the Stata side with `arch -arm64` from `test/`, and treat a skip as a skip, never as a
pass.

### E29.1 — Ground truth for the five omitted properties

**Write this first (must fail at HEAD).**

`test/test_scheme_fidelity.py::test_fixture_declares_the_TR_03_3_properties` — parametrised
over the 14 scheme names, asserting each fixture entry carries `foreground_color`,
`text_color`, `tick_label_color`, `body_color`, `subheading_color`, `body_size` and
`subheading_size`, and that each has a `sources` entry. At HEAD this fails **14 times**,
because the `stcolor` entry has 39 keys and none of the seven. Run it and read the failure
before touching the extractor.

**Second failing test, run at the intermediate state.** After TR-29.1–TR-29.3 (extractor and
fixture done, `.scheme` files not yet), run `test_scheme_property_fidelity`. It must fail for
all 14 with `NOT SUPPLIED by the .scheme file (Stata: ...)` lines. In the **same** run,
confirm `test_scheme_coverage` **passes** at 115/122 = 0.943 — that is TR-29.7's point, and
observing it is what stops a future maintainer from believing the coverage gate protects
these properties. Record both outcomes in the commit message.

**Unit tests (rule 4).**

| target | file | test |
|---|---|---|
| `color_of` | extractor tests | resolved hex returned and `sources[out_key]` written; absent chain → `None` plus an `unresolvable` entry naming every key tried |
| `SchemeResolver.resolve`, foreground branch (`:269-271`) | extractor tests | `color foreground` resolves without recursion; a chain past `MAX_INCLUDE_DEPTH` (32) terminates |
| `resolve_sized` (`:310-331`) | extractor tests | literal `3.0` → `{"name":"3.0","value":3.0,"sztype":"relative"}`; name `medsmall` → the style file's `val` and `sztype` |
| `_as_number` (`:300-306`) | extractor tests | `"3"`→int, `"3.0"`→float, `"medsmall"`→`None` |
| fixture provenance | `test_scheme_fidelity.py` | `_meta.generated_by == "scripts/extract_scheme_truth.py"`; `_meta.do_not_hand_edit` present; `generated_utc` parses as a UTC timestamp |
| fixture completeness | `test_scheme_fidelity.py::test_fixture_is_present_and_complete` (`:512`) | extended: exactly the 14 schemes, **and** every one carries the full property set |
| sanity anchors | `test_scheme_fidelity.py::test_fixture_sanity_anchors` (`:524`) | add two hand-verified anchors for the new keys, e.g. `s1rcolor.text_color == "#ffffff"` and `s2color.body_size["name"] == "medsmall"`, so a bad regeneration cannot pass silently — matching the existing comment, *"These are the only hardcoded expected values in this file"* |
| the new harness group | `test_scheme_fidelity.py` | `DECLARED_COLOR_SCALARS` entries are compared with `colors_close` (tolerance 2 per channel), not string equality, so `#FFFFFF` and `#ffffff` agree |
| unit count | `test_scheme_fidelity.py` | assert `len(evaluate_scheme("s2color")) == 122`, so the `:237` comment can never drift from the code again |
| header consistency (TR-29.11) | new test over `schemes/*.scheme` | no directive named as dropped in a comment appears live in the same file |
| render stability (TR-29.10) | `test_scheme.py` / `test_scheme_consumption.py` | for each of the 14, the rendered output is identical before and after the `.scheme` edits |

**Integration / cscript coverage.**

- `pytest test/test_scheme_fidelity.py` — the whole file, all 14 parametrisations of every
  arm, green at 122/122 per scheme.
- `pytest test/test_scheme.py test/test_scheme_coercion.py test/test_scheme_consumption.py
  test/test_scheme_grids.py test/test_scheme_grid_measured.py test/test_scheme_integration.py
  test/test_server_scheme.py test/test_immediate_scheme.py` — the scheme suite, unchanged and
  green; any change here means TR-29.10 was violated.
- `test/test_conformance.cscript` and `test/test_examples_run.cscript` — green and unchanged.
  No `dash` command behaves differently in this phase, and these two are what would notice if
  one did.
- Full pytest (baseline at HEAD: **3,498 passed / 37 skipped**) and the full certification
  suite (**25/25 cscripts**) before any commit, per project rule 5.

**Mutation — how each test is proved non-vacuous.**

| break this | this must die |
|---|---|
| Remove `"foreground_color"` from the extractor's `out` dict and regenerate | `test_fixture_declares_the_TR_03_3_properties`; `test_scheme_property_fidelity` for all 14 |
| Delete `color body #rrggbb` from `schemes/s2color.scheme` only | `test_scheme_property_fidelity[s2color]` with a `NOT SUPPLIED` line; the other 13 survive, proving the parametrisation is per-scheme |
| Change `schemes/s1rcolor.scheme`'s `color text` from `#ffffff` to `#fffffe` | nothing — inside `COLOR_CHANNEL_TOL` (2). Then change it to `#000000`: the fidelity test must die. This is the proof the tolerance is a tolerance and not a hole |
| Write `gsize body medium` where the fixture says `medsmall` | `test_scheme_property_fidelity`, on the **declared name** comparison — proving `STYLE_NAME_SCALARS` compares names, not resolved points |
| Hand-edit one value in `scheme_truth.json` instead of regenerating | the provenance/anchor tests, via the stale `generated_utc` and the anchor mismatch |
| Lower `COVERAGE_THRESHOLD` to 0.85 | no test dies — which is precisely why the threshold is **not** this phase's gate (TR-29.7). Restore it and confirm the fidelity test is what holds the line |
| Add all seven keys to the fixture but to none of the `.scheme` files | `test_scheme_property_fidelity` × 14 must die while `test_scheme_coverage` survives at 0.943. Both halves of this must be observed (BR-29.5) |
| Leave `economist.scheme`'s HONEST GAPS list naming `gsize body` after adding the directive | the header-consistency test (TR-29.11) |
| Rename a new directive to something Stata does not use, e.g. `color fg` | `test_scheme_property_fidelity`, because `declared()` walks the fixture's own `sources` chain and will not find it |
| Add an attribute assignment for `body_color` to `SchemeParser._init_properties` | the render-stability test must be re-examined: this phase asserts *no* render change, so an early parser edit must be caught here rather than merged silently into Phase 23/24's territory |

### E29.2 — Record the marker-slot change

**Write this first (must fail at HEAD).**

`test/test_changelog_sections.py::test_changelog_records_the_marker_slot_change` — parse
`.ultraplan/CHANGELOG.md`, assert an `## S03` section exists and that its body mentions
`smdiamond`, `smtriangle`, `circle` (the before value) and `dash_render.py`. At HEAD this
fails on the first assertion: there are twelve `##` sections and none is S03.

A test that reads a documentation file is only worth writing if it asserts something
falsifiable. This one does: the *before* value is the part a later reader cannot reconstruct,
and it is the part most likely to be omitted.

**Unit tests (rule 4).**

| target | test |
|---|---|
| section parser helper | given a Markdown file, returns its `##` headings in order — asserted against the twelve known ones at HEAD, so a rename is caught |
| section ordering | S03 precedes S07; the section list is sorted where the section numbers are comparable |
| `OptionTranslator.translate_msymbol` | `smdiamond` → `diamond`, `smtriangle` → `triangle`, `smdiamond_hollow` → `diamond`, `smtriangle_hollow` → `triangle` — a direct unit test of `dash_render.py:1199-1202`, which rule 4 requires and which pins the *after* value the changelog states. If one already exists in `test/test_scheme_coercion.py`, extend rather than duplicate |
| `SchemeParser._symbol` | for each of the six mono schemes, `p_symbols[11] == "diamond"` and `p_symbols[13] == "triangle"` — the assertion that would have caught the original circle-substitution bug |
| header consistency (TR-29.13) | no `.scheme` comment asserts `translate_msymbol` cannot handle a symbol the file declares **and** `_SYMBOL_MAP` contains |

**Integration coverage.**

`test/test_scheme_fidelity.py::test_translator_can_express_scheme_symbols_and_patterns`
(`:792`) already covers the functional half for all 14 schemes — it calls
`OptionTranslator.translate_msymbol` on every distinct symbol in each scheme's truth entry
and fails if any raises. It passes at HEAD; this phase does not change it, but the changelog
entry should cite it as the standing guard.

**Mutation.**

| break this | this must die |
|---|---|
| Delete the `## S03` heading, keep the body | the section test |
| Write the entry without the before value ("now draws a diamond") | the `circle` assertion |
| Remove `"smdiamond": "diamond"` from `_SYMBOL_MAP` (`dash_render.py:1199`) | the `translate_msymbol` unit test; `test_translator_can_express_scheme_symbols_and_patterns` for the six mono schemes; the `_symbol` per-scheme test |
| Restore the stale sentence in `schemes/sj.scheme:155-157` | the header-consistency test |
| Assert only that the file "mentions S03" | must be shown to pass against an S03 section containing the word "TODO" — which is why the content assertions are named individually |

---

## Definition of done

- [ ] `test_fixture_declares_the_TR_03_3_properties` was written first, run at HEAD, and its
      14 failures read before any extractor edit (rule 8).
- [ ] `scripts/extract_scheme_truth.py` records `foreground_color`, `text_color`,
      `tick_label_color`, `body_color` and `subheading_color` via `color_of`, and `body_size`
      and `subheading_size` via `scalar(... resolve_sized ...)` (TR-29.1, TR-29.2).
- [ ] `test/fixtures/scheme_truth.json` was **regenerated** by running the script, not
      hand-edited; `_meta.generated_utc` is new and `_meta.stata_version`, `scheme_dir` and
      `style_dir` are unchanged (TR-29.3).
- [ ] The regeneration diff adds 98 property values and 98 `sources` entries and changes no
      existing value; any other change was explained before the commit (TR-29.3).
- [ ] Every one of the 14 entries has an **empty** `unresolvable` list after the extension
      (BR-29.1).
- [ ] All 14 `schemes/*.scheme` files carry the seven directives — colours as resolved
      `#rrggbb`, sizes as the declared name the fixture records (TR-29.4).
- [ ] `s1rcolor` carries `#ffffff` for all five new colours, matching Stata's `white`
      (US-29.1.3).
- [ ] `test/test_scheme_fidelity.py` gates the new properties: the two `gsize` keys in
      `STYLE_NAME_SCALARS`, the five colours in a declared-token group compared with
      `colors_close`, with a comment saying they move to `COLOR_SCALARS` when Phase 23/24 adds
      the parser attributes (TR-29.6).
- [ ] The unit-count comment at `test_scheme_fidelity.py:237` reads **122**, and a test
      asserts `len(evaluate_scheme(...)) == 122` so it cannot drift again (TR-29.6).
- [ ] Faithful coverage is 122/122 for all 14 — **1,708 properties, 0 disagreements** — and
      the number is recorded in the commit message as the successor to 1,610 (BR-29.4).
- [ ] The intermediate state was observed: fidelity red for 14, coverage green at 0.943
      (BR-29.5, TR-29.7).
- [ ] `COVERAGE_THRESHOLD` is **unchanged at 0.90** (TR-29.7).
- [ ] `SchemeParser._init_properties` (`dash_render.py:1953-2060`) is **unmodified** — no
      parser attribute was added in this phase; that work is Phase 23/24's.
- [ ] The render-stability check passed for all 14 schemes: output before and after is
      identical (BR-29.6, TR-29.10).
- [ ] `schemes/economist.scheme`'s HONEST GAPS block no longer lists a key the file now
      declares, and the rewrite follows the `stgcolor`/`stmono2` precedent (TR-29.8, BR-29.7).
- [ ] The header-consistency test exists and was mutated to prove it bites (TR-29.11).
- [ ] `.ultraplan/CHANGELOG.md` has an `## S03` section, placed before `## S07`, recording
      before (circle), after (diamond / triangle), the affected schemes, and
      `dash_render.py:1195-1202` as evidence (TR-29.12, BR-29.8).
- [ ] The affected-schemes claim in that entry was **measured** with the greps in TR-29.14 and
      the output pasted into the commit message; any discrepancy with `REMAINING.md`'s row is
      stated in the entry rather than silently resolved (BR-29.9).
- [ ] The three stale marker-symbol comments (`sj.scheme:155-157`, `stmono2.scheme:150-152`,
      `s1mono.scheme:39-41`) are corrected, and `s1mono`'s line-pattern clause is left intact
      (TR-29.13).
- [ ] Unit tests exist for `color_of`, the foreground resolve branch, `resolve_sized`,
      `_as_number`, `translate_msymbol` on the four `sm*` names, and the changelog section
      parser (rule 4).
- [ ] Every mutation in the test plan was applied, the named test observed to fail, and the
      mutation reverted.
- [ ] `REMAINING.md` is untouched.
- [ ] Full pytest and the full certification suite green against the S01 baseline before the
      commit (rule 5); the cert suite was run with `arch -arm64` from `test/` and any skip is
      reported as a skip.
- [ ] Committed on `feature/batch4-interactive-layer`, with the merge command reported rather
      than run (rule 6), and no Claude/Anthropic reference in the message (rule 7).

---

## Risks and sequencing notes

**Run this phase early, despite its low rank.** It has no dependencies, touches no renderer,
and conflicts with no other phase's files — but three items in Phases 23–25 are blocked on its
output. `REMAINING.md` states the dependency directly for the subtitle: the work *"needs
S03-shaped work first … before any renderer edit can be correct rather than invented."* Running
Phase 23 or 24 first means either waiting mid-phase or inventing the values, and inventing
values is the specific failure S03 exists to correct (*"`dash` invented `color p1line`,
`symbol p1` and `linepattern p1line` where Stata writes `markerstyle p1 p1` and
`linestyle p1 p1`"*).

**Risk: the Stata install moves under the fixture.** The extractor is pinned to
`/Applications/StataNow/ado/base` (`DEFAULT_STATA_BASE`, `:61`) and `_meta` records
`StataNow 19.5 (MP), born 12 Aug 2026`. Regenerating on a different install silently
re-derives *every* property, not just the seven new ones. Mitigation: TR-29.3's expected diff
shape. If the diff is larger than 98 new values plus a timestamp, stop and find out why before
committing. The extractor documents an `--stata-base` override and a byte-comparison against
the older `/Applications/Stata/ado/base` tree; use it rather than editing the constant.

**Risk: adding directives the parser does not read looks like the mistake S03 was correcting.**
It is the opposite, and the difference is testable: the invented keys had no Stata source,
while these seven are directives Stata's own `scheme-s2color.scheme` declares and the
fixture's `sources` map will name. TR-29.5 states the admissibility rule, and
`stgcolor.scheme:33-38` is the precedent already in the tree for exactly this situation with
`yesno draw_major_hgrid`. Write the rule into the file headers so the next reviewer does not
have to rediscover it.

**Risk: the five colours quietly pull `dash_render.py` into scope.** `COLOR_SCALARS`
(`test_scheme_fidelity.py:168`) compares parser **attributes**, so the obvious way to wire the
new colours into the harness requires a parser change this phase does not own. TR-29.6 routes
around it with a declared-token group. If that routing is skipped, the phase grows a
`dash_render.py` edit, collides with Phase 23/24, and breaks the render-stability guarantee
(BR-29.6). This is the single most likely way to get this phase wrong.

**Risk: `gsize note` gets "fixed" here.** It is tempting, having established that `gsize note`
is a dead key at Stata scheme level, to rewire `SchemeParser.note_font_size`
(`dash_render.py:2047`) in the same commit. Do not. That is a rendered-output change — the
economist note moves from 14pt to ~8.6pt — and it belongs to Phase 23/24 with its own
failing-test-first cycle and its own changelog entry. This phase supplies `body_size` and
stops.

**Risk: a documentation test that asserts nothing.** The changelog test in E29.2 reads a
Markdown file, which is the classic shape of a test that goes green while certifying nothing —
the exact failure `REMAINING.md` documents for the certification suite (*"it was reporting
success while testing almost nothing"*). The mutation table is what earns the test: it must be
shown to fail against an S03 section containing only "TODO".

**Risk: the `REMAINING.md` scope wording.** The 03-04 row names `s2color`, while the
`smdiamond`/`smtriangle` directives are in the six mono translations and `dash_render.py`'s own
comment names *"s1mono, s2mono, sj, stmono1/2, stsj"*. TR-29.14 resolves this by measurement
rather than by preference. Whatever the greps say is what the changelog says; `REMAINING.md` is
not edited and not contradicted by implication.

**Sequencing out.** Phase 23 (text sizing and typography), Phase 24 (subtitle, caption and the
size stubs) and Phase 25 (legend, colour mapping and CSS delivery) all consume this phase's
fixture keys. Phase 31 (release gates and closeout) reconciles the changelog and will want the
S03 section present. Nothing consumes this phase's output before those, so it can sit anywhere
in Wave 1 — and because it touches no file any other phase touches, it can run fully in
parallel.

**Effort honesty.** Item 2 is small: one changelog section, three comment corrections, one
test. Item 1 is medium, and the medium is spread thin rather than deep — two helper calls in
the extractor, a regeneration, seven directives × 14 files, and a harness group. The largest
single cost is the 14-file edit, and it is mechanical because every value comes from the
regenerated fixture. There is no algorithm to get wrong here; there is only the discipline of
generating before writing.
