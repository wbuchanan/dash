"""Write the GitHub Pages site's pages: the landing page from README.md and
the user's guide from docs/guide.

    python3 scripts/pages_index.py <README.md> <index.html>
    python3 scripts/pages_index.py --guide <docs/guide> <guide/index.html>

.github/workflows/pages.yml runs both as it assembles the site, so the pages
are the README and guide of the commit CI passed on main.  The site holds
the Stata package at its root (the from() of net install), docs/gallery as
gallery/ and docs/guide/examples as guide/examples/.  The landing page leads
with a link to the gallery, then one to the guide.

Each page is read as the Markdown it uses: # headings, paragraphs, "- "
lists, fenced code, `code`, **bold**, [text](url), <url> and <address>
autolinks, raw HTML blocks, and the README's gallery block between
gallery.py's markers; the guide adds "@example <name> <height>" lines, each
drawing docs/guide/examples/<name>.do beside the live page it built (see
example_html).  Anything else is refused with the file and line it is on
(ValueError), so a page that cannot be shown fails the test suite
(test/test_pages_index.py, test/test_guide_examples.py) before it reaches a
deploy, instead of being published as literal text.

Paths are rewritten for the site (site_url): docs/gallery/ is gallery/, an
address on the Pages site is made relative, and any other relative link --
a file the site does not hold -- goes to that file on GitHub's main branch.

The pages run no script.  Each one's Content-Security-Policy allows only
images from the site itself and the one stylesheet, named by hash; the
guide may also frame pages of the site (its examples).  Standard library
only, Python 3.11 or later.
"""
import base64
import hashlib
import html
import os
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
GUIDE_CTA_TITLE = "Read the user's guide"
GUIDE_CTA_TEXT = ("KPI cards, filters, data tables, linked brushing and more, "
                  "each with a live example.")

_SCHEMES = ("https://", "http://", "mailto:")
_INLINE = re.compile(
    r"(?P<link>\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\))"
    r"|(?P<code>`(?P<ct>[^`]+)`)"
    r"|(?P<url><(?P<ut>https?://[^\s<>]+)>)"
    r"|(?P<mail><(?P<mt>[^@\s<>]+@[^@\s<>]+\.[A-Za-z]{2,})>)"
    r"|(?P<bold>\*\*(?P<bt>[^*]+)\*\*)")
_HEADING = re.compile(r"^(#{1,6}) (\S.*)$")
_HTML_START = re.compile(r"^<(?:!--|/?[A-Za-z][A-Za-z0-9-]*(?:[\s>/]|$))")
_EXAMPLE = re.compile(r"^@example ([a-z][a-z0-9-]*) (\d+)$")
_EXAMPLE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")
_EXAMPLE_TITLE = re.compile(r"^\* ([^:\n]+): ")
_REFUSED = (
    (re.compile(r"^\s"), "an indented line starts a block"),
    (re.compile(r"^>"), "a blockquote"),
    (re.compile(r"^\d+[.)]\s"), "a numbered list"),
    (re.compile(r"^[*+]\s"), "a list marked with * or +; use -"),
    (re.compile(r"^\|"), "a table"),
    (re.compile(r"^#"), "a heading needs a space after its #"),
    (re.compile(r"^(?:[-*_]\s*){3,}$"), "a thematic break"),
    (re.compile(r"^@"), "a line starting with @ that is not @example <name> <height>"),
)
_INTERRUPT = (
    (re.compile(r"^(?:=+|-+)\s*$"), "a setext heading"),
    (re.compile(r"^\|"), "a table"),
    (re.compile(r"^(?:[-*+]|\d+[.)])\s"), "a list must follow a blank line"),
    (re.compile(r"^>"), "a blockquote"),
    (re.compile(r"^@"), "an example must follow a blank line"),
)


