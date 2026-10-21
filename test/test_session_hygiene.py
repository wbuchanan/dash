"""dash leaves the Stata session's Mata library and Python as it found them
(WP-31 H7).

GAPS3 H7: four Mata functions (``_json_escape``, ``_is_utf8``,
``_expand_plottype_str``, ``_first_comma_pos``) were the library's only
unprefixed names, so ``_dash_require_mata``'s repair dropped them from a
hand list; ``sys.argv`` was replaced for the rest of the session by every
build and serve; ``_dash_xm``, ``_dash_render_ns`` and ``_dash_priv_argv``
stayed in Python's ``__main__``.  Section 55 (D-55d, D-55e): the four are
renamed with the prefix and the hand list deleted; argv is saved before
each run and restored before any exit (the run lines are ``capture
noisily``, so an error in the run cannot skip the restore); and the names
are popped from ``__main__`` once read.  test_env_guards.cscript U55-1
checks the running session.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

_MATA_DEF = re.compile(
    r"^(?:string|real|void|transmorphic|numeric|pointer(?:\([^)]*\))?"
    r"|struct\s+\w+|class\s+\w+)"
    r"(?:\s+(?:scalar|vector|rowvector|colvector|matrix))?\s+(\w+)\s*\(",
    re.M)
_OLD = ("_json_escape", "_is_utf8", "_expand_plottype_str",
        "_first_comma_pos")
#: The names a build or a serve puts in __main__ (BR-55.5).
_NAMES = ("_dash_saved_argv", "_dash_xm", "_dash_render_ns",
          "_dash_priv_argv", "_dash_dv")


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _program(ado, name):
    """The lines of dash.ado's program *name*, through its ``end``."""
    lines = ado.splitlines()
    start = next(i for i, l in enumerate(lines)
                 if re.match(r"program define %s\b" % re.escape(name), l))
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].strip() == "end")
    return [l.split("//", 1)[0] for l in lines[start:end + 1]]


def _code(line):
    return line.split("//", 1)[0]


class TestMataNames:
    def test_every_mata_function_is_prefixed(self):
        names = _MATA_DEF.findall(_read("dash_parse.mata"))
        assert len(names) > 200
        assert [n for n in names if not n.startswith("_dash_")] == []

    def test_no_old_name_is_left(self):
        word = re.compile(r"(?<![A-Za-z0-9_])(%s)\b" % "|".join(_OLD))
        for f in ("dash_parse.mata", "dash.ado", "dash_render.py"):
            assert not word.findall(_read(f)), f
        keys = re.findall(r'^ +"(\w+)": ', _read("test/program_coverage_map.py"),
                          re.M)
        assert not set(keys) & set(_OLD)

    def test_the_repair_has_no_hand_list(self):
        body = _program(_read("dash.ado"), "_dash_require_mata")
        drops = [l.strip() for l in body if "mata drop" in l]
        assert drops == ["capture mata: mata drop _dash_*()"]
        assert not any("foreach f in" in l for l in body)


class TestArgv:
    def _sites(self):
        ado = _read("dash.ado").splitlines()
        return ado, [i for i, l in enumerate(ado)
                     if re.match(r"\s*python: sys\.argv = \[", _code(l))]

    def test_dash_ado_saves_and_restores_argv(self):
        ado, sites = self._sites()
        assert len(sites) == 2
        for i in sites:
            assert "_dash_saved_argv = list(sys.argv)" in ado[i - 1], i + 1
            end = next(j for j in range(i, len(ado))
                       if ado[j].strip() == "end")
            body = [_code(l) for l in ado[i:end]]
            run = next(k for k, l in enumerate(body)
                       if "_dash_run_renderer(" in l)
            assert body[run].strip().startswith("capture noisily python:"), \
                body[run]
            assert body[run + 1].strip() == "local _rrc = _rc"
            restore = next(k for k, l in enumerate(body)
                           if "sys.argv = _dash_saved_argv" in l)
            assert restore == run + 2
            # no exit between the argv line and the restore
            assert not any(re.match(r"\s*(exit|error)\b", l)
                           for l in body[:restore]), i + 1

    def test_the_main_names_are_deleted(self):
        ado = _read("dash.ado")
        body = "\n".join(_program(ado, "_dash_py_tidy"))
        for n in _NAMES:
            assert '"%s"' % n in body, n
        assert "globals().pop" in body
        disp = "\n".join(_program(ado, "dash"))
        # after build, serve and the plot route; 3 -> 4: and after dash
        # image, which checks its file in Python (WP-33 33-06)
        assert disp.count("_dash_py_tidy") == 4
        # the render's own names go as soon as the run is over
        ren = "\n".join(_program(ado, "_dash_do_render"))
        assert ren.index("'_dash_render_ns', '_dash_priv_argv'") > \
            ren.index("_dash_run_renderer(")
        load = "\n".join(_program(ado, "_dash_xm_load"))
        assert load.index("del _dash_dv") > \
            load.rindex("_dash_dv[1]")
