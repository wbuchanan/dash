"""Probe groups and the gate's served subset (pytest speed, 22oct2026).

A truth test compares dash with twoway probe by probe, once per mode.  Two
rules keep those tests inside the five-minute target without dropping a
probe from the saved comparison:

* **Groups.**  ``probe_params`` cuts a test's sorted probe ids into
  consecutive groups of at most *size* (saved: *saved_size*) and gives
  each (mode, group) its own node, so xdist spreads one fixture's probes
  over the workers instead of one worker looping over all of them.  A
  node still fails once, naming every differing probe of its group.

* **The served subset.**  A served build costs several times a saved one.
  The batch-end gate (``DASH_TEST_TIER=batch``, make test-all) and the fast
  default (make test) check a deterministic representative subset of each
  heavy served comparison; ``representative`` states the rule.  The served
  groups of the other probes carry ``pytest.mark.release``, so a run of the
  whole suite deselects them at collection (conftest ``_deselect_tier``:
  never a skip, which DASH_STRICT=1 would turn red) and the release tier
  (``DASH_TEST_TIER=release``, make test-release) checks every probe in
  served mode.  A narrower run -- a file, a node id, -k, --lf -- keeps
  them, as it keeps every release test.  Saved mode always checks every
  probe.

A known-differences table (``<NAME>_KNOWN``, test/known_differences.py)
is checked group by group: ``known_in`` is the table's rows for one
group's probes, and ``known_outside`` the rows whose probe no group
covers, which the file's hygiene test (``test_every_known_difference_is_
open``) fails on, as ``known_problems`` rule (4) did when one test saw
every probe.
"""
import pytest

#: The mode ids of a probe test, in node order.
MODES = ("saved", "served")


def representative(ids, category=None, always=(), stride=4):
    """The served subset of *ids*, sorted.

    Deterministic and stated: (1) every id in *always* (a file passes the
    probes its known-differences table lists, and any probe it names as a
    lone case of its kind); (2) the first id, in sorted order, of each
    distinct ``category(id)`` (a file's category is the plot type, site,
    scheme or option family that takes a different branch); (3) every
    *stride*-th id of the rest, in sorted order, starting with the first.
    Ids in *always* that are not in *ids* are ignored.
    """
    if stride < 1:
        raise ValueError("stride must be at least 1, not %r" % (stride,))
    ids = sorted(set(ids))
    always = set(always)
    keep = {i for i in ids if i in always}
    if category is not None:
        seen = set()
        for i in ids:
            c = category(i)
            if c not in seen:
                seen.add(c)
                keep.add(i)
    rest = [i for i in ids if i not in keep]
    keep.update(rest[::stride])
    return sorted(keep)


def groups(ids, size=None):
    """*ids* (in their order) cut into consecutive tuples of at most
    *size*; one tuple of them all when *size* is None or 0."""
    ids = list(ids)
    if not ids:
        return []
    if not size:
        return [tuple(ids)]
    if size < 0:
        raise ValueError("size must not be negative, not %r" % (size,))
    return [tuple(ids[i:i + size]) for i in range(0, len(ids), size)]


def _gid(prefix, group, whole):
    if whole:
        return prefix
    if len(group) == 1:
        return "%s-%s" % (prefix, group[0])
    return "%s-%s-%s" % (prefix, group[0], group[-1])


def probe_params(ids, subset=None, size=None, saved_size=None,
                 modes=MODES):
    """``pytest.param(mode, group)`` for ``parametrize("mode,group", ...)``.

    Saved: every id (sorted) in groups of *saved_size* (default *size*).
    Served: the ids of *subset* (``representative``'s list; None: every
    id) in groups of *size*, then the other ids in groups of *size* marked
    ``release``.  Ids: ``saved``, ``served`` and ``served-rest`` without a
    size (one group a part), else the part's name and its group's first
    and last probe.
    Empty *ids* raise (a parameter set never comes out empty: pytest
    would skip it).
    """
    ids = sorted(set(ids))
    if not ids:
        raise ValueError("no probe ids: the fixture is missing or empty")
    sub = ids if subset is None else sorted(set(subset))
    stray = sorted(set(sub) - set(ids))
    if stray:
        raise ValueError("subset ids that are not probes: %r" % (stray,))
    rest = [i for i in ids if i not in set(sub)]
    out = []
    for mode in modes:
        if mode != "served":
            n = saved_size or size
            out += [pytest.param(mode, g, id=_gid(mode, g, not n))
                    for g in groups(ids, n)]
            continue
        out += [pytest.param(mode, g, id=_gid(mode, g, not size))
                for g in groups(sub, size)]
        out += [pytest.param(mode, g, id=_gid("served-rest", g, not size),
                             marks=pytest.mark.release)
                for g in groups(rest, size)]
    return out


def _probe_of(key):
    """A known-differences key's probe: the part before a ``:check``."""
    return str(key).partition(":")[0]


def known_in(known, group, probe_of=_probe_of):
    """The rows of *known* whose probe is in *group*."""
    group = set(group)
    return {k: v for k, v in known.items() if probe_of(k) in group}


def known_outside(known, ids, probe_of=_probe_of):
    """The keys of *known* whose probe is not among *ids*, sorted."""
    ids = set(ids)
    return sorted(k for k in known if probe_of(k) not in ids)
