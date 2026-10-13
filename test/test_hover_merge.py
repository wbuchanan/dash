"""hover() given in a layer and again after the comma (WP-31 A7).

The defect: ``dash (scatter mpg weight, hover(make)), hover(price)`` kept
only the rightmost list: the repeat merge (``_dash_rep_merge_locals``)
read hover() as category "R", the last copy, so the tooltip showed price
and not make.  hover() is dash's own option (twoway has none); its two
lists are now joined, blank-separated, in the order written, and the
reader of the merged text (``_dash_extract_hover_vars``, and the
renderer's ``_dash_build_hover``) keeps each variable once.

The Stata side is pinned by test/test_wp31_truth.cscript U07-5: the
registered "hover" text and the tooltip rows, saved and served.
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def _mata_function(name):
    with open(os.path.join(REPO, "dash_parse.mata"), encoding="utf-8") as fh:
        src = fh.read()
    body = src[src.index("string scalar %s(" % name):]
    return body[:body.index("\n}\n")]


class TestHoverIsMerged:
    def test_category_and_branch(self):
        cat = _mata_function("_dash_rep_cat")
        assert 'if (k == "hover") return("H")' in cat
        # Before the catch-all "R", which would otherwise answer first.
        assert cat.index('return("H")') < cat.index('return("R")')
        merge = _mata_function("_dash_rep_merge")
        m = re.search(r'if \(cat == "H"\) return\(strtrim\(v1\) \+ " " \+ '
                      r'strtrim\(v2\)\)', merge)
        assert m
        # After the empty-copy answers, before the "R" answer could take
        # hover's second copy alone.
        assert merge.index('if (cat == "R"') < m.start()
