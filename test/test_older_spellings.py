"""twoway's older spellings, read as the options they stand for (WP-47
basic:PT-10, section 47-04).

twoway_yxview_parse.class factors symbol(), msymangle(), mlabels(),
bcolor(), bfintensity(), blwidth(), blpattern(), afcolor(),
afintensity(), bsymbol() and bmsize() onto the marker, label and area
edits of msymbol(), msangle(), mlabel(), acolor(), fintensity(),
alwidth(), alpattern(), fcolor(), bmsymbol() and barbsize(); dash named
every one in its "ignoring unsupported option(s)" note and drew the
default.  Measured in test/fixtures/alias_truth.json
(scripts/extract_alias_truth.do, graph export SVG): each alias draws its
target's picture (P1); of two options factored onto one edit the one the
class factors later is drawn whatever the typed order (P2, P3, pairs),
except mlabels(), which is mlabel()'s own full name, where the rightmost
copy is drawn; each alias is read from twoway's minimum spelling (P4); a
bad value is what the target makes of it (P5).

No pytest runs Stata: these pin the fixture, the fold's table in
dash.ado's _dash_fold_alias and its place in the pipeline, and that both
renderers draw each target on the alias's probe type.  The S04 block of
test/test_wp47_truth.cscript (Q4704-1 ..) runs the aliases through dash.
"""
import json
import os
import re
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

import test_mode_parity as tp  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402
from test_server_layer_defects import plot_for  # noqa: E402

_ADO = os.path.join(_HERE, "..", "dash.ado")
_FIX = os.path.join(_HERE, "fixtures", "alias_truth.json")
_CATCH = os.path.join(_HERE, "fixtures", "catchall_options_truth.json")

#: The ten aliases _dash_fold_alias reads (symbol() is read by
#: _dash_fold_stat_words, WP-35 syn:SD-20c).
_ALIASES = ("msymangle", "mlabels", "bcolor", "bfintensity", "blwidth",
            "blpattern", "afcolor", "afintensity", "bsymbol", "bmsize")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _rows():
    """_dash_fold_alias's table: alias -> (minimum, target, yields), from
    its `local _fa_rows' line (alias:minimum:target:yields, the options
    the alias gives way to joined by '+', '-' for none, 'rightmost' for
    the typed order)."""
    body = _program_body(_read(_ADO), "_dash_fold_alias")
    assert body is not None, "_dash_fold_alias is not defined"
    m = re.search(r'^\s*local _fa_rows "([^"]*)"', body, re.M)
    assert m, "_dash_fold_alias has no _fa_rows table"
    out = {}
    for row in m.group(1).split():
        al, mn, tg, yl = row.split(":")
        out[al] = (mn, tg, () if yl == "-" else tuple(yl.split("+")))
    return out


class TestTheFixture:
    def test_meta(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit", "extracted",
                                      "method", "source", "stata_version"]
        assert d["_meta"]["source"] == "scripts/extract_alias_truth.do"

    @pytest.mark.parametrize("alias", ("symbol",) + _ALIASES)
    def test_each_alias_draws_its_target(self, alias):
        e = _truth()[alias]
        assert e["P1"]["rc"] == 0
        assert e["P1"]["same_as_target"] is True
        assert e["P1"]["same_as_target_w"] is True
        assert e["P1"]["differs_from_base"] is True

    def test_on_the_other_types_too(self):
        for o in _truth()["others"]:
            assert o["rc"] == 0 and o["same_as_target"] is True, o


def _draws(e, how):
    """Who wins a probe: 'alias', 'target' or None."""
    if how == "P2":       # T(v) A(w): first is T
        return {"first": "target", "second": "alias"}.get(e["P2"]["draws"])
    return {"first": "alias", "second": "target"}.get(e["P3"]["draws"])


