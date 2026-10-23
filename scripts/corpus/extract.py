"""Extract every runnable twoway example Stata ships, as the corpus (WP-33 33-02).

    python3 scripts/corpus/extract.py --out <run> [--stata-dir <dir>]
    python3 scripts/corpus/extract.py --freeze-audit --out <run>

Four sources: the help files' "click to run" links (gr_example, gr_example2,
tsline_ex), the [G] manual's prompted commands (docs/g.pdf through
pdftotext), the dash lines of examples/*.do (as their twoway twins) and the
drop-in audit's probes, frozen in scripts/corpus/audit_probes.txt.  Writes
<run>/examples.jsonl (one example per combination of plot types and option
names, maintainer decision P4-2), <run>/extract_dropped.tsv (every command
left out, with its reason) and <run>/extract_duplicates.tsv (every
duplicate, with the example it maps to).  No record holds a machine path.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import argparse
import datetime
import functools
import glob
import hashlib
import json
import re
import shutil
import subprocess

from scripts.corpus import datasets

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROBES_PATH = os.path.join(REPO, "scripts", "corpus", "audit_probes.txt")
AUDIT_PATH = os.path.join(REPO, ".ultraplan", "review", "DROPIN-AUDIT-19oct2026.md")
HAND_MARKER = ("# ---- hand-added: the appendix's unquoted prose probes "
               "(section 33-02, D-33-02.j); --freeze-audit keeps every line "
               "below ----")

SETUP_WORDS = ("sysuse", "webuse", "use", "generate", "gen", "replace",
               "label", "drop", "keep", "sort", "gsort", "tsset", "xtset",
               "format", "egen", "encode", "input", "end", "clear", "regress",
               "reg", "predict", "summarize", "sum", "collapse", "expand",
               "stset", "streg", "stcox")

_TWOWAY_WORDS = ("twoway", "twowa", "twow", "two", "tw")
_GRAPH_WORDS_BASE = ("twoway", "tw", "two", "twow", "twowa", "scatter", "line",
                     "tsline", "tsrline", "graph twoway", "gr twoway")

SOURCE_RANK = {"help": 0, "gpdf": 1, "ex": 2, "audit": 3}

HELP_NAMES = ("added_text_options", "axis_label_options", "axis_scale_options",
              "by_option", "clegend_option", "legend_options",
              "marker_label_options", "region_options", "scale_option",
              "title_options", "symbolstyle", "graph_text", "graph_intro",
              "graph_display", "gph_files", "graph_editor", "whatsnew7to8")

AREA_PREFIX = {"plot-types": "plot:", "type-options-basic": "basic:",
               "type-options-stat": "stat:", "platform": "plat:",
               "syntax-data": "syn:", "silent-divergence": "sil:"}

_MESSAGE_PHRASES = ("<", "...", "…", "not allowed", "invalid", "not a",
                    "does not")

_PREFIX_RE = re.compile(
    r"^\s*(?:(?:gr|gra|grap|graph)\s+)?(?:twoway|twowa|twow|two|tw)(?=$|[\s(,|])\s*")
_PREFIX_WORDS = ("quietly", "qui", "noisily", "noi")
_BY_PREFIX_RE = re.compile(r"^(?:by|bysort|bys)\s+[^:]*:\s*")


# ---------------------------------------------------------------- scanning

def _scan(s):
    """Per character of s: (paren depth before it, inside a quote)."""
    depth, stack, out, i = 0, [], [], 0
    n = len(s)
    while i < n:
        two = s[i:i + 2]
        if not stack:
            if two == '`"':
                stack.append("c")
                out += [(depth, True), (depth, True)]
                i += 2
                continue
            if s[i] == '"':
                stack.append("s")
                out.append((depth, True))
                i += 1
                continue
            if s[i] == "(":
                out.append((depth, False))
                depth += 1
                i += 1
                continue
            if s[i] == ")":
                depth = max(depth - 1, 0)
                out.append((depth, False))
                i += 1
                continue
            out.append((depth, False))
            i += 1
            continue
        if stack[-1] == "s":
            if s[i] == '"':
                stack.pop()
            out.append((depth, True))
            i += 1
            continue
        if two == "\"'":
            stack.pop()
            out += [(depth, True), (depth, True)]
            i += 2
            continue
        if two == '`"':
            stack.append("c")
            out += [(depth, True), (depth, True)]
            i += 2
            continue
        out.append((depth, True))
        i += 1
    return out


def _close_paren(s, i, sc=None):
    """Index of the parenthesis closing the one at s[i] (or len(s)-1)."""
    sc = sc or _scan(s)
    d0 = sc[i][0]
    for j in range(i + 1, len(s)):
        if s[j] == ")" and not sc[j][1] and sc[j][0] == d0:
            return j
    return len(s) - 1


def _split_top(s, sep):
    """Split s at every occurrence of sep at depth 0 outside quotes."""
    sc = _scan(s)
    parts, last, i = [], 0, 0
    while i < len(s):
        if s.startswith(sep, i) and sc[i][0] == 0 and not sc[i][1]:
            parts.append(s[last:i])
            i += len(sep)
            last = i
            continue
        i += 1
    parts.append(s[last:])
    return parts


def _first_comma(s):
    sc = _scan(s)
    for i, ch in enumerate(s):
        if ch == "," and sc[i][0] == 0 and not sc[i][1]:
            return i
    return -1


def _remove_words(s, paren_words=(), bare_words=(), top_only=True):
    """Remove word(...) and bare words outside quotes; return (text, removed)."""
    removed, i = [], 0
    while True:
        sc = _scan(s)
        hit = None
        while i < len(s):
            if sc[i][1] or (top_only and sc[i][0] != 0):
                i += 1
                continue
            if i > 0 and (s[i - 1].isalnum() or s[i - 1] in "_."):
                i += 1
                continue
            m = re.match(r"[A-Za-z_]\w*", s[i:])
            if m:
                w = m.group(0)
                end = i + len(w)
                if w in paren_words and end < len(s) and s[end] == "(":
                    hit = (i, _close_paren(s, end, sc) + 1)
                    break
                if w in bare_words and (end == len(s) or s[end] in " \t,)|"):
                    hit = (i, end)
                    break
                i = end
                continue
            i += 1
        if hit is None:
            break
        a, b = hit
        removed.append(s[a:b])
        s = s[:a] + " " + s[b:]
        i = a
    return s, removed


def _tidy(s):
    """Collapse the blanks a removal left (outside quotes) and a bare trailing comma."""
    sc = _scan(s)
    out = []
    for i, ch in enumerate(s):
        if ch in " \t" and not sc[i][1] and out and out[-1] == " ":
            continue
        out.append(" " if ch in " \t" and not sc[i][1] else ch)
    s = "".join(out).strip()
    # a comma a removal left with nothing after it inside a plot group
    sc = _scan(s)
    out, i = [], 0
    while i < len(s):
        m = re.match(r"\s*,\s*\)", s[i:]) if not sc[i][1] else None
        if m and s[i:i + m.end()].strip() != ")" and not sc[i + m.end() - 1][1]:
            out.append(")")
            i += m.end()
            continue
        out.append(s[i])
        i += 1
    s = "".join(out)
    while s.endswith(","):
        s = s[:-1].rstrip()
    return s


# ---------------------------------------------------------- plot types

@functools.lru_cache(maxsize=None)
def _plottype_table():
    """twoway's (full, minimum) plot-type rows, read from _dash_expand_plottype_str."""
    with open(os.path.join(REPO, "dash_parse.mata"), encoding="utf-8") as fh:
        src = fh.read()
    a = src.index("string scalar _dash_expand_plottype_str(")
    b = src.index("for (i = 1; i <= rows(tbl); i++)", a)
    body = src[a:b]
    rows = re.findall(r'\("(\w+)","(\w+)"\)', body)
    if not rows:
        raise ValueError("_dash_expand_plottype_str's table not found")
    extra = dict(re.findall(r'if \(name == "(\w+)"\) return\("(\w+)"\)', body))
    return tuple(rows), tuple(sorted(extra.items()))


