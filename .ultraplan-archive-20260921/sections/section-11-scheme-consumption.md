# Section 11: Scheme consumption and fidelity

## Overview
S03 authored fourteen faithful translations. This section makes the renderer use them.

Today it barely does. `SchemeParser` requests **108 keys** (`:918-974`) and exactly **three**
consumers exist in 10,455 lines: `default_color()` (38 glyph call sites),
`apply_to_figure()` (one call site, `:5661`) and `css_block()` (`:6595`, `:7476`).
**63 of the 108 parsed keys are discarded.** `default_symbol()` (`:996`) and
`default_line_pattern()` (`:1000`) have **zero call sites** — they exist only to be
unit-tested.

The consequence is that only *hue* varies across series. Marker symbol, marker size, line
pattern and line width are identical for every plot, because the keys carrying them are
parsed and dropped.

And `css_block()`, one of the three consumers, is inert: it emits `.dash-title`,
`.dash-subtitle` and `.kpi-card` while the HTML emits `db-title`, `db-subtitle` and
inline-styled KPI divs (`:6551`, `:6555`, `:6292-6300`). **All three selectors match
nothing.** Four scheme values become live for the cost of a class-name change — the
highest-leverage single fix in the plan.

## User story
> As a Stata user with `set scheme economist`, my dashboard is an Economist dashboard —
> colours, symbols, line weights, fonts and backgrounds — without my passing any option.

## Business requirements
- BR-11.1 The active Stata scheme (`c(scheme)`) is the default.
- BR-11.2 `scheme()` and `theme()` work on `dash build` and at graph level.
- BR-11.3 `scheme()` is **restricted to the translated set**; an unknown name is reported with
  the supported list, never silently substituted.
- BR-11.4 Every property a translated scheme carries is visible in the output.

## Technical requirements
- TR-11.1 `dash.ado` reads `c(scheme)` and serializes it as the default, overridable by
  `theme()`/`scheme()`.
- TR-11.2 `scheme()` becomes a real `dash build` option (`:1174-1185` omits it, while
  `dash.sthlp:79` documents it → `r(198)`).
- TR-11.3 Graph-level `scheme()` is honoured. It is parsed (`:239`, `:319`),
  abbreviation-expanded and escaped into `graph_options` (`:514`) — and never read, because
  `:4990-5000` resolves only from `build_options`.
- TR-11.4 An unresolvable *requested* scheme is an **error** naming the supported set. A
  missing scheme *directory* remains the degradation S02 built. Do not collapse the two.
- TR-11.5 Consume the 63 discarded keys.
- TR-11.6 Fix the dead CSS selectors.
- TR-11.7 Unit-test `SchemeParser`'s coercion layer — 8 of its 15 functions are untested
  (`_color`, `_gsize`, `_intensity`, `_symbol`, `_lpattern`, `_lwidth`, `_parse_file`,
  `_init_properties`) and that is exactly where the silent-black failure lives.

## Risk: [red] — this changes the appearance of every chart the package has ever produced. It is also where a wrong colour is hardest to notice.

## Dependencies
- Depends on: S03 and S10
- Blocks: S12
- Parallel batch: 4

## TDD test stubs
- Test: with no scheme option, the rendered colours are those of `c(scheme)`.
- Test: `dash build, scheme(economist)` works (today `r(198)`).
- Test: graph-level `scheme(economist)` affects only that graph.
- Test: `theme(dark)` — documented at `dash.sthlp:248`, absent from the map — reports an error
  naming the supported set rather than silently falling back.
- Test: an unknown scheme name errors with the supported list.
- Test: three overlaid scatters get three distinct symbols, line patterns and widths, not just
  three colours.
- Test: `fill_alpha`, `bar_alpha` and `area_alpha` from the scheme reach the glyphs.
- Test: title, subtitle, axis-title, tick-label, note and caption sizes come from the scheme.
- Test: the emitted CSS selectors match the emitted class names.
- Test: `stcolor` renders real colours, not `#000000`.
- Test: every coercion function in `SchemeParser` has a direct unit test, including the
  failure path that currently returns `#000000` silently.
