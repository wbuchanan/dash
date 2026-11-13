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
    "histogram_bin_4": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
    "lpoly_n_5": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
}

DELIBERATE = {
    "aspectratio_2": "D59: aspectratio() below 0 refused; twoway draws aspectratio(-1) as a plot region overflowing the graph, a layout defect dash does not copy",
}
