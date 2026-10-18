"""A Mata string literal is not a C string literal.

Mata keeps every character between the quotes.  Measured with the console
binary: ``strlen("\\\\")`` is 2 and ``"\\\\" == char(92)`` is 0.  A test of a
character against ``"\\\\"``, written to mean "one backslash", is therefore
never true, and dash_parse.mata has shipped that mistake three times:

* ``_dash_json_escape`` wrote four backslashes for one;
* ``_dash_json_get_str`` never decoded an escape;
* ``_dash_extract_qual_vars`` never stepped over one, so the quote of ``\\"``
  ended the value and every variable an ``if`` named after its first string
  literal was left out of the export -- for
  ``make != "AMC Concord" & foreign == 1`` both render modes warned "if_expr
  filter skipped" and drew all 74 cars instead of 22 (measured 23sep2026 at
  ad13a0f; test_json_escaping.cscript JSE-11..18).

The file writes the backslash as ``char(92)``, as its comments say.  This
keeps it so: no literal in its Mata code is ``"\\\\"``, and no character is
compared (``==`` / ``!=``) with a literal holding a backslash.  A backslash
in a literal for any other purpose -- a printf format's ``\\n``, say -- is
left alone.
"""
import os

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_MATA = os.path.join(_HERE, "..", "dash_parse.mata")

_BS = chr(92)


def _mata_segments(src):
    """The Mata code of *src* as ``(kind, line, text)`` segments in order.

    kind is ``"str"`` for a string literal (text is what is between the
    quotes) and ``"code"`` for what lies between literals.  The code is the
    lines after the one that is exactly ``mata:`` up to the one that is
    exactly ``end``; ``//`` and ``/* */`` comments are dropped.  A simple
    literal runs to the next double quote -- Mata has no escapes -- and a
    compound one from `" to the "' that closes it, nesting.
    """
    lines = src.split("\n")
    try:
        first = next(i for i, l in enumerate(lines) if l.strip() == "mata:")
    except StopIteration:
        return []
    body = []
    for l in lines[first + 1:]:
        if l.strip() == "end":
            break
        body.append(l)
    text = "\n".join(body)
    segs, code = [], []
    line, code_line = first + 2, first + 2
    i, n = 0, len(text)

    def flush():
        if code:
            segs.append(("code", code_line, "".join(code)))
            code.clear()

    while i < n:
        c = text[i]
        if text.startswith("//", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            end = n if j < 0 else j + 2
            line += text.count("\n", i, end)
            i = end
            continue
        if text.startswith('`"', i) or c == '"':
            flush()
            if c == '"':
                j = text.find('"', i + 1)
                j = n if j < 0 else j
                segs.append(("str", line, text[i + 1:j]))
                i = j + 1
            else:
                depth, j = 1, i + 2
                while j < n and depth:
                    if text.startswith('`"', j):
                        depth, j = depth + 1, j + 2
                    elif text.startswith('"\'', j):
                        depth, j = depth - 1, j + 2
                    else:
                        j += 1
                segs.append(("str", line, text[i + 2:max(i + 2, j - 2)]))
                line += text.count("\n", i, j)
                i = j
            code_line = line
            continue
        if c == "\n":
            line += 1
        if not code:
            code_line = line
        code.append(c)
        i += 1
    flush()
    return segs


def _backslash_comparisons(src):
    """``(line, literal)`` for each literal that is exactly two backslashes,
    or that holds a backslash and is an operand of ``==`` or ``!=``."""
    segs = _mata_segments(src)
    bad = []
    for k, (kind, line, text) in enumerate(segs):
        if kind != "str" or _BS not in text:
            continue
        before = segs[k - 1][2] if k > 0 and segs[k - 1][0] == "code" else ""
        after = (segs[k + 1][2] if k + 1 < len(segs)
                 and segs[k + 1][0] == "code" else "")
        compared = (before.rstrip().endswith(("==", "!="))
                    or after.lstrip().startswith(("==", "!=")))
        if text == _BS * 2 or compared:
            bad.append((line, text))
    return bad


@pytest.fixture(scope="module")
def mata_src():
    with open(_MATA, encoding="utf-8") as fh:
        return fh.read()


class TestNoCharacterIsComparedWithABackslashLiteral:

    def test_the_scan_reads_the_mata_code(self, mata_src):
        """Guards the guard: a scan that found nothing would pass anything."""
        segs = _mata_segments(mata_src)
        lits = [t for kind, _l, t in segs if kind == "str"]
        assert len(lits) > 200, len(lits)
        for want in ("True", "if_expr", "0123456789abcdef"):
            assert want in lits, want
        # Comment text is not code: this file's own comments quote "\\".
        assert not any("strlen(" in t for t in lits)
        # The count and the three literals prove the scan reached line
        # 2023 of 2820 (measured 24sep2026), not _dash_json_get_str at
        # 2447, one of the three functions that shipped the idiom.  It must
        # read every one of them, and on to the file's LAST `end' -- so an
        # early `end', or a second Mata block, cannot leave code unread.
        code = "".join(t for kind, _l, t in segs if kind == "code")
        for fn in ("string scalar _dash_json_escape(",
                   "void _dash_extract_qual_vars(",
                   "void _dash_json_get_str("):
            assert fn in code, f"the scan never read {fn}...)"
        # A literal never spans lines: one that does ran past its closing
        # quote and swallowed the code after it.
        assert not any("\n" in t for t in lits), [
            t[:60] for t in lits if "\n" in t]
        last_end = max(i for i, l in enumerate(mata_src.split("\n"), 1)
                       if l.strip() == "end")
        kind, start, text = segs[-1]
        assert start + text.count("\n") >= last_end - 1, (
            f"the scan stops at line {start + text.count(chr(10))}; the "
            f"Mata code runs to line {last_end}")

    def test_the_detector_flags_the_idiom_and_nothing_else(self):
        bs = _BS
        src = "\n".join([
            "*! header",
            "mata:",
            'x = ch == "' + bs * 2 + '"',            # 3: the idiom
            'if ("' + bs + 't" != c) y = 1',          # 4: compared, reversed
            's = "' + bs * 2 + '"',                    # 5: the literal itself
            'if (ch == char(92)) z = 1',               # fine
            'errprintf("done.' + bs + 'n")',           # fine: a format
            'u = "a//b" + "' + bs + 'd"',              # fine: not compared
            '// ch == "' + bs * 2 + '" in a comment',  # fine: a comment
            '/* ch == "' + bs * 2 + '"',               # fine: a block comment
            '   still the comment */',
            'w = `"a "' + bs * 2 + '" b"\'',           # fine: inside a
            "end",                                     # compound literal
            'v = ch == "' + bs * 2 + '"',              # after end: not Mata
        ])
        got = [line for line, _t in _backslash_comparisons(src)]
        assert got == [3, 4, 5], got

    def test_dash_parse_compares_no_character_with_one(self, mata_src):
        bad = _backslash_comparisons(mata_src)
        assert not bad, (
            "dash_parse.mata compares a character with a Mata literal "
            "holding a backslash, or writes the literal \"" + _BS * 2 +
            "\".  Mata does not collapse a doubled backslash: strlen(\"" +
            _BS * 2 + "\") is 2, so such a comparison is never true.  Write "
            "the backslash as char(92).  Lines: " +
            ", ".join("%d (%r)" % b for b in bad))
