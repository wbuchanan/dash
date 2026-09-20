"""Every plot type dash advertises must actually draw something.

`dash.ado` prints a list of supported plot types when it does not recognise
one. That list is the package's promise, and two entries on it -- `pci` and
`pcscatter` -- produced a titled, axed, empty plot region with rc 0 and no
warning until this test existed. Nothing noticed, because:

  * the 299-command conformance corpus appends `name()` to every probe, so
    it registers each spec and never renders one -- it proves the `syntax`
    layer and nothing past it;
  * the pytest coverage for those two was at the `GlyphMapper` level, which
    is downstream of the dispatch that never reached them.

So this test reads the promise out of `dash.ado` rather than restating it,
builds a minimal spec for each type in the shape `dash.ado` itself writes,
renders it, and asserts a glyph came out. A plot type added to that list
without a render path fails here.
"""
import json
import os
import re
import sys
import tempfile
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr

_ADO = os.path.join(_HERE, "..", "dash.ado")

# One tsset-style panel, wide enough for every smoother to have something to
# fit and every range type to have two bounds.
_N = 24
_DATA = {
    "variableNames": ["y", "x", "y2", "x2", "lo", "hi", "t", "g"],
    "values": [
        {"y": 10.0 + i * 1.5 + (i % 3), "x": float(100 + 10 * i),
         "y2": 12.0 + i * 1.4, "x2": float(105 + 10 * i),
         "lo": 8.0 + i * 1.5, "hi": 12.0 + i * 1.5,
         "t": float(i), "g": float(i % 2)}
        for i in range(_N)
    ],
}

_RANGE_TYPES = {"rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
                "rcapsym", "rscatter", "tsrline"}
_PC_VAR_TYPES = {"pcspike", "pcarrow", "pcbarrow", "pcscatter"}
_UNIVARIATE = {"histogram", "kdensity"}

# Layers that need an OPTIONAL package. dash_setup installs these, and
# dash.sthlp says a missing one degrades that layer to an empty glyph with a
# warning rather than blocking anything -- so on a machine without it, an
# empty layer is the documented behaviour, not the defect this file hunts.
_OPTIONAL_DEPS = {
    "lowess":  "statsmodels",
    "mspline": "scipy",
    "lfitci":  "scipy",
    "qfitci":  "scipy",
    "fpfitci": "scipy",
    "lpolyci": "scipy",
}


def _missing_dep(ptype):
    mod = _OPTIONAL_DEPS.get(ptype)
    if not mod:
        return None
    try:
        __import__(mod)
    except ImportError:
        return mod
    return None


def _advertised_plot_types():
    """The list dash.ado prints when it rejects an unknown plot type."""
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    # Start at the "Supported:" literal, not at the message above it: the
    # message ends mid-string, so pairing quotes from there shifts every
    # pair by one and the plot-type lines are never matched.
    i = src.index('"Supported:')
    j = src.index("exit(198)", i)
    block = src[i:j]
    names = []
    skip = {"dash", "supported", "unrecognised", "plot", "type", "n"}
    for line in re.findall(r'"([^"]*)"', block):
        for tok in line.split():
            tok = tok.strip(":.,'").lower()
            if re.fullmatch(r"[a-z][a-z0-9]*", tok) and tok not in skip:
                names.append(tok)
    return list(dict.fromkeys(names))


def _plot_for(ptype):
    if ptype in _UNIVARIATE:
        return {"type": ptype, "yvar": "y", "xvar": "", "options": {}}
    if ptype in _RANGE_TYPES:
        return {"type": ptype, "yvar1": "lo", "yvar2": "hi", "xvar": "x",
                "options": {}}
    if ptype in _PC_VAR_TYPES:
        return {"type": ptype, "y1var": "y", "x1var": "x",
                "y2var": "y2", "x2var": "x2", "options": {}}
    if ptype == "scatteri":
        return {"type": ptype, "values": [[20.0, 3000.0], [30.0, 4000.0]],
                "options": {}}
    if ptype == "pci":
        return {"type": ptype, "values": [[20.0, 3000.0], [30.0, 4000.0]],
                "options": {}}
    if ptype == "function":
        return {"type": ptype, "expr": "x", "options": {"range": "0 10"}}
    if ptype in ("tsline", "tsrline"):
        return {"type": ptype, "yvar": "y", "xvar": "t", "options": {}}
    return {"type": ptype, "yvar": "y", "xvar": "x", "options": {}}


def _render(plot):
    td = tempfile.mkdtemp()
    spec = {"graphs": [{"graph_options": {"name": "g1"}, "plots": [plot]}],
            "kpis": [], "build_options": {"layout": "auto", "level": "95"}}
    sp, dp = os.path.join(td, "s.json"), os.path.join(td, "d.json")
    with open(sp, "w") as fh:
        json.dump(spec, fh)
    with open(dp, "w") as fh:
        json.dump(_DATA, fh)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        r = dr.DashRenderer(sp, dp)
        r.render()
    return r.figures["g1"]


def test_the_advertised_list_was_found():
    """Guards the guard: an empty list would make every check below vacuous."""
    types = _advertised_plot_types()
    assert len(types) >= 30, (
        f"only {len(types)} plot types parsed out of dash.ado's own list: "
        f"{types}"
    )
    for expected in ("scatter", "line", "histogram", "pci", "pcscatter",
                     "function", "mband"):
        assert expected in types, f"{expected} missing from the parsed list"


@pytest.mark.parametrize("ptype", _advertised_plot_types())
def test_an_advertised_plot_type_draws_a_glyph(ptype):
    fig = _render(_plot_for(ptype))
    assert len(fig.renderers) >= 1, (
        f"`dash {ptype} ...' is in the list of supported plot types "
        f"dash.ado prints, and it draws nothing: an empty plot region, "
        f"rc 0, no warning"
    )


@pytest.mark.parametrize("ptype", _advertised_plot_types())
def test_an_advertised_plot_type_draws_real_data(ptype):
    """A renderer over an empty source is a plot type that failed quietly."""
    dep = _missing_dep(ptype)
    if dep:
        pytest.skip(
            f"{ptype} needs the optional package {dep}, which is not "
            f"installed here; an empty layer is the documented behaviour"
        )
    fig = _render(_plot_for(ptype))
    drawn = 0
    for r in fig.renderers:
        src = getattr(r, "data_source", None)
        if src is None:
            continue
        if any(len(v) for v in src.data.values()):
            drawn += 1
    assert drawn >= 1, (
        f"`dash {ptype} ...' produced {len(fig.renderers)} renderer(s), all "
        f"over empty data sources -- the layer is drawn, and it is blank"
    )
