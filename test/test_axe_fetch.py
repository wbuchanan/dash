"""axe_fetch.axe_source under concurrent fetches (found by WP-31's closeout
gate, 18oct2026).

The release tier runs test_accessibility_axe.py on several xdist workers;
each worker's module fixture fetched axe-core into the one shared
``<tmp>/dash_axe_4.12.1`` folder through the one ``axe.min.js.part``
name, so a worker whose part file another worker had already renamed
failed with FileNotFoundError (2 errors of 14 example pages).  Each fetch
now writes a part file of its own.  No network: the download and the pin
check are replaced.
"""
import concurrent.futures
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import axe_fetch  # noqa: E402

_DATA = b"/* axe stand-in */"


class _Resp:
    def __init__(self, data):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_concurrent_fetches_each_write_their_own_part_file(monkeypatch,
                                                            tmp_path):
    n = 4
    monkeypatch.setattr(axe_fetch.tempfile, "gettempdir",
                        lambda: str(tmp_path))
    monkeypatch.setattr(axe_fetch, "check", lambda data: None)
    monkeypatch.setattr(axe_fetch.urllib.request, "urlopen",
                        lambda url, timeout=None: _Resp(_DATA))
    # Every fetch reaches its rename before any rename runs, as when the
    # workers start together.
    barrier = threading.Barrier(n, timeout=10)
    real_replace = os.replace

    def replace(src, dst):
        barrier.wait()
        return real_replace(src, dst)

    monkeypatch.setattr(axe_fetch.os, "replace", replace)
    with concurrent.futures.ThreadPoolExecutor(n) as pool:
        futures = [pool.submit(axe_fetch.axe_source) for _ in range(n)]
    # The race surfaced as FileNotFoundError from the losers' rename.
    assert [f.exception() for f in futures] == [None] * n
    assert [f.result() for f in futures] == [_DATA.decode()] * n
    folder = os.path.dirname(axe_fetch.axe_path())
    assert sorted(os.listdir(folder)) == ["axe.min.js"]