def _expand_plottype(word):
    rows, extra = _plottype_table()
    extra = dict(extra)
    if word in extra:
        return extra[word]
    for full, mn in rows:
        if len(word) >= len(mn) and full.startswith(word):
            return full
    return None


@functools.lru_cache(maxsize=None)
def _drawn_types():
    """The plot types dash draws (D-33-02.b), from dash_render's dispatch tables."""
    import dash_render  # noqa: E402  (repository root is on sys.path)
    return frozenset(dash_render._dash_plot_type_names()) | {"tsline", "tsrline"}


def graph_words():
    """GRAPH_WORDS: the first words that start a graph command (TR-33-02.2)."""
    return tuple(_GRAPH_WORDS_BASE) + tuple(sorted(_drawn_types()))


def _strip_prefix(cmd):
    """(rest, had_prefix): cmd without its twoway/graph twoway prefix."""
    m = _PREFIX_RE.match(cmd)
    if m:
        return cmd[m.end():], True
    return cmd.lstrip(), False


def _first_word(s):
    m = re.match(r"\s*\(*\s*([A-Za-z_]\w*)", s)
    return m.group(1) if m else None


def plot_type(cmd):
    """The first plot type of cmd, expanded through twoway's abbreviations."""
    rest, prefixed = _strip_prefix(cmd)
    w = _first_word(rest)
    if w is None:
        return None
    if not prefixed:
        if rest.lstrip().startswith("("):
            return None
        return w if w in ("scatter", "line", "tsline", "tsrline") else None
    return _expand_plottype(w)


def _masked(s):
    """s with every quoted character blanked (option words are read outside quotes)."""
    sc = _scan(s)
    return "".join(" " if sc[i][1] else ch for i, ch in enumerate(s))


#: D57: the reason an examples/ line with a dash-only option is dropped.
DASH_ONLY = "uses an option twoway does not have"
_DASH_ONLY_RE = re.compile(r"(?<![\w.])(?:hover|colpalette)\s*\(|(?<![\w.])table(?![\w(])")


def twin_mismatch(cmd, dash_cmd):
    """D57: None when dash_cmd is cmd with its twoway prefix (or none) replaced by
    the word dash, else a one-line description of the difference."""
    rest, _ = _strip_prefix(cmd)
    if not dash_cmd.startswith("dash ") and dash_cmd != "dash":
        return "the dash command does not start with the word dash"
    if " ".join(rest.split()) != " ".join(dash_cmd[5:].split()):
        return "twoway runs %r, dash runs %r" % (rest.strip(), dash_cmd[5:].strip())
    return None


def to_dash(cmd):
    """The dash command: the twoway prefix replaced by dash (never dash twoway)."""
    rest, prefixed = _strip_prefix(cmd)
    return "dash " + rest.strip()


def plot_types(cmd):
    """Every plot's type in order, expanded as plot_type expands the first."""
    rest, _ = _strip_prefix(cmd)
    out = []
    for seg in _split_top(rest, "||"):
        for inner, _opts in _plots_of(seg):
            w = _first_word(inner)
            if w:
                out.append(_expand_plottype(w) or w)
    return out


def _plots_of(seg):
    """[(plot text, options text)] of one ||-segment, plus its graph options."""
    s = seg.strip()
    sc = _scan(s)
    if s.startswith("("):
        plots, i = [], 0
        while i < len(s):
            if s[i] == "(" and sc[i][0] == 0 and not sc[i][1]:
                j = _close_paren(s, i, sc)
                inner = s[i + 1:j]
                c = _first_comma(inner)
                plots.append((inner if c < 0 else inner[:c],
                              "" if c < 0 else inner[c + 1:]))
                i = j + 1
                continue
            if s[i] == "," and sc[i][0] == 0 and not sc[i][1]:
                plots.append(("", s[i + 1:]))
                break
            i += 1
        return plots
    c = _first_comma(s)
    if c < 0:
        return [(s, "")] if s else []
    return [(s[:c], s[c + 1:])]


