"""program_coverage_map.py -- which test exercises each Stata program and
Mata function dash ships (WP-24 AC-24.3, GAPS.md L7).

Every ``program define`` in dash.ado and dash_setup.ado and every function
in dash_parse.mata has an entry here, and test_program_coverage_map.py fails
when one appears without an entry, when an entry names a unit that is gone,
or when an entry names a test that does not exist.

A reference is ``"<script>:<case id>"``, a certification-script case that
displays ``"<case id> PASS"`` (itself, or through the script's helper that
displays one), or ``"<script>"`` alone for a script that shows no case ids
and names the unit in its code.  The first reference is the strongest: a
case that calls the unit by name and asserts on what it returns where one
exists (``direct``), otherwise a case whose assertion depends on the unit's
output (``e2e``, with what it depends on).

HOW THE MAP WAS MEASURED
------------------------
scripts/measure_stata_coverage.py instruments a scratch copy of the tree so
that each unit records its entry, then runs the certification scripts.
Measured 24sep2026: the whole suite at 68327a8 (59 passed, 0 failed,
0 skipped) entered 61 of its 63 ado programs and 52 of its 55 Mata
functions; dash_setup was entered only by test_setup_honesty's HON-14/15,
whose syntax line refuses the call, so its body never ran.  The units
a17c552 and a2c7502 added were measured by running the scripts that test
them (test_parser, test_registry_collision) with test_program_coverage:
every one is executed.  Which scripts execute a unit comes from those runs;
whether an assertion depends on it, from reading the case.

No pytest file runs Stata: the Python suite reads dash.ado and
dash_parse.mata as text at most, so none of these units is executed by it.
"""

