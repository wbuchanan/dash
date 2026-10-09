"""cert_truth.py: twoway's answers for the certification scripts, recorded
once and replayed (WP-30 test performance, B2).

test_twoway_option_parity.cscript, test_parser.cscript and
test_help_claims_6.cscript ask twoway, before each dash command, what it
does with the same command.  cert_truth.py keeps those answers in
test/fixtures/<name>_truth.json; DASH_CERT_REMEASURE says whether a run
reads them (replay), asks twoway and holds it to them (1, remeasure), or
asks twoway and writes them (record, for the extractor).  These tests hold
the module to that contract with a stand-in for Stata's sfi: a question
the fixture cannot answer, an answer twoway no longer gives, and a fixture
answer nothing asked for each fail the run; a recording with two answers
to one question writes nothing; and every value crosses by local name,
never as code.
"""
import json
import os
import sys
import types

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import cert_truth as ct  # noqa: E402


class _Sfi:
    """Stata's sfi as cert_truth.py uses it: the current program's locals,
    one dataset in memory, and the system missing value."""

    MISS = 8.98846567431158e307

    def __init__(self):
        self.locals = {}
        self.names = []
        self.rows = []
        sfi = types.ModuleType("sfi")
        me = self

        class Macro:
            @staticmethod
            def getLocal(name):
                return me.locals.get(name, "")

            @staticmethod
            def setLocal(name, value):
                me.locals[name] = value

        class Data:
            @staticmethod
            def getVarCount():
                return len(me.names)

            @staticmethod
            def getVarName(j):
                return me.names[j]

            @staticmethod
            def get(var, obs, selectvar, missingval=8.98846567431158e307):
                assert var is None and obs is None and selectvar is None
                return [[missingval if x == _Sfi.MISS else x for x in r]
                        for r in me.rows]

            @staticmethod
            def setObsTotal(n):
                assert not me.names and not me.rows, "memory was not clear"
                me.rows = [[] for _ in range(n)]

            @staticmethod
            def addVarDouble(name):
                me.names.append(name)
                for r in me.rows:
                    r.append(_Sfi.MISS)

            @staticmethod
            def store(var, obs, val):
                assert var is None and obs is None
                assert len(val) == len(me.rows)
                me.rows = [list(r) for r in val]

        class Missing:
            @staticmethod
            def getValue():
                return _Sfi.MISS

        sfi.Macro, sfi.Data, sfi.Missing = Macro, Data, Missing
        self.module = sfi


@pytest.fixture
def sfi(monkeypatch):
    s = _Sfi()
    monkeypatch.setitem(sys.modules, "sfi", s.module)
    return s


def _testdir(tmp_path, name="demo", answers=None, meta=None):
    """A test/ folder holding fixtures/<name>_truth.json."""
    (tmp_path / "fixtures").mkdir(exist_ok=True)
    if answers is not None:
        doc = {"_meta": meta or {"stata_version": "19.5"},
               "answers": answers}
        (tmp_path / "fixtures" / (name + "_truth.json")).write_text(
            json.dumps(doc), encoding="utf-8")
    return str(tmp_path)


#: A Stata text log as `log using' (not quietly) writes it, its path
#: wrapped at the column.
_LOG = (
    "-------------------------------------------------------------------\n"
    "      name:  _ztplog\n"
    "       log:  /private/tmp/a/very/long/folder/name/that/wraps/at/the/c\n"
    "> olumn/x.log\n"
    "  log type:  text\n"
    " opened on:   7 Oct 2026, 08:21:03\n"
    "\n"
    "option nosuch not allowed\n"
    "(note: named style zz not found)\n"
    "\n"
    "      name:  _ztplog\n"
    "       log:  /private/tmp/a/very/long/folder/name/that/wraps/at/the/c\n"
    "> olumn/x.log\n"
    "  log type:  text\n"
    " closed on:   7 Oct 2026, 08:21:04\n"
    "-------------------------------------------------------------------\n")


