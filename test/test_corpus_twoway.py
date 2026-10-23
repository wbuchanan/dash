"""
test_corpus_twoway.py -- the corpus's twoway runner (WP-33 33-03).

scripts/corpus/twoway_run.py writes do-files that run every corpus example
under twoway, between markers, in chunks through scripts/stata_slot.sh;
parses each batch log into a return code and the first message line; reads
the size twoway drew each SVG at; and sets aside every example whose dataset
the offline cache lacks, naming each such dataset once (DECISIONS A-26).
No test here starts Stata: run() is driven by a fake slot command.
"""
import json
import os
import shutil
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts.corpus import extract, twoway_run  # noqa: E402

_SMOKE = os.path.join(_ROOT, "test", "fixtures", "svg_truth_smoke.svg")


def _ex(i, cmd="twoway scatter mpg weight", setup=("sysuse auto, clear",), plottype="scatter"):
    # D57: every example carries its dash twin (extract.py writes both).
    return {"id": i, "cmd": cmd, "dash_cmd": extract.to_dash(cmd), "setup": list(setup),
            "plottype": plottype}


def _write_examples(run, examples):
    run.mkdir(parents=True, exist_ok=True)
    with open(run / "examples.jsonl", "w", encoding="utf-8") as fh:
        for e in examples:
            fh.write(json.dumps(e) + "\n")


def _rows(run):
    with open(run / "twoway.jsonl", encoding="utf-8") as fh:
        return [json.loads(ln) for ln in fh if ln.strip()]


_CANNED = """\
. display "##VERSION " c(stata_version)
##VERSION 19.5

. display "##BEGIN a"
##BEGIN a

. clear

. capture graph drop _all

. capture noisily {
. sysuse auto, clear
(1978 automobile data)
. }

. display "##SETUP a " _rc
##SETUP a 0

. if _rc == 0 {
. capture noisily twoway scatter mpg weight, nosuch
option nosuch not allowed
. display "##RC a " _rc
##RC a 198
. if _rc == 0 capture noisily graph export "x/a.svg", as(svg) replace
. display "##EXPORT a " _rc
##EXPORT a 198
. }
"""


class TestDoText:

    def test_markers_setup_and_export(self, tmp_path):
        cache = str(tmp_path / "cache")
        exs = [_ex("a", setup=["webuse lbw, clear"], cmd="twoway scatter bwt age"),
               _ex("b", setup=[], cmd="twoway function y = x")]
        text = twoway_run.do_text(exs, "/o", cache)
        assert text.splitlines() == [
            "version 19",
            "set more off",
            "set linesize 255",
            'display "##VERSION " c(stata_version)',
            'display "##BEGIN a"',
            "clear",
            "capture graph drop _all",
            "capture noisily {",
            'use "%s/lbw.dta", clear' % cache,
            "}",
            'display "##SETUP a " _rc',
            "if _rc == 0 {",
            "capture noisily twoway scatter bwt age",
            'display "##RC a " _rc',
            'if _rc == 0 capture noisily graph export "/o/a.svg", as(svg) replace',
            'display "##EXPORT a " _rc',
            "}",
            'display "##BEGIN b"',
            "clear",
            "capture graph drop _all",
            "capture noisily {",
            "}",
            'display "##SETUP b " _rc',
            "if _rc == 0 {",
            "capture noisily twoway function y = x",
            'display "##RC b " _rc',
            'if _rc == 0 capture noisily graph export "/o/b.svg", as(svg) replace',
            'display "##EXPORT b " _rc',
            "}",
        ]
        for word in ("scheme", "graph set", "permanently", "discard"):
            assert word not in text


