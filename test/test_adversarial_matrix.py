"""test_adversarial_matrix.py -- CLAUDE.md rule 18, ROADMAP.md WP-20 AC-20.3.

AC-20.3: "Three adversarial cases (auth bypass, injection, exhaustion) per
input surface exist and pass."  This file holds

* ``SURFACES``, the registry: every input surface dash has, and for each of
  the three categories the tests that attack it.  An entry is a pytest node
  id (``"test/test_x.py::TestY::test_z"``) or a certification-script case
  (``"test_adversarial.cscript:P19-18"``);
* the meta-tests that keep the registry honest: every surface has at least
  one entry in each category, every pytest node id is collected by pytest,
  and every cscript case id is displayed by its script as ``"<id> PASS"``;
* the tests written to fill the gaps the registry exposed.  The Stata-side
  gaps are the P20 section of ``test_adversarial.cscript``.

What the three categories mean here
-----------------------------------
dash has no authentication model (GAPS.md L10): it is a Stata command, and
the app ``dash serve`` runs is a single-user tool with no login.  So for each
surface "auth bypass" (``"bypass"`` below) is an attempt to get past THAT
surface's own guard -- its validation, escaping, path containment, origin
check or rate limit -- using the encodings and obfuscations CLAUDE.md rule 16
names: malformed or overlong UTF-8, NUL bytes, homoglyphs, SMCL markup, macro
characters, mixed case and abbreviation, doubled or mismatched quotes and
``///`` continuations.  "Injection" is code or markup reaching an
interpreter -- HTML, JavaScript, CSS, JSON, Python, Stata, SMCL, a shell.
"Exhaustion" is an input that could make dash use unbounded time, memory or
stack.

Standing note: CLAUDE.md rule 19 does not apply, by design
------------------------------------------------------------
Rule 19 asks that administrators' identities be verified before they reach
administrative components.  dash has no administrators, no accounts and no
administrative components: every dashboard is built by the Stata user who
runs the command, and the served app binds loopback by default and offers no
privileged route (``/health`` reports liveness and nothing else).  Rule 19 is
therefore not applicable -- by design, not by omission (GAPS.md L10;
``test_security_surface.py`` checks that the help does not claim an access
control dash has not got).  If dash ever gains accounts or an administrative
surface, this note is wrong and rule 19 applies.
"""
import argparse
import ast
import io
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
import tokenize
import types
import warnings
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import ColumnDataSource, Div, RangeSlider, Select
from bokeh.plotting import figure

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr
from conftest import make_data_json, make_spec


# ===========================================================================
# 1. The registry
# ===========================================================================
# A surface is an input an adversary can write: a command-line token, an
# option value, the data, a file dash reads, or a request to the served app.
# Each list names the tests of that category; the meta-tests below prove
# every name resolves to a test that is collected (pytest) or displayed as
# passing (cscript).

_M = "test/test_adversarial_matrix.py::"
_BS = "test/test_served_bs_layout.py::TestAdversarialServedBs::"
# WP-22 TR-22.3: clcolor()/clpattern()/clwidth(), mlabangle(), mlabformat().
_TW = "test/test_twoway_option_parity.py::TestAdversarialTwowayOptions::"

