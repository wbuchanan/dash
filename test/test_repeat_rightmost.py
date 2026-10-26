"""Repeated options taken rightmost, as twoway takes them (WP-35 MS-1).

twoway takes the last copy of yvarlabel(), xvarlabel(), mlabprefix(),
mlabsuffix(), lalign(), mlabstyle() and of contour's valued options
(twoway_zyx2view_parse.class: ``_parse combop ... rightmost``); dash's
_dash_label_split and _dash_contour_split ran one combined ``syntax`` over
every copy and refused the second, r(198).  Both now keep each valued
option's last copy, chosen by the Mata function _dash_rightmost_keep;
a flag keeps every copy, so a flag given twice is still refused as twoway
refuses it.  The behaviour is pinned by test_wp35_truth.cscript Q3501-1
.. Q3501-3 (twoway beside dash); this file pins that the helper exists
and that dash's Mata check names it.
"""
import os
import re

_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _needed(ado):
    """The names of _dash_require_mata's _needed list (one local, continued
    with ///)."""
    out = []
    for line in ado[ado.index("local _needed "):].split("\n"):
        out.extend(line.replace("local _needed ", "").replace("///", "").split())
        if not line.rstrip().endswith("///"):
            break
    return set(out)


class TestTheHelper:
    def test_the_helper_is_defined_and_needed(self):
        mata = _read("dash_parse.mata")
        ado = _read("dash.ado")
        assert re.search(
            r"^real rowvector _dash_rightmost_keep\(string rowvector names, "
            r"string scalar flags\)", mata, re.M), \
            "dash_parse.mata does not define _dash_rightmost_keep"
        assert "_dash_rightmost_keep" in _needed(ado), \
            "dash.ado's _needed list does not name _dash_rightmost_keep"
