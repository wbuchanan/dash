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
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

ADO_PATH   = os.path.join(ROOT, "dash.ado")
MATA_PATH  = os.path.join(ROOT, "dash_parse.mata")
HELP_PATH  = os.path.join(ROOT, "dash.sthlp")
FIXTURE    = os.path.join(HERE, "fixtures", "abbrev_truth.json")
UNKNOWN_FIXTURE = os.path.join(HERE, "fixtures", "unknown_option_truth.json")

sys.path.insert(0, HERE)
from known_differences import dead_rows, known_problems  # noqa: E402,F401


# ============================================================
# Loading
# ============================================================
@pytest.fixture(scope="module")
def truth():
    # Committed (test_fixtures_are_committed.py): missing is a defect, and
    # a skip here passed every check below that reads it.
    assert os.path.exists(FIXTURE), (
        "fixtures/abbrev_truth.json is missing; run "
        "scripts/extract_abbrev_truth.do to build it")
    with open(FIXTURE) as fh:
        return json.load(fh)


def _read(path):
    # dash.ado and dash.sthlp ship with the package: missing is a defect.
    assert os.path.exists(path), "%s not found" % os.path.basename(path)
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

    The run is of capital LETTERS: a digit ends it.  Measured 23sep2026 with
    the console binary (StataNow 19.5), one `syntax' per probe:

        T1title(string)          t(A) t1(A) t1t(A) t1title(A)  -> t1title
        T1title() T2title()      t(A) -> t1title,  t2(A) -> t2title
        YTITLE2(string)          ytitle(A) -> ytitle2,  yt(A) -> r(198)
        X1y(string)              x(A) x1(A) x1y(A)             -> x1y

    This helper used to count the digit into the run, which made T1title's
    minimum t1 and YTITLE2's the whole name -- the wrong rule the old
    comment in dash.ado gave for declaring T(), B(), L() and R() separately.
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
        head = re.match(r"^[A-Z]*", t).group(0)
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
    with no error.  Strictly, the first match that is still EMPTY: measured
    23sep2026, with T1title() T2title() declared, `t1title(B) t(A)' fills
    t2title with A.  This helper answers for a spelling's first use.
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

    # Flipped (WP-33 syn:SD-20): this compared the options dash records
    # under another key with dash_mismaps, which counts the spellings of
    # dash's former abbreviation table -- equal only while both were 0.
    # With every declared option measured, an option dash stores under its
    # twoway synonym's key is _STORED_UNDER's, and any other landing is a
    # known difference listed in ABBREV_KNOWN.
    mismapped = sorted(n for n, e in truth["options"].items()
                       if e["dash"].get("accepts")
                       and e["dash"].get("key") not in _landings(n))
    listed = set(k[len("land:"):] for k in ABBREV_KNOWN if k.startswith("land:"))
    assert set(mismapped) <= listed, sorted(set(mismapped) - listed)

    for name, e in truth["options"].items():
        assert e["min_abbrev"], "%s has no minimum abbreviation" % name
        assert name.startswith(e["min_abbrev"]), (
            "%s: minimum %r is not a prefix of the option name"
            % (name, e["min_abbrev"]))


#: The two tests below that hold today's declarations to the fixture's
#: Stata fields, which the fixture's _meta.status names.
_TESTS_OF_THE_STATA_FIELDS = (
    "test_declared_minimums_cover_stata_minimums",
    "test_declarations_resolve_abbreviations_like_twoway",
)


def test_fixture_says_its_dash_fields_are_the_pre_fix_record(truth):
    """GAPS.md L8, ROADMAP TR-25.5.  The fixture was probed on 18 Sep 2026,
    before the abbreviation fix it was committed with (896d117): its `dash'
    fields and dash_* lists record 7 mis-mappings and 18 declared options
    that rejected Stata's minimum abbreviation, and all 25 are fixed
    (measured 24sep2026 against today's declarations; the two tests the
    note names compare them).  Unannotated, the next audit re-reports 25
    resolved items as live gaps, so while the file is that record its
    _meta.status says so.  The extractor writes no status key: a
    regenerated file records dash as it is and carries no note."""
    meta = truth["_meta"]
    if meta["run_date"] == "18 Sep 2026":
        note = meta.get("status", "")
        assert note.startswith("PRE-FIX RECORD, not current behaviour"), note
        for name in _TESTS_OF_THE_STATA_FIELDS:
            assert name in note, name
            assert callable(globals().get(name)), (
                "the note names %s, which is not a test in this file" % name)
        assert "scripts/extract_abbrev_truth.do" in note
        # What the note says the record holds is what it holds.
        mismapped = [r.split(":", 1)[0].strip() for r in truth["dash_mismaps"]]
        assert sorted(mismapped) == sorted(
            ["xl", "yl", "m", "mlc", "mlw", "mls", "mlp"]), mismapped
        assert "(xl, yl, m, mlc, mlw, mls, mlp)" in note
        declared = truth["dash_rejects_min_abbrev_option_declared_by_dash"]
        assert len(declared) == 18 and "the 18 declared options" in note
    else:
        assert "status" not in meta, (
            "a regenerated abbrev_truth.json records dash as it is; the "
            "pre-fix note does not belong on it: %r" % meta["status"])