def site_url(url, up=0):
    """*url* as a page *up* folders below the site's root links it (see the
    module text)."""
    climb = "../" * up
    if url.startswith("docs/gallery/"):
        return climb + "gallery/" + url[len("docs/gallery/"):]
    if url.startswith(PAGES_URL):
        return (climb + url[len(PAGES_URL):]) or "./"
    if url.startswith(_SCHEMES) or url.startswith("#"):
        return url
    if not url or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", url):
        raise ValueError("a link to %r, which the page does not follow" % url)
    return REPO_URL + "/blob/main/" + url


def _plain(text):
    """Literal text as HTML; a mark the page cannot show is refused."""
    if "`" in text:
        raise ValueError("a backtick that opens no code span")
    if "*" in text:
        raise ValueError("emphasis other than **bold**")
    return html.escape(text, quote=False)


def inline(text, up=0):
    """The HTML of one paragraph's (or item's or heading's) inline Markdown,
    for a page *up* folders below the site's root."""
    out, at = [], 0
    for m in _INLINE.finditer(text):
        before = text[at:m.start()]
        if m.group("link") and before.endswith("!"):
            raise ValueError("an image written in Markdown")
        out.append(_plain(before))
        if m.group("link"):
            out.append('<a href="%s">%s</a>' % (
                html.escape(site_url(m.group("lu"), up), quote=True),
                inline(m.group("lt"), up)))
        elif m.group("code"):
            out.append("<code>%s</code>" % html.escape(
                m.group("ct").replace("\n", " "), quote=False))
        elif m.group("url"):
            u = m.group("ut")
            out.append('<a href="%s">%s</a>' % (
                html.escape(site_url(u, up), quote=True), html.escape(u, quote=False)))
        elif m.group("mail"):
            a = m.group("mt")
            out.append('<a href="mailto:%s">%s</a>' % (
                html.escape(a, quote=True), html.escape(a, quote=False)))
        else:
            out.append("<strong>%s</strong>" % inline(m.group("bt"), up))
        at = m.end()
    out.append(_plain(text[at:]))
    return "".join(out)


def slug(text):
    """The id of a heading: lower case, each run of other characters a -."""
    return re.sub(r"[^a-z0-9_]+", "-", text.lower()).strip("-")


def _html_block(text, up=0):
    """A raw HTML block with its src and href rewritten for the site and
    each image loaded lazily."""
    def url(m):
        new = site_url(html.unescape(m.group(2)), up)
        return '%s="%s"' % (m.group(1), html.escape(new, quote=True))

    text = re.sub(r'\b(src|href)="([^"]*)"', url, text)
    return re.sub(r"<img\b(?![^>]*\bloading=)([^>]*?)\s*>",
                  r'<img\1 loading="lazy" decoding="async">', text)


def example_title(code):
    """An example do-file's title: its first line, "* <title>: ...", up to
    the colon."""
    m = _EXAMPLE_TITLE.match(code)
    if not m:
        raise ValueError('an example\'s first line is "* <title>: <what it shows>"')
    return m.group(1).strip()


def example_html(name, height, code):
    """One guide example: the do-file *code* above the page it built,
    framed *height* pixels tall, with links to the page and the do-file."""
    title = example_title(code)
    return "\n".join([
        '<figure class="example" id="example-%s">' % name,
        "<figcaption>Example: %s</figcaption>" % html.escape(title, quote=False),
        '<pre><code class="language-stata">%s</code></pre>'
        % html.escape(code.rstrip("\n"), quote=False),
        '<iframe src="examples/%s.html" title="Live example: %s" height="%d" '
        'loading="lazy"></iframe>' % (name, html.escape(title, quote=True), height),
        '<p class="example-links"><a href="examples/%s.html">Open this dashboard '
        'on its own</a> &middot; <a href="examples/%s.do" download>Download '
        "%s.do</a></p>" % (name, name, name),
        "</figure>"])


