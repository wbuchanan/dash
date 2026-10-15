"""
test_pcycle_fraction.py -- pcycle() with a fractional value (WP-31 C8d,
section 32).

Before: dash refused every pcycle() that was not a positive integer,
"option seriesid() not allowed", where twoway draws a fraction whenever
every series' number mod(serid - 1, #) + 1 is whole.  Measured by
scripts/extract_pcycle_fraction_truth.do on 1, 2, 3, 4 and 16 series
(test/fixtures/pcycle_fraction_truth.json): pcycle(1.5) draws one or two
series (p1 p2) and refuses three; pcycle(0.5) draws every series in p1;
pcycle(2.2) draws three (p1 p2 p3) and refuses four; pcycle(15.5) draws
sixteen, the sixteenth with twoway's note "pstyle p16 not found in scheme"
and p1's look; pcycle(0) and pcycle(-1) are refused on every graph.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402
from test_colorvar_options import _figs, tmp  # noqa: E402,F401
from test_server_layer_defects import plot_for  # noqa: E402

_FIX = os.path.join(_HERE, "fixtures", "pcycle_fraction_truth.json")
_ADO = os.path.join(_HERE, "..", "dash.ado")
_MODES = ("saved", "served")


def _truth():
    with open(_FIX, encoding="utf-8") as fh:
        return json.load(fh)


def _probes():
    out = []
    for key, rec in sorted(_truth().items()):
        if key == "_meta" or key.endswith("_none"):
            continue
        n, p = key.split("_", 1)
        out.append((int(n[1:]), p.replace("p", ".").replace("m", "-"), rec))
    return out


class TestTheFixture:
    def test_it_is_stamped_and_complete(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert d["n2_1p5"]["rc"] == 0 and d["n2_1p5"]["pstyle"][:2] == [1, 2]
        assert d["n3_1p5"]["lines"] == ["option seriesid() not allowed"]
        assert d["n16_0p5"]["pstyle"][:16] == [1] * 16


class TestTheRule:
    """The refusal itself is dash.ado's (_dash_pcycle_bad), run against
    every probe of the fixture in test_option_validation.cscript U32-11."""

    def test_the_ado_reads_the_series(self):
        with open(_ADO, encoding="utf-8") as fh:
            ado = fh.read()
        assert "_dash_pcycle_bad(" in ado


class TestTheStyles:
    def test_every_drawn_probe(self):
        """The p# of each series, for every probe twoway drew."""
        bad = []
        for n, p, rec in _probes():
            if rec["rc"] != 0:
                continue
            got = [i + 1 for i in dr._dash_plot_style_indices(
                [{"type": "scatter"}] * n,
                dr._dash_pcycle({"pcycle": p}))]
            if got != rec["pstyle"][:n]:
                bad.append((n, p, got, rec["pstyle"][:n]))
        assert not bad, bad

    @pytest.mark.parametrize("mode", _MODES)
    @pytest.mark.parametrize("p, same", [("1.5", False), ("0.5", True)])
    def test_drawn(self, tmp, mode, p, same):  # noqa: F811
        plots = [dict(plot_for("scatter"), yvar=y) for y in ("mpg", "price")]
        (figs, _w) = _figs(tmp, mode, plots, go={"pcycle": p})
        [f] = figs
        cols = [str(r.glyph.fill_color).lower() for r in f.renderers
                if type(r.glyph).__name__ == "Scatter"]
        assert (cols[0] == cols[1]) == same, cols
