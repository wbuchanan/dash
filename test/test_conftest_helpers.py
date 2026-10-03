"""The shared test-data helper writes what Stata's exporter writes.

WP-29 P0.3: ``conftest.make_data_json`` used to label every variable with
its own name, so no test ever saw the ``""`` label that
``dash_render._dash_write_stata_data`` writes for an unlabelled variable,
and the blank titles, keys and tooltip rows that followed were invisible.
"""
import json
import os
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr
from conftest import make_data_json
from test_string_value_export import FakeSfi


def _written_labels(tmp_path, var_labels=None):
    path = str(tmp_path / "data.json")
    dr._dash_write_stata_data(
        path, "mpg weight",
        sfi=FakeSfi({"mpg": [1.0, 2.0], "weight": [3.0, 4.0]},
                    {"mpg": "double", "weight": "double"},
                    var_labels=var_labels))
    with open(path, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc.get("StataJSON", doc)["variableLabels"]


_DF = pd.DataFrame({"mpg": [1.0, 2.0], "weight": [3.0, 4.0]})


class TestTheHelperIsJsonioFaithful:
    def test_an_unlabelled_variable_has_an_empty_label(self, tmp_path):
        got = make_data_json(_DF)["StataJSON"]["variableLabels"]
        assert got == _written_labels(tmp_path) == {"mpg": "", "weight": ""}

    def test_labels_can_be_given(self, tmp_path):
        got = make_data_json(
            _DF, variable_labels={"mpg": "Mileage"})["StataJSON"]["variableLabels"]
        assert got == {"mpg": "Mileage", "weight": ""}
        assert got == _written_labels(tmp_path, {"mpg": "Mileage"})