# ============================================================
# WP-31 A3: the fixture is a live record, pinned both ways
#
# abbrev_truth.json was the 18 Sep 2026 record, probed before the fix it
# was committed with, and said so in _meta.status.  It is regenerated by
# scripts/extract_abbrev_truth.do after WP-31 A2, its dash probe written on
# the plot type twoway takes each option on (after C3 an option twoway
# refuses on scatter is refused there by dash too), so its dash fields are
# today's.  These pin it: no status, a date after A2, no mis-map, every
# option dash declares accepted at twoway's minimum and landing on its own
# key, no declared minimum shorter than twoway's but the listed ones, and
# the plot-type minimums equal to the Mata table's.
# ============================================================
#: {option: (dash's declared minimum, twoway's minimum)} for the options
#: dash takes by a shorter spelling than twoway does.  Pinned both ways:
#: a new shorter minimum fails, and an entry that is no longer shorter
#: fails.  Written from the regenerated fixture (WP-31 A3).
_SHORTER_THAN_TWOWAY = {
    # Flipped (WP-31 A3c): "aspectratio": ("asp", "aspect") -- dash taking
    # asp() and aspe(), which twoway refuses, was wrong; its minimum is
    # twoway's aspect (sizing_truth.json abbrev_*, U32-10).
    # b2title(), l2title(), r2title(), t2title(): a digit ends the run of
    # capitals, so B2title's minimum is b; b() binds b1title() first, as
    # in twoway, and only a second b() reaches b2title (_SHARED_SPELLINGS).
    # WP-31 A3b measured them (edge_title_truth.json spellings, and live
    # in test_abbreviations.cscript U27-11): twoway does not refuse b(),
    # t(), l() or r(); it binds each to the 1 title, and a repeat -- b(A)
    # b(B), b1title(A) b(B), b2title(A) b(B) -- to the 1 title, the last
    # copy, as dash does once _dash_opts_repeats has merged the copies.
    # The shorter declared minimum is -syntax-'s notation only: no
    # spelling reaches b2title() in dash that twoway sends elsewhere, so
    # the entries stay.
    "b2title": ("b", "b2"),
    "l2title": ("l", "l2"),
    "r2title": ("r", "r2"),
    "t2title": ("t", "t2"),
    # Flipped (WP-31 A3d): jitter() was ("jit", "jitter") -- dash took
    # jit() .. jitte(), which twoway refuses ("option jit() not allowed",
    # r(198)); dash declares twoway's minimum, the full name, now.
    # Flipped (WP-31 A3b): name() was ("nam", "name") -- dash took nam(),
    # which twoway refuses ("option nam() not allowed", r(198)); dash
    # declares twoway's minimum, the full name, now (U27-10).
}

#: twoway's plot-type minimums (twowaygraph_g.class _unab_cmd); every other
#: type is its full name only (WP-31 A2).
_TWOWAY_PT_MINIMUMS = {"scatter": "sc", "line": "li", "connected": "con",
                       "histogram": "hist", "rscatter": "rsc",
                       "rline": "rl", "rconnected": "rcon",
                       "function": "fun"}


class TestTheLivePin:

    def test_the_fixture_has_no_status(self, truth):
        assert "status" not in truth["_meta"], truth["_meta"].get("status")

    def test_run_date_is_after_the_fix(self, truth):
        import datetime
        when = datetime.datetime.strptime(truth["_meta"]["run_date"],
                                          "%d %b %Y").date()
        assert when >= datetime.date(2026, 10, 13), when

    def test_every_declared_option_is_taken_at_twoways_minimum(
            self, truth, plot_decls):
        """Live, the other way from test_declared_minimums_cover_stata_
        minimums: dash itself, probed with twoway's minimum on a plot type
        twoway takes the option on, accepts it and records it under the
        option's own key."""
        # Flipped (WP-33 syn:SD-20): the key must be the option's own, or
        # the twoway synonym's dash stores it under (_STORED_UNDER); a
        # landing elsewhere is a known difference (ABBREV_KNOWN "land:"),
        # judged by test/known_differences.py's rule.  The 93 options of
        # the old record all landed on their own key; the regenerated one
        # measures every declared option.
        declared = set(full for _, full in plot_decls)
        results = {}
        for name, e in sorted(truth["options"].items()):
            if name not in declared:
                continue
            d = e["dash"]
            ok = d.get("accepts") is True and d.get("key") in _landings(name)
            results["land:" + name] = None if ok else (
                "%s(%s...): %r" % (e["min_abbrev"], name, d))
        assert known_problems(_only(results, "land:"), _only(ABBREV_KNOWN, "land:"),
                              "abbrev", deliberate=ABBREV_DELIBERATE) == []

    def test_every_stored_under_row_is_measured(self, truth):
        """_STORED_UNDER pinned both ways: each row is an option the record
        measured and dash stored, at twoway's minimum, under that key."""
        bad = ["%s: %r" % (n, truth["options"].get(n, {}).get("dash"))
               for n, k in sorted(_STORED_UNDER.items())
               if truth["options"].get(n, {}).get("dash", {}).get("key") != k]
        assert not bad, bad

    def test_no_unpinned_minimum_is_shorter_than_twoways(self, truth,
                                                         plot_decls):
        declared = dict((full, mn) for mn, full in plot_decls)
        shorter = {name: (declared[name], e["min_abbrev"])
                   for name, e in truth["options"].items()
                   if name in declared
                   and len(declared[name]) < len(e["min_abbrev"])}
        assert shorter == _SHORTER_THAN_TWOWAY, (
            sorted(set(shorter.items()) ^ set(_SHORTER_THAN_TWOWAY.items())))

    def test_the_dash_probe_records_no_mismap(self, truth):
        c = truth["_meta"]["counts"]
        assert truth["dash_mismaps"] == [] and c["dash_mismaps"] == 0
        assert truth["dash_rejects_min_abbrev_option_declared_by_dash"] == []
        assert c["dash_rejects_min_abbrev_option_declared_by_dash"] == 0
        bad = {ab: r["status"] for ab, r in truth["abbrev_resolution"].items()
               if r["status"] not in ("agrees",
                                      "twoway rejects this abbreviation")
               and not r["status"].startswith("not determined")}
        assert not bad, bad

    def test_plot_type_minimums_match_the_table(self, truth):
        src = _read(MATA_PATH)
        k = src.index("string scalar _dash_expand_plottype_str")
        table = dict(re.findall(r'\("([a-z]+)","([a-z]+)"\)',
                                src[k:src.index("\n}\n", k)]))
        bad = []
        for name, e in sorted(truth["plottypes"].items()):
            want = _TWOWAY_PT_MINIMUMS.get(name, name)
            if e["min_abbrev"] != want or table.get(name) != want:
                bad.append("%s: twoway %s, table %s, want %s"
                           % (name, e["min_abbrev"], table.get(name), want))
            if e["dash"].get("accepts") is not True or \
                    e["dash"].get("type") != name:
                bad.append("%s: dash %r" % (name, e["dash"]))
        assert len(truth["plottypes"]) == 33
        assert not bad, "\n  ".join(bad)