SURFACES = {
    # `dash <plot> varlist, ...' -- the plot-type token and the varlist.
    "plot_varlist_and_type": {
        "bypass": [
            "test_adversarial.cscript:P20-01",
            "test_parser_integrity.cscript:P1B-13",
            "test_parser_integrity.cscript:P1B-14",
        ],
        "injection": [
            "test_adversarial.cscript:P2-79",
            "test_adversarial.cscript:P20-29",
            "test/test_security_surface.py::TestUserTextIsEchoedAsText::test_no_display_line_expands_user_text",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P2-83",
            "test_adversarial.cscript:P19-07",
            "test_adversarial.cscript:P19-08",
        ],
    },
    # `pcarrowi #y1 #x1 #y2 #x2 [(#clockpos)] ["label"] ...' -- a paired-
    # coordinate plot's immediate values: numbers, clock positions and free
    # text, read by dash.ado's Mata encoder into the spec and drawn by the
    # renderer (WP-22).
    "immediate_pc_values": {
        "bypass": [
            "test_adversarial.cscript:P22-01",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_a_malformed_record_is_named",
        ],
        "injection": [
            "test_adversarial.cscript:P22-02",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_the_label_is_text_not_markup",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P22-03",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_a_hundred_thousand_records_are_read_in_bounded_time",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_the_arrow_heads_are_added_in_one_change",
        ],
    },
    # `if' and `in' on a plot or a KPI; the renderer re-applies them.
    "if_in_qualifiers": {
        "bypass": [
            "test/test_security_surface.py::TestIfQualifierLeavesStringLiteralsAlone::test_the_literal_is_unchanged",
            _M + "TestIfQualifierEncodings::test_the_spelling_does_not_get_past_the_whitelist",
            "test/test_filter_widget_data.py::TestOneWidgetWhateverTheGraphsSelect::test_a_numeric_variable",
        ],
        "injection": [
            "test/test_axis_options.py::TestIfQualifierWhitelistIsNotWeakened::test_hostile_expressions_are_rejected",
            "test/test_phase5.py::TestIfExprRceHardening::test_at_poc_payload_blocked_end_to_end",
            "test/test_server_layer_defects.py::TestAKpiQualifierIsApplied::test_a_kpi_qualifier_cannot_execute",
        ],
        "exhaustion": [
            _M + "TestIfQualifierExhaustion::test_a_run_of_negations_is_skipped_not_raised",
            _M + "TestIfQualifierExhaustion::test_the_served_app_has_the_same_bound",
            "test_adversarial.cscript:P20-20",
        ],
    },
    # jitter(), level(), bin(), n(), bwidth(), bands(), xsize() ...
    "numeric_plot_options": {
        "bypass": [
            "test_adversarial.cscript:P20-02",
            "test_adversarial.cscript:P9-04",
            "test_adversarial.cscript:P20-18",
        ],
        "injection": [
            "test_adversarial.cscript:P9-01",
            "test_adversarial.cscript:P9-02",
            "test_adversarial.cscript:P9-03",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P9-06",
            "test_adversarial.cscript:P9-07",
            "test_adversarial.cscript:P9-08",
            "test_adversarial.cscript:P9-09",
            "test_adversarial.cscript:P9-10",
        ],
    },
    # mcolor(), msymbol(), lcolor(), lpattern(), msize(), kernel() ...
    "style_plot_options": {
        "bypass": [
            "test/test_security_surface.py::TestAColourMustBeAColour::test_a_non_hex_hash_string_is_rejected",
            "test_adversarial.cscript:P20-03",
            "test/test_option_validation.py::TestUserTextIsEchoedThroughDashDisplay::test_the_style_note",
            _TW + "test_an_angle_in_another_scripts_digits_is_not_an_angle",
        ],
        "injection": [
            "test_adversarial.cscript:P2-81",
            "test/test_html_output.py::TestAdversarialPlotOptions::test_injection_in_mcolor_produces_valid_html",
            _TW + "test_markup_in_a_value_is_named_as_text_and_never_drawn",
            _TW + "test_a_colour_that_is_code_is_refused_by_the_colour_reader",
        ],
        "exhaustion": [
            "test/test_option_validation.py::TestABadStyleValueNeverAborts::test_a_non_finite_size_or_width",
            _M + "TestStyleOptionBounds::test_a_megabyte_colour_is_judged_in_linear_time",
            _TW + "test_a_megabyte_angle_is_judged_at_once",
            _TW + "test_a_non_finite_clwidth_is_named_not_drawn",
        ],
    },
    # mlabel(varname) and the legend's label() and order() text.
    "text_plot_options": {
        "bypass": [
            "test_adversarial.cscript:P20-04",
            "test/test_option_validation.py::TestUserTextIsEchoedThroughDashDisplay::test_the_mlabel_extras_warning",
            _TW + "test_a_format_in_another_scripts_digits_is_not_applied",
        ],
        "injection": [
            "test/test_graph_options.py::TestLegendLabels::test_legend_label_xss_is_carried_as_text",
            _TW + "test_markup_in_a_value_is_named_as_text_and_never_drawn",
        ],
        "exhaustion": [
            _M + "TestTextPlotOptionBounds::test_a_legend_order_of_a_hundred_thousand_keys_is_bounded",
            _M + "TestTextPlotOptionBounds::test_a_long_legend_label_is_escaped_once",
            _TW + "test_a_format_stata_refuses_builds_no_giant_label",
            _TW + "test_the_widest_format_stata_accepts_is_bounded_by_stata",
        ],
    },
    # title(), subtitle(), note(), caption(), xtitle(), ytitle().
    "graph_text_options": {
        "bypass": [
            "test_adversarial.cscript:P20-15",
            "test_json_escaping.cscript:JSE-08",
        ],
        "injection": [
            "test_adversarial.cscript:P2-78",
            "test/test_html_output.py::TestXssInHtmlOutput::test_script_tag_in_title_is_escaped",
            "test/test_html_output.py::TestAdversarialPlotOptions::test_xss_in_note_option_escaped",
        ],
        "exhaustion": [
            _M + "TestGraphTextBounds::test_a_long_title_is_drawn_once_in_bounded_time",
        ],
    },
    # xlabel() / ylabel(): numlists, a(b)c, #N, value "label" pairs, format().
    "axis_label_options": {
        "bypass": [
            _M + "TestAxisLabelInjection::test_pre_escaped_markup_is_carried_as_written_not_decoded",
            _M + "TestAxisLabelBounds::test_a_non_finite_endpoint_does_not_raise",
        ],
        "injection": [
            _M + "TestAxisLabelInjection::test_a_tick_label_cannot_break_out_of_the_formatter_code",
        ],
        "exhaustion": [
            _M + "TestAxisLabelBounds::test_an_increment_past_the_tick_limit_keeps_the_default_ticks",
            _M + "TestAxisLabelBounds::test_a_huge_count_is_clamped",
            _M + "TestNumericFormatBounds::test_an_axis_format_with_a_billion_decimals_is_bounded",
        ],
    },
    # by(varlist, suboptions).
    "by_option": {
        "bypass": [
            "test_adversarial.cscript:P20-05",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_shell_injection_blocked",
        ],
        "injection": [
            "test/test_phase5.py::TestByFacetingSecurity::test_by_import_injection_blocked",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_xss_in_facet_label_is_canvas_text",
        ],
        "exhaustion": [
            "test/test_resource_limits.py::TestByOnAHighCardinalityVariable::test_the_first_groups_in_sort_order_are_kept",
            "test_resource_limits.cscript:RL-06",
            "test/test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_the_saved_page_hands_gridplot_the_panels_alone",
            "test/test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_the_served_app_hands_gridplot_the_panels_alone",
        ],
    },
    # name(name[, replace]) on a graph or a KPI.
    "name_option": {
        "bypass": [
            "test_adversarial.cscript:P19-25",
            "test_adversarial.cscript:P19-02",
            "test_adversarial.cscript:P20-32",
            "test/test_reserved_names.py::TestAdversarialReservedNames::test_bypass_no_spelling_takes_a_panel_s_place",
            "test_registry_collision.cscript:REG-16",
            "test/test_keyword_names.py::TestLinkAll::test_a_graph_named_all_is_refused_in_both_modes",
            "test_adversarial.cscript:P20-33",
            "test_registry_collision.cscript:REG-17",
            "test_registry_collision.cscript:REG-18",
            "test_registry_collision.cscript:REG-20",
            "test_registry_collision.cscript:REG-21",
            "test_registry_collision.cscript:REG-23",
            "test_registry_collision.cscript:REG-24",
            "test_registry_collision.cscript:REG-25",
            "test_registry_collision.cscript:REG-26",
            "test_registry_collision.cscript:REG-29",
            "test_registry_collision.cscript:REG-30",
            "test_registry_collision.cscript:REG-31",
            "test_registry_collision.cscript:REG-32",
            "test_registry_collision.cscript:REG-33",
            "test_registry_collision.cscript:REG-35",
            "test_registry_collision.cscript:REG-36",
        ],
        "injection": [
            "test_adversarial.cscript:P19-25",
            "test_adversarial.cscript:P19-26",
            "test_registry_collision.cscript:REG-17",
            "test_registry_collision.cscript:REG-22",
            "test_registry_collision.cscript:REG-29",
            "test_registry_collision.cscript:REG-32",
            "test/test_reserved_names.py::TestAdversarialReservedNames::test_injection_a_refused_name_is_inert_text",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-21",
            "test_adversarial.cscript:P19-01",
            "test/test_reserved_names.py::TestAdversarialReservedNames::test_exhaustion_many_refused_names_make_one_bounded_report",
        ],
    },
    # saving(path) on a plot and on dash build (.html and .py).
    "saving_path": {
        "bypass": [
            "test_path_validation.cscript:PV-03b",
            "test_path_validation.cscript:PV-14",
            "test_path_validation.cscript:PV-15",
            "test_adversarial.cscript:P20-16",
        ],
        "injection": [
            "test_path_validation.cscript:PV-04",
            "test_adversarial.cscript:P2-85c",
            "test_adversarial.cscript:P20-07",
            "test_adversarial.cscript:P20-08",
            "test_adversarial.cscript:P20-29",
        ],
        "exhaustion": [
            _M + "TestRendererOutputPath::test_a_megabyte_path_is_judged_in_linear_time",
        ],
    },
    # scheme() / theme() names, and .scheme files with #include.
    "scheme_and_theme": {
        "bypass": [
            "test/test_scheme.py::TestSecurity::test_path_traversal_raises",
            "test/test_scheme.py::TestSecurity::test_BUG_51_1a_symlink_to_external_file_raises",
            "test_theme_escaping.cscript:THM-03",
            _M + "TestSchemeIncludes::test_an_include_that_leaves_the_allowed_directories_is_not_read",
            "test_adversarial.cscript:P20-06",
        ],
        "injection": [
            "test_theme_escaping.cscript:THM-05",
            "test/test_security_surface.py::TestAColourMustBeAColour::test_a_scheme_cannot_break_out_of_its_css_rule",
            _M + "TestSchemeIncludes::test_scheme_values_reach_the_served_app_only_as_data",
            "test_adversarial.cscript:P20-11",
        ],
        "exhaustion": [
            _M + "TestSchemeIncludes::test_a_deep_include_chain_does_not_exhaust_the_stack",
            _M + "TestSchemeIncludes::test_include_cycles_terminate",
            "test/test_scheme_review_fixes.py::TestHostileSchemeValues::test_three_hostile_values_give_three_warnings_and_the_defaults",
        ],
    },
    # dash kpi stat(var), title(), subtitle(), fmt(), color(), bgcolor(),
    # update().
    "kpi": {
        "bypass": [
            "test_adversarial.cscript:P8-87",
            "test_adversarial.cscript:P20-12",
            "test_adversarial.cscript:P20-27",
            "test/test_kpi_security.py::TestKpiColourIsSanitisedOnTheInitialRender::test_the_rendered_value_is_what_the_sanitiser_would_give",
        ],
        "injection": [
            "test_adversarial.cscript:P9-11",
            "test_adversarial.cscript:P9-12",
            "test_adversarial.cscript:P9-13",
            "test_adversarial.cscript:P9-14",
            "test_adversarial.cscript:P4-85",
            "test/test_kpi_security.py::TestKpiColourIsSanitisedOnTheInitialRender::test_color_payload_does_not_reach_the_document",
            "test/test_server_kpi_card.py::TestTheCardLooksTheSameInBothModes::test_html_in_a_title_is_still_escaped",
            "test/test_kpi_security.py::TestKpiTextIsNeverMarkupOrMaths::test_the_saved_card_and_its_rebuild",
            "test/test_kpi_security.py::TestKpiTextIsNeverMarkupOrMaths::test_the_served_card_before_and_after_a_filter_moves",
            "test/test_kpi_security.py::TestKpiTextIsNeverMarkupOrMaths::test_a_hostile_name_stays_inside_its_attribute",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P19-01",
            "test/test_resource_limits.py::TestTheGraphAndPlotLimits::test_graphs_and_kpis_past_the_limit_are_dropped_in_registry_order",
            _M + "TestNumericFormatBounds::test_a_hand_edited_kpi_format_is_bounded",
            "test/test_kpi_security.py::TestAKpiFormatCannotBuildAHugeCard::test_both_modes_before_and_after_a_filter_moves",
        ],
    },
    # dash build: title(), subtitle(), layout(), link(), filter() (its
    # varname, type(), exclude(), label()), tabs(), filterposition(),
    # server, replace.
    "build_options": {
        "bypass": [
            "test_adversarial.cscript:P8-86",
            "test_adversarial.cscript:P8-88",
            "test_adversarial.cscript:P19-24",
            "test_adversarial.cscript:P20-09",
            "test_adversarial.cscript:P20-10",
            "test_adversarial.cscript:P20-17",
            "test_adversarial.cscript:P20-24",
            "test_filter_label.cscript:FL-06",
            _M + "TestLayoutGridBound::test_a_grid_only_int_can_read_is_no_grid",
            _M + "TestALayoutThatCannotBeReadIsReported::test_an_unknown_placement_is_left_out_and_named",
            _M + "TestALayoutThatCannotBeReadIsReported::test_a_bootstrap_spec_is_read_whole_or_said",
            "test_adversarial.cscript:P20-30",
            "test_echo_text.cscript:ECH-11",
            # layout(bs) as the served app reads it (WP-21).
            _BS + "test_bypass_only_the_grid_names_are_placed",
            "test/test_filter_exclude.py::TestTheSavedPageLeavesAnExcludedGraphAlone::test_whatever_order_the_graphs_came_in",
            "test/test_filter_exclude.py::TestTheSavedPageLeavesAnExcludedGraphAlone::test_a_graph_after_a_by_graph_is_left_alone",
            "test/test_filter_exclude.py::TestTheSavedPageLeavesAnExcludedGraphAlone::test_an_excluded_link_group_is_left_alone",
            "test/test_filter_widget_data.py::TestOneWidgetWhateverTheGraphsSelect::test_a_numeric_variable",
            "test/test_filter_widget_data.py::TestOneWidgetWhateverTheGraphsSelect::test_a_string_variable_is_refused_by_both",
        ],
        "injection": [
            "test_adversarial.cscript:P2-84",
            "test/test_axis_options.py::TestDashboardTitleEscaping::test_a_script_tag_is_still_escaped",
            "test/test_html_output.py::TestBuildSubtitleInHtml::test_build_subtitle_escaped",
            "test_path_validation.cscript:PV-12",
            _BS + "test_injection_no_spec_text_reaches_the_document",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-25",
            _M + "TestLayoutGridBound::test_the_saved_page_draws_it_as_auto",
            _M + "TestARepeatedLayoutNameIsPlacedOnce::test_the_saved_page_embeds_a_repeated_item_once",
            "test_adversarial.cscript:P20-31",
            _M + "TestLayoutGridBound::test_the_measure_is_never_smaller_than_the_grid",
            "test_echo_text.cscript:ECH-08",
            "test_echo_text.cscript:ECH-09",
            "test_adversarial.cscript:P19-13",
            "test_resource_limits.cscript:RL-09",
            "test_resource_limits.cscript:RL-10",
            _BS + "test_exhaustion_repeats_cannot_grow_the_served_grid",
        ],
    },
    # dash serve: port(), timeout(), nobrowser.
    "serve_options": {
        "bypass": [
            "test_adversarial.cscript:P20-14",
            "test_adversarial.cscript:P20-26",
            "test_echo_text.cscript:ECH-05",
        ],
        "injection": [
            "test_adversarial.cscript:P4-84",
            "test_adversarial.cscript:P20-13",
            "test_echo_text.cscript:ECH-03",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-19",
        ],
    },
    # global dash_max_cells, dash_max_graphs ... (WP-19).
    "resource_limit_globals": {
        "bypass": [
            "test_adversarial.cscript:P19-17",
            "test_adversarial.cscript:P19-18",
        ],
        "injection": [
            "test_adversarial.cscript:P19-19",
            "test_adversarial.cscript:P19-20",
            "test_adversarial.cscript:P19-21",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P19-11",
            "test_adversarial.cscript:P19-23",
            "test_resource_limits.cscript:RL-01",
        ],
    },
    # dash_setup: its options, and what the environment reports back
    # (installed package names and versions, file paths).
    "dash_setup_inputs": {
        "bypass": [
            "test_setup_honesty.cscript:HON-14",
            "test_setup_honesty.cscript:HON-15",
        ],
        "injection": [
            "test_adversarial.cscript:P20-22",
            "test_setup_injection.cscript:INJ-02",
            "test_setup_injection.cscript:INJ-10",
            "test_setup_injection.cscript:INJ-11",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-23",
            "test_setup_injection.cscript:INJ-07",
        ],
    },
    # The data: variable names, variable labels, value labels, string
    # values, display formats.
    "data_content": {
        "bypass": [
            "test_adversarial.cscript:P20-28",
            "test/test_server.py::TestDropdownSentinelCollision::test_standalone_sentinel_unique_when_data_has_all_value",
        ],
        "injection": [
            "test_adversarial.cscript:P4-86",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_xss_in_facet_label_is_canvas_text",
            "test/test_filters.py::TestFilterSecurity::test_filter_values_are_text_and_never_code",
            "test/test_server.py::test_escape_chars_in_data_do_not_break_syntax",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P19-11",
            "test_resource_limits.cscript:RL-03",
            "test/test_resource_limits.py::TestADropdownOnAContinuousVariable::test_the_widget_lists_at_most_the_limit",
        ],
    },
    # The spec JSON and data JSON dash_render.py reads -- written by
    # dash.ado, or by hand.
    "renderer_spec_and_data_json": {
        "bypass": [
            "test/test_resource_limits.py::TestTheLimitsTable::test_the_ceiling_cannot_be_lifted_by_the_spec",
            _M + "TestHostileSpec::test_limits_written_in_other_digits_are_refused",
            _M + "TestHostileSpec::test_an_infinite_point_count_is_clamped_not_raised",
            "test_registry_collision.cscript:REG-28",
        ],
        "injection": [
            _M + "TestHostileSpec::test_a_nul_inside_a_title_does_not_split_the_escaping",
            "test_registry_collision.cscript:REG-27",
            "test/test_server_function_security.py::TestAKeywordArgumentCannotExecute::test_the_standalone_renderer_does_not_either",
            # A graph name reaching the save button's file name (WP-21).
            "test/test_toolbar.py::TestTheBootstrapPage::test_only_a_stata_name_reaches_the_page",
            "test/test_toolbar.py::TestSaveFilename::test_anything_else_is_dashboard",
        ],
        "exhaustion": [
            _M + "TestHostileSpec::test_a_deeply_nested_spec_fails_before_anything_is_written",
            "test/test_toolbar.py::TestSaveFilename::test_a_huge_name_is_refused_without_being_scanned",
            _M + "TestLayoutGridBound::test_an_oversized_grid_is_drawn_as_auto",
            "test/test_resource_limits.py::TestAnOversizedDatasetIsRefused::test_the_saved_renderer_refuses_before_drawing",
        ],
    },
    # A `function y = <expr>' plot: an expression the renderer evaluates.
    "function_plot_expression": {
        "bypass": [
            _M + "TestFunctionExpressionEncodings::test_the_layer_draws_nothing",
        ],
        "injection": [
            "test/test_server_function_security.py::TestAKeywordArgumentCannotExecute::test_the_standalone_renderer_does_not_either",
            "test/test_server_function_security.py::TestAKeywordArgumentCannotExecute::test_the_served_app_does_not_run_a_keyword_payload",
        ],
        "exhaustion": [
            "test/test_resource_limits.py::TestAFunctionExpressionAlwaysReturns::test_a_power_tower_does_not_hang",
            "test/test_resource_limits.py::TestAFunctionExpressionAlwaysReturns::test_a_very_long_expression_is_reported_not_fatal",
        ],
    },
    # The served app's GET /health.
    "served_health_endpoint": {
        "bypass": [
            _M + "TestHealthEndpoint::test_a_rotating_forged_header_does_not_escape_the_limit",
            "test/test_server_rate_limit.py::TestSpoofingDoesNotCreateNewBuckets::test_many_spoofed_values_share_one_bucket",
        ],
        "injection": [
            _M + "TestHealthEndpoint::test_the_response_reflects_nothing_from_the_request",
        ],
        "exhaustion": [
            "test/test_server_rate_limit.py::TestHealthAndSessionsHaveSeparateBudgets::test_spending_health_does_not_refuse_sessions",
            _M + "TestHealthEndpoint::test_trusted_rotating_keys_share_the_first_contact_budget",
        ],
    },
    # Opening a session: the websocket Origin, X-Forwarded-For, the limiter.
    "served_session_creation": {
        "bypass": [
            _M + "TestSessionOrigin::test_a_foreign_origin_is_refused",
            "test/test_server_rate_limit.py::TestTheHeaderIsNotTrustedByDefault::test_the_header_is_ignored",
        ],
        "injection": [
            "test/test_server_rate_limit.py::TestAForwardedTokenIsOneBoundedKeyPerAddress::test_a_control_character_is_not_a_key",
            _M + "TestSessionOrigin::test_the_refusal_page_carries_no_request_data",
        ],
        "exhaustion": [
            "test/test_server_rate_limit.py::TestTheForwardedKeyCycleIsHeldToTheNominalRate::test_trusted_the_cycle_gets_at_most_the_nominal_rate",
            "test/test_server_rate_limit.py::TestTheStoreIsBounded::test_twenty_thousand_keys_never_exceed_the_cap",
            "test/test_server_rate_limit.py::TestAForwardedTokenIsOneBoundedKeyPerAddress::test_a_zone_of_any_length_is_not_a_key",
        ],
    },
    # Widget model changes a browser client sends: filter values, selections.
    "served_widget_model_changes": {
        "bypass": [
            _M + "TestWidgetValuesFromTheClient::test_a_select_value_outside_its_options_raises_nothing",
            _M + "TestWidgetValuesFromTheClient::test_a_range_of_nan_or_inf_raises_nothing",
            _M + "TestWidgetValuesFromTheClient::test_out_of_range_selection_indices_are_dropped",
            "test/test_filter_exclude.py::TestTheServedAppLeavesAnExcludedGraphAlone::test_whatever_order_the_graphs_came_in",
        ],
        "injection": [
            _M + "TestWidgetValuesFromTheClient::test_a_value_is_never_evaluated_or_reflected",
        ],
        "exhaustion": [
            "test/test_served_throttle.py::TestAFloodOfFilterChangesIsThrottled::test_a_thousand_select_changes_run_at_most_burst_recomputes",
            "test/test_served_throttle.py::TestTheBrushIsThrottled::test_a_thousand_selections_run_at_most_burst_and_the_last_wins",
        ],
    },
    # The served app's own command line (python app.py --port ...).
    "served_app_cli_flags": {
        "bypass": [
            "test/test_server_rate_limit.py::TestTheLauncherFlags::test_each_new_flag_refuses_a_value_outside_1_to_1000000",
            "test/test_server_rate_limit.py::TestTheLauncherFlags::test_the_value_check_names_the_range",
            _M + "TestServedCliFlags::test_a_limit_that_is_not_ascii_digits_is_refused",
        ],
        "injection": [
            _M + "TestServedCliFlags::test_flag_values_are_carried_as_data",
            "test/test_security_surface.py::TestServeBindsLoopbackByDefault::test_the_generated_app_binds_loopback_by_default",
        ],
        "exhaustion": [
            _M + "TestServedCliFlags::test_a_five_thousand_digit_limit_is_refused_quickly",
            "test/test_render_cli_port.py::TestPortReachesTheGeneratedApp::test_an_out_of_range_port_is_clamped_not_embedded_raw",
        ],
    },
    # dash_render.py's own command line (--spec --data --output --mode
    # --port --timeout --launch).
    "renderer_cli": {
        "bypass": [
            _M + "TestRendererOutputPath::test_a_hostile_output_path_is_refused",
        ],
        "injection": [
            _M + "TestRendererOutputPath::test_the_launcher_runs_the_app_without_a_shell",
            _M + "TestRendererOutputPath::test_main_refuses_before_it_writes",
        ],
        "exhaustion": [
            _M + "TestRendererOutputPath::test_a_megabyte_path_is_judged_in_linear_time",
            "test/test_render_cli_port.py::TestPortReachesTheGeneratedApp::test_an_out_of_range_port_is_clamped_not_embedded_raw",
        ],
    },
    # The CSV download (WP-21, `dash build, csv'): what a viewer's click
    # makes the page or the server write, and where it lands -- in a
    # spreadsheet.
    "csv_download": {
        "bypass": [
            "test/test_export.py::TestTheButtonIsThereWhenAsked::test_the_served_app_has_it_only_with_csv",
            "test/test_export.py::TestTheFileHoldsTheFilteredRows::test_the_modes_agree_on_every_filter_state",
            "test_export.cscript:EXP-06",
        ],
        "injection": [
            "test/test_export.py::TestTheCsvFormatter::test_a_text_cell_that_a_spreadsheet_would_run_is_defused",
            "test/test_export.py::TestTheCsvFormatter::test_a_label_that_a_spreadsheet_would_run_is_defused",
            "test/test_export.py::TestTheCsvFormatter::test_rfc_4180_quoting",
        ],
        "exhaustion": [
            "test/test_export.py::TestTheServedDownload::test_a_burst_of_clicks_is_held_to_the_bucket",
        ],
    },
}

