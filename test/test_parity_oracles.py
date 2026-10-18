"""The saved-JS move oracle of test_mode_parity.py (WP-31 H6, S60 D-60f):
``_saved_js_after_move`` runs the saved page's own filter script under node
and reads the glyphs back from the sources it wrote.  One spec, checked
against the rows the move keeps, so the oracle is known to read the
mutated sources rather than the build's."""
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import js_runner  # noqa: E402

pytestmark = pytest.mark.skipif(js_runner.find_node() is None,
                                reason="node is not installed")


class TestTheJsOracle:

    def test_it_reads_the_mutated_sources(self):
        import test_mode_parity as mp
        spec = mp._spec([mp.plot_for("scatter")],
                        {"filter": "price, type(slider)"})
        before, _ = mp._standalone(spec)
        figs = []
        mp._layout_tree(before._last_layout_root, figs)
        n_before = len(figs[0]["glyphs"][0]["coords"]["x"][1])
        after = mp._saved_js_after_move(spec, ("Slider", 4500.0))
        x_after = after[0][0]["coords"]["x"][1]
        kept = int((mp._DF["price"] >= 4500).sum())
        assert 0 < kept < n_before
        assert len(x_after) == kept
        served, _ = mp._served_after_move(spec, ("Slider", 4500.0))
        assert after[0] == served[0]["glyphs"]
