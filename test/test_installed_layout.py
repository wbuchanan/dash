"""A ``net install``ed dash must resolve the schemes it shipped.

What Stata actually does with the manifest
------------------------------------------
Measured, by running a real ``net install`` from a local source into a clean
``PLUS`` and listing the tree (``sysdir set PLUS <tmp>``; ``net from <src>``;
``net install dash, replace``).  Stata's own ``stata.trk`` records the same
destinations, so this is not an artefact of how the source was staged::

    PLUS/d/dash.ado  dash.sthlp  dash_parse.mata  dash_setup.ado  dash_setup.sthlp
    PLUS/py/dash_render.py                      <- EXTENSION subdirectory
    PLUS/py/dash_setup_lib.py                   (WP-29 P0.19)
    PLUS/e/economist.scheme
    PLUS/s/s1color s1mono s1rcolor s2color s2gcolor s2mono sj stcolor
          stcolor_alt stgcolor stmono1 stmono2 stsj                (.scheme)

The ``schemes/`` component of each ``f schemes/<name>.scheme`` line is dropped;
Stata files by basename and extension, not by the path in the manifest.

That was the layout until WP-28.  Since then dash ships each scheme as
``f dash-<name>.scheme`` in the package root, and Stata files every one of them
under ``PLUS/d/`` (the first letter of ``dash-``).  The staging below follows
the manifest, so it holds the current layout.

The defect this file exists for
-------------------------------
``SchemeParser._SCHEME_SEARCH_DIRS`` is ``(<dir of dash_render.py>/schemes,
<dir of dash_render.py>)``.  On an installed tree that is ``PLUS/py/schemes``
and ``PLUS/py`` -- neither holds a ``.scheme`` file.  Measured against the
installed copy, all fourteen built-in names returned ``is_fallback=True``,
``name='s2color'``, with two ``UserWarning``\\ s each: **0 of 14 resolved**.

End to end from Stata, on the installed tree::

    dash scatter mpg weight, name(g1) scheme(s1color)
    dash build, saving(out.html) replace nobrowser

returned rc 0, wrote a 1,227,573-byte dashboard, printed four raw Python
``UserWarning`` blocks, and the HTML carried s2color's ``#eaf2f3`` background
twice -- s1color's white background appears nowhere.  The default scheme fails
the same way, so *every* installed build warns, and Stata 18+ defaults
``c(scheme)`` to ``stcolor``, which differs from the fallback in 9 of 15
measured properties.

Why nine existing scheme test files missed it
---------------------------------------------
All of them run in the development tree, where ``dash_render.py`` sits beside
``schemes/`` and resolution always succeeds.  ``test_packaging.py`` stages a
manifest-only install and comes closest, but its assertions are satisfied by
``SchemeParser.fallback()`` -- ``scheme is not None`` and ``default_color()``
starts with ``#`` are both true of the fallback -- so it passes on a tree where
no scheme file is readable at all.  The assertions here are about *provenance*:
``is_fallback`` and ``name``, which the fallback cannot fake.

Security
--------
The resolver's abspath-containment and realpath-symlink checks are the only
thing standing between a ``scheme()`` string and the filesystem, and
``scheme()`` is user input that reaches ``_resolve_path`` unfiltered at the
graph level (``dash_render.py`` ``_make_figure``).  Widening the resolver to
find the installed files must not widen what else it can read.

The trap, and why the tests below are shaped the way they are: the obvious
patch appends the install's letter directory to the shared ``allowed`` list.
``allowed`` also governs the **CWD candidate**, which the caller fully
controls, so that patch would let a symlink named ``s2color.scheme`` planted in
the working directory point at any file in ``PLUS/s`` -- reopening BUG-51
(``test_scheme.py`` "symlink path traversal bypass").  The existing BUG-51
tests cannot catch it: they use a name that is not one of the fourteen, and
they run in the dev layout where the installed lookup is inert.
``TestTheInstalledLookupDoesNotWidenWhatElseIsReadable`` closes exactly that.

Tests: INST-01 through INST-18.  INST-01..02 run over every scheme dash.pkg
ships (twenty since WP-17, twenty-six since WP-30 P1.25a), not only the fourteen measured; INST-18 holds
the help text B3 was closed by.
"""
from __future__ import annotations

