"""No secret in the tree (WP-31 I6, S60 D-60g).

Every file git tracks is scanned as text for the shapes of the keys a
leak would carry: an AWS access key id, a PEM private key, a GitHub
personal token, a Slack token, and a dashboard key handed to the server
in DASH_SERVE_TOKEN=<value> form.  The suite's own dashboard key
(test/serve_token_probe.py TEST_TOKEN) is a published test value and the
one DASH_SERVE_TOKEN value allowed.  The maintainer's e-mail address
(read from `git config user.email', never written here) may appear only in
the planning records under .ultraplan/ and where ruling D38 publishes it
as the support contact (dash.pkg, dash.sthlp, README.md).

This file holds the patterns, so it is the one file not scanned; the
planted samples below are built from fragments at run time, so the
repository never holds a matching string.
"""
import base64
import getpass
import os
import re
import socket
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

#: Where the maintainer's address may appear: the planning records (and
#: their .ultraplan-archive-* copies), and
#: the three places the maintainer's ruling D38 (18oct2026) publishes it
#: as the package's support contact -- dash.pkg's `d Support:' line,
#: dash.sthlp's Author section and README.md.  It is a contact, not a
#: secret; every key pattern above is still refused in these files.
_EMAIL_ALLOWED = (".ultraplan/", ".ultraplan-archive-")
# test/test_readme.py pins the address those three files must give (D38).
_EMAIL_ALLOWED_FILES = frozenset({"dash.pkg", "dash.sthlp", "README.md",
                                  "test/test_readme.py"})


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
                and not rel.startswith(_EMAIL_ALLOWED)
                and rel not in _EMAIL_ALLOWED_FILES):
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


def test_the_contact_files_still_refuse_keys():
    """D38's three files, and the test that pins their address, are exempt
    from the address check only."""
    assert _EMAIL_ALLOWED_FILES == {"dash.pkg", "dash.sthlp", "README.md",
                                    "test/test_readme.py"}
    # README.md arrives with S59 (batch 20); the two shipped files exist.
    assert _text("dash.pkg") is not None and _text("dash.sthlp") is not None
    for rel in sorted(_EMAIL_ALLOWED_FILES):
        text = _text(rel)
        if text is not None:
            assert _findings(text) == [], rel


# ---- the gallery (WP-33 33-08, D-33-08.l) -----------------------------------
# Every file under docs/gallery/ (built only at WP-50's closeout) and the
# README text between the gallery markers must name no machine path, no
# user, host or licensee name and not the maintainer's address, payloads
# encoded as base64 included.  $DASH_GALLERY_DIR and $DASH_GALLERY_README
# point the scan at a scratch build.

_GALLERY_START = "<!-- dash-gallery:start -->"
_GALLERY_END = "<!-- dash-gallery:end -->"
_GALLERY_PATHS = (
    re.compile(r"(?<![\w.])/(Users|private|var|tmp|home|Applications|Volumes|opt)/"),
    re.compile(r"\b[A-Za-z]:\\"),
    re.compile(r"file://"),
    re.compile(r"~/"),
    re.compile(r"Licensed to"),
    re.compile(r"Serial number"),
)
_B64_URI = re.compile(r"data:[^,;]*;base64,([A-Za-z0-9+/=]{64,})")
_B64_RUN = re.compile(r"[A-Za-z0-9+/=]{200,}")


