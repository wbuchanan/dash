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
        # Any properties after the comma: `rclass sortpreserve' is two.
        r"^program define %s(?:,[ \t\w]*)?\s*$(.*?)^end\s*$" % re.escape(name),
        src, re.MULTILINE | re.DOTALL,
    )
    assert m, f"program {name} not found in dash.ado"
    return m.group(1)


def _stata_code(body: str) -> str:
    """*body* with its comments dropped: ``/* */`` blocks, lines that start
    with ``*`` and ``//`` to the end of a line (``//`` after a blank or at
    the start, so the ``//`` of a URL in a string stays)."""
    body = re.sub(r"/\*.*?\*/", " ", body, flags=re.DOTALL)
    return "\n".join(re.sub(r"(^|\s)//.*$", "", line)
                     for line in body.splitlines()
                     if not line.lstrip().startswith("*"))


#: One option as `syntax` declares it: a name, then its argument spec in
#: parentheses if it takes one -- ``SAVing(string)``, ``TABS(string asis)``.
_OPTION = r"([A-Za-z_][A-Za-z0-9_]*)(?:\([^)]*\))?"


def _syntax_options(body: str) -> set:
    """The option names a program's first `syntax` block declares: every
    option on every line, lower-cased.

    This took only the option written last before each line's ``///``, so
    a line declaring two gave one (measured 24sep2026: ``FOO(string)``
    written before ``CSV`` on _dash_build's line, and ``TItle(string)``
    before ``PORT(string)`` on _dash_serve_spec's, were both unseen, and
    the tests below passed).  Now every line must be read in full --
    options, the ``*`` catch-all, blanks and its ``///`` -- or this fails
    naming it, and no option may be declared twice.
    """
    m = re.search(r"^\s*syntax \[, ///\n(.*?)^\s*\]\s*$", body,
                  re.MULTILINE | re.DOTALL)
    assert m, "no multi-line syntax block found"
    names = []
    for line in m.group(1).splitlines():
        assert line.rstrip().endswith("///"), (
            f"a syntax line that does not continue: {line!r}")
        code = line.rstrip()[:-3]
        unread = re.sub(_OPTION + r"|\*", " ", code)
        assert not unread.strip(), (
            f"text in a syntax line this does not read as an option: "
            f"{line!r}")
        names += [t.lower() for t in re.findall(_OPTION, code)]
    assert len(names) == len(set(names)), f"an option declared twice: {names}"
    return set(names)


# Options that belong to one command only and are deliberately not shared.
_PREPARE_ONLY = {"cmdname", "specpath", "datapath", "inherit"}
# Options every dash build has; a reader that finds them has read the list
# (one that had stopped matching would find nothing, and a set difference
# of nothing passes).
_ANCHORS = {"saving", "replace", "nobrowser", "csv"}
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
        # The reader sees both lists: options every build has, in each.
        assert _ANCHORS <= build and _ANCHORS <= prep, (build, prep)
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
        list to drift.

        Exactly its own five, not a subset of them: a subset held for a
        list the reader had read none of (see _syntax_options for the
        option it did not see)."""
        body = _program_body(_read_ado(), "_dash_serve_spec")
        declared = _syntax_options(body)
        assert declared == {"specpath", "datapath", "port", "nobrowser",
                            "timeout"}, (
            f"_dash_serve_spec declares {sorted(declared)}; it should declare "
            f"its own five and forward every build option untouched"
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
        names = re.findall(r"^program define (\S+?)(?:,|\s*$)", src,
                           re.MULTILINE)
        # Every program is read, once: as many names as definitions.
        assert len(names) == len(set(names)) == len(
            re.findall(r"^program define\b", src, re.MULTILINE)), names
        # A program assembles build_options when its CODE names the key, in
        # any spelling -- "build_options":, a key held in a local, a python
        # dict -- which is why the word is searched for, comments dropped.
        # This looked for the key in double quotes, so a program writing it
        # from `local _k build_options' and "`_k'": went unseen, and its
        # subset check held for no writer at all (measured 24sep2026: a
        # second writer in _dash_build, spelled so, passed).
        assemblers = sorted(n for n in names
                            if re.search(r"\bbuild_options\b",
                                         _stata_code(_program_body(src, n))))
        # _dash_render_immediate has its own single-graph spec with no
        # registry, no KPIs and no filters; it is a different document.
        assert assemblers == ["_dash_prepare_spec",
                              "_dash_render_immediate"], assemblers