def _option_tokens(opts):
    """The option names given at depth 0 of an options text, lower-cased."""
    sc = _scan(opts)
    names, i = [], 0
    while i < len(opts):
        if sc[i][1] or sc[i][0] != 0:
            i += 1
            continue
        if i > 0 and (opts[i - 1].isalnum() or opts[i - 1] in "_.#%"):
            i += 1
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", opts[i:])
        if m:
            names.append(m.group(0).lower())
            i += len(m.group(0))
            continue
        i += 1
    return names


@functools.lru_cache(maxsize=None)
def option_table(repo):
    """(minimum, full) option pairs dash's parser binds spellings with (D-33-02.f)."""
    with open(os.path.join(repo, "dash.ado"), encoding="utf-8", errors="replace") as fh:
        ado = fh.read()
    with open(os.path.join(repo, "dash_parse.mata"), encoding="utf-8", errors="replace") as fh:
        mata = fh.read()
    out = []
    for prog in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
        m = re.search(r"^program define %s\b.*?$" % re.escape(prog), ado, re.M)
        if not m:
            raise ValueError("program %s not found in dash.ado" % prog)
        tail = ado[m.end():]
        e = re.search(r"^end\s*$", tail, re.M)
        body = tail[:e.start()] if e else tail
        decl = _syntax_words(body)
        if not decl:
            raise ValueError("no syntax declaration in %s" % prog)
        out += decl
    a = mata.find("// BEGIN tw_takes")
    b = mata.find("// END tw_takes")
    if a < 0 or b < 0:
        raise ValueError("_dash_tw_takes_tab()'s BEGIN/END tw_takes block not found")
    for full, mn in re.findall(r'\("(\w+)",\s*"(\w+)"', mata[a:b]):
        out.append((mn, full))
    return tuple(out)


def _syntax_words(body):
    """[(minimum, full)] of the first syntax command (test_abbreviations's rule)."""
    lines = body.split("\n")
    start = next((k for k, ln in enumerate(lines) if re.match(r"^\s*syntax\b", ln)), None)
    if start is None:
        return []
    chunk, k = [], start
    while k < len(lines):
        chunk.append(re.sub(r"///.*$", " ", lines[k]))
        if not lines[k].rstrip().endswith("///"):
            break
        k += 1
    decl = re.sub(r"^\s*syntax\b", " ", " ".join(chunk))
    toks, depth, tok = [], 0, ""
    for ch in decl:
        if ch == "(":
            depth += 1
            if depth == 1 and tok:
                toks.append(tok)
            tok = "" if depth == 1 else tok
            continue
        if ch == ")":
            depth -= 1
            continue
        if depth > 0:
            continue
        if ch.isalnum() or ch == "_":
            tok += ch
        else:
            if tok:
                toks.append(tok)
            tok = ""
    if tok:
        toks.append(tok)
    res, seen = [], set()
    for t in toks:
        if t in seen:
            continue
        seen.add(t)
        head = re.match(r"^[A-Z]*", t).group(0)
        full = t.lower()
        mn = head.lower() if head and head.lower() != full else full
        res.append((mn, full))
    return res


def expand_option(name, table):
    """The full option name name abbreviates, else name unchanged."""
    for mn, full in table:
        if full.startswith(name) and len(name) >= len(mn):
            return full
    return name


def option_names(cmd):
    """Sorted distinct full option names cmd gives (no values, no weight)."""
    table = option_table(REPO)
    rest, _ = _strip_prefix(cmd)
    names = set()
    for seg in _split_top(rest, "||"):
        for _plot, opts in _plots_of(seg):
            for n in _option_tokens(opts):
                names.add(expand_option(n, table))
    return sorted(names)


def signature(cmd):
    """Plot types in order and option names: the duplicate key (P4-2)."""
    return "+".join(plot_types(cmd)) + "|" + ",".join(option_names(cmd))


# ------------------------------------------------------------ filters

def is_schematic(cmd):
    """True for a syntax diagram rather than a runnable command."""
    if "..." in cmd or "…" in cmd or "{it:" in cmd or ". . ." in cmd:
        return True
    # A placeholder is a whole word outside quoted text and not an option or
    # function name: xvarlab() and exp() are runnable, a title may say varlist.
    sc = _scan(cmd)
    bare = "".join(" " if sc[i][1] else ch for i, ch in enumerate(cmd))
    return re.search(r"\b(?:yvar\w*|xvar\w*|varlist|varname|ylist|xlist|zvar|exp|any_options)"
                     r"\b(?!\s*\()",
                     bare) is not None


# ------------------------------------------- each example's own data (D52)

#: Plot types that read no variables: their data are typed in the command.
_NO_VARS = ("function", "scatteri", "pci", "pcarrowi")
#: Setup commands that make variables in ways setup_vars does not follow.
_OPAQUE = ("collapse", "reshape", "merge", "append", "contract", "separate", "statsby",
           "joinby", "cross", "xpose", "stack", "mkspline", "xi", "do", "run", "svmat",
           "tabulate", "tab", "kdensity", "lowess", "lpoly", "split", "xtile", "pctile",
           "fillin", "encode", "decode")
_TYPES = r"(?:byte|int|long|float|double|str\d*|strL)"


def dta_varnames(path):
    """The variable names of a Stata .dta file of release 117-119; None if unreadable."""
    try:
        with open(path, "rb") as fh:
            data = fh.read()
    except OSError:
        return None
    m = re.match(rb"<stata_dta><header><release>(\d+)</release><byteorder>(LSF|MSF)"
                 rb"</byteorder><K>", data)
    if not m or int(m.group(1)) not in (117, 118, 119):
        return None
    rel, order = int(m.group(1)), "<" if m.group(2) == b"LSF" else ">"
    import struct
    kfmt, klen = ("I", 4) if rel == 119 else ("H", 2)
    k = struct.unpack(order + kfmt, data[m.end():m.end() + klen])[0]
    a = data.find(b"<varnames>")
    if a < 0:
        return None
    a += len(b"<varnames>")
    width = 33 if rel == 117 else 129
    return [data[a + j * width:a + (j + 1) * width].split(b"\x00")[0].decode("utf-8", "replace")
            for j in range(k)]


