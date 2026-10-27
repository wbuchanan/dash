"""dash's known differences from twoway on value_truth.json (WP-33 TR-11).

Certification block S10 TR-11 of test/test_wp33_truth.cscript (Q3310-1)
runs every probe of test/fixtures/value_truth.json through dash and
compares the rc (and, where twoway refuses, the first line) with twoway's.
Each probe that differs is listed here under the GAPS4 item that fixes or
documents it, by test/known_differences.py's rule (section 33-10,
D-33-10.a/b): ``"<probe id>": "<GAPS4 id>",  # twoway <rc/line> / dash
<rc/line>``.  An item's closing commit deletes its plain rows
(``python3 test/known_differences.py <id>`` prints them); a difference its
ruling keeps moves into DELIBERATE as ``"<probe id>": "<ruling id>: <what
is kept>"``.
"""

VALUE_KNOWN = {
    "by_1": "plot:PT-7",  # twoway r(111) variable nosuchvar not found / dash r(111)
    "histogram_bin_4": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
    "lpoly_n_3": "plot:PT-7",  # twoway r(198) option n() not allowed / dash r(198)
    "lpoly_n_5": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
    "mlabel_1": "plot:PT-7",  # twoway r(111) variable nosuchvar not found / dash r(111)
    "scheme_1": "ST-16",  # twoway r(0) / dash r(198)
    "xlabel2_1": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel2_2": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel2_3": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xmlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xmtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ylabel2_1": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel2_2": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel2_3": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ymlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ymtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ytick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
}

DELIBERATE = {
    "aspectratio_2": "D59: aspectratio() below 0 refused; twoway draws aspectratio(-1) as a plot region overflowing the graph, a layout defect dash does not copy",
}
