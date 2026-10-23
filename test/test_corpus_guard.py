"""
test_corpus_guard.py -- the certification suite's twenty-example corpus guard
(WP-33 33-09).

scripts/corpus/guard.py chooses about twenty help-file examples, one per
common plot type (D-33-09.b), wraps 33-03's and 33-04's do-file texts in a
guard.do that leaves the Stata session as it found it (D-33-09.d), measures
each example through 33-04's exporter and 33-05's judge, and compares the
rows with test/fixtures/corpus_guard_truth.json (D-33-09.c).  None of these
tests runs Stata or Chrome; block S09 of test_wp33_truth.cscript does.
"""
import json
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(_ROOT, "test")
sys.path.insert(0, _ROOT)

from scripts.corpus import dash_run, guard, twoway_run  # noqa: E402

_FIXTURE = os.path.join(_HERE, "fixtures", "corpus_guard_truth.json")
_SCRIPT = "scripts/extract_corpus_guard_truth.do"
_RECORD_KEYS = {"id", "source", "sources", "file", "line", "entry", "finding", "setup",
                "cmd", "dash_cmd", "plottype", "datasets", "stripped", "signature",
                "duplicates"}


def _rec(i, plottype="scatter", cmd=None, setup=("sysuse auto, clear",),
         source="help", ds=("auto",), sig=None):
    # D58: a record's command is written twoway <rest>, its twin dash <rest>.
    cmd = cmd or "twoway %s mpg weight" % plottype
    return {"id": i, "source": source, "sources": [source], "file": "base/x.sthlp",
            "line": 1, "entry": None, "finding": None, "setup": list(setup),
            "cmd": cmd, "dash_cmd": "dash " + cmd[len("twoway "):], "plottype": plottype,
            "datasets": list(ds), "stripped": [],
            "signature": sig or "%s|" % plottype, "duplicates": []}


def _jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")


def _row(verdict="Close", checks=("margins",), rc_tw=0, rc_da=0, summary="margins"):
    return {"rc_twoway": rc_tw, "first_twoway": None, "rc_dash": rc_da,
            "first_dash": None, "verdict": verdict, "checks": list(checks),
            "summary": summary, "ledger": [], "ssim": 0.8, "size_matched": True}


def _run(tmp_path, recs, tw_rc=None, ssim=None):
    run = tmp_path / "run"
    run.mkdir()
    _jsonl(run / "examples.jsonl", recs)
    _jsonl(run / "twoway.jsonl", [{"id": r["id"], "rc": (tw_rc or {}).get(r["id"], 0)}
                                  for r in recs])
    _jsonl(run / "verdicts.jsonl", [{"id": r["id"], "ssim": (ssim or {}).get(r["id"], 0.5)}
                                    for r in recs])
    return str(run)


class TestReadList:

    def test_ignores_comments_and_blanks(self, tmp_path):
        p = tmp_path / "g.txt"
        p.write_text("# header\n\nhelp-a-1  # scatter: scatter y x\n  \n"
                     "help-b-2\n# help-c-3\n", encoding="utf-8")
        assert guard.read_list(str(p)) == ["help-a-1", "help-b-2"]


class TestCandidates:

    def test_help_shipped_setup_words_only(self):
        recs = [_rec("a"),
                _rec("b", source="gpdf"),
                _rec("c", setup=("webuse lbw, clear",), ds=("lbw",)),
                _rec("d", setup=("sysuse auto, clear", "predict r")),
                _rec("e", setup=("sysuse auto, clear", "gen z = 1", "replace z = 2",
                                 "label variable z \"Z\"", "sort z", "tsset z",
                                 "generate w = 2")),
                _rec("f", setup=("sysuse nlsw88, clear",), ds=("nlsw88",)),
                _rec("g", setup=())]
        got = [r["id"] for r in guard.candidates(recs, {"auto"})]
        assert got == ["a", "e", "g"]