def dataset_vars(stata_dir, cache):
    """{dataset: its variable names} of the shipped datasets and the cached webuse ones."""
    out = {}
    paths = sorted(glob.glob(os.path.join(stata_dir, "ado", "base", "*", "*.dta")))
    paths += sorted(glob.glob(os.path.join(cache, "*.dta")))
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        names = dta_varnames(p)
        if names is not None and name not in out:
            out[name] = names
    return out


def command_vars(cmd):
    """The variable names in the varlists of cmd's plots, in order, each once."""
    rest, _ = _strip_prefix(cmd)
    plots = []
    for seg in _split_top(rest, "||"):
        for inner, _opts in _plots_of(seg):
            plots += [p.strip() for p in _split_top(inner, "||")]
    out = []
    for inner in plots:
        c = _first_comma(inner)
        words = (inner if c < 0 else inner[:c]).split()
        if not words:
            continue
        pt = _expand_plottype(words[0])
        if pt is None or pt in _NO_VARS:
            continue
        for w in words[1:]:
            if w in ("if", "in", "using") or w.startswith(("[", "if(", "in(")):
                break
            w = re.sub(r"^(?:[A-Za-z]*\d*\.)+", "", w)  # time-series operators
            if re.fullmatch(r"[A-Za-z_]\w*", w) and w not in out:
                out.append(w)
    return out


def setup_vars(setup, dsvars):
    """The variables setup leaves in memory, or None when they cannot be known."""
    have, in_input = set(), False
    for c in setup:
        if in_input:
            in_input = c.strip() != "end"
            continue
        m = datasets._LOAD_RE.match(c)
        if m:
            name = os.path.splitext(m.group(2).split("/")[-1])[0]
            if name not in dsvars:
                return None
            have = set(dsvars[name])
            continue
        s = _unprefixed(c)
        word = (re.match(r"[A-Za-z_]\w*", s) or [None])[0]
        if word in _OPAQUE or re.search(r"\bgen(?:erate)?\(", s):
            return None
        if s == "clear" or re.match(r"^drop\s+_all\s*$", s):
            have = set()
        elif word in ("gen", "generate", "egen"):
            m = re.match(r"^\w+\s+(?:%s\s+)?([A-Za-z_]\w*)\s*=" % _TYPES, s)
            if m:
                have.add(m.group(1))
        elif word == "predict":
            body = s.split(",")[0].split()[1:]
            have.update(w for w in body if not re.fullmatch(_TYPES, w))
        elif word == "input":
            have.update(w for w in s.split()[1:] if not re.fullmatch(_TYPES, w))
            in_input = True
        elif word in ("rename", "ren") and len(s.split()) == 3:
            have.add(s.split()[2])
        elif word == "range" and len(s.split()) > 1:
            have.add(s.split()[1])
        elif word == "stset":
            have.update(("_t", "_d", "_st", "_t0"))
    return have


def _holds(have, need):
    """Whether have holds every name of need, in full or as Stata's unique abbreviation."""
    for v in need:
        if v not in have and sum(h.startswith(v) for h in have) != 1:
            return False
    return True


def infer_setup(cmd, setup, candidates, dsvars):
    """(the setup cmd runs on, None) or (None, why it is dropped) (D52).

    A setup that leaves cmd's variables in memory (a unique abbreviation
    counts, as in Stata), a setup whose variables cannot be known and a plot
    that reads no variables keep their setup; otherwise the first candidate
    dataset that holds every variable is loaded instead."""
    need = command_vars(cmd)
    if not need:
        return setup, None
    have = setup_vars(setup, dsvars)
    if have is None or _holds(have, need):
        return setup, None
    for name in candidates:
        if name in dsvars and _holds(set(dsvars[name]), need):
            word = "sysuse" if name in _shipped_names() else "webuse"
            return ["%s %s, clear" % (word, name)], None
    return None, "no dataset holds its variables"


def strip_registry_options(cmd):
    """Remove name(), saving() and nodraw (depth 0, outside quotes)."""
    s, removed = _remove_words(cmd, paren_words=("name", "saving"),
                               bare_words=("nodraw",), top_only=True)
    return _tidy(s), removed


def example_id(src, stem, setup, cmd):
    """<src>-<stem>-<first 8 hex digits of sha1(setup + cmd)> (D-33-02.a)."""
    h = hashlib.sha1(("\n".join(setup) + "\n" + cmd).encode("utf-8")).hexdigest()[:8]
    return "%s-%s-%s" % (src, stem, h)


# ------------------------------------------------------------ help files

_ESCAPES = (("{c -(}", "{"), ("{c )-}", "}"), ("{c 34}", '"'), ("{c 'g}", "`"))
_LINK_RE = re.compile(r"\{stata\s+(?:`\"(.*?)\"'|\"(.*?)\")\s*:", re.S)


def help_links(text, fname):
    """The gr_example, gr_example2 and tsline_ex links of one help file."""
    out = []
    for m in _LINK_RE.finditer(text):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        for a, b in _ESCAPES:
            s = s.replace(a, b)
        s = " ".join(s.split())
        for kind in ("gr_example2", "gr_example", "tsline_ex"):
            if s.startswith(kind + " "):
                out.append({"kind": kind, "arg": s[len(kind) + 1:].strip(),
                            "file": fname,
                            "line": text.count("\n", 0, m.start()) + 1})
                break
    return out


def _strip_ado_comments(text):
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    out = []
    for ln in text.split("\n"):
        ln = re.sub(r"(^|\s)//(?!/).*$", "", ln)
        out.append(ln)
    return out