# ============================================================
# 2. dash.ado must permit every abbreviation twoway permits   (BR-04.1)
# ============================================================
def test_declared_minimums_cover_stata_minimums(truth, plot_decls):
    declared = dict((full, mn) for mn, full in plot_decls)
    results = {}
    checked = 0
    for name, e in sorted(truth["options"].items()):
        if name not in declared:
            continue                       # option dash does not have: S05
        checked += 1
        want, got = e["min_abbrev"], declared[name]
        # No exception for t(), b(), l() and r(): a digit ends the run of
        # capitals, so T1title's minimum is t itself (see _syntax_options),
        # and the *1title declarations cover twoway's single letters.
        if want.startswith(got) and len(got) <= len(want):
            results["min:" + name] = None
            continue
        # Flipped (WP-33 syn:SD-20): a declaration longer than twoway's
        # minimum is no difference when dash, probed live with twoway's
        # minimum, stored it under the option's own key or its synonym's
        # (a fold before -syntax-: nodropb(); a synonym: bin(), cmiss());
        # any other is a known difference listed under "min:".
        d = e["dash"]
        if d.get("accepts") is True and d.get("key") in _landings(name):
            results["min:" + name] = None
            continue
        results["min:" + name] = ("%s(): dash needs %r, declaration only "
                                  "allows %r" % (name, want, got))
    # dash declares all 180 of the fixture's options, so all are compared.
    # The skip above passed a reader that found no declaration, or fixture
    # keys that no longer match one, with nothing compared at all.
    # old -> new: 93 -> 180: syn:SD-20 regenerated fixture
    assert checked == 180, (
        "%d of the fixture's %d options were compared with a declaration"
        % (checked, len(truth["options"])))
    assert known_problems(_only(results, "min:"), _only(ABBREV_KNOWN, "min:"),
                          "abbrev", deliberate=ABBREV_DELIBERATE) == []


# ============================================================
# 3. ... and must not bind an abbreviation somewhere else     (BR-04.2)
# ============================================================
def test_declarations_resolve_abbreviations_like_twoway(truth, plot_decls):
    declared = set(full for _, full in plot_decls)
    bad = []
    checked = 0
    for ab, r in sorted(truth["abbrev_resolution"].items()):
        want = r.get("stata_resolves_to")
        if not want or want not in declared:
            continue
        checked += 1
        got = _resolves_to(ab, plot_decls)
        if got != want:
            where = "reject it outright" if got is None else "bind it to %s()" % got
            bad.append("%s(): twoway binds it to %s(), dash's declarations %s"
                       % (ab, want, where))
    # 40 of the 61 recorded spellings have a twoway binding to an option dash
    # declares; the other 21 record no binding.  As above, the skip let a
    # test with nothing compared pass.
    # old -> new: 39 -> 40: syn:SD-20 regenerated fixture (bgc() now binds
    # to bgcolor(), measured)
    assert checked == 40, (
        "%d of %d recorded spellings were compared"
        % (checked, len(truth["abbrev_resolution"])))
    assert not bad, (
        "%d abbreviation(s) do not land where twoway lands.\n  "
        % len(bad)) + "\n  ".join(bad)


