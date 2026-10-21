"""
test_corpus_datasets.py -- the corpus's dataset cache (WP-33 33-02, A-26).

scripts/corpus/datasets.py keeps the webuse datasets the corpus needs in a
git-ignored cache, fetches only those the cache lacks, and rewrites a setup's
webuse lines to read the cache, naming each dataset it lacks.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts.corpus import datasets  # noqa: E402


class TestDatasets:

    def test_shipped_and_rewrite(self, tmp_path, monkeypatch):
        stata = tmp_path / "stata"
        (stata / "ado" / "base" / "a").mkdir(parents=True)
        (stata / "ado" / "base" / "a" / "auto.dta").write_bytes(b"x")
        assert datasets.shipped(str(stata)) == {"auto"}
        cache = tmp_path / "cache"
        cache.mkdir()
        setup = ["webuse nlswork, clear", "gen x = 1", "webuse lbw", "webuse lbw, clear"]
        out, missing = datasets.rewrite_setup(setup, str(cache))
        assert missing == ["nlswork", "lbw"]
        assert out == ['use "%s/nlswork.dta", clear' % cache, "gen x = 1",
                       'use "%s/lbw.dta", clear' % cache, 'use "%s/lbw.dta", clear' % cache]
        (cache / "lbw.dta").write_bytes(b"x")
        assert datasets.rewrite_setup(setup, str(cache))[1] == ["nlswork"]
        assert datasets.datasets_of(["sysuse auto, clear", "webuse lbw",
                                     "qui reg mpg weight", "sysuse auto"]) == ["auto", "lbw"]
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(cache))
        assert datasets.cache_dir() == str(cache)
        monkeypatch.delenv("DASH_CORPUS_CACHE")
        assert datasets.cache_dir() == os.path.join(_ROOT, "scripts", "corpus", ".cache")

    def test_fetch_do_text(self, tmp_path, monkeypatch):
        text = datasets.fetch_do(["lbw", "nhanes2l"], "/c")
        assert "capture noisily webuse lbw, clear\n" in text
        assert 'if _rc == 0 save "/c/lbw.dta", replace\n' in text
        assert 'display "CORPUS-FETCH nhanes2l " _rc\n' in text
        # fetch: writes fetch.do, runs the slot script once, reads the log.
        calls = []
        run = tmp_path / "run"

        def fake_run(argv, check=False):
            calls.append(argv)
            (run / "fetch.log").write_text(". display \"CORPUS-FETCH lbw \" _rc\n"
                                           "CORPUS-FETCH lbw 0\nCORPUS-FETCH nhanes2l 631\n")
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(tmp_path / "cache"))
        monkeypatch.setattr(datasets.subprocess, "run", fake_run)
        res = datasets.fetch(["lbw", "nhanes2l"], str(run))
        assert res == {"lbw": 0, "nhanes2l": 631}
        assert len(calls) == 1 and calls[0][0] == "sh"
        assert calls[0][1].endswith(os.path.join("scripts", "stata_slot.sh"))
        assert (run / "fetch.do").read_text().count("webuse") == 2

    def test_fetch_skips_cached_datasets(self, tmp_path, monkeypatch, capsys):
        cache = tmp_path / "cache"
        cache.mkdir()
        (cache / "lbw.dta").write_bytes(b"x")
        assert datasets.uncached(["lbw", "nhanes2l", "lbw"], str(cache)) == ["nhanes2l"]
        run = tmp_path / "run"
        run.mkdir()
        recs = [{"id": "a", "datasets": ["lifeexp2"]}, {"id": "b", "datasets": ["lbw"]},
                {"id": "c", "datasets": ["nhanes2l", "lifeexp2"]}]
        (run / "examples.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
        empty = tmp_path / "stata"
        empty.mkdir()
        monkeypatch.setenv("DASH_CORPUS_CACHE", str(cache))
        monkeypatch.setenv("DASH_STATA_DIR", str(empty))
        calls = []

        def fake_fetch(names, run_dir):
            calls.append(list(names))
            for n in names:
                (cache / (n + ".dta")).write_bytes(b"x")
            return {n: 0 for n in names}
        monkeypatch.setattr(datasets, "fetch", fake_fetch)
        assert datasets.main(["--fetch", str(run)]) == 0
        assert calls == [["lifeexp2", "nhanes2l"]]
        out = capsys.readouterr().out
        assert "corpus: lbw already cached" in out
        assert "corpus: lifeexp2 cached" in out
        assert datasets.main(["--fetch", str(run)]) == 0
        assert calls == [["lifeexp2", "nhanes2l"]]
        out = capsys.readouterr().out
        for n in ("lbw", "lifeexp2", "nhanes2l"):
            assert "corpus: %s already cached" % n in out