#: file -> {unit: (reference, ...)}.  Order follows the source files.
COVERAGE = {
    "dash.ado": {
        # e2e: the subcommand router -- a plot, kpi, clear and build each reach
        # their program and assert what that program makes.
        "dash": ("test_e2e_single.cscript:P1C-15a",
                 "test_e2e_kpi.cscript:P2-76",
                 "test_clear_registry.cscript:CLR-01"),
        "_dash_python_ok": ("test_env_guards.cscript:ENV-01",
                            "test_env_guards.cscript:ENV-03"),
        "_dash_require_python": ("test_env_guards.cscript:ENV-06",
                                 "test_env_guards.cscript:ENV-05"),
        "_dash_require_mata": ("test_env_guards.cscript:ENV-10",
                               "test_program_coverage.cscript:PC-30"),
        "_dash_find_render": ("test_render_locate.cscript:LOC-04",
                              "test_render_locate.cscript:LOC-09"),
        # e2e: the page it renders is searched for Bokeh's embed.
        "_dash_do_render": ("test_e2e_single.cscript:P1C-15c",
                            "test_render_locate.cscript:LOC-08"),
        # e2e: saving() into a directory that does not exist is twoway's
        # r(603), naming it, on every route, before rendering.
        "_dash_saving_dir": ("test_json_escaping.cscript:JSE-52",),
        "_dash_validate_path": ("test_path_validation.cscript:PV-01",
                                "test_path_validation.cscript:PV-02",
                                "test_path_validation.cscript:PV-04"),
        "_dash_json_str": ("test_json_escaping.cscript:JSE-01",
                           "test_json_escaping.cscript:JSE-27"),
        # no caller (UNCALLED); direct.
        "_dash_kv_json": ("test_program_coverage.cscript:PC-29",),
        # e2e: side-title spellings land in the graph's JSON at every level.
        "_dash_parse_graph_opts": ("test_alias_semantics.cscript:AS-06",
                                   "test_parser.cscript:P1A-36"),
        # TP-13: twoway's minimum abbreviations both ways, and clwidth()'s
        # bounds, measured against twoway.
        "_dash_parse_plot_opts": ("test_parser.cscript:P1A-34",
                                  "test_parser.cscript:P1A-35",
                                  "test_twoway_option_parity.cscript:TP-13"),
        "_dash_parse_varpart_std": ("test_parser.cscript:P1A-31",
                                    "test_varlist_expansion.cscript:V2-01"),
        "_dash_parse_varpart_1v": ("test_parser.cscript:P1A-43",),
        # e2e: every range type's "yvar1","yvar2","xvar" keys.
        "_dash_parse_varpart_3v": ("test_parser.cscript:P1A-56",),
        # e2e: pccapsym's "y1var".."x2var" keys.
        "_dash_parse_varpart_4v": ("test_parser.cscript:P1A-52",
                                   "test_parser.cscript:P1A-56"),
        "_dash_parse_varpart_any": ("test_parser.cscript:P1A-75",
                                    "test_varlist_expansion.cscript:V2-06"),
        # e2e: the registered graph's if_expr/in_expr, and the r(198)s.
        "_dash_graph_qualifier": ("test_help_claims_1.cscript:HC1-01",
                                  "test_help_claims_1.cscript:HC1-02",
                                  "test_help_claims_1.cscript:HC1-04"),
        # e2e: bw() is bwidth, barwidth or named, per type; kdensity width().
        "_dash_fold_bw": ("test_alias_semantics.cscript:AS-01",
                          "test_alias_semantics.cscript:AS-02",
                          "test_help_claims_6.cscript:HC6-06"),
        # e2e: the cl triple kept or dropped per plot type.
        "_dash_fold_cl": ("test_twoway_option_parity.cscript:TP-01",),
        # e2e: mlabel() refused or dropped exactly where twoway does.
        "_dash_fold_mlab": ("test_twoway_option_parity.cscript:TP-08",
                            "test_twoway_option_parity.cscript:TP-12"),
        # e2e: colorvar() and jitter() named in the note per type.
        "_dash_fold_typed": ("test_help_claims_7.cscript:HC7-02",
                             "test_help_claims_7.cscript:HC7-03"),
        # e2e: legend(top) and the rest refused, labels accepted.
        "_dash_check_legend": ("test_help_claims_7.cscript:HC7-01",),
        "_dash_shipped_schemes": ("test_custom_scheme.cscript:CS-12",),
        # e2e: the table's bounds and normalisations, through the commands.
        "_dash_option_rules": ("test_option_validation.cscript:OV-104",
                               "test_option_validation.cscript:OV-128"),
        "_dash_validate_value": ("test_option_validation.cscript:OV-100",
                                 "test_option_validation.cscript:OV-109",
                                 "test_option_validation.cscript:OV-116"),
        "_dash_validate_opts": ("test_option_validation.cscript:OV-104",
                                "test_option_validation.cscript:OV-126"),
        # e2e: every default and ceiling read back through _dash_limit.
        "_dash_limit_table": ("test_adversarial.cscript:P19-05",),
        "_dash_count_fmt": ("test_adversarial.cscript:P19-22",),
        "_dash_limit": ("test_adversarial.cscript:P19-05",
                        "test_adversarial.cscript:P19-17",
                        "test_adversarial.cscript:P19-18"),
        "_dash_limits_json": ("test_adversarial.cscript:P19-14",
                              "test_adversarial.cscript:P19-15"),
        # e2e: the refusal's exact words and rc 134.
        "_dash_graph_cap": ("test_adversarial.cscript:P19-01",
                            "test_adversarial.cscript:P19-04"),
        "_dash_plot_cap_refuse": ("test_adversarial.cscript:P19-07",
                                  "test_adversarial.cscript:P19-09"),
        "_dash_cell_cap": ("test_adversarial.cscript:P19-11",
                           "test_adversarial.cscript:P19-23"),
        # e2e: the option keys in a segment's JSON.
        "_dash_plot_opts_to_json": ("test_parser.cscript:P1A-52",
                                    "test_parser.cscript:P1A-47"),
        # no caller (UNCALLED), and no test: it cannot do what it says.
        "_dash_graph_opts_to_json": (),
        # e2e: "weight":"aweight","wexp":"price" in the plot's options.
        "_dash_seg_weight_s": ("test_statistical_options.cscript:SO-01",
                               "test_statistical_options.cscript:SO-02"),
        "_dash_plottype_families": ("test_parser.cscript:P1A-56",),
        "_dash_process_segment": ("test_parser.cscript:P1A-31",
                                  "test_parser.cscript:P1A-52"),
        "_dash_formats_json": ("test_program_coverage.cscript:PC-01",
                               "test_program_coverage.cscript:PC-02",
                               "test_program_coverage.cscript:PC-03",
                               "test_program_coverage.cscript:PC-04"),
        "_dash_empty_data": ("test_parser.cscript:P1A-75",
                             "test_parser.cscript:P1A-72"),
        "_dash_date_fmts_swap": ("test_program_coverage.cscript:PC-05",
                                 "test_program_coverage.cscript:PC-06",
                                 "test_program_coverage.cscript:PC-07",
                                 "test_program_coverage.cscript:PC-09"),
        "_dash_date_fmts_restore": ("test_program_coverage.cscript:PC-05",
                                    "test_program_coverage.cscript:PC-06",
                                    "test_program_coverage.cscript:PC-07",
                                    "test_program_coverage.cscript:PC-11"),
        # e2e: the note names each unsupported option once, by name.
        "_dash_report_ignored": ("test_twoway_option_parity.cscript:TP-06",
                                 "test_twoway_option_parity.cscript:TP-07"),
        # e2e: paren mode keeps the last segment's title.
        "_dash_plot": ("test_graph_option_scope.cscript:GOS-01",
                       "test_adversarial.cscript:P20-33"),
        "_dash_browser_wanted": ("test_nodraw_honoured.cscript:ND-04",),
        "_dash_registry_nodraw": ("test_nodraw_honoured.cscript:ND-05",),
        "_dash_dashboard_browser": ("test_serve_browser.cscript:SB-01",
                                    "test_serve_browser.cscript:SB-03",
                                    "test_serve_browser.cscript:SB-05"),
        # Each platform's command, ordinary and hostile paths, by dryrun;
        # stub openers receive the path whole; dash build reaches it.
        "_dash_open_page": ("test_serve_browser.cscript:SB-14",
                            "test_serve_browser.cscript:SB-19",
                            "test_help_claims_2.cscript:HC2-30"),
        # e2e: the superseded item's globals are gone, a neighbour's kept.
        "_dash_drop_item": ("test_registry_collision.cscript:REG-05",
                            "test_registry_collision.cscript:REG-13",
                            "test_registry_collision.cscript:REG-26"),
        "_dash_name_split": ("test_registry_collision.cscript:REG-17",
                             "test_registry_collision.cscript:REG-36"),
        # e2e: the refusal, and nothing registered or dropped.
        "_dash_refuse_second_name": ("test_registry_collision.cscript:REG-37",
                                     "test_registry_collision.cscript:REG-38",
                                     "test_registry_collision.cscript:REG-40"),
        "_dash_register_graph": ("test_varlist_expansion.cscript:V2-08",
                                 "test_registry_collision.cscript:REG-01"),
        # QL-14/15: each layer's own if and in select its rows, and the
        # export carries every row they need.
        "_dash_render_immediate": ("test_varlist_expansion.cscript:V2-09",
                                   "test_varlist_expansion.cscript:V2-07",
                                   "test_json_escaping.cscript:JSE-08",
                                   "test_qualifier_literals.cscript:QL-14",
                                   "test_qualifier_literals.cscript:QL-15"),
        "_dash_clear": ("test_clear_registry.cscript:CLR-01",
                        "test_clear_registry.cscript:CLR-04"),
        # e2e: the card's value in the page.
        "_dash_kpi": ("test_e2e_kpi.cscript:P2-76",
                      "test_help_claims_4.cscript:HC4-01"),
        "_dash_prepare_spec": ("test_json_escaping.cscript:JSE-15",
                               "test_program_coverage.cscript:PC-10",
                               "test_program_coverage.cscript:PC-13"),
        "_dash_build": ("test_render_locate.cscript:LOC-08",
                        "test_e2e_single.cscript:P1C-18c"),
        "_dash_serve_spec": ("test_serve_launch.cscript:SRV-01",
                             "test_export.cscript:EXP-04",
                             "test_adversarial.cscript:P20-14"),
        # e2e: a real dash serve, ended by timeout(1).
        # SRV-20: the renderer's path, holding a payload, reaches Python
        # as data (the serve-side twin of LOC-17).
        "_dash_serve": ("test_help_claims_4.cscript:HC4-19",
                        "test_serve_browser.cscript:SB-02",
                        "test_serve_launch.cscript:SRV-20"),
    },
    "dash_setup.ado": {
        # e2e: every branch this machine can reach, installing nothing.
        "dash_setup": ("test_program_coverage.cscript:PC-15",
                       "test_program_coverage.cscript:PC-16",
                       "test_program_coverage.cscript:PC-19",
                       "test_program_coverage.cscript:PC-23",
                       "test_setup_honesty.cscript:HON-14"),
        "_dash_pymin": ("test_setup_python_gate.cscript",
                        "test_program_coverage.cscript:PC-16"),
        "_dash_pyver_ok": ("test_setup_python_gate.cscript",
                           "test_setup_honesty.cscript:HON-08"),
        "_dash_pkg_version": ("test_setup_version_gate.cscript:SVG-02",
                              "test_setup_injection.cscript:INJ-11",
                              "test_program_coverage.cscript:PC-22"),
        "_dash_setup_summary": ("test_setup_honesty.cscript:HON-01",
                                "test_setup_honesty.cscript:HON-04",
                                "test_program_coverage.cscript:PC-18"),
        "_dash_setup_gate": ("test_setup_honesty.cscript:HON-07",
                             "test_setup_injection.cscript:INJ-01",
                             "test_program_coverage.cscript:PC-21"),
        "_dash_setup_check_files": ("test_setup_honesty.cscript:HON-17",
                                    "test_program_coverage.cscript:PC-25",
                                    "test_program_coverage.cscript:PC-26"),
    },
    "dash_parse.mata": {
        # e2e: through _dash_json_str_args; direct in PC-28.
        "_json_escape": ("test_json_escaping.cscript:JSE-01",
                         "test_program_coverage.cscript:PC-28"),
        # no caller but _dash_html_esc (UNCALLED); direct.
        "_html_escape": ("test_program_coverage.cscript:PC-27",),
        "_dash_json_esc": ("test_program_coverage.cscript:PC-28",),
        "_dash_html_esc": ("test_program_coverage.cscript:PC-27",),
        # e2e: _dash_json_str is this function's one caller.
        "_dash_json_str_args": ("test_json_escaping.cscript:JSE-01",
                                "test_json_escaping.cscript:JSE-27"),
        "_is_utf8": ("test_utf8_validation.cscript:UTF-01",
                     "test_utf8_validation.cscript:UTF-10"),
        "_dash_path_badchar": ("test_path_validation.cscript:PV-03b",
                               "test_program_coverage.cscript:PC-30"),
        "_dash_check_utf8": ("test_utf8_validation.cscript:UTF-12",
                             "test_utf8_validation.cscript:UTF-11"),
        "_dash_smcl_text": ("test_echo_text.cscript:ECH-01",
                            "test_echo_text.cscript:ECH-02"),
        "_dash_say": ("test_echo_text.cscript:ECH-03",
                      "test_echo_text.cscript:ECH-04"),
        "_dash_is_digits": ("test_echo_text.cscript:ECH-05",),
        "_dash_ascii_in": ("test_echo_text.cscript:ECH-06",),
        # e2e: what a percentile is stored as, and every refusal.
        "_dash_kpi_pctile": ("test_help_claims_4.cscript:HC4-04",
                             "test_help_claims_4.cscript:HC4-06"),
        "_dash_layout_scan": ("test_echo_text.cscript:ECH-10",),
        "_dash_layout_cells": ("test_echo_text.cscript:ECH-07",
                               "test_echo_text.cscript:ECH-09"),
        "_dash_is_name": ("test_echo_text.cscript:ECH-10",),
        "_dash_layout_refusal": ("test_echo_text.cscript:ECH-11",),
        # e2e: through _dash_expand_plottype, every abbreviation.
        "_expand_plottype_str": ("test_parser.cscript:P1A-40",
                                 "test_parser.cscript:P1A-57"),
        "_dash_expand_plottype": ("test_parser.cscript:P1A-40",
                                  "test_parser.cscript:P1A-57"),
        "_dash_undrawn_plottype": ("test_parser.cscript:P1A-58",
                                   "test_parser.cscript:P1A-59"),
        # e2e: _dash_imm_gettoken's asserted tokens, quotes and compound
        # quotes among them, are made by these four.
        "_dash_imm_dq_end": ("test_parser.cscript:P1A-67",),
        "_dash_imm_cq_at": ("test_parser.cscript:P1A-67",),
        "_dash_imm_cq_end": ("test_parser.cscript:P1A-67",),
        "_dash_imm_next": ("test_parser.cscript:P1A-67",),
        "_dash_imm_gettoken": ("test_parser.cscript:P1A-67",),
        # e2e: _dash_imm_number's asserted numbers are made by these three.
        "_dash_imm_trim": ("test_parser.cscript:P1A-67",),
        "_dash_imm_numchars": ("test_parser.cscript:P1A-67",),
        "_dash_imm_decimal": ("test_parser.cscript:P1A-67",),
        "_dash_json_number": ("test_parser.cscript:P1A-67",
                              "test_parser.cscript:P1A-58"),
        "_dash_imm_number": ("test_parser.cscript:P1A-67",),
        "_dash_imm_clock": ("test_parser.cscript:P1A-67",),
        "_dash_imm_echo": ("test_parser.cscript:P1A-67",),
        "_dash_imm_records": ("test_parser.cscript:P1A-67",),
        "_dash_immediate": ("test_parser.cscript:P1A-60",
                            "test_adversarial.cscript:P20-35"),
        "_dash_pc_immediate": ("test_adversarial.cscript:P22-02",
                               "test_parser.cscript:P1A-67"),
        # e2e: the scanner step every splitter takes; quotes, compound
        # quotes and an unterminated quote.
        "_dash_quote_step": ("test_parser_integrity.cscript:P1B-02",
                             "test_parser_integrity.cscript:P1B-08",
                             "test_parser_integrity.cscript:P1B-14"),
        "_first_comma_pos": ("test_tokenizer.cscript:P1A-26",
                             "test_parser_integrity.cscript:P1B-09"),
        "_dash_comma_pos": ("test_tokenizer.cscript:P1A-26",
                            "test_tokenizer.cscript:P1A-28"),
        "_dash_split_segs": ("test_tokenizer.cscript:P1A-21",
                             "test_parser_integrity.cscript:P1B-06"),
        "_dash_extract_vars": ("test_parser.cscript:P1A-48",
                               "test_help_claims_6.cscript:HC6-48"),
        # e2e: the names _dash_extract_qual_vars returns past escapes.
        "_dash_qual_str": ("test_json_escaping.cscript:JSE-11",
                           "test_json_escaping.cscript:JSE-13"),
        "_dash_extract_qual_vars": ("test_json_escaping.cscript:JSE-12",
                                    "test_json_escaping.cscript:JSE-30"),
        "_dash_extract_filters": ("test_parser_integrity.cscript:P1B-19",
                                  "test_parser_integrity.cscript:P1B-20"),
        "_dash_is_blank": ("test_program_coverage.cscript:PC-12",
                           "test_help_claims_3.cscript:HC3-19"),
        "_dash_blank_trim": ("test_program_coverage.cscript:PC-12",
                             "test_help_claims_3.cscript:HC3-19"),
        "_dash_filter_split": ("test_help_claims_3.cscript:HC3-19",
                               "test_help_claims_3.cscript:HC3-20"),
        # e2e: through _dash_filter_refusal and _dash_filter_setvars.
        "_dash_filter_items": ("test_program_coverage.cscript:PC-12",
                               "test_help_claims_3.cscript:HC3-08"),
        # e2e: link() and exclude() names split at blanks with their quotes,
        # as the renderer splits them, and refused by dash by name.
        "_dash_blank_words": ("test_json_escaping.cscript:JSE-56",),
        "_dash_link_refusal": ("test_json_escaping.cscript:JSE-56",),
        # e2e: a program's own arguments and the user's text between them,
        # read by value -- a title, a qualifier and values holding "'.
        # e2e: a qualifier's names outside its literals are exported, each
        # under its full name, and its abbreviations are written out when it
        # is registered -- both modes then draw Stata's rows.
        "_dash_qual_json_text": ("test_qualifier_literals.cscript:QL-21",),
        "_dash_qual_name_spans": ("test_qualifier_literals.cscript:QL-21",
                                  "test_qualifier_literals.cscript:QL-22"),
        "_dash_qual_expand": ("test_qualifier_literals.cscript:QL-22",),
        "_dash_text_args": ("test_json_escaping.cscript:JSE-42",
                            "test_json_escaping.cscript:JSE-46",
                            "test_json_escaping.cscript:JSE-47"),
        "_dash_filter_refusal": ("test_help_claims_3.cscript:HC3-20",
                                 "test_help_claims_3.cscript:HC3-08"),
        "_dash_filter_setvars": ("test_program_coverage.cscript:PC-12",
                                 "test_program_coverage.cscript:PC-13",
                                 "test_help_claims_3.cscript:HC3-16"),
        "_dash_json_get_str": ("test_json_escaping.cscript:JSE-28",
                               "test_help_claims_1.cscript:HC1-01"),
        # e2e: through _dash_option_names.
        "_dash_optname_of": ("test_parser_integrity.cscript:P1B-23",
                             "test_parser_integrity.cscript:P1B-25"),
        "_dash_option_names_scan": ("test_parser_integrity.cscript:P1B-23",
                                    "test_registry_collision.cscript:REG-39"),
        "_dash_kpi_fields": ("test_registry_collision.cscript:REG-26",),
        "_dash_item_globals": ("test_registry_collision.cscript:REG-26",
                               "test_registry_collision.cscript:REG-20"),
        "_dash_option_names": ("test_parser_integrity.cscript:P1B-24",
                               "test_parser_integrity.cscript:P1B-25"),
        # e2e: a second name() refused, text that looks like one not.
        "_dash_has_name_opt": ("test_registry_collision.cscript:REG-39",
                               "test_registry_collision.cscript:REG-37"),
        "_dash_spec_types_in": ("test_parser.cscript:P1A-75",
                                "test_parser.cscript:P1A-74"),
    },
}


