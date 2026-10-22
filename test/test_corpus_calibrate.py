"""
test_corpus_calibrate.py -- the verdict's calibration (WP-33 33-05).

scripts/corpus/calibrate.py measures the verdict's tolerances and image-score
thresholds on the committed calibration set (scripts/corpus/calibration.tsv)
and writes test/fixtures/corpus_verdict_rules.json.  The thresholds are
recorded, never gating (DECISIONS A-4): no stop rule, nothing raises.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts.corpus import calibrate, verdict  # noqa: E402

_FIXTURE = os.path.join(_ROOT, "test", "fixtures", "corpus_verdict_rules.json")


def _r(label="Same", ssim=0.8, aspect=0.01, checks=(), dists=()):
    return {"label": label, "ssim": ssim, "aspect_diff": aspect, "checks": list(checks),
            "colour_dists": list(dists)}


class TestThresholds:

    def test_from_rows(self, capsys):
        rows = [_r(ssim=0.80), _r(ssim=0.82, checks=["frame_aspect"], aspect=0.031),
                _r(ssim=0.84, checks=["colours"]), _r(ssim=0.10, checks=["titles"]),
                _r("Close", ssim=0.70, checks=["x_ticks"]), _r("Differs", ssim=0.95)]
        t = calibrate.thresholds(rows)
        # Clean Same rows: 0.80, 0.82, 0.84 (the titles row is left out).
        assert t["T_same"] == 0.8
        assert t["T_close"] == 0.7
        # D47: T_same is the lowest clean Same score, so no clean pair is Close.
        low = [_r(ssim=0.7334), _r(ssim=0.7416), _r(ssim=0.8287), _r(ssim=0.80),
               _r(ssim=0.81), _r(ssim=0.79), _r(ssim=0.78), _r(ssim=0.77)]
        assert calibrate.thresholds(low)["T_same"] == 0.7334
        assert t["aspect_abs"] == 0.035
        assert t["tick_rel"] == 1e-6 and t["extent_rel"] == 0.01
        # D49: the size and margin tolerances are recorded with the rules.
        assert (t["text_rel"], t["inset_abs"], t["size_rel"]) == (0.05, 0.005, 0.05)
        rows = [_r(dists=[1]), _r(dists=[2.0]), _r(dists=[3])]
        assert calibrate.thresholds(rows)["colour_tol"] == 3
        far = _r(dists=[200], checks=["colours"])
        assert calibrate.thresholds(rows + [far])["colour_tol"] == 3
        # The 200 row is a known colour difference: a colours ledger row
        # explains it at colour_tol 3 and the pair is Close.
        d = verdict.compare(
            {"colours": {"set": ["#1a85ff"]}}, {"colours": {"set": ["#ff0000"]}},
            {"tick_rel": 1e-6, "extent_rel": 0.01, "aspect_abs": 0.05, "colour_tol": 3})
        row = {"gaps4_id": "PIC-1", "id": "PIC-1", "form": "plain", "check": "colours",
               "plottype": "*", "when": "*", "note": "n"}
        d = verdict.explain(d, {"plottype": "area", "cmd": "twoway area y x"}, [row],
                            {"PIC-1": "open"})
        assert d[0]["gaps4"] == "PIC-1"
        assert verdict.verdict(0, 0, None, None, d, 0.99, {"T_same": 0.8}) == "Close"
        capsys.readouterr()
        assert calibrate.thresholds([_r(), _r(), _r()])["colour_tol"] == 0
        assert "calibrate: colour_tol 0:" in capsys.readouterr().out

    def test_no_stop_rule(self, capsys):
        rows = [_r(ssim=0.80), _r(ssim=0.81), _r(ssim=0.82),
                _r("Differs", ssim=0.99, checks=["titles"])]
        t = calibrate.thresholds(rows)
        assert t["T_same"] is not None and t["T_close"] is None
        two = calibrate.thresholds([_r(), _r()])
        assert two["T_same"] is None
        assert "calibrate: T_same null: 2 clean Same rows" in capsys.readouterr().out
        assert calibrate.thresholds([])["aspect_abs"] == 0.05


class TestPrepare:

    def test_mutated_copies(self, tmp_path):
        assert calibrate.mutate("dash scatter mpg weight", 'title("Mutated")') == \
            'dash scatter mpg weight, title("Mutated")'
        assert calibrate.mutate("dash scatter mpg weight, ms(O)", "msymbol(T)") == \
            "dash scatter mpg weight, ms(O) msymbol(T)"
        table = tmp_path / "calibration.tsv"
        table.write_text("# id\tlabel\tmutation\nA\tSame\t-\nA\tDiffers\tmsymbol(T)\n"
                         "B\tClose\t-\n", encoding="utf-8")
        rows = calibrate.read_table(str(table))
        assert [r["case"] for r in rows] == ["A", "cal-A-1", "B"]
        ex = {"id": "A", "cmd": "twoway scatter mpg weight",
              "dash_cmd": "dash scatter mpg weight", "plottype": "scatter"}
        (tmp_path / "examples.jsonl").write_text(json.dumps(ex) + "\n" +
                                                 json.dumps(dict(ex, id="B")) + "\n")
        assert calibrate.prepare(str(tmp_path), str(table)) == 1
        assert calibrate.prepare(str(tmp_path), str(table)) == 0
        got = [json.loads(x) for x in (tmp_path / "examples.jsonl").read_text().splitlines()]
        cal = got[-1]
        assert cal["id"] == "cal-A-1" and cal["cmd"] == "twoway scatter mpg weight"
        assert cal["dash_cmd"] == "dash scatter mpg weight, msymbol(T)"

    def test_write_rules_and_main(self, tmp_path, monkeypatch, capsys):
        seen = []
        monkeypatch.setattr(calibrate, "_measure", lambda run, table, rules, probe: (
            seen.append(rules) or [dict(_r(ssim=0.9), id=t["case"]) for t in table]))
        monkeypatch.setattr(verdict, "_open_probe", lambda run: (_ for _ in ()).throw(
            RuntimeError("no Chrome")))
        table = tmp_path / "calibration.tsv"
        table.write_text("A\tSame\t-\nB\tSame\t-\nC\tSame\t-\n", encoding="utf-8")
        (tmp_path / "stata_version.txt").write_text("19.5\n")
        (tmp_path / "twoway.jsonl").write_text("")
        out = tmp_path / "rules.json"
        doc = calibrate.write_rules(str(tmp_path), str(out), str(table))
        assert doc["T_same"] == 0.9 and len(doc["calibration"]) == 3
        assert json.loads(out.read_text())["_meta"]["source"] == "scripts/corpus/calibrate.py"
        assert calibrate.main(["--write", str(tmp_path), "--table", str(table),
                               "--out", str(out)]) == 0
        assert "calibrate: T_same 0.9" in capsys.readouterr().out


class TestTheFixture:

    def test_rules_fixture(self):
        with open(_FIXTURE, encoding="utf-8") as fh:
            d = json.load(fh)
        for k in ("_meta", "T_same", "T_close", "tick_rel", "extent_rel", "aspect_abs",
                  "colour_tol", "text_rel", "inset_abs", "size_rel", "calibration"):
            assert k in d, k
        assert d["T_same"] is None or 0 < d["T_same"] <= 1
        assert d["aspect_abs"] <= 0.05
        assert isinstance(d["colour_tol"], int) and 0 <= d["colour_tol"] <= 32
        assert len(d["calibration"]) == 32
        table = calibrate.read_table()
        assert [r["case"] for r in table] == [c["id"] for c in d["calibration"]]
        # Flipped: the set held Same rows; the maintainer relabelled every
        # unmutated pair Close (D49), so T_same is recorded null.
        assert sorted({r["label"] for r in table}) == ["Close", "Differs"]
        assert d["T_same"] is None