- Test: `test_scheme.py:404-415` — which feeds a real Stata scheme and asserts only
  `p_colors[0]`, concealing the gap — is strengthened, and `test_scheme.py:194-203`, which
  green-lights dead API, is removed or repointed.

## Tasks

<task type="auto" id="11-01">
  <name>Test the coercion layer and its silent-failure path</name>
  <files>test/test_scheme_coercion.py</files>
  <action>
    Write direct unit tests for the 8 untested functions. The important one is `_color()`
    (`:863`): given an unresolvable colour token it swallows the failure and returns its
    `"#000000"` default (`:934`). That single behaviour turned the whole `stcolor` scheme
    black.

    Assert that an unresolvable token **warns** and names the token and the scheme. Silence
    here is what made the failure invisible.

    Repair the two landmine tests: `test_scheme.py:404-415` asserts only `p_colors[0]`, which
    is the one thing that works; `test_scheme.py:194-203` green-lights API with no call sites.

    Run. The warning tests fail; the strengthened fidelity test fails on unconsumed
    properties.
  </action>
  <verify>Coercion failures currently return a default silently, as the tests now demonstrate.</verify>
  <done>The coercion layer is tested, and its silent-failure path is pinned by a test.</done>
</task>

<task type="auto" id="11-02">
  <name>Make c(scheme) the default and scheme() a real option everywhere</name>
  <files>dash.ado, dash_render.py</files>
  <action>
    `dash.ado` reads `c(scheme)` and serializes it. Precedence: graph-level `scheme()`, then
    build-level `scheme()`/`theme()`, then `c(scheme)`, then the package default.

    Add `scheme()` to `dash build`'s syntax (`:1174-1185`) — documented at `dash.sthlp:79`
    and currently `r(198)`.

    Fix the three hardcoded master-JSON defaults: `"theme":"default"` at `:974` (so immediate
    render can never use a non-default scheme), `:1282`, and `:1603`.

    In `dash_render.py:4990-5005`, resolve graph-level scheme per figure rather than only
    `build_options`. This is a structural change: today one `SchemeParser` is built in
    `__init__` and handed to one `GlyphMapper`. Per-graph schemes need resolution per figure.
    Cache by name so a 20-graph dashboard parses each scheme once.

    Implement TR-11.4's distinction: a **requested** scheme that will not resolve is an error
    listing the translated set; a missing scheme **directory** stays S02's warned degradation.
    `theme(dark)` becomes an error naming the real values, not a silent `s2color`.
  </action>
  <verify>`c(scheme)` drives the default; both scheme levels work; unknown names error with the supported list.</verify>
  <done>Scheme selection honours the user's Stata session and every documented path works.</done>
</task>

<task type="auto" id="11-03">
  <name>Consume the per-series style cycle</name>
  <files>dash_render.py</files>
  <action>
    Wire the four per-series cycles so the Nth overlaid plot takes the Nth style, the way
    `twoway` resolves `p#`:

    - `p_symbols` (`:951`) → the marker, replacing the hardcoded `marker = "circle"`
      (`:1936`). `default_symbol()` (`:996`) exists with zero call sites — use it.
    - `p_line_patterns` (`:956`) → the dash pattern, replacing `line_dash="solid"` (`:2330`).
      `default_line_pattern()` (`:1000`) exists with zero call sites — use it.
    - `default_line_width` (`:961`) → line width, replacing the literals 1.5 and 2.0 across
      nine sites.
    - marker size from the scheme's `gsize`, replacing `size = 8` (`:1971`). Note that
      `:3586` in the same file already uses `medium` — the file disagrees with itself.

    `p_mark_colors` (`:945`) is parsed and never read at all; wire it or remove it, and say
    which in the commit message.

    An explicit user option must always win over the scheme. Add a test for that precedence
    on each of the four.
  </action>
  <verify>Three overlaid scatters differ in symbol, pattern, width and size as well as colour; explicit options override.</verify>
  <done>The per-series style cycle is real, not colour-only.</done>
</task>

