"""
test_abbreviations.py — static companion to test_abbreviations.cscript.

Plan task 04-02 (batch 2).  These tests are written BEFORE the fix, per
project rule 8, and most of them fail today.

The certification script is the behavioural test: it runs real `dash`
commands and reads the keys back out of the registry JSON.  It needs Stata,
so it cannot run in a pytest-only environment.  This file covers the same
section from the other side, by reading the source:

  * `dash.ado` declares its options in a `syntax` block.  Stata derives the
    minimum abbreviation of an option from the capitalised prefix of its
    declared name, so the declaration IS the abbreviation specification and
    can be checked without running anything.
  * `test/fixtures/abbrev_truth.json` records, for every option, the minimum
    abbreviation `twoway` itself accepts (probed in task 04-01).
  * `dash.sthlp` documents abbreviations with `{cmdab:min:rest}` markup.

Checking those three against each other catches the whole section statically:
an option whose declared minimum is longer than Stata's rejects abbreviations
twoway accepts; a declared minimum short enough to be claimed by two options
silently routes a value to the wrong one (measured: Stata's `syntax` has NO
ambiguity error — it takes the first matching declaration); and a spelling the
help documents but no declaration permits is a lie in the manual.

Run:  /opt/homebrew/bin/python3.14 -m pytest test/test_abbreviations.py -v
"""
import json
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ADO_PATH   = os.path.join(ROOT, "dash.ado")
MATA_PATH  = os.path.join(ROOT, "dash_parse.mata")
HELP_PATH  = os.path.join(ROOT, "dash.sthlp")
FIXTURE    = os.path.join(HERE, "fixtures", "abbrev_truth.json")


# ============================================================
# Loading
# ============================================================
@pytest.fixture(scope="module")
def truth():
    if not os.path.exists(FIXTURE):
        pytest.skip("fixtures/abbrev_truth.json missing; run "
                    "scripts/extract_abbrev_truth.do to build it")
    with open(FIXTURE) as fh:
        return json.load(fh)


def _read(path):
    if not os.path.exists(path):
        pytest.skip("%s not found" % os.path.basename(path))
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _program_body(src, name):
    """The text of `program define <name>` up to its terminating `end`."""
    m = re.search(r"^program define %s\b.*?$" % re.escape(name), src,
                  re.MULTILINE)
    if not m:
        return None
    tail = src[m.end():]
    e = re.search(r"^end\s*$", tail, re.MULTILINE)
    return tail[:e.start()] if e else tail


def _syntax_options(body):
    """
    Option declarations of the first `syntax` command in `body`, in order.

    Returns [(declared_min, full_name), ...].  Stata's rule: the capitalised
    leading run of the declared name is the minimum abbreviation; a name with
    no lowercase tail (FMT, UPDATE) or no capitals at all (name, title)
    admits no abbreviation, so its minimum is the full name.
    """
    lines = body.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*syntax\b", ln):
            start = i
            break
    if start is None:
        return []
    # a Stata command continues while the line ends with ///
    chunk = []
    i = start
    while i < len(lines):
        chunk.append(re.sub(r"///.*$", " ", lines[i]))
        if not lines[i].rstrip().endswith("///"):
            break
        i += 1
    decl = " ".join(chunk)
    decl = re.sub(r"^\s*syntax\b", " ", decl)

    out, depth, tok = [], 0, ""
    for ch in decl:
        if ch == "(":
            depth += 1
            if depth == 1:
                if tok:
                    out.append(tok)
                tok = ""
            continue
        if ch == ")":
            depth -= 1
            continue
        if depth > 0:
            continue                             # inside (string asis) etc.
        if ch.isalnum() or ch == "_":
            tok += ch
        else:
            if tok:
                out.append(tok)
            tok = ""
    if tok:
        out.append(tok)

    SKIP = {"syntax", "anything", "if", "in", "using", "weight", "fweight",
            "aweight", "pweight", "iweight", "varlist", "varname", "namelist"}
    res, seen = [], set()
    for t in out:
        if t in SKIP or t in seen:
            continue
        seen.add(t)
        head = re.match(r"^[A-Z0-9_]*", t).group(0)
        full = t.lower()
        mn = head.lower() if head and head.lower() != full else full
        res.append((mn, full))
    return res


@pytest.fixture(scope="module")
def declarations():
    """{block: [(min, full), ...]} for the four syntax blocks S04 touches."""
    src = _read(ADO_PATH)
    out = {}
    for prog in ("_dash_parse_graph_opts", "_dash_parse_plot_opts",
                 "_dash_kpi", "_dash_build"):
        body = _program_body(src, prog)
        assert body is not None, "program %s not found in dash.ado" % prog
        out[prog] = _syntax_options(body)
    return out