# ============================================================
# 4. No prefix may be claimed by two options -- beyond the ones that are
#
# Stata's `syntax` does not report an ambiguous abbreviation, it silently
# binds the first declaration that admits the spelling, so a collision
# introduced while capitalising the minimums would be invisible at run time.
#
# This test passed while _syntax_options counted a digit into the run of
# capitals, which made every name with a digit unabbreviable.  A digit ends
# the run (measured 23sep2026, see _syntax_options), so T1title and T2title
# both admit t, YTitle and YTITLE2 both admit ytitle, XLabel and XLA2 both
# admit xla, and SORT and SORT1 both admit sort.  Those are the spellings in
# _SHARED_SPELLINGS.  On first use each binds where the user means it to
# (the next test holds that).  A SECOND use does not: -syntax- moves on to
# the next declaration that admits the spelling and is still empty.
# Measured 23sep2026 on dash itself, at plot and at graph level alike:
#
#     ytitle(A) ytitle(B)    records ytitle "A" and ytitle2 "B"
#     title(A) title(B)      records title "A" and title2 "B"
#     t(A) t(B)              records t1title "A" and t2title "B"
#
# where twoway, measured from the saved .gph, applies both and draws the
# last, B, as the y title, the title and the t1title.  (For plot options its
# class files merge a repeat before -syntax- sees it: twoway_yxview_parse.
# class runs `_parse combop 0 : 0, option(SORT1) rightmost'.)  dash.ado's
# _dash_opts_repeats now reads such a list as twoway does before the
# result is used -- each spelling put to the parser alone, one copy of
# each option kept (test_twoway_option_parity.cscript TP-14) -- but the
# fall-through is still -syntax-'s, so the list stays pinned and can only
# shrink: a new shared spelling fails here, and one that stops being
# shared must be taken off the list.
# ============================================================
_SHARED_SPELLINGS = {
    "t": ("t1title", "t2title"),          "b": ("b1title", "b2title"),
    "l": ("l1title", "l2title"),          "r": ("r1title", "r2title"),
    "title": ("title", "title2"),         "subtitle": ("subtitle", "subtitle2"),
    "xtitle": ("xtitle", "xtitle2"),      "ytitle": ("ytitle", "ytitle2"),
    "xlabel": ("xlabel", "xlabel2"),      "ylabel": ("ylabel", "ylabel2"),
    "xscale": ("xscale", "xscale2"),      "yscale": ("yscale", "yscale2"),
    "xti": ("xtitle", "xti2"),            "yti": ("ytitle", "yti2"),
    "xla": ("xlabel", "xla2"),            "yla": ("ylabel", "yla2"),
    "xsc": ("xscale", "xsc2"),            "ysc": ("yscale", "ysc2"),
    "sort": ("sort", "sort1"),
    # WP-30 P1.6 part 2: dash's axis-2 spellings of the time-axis options,
    # as XLABEL2 is; a repeat is merged before -syntax- (TA-02's
    # tlabel(2001m1) tlabel(2003m1)).
    "tlabel": ("tlabel", "tlabel2"),      "ttick": ("ttick", "ttick2"),
    "tline": ("tline", "tline2"),         "tscale": ("tscale", "tscale2"),
    "ttitle": ("ttitle", "ttitle2"),
    # WP-31 H2t: dash's own table, bare (TABLE) or table(...) (TABLE2),
    # written in full, so only the full name is shared.
    "table": ("table", "table2"),
}


#: Known binding differences from twoway (WP-33 section 33-10, syn:SD-20):
#: {"<option or spelling>": "<GAPS4 id>",  # twoway <x> / dash <y>}, by
#: test/known_differences.py's rule (D-33-10.a); every known_problems call
#: over it passes deliberate=ABBREV_DELIBERATE, the differences a ruling
#: keeps ({"<key>": "<ruling id>: <what is kept>"}).
ABBREV_KNOWN = {
    "land:fxsize": "GW-4",  # twoway fxsiz() / dash noted, no key
    "land:fysize": "GW-4",  # twoway fysiz() / dash noted, no key
    "min:fxsize": "GW-4",  # twoway fxsiz / dash declares fxsize in full
    "min:fysize": "GW-4",  # twoway fysiz / dash declares fysize in full
}

ABBREV_DELIBERATE = {
}

#: {option: key}: options dash stores under the key of the twoway option
#: they are a synonym of, so landing there is landing on the option itself
#: (measured, abbrev_truth.json; pinned both ways by
#: TestTheLivePin::test_every_stored_under_row_is_measured).
_STORED_UNDER = {
    "tlabel": "xlabel", "tline": "xline", "tmlabel": "xmlabel",
    "tmtick": "xmtick", "tscale": "xscale", "ttick": "xtick",
    "ttitle": "xtitle", "ttext": "text", "bins": "bin",
    "cmissings": "cmissing", "colorformissing": "colormissing",
}


def _landings(name):
    """The keys landing on option name means: its own, and its synonym's."""
    return {name, _STORED_UNDER.get(name, name)}


def _only(table, prefix):
    """The rows of a results or known table whose key starts with prefix."""
    return {k: v for k, v in table.items() if k.startswith(prefix)}


def _shared_spellings(decls):
    """{spelling: (every option admitting it, in declaration order)} for the
    spellings more than one declaration admits."""
    claims = {}
    for mn, full in decls:
        for L in range(len(mn), len(full) + 1):
            claims.setdefault(full[:L], []).append(full)
    return {p: tuple(v) for p, v in claims.items() if len(set(v)) > 1}


def _twoway_binding(spelling, truth):
    """The option twoway binds `spelling' to, per abbrev_truth.json, or None
    when the fixture does not settle it."""
    r = truth["abbrev_resolution"].get(spelling)
    if r and r.get("stata_resolves_to"):
        return r["stata_resolves_to"]
    hits = [n for n, e in truth["options"].items()
            if n.startswith(spelling) and len(spelling) >= len(e["min_abbrev"])]
    return hits[0] if len(hits) == 1 else None


def test_no_prefix_is_claimed_by_two_options(plot_decls):
    shared = _shared_spellings(plot_decls)
    new = ["%s() -> %s" % (p, ", ".join(v)) for p, v in sorted(shared.items())
           if _SHARED_SPELLINGS.get(p) != v]
    assert not new, (
        "%d spelling(s) are legal abbreviations of more than one option "
        "beyond the pinned list; Stata binds the first declared one without "
        "warning, and a repeated option falls through to the next.\n  "
        % len(new)) + "\n  ".join(new)
    gone = sorted(set(_SHARED_SPELLINGS) - set(shared))
    assert not gone, (
        "no longer shared by two declarations -- take them off "
        "_SHARED_SPELLINGS: %s" % gone)


