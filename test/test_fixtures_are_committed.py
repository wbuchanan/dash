"""A fixture the suite reads but git does not hold makes the suite lie.

`.git/info/exclude` in this working copy lists `*.json` under "Common ASCII
dataset extensions" -- a sensible local rule for a Stata repository, and the
reason seven of the nine truth fixtures were added with `git add -f`. The two
most recent were added without it, so they exist on this machine and in no
clone.

Measured, clean `git archive HEAD` export against the working tree:

    clean checkout   2934 passed, 116 skipped
    working tree     3056 passed,  33 skipped

174 tests do not run on a clone, and the suite still exits 0, because each of
them skips politely when its fixture is missing. Those 174 are the
Stata-ground-truth checks -- whether dash's KPI statistics and its colour
table match Stata's -- which is the claim the package is built on.

This test asks git, not the filesystem, so a fixture that exists only here
fails.

A fixture git holds and nothing reads is the other way to lie: a file that
looks like ground truth and checks nothing (GAPS.md L8, ROADMAP TR-25.4).
Measured 24sep2026: the nine files of test/fixtures/scheme_visual/ were named
by no test file or certification script, while the message below called
every fixture "read by the test suite"; and fifteen .do files in test/,
March 2026 diagnostics with no assertion in them, were named by nothing at
all.  Two guards keep both from coming back.  They read the test files and
certification scripts in test/ (every .py, .cscript and .do there) rather
than asking git, so they run on any copy:

* every file under test/fixtures is named by one of them -- by its file
  name, or, for a file a test loads from a subdirectory under a computed
  name (test_statistical_truth.py reads data/<name>.csv for each dataset
  its record lists), by that directory as a fixtures path together with
  the file's stem;
* every .do file under test/ is named by another of them --
  run_all_cscripts.do by test_cscript_hygiene.py, cert_helpers.do by the
  scripts that run it, fixtures/twoway_corpus.do by
  test_option_surface.cscript.

This file names fixtures only to guard them, so it is not one of the files
that can name them.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
_FIXTURES = os.path.join(_HERE, "fixtures")


def _git(*args):
    return subprocess.run(["git", "-C", _REPO, *args],
                          capture_output=True, text=True)


@pytest.fixture(scope="module")
def tracked():
    p = _git("ls-files")
    if p.returncode != 0:
        pytest.skip("not a git working tree")
    return {os.path.normpath(line) for line in p.stdout.splitlines()}


def _fixture_files():
    out = []
    for root, _dirs, files in os.walk(_FIXTURES):
        for f in files:
            if f.startswith(".") or f.endswith(".pyc"):
                continue
            full = os.path.join(root, f)
            out.append(os.path.relpath(full, _REPO))
    return sorted(out)


def test_the_scan_found_the_fixtures(tracked):
    """Guards the guard: an empty list would pass every check below, and so
    would a partial one -- a file the scan misses is never checked."""
    found = _fixture_files()
    # Measured 24sep2026: git tracks 32 files under test/fixtures, 13 of
    # them in data/ and scheme_visual/.  The floor this replaced, 8, passed
    # a scan that never left the top directory (19 files), and then no file
    # below it was asked about.  Every file git holds there must be one the
    # scan found; the parametrized test below asks the converse.  Outside a
    # git working tree `tracked' skips this, as it skips every check it
    # guards.
    prefix = os.path.join("test", "fixtures", "")
    under = {f for f in tracked if f.startswith(prefix)}
    assert under, "git tracks no file under test/fixtures"
    missed = sorted(under - set(found))
    assert not missed, (
        f"the scan found {len(found)} files under test/fixtures and missed "
        f"{len(missed)} that git tracks there, so the checks below never "
        f"see them: {missed}"
    )
    assert any(f.endswith("stat_truth.json") for f in found)


@pytest.mark.parametrize("rel", _fixture_files())
def test_every_fixture_is_tracked_by_git(rel, tracked):
    assert os.path.normpath(rel) in tracked, (
        f"{rel} is a test fixture -- test_every_fixture_is_named_by_a_test "
        f"holds that a test file or certification script names it -- and "
        f"git does not track it, so a clone does not have it. Add it with "
        f"`git add -f' -- .git/info/exclude carries a `*.json' rule that "
        f"silently drops it otherwise."
    )


# ---------------------------------------------------------------------------
# Nothing under test/ that nothing names
# ---------------------------------------------------------------------------

#: The kinds of file in test/ that can name a fixture or a do-file: the test
#: modules and their helpers, the certification scripts, the do-files.
_READER_EXTENSIONS = (".py", ".cscript", ".do")


@pytest.fixture(scope="module")
def readers():
    """{file name: text} of every test file and certification script in
    test/, this file excepted."""
    me = os.path.abspath(__file__)
    out = {}
    for f in sorted(os.listdir(_HERE)):
        path = os.path.join(_HERE, f)
        if (not f.endswith(_READER_EXTENSIONS) or not os.path.isfile(path)
                or os.path.abspath(path) == me):
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            out[f] = fh.read()
    return out


def _names(text, name):
    """Whether *text* names *name* as a whole token: "truth.json" is not
    named by "stat_truth.json", nor "sp500" by "sp5000"."""
    return re.search(r"(?<![\w.-])" + re.escape(name) + r"(?![\w-])",
                     text) is not None


def _names_dir(text, directory):
    """Whether *text* names test/fixtures/<directory> as a path: `"fixtures",
    "data"' in an os.path.join, or `fixtures/data' in a string.  A bare
    "data" is a JSON key in half the suite and names nothing."""
    return re.search(r"fixtures(?:[\"']\s*,\s*[\"']|/)"
                     + re.escape(directory) + r"(?![\w.-])", text) is not None


def _named_by(sub, readers):
    """The readers that name the fixture at *sub*, a path relative to
    test/fixtures: by its file name, or by its directory and its stem.  A
    file deeper than one directory must be named by its file name."""
    parts = sub.split(os.sep)
    hits = [f for f, t in readers.items() if _names(t, parts[-1])]
    if not hits and len(parts) == 2:
        stem = os.path.splitext(parts[-1])[0]
        hits = [f for f, t in readers.items()
                if _names_dir(t, parts[0]) and _names(t, stem)]
    return hits


def _do_files():
    out = []
    for root, _dirs, files in os.walk(_HERE):
        for f in files:
            if f.endswith(".do"):
                out.append(os.path.relpath(os.path.join(root, f), _REPO))
    return sorted(out)


def test_the_readers_are_found(readers):
    """Guards the two guards below: a scan that read nothing would find
    every file unnamed, and one that read this file would find every
    fixture named."""
    names = set(readers)
    cscripts = {f for f in os.listdir(_HERE) if f.endswith(".cscript")}
    # Measured 24sep2026: 63 certification scripts, all of them read.
    assert len(cscripts) >= 63 and cscripts <= names, sorted(cscripts - names)
    assert {"conftest.py", "cert_helpers.do", "run_all_cscripts.do",
            "test_statistical_truth.py", "test_scheme_visual_truth.py"} <= names
    assert os.path.basename(__file__) not in names


def test_the_readers_name_what_they_load(readers):
    """The two ways a fixture is named, each on a file that loads it that
    way, and each refusing what only looks like it."""
    assert _named_by("stat_truth.json", readers)
    assert "test_scheme_visual_truth.py" in _named_by(
        os.path.join("scheme_visual", "truth.json"), readers)
    # data/nlsw88.csv appears nowhere by its file name: it is loaded as
    # os.path.join(_DATA_DIR, f"{name}.csv").
    assert not [f for f, t in readers.items() if _names(t, "nlsw88.csv")]
    assert "test_statistical_truth.py" in _named_by(
        os.path.join("data", "nlsw88.csv"), readers)
    assert not _named_by(os.path.join("data", "nlsw88x.csv"), readers)
    assert not _named_by("no_such_fixture.json", readers)
    assert not _names('"stat_truth.json"', "truth.json")
    assert _names('os.path.join(_DIR, "truth.json")', "truth.json")
    assert _names_dir('os.path.join(_HERE, "fixtures", "data")', "data")
    assert _names_dir('"test/fixtures/data/auto.csv"', "data")
    assert not _names_dir('{"data": [1, 2]}', "data")
    assert not _names_dir('os.path.join(_HERE, "fixtures", "database")',
                          "data")


@pytest.mark.parametrize("rel", _fixture_files())
def test_every_fixture_is_named_by_a_test(rel, readers):
    sub = os.path.relpath(os.path.join(_REPO, rel), _FIXTURES)
    assert _named_by(sub, readers), (
        f"{rel} is named by no test file or certification script in test/, "
        f"so nothing reads it: wire it to a test or delete it (GAPS.md L8). "
        f"A file in a subdirectory may instead be named by that directory, "
        f"as a fixtures path, and its stem."
    )


def test_the_do_file_scan_found_the_scripts():
    # Measured 24sep2026, after the fifteen dead diagnostics were deleted:
    # these three are every .do file under test/.
    found = {os.path.basename(p) for p in _do_files()}
    assert {"cert_helpers.do", "run_all_cscripts.do",
            "twoway_corpus.do"} <= found, sorted(found)


@pytest.mark.parametrize("rel", _do_files())
def test_every_do_file_is_named_by_another_script_or_test(rel, readers):
    base = os.path.basename(rel)
    hits = [f for f, t in readers.items() if f != base and _names(t, base)]
    assert hits, (
        f"{rel} is named by no other test file or certification script in "
        f"test/: run_all_cscripts.do does not run it and no script or test "
        f"calls it, so it tests nothing (GAPS.md L8).  Wire it in or delete "
        f"it."
    )


# ---------------------------------------------------------------------------
# Every fixture names its generator, carries complete _meta and holds no
# absolute path (WP-31 K3, S60 D-60a..D-60c)
# ---------------------------------------------------------------------------

#: A fixture written by hand: no generator regenerates it.  The two text
#: corpora are read line by line by test_conformance.cscript (a header
#: line would be registered as a command), so the exemption lives here.
HAND_WRITTEN = None

#: {top-level file in test/fixtures: the committed script that writes it}.
#: data/ (datasets) and scheme_visual/ (scripts/svg_truth.py renders) are
#: exempt by directory.  A fixture whose _meta names a source must agree.
GENERATORS = {
    "abbrev_truth.json": "scripts/extract_abbrev_truth.do",
    "added_text_globals.json": "scripts/extract_added_text_globals.do",
    "added_text_truth.json": "scripts/extract_added_text_truth.do",
    "alias_spelling_truth.json": "scripts/extract_alias_spelling_truth.do",
    "applicability_truth.json": "scripts/extract_applicability_truth.do",
    "area_cmissing_truth.json": "scripts/extract_area_cmissing_truth.do",
    "arrowhead_truth.json": "scripts/extract_arrowhead_truth.do",
    "axes_n_truth.json": "scripts/extract_axes_n_truth.do",
    "axis2_move_truth.json": "scripts/extract_axis2_move_truth.do",
    "axis2_truth.json": "scripts/extract_axis2_truth.do",
    "axis_add_truth.json": "scripts/extract_axis_add_truth.do",
    "axis_format_truth.json": "scripts/extract_axis_format_truth.do",
    "axis_look_truth.json": "scripts/extract_axis_look_truth.do",
    "axis_subopt_truth.json": "scripts/extract_axis_subopt_truth.do",
    "axis_truth.json": "scripts/extract_axis_truth.do",
    "axisn_alt_truth.json": "scripts/extract_axisn_alt_truth.do",
    "axisn_date_truth.json": "scripts/extract_axisn_date_truth.do",
    "axisn_minor_truth.json": "scripts/extract_axisn_minor_truth.do",
    "bar_geometry_truth.json": "scripts/extract_bar_geometry_truth.do",
    "bare_intensity_truth.json": "scripts/extract_bare_intensity_truth.do",
    "bare_prefix_truth.json": "scripts/extract_bare_prefix_truth.do",
    "by_chrome_truth.json": "scripts/extract_by_chrome_truth.do",
    "by_grid_truth.json": "scripts/extract_by_grid_truth.do",
    "by_remainder_truth.json": "scripts/extract_by_remainder_truth.do",
    "by_scales_truth.json": "scripts/extract_by_scales_truth.do",
    "by_text_truth.json": "scripts/extract_by_text_truth.do",
    "bystyle_truth.json": "scripts/extract_bystyle_truth.do",
    "catchall_options_truth.json": "scripts/extract_catchall_options_truth.do",
    "chrome_truth.json": "scripts/extract_chrome_truth.do",
    "ci_band_style_truth.json": "scripts/extract_scheme_truth.py",
    "ci_plot_index_truth.json": "scripts/extract_ci_plot_index_truth.do",
    "color_truth.json": "scripts/extract_color_truth.py",
    "colorvar_options_truth.json": "scripts/extract_colorvar_options_truth.do",
    "colorvar_qualifier_truth.json": "scripts/extract_colorvar_qualifier_truth.do",
    "colorvar_truth.json": "scripts/extract_colorvar_truth.do",
    "colorvar_types_truth.json": "scripts/extract_colorvar_types_truth.do",
    "colour_grammar_truth.json": "scripts/extract_colour_grammar_truth.do",
    "colour_width_edges_truth.json": "scripts/extract_colour_width_edges_truth.do",
    "conformance_corpus.txt": HAND_WRITTEN,
    "connect_truth.json": "scripts/extract_connect_truth.do",
    "contour_truth.json": "scripts/extract_contour_truth.do",
    "data_locale_truth.json": "scripts/extract_data_locale_truth.do",
    "date_axes_truth.json": "scripts/extract_date_axes_truth.do",
    "date_axis_truth.json": "scripts/extract_date_axis_truth.do",
    "date_truth.json": "scripts/extract_date_truth.do",
    "date_units_truth.json": "scripts/extract_date_units_truth.do",
    "default_axes_truth.json": "scripts/extract_default_axes_truth.do",
    "default_base_truth.json": "scripts/extract_default_base_truth.do",
    "dot_truth.json": "scripts/extract_dot_truth.do",
    "edge_title_truth.json": "scripts/extract_edge_title_truth.do",
    "embedded_rows_truth.json": "scripts/extract_embedded_rows_truth.do",
    "emptied_layer_truth.json": "scripts/extract_emptied_layer_truth.do",
    "estimator_edges_truth.json": "scripts/extract_estimator_edges_truth.do",
    "filter_truth.json": "scripts/extract_filter_truth.do",
    "fit_options_truth.json": "scripts/extract_fit_options_truth.do",
    "format_truth.json": "scripts/extract_format_truth.do",
    "fp_edge_truth.json": "scripts/extract_fp_edge_truth.do",
    "function_expr_truth.json": "scripts/extract_function_truth.do",
    "geometry_truth.json": "scripts/extract_geometry_truth.do",
    "global_text_truth.json": "scripts/extract_global_text_truth.do",
    "graph_export_truth.json": "scripts/extract_graph_export_truth.do",
    "graph_text_truth.json": "scripts/extract_graph_text_truth.do",
    "help_claims_6_truth.json": "scripts/extract_twoway_oracle_truth.do",
    "help_examples.txt": HAND_WRITTEN,
    "horizontal_truth.json": "scripts/extract_horizontal_truth.do",
    "intensity_truth.json": "scripts/extract_intensity_truth.do",
    "join_order_truth.json": "scripts/extract_join_order_truth.do",
    "kde_hist_fn_truth.json": "scripts/extract_kde_hist_fn_truth.do",
    "key_text_truth.json": "scripts/extract_key_text_truth.do",
    "kpi_pctile_truth.json": "scripts/extract_kpi_pctile_truth.do",
    "kpi_truth.json": "scripts/extract_kpi_truth.do",
    "kpi_weights_truth.json": "scripts/extract_kpi_weights_truth.do",
    "legend_geometry_truth.json": "scripts/extract_legend_geometry_truth.do",
    "legend_remainder_truth.json": "scripts/extract_legend_remainder_truth.do",
    "line_width_truth.json": "scripts/extract_line_width_truth.do",
    "linewidth_chain_truth.json": "scripts/extract_linewidth_chain_truth.do",
    "lpoly_rot_truth.json": "scripts/extract_lpoly_rot_truth.do",
    "lpolyci_truth.json": "scripts/extract_lpolyci_truth.do",
    "margin_truth.json": "scripts/extract_margin_truth.do",
    "marker_linewidth_truth.json": "scripts/extract_marker_linewidth_truth.do",
    "mband_band_edges.json": "scripts/extract_mband_band_edges.do",
    "minor_tick_truth.json": "scripts/extract_minor_tick_truth.do",
    "mlabtextstyle_truth.json": "scripts/extract_mlabtextstyle_truth.do",
    "mlabvpos_truth.json": "scripts/extract_mlabvpos_truth.do",
    "named_style_truth.json": "scripts/extract_named_style_truth.do",
    "natscale_axes_truth.json": "scripts/extract_natscale_axes_truth.do",
    "natscale_truth.json": "scripts/extract_natscale_truth.do",
    "parsed_values_truth.json": "scripts/extract_parsed_values_truth.do",
    "parser_twoway_truth.json": "scripts/extract_twoway_oracle_truth.do",
    "pcycle_fraction_truth.json": "scripts/extract_pcycle_fraction_truth.do",
    "pip_refusals.json": "scripts/extract_pip_refusals.py",
    "qualified_stat_truth.json": "scripts/extract_qualified_stat_truth.do",
    "rangept_truth.json": "scripts/extract_rangept_truth.do",
    "rbar_dot_truth.json": "scripts/extract_rbar_dot_truth.do",
    "recast_truth.json": "scripts/extract_recast_truth.do",
    "refline_extent_truth.json": "scripts/extract_refline_extent_truth.do",
    "refline_frame_truth.json": "scripts/extract_refline_frame_truth.do",
    "refline_truth.json": "scripts/extract_refline_truth.do",
    "region_remainder_truth.json": "scripts/extract_region_remainder_truth.do",
    "region_truth.json": "scripts/extract_region_truth.do",
    "rejected_options.json": "scripts/extract_rejected_options.do",
    "saving_chars_truth.json": "scripts/extract_saving_chars_truth.do",
    "scheme_layer_truth.json": "scripts/extract_scheme_layer_truth.do",
    "scheme_lookup_truth.json": "scripts/extract_scheme_lookup_truth.do",
    "scheme_ref_gsize_truth.json": "scripts/extract_scheme_ref_gsize_truth.do",
    "scheme_truth.json": "scripts/extract_scheme_truth.py",
    "series_label_truth.json": "scripts/extract_series_label_truth.do",
    "size_units_truth.json": "scripts/extract_size_units_truth.do",
    "sizing_truth.json": "scripts/extract_sizing_truth.do",
    "smcl_more_truth.json": "scripts/extract_smcl_more_truth.do",
    "smcl_text_truth.json": "scripts/extract_smcl_text_truth.do",
    "stat_truth.json": "scripts/extract_stat_truth.do",
    "stata_ticks_truth.json": "scripts/extract_stata_ticks_truth.do",
    "style_files_truth.json": "scripts/extract_style_files_truth.do",
    "style_name_truth.json": "scripts/extract_style_name_truth.do",
    "stylelist_truth.json": "scripts/extract_stylelist_truth.do",
    "subopt_abbrev_truth.json": "scripts/extract_subopt_abbrev_truth.do",
    "svg_truth_smoke.json": "scripts/extract_svg_truth_smoke.do",
    "svg_truth_smoke.svg": "scripts/extract_svg_truth_smoke.do",
    "svg_truth_tiny.svg": HAND_WRITTEN,
    "symbol_pattern_truth.json": "scripts/extract_symbol_pattern_truth.do",
    "tabs_legend_edges_truth.json": "scripts/extract_tabs_legend_edges_truth.do",
    "taxis_truth.json": "scripts/extract_taxis_truth.do",
    "text_truth.json": "scripts/extract_text_truth.do",
    "textbox_truth.json": "scripts/extract_textbox_truth.do",
    "ts_operator_truth.json": "scripts/extract_ts_operator_truth.do",
    "twoway_command_form_truth.json": "scripts/extract_twoway_command_form_truth.do",
    "twoway_corpus.do": HAND_WRITTEN,
    "twoway_option_parity_truth.json": "scripts/extract_twoway_oracle_truth.do",
    "unlabelled_truth.json": "scripts/extract_unlabelled_truth.do",
    "user_scheme_rule_truth.json": "scripts/extract_user_scheme_rule_truth.do",
    "utf8_cases.txt": "scripts/gen_utf8_cases.py",
    "value_bounds_truth.json": "scripts/extract_value_bounds_truth.do",
    "value_list_truth.json": "scripts/extract_value_list_truth.do",
    "value_truth.json": "scripts/merge_value_truth.py",
    "varlabel_mlabel_truth.json": "scripts/extract_varlabel_mlabel_truth.do",
    "weight_operator_truth.json": "scripts/extract_weight_operator_truth.do",
    "weighted_markers_truth.json": "scripts/extract_weighted_markers_truth.do",
}

#: The five _meta keys every regenerated fixture carries.
META_KEYS = ("stata_version", "born_date", "dash_commit", "extracted",
             "source")

#: Fixtures written before the five keys were required, each by a generator
#: that predates them; `make truth' rewrites them with the five keys and the
#: entry is then deleted (test_a_pending_fixture_is_still_pending fails
#: until it is).  Nothing may join this list.
PENDING_META = frozenset({
    "added_text_truth.json",
    "alias_spelling_truth.json",
    "axis2_truth.json",
    "axis_add_truth.json",
    "axis_format_truth.json",
    "axis_subopt_truth.json",
    "bar_geometry_truth.json",
    "by_chrome_truth.json",
    "by_grid_truth.json",
    "by_scales_truth.json",
    "by_text_truth.json",
    "chrome_truth.json",
    "ci_band_style_truth.json",
    "color_truth.json",
    "colorvar_qualifier_truth.json",
    "colorvar_truth.json",
    "colour_grammar_truth.json",
    "connect_truth.json",
    "date_axis_truth.json",
    "date_units_truth.json",
    "format_truth.json",
    "function_expr_truth.json",
    "graph_text_truth.json",
    "help_claims_6_truth.json",
    "horizontal_truth.json",
    "intensity_truth.json",
    "join_order_truth.json",
    "key_text_truth.json",
    "lpoly_rot_truth.json",
    "lpolyci_truth.json",
    "mlabtextstyle_truth.json",
    "mlabvpos_truth.json",
    "named_style_truth.json",
    "parser_twoway_truth.json",
    "pip_refusals.json",
    "recast_truth.json",
    "refline_extent_truth.json",
    "refline_truth.json",
    "scheme_lookup_truth.json",
    "scheme_truth.json",
    "series_label_truth.json",
    "stylelist_truth.json",
    "subopt_abbrev_truth.json",
    "svg_truth_smoke.json",
    "taxis_truth.json",
    "text_truth.json",
    "twoway_option_parity_truth.json",
    "unlabelled_truth.json",
    "value_list_truth.json",
    "value_truth.json",
})

#: Fixtures whose generator GENERATORS names but which is not yet written:
#: such a fixture keeps its old _meta and probe paths, and
#: test_the_pending_generator_is_still_pending fails the day the script is
#: committed, so the entry is deleted then.  Empty since S60 wrote
#: scripts/extract_qualified_stat_truth.do (WP-31 K3); nothing may join it.
GENERATOR_PENDING = frozenset()

#: A string that is a machine path: POSIX roots a probe writes under, or a
#: Windows drive.
_ABSOLUTE = re.compile(r"^/(Users|private|var|tmp|home)/|^[A-Z]:\\")


def _top_fixtures():
    return sorted(f for f in os.listdir(_FIXTURES)
                  if os.path.isfile(os.path.join(_FIXTURES, f))
                  and not f.startswith("."))


def _json_fixtures():
    return [f for f in _top_fixtures() if f.endswith(".json")]


def _load(name):
    with open(os.path.join(_FIXTURES, name), encoding="utf-8") as fh:
        return json.load(fh)


def _meta(doc):
    m = doc.get("_meta") if isinstance(doc, dict) else None
    return m if isinstance(m, dict) else {}


def _strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


class TestEveryFixtureHasMeta:

    def test_the_table_lists_every_fixture(self):
        assert sorted(GENERATORS) == _top_fixtures()

    @pytest.mark.parametrize("rel", _top_fixtures())
    def test_every_fixture_names_a_generator(self, rel):
        gen = GENERATORS[rel]
        if gen is HAND_WRITTEN:
            assert not rel.endswith(".json"), f"{rel}: a JSON fixture is generated"
            return
        if rel in GENERATOR_PENDING:
            assert not os.path.isfile(os.path.join(_REPO, gen)), rel
            return
        assert os.path.isfile(os.path.join(_REPO, gen)), (rel, gen)
        with open(os.path.join(_REPO, gen), encoding="utf-8",
                  errors="replace") as fh:
            assert _names(fh.read(), rel), f"{gen} does not name {rel}"
        if rel.endswith(".json"):
            src = _meta(_load(rel)).get("source")
            assert src in (None, gen), (rel, src, gen)

    @pytest.mark.parametrize(
        "rel", [f for f in _json_fixtures()
                if f not in PENDING_META | GENERATOR_PENDING])
    def test_every_fixture_has_meta(self, rel):
        missing = [k for k in META_KEYS if k not in _meta(_load(rel))]
        assert not missing, f"{rel}: _meta lacks {missing}"
        assert _meta(_load(rel))["source"] == GENERATORS[rel]

    @pytest.mark.parametrize("rel", sorted(PENDING_META))
    def test_a_pending_fixture_is_still_pending(self, rel):
        missing = [k for k in META_KEYS if k not in _meta(_load(rel))]
        assert missing, f"{rel} has the five keys: delete it from PENDING_META"

    def test_the_pending_generator_is_still_pending(self):
        for rel in GENERATOR_PENDING:
            assert GENERATORS[rel]
            assert not os.path.isfile(os.path.join(_REPO, GENERATORS[rel])), (
                f"{GENERATORS[rel]} exists: regenerate {rel} and delete it "
                f"from GENERATOR_PENDING")

    @pytest.mark.parametrize(
        "rel", [f for f in _json_fixtures() if f not in GENERATOR_PENDING])
    def test_no_absolute_path(self, rel):
        bad = sorted({s[:120] for s in _strings(_load(rel))
                      if _ABSOLUTE.search(s)})
        assert not bad, f"{rel} holds machine paths: {bad[:5]}"

    def test_the_path_rule_catches_each_root(self):
        # Built from fragments: no file in the tree holds a home path.
        for s in ("/" + "Users/x/a.do", "/private/tmp/a", "/var/folders/a",
                  "/tmp/a", "/" + "home/u/a", "C:\\tmp\\a"):
            assert _ABSOLUTE.search(s), s
        for s in ("scripts/extract_kpi_truth.do", "a/Users/b", "%td", "/"):
            assert not _ABSOLUTE.search(s), s

    def test_make_truth_lists_every_generator(self):
        with open(os.path.join(_REPO, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        m = re.search(r"^truth:\n((?:\t.*\n)+)", mk, re.M)
        assert m, "the Makefile has no truth: target"
        recipe = m.group(1)
        assert "for f in scripts/extract_*.do" in recipe
        assert "scripts/stata_slot.sh" in recipe
        assert re.search(r"^truth-check:\n\t.*test_fixtures_are_committed\.py",
                         mk, re.M)
        for gen in sorted({g for g in GENERATORS.values() if g}):
            base = os.path.basename(gen)
            if base.startswith("extract_") and base.endswith(".do"):
                continue
            assert gen in recipe, f"make truth does not run or name {gen}"
