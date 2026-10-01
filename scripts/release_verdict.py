"""Judge a release-gate run (scripts/release_gate.do) from its log.

The gate prints one ``GATE ...`` line per result; each example and each
scheme page also has a log of its own, which this reads for the diagnostics
a clean run must not print.  A release passes only when:

* dash was net installed into the scratch PLUS (rc 0), and dash.ado,
  dash_setup.ado, dash_parse.mata and the renderer the locator finds all
  resolve inside it (BR-27.1);
* every examples/*.do in the repository ran from the installed tree with rc 0
  and its log holds no diagnostic it does not declare (TR-27.1);
* every scheme dash.pkg ships built a page with rc 0 and no diagnostic
  (AC-27.2: a missing or unreadable scheme is reported by the renderer as
  "was not found", "not found" or a fallback);
* adoupdate reported nothing to update against the installed source and
  reported dash against a copy one day newer (TR-27.5), and dash.pkg's
  Distribution-Date is no older than the newest change to a shipped file;
* PLUS was put back and the run reached its end;
* with the two venv-linked session logs (scripts/release_gate_venv.do,
  WP-29 P0.19): a venv made from the linked Python, verified by
  dash_setup, venv(); a fresh session linked to it by a relative path,
  which dash_setup finds linked, builds a saved page and serves /health.

A diagnostic is a line of a log that is not an echoed command (". " or
"> ") and matches one of ``DIAGNOSTICS``, case-insensitively.  An example
that means to draw one declares it in its header, one per line::

    *! release-gate allows: <text the line holds>

Usage:  python3 scripts/release_verdict.py <gate log> <repo> <min yyyymmdd>
            [<venvmake log> <venvuse log>]
Exit:   0 when the release passes; 1 otherwise, naming each failure.
"""
import os
import re
import sys

#: What a clean build prints none of: the renderer's fallback and
#: ignored-option notes, dash.ado's ignored-option notes, Python warnings
#: and tracebacks, and Bokeh's validation log.
DIAGNOSTICS = (
    "ignor",            # "ignoring unsupported option(s)", "... ignored"
    "not implemented",
    "not found",
    "fallback",
    "not a recognised",
    "warning",          # UserWarning, BokehUserWarning, WARNING:bokeh
    "traceback",
    "error:",           # ERROR:bokeh..., SyntaxError: ...
    "drew nothing",
)

_GATE = re.compile(r"^GATE (\S+)(.*)$", re.M)
_KV = re.compile(r"(\w+)=(\[[^\]]*\]|\S+)")
_ALLOWS = re.compile(r"^\*!\s*release-gate allows:\s*(.+?)\s*$", re.M)
_DATE = re.compile(r"^d Distribution-Date:\s*(\d{8})\s*$", re.M)
_SHIPPED_SCHEME = re.compile(r"^f dash-(\S+)\.scheme\s*$", re.M)

INSTALLED = ("dash.ado", "dash_setup.ado", "dash_parse.mata",
             "dash_render.py", "dash_setup_lib.py", "locator")

#: What the two venv-linked sessions must each report (WP-29 P0.19):
#: (log, tag, {key: value}).
VENV_REQUIRED = (
    ("make", "venv-made", {"rc": "0"}),
    ("make", "venv-setup", {"rc": "0", "ready": "1", "linked": "0"}),
    ("use", "venv-link", {"rc": "0"}),
    ("use", "venv-setup2", {"rc": "0", "linked": "1"}),
    ("use", "venv-saved", {"rc": "0", "html": "1"}),
    ("use", "venv-served", {"rc": "0", "health": "1"}),
    ("use", "venv-done", {}),
)


def _unwrap(log_text):
    """The log with each wrapped line joined back: Stata continues a line
    longer than its line size on the next, after "> "."""
    out = []
    for line in log_text.splitlines():
        if line.startswith("> ") and out and out[-1].startswith("GATE "):
            out[-1] += line[2:]
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def parse(log_text):
    """[(tag, {key: value})] for each GATE line, in order."""
    log_text = _unwrap(log_text)
    out = []
    for tag, rest in _GATE.findall(log_text):
        kv = {k: v for k, v in _KV.findall(rest)}
        # the path may hold spaces: keep everything after "path="
        if " path=" in rest:
            kv["path"] = rest.split(" path=", 1)[1].strip()
        if " log=" in rest:
            kv["log"] = rest.split(" log=", 1)[1].strip()
        out.append((tag, kv))
    return out


def diagnostics(log_text, allowed=()):
    """The lines of a log that are diagnostics its source does not allow."""
    found = []
    for line in log_text.splitlines():
        s = line.strip()
        if not s or s == "." or line.startswith(". ") or line.startswith("> "):
            continue
        low = s.lower()
        if not any(d in low for d in DIAGNOSTICS):
            continue
        if any(a.lower() in low for a in allowed):
            continue
        found.append(s)
    return found


def allowed_in(example_text):
    return tuple(_ALLOWS.findall(example_text))


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return None


