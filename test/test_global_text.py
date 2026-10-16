"""Global macros in graph text options, drawn as twoway draws them
(WP-31 D13b).

The defect: a text typed with ``\\$name`` (so that it reaches the command
as ``$name``) is expanded by twoway in every graph text option -- title(),
subtitle(), note(), caption(), the axis and edge titles, legend labels,
tick labels and text() -- while dash expanded it only in text() (S30) and
drew the others literally.  twoway reads the option's whole text again
before its quotes and sub-options are read (measured,
test/fixtures/global_text_truth.json from
scripts/extract_global_text_truth.do): a global holding a double quote
splits the string, and twoway refuses it in a tick label or text().
dash expands by text at registration (Mata ``_dash_at_globals`` on the
option's whole text), never evaluating: a global holding an =exp is drawn
as written.  Both modes and the stored text are checked by
test/test_wp31_truth.cscript U42-05 and U42-06.
"""

import json
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_FIXTURE = os.path.join(_HERE, "fixtures", "global_text_truth.json")
_OPTIONS = ("title", "subtitle", "note", "caption", "xtitle", "ytitle",
            "t1title", "b2title", "l1title", "r1title", "legend", "xlabel",
            "text")
_KINDS = ("plain", "braced", "smcl", "quote", "eval", "empty", "unset",
          "nested")


def _truth():
    if not os.path.exists(_FIXTURE):
        pytest.fail(f"{_FIXTURE} is missing; run "
                    "scripts/extract_global_text_truth.do")
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


class TestGlobalFixture:

    def test_meta(self):
        d = _truth()
        assert sorted(d["_meta"]) == ["born_date", "dash_commit",
                                      "extracted", "source",
                                      "stata_version"]
        assert len(d["cases"]) == len(_OPTIONS) * len(_KINDS)

    def test_twoway_expands_in_every_option(self):
        """Every option expands every kind the same way, before its quotes
        are read: a global holding a double quote ends the string ("a say "),
        and a tick label or text() holding it is refused, r(198)."""
        d = _truth()
        want = {"plain": "a hello b", "braced": "a hellob",
                "smcl": "a xy b", "quote": "a say ", "eval": "a 2 b",
                "empty": "a  b", "unset": "a  b", "nested": "a hello b"}
        refused = {("quote", "xlabel"), ("quote", "text")}
        bad = []
        for c in d["cases"]:
            if (c["kind"], c["option"]) in refused:
                if c["rc"] != 198:
                    bad.append((c["option"], c["kind"], c["rc"]))
            elif c["rc"] != 0 or c.get("drawn") != [want[c["kind"]]]:
                bad.append((c["option"], c["kind"], c.get("drawn")))
        assert not bad


class TestTheRegistration:

    def test_text_options_expand_their_globals(self):
        """The gopts loop expands each text option's globals, then its
        {ccl} (twoway expands macros when it reads the option and SMCL when
        it draws), and refuses an expansion past 4,000 characters."""
        ado = _read("dash.ado")
        at = ado.index('_dash_at_globals(st_local("gv"))')
        assert at < ado.index('_dash_gt_ccl(st_local("_gtg"))')
        assert "(): expanded text is too long" in ado[at:at + 800]


class TestTheHelp:

    def test_the_help_says_every_text_option_expands(self):
        src = _read("dash.sthlp")
        para = src[src.index("{ul:Text in graphs.}"):
                   src.index("{ul:Tooltips.}")]
        assert "before its quotes are read" in para
        assert "is drawn as written" in para
        assert "expanded text is too long" in para


class TestTheQuoteRefusals:

    def test_the_help_names_the_refusals_and_the_col_difference(self):
        """A global holding a double quote in text(), ttext() or a tick
        label is refused in twoway's words (test_wp31_truth.cscript
        U42-08); {col #:t}'s repeat is a documented, measured difference
        (smcl_more_truth.json col.colon)."""
        src = _read("dash.sthlp")
        para = src[src.index("{ul:Text in graphs.}"):
                   src.index("{ul:Tooltips.}")]
        assert "invalid point" in para
        assert "invalid label specifier" in para
        assert "{cmd:{c -(}col }{it:#}{cmd::}{it:text}{cmd:{c )-}}" in para
        with open(os.path.join(_HERE, "fixtures", "smcl_more_truth.json"),
                  encoding="utf-8") as fh:
            assert json.load(fh)["col.colon"]["texts"] == ["Qxxx"]
