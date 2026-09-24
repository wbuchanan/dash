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
import base64
import html as _htmllib
import io
import json
import math
import os
import re
import socket
import struct
import subprocess
import sys
import tempfile
import time
import tokenize
import types
import urllib.request
import warnings

import numpy as np
import pandas as pd
import pytest
from bokeh.document import Document
from bokeh.models import (ColumnDataSource, Div, GridPlot, Label, Legend,
                          LegendItem, Plot, RangeSlider, Select, Title)
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
# The renderer's text boxes, read as Stata reads them (24sep2026).
_TBX = "test/test_textbox_multiline.py::TestTextboxAdversarial::"
# T3r (24sep2026): a qualifier's logical operators.
_LOGIC = "test/test_qualifier_logic.py::TestAdversarialLogicalOperators::"

SURFACES = {
    # `dash <plot> varlist, ...' -- the plot-type token and the varlist.
    "plot_varlist_and_type": {
        "bypass": [
            "test_adversarial.cscript:P20-01",
            "test_parser_integrity.cscript:P1B-13",
            "test_parser_integrity.cscript:P1B-14",
            "test_parser.cscript:P1A-69",
            "test_parser.cscript:P1A-74",
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
            "test_parser.cscript:P1A-75",
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
            "test_adversarial.cscript:P20-35",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P22-03",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_a_hundred_thousand_records_are_read_in_bounded_time",
            "test/test_pccapsym_pcarrowi.py::TestMapPcarrowi::test_the_arrow_heads_are_added_in_one_change",
        ],
    },
    # `scatteri #y #x [(#clockpos)] ["label"] ...' and `pci #y1 #x1 #y2 #x2
    # [(#clockpos)] ["label"] ...': immediate values typed on the command
    # line -- numbers, clock positions and free text -- read by the same
    # Mata reader as pcarrowi's into the spec, and drawn by the renderer.
    # They were written into the spec token by token, unchecked.
    "immediate_scatteri_pci_values": {
        "bypass": [
            "test_adversarial.cscript:P20-34",
            "test_parser.cscript:P1A-70",
            "test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_a_malformed_record_is_named",
            "test/test_immediate_values.py::TestPciDrawsItsRecords::test_a_malformed_record_is_named",
            "test/test_immediate_values.py::TestPciDrawsItsRecords::test_the_old_two_point_shape_is_named_not_redrawn",
            "test_help_claims_6.cscript:HC6-48",
        ],
        "injection": [
            "test_adversarial.cscript:P20-35",
            "test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_the_label_is_text_not_markup",
            "test/test_immediate_values.py::TestBothModesDrawTheSame::test_a_scatteri_label_reaches_the_served_page_as_text",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-36",
            "test/test_immediate_values.py::TestScatteriDrawsItsRecords::test_a_hundred_thousand_records_are_read_in_bounded_time",
            "test/test_immediate_values.py::TestPciDrawsItsRecords::test_a_hundred_thousand_records_are_read_in_bounded_time",
        ],
    },
    # `if' and `in' on a plot or a KPI; the renderer re-applies them.
    "if_in_qualifiers": {
        "bypass": [
            "test/test_security_surface.py::TestIfQualifierLeavesStringLiteralsAlone::test_the_literal_is_unchanged",
            _M + "TestIfQualifierEncodings::test_the_spelling_does_not_get_past_the_whitelist",
            "test/test_filter_widget_data.py::TestOneWidgetWhateverTheGraphsSelect::test_a_numeric_variable",
            "test/test_served_linked_views.py::TestEachServedViewShowsItsOwnRows::test_a_per_layer_qualifier_keeps_its_panel",
            "test_json_escaping.cscript:JSE-11",
            "test_json_escaping.cscript:JSE-12",
            "test_json_escaping.cscript:JSE-14",
            "test_json_escaping.cscript:JSE-22",
            "test_json_escaping.cscript:JSE-33",
            "test_json_escaping.cscript:JSE-35",
            "test_help_claims_1.cscript:HC1-21",
            "test_help_claims_1.cscript:HC1-04",
            # A plot's or the graph's qualifier that closes its quote and
            # writes name() and saving(): text, naming and writing nothing.
            "test_json_escaping.cscript:JSE-47",
            # Stata's logical operators read by the renderer (T3r,
            # 24sep2026): a look-alike ! or ~ is not an operator.
            _LOGIC + "test_a_lookalike_operator_is_not_read_as_one",
        ],
        "injection": [
            "test/test_axis_options.py::TestIfQualifierWhitelistIsNotWeakened::test_hostile_expressions_are_rejected",
            "test/test_phase5.py::TestIfExprRceHardening::test_at_poc_payload_blocked_end_to_end",
            "test/test_server_layer_defects.py::TestAKpiQualifierIsApplied::test_a_kpi_qualifier_cannot_execute",
            "test_json_escaping.cscript:JSE-13",
            "test_json_escaping.cscript:JSE-32",
            "test_json_escaping.cscript:JSE-34",
            "test_help_claims_1.cscript:HC1-22",
            # SMCL, markup, Python code and an =exp behind a quote and an
            # apostrophe; a global, an =exp that writes a file and a macro
            # reference, never expanded a second time: the typed text is
            # the sample the rows, a weight and start() are judged over.
            "test_json_escaping.cscript:JSE-48",
            "test_json_escaping.cscript:JSE-66",
            # A payload under ! or ~ still meets the whitelist (T3r).
            _LOGIC + "test_a_payload_behind_a_not_does_not_run",
        ],
        "exhaustion": [
            _M + "TestIfQualifierExhaustion::test_a_run_of_negations_is_skipped_not_raised",
            _M + "TestIfQualifierExhaustion::test_the_served_app_has_the_same_bound",
            "test_adversarial.cscript:P20-20",
            "test_json_escaping.cscript:JSE-18",
            "test_json_escaping.cscript:JSE-36",
            "test_help_claims_1.cscript:HC1-23",
            # A literal of 20,000 apostrophes, stored whole and applied in
            # bounded time.
            "test_json_escaping.cscript:JSE-49",
            # The logic reader is one pass, bounded in both modes (T3r).
            _LOGIC + "test_a_qualifier_past_the_bound_is_refused_in_bounded_time",
            _LOGIC + "test_a_long_operand_under_many_operators_costs_linear_memory",
            _LOGIC + "test_a_long_name_is_read_in_linear_time",
            _LOGIC + "test_redundant_parentheses_cost_nothing",
        ],
    },
    # jitter(), level(), bin(), n(), bwidth(), bands(), xsize() ...
    "numeric_plot_options": {
        "bypass": [
            "test_adversarial.cscript:P20-02",
            "test_adversarial.cscript:P9-04",
            "test_adversarial.cscript:P20-18",
            "test/test_help_claims_6.py::TestTheFitRangeIsReadSafely::test_an_unreadable_range_draws_the_observed_range",
            "test/test_help_claims_6.py::TestKdensityRangeAndWidth::test_an_unusable_width_draws_the_default_bandwidth",
            "test/test_help_claims_6.py::TestDroplineBase::test_an_unusable_base_draws_from_zero",
        ],
        "injection": [
            "test_adversarial.cscript:P9-01",
            "test_adversarial.cscript:P9-02",
            "test_adversarial.cscript:P9-03",
            "test/test_help_claims_6.py::TestTheFitRangeIsReadSafely::test_an_unreadable_range_draws_the_observed_range",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P9-06",
            "test_adversarial.cscript:P9-07",
            "test_adversarial.cscript:P9-08",
            "test_adversarial.cscript:P9-09",
            "test_adversarial.cscript:P9-10",
            "test/test_help_claims_6.py::TestTheFitRangeIsReadSafely::test_a_huge_range_keeps_the_point_count",
            "test/test_help_claims_6.py::TestTheFitRangeIsReadSafely::test_n_past_its_bound_is_not_honoured",
        ],
    },
    # mcolor(), msymbol(), lcolor(), lpattern(), msize(), kernel() ...
    "style_plot_options": {
        "bypass": [
            "test/test_security_surface.py::TestAColourMustBeAColour::test_a_non_hex_hash_string_is_rejected",
            "test_adversarial.cscript:P20-03",
            "test/test_option_validation.py::TestUserTextIsEchoedThroughDashDisplay::test_the_style_note",
            _TW + "test_an_angle_in_another_scripts_digits_is_not_an_angle",
            "test/test_help_claims_2.py::TestAStyleOptionGivenEmptyParenthesesIsReported::test_one_note_naming_it_identical_in_both_modes",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_position_in_another_spelling_is_not_a_position",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_gap_in_another_spelling_is_not_a_gap",
            "test/test_help_claims_5.py::TestTheClockHelpers::test_the_gap_reader_refuses_what_is_not_a_gap",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_quotes_that_are_not_a_pair_are_not_stripped",
        ],
        "injection": [
            "test_adversarial.cscript:P2-81",
            "test/test_html_output.py::TestAdversarialPlotOptions::test_injection_in_mcolor_produces_valid_html",
            _TW + "test_markup_in_a_value_is_named_as_text_and_never_drawn",
            _TW + "test_a_colour_that_is_code_is_refused_by_the_colour_reader",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_markup_in_either_option_is_named_as_text",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_hostile_colour_is_refused_not_passed_through",
        ],
        "exhaustion": [
            "test/test_option_validation.py::TestABadStyleValueNeverAborts::test_a_non_finite_size_or_width",
            _M + "TestStyleOptionBounds::test_a_megabyte_colour_is_judged_in_linear_time",
            _TW + "test_a_megabyte_angle_is_judged_at_once",
            _TW + "test_a_non_finite_clwidth_is_named_not_drawn",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_megabyte_value_is_judged_at_once",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_hundred_thousand_character_colour_is_named_quickly",
        ],
    },
    # mlabel(varname) and the legend's label() and order() text.
    "text_plot_options": {
        "bypass": [
            "test_adversarial.cscript:P20-04",
            "test/test_option_validation.py::TestUserTextIsEchoedThroughDashDisplay::test_the_mlabel_extras_warning",
            _TW + "test_a_format_in_another_scripts_digits_is_not_applied",
            "test_json_escaping.cscript:JSE-29",
            "test_twoway_option_parity.cscript:TP-12",
        ],
        "injection": [
            "test/test_graph_options.py::TestLegendLabels::test_legend_label_xss_is_carried_as_text",
            _TW + "test_markup_in_a_value_is_named_as_text_and_never_drawn",
            "test_twoway_option_parity.cscript:TP-12",
        ],
        "exhaustion": [
            _M + "TestTextPlotOptionBounds::test_a_legend_order_of_a_hundred_thousand_keys_is_bounded",
            _M + "TestTextPlotOptionBounds::test_a_long_legend_label_is_escaped_once",
            _TW + "test_a_format_stata_refuses_builds_no_giant_label",
            _TW + "test_the_widest_format_stata_accepts_is_bounded_by_stata",
            "test_twoway_option_parity.cscript:TP-12",
        ],
    },
    # title(), subtitle(), note(), caption(), xtitle(), ytitle().
    "graph_text_options": {
        "bypass": [
            "test_adversarial.cscript:P20-15",
            "test_json_escaping.cscript:JSE-08",
            "test_json_escaping.cscript:JSE-29",
            "test/test_help_claims_2.py::TestAnUnknownStyleInsideAStructuredOption::test_one_note_and_the_schemes_default_in_both_modes",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_direction_word_in_any_spelling_is_not_a_placement",
            # The renderer's text boxes: text a string or a parenthesis
            # holds is never read as a sub-option (24sep2026).
            _TBX + "test_text_inside_a_string_never_becomes_a_suboption",
            "test_json_escaping.cscript:JSE-63",
            # A title that closes its quote and writes name() and saving(),
            # and values holding the quote, meeting dash's own checks.
            "test_json_escaping.cscript:JSE-47",
        ],
        "injection": [
            "test_adversarial.cscript:P2-78",
            "test/test_html_output.py::TestXssInHtmlOutput::test_script_tag_in_title_is_escaped",
            "test/test_html_output.py::TestAdversarialPlotOptions::test_xss_in_note_option_escaped",
            "test_json_escaping.cscript:JSE-27",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_label_text_is_a_label_and_never_read",
            _TBX + "test_macro_smcl_markup_and_python_in_a_string_arrive_as_written",
            "test_json_escaping.cscript:JSE-64",
            # SMCL, markup, Python code and an =exp behind a quote and an
            # apostrophe; then a global, an =exp that writes a file and a
            # macro reference, in the titles, the text options, a legend
            # label, the paren, || and one-line forms and the values dash
            # checks, never expanded a second time.
            "test_json_escaping.cscript:JSE-48",
            "test_json_escaping.cscript:JSE-65",
            "test_json_escaping.cscript:JSE-67",
            "test_json_escaping.cscript:JSE-69",
        ],
        "exhaustion": [
            _M + "TestGraphTextBounds::test_a_long_title_is_drawn_once_in_bounded_time",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_ten_thousand_word_legend_is_read_in_bounded_time",
            _TBX + "test_long_runs_of_quotes_and_apostrophes_are_read_in_bounded_time",
            # A title of 5,000 strings each an apostrophe.
            "test_json_escaping.cscript:JSE-49",
        ],
    },
    # xlabel() / ylabel(): numlists, a(b)c, #N, value "label" pairs, format().
    "axis_label_options": {
        "bypass": [
            _M + "TestAxisLabelInjection::test_pre_escaped_markup_is_carried_as_written_not_decoded",
            _M + "TestAxisLabelBounds::test_a_non_finite_endpoint_does_not_raise",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_tick_positions_are_numbers_only",
        ],
        "injection": [
            _M + "TestAxisLabelInjection::test_a_tick_label_cannot_break_out_of_the_formatter_code",
            "test/test_help_claims_8.py::TestTheTickMarkCodeCarriesNoUserText::test_a_hostile_label_in_xtick_reaches_no_model",
            "test/test_help_claims_8.py::TestTheTickMarkCodeCarriesNoUserText::test_the_code_is_the_same_for_any_positions",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_axis_label_text_is_data_never_code",
        ],
        "exhaustion": [
            _M + "TestAxisLabelBounds::test_an_increment_past_the_tick_limit_keeps_the_default_ticks",
            _M + "TestAxisLabelBounds::test_a_huge_count_is_clamped",
            _M + "TestNumericFormatBounds::test_an_axis_format_with_a_billion_decimals_is_bounded",
            "test/test_help_claims_8.py::TestTheTickMarkCodeCarriesNoUserText::test_a_huge_request_is_bounded",
            "test/test_help_claims_7.py::TestAdversarialLegendAxesRegions::test_a_huge_increment_on_a_second_axis_or_a_tick_is_bounded",
        ],
    },
    # by(varlist, suboptions).
    "by_option": {
        "bypass": [
            "test_adversarial.cscript:P20-05",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_shell_injection_blocked",
            "test_json_escaping.cscript:JSE-29",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_title_label_keyed_by_another_spelling_is_not_matched",
            "test/test_help_claims_5.py::TestTheSubOptionSplitterReadsStataQuotes::test_the_tokens",
        ],
        "injection": [
            "test/test_phase5.py::TestByFacetingSecurity::test_by_import_injection_blocked",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_xss_in_facet_label_is_canvas_text",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_markup_in_a_title_label_is_carried_as_text",
        ],
        "exhaustion": [
            "test/test_resource_limits.py::TestByOnAHighCardinalityVariable::test_the_first_groups_in_sort_order_are_kept",
            "test_resource_limits.cscript:RL-06",
            "test/test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_the_saved_page_hands_gridplot_the_panels_alone",
            "test/test_resource_limits.py::TestByColsCannotOutgrowThePanels::test_the_served_app_hands_gridplot_the_panels_alone",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_huge_label_set_titles_at_once",
            "test/test_help_claims_5.py::TestTheSubOptionSplitterReadsStataQuotes::test_a_megabyte_of_quotes_is_split_at_once",
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
            "test_registry_collision.cscript:REG-37",
            "test_registry_collision.cscript:REG-38",
            "test_registry_collision.cscript:REG-40",
            # name(\$m) is not the name $m holds, and name(`"q"7"') is no
            # name: each is dash's refusal, and nothing registers.
            "test_json_escaping.cscript:JSE-68",
        ],
        "injection": [
            "test_adversarial.cscript:P19-25",
            "test_adversarial.cscript:P19-26",
            "test_registry_collision.cscript:REG-17",
            "test_registry_collision.cscript:REG-22",
            "test_registry_collision.cscript:REG-29",
            "test_registry_collision.cscript:REG-32",
            "test/test_reserved_names.py::TestAdversarialReservedNames::test_injection_a_refused_name_is_inert_text",
            "test_registry_collision.cscript:REG-39",
            # A global, a macro reference and an =exp that writes a file in
            # name(), never expanded or evaluated.
            "test_json_escaping.cscript:JSE-68",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-21",
            "test_adversarial.cscript:P19-01",
            "test/test_reserved_names.py::TestAdversarialReservedNames::test_exhaustion_many_refused_names_make_one_bounded_report",
            "test_registry_collision.cscript:REG-41",
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
            "test_help_claims_4.cscript:HC4-06",
            # update() and name() holding quotes; a title that closes its
            # quote and names another KPI and update() (24sep2026).
            "test_json_escaping.cscript:JSE-55",
            "test_json_escaping.cscript:JSE-57",
        ],
        "injection": [
            # $name, `=exp', a file-writing function, SMCL, markup and
            # Python code in a title, a subtitle, a qualifier's literal and
            # the validated options: data, as written (24sep2026).
            "test_json_escaping.cscript:JSE-58",
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
            "test_json_escaping.cscript:JSE-32",
            "test_help_claims_4.cscript:HC4-06",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P19-01",
            "test/test_resource_limits.py::TestTheGraphAndPlotLimits::test_graphs_and_kpis_past_the_limit_are_dropped_in_registry_order",
            _M + "TestNumericFormatBounds::test_a_hand_edited_kpi_format_is_bounded",
            "test/test_kpi_security.py::TestAKpiFormatCannotBuildAHugeCard::test_both_modes_before_and_after_a_filter_moves",
            "test_help_claims_4.cscript:HC4-06",
            # A title of 20,000 "'90s" strings and a qualifier literal of
            # 20,000 apostrophes, stored whole in bounded time (24sep2026).
            "test_json_escaping.cscript:JSE-59",
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
            "test_json_escaping.cscript:JSE-37",
            "test/test_help_claims_3.py::TestAdversarialFilterText::test_bypass_a_label_cannot_add_a_group",
            "test_help_claims_3.cscript:HC3-20",
            "test_help_claims_3.cscript:HC3-08",
            # filterposition(), link() and exclude() holding quotes; a
            # filter() label that closed the quotes dash build handed it on
            # in and became csv and title() options (24sep2026).
            "test_json_escaping.cscript:JSE-55",
            "test_json_escaping.cscript:JSE-56",
            "test_json_escaping.cscript:JSE-57",
        ],
        "injection": [
            "test_adversarial.cscript:P2-84",
            "test/test_axis_options.py::TestDashboardTitleEscaping::test_a_script_tag_is_still_escaped",
            "test/test_html_output.py::TestBuildSubtitleInHtml::test_build_subtitle_escaped",
            "test_path_validation.cscript:PV-12",
            _BS + "test_injection_no_spec_text_reaches_the_document",
            "test/test_help_claims_3.py::TestAdversarialFilterText::test_injection_a_label_cannot_exclude_a_graph",
            "test/test_help_claims_3.py::TestAnApostropheInALabelLeavesExcludeAlone::test_saved",
            "test/test_help_claims_3.py::TestAnApostropheInALabelLeavesExcludeAlone::test_served",
            "test_help_claims_3.cscript:HC3-06",
            "test_help_claims_3.cscript:HC3-09",
            # $name, `=exp' and a file-writing function in a title, a
            # subtitle, a tab, a filter label, a scheme file's name,
            # saving(), link() and filterposition() (24sep2026).
            "test_json_escaping.cscript:JSE-58",
        ],
        "exhaustion": [
            # A dashboard title of 20,000 "'90s" strings (24sep2026).
            "test_json_escaping.cscript:JSE-59",
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
            "test/test_help_claims_3.py::TestAdversarialFilterText::test_exhaustion_a_huge_label_is_read_in_linear_time",
        ],
    },
    # dash serve: port(), timeout(), nobrowser.
    "serve_options": {
        "bypass": [
            "test_adversarial.cscript:P20-14",
            "test_adversarial.cscript:P20-26",
            "test_echo_text.cscript:ECH-05",
            # The build options dash serve hands on: a filter() label that
            # closed the quotes it was handed on in (24sep2026).
            "test_json_escaping.cscript:JSE-57",
        ],
        "injection": [
            "test_adversarial.cscript:P4-84",
            "test_adversarial.cscript:P20-13",
            "test_echo_text.cscript:ECH-03",
            # An inherited and a restated title holding $name and `=exp',
            # and a scheme file's name holding $, served as written
            # (24sep2026).
            "test_json_escaping.cscript:JSE-58",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P20-19",
            # A served title of 20,000 "'90s" strings (24sep2026).
            "test_json_escaping.cscript:JSE-59",
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
            "test_program_coverage.cscript:PC-22",
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
            "test_program_coverage.cscript:PC-03",
            "test/test_server.py::TestDropdownSentinelCollision::test_standalone_sentinel_unique_when_data_has_all_value",
            "test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_a_label_keyed_by_another_spelling_is_not_matched",
            # WP-25 (24sep2026): a date value outside Stata's range, or no
            # number at all, is one missing point, counted, never a crash
            # and never the whole column (pandas 2.3 and 3.0 alike).
            "test/test_date_range.py::TestHostileDateValues::test_non_finite_and_huge_values_are_missing_and_counted",
            "test/test_date_range.py::TestHostileDateValues::test_an_integer_too_large_for_a_double_is_counted_not_raised",
            "test/test_date_range.py::TestTheConversionHoldsStatasWholeRange::test_the_first_and_last_date_convert_and_one_past_is_missing",
            "test/test_date_range.py::TestTheConversionHoldsStatasWholeRange::test_a_fraction_below_the_first_day_is_no_date",
        ],
        "injection": [
            "test_adversarial.cscript:P4-86",
            "test/test_phase5.py::TestByFacetingSecurity::test_by_xss_in_facet_label_is_canvas_text",
            "test/test_filters.py::TestFilterSecurity::test_filter_values_are_text_and_never_code",
            "test/test_server.py::test_escape_chars_in_data_do_not_break_syntax",
            "test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_markup_in_a_value_label_is_carried_as_text",
            "test_program_coverage.cscript:PC-09",
            "test_program_coverage.cscript:PC-10",
            "test/test_date_range.py::TestHostileDateValues::test_a_hostile_date_in_the_data_file_is_one_missing_point",
        ],
        "exhaustion": [
            "test_adversarial.cscript:P19-11",
            "test_resource_limits.cscript:RL-03",
            "test/test_resource_limits.py::TestADropdownOnAContinuousVariable::test_the_widget_lists_at_most_the_limit",
            "test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_a_huge_label_set_is_read_at_once",
            "test/test_marker_label_parity.py::TestAdversarialMarkerLabels::test_a_number_stata_would_write_long_is_bounded",
            "test/test_help_claims_5.py::TestAdversarialLabelPlacement::test_a_date_no_calendar_holds_is_a_dot_not_a_crash",
            "test/test_date_range.py::TestHostileDateValues::test_two_million_values_convert_in_bounded_time_and_memory",
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
            "test/test_help_claims_4.py::TestAHandEditedStatistic::test_other_digits_are_no_percentile_in_either_mode",
        ],
        "injection": [
            _M + "TestHostileSpec::test_a_nul_inside_a_title_does_not_split_the_escaping",
            "test_registry_collision.cscript:REG-27",
            "test/test_server_function_security.py::TestAKeywordArgumentCannotExecute::test_the_standalone_renderer_does_not_either",
            # A graph name reaching the save button's file name (WP-21).
            "test/test_toolbar.py::TestTheBootstrapPage::test_only_a_stata_name_reaches_the_page",
            "test/test_toolbar.py::TestSaveFilename::test_anything_else_is_dashboard",
            "test/test_help_claims_1.py::TestTheFallbackTooltipIsSafe::test_no_field_holds_the_name",
        ],
        "exhaustion": [
            _M + "TestHostileSpec::test_a_deeply_nested_spec_fails_before_anything_is_written",
            "test/test_toolbar.py::TestSaveFilename::test_a_huge_name_is_refused_without_being_scanned",
            _M + "TestLayoutGridBound::test_an_oversized_grid_is_drawn_as_auto",
            "test/test_resource_limits.py::TestAnOversizedDatasetIsRefused::test_the_saved_renderer_refuses_before_drawing",
            "test/test_help_claims_4.py::TestAHandEditedStatistic::test_a_huge_digit_run_is_cheap_in_both_modes",
        ],
    },
    # A `function y = <expr>' plot: an expression the renderer evaluates.
    "function_plot_expression": {
        "bypass": [
            _M + "TestFunctionExpressionEncodings::test_the_layer_draws_nothing",
            "test/test_immediate_dashboards.py::TestARejectedExpressionIsStillReported::test_with_data_or_none",
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
            # WP-25 (24sep2026): under a Bokeh that admits a host which
            # only begins with an allowed one (3.8, which Stata's Python
            # ships), the origin is still refused.
            _M + "TestSessionOriginUnderALenientBokeh::test_a_host_that_begins_with_an_allowed_one_is_refused",
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
            "test/test_served_linked_views.py::TestEachServedViewShowsItsOwnRows::test_after_one_move",
            # T5 (24sep2026): no widget value widens a layer's own
            # if()/in(), and no selection outlives the rows it named.
            "test/test_served_filter_move.py::TestAdversarialFilterMoves::test_no_widget_value_widens_a_layers_own_rows",
            "test/test_served_filter_move.py::TestAdversarialFilterMoves::test_a_selection_cannot_outlive_the_rows_it_named",
        ],
        "injection": [
            _M + "TestWidgetValuesFromTheClient::test_a_value_is_never_evaluated_or_reflected",
            "test/test_served_filter_move.py::TestAdversarialFilterMoves::test_a_value_is_data_not_a_qualifier",
        ],
        "exhaustion": [
            "test/test_served_throttle.py::TestAFloodOfFilterChangesIsThrottled::test_a_thousand_select_changes_run_at_most_burst_recomputes",
            "test/test_served_throttle.py::TestTheBrushIsThrottled::test_a_thousand_selections_run_at_most_burst_and_the_last_wins",
            "test/test_served_linked_views.py::TestTheSharedSourceHoldsEveryFilteredRowOnce::test_written_once_per_move",
            "test/test_served_filter_move.py::TestAdversarialFilterMoves::test_a_move_over_many_rows_is_linear",
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
            "test/test_help_claims_4.py::TestTheOutputPathRule::test_the_launch_route_never_overwrites_a_file_that_is_not_py",
            "test/test_help_claims_4.py::TestTheOutputPathRule::test_the_other_checks_hold_on_the_launch_route",
            "test/test_help_claims_4.py::TestTheOutputPathRule::test_building_a_server_app_still_needs_a_py",
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
            "test/test_help_claims_2.py::TestTheCsvCarriesEveryVariableTheDashboardUses::test_a_served_page_sends_only_what_it_draws",
        ],
        "injection": [
            "test/test_export.py::TestTheCsvFormatter::test_a_text_cell_that_a_spreadsheet_would_run_is_defused",
            "test/test_export.py::TestTheCsvFormatter::test_a_label_that_a_spreadsheet_would_run_is_defused",
            "test/test_export.py::TestTheCsvFormatter::test_rfc_4180_quoting",
        ],
        "exhaustion": [
            "test/test_export.py::TestTheServedDownload::test_a_burst_of_clicks_is_held_to_the_bucket",
            "test/test_help_claims_2.py::TestTheServedDownloadRate::test_the_bucket_with_a_clock",
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


def _page_blocks(page):
    """The raw text of the document blocks a saved page embeds, as the page
    carries them -- HTML-escaped by Bokeh.  file_html (every layout but bs)
    writes a ``<script type="application/json">`` block; components()
    (layout(bs)) writes the JS string ``const docs_json = '...'``, whose
    backslashes are doubled (test_layout_tabs.py reads them the same way)."""
    blocks = re.findall(r'<script type="application/json" id="[^"]+">'
                        r'\s*(.*?)\s*</script>', page, re.S)
    blocks += [m.group(1).replace("\\\\", "\\") for m in
               re.finditer(r"const docs_json = '(.*?)';", page, re.S)]
    return blocks


def _page_document(page):
    """The one Bokeh document a saved page embeds, read back as models.

    Not the page text: the page inlines BokehJS, which names every model and
    class, and it HTML-escapes the document it embeds -- measured 24sep2026,
    a legend label of 20,000 "<b>" and a title of 25,000 "<i>x</i>" are on
    the page only as ``&lt;b&gt;`` and ``&lt;i&gt;``, so a check that
    "<b><b>" is absent from the page cannot fail whatever the label became.
    """
    docs = [d for b in _page_blocks(page)
            for d in json.loads(_htmllib.unescape(b)).values()]
    assert len(docs) == 1, f"{len(docs)} embedded Bokeh documents, not 1"
    return Document.from_json(docs[0])


def _text_of(value):
    """A text property's plain string: Bokeh writes a LegendItem label as
    {"value": ...}, which reads back as a Value or a dict."""
    if isinstance(value, dict):
        return value.get("value")
    return getattr(value, "value", value)


def _strings_in(value):
    """Every string a property value holds, through dicts, lists, tuples,
    object arrays and Value wrappers; a model it refers to is left to
    ``doc.select``, which visits every model."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings_in(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            yield from _strings_in(v)
    elif isinstance(value, np.ndarray):
        if value.dtype == object:
            for v in value.tolist():
                yield from _strings_in(v)
    elif isinstance(getattr(value, "value", None), str):
        yield value.value


def _holding(doc, needle):
    """Sorted ``(model type, property)`` for every property of every model
    in *doc* whose value holds *needle* -- defaults included, so nothing a
    model draws is skipped."""
    out = []
    for m in doc.select({}):
        for name, value in m.properties_with_values(
                include_defaults=True).items():
            if any(needle in s for s in _strings_in(value)):
                out.append((type(m).__name__, name))
    return sorted(out)


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
        come out as a string literal and nothing else -- in the source, and
        when the app runs.

        The source is read token by token, as before.  The app is now also
        RUN -- imported and a session opened -- in the directory the payload
        writes its marker to.  Measured 24sep2026: this test asserted the
        marker absent without ever running the app, and its payload called
        ``os.system('touch_pwned')``, a command that does not exist, so it
        could leave no marker even when executed; an app that spliced the
        carried value into code it runs at import (exec of
        ``['<value>']``) passed it.  The payload now writes the marker from
        Python, and the first assertion shows that it does whenever it is
        executed in the context it is written to break out of.
        """
        monkeypatch.chdir(tmp_path)
        marker = tmp_path / "pwned_marker"
        payload = "x'];open('pwned_marker','w').close()#"
        heading = '"</script><script>alert(1)</script>'
        # The check can see an execution: closed into the list literal it
        # breaks out of, the payload leaves the marker.
        exec("_dash_probe = ['" + payload + "']", {})
        assert marker.exists()
        marker.unlink()
        (tmp_path / "hostile.scheme").write_text(
            "#include s2color\n"
            "color background %s\n"
            "color heading %s\n"
            "color plotregion #abcdef\n" % (payload, heading))
        spec = make_spec([dict(_SCATTER)])
        spec["build_options"]["scheme"] = "hostile"
        src = _app_source(tmp_path, spec)
        ast.parse(src)
        code_only = []
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type not in (tokenize.STRING, tokenize.COMMENT):
                code_only.append(tok.string)
        code = " ".join(code_only)
        assert "_SCHEME_PROPS" in code   # the reader sees the code tokens
        assert "pwned_marker" not in code
        assert "alert(1)" not in code
        assert payload in src  # carried, as a literal
        # Run: the app imported and a session opened, here.
        ns = _load_app(src, "hostile_scheme")
        doc = _session(ns)
        assert not marker.exists(), "a scheme value was executed"
        # The values reached the running app, as the text written ...
        props = ns["_DASH_SCHEME"]._props
        assert props["color background"] == payload
        assert props["color heading"] == heading
        # ... and no model of the served document holds either, where a
        # colour from the same file does reach it (the reader can see it).
        assert _holding(doc, "#abcdef") == [("figure",
                                             "background_fill_color")]
        assert _holding(doc, "pwned_marker") == []
        assert _holding(doc, "alert(1)") == []


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


def _three_graph_spec(layout):
    """g1, g2 and g3, drawing mpg, price and foreign against weight, so each
    figure is known by its y-axis title."""
    spec = _two_graph_spec(layout)
    spec["graphs"].append({
        "plots": [{"type": "scatter", "yvar": "foreign", "xvar": "weight",
                   "options": {}}],
        "graph_options": {"name": "g3"}, "if_expr": "", "in_expr": ""})
    spec["build_options"]["registry"] = "g1 g2 g3"
    return spec


def _grid_cells(doc):
    """``[(row, col, y-axis title), ...]`` of the one GridPlot in *doc*,
    sorted: where each figure sits, known by the variable it draws."""
    grids = list(doc.select({"type": GridPlot}))
    assert len(grids) == 1, f"{len(grids)} grids, not 1"
    return sorted((r, c, str(m.yaxis[0].axis_label))
                  for m, r, c in grids[0].children)


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

    # A zero is read as one in either place: a zero-column grid would
    # divide by zero where the saved page fills its rows.  "2 0" and "0 0"
    # were not here, so a reader that clamped the rows alone passed
    # (measured 24sep2026: the saved render of layout(2 0) then raised
    # ZeroDivisionError).
    @pytest.mark.parametrize("layout,dims", [
        ("2 3", (2, 3)), ("  2 \t 3 ", (2, 3)), ("0 5", (1, 5)),
        ("2 0", (2, 1)), ("0 0", (1, 1)),
        ("999999999 1", (999999999, 1)), ("1234567890 1", None),
        ("2 3 4", None), ("2", None), ("auto", None), ("bs", None),
        ("g1:1,1", None), ("", None), (None, None)])
    def test_grid_dims(self, layout, dims):
        assert dr._dash_grid_dims(layout) == dims

    @pytest.mark.parametrize("layout,cells", [
        ("2 3", 6), ("0 5", 5), ("2 0", 2), ("10 10", 100),
        ("g1:1,1 g2:3,4", 12), ("g1:0,0 g2:0,1", 2),
        ("999999999 1", 999999999), ("1234567890 1", 10 ** 18)]
        + [(lax, None) for lax in _LAX])
    def test_the_measure_is_never_smaller_than_the_grid(self, layout, cells,
                                                        tmp_path):
        """Whatever the grid reader builds, the cell count measured first.

        The measure (``_dash_layout_cells``) is what ``_dash_cap_spec`` holds
        to the graphs limit before either mode builds anything; the grid is
        what the saved page's reader (``_compute_grid``: ``_dash_grid_dims``
        for rows and columns, ``_dash_placement_map`` for placements) builds
        from the same text.  They are the same number, or the measure says
        the text is larger than any limit (an index too long to read, which
        the cap draws as auto) or has no size of its own (auto is drawn).

        This used to compare the two only where ``_dash_grid_dims`` read the
        text -- three of its thirteen layouts -- and asked only that the
        measure be no smaller: a measure one row and one column short for
        every placement grid passed it (24sep2026)."""
        assert dr._dash_layout_cells(layout) == cells
        sp, dp = _write_inputs(tmp_path, _two_graph_spec(layout))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = dr.DashRenderer(sp, dp)
        names = ["g1", "g2"]
        auto = r._compute_grid(names, "auto")
        rows, cols = r._compute_grid(names, layout)
        if cells is None:
            assert (rows, cols) == auto
        elif cells == 10 ** 18:
            assert cells > dr._DASH_LIMITS["graphs"][1]
            assert (rows, cols) == auto
        else:
            assert rows * cols == cells

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
        # The test both modes run (DashRenderer._is_bootstrap_layout only
        # delegated to it, and WP-26 deleted it, 24sep2026).
        assert dr._dash_is_bs_layout(got)

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

    @pytest.mark.parametrize("layout,spec_of,cells", [
        ("2 0", _two_graph_spec, [(0, 0, "mpg"), (1, 0, "price")]),
        ("0 3", _three_graph_spec,
         [(0, 0, "mpg"), (0, 1, "price"), (0, 2, "foreign")]),
    ])
    def test_a_zero_in_a_grid_is_one_in_both_modes(self, layout, spec_of,
                                                   cells, tmp_path):
        """layout(R C) with a zero in it, read the same way by both modes.

        dash.ado refuses both (its grid form wants each number at least 1),
        so they reach the renderer only in a spec that did not come through
        it.  ``_dash_grid_dims`` reads each 0 as 1: layout(2 0) is 2 x 1 and
        layout(0 3) is 1 x 3.  The served template once read the grid with
        ``int()``, and a check that its source held the text
        ``_dash_grid_dims(layout_opt)`` was all that guarded it -- a reading
        that ignored that call's result passed.  Measured 24sep2026 on such a
        reading: layout(2 0) served an empty grid, no figure placed, and
        layout(0 3) fell through to the automatic 2 x 2 (the third figure at
        row 1, column 0).  layout(0 2) could not tell them apart: the
        automatic grid of two graphs is 1 x 2.  Each mode's own document is
        read: the saved page's embedded one, and a served session's."""
        spec = spec_of(layout)
        page, _msgs = _render(tmp_path, spec)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            served = _session(_load_app(_app_source(tmp_path, spec),
                                        "zero_grid"))
        assert _grid_cells(_page_document(page)) == cells
        assert _grid_cells(served) == cells

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
        """2,000 repeats of g1 make the page one placement of g1 makes.

        Each embedded root is one ``<div id=... data-root-id=...>``, and the
        page has exactly two -- g1 at its first place, then g2 -- each a
        root of the page's one document, each element id once.  Then the
        whole page: with its generated ids set aside it is the page of
        layout(bs: g1=6 g2=6), character for character (measured 24sep2026:
        equal, and two renders of one layout are equal too).  This used to
        allow up to four roots, where the page has two: a reader that kept
        a repeated name's first two places -- g1's div twice, one element
        id on two elements -- passed it."""
        page, msgs = _render(tmp_path, _two_graph_spec(
            "bs: " + "g1=6 " * 2000 + "g2=6"))
        said = [m for m in msgs if "placed more than once" in m]
        assert len(said) == 1, msgs
        assert said[0].endswith(
            "g1 is placed more than once; its first place is kept."), said
        divs = re.findall(r'<div id="([^"]+)" data-root-id="([^"]+)"', page)
        doc = _page_document(page)
        roots = {r.id: str(r.yaxis[0].axis_label) for r in doc.roots}
        assert [roots.get(rid) for _eid, rid in divs] == ["mpg", "price"]
        assert len({eid for eid, _rid in divs}) == 2
        once_dir = tmp_path / "once"
        once_dir.mkdir()
        once, _ = _render(once_dir, _two_graph_spec("bs: g1=6 g2=6"))

        def _ids_aside(text):
            text = re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-"
                          r"[0-9a-f]{12}", "UUID", text)
            return re.sub(r"\bp\d{4,}\b", "PID", text)

        assert _ids_aside(page) == _ids_aside(once)

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
        """200,000 nested lists are refused by the JSON reader as the spec
        is read -- a RecursionError "while decoding a JSON array", in a
        hundredth of a second (measured 24sep2026) -- and no page is
        written.

        This used to accept any of RecursionError, ValueError, TypeError
        and AttributeError: a main() that could render nothing at all
        (DashRenderer called without its data: TypeError) passed it, and so
        did a reader that swallowed the refusal and failed later on a list
        (AttributeError).  The same data and output path render a valid
        spec first, so the page that is absent is one main() writes."""
        dp = tmp_path / "data.json"
        dp.write_text(json.dumps(make_data_json(_DF)))
        out = tmp_path / "out.html"
        good = tmp_path / "good.json"
        good.write_text(json.dumps(make_spec([dict(_SCATTER)])))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            dr.main(str(good), str(dp), str(out))
        assert out.stat().st_size > 0
        out.unlink()
        sp = tmp_path / "deep.json"
        sp.write_text("[" * 200000 + "]" * 200000)
        t0 = time.monotonic()
        with pytest.raises(RecursionError,
                           match="while decoding a JSON array"):
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
        is charged to ONE first-contact window, so the cycle gets one
        client's 600: the first 600 answered, the other 900 refused, on a
        clock that stands still.  This asked only for at most 600 answered
        and at least 900 refused, so a first-contact window of 300 -- or of
        none, every trusted client refused -- passed it (24sep2026)."""
        ns = fresh_limiters.ns
        monkeypatch.setitem(ns, "_TRUST_FORWARDED_FOR", True)
        statuses = [_health(ns, _Req("10.7.7.8", **{
            "X-Forwarded-For": "198.18.%d.%d" % (i // 256, i % 256)}))[0]
            for i in range(1500)]
        assert ns["_HEALTH_LIMIT_RPM"] == 600
        assert statuses == [200] * 600 + [429] * 900


class _ServerRecorder:
    """Stands in for bokeh.server.server.Server: records its arguments."""
    calls = []

    def __init__(self, apps, **kw):
        type(self).calls.append(kw)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _LiveApp:
    """The generated app running itself -- ``python app.py --port P``, the
    launcher ``dash serve`` runs -- with ``BOKEH_ALLOW_WS_ORIGIN`` unset
    unless *env* sets it (``{port}`` in a value is the app's port).

    Stopped on every path.  test_server_serves.py's _Launched raises out of
    ``__enter__`` when the app exits early or never answers, and a context
    manager whose ``__enter__`` raises gets no ``__exit__``, so an app still
    starting was left running; here a failure while starting stops the
    process before it propagates.  The app's output goes to a file, not a
    pipe that a chatty app could fill and stall on, and is quoted when the
    app will not start.  ``--show`` is never passed: no browser opens."""

    def __init__(self, app_path, env=None):
        self.app = app_path
        self.env = dict(env or {})
        self.port = None
        self.proc = None
        self._log = None
        self._log_path = app_path + ".log"

    def __enter__(self):
        self.port = _free_port()
        env = {k: v for k, v in os.environ.items()
               if k != "BOKEH_ALLOW_WS_ORIGIN"}
        env.update({k: v.format(port=self.port) for k, v in self.env.items()})
        try:
            self._log = open(self._log_path, "w", encoding="utf-8")
            self.proc = subprocess.Popen(
                [sys.executable, self.app, "--port", str(self.port)],
                cwd=os.path.dirname(self.app), env=env,
                stdout=self._log, stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 60
            while not self._answers():
                if self.proc.poll() is not None:
                    raise AssertionError(
                        "the app exited early:\n" + self._tail())
                if time.monotonic() > deadline:
                    raise AssertionError(
                        "the app never answered:\n" + self._tail())
                time.sleep(0.2)
        except BaseException:
            self._stop()
            raise
        return self

    def __exit__(self, *exc):
        self._stop()
        return False

    def _answers(self):
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:%d/health" % self.port,
                    timeout=5) as r:
                return r.status == 200
        except OSError:          # refused, reset, or an HTTP error status
            return False

    def _stop(self):
        if self.proc is not None and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=15)
        if self._log is not None and not self._log.closed:
            self._log.close()

    def _tail(self):
        self._log.flush()
        with open(self._log_path, encoding="utf-8", errors="replace") as fh:
            return fh.read()[-3000:]

    def session(self, origin):
        """``(status, first message type)`` for a browser's websocket
        handshake sent with *origin* -- the page fetched for its session
        token, then ``/ws`` asked to upgrade with the Bokeh subprotocol and
        that token, as BokehJS asks.  ``(101, "ACK")`` is a session opened;
        a refusal is its status and None.  Measured 24sep2026 on this app:
        an origin it allows is answered 101 and then the server's ACK, one
        it does not is answered 403 before any upgrade."""
        with urllib.request.urlopen("http://127.0.0.1:%d/" % self.port,
                                    timeout=10) as r:
            page = r.read().decode("utf-8", "replace")
        token = re.search(r'"token":\s*"([^"]+)"', page)
        assert token, "the served page carries no session token"
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = ("GET /ws HTTP/1.1\r\n"
                   "Host: 127.0.0.1:%d\r\n"
                   "Upgrade: websocket\r\n"
                   "Connection: Upgrade\r\n"
                   "Sec-WebSocket-Key: %s\r\n"
                   "Sec-WebSocket-Version: 13\r\n"
                   "Sec-WebSocket-Protocol: bokeh, %s\r\n"
                   "Origin: %s\r\n\r\n") % (self.port, key, token.group(1),
                                            origin)
        with socket.create_connection(("127.0.0.1", self.port),
                                      timeout=10) as s:
            s.sendall(request.encode("utf-8"))
            buf = b""
            while b"\r\n\r\n" not in buf:
                chunk = s.recv(4096)
                assert chunk, "the connection closed inside the response"
                buf += chunk
            head, _, buf = buf.partition(b"\r\n\r\n")
            status = re.match(rb"HTTP/1\.[01] (\d{3}) ", head)
            assert status, head[:200]
            if int(status.group(1)) != 101:
                return int(status.group(1)), None

            def _take(n):
                nonlocal buf
                while len(buf) < n:
                    chunk = s.recv(4096)
                    assert chunk, "the connection closed inside a frame"
                    buf += chunk
                out, buf = buf[:n], buf[n:]
                return out

            # The server's first frame, unmasked: the ACK message's header.
            b0, b1 = _take(2)
            assert b0 & 0x0F == 1, "the first frame is not text: %r" % b0
            size = b1 & 0x7F
            if size == 126:
                size = struct.unpack(">H", _take(2))[0]
            elif size == 127:
                size = struct.unpack(">Q", _take(8))[0]
            return 101, json.loads(_take(size))["msgtype"]


@pytest.fixture(scope="class")
def live_app(tmp_path_factory):
    """One served app, running itself with no BOKEH_ALLOW_WS_ORIGIN."""
    tmp = tmp_path_factory.mktemp("live_origin")
    _app_source(tmp, make_spec([dict(_SCATTER)]))
    with _LiveApp(os.path.join(str(tmp), "app.py")) as app:
        yield app


def _launcher_said(app):
    """What a running _LiveApp's launcher has written to its console."""
    with open(app._log_path, encoding="utf-8") as fh:
        return fh.read()


class TestSessionOrigin:
    """The websocket Origin check.  The served app passes Bokeh an
    allowlist; Bokeh lower-cases the Origin's host:port and matches it with
    ``check_allowlist``.  Nothing tested either half before.

    The origins are sent to the app running itself, as ``dash serve`` runs
    it, in the handshake a browser makes (``_LiveApp.session``).  They used
    to be matched in the test process: the allowlist ``_dash_server_app``
    handed a stand-in Server, run through Bokeh's ``check_allowlist`` after
    the test had lower-cased the origin itself.  Measured 24sep2026, both
    of these passed that: a launcher that added ``*`` to the allowlist it
    started (``_dash_server_app`` untouched), and an origin check that no
    longer lower-cased what it was sent."""

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

    # {P} is the live app's port, {Q} the port after it.
    @pytest.mark.serve
    @pytest.mark.parametrize("origin", [
        "http://evil.example:{P}",
        "http://localhost:{P}.evil.example",
        "http://localhost.evil.example:{P}",
        "http://127.0.0.1.nip.io:{P}",
        "http://localhost:{Q}",
        "http://localhost",
        "http://0.0.0.0:{P}",
        "http://[::1]:{P}",
        "null",
        "http://localhost:{P}@evil.example",
        "http://evil.example/#localhost:{P}",
        "http://\u217cocalhost:{P}",          # Roman numeral fifty: a homoglyph
    ])
    def test_a_foreign_origin_is_refused(self, live_app, origin):
        sent = origin.format(P=live_app.port, Q=live_app.port + 1)
        assert live_app.session(sent) == (403, None), sent
        # The same handshake from loopback opens a session: the refusal is
        # the origin check's, not an app that opens none.
        assert live_app.session(
            "http://localhost:%d" % live_app.port) == (101, "ACK")

    @pytest.mark.serve
    @pytest.mark.parametrize("origin", ["http://localhost:{P}",
                                        "http://127.0.0.1:{P}",
                                        "http://LOCALHOST:{P}"])
    def test_loopback_is_accepted(self, live_app, origin):
        sent = origin.format(P=live_app.port)
        assert live_app.session(sent) == (101, "ACK"), sent

    def test_an_operator_origin_is_added_literally(self, served_app,
                                                   monkeypatch):
        _ServerRecorder.calls = []
        monkeypatch.setitem(served_app, "Server", _ServerRecorder)
        served_app["_dash_server_app"](port=5006,
                                       origins=["dash.example.org:5006"])
        (kw,) = _ServerRecorder.calls
        assert "dash.example.org:5006" in kw["allow_websocket_origin"]
        assert "*" not in kw["allow_websocket_origin"]

    @pytest.mark.serve
    def test_bokeh_lets_the_environment_replace_it(self, live_app, tmp_path,
                                                   monkeypatch):
        """Pinned third-party behaviour (BR-20.3): Bokeh's websocket handler
        uses BOKEH_ALLOW_WS_ORIGIN, when it is set, INSTEAD of the app's
        allowlist.  An operator who sets it owns the origin policy.

        What the code promises, read 24sep2026 in bokeh 3.9's
        ``WSHandler.check_origin``: when the setting is non-empty,
        ``allowed_hosts = set(settings.allowed_ws_origin())`` replaces
        ``self.application.websocket_origins`` -- the list the app passed --
        where Bokeh's own ``bokeh serve`` documentation (the docstring of
        bokeh/command/subcommands/serve.py) speaks of "additional hosts".
        So the app is run with the variable naming one origin: that origin
        opens a session, and loopback -- the app's own allowlist -- is
        refused.
        This used to read the setting in the test process and find the
        word ``allowed_ws_origin`` in Bokeh's source; a Bokeh that extended
        the allowlist instead, and a launcher that dropped the variable,
        both passed it (24sep2026)."""
        from bokeh.settings import settings
        monkeypatch.setenv("BOKEH_ALLOW_WS_ORIGIN", "a.example:1,b.example:2")
        assert settings.allowed_ws_origin() == ["a.example:1", "b.example:2"]
        # Without the variable (the class's app): loopback opens a session
        # and the origin about to be allowed is refused -- both answers can
        # be told apart, and the variable is what changes them.
        assert live_app.session(
            "http://evil.example:%d" % live_app.port) == (403, None)
        assert live_app.session(
            "http://localhost:%d" % live_app.port) == (101, "ACK")
        _app_source(tmp_path, make_spec([dict(_SCATTER)]))
        with _LiveApp(os.path.join(str(tmp_path), "app.py"),
                      {"BOKEH_ALLOW_WS_ORIGIN": "evil.example:{port}"}) as app:
            p = app.port
            assert app.session("http://evil.example:%d" % p) == (101, "ACK")
            assert app.session("http://localhost:%d" % p) == (403, None)
            assert app.session("http://127.0.0.1:%d" % p) == (403, None)
            assert app.session("http://evil.example:%d" % (p + 1)) == (
                403, None)
            said = _launcher_said(app)
        # The launcher verifies the variable at start (CLAUDE.md rule 15)
        # and says what it does, naming what it admits; it used to say
        # nothing, and the page at the address it printed stayed blank
        # (24sep2026).  Looked for by its own "dash: " opening: Bokeh's
        # refusals name the variable and the origin too.  The app without
        # the variable says nothing of it.
        note = [ln for ln in said.splitlines()
                if ln.startswith("dash: BOKEH_ALLOW_WS_ORIGIN")]
        assert len(note) == 1, said
        assert "instead of" in note[0], note
        assert ("evil.example:%d" % p) in note[0], note
        assert "any web site" not in said, said
        assert "dash: BOKEH_ALLOW_WS_ORIGIN" not in _launcher_said(live_app)

    @pytest.mark.serve
    def test_a_star_in_the_environment_is_warned_of(self, tmp_path):
        """BOKEH_ALLOW_WS_ORIGIN=* admits every origin -- Bokeh's rule, the
        operator's to choose (above) -- so any web site the user visits
        while the dashboard runs can open a session with it and read what
        it draws.  The launcher says so, prominently, at start; it said
        nothing (measured 24sep2026)."""
        _app_source(tmp_path, make_spec([dict(_SCATTER)]))
        with _LiveApp(os.path.join(str(tmp_path), "app.py"),
                      {"BOKEH_ALLOW_WS_ORIGIN": "*"}) as app:
            assert app.session("http://attacker.example") == (101, "ACK")
            said = _launcher_said(app)
        assert "dash: BOKEH_ALLOW_WS_ORIGIN" in said, said
        assert "any web site can open a session" in said, said

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


# Bokeh 3.8.0's host matcher, in behaviour (bokeh/server/util.py
# match_host): it compares only as many dot-separated labels as the pattern
# has, so a host that merely BEGINS with an allowed one matches it.  Bokeh
# 3.9 requires the counts to be equal.  Planted into the app's own process,
# ahead of the app, so the development interpreter's Bokeh 3.9 cannot hide
# what the one Stata's Python ships does.
_LENIENT_BOKEH_APP = """\
import runpy
import sys

import bokeh.server.util as _bokeh_util


def _lenient_match_host(host, pattern):
    host_port = None
    if ':' in host:
        host, host_port = host.rsplit(':', 1)
    pattern_port = None
    if ':' in pattern:
        pattern, pattern_port = pattern.rsplit(':', 1)
        if pattern_port == '*':
            pattern_port = None
    if pattern_port is not None and host_port != pattern_port:
        return False
    host_parts = host.split('.')
    pattern_parts = pattern.split('.')
    if len(pattern_parts) > len(host_parts):
        return False
    return all(h == p or p == '*' for h, p in zip(host_parts, pattern_parts))


_bokeh_util.match_host = _lenient_match_host
_app = __APP__
sys.argv = [_app] + sys.argv[1:]
runpy.run_path(_app, run_name='__main__')
"""


@pytest.fixture(scope="class")
def lenient_live_app(tmp_path_factory):
    """The served app running itself with Bokeh 3.8's host matcher."""
    tmp = tmp_path_factory.mktemp("lenient_origin")
    _app_source(tmp, make_spec([dict(_SCATTER)]))
    app = os.path.join(str(tmp), "app.py")
    wrapper = os.path.join(str(tmp), "lenient_app.py")
    with open(wrapper, "w", encoding="utf-8") as fh:
        fh.write(_LENIENT_BOKEH_APP.replace("__APP__", repr(app)))
    with _LiveApp(wrapper) as live:
        yield live


class TestSessionOriginUnderALenientBokeh:
    """Bokeh before 3.9 admitted a websocket origin whose host merely
    begins with an allowed one.  Measured 24sep2026 with pytest under
    Stata's own interpreter, /opt/anaconda3/bin/python3 with bokeh 3.8.0:
    TestSessionOrigin's handshakes from http://localhost.evil.example:<port>
    and http://127.0.0.1.nip.io:<port> were answered 101 and ACK -- a page
    from a DNS name that starts with localhost, or from a rebinding
    service's name for 127.0.0.1, opened a session and could read the
    dashboard -- where the development interpreter's bokeh 3.9 refuses
    them.  dash checks origins label for label itself
    (_dash_harden_origin_check), whatever Bokeh it runs under."""

    @pytest.mark.serve
    @pytest.mark.parametrize("origin", [
        "http://localhost.evil.example:{P}",
        "http://127.0.0.1.nip.io:{P}",
        "http://127.0.0.1.evil.example:{P}",
        "http://localhost.localhost:{P}",
    ])
    def test_a_host_that_begins_with_an_allowed_one_is_refused(
            self, lenient_live_app, origin):
        sent = origin.format(P=lenient_live_app.port)
        assert lenient_live_app.session(sent) == (403, None), sent
        assert lenient_live_app.session(
            "http://localhost:%d" % lenient_live_app.port) == (101, "ACK")

    @pytest.mark.serve
    def test_the_launcher_says_it_checks_origins_itself(self,
                                                        lenient_live_app):
        said = _launcher_said(lenient_live_app)
        assert "checks each websocket origin label for label" in said, said


class TestTheStrictHostMatcher:
    """_dash_strict_match_host holds Bokeh 3.9's rules, and
    _dash_harden_origin_check installs it only over a lenient matcher."""

    @pytest.mark.parametrize("host, pattern, want", [
        # Bokeh 3.9's own documented examples.
        ("192.168.0.1:80", "192.168.0.1:80", True),
        ("192.168.0.1:80", "192.168.0.1", True),
        ("192.168.0.1:80", "192.168.0.1:8080", False),
        ("192.168.0.1", "192.168.0.2", False),
        ("192.168.0.1", "192.168.*.*", True),
        ("alice", "alice", True),
        ("alice:80", "alice", True),
        ("alice", "bob", False),
        ("example.com", "example.com.net", False),
        ("example.com.bad.com", "example.com", False),
        ("alice", "*", True),
        ("alice", "*:*", True),
        ("alice:80", "*", True),
        ("alice:80", "*:80", True),
        ("alice:8080", "*:80", False),
        # The hosts Bokeh 3.8 admitted.
        ("localhost.evil.example:5006", "localhost:5006", False),
        ("127.0.0.1.nip.io:5006", "127.0.0.1:5006", False),
        ("localhost.:5006", "localhost:5006", False),
        # Loopback and an IPv6 literal, exactly.
        ("localhost:5006", "localhost:5006", True),
        ("127.0.0.1:5006", "127.0.0.1:5006", True),
        ("[::1]:5006", "[::1]:5006", True),
        ("[::1]:5007", "[::1]:5006", False),
    ])
    def test_a_host_matches_label_for_label(self, host, pattern, want):
        assert dr._dash_strict_match_host(host, pattern) is want

    def test_a_lenient_matcher_is_replaced(self, monkeypatch):
        import bokeh.server.util as bokeh_util

        def lenient(host, pattern):
            return host.split(":")[0].startswith(pattern.split(":")[0])

        monkeypatch.setattr(bokeh_util, "match_host", lenient)
        assert dr._dash_harden_origin_check() is True
        assert bokeh_util.match_host is dr._dash_strict_match_host
        assert not bokeh_util.check_allowlist(
            "localhost.evil.example:5006", ["localhost:5006"])
        assert bokeh_util.check_allowlist("localhost:5006",
                                          ["localhost:5006"])

    def test_a_strict_matcher_is_left_alone(self, monkeypatch):
        import bokeh.server.util as bokeh_util

        def strict(host, pattern):
            return dr._dash_strict_match_host(host, pattern)

        monkeypatch.setattr(bokeh_util, "match_host", strict)
        assert dr._dash_harden_origin_check() is False
        assert bokeh_util.match_host is strict


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
        """order() of 100,000 keys -- 0, 1, 2 over and over -- is read in
        bounded time and drawn as twoway draws it, from the graph's own two
        keys.

        twoway draws every key order() lists, a repeat as often as it is
        listed, and drops a number that is no key.  Measured 24sep2026 in
        Stata 19.5 on (scatter mpg weight) (scatter price weight), counting
        the key labels in the exported SVG: order(1 2 1 2) drew each key
        twice, and this very list drew 33,333 of each -- 66,666 entries,
        after more than ten minutes; dash takes 2 s.  The entries are
        references to the two keys the graph has, not 66,666 keys of their
        own.  This used to check only that a page came back: a renderer
        that built a new key for every listed number (66,666 LegendItem
        models on the page, rendered in 15 s) passed it, and so did one
        that dropped the order in silence."""
        spec = make_spec([dict(_SCATTER), dict(_SCATTER2)])
        spec["graphs"][0]["graph_options"]["legend"] = (
            "order(" + " ".join(str(i % 3) for i in range(100000)) + ")")
        t0 = time.monotonic()
        page, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        doc = _page_document(page)
        legends = list(doc.select({"type": Legend}))
        assert len(legends) == 1, legends
        items = list(legends[0].items)
        assert [_text_of(it.label) for it in items] == ["mpg",
                                                         "price"] * 33333
        assert len(list(doc.select({"type": LegendItem}))) == 2
        assert len({it.id for it in items}) == 2

    def test_a_long_legend_label_is_escaped_once(self, tmp_path):
        """label(1 "...") of 20,000 "<b>" becomes key 1's label as written,
        held once, and escaped once on the page.

        A legend label is text BokehJS draws, so the model carries the raw
        text, and the page's only escaping is Bokeh's own, of the document
        it embeds: the label is on the page once, as 20,000 ``&lt;b&gt;``.
        This used to check that "<b><b>" was not on the page -- it never
        is, since the page escapes its document -- and that the page was
        under 3.2 MB: a label escaped before it reached the model (drawn as
        ``&lt;b&gt;``, on the page as ``&amp;lt;b&amp;gt;``) passed it, and
        so did a label that was dropped (24sep2026)."""
        text = "<b>" * 20000
        spec = make_spec([dict(_SCATTER), dict(_SCATTER2)])
        spec["graphs"][0]["graph_options"]["legend"] = 'label(1 "%s")' % text
        t0 = time.monotonic()
        page, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        doc = _page_document(page)
        legends = list(doc.select({"type": Legend}))
        assert len(legends) == 1, legends
        assert [_text_of(it.label) for it in legends[0].items] == [
            text, "price"]
        assert _holding(doc, text) == [("LegendItem", "label")]
        (block,) = _page_blocks(page)
        assert block.count("&lt;b&gt;" * 20000) == 1
        assert "&amp;lt;b&amp;gt;" not in block


class TestGraphTextBounds:

    def test_a_long_title_is_drawn_once_in_bounded_time(self, tmp_path):
        """A 200,000-character title and note are each drawn once, as
        written: the title by the figure's Title, the note by one Label.

        This used to check that "<i>x</i><i>x</i>" was not on the page --
        it never is, since the page HTML-escapes the document it embeds --
        and that the page was under 6 MB, room for eight copies of each: a
        title escaped before it reached its model, and a title drawn a
        second time, both passed it (24sep2026).  The note now has a text
        of its own, so each text is known by what holds it."""
        title = "<i>x</i>" * 25000   # 200,000 characters
        note = "<u>y</u>" * 25000
        spec = make_spec([dict(_SCATTER)])
        spec["graphs"][0]["graph_options"]["title"] = title
        spec["graphs"][0]["graph_options"]["note"] = note
        t0 = time.monotonic()
        page, _msgs = _render(tmp_path, spec)
        assert time.monotonic() - t0 < 30
        doc = _page_document(page)
        assert [t.text for t in doc.select({"type": Title})] == [title]
        assert [lb.text for lb in doc.select({"type": Label})] == [note]
        assert _holding(doc, title) == [("Title", "text")]
        assert _holding(doc, note) == [("Label", "text")]
        (block,) = _page_blocks(page)
        assert block.count(_htmllib.escape(title, quote=False)) == 1
        assert block.count(_htmllib.escape(note, quote=False)) == 1
        assert "&amp;lt;" not in block