_CATEGORIES = ("bypass", "injection", "exhaustion")

# The surfaces ROADMAP WP-20 AC-20.3 was scoped against; the registry may
# name more, never fewer.
_REQUIRED_SURFACES = frozenset({
    "plot_varlist_and_type", "if_in_qualifiers", "numeric_plot_options",
    "style_plot_options", "text_plot_options", "graph_text_options",
    "axis_label_options", "by_option", "name_option", "saving_path",
    "scheme_and_theme", "kpi", "build_options", "serve_options",
    "resource_limit_globals", "dash_setup_inputs", "data_content",
    "renderer_spec_and_data_json", "served_health_endpoint",
    "served_session_creation", "served_widget_model_changes",
    "served_app_cli_flags", "csv_download",
})

_PYTEST_ID = re.compile(r"^test/test_\w+\.py::(?:\w+::)?test_\w+$")
_CSCRIPT_ID = re.compile(r"^(test_\w+\.cscript):([A-Za-z0-9]+-[A-Za-z0-9]+)$")


def _entries():
    for surface, cats in SURFACES.items():
        for cat, ids in cats.items():
            for nid in ids:
                yield surface, cat, nid


def _pytest_entries():
    return sorted({nid for _s, _c, nid in _entries() if "::" in nid})


def _cscript_entries():
    return sorted({nid for _s, _c, nid in _entries() if "::" not in nid})


# ===========================================================================
# 2. The meta-tests
# ===========================================================================

@pytest.fixture(scope="session")
def collected_ids():
    """Every node id pytest collects from the files the registry names.

    One ``pytest --collect-only`` subprocess per session.  Collection runs
    no test and takes no suite lock.  ``-n 0`` keeps a config that turns on
    xdist by default from spreading a collection over workers; the rootdir is
    pinned so node ids read ``test/test_x.py::...`` however pytest is run.
    """
    files = sorted({nid.split("::", 1)[0] for nid in _pytest_entries()})
    cmd = [sys.executable, "-m", "pytest", "--collect-only", "-q",
           "-p", "no:cacheprovider", "--rootdir", _ROOT]
    try:
        import xdist  # noqa: F401
        cmd += ["-n", "0"]
    except ImportError:
        pass
    cmd += files
    proc = subprocess.run(cmd, cwd=_ROOT, capture_output=True, text=True,
                          timeout=900)
    ids = set()
    for line in proc.stdout.splitlines():
        line = line.strip()
        if "::" in line and line.startswith("test/"):
            ids.add(re.sub(r"\[.*\]$", "", line))
    return types.SimpleNamespace(ids=ids, proc=proc, files=files)


_DISPLAY_LINE = (r'^[ \t]*(?:(?:capture|cap|noisily|noi|quietly|qui)[ \t]+)*'
                 r'di(?:s(?:p(?:l(?:a(?:y)?)?)?)?)?[ \t]+'
                 r'(?:as[ \t]+\w+[ \t]+)?`?"')


def _script_displays_case(text, case_id):
    """True when *text* has a display line whose string starts with the case
    id followed by " PASS" or by a space."""
    pat = re.compile(_DISPLAY_LINE + re.escape(case_id) + r'(?: PASS|[ \t])',
                     re.M)
    return pat.search(text) is not None


class TestTheMatrixIsComplete:
    """The registry names a real test for every category of every surface."""

    def test_every_required_surface_is_registered(self):
        missing = sorted(_REQUIRED_SURFACES - set(SURFACES))
        assert not missing, f"surfaces with no entry: {missing}"

    def test_every_surface_has_an_entry_in_each_category(self):
        gaps = [(s, c) for s, cats in SURFACES.items() for c in _CATEGORIES
                if not cats.get(c)]
        assert not gaps, f"surface/category pairs with no test: {gaps}"
        extra = [(s, c) for s, cats in SURFACES.items() for c in cats
                 if c not in _CATEGORIES]
        assert not extra, f"unknown categories: {extra}"

    def test_every_entry_is_a_node_id_or_a_cscript_case(self):
        bad = [nid for _s, _c, nid in _entries()
               if not (_PYTEST_ID.match(nid) or _CSCRIPT_ID.match(nid))]
        assert not bad, f"malformed registry entries: {bad}"

    def test_every_pytest_entry_is_collected(self, collected_ids):
        assert collected_ids.proc.returncode == 0, (
            "pytest --collect-only failed on the registry's files:\n"
            + collected_ids.proc.stdout[-3000:]
            + collected_ids.proc.stderr[-3000:])
        missing = [nid for nid in _pytest_entries()
                   if nid not in collected_ids.ids]
        assert not missing, (
            f"registry names tests pytest does not collect: {missing}")

    def test_every_cscript_entry_is_displayed_as_a_case(self):
        missing = []
        texts = {}
        for entry in _cscript_entries():
            script, case_id = _CSCRIPT_ID.match(entry).groups()
            path = os.path.join(_HERE, script)
            if script not in texts:
                assert os.path.isfile(path), f"no such script: {script}"
                with open(path, encoding="utf-8") as fh:
                    texts[script] = fh.read()
            if not _script_displays_case(texts[script], case_id):
                missing.append(entry)
        assert not missing, (
            f"registry names cscript cases their scripts never display as "
            f"'<id> PASS': {missing}")

    def test_the_case_detector_reads_display_lines_only(self):
        text = ('display "P9-01 PASS: x"\n'
                'display `"P9-13 PASS: y"\'\n'
                '// display "P7-01 PASS: in a comment"\n'
                'display "  P19-17..21: a summary line"\n'
                'display "P9-05 NOTE: not probed"\n'
                'local s "P8-01 PASS"\n')
        assert _script_displays_case(text, "P9-01")
        assert _script_displays_case(text, "P9-13")
        assert _script_displays_case(text, "P9-05")
        assert not _script_displays_case(text, "P7-01")
        assert not _script_displays_case(text, "P19-17")
        assert not _script_displays_case(text, "P8-01")
        assert not _script_displays_case(text, "P9-0")