def test_a_shared_spelling_binds_where_the_user_means_it(truth, plot_decls):
    """First use: the option the spelling is the full name of, else the one
    twoway binds it to.  A spelling neither settles is an ambiguity nobody
    measured, and fails."""
    bad = []
    for p, owners in sorted(_shared_spellings(plot_decls).items()):
        got = _resolves_to(p, plot_decls)
        if p in owners:
            if got != p:
                bad.append("%s() binds to %s(), not to the option of that "
                           "name" % (p, got))
            continue
        want = _twoway_binding(p, truth)
        if want is None:
            bad.append("%s() is admitted by %s and twoway's binding of it is "
                       "not measured" % (p, ", ".join(owners)))
        elif got != want:
            bad.append("%s() binds to %s(), twoway binds it to %s()"
                       % (p, got, want))
    assert not bad, "\n  ".join(bad)


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

    # WP-31 A3b: dash kpi's name() takes nam(), the graph's name() only
    # name(), as twoway's; a spelling written for dash kpi -- its Syntax
    # block and its own section -- is held to dash kpi's declaration first.
    k0 = help_txt.index("{pstd}{ul:KPI card}")
    kpi_spans = ((k0, help_txt.index("{pstd}{ul:", k0 + 1)),
                 (help_txt.index("{marker kpi}"),
                  help_txt.index("{marker server_mode}")))
    bad, seen = [], set()
    for m in re.finditer(r"\{cmdab:([^}]*)\}", help_txt):
        tok = m.group(1)
        if ":" not in tok or " " in tok:
            continue
        mn, rest = tok.split(":", 1)
        full = (mn + rest).split("(")[0]
        if not re.match(r"^[a-z][a-z0-9]*$", mn) or not full:
            continue
        if (mn, full) in seen:
            continue
        seen.add((mn, full))

        order = (("a plot/graph", plot), ("dash kpi", kpi),
                 ("dash build", build))
        if any(a <= m.start() < b for a, b in kpi_spans):
            order = (order[1], order[0], order[2])
        for where, table in order:
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

    # dash.sthlp's {cmdab:} tokens hold 54 distinct spellings this checks
    # (measured 24sep2026; 47 before the S3 batch's table of the ci band's
    # options added ac, alc, alw, alp, fc, fi and lc).  59 since WP-28
    # batch 2 (S16, GAPS2 X2) documented colorlev, colorvarminm, zlab, zti
    # and zsc, each accepted by twoway (measured 30sep2026, rc 0; colorle,
    # colorvarmin and zs refused, rc 198).  Markup that
    # stopped matching the pattern -- {opt}, say -- would leave the loop
    # nothing to check.
    # 68 since WP-30 P1.14a documented the named styles' minimums: psty,
    # mst, mls, ls, cls, ast, al, bst and bl (twoway's, A01-A10 of
    # test/fixtures/named_style_truth.json).
    # 68 -> 69: WP-30 P1.24 documented mlabv:position(), twoway's minimum.
    # 69 -> 70: and mlabt:extstyle() (part 2).
    # 70 -> 77: WP-30 P1.6 documented the seven time-axis minimums, tl,
    # ttic, tml, tmt, tt, tsc and tli (twoway's, taxis_truth.json ab_*).
    # 77 -> 76: A3d jitter() is documented by its full name, twoway's
    # minimum; jit:ter is gone.
    # 76 -> 88: WP-31 C8b documented colorr, colorst, colore, colorli,
    # colorformiss, colorkeysran, colorkeysrev, colorotherlab,
    # colorusepleg, cleg, pleg and pcyc (twoway's minimums).
    # 88 -> 89: WP-31 H2l documented br:ush(), dash's own option (twoway
    # has no brush), at the minimum its BRush() declaration takes.
    assert len(seen) == 89, (
        "%d documented abbreviations were checked" % len(seen))
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
    # Any Mata return type, not three: a table brought back as, say,
    # `string rowvector _expand_optkey(' or `function _expand_optkey(' was
    # not a definition to the pattern above.  dash_parse.mata declares
    # real scalar, string scalar, string rowvector and void today.
    _type = (r"(?:transmorphic|numeric|real|complex|string|pointer(?:\([^)]*\))?"
             r"|struct\s+\w+|class\s+\w+|void|function"
             r"|scalar|vector|rowvector|colvector|matrix)")
    leftovers += [
        n for n in ("_expand_optkey", "_dash_expand_opts_str")
        if n not in leftovers
        and re.search(r"^\s*(?:%s\s+)+%s\s*\(" % (_type, n), src, re.M)
    ]
    assert re.search(r"^\s*(?:%s\s+)+_dash_\w+\s*\(" % _type, src, re.M), (
        "the definition pattern matches no function in dash_parse.mata")
    assert not leftovers, (
        "dash_parse.mata still defines %s.  TR-04.2: once the syntax "
        "declarations carry the minimum abbreviations, the hard-coded table "
        "is not just redundant, it rewrites option keys before -syntax- sees "
        "them and is the source of the seven mis-mappings."
        % " and ".join(leftovers))


# ============================================================
# 8. TR-23.6 (GAPS.md M4) -- each parser comment and fold once, none dead
#
# dash.ado carried the generator NOTE twice at the head of both option
# parsers, and the t()/b()/l()/r() fold twice in _dash_parse_graph_opts.  The
# reason both folds gave -- that T1title's minimum is t1, so t(), b(), l()
# and r() had to be declared on their own -- was wrong: a digit ends the run
# of capitals (see _syntax_options), so T1title() takes t() itself.  T(),
# B(), L() and R() were declared after T1title() .. R2title(), which admit
# their only spelling first, so -syntax- reached them only for a THIRD t()
# written after t1title() and t2title() -- and the fold then dropped that
# value without naming it.  The plot-level parser never declared them at
# all and folded locals -syntax- never set.
# ============================================================
_PARSERS = ("_dash_parse_plot_opts", "_dash_parse_graph_opts")

#: `if `: length local a' & !`: length local t' local t : copy local a` --
#: alias a folded into t, read and copied by value.  The form it replaced
#: (24sep2026), `if `"`a'"' != "" & `"`t'"' == "" local t `"`a'"'`, put the
#: user's text back on a command line, where a macro in it was expanded a
#: second time (test_json_escaping.cscript JSE-65).  Both forms are matched,
#: so a fold written the old way is still one the checks below see.
_FOLD = re.compile(
    r"""if `: length local (\w+)' & !`: length local (\w+)' """
    r"""local \2 : copy local \1\b"""
    r"""|if `"`(\w+)'"' != "" & `"`(\w+)'"' == "" local \4 `"`\3'"'""")