class TestSelect:

    def test_one_per_type_smallest_id_away_from_t_same(self, tmp_path):
        recs = [_rec("help-a-1"), _rec("help-a-0"), _rec("help-b-1", "line"),
                _rec("help-b-0", "line"), _rec("help-c-1", "bar"),
                _rec("help-d-1", "scatter", cmd="scatter y x || lfit y x",
                     sig="scatter|")]
        run = _run(tmp_path, recs, tw_rc={"help-a-0": 198},
                   ssim={"help-b-0": 0.895, "help-b-1": 0.85})
        ids, skipped = guard.select(run, {"T_same": 0.9}, shipped={"auto"})
        # help-a-0: twoway refused; help-b-0: 0.005 from T_same; lfit only
        # as a later layer of help-d-1.
        assert ids == ["help-a-1", "help-b-1", "help-c-1", "help-d-1"]
        assert "contour" in skipped and "colorvar" in skipped
        assert "scatter" not in skipped and "lfit" not in skipped
        ids, _ = guard.select(run, {"T_same": None}, shipped={"auto"})
        assert "help-b-0" in ids and "help-b-1" not in ids
        ids, skipped = guard.select(run, {"T_same": None}, shipped=set())
        assert ids == [] and "scatter" in skipped


class TestRecordsFromRun:

    def test_a_missing_id_is_refused(self, tmp_path):
        run = tmp_path / "run"
        run.mkdir()
        _jsonl(run / "examples.jsonl", [_rec("a")])
        with pytest.raises(ValueError) as e:
            guard.records_from_run(str(run), ["a", "zz", "yy"])
        assert "zz" in str(e.value) and "yy" in str(e.value)

    def test_reuses_the_fixtures_records(self, tmp_path):
        run = tmp_path / "run"
        run.mkdir()
        _jsonl(run / "examples.jsonl", [_rec("a", cmd="scatter run x"), _rec("b")])
        fixture = {"examples": {"a": {"record": _rec("a", cmd="scatter frozen x")}}}
        got = guard.records_from_run(str(run), ["a", "b"], fixture)
        assert got["a"]["cmd"] == "scatter frozen x"
        assert got["b"]["id"] == "b"
        got = guard.records_from_run(None, ["a"], fixture)
        assert got["a"]["cmd"] == "scatter frozen x"
        got = guard.records_from_run(str(tmp_path / "absent"), ["a"], fixture)
        assert list(got) == ["a"]


class TestWriteExamples:

    def test_sorted_jsonl(self, tmp_path):
        path = guard.write_examples({"b": _rec("b"), "a": _rec("a")}, str(tmp_path / "r"))
        assert path == str(tmp_path / "r" / "examples.jsonl")
        with open(path, encoding="utf-8") as fh:
            lines = [json.loads(ln) for ln in fh]
        assert [r["id"] for r in lines] == ["a", "b"]
        assert lines[0] == _rec("a")


class TestGuardDo:

    def _make(self, tmp_path):
        run, cache, repo = str(tmp_path / "run"), str(tmp_path / "cache"), str(tmp_path / "repo")
        ex = [_rec("a"), _rec("b", "line", setup=("webuse lbw, clear",), ds=("lbw",))]
        path = guard.guard_do(ex, run, cache, repo)
        return ex, run, cache, repo, path

    def test_wraps_the_runners_do_files(self, tmp_path):
        ex, run, cache, repo, path = self._make(tmp_path)
        assert path == os.path.join(run, "guard.do")
        with open(os.path.join(run, "tw", "guard_tw.do"), encoding="utf-8") as fh:
            assert fh.read() == twoway_run.do_text(ex, run + "/tw/svg", cache)
        with open(os.path.join(run, "dash", "guard_dash.do"), encoding="utf-8") as fh:
            assert fh.read() == dash_run.do_text(ex, run + "/dash", cache, repo)
        assert os.path.isdir(os.path.join(run, "tw", "svg"))
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for s in ("local _g_scheme \"\x60c(scheme)'\"", "local _g_ls = c(linesize)",
                  "local _g_ado \x60\"$S_ADO\"'", "local _g_nb \x60\"$dash_nobrowser\"'",
                  "preserve", "restore", "set scheme \x60_g_scheme'",
                  "set linesize \x60_g_ls'", "global S_ADO \x60\"\x60_g_ado'\"'",
                  "global dash_nobrowser \x60\"\x60_g_nb'\"'",
                  "name(s09tw)", "log close s09tw", "name(s09da)", "log close s09da",
                  "capture serset clear", "dash clear", "capture graph drop _all"):
            assert s in text, s
        assert text.index("preserve") < text.index("set scheme stcolor") \
            < text.index("s09tw") < text.index("restore") < text.index("set scheme \x60_g_scheme'")
        assert "permanently" not in text

    def test_no_absolute_path_but_the_run_folder_and_repo(self, tmp_path):
        ex, run, cache, repo, path = self._make(tmp_path)
        allowed = (run, cache, repo)
        for name in ("guard.do", "tw/guard_tw.do", "dash/guard_dash.do"):
            with open(os.path.join(run, name), encoding="utf-8") as fh:
                text = fh.read()
            for m in re.finditer(r"(?<![\w.])/[^\s\"']+", text):
                assert m.group(0).startswith(allowed), (name, m.group(0))


