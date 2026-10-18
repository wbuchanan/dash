"""The suite's temporary files live in one folder per test process, which
is removed when the process ends (test/conftest.py).  Dozens of modules
make folders with tempfile.mkdtemp at import or per test and never remove
them; before this, each full run left 15-20 GB in the system temporary
directory (922 dash_parity_* folders, 124 GB, by 18oct2026)."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import conftest  # noqa: E402


def test_temporary_files_go_to_the_process_folder():
    d = tempfile.gettempdir()
    assert os.path.basename(d).startswith(conftest._TMP_PREFIX), d
    assert os.path.realpath(os.environ["TMPDIR"]) == os.path.realpath(d)
    assert os.path.realpath(tempfile.mkdtemp()).startswith(
        os.path.realpath(d) + os.sep)


def test_the_folder_is_removed_at_exit(tmp_path):
    d = tmp_path / (conftest._TMP_PREFIX + "x")
    (d / "a" / "b").mkdir(parents=True)
    (d / "a" / "b" / "f.txt").write_text("x")
    conftest._remove_tmp(str(d))
    assert not d.exists()


def test_a_stale_folder_is_swept(tmp_path):
    old = tmp_path / (conftest._TMP_PREFIX + "old")
    new = tmp_path / (conftest._TMP_PREFIX + "new")
    other = tmp_path / "someone_else"
    for p in (old, new, other):
        p.mkdir()
    t = os.stat(new).st_mtime - 2 * 86400
    os.utime(old, (t, t))
    conftest._sweep_stale_tmp(str(tmp_path))
    assert not old.exists() and new.exists() and other.exists()