def _folds(body):
    """[(alias, target), ...], one per fold statement in `body', in order."""
    return [(m.group(1) or m.group(3), m.group(2) or m.group(4))
            for m in _FOLD.finditer(body)]


def _bodies(programs=None):
    """{program: body} for `programs', or for every program with a syntax
    statement when None."""
    src = _read(ADO_PATH)
    if programs is None:
        programs = re.findall(r"^program define (\w+)", src, re.M)
    out = {}
    for prog in programs:
        body = _program_body(src, prog)
        assert body is not None, "program %s not found in dash.ado" % prog
        out[prog] = body
    return out


def test_the_tr_23_6_scans_see_what_they_look_for():
    """Every check below is vacuous if its scan finds nothing."""
    bodies = _bodies(_PARSERS)
    folds = _folds(bodies["_dash_parse_plot_opts"])
    assert ("mlg", "mlabgap") in folds and ("pbgc", "plotbgcolor") in folds
    assert ("pbgc", "plotbgcolor") in _folds(bodies["_dash_parse_graph_opts"])
    # Exactly 12 programs declare options with -syntax- (measured 24sep2026:
    # _dash_do_render, the two parsers, _dash_limit, _dash_browser_wanted,
    # _dash_dashboard_browser, _dash_kpi, _dash_prepare_spec, _dash_build,
    # _dash_serve_spec, _dash_open_page, the one browser opener, since
    # WP-24, and _dash_by_panels, since the S3 batch's by() answers).  ">= 6" let four of them drop out of every whole-file scan
    # below -- a `program' written without `define' does.  Flipped to 13
    # (WP-29 P0.1): _dash_sort_names declares SORT1(namelist), the check
    # twoway makes of sort()'s names; 15 since WP-29 P0.12b, P0.14:
    # _dash_tmp_preview and _dash_tmp_close, the private temporary
    # folder's programs, take opened()/noted() and dir().  16 at WP-30
    # batch 4, whose list includes _dash_browser_wanted (P1.27) and
    # _dash_stylelist_bind, the probe that binds a quoted stylelist value.
    with_syntax = sorted(p for p, b in _bodies().items() if _syntax_options(b))
    assert len(with_syntax) >= 6
    # 16 -> 17: WP-30 P1.24's _dash_mlabv_parse declares MLABVposition(name),
    # twoway's own reading of mlabvposition().
    # 17 -> 18: WP-30 P1.10's _dash_at_opts reads a text() copy's
    # sub-options with twoway's own syntax statements.
    # 18 -> 19: C4 WP-31's _dash_fit_points declares the arguments it
    # hands twoway's fit generators.
    # 19 -> 20: B4b WP-31's _dash_contour_split declares contour's
    # options, which the plot parser's syntax has no room left for.
    # 20 -> 21: B4b _dash_le_typed declares LE() alone, to tell le()
    # typed from level() on the contour types.
    # 21 -> 22: D5 WP-31's _dash_aspect_split reads aspectratio()'s
    # placement() with twoway's own syntax statement; 22 -> 23: D8
    # _dash_label_split declares yvarlabel() and xvarlabel(), which the
    # plot parser's syntax has no room for.  23 -> 24: WP-33 33-06
    # _dash_image (dash image using <file>, name() caption() alt() link()).
    assert len(with_syntax) == 24, with_syntax
    assert {"_dash_browser_wanted", "_dash_stylelist_bind"} <= set(with_syntax)
    assert {"_dash_tmp_preview", "_dash_tmp_close"} <= set(with_syntax)
    assert "_dash_open_page" in with_syntax, with_syntax
    # The comment lines the duplicate-block scan reads, per parser: 108
    # in the plot parser and 71 in the graph parser (measured 24sep2026,
    # after the S3 batch's notes on the fitarea options and on log and
    # logit; 95 after the note on why the text options are declared
    # asis; and 114 after P1.1a's note on the style options' quotes,
    # 03oct2026).  It
    # was ">= 20", for the plot parser alone, and the plot parser split in
    # two -- its second half moved into a program of its own, a pasted
    # duplicate comment block with it -- still showed the scan 38 comment
    # lines: every check below passed on the half they could see.  A parser
    # that gains or loses comments moves these on purpose.
    comments = {prog: sum(1 for ln in body.split("\n")
                          if ln.strip().startswith("//"))
                for prog, body in bodies.items()}
    # 108 -> 114: P1.1a explains the asis style options and their
    # normalisation.  114 -> 117: P1.5 names xvarformat()'s measured
    # minimum.
    # 117 -> 120: P1.14a's note on the named styles in the sreturn
    # block and the fitarea comment's rewording.
    # 120 -> 124: P1.14b's notes on dstyle/dlstyle/bmlinestyle (pending
    # three lines, sreturn one).
    # 124 -> 125: P1.24's pending comment is one line shorter (two), and
    # the mlabvposition sreturn gains two.  125 -> 124: part 2 drops the
    # pending comment (two) and gives the mlabtextstyle sreturn one.
    # 124 -> 130: P1.8a's notes on cmissings() (three) and on the
    # cmissing and connect pending lines (three).
    # 130 -> 132: P1.8b's note on recast(), recastas() and type() in the
    # sreturn block (two).
    # 132 -> 134 and 71 -> 73: P1.6's note on the tmlabel and tmtick
    # pending lines (two, in each parser).
    # 134 -> 137: C1 the note on the mangle/barbsize/headlabel sreturn
    # lines (three).
    # 137 -> 139: A4 the note on the mlalign pending line (two).
    # 139 -> 144: C4 the note on the fit options' sreturn lines (five);
    # 144 -> 147: C5 the note on the gap ... nodropbase sreturn lines
    # (three).
    # 147 -> 144: C6 the note on the cmissing and connect pending lines
    # goes with them (three).
    # 144 -> 151: C8b the notes on the colorformissing() fold (four) and
    # on colorvar(i.var) (three).
    # 151 -> 156: B5b the pending note -- bmlinestyle's two lines, the
    # d-options' four and dlalign's two for dstyle/dlstyle's three.
    # 156 -> 154 and 73 -> 71: D1 the note on the tmlabel and tmtick
    # pending lines goes with them (two, in each parser).
    # 154 -> 159: B4b the notes on contour's split (three), its sreturn
    # lines and its pending lines (one each).  71 -> 72: A3b the note on
    # NAMe, now NAME, is one line longer.
    # 72 -> 73: D5 the overhangs' pending note goes (one) and the
    # aspectratio() split's note comes (two); 159 -> 161: D8 the note on
    # _dash_label_split's call (two); 161 -> 162: E3 mlalign()'s pending
    # note becomes three lines.
    # 162 -> 163 and 73 -> 75: H2t the notes on table's fold (one in the
    # plot parser, two in the graph parser).
    # 163 -> 167: WP-32 the note on the refused pending lines (five) for
    # the filter() line's (one).
    # 167 -> 172 and 75 -> 77: WP-32 the notes on the silent, play() and
    # replace refusals (c2's later commits).
    assert comments == {"_dash_parse_plot_opts": 172,
                        "_dash_parse_graph_opts": 77}, comments
    # Every fold, in either form: 11 in the plot parser and 7 in the graph
    # parser (measured 24sep2026).  A fold the pattern stopped matching --
    # rewritten in a third form -- would leave the fold checks below
    # nothing to look at.
    assert len(folds) == 11, folds
    assert len(_folds(bodies["_dash_parse_graph_opts"])) == 7