def ado_programs(text):
    """Program name -> the commands its Xeq lines run, in order."""
    progs, name, delim, buf = {}, None, False, None
    lines = _strip_ado_comments(text)
    k = 0
    while k < len(lines):
        ln = lines[k]
        k += 1
        st = ln.strip()
        if not delim:
            while st.endswith("///") and k < len(lines):
                st = st[:-3].rstrip() + " " + lines[k].strip()
                k += 1
        if not st:
            continue
        m = re.match(r"^program\s+(?:define\s+)?([A-Za-z_]\w*)", st)
        if m and not delim:
            name = m.group(1)
            progs[name] = []
            continue
        if st == "end" and not delim and buf is None:
            name = None
            continue
        if re.match(r"^#delimit\s*;", st):
            delim = True
            continue
        if re.match(r"^#delimit\s+cr", st):
            delim = False
            buf = None
            continue
        if name is None:
            continue
        if delim:
            buf = st if buf is None else buf + " " + st
            while ";" in buf:
                stmt, buf = buf.split(";", 1)
                stmt = " ".join(stmt.split())
                buf = buf.strip() or None
                _add_xeq(progs[name], stmt)
                if buf is None:
                    break
            continue
        (_add_raw if name.startswith("_") else _add_xeq)(progs[name], " ".join(st.split()))
    return progs


def _add_raw(cmds, stmt):
    """A helper program's statement: helpers run their commands without Xeq."""
    first = stmt.split()[0]
    if first in ("Msg", "preserve", "restore", "version", "args", "syntax") \
            or stmt.startswith("set more"):
        return
    cmds.append(stmt)


def inline_helpers(body, progs, depth=0):
    """body with each call of a helper program (_name) replaced by its commands."""
    out = []
    for c in body:
        if re.match(r"^_[A-Za-z]\w*$", c) and c in progs and depth < 5:
            out += inline_helpers(progs[c], progs, depth + 1)
        else:
            out.append(c)
    return out


def _add_xeq(cmds, stmt):
    if re.match(r"^_[A-Za-z]\w*$", stmt):
        cmds.append(stmt)  # a call of a helper program, inlined by inline_helpers
        return
    m = re.match(r"^Xeq(?:\s+(.*))?$", stmt)
    if not m or not (m.group(1) or "").strip():
        return
    c = m.group(1).strip()
    first = c.split()[0]
    if first in ("Msg", "preserve", "restore", "version") or c.startswith("set more"):
        return
    cmds.append(c)


def _unprefixed(cmd):
    s = cmd.strip()
    while True:
        m = re.match(r"^(?:%s)\b\s*:?\s*" % "|".join(_PREFIX_WORDS), s)
        if m and m.end() > 0:
            s = s[m.end():]
            continue
        m = _BY_PREFIX_RE.match(s)
        if m:
            s = s[m.end():]
            continue
        return s


def _is_graph(cmd):
    s = _unprefixed(cmd)
    words = s.split()
    if not words:
        return False
    w0 = re.match(r"[A-Za-z_]\w*", words[0])
    w0 = w0.group(0) if w0 else words[0]
    if w0 in ("gr", "gra", "grap", "graph") and len(words) > 1:
        return re.match(r"^(?:twoway|twowa|twow|two|tw)\b", words[1]) is not None
    return w0 in graph_words()


def _is_setup(cmd):
    s = _unprefixed(cmd)
    if re.match(r"^set\s+(?:obs|seed)\s+\S+\s*$", s):
        return True
    m = re.match(r"[A-Za-z_]\w*", s)
    return bool(m) and m.group(0) in SETUP_WORDS


def split_setup(cmds):
    """([(setup, graph command)], dropped): the setup each graph command needs."""
    pairs, setup, dropped, in_input = [], [], [], False
    for c in cmds:
        if in_input:
            setup.append(c)
            if c.strip() == "end":
                in_input = False
            continue
        if _is_graph(c):
            pairs.append((list(setup), c))
            continue
        if _is_setup(c):
            setup.append(c)
            if re.match(r"^input\b", _unprefixed(c)):
                in_input = True
            continue
        dropped.append(c)
    return pairs, dropped


# ---------------------------------------------------------------- g.pdf

_CURLY = (("”", '"'), ("“", '"'), ("’", "'"), ("‘", "`"),
          ("−", "-"))
_PROMPT_RE = re.compile(r"^(\s*)\. (\S.*)$")
_LOAD_RE = re.compile(r"^(?:use|sysuse|webuse)\s+(\S+?)(?:\s*,\s*clear)?\s*$")
#: A margin annotation the manual prints beside a command line, "(note 1)"
#: or "← new".
_NOTE_RE = re.compile(r"\s{4,}(?:\(note \d+\)|←\s*\w*)\s*$")


def _uncurl(s):
    for a, b in _CURLY:
        s = s.replace(a, b)
    return s


def _continues(line, p_ind, cmd):
    """Whether a page line continues the prompted command cmd."""
    if not line.strip() or _PROMPT_RE.match(line):
        return False
    ind = len(line) - len(line.lstrip())
    st = line.strip()
    if ind >= p_ind + 4 and not (st.startswith("(") and not _starts_plot(st)):
        return True
    if ind < p_ind or not _PREFIX_RE.match(cmd):
        return False
    if st.startswith("(") and _starts_plot(st):
        return True
    if st.startswith((",", "||")):
        return True
    sc = _scan(cmd)
    if sc and (sc[-1][0] > 0 or cmd[-1] == "(" or cmd.endswith(",")):
        return True
    return re.match(r"^[a-z]\w*\(", st) is not None and _first_comma(cmd) >= 0


def _starts_plot(st):
    w = _first_word(st)
    return w is not None and _expand_plottype(w) is not None


def gpdf_commands(text):
    """The prompted graph commands of pdftotext -layout output, with setup."""
    shipped = None
    out, entry, setup = [], None, []
    for pno, page in enumerate(text.split("\f"), start=1):
        lines = page.split("\n")
        head = lines[0].strip() if lines else ""
        m = re.match(r"^(?:\d+\s+)?(.+?) — ", head)
        new_entry = m.group(1).strip() if m else entry
        if new_entry != entry:
            entry, setup = new_entry, []
        k = 1
        while k < len(lines):
            pm = _PROMPT_RE.match(lines[k])
            k += 1
            if not pm:
                continue
            p_ind = len(pm.group(1))
            cmd = " ".join(_uncurl(_NOTE_RE.sub("", pm.group(2))).split())
            graphish = _is_graph(cmd)
            while k < len(lines):
                st = lines[k].strip()
                if st.startswith(">"):
                    piece = st[1:]  # Stata's own continuation mark
                elif graphish and _continues(lines[k], p_ind, cmd):
                    piece = lines[k]
                else:
                    break
                cmd = cmd + " " + " ".join(_uncurl(_NOTE_RE.sub("", piece)).split())
                k += 1
            if re.match(r"^input\b", cmd):
                rows, k = _input_rows(lines, k)
                setup += [cmd] + rows
                continue
            lm = _LOAD_RE.match(cmd)
            if lm:
                setup = [_data_load(lm.group(1), cmd)]
                continue
            if _is_graph(cmd):
                out.append({"entry": entry, "page": pno, "cmd": cmd,
                            "setup": list(setup)})
            else:
                setup.append(cmd)
    return out