def verdict(log_text, repo, min_date, read=_read):
    """(ok, lines).  ``read`` reads a file or returns None (a test seam)."""
    problems = []
    results = parse(log_text)
    first = {}
    for tag, kv in results:
        first.setdefault(tag, kv)

    def need(tag, key, want):
        kv = first.get(tag)
        if kv is None:
            problems.append("no %s line" % tag)
        elif kv.get(key) != want:
            problems.append("%s: %s=%s, wanted %s"
                            % (tag, key, kv.get(key), want))

    need("plus-moved", "ok", "1")
    need("install", "rc", "0")
    seen = {kv.get("file"): kv for tag, kv in results if tag == "installed"}
    for name in INSTALLED:
        kv = seen.get(name)
        if kv is None:
            problems.append("installed %s: never checked" % name)
        elif kv.get("rc") != "0" or kv.get("inplus") != "1":
            problems.append("installed %s: rc=%s inplus=%s path=%s"
                            % (name, kv.get("rc"), kv.get("inplus"),
                               kv.get("path")))

    # examples: every repository example, once, rc 0, a clean log
    exdir = os.path.join(repo, "examples")
    try:
        want = sorted(f for f in os.listdir(exdir) if f.endswith(".do"))
    except OSError:
        want = []
    if not want:
        problems.append("the repository has no examples/*.do")
    ran = [kv for tag, kv in results if tag == "example"]
    names = [kv.get("file") for kv in ran]
    for f in want:
        if names.count(f) != 1:
            problems.append("example %s: reported %d times"
                            % (f, names.count(f)))
    for f in sorted(set(names) - set(want)):
        problems.append("example %s: not in the repository" % f)
    n_ex_ok = 0
    for kv in ran:
        f = kv.get("file")
        bad = []
        if kv.get("rc") != "0":
            bad.append("rc=%s" % kv.get("rc"))
        text = read(kv.get("log", ""))
        if text is None:
            bad.append("no log")
        else:
            src = read(os.path.join(exdir, f or "")) or ""
            for d in diagnostics(text, allowed_in(src)):
                bad.append("printed: %s" % d)
        if bad:
            problems.append("example %s: %s" % (f, "; ".join(bad)))
        else:
            n_ex_ok += 1

    # schemes: every shipped scheme, once, rc 0, a clean log
    pkg = read(os.path.join(repo, "dash.pkg")) or ""
    shipped = sorted(_SHIPPED_SCHEME.findall(pkg))
    built = [kv for tag, kv in results if tag == "scheme"]
    bnames = [kv.get("name") for kv in built]
    for s in shipped:
        if bnames.count(s) != 1:
            problems.append("scheme %s: built %d times" % (s, bnames.count(s)))
    n_sch_ok = 0
    for kv in built:
        bad = []
        if kv.get("rc") != "0":
            bad.append("rc=%s" % kv.get("rc"))
        text = read(kv.get("log", ""))
        if text is None:
            bad.append("no log")
        else:
            bad += ["printed: %s" % d for d in diagnostics(text)]
        if bad:
            problems.append("scheme %s: %s" % (kv.get("name"), "; ".join(bad)))
        else:
            n_sch_ok += 1

    # adoupdate, and a current Distribution-Date
    need("adoupdate-same", "rc", "0")
    need("adoupdate-same", "pkglist", "[]")
    need("newer-source", "bumped", "1")
    moved = first.get("trk-source", {}).get("moved", "0")
    if not moved.isdigit() or int(moved) < 1:
        problems.append("trk-source: the install's source was not recorded")
    need("adoupdate-newer", "rc", "0")
    need("adoupdate-newer", "pkglist", "[dash]")
    m = _DATE.search(pkg)
    if not m:
        problems.append("dash.pkg declares no Distribution-Date")
    elif not re.fullmatch(r"\d{8}", min_date or ""):
        problems.append("no newest-change date to compare with (%r)"
                        % min_date)
    elif m.group(1) < min_date:
        problems.append("Distribution-Date %s is older than the newest "
                        "change to a shipped file, %s" % (m.group(1), min_date))

    need("restored", "ok", "1")
    if "done" not in first:
        problems.append("the gate did not reach its end")

    ok = not problems
    lines = ["release gate: %d of %d examples and %d of %d scheme pages clean"
             % (n_ex_ok, len(want), n_sch_ok, len(shipped))]
    lines += ["  " + p for p in problems]
    lines.append("verdict: " + ("PASS" if ok else "FAIL"))
    return ok, lines


def venv_verdict(make_text, use_text):
    """The problems of the two venv-linked sessions' logs ([] when both
    report every VENV_REQUIRED line as required)."""
    problems = []
    logs = {"make": make_text, "use": use_text}
    firsts = {}
    for name, text in logs.items():
        firsts[name] = {}
        if text is None:
            problems.append("no venv%s log" % name)
            continue
        for tag, kv in parse(text):
            firsts[name].setdefault(tag, kv)
    for name, tag, want in VENV_REQUIRED:
        if logs[name] is None:
            continue
        kv = firsts[name].get(tag)
        if kv is None:
            problems.append("no %s line" % tag)
            continue
        for k, v in sorted(want.items()):
            if kv.get(k) != v:
                problems.append("%s: %s=%s, wanted %s" % (tag, k, kv.get(k), v))
    return problems


def main(argv):
    if len(argv) not in (4, 6):
        sys.stderr.write(__doc__)
        return 2
    text = _read(argv[1])
    if text is None:
        print("release gate: no log to judge (%s)" % argv[1])
        print("verdict: FAIL")
        return 1
    ok, lines = verdict(text, argv[2], argv[3])
    if len(argv) == 6:
        vp = venv_verdict(_read(argv[4]), _read(argv[5]))
        lines.pop()                       # the verdict line, rewritten below
        lines.append("venv-linked sessions: %s"
                     % ("clean" if not vp else "%d problem(s)" % len(vp)))
        lines += ["  " + p for p in vp]
        ok = ok and not vp
        lines.append("verdict: " + ("PASS" if ok else "FAIL"))
    print("\n".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
