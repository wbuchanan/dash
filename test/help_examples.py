"""help_examples -- the example commands of dash's help files, as the help shows them.

GAPS.md F5 once ran every numbered example in ``dash.sthlp`` by hand.  Nothing
ran them afterwards, so an example could rot without a word.  This module is
the one reading of the help that both suites use:

* ``test/test_help_examples.cscript`` calls :func:`stata_plan` through
  ``python:`` to learn the examples, runs each in Stata, and hands every
  command's log to :func:`stata_judge`;
* ``test/test_help_examples.py`` imports it and pins what it finds.

One reader, so the Stata suite and the Python suite cannot disagree about
what the examples are.  Nothing here is a test by itself (the file name does
not start with ``test_``, so pytest does not collect it).

What counts as an example
-------------------------
A line showing a command typed at Stata's dot prompt: ``{cmd:. ...}``.  The
help's other command-shaped lines -- prompt-less ones such as
``{cmd:python app.py}`` -- are not examples by this definition.

* A command whose text ends in ``///`` continues on the next example line,
  which the help writes with the prompt again (``{cmd:.     title(...)}``).
* SMCL's character escapes are undone: ``{c -(}``, ``{c )-}``, ``{c |}``,
  ``{c S|}`` ($), ``{c 'g}`` (`), and ``{c #}`` / ``{c 0x#}`` /
  ``{char #}`` codes.  Any other directive inside a command -- ``{it:...}``
  -- is a template, not a runnable command, and is refused.
* ``//`` and ``/* */`` comments are removed, as Stata's do-file reader
  removes them; a line that is a ``*`` comment stays, and runs as one.
* A line the help shows right after a command, in ``{cmd:...}`` with no
  prompt, is that command's output (the refusal or the note the help says
  it prints).

Groups
------
A group is a run of example lines and their output lines with nothing else
between them.  Each ``{ul:...}`` heading or paragraph therefore starts a new
group, and a group's own setup lines -- ``sysuse auto, clear`` -- belong to
it.  Its label is the section title, the ``{dlgtab}`` above it if any, and
the last ``{ul:...}`` heading since, for reports only.

Shown, not run
--------------
Everything else the help shows as a command is collected too, so that none
of it is outside the harness in silence: a command line written without the
prompt (``{phang2}{cmd:python app.py}{p_end}``; a line that is only a
``{cmd:...}`` continues the one above it, as dash_setup.sthlp's two-line
pip commands do), and a dash command written inline in prose
(``{cmd:dash build, saving(app.py) server} writes ...``) -- any
``{cmd:dash ...}`` that is more than a subcommand's name and is not a
message dash prints.  The Syntax sections are grammar, not commands, and
are not read.  test_help_examples.cscript pins each by its text with the
reason it is not run.

Python 3.8+ and the standard library only: Stata's interpreter
(``c(python_exec)``) and pytest's are different builds.
"""
import os
import re
import unicodedata

HELP_FILES = ("dash.sthlp", "dash_setup.sthlp")

#: The cscript whose cases run the help's recipe blocks as shown (the
#: ``recipe`` shown pin; WP-48 ECO-16).
RECIPE_SCRIPT = "test_help_claims_8.cscript"


class HelpExampleError(ValueError):
    """The help holds an example line this reader cannot read faithfully."""


class Command(object):
    """One example command: its text as it would be typed, where it is, and
    what the help shows it printing (``outputs``, on ``output_lines``)."""

    __slots__ = ("file", "lines", "text", "outputs", "output_lines")

    def __init__(self, file, lines, text, outputs=None):
        self.file = file
        self.lines = tuple(lines)
        self.text = text
        self.outputs = list(outputs or [])
        self.output_lines = []

    @property
    def line(self):
        """The first physical line of the command."""
        return self.lines[0]

    def __repr__(self):
        return "Command(%s:%d %r)" % (self.file, self.line, self.text)


class Shown(object):
    """A command the help shows and does not present as an example to type:
    ``form`` is ``"line"`` for a prompt-less command line, ``"inline"`` for
    a dash command written in a sentence."""

    __slots__ = ("file", "lines", "text", "form")

    def __init__(self, file, lines, text, form):
        self.file = file
        self.lines = tuple(lines)
        self.text = text
        self.form = form

    @property
    def line(self):
        return self.lines[0]

    def __repr__(self):
        return "Shown(%s:%d %s %r)" % (self.file, self.line, self.form,
                                       self.text)


class Group(object):
    """A run of example lines with nothing between them."""

    __slots__ = ("file", "label", "commands")

    def __init__(self, file, label):
        self.file = file
        self.label = label
        self.commands = []

    @property
    def line(self):
        return self.commands[0].line

    def __repr__(self):
        return "Group(%s:%d %r, %d)" % (self.file, self.line, self.label,
                                        len(self.commands))


# ---------------------------------------------------------------------------
# SMCL
# ---------------------------------------------------------------------------

#: An example line: the {cmd:} directive opening with Stata's dot prompt.
_PROMPT = re.compile(r"\{cmd:\.(?=\s)")

#: The paragraph directives an example or output line may open with.
_PARA = re.compile(r"^\{(?:p(?:\s+\d+)*|phang\d?|pstd|pin\d?|pmore\d?|psee)\}$")

#: {c ...} names SMCL defines for characters a command may hold.
_C_NAMED = {"-(": "{", ")-": "}", "|": "|", "S|": "$", "'g": "`"}


def _close(s, start):
    """Index just past the ``}`` closing the directive opened at ``s[start]``."""
    depth = 0
    for i in range(start, len(s)):
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise HelpExampleError("an SMCL directive is not closed: %r" % s[start:])


def _char(code):
    """The character a ``{c code}`` directive stands for."""
    if code in _C_NAMED:
        return _C_NAMED[code]
    if re.match(r"^0x[0-9a-fA-F]{1,2}$", code):
        n = int(code, 16)
    elif re.match(r"^\d{1,3}$", code):
        n = int(code)
    else:
        raise HelpExampleError("{c %s} is not a character this reader "
                               "knows how to write" % code)
    if not 1 <= n <= 255:
        raise HelpExampleError("{c %s} is outside SMCL's 1 to 255" % code)
    # SMCL's codes are Latin-1, whose code points are Unicode's.
    return chr(n)


