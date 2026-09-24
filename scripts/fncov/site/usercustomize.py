"""Start dash's function-coverage recorder in every Python process.

Python imports ``usercustomize`` at start-up (after ``sitecustomize``), from
the first directory on ``sys.path`` that has one.  This directory is put on
``PYTHONPATH`` only by ``scripts/fncov/run_fncov.sh`` and by
``dash_fncov_plugin.py``, and this file does nothing unless
``DASH_FNCOV_DIR`` is set, so it never affects an ordinary run.  It is a
``usercustomize`` and not a ``sitecustomize`` so that it cannot shadow the
interpreter's own ``sitecustomize`` (Homebrew's adds its site-packages).
"""
import os

if os.environ.get("DASH_FNCOV_DIR"):
    import sys

    _dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _dir not in sys.path:
        sys.path.insert(0, _dir)
    try:
        import dash_fncov_recorder

        dash_fncov_recorder.start(os.environ["DASH_FNCOV_DIR"])
    except Exception:  # never break the process being measured
        pass
