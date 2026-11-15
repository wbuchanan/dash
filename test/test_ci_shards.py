"""ci_shards and conftest's DASH_SHARD: the CI workflow's split of the suite.

GitHub's runner for this repository has 2 CPUs and about 8 GB; the whole
default tier on one runner needed more than its hour (14nov2026), so the
workflow runs it as four jobs, job k with DASH_SHARD=k/4, and each collects
only its shard's test files.
"""
import json
import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import ci_shards as S  # noqa: E402
import conftest as C  # noqa: E402


class TestParse:

    @pytest.mark.parametrize("value,expect", [
        ("1/4", (1, 4)), ("4/4", (4, 4)), ("1/1", (1, 1)), (" 2/3 ", (2, 3)),
    ])
    def test_a_shard_of_n(self, value, expect):
        assert S.parse(value) == expect

    @pytest.mark.parametrize("value", ["", "4", "0/4", "5/4", "a/4", "1/0",
                                       "1/4/2", "-1/4"])
    def test_anything_else_is_refused(self, value):
        with pytest.raises(ValueError):
            S.parse(value)


class TestAssign:

    def test_longest_first_onto_the_least_loaded(self):
        secs = {"a": 10, "b": 7, "c": 5, "d": 4}
        got = S.assign(["d", "c", "b", "a"], secs, 2)
        assert got == {"a": 1, "b": 2, "c": 2, "d": 1}

    def test_equal_loads_go_to_the_lowest_shard(self):
        got = S.assign(["x", "y"], {"x": 1, "y": 1}, 3)
        assert got == {"x": 1, "y": 2}

    def test_a_file_the_table_lacks_counts_its_median(self):
        secs = {"a": 9, "b": 3, "c": 1}
        assert S.weight("new", secs) == 3
        assert S.weight("a", secs) == 9
        assert S.weight("new", {}) == 1.0
        got = S.assign(["a", "b", "c", "new"], secs, 2)
        assert got["a"] == 1 and got["new"] == 2

    def test_the_split_does_not_depend_on_the_order_given(self):
        secs = {"f%d" % i: (i * 7) % 11 for i in range(30)}
        files = sorted(secs)
        assert S.assign(files, secs, 4) == S.assign(files[::-1], secs, 4)

    def test_every_file_lands_in_exactly_one_shard(self):
        files = ["f%d" % i for i in range(17)]
        got = S.assign(files, {}, 4)
        assert sorted(got) == sorted(files)
        assert set(got.values()) == {1, 2, 3, 4}


class TestTheTable:

    def test_seconds_from_a_timing_report(self):
        report = {"files": [{"file": "test/test_a.py", "seconds": 12.345,
                             "tests": 3},
                            {"file": "test/test_b.py", "seconds": 0.04,
                             "tests": 1}]}
        assert S.seconds_from_report(report) == {"test/test_a.py": 12.3,
                                                 "test/test_b.py": 0.0}

    def test_load_seconds_reads_the_table_or_nothing(self, tmp_path):
        p = tmp_path / "t.json"
        p.write_text(json.dumps({"note": "n", "seconds": {"test/x.py": 2.5}}))
        assert S.load_seconds(str(p)) == {"test/x.py": 2.5}
        assert S.load_seconds(str(tmp_path / "missing.json")) == {}

    def test_main_writes_the_table(self, tmp_path, capsys):
        rep = tmp_path / "timing.json"
        rep.write_text(json.dumps({"files": [{"file": "test/test_a.py",
                                              "seconds": 4.0, "tests": 1}]}))
        out = tmp_path / "table.json"
        assert S.main([str(rep), str(out)]) == 0
        table = json.loads(out.read_text())
        assert table["seconds"] == {"test/test_a.py": 4.0}
        assert "DASH_SUITE_TIMING" in table["note"]
        assert S.main([]) == 2
        assert "usage" in capsys.readouterr().err

    def test_the_committed_table_covers_the_default_tier(self):
        """The files it lacks (new ones, and the release tier, which a
        timed default run deselects) weigh its median; past a tenth of
        the files the shards stop balancing on measured seconds."""
        secs = S.load_seconds()
        every = C._shard_candidates(_cfg())
        missing = [f for f in every if f not in secs]
        assert len(missing) <= 0.1 * len(every), missing
        assert all(v >= 0 for v in secs.values())


def _cfg(args=(), worker=False, **opts):
    cfg = SimpleNamespace(args=list(args), rootpath=_ROOT,
                          getoption=lambda name, default=None:
                          opts.get(name, default))
    if worker:
        cfg.workerinput = {"workerid": "gw0"}
    return cfg


@pytest.fixture
def shard_env(monkeypatch):
    """A clean DASH_SHARD environment (the CI jobs set both variables).
    Each is set before it is removed, so the value _shard_for writes is
    undone too where the variable was absent."""
    for name in (C.SHARD_ENV, C.SHARD_OWNER_ENV, C.TIER_ENV):
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)
    return monkeypatch