def smcl_unescape(text):
    """Undo SMCL's character escapes in *text*.

    Raises :class:`HelpExampleError` on any other directive: a command that
    holds ``{it:varname}`` is a template, and running it would test nothing.
    """
    out, i = [], 0
    while i < len(text):
        ch = text[i]
        if ch == "{":
            j = _close(text, i)
            m = re.match(r"^\{(?:c|char)\s+(\S+)\}$", text[i:j])
            if not m:
                raise HelpExampleError("SMCL directive %r inside an example "
                                       "command" % text[i:j])
            out.append(_char(m.group(1)))
            i = j
        elif ch == "}":
            raise HelpExampleError("an unmatched } inside an example command")
        else:
            out.append(ch)
            i += 1
    return unicodedata.normalize("NFC", "".join(out))


def _pieces(line):
    """``[(kind, text)]`` for a line, split at its top-level braces.

    *kind* is ``"dir"`` for a directive, ``"text"`` for text between them and
    ``"open"`` for a directive the line does not close -- prose runs
    ``{cmd:...}`` over two lines, and such a line is neither an example, an
    output line nor a heading.
    """
    out, buf, i = [], "", 0
    while i < len(line):
        if line[i] == "{":
            if buf:
                out.append(("text", buf))
                buf = ""
            try:
                j = _close(line, i)
            except HelpExampleError:
                out.append(("open", line[i:]))
                return out
            out.append(("dir", line[i:j]))
            i = j
        else:
            buf += line[i]
            i += 1
    if buf:
        out.append(("text", buf))
    return out


def _cmd_text(line):
    """The text of the ``{cmd:}`` directives of an example or output line.

    The line must be a paragraph directive, one or more ``{cmd:...}`` and an
    optional ``{p_end}``, and nothing else; anything else is refused, so a
    command is never read from half a line.  Returns None when the line has
    that shape but no {cmd:} (it is not an example or output line at all).
    """
    texts = []
    for kind, piece in _pieces(line):
        if kind == "open":
            return None
        if kind == "text":
            if piece.strip():
                return None
            continue
        if piece.startswith("{cmd:"):
            texts.append(piece[len("{cmd:"):-1])
        elif piece == "{p_end}" or _PARA.match(piece):
            continue
        else:
            return None
    if not texts:
        return None
    return "".join(texts)


def _strip_comments(text):
    """Remove ``//`` and ``/* */`` comments outside double quotes, as Stata's
    do-file reader does before a command runs.  A ``*`` comment line is left
    whole: it is a command, and it runs as one."""
    if text.lstrip().startswith("*"):
        return text
    out, i, in_q = [], 0, False
    while i < len(text):
        ch = text[i]
        if ch == '"':
            in_q = not in_q
        elif not in_q and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            if j == -1:
                raise HelpExampleError("an unclosed /* comment in an example")
            out.append(" ")
            i = j + 2
            continue
        elif (not in_q and text.startswith("//", i)
              and (i == 0 or text[i - 1].isspace())):
            break
        out.append(ch)
        i += 1
    return "".join(out).rstrip()


def _label_text(s):
    """Plain text of a heading, for reports: directives dropped, escapes undone."""
    prev = None
    while prev != s:
        prev = s

        def _inner(m):
            body = m.group(1)
            c = re.match(r"^(?:c|char)\s+(\S+)$", body)
            if c:
                try:
                    return _char(c.group(1))
                except HelpExampleError:
                    return "?"
            return body.split(":", 1)[1] if ":" in body else ""

        s = re.sub(r"\{([^{}]*)\}", _inner, s)
    return " ".join(s.split())


def _headings(line):
    """``(kind, text)`` for each {title}, {dlgtab} and {ul} on a line."""
    found = []
    for kind, piece in _pieces(line):
        if kind != "dir":
            continue
        m = re.match(r"^\{(title|dlgtab|ul):(.*)\}$", piece, re.S)
        if m:
            found.append((m.group(1), _label_text(m.group(2))))
    return found


# ---------------------------------------------------------------------------
# Reading a help file
# ---------------------------------------------------------------------------

#: A {cmd:...} directive anywhere on a line, SMCL character escapes and all.
_CMD_ANY = re.compile(r"\{cmd:((?:[^{}]|\{c(?:har)?\s+[^{}]*\})*)\}")

#: Not a command: a subcommand's bare name, or a message dash prints
#: ("dash: ...", "dash build: ...").  dash image joined the subcommands in
#: WP-33 33-06.
_NOT_A_MENTION = re.compile(
    r"^dash(?:\s+(?:build|serve|kpi|clear|image))?\s*$|^dash(?:\s+\w+)?\s*:")


def is_mention(content):
    """Is this inline ``{cmd:...}`` text a dash command written in prose?"""
    t = " ".join(content.split())
    return bool(re.match(r"^dash\s+\S", t)) and not _NOT_A_MENTION.match(t)


def _lenient_unescape(s):
    try:
        return smcl_unescape(s)
    except HelpExampleError:
        return s