class TestParseLog:

    def test_rc_first_line_and_setup(self):
        log = """\
##VERSION 19.5
. display "##BEGIN a"
##BEGIN a
. capture noisily {
. sysuse auto, clear
(1978 automobile data)
. }
##SETUP a 0
. if _rc == 0 {
. capture noisily twoway scatter mpg weight,  ///
>     foo(1)
  2. display "x"
option foo() not allowed   \n\
r(198);
##RC a 198
##EXPORT a 198
. }
##BEGIN b
. capture noisily {
. use nosuch, clear
file nosuch.dta not found
. }
##SETUP b 601
##BEGIN c
##SETUP c 0
. capture noisily twoway scatter mpg weight
##RC c 0
. if _rc == 0 capture noisily graph export "x/c.svg", as(svg) replace
file x/c.svg saved as SVG format
##EXPORT c 0
"""
        p = twoway_run.parse_log(log)
        assert p["_version"] == "19.5"
        assert p["a"] == {"setup_rc": 0, "rc": 198,
                          "first_line": "option foo() not allowed", "export_rc": None}
        assert p["b"] == {"setup_rc": 601, "rc": None, "first_line": None, "export_rc": None}
        assert p["c"] == {"setup_rc": 0, "rc": 0, "first_line": None, "export_rc": 0}
        assert set(p) == {"_version", "a", "b", "c"}

    def test_setup_output_is_not_the_message(self):
        p = twoway_run.parse_log(_CANNED)
        assert p["a"]["first_line"] == "option nosuch not allowed"
        assert p["a"]["rc"] == 198


class TestSvgSize:

    def test_inches_and_pixels(self, tmp_path):
        assert twoway_run.svg_size(_SMOKE) == (7.5, 4.5)
        px = tmp_path / "p.svg"
        px.write_text('<?xml version="1.0"?>\n<svg version="1.1" width="960px" '
                      'height="480px" viewBox="0 0 10 10"><rect width="5in"/></svg>\n')
        assert twoway_run.svg_size(str(px)) == (10.0, 5.0)
        bare = tmp_path / "b.svg"
        bare.write_text('<svg viewBox="0 0 10 10"></svg>')
        assert twoway_run.svg_size(str(bare)) is None


class TestChunks:

    def test_sizes(self):
        exs = [_ex("e%02d" % i) for i in range(51)]
        exs[30] = _ex("e30", cmd="twoway contour z y x", plottype="contour")
        got = twoway_run.chunks(list(reversed(exs)))
        assert [len(c) for c in got] in ([25, 25, 1], [1, 25, 25])
        alone = [c for c in got if len(c) == 1]
        assert alone == [[exs[30]]]
        ids = [e["id"] for c in got if len(c) > 1 for e in c]
        assert ids == sorted(ids) and "e30" not in ids and len(ids) == 50
        assert [len(c) for c in twoway_run.chunks(exs[:5], size=2)] == [2, 2, 1]


_SIX = [_ex("a", setup=["webuse lbw, clear"]),
        _ex("b", setup=["webuse lbw, clear"]),
        _ex("c", setup=["webuse nhanes2l, clear"]),
        _ex("d", setup=["webuse lifeexp2, clear"]),
        _ex("e", setup=["sysuse auto, clear"]),
        _ex("f", setup=["webuse lbw, clear", "webuse nlswork, clear"])]


class TestMissingDatasets:

    def _cache(self, tmp_path):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "lifeexp2.dta").write_bytes(b"x")
        return str(cache)

    def test_one_line_per_dataset(self, tmp_path):
        cache = self._cache(tmp_path)
        assert twoway_run.missing_datasets(_SIX, cache) == {
            "lbw": ["a", "b", "f"], "nhanes2l": ["c"], "nlswork": ["f"]}
        rows = twoway_run.skip_rows(_SIX, cache)
        assert [r["id"] for r in rows] == ["a", "b", "c", "f"]
        for r in rows:
            assert r["rc"] is None and r["svg"] is None and r["setup_rc"] is None
            assert r["skip"] == ("dataset nhanes2l not cached" if r["id"] == "c"
                                 else "dataset lbw not cached")

    def test_run_names_each_missing_dataset_once(self, tmp_path, monkeypatch, capsys):
        cache = self._cache(tmp_path)
        monkeypatch.setenv("DASH_CORPUS_CACHE", cache)
        run = tmp_path / "run"
        _write_examples(run, _SIX)
        monkeypatch.setattr(twoway_run, "SLOT_CMD", ["sh", "-c", "exit 0", "sh"])
        twoway_run.run(str(run))
        out = capsys.readouterr().out.splitlines()
        skips = [ln for ln in out if ln.startswith("skip:")]
        assert skips == ["skip: dataset lbw not cached",
                         "skip: dataset nhanes2l not cached",
                         "skip: dataset nlswork not cached"]
        do_text = ""
        for root, _d, files in os.walk(run / "tw"):
            for f in files:
                if f.endswith(".do"):
                    do_text += (open(os.path.join(root, f), encoding="utf-8").read())
        for i in "abcf":
            assert "##BEGIN %s\"" % i not in do_text
        assert "##BEGIN d\"" in do_text and "##BEGIN e\"" in do_text
        rows = _rows(run)
        assert [r["id"] for r in rows] == list("abcdef")

    def test_nothing_left_starts_no_stata(self, tmp_path, monkeypatch):
        empty = tmp_path / "empty"
        empty.mkdir()
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(empty))
        run = tmp_path / "run"
        _write_examples(run, [_SIX[0], _SIX[1]])
        monkeypatch.setattr(twoway_run, "SLOT_CMD", ["sh", "-c", "exit 9", "sh"])
        counts = twoway_run.run(str(run))
        assert not (run / "tw").exists()
        assert counts == {"rc0": 0, "refused": 0, "skipped": 2}
        assert {r["skip"] for r in _rows(run)} == {"dataset lbw not cached"}


