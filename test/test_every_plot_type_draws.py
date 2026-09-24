"""Every plot type dash draws must actually draw something.

`dash.ado` prints a list of supported plot types when it does not recognise
one. That list is the package's promise, and two entries on it -- `pci` and
`pcscatter` -- produced a titled, axed, empty plot region with rc 0 and no
warning until this test existed. Nothing noticed, because:

  * the 299-command conformance corpus appends `name()` to every probe, so
    it registers each spec and never renders one -- it proves the `syntax`
    layer and nothing past it;
  * the pytest coverage for those two was at the `GlyphMapper` level, which
    is downstream of the dispatch that never reached them.

So this test builds a minimal spec for each type in the shape `dash.ado`
itself writes, renders it, and asserts a glyph came out -- a glyph over real
data.

WHICH types: the dispatch table itself.  ``dr._dash_plot_type_names()``
reads the tables both render modes dispatch through (``_dash_glyph_dispatch``
and ``_dash_pc_dispatch``) and the literal types.  The list used to be
parsed out of the "Supported:" message dash.ado prints -- a regex over prose,
so a reflowed message dropped a type from the parametrization without a
word, under a ``>= 30`` floor that would not notice one or two going
(GAPS.md L6).  The registry is held equal, both ways, to the two places
dash.ado names plot types:

  * the Mata table ``_expand_plottype_str`` (dash_parse.mata) -- every name
    a user's spelling can become, so no type dash.ado accepts goes untested
    here, and none the registry lists is unreachable;
  * the family lists of ``_dash_plottype_families`` (dash.ado), which decide
    the shape of the spec dash.ado writes for a type -- each spec here is
    built in that shape, read from those lists rather than restated.

test_plottype_families.py holds those families to the renderer's own
categories; the "Supported:" message is held to the registry by
test_mode_parity.py (TestTheCorpusIsComplete) and test_help_claims_1.py.
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
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")

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


def _ado_families():
    """``{family: frozenset(types)}`` from dash.ado's _dash_plottype_families.

    Code, not prose: the program's own ``c_local`` word lists, each read
    whole.  test_plottype_families.py holds the same lists to the
    renderer's ``_DASH_*_TYPES``.
    """
    with open(_ADO, encoding="utf-8") as fh:
        src = fh.read()
    m = re.search(r"^program define _dash_plottype_families\b(.*?)^end\b",
                  src, re.S | re.M)
    assert m, "dash.ado defines no _dash_plottype_families program"
    return {name: frozenset(words.split())
            for name, words in re.findall(
                r'^\s*c_local\s+(_pt_\w+)\s+"([^"]*)"', m.group(1), re.M)}


def _mata_expanded_types():
    """The full names ``_expand_plottype_str`` can return: its table's first
    column, and the two spellings it maps outside the table."""
    with open(_MATA, encoding="utf-8") as fh:
        src = fh.read()
    k = src.index("string scalar _expand_plottype_str(")
    body = src[k:src.index("\n}\n", k)]
    table = re.search(r"tbl = (.*?)\n\s*\n", body, re.S)
    assert table, "_expand_plottype_str has no tbl = ... table"
    names = set(re.findall(r'\("([a-z]+)","[a-z]+"\)', table.group(1)))
    names |= set(re.findall(r'return\("([a-z]+)"\)', body))
    return frozenset(names)


_FAMILIES = _ado_families()

#: The types this file renders: the registry, every one of them.
_TYPES = sorted(dr._dash_plot_type_names())

# Layers that need an OPTIONAL package. dash_setup installs these, and
# dash.sthlp says a missing one degrades that layer to an empty glyph with a
# warning rather than blocking anything -- so on a machine without it, an
# empty layer is the documented behaviour, not the defect this file hunts.
#
# Read off the mappers rather than listed by hand: a layer needs an optional
# package exactly when its map_* method calls _optional_import(module, attr,
# package, feature).  The hand-written list this replaces named statsmodels
# for lowess and scipy for mspline (both gone since WP-18: Stata's smoother
# and Stata's cross-median spline are numpy) and scipy for qfitci, fpfitci
# and lpolyci, none of which ever imported it.


def _optional_deps():
    import inspect
    out = {}
    for name in dir(dr.GlyphMapper):
        if not name.startswith("map_"):
            continue
        try:
            src = inspect.getsource(getattr(dr.GlyphMapper, name))
        except (OSError, TypeError):
            continue
        code = "\n".join(l.split("#", 1)[0] for l in src.splitlines())
        m = re.search(r'_optional_import\(\s*"[^"]+"\s*,\s*[^,]+,\s*"([^"]+)"',
                      code)
        if m:
            out[name[4:]] = m.group(1)
    return out


_OPTIONAL_DEPS = _optional_deps()


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
    """The list dash.ado prints when it rejects an unknown plot type.

    The user-facing promise, parsed out of a message.  Nothing here is
    parametrized over it: test_mode_parity.py compares it, as a set, with
    ``_dash_plot_type_names()``, so a message that stops parsing fails that
    comparison instead of dropping a type unseen.
    """
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
    """A one-layer plot spec for *ptype*, in the shape dash.ado writes it:
    its varlist keys chosen by the family dash.ado routes it through."""
    if ptype in _FAMILIES["_pt_univar"]:
        return {"type": ptype, "yvar": "y", "xvar": "", "options": {}}
    if ptype in _FAMILIES["_pt_range"]:
        # tsrline is a range type whose x is the time variable.
        xvar = "t" if ptype in _FAMILIES["_pt_ts"] else "x"
        return {"type": ptype, "yvar1": "lo", "yvar2": "hi", "xvar": xvar,
                "options": {}}
    if ptype in _FAMILIES["_pt_pc"]:
        return {"type": ptype, "y1var": "y", "x1var": "x",
                "y2var": "y2", "x2var": "x2", "options": {}}
    if ptype in _FAMILIES["_pt_literal"]:
        # Literal values or an expression, a shape per type; a literal type
        # added to the family without one here fails rather than being
        # drawn from a variable spec it would never be given.
        if ptype == "scatteri":
            return {"type": ptype, "values": [[20.0, 3000.0], [30.0, 4000.0]],
                    "options": {}}
        if ptype in ("pci", "pcarrowi"):
            # One record per segment or arrow, y1 x1 y2 x2, as dash.ado
            # writes `pci 20 3000 30 4000' and `pcarrowi 20 3000 30 4000'.
            return {"type": ptype, "values": [[20.0, 3000.0, 30.0, 4000.0]],
                    "options": {}}
        if ptype == "function":
            return {"type": ptype, "expr": "x", "options": {"range": "0 10"}}
        raise AssertionError(
            f"{ptype} is a literal type with no spec shape in _plot_for")
    xvar = "t" if ptype in _FAMILIES["_pt_ts"] else "x"
    return {"type": ptype, "yvar": "y", "xvar": xvar, "options": {}}


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


class TestTheListIsTheDispatchTable:
    """Guards the guard: the tests below run once per type in ``_TYPES``, so
    a type missing from it is a type never rendered here."""

    def test_the_registry_is_every_type_dash_ado_accepts(self):
        """Both ways: a type the Mata table expands to and the registry
        lacks would never be drawn by this file (a dispatch entry whose
        method is not named map_<type> drops out of the registry); a
        registry type the table cannot produce is one no command reaches."""
        mata, code = _mata_expanded_types(), frozenset(_TYPES)
        assert mata == code, (
            f"only in _expand_plottype_str: {sorted(mata - code)}; only in "
            f"_dash_plot_type_names(): {sorted(code - mata)}")

    def test_every_family_member_is_in_the_list(self):
        for fam in ("_pt_univar", "_pt_range", "_pt_pc", "_pt_literal",
                    "_pt_ts"):
            assert _FAMILIES.get(fam), f"dash.ado defines no {fam}"
            stray = sorted(_FAMILIES[fam] - set(_TYPES))
            assert not stray, f"{fam} names types the registry lacks: {stray}"

    def test_the_parametrization_is_the_list(self):
        """What pytest collects below is ``_TYPES`` itself: no floor, no
        subset, no duplicate."""
        assert len(_TYPES) == len(set(_TYPES)) == len(dr._dash_plot_type_names())
        for expected in ("scatter", "line", "histogram", "pci", "pcscatter",
                         "function", "mband"):
            assert expected in _TYPES


@pytest.mark.parametrize("ptype", _TYPES)
def test_a_plot_type_draws_a_glyph(ptype):
    fig = _render(_plot_for(ptype))
    assert len(fig.renderers) >= 1, (
        f"`dash {ptype} ...' is a plot type dash draws, and it draws "
        f"nothing: an empty plot region, rc 0, no warning"
    )


@pytest.mark.parametrize("ptype", _TYPES)
def test_a_plot_type_draws_real_data(ptype):
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