def _parse(text, name):
    """``(groups, shown)`` for one help file's *text*; *name* names it in
    reports.  See the module's docstring for what each is."""
    groups, shown = [], []
    title, dlgtab, ul = "", "", ""
    run = None            # the Group being filled, or None between runs
    joining = False       # the last command ended in ///
    shown_open = False    # the last line was a shown command line ...
    shown_more = False    # ... that ended in ///
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        if _PROMPT.search(line):
            body = _cmd_text(line)
            if body is None:
                raise HelpExampleError(
                    "%s:%d: an example line must be a paragraph directive, "
                    "{cmd:...} and {p_end}, and nothing else: %r"
                    % (name, n, line))
            body = smcl_unescape(body)
            if not re.match(r"^\.\s", body):
                raise HelpExampleError("%s:%d: no dot prompt: %r"
                                       % (name, n, body))
            cmd = body[1:].strip()
            m = re.search(r"(^|\s)///", cmd)
            more = m is not None
            if more:
                cmd = cmd[:m.start()].rstrip()
            if run is None:
                label = " / ".join(p for p in (title, dlgtab, ul) if p)
                run = Group(name, label)
                groups.append(run)
            if joining:
                prev = run.commands[-1]
                prev.text = (prev.text + " " + cmd).strip()
                prev.lines = prev.lines + (n,)
            else:
                if not cmd:
                    raise HelpExampleError("%s:%d: an empty example command"
                                           % (name, n))
                run.commands.append(Command(name, (n,), cmd))
            joining = more
            if not joining:
                c = run.commands[-1]
                c.text = _strip_comments(c.text)
                if "\t" in c.text:
                    raise HelpExampleError("%s:%d: a tab in an example "
                                           "command" % (name, c.line))
            shown_open = False
            continue
        if joining:
            raise HelpExampleError(
                "%s:%d: the command above ends in ///, and this line does not "
                "continue it" % (name, n))
        body = _cmd_text(line)
        if run is not None and body is not None:
            # Output the help shows the command printing.
            run.commands[-1].outputs.append(smcl_unescape(body).strip())
            run.commands[-1].output_lines.append(n)
            continue
        run = None
        bare = body is not None and \
            _pieces(line.lstrip())[0][1].startswith("{cmd:")
        if body is not None and title != "Syntax" and (not bare or shown_open):
            # A command line without the prompt: shown, not run.  It opens
            # with its own paragraph directive; a line that is only a
            # {cmd:...} continues the shown line above it (and is otherwise
            # the wrapped end of a {synopt} or a sentence), as does any line
            # after one ending in ///.
            cmd = smcl_unescape(body).strip()
            m = re.search(r"(^|\s)///", cmd)
            more = m is not None
            if more:
                cmd = cmd[:m.start()].rstrip()
            if shown_open and (shown_more or bare):
                prev = shown[-1]
                prev.text = (prev.text + " " + cmd).strip()
                prev.lines = prev.lines + (n,)
            else:
                shown.append(Shown(name, (n,), cmd, "line"))
            shown_open, shown_more = True, more
            continue
        shown_open = False
        for kind, head in _headings(line):
            if kind == "title":
                title, dlgtab, ul = head, "", ""
            elif kind == "dlgtab":
                dlgtab, ul = head, ""
            else:
                ul = head
        if title != "Syntax":
            for m in _CMD_ANY.finditer(line):
                content = " ".join(_lenient_unescape(m.group(1)).split())
                if is_mention(content):
                    shown.append(Shown(name, (n,), content, "inline"))
    if joining:
        raise HelpExampleError("%s: the last example ends in ///" % name)
    return groups, shown


def extract_text(text, name):
    """The example groups of one help file's *text*."""
    return _parse(text, name)[0]


def shown_text(text, name):
    """The commands one help file's *text* shows and does not run."""
    return _parse(text, name)[1]


_CACHE = {}


def _parsed(path):
    key = (os.path.abspath(path), os.path.getmtime(path))
    if key not in _CACHE:
        with open(path, encoding="utf-8") as fh:
            _CACHE[key] = _parse(fh.read(), os.path.basename(path))
    return _CACHE[key]


def extract(path):
    """The example groups of the help file at *path* (cached by mtime)."""
    return _parsed(path)[0]


def shown(path):
    """The shown, not run, commands of the help file at *path*."""
    return _parsed(path)[1]


def extract_all(repo):
    """Every group of every help file in *repo*, in :data:`HELP_FILES` order."""
    out = []
    for f in HELP_FILES:
        out.extend(extract(os.path.join(repo, f)))
    return out


def shown_all(repo):
    """Every shown, not run, command of every help file in *repo*."""
    out = []
    for f in HELP_FILES:
        out.extend(shown(os.path.join(repo, f)))
    return out


def prompt_lines(text):
    """Line numbers holding ``{cmd:. `` -- a plain scan, independent of the
    reader above, for checking that every example line was read."""
    return [n for n, ln in enumerate(text.split("\n"), 1) if "{cmd:. " in ln]


# ---------------------------------------------------------------------------
# What may not run as written
# ---------------------------------------------------------------------------

_PREFIX = re.compile(
    r"^(?:(?:cap(?:t(?:u(?:r(?:e)?)?)?)?|qui(?:e(?:t(?:l(?:y)?)?)?)?"
    r"|n(?:o(?:i(?:s(?:i(?:l(?:y)?)?)?)?)?)?)\b\s*:?\s*)+")

#: Commands a test must never run as the help writes them.  Each needs a pin
#: in test_help_examples.cscript naming the non-blocking check that stands in
#: for it; the script refuses to run a matching example that has none.
MUST_PIN = (
    (re.compile(r"^dash\s+serve\b"),
     "dash serve blocks Stata until the server is stopped"),
    (re.compile(r"^dash_setup\b"),
     "dash_setup installs packages"),
    (re.compile(r"^(?:python|shell|winexec|xshell|unix)\b|^!"),
     "it runs Python or an operating-system command"),
    (re.compile(r"^(?:net|ssc|ado)\s|^webuse\b|^use\s+\"?https?:"),
     "it installs packages or reads from the network"),
    (re.compile(r"^(?:cd|chdir)\b"),
     "it moves the working directory out of the test's own"),
    (re.compile(r"^set\s.*\bperm(?:a(?:n(?:e(?:n(?:t(?:l(?:y)?)?)?)?)?)?)?\b"),
     "it changes a setting permanently"),
    (re.compile(r"^(?:exit|discard|cscript|log\s+close)\b"
                r"|^clear\s+(?:all\b|\*|programs?\b|mata\b)"
                r"|^(?:macro|program)\s+drop\s+_all\b"
                r"|^mata\s*:?\s*mata\s+clear\b"),
     "it tears down the session the test runs in"),
)


def must_pin(text):
    """Why *text* may not run as written, or "" when it may."""
    t = _PREFIX.sub("", text.strip())
    for rx, why in MUST_PIN:
        if rx.search(t):
            return why
    return ""