def _input_rows(lines, k):
    """(the data rows of an input listing starting at lines[k], ending with end; next k)."""
    rows = []
    while k < len(lines) and not _PROMPT_RE.match(lines[k]):
        m = re.match(r"^\s*\d+\.\s*(.*?)\s*$", lines[k])
        if not m:
            if rows or not lines[k].strip():
                break
            k += 1  # the variable-name header
            continue
        k += 1
        rows.append(" ".join(_uncurl(m.group(1)).split()))
        if rows[-1] == "end":
            break
    if not rows or rows[-1] != "end":
        rows.append("end")
    return rows, k


def _data_load(target, cmd):
    name = re.sub(r"\.dta$", "", target.rstrip(",").split("/")[-1])
    word = cmd.split()[0]
    if word == "sysuse":
        return "sysuse %s, clear" % name
    if word == "webuse":
        return "webuse %s, clear" % name
    return ("sysuse %s, clear" if name in _shipped_names() else "webuse %s, clear") % name


@functools.lru_cache(maxsize=None)
def _shipped_names():
    return frozenset(datasets.shipped(_stata_dir()))


def _stata_dir():
    return os.environ.get("DASH_STATA_DIR") or "/Applications/StataNow"


# ------------------------------------------------------------ examples/

def example_commands(text, fname):
    """The dash graph lines of an examples/*.do file, with their twoway twins."""
    raw = text.split("\n")
    lines, k = [], 0
    while k < len(raw):
        start = k
        ln = re.sub(r"\s//(?!/).*$", "", raw[k])
        while re.search(r"///.*$", ln) and k + 1 < len(raw):
            ln = re.sub(r"///.*$", " ", ln) + re.sub(r"\s//(?!/).*$", "", raw[k + 1]).strip()
            k += 1
        lines.append((start + 1, " ".join(ln.split())))
        k += 1
    out, setup = [], []
    for n, ln in lines:
        if not ln or ln.startswith(("*", "//")):
            continue
        if ln.startswith("sysuse "):
            setup = [ln]
            continue
        if ln.startswith("dash ") or ln == "dash":
            rest = ln[5:].strip()
            if not (rest.startswith("(") or plot_type("twoway " + rest)):
                continue
            # D57: the twin is the line with dash replaced by twoway, never
            # edited; a line using a dash-only option is no comparison.
            e = {"dash_cmd": ln, "cmd": "twoway " + rest, "setup": list(setup),
                 "file": fname, "line": n}
            if _DASH_ONLY_RE.search(_masked(rest)):
                e["dropped"] = DASH_ONLY
            out.append(e)
            continue
        if setup and _is_setup(ln):
            setup.append(ln)
    return out


# ------------------------------------------------------------ audit probes

def _audit_spans(line):
    """The backtick and single-quoted spans of one line, in line order."""
    found = [(m.start(), m.group(1)) for m in re.finditer(r"`([^`]+)`", line)]
    found += [(m.start(), m.group(1)) for m in
              re.finditer(r"(?<![A-Za-z0-9`])'([^']+?)'(?![A-Za-z0-9])", line)]
    return [s for _, s in sorted(found)]


def _span_ok(span):
    s = " ".join(span.split())
    body = s[5:] if s.startswith("dash ") else s
    if s.startswith("dash ") or s == "dash":
        twin = "twoway " + body
    else:
        twin = s
    pt = plot_type(twin)
    if pt is None:
        return None
    rest, _ = _strip_prefix(twin)
    m = re.match(r"\s*\(*\s*[A-Za-z_]\w*", rest)
    if not rest[m.end():].strip(" )"):
        return None
    if re.search(r"(?<!\|)\|(?!\|)", s):
        return None
    if any(p in s for p in _MESSAGE_PHRASES):
        return None
    return twin


def audit_probe_commands(text):
    """The quoted probe commands of the audit appendix's twoway/dash/evidence lines."""
    out, area, finding, in_app = [], None, None, False
    for ln in text.split("\n"):
        if ln.startswith("## Appendix"):
            in_app = True
            continue
        h = re.match(r"^### (\S+) \(\d+\)", ln)
        if h:
            area, in_app = h.group(1), True
            continue
        f = re.match(r"^- \*\*([A-Z]{1,5}-?\d+[a-z]?)\*\*", ln)
        if f:
            finding = f.group(1)
            continue
        if not in_app or finding is None:
            continue
        lm = re.match(r"^  - (twoway|dash|evidence):", ln)
        if not lm:
            continue
        for span in _audit_spans(ln):
            span = " ".join(span.split())
            twin = _span_ok(span)
            if twin is None:
                continue
            dash_cmd = span if span.startswith("dash ") else to_dash(span)
            ds = re.search(r"\b(sysuse|webuse)\s+([A-Za-z_]\w*)", ln)
            setup = ["%s %s, clear" % (ds.group(1), ds.group(2))] if ds else ["sysuse auto, clear"]
            out.append({"finding": AREA_PREFIX.get(area, "") + finding,
                        "cmd": twin, "dash_cmd": dash_cmd, "setup": setup})
    return out