# ===========================================================================
# 3. Shared helpers for the gap tests
# ===========================================================================

_DF = pd.DataFrame({
    "mpg": [22.0, 17.0, 25.0, 30.0, 21.0, 19.0, 14.0, 28.0, 16.0, 23.0],
    "weight": [2930.0, 3350.0, 2200.0, 1800.0, 3000.0, 3100.0, 4080.0,
               2010.0, 3600.0, 2650.0],
    "foreign": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    "price": [4099.0, 4749.0, 3799.0, 4816.0, 5788.0, 4453.0, 5189.0,
              10372.0, 4082.0, 11385.0],
})
_SCATTER = {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {}}
_SCATTER2 = {"type": "scatter", "yvar": "price", "xvar": "weight",
             "options": {}}


def _kpi(update="both", if_expr=""):
    return {"name": "k1", "stat": "mean", "var": "mpg", "fmt": "%9.2f",
            "title": "Mean mpg", "subtitle": "", "color": "", "bgcolor": "",
            "update": update, "if_expr": if_expr, "in_expr": ""}


def _write_inputs(tmp_path, spec, df=_DF):
    sp = os.path.join(str(tmp_path), "spec.json")
    dp = os.path.join(str(tmp_path), "data.json")
    with open(sp, "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    with open(dp, "w", encoding="utf-8") as fh:
        json.dump(make_data_json(df), fh)
    return sp, dp


def _render(tmp_path, spec, df=_DF):
    """(html, warning texts) for *spec* through the saved renderer."""
    sp, dp = _write_inputs(tmp_path, spec, df)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        html = dr.DashRenderer(sp, dp).render()
    return html, [str(x.message) for x in w]


def _app_source(tmp_path, spec, df=_DF):
    """The generated server app's source for *spec*."""
    sp, dp = _write_inputs(tmp_path, spec, df)
    op = os.path.join(str(tmp_path), "app.py")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        dr.ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        return fh.read()


_CURDOC_ATTACH = "if __name__ != '__main__':\n    make_document(curdoc())"


def _load_app(src, tag):
    """The generated app as a namespace, with everything it defines --
    make_document, the limiters, _HealthHandler, the launcher's parser and
    _dash_server_app -- and without attaching a document to curdoc() or
    running the launcher."""
    assert _CURDOC_ATTACH in src, "the generated app's curdoc attach moved"
    ns = {"__name__": "dash_matrix_app_%s" % tag}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(src.replace(_CURDOC_ATTACH, "pass"),
                     "dash_matrix_app_%s.py" % tag, "exec"), ns)
    return ns


@pytest.fixture(scope="module")
def served_app(tmp_path_factory):
    """One generated app: a scatter, a dropdown and a range filter, and a
    KPI that follows both filters and the brush."""
    tmp = tmp_path_factory.mktemp("matrix_app")
    spec = make_spec([dict(_SCATTER)],
                     filters=[{"varname": "foreign", "type": "dropdown"},
                              {"varname": "price", "type": "range"}],
                     kpis=[_kpi("both")])
    return _load_app(_app_source(tmp, spec), "main")


class _Req:
    def __init__(self, remote_ip="10.0.0.1", **headers):
        self.remote_ip = remote_ip
        self.headers = headers


class _SessionDoc(Document):
    """A Document with a session context carrying *request*, as Bokeh gives
    make_document one; a subclass, so Document itself is never patched."""

    def __init__(self, request):
        super().__init__()
        self._matrix_request = request

    @property
    def session_context(self):
        return types.SimpleNamespace(request=self._matrix_request)


def _session(ns, request=None):
    doc = _SessionDoc(request) if request is not None else Document()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        ns["make_document"](doc)
    return doc


def _texts(doc):
    return " ".join(d.text for d in doc.select({"type": Div}))


def _unthrottled(model, attr):
    """The callback registered for *attr* on *model*, unwrapped from the
    event throttle so a test drives the recompute directly."""
    cbs = model._callbacks.get(attr, [])
    assert cbs, f"no callback on {type(model).__name__}.{attr}"
    return cbs[0]


# ===========================================================================
# 4. if / in qualifiers
# ===========================================================================

class TestIfQualifierExhaustion:
    """A short qualifier recursed past Python's limit.

    Measured 23sep2026 at e932446: ``if !!!...(mpg > 1)`` with about 490 !s
    (497 characters) made pandas' evaluator raise RecursionError, which
    neither ``_validate_if_expr`` (it caught SyntaxError only) nor
    ``_dash_qualified_frame`` caught -- r(7102) and a traceback on the
    immediate route and on ``dash build``, and in every served session.  A
    qualifier that cannot be applied is now reported and skipped, the rule
    the file already had for one that fails the whitelist.
    """

    @staticmethod
    def _apply(fn, expr, in_expr=""):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t0 = time.monotonic()
            out = fn(_DF, expr, in_expr, where="t")
            took = time.monotonic() - t0
        return out, [str(x.message) for x in w], took

    def test_a_run_of_negations_is_skipped_not_raised(self):
        out, msgs, took = self._apply(dr._dash_qualified_frame,
                                      "!" * 600 + "(mpg > 1)")
        assert len(out) == len(_DF)
        assert any("if_expr filter skipped" in m for m in msgs), msgs
        assert took < 10

    @pytest.mark.parametrize("expr", [
        " & ".join(["(mpg > 1)"] * 600),
        "inlist(mpg," + ",".join(str(i) for i in range(600)) + ")",
        "~" * 50000 + "mpg",
    ])
    def test_other_deep_shapes_are_skipped_not_raised(self, expr):
        out, msgs, took = self._apply(dr._dash_qualified_frame, expr)
        assert len(out) == len(_DF)
        assert any("if_expr filter skipped" in m for m in msgs), msgs
        assert took < 20

    def test_the_whitelist_answers_false_rather_than_raising(self):
        assert dr._validate_if_expr("~" * 5000 + "(mpg > 1)", ["mpg"]) is False
        assert dr._validate_if_expr("~" * 50000 + "mpg", ["mpg"]) is False

    def test_an_in_range_too_long_for_int_is_read_not_raised(self):
        out, _msgs, _took = self._apply(dr._dash_qualified_frame, "",
                                        "2/" + "9" * 5000)
        assert len(out) == len(_DF) - 1
        out, _msgs, _took = self._apply(dr._dash_qualified_frame, "",
                                        "9" * 5000 + "/3")
        assert len(out) == 0

    def test_an_ordinary_qualifier_still_filters(self):
        out, msgs, _took = self._apply(dr._dash_qualified_frame, "mpg > 20")
        assert len(out) == int((_DF["mpg"] > 20).sum())
        assert not any("skipped" in m for m in msgs)

    def test_the_saved_render_survives_it(self, tmp_path):
        spec = make_spec([dict(_SCATTER)], kpis=[
            _kpi("filter", if_expr="!" * 600 + "(mpg > 1)")])
        spec["graphs"][0]["if_expr"] = "!" * 600 + "(mpg > 1)"
        html, msgs = _render(tmp_path, spec)
        assert "<html" in html.lower()
        assert any("if_expr filter skipped" in m for m in msgs), msgs

    def test_the_served_app_has_the_same_bound(self, served_app):
        out, msgs, took = self._apply(served_app["_dash_qualified_frame"],
                                      "!" * 600 + "(mpg > 1)")
        assert len(out) == len(_DF)
        assert any("if_expr filter skipped" in m for m in msgs), msgs
        assert served_app["_validate_if_expr"]("~" * 50000 + "mpg",
                                               ["mpg"]) is False


class TestIfQualifierEncodings:
    """Homoglyph, NUL and look-alike spellings of what the whitelist refuses.

    Python folds identifiers to NFKC before parsing, so a full-width or
    mathematical-alphabet spelling of ``__import__`` or ``eval`` IS that
    name to the parser.  The whitelist walks the parsed tree, so it sees the
    folded name -- these pin that it keeps doing so, and that the pandas
    evaluator never receives any of them.
    """

    @pytest.mark.parametrize("expr", [
        "\uff4d\uff50\uff47.__class__",                       # full-width mpg
        "mpg > 1 | \uff3f\uff3fimport\uff3f\uff3f('os')",      # full-width _
        "\U0001d41e\U0001d42f\U0001d41a\U0001d425('1')",       # bold eval
        "mpg > 1 | \U0001d4ee\U0001d501\U0001d4ee\U0001d4ec('x')",  # script exec
        "mpg == 1\x00 | __import__('os')",                     # NUL
        "mpg > 1 & (lambda: 0)()",
        "mpg > 1 & @mpg",
        "mpg.__class__.__mro__",
        "mpg > 1 & \u0435val('1')",                            # Cyrillic e
    ])
    def test_the_spelling_does_not_get_past_the_whitelist(self, expr):
        assert dr._validate_if_expr(dr._stata_if_to_pandas(expr),
                                    ["mpg"]) is False
        called = []
        real_query = pd.DataFrame.query

        def _spy(self, *a, **k):
            called.append(a)
            return real_query(self, *a, **k)

        pd.DataFrame.query = _spy
        try:
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                out = dr._dash_qualified_frame(_DF, expr, "", where="t")
        finally:
            pd.DataFrame.query = real_query
        assert not called, f"pandas.query was handed {expr!r}"
        assert len(out) == len(_DF)
        assert any("skipped" in str(x.message) for x in w)

    def test_a_folded_spelling_of_a_real_column_is_that_column(self):
        # Not a bypass: NFKC makes it the column itself, which is allowed.
        out = dr._dash_qualified_frame(_DF, "\uff4d\uff50\uff47 > 20", "")
        assert len(out) == int((_DF["mpg"] > 20).sum())


# ===========================================================================
# 5. A `function' plot's expression
# ===========================================================================

class TestFunctionExpressionEncodings:
    """The function-plot whitelist against the same folded spellings."""

    @pytest.mark.parametrize("expr", [
        "\uff45\uff58\uff45\uff43('import os')",               # full-width exec
        "\U0001d41e\U0001d42f\U0001d41a\U0001d425('1')",       # bold eval
        "x + \uff3f\uff3fimport\uff3f\uff3f('os').getpid()",
        "\uff53\uff49\uff4e(x).__class__",                     # folded sin, attr
        "sin(x)\x00 + __import__('os')",
        "\u0435xp(x)",                                          # Cyrillic e
    ])
    def test_the_layer_draws_nothing(self, gm, fig, expr):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = gm.map_function(fig, expr, (0, 1), 10, {})
        assert len(result[0].data_source.data["x_fn"]) == 0

    def test_a_folded_spelling_of_an_allowed_function_still_draws(self, gm,
                                                                   fig):
        # NFKC folds \uff53\uff49\uff4e to sin, which is allowed: harmless.
        result = gm.map_function(fig, "\uff53\uff49\uff4e(x)", (0, 1), 10, {})
        assert len(result[0].data_source.data["x_fn"]) == 10