def saved_file(text):
    """The file a command's ``saving()`` names, as dash writes it, or ""."""
    m = re.search(r"\bsav(?:i(?:n(?:g)?)?)?\(\s*\"?([^\",)]+?)\"?\s*[,)]",
                  text)
    if not m:
        return ""
    f = m.group(1).strip()
    if f.lower().endswith(".gph"):
        f = f[:-4]
    if "." not in os.path.basename(f):
        f += ".html"
    return f


def registered_name(text):
    """The name a plot or KPI command registers under ``name()``, or "".
    Stata's ``frame <name>:`` prefix registers the graph in that frame."""
    text = re.sub(r"^frame\s+[A-Za-z_][A-Za-z0-9_]*\s*:\s*", "", text)
    if not re.match(r"^dash\s", text) or re.match(r"^dash\s+(?:build|serve|clear)\b", text):
        return ""
    m = re.search(r"\bnam(?:e)?\(\s*([A-Za-z_][A-Za-z0-9_]*)", text)
    return m.group(1) if m else ""


# ---------------------------------------------------------------------------
# Judging a command's log
# ---------------------------------------------------------------------------

#: Lines an example the help shows working must not print (unless the help
#: shows that very line): GAPS.md F5's standard -- nothing named as ignored --
#: and any warning or traceback the renderer lets through.
FLAGGED = (
    # WP-30 P1.26a: a note prints as twoway's do, "(note:  dash: ...)".
    (re.compile(r"^(?:\(note:\s+)?dash: ignoring unsupported option\(s\):"),
     "names an option as ignored"),
    (re.compile(r"not implemented and ignored"),
     "names a sub-option as ignored"),
    (re.compile(r"\w*Warning:"),
     "prints a warning"),
    # Python's logging, in its basic format -- LEVEL:logger:message -- which
    # is how Bokeh prints a validation warning or error to stderr
    # (bokeh/util/logconfig.py: "WARNING:bokeh.core.validation.check:W-1005
    # ...", "ERROR:...:E-1001 ...").  The pattern above is case-sensitive
    # and never matched them (24sep2026).
    (re.compile(r"^(?:WARNING|ERROR|CRITICAL):[A-Za-z_][\w.]*:"),
     "prints a logged warning or error"),
    (re.compile(r"Traceback \(most recent call last\)"),
     "prints a Python traceback"),
    # WP-30 P1.26a: every note dash prints is one "(note:  dash: ...)" line
    # in twoway's form, and dash's copies of twoway's estimator and scheme
    # notes keep twoway's "(note:  ...)" words; no "Warning:" is left in
    # either.  Last, so the specific labels above still win.
    (re.compile(r"\(note:\s"),
     "prints a note"),
)


def _norm(s):
    return " ".join(s.split())


def log_lines(text):
    """A text log's lines, with Stata's wrapped continuations (``> ``) re-joined."""
    out = []
    for raw in text.splitlines():
        if raw.startswith("> ") and out:
            out[-1] += raw[2:]
        else:
            out.append(raw)
    return out


def shown_at(lines, expected, span=4):
    """Indices of the log lines that show *expected* whole, or None.

    Whole lines only: the expected text must start a line and end one, so a
    note with something after it -- ``play() text() [aweight]`` for
    ``play() text()`` -- is not a match.  A message dash prints over two
    lines, which the help shows as one, matches across up to *span* lines,
    blanks compared as blanks.
    """
    want = _norm(expected)
    if not want:
        return None
    for i in range(len(lines)):
        acc = ""
        for j in range(i, min(i + span, len(lines))):
            acc = _norm(acc + " " + lines[j])
            if acc == want:
                return list(range(i, j + 1))
            if not acc or not want.startswith(acc):
                break
    return None


def judge(log_text, rc, rc_expected, outputs):
    """Problems with one command's run, as sentences (none: it did what the
    help says).

    *rc* against *rc_expected*; every line of *outputs* -- what the help shows
    the command printing -- shown whole in the log; and no :data:`FLAGGED`
    line anywhere else in it.
    """
    lines = log_lines(log_text)
    problems = []
    if rc != rc_expected:
        problems.append("rc %d, where the help shows rc %d" % (rc, rc_expected))
    covered = set()
    for out in outputs:
        at = shown_at(lines, out)
        if at is None:
            problems.append("the help shows %r and the log does not" % out)
        else:
            covered.update(at)
    for i, ln in enumerate(lines):
        if i in covered:
            continue
        for rx, what in FLAGGED:
            if rx.search(ln):
                problems.append("%s: %s" % (what, ln.strip()))
                break
    return problems


# ---------------------------------------------------------------------------
# The Stata side (called through python: from test_help_examples.cscript)
# ---------------------------------------------------------------------------

def _put_global(name, value):
    """Set a Stata global to *value* exactly, or raise.

    ``sfi.Macro.setGlobal`` substitutes macros in what it is given (measured:
    a value holding `` `z' $w `` arrived without them), so the value is
    read back, and set again with ``\\$`` and ``\\``` escapes if it changed.
    A value that cannot be carried whole stops the script: an example that
    ran as some other text would test nothing.
    """
    from sfi import Macro
    Macro.setGlobal(name, value)
    if Macro.getGlobal(name) == value:
        return
    Macro.setGlobal(name, value.replace("$", "\\$").replace("`", "\\`"))
    if Macro.getGlobal(name) != value:
        raise HelpExampleError("global %s cannot carry %r through Stata's "
                               "macro substitution" % (name, value))