def read_audit_probes(path):
    """The probes of audit_probes.txt, frozen and hand-added."""
    out, hand = [], False
    with open(path, encoding="utf-8") as fh:
        for n, ln in enumerate(fh.read().split("\n"), start=1):
            if ln == HAND_MARKER:
                hand = True
                continue
            if not ln.strip() or ln.startswith("#"):
                continue
            f = ln.split("\t")
            if len(f) != 3:
                raise ValueError("%s line %d: expected 3 tab-separated fields, found %d"
                                 % (os.path.basename(path), n, len(f)))
            setup = [s for s in f[1].split(" ; ") if s.strip()]
            out.append({"finding": f[0], "setup": setup, "cmd": f[2],
                        "dash_cmd": to_dash(f[2]), "hand": hand, "line": n})
    return out


def freeze_audit(audit_path, probes_path, date=None):
    """Rewrite the frozen lines of audit_probes.txt; keep the hand-added block."""
    with open(audit_path, encoding="utf-8") as fh:
        probes = audit_probe_commands(fh.read())
    date = date or datetime.date.today().strftime("%d%b%Y").lower()
    head = ["# Frozen from the drop-in audit's appendix on %s; regenerate only with --freeze-audit." % date]
    seen, body = set(), []
    for p in probes:
        ln = "%s\t%s\t%s" % (p["finding"], " ; ".join(p["setup"]), p["cmd"])
        if ln not in seen:
            seen.add(ln)
            body.append(ln)
    tail = HAND_MARKER + "\n"
    if os.path.exists(probes_path):
        with open(probes_path, encoding="utf-8") as fh:
            old = fh.read()
        i = old.find(HAND_MARKER)
        if i >= 0:
            tail = old[i:]
    with open(probes_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(head + body) + "\n" + tail)
    return len(body)


# ------------------------------------------------------------ the run

def _help_files(stata_dir):
    base = os.path.join(stata_dir, "ado", "base")
    files = sorted(glob.glob(os.path.join(base, "t", "twoway_*.sthlp")))
    files += [os.path.join(base, p) for p in ("s/scatter.sthlp", "l/line.sthlp",
                                               "t/tsline.sthlp", "g/graph_twoway.sthlp")]
    for n in HELP_NAMES:
        files += sorted(glob.glob(os.path.join(base, "*", n + ".sthlp")))
    return [f for f in files if os.path.exists(f)]


def _rel(path, root):
    return os.path.relpath(path, root).replace(os.sep, "/")


def _read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _record(src, stem, setup, cmd, dash_cmd=None, file=None, line=None,
            entry=None, finding=None):
    return {"src": src, "stem": stem, "setup": list(setup), "cmd": cmd,
            "dash_cmd": dash_cmd if dash_cmd is not None else to_dash(cmd),
            "file": file, "line": line, "entry": entry, "finding": finding}


def _help_records(stata_dir, dropped):
    base = os.path.join(stata_dir, "ado", "base")
    progs = {}
    for kind, rel in (("gr_example2", "g/gr_example2.ado"), ("tsline_ex", "t/tsline_ex.ado")):
        p = os.path.join(base, rel)
        progs[kind] = ado_programs(_read(p)) if os.path.exists(p) else {}
    recs = []
    for f in _help_files(stata_dir):
        relf = "base/" + _rel(f, base)
        stem = os.path.splitext(os.path.basename(f))[0]
        for lk in help_links(_read(f), relf):
            where = "%s:%d" % (relf, lk["line"])
            if lk["kind"] == "gr_example":
                arg = lk["arg"]
                if arg.startswith("graph "):
                    setup, cmd = [], arg
                else:
                    ds, _, cmd = arg.partition(":")
                    setup, cmd = ["sysuse %s, clear" % ds.strip()], cmd.strip()
                if not _is_graph(cmd):
                    dropped.append(("help", where, "not a twoway command", cmd))
                    continue
                recs.append(_record("help", stem, setup, cmd, file=relf, line=lk["line"]))
                continue
            name = lk["arg"].split()[0] if lk["arg"].split() else ""
            body = progs[lk["kind"]].get(name)
            if body is None:
                dropped.append(("help", where, "no such program", lk["kind"] + " " + lk["arg"]))
                continue
            pairs, other = split_setup(inline_helpers(body, progs[lk["kind"]]))
            for c in other:
                dropped.append(("help", where, "not a setup command", c))
            for setup, cmd in pairs:
                recs.append(_record("help", stem, setup, _unprefixed(cmd),
                                    file=relf, line=lk["line"], entry=name))
    return recs


def _gpdf_records(stata_dir, pdftotext, dropped):
    pdf = os.path.join(stata_dir, "docs", "g.pdf")
    if not pdftotext or not os.path.exists(pdf):
        why = "pdftotext not found" if not pdftotext else "docs/g.pdf not found"
        print("corpus: %s; the g.pdf examples are skipped" % why)
        dropped.append(("gpdf", "docs/g.pdf", why, ""))
        return []
    txt = subprocess.run([pdftotext, "-layout", pdf, "-"], capture_output=True,
                         check=True).stdout.decode("utf-8", errors="replace")
    recs = []
    for c in gpdf_commands(txt):
        setup, in_input = [], False
        for s in c["setup"]:
            if in_input or _is_setup(s):
                setup.append(s)
                if re.match(r"^input\b", _unprefixed(s)):
                    in_input = True
                elif s.strip() == "end":
                    in_input = False
            else:
                dropped.append(("gpdf", "docs/g.pdf:%d" % c["page"], "not a setup command", s))
        stem = re.sub(r"\s+", "_", c["entry"] or "g")
        recs.append(_record("gpdf", stem, setup, c["cmd"], file="docs/g.pdf",
                            line=c["page"], entry=c["entry"]))
    return recs


def _example_records(repo):
    recs = []
    for f in sorted(glob.glob(os.path.join(repo, "examples", "*.do"))):
        relf = _rel(f, repo)
        stem = os.path.splitext(os.path.basename(f))[0]
        for e in example_commands(_read(f), relf):
            r = _record("ex", stem, e["setup"], e["cmd"], dash_cmd=e["dash_cmd"],
                        file=relf, line=e["line"])
            if e.get("dropped"):
                r["dropped"] = e["dropped"]
            recs.append(r)
    return recs