class TestTheMode:

    @pytest.mark.parametrize("value,mode", [
        (None, "replay"), ("", "replay"), ("  ", "replay"), ("1", "remeasure"),
        (" 1 ", "remeasure"), ("record", "record")])
    def test_each_value_names_its_mode(self, value, mode):
        assert ct.mode_of(value) == mode

    @pytest.mark.parametrize("value", ["0", "yes", "Record", "2", "true"])
    def test_any_other_value_is_refused(self, value):
        with pytest.raises(ValueError, match="DASH_CERT_REMEASURE"):
            ct.mode_of(value)

    def test_the_fixture_name(self):
        assert ct.fixture_name("help_claims_6") == "help_claims_6_truth.json"
        for bad in ("", "../x", "a b", "a/b", None):
            with pytest.raises(ValueError):
                ct.fixture_name(bad)

    def test_an_answer_is_compared_as_json_reads_it(self):
        assert ct.canon((1, "a", {2: 3})) == [1, "a", {"2": 3}]


class TestTheKey:

    def test_a_key_is_the_kind_and_the_command(self):
        assert ct.make_key("rc", "TP-01|twoway x") == "rc|TP-01|twoway x"

    def test_a_long_command_keeps_its_head_and_a_digest(self):
        import hashlib
        cmd = "TP-14e|twoway scatter mpg weight," + " mcolor(blue)" * 10000
        key = ct.make_key("rc", cmd)
        whole = "rc|" + cmd
        assert len(key) < 320
        assert key.startswith(whole[:ct.KEY_HEAD])
        assert key.endswith("[%d characters, sha256 %s]" % (
            len(whole), hashlib.sha256(whole.encode("utf-8")).hexdigest()))
        # One character more is another key.
        assert ct.make_key("rc", cmd + " ") != key
        # At the limit a key is kept whole.
        at = "x" * (ct.KEY_MAX - 3)
        assert ct.make_key("rc", at) == "rc|" + at

    def test_put_and_get_agree_on_a_long_key(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        cmd = "twoway lfit mpg weight," + " atobs" * 10000
        t = ct.Truth("demo", str(tmp_path), "record", str(out))
        t.put("rc", cmd, 1003)
        assert t.close() == []
        answers = json.loads((out / "demo.json").read_text())
        d = _testdir(tmp_path, answers=answers)
        assert ct.Truth("demo", d, "replay").get("rc", cmd) == 1003


class TestTheLogBody:

    def test_the_header_and_footer_go(self):
        assert ct.log_body(_LOG) == ("option nosuch not allowed\n"
                                     "(note: named style zz not found)\n")

    def test_a_quiet_log_is_kept_whole_but_its_blank_ends(self):
        text = "\n\nvariable nosuch not found\n> continued\n\n"
        assert ct.log_body(text) == "variable nosuch not found\n> continued\n"

    def test_carriage_returns_and_an_empty_log(self):
        assert ct.log_body("a\r\nb\r\n") == "a\nb\n"
        assert ct.log_body("") == ""
        assert ct.log_body("\n\n") == ""

    def test_two_runs_of_one_command_give_one_body(self):
        other = _LOG.replace("08:21:03", "09:00:00").replace("/x.log", "/y.log")
        assert ct.log_body(other) == ct.log_body(_LOG)


class TestReplay:

    def test_answers_come_from_the_fixture(self, tmp_path):
        d = _testdir(tmp_path, answers={"rc|c|twoway x": 198})
        t = ct.Truth("demo", d, "replay")
        assert not t.live()
        assert t.get("rc", "c|twoway x") == 198
        assert t.close() == []

    def test_a_question_with_no_answer_fails_the_run_and_is_said_at_once(
            self, tmp_path, capsys):
        d = _testdir(tmp_path, answers={})
        t = ct.Truth("demo", d, "replay")
        assert t.get("rc", "c|twoway y") is None
        assert t.get("rc", "c|twoway y") is None
        said = capsys.readouterr().out
        assert said.count("TRUTH FAIL demo_truth.json holds no answer") == 1
        assert ct.EXTRACTOR in said
        probs = t.close()
        assert len(probs) == 1 and "holds no answer to rc|c|twoway y" in probs[0]

    def test_an_answer_nothing_asked_for_is_no_problem(self, tmp_path):
        d = _testdir(tmp_path, answers={"rc|c|twoway x": 0})
        assert ct.Truth("demo", d, "replay").close() == []

    def test_a_missing_fixture_stops_the_run(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ct.Truth("demo", _testdir(tmp_path), "replay")


class TestRemeasure:

    def _truth(self, tmp_path, answers):
        return ct.Truth("demo", _testdir(tmp_path, answers=answers),
                        "remeasure")

    def test_twoway_answering_as_the_fixture_does_passes(self, tmp_path):
        t = self._truth(tmp_path, {"rc|a|twoway x": 198,
                                   "log|a|twoway y": {"rc": 0, "log": "w\n"}})
        assert t.live()
        t.put("rc", "a|twoway x", 198)
        t.put("log", "a|twoway y", {"rc": 0, "log": "w\n"})
        assert t.close() == []

    def test_a_different_answer_is_stale(self, tmp_path):
        t = self._truth(tmp_path, {"rc|a|twoway x": 198})
        t.put("rc", "a|twoway x", 0)
        probs = t.close()
        assert probs == ["twoway's answer to rc|a|twoway x is no longer the "
                         "fixture's"]

    def test_a_question_the_fixture_lacks_fails(self, tmp_path):
        t = self._truth(tmp_path, {})
        t.put("rc", "a|twoway new", 0)
        assert ["demo_truth.json holds no answer to rc|a|twoway new"] == \
            t.close()

    def test_an_answer_nothing_asked_for_fails(self, tmp_path):
        t = self._truth(tmp_path, {"rc|a|twoway gone": 0})
        assert t.close() == ["demo_truth.json answers rc|a|twoway gone, "
                             "which this run never asked"]

    def test_floats_and_text_must_match_exactly(self, tmp_path):
        t = self._truth(tmp_path, {"val:m|a|q": "0.1", "data|a|q":
                                   {"names": ["c1"], "rows": [[0.1]]},
                                   "data|b|q": {"names": ["c1"],
                                                "rows": [[0.1]]}})
        t.put("val:m", "a|q", "0.10")
        t.put("data", "a|q", {"names": ["c1"],
                              "rows": [[0.30000000000000004 - 0.2]]})
        t.put("data", "b|q", {"names": ["c1"], "rows": [[0.1]]})
        probs = t.close()
        assert len(probs) == 2, probs
        assert "val:m|a|q" in probs[0] and "data|a|q" in probs[1]


class TestRecord:

    def test_record_needs_an_existing_folder(self, tmp_path):
        for out in ("", str(tmp_path / "absent")):
            with pytest.raises(ValueError, match="DASH_CERT_TRUTH_OUT"):
                ct.Truth("demo", str(tmp_path), "record", out)

    def test_the_answers_are_written_for_the_extractor(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        t = ct.Truth("demo", str(tmp_path), "record", str(out))
        t.put("rc", "a|twoway x", 198)
        t.put("rc", "a|twoway x", 198)
        t.put("val:n", "b|twoway x", "3")
        assert t.close() == []
        got = json.loads((out / "demo.json").read_text())
        assert got == {"rc|a|twoway x": 198, "val:n|b|twoway x": "3"}

    def test_two_answers_to_one_question_write_nothing(self, tmp_path):
        out = tmp_path / "out"
        out.mkdir()
        t = ct.Truth("demo", str(tmp_path), "record", str(out))
        t.put("rc", "a|twoway x", 198)
        t.put("rc", "a|twoway x", 0)
        t.put("rc", "a|twoway x", 1)
        assert t.close() == ["twoway answered rc|a|twoway x twice, "
                             "differently"]
        assert not (out / "demo.json").exists()


class TestTheStataSide:
    """The calls cert_truth.do and the scripts make, each argument the NAME
    of a local, through the stand-in sfi."""

    def _open(self, tmp_path, mode, answers=None):
        out = tmp_path / "out"
        out.mkdir(exist_ok=True)
        env = {"replay": "", "remeasure": "1", "record": "record"}[mode]
        d = _testdir(tmp_path, answers=answers if answers is not None
                     else ({} if mode != "record" else None))
        assert ct.open_truth("demo", d, env, str(out)) == mode
        return out

    def test_without_open_nothing_answers(self, monkeypatch):
        monkeypatch.setitem(ct._state, "truth", None)
        with pytest.raises(RuntimeError, match="cert_truth_init"):
            ct.current()

    def test_flag(self, tmp_path, sfi):
        self._open(tmp_path, "replay")
        ct.flag("l")
        assert sfi.locals["l"] == "0"
        self._open(tmp_path, "record")
        ct.flag("l")
        assert sfi.locals["l"] == "1"

    def test_rc_round_trip_with_the_context(self, tmp_path, sfi):
        out = self._open(tmp_path, "record")
        ct.ctx("TP-01")
        sfi.locals.update(cmd="twoway scatter mpg weight, nosuch", rc="198")
        ct.rc_put("cmd", "rc")
        ct.ctx("TP-02")
        sfi.locals.update(rc="0")
        ct.rc_put("cmd", "rc")
        ct.finish("n")
        assert sfi.locals["n"] == "0"
        answers = json.loads((out / "demo.json").read_text())
        assert answers == {
            "rc|TP-01|twoway scatter mpg weight, nosuch": 198,
            "rc|TP-02|twoway scatter mpg weight, nosuch": 0}
        self._open(tmp_path, "replay", answers)
        ct.ctx("TP-01")
        ct.rc_get("cmd", "got")
        assert sfi.locals["got"] == "198"
        ct.ctx("TP-03")
        ct.rc_get("cmd", "got")
        assert sfi.locals["got"] == ""

    def test_a_hostile_command_is_a_key_like_any_other(self, tmp_path, sfi):
        hostile = ("twoway scatter mpg weight, title(`\"{bf:B} $S_ADO "
                   "`c(pwd)' _dup(3) \"INJ\"'\") \x01")
        out = self._open(tmp_path, "record")
        sfi.locals.update(cmd=hostile, rc="198")
        ct.rc_put("cmd", "rc")
        ct.finish("n")
        answers = json.loads((out / "demo.json").read_text())
        assert answers == {"rc||" + hostile: 198}
        self._open(tmp_path, "replay", answers)
        ct.rc_get("cmd", "got")
        assert sfi.locals["got"] == "198"

    def test_log_round_trip(self, tmp_path, sfi):
        log = tmp_path / "x.log"
        log.write_text(_LOG)
        out = self._open(tmp_path, "record")
        sfi.locals.update(cmd="twoway scatter mpg weight, nosuch", rc="198",
                          path=str(log))
        ct.log_put("cmd", "rc", "path")
        ct.finish("n")
        answers = json.loads((out / "demo.json").read_text())
        self._open(tmp_path, "replay", answers)
        back = tmp_path / "back.log"
        sfi.locals.update(path=str(back))
        ct.log_get("cmd", "path", "rc2")
        assert sfi.locals["rc2"] == "198"
        assert back.read_text() == ct.log_body(_LOG)
        sfi.locals.update(cmd="twoway other")
        ct.log_get("cmd", "path", "rc2")
        assert sfi.locals["rc2"] == "" and back.read_text() == ""

    def test_value_round_trip(self, tmp_path, sfi):
        out = self._open(tmp_path, "record")
        sfi.locals.update(cmd="twoway lowess zb weight", v=".4459459459459459")
        ct.val_put("mean", "cmd", "v")
        ct.finish("n")
        answers = json.loads((out / "demo.json").read_text())
        self._open(tmp_path, "replay", answers)
        ct.val_get("mean", "cmd", "w")
        assert sfi.locals["w"] == ".4459459459459459"
        ct.val_get("sd", "cmd", "w")
        assert sfi.locals["w"] == ""

    def test_data_round_trip(self, tmp_path, sfi):
        out = self._open(tmp_path, "record")
        sfi.names = ["c1", "c2"]
        sfi.rows = [[30.81702202950237, 1760], [_Sfi.MISS, 1800]]
        sfi.locals.update(cmd="serset 0: twoway lowess mpg weight")
        ct.data_put("cmd")
        ct.finish("n")
        answers = json.loads((out / "demo.json").read_text())
        key = "data||serset 0: twoway lowess mpg weight"
        assert answers[key] == {"names": ["c1", "c2"],
                                "rows": [[30.81702202950237, 1760],
                                         [None, 1800]]}
        self._open(tmp_path, "replay", answers)
        sfi.names, sfi.rows = [], []
        ct.data_get("cmd", "ok")
        assert sfi.locals["ok"] == "1"
        assert sfi.names == ["c1", "c2"]
        assert sfi.rows == [[30.81702202950237, 1760], [_Sfi.MISS, 1800]]
        sfi.names, sfi.rows = [], []
        sfi.locals.update(cmd="serset 0: twoway none")
        ct.data_get("cmd", "ok")
        assert sfi.locals["ok"] == "" and sfi.names == []

    def test_finish_counts_and_says_the_problems(self, tmp_path, sfi,
                                                 capsys):
        self._open(tmp_path, "remeasure", {"rc||twoway x": 0})
        sfi.locals.update(cmd="twoway x", rc="198")
        ct.rc_put("cmd", "rc")
        ct.finish("n")
        assert sfi.locals["n"] == "1"
        said = capsys.readouterr().out
        assert "TRUTH FAIL twoway's answer to rc||twoway x" in said
        assert "TRUTH FAIL 1 problem(s) with demo_truth.json" in said
        assert ct.EXTRACTOR in said


class TestTheFixtures:
    """The committed fixtures: each names its script and Stata, and every
    answer is a kind this module writes."""

    @pytest.mark.parametrize("name,script", [
        ("twoway_option_parity", "test_twoway_option_parity.cscript"),
        ("parser_twoway", "test_parser.cscript"),
        ("help_claims_6", "test_help_claims_6.cscript")])
    def test_each_fixture_is_stamped_and_well_formed(self, name, script):
        path = os.path.join(_HERE, "fixtures", ct.fixture_name(name))
        with open(path, encoding="utf-8") as fh:
            doc = json.load(fh)
        meta = doc["_meta"]
        for k in ("stata_version", "born_date", "dash_commit", "extracted"):
            assert meta.get(k), k
        assert meta["script"] == script
        answers = doc["answers"]
        assert meta["answers"] == len(answers) > 0
        for key, value in answers.items():
            kind = key.split("|", 1)[0]
            assert kind in ("rc", "log", "data") or kind.startswith("val:")
            if kind == "rc":
                assert isinstance(value, int)
            if kind == "log":
                assert set(value) == {"rc", "log"}
            if kind == "data":
                assert set(value) == {"names", "rows"}
        with open(os.path.join(_HERE, script), encoding="utf-8") as fh:
            src = fh.read()
        assert "cert_truth_init %s\n" % name in src
        assert ct.fixture_name(name) in src


#: The one line that binds the truth module in a Stata program or script.
_BIND = 'python: _dct = __import__("sys").modules["_dash_cert_truth"]'


def _truth_users():
    out = []
    for f in sorted(os.listdir(_HERE)):
        if f.endswith((".cscript", ".do")):
            with open(os.path.join(_HERE, f), encoding="utf-8",
                      errors="replace") as fh:
                text = fh.read()
            if "_dct." in text:
                out.append(f)
    return out


class TestTheModuleIsBoundWhereItIsUsed:
    """Python names a `python:' line makes inside a Stata program end with
    the program (measured 07oct2026: cert_truth_init bound _dct, and the
    next program's `_dct.flag' was a NameError, r(7102)).  So every program
    that calls the module binds it before its first call, and a script's
    own lines bind it after cert_truth_init and before theirs."""

    def test_the_users_are_found(self):
        assert "cert_truth.do" in _truth_users()
        assert "test_help_claims_6.cscript" in _truth_users()

    @pytest.mark.parametrize("name", _truth_users())
    def test_each_use_follows_a_binding_in_its_scope(self, name):
        with open(os.path.join(_HERE, name), encoding="utf-8",
                  errors="replace") as fh:
            lines = fh.read().splitlines()
        bad = []
        in_prog = False
        bound_prog = False
        bound_top = False
        for i, raw in enumerate(lines, 1):
            line = raw.split("//", 1)[0].strip()
            if line.startswith("*"):
                continue
            if line.startswith("program define ") or \
                    line.startswith("program "):
                if not line.startswith("program drop"):
                    in_prog, bound_prog = True, False
                    continue
            if in_prog and line == "end":
                in_prog = False
                continue
            # The binding, or (cert_truth_init) the line that makes it.
            if line.endswith(_BIND) or line.startswith("python: _dct = "):
                if in_prog:
                    bound_prog = True
                else:
                    bound_top = True
                continue
            if "_dct." in line and line.lstrip().startswith(
                    ("python:", "else python:", "if ")):
                if not (bound_prog if in_prog else bound_top):
                    bad.append("%s:%d: %s" % (name, i, line[:80]))
        assert not bad, bad
