"""Unit tests of scripts/merge_value_truth.py, which appends Stata-measured
probes to test/fixtures/value_truth.json without touching earlier ones."""
import copy
import importlib.util
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "merge_value_truth",
    os.path.join(_HERE, "..", "scripts", "merge_value_truth.py"))
mv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mv)


def _probe(tmp_path, pid, rc, option, value, cmd, log):
    (tmp_path / ("probe_%s.rc" % pid)).write_text(
        "%d\n%s\n%s\n%s\n" % (rc, option, value, cmd), encoding="utf-8")
    (tmp_path / ("probe_%s.log" % pid)).write_text(log, encoding="utf-8")
    return str(tmp_path / ("probe_%s.rc" % pid))


def _fixture():
    return {"_meta": {"counts": {"twoway": 1, "twoway_rc0": 1,
                                 "twoway_rejected": 0}, "additions": []},
            "twoway": [{"id": "old_1", "option": "old", "value": "1",
                        "command": "c", "rc": 0, "message": ""}]}


def test_read_probe_joins_the_non_blank_lines(tmp_path):
    p = _probe(tmp_path, "xtick_1", 198, "xtick", "abc", "twoway x",
               "\n  invalid label specifier\n\n more \n")
    assert mv.read_probe(p) == {
        "id": "xtick_1", "option": "xtick", "value": "abc",
        "command": "twoway x", "rc": 198,
        "message": "invalid label specifier more"}


def test_read_probe_refuses_a_malformed_id(tmp_path):
    p = _probe(tmp_path, "Bad-id_1", 0, "o", "v", "c", "")
    with pytest.raises(ValueError):
        mv.read_probe(p)


def test_merge_appends_in_order_and_recounts():
    fx = _fixture()
    before = copy.deepcopy(fx["twoway"])
    recs = [{"id": "a_10", "rc": 0}, {"id": "a_2", "rc": 198},
            {"id": "a_1", "rc": 0}]
    mv.merge(fx, recs, "note")
    assert fx["twoway"][:1] == before
    assert [r["id"] for r in fx["twoway"][1:]] == ["a_1", "a_2", "a_10"]
    assert fx["_meta"]["counts"] == {"twoway": 4, "twoway_rc0": 3,
                                     "twoway_rejected": 1}
    assert fx["_meta"]["additions"] == ["note"]


def test_merge_never_overwrites_a_measured_record():
    fx = _fixture()
    with pytest.raises(ValueError):
        mv.merge(fx, [{"id": "old_1", "rc": 198}], "note")
    assert fx == _fixture()
