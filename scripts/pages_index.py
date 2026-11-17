"""Write the GitHub Pages landing page, index.html, from README.md.

    python3 scripts/pages_index.py <README.md> <index.html>

.github/workflows/pages.yml runs it as it assembles the site, so the page is
the README of the commit CI passed on main.  The site holds the Stata package
at its root (the from() of net install) and docs/gallery as gallery/; the
page leads with a link to the gallery.

The README is read as the Markdown it uses: # headings, paragraphs, "- "
lists, fenced code, `code`, **bold**, [text](url), <url> and <address>
autolinks, raw HTML blocks, and the gallery block between gallery.py's
markers.  Anything else is refused with the README line it is on
(ValueError), so a README the page cannot show fails the test suite
(test/test_pages_index.py) before it reaches a deploy, instead of being
published as literal text.

Paths are rewritten for the site (site_url): docs/gallery/ is gallery/, an
address on the Pages site is made relative, and any other relative link --
a file the site does not hold -- goes to that file on GitHub's main branch.

The page runs no script.  Its Content-Security-Policy allows only images
from the site itself and its one stylesheet, named by hash.  Standard
library only, Python 3.11 or later.
"""
import base64
import hashlib
import html
import re
import sys

REPO_URL = "https://github.com/wbuchanan/dash"
PAGES_URL = "https://wbuchanan.github.io/dash/"
#: scripts/corpus/gallery.py's README block markers (test_pages_index checks
#: they are the same).
START = "<!-- dash-gallery:start -->"
END = "<!-- dash-gallery:end -->"

CTA_TITLE = "Open the gallery"
CTA_TEXT = ("Stata's twoway graph beside the live dash graph for the same "
            "command, one page for each plot type.")

_SCHEMES = ("https://", "http://", "mailto:")
_INLINE = re.compile(
    r"(?P<link>\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\))"
    r"|(?P<code>`(?P<ct>[^`]+)`)"
    r"|(?P<url><(?P<ut>https?://[^\s<>]+)>)"
    r"|(?P<mail><(?P<mt>[^@\s<>]+@[^@\s<>]+\.[A-Za-z]{2,})>)"
    r"|(?P<bold>\*\*(?P<bt>[^*]+)\*\*)")
_HEADING = re.compile(r"^(#{1,6}) (\S.*)$")
_HTML_START = re.compile(r"^<(?:!--|/?[A-Za-z][A-Za-z0-9-]*(?:[\s>/]|$))")
_REFUSED = (
    (re.compile(r"^\s"), "an indented line starts a block"),
    (re.compile(r"^>"), "a blockquote"),
    (re.compile(r"^\d+[.)]\s"), "a numbered list"),
    (re.compile(r"^[*+]\s"), "a list marked with * or +; use -"),
    (re.compile(r"^\|"), "a table"),
    (re.compile(r"^#"), "a heading needs a space after its #"),
    (re.compile(r"^(?:[-*_]\s*){3,}$"), "a thematic break"),
)
_INTERRUPT = (
    (re.compile(r"^(?:=+|-+)\s*$"), "a setext heading"),
    (re.compile(r"^\|"), "a table"),
    (re.compile(r"^(?:[-*+]|\d+[.)])\s"), "a list must follow a blank line"),
    (re.compile(r"^>"), "a blockquote"),
)


def site_url(url):
    """*url* as the page on the Pages site links it (see the module text)."""
    if url.startswith("docs/gallery/"):
        return "gallery/" + url[len("docs/gallery/"):]
    if url.startswith(PAGES_URL):
        return url[len(PAGES_URL):] or "./"
    if url.startswith(_SCHEMES) or url.startswith("#"):
        return url
    if not url or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url):
        raise ValueError("a link to %r, which the page does not follow" % url)
    return REPO_URL + "/blob/main/" + url


def _plain(text):
    """Literal README text as HTML; a mark the page cannot show is refused."""
    if "`" in text:
        raise ValueError("a backtick that opens no code span")
    if "*" in text:
        raise ValueError("emphasis other than **bold**")
    return html.escape(text, quote=False)


def inline(text):
    """The HTML of one paragraph's (or item's or heading's) inline Markdown."""
    out, at = [], 0
    for m in _INLINE.finditer(text):
        before = text[at:m.start()]
        if m.group("link") and before.endswith("!"):
            raise ValueError("an image written in Markdown")
        out.append(_plain(before))
        if m.group("link"):
            out.append('<a href="%s">%s</a>' % (
                html.escape(site_url(m.group("lu")), quote=True),
                inline(m.group("lt"))))
        elif m.group("code"):
            out.append("<code>%s</code>" % html.escape(
                m.group("ct").replace("\n", " "), quote=False))
        elif m.group("url"):
            u = m.group("ut")
            out.append('<a href="%s">%s</a>' % (
                html.escape(site_url(u), quote=True), html.escape(u, quote=False)))
        elif m.group("mail"):
            a = m.group("mt")
            out.append('<a href="mailto:%s">%s</a>' % (
                html.escape(a, quote=True), html.escape(a, quote=False)))
        else:
            out.append("<strong>%s</strong>" % inline(m.group("bt")))
        at = m.end()
    out.append(_plain(text[at:]))
    return "".join(out)