def _gallery_texts():
    """(where, text) of every gallery file and of the README block, each base64
    payload decoded and added as its own text."""
    gdir = os.environ.get("DASH_GALLERY_DIR") or os.path.join(_REPO, "docs", "gallery")
    readme = os.environ.get("DASH_GALLERY_README") or os.path.join(_REPO, "README.md")
    out = []
    if os.path.isdir(gdir):
        for base, _dirs, files in os.walk(gdir):
            for f in sorted(files):
                p = os.path.join(base, f)
                with open(p, "rb") as fh:
                    out.append((os.path.relpath(p, gdir), fh.read().decode("utf-8", "replace")))
    if os.path.exists(readme):
        with open(readme, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        if _GALLERY_START in text and _GALLERY_END in text:
            a = text.index(_GALLERY_START)
            out.append(("README block", text[a:text.index(_GALLERY_END, a)]))
    decoded = []
    for where, text in out:
        runs = [m.group(1) for m in _B64_URI.finditer(text)]
        runs += [m.group(0) for m in _B64_RUN.finditer(text)]
        for s in runs:
            try:
                raw = base64.b64decode(s + "=" * (-len(s) % 4))
                # Text only: a binary payload (Bokeh's base64 arrays) can
                # hold the bytes of "~/" by chance (WP-50 WE.7).
                decoded.append((where + " (base64)", raw.decode("utf-8")))
            except ValueError:
                continue
    return out + decoded


def _names():
    names = [getpass.getuser(), socket.gethostname().split(".")[0]]
    p = subprocess.run(["git", "-C", _REPO, "config", "user.name"],
                       capture_output=True, text=True)
    names += p.stdout.split() if p.returncode == 0 else []
    return [n for n in names if len(n) >= 3]


def _gallery_findings(texts):
    bad = []
    names = [re.compile(r"(?<!\w)%s(?!\w)" % re.escape(n)) for n in _names()]
    email = _email()
    for where, text in texts:
        for pat in _GALLERY_PATHS + tuple(names):
            if pat.search(text):
                bad.append("%s: %s" % (where, pat.pattern))
        if email and email in text:
            bad.append("%s: the maintainer's e-mail address" % where)
    return bad


def test_the_gallery_holds_no_path_or_name():
    assert _gallery_findings(_gallery_texts()) == []


def test_the_gallery_scan_catches_planted_samples(tmp_path, monkeypatch):
    g = tmp_path / "g"
    (g / "svg").mkdir(parents=True)
    readme = tmp_path / "README.md"
    readme.write_text("# x\n" + _GALLERY_START + "\nclean\n" + _GALLERY_END + "\n",
                      encoding="utf-8")
    monkeypatch.setenv("DASH_GALLERY_DIR", str(g))
    monkeypatch.setenv("DASH_GALLERY_README", str(readme))
    assert _gallery_findings(_gallery_texts()) == []
    user = getpass.getuser()
    samples = {
        "a.html": "<p>" + "/Us" + "ers/someone/x.dta</p>",
        "b.html": "by %s today" % user,
        "c.html": "Licensed" + " to: someone",
        "svg/d.svg": '<image href="data:text/plain;base64,%s"/>'
        % base64.b64encode(("see " + "/pri" + "vate/tmp/x" + " " * 60).encode()).decode(),
    }
    for name, text in samples.items():
        for f in list(g.rglob("*.*")):
            f.unlink()
        (g / name).write_text(text, encoding="utf-8")
        assert _gallery_findings(_gallery_texts()) != [], name
    for f in list(g.rglob("*.*")):
        f.unlink()
    readme.write_text(_GALLERY_START + "\nC:" + "\\Users\\x\n" + _GALLERY_END + "\n",
                      encoding="utf-8")
    assert _gallery_findings(_gallery_texts()) != []
    # A page's numbers are base64 binary (Bokeh's arrays): bytes that
    # happen to read "~/" between bytes no text holds are not a path
    # (WP-50 WE.7: six such runs in the first gallery's pages).
    readme.write_text("# x\n", encoding="utf-8")
    noise = bytes([0x11, 0xff, 0x3b, 0x13, 0x7e, 0x2f, 0x40, 0xa9, 0x11]) * 40
    (g / "e.html").write_text('<script>"%s"</script>'
                              % base64.b64encode(noise).decode(), encoding="utf-8")
    assert _gallery_findings(_gallery_texts()) == []