class TestTheFold:
    def test_fold_is_defined_and_runs_before_the_rules(self):
        """_dash_fold_alias runs in _dash_process_segment after the
        refusals and the repeat merge, first in the fold chain (before
        _dash_fold_mlabv and _dash_fold_bw, so before _dash_validate_opts
        judges the target's value)."""
        src = _read(_ADO)
        body = _program_body(src, "_dash_fold_alias")
        assert body is not None
        assert re.search(r"^\s*version 19\s*$", body, re.M)
        assert re.search(r"^program define _dash_fold_alias, sclass", src, re.M)
        seg = _program_body(src, "_dash_process_segment")
        lines = [ln.strip() for ln in seg.splitlines()]
        at = {k: [i for i, ln in enumerate(lines) if ln.startswith(k + " ")]
              for k in ("_dash_fold_alias", "_dash_opts_repeats",
                        "_dash_fold_mlabv", "_dash_fold_bw")}
        assert len(at["_dash_fold_alias"]) == 1, at
        i = at["_dash_fold_alias"][0]
        assert at["_dash_opts_repeats"][0] < i < at["_dash_fold_mlabv"][0] \
            < at["_dash_fold_bw"][0], at

    @pytest.mark.parametrize("alias", _ALIASES)
    def test_the_target_is_twoways(self, alias):
        assert _rows()[alias][1] == _truth()[alias]["target"]

    @pytest.mark.parametrize("alias", _ALIASES)
    @pytest.mark.parametrize("how", ("P2", "P3"))
    def test_precedence(self, alias, how):
        """T(v) A(w) and A(w) T(v): the fold gives way to the target
        exactly where twoway draws the target (mlabels: the rightmost)."""
        e = _truth()[alias]
        win = _draws(e, how)
        yields = _rows()[alias][2]
        if yields == ("rightmost",):
            assert win == ("alias" if how == "P2" else "target"), (alias, how)
        elif e["target"] in yields:
            assert win == "target", (alias, how, win)
        else:
            assert win == "alias", (alias, how, win)

    @pytest.mark.parametrize("pair", (
        "fcolor_afcolor", "bfcolor_afcolor", "bcolor_afcolor",
        "afintensity_bfintensity", "fintensity_bfintensity",
        "fintensity_afintensity", "acolor_bcolor", "alcolor_bcolor",
        "alwidth_blwidth", "alpattern_blpattern", "barbsize_bmsize",
        "bmsymbol_bsymbol", "msangle_msymangle", "mlabel_mlabels"))
    def test_pair_precedence(self, pair):
        """The other option of each measured pair: an alias gives way to it
        exactly where twoway draws it, whatever the order."""
        p = _truth()["pairs"][pair]
        x = p["first"].split("(")[0]
        y = p["second"].split("(")[0]
        rows = _rows()
        al, other = (y, x) if y in rows else (x, y)
        yields = rows[al][2]
        if yields == ("rightmost",):
            assert (p["xy"]["draws"], p["yx"]["draws"]) == ("second", "first")
            return
        al_pos = "first" if al == x else "second"
        for k in ("xy", "yx"):
            assert p[k]["rc"] == 0
            won = p[k]["draws"] == al_pos
            assert won == (other not in yields), (pair, k, yields)

    def test_bcolor_clears_alcolor(self):
        """bcolor() is drawn over alcolor() (pairs alcolor_bcolor): the
        fold empties s(alcolor), which _dash_fold_typed would draw over
        acolor()."""
        assert _truth()["pairs"]["alcolor_bcolor"]["xy"]["draws"] == "second"
        body = _program_body(_read(_ADO), "_dash_fold_alias")
        assert re.search(r'sreturn local alcolor ""', body)

    def test_symbol_is_drawn_over_msymbol(self):
        """syn:SD-20c read symbol() only when no msymbol() was given;
        twoway draws symbol() over msymbol() in either order
        (alias_truth.json pairs msymbol_symbol)."""
        p = _truth()["pairs"]["msymbol_symbol"]
        assert (p["xy"]["draws"], p["yx"]["draws"]) == ("second", "second")
        body = _program_body(_read(_ADO), "_dash_fold_stat_words")
        assert "_fsw_m" not in body

    @pytest.mark.parametrize("alias", ("symbol",) + _ALIASES)
    def test_not_named(self, alias):
        """dash's note (catchall_options_truth.json, re-measured) no
        longer names a folded alias, and bmsize() off the arrows without a
        back symbol stays named (twoway draws nothing different with it).
        Flipped (WP-47 basic:PT-11): bsymbol() was named as bmsymbol(),
        which was wrong once 47-05 draws the back marker it asks for."""
        with open(_CATCH, encoding="utf-8") as fh:
            c = json.load(fh)
        noted = c["probes"][alias]["noted"]
        want = {"bmsize": ["bmsize"]}.get(alias, [])
        assert noted == want, (alias, noted)
        if not want:
            assert alias not in c["options"]

    def test_mlabels_reaches_the_pattern_rule(self):
        """mlabels() is written to s(mlabel) before _dash_validate_opts,
        whose mlabel rule is _dash_mlabel_list (47-02's pattern reader):
        mlabels(t*) is read as mlabel(t*) (Q4704-4 runs both)."""
        body = _program_body(_read(_ADO), "_dash_fold_alias")
        assert re.search(r'st_global\("s\(mlabel\)"', body)
        assert "mlabels:mlabels:mlabel:rightmost" in body


