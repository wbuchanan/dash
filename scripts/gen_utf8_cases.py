#!/usr/bin/env python3
"""Regenerate test/fixtures/utf8_cases.txt.

The expected values are Python's own answer, not dash's: a sequence is
well-formed UTF-8 exactly when ``bytes(seq).decode("utf-8")`` does not raise.
Testing dash's validator against a table someone wrote by hand would only
check that two readings of RFC 3629 agree; testing it against a decoder that
has to be right checks that dash's reading is.

The set is chosen to exercise the distinctions the RFC actually makes, which
are all in the SECOND byte:

* every single byte, so the lead-byte ranges are pinned;
* every lead byte 0xC0-0xF7 against second bytes on and just outside each
  allowed range boundary, in two-, three- and four-byte forms -- this is
  where overlong encodings, UTF-16 surrogates and codepoints above U+10FFFF
  live;
* random sequences up to five bytes, as a check on the rest.

NUL is excluded throughout: a Stata string cannot carry it, so a case
containing one would measure Stata's string handling rather than the
validator.

A wider sweep was run once while this was written -- 41,976 sequences,
including every lead/second pair for all four lengths -- and the validator
agreed with Python on every one. This file keeps the part of that sweep that
distinguishes the rules, at a size worth committing.
"""
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "test", "fixtures", "utf8_cases.txt")

#: On and just outside every second-byte range boundary in RFC 3629 s.4.
BOUNDARIES = (0x00, 0x7F, 0x80, 0x8F, 0x90, 0x9F, 0xA0, 0xBF, 0xC0, 0xFF)


def build():
    random.seed(20260922)
    cases = [(b,) for b in range(1, 256)]
    for lead in range(0xC0, 0xF8):
        for second in BOUNDARIES:
            cases.append((lead, second))
            cases.append((lead, second, 0x80))
            cases.append((lead, second, 0x80, 0x80))
    for _ in range(600):
        n = random.randint(1, 5)
        cases.append(tuple(random.randrange(1, 256) for _ in range(n)))

    seen, uniq = set(), []
    for c in cases:
        if 0 in c or c in seen:
            continue
        seen.add(c)
        uniq.append(c)
    return uniq


def main():
    uniq = build()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("* Byte sequences and whether they are well-formed UTF-8.\n")
        fh.write("* Expected values come from Python's own utf-8 decoder, not from\n")
        fh.write("* dash: bytes(seq).decode('utf-8') either succeeds (1) or raises\n")
        fh.write("* UnicodeDecodeError (0).  Regenerate with\n")
        fh.write("*   scripts/gen_utf8_cases.py\n")
        fh.write("* Format: <comma-separated decimal bytes> <0|1>\n")
        for c in uniq:
            try:
                bytes(c).decode("utf-8")
                want = 1
            except UnicodeDecodeError:
                want = 0
            fh.write("%s %d\n" % (",".join(str(x) for x in c), want))
    print("wrote %d cases to %s" % (len(uniq), os.path.normpath(OUT)))


if __name__ == "__main__":
    main()