def read_examples(folder):
    """{name: do-file text} of every <name>.do in *folder*; a name that is
    not lower-case letters, digits and hyphens, or a do-file whose first
    line is not its title, is refused."""
    out = {}
    for f in sorted(os.listdir(folder)):
        if not f.endswith(".do"):
            continue
        name = f[:-3]
        with open(os.path.join(folder, f), encoding="utf-8") as fh:
            code = fh.read()
        try:
            if not _EXAMPLE_NAME.match(name):
                raise ValueError("a name of lower-case letters, digits and hyphens")
            example_title(code)
        except ValueError as e:
            raise ValueError("%s: %s" % (f, e)) from None
        out[name] = code
    return out


def render(md, first_line=1, examples=None, source="README.md", up=0):
    """[(kind, html)] of the page's blocks, in order; kind is h1..h6, p, ul,
    pre, html, pairs (the gallery block) or example.  *examples* is
    {name: do-file text} for a page that may draw them (the guide), *source*
    the file named in a refusal, *up* how many folders below the site's root
    the page is."""
    def fail(no, what):
        raise ValueError("%s line %d: %s" % (source, no, what))

    def inline_at(no, text):
        try:
            return inline(text, up)
        except ValueError as e:
            fail(no, str(e))

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
                fail(no, "the gallery block is not closed by " + END)
            inner = render("\n".join(lines[i + 1:end]), no + 1, examples, source, up)
            blocks.append(("pairs", '<div class="pairs">\n%s\n</div>'
                           % "\n".join(h for _, h in inner)))
            i = end + 1
            continue
        if line.startswith("@"):
            m = _EXAMPLE.match(line)
            if m and examples is None:
                fail(no, "an example belongs in the guide")
            if m:
                name, height = m.group(1), int(m.group(2))
                if name not in examples:
                    fail(no, "no example %s in the examples folder" % name)
                if not 100 <= height <= 3000:
                    fail(no, "an example's frame takes a height from 100 to 3000 pixels")
                blocks.append(("example", example_html(name, height, examples[name])))
                i += 1
                continue
        if line.startswith("```"):
            lang = line[3:].strip()
            try:
                end = lines.index("```", i + 1)
            except ValueError:
                fail(no, "a code fence that is not closed")
            body = html.escape("\n".join(lines[i + 1:end]), quote=False)
            cls = ' class="language-%s"' % html.escape(lang, quote=True) if lang else ""
            blocks.append(("pre", "<pre><code%s>%s</code></pre>" % (cls, body)))
            i = end + 1
            continue
        m = _HEADING.match(line)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            blocks.append(("h%d" % level, '<h%d id="%s">%s</h%d>'
                           % (level, slug(text), inline_at(no, text), level)))
            i += 1
            continue
        if _HTML_START.match(line) and not re.match(r"^<(?:https?://|[^@\s<>]+@)", line):
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            blocks.append(("html", _html_block("\n".join(lines[i:j]), up)))
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
                    fail(no, "a list item's next line is indented by two spaces")
                i += 1
            blocks.append(("ul", "<ul>\n%s\n</ul>" % "\n".join(
                "<li>%s</li>" % inline_at(n, "\n".join(it)) for n, it in items)))
            continue
        for pat, what in _REFUSED:
            if pat.match(line):
                fail(no, what)
        para = [line]
        i += 1
        while i < len(lines) and lines[i].strip():
            for pat, what in _INTERRUPT:
                if pat.match(lines[i]):
                    fail(first_line + i, what)
            if lines[i].startswith(("#", "```")):
                fail(first_line + i, "a heading or a fence must follow a blank line")
            para.append(lines[i])
            i += 1
        blocks.append(("p", "<p>%s</p>" % inline_at(no, "\n".join(para))))
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
.links a:hover,.links a:focus-visible,.links a[aria-current]{text-decoration:underline}
main{max-width:960px;margin:0 auto;padding:0 16px 48px}
.wide main,.wide .bar nav,.wide footer div{max-width:1100px}
.hero{padding:40px 0 32px;border-bottom:1px solid var(--line)}
h1{font-size:clamp(28px,5vw,40px);line-height:1.2;margin:0 0 16px}
.lead{font-size:18px}
.ctas{display:flex;flex-wrap:wrap;gap:16px;margin:28px 0 0}
.cta{display:block;flex:1 1 300px;max-width:560px;padding:20px 24px;
border-radius:12px;background:var(--accent);color:var(--accent-fg);text-decoration:none}
.cta.secondary{flex:0 1 380px;background:transparent;color:var(--accent);
border:2px solid var(--accent);padding:18px 22px}
.cta:hover{filter:brightness(1.08)}
.cta:focus-visible{outline:3px solid var(--fg);outline-offset:3px}
.cta-title{display:block;font-size:22px;font-weight:700}
.cta.secondary .cta-title{font-size:19px}
.cta-title::after{content:" \\2192"}
.cta-text{display:block;margin-top:4px;font-size:15px}
h2{font-size:24px;line-height:1.3;margin:40px 0 12px;padding-bottom:6px;
border-bottom:1px solid var(--line)}
h3{font-size:19px;line-height:1.3;margin:28px 0 8px}
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
.contents{margin:28px 0 0;padding:16px 20px;border:1px solid var(--line);
border-radius:10px;background:var(--panel)}
.contents p{margin:0 0 8px;font-weight:700}
.contents ol{margin:0;padding-left:22px;columns:2 280px;column-gap:40px}
.contents li{max-width:none;break-inside:avoid}
.example{margin:24px 0 36px}
.example figcaption{font-weight:700;margin:0 0 8px}
.example pre{margin:0 0 12px}
.example iframe{display:block;width:100%;border:1px solid var(--line);
border-radius:8px;background:#fff}
.example-links{margin:8px 0 0;font-size:14px}
@media (max-width:760px){.example iframe{height:85vh}}
footer{border-top:1px solid var(--line);color:var(--muted);font-size:14px}
footer div{max-width:960px;margin:0 auto;padding:16px}
"""


def _text_of(fragment):
    """The words of an HTML fragment, its tags dropped and spaces collapsed."""
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def _title_and_lead(blocks, source):
    """The page's # title and the paragraph after it, as HTML; refused when
    the page does not begin with both."""
    if len(blocks) < 2 or blocks[0][0] != "h1" or blocks[1][0] != "p":
        raise ValueError("%s: the page needs a # title and a paragraph after it" % source)
    return blocks[0][1], blocks[1][1][len("<p>"):-len("</p>")]


def _shell(title, lead, links, body, footer, wide=False, frames=False):
    """A whole page: its head and policy, the site's bar (*links* is
    [(href, text, current)], the first the brand), *body* in <main>, and
    *footer*'s text; a *wide* page's bar, main and footer are wider."""
    digest = base64.b64encode(hashlib.sha256(_CSS.encode()).digest()).decode()
    csp = ("default-src 'none'; img-src 'self'; %sstyle-src 'sha256-%s'; "
           "base-uri 'none'; form-action 'none'"
           % ("frame-src 'self'; " if frames else "", digest))
    head = [
        "<!DOCTYPE html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        '<meta http-equiv="Content-Security-Policy" content="%s">' % csp,
        "<title>%s</title>" % html.escape(_text_of(title), quote=False),
        '<meta name="description" content="%s">' % html.escape(_text_of(lead), quote=True),
        "<style>%s</style>" % _CSS, "</head>",
        '<body class="wide">' if wide else "<body>"]
    brand, rest = links[0], links[1:]
    bar = ['<header class="bar">', '<nav aria-label="Site">',
           '<a class="brand" href="%s">%s</a>' % brand[:2], '<span class="links">']
    bar += ['<a href="%s"%s>%s</a>' % (html.escape(u, quote=True),
                                       ' aria-current="page"' if cur else "", t)
            for u, t, cur in rest]
    bar += ["</span>", "</nav>", "</header>"]
    main = ["<main>"]
    foot =["</main>", "<footer><div>%s</div></footer>" % footer, "</body>", "</html>", ""]
    return "\n".join(head + bar + main + body + foot)


def _cta(href, title, text, secondary=False):
    return ('<a class="cta%s" href="%s"><span class="cta-title">%s</span>'
            '<span class="cta-text">%s</span></a>'
            % (" secondary" if secondary else "", href, html.escape(title, quote=False),
               html.escape(text, quote=False)))


def page(md):
    """The landing page: the README's title and first paragraph above the
    gallery link and the guide's, then the rest of the README."""
    blocks = render(md)
    title, lead = _title_and_lead(blocks, "README.md")
    ids = {re.search(r' id="([^"]+)"', h).group(1)
           for k, h in blocks[2:] if k == "h2"}
    links = [("./", "dash", False), ("gallery/", "Gallery", False), ("guide/", "Guide", False)]
    links += [("#" + i, t, False) for i, t in (("installation", "Install"),
                                              ("documentation", "Documentation"))
              if i in ids]
    links.append((REPO_URL, "GitHub", False))
    hero = ['<section class="hero">', title, '<p class="lead">%s</p>' % lead,
            '<div class="ctas">', _cta("gallery/", CTA_TITLE, CTA_TEXT),
            _cta("guide/", GUIDE_CTA_TITLE, GUIDE_CTA_TEXT, secondary=True),
            "</div>", "</section>"]
    footer = ("This page is the project's README.md. "
              '<a href="gallery/">Gallery</a> &middot; <a href="guide/">Guide</a> &middot; '
              '<a href="%s">Source and issues on GitHub</a>' % REPO_URL)
    return _shell(title, lead, links, hero + [h for _, h in blocks[2:]], footer)