def _audit_records(probes_path):
    recs = []
    if not os.path.exists(probes_path):
        return recs
    for p in read_audit_probes(probes_path):
        recs.append(_record("audit", p["finding"].replace(":", "_"), p["setup"], p["cmd"],
                            dash_cmd=p["dash_cmd"], file="scripts/corpus/audit_probes.txt",
                            line=p["line"], finding=p["finding"]))
    return recs


def dedupe(records):
    """One record per signature (D-33-02.f); returns (kept, [(dropped_id, kept_id)])."""
    groups = {}
    for r in records:
        r.setdefault("signature", signature(r["cmd"]))
        groups.setdefault(r["signature"], []).append(r)
    kept, pairs = [], []
    for sig, rs in groups.items():
        rs.sort(key=lambda r: (SOURCE_RANK.get(r["source"], 9), len(r["cmd"]), r["id"]))
        k = rs[0]
        k["duplicates"] = sorted(r["id"] for r in rs[1:])
        srcs = set(k.get("sources") or [k["source"]])
        for r in rs[1:]:
            srcs.update(r.get("sources") or [r["source"]])
            pairs.append((r["id"], k["id"]))
        k["sources"] = sorted(srcs, key=lambda s: SOURCE_RANK.get(s, 9))
        kept.append(k)
    kept.sort(key=lambda r: r["id"])
    return kept, sorted(pairs)


KEYS = ("id", "source", "sources", "file", "line", "entry", "finding", "setup",
        "cmd", "dash_cmd", "plottype", "datasets", "stripped", "signature",
        "duplicates")


def extract(stata_dir, repo, out, pdftotext=None):
    """Run every source; write examples.jsonl and the dropped and duplicate lists."""
    if not os.path.isdir(stata_dir):
        raise SystemExit("corpus: Stata's folder %s not found (set DASH_STATA_DIR)"
                         % os.path.basename(stata_dir.rstrip("/")))
    os.makedirs(out, exist_ok=True)
    dropped = []
    raw = (_help_records(stata_dir, dropped)
           + _gpdf_records(stata_dir, pdftotext, dropped)
           + _example_records(repo)
           + _audit_records(os.path.join(repo, "scripts", "corpus", "audit_probes.txt")))
    drawn = _drawn_types()
    dsvars = dataset_vars(stata_dir, datasets.cache_dir())
    entry_ds = {}
    for r in raw:
        for n in datasets.datasets_of(r["setup"]):
            lst = entry_ds.setdefault((r["src"], r["stem"]), [])
            if n not in lst:
                lst.append(n)
    shipped_sorted = sorted(n for n in dsvars if n in _shipped_names())
    byid, counts = {}, {"help": 0, "gpdf": 0, "ex": 0, "audit": 0}
    for r in raw:
        where = "%s:%s" % (r["file"], r["line"])
        cmd = r["cmd"]
        if r.get("dropped"):
            dropped.append((r["src"], where, r["dropped"], cmd))
            continue
        if is_schematic(cmd):
            dropped.append((r["src"], where, "schematic", cmd))
            continue
        cands = entry_ds.get((r["src"], r["stem"]), []) + shipped_sorted
        setup, why = infer_setup(cmd, r["setup"], cands, dsvars)
        if setup is None:
            dropped.append((r["src"], where, why, cmd))
            continue
        r = dict(r, setup=setup)
        pt = plot_type(cmd)
        if pt is None:
            dropped.append((r["src"], where, "not a twoway command", cmd))
            continue
        if pt not in drawn:
            dropped.append((r["src"], where, "a plot type dash does not draw", cmd))
            continue
        cmd, stripped = strip_registry_options(cmd)
        dash_cmd, _ = strip_registry_options(r["dash_cmd"])
        rid = example_id(r["src"], r["stem"], r["setup"], cmd)
        if rid in byid:
            continue
        counts[r["src"]] += 1
        byid[rid] = {"id": rid, "source": r["src"], "sources": [r["src"]],
                     "file": r["file"], "line": r["line"], "entry": r["entry"],
                     "finding": r["finding"], "setup": r["setup"], "cmd": cmd,
                     "dash_cmd": dash_cmd, "plottype": pt,
                     "datasets": datasets.datasets_of(r["setup"]),
                     "stripped": stripped}
    kept, pairs = dedupe(list(byid.values()))
    with open(os.path.join(out, "examples.jsonl"), "w", encoding="utf-8") as fh:
        for r in kept:
            fh.write(json.dumps({k: r[k] for k in KEYS}, ensure_ascii=False) + "\n")
    with open(os.path.join(out, "extract_dropped.tsv"), "w", encoding="utf-8") as fh:
        fh.write("source\twhere\treason\tcmd\n")
        for d in dropped:
            fh.write("\t".join(str(x).replace("\t", " ") for x in d) + "\n")
    cmd_of = {r["id"]: r for r in byid.values()}
    with open(os.path.join(out, "extract_duplicates.tsv"), "w", encoding="utf-8") as fh:
        fh.write("dropped_id\tkept_id\tsource\tcmd\n")
        for d, k in pairs:
            fh.write("%s\t%s\t%s\t%s\n" % (d, k, cmd_of[d]["source"], cmd_of[d]["cmd"]))
    res = dict(counts)
    res.update({"kept": len(kept), "duplicates": len(pairs), "dropped": len(dropped)})
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True)
    ap.add_argument("--stata-dir", default=None)
    ap.add_argument("--freeze-audit", action="store_true")
    ap.add_argument("--audit", default=AUDIT_PATH, help=argparse.SUPPRESS)
    ap.add_argument("--probes", default=PROBES_PATH, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.freeze_audit:
        n = freeze_audit(a.audit, a.probes)
        print("corpus: %d audit probes frozen" % n)
        return 0
    stata_dir = a.stata_dir or _stata_dir()
    pdft = os.environ.get("DASH_PDFTOTEXT") or shutil.which("pdftotext")
    res = extract(stata_dir, REPO, a.out, pdftotext=pdft)
    print("corpus: help %(help)d, gpdf %(gpdf)d, examples %(ex)d, audit %(audit)d; "
          "kept %(kept)d after removing %(duplicates)d duplicates; dropped %(dropped)d" % res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