<task type="auto" id="11-04">
  <name>Consume the remaining discarded keys and fix the dead CSS</name>
  <files>dash_render.py</files>
  <action>
    Alphas: `fill_alpha`, `bar_alpha`, `area_alpha` (all 0.8, all unread) replace the literals
    `alpha=0.7` (`:1974`), `fill_alpha=0.8` (`:2199`) and `fill_alpha=0.5` (`:2106`).

    Text: `text_font_size` replaces the mlabel `"10px"` (`:1860`); `title_color` and
    `heading_font_size` reach the figure title (`:5643-5644`), which today gets no colour,
    size or alignment; `note_font_size` reaches the note; the subtitle uses a real scheme
    value. S09 applied the explicit sub-options — this supplies their defaults.

    Legend: `legend_bg_color` and `legend_border_color` (`:923-924`) currently have **zero
    consumers**, because with no `legend()` option nothing is styled at all (`:6004-6005`).
    Style the legend from the scheme unconditionally.

    Colour mapping: the discrete `colorvar` palette (`Category10_10`, `:1727-1730`) and the
    continuous one (`Viridis256`, `:1780-1781`) both ignore the scheme; use `scheme.p_colors`
    for discrete. Colorbar placement is hardcoded `"right"` (`:1769`, `:1797`) while
    `legend(position() ring())` is parsed and ignored — honour it.

    **The dead CSS.** `css_block()` (`:1026-1035`) emits `.dash-title`, `.dash-subtitle` and
    `.kpi-card`; the HTML emits `db-title`, `db-subtitle` and inline-styled KPI divs
    (`:6551`, `:6555`, `:6292-6300`). Align them so the block applies, and add a test
    asserting every selector `css_block()` emits matches a class the HTML actually uses.
    That test is what stops this recurring.

    `minor_grid_color` is also parsed and unread; wire it.
  </action>
  <verify>Alphas, text sizes, legend styling and colour palettes all track the scheme; the CSS selector test passes.</verify>
  <done>No parsed scheme key is discarded, and the check is mechanical.</done>
</task>

<task type="auto" id="11-05">
  <name>Restrict scheme() to the translated set and document it</name>
  <files>dash.ado, dash_render.py, dash.sthlp</files>
  <action>
    Per the decision taken, `scheme()` accepts only the fourteen translated names. Validate in
    **Stata**, where the user sees the error, listing the supported set.

    This retires the arbitrary-`.scheme`-file path, which also removes the path-traversal
    surface that commits `fae476d` and its predecessor were hardening — note that in the
    commit message. Keep the `_resolve_path` guards for the bundled set; do not delete
    defence in depth just because the input is now constrained.

    Correct the help: `dash.sthlp:248` lists `default, clean, dark` — `dark` does not exist;
    `:708-713` says a custom scheme can be loaded by base name from the CWD — it cannot, and
    now will not. Replace both with the supported list and a note that a user wanting another
    scheme should request a translation.

    Update `dash.sthlp:161-162`'s claim that `scheme()` is "fully supported" so it is finally
    accurate.
  </action>
  <verify>Only translated names are accepted; the error names the set; the help matches the code.</verify>
  <done>The scheme surface is constrained, honest and documented.</done>
</task>

<task type="auto" id="11-06">
  <name>Visual fidelity check against Stata, then commit</name>
  <files>test/, .ultraplan/CHANGELOG.md</files>
  <action>
    For at least four schemes — `stcolor`, `s2color`, `economist`, `s1mono` — produce the same
    graph in Stata (`twoway`, exported to PNG) and in `dash`, and compare them side by side by
    looking at them.

    This is the only check that can substantiate BR-11.4 and the decision's requirement that
    translations "faithfully reproduce the aesthetics". A structural assertion that a hex
    value reached a glyph does not.

    Record the comparisons. Where a translation is visibly off, fix the `.scheme` file — that
    is S03 work landing late, which is expected and fine.

    This section changes the appearance of every chart the package produces. Record that in
    the CHANGELOG as a single deliberate change with the reasoning, and list the specific
    differences a user will notice: non-circle markers on later series, varying line patterns
    and widths, scheme-driven text sizes, and different default colours for anyone whose
    `c(scheme)` is not `s2color` — which, since Stata 18, is almost everyone.

    Run all suites against the S01 baseline. Commit as single-issue commits.
  </action>
  <verify>Side-by-side comparisons for four schemes look like their Stata originals; suites green.</verify>
  <done>Schemes are consumed, restricted, documented, and verified by eye against Stata.</done>
</task>
