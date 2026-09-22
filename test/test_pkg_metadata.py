"""``dash.pkg`` must carry the metadata Stata's update machinery reads.

What ``adoupdate`` actually compares
------------------------------------
Only the ``d Distribution-Date:`` line.  StataCorp's own documentation is the
authority -- ``/Applications/StataNow/ado/base/u/usersite.sthlp``, "[R] net --
Creating your own site" -- and it is confirmed by what ``net install`` writes:
the ``v`` line is **not** copied into ``stata.trk`` at all, so it cannot take
part in an update comparison.  ``dash.pkg`` has no ``Distribution-Date`` line,
so ``adoupdate`` has nothing to compare and can never report a new release.

This corrects two things ``GAPS.md`` B4 and ``ROADMAP.md`` TR-05.6 got wrong,
both of which were read rather than measured:

* "add ``v 2``".  ``v`` is the **file-format** version of the manifest, not the
  package's version, and it is the same field as ``stata.toc``'s ``v 3``.  The
  maximum Stata accepts is 3; ``v 4`` is ``r(610)``.  Writing ``v 2`` would
  declare an older format, not version 2 of dash.
* "no ``v`` line **and** no ``Distribution-Date`` line" as joint causes of the
  ``adoupdate`` failure.  The ``v`` line has no bearing on ``adoupdate``
  whatsoever.  It is carried here as StataCorp conformance (usersite.sthlp
  says "specify ``v 3``"), and it is asserted separately so the two reasons
  are not conflated again.

The version strings
-------------------
Seven shipped files declared two different versions -- ``dash.ado`` and
``dash_parse.mata`` said ``2.0  27mar2026`` while ``dash.pkg``,
``dash_setup.ado``, ``dash.sthlp`` and ``dash_setup.sthlp`` said
``1.0.0  25mar2026``.  The manifest's is the one a user sees from ``net
describe`` and ``ado describe``, so an installed dash reported 1.0.0 while its
code was 2.0.

Tests: PKG-01 through PKG-08.
"""
from __future__ import annotations

import os
import re

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG_FILE = os.path.join(REPO_ROOT, "dash.pkg")
TOC_FILE = os.path.join(REPO_ROOT, "stata.toc")

#: Every file that states the package version, and the pattern that finds it.
#: The `.sthlp` files use SMCL's own comment form.
VERSION_SOURCES = {
    "dash.ado":          r"^\*!\s*Version:\s*(\S+)\s+(\S+)\s*$",
    "dash_parse.mata":   r"^\*!\s*Version:\s*(\S+)\s+(\S+)\s*$",
    "dash_setup.ado":    r"^\*!\s*Version:\s*(\S+)\s+(\S+)\s*$",
    "dash.pkg":          r"^d Version:\s*(\S+)\s+(\S+)\s*$",
    # `\S+` for the date would run past the closing brace and capture
    # "27mar2026}{..." -- exclude the brace explicitly.
    "dash.sthlp":        r"^\{\*\s*\*!\s*version\s+(\S+)\s+([^}\s]+)\}",
    "dash_setup.sthlp":  r"^\{\*\s*\*!\s*version\s+(\S+)\s+([^}\s]+)\}",
}


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _declared_version(filename):
    """Return ``(version, date)`` as declared in *filename*, or None."""
    pattern = re.compile(VERSION_SOURCES[filename], re.MULTILINE)
    match = pattern.search(_read(os.path.join(REPO_ROOT, filename)))
    return match.groups() if match else None


def _pkg_directives(letter):
    """Every ``<letter> ...`` line of dash.pkg, without the directive."""
    out = []
    for raw in _read(PKG_FILE).splitlines():
        parts = raw.split(None, 1)
        if len(parts) == 2 and parts[0] == letter:
            out.append(parts[1].strip())
    return out


# ==========================================================================
# PKG-01..03 — adoupdate can see a new release
# ==========================================================================