# ===========================================================================
# 6. Scheme files and #include
# ===========================================================================

class TestSchemeIncludes:
    """``#include`` inside a .scheme file.

    None of the twenty shipped schemes has an ``#include`` line, and the one
    earlier cycle test wrote its files without changing directory, so its
    include never resolved and the cycle guard was never reached.  These
    run in the working directory, where dash reads custom schemes.
    """

    def test_include_cycles_terminate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "selfinc.scheme").write_text(
            "#include selfinc\ncolor background white\n")
        (tmp_path / "ma.scheme").write_text(
            "#include mb\ncolor background white\n")
        (tmp_path / "mb.scheme").write_text(
            "#include ma\ncolor foreground black\n")
        t0 = time.monotonic()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p1 = dr.SchemeParser("selfinc")
            p2 = dr.SchemeParser("ma")
        assert time.monotonic() - t0 < 5
        assert p1._props.get("color background") == "white"
        # Both files of the cycle were read: the include DID resolve.
        assert p2._props.get("color background") == "white"
        assert p2._props.get("color foreground") == "black"

    def test_a_deep_include_chain_does_not_exhaust_the_stack(self, tmp_path,
                                                            monkeypatch):
        """Measured 23sep2026: a chain of 1,500 distinct files raised
        RecursionError out of SchemeParser, and resolve_or_fallback catches
        only ValueError and OSError, so the render died with a traceback."""
        monkeypatch.chdir(tmp_path)
        n = 1500
        for i in range(n):
            nxt = ("#include c%d\n" % (i + 1)) if i < n - 1 else ""
            (tmp_path / ("c%d.scheme" % i)).write_text(
                nxt + "color c%d #%06x\n" % (i, i))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            p = dr.SchemeParser("c0")
            q = dr.SchemeParser.resolve_or_fallback("c0", "a test")
        assert p._props.get("color c0") == "#000000"
        assert "color c%d" % (n - 1) not in p._props
        assert q._props.get("color c0") == "#000000"
        msgs = [str(x.message) for x in w]
        assert any("#include" in m and
                   str(dr._MAX_SCHEME_INCLUDE_DEPTH) in m for m in msgs), msgs

    def test_a_chain_within_the_depth_is_read_whole(self, tmp_path,
                                                    monkeypatch):
        monkeypatch.chdir(tmp_path)
        n = dr._MAX_SCHEME_INCLUDE_DEPTH
        for i in range(n):
            nxt = ("#include d%d\n" % (i + 1)) if i < n - 1 else ""
            (tmp_path / ("d%d.scheme" % i)).write_text(
                nxt + "color d%d #%06x\n" % (i, i))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            p = dr.SchemeParser("d0")
        assert all("color d%d" % i in p._props for i in range(n))
        assert not any("#include" in str(x.message) for x in w)

    def test_an_include_that_leaves_the_allowed_directories_is_not_read(
            self, tmp_path, monkeypatch):
        inside = tmp_path / "inside"
        outside = tmp_path / "outside"
        inside.mkdir()
        outside.mkdir()
        secret = outside / "secret.scheme"
        secret.write_text("color heading #5ec2e7\n")
        (inside / "link.scheme").symlink_to(secret)
        monkeypatch.chdir(inside)
        for spelling in ("../outside/secret.scheme", str(secret),
                         "link", "link.scheme",
                         "..%s..%soutside%ssecret.scheme" % (os.sep, os.sep,
                                                             os.sep)):
            (inside / "evil.scheme").write_text(
                "#include %s\ncolor foreground black\n" % spelling)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                p = dr.SchemeParser("evil")
            assert p._props.get("color heading") != "#5ec2e7", spelling
            assert p._props.get("color foreground") == "black"

    def test_scheme_values_reach_the_served_app_only_as_data(self, tmp_path,
                                                            monkeypatch):
        """The scheme travels into the generated app as ``repr`` of its
        property dict: a value carrying Python, JavaScript or a quote must
        come out as a string literal and nothing else."""
        monkeypatch.chdir(tmp_path)
        payload = "x'];__import__('os').system('touch_pwned')#"
        (tmp_path / "hostile.scheme").write_text(
            "#include s2color\n"
            "color background %s\n"
            "color heading \"</script><script>alert(1)</script>\n" % payload)
        spec = make_spec([dict(_SCATTER)])
        spec["build_options"]["scheme"] = "hostile"
        src = _app_source(tmp_path, spec)
        ast.parse(src)
        code_only = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                code_only.append(tok.string)
        code = " ".join(code_only)
        assert "touch_pwned" not in code
        assert "__import__('os')" not in code
        assert payload in src  # carried, as a literal
        assert not (tmp_path / "touch_pwned").exists()


# ===========================================================================
# 7. Axis labels
# ===========================================================================

class TestAxisLabelBounds:
    """``xlabel()``/``ylabel()`` are not in dash.ado's validation table, so
    the renderer's parser is the only guard.  Measured 23sep2026: the
    ``a(b)c`` form expanded every tick into a Python list -- 10**7 ticks took
    0.8 s and 1 GB, and ``xlabel(0(0.000001)1000000)`` (10**12) could not
    finish; ``xlabel(1e400(1)1e400)`` and a 5,000-digit ``#N`` raised
    ValueError out of the render.  twoway draws all three without error."""

    @staticmethod
    def _parse(raw):
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            t0 = time.monotonic()
            spec = dr._dash_parse_axis_spec(raw)
            took = time.monotonic() - t0
        return spec, [str(x.message) for x in w], took

    def test_an_increment_past_the_tick_limit_keeps_the_default_ticks(self):
        spec, msgs, took = self._parse("0(0.000001)1000000")
        assert took < 2
        assert spec["mode"] == "default" and spec["ticks"] == []
        assert any(f"{dr._MAX_AXIS_TICKS:,}" in m for m in msgs), msgs

    def test_several_increments_are_held_to_the_limit_together(self):
        half = dr._MAX_AXIS_TICKS // 2
        spec, msgs, took = self._parse(
            "0(1)%d %d(1)%d" % (half, half + 1, 3 * half))
        assert took < 2
        assert len(spec["ticks"]) <= dr._MAX_AXIS_TICKS
        assert any(f"{dr._MAX_AXIS_TICKS:,}" in m for m in msgs), msgs

    def test_a_limit_sized_increment_still_draws(self):
        spec, msgs, _took = self._parse("0(1)1000")
        assert spec["mode"] == "explicit" and len(spec["ticks"]) == 1001
        assert not msgs

    @pytest.mark.parametrize("raw", ["1e400(1)1e400", "0(1)1e400",
                                     "-1e400(1)0", "0(1e400)10"])
    def test_a_non_finite_endpoint_does_not_raise(self, raw):
        spec, _msgs, took = self._parse(raw)
        assert took < 2
        assert len(spec["ticks"]) <= dr._MAX_AXIS_TICKS

    def test_a_huge_count_is_clamped(self):
        spec, _msgs, _took = self._parse("#999999999999")
        assert spec["mode"] == "count"
        assert spec["count"] == dr._MAX_AXIS_TICKS
        spec, _msgs, took = self._parse("#" + "9" * 5000)
        assert took < 2
        assert spec["count"] == dr._MAX_AXIS_TICKS

    def test_an_ordinary_count_is_kept(self):
        spec, _msgs, _took = self._parse("#5")
        assert spec["count"] == 5

    def test_both_modes_share_the_bound(self, served_app):
        spec = served_app["_dash_parse_axis_spec"]("0(0.000001)1000000")
        assert spec["mode"] == "default" and spec["ticks"] == []
        assert served_app["_MAX_AXIS_TICKS"] == dr._MAX_AXIS_TICKS

    def test_a_saved_render_with_the_increment_completes(self, tmp_path):
        spec = make_spec([dict(_SCATTER)])
        spec["graphs"][0]["graph_options"]["xlabel"] = "0(0.000001)1000000"
        t0 = time.monotonic()
        html, msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        assert "<html" in html.lower()
        assert any(f"{dr._MAX_AXIS_TICKS:,}" in m for m in msgs), msgs


class TestAxisLabelInjection:
    """Tick-label text reaches the page as DATA: the CustomJSTickFormatter's
    code is fixed text, and the labels travel in its ``args`` as one JSON
    string the code parses.  (They used to be html-escaped into the code
    itself; WP-20's sink work moved them out, and a tick label is canvas
    text, so it is carried raw -- see test_label_sinks.py.)"""

    @staticmethod
    def _formatter(raw):
        fig = figure()
        spec = dr._dash_parse_axis_spec(raw)
        dr._dash_apply_axis_spec(fig.xaxis, fig.xgrid, spec)
        fmt = fig.xaxis[0].formatter
        return fmt.code, json.loads(fmt.args["labels"])

    def test_a_tick_label_cannot_break_out_of_the_formatter_code(self):
        payload = ('1 "</script><script>alert(1)</script>" '
                   '2 "x\u2028y" 3 "a`${alert(3)}`"')
        code, labels = self._formatter(payload)
        # The code is the fixed parser: no label text reaches it at all.
        assert code == ("const m = JSON.parse(labels); "
                        "return m[String(tick)] || String(tick);")
        assert "alert" not in code and "<" not in code and "`" not in code
        # The labels arrive whole, as the text the user wrote.
        assert labels["1.0"] == "</script><script>alert(1)</script>"
        assert "`${alert(3)}`" in labels["3.0"]

    def test_pre_escaped_markup_is_carried_as_written_not_decoded(self):
        _code, labels = self._formatter('1 "&lt;script&gt;" 2 "x"')
        # Neither decoded into markup nor escaped a second time: the canvas
        # draws exactly what was written.
        assert labels["1.0"] == "&lt;script&gt;"


# ===========================================================================
# 8. Numeric display formats
# ===========================================================================

class TestNumericFormatBounds:
    """A Stata numeric format has a width of at most 2,045 and fewer
    decimals than its width -- measured with ``confirm numeric format``:
    %2045.2f and %1000.999f pass, %2046.2f, %9.30f and %9.300f do not.
    The renderer reproduced any ``%w.df`` it was handed, so
    ``xlabel(, format(%9.999999999f))`` -- which dash.ado does not check --
    built a pattern of a billion zeros, and a hand-edited KPI ``fmt`` of the
    same made a 1 GB card (measured: 1,000,000,001 characters in 0.8 s)."""

    @pytest.mark.parametrize("fmt", ["%9.999999999f", "%2046.2f", "%9.30f",
                                     "%9.300f", "%99999999999.2f",
                                     "%1" + "0" * 5000 + ".2f"])
    def test_a_format_stata_refuses_is_not_reproduced(self, fmt):
        t0 = time.monotonic()
        assert dr._parse_stata_numeric_fmt(fmt) is None
        assert dr._stata_numeric_pattern(fmt) is None
        assert len(dr._format_stata_numeric(1.5, fmt)) < 64
        assert time.monotonic() - t0 < 1

    @pytest.mark.parametrize("fmt,want", [
        ("%9.2f", (9, 2, "f", False)),
        ("%12.0fc", (12, 0, "f", True)),
        ("%-12.3e", (12, 3, "e", False)),
        ("%2045.2044f", (2045, 2044, "f", False)),
    ])
    def test_the_formats_stata_accepts_still_parse(self, fmt, want):
        assert dr._parse_stata_numeric_fmt(fmt) == want

    def test_an_axis_format_with_a_billion_decimals_is_bounded(self):
        fig = figure()
        t0 = time.monotonic()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            spec = dr._dash_parse_axis_spec("0(1)10, format(%9.999999999f)")
            dr._dash_apply_axis_spec(fig.xaxis, fig.xgrid, spec)
        assert time.monotonic() - t0 < 2
        fmt = fig.xaxis[0].formatter
        assert len(getattr(fmt, "format", "") or "") < 5000

    def test_a_hand_edited_kpi_format_is_bounded(self):
        t0 = time.monotonic()
        out = dr._dash_format_kpi_value(1.5, "%9.999999999f")
        assert time.monotonic() - t0 < 1
        assert len(out) < 64
        assert dr._dash_format_kpi_value(1.5, "%9.2f") == "1.50"
        assert dr._dash_format_kpi_value(1234.5, "%12.1fc") == "1,234.5"


