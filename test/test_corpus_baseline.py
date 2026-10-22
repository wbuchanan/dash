"""
test_corpus_baseline.py -- the first corpus run's record (WP-33 33-14, TR-2).

make corpus compared every de-duplicated twoway example with dash once;
scripts/corpus/summary.py --out wrote the run's counts to
test/fixtures/corpus_baseline.json after the maintainer approved them.  This
file reads committed files only: no Stata, no Chrome.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "test"))

from scripts.corpus import ledger  # noqa: E402
from test_fixtures_are_committed import META_KEYS  # noqa: E402

_FIXTURE = os.path.join(_ROOT, "test", "fixtures", "corpus_baseline.json")
_VERDICTS = ("Same", "Close", "Differs", "skipped")


def _load():
    with open(_FIXTURE, encoding="utf-8") as fh:
        return json.load(fh)


class TestTheBaseline:

    def test_meta_and_counts(self):
        d = _load()
        meta = d["_meta"]
        assert [k for k in META_KEYS if k not in meta] == []
        assert meta["source"] == "scripts/corpus/summary.py"
        # Whether the count is plausible was judged at the checkpoint (Q12)
        # and by 33-02's AC-33-02.3; the pin only asks for a run.
        assert d["examples"] >= 1
        assert sorted(d["verdicts"]) == sorted(_VERDICTS)
        assert sum(d["verdicts"].values()) == d["examples"]
        total = 0
        for name, t in d["by_plottype"].items():
            assert t["examples"] == sum(t[v] for v in _VERDICTS), name
            total += t["examples"]
        assert total == d["examples"]
        assert d["duplicates"] >= 1
        # D52: an example twoway refuses is dropped, so every example compared
        # is one twoway accepts and the gallery holds at most all of them.
        assert d["twoway_refuses"] >= 0 and set(d["refused"]) == {"dash"}
        assert d["gallery"] <= d["examples"]

    def test_every_ledger_id_is_a_gaps4_id(self):
        tracked = set(ledger.gaps4_states())
        assert tracked
        assert sorted(set(_load()["ledger"]) - tracked) == []
