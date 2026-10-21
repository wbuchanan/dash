"""The known-differences rule (WP-33 section 33-10, D-33-10.a; TR-11).

test/known_differences.py is the one rule every truth table of WP-33 uses
for its list of known differences from twoway: a ``<NAME>_KNOWN`` dict
``{key: "<GAPS4 lead id>[ (documented|residual)]"}`` beside a
``<NAME>_DELIBERATE`` dict of differences a ruling keeps.  A check built on
``known_problems`` fails on (1) an unlisted difference, (2) a listed key
that now agrees with twoway, (3) a row whose item is no longer live and
(4) a listed key the comparison no longer produces.  Each test builds its
own small GAPS4.md text or test folder in ``tmp_path``.
"""
import os
import sys
import textwrap

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import known_differences as kd  # noqa: E402

_GAPS4 = textwrap.dedent("""\
    # GAPS4

    - **AA-1 Tracked:** Open (WP-35 section 35-05).
    - **BB-2 Tracked:** Closed in WP-35, BUGS.md "b", commit pending.
    - **CC-3 Tracked:** Documented in WP-40, BUGS.md "c", commit abc1234.
    - **DD-4 Tracked:** Partly closed in WP-43 (section 43-01, commit pending): x; open: y (BUGS.md "d").
    - **syn:EE-5 Tracked:** Open (WP-33 section 33-10).
    """)


def _gaps4(tmp_path):
    p = tmp_path / "GAPS4.md"
    p.write_text(_GAPS4, encoding="utf-8")
    return str(p)


class TestKnownProblems:
    def test_an_unlisted_difference(self, tmp_path):
        probs = kd.known_problems({"a": "twoway r(198) / dash r(0)"}, {},
                                  "t", path=_gaps4(tmp_path))
        assert len(probs) == 1
        assert "a" in probs[0] and "not listed" in probs[0]

    def test_a_listed_key_that_agrees(self, tmp_path):
        probs = kd.known_problems({"a": None}, {"a": "AA-1"}, "t",
                                  path=_gaps4(tmp_path))
        assert probs == ["t: a now agrees with twoway: delete its row: "
                         "AA-1 fixed it"]

    def test_a_closed_id(self, tmp_path):
        probs = kd.known_problems({"a": "differs"}, {"a": "BB-2"}, "t",
                                  path=_gaps4(tmp_path))
        assert len(probs) == 1
        assert "BB-2" in probs[0] and "should have gone" in probs[0]

    def test_a_vanished_key(self, tmp_path):
        probs = kd.known_problems({}, {"gone": "AA-1"}, "t",
                                  path=_gaps4(tmp_path))
        assert len(probs) == 1
        assert "gone" in probs[0] and "no longer produces" in probs[0]

    def test_all_clean(self, tmp_path):
        results = {"a": None, "b": "differs", "c": "differs",
                   "d": "differs", "e": "differs"}
        known = {"b": "AA-1", "c": "CC-3 (documented)",
                 "d": "DD-4 (residual)", "e": "syn:EE-5"}
        assert kd.known_problems(results, known, "t",
                                 path=_gaps4(tmp_path)) == []

    def test_a_documented_row_survives_its_closure(self, tmp_path):
        g = _gaps4(tmp_path)
        assert kd.known_problems({"c": "differs"},
                                 {"c": "CC-3 (documented)"}, "t",
                                 path=g) == []
        # A documented row of an item that closed Closed is dead.
        probs = kd.known_problems({"c": "differs"},
                                  {"c": "BB-2 (documented)"}, "t", path=g)
        assert len(probs) == 1 and "BB-2" in probs[0]

    def test_a_residual_row_survives_a_partly_closure(self, tmp_path):
        g = _gaps4(tmp_path)
        assert kd.known_problems({"d": "differs"},
                                 {"d": "DD-4 (residual)"}, "t",
                                 path=g) == []
        # A residual row needs the item open or Partly closed, not
        # Documented.
        probs = kd.known_problems({"d": "differs"},
                                  {"d": "CC-3 (residual)"}, "t", path=g)
        assert len(probs) == 1 and "CC-3" in probs[0]

    def test_a_deliberate_key_is_ignored(self, tmp_path):
        g = _gaps4(tmp_path)
        deliberate = {"hover": "P4-7: hover() kept"}
        assert kd.known_problems({"hover": "differs"}, {}, "t", path=g,
                                 deliberate=deliberate) == []
        # The same key in both dicts fails rule 4.
        probs = kd.known_problems({"hover": "differs"}, {"hover": "AA-1"},
                                  "t", path=g, deliberate=deliberate)
        assert len(probs) == 1 and "no longer produces" in probs[0]

    def test_dead_rows_is_rule_3_alone(self, tmp_path):
        g = _gaps4(tmp_path)
        known = {"a": "AA-1", "b": "BB-2", "c": "CC-3 (documented)",
                 "x": "not a row (form)"}
        dead = kd.dead_rows(known, "t", path=g)
        assert len(dead) == 2
        assert any("b:" in s and "BB-2" in s for s in dead)
        assert any("x:" in s for s in dead)
        # The same strings known_problems gives for rule 3.
        probs = kd.known_problems({"b": "differs"}, {"b": "BB-2"}, "t",
                                  path=g)
        assert probs == kd.dead_rows({"b": "BB-2"}, "t", path=g)


class TestOpenIds:
    def test_reads_only_the_open_form(self, tmp_path):
        assert kd.gaps4_open_ids(_gaps4(tmp_path)) == frozenset(
            {"AA-1", "syn:EE-5"})

    def test_reads_the_documented_form(self, tmp_path):
        assert kd.gaps4_documented_ids(_gaps4(tmp_path)) == frozenset(
            {"CC-3"})

    def test_reads_the_partly_form(self, tmp_path):
        assert kd.gaps4_partly_ids(_gaps4(tmp_path)) == frozenset({"DD-4"})


class TestRowsFor:
    def _tables(self, tmp_path):
        (tmp_path / "one_known.py").write_text(
            'X_KNOWN = {\n    "a": "AA-1",\n    "b": "BB-2",\n}\n',
            encoding="utf-8")
        (tmp_path / "test_two.py").write_text(
            'Y_KNOWN = {\n    "c": "AA-1 (documented)",\n}\n'
            'NOT_A_TABLE = {"d": "AA-1"}\n'
            'def test_every_known_difference_is_open():\n'
            '    assert True\n', encoding="utf-8")
        (tmp_path / "test_three.py").write_text(
            'class TestX:\n'
            '    def test_every_known_difference_is_open(self):\n'
            '        assert True\n', encoding="utf-8")
        return str(tmp_path)

    def test_finds_rows_in_every_table(self, tmp_path):
        d = self._tables(tmp_path)
        assert kd.rows_for("AA-1", test_dir=d) == [
            'one_known.py:2: a: AA-1']
        assert kd.rows_for("AA-1", test_dir=d, every_form=True) == [
            'one_known.py:2: a: AA-1',
            'test_two.py:2: c: AA-1 (documented)']

    def test_names_the_hygiene_files(self, tmp_path):
        d = self._tables(tmp_path)
        assert kd.hygiene_files(test_dir=d) == [
            os.path.join(d, "test_three.py"),
            os.path.join(d, "test_two.py")]
