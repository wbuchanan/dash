"""`dash serve` and `dash build` must offer the same build options.

They did not. `_dash_serve` declared three options — port(), nobrowser(),
timeout() — and wrote a master JSON whose build_options were literal
constants::

    "layout":"auto","link":"","filter":"","theme":"","title":"","subtitle":""

with no scheme, tabs or filter_position key present at all. So no build
option could be given to `dash serve` and none was inherited, which means the
live server could never have a filter in it — the one capability it is sold
on, since a filter is what makes it recompute aggregates instead of masking
precomputed ones.

Both commands now go through `_dash_prepare_spec`. `_dash_serve_spec` does not
enumerate the build surface at all: it declares only the options it owns and
lets `syntax`'s `*` collect the rest, so the list it forwards is whatever the
user wrote. The invariant left to check is between `_dash_build` and
`_dash_prepare_spec`, which do each declare a list.

The behaviour itself is certified by test_serve_options.cscript, which runs
Stata. This file is the cheap structural half that runs in CI without it:
every test here reads dash.ado as text, ON PURPOSE, and each says what it
pins and which cscript case runs the behaviour.

What the text cannot show (GAPS.md L4, measured in WP-24): an option named
in ``_dash_prepare_spec``'s syntax block need not reach the served spec.
Dropping link() and theme() from the build_options it writes left all
fifteen tests here green; the cscript's [6/7], which runs them through
``dash serve``'s spec path, fails.  Where this file and the cscript
disagree, the cscript is right.
"""
import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ADO = os.path.join(_HERE, "..", "dash.ado")


def _read_ado() -> str:
    with open(_ADO, encoding="utf-8") as fh:
        return fh.read()


def _program_body(src: str, name: str) -> str:
    m = re.search(
        r"^program define %s(?:,\s*\w+)?\s*$(.*?)^end\s*$" % re.escape(name),
        src, re.MULTILINE | re.DOTALL,
    )
    assert m, f"program {name} not found in dash.ado"
    return m.group(1)


def _syntax_options(body: str) -> set:
    """The option names a program's first `syntax` block declares."""
    m = re.search(r"^\s*syntax \[, ///(.*?)^\s*\]\s*$", body,
                  re.MULTILINE | re.DOTALL)
    assert m, "no multi-line syntax block found"
    names = set()
    for tok in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\s*(?:\([^)]*\))?\s*///",
                          m.group(1)):
        names.add(tok.lower())
    return names


# Options that belong to one command only and are deliberately not shared.
_PREPARE_ONLY = {"cmdname", "specpath", "datapath", "inherit"}
# `filter()` is pre-extracted from `0` by _dash_extract_filters and passed
# separately, so _dash_build never declares it.
_PASSED_SEPARATELY = {"filter"}


class TestTheBuildSurfaceIsShared:
    def test_prepare_spec_accepts_every_option_dash_build_accepts(self):
        """Otherwise forwarding `0` aborts the user's build.

        A structural guard, deliberately: it compares the two syntax blocks
        themselves, so an option added to ``_dash_build`` alone fails here
        before any behavioural test has been taught its name.  The
        behaviour, for today's list, is test_serve_options.cscript [7/7]:
        every dash build option through both commands, rc 0.
        """
        src = _read_ado()
        build = _syntax_options(_program_body(src, "_dash_build"))
        prep = _syntax_options(_program_body(src, "_dash_prepare_spec"))
        missing = build - prep
        assert not missing, (
            f"_dash_build accepts {sorted(missing)} but _dash_prepare_spec "
            f"does not; forwarding `0' would fail with "
            f"'option not allowed'"
        )

    def test_dash_build_accepts_every_shared_option_prepare_spec_accepts(self):
        """Otherwise `dash serve` silently accepts what `dash build` rejects.

        `_dash_serve_spec` forwards with `*`, so anything `_dash_prepare_spec`
        declares is reachable from `dash serve`. If `dash build` does not
        declare it too, the two commands have different option surfaces
        again — which is the defect this whole change exists to remove.

        A structural guard, deliberately, for the reason the test above is
        one; the behaviour for today's list is the cscript's [7/7].
        """
        src = _read_ado()
        build = _syntax_options(_program_body(src, "_dash_build"))
        prep = _syntax_options(_program_body(src, "_dash_prepare_spec"))
        extra = prep - build - _PREPARE_ONLY - _PASSED_SEPARATELY
        assert not extra, (
            f"_dash_prepare_spec accepts {sorted(extra)}, reachable from "
            f"`dash serve', but `dash build' does not declare it"
        )

    @pytest.mark.parametrize("opt", ["layout", "link", "theme", "scheme",
                                     "title", "subtitle", "tabs",
                                     "filterposition"])
    def test_the_option_that_could_not_reach_the_server_now_can(self, opt):
        """The option is declared where ``dash serve`` forwards to.

        A declaration is not delivery: this stayed green with link() and
        theme() dropped from the served build_options.  That each of the
        eight reaches the served spec is the cscript's [1/5] (layout,
        scheme, title, subtitle, tabs, filterposition) and [6/7] (link,
        theme), which this duplicates in the cheap, text-only form.
        """
        src = _read_ado()
        prep = _syntax_options(_program_body(src, "_dash_prepare_spec"))
        assert opt in prep


