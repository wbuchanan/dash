"""`theme(dark)` was advertised for as long as dash has had a help file.

dash.sthlp's Dashboard Options table has always listed
``theme(default, clean, dark)``. ``_THEME_SCHEME_MAP`` has three of those
names and not ``dark``, so ``dash build, theme(dark)`` warned that the name
was unknown and drew s2color -- a white dashboard, from the one theme name a
user picks precisely because they want a dark one.

s1rcolor is Stata's own dark scheme: light text and light markers on a black
plot region. It has shipped in schemes/ since the scheme translation work, so
the option the help advertises can simply be made to mean it.

The table also omitted ``mono``, ``economist`` and ``sj``, which do work, so
the documented set and the working set were wrong in both directions.
"""
import os
import re
import sys
import warnings

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))

import dash_render as dr

_HELP = os.path.join(_HERE, "..", "dash.sthlp")


def _resolve(theme):
    spec = {"graphs": [], "kpis": [],
            "build_options": {"theme": theme, "scheme": "",
                              "session_scheme": ""}}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        name = dr._resolve_scheme_name(spec)
    return name, [str(w.message) for w in caught]


class TestEveryAdvertisedThemeResolves:
    def test_dark_is_statas_dark_scheme(self):
        name, msgs = _resolve("dark")
        assert name == "s1rcolor", (
            f"theme(dark) resolves to {name!r}; the help has advertised "
            f"`dark' since the first release and s1rcolor is the dark scheme "
            f"dash ships"
        )
        assert not msgs, f"theme(dark) still warns: {msgs}"

    @pytest.mark.parametrize("theme,scheme", [
        ("default", "s2color"), ("clean", "s1color"), ("mono", "s1mono"),
        ("dark", "s1rcolor"), ("economist", "economist"), ("sj", "sj"),
    ])
    def test_each_alias_maps_to_a_scheme_that_ships(self, theme, scheme):
        name, msgs = _resolve(theme)
        assert name == scheme
        assert not msgs
        assert scheme in dr.SchemeParser._BUILTIN_NAMES

    def test_case_does_not_matter(self):
        assert _resolve("DARK")[0] == "s1rcolor"

    def test_an_unknown_theme_is_still_reported(self):
        """The control: a name that is not an alias must not resolve."""
        name, msgs = _resolve("chartreuse")
        assert name == "s2color"
        assert any("not a known theme or scheme" in m for m in msgs)


class TestTheHelpAndTheMapAgree:
    @staticmethod
    def _documented():
        with open(_HELP, encoding="utf-8") as fh:
            h = fh.read()
        i = h.index("{marker dashboard_options}")
        j = h.index("{marker layout}", i)
        m = re.search(r"\{cmd:theme\(\}.*?\n?.*?\(([^)]*)\)", h[i:j], re.S)
        assert m, "the theme() row moved; this check would go blind"
        return sorted(set(re.findall(r"\{cmd:([a-z0-9_]+)\}", m.group(1))))

    def test_every_documented_theme_exists(self):
        missing = [t for t in self._documented()
                   if t not in dr._THEME_SCHEME_MAP]
        assert not missing, (
            f"the help advertises theme names dash does not accept: {missing}"
        )

    def test_every_theme_that_works_is_documented(self):
        doc = self._documented()
        missing = [t for t in sorted(dr._THEME_SCHEME_MAP) if t not in doc]
        assert not missing, (
            f"theme() accepts {missing} and the help does not list them"
        )
