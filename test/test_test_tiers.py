"""The release tier: what a run of the whole suite leaves out (WP-30 D).

Tests marked ``release`` -- headless Chrome, nested pytest runs, the
scipy/statsmodels-free subprocess sweeps, datasets over the size threshold
-- run at release (``make test-release``, part of ``make release``), not in
the default run of the whole suite.  ``conftest._runs_release_tier``
decides, and ``conftest._deselect_release_tier`` drops them and reports
them as deselected.  A file, a node id, -k, --lf or --collect-only keeps
them, so a release test is run directly the usual way.
"""
import os
import sys
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)

import conftest as C  # noqa: E402


class TestWhoRunsTheReleaseTier:

    @pytest.mark.parametrize("args", [[], ["test/"], [_ROOT]])
    def test_the_whole_suite_leaves_it_out(self, args):
        assert not C._runs_release_tier(args, _ROOT)

    @pytest.mark.parametrize("args", [["test/test_csp_browser.py"],
                                      ["test/test_suite_lock.py::TestX"]])
    def test_a_file_or_a_node_id_keeps_it(self, args):
        assert C._runs_release_tier(args, _ROOT)

    @pytest.mark.parametrize("kw", [{"keyword": "chrome"},
                                    {"lastfailed": True},
                                    {"collectonly": True}])
    def test_k_last_failed_and_collect_only_keep_it(self, kw):
        assert C._runs_release_tier(["test/"], _ROOT, **kw)

    @pytest.mark.parametrize("markexpr", ["release", "not release",
                                          "serve or release"])
    def test_a_mark_expression_naming_it_decides_instead(self, markexpr):
        assert C._runs_release_tier(["test/"], _ROOT, markexpr=markexpr)

    def test_a_mark_expression_naming_something_else_does_not(self):
        assert not C._runs_release_tier(["test/"], _ROOT, markexpr="serve")
        assert not C._runs_release_tier(["test/"], _ROOT,
                                        markexpr="not prerelease")

    def test_the_release_tier_keeps_it(self):
        assert C._runs_release_tier(["test/"], _ROOT, tier="release")
        assert not C._runs_release_tier(["test/"], _ROOT, tier="default")


class _Item:
    def __init__(self, name, release):
        self.name, self.release = name, release

    def get_closest_marker(self, name):
        return object() if (name == "release" and self.release) else None


def _config(args, reported):
    opts = {"keyword": "", "lf": False, "collectonly": False,
            "markexpr": ""}
    return SimpleNamespace(
        args=args, rootpath=_ROOT,
        getoption=lambda name, default=None: opts.get(name, default),
        hook=SimpleNamespace(
            pytest_deselected=lambda items: reported.extend(items)))


class TestTheDeselection:

    def test_a_whole_suite_run_drops_and_reports_the_tier(self, monkeypatch):
        monkeypatch.delenv(C.TIER_ENV, raising=False)
        items = [_Item("a", False), _Item("b", True), _Item("c", False)]
        reported = []
        dropped = C._deselect_release_tier(_config(["test/"], reported),
                                           items)
        assert [i.name for i in items] == ["a", "c"]
        assert [i.name for i in dropped] == [i.name for i in reported] \
            == ["b"]

    def test_the_tier_variable_keeps_it(self, monkeypatch):
        monkeypatch.setenv(C.TIER_ENV, "release")
        items = [_Item("a", False), _Item("b", True)]
        reported = []
        assert C._deselect_release_tier(_config(["test/"], reported),
                                        items) == []
        assert [i.name for i in items] == ["a", "b"] and reported == []

    def test_a_targeted_run_keeps_it(self, monkeypatch):
        monkeypatch.delenv(C.TIER_ENV, raising=False)
        items = [_Item("b", True)]
        reported = []
        C._deselect_release_tier(_config(["test/test_x.py"], reported), items)
        assert [i.name for i in items] == ["b"] and reported == []

    def test_the_mark_is_registered(self, request):
        lines = request.config.getini("markers")
        assert [ln for ln in lines if ln.startswith("release:")]


class TestTheMakefileRunsIt:

    def test_test_release_runs_the_tier_and_release_runs_test_release(self):
        with open(os.path.join(_ROOT, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        recipe = mk.split("\ntest-release:", 1)[1].split("\n\n", 1)[0]
        assert "DASH_TEST_TIER=release" in recipe
        assert "-m pytest test/ -m release" in recipe
        release = [ln for ln in mk.splitlines() if ln.startswith("release:")]
        assert release and "test-release" in release[0].split()
        phony = [ln for ln in mk.splitlines() if ln.startswith(".PHONY:")]
        assert phony and "test-release" in phony[0].split()


class TestTheBatchTier:
    """test_mode_parity.py runs at batch ends and at release (make test-all,
    make test-batch, make release), not in the default whole-suite run."""

    @pytest.mark.parametrize("args", [[], ["test/"], [_ROOT]])
    def test_the_whole_suite_leaves_it_out(self, args):
        assert not C._runs_tier("batch", args, _ROOT)

    def test_a_file_or_a_node_id_keeps_it(self):
        assert C._runs_tier("batch", ["test/test_mode_parity.py"], _ROOT)

    def test_the_batch_and_release_tiers_keep_it(self):
        assert C._runs_tier("batch", ["test/"], _ROOT, tier="batch")
        assert C._runs_tier("batch", ["test/"], _ROOT, tier="release")

    def test_the_batch_tier_does_not_keep_the_release_tier(self):
        assert not C._runs_tier("release", ["test/"], _ROOT, tier="batch")

    def test_a_mark_expression_naming_it_keeps_it(self):
        assert C._runs_tier("batch", ["test/"], _ROOT, markexpr="batch")
        assert not C._runs_tier("batch", ["test/"], _ROOT,
                                markexpr="batches")

    def test_a_whole_suite_run_drops_it(self, monkeypatch):
        monkeypatch.delenv(C.TIER_ENV, raising=False)

        class _B:
            def __init__(self, name, batch):
                self.name, self.batch = name, batch

            def get_closest_marker(self, name):
                return object() if (name == "batch" and self.batch) else None
        items = [_B("a", False), _B("p", True)]
        reported = []
        C._deselect_tier(_config(["test/"], reported), items, "batch")
        assert [i.name for i in items] == ["a"]
        assert [i.name for i in reported] == ["p"]

    def test_the_parity_file_carries_the_mark(self):
        with open(os.path.join(_HERE, "test_mode_parity.py"),
                  encoding="utf-8") as fh:
            assert "\npytestmark = pytest.mark.batch\n" in fh.read()

    def test_the_mark_is_registered(self, request):
        lines = request.config.getini("markers")
        assert [ln for ln in lines if ln.startswith("batch:")]

    def test_the_makefile_runs_it_at_batch_ends_and_release(self):
        with open(os.path.join(_ROOT, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        recipe = mk.split("\ntest-batch:", 1)[1].split("\n\n", 1)[0]
        assert "DASH_TEST_TIER=batch" in recipe
        assert "-m pytest test/ -m batch" in recipe
        release = [ln for ln in mk.splitlines() if ln.startswith("release:")]
        assert release and "test-batch" in release[0].split()
