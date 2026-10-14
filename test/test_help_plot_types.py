"""The help names every plot type dash draws, and the two it refuses.

WP-22 TR-22.1 / TR-22.2 (GAPS.md F1, F2).  Measured 23sep2026 at 9f48cf7:
dash dispatched 38 plot types, dash.sthlp listed none of them anywhere, and
nine -- pcarrow pcbarrow pci pcscatter pcspike rconnected rscatter tsline
tsrline -- were not named in it at all.  A plot type dash does not draw is
an error, r(198), unlike an unknown option, so a user had no way to know
beforehand which of their twoway commands would run.

The Plot types section lists them, and these checks hold it to the code in
both directions: the code's own list of the types it draws
(``_dash_plot_type_names``, read from the dispatch tables both renderers
use), and the types dash.ado refuses by name.
"""
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr

#: twoway plot types dash does not draw: a surface interpolated over a grid
#: (contour, contourline) and a point on a range (rpcap, rpspike) -- the
#: last two new in StataNow 19.5.
# Flipped (WP-31 B1): rpcap and rpspike are drawn.  WP-31 B2: sunflower is
# refused by name.
_REFUSED = ("contour", "contourline", "sunflower")


def _help():
    with open(os.path.join(_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
        return fh.read()


def _section():
    """The Plot types section, from its marker to the next one."""
    text = _help()
    start = text.find("{marker plottypes}")
    assert start >= 0, "dash.sthlp has no {marker plottypes} section"
    end = text.find("{marker ", start + 1)
    return text[start:end if end > 0 else None]


def _table(section):
    """The {cmd:} names in the section's table of types drawn."""
    table = section.split("{synoptline}")[1] if "{synoptline}" in section \
        else ""
    return set(re.findall(r"\{cmd:([a-z]+)\}", table))


class TestThePlotTypesSection:

    def test_every_type_the_code_draws_is_listed(self):
        missing = sorted(dr._dash_plot_type_names() - _table(_section()))
        assert not missing, (
            f"plot types dash draws that dash.sthlp's Plot types table does "
            f"not list: {missing}")

    def test_it_lists_no_type_the_code_does_not_draw(self):
        extra = sorted(_table(_section()) - dr._dash_plot_type_names())
        assert not extra, (
            f"plot types the table lists that dash does not draw: {extra}")

    def test_the_types_dash_refuses_are_named_as_not_drawn(self):
        section = _section()
        tail = section.split("{synoptline}")[-1]
        for name in _REFUSED:
            assert f"{{cmd:{name}}}" in tail, (
                f"{name} is not named after the table as a type dash does "
                f"not draw")
            assert name not in dr._dash_plot_type_names()

    def test_dash_ado_refuses_them_by_name(self):
        """dash.ado refuses a type the Mata helper _dash_undrawn_plottype
        names, with a reason of its own (test_parser.cscript P1A-49..59);
        the helper is where the list is kept."""
        with open(os.path.join(_ROOT, "dash_parse.mata"),
                  encoding="utf-8") as fh:
            mata = fh.read()
        start = mata.index("string scalar _dash_undrawn_plottype(")
        body = mata[start:mata.index("\n}\n", start)]
        for name in _REFUSED:
            assert f'"{name}"' in body, (
                f"_dash_undrawn_plottype does not refuse {name}")
        with open(os.path.join(_ROOT, "dash.ado"), encoding="utf-8") as fh:
            assert "_dash_undrawn_plottype(" in fh.read()

    def test_the_syntax_and_the_differences_point_to_it(self):
        text = _help()
        # Measured 24sep2026: three links, one each in the Syntax (the
        # {it:plottype} line), the differences (item 5, the plot types it
        # refuses) and the marker-label sections.  The count >= 2 this
        # replaced still passed with the Syntax's link deleted, since the
        # other two made two; each link is now placed in its section.
        link = "{help dash##plottypes:"
        where, section = {}, "(before any marker)"
        for ln in text.split("\n"):
            m = re.match(r"\{marker ([a-z_]+)\}", ln)
            if m:
                section = m.group(1)
            if link in ln:
                where[section] = where.get(section, 0) + ln.count(link)
        assert where == {"syntax": 1, "differences": 1,
                         "marker_labels": 1}, (
            f"links to the Plot types section, by the section that holds "
            f"them: {where}; the Syntax and the differences must each "
            f"point to it (re-measure if a link was added on purpose)")
