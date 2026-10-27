"""The saved page's scripts read dash's working-column names from their
config (WP-35 DT-19, TR-35-08.5).

The filter mask (``_DASH_FILTER_MASK_JS``) read an extended missing value's
code column as ``'__dashm_' + fvar``; under a spec whose prefix is
``__dsh1_`` the codes travel in ``__dsh1_m_<var>`` and a user variable
``__dashm_<var>`` is data, so the mask reads the prefix from the filter's
own config (``code_prefix``, written by the renderer whenever it is not
the default).  The colorvar() relevel script fell back to
``"__dash_row__"`` for a line's row key; Python always hands it the key.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from js_runner import requires_node, run_js  # noqa: E402


def _mask(spec, value, orig):
    script = (dr._DASH_FILTER_MASK_JS
              + "\nconst orig = " + json.dumps(orig)
              + ";\nconst specs = " + json.dumps([spec])
              + ";\nconst widgets = " + json.dumps([{"value": value}])
              + ";\nprocess.stdout.write(JSON.stringify("
              "dash_filter_mask(orig, specs, widgets)));")
    return run_js(script)


@requires_node
def test_the_missing_code_prefix_comes_from_config():
    # mpg holds .a in rows 1 and 3; the codes travel in __dsh1_m_mpg, and
    # the user's own __dashm_mpg holds other letters.
    orig = {"mpg": [22.0, None, 25.0, None],
            "__dsh1_m_mpg": ["", "a", "", "b"],
            "__dashm_mpg": ["a", "", "a", "a"]}
    spec = {"varname": "mpg", "type": "dropdown", "sentinel": "__all__",
            "numeric": True, "code_prefix": "__dsh1_m_"}
    assert _mask(spec, "__dsh1_m_mpg=a", orig) == [False, True, False,
                                                     False]
    multi = dict(spec, type="multi", multi_values={})
    assert _mask(multi, ["__dsh1_m_mpg=b"], orig) == [False, False, False,
                                                       True]
    # No code_prefix: the default prefix, as every page dash wrote before.
    plain = {"varname": "mpg", "type": "dropdown", "sentinel": "__all__",
             "numeric": True}
    orig2 = {"mpg": [22.0, None], "__dashm_mpg": ["", "a"]}
    assert _mask(plain, "__dashm_mpg=a", orig2) == [False, True]


def test_the_relevel_script_has_no_row_id_fallback():
    js = dr._DASH_CVAR_RELEVEL_JS
    assert '"__dash_row__"' not in js
    assert "pl.key" in js and "ln.key" in js


def test_the_renderer_writes_the_code_prefix_only_when_not_the_default():
    m = dr._dash_module_for({"_dash_prefix": "__dsh1_"})
    assert m._DASH_CODE_PREFIX == "__dsh1_m_"
    assert dr._DASH_CODE_PREFIX == "__dashm_"
    assert dr._dash_filter_code_prefix() is None
    assert m._dash_filter_code_prefix() == "__dsh1_m_"