class _Probe:
    opened = []

    def __init__(self, path, chrome=None, timeout=60, ready=None):
        _Probe.opened.append((path, ready))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestMeasure:

    def test_rows_from_canned_logs(self, tmp_path, monkeypatch):
        run = tmp_path / "run"
        (run / "tw" / "svg").mkdir(parents=True)
        (run / "dash").mkdir(parents=True)
        ex = [_rec("a"), _rec("b", "line")]
        (run / "tw" / "svg" / "a.svg").write_text(
            '<svg width="5in" height="4in"></svg>', encoding="utf-8")
        (run / "tw" / "svg" / "b.svg").write_text(
            '<svg width="6in" height="4in"></svg>', encoding="utf-8")
        log = ("##VERSION 19.5\n##BEGIN a\n##SETUP a 0\n##RC a 0\n##EXPORT a 0\n"
               "##BEGIN b\n##SETUP b 0\n##RC b 0\n##EXPORT b 0\n")
        (run / "tw" / "guard.log").write_text(log, encoding="utf-8")
        (run / "dash" / "guard.log").write_text(
            log.replace("##EXPORT a 0\n", "").replace("##EXPORT b 0\n", ""),
            encoding="utf-8")
        (run / "dash" / "a.html").write_text("<html></html>", encoding="utf-8")
        (run / "dash" / "b.html").write_text("<html></html>", encoding="utf-8")
        rules = tmp_path / "rules.json"
        rules.write_text('{"T_same": null}', encoding="utf-8")
        ledger = tmp_path / "ledger.json"
        ledger.write_text('{"rows": []}', encoding="utf-8")
        gaps4 = tmp_path / "GAPS4.md"
        gaps4.write_text("# none\n", encoding="utf-8")
        seen = {}

        def fake_export(pages, sizes, out_dir, probe=None):
            seen["sizes"] = sizes
            return {"a": {"svg": out_dir + "/a.svg", "view": out_dir + "/a.view.json",
                          "size_matched": False, "js_errors": [], "w": 480, "h": 384},
                    "b": {"error": "page failed at " + str(run)}}

        def fake_judge(example, tw, da, run_dir, rules, ledger, states, probe=None):
            seen.setdefault("da", {})[example["id"]] = da
            seen.setdefault("tw", {})[example["id"]] = tw
            return {"id": example["id"], "rc_twoway": tw["rc"], "first_twoway": None,
                    "rc_dash": da["rc"], "first_dash": None, "verdict": "Same",
                    "checks": [], "summary": "Same", "ledger": [], "ssim": None,
                    "size_matched": da.get("size_matched"), "colours": {}, "gallery": True}

        _Probe.opened = []
        monkeypatch.setattr(dash_run, "export_pages", fake_export)
        monkeypatch.setattr(dash_run, "CorpusProbe", _Probe)
        monkeypatch.setattr(guard.verdict, "judge", fake_judge)
        got = guard.measure(str(run), ex, str(rules), str(ledger), str(gaps4))
        assert seen["sizes"] == {"a": (480, 384), "b": (576, 384)}
        assert seen["tw"]["a"]["svg"] == "twoway/a.svg"
        assert seen["da"]["a"]["svg"] == "dash/a.svg"
        assert seen["da"]["a"]["view"] == "dash/a.view.json"
        assert seen["da"]["a"]["size_matched"] is False
        assert seen["da"]["b"]["svg"] is None
        assert seen["da"]["b"]["export_error"] == "page failed at <run>"
        assert _Probe.opened == [(str(run / "raster.html"),
                                  "document.readyState === 'complete'")]
        with open(run / "raster.html", encoding="utf-8") as fh:
            assert fh.read().startswith('<!doctype html><meta charset="utf-8"><title>raster')
        assert sorted(got) == ["a", "b"]
        assert set(got["a"]) == set(guard.MEASURED) and len(guard.MEASURED) == 10
        assert got["a"]["verdict"] == "Same" and got["a"]["size_matched"] is False