import os
import shutil
import sys
import warnings
from unittest import mock

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from test_packaging import REPO_ROOT, load_staged_render  # noqa: E402

#: The fourteen schemes shipped when the install was measured, and the letter
#: directory Stata filed each one under -- taken from that install, not from
#: the manifest.
MEASURED_INSTALL = {
    "economist": "e",
    "s1color": "s", "s1mono": "s", "s1rcolor": "s",
    "s2color": "s", "s2gcolor": "s", "s2mono": "s",
    "sj": "s",
    "stcolor": "s", "stcolor_alt": "s", "stgcolor": "s",
    "stmono1": "s", "stmono2": "s", "stsj": "s",
}


def _manifest_schemes():
    """Every scheme ``dash.pkg`` ships, with the letter directory it lands in.

    The rule is the one measured above -- Stata files a ``.scheme`` by its
    first letter -- applied to the manifest, so a scheme shipped later is
    held too.  Six were added after the measurement (WP-17), and with the
    lookup narrowed back to the measured fourteen, INST-01..16 all passed
    (WP-24); only test_help_claims_8.py's all-twenty staging noticed.
    Since WP-28 each ships as ``f dash-<name>.scheme``, so every one lands in
    ``d/``.
    """
    out = {}
    with open(os.path.join(REPO_ROOT, "dash.pkg"), encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.split()
            if (len(parts) == 2 and parts[0] == "f"
                    and parts[1].startswith("dash-")
                    and parts[1].endswith(".scheme")):
                name = parts[1][len("dash-"):-len(".scheme")]
                out[name] = "d"
    return out


def _shipped(name):
    """The file name dash ships scheme *name* under."""
    return "dash-%s.scheme" % name


#: Every scheme dash ships, and the letter directory Stata files it under.
INSTALLED_SCHEMES = _manifest_schemes()

#: Files a Stata PLUS directory holds that belong to OTHER packages.  Planted
#: so the containment tests have something real to try to reach.
FOREIGN_FILES = {
    "j/jsonio.ado": "* another package's source\n",
    "j/jsonio.jar": "PK\x03\x04not-a-real-jar\n",
    "d/dash.ado": "* dash's own ado, which is not a scheme\n",
    "stata.trk": "S https://example.invalid/\nN dash.pkg\n",
}


def _build_installed_tree(root: str) -> str:
    """Stage the MEASURED ``net install`` layout under *root*.

    Returns the install root.  ``dash_render.py`` goes to ``py/`` and each
    scheme to its first letter's directory, exactly as Stata filed them.
    """
    for sub in ("py", "d", "e", "s", "j"):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
    shutil.copy2(os.path.join(REPO_ROOT, "dash_render.py"),
                 os.path.join(root, "py", "dash_render.py"))
    for name, letter in INSTALLED_SCHEMES.items():
        shutil.copy2(os.path.join(REPO_ROOT, _shipped(name)),
                     os.path.join(root, letter, _shipped(name)))
    for rel, body in FOREIGN_FILES.items():
        target = os.path.join(root, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as fh:
            fh.write(body)
    return root


@pytest.fixture
def installed(tmp_path, monkeypatch):
    """``dash_render`` loaded from a staged install, CWD outside it.

    The working directory is moved to an EMPTY directory: the resolver tries
    CWD first, and a test that ran from the repo would resolve every scheme
    out of ``./schemes`` and prove nothing.
    """
    root = _build_installed_tree(str(tmp_path / "plus"))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    name, module = load_staged_render(os.path.join(root, "py"))
    try:
        yield module, root, str(elsewhere)
    finally:
        sys.modules.pop(name, None)


def _resolve(module, name):
    """Resolve *name* and report (is_fallback, resolved_name, n_warnings)."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        scheme = module.SchemeParser.resolve_or_fallback(name, "a test")
    return scheme.is_fallback, scheme.name, len(caught)


# ==========================================================================
# INST-01..03 — the gate: an installed tree resolves what it shipped
# ==========================================================================

class TestAnInstalledTreeResolvesItsOwnSchemes:

    @pytest.mark.parametrize("name", sorted(INSTALLED_SCHEMES))
    def test_the_scheme_is_read_from_the_file_not_faked(self, installed, name):
        """INST-01. Measured before the fix: 14 of 14 came back fallback."""
        module, _root, _cwd = installed
        is_fallback, resolved, _n = _resolve(module, name)
        assert is_fallback is False, (
            "%s fell back to built-in defaults on an installed tree; the "
            "shipped file was never found" % name
        )
        assert resolved == name, (
            "asked for %r and got %r" % (name, resolved)
        )

    @pytest.mark.parametrize("name", sorted(INSTALLED_SCHEMES))
    def test_resolving_it_says_nothing(self, installed, name):
        """INST-02. Two UserWarnings per resolution before the fix.

        A warning on a healthy install is not cosmetic: it tells the user to
        reinstall a package that is fine, and it fires for the DEFAULT scheme
        too, so it appears on every build.
        """
        module, _root, _cwd = installed
        _f, _n, n_warn = _resolve(module, name)
        assert n_warn == 0, "%s warned %d time(s) on a healthy install" % (name, n_warn)

    def test_the_manifest_ships_every_built_in_name_and_the_measured_ones(
            self):
        """INST-17. The list INST-01..02 run over is complete.

        Every name the renderer treats as built in is shipped, every shipped
        name is one it treats as built in, and each of the fourteen measured
        in the real install is still shipped -- now to ``d/``, as every
        ``dash-<name>.scheme`` is (WP-28).
        """
        import dash_render as dr
        assert set(INSTALLED_SCHEMES) == set(dr.SchemeParser._BUILTIN_NAMES), (
            "dash.pkg and SchemeParser._BUILTIN_NAMES disagree: %r"
            % (set(INSTALLED_SCHEMES) ^ set(dr.SchemeParser._BUILTIN_NAMES),)
        )
        for name, letter in MEASURED_INSTALL.items():
            assert INSTALLED_SCHEMES.get(name) == "d", (name, letter)

    def test_the_default_scheme_is_the_real_s2color(self, installed,
                                                    monkeypatch):
        """INST-03. The fallback mimics s2color, so only provenance separates
        them: the shipped file is the one read.  (The fallback has the same
        219 keys since WP-30 P1.14b gave it `symbol p', `linepattern p' and
        `linewidth pbar', so a count no longer tells them apart.)"""
        module, root, _cwd = installed
        on_disk = os.path.join(root, "d", "dash-s2color.scheme")
        read = []
        real = module.SchemeParser.__dict__["_read_scheme_lines"].__func__

        def spy(cls, path, *a, **k):
            read.append(os.path.realpath(path))
            return real(cls, path, *a, **k)

        monkeypatch.setattr(module.SchemeParser, "_read_scheme_lines",
                            classmethod(spy))
        scheme = module.SchemeParser("s2color")
        assert scheme.is_fallback is False
        assert os.path.realpath(on_disk) in read, (on_disk, read)
        assert scheme._props != module.SchemeParser._FALLBACK_PROPS


# ==========================================================================
# INST-04..09 — the installed lookup must widen nothing else
# ==========================================================================

class TestTheInstalledLookupDoesNotWidenWhatElseIsReadable:

    @pytest.mark.parametrize("attempt", [
        "j/jsonio.ado",
        "d/dash.ado",
        "../d/dash.ado",
        "../stata.trk",
        "../j/jsonio.jar",
        "../../../../etc/passwd.scheme",
        "./../j/jsonio.ado",
    ])
    def test_a_traversal_out_of_the_install_is_refused(self, installed, attempt):
        """INST-04. Every one of these is refused today; it must stay refused.

        These are the exact strings that the over-broad patch -- the one that
        appends the install root and its letter directories to ``allowed`` --
        was measured to make readable.
        """
        module, _root, _cwd = installed
        with pytest.raises(ValueError):
            module.SchemeParser._resolve_path(
                module.SchemeParser.__new__(module.SchemeParser), attempt)

    def test_a_cwd_symlink_named_after_a_builtin_cannot_reach_the_install(
            self, installed):
        """INST-05. The BUG-51 contract, in the layout that can break it.

        ``test_scheme.py``'s symlink tests use a name that is not one of the
        fourteen and run where the installed lookup is inert, so they pass
        whether or not this holds.  Here the name IS a built-in and the tree
        IS an install, which is the only combination that can regress.

        WP-30 P1.25b: a shipped name never consults the working directory
        (twoway's BASE comes first), so the link is never opened at all and
        the install's own file is what resolves.
        """
        module, root, cwd = installed
        target = os.path.join(root, "d", "someone_elses_secret.scheme")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("color background #123456\n")
        link = os.path.join(cwd, "s2color.scheme")
        os.symlink(target, link)

        import builtins
        opened = []
        real_open = builtins.open

        def spy(path, *a, **k):
            opened.append(os.path.realpath(str(path)))
            return real_open(path, *a, **k)

        inst = module.SchemeParser.__new__(module.SchemeParser)
        with mock.patch.object(module, "open", spy, create=True):
            got = inst._resolve_path("s2color.scheme")
            module.SchemeParser("s2color.scheme")
        assert os.path.realpath(got) == os.path.realpath(
            os.path.join(root, "d", "dash-s2color.scheme"))
        assert os.path.realpath(target) not in opened, opened

    def test_a_file_planted_in_the_letter_directory_is_not_reachable(
            self, installed):
        """INST-06. Only the fourteen names may be looked up there.

        The letter directory is shared: every package whose name starts with
        the same letter installs into it.  Resolution must be a function of
        the fourteen literals, never of an arbitrary caller string.
        """
        module, root, _cwd = installed
        planted = os.path.join(root, "d", "planted.scheme")
        with open(planted, "w", encoding="utf-8") as fh:
            fh.write("color background #abcdef\n")
        inst = module.SchemeParser.__new__(module.SchemeParser)
        with pytest.raises(ValueError):
            inst._resolve_path("planted.scheme")
        with pytest.raises(ValueError):
            inst._resolve_path("planted")

    def test_a_symlinked_scheme_in_the_install_is_still_refused(self, installed):
        """INST-07. The realpath check must stay load-bearing on the new path.

        A writable ``PLUS/s`` must not become a pivot to a file outside it.
        """
        module, root, _cwd = installed
        outside = os.path.join(os.path.dirname(root), "outside.txt")
        with open(outside, "w", encoding="utf-8") as fh:
            fh.write("not a scheme\n")
        shipped = os.path.join(root, "d", "dash-s2color.scheme")
        os.remove(shipped)
        os.symlink(outside, shipped)

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            scheme = module.SchemeParser.resolve_or_fallback("s2color", "a test")
        assert scheme.is_fallback is True, (
            "a scheme file symlinked out of the install was READ; the "
            "realpath check is no longer applied to the installed candidate"
        )
        # Said in so many words.  The fallback's own two warnings say the
        # scheme was "not found", which is false -- the file is there and
        # points elsewhere -- so a count of warnings passed with the
        # tampering message deleted (WP-24).
        text = " ".join(str(w.message) for w in caught)
        assert "resolves outside" in text and "was not read" in text, (
            "a tampered install is not reported as tampered: %s" % text
        )

    def test_the_cwd_still_wins_over_the_install(self, installed):
        """INST-08. WP-30 P1.25b: the shipped file wins over a working-
        directory file of the same name, as twoway's BASE wins (research
        t1/t3, M7, P1.25.3); the node keeps its name (flipped in place).
        """
        module, root, cwd = installed
        mine = os.path.join(cwd, "s2color.scheme")
        with open(mine, "w", encoding="utf-8") as fh:
            fh.write("color background #0f0f0f\n")
        inst = module.SchemeParser.__new__(module.SchemeParser)
        assert os.path.realpath(inst._resolve_path("s2color")) == \
            os.path.realpath(os.path.join(root, "d", "dash-s2color.scheme"))

    def test_a_missing_install_still_reports_the_truth(self, tmp_path,
                                                       monkeypatch):
        """INST-09. Deleting the shipped files must still warn, not pretend."""
        root = _build_installed_tree(str(tmp_path / "plus"))
        for name, letter in INSTALLED_SCHEMES.items():
            os.remove(os.path.join(root, letter, _shipped(name)))
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        mod_name, module = load_staged_render(os.path.join(root, "py"))
        try:
            is_fallback, _n, n_warn = _resolve(module, "stcolor")
            assert is_fallback is True
            assert n_warn >= 1
        finally:
            sys.modules.pop(mod_name, None)


# ==========================================================================
# INST-10..13 — the mechanism is inert wherever it is not an install
# ==========================================================================

class TestTheInstalledLookupIsInertOutsideAnInstall:

    def test_the_repo_layout_is_unaffected(self):
        """INST-10. The dev tree resolves from schemes/ and must not change."""
        import dash_render as dr
        assert dr.SchemeParser._PLUS_ROOT is None, (
            "the repo's dash_render.py is not under a py/ directory, so the "
            "installed lookup must be switched off entirely here"
        )
        scheme = dr.SchemeParser("stcolor")
        assert scheme.is_fallback is False and scheme.name == "stcolor"

    def test_a_loose_copy_does_not_open_its_parent_directory(self, tmp_path,
                                                             monkeypatch):
        """INST-11. dash_render.py copied somewhere ordinary.

        ``dirname(dirname(__file__))`` is then an unrelated directory -- a
        home directory, a Downloads folder.  Measured against the over-broad
        patch: from ``~/Downloads/dash_render.py`` the ENTIRE home tree passed
        the containment check, including files that are not schemes at all.
        The guard is that the lookup only arms when the file's own directory
        is named ``py``.
        """
        home = tmp_path / "fakehome"
        (home / "Downloads").mkdir(parents=True)
        (home / "Documents").mkdir()
        secret = home / "Documents" / "private.scheme"
        secret.write_text("color background #ff0000\n", encoding="utf-8")
        shutil.copy2(os.path.join(REPO_ROOT, "dash_render.py"),
                     str(home / "Downloads" / "dash_render.py"))
        elsewhere = tmp_path / "nowhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)

        mod_name, module = load_staged_render(str(home / "Downloads"))
        try:
            assert module.SchemeParser._PLUS_ROOT is None
            inst = module.SchemeParser.__new__(module.SchemeParser)
            with pytest.raises(ValueError):
                inst._resolve_path("../Documents/private.scheme")
        finally:
            sys.modules.pop(mod_name, None)

    def test_the_letter_directory_is_only_computed_for_shipped_names(
            self, installed):
        """INST-12. The narrowing itself, asserted directly."""
        module, root, _cwd = installed
        parser = module.SchemeParser
        assert parser._PLUS_ROOT == os.path.abspath(root)
        for name in INSTALLED_SCHEMES:
            assert parser._installed_letter_dir(name) == \
                os.path.join(os.path.abspath(root), INSTALLED_SCHEMES[name])
        for name in ("planted", "jsonio", "", "dash", "S2COLOR_NOT_SHIPPED"):
            assert parser._installed_letter_dir(name) is None, name

    @pytest.mark.parametrize("name", [
        "s/s2color", "../s/s2color", "s2color/../../etc/passwd",
        "/abs/s2color", "s2color/x",
    ])
    def test_a_name_carrying_a_separator_never_reaches_the_letter_directory(
            self, installed, name):
        """INST-13. No caller string may steer the join."""
        module, _root, _cwd = installed
        assert module.SchemeParser._installed_letter_dir(name) is None


# ==========================================================================
# INST-14..16 — what the user is told
# ==========================================================================

class TestTheDiagnosticsNameWhereItLooked:

    def test_the_last_resort_warning_names_the_install_directory(
            self, tmp_path, monkeypatch):
        """INST-14. A genuinely broken install must say where it looked.

        Before the fix the message named only ``PLUS/py/schemes`` and
        ``PLUS/py`` -- neither of which is where the files go -- so it pointed
        the user at the wrong place.
        """
        root = _build_installed_tree(str(tmp_path / "plus"))
        for name, letter in INSTALLED_SCHEMES.items():
            os.remove(os.path.join(root, letter, _shipped(name)))
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        monkeypatch.chdir(elsewhere)
        mod_name, module = load_staged_render(os.path.join(root, "py"))
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                module.SchemeParser.resolve_or_fallback("stcolor", "a test")
            text = " ".join(str(w.message) for w in caught)
            # The install root alone is not enough: PLUS/py is already in the
            # message and contains it as a prefix.  The message has to point
            # at the LETTER directories, which is where the files actually go.
            letter_dir = os.path.join(os.path.abspath(root), "<letter>")
            assert letter_dir in text, (
                "the 'searched ...' message names only %s, neither of which "
                "is where a net install puts a .scheme file, so it sends the "
                "user to the wrong directory. Message: %s"
                % (module.SchemeParser._SCHEME_SEARCH_DIRS, text)
            )
        finally:
            sys.modules.pop(mod_name, None)

    def test_a_file_reference_is_still_honoured_on_an_installed_tree(
            self, installed):
        """INST-15. scheme(mytheme.scheme) from the working directory."""
        module, _root, cwd = installed
        mine = os.path.join(cwd, "mytheme.scheme")
        with open(mine, "w", encoding="utf-8") as fh:
            fh.write("color background #010203\n")
        inst = module.SchemeParser.__new__(module.SchemeParser)
        assert os.path.realpath(inst._resolve_path("mytheme.scheme")) == \
            os.path.realpath(mine)

    def test_an_unknown_name_still_fails_with_the_list_of_built_ins(
            self, installed):
        """INST-16. The not-found message must not regress."""
        module, _root, _cwd = installed
        inst = module.SchemeParser.__new__(module.SchemeParser)
        with pytest.raises(ValueError, match="Built-in schemes"):
            inst._resolve_path("nosuchscheme")


# ==========================================================================
# INST-18 -- the decision GAPS B3 was closed by is written where users read
# ==========================================================================

class TestTheHelpStatesTheInstalledLayout:

    def test_the_help_says_where_an_install_puts_them_and_why_they_are_named_so(
            self):
        """INST-18. TR-05.7 closed B3 as a documented limitation: the plain
        ``<name>.scheme`` names are kept, deliberately, and the clash with
        another package's bare ``<name>.scheme`` is accepted.  The
        documentation IS the deliverable, so it is held here.  Measured under
        WP-24: with either of the two paragraphs deleted from dash.sthlp,
        every help and tracking test passed.  Since WP-28 the files are
        ``dash-<name>.scheme`` in ``PLUS/d/`` and cannot clash, which the two
        paragraphs now state.  Whitespace is normalised
        because SMCL wraps the sentences over lines.
        """
        with open(os.path.join(REPO_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
            text = " ".join(fh.read().split())
        for phrase in (
            "{ul:Where the shipped schemes live after an install.}",
            "{cmd:dash_render.py} goes to {cmd:PLUS/py/}",
            "{cmd:PLUS/d/}",
            "{ul:Why they are named {cmd:dash-}{it:name}{cmd:.scheme}.}",
            "cannot collide with Stata's own {cmd:scheme-}{it:name}{cmd:.scheme} files",
            "{cmd:set scheme} {it:name} finds Stata's own {cmd:scheme-}{it:name}{cmd:.scheme} in {cmd:BASE} first, so it never reads them",
            "you name each by Stata's own name, {cmd:scheme(s2color)}",
        ):
            assert phrase in text, (
                "dash.sthlp no longer states %r; GAPS B3 was closed by "
                "documenting it" % (phrase,)
            )


def test_the_help_never_offers_set_scheme_dash():
    """`set scheme <name>' tries scheme-<name>.scheme first, so the shipped
    dash-<name>.scheme files are not Stata schemes by that name, and the
    help must not say `set scheme dash-<name>' works."""
    with open(os.path.join(REPO_ROOT, "dash.sthlp"), encoding="utf-8") as fh:
        text = " ".join(fh.read().split())
    assert "set scheme dash-" not in text
    assert "{cmd:set scheme dash-}" not in text