def guide_page(md, examples):
    """The user's guide: its title and first paragraph, a list of its
    sections, then the guide with each @example drawn from *examples*
    ({name: do-file text}).  The page sits at guide/, one folder down."""
    blocks = render(md, examples=examples, source="guide.md", up=1)
    title, lead = _title_and_lead(blocks, "guide.md")
    rows = []
    for k, h in blocks[2:]:
        if k == "h2":
            m = re.match(r'<h2 id="([^"]+)">(.*)</h2>$', h)
            rows.append('<li><a href="#%s">%s</a></li>' % (m.group(1), m.group(2)))
    contents = ['<nav class="contents" aria-label="Contents">', "<p>Contents</p>", "<ol>",
                *rows, "</ol>", "</nav>"]
    hero = ['<section class="hero">', title, '<p class="lead">%s</p>' % lead,
            *contents, "</section>"]
    links = [("../", "dash", False), ("../gallery/", "Gallery", False),
             ("./", "Guide", True), (REPO_URL, "GitHub", False)]
    footer = ("This guide is docs/guide/guide.md; each example is the do-file shown "
              'beside it. <a href="../">Home</a> &middot; <a href="../gallery/">Gallery</a> '
              '&middot; <a href="%s">Source and issues on GitHub</a>' % REPO_URL)
    return _shell(title, lead, links, hero + [h for _, h in blocks[2:]], footer,
                  wide=True, frames=True)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    guide = bool(argv) and argv[0] == "--guide"
    args = argv[1:] if guide else argv
    if len(args) != 2:
        print("usage: pages_index.py <README.md> <index.html>\n"
              "       pages_index.py --guide <docs/guide> <guide/index.html>", file=sys.stderr)
        return 2
    try:
        if guide:
            with open(os.path.join(args[0], "guide.md"), encoding="utf-8") as fh:
                md = fh.read()
            text = guide_page(md, read_examples(os.path.join(args[0], "examples")))
        else:
            with open(args[0], encoding="utf-8") as fh:
                md = fh.read()
            text = page(md)
    except ValueError as e:
        print("pages_index: %s" % e, file=sys.stderr)
        return 1
    with open(args[1], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
