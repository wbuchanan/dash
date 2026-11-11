"""
test_corpus_ledger.py -- the corpus's known-differences ledger (WP-33 33-05).

scripts/corpus/ledger.tsv keys each known difference from twoway by its GAPS4
id; scripts/corpus/ledger.py compiles it into test/fixtures/
corpus_ledger.json.  Every row must be live (DECISIONS A-10): a plain row
while its item is open, a `(documented)` row while it is open or
Documented, a `(residual)` row while it is open or Partly closed -- so an
item's closing commit deletes its plain rows.
"""
import json
import os
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "test"))

import known_differences  # noqa: E402
from scripts.corpus import ledger, verdict  # noqa: E402

_FIXTURE = os.path.join(_ROOT, "test", "fixtures", "corpus_ledger.json")
_TSV = os.path.join(_ROOT, "scripts", "corpus", "ledger.tsv")


class TestTheLedger:

    def test_every_ledger_row_is_live(self):
        states = ledger.gaps4_states()
        rows = verdict.load_ledger(_FIXTURE)
        assert rows
        dead = [r["gaps4_id"] + " " + r["check"] for r in rows if not ledger.live(r, states)]
        assert dead == []
        unknown = [r["check"] for r in rows if r["check"] not in verdict.STATA_TERMS]
        assert unknown == []

    def test_the_json_is_the_tsv(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            doc = json.load(fh)
        assert doc["rows"] == ledger.read_tsv(_TSV)
        assert doc["_meta"]["source"] == "scripts/corpus/ledger.py"

    def test_the_states_agree_with_known_differences(self):
        s = ledger.gaps4_states()
        assert {i for i, v in s.items() if v == "open"} == known_differences.gaps4_open_ids()
        assert {i for i, v in s.items() if v == "documented"} == \
            known_differences.gaps4_documented_ids()
        assert {i for i, v in s.items() if v == "partly"} == known_differences.gaps4_partly_ids()


class TestOwners:

    def test_bar_outlines_belong_to_pt4(self):
        # D51: an outline dash strokes where twoway strokes none is
        # basic:PT-4's (outline_extra); a line-width difference stays VF-4's
        # on every plot type, bars included.  Flipped (WP-45 VF-4): VF-4 is
        # closed in part, the size unit open, so its rows are its residual's
        # ("VF-4 (residual)"); the figure was held in a 160-560 px band, and
        # twoway draws its graph's shape at any size (DECISIONS A-1).
        rows = verdict.load_ledger(_FIXTURE)
        states = ledger.gaps4_states()
        extra = [{"check": "outline_extra", "twoway": False, "dash": True,
                  "within_tol": False}]
        width = [{"check": "line_width", "twoway": [0.0012], "dash": [0.00107],
                  "within_tol": False}]
        for t in ("bar", "histogram", "rbar", "area", "line"):
            ex = {"plottype": t, "cmd": "twoway %s y x" % t}
            # Flipped (WP-47 basic:PT-4): basic:PT-4 is closed and its
            # plain outline_extra row deleted (D-33-05.i), so an extra
            # outline is owned by no open item.
            assert verdict.explain(extra, ex, rows, states)[0]["gaps4"] \
                is None, t
            assert verdict.explain(width, ex, rows, states)[0]["gaps4"] == \
                "VF-4 (residual)", t

    def test_clipped_marker_labels_belong_to_ms15(self):
        # D50: twoway draws a marker label past the plot region.  Flipped
        # (WP-47 MS-15, Partly): dash draws it so too, so a clipped label is
        # no item's; under by() it stops at its panel's edge, MS-15's
        # residual.
        rows = verdict.load_ledger(_FIXTURE)
        d = [{"check": "marker_labels", "twoway": True, "dash": False, "within_tol": False}]
        st = ledger.gaps4_states()
        ex = {"plottype": "scatter", "cmd": "scatter y x, mlabel(country)"}
        assert verdict.explain(d, ex, rows, st)[0]["gaps4"] is None
        ex = {"plottype": "scatter", "cmd": "scatter y x, mlabel(country) by(g)"}
        assert verdict.explain(d, ex, rows, st)[0]["gaps4"] == "MS-15 (residual)"


class TestReading:

    def test_read_tsv_and_live(self, tmp_path):
        p = tmp_path / "l.tsv"
        p.write_text("# header\nAX-4\tx_ticks\thistogram\t*\tbins\n"
                     "GW-6 (documented)\tframe_aspect\t*\t\\bby\\(\tmargins\n",
                     encoding="utf-8")
        rows = ledger.read_tsv(str(p))
        assert rows[0] == {"gaps4_id": "AX-4", "id": "AX-4", "form": "plain",
                           "check": "x_ticks", "plottype": "histogram", "when": "*",
                           "note": "bins"}
        assert rows[1]["form"] == "documented" and rows[1]["id"] == "GW-6"
        assert ledger.live(rows[0], {"AX-4": "open"})
        assert not ledger.live(rows[0], {"AX-4": "closed"})
        assert ledger.live(rows[1], {"GW-6": "documented"})
        assert not ledger.live(rows[1], {"GW-6": "partly"})
        assert ledger.live(dict(rows[1], form="residual"), {"GW-6": "partly"})
        p.write_text("AX-4\tx_ticks\thistogram\n", encoding="utf-8")
        with pytest.raises(ValueError, match="line 1"):
            ledger.read_tsv(str(p))

    def test_gaps4_states(self, tmp_path):
        p = tmp_path / "G.md"
        p.write_text("- **AX-1 Tracked:** Open (WP-34 section 34-03).\n"
                     "- **AX-2 Tracked:** Closed in WP-34 (commit pending).\n"
                     "- **AX-3 Tracked:** Documented in WP-34 (commit pending).\n"
                     "- **AX-4 Tracked:** Partly closed in WP-34 (commit pending).\n",
                     encoding="utf-8")
        assert ledger.gaps4_states(str(p)) == {"AX-1": "open", "AX-2": "closed",
                                               "AX-3": "documented", "AX-4": "partly"}

    def test_write_json_and_main(self, tmp_path):
        run = tmp_path / "run"
        run.mkdir()
        (run / "stata_version.txt").write_text("19.5\n")
        out = tmp_path / "l.json"
        rows = [{"gaps4_id": "AX-4", "id": "AX-4", "form": "plain", "check": "x_ticks",
                 "plottype": "*", "when": "*", "note": "n"}]
        doc = ledger.write_json(rows, str(out), str(run))
        assert doc["_meta"]["stata_version"] == "19.5"
        again = ledger.write_json(rows, str(out))
        assert again["_meta"]["stata_version"] == "19.5" and again["rows"] == rows
        tsv = tmp_path / "l.tsv"
        tsv.write_text("AX-4\tx_ticks\t*\t*\tn\n", encoding="utf-8")
        assert ledger.main(["--tsv", str(tsv), "--out", str(out)]) == 0
        assert json.loads(out.read_text())["rows"] == rows