class TestServeDoesNotEnumerateTheBuildSurface:
    def test_serve_spec_forwards_with_a_catch_all(self):
        """The structural reason the two lists cannot drift again.

        A structural guard, deliberately: it pins HOW ``dash serve`` takes
        the build surface -- by forwarding, never by listing it -- which no
        run of today's options can show.
        """
        body = _program_body(_read_ado(), "_dash_serve_spec")
        m = re.search(r"^\s*syntax \[, ///(.*?)^\s*\]\s*$", body,
                      re.MULTILINE | re.DOTALL)
        assert m, "no syntax block in _dash_serve_spec"
        assert re.search(r"^\s*\*\s*///", m.group(1), re.MULTILINE), (
            "_dash_serve_spec must use syntax's * catch-all rather than "
            "listing the build options itself"
        )

    def test_serve_spec_declares_only_its_own_options(self):
        """A structural guard, deliberately, the other half of the catch-all
        rule above: a build option declared here again would be a second
        list to drift."""
        body = _program_body(_read_ado(), "_dash_serve_spec")
        declared = _syntax_options(body)
        assert declared <= {"specpath", "datapath", "port", "nobrowser",
                            "timeout"}, (
            f"_dash_serve_spec declares build options {sorted(declared)}; "
            f"it should forward them untouched instead"
        )

    def test_serve_spec_asks_prepare_spec_to_inherit(self):
        """The documented build-then-serve sequence depends on it.

        Text only; the behaviour is the cscript's [3/5] (a dash build's
        options are inherited) and [4/5] (an explicit one wins).
        """
        body = _program_body(_read_ado(), "_dash_serve_spec")
        assert re.search(r"_dash_prepare_spec[^\n]*inherit", body), (
            "dash serve must inherit the preceding dash build's options"
        )


class TestTheHardcodedMasterJsonIsGone:
    def test_no_build_options_literal_survives_in_dash_serve(self):
        """Text only; the behaviour -- the options given to ``dash serve``
        are the ones in its spec, not constants -- is the cscript's [1/5],
        [6/7] and [7/7]."""
        src = _read_ado()
        for name in ("_dash_serve", "_dash_serve_spec"):
            body = _program_body(src, name)
            assert '"layout":"auto"' not in body, (
                f"{name} still hardcodes build_options"
            )
            assert "build_options" not in body, (
                f"{name} still assembles its own master JSON"
            )

    def test_only_one_program_assembles_build_options(self):
        """Two copies is how they drifted; three would be worse.

        A structural guard, deliberately: that there is ONE writer of the
        dashboard's build_options is a property of the source, not of any
        one dashboard.
        """
        src = _read_ado()
        assemblers = [
            name for name in re.findall(
                r"^program define (\S+?)(?:,|\s*$)", src, re.MULTILINE)
            if '"build_options"' in _program_body(src, name.rstrip(","))
            or '"build_options":' in _program_body(src, name.rstrip(","))
        ]
        # _dash_render_immediate has its own single-graph spec with no
        # registry, no KPIs and no filters; it is a different document.
        assert set(assemblers) <= {"_dash_prepare_spec",
                                   "_dash_render_immediate"}, assemblers
