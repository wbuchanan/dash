"""test_pages_index.py -- scripts/pages_index.py, which writes the GitHub
Pages landing page (index.html) from README.md (17nov2026).

The site (.github/workflows/pages.yml) holds the Stata package at its root
and docs/gallery as gallery/.  The page is the README, read as the Markdown
it uses, with its paths rewritten for the site, a link to the gallery
before anything else, and no script.  A README construct the page cannot
show is refused here, before it reaches a deploy.
"""
import base64
import hashlib
import os
import re
import subprocess
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from scripts import pages_index as pi  # noqa: E402
from scripts.corpus import gallery  # noqa: E402

_README = os.path.join(_ROOT, "README.md")
_BLOB = "https://github.com/wbuchanan/dash/blob/main/"


def _readme():
    with open(_README, encoding="utf-8") as fh:
        return fh.read()


def _git_ls(path):
    out = subprocess.run(["git", "ls-files", path], cwd=_ROOT,
                         capture_output=True, text=True, check=True).stdout
    return set(out.split())


# ---- site_url ---------------------------------------------------------------

@pytest.mark.parametrize("url, want", [
    ("docs/gallery/index.html", "gallery/index.html"),
    ("docs/gallery/svg/a-dash.svg", "gallery/svg/a-dash.svg"),
    ("https://wbuchanan.github.io/dash/gallery/", "gallery/"),
    ("https://wbuchanan.github.io/dash/gallery/bar.html", "gallery/bar.html"),
    ("https://wbuchanan.github.io/dash/", "./"),
    ("https://wbuchanan.github.io/dash/dash.pkg", "dash.pkg"),
    ("CHANGELOG.md", _BLOB + "CHANGELOG.md"),
    ("docs/other.md", _BLOB + "docs/other.md"),
    ("https://github.com/wbuchanan/dash", "https://github.com/wbuchanan/dash"),
    ("http://example.org/x", "http://example.org/x"),
    ("mailto:someone@example.org", "mailto:someone@example.org"),
    ("#installation", "#installation"),
])
def test_site_url_rewrites_paths_for_the_site(url, want):
    assert pi.site_url(url) == want


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,x",
                                 "JavaScript:x", "vbscript:x", ""])
def test_site_url_refuses_other_schemes(url):
    with pytest.raises(ValueError):
        pi.site_url(url)


# ---- inline -----------------------------------------------------------------

@pytest.mark.parametrize("text, want", [
    ("plain -- text", "plain -- text"),
    ("a < b & c > d", "a &lt; b &amp; c &gt; d"),
    ("run `help dash` now", "run <code>help dash</code> now"),
    ("`<b>&`", "<code>&lt;b&gt;&amp;</code>"),
    ("**Close**: margins", "<strong>Close</strong>: margins"),
    ("see [CHANGELOG.md](CHANGELOG.md) here",
     'see <a href="%sCHANGELOG.md">CHANGELOG.md</a> here' % _BLOB),
    ("[`x`](docs/gallery/index.html)",
     '<a href="gallery/index.html"><code>x</code></a>'),
    ("at <https://github.com/wbuchanan/dash> (the Issues tab)",
     'at <a href="https://github.com/wbuchanan/dash">'
     "https://github.com/wbuchanan/dash</a> (the Issues tab)"),
    ("at <someone@example.org>",
     'at <a href="mailto:someone@example.org">someone@example.org</a>'),
    ("dash_setup and bokeh>=3.8,<3.10", "dash_setup and bokeh&gt;=3.8,&lt;3.10"),
])
def test_inline_renders_the_readmes_inline_markdown(text, want):
    assert pi.inline(text) == want


@pytest.mark.parametrize("text", ["an ![image](a.png) here", "one *star* here",
                                  "a lone ` tick"])
def test_inline_refuses_what_it_cannot_show(text):
    with pytest.raises(ValueError):
        pi.inline(text)


# ---- slug -------------------------------------------------------------------

@pytest.mark.parametrize("text, want", [
    ("Installation", "installation"), ("dash_setup", "dash_setup"),
    ("Requirements & more", "requirements-more"), ("  A  b ", "a-b")])
def test_slug_names_a_heading(text, want):
    assert pi.slug(text) == want


# ---- render -----------------------------------------------------------------

def test_render_draws_each_block_the_readme_uses():
    md = "\n".join([
        "# Title here", "", "Lead `x` line", "goes on.", "", "## Two words", "",
        "- one", "  more of one;", "- two", "", "```stata", 'sysuse "a" <b>', "```",
        "", "<p><img src=\"docs/gallery/svg/a.svg\" alt=\"a &amp; b\"></p>", "",
        "Last."])
    blocks = pi.render(md)
    assert blocks == [
        ("h1", '<h1 id="title-here">Title here</h1>'),
        ("p", "<p>Lead <code>x</code> line\ngoes on.</p>"),
        ("h2", '<h2 id="two-words">Two words</h2>'),
        ("ul", "<ul>\n<li>one\nmore of one;</li>\n<li>two</li>\n</ul>"),
        ("pre", '<pre><code class="language-stata">sysuse "a" '
                "&lt;b&gt;</code></pre>"),
        ("html", '<p><img src="gallery/svg/a.svg" alt="a &amp; b" '
                 'loading="lazy" decoding="async"></p>'),
        ("p", "<p>Last.</p>"),
    ]