def stata_plan():
    """Hand the examples to Stata as globals (read by the cscript).

    Reads ``$hx_repo``.  Sets ``hx_ng``; per group g ``hx_g<g>_n``,
    ``hx_g<g>_file``, ``hx_g<g>_line``, ``hx_g<g>_label``; per command c
    ``hx_g<g>_c<c>`` (the text), ``hx_g<g>_c<c>_line``,
    ``hx_g<g>_c<c>_nout`` and ``hx_g<g>_c<c>_guard`` (:func:`must_pin`);
    ``hx_nphys_<stem>`` per help file, the physical lines read; and
    ``hx_saved``, every file an example's saving() names.
    """
    from sfi import Macro
    repo = os.path.abspath(Macro.getGlobal("hx_repo"))
    groups = extract_all(repo)
    _put_global("hx_ng", str(len(groups)))
    saved = []
    for g, grp in enumerate(groups, 1):
        _put_global("hx_g%d_n" % g, str(len(grp.commands)))
        _put_global("hx_g%d_file" % g, grp.file)
        _put_global("hx_g%d_line" % g, str(grp.line))
        _put_global("hx_g%d_label" % g,
                    grp.label.replace("$", "?").replace("`", "?") or "-")
        for c, cmd in enumerate(grp.commands, 1):
            key = "hx_g%d_c%d" % (g, c)
            _put_global(key, cmd.text)
            _put_global(key + "_line", str(cmd.line))
            _put_global(key + "_nout", str(len(cmd.outputs)))
            _put_global(key + "_guard", must_pin(cmd.text))
            f = saved_file(cmd.text)
            if f and f not in saved:
                saved.append(f)
    for f in HELP_FILES:
        stem = os.path.splitext(f)[0]
        n = sum(len(c.lines) for grp in groups if grp.file == f
                for c in grp.commands)
        _put_global("hx_nphys_" + stem, str(n))
    for f in saved:
        if not re.match(r"^[A-Za-z0-9_.-]+$", f):
            raise HelpExampleError("an example saves to %r; the script checks "
                                   "plain file names only" % f)
    _put_global("hx_saved", " ".join(saved))
    items = shown_all(repo)
    _put_global("hx_ns", str(len(items)))
    for k, s in enumerate(items, 1):
        key = "hx_s%d" % k
        _put_global(key, s.text)
        _put_global(key + "_file", s.file)
        _put_global(key + "_line", str(s.line))
        _put_global(key + "_form", s.form)


def _shown_at(repo, file, line):
    for s in shown(os.path.join(repo, file)):
        if s.line == line:
            return s
    raise HelpExampleError("nothing shown starts at %s:%d" % (file, line))


def check_shown(item, kind, groups):
    """Problems with a shown, not run, command under its pinned *kind*.

    ``python``: the Python after ``python:`` compiles (it is not run).
    ``outside``: the file the command runs is one an example writes.
    ``described``: an example runs the command the sentence describes (its
    text begins with this one).  ``recipe``: a line of a recipe the help
    shows as a block, run as shown by a case of test_help_claims_8.cscript
    (its text is in that script).  ``placeholder`` and ``fragment`` are not
    commands a test can run -- a path to fill in, a subcommand with an
    option -- and are only accounted for.
    """
    problems = []
    cmds = [c.text for g in groups for c in g.commands]
    if kind == "python":
        m = re.match(r"^python\s*:(.*)$", item.text, re.S)
        if not m:
            problems.append("pinned as python, but it is no python: line")
        else:
            try:
                compile(m.group(1).strip(), "<%s:%d>" % (item.file, item.line),
                        "exec")
            except SyntaxError as exc:
                problems.append("its Python does not compile: %s" % exc)
    elif kind == "outside":
        py = [t for t in item.text.split() if t.endswith(".py")]
        written = {saved_file(t) for t in cmds}
        if not py or py[-1] not in written:
            problems.append("no example writes the file it runs (%s)"
                            % (py[-1] if py else "no .py named"))
    elif kind == "described":
        if not any(t.startswith(item.text) for t in cmds):
            problems.append("no example runs the command it describes")
    elif kind == "recipe":
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            RECIPE_SCRIPT)
        try:
            with open(path, encoding="utf-8") as fh:
                ran = item.text in fh.read()
        except OSError:
            ran = False
        if not ran:
            problems.append("no %s case runs the recipe line" % RECIPE_SCRIPT)
    elif kind not in ("placeholder", "fragment", "install"):
        problems.append("no check for the kind %r" % kind)
    return problems


def stata_check_shown():
    """``check_shown`` for the cscript.  Reads ``$hx_repo``, ``$hx_j_file``,
    ``$hx_j_line`` and ``$hx_j_kind``; prints each problem and sets
    ``$hx_nbad``."""
    from sfi import Macro
    repo = os.path.abspath(Macro.getGlobal("hx_repo"))
    file = Macro.getGlobal("hx_j_file")
    line = int(Macro.getGlobal("hx_j_line"))
    item = _shown_at(repo, file, line)
    problems = check_shown(item, Macro.getGlobal("hx_j_kind"),
                           extract_all(repo))
    for p in problems:
        print("HX FAIL %s:%d: %s" % (file, line, p))
    Macro.setGlobal("hx_nbad", str(len(problems)))


def _command_at(repo, file, line):
    for grp in extract(os.path.join(repo, file)):
        for cmd in grp.commands:
            if cmd.line == line:
                return cmd
    raise HelpExampleError("no example command starts at %s:%d" % (file, line))


def stata_judge():
    """Judge one command's run for the cscript.

    Reads ``$hx_repo``, ``$hx_j_file``, ``$hx_j_line`` (the command's first
    line), ``$hx_j_log``, ``$hx_j_rc``, ``$hx_j_expect`` and ``$hx_j_dir``
    (the group's working directory).  Beyond :func:`judge`, a command that
    ran with rc 0 must have written the file its saving() names into that
    directory, and registered the name its name() gives.  Prints each
    problem and sets ``$hx_nbad`` to their count.
    """
    from sfi import Macro
    repo = os.path.abspath(Macro.getGlobal("hx_repo"))
    file = Macro.getGlobal("hx_j_file")
    line = int(Macro.getGlobal("hx_j_line"))
    rc = int(Macro.getGlobal("hx_j_rc"))
    rc_expected = int(Macro.getGlobal("hx_j_expect"))
    cmd = _command_at(repo, file, line)
    with open(Macro.getGlobal("hx_j_log"), encoding="utf-8",
              errors="replace") as fh:
        problems = judge(fh.read(), rc, rc_expected, cmd.outputs)
    if rc == 0 and rc_expected == 0:
        f = saved_file(cmd.text)
        wd = Macro.getGlobal("hx_j_dir")
        if f and not os.path.isfile(os.path.join(wd, f)):
            problems.append("saving(%s) wrote no %s in the working directory"
                            % (f, f))
        nm = registered_name(cmd.text)
        if nm and nm not in Macro.getGlobal("dash_graph_registry").split():
            problems.append("name(%s) is not in the registry" % nm)
    for p in problems:
        print("HX FAIL %s:%d: %s" % (file, line, p))
    Macro.setGlobal("hx_nbad", str(len(problems)))