def test_no_comment_block_is_repeated_in_a_parser():
    """Three or more comment lines appearing twice in one parser is a pasted
    duplicate (the generator NOTE was, in both).

    A structural guard over dash.ado's text, deliberately: a comment exists
    only in the source, so no run of the parser can show a pasted one."""
    bad = []
    for prog, body in _bodies(_PARSERS).items():
        lines = [ln.strip() for ln in body.split("\n")]
        first = {}
        for i in range(len(lines) - 2):
            win = tuple(lines[i:i + 3])
            if not all(w.startswith("//") and len(w) > 3 for w in win):
                continue
            if win in first and i >= first[win] + 3:
                bad.append("%s repeats the comment block starting %r"
                           % (prog, win[0]))
            first.setdefault(win, i)
    assert not bad, "\n  ".join(sorted(set(bad)))


def test_no_fold_is_repeated_in_a_parser():
    bad = []
    for prog, body in _bodies(_PARSERS).items():
        folds = _folds(body)
        for f in sorted(set(folds)):
            if folds.count(f) > 1:
                bad.append("%s folds %s() into %s() %d times"
                           % (prog, f[0], f[1], folds.count(f)))
    assert not bad, "\n  ".join(bad)


def test_every_fold_reads_an_option_its_parser_declares():
    """A fold whose alias the parser's own -syntax- never declares reads a
    local that is always empty: dead code."""
    bad = []
    for prog, body in _bodies(_PARSERS).items():
        declared = {full for _, full in _syntax_options(body)}
        bad += ["%s folds %s() into %s(), and declares no %s()"
                % (prog, a, t, a) for a, t in _folds(body) if a not in declared]
    assert not bad, "\n  ".join(bad)


def test_no_declaration_is_shadowed_by_an_earlier_one():
    """An option every spelling of which an earlier declaration admits is
    never bound by its own name: -syntax- reaches it only when a repeated
    option finds the earlier ones already filled."""
    bad = []
    for prog, body in sorted(_bodies().items()):
        decls = _syntax_options(body)
        for i, (mn, full) in enumerate(decls):
            spellings = [full[:L] for L in range(len(mn), len(full) + 1)]
            takers = [_resolves_to(s, decls[:i]) for s in spellings]
            if all(takers):
                bad.append("%s: %s() -- %s" % (prog, full, ", ".join(
                    "%s() binds to %s()" % (s, t)
                    for s, t in zip(spellings, takers))))
    assert not bad, (
        "declared options -syntax- never binds by their own name:\n  "
        + "\n  ".join(bad))