@pytest.fixture(scope="module")
def mata_alias():
    """dash's hard-coded option-key table, if it still exists."""
    src = _read(MATA_PATH)
    body = src[src.find("_expand_optkey"):] if "_expand_optkey" in src else ""
    return dict(re.findall(r'name\s*==\s*"([a-z0-9_]+)"\s*\)?\s*return\("([a-z0-9_]+)"\)',
                           body))


@pytest.fixture(scope="module")
def plot_decls(declarations):
    """Every option dash accepts on a plot command, in declaration order."""
    seen, out = set(), []
    for block in ("_dash_parse_plot_opts", "_dash_parse_graph_opts"):
        for mn, full in declarations[block]:
            if full not in seen:
                seen.add(full)
                out.append((mn, full))
    return out


def _resolves_to(abbrev, decls):
    """
    Which option Stata's `syntax` would bind `abbrev` to.

    Measured behaviour, not a guess: with
        syntax [, MLABColor(string) MLABCuts(string) ]
    the call `mlabc(red)` fills mlabcolor, and swapping the declaration order
    makes the same call fill mlabcuts.  First match in declaration order wins,
    with no error.
    """
    for mn, full in decls:
        if full.startswith(abbrev) and len(abbrev) >= len(mn):
            return full
    return None


# ============================================================
# 1. The fixture itself
# ============================================================
def test_fixture_is_self_consistent(truth):
    """The counts the cscript cross-checks against must match the lists."""
    c = truth["_meta"]["counts"]
    assert c["options"] == len(truth["options"])
    assert c["plottypes"] == len(truth["plottypes"])
    assert c["dash_mismaps"] == len(truth["dash_mismaps"])
    assert c["dash_rejects_min_abbrev"] == len(truth["dash_rejects_min_abbrev"])
    assert (c["dash_rejects_min_abbrev_option_declared_by_dash"] +
            c["dash_rejects_min_abbrev_option_not_in_dash"] ==
            c["dash_rejects_min_abbrev"])

    rejects = sorted(n for n, e in truth["options"].items()
                     if not e["dash"].get("accepts"))
    assert rejects == sorted(truth["dash_rejects_min_abbrev"])

    mismapped = sorted(n for n, e in truth["options"].items()
                       if e["dash"].get("accepts") and e["dash"].get("key") != n)
    assert len(mismapped) == c["dash_mismaps"]

    for name, e in truth["options"].items():
        assert e["min_abbrev"], "%s has no minimum abbreviation" % name
        assert name.startswith(e["min_abbrev"]), (
            "%s: minimum %r is not a prefix of the option name"
            % (name, e["min_abbrev"]))


# ============================================================
# 2. dash.ado must permit every abbreviation twoway permits   (BR-04.1)
# ============================================================
def test_declared_minimums_cover_stata_minimums(truth, plot_decls):
    declared = dict((full, mn) for mn, full in plot_decls)
    bad = []
    for name, e in sorted(truth["options"].items()):
        if name not in declared:
            continue                       # option dash does not have: S05
        want, got = e["min_abbrev"], declared[name]
        if want.startswith(got) and len(got) <= len(want):
            continue
        # Stata derives the minimum from the LEADING RUN OF CAPITALS, and a
        # digit ends that run -- so "T1title" yields a minimum of "t1", and
        # there is no capitalisation of "t1title" that yields "t".  twoway
        # nevertheless accepts t(), b(), l() and r() for the *1title options.
        # dash covers those by declaring the single letter as its own option
        # and folding it into the *1title local after -syntax- (see dash.ado).
        # Accept that as covering the gap; the runtime behaviour is asserted
        # end to end by test_abbreviations.cscript.
        if want in declared:
            continue
        bad.append("%s(): dash needs %r, declaration only allows %r"
                   % (name, want, got))
    assert not bad, (
        "%d option(s) reject an abbreviation twoway accepts.\n  "
        % len(bad)) + "\n  ".join(bad)