def stata_file_has():
    """Does a line of the file ``$hx_j_path`` (a log's wrapped lines
    re-joined) hold ``$hx_j_needle``?  Sets ``$hx_found`` to 1 or 0."""
    from sfi import Macro
    with open(Macro.getGlobal("hx_j_path"), encoding="utf-8",
              errors="replace") as fh:
        lines = log_lines(fh.read())
    needle = Macro.getGlobal("hx_j_needle")
    found = bool(needle) and any(needle in ln for ln in lines)
    Macro.setGlobal("hx_found", "1" if found else "0")


def stata_check_titled():
    """``check titled``: the graph the command registers carries the title it
    writes.  Reads ``$hx_cmd``; sets ``$hx_nbad``."""
    from sfi import Macro
    text = Macro.getGlobal("hx_cmd")
    problems = []
    nm = registered_name(text)
    t = re.search(r"\bti(?:t(?:l(?:e)?)?)?\(\"([^\"]*)\"\)", text)
    if not nm or not t:
        problems.append("check titled: no name() and title(\"...\") in %r"
                        % text)
    else:
        spec = Macro.getGlobal("dash_json_" + nm)
        needle = '"title":"\\"%s\\""' % t.group(1)
        if needle not in spec:
            problems.append("graph %s does not carry %s: %s"
                            % (nm, needle, spec))
    for p in problems:
        print("HX FAIL: " + p)
    Macro.setGlobal("hx_nbad", str(len(problems)))


def stata_saved_path():
    """``$hx_j_py``: the file ``$hx_cmd``'s saving() names, in ``$hx_j_dir``."""
    from sfi import Macro
    f = saved_file(Macro.getGlobal("hx_cmd"))
    _put_global("hx_j_py", os.path.join(Macro.getGlobal("hx_j_dir"), f)
                if f else "")


def stata_check_python_file():
    """The Python file ``$hx_j_py`` exists and compiles (``compile()``, which
    writes no byte code anywhere).  Sets ``$hx_nbad``."""
    from sfi import Macro
    path = Macro.getGlobal("hx_j_py")
    problems = []
    if not path or not os.path.isfile(path):
        problems.append("%s was not written" % (path or "the app"))
    else:
        try:
            with open(path, encoding="utf-8") as fh:
                compile(fh.read(), path, "exec")
        except (SyntaxError, ValueError, UnicodeDecodeError) as exc:
            problems.append("%s does not compile: %s" % (path, exc))
    for p in problems:
        print("HX FAIL: " + p)
    Macro.setGlobal("hx_nbad", str(len(problems)))


# ---------------------------------------------------------------------------
# How Stata renders SMCL
# ---------------------------------------------------------------------------
#
# Measured 23sep2026 with StataNow 19.5's translator (translate ...,
# translator(smcl2txt)), which returns rc 0 in every case below:
#
# * A paragraph directive met while a paragraph is open -- one begun by a
#   paragraph directive and not yet ended by {p_end} or a blank line -- and
#   the rest of the file is lost: dropped without a word, or shown as SMCL
#   text.  That holds mid-line too.  {synoptset}, {p2colset}, {marker},
#   the viewer directives and {* comments} inside a paragraph are harmless.
# * A line-mode directive inside an open paragraph -- {title}, {dlgtab},
#   {center}, {synopthdr}, {synoptline} -- is folded into the paragraph or
#   dropped; a bare {hline} there is shown as text ({hline 2} renders).
# * A directive split across two lines, a name SMCL does not know ({in}),
#   and {opt}/{opth} whose argument leaves a "(" unclosed are shown as text;
#   the rest renders.  A ")" with no "(" renders as itself.
# * A brace the source escapes ({c -(}) is text, by design.
#
# render_problems() predicts those from the source.  test_help_examples.py
# holds it to the measured cases; the cscript holds it to Stata's rendering
# of the help itself.

#: SMCL's directives (smcl.sthlp, StataNow 19.5) and the viewer's.
SMCL_DIRECTIVES = frozenset("""
    ado ado_d asis back bf bind break browse c ccl center centre char
    clearmore cmd cmdab col depvar depvars dialog dlgtab dtype dup err error
    help help_d helpb hi hilite hline ifin indepvars inp input it lalign
    manhelp manhelpi manlink manlinki manpage mansection marker matacmd net
    net_d netfrom_d newvar opt opth p p2col p2coldent p2colreset p2colset
    p2line p_end phang phang2 phang3 pin pin2 pin3 pmore pmore2 pmore3 psee
    pstd ralign rcenter rcentre res reset result right search search_d sf
    smcl space stata synopt synopthdr synoptline synoptset syntab tab text
    title txt ul update update_d var varlist varname vars view view_d weight
    vieweralsosee viewerjumpto viewerdialog""".split())

#: Directives that begin a paragraph.
_PARAGRAPH = frozenset("""p pstd psee phang phang2 phang3 pmore pmore2 pmore3
    pin pin2 pin3 synopt p2col p2coldent""".split())

#: Line-mode directives an open paragraph swallows.
_LINE_MODE = frozenset("title dlgtab center centre synopthdr synoptline"
                       .split())


def _dname(d):
    """The name of the directive text *d*, or "" ({...}, {* ...}, {!x})."""
    m = re.match(r"^\{([A-Za-z_][A-Za-z0-9_]*)", d)
    return m.group(1) if m else ""