class TestRecords:

    def test_rows_from_a_parsed_log(self, tmp_path):
        svg_dir = tmp_path / "chunk" / "svg"
        svg_dir.mkdir(parents=True)
        shutil.copy(_SMOKE, svg_dir / "a.svg")
        run = tmp_path / "run"
        run.mkdir()
        parsed = {"_version": "19.5",
                  "a": {"setup_rc": 0, "rc": 0, "first_line": None, "export_rc": 0},
                  "b": {"setup_rc": 0, "rc": 601,
                        "first_line": "file %s/x.dta not found" % run, "export_rc": None},
                  "c": {"setup_rc": 111, "rc": None, "first_line": None, "export_rc": None}}
        exs = [_ex("a"), _ex("b"), _ex("c"), _ex("d")]
        rows = twoway_run.records(exs, parsed, str(svg_dir), str(run))
        a, b, c, d = rows
        assert a == {"id": "a", "rc": 0, "first_line": None, "setup_rc": 0, "export_rc": 0,
                     "svg": "twoway/a.svg", "width_in": 7.5, "height_in": 4.5, "skip": None}
        assert (run / "twoway" / "a.svg").exists() and not (svg_dir / "a.svg").exists()
        assert b["first_line"] == "file <run>/x.dta not found" and b["svg"] is None
        assert c["skip"] == "setup rc 111" and c["rc"] is None
        assert d["skip"] == "chunk ended early" and d["rc"] is None


def _fake_canned(tmp_path, log_text, svg_ids=(), status=0):
    """A fake slot command: copies a canned log (and SVGs) into the chunk folder."""
    log = tmp_path / "canned.log"
    log.write_text(log_text)
    cp = "".join('cp "%s" "$1/svg/%s.svg"; ' % (_SMOKE, i) for i in svg_ids)
    script = 'mkdir -p "$1/svg"; cp "%s" "$1/twoway.log"; %sexit %d' % (log, cp, status)
    return ["sh", "-c", script, "sh"]


class TestTwowayRefusals:

    def test_refused_examples_join_the_dropped_list_once(self, tmp_path):
        # D52: an example twoway refuses is dropped from the comparison and
        # listed with its reason; rewriting the list never repeats a row.
        run = tmp_path / "run"
        run.mkdir()
        (run / "extract_dropped.tsv").write_text(
            "source\twhere\treason\tcmd\nhelp\tx.sthlp:1\tschematic\tscatter yvar xvar\n",
            encoding="utf-8")
        exs = [dict(_ex("a", cmd="twoway scatter mpg weight, nosuch"), source="audit",
                    file="scripts/corpus/audit_probes.txt", line=3),
               dict(_ex("b"), source="help", file="t.sthlp", line=9)]
        rows = [{"id": "a", "rc": 198, "skip": None}, {"id": "b", "rc": 0, "skip": None}]
        for _ in range(2):
            assert twoway_run.drop_refused(str(run), exs, rows) == ["a"]
        with open(run / "twoway.jsonl", "w", encoding="utf-8") as fh:
            for r in rows + [{"id": "s", "rc": None, "skip": "setup rc 111"}]:
                fh.write(json.dumps(r) + "\n")
        assert twoway_run.refused_ids(str(run)) == {"a"}
        lines = (run / "extract_dropped.tsv").read_text(encoding="utf-8").splitlines()
        assert lines == ["source\twhere\treason\tcmd",
                         "help\tx.sthlp:1\tschematic\tscatter yvar xvar",
                         "audit\tscripts/corpus/audit_probes.txt:3\ttwoway refuses (rc 198)"
                         "\ttwoway scatter mpg weight, nosuch"]