def test_render_puts_the_gallery_block_in_its_own_division():
    md = "\n".join(["## Gallery", "", gallery.START, "Drawn on a day.", "",
                    '<p><img src="docs/gallery/svg/a.svg" alt="a"></p>', "",
                    "More: [x](https://wbuchanan.github.io/dash/gallery/).",
                    gallery.END, "", "## Next"])
    kinds = [k for k, _ in pi.render(md)]
    assert kinds == ["h2", "pairs", "h2"]
    pairs = dict(pi.render(md))["pairs"]
    assert pairs.startswith('<div class="pairs">\n<p>Drawn on a day.</p>')
    assert '<a href="gallery/">x</a>' in pairs and pairs.endswith("</div>")
    assert "dash-gallery" not in pairs


@pytest.mark.parametrize("md", [
    "| a | b |\n|---|---|",                # a table
    "> quoted",                           # a blockquote
    "1. first",                           # a numbered list
    "* star item",                        # another list marker
    "    indented code",                  # an indented code block
    "Title\n=====",                       # a setext heading
    "```stata\nnever closed",             # an unterminated fence
    "#No space",                          # not an ATX heading
    gallery.START + "\nno end",           # a gallery block left open
])
def test_render_refuses_a_construct_it_cannot_show(md):
    with pytest.raises(ValueError, match="README.md line"):
        pi.render(md)


# ---- page -------------------------------------------------------------------

_MD = "\n".join(["# dash: a title", "", "The lead.", "", "Body text.", "",
                 "## Installation", "", "```stata", "net install dash", "```",
                 "", "## Documentation", "", "- `help dash`"])


def test_page_leads_with_the_gallery_and_runs_no_script():
    page = pi.page(_MD)
    assert page.startswith("<!DOCTYPE html>\n<html lang=\"en\">")
    assert "<title>dash: a title</title>" in page
    assert '<meta name="description" content="The lead.">' in page
    assert "<script" not in page.lower()
    hero = page.split('<section class="hero">', 1)[1].split("</section>", 1)[0]
    assert "<h1" in hero and '<p class="lead">The lead.</p>' in hero
    assert '<a class="cta" href="gallery/">' in hero
    # The gallery link comes before every section of the README.
    assert page.index('class="cta" href="gallery/"') < page.index("<h2")
    nav = page.split('<nav aria-label="Site">', 1)[1].split("</nav>", 1)[0]
    assert re.findall(r'href="([^"]+)"', nav) == [
        "./", "gallery/", "#installation", "#documentation",
        "https://github.com/wbuchanan/dash"]
    assert "Body text." in page and "The lead." not in page.split("</section>", 1)[1]


def test_page_policy_names_its_one_stylesheet_by_hash():
    page = pi.page(_MD)
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">',
                    page).group(1)
    styles = re.findall(r"<style>(.*?)</style>", page, re.S)
    assert len(styles) == 1
    digest = base64.b64encode(hashlib.sha256(styles[0].encode()).digest()).decode()
    assert csp == ("default-src 'none'; img-src 'self'; style-src 'sha256-%s'; "
                   "base-uri 'none'; form-action 'none'" % digest)
    assert " style=" not in page


def test_page_refuses_a_readme_without_a_title_and_lead():
    for md in ("Just text.", "# Title only", "# Title\n\n## Section"):
        with pytest.raises(ValueError):
            pi.page(md)


# ---- main -------------------------------------------------------------------

def test_main_writes_the_page_and_says_why_it_cannot(tmp_path, capsys):
    src, out = tmp_path / "README.md", tmp_path / "site" / "index.html"
    src.write_text(_MD, encoding="utf-8")
    out.parent.mkdir()
    assert pi.main([str(src), str(out)]) == 0
    assert out.read_text(encoding="utf-8") == pi.page(_MD)
    src.write_text("# T\n\nLead.\n\n> quoted\n", encoding="utf-8")
    assert pi.main([str(src), str(out)]) == 1
    assert "README.md line 5" in capsys.readouterr().err
    assert pi.main([str(src)]) == 2


# ---- the README itself ------------------------------------------------------

def test_the_readme_builds_a_page_for_the_site():
    """The README on this commit is the page the next deploy publishes: it
    builds, keeps every section, and points only at what the site holds
    or at absolute addresses."""
    readme = _readme()
    page = pi.page(readme)
    for h2 in re.findall(r"^## (.+)$", readme, re.M):
        assert '<h2 id="%s">' % pi.slug(h2) in page, h2
    assert "docs/gallery/" not in page
    tracked = _git_ls("docs/gallery")
    images = re.findall(r'<img src="([^"]+)"', page)
    assert images
    for src in images:
        assert src.startswith("gallery/svg/"), src
        assert "docs/" + src in tracked, src
    for href in re.findall(r'href="([^"]+)"', page):
        if href.startswith("gallery/") and href != "gallery/":
            assert "docs/" + href in tracked, href
        elif href.startswith("#"):
            assert 'id="%s"' % href[1:] in page, href
        else:
            assert (href in ("./", "gallery/")
                    or href.startswith(("https://", "mailto:"))), href


def test_the_markers_are_gallery_pys():
    assert (pi.START, pi.END) == (gallery.START, gallery.END)