#: Units no shipped code calls, as measured -- never executed by the
#: certification suite before test_program_coverage.cscript.  GAPS.md N
#: lists them and ROADMAP WP-26 TR-26.1..3 deletes them.  ``callers`` are
#: the only units allowed to name one (themselves uncalled), and
#: ``dropped_by`` the units that name one only to drop it -- the reload in
#: _dash_require_mata drops every function the library defines before it
#: runs the file again (test_env_guards.cscript ENV-23), which is not a
#: call;
#: test_program_coverage_map.py fails the moment any other code calls one,
#: because a live unit needs the tests a live unit has.
UNCALLED = {
    "_dash_graph_opts_to_json": {
        "callers": (),
        "why": "No test: it reads the g_* locals of its own scope, which "
               "are always empty -- a program cannot see its caller's "
               "locals -- so it writes {} whatever the caller holds "
               "(measured 24sep2026: g_title set in the calling program, "
               "{} returned).  The graph JSON is assembled inline in "
               "_dash_plot.  WP-26 TR-26.1 deletes it.",
    },
    "_dash_kv_json": {
        "callers": (),
        "why": "Tested as written (PC-29); WP-26 TR-26.2 deletes it.",
    },
    "_dash_json_esc": {
        "callers": (),
        "why": "Tested as written (PC-28); WP-26 TR-26.3 deletes it.",
    },
    "_dash_html_esc": {
        "callers": (),
        "why": "Tested as written (PC-27); WP-26 TR-26.3 deletes it.",
    },
    "_html_escape": {
        "callers": ("_dash_html_esc",),
        "dropped_by": ("_dash_require_mata",),
        "why": "Called only by _dash_html_esc; tested as written (PC-27); "
               "WP-26 TR-26.3 deletes it.",
    },
}
