"""test_saving_chars.py -- the characters twoway's saving() writes as typed,
and the renderer's route for them (WP-30 P1.29; S12 reads the same
fixture for P1.27).

``test/fixtures/saving_chars_truth.json`` is written by
``scripts/extract_saving_chars_truth.do``: for each character WP-30 rules
on -- ``%`` (``pct%PATH%x``), ``!``, ``%%``, ``^``, ``&``, ``;``, ``|``,
``<``, ``>`` and a ``..`` segment -- twoway's return code for
``twoway scatter mpg weight, saving("<dir>/<name>.gph", replace) nodraw``
and whether the file was written under the name as typed.  twoway runs no
shell for saving(), so it writes every one of them (StataNow 19.5 on macOS;
Windows is unmeasured, WP-30 M4).  dash accepts the first four, as twoway
does; the rest are S12's.
"""
import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr  # noqa: E402

_TRUTH = os.path.join(_HERE, "fixtures", "saving_chars_truth.json")

_KEYS = ("pct_path", "bang", "pct_pct", "caret", "amp", "semi", "pipe", "lt",
         "gt", "dotdot")

#: The characters dash accepts in saving() at WP-30 P1.29.
_S04_KEYS = ("pct_path", "bang", "pct_pct", "caret")


@pytest.fixture(scope="module")
def truth():
    with open(_TRUTH, encoding="utf-8") as fh:
        return json.load(fh)


def _stem(record):
    """The probe's file name without ``tw_`` and ``.gph``."""
    f = record["file"]
    assert f.startswith("tw_") and f.endswith(".gph"), f
    return f[len("tw_"):-len(".gph")]


class TestTheTruthFixture:

    def test_meta_carries_the_stamp(self, truth):
        meta = truth["_meta"]
        for key in ("stata_version", "born_date", "dash_commit",
                    "extracted"):
            assert str(meta.get(key, "")).strip(), key
        assert meta["source"] == "scripts/extract_saving_chars_truth.do"

    def test_every_probe_is_recorded(self, truth):
        assert set(truth["probes"]) == set(_KEYS)
        for key, rec in truth["probes"].items():
            assert set(rec) == {"command", "file", "rc", "written"}, key
            assert rec["command"].startswith(
                "twoway scatter mpg weight, saving(\"<dir>/"), key

    def test_twoway_writes_every_name_as_typed(self, truth):
        for key in _KEYS:
            rec = truth["probes"][key]
            assert rec["rc"] == 0 and rec["written"] is True, (key, rec)


class TestTheRendererAcceptsWhatTwowayWrites:

    @pytest.mark.parametrize("key", _S04_KEYS)
    def test_the_four_s04_characters_pass_the_python_route(self, truth, key):
        stem = _stem(truth["probes"][key])
        html = "/tmp/x/%s.html" % stem
        py = "%s.py" % stem
        assert dr._validate_output_path(html, "standalone") == html
        assert dr._validate_output_path(py, "server") == py
