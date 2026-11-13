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
import re
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
        # Flipped: the prerequisite line, not the first release: line --
        # `release: GATE_CERT_TIER = release` (the cert release tier,
        # 22oct2026) is a target variable above it.
        release = [ln for ln in mk.splitlines()
                   if ln.startswith("release:") and "=" not in ln]
        assert release and "test-release" in release[0].split()
        phony = [ln for ln in mk.splitlines() if ln.startswith(".PHONY:")]
        assert phony and "test-release" in phony[0].split()


#: The files of the batch tier besides test_mode_parity.py.
#: old -> new: test_mode_parity.py alone -> it and these 52: WP-50 50-03
#: <file> to the batch tier (ruled 13nov2026 at 50-01-04), the tier
#: candidates of wp50-profile.txt, which kept make test above five minutes.
_RULED_BATCH_FILES = (
    "test_serve_token.py", "test_label_sinks.py", "test_server.py",
    "test_js_fit_refit.py", "test_installed_layout.py",
    "test_help_claims_7.py", "test_runner_portability.py",
    "test_saved_filter_layers.py", "test_unsupported_report_is_true.py",
    "test_named_styles.py", "test_lpolyci_band.py",
    "test_scheme_rendered_output.py", "test_scheme_resolution.py",
    "test_horizontal_moves.py", "test_by_axes_keys.py",
    "test_serve_lifecycle.py", "test_size_units.py",
    "test_server_layer_defects.py", "test_help_claims_4.py",
    "test_embedded_rows.py", "test_resource_limits.py",
    "test_legend_place.py", "test_qualifier_logic.py",
    "test_marker_label_parity.py", "test_date_axis_residuals.py",
    "test_server_serves.py", "test_help_claims_5.py", "test_horizontal.py",
    "test_by_types.py", "test_function_expr.py", "test_layer_reports.py",
    "test_join_order.py", "test_note_channel.py", "test_intensity_blend.py",
    "test_graph_text.py", "test_by_layout.py", "test_ci_band_style.py",
    "test_server_facets.py", "test_default_axes.py",
    "test_dependency_guards.py", "test_by_remainder.py",
    "test_ts_operators.py", "test_help_claims_2.py",
    "test_textbox_grammar.py", "test_served_bs_layout.py",
    "test_axis_format_fallback.py", "test_help_claims_6.py",
    "test_by_text.py", "test_tracking_documents.py",
    "test_scheme_consumption.py", "test_help_claims_1.py",
    "test_twenty_six_schemes.py",
)


class TestTheBatchTier:
    """test_mode_parity.py and the files WP-50 50-03 moved
    (``_RULED_BATCH_FILES``) run at batch ends and at release (make
    test-all, make test-batch, make release), not in the default
    whole-suite run (make test)."""

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

    def test_the_ruled_files_are_52(self):
        assert len(set(_RULED_BATCH_FILES)) == len(_RULED_BATCH_FILES) == 52

    @pytest.mark.parametrize("name", _RULED_BATCH_FILES)
    def test_a_ruled_file_carries_the_mark(self, name):
        """The module's own mark, alone or beside the marks it had."""
        with open(os.path.join(_HERE, name), encoding="utf-8") as fh:
            text = fh.read()
        assert re.search(r"(?m)^pytestmark = (pytest\.mark\.batch"
                         r"|\[[^\]\n]*\bpytest\.mark\.batch\b[^\]\n]*\])$",
                         text), name

    def test_the_mark_is_registered(self, request):
        lines = request.config.getini("markers")
        assert [ln for ln in lines if ln.startswith("batch:")]


def _cfg(args=(), **opts):
    """A stand-in pytest config for the collection hook."""
    return SimpleNamespace(args=list(args), rootpath=_ROOT,
                           getoption=lambda name, default=None:
                           opts.get(name, default))


class TestTheBatchTierIsNotCollected:
    """WP-50 50-04: a run that leaves the batch tier out does not collect
    its files at all (it spent 21 s collecting 21,937 tests it then
    deselected); a file is in the tier by its own module-level mark."""

    @pytest.mark.parametrize("line,expect", [
        ("pytestmark = pytest.mark.batch", True),
        ("pytestmark = [pytest.mark.serve, pytest.mark.batch]", True),
        ("pytestmark = pytest.mark.release", False),
        ("    pytestmark = pytest.mark.batch", False),
        ("x = 1", False),
    ])
    def test_a_module_mark_makes_a_batch_file(self, tmp_path, line, expect):
        f = tmp_path / "test_x.py"
        f.write_text('"""Doc."""\nimport pytest\n\n%s\n' % line)
        assert C._batch_file(str(f)) is expect

    def test_a_whole_suite_run_does_not_collect_a_batch_file(self, monkeypatch):
        monkeypatch.delenv(C.TIER_ENV, raising=False)
        parity = os.path.join(_HERE, "test_mode_parity.py")
        other = os.path.join(_HERE, "test_test_tiers.py")
        assert C.pytest_ignore_collect(collection_path=C.Path(parity),
                                       config=_cfg()) is True
        assert C.pytest_ignore_collect(collection_path=C.Path(other),
                                       config=_cfg()) is None

    @pytest.mark.parametrize("tier,args,opts", [
        ("batch", [], {}),
        ("release", [], {}),
        ("", ["test/test_mode_parity.py"], {}),
        ("", [], {"markexpr": "batch"}),
        ("", [], {"collectonly": True}),
    ])
    def test_a_run_that_keeps_the_tier_collects_it(self, monkeypatch, tier,
                                                   args, opts):
        monkeypatch.setenv(C.TIER_ENV, tier)
        parity = os.path.join(_HERE, "test_mode_parity.py")
        assert C.pytest_ignore_collect(collection_path=C.Path(parity),
                                       config=_cfg(args, **opts)) is None

    def test_the_batch_files_are_the_parity_file_and_the_ruled_ones(self):
        found = {n for n in os.listdir(_HERE)
                 if n.startswith("test_") and n.endswith(".py")
                 and C._batch_file(os.path.join(_HERE, n))}
        assert found == {"test_mode_parity.py"} | set(_RULED_BATCH_FILES)

    def test_the_makefile_runs_it_at_batch_ends_and_release(self):
        with open(os.path.join(_ROOT, "Makefile"), encoding="utf-8") as fh:
            mk = fh.read()
        recipe = mk.split("\ntest-batch:", 1)[1].split("\n\n", 1)[0]
        assert "DASH_TEST_TIER=batch" in recipe
        assert "-m pytest test/ -m batch" in recipe
        # Flipped: the prerequisite line, not the first release: line --
        # `release: GATE_CERT_TIER = release` (the cert release tier,
        # 22oct2026) is a target variable above it.
        release = [ln for ln in mk.splitlines()
                   if ln.startswith("release:") and "=" not in ln]
        assert release and "test-batch" in release[0].split()