class TestWhoShards:

    def test_no_variable_runs_whole(self, shard_env):
        assert C._shard_for(_cfg()) is None

    def test_the_controlling_process_takes_the_shard(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "2/4")
        got = C._shard_for(_cfg())
        assert (got.k, got.n) == (2, 4) and got.files
        assert os.environ[C.SHARD_OWNER_ENV] == str(os.getpid())

    def test_a_worker_of_the_owner_takes_it_too(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "2/4")
        shard_env.setenv(C.SHARD_OWNER_ENV, str(os.getppid()))
        got = C._shard_for(_cfg(worker=True))
        assert (got.k, got.n) == (2, 4)
        assert os.environ[C.SHARD_OWNER_ENV] == str(os.getppid())

    def test_a_nested_runs_workers_run_whole(self, shard_env):
        """test_strict_mode starts a nested run with xdist workers; they
        took the shard, and its copied conftest has no ci_shards beside
        it (INTERNALERROR)."""
        shard_env.setenv(C.SHARD_ENV, "2/4")
        shard_env.setenv(C.SHARD_OWNER_ENV, "1")
        assert C._shard_for(_cfg(worker=True)) is None

    def test_a_nested_run_a_test_starts_runs_whole(self, shard_env):
        """It inherits DASH_SHARD from the run that owns the shard."""
        shard_env.setenv(C.SHARD_ENV, "2/4")
        shard_env.setenv(C.SHARD_OWNER_ENV, "1")
        assert C._shard_for(_cfg()) is None

    @pytest.mark.parametrize("args,opts", [
        (["test/test_ci_shards.py"], {}),
        ([], {"keyword": "shard"}),
        ([], {"lf": True}),
    ])
    def test_a_targeted_run_runs_whole(self, shard_env, args, opts):
        shard_env.setenv(C.SHARD_ENV, "1/4")
        assert C._shard_for(_cfg(args, **opts)) is None

    def test_collect_only_lists_the_shard_a_run_collects(self, shard_env):
        """--collect-only keeps the batch tier; the shard it lists must
        still be the one a run collects."""
        shard_env.setenv(C.SHARD_ENV, "1/4")
        listed = C._shard_for(_cfg(collectonly=True))
        shard_env.delenv(C.SHARD_OWNER_ENV)
        run = C._shard_for(_cfg())
        assert listed.k == 1 and listed == run
        cfg = _cfg(collectonly=True)
        cfg._dash_shard = listed
        assert C.pytest_ignore_collect(
            collection_path=C.Path(_HERE, "test_mode_parity.py"),
            config=cfg) is True

    def test_a_bad_value_is_a_usage_error(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "5/4")
        with pytest.raises(pytest.UsageError, match="DASH_SHARD=5/4"):
            C._shard_for(_cfg())


class TestTheShards:

    def test_four_shards_split_the_default_tier_once(self, shard_env):
        shards = []
        for k in range(1, 5):
            shard_env.setenv(C.SHARD_ENV, "%d/4" % k)
            shard_env.delenv(C.SHARD_OWNER_ENV, raising=False)
            shards.append(C._shard_for(_cfg()))
        every = C._shard_candidates(_cfg())
        assert all(s.of == len(every) for s in shards)
        assert sorted(f for s in shards for f in s.files) == sorted(every)
        assert "test/test_mode_parity.py" not in every     # batch tier
        assert "test/test_ci_shards.py" in every

    def test_the_shards_are_balanced(self):
        secs = S.load_seconds()
        every = C._shard_candidates(_cfg())
        got = S.assign(every, secs, 4)
        loads = [sum(S.weight(f, secs) for f in every if got[f] == k)
                 for k in range(1, 5)]
        assert max(loads) <= 1.1 * (sum(loads) / 4), loads

    def test_a_file_outside_the_shard_is_not_collected(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "1/4")
        cfg = _cfg()
        cfg._dash_shard = C._shard_for(cfg)
        inside = sorted(cfg._dash_shard.files)[0]
        outside = sorted(set(C._shard_candidates(cfg))
                         - cfg._dash_shard.files)[0]
        assert C.pytest_ignore_collect(
            collection_path=C.Path(_ROOT, outside), config=cfg) is True
        assert C.pytest_ignore_collect(
            collection_path=C.Path(_ROOT, inside), config=cfg) is None

    def test_a_config_with_no_shard_collects_as_before(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "1/4")
        other = os.path.join(_HERE, "test_ci_shards.py")
        assert C.pytest_ignore_collect(collection_path=C.Path(other),
                                       config=_cfg()) is None

    def test_the_header_names_the_shard(self, shard_env):
        shard_env.setenv(C.SHARD_ENV, "3/4")
        cfg = _cfg()
        cfg._dash_shard = C._shard_for(cfg)
        line = C.pytest_report_header(cfg)
        assert line.startswith("DASH_SHARD=3/4: %d of %d test files"
                               % (len(cfg._dash_shard.files),
                                  cfg._dash_shard.of))
        assert C.pytest_report_header(_cfg()) is None
