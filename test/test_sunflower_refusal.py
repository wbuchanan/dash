"""
test_sunflower_refusal.py -- twoway sunflower refused by name (WP-31 B2,
section 21).

The defect (measured at a4fb89c): ``dash sunflower mpg weight`` was
answered "sunflower is not a twoway plot type" with the Supported: list,
as if twoway had no such type, and dash.sthlp's Not-drawn paragraph did
not name it.  twoway draws it (test/fixtures/rangept_truth.json
draw.sunflower: rc 0); its manual recommends the sunflower command over
twoway sunflower (twoway_sunflower.sthlp, advice.sunflower).  dash does
not draw it (PRD section 7) and refuses it by name, r(198), with that
advice (DECISIONS M4).
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

with open(os.path.join(_HERE, "fixtures", "rangept_truth.json"),
          encoding="utf-8") as _fh:
    _T = json.load(_fh)

#: The sentence dash.ado prints after "dash: 'sunflower' is a twoway plot
#: type dash does not draw: ".
_WHY = ("it bins points into density petals. Use Stata's own sunflower "
        "command, which Stata recommends over twoway sunflower, or dash "
        "scatter y x with jitter() or colorvar().")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestSunflowerRefused:

    def test_tuple(self):
        """_dash_undrawn_plottype names sunflower, the full name only, as
        twoway takes it (sunflow is "not a twoway plot type")."""
        mata = _read("dash_parse.mata")
        start = mata.index("string scalar _dash_undrawn_plottype(")
        body = mata[start:mata.index("\n}\n", start)]
        assert '"sunflower"' in body
        assert _T["probes"]["draw.sunflower"]["rc"] == 0
        assert _T["probes"]["abbrev.sunflow"]["message"] == \
            "sunflow is not a twoway plot type"

    def test_sentence(self):
        ado = _read("dash.ado")
        assert _WHY in ado
        assert re.search(r'"`_pt_nodraw\'" == "sunflower"', ado)
        # The manual's words the sentence paraphrases.
        lines = " ".join(_T["advice"]["sunflower"])
        assert "We" in lines and "recommend the {cmd:sunflower} command" \
            in lines

    def test_help(self):
        help_text = _read("dash.sthlp")
        para = help_text[help_text.index("{ul:Not drawn.}"):]
        para = para[:para.index("{marker ")]
        assert "{cmd:sunflower}" in para
        assert "Stata's {cmd:sunflower} command" in para
