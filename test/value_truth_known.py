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
    "aspectratio_1": "plot:PT-7",  # twoway r(198) option aspectratio() incorrectly specified / dash r(198)
    "aspectratio_2": "basic:PT-13",  # twoway r(0) / dash r(198)
    "barwidth_1": "plot:PT-7",  # twoway r(198) option barwidth() incorrectly specified / dash r(198)
    "barwidth_2": "basic:PT-13",  # twoway r(0) / dash r(198)
    "barwidth_3": "basic:PT-13",  # twoway r(0) / dash r(198)
    "base_1": "basic:PT-9",  # twoway r(4026) option base() incorrectly specified, abc is not a  / dash r(198)
    "by_1": "plot:PT-7",  # twoway r(111) variable nosuchvar not found / dash r(111)
    "colorlevels_1": "plot:PT-7",  # twoway r(198) option colorlevels() incorrectly specified / dash r(198)
    "colorlevels_8": "plot:PT-7",  # twoway r(198) option colorlevels() incorrectly specified / dash r(198)
    "histogram_bin_1": "basic:PT-9",  # twoway r(125) bins() invalid -- invalid number, outside of allow / dash r(198)
    "histogram_bin_2": "basic:PT-9",  # twoway r(121) bins() invalid -- invalid number / dash r(198)
    "histogram_bin_3": "basic:PT-9",  # twoway r(126) bins() invalid -- invalid number, noninteger value / dash r(198)
    "histogram_bin_4": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
    "histogram_bin_6": "basic:PT-9",  # twoway r(125) bins() invalid -- invalid number, outside of allow / dash r(198)
    "histogram_freqpct_1": "stat:PT-1",  # twoway r(198) options frequency percent may not be combined / dash r(0) draws
    "histogram_start_1": "basic:PT-9",  # twoway r(121) start() invalid -- invalid number / dash r(198)
    "histogram_width_1": "basic:PT-9",  # twoway r(125) width() invalid -- invalid number, outside of allo / dash r(198)
    "histogram_width_2": "basic:PT-9",  # twoway r(121) width() invalid -- invalid number / dash r(198)
    "histogram_width_3": "basic:PT-9",  # twoway r(125) width() invalid -- invalid number, outside of allo / dash r(198)
    "jitter_1": "basic:PT-13",  # twoway r(0) / dash r(198)
    "jitter_4": "basic:PT-13",  # twoway r(0) / dash r(198)
    "jitter_7": "plot:PT-7",  # twoway r(198) .z_ invalid name / dash r(198)
    "jitterseed_1": "basic:PT-13",  # twoway r(0) / dash r(198)
    "jitterseed_2": "basic:PT-13",  # twoway r(0) / dash r(198)
    "jitterseed_3": "basic:PT-13",  # twoway r(0) / dash r(198)
    "kdensity_bwidth_1": "plot:PT-7",  # twoway r(198) bandwidth must be positive / dash r(198)
    "kdensity_bwidth_3": "plot:PT-7",  # twoway r(198) option bwidth() not allowed / dash r(198)
    "kdensity_kernel_1": "plot:PT-7",  # twoway r(198) invalid kernel function / dash r(198)
    "kdensity_n_1": "plot:PT-7",  # twoway r(198) option n() requires a positive integer / dash r(198)
    "level_1": "plot:PT-7",  # twoway r(198) option level() not allowed / dash r(198)
    "lowess_bwidth_3": "plot:PT-7",  # twoway r(198) option bwidth() not allowed / dash r(198)
    "lpoly_n_3": "plot:PT-7",  # twoway r(198) option n() not allowed / dash r(198)
    "lpoly_n_5": "stat:PT-15 (documented)",  # twoway r(0) / dash r(198)
    "mband_bands_1": "plot:PT-7",  # twoway r(198) bands must be between 1 and 200 / dash r(198)
    "mband_bands_2": "plot:PT-7",  # twoway r(198) option bands() not allowed / dash r(198)
    "mband_bands_3": "plot:PT-7",  # twoway r(198) option bands() not allowed / dash r(198)
    "mband_bands_4": "plot:PT-7",  # twoway r(198) bands must be between 1 and 200 / dash r(198)
    "mlabangle_4": "plot:PT-7",  # twoway r(198) textangle must be between -360.000 and 360.000 / dash r(198)
    "mlabangle_5": "basic:PT-9",  # twoway r(111) variable z_ not found / dash r(198)
    "mlabel_1": "plot:PT-7",  # twoway r(111) variable nosuchvar not found / dash r(111)
    "msangle_4": "plot:PT-7",  # twoway r(198) symbolangle must be between -360.000 and 360.000 / dash r(198)
    "msangle_5": "plot:PT-7",  # twoway r(198) .z_ invalid name / dash r(198)
    "msize_7": "plot:PT-7",  # twoway r(198) invalid syntax / dash r(198)
    "mspline_bands_1": "plot:PT-7",  # twoway r(198) bands must be between 1 and 200 / dash r(198)
    "mspline_bands_2": "plot:PT-7",  # twoway r(198) option bands() not allowed / dash r(198)
    "scheme_1": "ST-16",  # twoway r(0) / dash r(198)
    "xlabel2_1": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel2_2": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel2_3": "DT-15",  # twoway r(198) option xlabel2() not allowed / dash r(0) draws
    "xlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xmlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xmtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "xsize_2": "plot:PT-7",  # twoway r(198) graph xsize invalid; minimum xsize is 1 inch maxim / dash r(198)
    "xsize_3": "plot:PT-7",  # twoway r(198) graph xsize invalid; minimum xsize is 1 inch maxim / dash r(198)
    "xsize_4": "plot:PT-7",  # twoway r(198) graph xsize invalid; minimum xsize is 1 inch maxim / dash r(198)
    "xtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ylabel2_1": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel2_2": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel2_3": "DT-15",  # twoway r(198) option ylabel2() not allowed / dash r(0) draws
    "ylabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ymlabel_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ymtick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
    "ysize_1": "plot:PT-7",  # twoway r(198) graph ysize invalid; minimum ysize is 1 inch maxim / dash r(198)
    "ysize_3": "plot:PT-7",  # twoway r(198) graph ysize invalid; minimum ysize is 1 inch maxim / dash r(198)
    "ytick_1": "DG-9",  # twoway r(198) invalid label specifier, : abc: / dash r(0) draws
}

DELIBERATE = {
}