# ===========================================================================
# 9. layout() grid size
# ===========================================================================

def _two_graph_spec(layout, limits=None):
    g2 = {"plots": [dict(_SCATTER2)], "graph_options": {"name": "g2"},
          "if_expr": "", "in_expr": ""}
    spec = make_spec([dict(_SCATTER)], extra_graphs=[g2])
    spec["build_options"]["registry"] = "g1 g2"
    spec["build_options"]["layout"] = layout
    if limits:
        spec["build_options"]["limits"] = limits
    return spec


class TestLayoutGridBound:
    """The saved page pads its grid to rows x cols cells.  Measured 23sep2026:
    a 4000 x 4000 grid of two graphs peaked at 1.5 GB, growing with the
    cells, so layout(99999 99999) could not finish; the served template pads
    the same way on every session.  No grid needs more cells than a
    dashboard can hold graphs and KPI cards, so ``_dash_cap_spec`` -- which
    both renderers apply before anything else reads the spec -- draws a grid
    larger than the graphs limit as layout(auto)."""

    @staticmethod
    def _capped(spec):
        limits = dr._dash_limits(spec["build_options"])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, limits)
        return out["build_options"]["layout"], [str(x.message) for x in w]

    @pytest.mark.parametrize("layout", [
        "99999 99999", "10 11", "1 101",
        "g1:1,1 g2:99999,99999", "g1:1,1 g2:11,10", "g1:0,0 g2:0,100",
    ])
    def test_an_oversized_grid_is_drawn_as_auto(self, layout):
        got, msgs = self._capped(_two_graph_spec(layout))
        assert got == "auto"
        assert any("dash_max_graphs" in m for m in msgs), msgs

    def test_a_placement_index_too_long_for_int_does_not_raise(self):
        got, msgs = self._capped(_two_graph_spec("g1:1,1 g2:1," + "9" * 5000))
        assert got == "auto"
        assert msgs

    @pytest.mark.parametrize("layout", ["10 10", "2 3", "auto", "bs",
                                        "bs: g1=6 g2=6", "g1:1,1 g2:10,10",
                                        "g1:0,0 g2:9,9"])
    def test_a_grid_within_the_limit_is_kept(self, layout):
        got, msgs = self._capped(_two_graph_spec(layout))
        assert got == layout
        assert not any("dash_max_graphs" in m for m in msgs), msgs

    def test_the_bound_is_the_graphs_limit(self):
        got, _msgs = self._capped(_two_graph_spec("10 20", {"graphs": 200}))
        assert got == "10 20"
        got, _msgs = self._capped(_two_graph_spec("10 21", {"graphs": 200}))
        assert got == "auto"

    # int() reads 1_000, +5 and full-width digits, and str.split() splits at
    # an ideographic space.  The cell count read none of them, so such a grid
    # was measured as no grid at all and then built at full size by both
    # grid readers: layout(1_000 1_000) of two graphs was a 1,000 x 1,000
    # grid in the saved page and the served app.
    _LAX = ["1_000 1_000", "+99999 +99999", "1_0 1",
            "１０００ １０００",
            "1000　1000", "1000  1000"]

    @pytest.mark.parametrize("layout", _LAX)
    def test_a_grid_only_int_can_read_is_no_grid(self, layout):
        assert dr._dash_grid_dims(layout) is None
        assert dr._dash_layout_cells(layout) is None

    @pytest.mark.parametrize("layout", _LAX)
    def test_the_saved_page_draws_it_as_auto(self, layout, tmp_path):
        sp, dp = _write_inputs(tmp_path, _two_graph_spec(layout))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
        names = ["g1", "g2"]
        assert r._compute_grid(names, layout) == r._compute_grid(names, "auto")

    def test_the_served_app_reads_the_grid_with_the_same_rule(self, tmp_path):
        src = _app_source(tmp_path, _two_graph_spec("2 1"))
        assert "_dash_grid_dims(layout_opt)" in src
        assert "int(parts[0])" not in src

    @pytest.mark.parametrize("layout,dims", [
        ("2 3", (2, 3)), ("  2 \t 3 ", (2, 3)), ("0 5", (1, 5)),
        ("999999999 1", (999999999, 1)), ("1234567890 1", None),
        ("2 3 4", None), ("2", None), ("auto", None), ("bs", None),
        ("g1:1,1", None), ("", None), (None, None)])
    def test_grid_dims(self, layout, dims):
        assert dr._dash_grid_dims(layout) == dims

    @pytest.mark.parametrize("layout", [
        "2 3", "0 5", "10 10", "g1:1,1 g2:3,4", "g1:0,0 g2:0,1",
        "999999999 1", "1234567890 1"] + _LAX)
    def test_the_measure_is_never_smaller_than_the_grid(self, layout):
        """Whatever the grid reader builds, the cell count measured first."""
        dims = dr._dash_grid_dims(layout)
        if dims is not None:
            cells = dr._dash_layout_cells(layout)
            assert cells is not None and cells >= dims[0] * dims[1]

    def test_both_modes_are_bounded(self, tmp_path):
        spec = _two_graph_spec("99999 99999")
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            saved = dr.DashRenderer(sp, dp)
            served = dr.ServerAppBuilder(sp, dp)
            t0 = time.monotonic()
            html = saved.render()
        assert time.monotonic() - t0 < 30
        assert "<html" in html.lower()
        assert saved.master_spec["build_options"]["layout"] == "auto"
        assert served.spec["build_options"]["layout"] == "auto"
        assert json.loads(served._spec_str)["build_options"]["layout"] == "auto"


