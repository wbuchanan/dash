"""An option twoway refuses on a plot type is refused by dash there too.

WP-31 C3 (GAPS3 A12; BUGS.md "kernel() on a type that takes no kernel is
written to the spec without a note").  twoway's plot parsers leave an
option they do not declare in ``.options``, and the graph class runs
``syntax [, FAKE_OPT_FOR_BETTER_MSG]`` on what is left, so ``twoway scatter
mpg weight, kernel(gaussian)`` is r(198) "option kernel() not allowed".
dash wrote every such option to the spec and drew nothing different.

Which type takes which option is measured, never typed:
scripts/extract_applicability_truth.do probes fourteen value options on
forty types into test/fixtures/applicability_truth.json, and
scripts/gen_applicability_table.py writes the ``applies`` block of
``_dash_option_rules`` from it.  ``_dash_validate_opts`` reads the block and
refuses an option on a type outside its list before any value rule runs.
These tests check the table against the fixture and the check's place
without Stata; test/test_option_validation.cscript U04-01..U04-04 compare
dash's rc and line with twoway's live.
"""
import json
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")
sys.path.insert(0, _ROOT)
sys.path.insert(0, _HERE)

import dash_render as dr  # noqa: E402
from test_abbreviations import _program_body  # noqa: E402

_ADO = os.path.join(_ROOT, "dash.ado")
_FIXTURE = os.path.join(_HERE, "fixtures", "applicability_truth.json")
_GEN = os.path.join(_ROOT, "scripts", "gen_applicability_table.py")
_BEGIN = "// BEGIN applies"
_END = "// END applies"

# WP-31 B5b: ndots() and dotextend(), dot's own two, measured too.
OPTIONS = ("kernel", "n", "level", "bwidth", "bands", "range", "base",
           "degree", "bin", "width", "start", "barwidth", "ndots",
           "dotextend")

with open(_FIXTURE, encoding="utf-8") as _fh:
    TRUTH = json.load(_fh)
PAIRS = TRUTH["pairs"]


def _ado():
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _rules_block():
    """The text between the applies markers of _dash_option_rules."""
    src = _program_body(_ado(), "_dash_option_rules")
    i = src.index(_BEGIN)
    i = src.index("\n", i) + 1
    return src[i:src.index(_END, i)]


def _table():
    """``{option: [type, ...]}`` read back from dash.ado's applies block."""
    text = _rules_block().replace("///", " ")
    out = {}
    for tok in text.split():
        if "@" in tok:
            opt, types = tok.split("@", 1)
            out[opt] = types.split("|")
    return out


def _is_refusal(opt, rec):
    """twoway's syntax refusal: r(198) "option <opt>() not allowed".  Any
    other answer (rc 0, or a class's own message on a value) means the type
    declares the option, so the pair applies (D-04.b)."""
    return rec["rc"] == 198 and rec["message"] == f"option {opt}() not allowed"


def _accepted(opt):
    return [t for t in TRUTH["types"]
            if not _is_refusal(opt, PAIRS[f"{opt}@{t}"])]


def _refused(opt):
    return [t for t in TRUTH["types"]
            if _is_refusal(opt, PAIRS[f"{opt}@{t}"])]


class TestTheFixture:
    def test_meta_is_stamped(self):
        assert sorted(TRUTH["_meta"]) == ["born_date", "dash_commit",
                                          "extracted", "source",
                                          "stata_version"]
        assert TRUTH["_meta"]["source"] == \
            "scripts/extract_applicability_truth.do"

    def test_every_pair_was_measured(self):
        assert tuple(TRUTH["options"]) == OPTIONS
        assert len(TRUTH["types"]) == 40
        # 480 -> 560: B5b ndots() and dotextend() on the forty types
        assert len(PAIRS) == 560
        for key, rec in PAIRS.items():
            assert rec["rc"] in (0, 198) or rec["message"], key


class TestTheTableIsTheFixture:
    def test_the_block_is_generated(self):
        """A hand edit of the block fails here: --check regenerates it."""
        res = subprocess.run([sys.executable, _GEN, "--check"],
                             capture_output=True, text=True)
        assert res.returncode == 0, res.stdout + res.stderr

    @pytest.mark.parametrize("opt", OPTIONS)
    def test_each_option_lists_its_types(self, opt):
        assert _table().get(opt) == _accepted(opt)

    def test_every_type_exists(self):
        drawn = set(dr._dash_plot_type_names())
        listed = {t for ts in _table().values() for t in ts}
        assert listed and listed <= drawn, sorted(listed - drawn)


class TestTheCheck:
    def test_the_check_precedes_the_value_rules(self):
        body = _program_body(_ado(), "_dash_validate_opts")
        loop = body.find("foreach tok of local _dash_rules_applies")
        typed = body.find('local typed ""')
        assert loop != -1 and typed != -1 and loop < typed

    def test_the_message_is_twoways(self):
        """Every refused pair carries one form, the one the check prints."""
        assert all(_refused(o) for o in OPTIONS)
        forms = {PAIRS[f"{o}@{t}"]["message"].replace(f"{o}()", "<opt>()")
                 for o in OPTIONS for t in _refused(o)}
        assert forms == {"option <opt>() not allowed"}, forms
        body = _program_body(_ado(), "_dash_validate_opts")
        assert 'display as error "option `o\'() not allowed"' in body


class TestNothingRefusedIsAlsoNamed:
    def test_pending_blocks(self):
        named = re.findall(r"_dash_pending' (\w+)\"", _ado())
        assert not set(named) & set(OPTIONS), sorted(set(named) & set(OPTIONS))

    def test_plot_values(self):
        """PLOT_VALUES probes an option as accepted and not honoured on its
        type; on a type twoway refuses it on, dash now refuses it."""
        from test_unsupported_report_is_true import PLOT_VALUES
        table = _table()
        bad = {o: v[2] for o, v in PLOT_VALUES.items()
               if o in table and v[2] not in table[o]}
        assert not bad, bad

    def test_the_json_keys_are_kept(self):
        """The accepting types still carry the options to the renderer."""
        body = _program_body(_ado(), "_dash_plot_opts_to_json")
        words = set(re.sub(r"///", " ", body).split())
        assert set(OPTIONS) <= words, sorted(set(OPTIONS) - words)
