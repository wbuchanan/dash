"""
test_sidebar_fit.py -- under layout(bs) and filterposition(left) every
filter widget takes the sidebar's width.

The Bootstrap page embeds each filter widget on its own, in a sidebar
column two twelfths of the page wide (about 180 px at 1068 px).  A slider
kept BokehJS's default width of 300 px, so the range and slider filters
of the user's guide's filters example ran past the sidebar's edge and
under the first graph (17nov2026).  In the sidebar each widget now
stretches to its column; in the filter bar above the grid each keeps its
own width, and the plain layout's sidebar (a 240 px Bokeh column, which
sizes its children) is as it was.  The browser reads the boxes in
test_sidebar_fit_browser.py.
"""
import os
import re
import sys
import warnings

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from bokeh.models import Div, Widget  # noqa: E402
from test_adversarial_matrix import _write_inputs  # noqa: E402
from test_served_bs_layout import _spec  # noqa: E402

#: A dropdown, a range slider and a threshold slider.
FILTERS = "foreign || price, type(range) || mpg, type(slider)"


def _inputs(models):
    """The widgets a user sets: the filter area's note Div stretches in
    every layout."""
    return [m for m in models if isinstance(m, Widget)
            and not isinstance(m, Div)]


def _saved(tmp_path, monkeypatch, position, layout="bs: g1=6 g2=6"):
    """The saved page and the models handed to components(), by id."""
    handed = {}
    real = dr.components

    def spy(models, *a, **k):
        handed.update((m.id, m) for m in models)
        return real(models, *a, **k)

    monkeypatch.setattr(dr, "components", spy)
    spec = _spec(["g1", "g2"], layout=layout, filter=FILTERS,
                 filter_position=position)
    sp, dp = _write_inputs(tmp_path, spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        page = r.render()
    return r, page, handed


def _roots_between(page, start, end):
    """The models whose root markup lies between two class names."""
    body = page[page.index('<div class="db-container">'):]
    chunk = body[body.index(start):body.index(end)]
    return re.findall(r'data-root-id="([^"]+)"', chunk)


def test_each_sidebar_widget_stretches_to_the_sidebar(tmp_path, monkeypatch):
    _, page, handed = _saved(tmp_path, monkeypatch, "left")
    ids = _roots_between(page, "db-sidebar-col", "db-col-md-10")
    widgets = [handed[i] for i in ids if isinstance(handed.get(i), Widget)]
    kinds = sorted(type(w).__name__ for w in widgets)
    assert {"RangeSlider", "Slider", "Select"} <= set(kinds), kinds
    for w in widgets:
        assert w.sizing_mode == "stretch_width", (type(w).__name__,
                                                  w.sizing_mode, w.width)


def test_the_filter_bar_keeps_each_widget_s_own_width(tmp_path, monkeypatch):
    _, page, handed = _saved(tmp_path, monkeypatch, "top")
    ids = _roots_between(page, "db-filter-bar", "db-row db-section")
    widgets = _inputs(handed.get(i) for i in ids)
    assert any(type(w).__name__ == "RangeSlider" for w in widgets), widgets
    for w in widgets:
        assert w.sizing_mode != "stretch_width", type(w).__name__
    slider = next(w for w in widgets if type(w).__name__ == "RangeSlider")
    assert slider.width == 300


def test_the_plain_sidebar_is_unchanged(tmp_path, monkeypatch):
    """layout(auto): a 240 px column of widgets beside the grid, each
    widget at its own size inside it."""
    r, _, _ = _saved(tmp_path, monkeypatch, "left", layout="auto")
    root = r._last_layout_root
    sidebars = [m for m in root.references()
                if type(m).__name__ == "Column"
                and m.width == dr._SIDEBAR_WIDTH_PX]
    assert len(sidebars) == 1
    kids = _inputs(sidebars[0].children)
    assert any(type(w).__name__ == "RangeSlider" for w in kids), kids
    for w in kids:
        assert w.sizing_mode is None, type(w).__name__