def _token(s):
    """What a failed directive shows first: its text up to a blank."""
    return s.split()[0] if s.split() else s


def _literal_directives(d):
    """``(fragment, why)`` for *d* and every directive nested in it that the
    renderer would show as text; *why* quotes the directive."""
    out = []
    nm = _dname(d)
    if not nm:
        if not (d.startswith("{...}") or d.startswith("{*")):
            out.append((_token(d), "%s is no SMCL directive" % d))
    elif nm not in SMCL_DIRECTIVES:
        out.append((_token(d), "%s names no SMCL directive" % d))
    elif nm in ("opt", "opth"):
        arg = d[len(nm) + 1:-1]
        if arg.count("(") > arg.count(")"):
            out.append((_token(d), "%s leaves a ( unclosed, which {%s} "
                        "cannot read" % (d, nm)))
    inner = d[1:-1]
    i = 0
    while i < len(inner):
        if inner[i] == "{":
            try:
                j = _close(inner, i)
            except HelpExampleError:
                break
            out.extend(_literal_directives(inner[i:j]))
            i = j
        else:
            i += 1
    return out


def render_problems(text):
    """Where Stata's renderer will fail on the SMCL *text*, by the measured
    rules above: ``[(line, kind, fragment, message)]``, kind ``literal``
    (shown as text; the rest renders), ``inlined`` (a heading or rule folded
    into the paragraph above) or ``cascade`` (nothing after it renders; the
    scan stops there)."""
    problems = []
    open_para = False
    for n, raw in enumerate(text.split("\n"), 1):
        line = raw.rstrip("\r")
        if not line.strip():
            open_para = False
            continue
        i = 0
        while i < len(line):
            if line[i] != "{":
                i += 1
                continue
            try:
                j = _close(line, i)
            except HelpExampleError:
                rest = line[i:].strip()
                problems.append((n, "literal", _token(line[i:]),
                                 "%s ... is split across two lines; a "
                                 "directive must close on its line"
                                 % (rest if len(rest) <= 50
                                    else rest[:47] + "...")))
                break
            d = line[i:j]
            for frag, why in _literal_directives(d):
                problems.append((n, "literal", frag, why))
            nm = _dname(d)
            if nm in _PARAGRAPH:
                if open_para:
                    problems.append((
                        n, "cascade", _token(d),
                        "%s begins a paragraph while the one above is still "
                        "open (no {p_end} or blank line): nothing after it "
                        "renders" % _token(d)))
                    return problems
                open_para = True
            elif nm == "p_end":
                open_para = False
            elif open_para and nm in _LINE_MODE:
                problems.append((n, "inlined", d,
                                 "%s inside an open paragraph is folded into "
                                 "it" % _token(d)))
            elif open_para and d == "{hline}":
                problems.append((n, "literal", d,
                                 "{hline} inside an open paragraph is shown "
                                 "as text"))
            i = j
    return problems


def titles(text):
    """The text of every {title:...} heading of SMCL *text*, in order."""
    out = []
    for line in text.split("\n"):
        for kind, head in _headings(line):
            if kind == "title":
                out.append(head)
    return out


def predicted_title_losses(text):
    """The headings render_problems() says will not render as headings:
    folded into a paragraph, or after a cascade."""
    lost, cut = [], None
    probs = render_problems(text)
    for n, kind, frag, _msg in probs:
        if kind == "cascade":
            cut = n
        elif kind == "inlined" and frag.startswith("{title:"):
            lost.append(_label_text(frag[len("{title:"):-1]))
    if cut is not None:
        lines = text.split("\n")
        for line in lines[cut - 1:]:
            for kind, head in _headings(line):
                if kind == "title":
                    lost.append(head)
    return lost


#: An escaped opening brace, in each of SMCL's spellings.
_ESCAPED_OPEN = re.compile(r"\{(?:c|char)\s+(?:-\(|123|0[xX]7[bB])\}")

#: What an escaped brace is rendered as in the copy checked for leftovers:
#: SMCL's Latin-1 currency sign, which no dash help file uses.
SENTINEL = "{c 164}"


def with_braces_marked(text):
    """*text* with every escaped opening brace rendered as the sentinel
    instead, so that a "{" in the rendered copy can only be a directive
    that did not render -- never a brace the help shows on purpose (the
    fracpoly power set, an example of SMCL a user types)."""
    return _ESCAPED_OPEN.sub(SENTINEL, text)


def rendered_leftovers(rendered):
    """``{token: count}`` of the directives shown as text in rendered help
    (of a copy made with ``with_braces_marked``): each "{" and what follows
    it up to a blank."""
    counts = {}
    for m in re.finditer(r"\{\S*", rendered):
        counts[m.group(0)] = counts.get(m.group(0), 0) + 1
    return counts


def rendered_title_losses(rendered, heads):
    """The headings of *heads* that do not render as a line of their own,
    in order, in the rendered text."""
    lines = [ln.strip() for ln in rendered.splitlines()]
    lost, at = [], 0
    for h in heads:
        try:
            at = lines.index(h, at) + 1
        except ValueError:
            lost.append(h)
    return lost


def predicted_leftovers(text):
    """``{token: count}`` of the directives render_problems() says will be
    shown as text -- comparable with ``rendered_leftovers``."""
    counts = {}
    for _n, kind, frag, _msg in render_problems(text):
        if kind == "literal":
            t = _token(frag)
            counts[t] = counts.get(t, 0) + 1
    return counts


def stata_marked_copy():
    """Write ``$hx_j_src`` with its escaped braces marked to ``$hx_j_path``
    (see ``with_braces_marked``)."""
    from sfi import Macro
    with open(Macro.getGlobal("hx_j_src"), encoding="utf-8") as fh:
        text = fh.read()
    with open(Macro.getGlobal("hx_j_path"), "w", encoding="utf-8") as fh:
        fh.write(with_braces_marked(text))