class TestTheManifestCanBeUpdated:

    def test_a_distribution_date_is_declared(self):
        """PKG-01. Without it adoupdate has nothing to compare."""
        dates = [d for d in _pkg_directives("d")
                 if d.startswith("Distribution-Date:")]
        assert len(dates) == 1, (
            "dash.pkg must carry exactly one 'd Distribution-Date:' line; "
            "found %d. adoupdate reads this line and nothing else to decide "
            "whether a package is out of date." % len(dates)
        )

    def test_the_distribution_date_is_eight_digits(self):
        """PKG-02. yyyymmdd is the format Stata parses."""
        date = [d for d in _pkg_directives("d")
                if d.startswith("Distribution-Date:")][0]
        value = date.split(":", 1)[1].strip()
        assert re.fullmatch(r"\d{8}", value), (
            "Distribution-Date must be yyyymmdd, got %r" % value
        )
        year = int(value[:4])
        month = int(value[4:6])
        day = int(value[6:])
        assert 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31, (
            "Distribution-Date %r is not a plausible date" % value
        )

    def test_the_distribution_date_matches_the_declared_version_date(self):
        """PKG-03. Two dates that drift are worse than one.

        ``d Version: 2.0  27mar2026`` and ``d Distribution-Date: 20260927``
        must describe the same day, or a user comparing them has to guess
        which is the release.
        """
        _version, human = _declared_version("dash.pkg")
        date = [d for d in _pkg_directives("d")
                if d.startswith("Distribution-Date:")][0]
        iso = date.split(":", 1)[1].strip()
        months = ["jan", "feb", "mar", "apr", "may", "jun",
                  "jul", "aug", "sep", "oct", "nov", "dec"]
        match = re.fullmatch(r"(\d{1,2})([a-z]{3})(\d{4})", human.lower())
        assert match, "d Version: date %r is not Stata's ddmonyyyy form" % human
        day, mon, year = match.groups()
        assert iso == "%s%02d%02d" % (year, months.index(mon) + 1, int(day)), (
            "Distribution-Date %s and 'd Version:' date %s are different days"
            % (iso, human)
        )


# ==========================================================================
# PKG-04..05 — the manifest declares its own file format
# ==========================================================================

class TestTheManifestFormatIsDeclared:

    def test_the_pkg_declares_a_format_version(self):
        """PKG-04. usersite.sthlp: "specify v 3".

        Asserted separately from PKG-01 on purpose: this is conformance, and
        it has NO effect on adoupdate.  Conflating the two is what GAPS B4
        did.
        """
        assert _pkg_directives("v") == ["3"], (
            "dash.pkg should declare 'v 3'; found %r" % (_pkg_directives("v"),)
        )

    def test_the_format_version_is_not_mistaken_for_the_package_version(self):
        """PKG-05. ``v`` is the file format, max 3; ``v 4`` is r(610).

        The package's own version lives on the ``d Version:`` line.  A future
        dash 4 that wrote ``v 4`` here would stop installing on every Stata.
        """
        for line in _pkg_directives("v"):
            head = line.split(".", 1)[0]
            assert head.isdigit() and int(head) <= 3, (
                "the v line is Stata's manifest FORMAT version and must be "
                "<= 3; %r would be rejected" % line
            )
        assert _pkg_directives("v") == _pkg_directives_toc("v"), (
            "dash.pkg and stata.toc declare different manifest formats"
        )


def _pkg_directives_toc(letter):
    out = []
    for raw in _read(TOC_FILE).splitlines():
        parts = raw.split(None, 1)
        if len(parts) == 2 and parts[0] == letter:
            out.append(parts[1].strip())
    return out


# ==========================================================================
# PKG-06..08 — one version, stated once per file
# ==========================================================================

class TestEveryShippedFileAgreesOnTheVersion:

    @pytest.mark.parametrize("filename", sorted(VERSION_SOURCES))
    def test_the_file_states_a_version(self, filename):
        """PKG-06."""
        assert _declared_version(filename) is not None, (
            "%s states no version; the pattern %r found nothing"
            % (filename, VERSION_SOURCES[filename])
        )

    def test_all_shipped_files_state_the_same_version(self):
        """PKG-07. Measured before the fix: 2.0/27mar2026 in two files,
        1.0.0/25mar2026 in four, including the manifest a user reads."""
        seen = {f: _declared_version(f) for f in VERSION_SOURCES}
        distinct = set(seen.values())
        assert len(distinct) == 1, (
            "shipped files disagree on the version: %s"
            % ", ".join("%s=%s %s" % (f, v[0], v[1]) for f, v in sorted(seen.items()))
        )

    def test_the_manifest_version_is_the_code_version(self):
        """PKG-08. The manifest's is what `ado describe` shows the user."""
        assert _declared_version("dash.pkg") == _declared_version("dash.ado"), (
            "dash.pkg says %s and dash.ado says %s, so an installed dash "
            "reports a version its own code does not"
            % (_declared_version("dash.pkg"), _declared_version("dash.ado"))
        )