def slug(text):
    """The id of a heading: lower case, each run of other characters a -."""
    return re.sub(r"[^a-z0-9_]+", "-", text.lower()).strip("-")


def _html_block(text):
    """A raw HTML block with its src and href rewritten for the site and
    each image loaded lazily."""
    def url(m):
        new = site_url(html.unescape(m.group(2)))
        return '%s="%s"' % (m.group(1), html.escape(new, quote=True))

    text = re.sub(r'\b(src|href)="([^"]*)"', url, text)
    return re.sub(r"<img\b(?![^>]*\bloading=)([^>]*?)\s*>",
                  r'<img\1 loading="lazy" decoding="async">', text)


def _fail(no, what):
    raise ValueError("README.md line %d: %s" % (no, what))


def _inline_at(no, text):
    """inline(text), a refusal naming README line *no*."""
    try:
        return inline(text)
    except ValueError as e:
        _fail(no, str(e))


def render(md, first_line=1):
    """[(kind, html)] of the README's blocks, in order; kind is h1..h6, p,
    ul, pre, html or pairs (the gallery block)."""
    lines = md.split("\n")
    blocks, i = [], 0
    while i < len(lines):
        line, no = lines[i], first_line + i
        if not line.strip():
            i += 1
            continue
        if line == START:
            try:
                end = lines.index(END, i + 1)
            except ValueError:
                _fail(no, "the gallery block is not closed by " + END)
            inner = render("\n".join(lines[i + 1:end]), no + 1)
            blocks.append(("pairs", '<div class="pairs">\n%s\n</div>'
                           % "\n".join(h for _, h in inner)))
            i = end + 1
            continue
        if line.startswith("```"):
            lang = line[3:].strip()
            try:
                end = lines.index("```", i + 1)
            except ValueError:
                _fail(no, "a code fence that is not closed")
            body = html.escape("\n".join(lines[i + 1:end]), quote=False)
            cls = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
            blocks.append(("pre", "<pre><code%s>%s</code></pre>" % (cls, body)))
            i = end + 1
            continue
        m = _HEADING.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            blocks.append(("h%d" % level, '<h%d id="%s">%s</h%d>'
                           % (level, slug(text), _inline_at(no, text), level)))
            i += 1
            continue
        if _HTML_START.match(line) and not re.match(r"^<(?:https?://|[^@\s<>]+@)", line):
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            blocks.append(("html", _html_block("\n".join(lines[i:j]))))
            i = j
            continue
        if line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip():
                cur, no = lines[i], first_line + i
                if cur.startswith("- "):
                    items.append((no, [cur[2:]]))
                elif cur.startswith("  ") and cur[2:3].strip():
                    items[-1][1].append(cur[2:])
                else:
                    _fail(no, "a list item's next line is indented by two spaces")
                i += 1
            blocks.append(("ul", "<ul>\n%s\n</ul>" % "\n".join(
                "<li>%s</li>" % _inline_at(n, "\n".join(it)) for n, it in items)))
            continue
        for pat, what in _REFUSED:
            if pat.match(line):
                _fail(no, what)
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip():
            for pat, what in _INTERRUPT:
                if pat.match(lines[i]):
                    _fail(first_line + i, what)
            if lines[i].startswith(("#", "```")):
                _fail(first_line + i, "a heading or a fence must follow a blank line")
            para.append(lines[i])
            i += 1
        blocks.append(("p", "<p>%s</p>" % _inline_at(no, "\n".join(para))))
    return blocks


_CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#59636e;--line:#d1d9e0;--panel:#f6f8fa;
--accent:#0b5cad;--accent-fg:#ffffff;--code:#eff2f5}
@media (prefers-color-scheme: dark){:root{--bg:#0d1117;--fg:#e6edf3;
--muted:#9198a1;--line:#30363d;--panel:#151b23;--accent:#4493f8;
--accent-fg:#0d1117;--code:#1f2630}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--fg);
font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.bar{background:var(--panel);border-bottom:1px solid var(--line)}
.bar nav{max-width:960px;margin:0 auto;padding:12px 16px;display:flex;
flex-wrap:wrap;gap:8px 24px;align-items:center;justify-content:space-between}
.brand{font-weight:700;font-size:18px;color:var(--fg);text-decoration:none}
.links{display:flex;flex-wrap:wrap;gap:4px 20px}
.links a{font-weight:500;text-decoration:none}
.links a:hover,.links a:focus-visible{text-decoration:underline}
main{max-width:960px;margin:0 auto;padding:0 16px 48px}
.hero{padding:40px 0 32px;border-bottom:1px solid var(--line)}
h1{font-size:clamp(28px,5vw,40px);line-height:1.2;margin:0 0 16px}
.lead{font-size:18px}
.cta{display:block;max-width:560px;margin:28px 0 0;padding:20px 24px;
border-radius:12px;background:var(--accent);color:var(--accent-fg);text-decoration:none}
.cta:hover{filter:brightness(1.08)}
.cta:focus-visible{outline:3px solid var(--fg);outline-offset:3px}
.cta-title{display:block;font-size:22px;font-weight:700}
.cta-title::after{content:" \\2192"}
.cta-text{display:block;margin-top:4px;font-size:15px}
h2{font-size:24px;line-height:1.3;margin:40px 0 12px;padding-bottom:6px;
border-bottom:1px solid var(--line)}
p,li{max-width:72ch}
code{font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
background:var(--code);padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
pre{background:var(--code);padding:14px 16px;border-radius:8px;overflow-x:auto}
pre code{padding:0;background:none;overflow-wrap:normal}
.pairs p{max-width:none;margin:0 0 32px}
.pairs img{width:49%;height:auto;vertical-align:top;background:#fff;
border:1px solid var(--line);border-radius:6px}
.pairs code{display:inline-block;margin:8px 0 2px;white-space:pre-wrap}
@media (max-width:640px){.pairs img{width:100%;margin-bottom:8px}}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px}
footer div{max-width:960px;margin:0 auto;padding:16px}
"""


def _text_of(fragment):
    """The words of an HTML fragment, its tags dropped and spaces collapsed."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def page(md):
    """The landing page: the README's title and first paragraph above the
    gallery link, then the rest of the README."""
    blocks = render(md)
    if len(blocks) < 2 or blocks[0][0] != "h1" or blocks[1][0] != "p":
        raise ValueError("README.md: the page needs a # title and a paragraph after it")
    title, lead = blocks[0][1], blocks[1][1][len("<p>"):-len("</p>")]
    ids = {re.search(r' id="([^"]+)"', h).group(1)
           for k, h in blocks[2:] if k == "h2"}
    nav = [("./", "dash", "brand"), ("gallery/", "Gallery", "")]
    nav += [("#" + i, t, "") for i, t in (("installation", "Install"),
                                         ("documentation", "Documentation"))
            if i in ids]
    nav.append((REPO_URL, "GitHub", ""))
    brand, links = nav[0], nav[1:]
    digest = base64.b64encode(hashlib.sha256(_CSS.encode()).digest()).decode()
    csp = ("default-src 'none'; img-src 'self'; style-src 'sha256-%s'; "
           "base-uri 'none'; form-action 'none'" % digest)
    head = [
        "<!DOCTYPE html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<meta http-equiv="Content-Security-Policy" content="%s">' % csp,
        "<title>%s</title>" % html.escape(_text_of(title), quote=False),
        '<meta name="description" content="%s">' % html.escape(_text_of(lead), quote=True),
        "<style>%s</style>" % _CSS, "</head>", "<body>"]
    bar = ['<header class="bar">', '<nav aria-label="Site">',
           '<a class="brand" href="%s">%s</a>' % brand[:2], '<span class="links">']
    bar += ['<a href="%s">%s</a>' % (html.escape(u, quote=True), t) for u, t, _ in links]
    bar += ["</span>", "</nav>", "</header>"]
    hero = ["<main>", '<section class="hero">', title, '<p class="lead">%s</p>' % lead,
            '<a class="cta" href="gallery/"><span class="cta-title">%s</span>'
            '<span class="cta-text">%s</span></a>'
            % (CTA_TITLE, html.escape(CTA_TEXT, quote=False)), "</section>"]
    body = [h for _, h in blocks[2:]]
    foot = ["</main>", "<footer><div>This page is the project's README.md. "
            '<a href="gallery/">Gallery</a> &middot; '
            '<a href="%s">Source and issues on GitHub</a></div></footer>' % REPO_URL,
            "</body>", "</html>", ""]
    return "\n".join(head + bar + hero + body + foot)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2:
        print("usage: pages_index.py <README.md> <index.html>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as fh:
        md = fh.read()
    try:
        text = page(md)
    except ValueError as e:
        print("pages_index: %s" % e, file=sys.stderr)
        return 1
    with open(argv[1], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