# ============================================================
# 3. ... and must not bind an abbreviation somewhere else     (BR-04.2)
# ============================================================
def test_declarations_resolve_abbreviations_like_twoway(truth, plot_decls):
    declared = set(full for _, full in plot_decls)
    bad = []
    for ab, r in sorted(truth["abbrev_resolution"].items()):
        want = r.get("stata_resolves_to")
        if not want or want not in declared:
            continue
        got = _resolves_to(ab, plot_decls)
        if got != want:
            where = "reject it outright" if got is None else "bind it to %s()" % got
            bad.append("%s(): twoway binds it to %s(), dash's declarations %s"
                       % (ab, want, where))
    assert not bad, (
        "%d abbreviation(s) do not land where twoway lands.\n  "
        % len(bad)) + "\n  ".join(bad)


# ============================================================
# 4. No prefix may be claimed by two options
#
# Passes today (nothing is abbreviated, so nothing can collide) and guards
# task 04-03: Stata's `syntax` does not report an ambiguous abbreviation, it
# silently binds the first declaration, so a collision introduced while
# capitalising the minimums would be invisible at run time.
# ============================================================
def test_no_prefix_is_claimed_by_two_options(plot_decls):
    claims = {}
    for mn, full in plot_decls:
        for L in range(len(mn), len(full) + 1):
            claims.setdefault(full[:L], []).append(full)
    clashes = ["%s() -> %s" % (p, ", ".join(v))
               for p, v in sorted(claims.items()) if len(set(v)) > 1]
    assert not clashes, (
        "%d prefix(es) are legal abbreviations of more than one option; "
        "Stata binds the first declared one without warning.\n  "
        % len(clashes)) + "\n  ".join(clashes)


# ============================================================
# 5. dash kpi
# ============================================================
def test_kpi_declares_the_documented_abbreviations(declarations):
    kpi = dict((full, mn) for mn, full in declarations["_dash_kpi"])
    bad = []
    for full, want in (("name", "nam"), ("update", "upd")):
        got = kpi.get(full)
        if got is None:
            bad.append("dash kpi does not declare %s()" % full)
        elif not (want.startswith(got) and len(got) <= len(want)):
            bad.append("dash kpi %s(): dash.sthlp documents %s(), the "
                       "declaration only allows %r" % (full, want, got))
    assert not bad, "\n  ".join(bad)


# ============================================================
# 6. The help must not document a spelling dash rejects
# ============================================================
def test_help_documents_only_accepted_abbreviations(declarations, plot_decls,
                                                    mata_alias):
    help_txt = _read(HELP_PATH)
    kpi   = dict((full, mn) for mn, full in declarations["_dash_kpi"])
    build = dict((full, mn) for mn, full in declarations["_dash_build"])
    plot  = dict((full, mn) for mn, full in plot_decls)

    bad, seen = [], set()
    for tok in re.findall(r"\{cmdab:([^}]*)\}", help_txt):
        if ":" not in tok or " " in tok:
            continue
        mn, rest = tok.split(":", 1)
        full = (mn + rest).split("(")[0]
        if not re.match(r"^[a-z][a-z0-9]*$", mn) or not full:
            continue
        if (mn, full) in seen:
            continue
        seen.add((mn, full))

        for where, table in (("a plot/graph", plot), ("dash kpi", kpi),
                             ("dash build", build)):
            if full in table:
                declared = table[full]
                ok = full.startswith(mn) and mn.startswith(declared) \
                    and len(declared) <= len(mn)
                if not ok and where == "a plot/graph":
                    ok = mata_alias.get(mn) == full
                if not ok:
                    bad.append("%s() is documented for %s option %s(), which "
                               "only accepts %r or longer"
                               % (mn, where, full, declared))
                break
        else:
            bad.append("%s() is documented as an abbreviation of %s(), which "
                       "dash does not declare anywhere" % (mn, full))

    assert not bad, (
        "dash.sthlp documents %d spelling(s) dash rejects.\n  "
        % len(bad)) + "\n  ".join(bad)


# ============================================================
# 7. TR-04.2 — the Mata option-key table is gone
# ============================================================
def test_mata_option_key_table_is_removed():
    src = _read(MATA_PATH)
    # Look for a DEFINITION, not any mention.  The file keeps a comment at each
    # removal site explaining what the function did and why it had to go; that
    # history is worth keeping and must not fail this test.
    leftovers = [
        n for n in ("_expand_optkey", "_dash_expand_opts_str")
        if re.search(r"^\s*(?:string scalar|void|real scalar)\s+%s\s*\(" % n,
                     src, re.M)
    ]
    assert not leftovers, (
        "dash_parse.mata still defines %s.  TR-04.2: once the syntax "
        "declarations carry the minimum abbreviations, the hard-coded table "
        "is not just redundant, it rewrites option keys before -syntax- sees "
        "them and is the source of the seven mis-mappings."
        % " and ".join(leftovers))