class TestCompare:

    def test_equal_rows_pass(self):
        want = {"a": dict(_row(), record=_rec("a")), "b": _row("Same", ())}
        got = {"a": _row(), "b": dict(_row("Same", ()), ssim=0.1, first_dash="x")}
        assert guard.compare(want, got) == []

    def test_a_worse_verdict_fails(self):
        got = guard.compare({"a": _row("Close")}, {"a": _row("Differs")})
        assert len(got) == 1
        assert got[0].startswith("a: verdict was Close now Differs: ")
        assert _SCRIPT in got[0] and "regression" in got[0]

    def test_an_improvement_fails_and_names_the_ledger_and_the_script(self):
        got = guard.compare({"a": _row("Close", ("margins", "text_size"))},
                            {"a": _row("Close", ("margins",))})
        assert len(got) == 1
        assert got[0].startswith("a improved from Close (margins, text_size) to Close (margins)")
        assert "scripts/corpus/ledger.tsv" in got[0] and "ledger.py" in got[0]
        assert _SCRIPT in got[0]
        got = guard.compare({"a": _row("Differs")}, {"a": _row("Same", ())})
        assert got[0].startswith("a improved from Differs (margins) to Same ()")

    def test_a_new_check_fails(self):
        got = guard.compare({"a": _row("Close", ("margins",))},
                            {"a": _row("Close", ("margins", "text_size"))})
        assert len(got) == 1 and got[0].startswith("a: checks was ")
        got = guard.compare({"a": _row(), "b": _row()}, {"b": _row()})
        assert len(got) == 1 and got[0].startswith("a: ") and _SCRIPT in got[0]

    def test_a_changed_rc_fails(self):
        got = guard.compare({"a": _row(rc_da=0)}, {"a": _row(rc_da=198)})
        assert got == [got[0]]
        assert got[0].startswith("a: rc_dash was 0 now 198: ")
        assert _SCRIPT in got[0]


class TestMain:

    def test_select_prints_the_lines_and_the_skipped_types(self, tmp_path, monkeypatch,
                                                            capsys):
        base = tmp_path / "stata" / "ado" / "base" / "a"
        base.mkdir(parents=True)
        (base / "auto.dta").write_bytes(b"")
        monkeypatch.setenv("DASH_STATA_DIR", str(tmp_path / "stata"))
        run = _run(tmp_path, [_rec("help-z-1", "line", cmd="line mpg weight, sort"),
                              _rec("help-a-1", "scatter")])
        assert guard.main(["--select", run]) == 0
        out = capsys.readouterr().out.splitlines()
        assert out[0] == "help-a-1  # scatter: twoway scatter mpg weight"  # D58: twoway first
        assert out[1] == "help-z-1  # line: line mpg weight, sort"
        assert out[2].startswith("skipped: ") and "contour" in out[2].split()
        assert len(out) == 3


def _fixture():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheList:

    def test_about_twenty_distinct_types(self):
        ids = guard.read_list()
        assert 18 <= len(ids) <= 24
        assert len(set(ids)) == len(ids)
        fx = _fixture()["examples"]
        assert set(ids) <= set(fx)
        assert len({fx[i]["record"]["plottype"] for i in ids}) >= 15


class TestTheFixture:

    def test_meta_and_rows(self):
        fx = _fixture()
        assert set(fx["_meta"]) == {"stata_version", "born_date", "dash_commit", "extracted",
                                    "source", "rules", "ledger"}
        assert fx["_meta"]["source"] == _SCRIPT
        with open(os.path.join(_ROOT, "GAPS4.md"), encoding="utf-8") as fh:
            gaps4 = fh.read()
        for i, row in fx["examples"].items():
            assert set(row["record"]) == _RECORD_KEYS, i
            assert row["record"]["id"] == i
            assert row["verdict"] in ("Same", "Close", "Differs"), i
            assert set(guard.MEASURED) <= set(row), i
            for gid in row["ledger"]:
                assert re.search(r"\b%s\b" % re.escape(gid), gaps4), (i, gid)
        text = json.dumps(fx)
        assert not re.search(r"/(Users|private|var|tmp|home|Applications)/", text)
