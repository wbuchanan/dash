"""The parity corpus's xdist groups reach xdist (WP-30 test performance, A1).

test_mode_parity.py renders each corpus entry once per process and compares
it eleven ways, and ``conftest.pytest_collection_modifyitems`` marks every
comparison of one entry with one ``xdist_group``, so that under
``--dist loadgroup`` (pyproject.toml) the eleven run on one worker and the
entry is rendered once.

They never did.  An xdist worker reads each item's ``xdist_group`` marks in
its own ``pytest_collection_modifyitems`` and appends the group to the node
id -- the name its scheduler groups by.  pluggy calls the implementations
registered last first, and a worker registers its hook after the conftest
is loaded, so xdist looked before the conftest had marked anything: no node
id carried its group, and every comparison rendered its entry again.
Measured 07oct2026: 446 test-seconds for TestTheTwoModesAgree, 138 with the
groups in place.  The conftest's hook is now ``tryfirst``.

``test_mode_parity.py::test_an_entrys_comparisons_share_one_group`` checks
the same thing on a real worker of the run it is part of.
"""
import os
from types import SimpleNamespace

from xdist.remote import WorkerInteractor

_HERE = os.path.dirname(os.path.abspath(__file__))


class _Item:
    """The parts of a pytest item the two hooks touch."""

    def __init__(self, nodeid, **params):
        self._nodeid = nodeid
        self.callspec = SimpleNamespace(params=params)
        self.marks = []

    @property
    def nodeid(self):
        return self._nodeid

    def add_marker(self, marker):
        self.marks.append(getattr(marker, "mark", marker))

    def iter_markers(self, name=None):
        return (m for m in self.marks if name is None or m.name == name)


class _WorkerConfig:
    """A worker's config as xdist's hook reads it: ``--dist loadgroup``."""

    def getvalue(self, name):
        assert name == "loadgroup", name
        return True


class _Worker:
    """xdist's own worker hook, registered as a worker registers it: after
    the conftest has been loaded."""

    pytest_collection_modifyitems = (
        WorkerInteractor.pytest_collection_modifyitems)


def _conftest_plugin(config):
    """The conftest module pytest registered, not the copy a test module
    gets with ``import conftest``."""
    want = os.path.join(_HERE, "conftest.py")
    for plugin in config.pluginmanager.get_plugins():
        path = getattr(plugin, "__file__", None)
        if path and os.path.abspath(path) == want:
            return plugin
    raise AssertionError("pytest has not registered %s" % want)


def _modify(config, items):
    """Run the conftest's hook and xdist's worker hook on *items*, in the
    order pluggy calls them on a worker, and nothing else's."""
    pm = config.pluginmanager
    conftest = _conftest_plugin(config)
    worker = _Worker()
    pm.register(worker, "test-xdist-groups-worker")
    try:
        others = [p for p in pm.get_plugins()
                  if p is not conftest and p is not worker]
        hook = pm.subset_hook_caller("pytest_collection_modifyitems", others)
        hook(session=None, config=_WorkerConfig(), items=items)
    finally:
        pm.unregister(worker)


class TestTheParityGroupsReachXdist:

    def test_a_parity_comparison_carries_its_group_in_its_node_id(
            self, request):
        nodeid = ("test/test_mode_parity.py::TestTheTwoModesAgree::"
                  "test_same_glyphs[scatter-spec0]")
        items = [_Item(nodeid, name="scatter", spec={})]
        _modify(request.config, items)
        assert [m.kwargs for m in items[0].iter_markers("xdist_group")] \
            == [{"name": "parity:scatter"}]
        assert items[0].nodeid == nodeid + "@parity:scatter", (
            "xdist read the item before the conftest marked it, so the "
            "entry's comparisons are scheduled one by one")

    def test_any_other_item_is_left_alone(self, request):
        nodeid = "test/test_kpi.py::TestKpi::test_mean[x]"
        items = [_Item(nodeid, name="x")]
        _modify(request.config, items)
        assert items[0].nodeid == nodeid
        assert list(items[0].iter_markers("xdist_group")) == []