class TestRun:

    def test_records_from_a_canned_log(self, tmp_path, monkeypatch, capsys):
        cache = tmp_path / "cache"
        cache.mkdir()
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(cache))
        run = tmp_path / "run"
        _write_examples(run, [_ex("a", cmd="twoway scatter mpg weight, nosuch"), _ex("b"),
                              _ex("c")])
        log = (_CANNED
               + "##BEGIN b\n##SETUP b 0\n##RC b 0\n##EXPORT b 0\n"
               + "##BEGIN c\n##SETUP c 0\n. capture noisily twoway x\n"
               + "file %s/q.dta not found; see %s/z\n##RC c 601\n" % (cache, run))
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_canned(tmp_path, log, ["b"]))
        counts = twoway_run.run(str(run), only={"a", "b", "c"})
        assert counts == {"rc0": 1, "refused": 2, "skipped": 0}
        rows = {r["id"]: r for r in _rows(run)}
        assert rows["a"]["rc"] == 198
        assert rows["a"]["first_line"] == "option nosuch not allowed"
        assert rows["b"]["svg"] == "twoway/b.svg"
        assert (rows["b"]["width_in"], rows["b"]["height_in"]) == (7.5, 4.5)
        assert rows["c"]["first_line"] == "file <cache>/q.dta not found; see <run>/z"
        assert (run / "stata_version.txt").read_text().strip() == "19.5"
        assert (run / "tw" / "c1" / "twoway.do").exists()
        text = (run / "twoway.jsonl").read_text()
        assert str(tmp_path) not in text
        assert list(json.loads(text.splitlines()[0])) == [
            "id", "rc", "first_line", "setup_rc", "export_rc", "svg", "width_in",
            "height_in", "skip"]

    def test_a_timeout_marks_the_rest(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(tmp_path))
        run = tmp_path / "run"
        _write_examples(run, [_ex("a"), _ex("b")])
        monkeypatch.setattr(twoway_run, "SLOT_CMD", ["sh", "-c", "sleep 5", "sh"])
        counts = twoway_run.run(str(run), timeout=1)
        assert counts["skipped"] == 2
        assert {r["skip"] for r in _rows(run)} == {"timeout"}
        out = capsys.readouterr().out
        assert ("corpus: chunk 1 timed out; if no stata-mp process is left, remove a "
                "stale /tmp/dash-stata-slot-<n>.d") in out

    def test_a_dead_chunk_marks_the_rest(self, tmp_path, monkeypatch):
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(tmp_path))
        run = tmp_path / "run"
        _write_examples(run, [_ex("a"), _ex("b"), _ex("c")])
        log = "##VERSION 19.5\n##BEGIN a\n##SETUP a 0\n##RC a 0\n##EXPORT a 0\n##BEGIN b\n"
        monkeypatch.setattr(twoway_run, "SLOT_CMD", _fake_canned(tmp_path, log, ["a"], 3))
        twoway_run.run(str(run))
        rows = {r["id"]: r for r in _rows(run)}
        assert rows["a"]["rc"] == 0 and rows["a"]["svg"] == "twoway/a.svg"
        assert rows["b"]["skip"] == rows["c"]["skip"] == "chunk ended early (rc 3)"


class TestMain:

    def test_cli_prints_the_counts(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(tmp_path))
        run = tmp_path / "run"
        _write_examples(run, [_ex("a"), _ex("b")])
        monkeypatch.setattr(twoway_run, "SLOT_CMD", ["sh", "-c", "exit 0", "sh"])
        assert twoway_run.main(["--run", str(run), "--jobs", "1", "--timeout", "60",
                                "--only", "a"]) == 0
        assert [r["id"] for r in _rows(run)] == ["a"]
        assert "rc0 0, refused 0, skipped 1" in capsys.readouterr().out
