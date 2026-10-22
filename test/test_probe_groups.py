"""Unit tests for test/probe_groups.py: probe groups and the gate's served
subset (pytest speed, 22oct2026)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import probe_groups as pg  # noqa: E402

_IDS = ["p%02d" % i for i in range(10)]


def _parts(params):
    return [(p.values[0], p.values[1], p.id,
             [m.name for m in p.marks]) for p in params]


class TestRepresentative:
    def test_always_then_each_category_then_the_stride(self):
        cat = {"p00": "a", "p01": "a", "p02": "a", "p03": "b", "p04": "a",
               "p05": "a", "p06": "c", "p07": "a", "p08": "a", "p09": "a"}
        got = pg.representative(_IDS, category=cat.get, always=["p08", "zz"],
                                stride=3)
        # always p08; categories a -> p00, b -> p03, c -> p06; the rest
        # p01 p02 p04 p05 p07 p09 at stride 3 -> p01 p05.
        assert got == ["p00", "p01", "p03", "p05", "p06", "p08"]

    def test_it_is_deterministic_and_sorted(self):
        a = pg.representative(list(reversed(_IDS)), stride=4)
        assert a == pg.representative(_IDS, stride=4) == ["p00", "p04", "p08"]

    def test_stride_one_keeps_every_id(self):
        assert pg.representative(_IDS, stride=1) == _IDS

    def test_a_stride_below_one_raises(self):
        with pytest.raises(ValueError):
            pg.representative(_IDS, stride=0)


class TestGroups:
    def test_cuts_in_order(self):
        assert pg.groups(_IDS[:5], 2) == [("p00", "p01"), ("p02", "p03"),
                                          ("p04",)]

    def test_no_size_is_one_group_and_none_is_empty(self):
        assert pg.groups(_IDS[:3]) == [("p00", "p01", "p02")]
        assert pg.groups([], 3) == []

    def test_a_negative_size_raises(self):
        with pytest.raises(ValueError):
            pg.groups(_IDS, -1)


class TestProbeParams:
    def test_whole_parts_keep_the_mode_ids(self):
        got = _parts(pg.probe_params(_IDS, subset=["p00", "p05"]))
        assert got == [
            ("saved", tuple(_IDS), "saved", []),
            ("served", ("p00", "p05"), "served", []),
            ("served", tuple(i for i in _IDS if i not in ("p00", "p05")),
             "served-rest", ["release"])]

    def test_groups_cover_every_probe_once_per_mode(self):
        sub = pg.representative(_IDS, stride=3)
        params = pg.probe_params(_IDS, subset=sub, size=2, saved_size=4)
        got = _parts(params)
        saved = [g for m, g, _, _ in got if m == "saved"]
        assert [len(g) for g in saved] == [4, 4, 2]
        served = [(g, mk) for m, g, _, mk in got if m == "served"]
        assert sorted(i for g, _ in served for i in g) == _IDS
        assert {i for g, mk in served if not mk for i in g} == set(sub)
        assert all(mk == ["release"] for g, mk in served
                   if set(g) - set(sub))
        assert got[0][2] == "saved-p00-p03"
        assert [i for _, _, i, _ in got if i.startswith("served-rest")][0] \
            == "served-rest-p01-p02"
        assert len({p.id for p in params}) == len(params)

    def test_no_subset_is_every_served_probe_unmarked(self):
        got = _parts(pg.probe_params(_IDS[:2], size=1))
        assert got == [("saved", ("p00",), "saved-p00", []),
                       ("saved", ("p01",), "saved-p01", []),
                       ("served", ("p00",), "served-p00", []),
                       ("served", ("p01",), "served-p01", [])]

    def test_empty_ids_and_a_stray_subset_raise(self):
        with pytest.raises(ValueError):
            pg.probe_params([])
        with pytest.raises(ValueError):
            pg.probe_params(_IDS, subset=["nope"])


class TestKnown:
    _KNOWN = {"p01": "X-1", "p02:text": "X-2", "q9": "X-3"}

    def test_known_in_takes_the_groups_rows(self):
        assert pg.known_in(self._KNOWN, ("p01", "p02")) == {
            "p01": "X-1", "p02:text": "X-2"}
        assert pg.known_in(self._KNOWN, ("p03",)) == {}

    def test_known_outside_names_rows_no_group_covers(self):
        assert pg.known_outside(self._KNOWN, _IDS) == ["q9"]

    def test_a_probe_of_reader(self):
        assert pg.known_outside({("a", 1): "X"}, ["a"],
                                probe_of=lambda k: k[0]) == []
