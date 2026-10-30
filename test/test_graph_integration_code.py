"""The code behind dash.sthlp's Stata graph integration section (WP-38
section 38-01): the facts its paragraphs state that a help-claim test
cannot see.

* ECO-15 -- One page per command: a session keeps its newest five
  previews; older ones go when the next is written, except a page a
  browser was asked to open in the last minute (TestPreviews).

The graph-memory note the section's Graph memory paragraph relies on is
pinned by test_export_result.py::TestTheGraphExportNote, not here.
"""
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)

import dash_render as dr  # noqa: E402


def _page(folder, n, kind, age):
    """Write preview n of this process, of kind b (opened) or q, *age*
    seconds old; return its name."""
    name = "dash-preview-20261030-%06d-%d-%08x-%s.html" % (
        n, os.getpid(), n, kind)
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("<html></html>")
    t = time.time() - age
    os.utime(path, (t, t))
    return name


class TestPreviews:

    def test_the_newest_five_are_kept(self, tmp_path):
        """Before a new preview is written the newest four stay, so five
        are kept with it; an older page opened in the last minute stays
        too, and an older one opened before that goes."""
        assert dr._DASH_PREVIEW_KEEP == 5
        assert dr._DASH_PREVIEW_GRACE_S == 60
        folder = str(tmp_path)
        newest = [_page(folder, n, "q", 1000 - n) for n in range(1, 5)]
        old_q = _page(folder, 10, "q", 5000)
        old_b = _page(folder, 11, "b", 4000)
        young_b = _page(folder, 12, "b", 0)
        # The four are younger still, so young_b falls outside them.
        for k, name in enumerate(newest):
            t = time.time() + 10 + k
            os.utime(os.path.join(folder, name), (t, t))
        dr._dash_prune_previews(folder, "preview")
        left = set(os.listdir(folder))
        assert set(newest) <= left
        assert young_b in left
        assert old_q not in left and old_b not in left