def whole_file_render_problems(source, rendered):
    """Problems with Stata's rendering (*rendered*, of a copy of *source*
    made with ``with_braces_marked``) of a whole help file, as sentences:
    each directive shown as text, each heading that did not render as one,
    and each disagreement with render_problems(), the Python twin."""
    problems = []
    left = rendered_leftovers(rendered)
    for ln in rendered.splitlines():
        if "{" in ln:
            problems.append("rendered with SMCL left in it: %s" % ln.strip())
    heads = titles(source)
    lost = rendered_title_losses(rendered, heads)
    for h in lost:
        problems.append("the heading %r did not render as one (dropped, or "
                        "folded into a paragraph)" % h)
    # After a cascade the renderer drops some of the rest and shows some as
    # text, erratically, so there the twin's leftovers need only be among
    # Stata's; without one they must be the same.
    want = predicted_leftovers(source)
    cascade = any(k == "cascade" for _n, k, _f, _m in render_problems(source))
    agree = (all(left.get(t, 0) >= c for t, c in want.items()) if cascade
             else want == left)
    if not agree:
        problems.append("the Python twin predicts %r shown as text; Stata "
                        "shows %r" % (want, left))
    if sorted(predicted_title_losses(source)) != sorted(lost):
        problems.append("the Python twin predicts the headings %r lost; "
                        "Stata loses %r"
                        % (predicted_title_losses(source), lost))
    return problems


def stata_whole_file_ok():
    """``whole_file_render_problems`` for ``$hx_j_src`` rendered to
    ``$hx_j_path``; prints each and sets ``$hx_nbad`` to their count."""
    from sfi import Macro
    with open(Macro.getGlobal("hx_j_src"), encoding="utf-8") as fh:
        source = fh.read()
    with open(Macro.getGlobal("hx_j_path"), encoding="utf-8",
              errors="replace") as fh:
        rendered = fh.read()
    bad = whole_file_render_problems(source, rendered)
    name = os.path.basename(Macro.getGlobal("hx_j_src"))
    for p in bad:
        print("HX FAIL %s: %s" % (name, p))
    for n, kind, frag, msg in render_problems(source):
        print("HX       %s:%d (%s) %s" % (name, n, kind, msg))
    Macro.setGlobal("hx_nbad", str(len(bad)))


def rendered_prompt_lines(text):
    """The example lines of rendered help text -- a line whose text starts
    with Stata's prompt, ``. `` (a ``///`` continuation is written
    ``.     title(...)``) -- each with the wrapped lines under it (indented
    deeper, no prompt of their own) joined on."""
    prompt = re.compile(r"^(\s*)\.\s+\S")
    lines = text.splitlines()
    out = []
    for i, ln in enumerate(lines):
        m = prompt.match(ln)
        if not m:
            continue
        block, depth = [ln.strip()], len(m.group(1))
        for nxt in lines[i + 1:]:
            ind = len(nxt) - len(nxt.lstrip())
            if not nxt.strip() or ind <= depth or prompt.match(nxt):
                break
            block.append(nxt.strip())
        out.append(" ".join(block))
    return out


def rendered_problems(text, n_examples, limit=3):
    """How the examples fail to render in help text Stata translated
    (``translator(smcl2txt)``) from a copy made with ``with_braces_marked``,
    given the file's *n_examples* example lines.

    Every example line must render as a line of its own that starts with the
    prompt, and none may hold a "{" (in the marked copy, only a directive
    that did not render can leave one).  As many lines render with the
    prompt as the file has example lines, no fewer and no more: a line
    written ``{input}. dash ...`` or ``{cmd}. dash ...`` renders with the
    prompt, but neither the reader nor the plain scan (both look for
    ``{cmd:.``) sees it, so it would never run -- until 24sep2026 only too
    few lines failed here.  Measured on dash.sthlp at 4ede074:
    a paragraph left open before an example -- ``{pstd}`` /
    ``{it:Example:}`` / ``{phang2}{cmd:. ...}{p_end}`` -- made the renderer
    show every directive after it as text, so the first example after it
    read ``. dash scatter mpg weight, by(foreign){p_end} Marker Label
    Options {pstd} ...`` and every later one ran on inside that paragraph,
    where no one could type it.
    """
    shown = rendered_prompt_lines(text)
    problems = []
    if len(shown) != n_examples:
        problems.append("%d example lines rendered as lines of their own; "
                        "the file has %d" % (len(shown), n_examples))
    problems.extend("rendered with a directive in it: %s"
                    % (ln if len(ln) <= 100 else ln[:97] + "...")
                    for ln in shown if "{" in ln)
    return problems[:limit]


def stata_rendered_ok():
    """``rendered_problems`` of the text file ``$hx_j_path`` for
    ``$hx_j_nexp`` example lines; prints them and sets ``$hx_nbad`` to their
    count."""
    from sfi import Macro
    with open(Macro.getGlobal("hx_j_path"), encoding="utf-8",
              errors="replace") as fh:
        bad = rendered_problems(fh.read(), int(Macro.getGlobal("hx_j_nexp")))
    for p in bad:
        print("HX FAIL: %s" % p)
    Macro.setGlobal("hx_nbad", str(len(bad)))


def stata_repo_files():
    """``$hx_repo_has``: which of ``$hx_saved`` exist in the repository root
    or test/ -- taken before and after the run, which must agree."""
    from sfi import Macro
    repo = os.path.abspath(Macro.getGlobal("hx_repo"))
    have = []
    for f in Macro.getGlobal("hx_saved").split():
        for d in (repo, os.path.join(repo, "test")):
            if os.path.exists(os.path.join(d, f)):
                have.append(os.path.relpath(os.path.join(d, f), repo))
    Macro.setGlobal("hx_repo_has", " ".join(sorted(have)))


def stata_remove_tree():
    """Remove the script's own work directory ``$hx_root``, which must lie
    under ``c(tmpdir)`` and end in ``_hx``."""
    import shutil
    from sfi import Macro
    root = os.path.abspath(Macro.getGlobal("hx_root"))
    tmp = os.path.abspath(Macro.getGlobal("hx_tmpdir"))
    if not root.startswith(tmp + os.sep) or not root.endswith("_hx"):
        raise HelpExampleError("refusing to remove %r" % root)
    shutil.rmtree(root)