# What _dash_fold_typed writes for a bar's area options (af_fill).
_ON_BAR = {"acolor": "color", "alwidth": "lwidth", "alpattern": "lpattern"}


def _profile(mode, plot):
    spec = tp._spec([plot])
    if mode == "saved":
        r, _w = tp._standalone(spec)
        models = list(r._last_layout_root.references())
    else:
        doc, _w = tp._served(spec)
        models = [m for root in doc.roots for m in root.references()]
    figs = [m for m in models if type(m).__name__.lower() == "figure"]
    assert figs
    labels = sorted(str(getattr(m.text, "field", m.text)) for m in models
                    if type(m).__name__ == "LabelSet")
    return tp._figure_profile(figs[0]), labels


def _ptype(cmd):
    return cmd.split()[0]


@pytest.mark.parametrize("mode", ("saved", "served"))
@pytest.mark.parametrize("alias", tuple(a for a in _ALIASES if a != "bsymbol"))
def test_alias_draws_its_target(mode, alias):
    """The option the fold writes for each alias is one both renderers
    draw on the alias's probe type: its picture is not the plain one, as
    twoway's is not (P1 differs_from_base).  bsymbol() is bmsymbol(),
    drawn by 47-05."""
    e = _truth()[alias]
    tg = _rows()[alias][1]
    assert tg == e["target"]
    t = _ptype(e["command"])
    base = {"msymbol": "T"} if alias == "msymangle" else {}
    key = _ON_BAR.get(tg, tg) if t == "bar" else tg
    o = dict(base)
    o[key] = e["v"]
    if alias == "mlabels":
        o[key] = "price"  # a column of the test data
    assert _profile(mode, plot_for(t, o)) != _profile(mode, plot_for(t, base))


@pytest.mark.parametrize("alias", ("symbol",) + _ALIASES)
def test_spellings_bind_as_twoways(alias):
    """Each spelling twoway reads as the alias (P4: rc 0 and the alias's
    picture) is one the fold reads, and no shorter one: its minimum is
    twoway's."""
    e = _truth()[alias]
    if alias == "symbol":
        body = _program_body(_read(_ADO), "_dash_fold_stat_words")
        m = re.search(r'inlist\("`_fsw_nm\'", ((?:"[a-z]+",? ?)+)\)', body)
        assert m
        dash = set(re.findall(r'"([a-z]+)"', m.group(1)))
    else:
        mn = _rows()[alias][0]
        dash = {alias[:j] for j in range(len(mn), len(alias) + 1)}
    twoway = {s for s, x in e["P4"].items()
              if x["rc"] == 0 and x["draws_alias"]}
    if alias == "mlabels":
        # mlabel() is MLabels' own minimum: ml .. mlabel are dash's
        # MLabel(), the same option; only the full name reaches the fold.
        assert twoway == {"ml", "mla", "mlab", "mlabe", "mlabel", "mlabels"}
        assert dash == {"mlabels"}
        return
    assert dash == twoway, (alias, sorted(dash), sorted(twoway))
    assert e["min_abbrev"] == min(dash, key=len)
