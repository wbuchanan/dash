"""test_readme.py -- the repository's README, dash.pkg's author and keyword
lines, and help dash's Installation, Author and Jump To (WP-31 I2).

GAPS3 I2 (re-read at 6370ca4): there was no README, dash.pkg had no
``d Author:`` or ``d KW:`` line, help dash gave no ``net install`` line, its
last section was ``{marker author}`` titled "Also see" and named no one, and
its Jump To list named 19 of its titled sections.  These tests hold:

* README.md gives one ``net install`` line, and its ``from()`` is the
  package's GitHub host (INSTALL_URL; no Makefile target or script names an
  install URL, so the constant is the one source -- ratification item 2 of
  WP-31 section 59), and help dash gives the same line;
* README.md states dash.pkg's ``Requires:`` lines word for word;
* dash.pkg carries ``d Author:`` and four ``d KW:`` lines;
* help dash has an Installation section, an Author section naming the
  author, and a separate Also see section;
* every ``{marker}`` followed by a ``{title:}`` is in the Jump To list.
"""
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)

#: The net install source (WP-31 D-59.a; ratification item 2): the raw tree
#: of the GitHub repository's main branch, which holds stata.toc and
#: dash.pkg at its root.
INSTALL_URL = "https://wbuchanan.github.io/dash"
#: The maintainer's support address and issue tracker (maintainer, 18oct2026).
SUPPORT_EMAIL = "william@williambuchanan.net"
ISSUES_URL = "https://github.com/wbuchanan/dash"

_NET_INSTALL = re.compile(r'net install dash, from\("([^"]+)"\)')


def _read(name):
    with open(os.path.join(_ROOT, name), encoding="utf-8") as fh:
        return fh.read()


def _pkg_d_lines():
    return [l[2:] for l in _read("dash.pkg").splitlines() if l.startswith("d ")]


def test_the_install_line_names_the_toc_host():
    readme = _read("README.md")
    fences = re.findall(r"```[a-z]*\n(.*?)```", readme, re.S)
    urls = [u for block in fences for u in _NET_INSTALL.findall(block)]
    assert urls, "README.md gives no net install line in a fenced block"
    assert set(urls) == {INSTALL_URL}, urls
    # the host serves the package: stata.toc and dash.pkg sit at the root
    # of the tree the URL names, and the toc lists dash.pkg.
    assert re.search(r"^p dash dash\.pkg\b", _read("stata.toc"), re.M)
    assert set(_NET_INSTALL.findall(_read("dash.sthlp"))) == {INSTALL_URL}


def test_requirements_match_dash_pkg():
    readme = " ".join(_read("README.md").split())
    reqs = [l for l in _pkg_d_lines() if l.startswith("Requires:")]
    assert len(reqs) == 2, reqs
    # dash.pkg's measured-on line follows the Stata requirement.
    stata = _pkg_d_lines()[_pkg_d_lines().index(reqs[0]) + 1]
    for line in reqs + [stata]:
        text = " ".join(line[len("Requires:"):].split()) \
            if line.startswith("Requires:") else " ".join(line.split())
        assert text in readme, "README.md does not state: " + text


def test_dash_pkg_has_author_and_kw():
    d = _pkg_d_lines()
    assert d.count("Author: Billy Buchanan") == 1, d
    kws = [l[len("KW: "):] for l in d if l.startswith("KW: ")]
    assert kws == ["twoway", "dashboard", "bokeh", "interactive graphics"]
    # the maintainer's support address (ratified 18oct2026)
    assert [l for l in d if l.startswith("Support:")] == [
        "Support: " + SUPPORT_EMAIL], d
    dist = d.index(next(l for l in d if l.startswith("Distribution-Date:")))
    assert d[dist + 1] == "Author: Billy Buchanan"


def test_help_has_an_author_and_an_install_paragraph():
    h = _read("dash.sthlp")
    assert h.count("{title:Author}") == 1
    assert h.count("{title:Also see}") == 1
    assert re.search(r"\{marker author\}\n\{title:Author\}\n\n\{pstd\}\n?"
                     r"Billy Buchanan", h), "no Author section naming the author"
    assert re.search(r"\{marker alsosee\}\n\{title:Also see\}\n\n\{psee\}\n"
                     r"\{helpb dash_setup\}, \{helpb twoway\}, \{helpb python\}",
                     h), "the Also see section lost its psee lines"
    m = re.search(r"\{marker install\}\n\{title:Installation\}\n(.*?)\n\{marker ",
                  h, re.S)
    assert m, "no Installation section"
    body = m.group(1)
    # written without the dot prompt: shown, not run, by the help-example
    # suite (test_help_examples.cscript pins both as "install")
    assert "{phang2}{cmd:net install dash, from(\"%s\")}{p_end}" \
        % INSTALL_URL in body
    assert "{phang2}{cmd:dash_setup}{p_end}" in body
    # after Description, before Plot types
    assert h.index("{marker description}") < h.index("{marker install}") \
        < h.index("{marker plottypes}")


def _titled_markers(h):
    out = []
    lines = h.split("\n")
    for i, line in enumerate(lines):
        for m in re.finditer(r"\{marker ([A-Za-z0-9_]+)\}", line):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            t = re.match(r"\{title:([^}]*)\}", nxt)
            if t:
                out.append((m.group(1), t.group(1)))
    return out


def test_every_help_title_is_in_the_jump_list():
    h = _read("dash.sthlp")
    jumps = re.findall(r'\{viewerjumpto "([^"]+)"\s+"dash##([^"]+)"\}', h)
    targets = [t for _, t in jumps]
    titled = _titled_markers(h)
    missing = [m for m, _ in titled if m not in targets]
    assert not missing, "titled sections absent from Jump To: " + ", ".join(missing)
    # one entry each, in the file's order
    assert len(set(targets)) == len(targets)
    order = [m for m, _ in titled]
    assert [t for t in targets if t in order] == order
    # every jump lands on a marker
    markers = set(re.findall(r"\{marker ([A-Za-z0-9_]+)\}", h))
    assert not [t for t in targets if t not in markers]


def test_help_and_readme_say_where_to_file_an_issue():
    """The help's Author section and the README name the support address
    and say to file an issue at the repository (maintainer, 18oct2026)."""
    h = _read("dash.sthlp")
    m = re.search(r"\{marker author\}\n\{title:Author\}\n(.*?)\n\{marker ",
                  h, re.S)
    assert m, "no Author section"
    body = m.group(1)
    assert SUPPORT_EMAIL in body, body
    assert ISSUES_URL in body and "issue" in body.lower(), body
    readme = _read("README.md")
    assert SUPPORT_EMAIL in readme and ISSUES_URL in readme