# ============================================================
# WP-29 P0.5: the axis route's spellings are twoway's, and the seven
# graph-key lists of dash.ado carry the four new second-axis keys.
# ============================================================
class TestTheAxisRouteKnowsDashsSpellings:
    """dash_parse.mata's ``_dash_axfam`` is twoway's ParseAndLogAxes table
    (graph_g.class:1300-1422): optnames SCale Labels MLabels TICks MTicks
    Title LInes, so the whole option names' minimums -- the side letter
    included -- are xt/yt 2, xl 2, xml 3, xtic 4, xmt 3, xli 3, xsc 3, and
    the full names are twoway's plurals."""

    _ROW = re.compile(r'"(\w+)",\s*"(\w+)",\s*"(\w+)",\s*"(\d)",\s*"(\d)",'
                      r'\s*"(\w*)"')

    def _table(self):
        src = _read(MATA_PATH)
        m = re.search(r"^string matrix _dash_axfam\(\)\s*\{(.*?)^\}", src,
                      re.S | re.M)
        assert m, "dash_parse.mata defines no _dash_axfam()"
        return {r[0]: r[1:] for r in self._ROW.findall(m.group(1))}

    def test_mata_family_minimums_match_twoway(self):
        t = self._table()
        assert list(t) == ["title", "label", "mlabel", "tick", "mtick",
                           "line", "scale"]
        assert [int(t[f][2]) for f in t] == [2, 2, 3, 4, 3, 3, 3]
        assert {f: t[f][0] for f in t} == {
            "title": "title", "label": "labels", "mlabel": "mlabels",
            "tick": "ticks", "mtick": "mticks", "line": "lines",
            "scale": "scale"}
        # twoway's family order: SCale Labels MLabels TICks MTicks Title LInes
        assert {f: int(t[f][3]) for f in t} == {
            "scale": 1, "label": 2, "mlabel": 3, "tick": 4, "mtick": 5,
            "title": 6, "line": 7}
        # dash draws title, label, tick, line and scale on axis 2, and
        # (Flipped, WP-31 D1: "" was wrong once minor ticks and labels are
        # drawn) mlabel and mtick
        assert {f: t[f][4] for f in t} == {
            "title": "title2", "label": "label2", "mlabel": "mlabel2",
            "tick": "tick2", "mtick": "mtick2", "line": "line2",
            "scale": "scale2"}

    def test_the_seven_graph_key_lists_agree(self):
        src = _read(ADO_PATH)
        lists = []
        for m in re.finditer(r"foreach (?:gk|gkey) in ((?:[^{]|\n)*?)\{",
                             src):
            words = m.group(1).replace("///", " ").split()
            lists.append(tuple(words))
        assert len(lists) == 7, len(lists)
        assert len(set(lists)) == 1, set(lists)
        for key in ("ytick2", "xtick2", "yline2", "xline2"):
            assert key in lists[0], key


class TestJitterMinimum:
    """WP-31 A3d: twoway's minimum for jitter() is the full name (measured
    14oct2026, test_abbreviations.cscript U15-06: j() ji() jit() jitt()
    jitte() and bare jit are "option <word> not allowed", r(198)).  dash
    declares JITTER, and refuses the shorter spellings in twoway's words
    (_dash_refuse_jit), where -syntax- would leave them to the note."""

    def test_dash_declares_twoways_minimum(self):
        ado = open(ADO_PATH, encoding="utf-8").read()
        assert "JITTER(string asis)" in ado
        assert "JITter(" not in ado

    def test_the_short_spellings_are_refused(self):
        ado = open(ADO_PATH, encoding="utf-8").read()
        body = ado[ado.index("program define _dash_refuse_jit"):]
        body = body[:body.index("\nend\n")]
        assert "(j|ji|jit|jitt|jitte)" in body
        assert '"type mismatch"' in body and "exit 109" in body
        assert "exit 198" in body
        seg = ado[ado.index("_dash_refuse_unbound _dash_parse_plot_opts"):]
        assert seg.index("_dash_refuse_jit") < seg.index("_dash_refuse_foreign")

    def test_the_options_after_the_comma_are_checked_too(self):
        """(scatter mpg weight), jit(5) is "option jit() not allowed",
        r(198), in twoway (U15-06); dash named it in its note."""
        ado = open(ADO_PATH, encoding="utf-8").read()
        g = ado[ado.index("_dash_refuse_foreign _dash_parse_graph_opts - "):]
        g = g[:g.index("_dash_opts_repeats _dash_parse_graph_opts")]
        assert "_dash_refuse_jit" in g


# ============================================================
# WP-33 syn:SD-20: every option dash declares is measured
#
# abbrev_truth.json measured 93 options and listed 28 as unprobeable;
# about 120 more that dash's two parsers declare had no measurement at
# all, and the hand-written reason for bgcolor() said twoway has no such
# option, which is false (twowaygraph_g.class declares BGColor(string);
# bgc(red), bgcol(red) and bgcolor(red) are rc 0 in twoway).
# ============================================================
def _unmeasured(truth, plot_decls):
    """The declared options the fixture neither measures nor gives a
    reason for (the recompute one-liner of section 33-10's Evidence)."""
    return [full for _mn, full in plot_decls
            if full not in truth["options"]
            and full not in truth["unprobeable"]]


class TestEveryDeclaredOptionIsMeasured:
    def test_every_declared_option_is_measured(self, truth, plot_decls):
        missing = _unmeasured(truth, plot_decls)
        assert not missing, "%d declared option(s) unmeasured: %s" % (
            len(missing), " ".join(missing))

    def test_bgcolor_is_measured_as_twoways(self, truth):
        assert "bgcolor" in truth["options"], truth["unprobeable"].get(
            "bgcolor")
        assert truth["options"]["bgcolor"]["min_abbrev"] == "bgc"
        rows = [r for r in truth.get("dash_abbrev_stata_rejects", [])
                if r.startswith("bgc:")]
        assert not rows, rows

    def test_no_rejection_contradicts_another_oracle(self, truth):
        with open(UNKNOWN_FIXTURE, encoding="utf-8") as fh:
            probes = json.load(fh)["probes"]
        bad = []
        for name, reason in sorted(truth["unprobeable"].items()):
            if not reason.startswith("twoway rejected the full option name"):
                continue
            p = probes.get(name)
            if p is not None and p.get("twoway_rc") == 0:
                bad.append("%s: abbrev_truth says twoway rejects it; "
                           "unknown_option_truth.json measured rc 0" % name)
        assert not bad, "\n  ".join(bad)

    def test_every_known_difference_is_open(self, truth, plot_decls):
        assert dead_rows(ABBREV_KNOWN, "abbrev") == []
        assert not set(ABBREV_KNOWN) & set(ABBREV_DELIBERATE)
