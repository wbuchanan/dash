"""numpy's BLAS runs on one thread in every test process (WP-50 50-03).

Under Stata's Python numpy uses OpenBLAS, which opens a pool of one thread
per core in every process: eight xdist workers on a twelve-core machine ran
96 BLAS threads, and the contour tests took 175 s of wall instead of 12 s
(wp50-profile.txt, lever 1).  test/conftest.py sets the thread variables to
1 before numpy is imported; the workers and their subprocesses inherit them.
"""
import os
import subprocess
import sys
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VARS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS")


class TestOneBlasThread:
    def test_this_process_sees_one_thread(self):
        assert {v: os.environ.get(v) for v in VARS} == {v: "1" for v in VARS}

    def test_an_xdist_worker_sees_one_thread(self, tmp_path):
        """A throwaway suite that loads test/conftest.py, run with -n 2 in a
        child whose environment has none of the variables: its tests run in
        the workers and read them there."""
        (tmp_path / "conftest.py").write_text(textwrap.dedent("""
            import sys
            sys.path.insert(0, %r)
            import test.conftest
        """ % ROOT))
        (tmp_path / "test_sample.py").write_text(textwrap.dedent("""
            import os
            VARS = %r
            def test_in_a_worker_a():
                assert os.environ.get("PYTEST_XDIST_WORKER")
                assert [os.environ.get(v) for v in VARS] == ["1"] * len(VARS)
            def test_in_a_worker_b():
                assert os.environ.get("PYTEST_XDIST_WORKER")
                assert [os.environ.get(v) for v in VARS] == ["1"] * len(VARS)
        """ % (VARS,)))
        env = {k: v for k, v in os.environ.items()
               if k not in VARS and not k.startswith("PYTEST_")}
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
             "-o", "addopts=", "-n", "2", str(tmp_path)],
            cwd=str(tmp_path), env=env, capture_output=True, text=True,
            timeout=180)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "2 passed" in r.stdout, r.stdout