class TestALayoutThatCannotBeReadIsReported:
    """layout() was accepted or dropped in silence.  Measured at f2ecdd4 in
    both modes: layout(g1:1,1\\), layout(g1:1,1 junk), layout(3 4 5) and
    layout(g1:1,1,g2:1,2) were drawn as layout(auto) with no word; a
    placement naming no registered item made the modes disagree --
    layout(nosuch:1,1) was a 3 x 1 grid, the two graphs stacked above an
    empty cell, when saved and 1 x 2 when served; and layout(bs: ...)
    dropped an unknown
    name and clamped a span of 99 to 12 without saying so.  dash.ado now
    refuses each of these (P20-30); for a spec that did not come through it,
    ``_dash_cap_spec`` -- which both modes apply first -- reports each
    problem once, draws an unreadable layout as auto, and leaves an unknown
    placement out, so both modes draw the same grid."""

    @staticmethod
    def _capped(layout):
        spec = _two_graph_spec(layout)
        limits = dr._dash_limits(spec["build_options"])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, limits)
        msgs = [str(x.message) for x in w if "layout(" in str(x.message)]
        return out["build_options"]["layout"], msgs

    @pytest.mark.parametrize("layout", [
        "g1:1,1\\", "g1:1,1 junk", "3 4 5", "g1:1,1,g2:1,2", "2",
        "g1:1,", "１ ２", "g1 : 1 , 1 ;"])
    def test_an_unreadable_layout_is_drawn_as_auto_and_said(self, layout):
        got, msgs = self._capped(layout)
        assert got == "auto"
        assert len(msgs) == 1, msgs
        assert "drawn as layout(auto)" in msgs[0], msgs

    @pytest.mark.parametrize("layout,kept,unknown", [
        ("nosuch:1,1", "auto", "nosuch"),
        ("g1:1,1 nosuch:2,2", "g1:1,1", "nosuch"),
        ("g1:2,1 k9:1,1 g2:1,1", "g1:2,1 g2:1,1", "k9"),
    ])
    def test_an_unknown_placement_is_left_out_and_named(self, layout, kept,
                                                        unknown):
        got, msgs = self._capped(layout)
        assert got == kept
        assert len(msgs) == 1 and unknown in msgs[0], msgs
        assert "not a registered graph or KPI card" in msgs[0], msgs

    @pytest.mark.parametrize("layout,needle", [
        ("bs: g1=6 nosuch=6", "nosuch"),
        ("bs: g1=99 g2=6", "99"),
        ("bs: g1=x g2=6", "'x'"),
        ("bs: g1= g2=6", "g1="),
        ("bs\\", "drawn as layout(bs)"),
        ("bsx", "drawn as layout(bs)"),
        ("bs:", "drawn as layout(bs)"),
    ])
    def test_a_bootstrap_spec_is_read_whole_or_said(self, layout, needle):
        got, msgs = self._capped(layout)
        assert len(msgs) == 1 and needle in msgs[0], msgs
        assert dr.DashRenderer._is_bootstrap_layout(got)

    @pytest.mark.parametrize("layout", [
        "auto", "", "2 1", " 2  1 ", "g1:1,2 g2:1,1", "g1:0,0 g2:0,1",
        "bs", "bs: g1=6 g2=6", "bs: g1 / g2=12", "BS: g1=12"])
    def test_a_readable_layout_is_kept_without_a_word(self, layout):
        got, msgs = self._capped(layout)
        assert got == layout
        assert msgs == []

    def test_an_item_the_graphs_limit_dropped_is_left_out_quietly(self):
        """The limit has already said it dropped the item; the layout must
        not call a registered item unregistered."""
        assert dr._dash_layout_check("g1:1,1 g2:1,2", {"g1"},
                                     {"g1", "g2"}) == ("g1:1,1", None)
        assert dr._dash_layout_check("g2:1,1", {"g1"},
                                     {"g1", "g2"}) == ("auto", None)
        got, problem = dr._dash_layout_check("g2:1,1 zz:1,2", {"g1"},
                                             {"g1", "g2"})
        assert got == "auto"
        assert "zz is not a registered" in problem, problem
        assert "g2 is not" not in problem and "g2, zz" not in problem, problem
        spec = _two_graph_spec("g1:1,1 g2:1,2", {"graphs": 1})
        limits = dr._dash_limits(spec["build_options"])
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            out = dr._dash_cap_spec(spec, limits)
        msgs = [str(x.message) for x in w]
        assert out["build_options"]["layout"] == "g1:1,1"
        assert any("dash_max_graphs" in m for m in msgs), msgs
        assert not any("not a registered" in m for m in msgs), msgs

    def test_the_checks_read_what_their_readers_read(self):
        """Each form's check and its reader agree on the same values."""
        for layout in ("g1:1,1 g2:1,2", "g1:0,0", " 2  3 ", "bs",
                       "bs: g1=6 / g2"):
            assert dr._dash_layout_check(layout, {"g1", "g2"})[1] is None
        assert dr._dash_bs_layout_check("bs: g1=12", "bs: g1=12", {"g1"},
                                        "bs: g1=12") == ("bs: g1=12", None)
        got, problem = dr._dash_bs_layout_check(
            "bs: g1=12 g9", "bs: g1=12 g9", {"g1"}, "x")
        assert got == "bs: g1=12 g9" and "g9 is not a registered" in problem

    @pytest.mark.parametrize("layout", ["nosuch:1,1", "g1:1,1 nosuch:2,2",
                                        "g1:1,1 junk"])
    def test_both_modes_draw_the_same_grid(self, layout, tmp_path):
        spec = _two_graph_spec(layout)
        sp, dp = _write_inputs(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            saved = dr.DashRenderer(sp, dp)
            saved.render()
            src = _app_source(tmp_path, spec)
        rows, cols = saved._compute_grid(
            ["g1", "g2"], saved.master_spec["build_options"]["layout"])
        placed = dr._dash_placement_map(
            saved.master_spec["build_options"]["layout"], {"g1", "g2"})
        doc = _session(_load_app(src, "layout_parity"))
        from bokeh.models import GridPlot
        grids = list(doc.select({"type": GridPlot}))
        assert grids, "the served app drew no grid"
        served_cells = sorted((r, c) for _m, r, c in grids[0].children)
        # The saved page fills its grid in reading order after placing any
        # named item: the served app must put the two figures in the same
        # cells.
        free = [(r, c) for r in range(rows) for c in range(cols)
                if (r, c) not in placed.values()]
        saved_cells = sorted(list(placed.values())
                             + free[:2 - len(placed)])
        assert served_cells == saved_cells, (served_cells, saved_cells,
                                             (rows, cols))


class TestARepeatedLayoutNameIsPlacedOnce:
    """Found by WP-21, measured 23sep2026: a name repeated in layout(bs: ...)
    was placed once per repeat.  The saved page embedded the item again for
    every repeat, with the same element id -- 100,000 repeats made an 18.1 MB
    page, and dash.ado let it through -- and the served app read the whole
    spec on every session (a 4 MB spec: about 3 s and 300 MB each).  A
    placement repeated in layout(name:row,col ...) silently kept the LAST
    place.  Now the first place is kept in both forms and both modes, the
    renderer says so, and dash.ado refuses it (P20-31)."""

    def test_the_bs_reader_keeps_the_first_place(self):
        rows = dr._dash_parse_bs_layout("bs: g1=4 g1=8 g2=6 / g1=12",
                                        ["g1", "g2"], [])
        assert rows == [[("g1", 4), ("g2", 6)]]

    def test_the_saved_page_embeds_a_repeated_item_once(self, tmp_path):
        spec = _two_graph_spec("bs: " + "g1=6 " * 2000 + "g2=6")
        html, _msgs = _render(tmp_path, spec)
        # Each embedded root is one <div ... data-root-id=...>.
        assert html.count("data-root-id") <= 4
        assert len(html) < 5_000_000

    def test_the_served_grid_places_it_once(self, tmp_path):
        from bokeh.models import GridBox
        src = _app_source(tmp_path, _two_graph_spec("bs: g1=6 g1=6 g2=6"))
        doc = _session(_load_app(src, "bs_repeat"))
        cells = [c for gb in doc.select({"type": GridBox}) for c in gb.children]
        assert len(cells) == 2

    @pytest.mark.parametrize("layout,kept", [
        ("bs: g1=6 g1=6 g2=6", "bs: g1=6 g1=6 g2=6"),
        ("g1:1,1 g1:2,2 g2:1,2", "g1:1,1 g2:1,2"),
    ])
    def test_the_repeat_is_reported(self, layout, kept):
        got, problem = dr._dash_layout_check(layout, {"g1", "g2"})
        assert got == kept
        assert problem and "g1 is placed more than once" in problem, problem


# ===========================================================================
# 10. The spec and data JSON
# ===========================================================================

class TestHostileSpec:
    """A spec that did not come through dash.ado."""

    @pytest.mark.parametrize("val", ["\u00b2", "\u0663", " 5", "+5", "5\n",
                                     "\uff15", "1_0"])
    def test_limits_written_in_other_digits_are_refused(self, val):
        """dash.ado takes ASCII digits only; so must the spec's re-check.
        Measured: "\u00b2" passed ``str.isdigit()`` and then raised
        ValueError out of ``int()``, and "\u0663" was read as 3."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            got = dr._dash_limits({"limits": {"tabs": val}})
        assert got["tabs"] == dr._DASH_LIMITS["tabs"][0]
        assert any("dash_max_tabs" in str(x.message) for x in w)

    def test_ascii_digits_in_a_string_are_still_read(self):
        assert dr._dash_limits({"limits": {"tabs": "7"}})["tabs"] == 7

    @pytest.mark.parametrize("n", [float("inf"), float("-inf"),
                                   float("nan"), "inf", "1e400", None])
    def test_an_infinite_point_count_is_clamped_not_raised(self, n):
        """``"n": Infinity`` is legal to Python's JSON reader, and
        ``int(inf)`` raises OverflowError, which ``_dash_function_args``
        did not catch."""
        (_lo, _hi), pts = dr._dash_function_args({"n": n})
        assert 2 <= pts <= 10000

    def test_a_deeply_nested_spec_fails_before_anything_is_written(
            self, tmp_path):
        sp = tmp_path / "deep.json"
        sp.write_text("[" * 200000 + "]" * 200000)
        dp = tmp_path / "data.json"
        dp.write_text(json.dumps(make_data_json(_DF)))
        out = tmp_path / "out.html"
        t0 = time.monotonic()
        with pytest.raises((RecursionError, ValueError, TypeError,
                            AttributeError)):
            dr.main(str(sp), str(dp), str(out))
        assert time.monotonic() - t0 < 30
        assert not out.exists()

    def test_a_nul_inside_a_title_does_not_split_the_escaping(self, tmp_path):
        spec = make_spec([dict(_SCATTER)])
        spec["build_options"]["title"] = "<scr\x00ipt>alert(1)</scr\x00ipt>"
        spec["graphs"][0]["graph_options"]["title"] = "<img\x00 src=x onerror=a()>"
        html, _msgs = _render(tmp_path, spec)
        assert "<scr\x00ipt>" not in html
        assert "<img\x00" not in html
        assert "&lt;scr" in html


# ===========================================================================
# 11. The served app: /health, sessions, widgets, its command line
# ===========================================================================

def _health(ns, request):
    """(status, body) from ``_HealthHandler`` for *request*: prepare(), then
    get() when prepare() let it through."""
    seen = {"status": 200, "body": []}

    class _Handler(ns["_HealthHandler"]):
        def set_status(self, code, reason=None):
            seen["status"] = code

        def set_header(self, name, value):
            pass

        def finish(self, chunk=None):
            seen["finished"] = True
            if chunk:
                seen["body"].append(chunk)

        def write(self, chunk):
            seen["body"].append(chunk)

    handler = object.__new__(_Handler)
    handler.request = request
    handler.prepare()
    if not seen.get("finished"):
        handler.get()
    return seen["status"], "".join(seen["body"])


@pytest.fixture
def fresh_limiters(served_app, monkeypatch):
    """The app with its own copy of each limiter, the trust flag off, and a
    clock that stands still, restored after the test."""
    import copy
    clock = types.SimpleNamespace(t=1000.0)
    monkeypatch.setitem(served_app, "_time", types.SimpleNamespace(
        monotonic=lambda: clock.t, time=lambda: clock.t))
    for name in ("_SESSION_LIMITER", "_HEALTH_LIMITER"):
        monkeypatch.setitem(served_app, name,
                            copy.deepcopy(served_app[name]))
    monkeypatch.setitem(served_app, "_LIMITER",
                        served_app["_SESSION_LIMITER"])
    monkeypatch.setitem(served_app, "_TRUST_FORWARDED_FOR", False)
    return types.SimpleNamespace(ns=served_app, clock=clock)


class TestHealthEndpoint:

    def test_the_response_reflects_nothing_from_the_request(self,
                                                            fresh_limiters):
        ns = fresh_limiters.ns
        hostile = "<script>alert(1)</script>\r\nX-Injected: 1"
        status, body = _health(ns, _Req(
            "10.9.9.9", **{"X-Forwarded-For": hostile, "User-Agent": hostile,
                           "Host": hostile, "Referer": hostile}))
        assert status == 200
        doc = json.loads(body)
        assert set(doc) == {"status", "timestamp"}
        assert doc["status"] == "ok"
        assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ",
                            doc["timestamp"])
        assert "script" not in body and "Injected" not in body

    def test_a_rotating_forged_header_does_not_escape_the_limit(
            self, fresh_limiters):
        """Untrusted, the header is not the key: 700 requests from one peer,
        each with a new forged address, are one client held to 600."""
        ns = fresh_limiters.ns
        statuses = [_health(ns, _Req("10.7.7.7", **{
            "X-Forwarded-For": "198.18.%d.%d" % (i // 256, i % 256)}))[0]
            for i in range(700)]
        assert statuses.count(200) == ns["_HEALTH_LIMIT_RPM"]
        assert statuses[-1] == 429

    def test_trusted_rotating_keys_share_the_first_contact_budget(
            self, fresh_limiters, monkeypatch):
        """Trusted, each forged address is a new key -- and every new key
        is charged to ONE first-contact window, so the cycle gets no more
        than one client's 600."""
        ns = fresh_limiters.ns
        monkeypatch.setitem(ns, "_TRUST_FORWARDED_FOR", True)
        statuses = [_health(ns, _Req("10.7.7.8", **{
            "X-Forwarded-For": "198.18.%d.%d" % (i // 256, i % 256)}))[0]
            for i in range(1500)]
        assert statuses.count(200) <= ns["_HEALTH_LIMIT_RPM"]
        assert statuses.count(429) >= 900


class _ServerRecorder:
    """Stands in for bokeh.server.server.Server: records its arguments."""
    calls = []

    def __init__(self, apps, **kw):
        type(self).calls.append(kw)


class TestSessionOrigin:
    """The websocket Origin check.  The served app passes Bokeh an
    allowlist; Bokeh lower-cases the Origin's host:port and matches it with
    ``check_allowlist``.  Nothing tested either half before."""

    @pytest.fixture
    def allowlist(self, served_app, monkeypatch):
        _ServerRecorder.calls = []
        monkeypatch.setitem(served_app, "Server", _ServerRecorder)
        served_app["_dash_server_app"](port=5006)
        (kw,) = _ServerRecorder.calls
        assert kw["address"] == "127.0.0.1"
        return kw["allow_websocket_origin"]

    def test_the_default_allowlist_is_loopback_on_the_port(self, allowlist):
        assert sorted(allowlist) == ["127.0.0.1:5006", "localhost:5006"]

    @pytest.mark.parametrize("origin", [
        "http://evil.example:5006",
        "http://localhost:5006.evil.example",
        "http://localhost.evil.example:5006",
        "http://127.0.0.1.nip.io:5006",
        "http://localhost:5007",
        "http://localhost",
        "http://0.0.0.0:5006",
        "http://[::1]:5006",
        "null",
        "http://localhost:5006@evil.example",
        "http://evil.example/#localhost:5006",
        "http://\u217cocalhost:5006",          # Roman numeral fifty: a homoglyph
    ])
    def test_a_foreign_origin_is_refused(self, allowlist, origin):
        from bokeh.server.util import check_allowlist
        host = urlparse(origin).netloc.lower()
        assert not check_allowlist(host, allowlist), origin

    @pytest.mark.parametrize("origin", ["http://localhost:5006",
                                        "http://127.0.0.1:5006",
                                        "http://LOCALHOST:5006"])
    def test_loopback_is_accepted(self, allowlist, origin):
        from bokeh.server.util import check_allowlist
        assert check_allowlist(urlparse(origin).netloc.lower(), allowlist)

    def test_an_operator_origin_is_added_literally(self, served_app,
                                                   monkeypatch):
        _ServerRecorder.calls = []
        monkeypatch.setitem(served_app, "Server", _ServerRecorder)
        served_app["_dash_server_app"](port=5006,
                                       origins=["dash.example.org:5006"])
        (kw,) = _ServerRecorder.calls
        assert "dash.example.org:5006" in kw["allow_websocket_origin"]
        assert "*" not in kw["allow_websocket_origin"]

    def test_bokeh_lets_the_environment_replace_it(self, monkeypatch):
        """Pinned third-party behaviour (BR-20.3): Bokeh's websocket handler
        uses BOKEH_ALLOW_WS_ORIGIN, when it is set, INSTEAD of the app's
        allowlist.  An operator who sets it owns the origin policy."""
        from bokeh.settings import settings
        monkeypatch.setenv("BOKEH_ALLOW_WS_ORIGIN", "evil.example:5006")
        assert "evil.example:5006" in (settings.allowed_ws_origin() or [])
        import inspect
        from bokeh.server.views.ws import WSHandler
        assert "allowed_ws_origin" in inspect.getsource(WSHandler.check_origin)

    def test_the_refusal_page_carries_no_request_data(self, fresh_limiters,
                                                      monkeypatch):
        ns = fresh_limiters.ns
        monkeypatch.setitem(ns, "_SESSION_LIMITER", ns["_RateLimiter"](0))
        marker = "<script>alert('xff')</script>"
        doc = _session(ns, _Req("10.66.66.66", **{
            "X-Forwarded-For": marker, "User-Agent": marker}))
        text = _texts(doc)
        assert "429" in text
        assert "10.66.66.66" not in text
        assert "xff" not in text and "<script" not in text


def _widget(doc, cls):
    found = [m for m in doc.select({"type": cls}) if type(m) is cls]
    assert len(found) == 1, f"expected one {cls.__name__}, found {found}"
    return found[0]


class TestWidgetValuesFromTheClient:
    """A browser client can send any value its widget's property type
    admits: Bokeh checks the type, dash checks nothing further.  These pin
    that no such value raises, is evaluated, or is written into the page.
    (The effect of a nonsense value is confined to the session that sent
    it: an empty frame, or every row.)"""

    def test_a_select_value_outside_its_options_raises_nothing(self,
                                                               served_app):
        doc = _session(served_app)
        sel = _widget(doc, Select)
        cb = _unthrottled(sel, "value")
        for v in ("not-an-option", "", "\x00", "9" * 100000, "__all__x"):
            sel.value = v
            cb("value", None, v)
        assert "Mean mpg" in _texts(doc)

    def test_a_range_of_nan_or_inf_raises_nothing(self, served_app):
        doc = _session(served_app)
        rs = _widget(doc, RangeSlider)
        cb = _unthrottled(rs, "value_throttled")
        for v in ((float("nan"), float("nan")), (float("inf"), float("-inf")),
                  (float("-inf"), float("inf")), (1e308, -1e308)):
            rs.value = v
            cb("value_throttled", None, v)
        assert "Mean mpg" in _texts(doc)

    def test_out_of_range_selection_indices_are_dropped(self, served_app):
        doc = _session(served_app)
        src = next(m.data_source for m in doc.select({"type": object})
                   if isinstance(getattr(m, "data_source", None),
                                 ColumnDataSource)
                   and m.data_source.selected._callbacks.get("indices"))
        cb = _unthrottled(src.selected, "indices")
        n = len(src.data["index"])
        cb("indices", [], [-1, -10 ** 12, 10 ** 12, n, 3])
        ids = [src.data["index"][3]]
        want = f"{_DF.loc[ids, 'mpg'].mean():.2f}"
        assert want in _texts(doc), _texts(doc)

    def test_a_value_is_never_evaluated_or_reflected(self, served_app,
                                                     tmp_path):
        doc = _session(served_app)
        sel = _widget(doc, Select)
        cb = _unthrottled(sel, "value")
        mark = tmp_path / "evaluated"
        for v in ("__import__('os').system('touch %s')" % mark,
                  "<img src=x onerror=alert(1)>",
                  "\"; alert(1); //", "{bf:INJ}", "${7*7}"):
            sel.value = v
            cb("value", None, v)
            page = _texts(doc)
            assert "onerror" not in page and "alert(" not in page
            assert "{bf:INJ}" not in page and "${7*7}" not in page
        assert not mark.exists()


class TestServedCliFlags:
    """The generated app's launcher flags."""

    @pytest.mark.parametrize("text", [
        "\u0666\u0660",        # Arabic-Indic 60
        "\uff16\uff10",        # full-width 60
        "60\n", "6_0", "0x3c", "+60", "60.0", "1e2", " 60", "",
    ])
    def test_a_limit_that_is_not_ascii_digits_is_refused(self, served_app,
                                                         text):
        with pytest.raises(argparse.ArgumentTypeError):
            served_app["_dash_limit_value"](text)

    def test_a_five_thousand_digit_limit_is_refused_quickly(self, served_app):
        t0 = time.monotonic()
        with pytest.raises(argparse.ArgumentTypeError) as exc:
            served_app["_dash_limit_value"]("9" * 5000)
        assert time.monotonic() - t0 < 1
        assert len(str(exc.value)) < 200

    def test_flag_values_are_carried_as_data(self, served_app, monkeypatch,
                                             tmp_path):
        """--allow-websocket-origin and --address go to Bokeh as data; no
        flag value is evaluated or handed to a shell."""
        mark = tmp_path / "flag_evaluated"
        hostile = "evil.example;touch %s" % mark
        args = served_app["_dash_arg_parser"]().parse_args(
            ["--allow-websocket-origin", hostile,
             "--allow-websocket-origin", "$(touch %s)" % mark,
             "--address", "127.0.0.1"])
        _ServerRecorder.calls = []
        monkeypatch.setitem(served_app, "Server", _ServerRecorder)
        served_app["_dash_server_app"](port=5006, address=args.address,
                                       origins=args.origins)
        (kw,) = _ServerRecorder.calls
        assert hostile in kw["allow_websocket_origin"]
        assert kw["address"] == "127.0.0.1"
        assert not mark.exists()


# ===========================================================================
# 12. dash_render.py's command line
# ===========================================================================

class TestRendererOutputPath:
    """``_validate_output_path`` mirrors dash.ado's saving() check for a
    renderer invoked directly.  It had no test."""

    @pytest.mark.parametrize("path", [
        "../x.html", "a/../x.html", "a\\..\\x.html", "a/..", "..",
        "-x.html", "d/-x.html", "x.html\n", "x\x00.html", "x\r.html",
        "x\x1b[31m.html", "x\x7f.html", "x.htm", "x.html.py", "",
        "   ", "x.HTML.exe",
    ])
    def test_a_hostile_output_path_is_refused(self, path):
        with pytest.raises(ValueError):
            dr._validate_output_path(path, "standalone")

    def test_server_mode_wants_a_py_path(self):
        with pytest.raises(ValueError):
            dr._validate_output_path("app.html", "server")
        assert dr._validate_output_path("app.py", "server") == "app.py"

    @pytest.mark.parametrize("path", ["out.html", "dir/out.html",
                                      "my..report.html", "a-b.html",
                                      "OUT.HTML", "C:\\dir\\out.html",
                                      "\u2025\u2215x.html"])
    def test_ordinary_paths_pass(self, path):
        assert dr._validate_output_path(path, "standalone") == path

    def test_a_megabyte_path_is_judged_in_linear_time(self):
        long_ok = "a/" * 500000 + "x.html"
        long_bad = "a/" * 500000 + "../x.html"
        t0 = time.monotonic()
        assert dr._validate_output_path(long_ok, "standalone") == long_ok
        with pytest.raises(ValueError):
            dr._validate_output_path(long_bad, "standalone")
        assert time.monotonic() - t0 < 2

    def test_main_refuses_before_it_writes(self, tmp_path):
        sp, dp = _write_inputs(tmp_path, make_spec([dict(_SCATTER)]))
        sub = tmp_path / "sub"
        sub.mkdir()
        target = str(sub / ".." / "escaped.html")
        with pytest.raises(ValueError):
            dr.main(sp, dp, target)
        assert not (tmp_path / "escaped.html").exists()

    def test_the_launcher_runs_the_app_without_a_shell(self):
        """``--launch`` starts the generated app with an argv list; no call
        in the renderer asks for a shell."""
        with open(os.path.join(_ROOT, "dash_render.py"),
                  encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        popens = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = getattr(node.func, "attr", None) or getattr(
                    node.func, "id", None)
                if name in ("Popen", "run", "call", "check_call",
                            "check_output", "system"):
                    popens.append(node)
                    for kw in node.keywords:
                        assert not (kw.arg == "shell" and getattr(
                            kw.value, "value", False) is True), (
                            f"a {name}() call asks for a shell")
                    assert name != "system", "os.system is called"
        assert popens, "the launcher's Popen call was not found"


# ===========================================================================
# 13. Style, text and title bounds
# ===========================================================================

class TestStyleOptionBounds:

    def test_a_megabyte_colour_is_judged_in_linear_time(self):
        hostile = ["#" + "a" * 10 ** 6, "(" * 10 ** 5 + ")" * 10 ** 5,
                   "rgb(" + "1," * 10 ** 5 + ")", "red" + " " * 10 ** 6 + ";",
                   "#" + "0" * 999999 + "g"]
        t0 = time.monotonic()
        for h in hostile:
            assert dr._sanitize_css_color(h, "#000000") == "#000000"
            try:
                dr.OptionTranslator.translate_mcolor(h)
            except ValueError:
                pass
        assert time.monotonic() - t0 < 5


class TestTextPlotOptionBounds:

    def test_a_legend_order_of_a_hundred_thousand_keys_is_bounded(self,
                                                                 tmp_path):
        spec = make_spec([dict(_SCATTER), dict(_SCATTER2)])
        spec["graphs"][0]["graph_options"]["legend"] = (
            "order(" + " ".join(str(i % 3) for i in range(100000)) + ")")
        t0 = time.monotonic()
        html, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        assert "<html" in html.lower()

    def test_a_long_legend_label_is_escaped_once(self, tmp_path):
        text = "<b>" * 20000
        spec = make_spec([dict(_SCATTER), dict(_SCATTER2)])
        spec["graphs"][0]["graph_options"]["legend"] = 'label(1 "%s")' % text
        t0 = time.monotonic()
        html, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        assert "<b><b>" not in html
        assert len(html) < 2_000_000 + 20 * len(text)


class TestGraphTextBounds:

    def test_a_long_title_is_drawn_once_in_bounded_time(self, tmp_path):
        text = "<i>x</i>" * 25000   # 200,000 characters
        spec = make_spec([dict(_SCATTER)])
        spec["graphs"][0]["graph_options"]["title"] = text
        spec["graphs"][0]["graph_options"]["note"] = text
        t0 = time.monotonic()
        html, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        assert "<i>x</i><i>x</i>" not in html
        assert len(html) < 2_000_000 + 20 * len(text)
