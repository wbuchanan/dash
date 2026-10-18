"""No secret in the tree (WP-31 I6, S60 D-60g).

Every file git tracks is scanned as text for the shapes of the keys a
leak would carry: an AWS access key id, a PEM private key, a GitHub
personal token, a Slack token, and a dashboard key handed to the server
in DASH_SERVE_TOKEN=<value> form.  The suite's own dashboard key
(test/serve_token_probe.py TEST_TOKEN) is a published test value and the
one DASH_SERVE_TOKEN value allowed.  The maintainer's e-mail address
(read from `git config user.email', never written here) may appear only in
the planning records under .ultraplan/, which are not shipped.

This file holds the patterns, so it is the one file not scanned; the
planted samples below are built from fragments at run time, so the
repository never holds a matching string.
"""
import os
import re
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from serve_token_probe import TEST_TOKEN  # noqa: E402

#: (name, pattern) of every secret shape the scan looks for.
PATTERNS = (
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PEM private key",
     re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]+")),
    ("dashboard key", re.compile(r"DASH_SERVE_TOKEN=([A-Za-z0-9_-]{20,})")),
)

#: Where the maintainer's address may appear: the planning records.
_EMAIL_ALLOWED = (".ultraplan/",)


def _tracked():
    p = subprocess.run(["git", "-C", _REPO, "ls-files", "-z"],
                       capture_output=True)
    if p.returncode != 0:
        pytest.skip("not a git working tree")
    return [f for f in p.stdout.decode("utf-8", "replace").split("\0") if f]


def _text(rel):
    try:
        with open(os.path.join(_REPO, rel), "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    if b"\0" in raw[:8192]:
        return None
    return raw.decode("utf-8", "replace")


def _findings(text):
    out = []
    for name, pat in PATTERNS:
        for m in pat.finditer(text):
            if name == "dashboard key" and m.group(1) == TEST_TOKEN:
                continue
            out.append(name)
    return out


def _email():
    p = subprocess.run(["git", "-C", _REPO, "config", "user.email"],
                       capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def test_no_pattern_matches():
    me = os.path.relpath(os.path.abspath(__file__), _REPO)
    email = _email()
    bad = []
    files = _tracked()
    assert len(files) > 500, len(files)
    for rel in files:
        if rel == me:
            continue
        text = _text(rel)
        if text is None:
            continue
        bad += ["%s: %s" % (rel, n) for n in _findings(text)]
        if (email and email in text
                and not rel.startswith(_EMAIL_ALLOWED)):
            bad.append("%s: the maintainer's e-mail address" % rel)
    assert not bad, bad


def test_the_patterns_catch_a_planted_sample():
    samples = {
        "AWS access key id": "AK" + "IA" + "Q" * 16,
        "PEM private key": "-----BEGIN " + "RSA PRIVATE" + " KEY-----",
        "GitHub token": "gh" + "p_" + "a1" * 18,
        "Slack token": "xo" + "xb-" + "123-abc",
        "dashboard key": "DASH_SERVE" + "_TOKEN=" + "k" * 43,
    }
    for name, sample in samples.items():
        assert _findings("x = '%s'" % sample) == [name], name


def test_the_suites_own_key_is_allowed():
    assert _findings("DASH_SERVE" + "_TOKEN=" + TEST_TOKEN) == []
