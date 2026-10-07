"""Twoway's own answers for the certification scripts, recorded once and
replayed (WP-30 test performance, B2).

test_twoway_option_parity.cscript, test_parser.cscript and
test_help_claims_6.cscript hold dash to twoway: before each dash command
they ask twoway the same question -- its return code, the words it logs, a
serset it draws, a count read off its SVG export.  Drawing those graphs
cost about 120 s of every certification run (the timed run of 07oct2026),
to learn answers that change only when Stata does.  Each such question now
goes through this module, which cert_truth.do loads, in one of three modes
named by DASH_CERT_REMEASURE:

* unset or empty -- replay: the answer is the one the script's committed
  fixture, test/fixtures/<name>_truth.json, holds.  A question the fixture
  has no answer for fails the script: the fixture is stale, and
  scripts/extract_twoway_oracle_truth.do writes it again.
* ``1`` -- remeasure: twoway is asked in the run, as the scripts always
  did, and each answer is compared with the fixture's.  A different
  answer, a question the fixture lacks, or a fixture answer no question
  asked for fails the script.  This is the release and closeout run.
* ``record`` -- twoway is asked in the run and every answer is written to
  DASH_CERT_TRUTH_OUT/<name>.json; the extractor turns those into the
  fixtures, with their ``_meta`` stamp.  A question asked twice that
  twoway answered differently fails the recording.

A question's key is its kind and the exact command text, which reaches
Python by value (``sfi.Macro.getLocal``), never through a macro, so the
hostile values the scripts feed twoway are keys like any other.  Answers
are JSON values and are compared exactly, as JSON reads them back.

Nothing here runs twoway: cert_truth.do does that in Stata and hands this
module the answers.
"""
import json
import os

#: DASH_CERT_REMEASURE's values and the modes they name.
MODES = {"": "replay", "1": "remeasure", "record": "record"}

#: Where the scripts' fixtures are read, relative to test/.
FIXTURE_DIR = "fixtures"

#: The extractor named in every message that asks for a new fixture.
EXTRACTOR = "scripts/extract_twoway_oracle_truth.do"

#: A key longer than this keeps its first KEY_HEAD characters and the
#: SHA-256 of the whole: the scripts' resource-exhaustion questions hold
#: 10,000 copies of an option (190,000 characters), which as keys would
#: make most of a fixture.
KEY_MAX = 512
KEY_HEAD = 200

#: The lines of a Stata text log that `log using' writes before the
#: output and `log close' writes after it (when not run quietly).
_HEAD = ("      name:", "       log:", "  log type:", " opened on:",
         " closed on:")


def mode_of(value):
    """The mode DASH_CERT_REMEASURE's *value* names; any other value is
    refused, so a typo can never quietly mean replay."""
    v = "" if value is None else str(value).strip()
    if v not in MODES:
        raise ValueError(
            "DASH_CERT_REMEASURE must be empty, 1 or record (got %r)" % v)
    return MODES[v]


def canon(value):
    """*value* as it reads back from JSON: what an answer is compared as."""
    return json.loads(json.dumps(value))


def fixture_name(name):
    """The fixture file of the script whose truth is *name*."""
    if not name or not all(c.isalnum() or c == "_" for c in name):
        raise ValueError("a truth name is letters, digits and _ (got %r)"
                         % (name,))
    return name + "_truth.json"


def make_key(kind, command):
    """The fixture's key for a question: its kind and the command text, a
    long one cut to its head and the SHA-256 of the whole."""
    key = kind + "|" + command
    if len(key) > KEY_MAX:
        import hashlib
        key = (key[:KEY_HEAD] + "...[%d characters, sha256 %s]"
               % (len(key), hashlib.sha256(key.encode("utf-8"))
                  .hexdigest()))
    return key


def log_body(text):
    """The output a Stata text log holds, without the header `log using'
    writes and the footer `log close' writes -- which carry the log's path
    and the time, so they would differ between two runs -- and without
    the blank lines at either end.  A log opened quietly has neither, and
    is returned whole but for those blank lines."""
    lines = text.replace("\r\n", "\n").split("\n")
    start = 0
    for i, ln in enumerate(lines[:12]):
        if ln.startswith(" opened on:"):
            start = i + 1
            break
    end = len(lines)
    for i in range(len(lines) - 1, start - 1, -1):
        if lines[i].startswith(" closed on:"):
            j = i
            while j > start and (lines[j - 1].startswith(_HEAD)
                                 or lines[j - 1].startswith("> ")):
                j -= 1
            end = j
            break
    body = lines[start:end]
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    return "".join(ln + "\n" for ln in body)


class Truth:
    """One script's answers: the fixture's, and those measured in the run."""

    def __init__(self, name, testdir, mode, out_dir=""):
        self.name = name
        self.mode = mode
        self.path = os.path.join(testdir, FIXTURE_DIR, fixture_name(name))
        self.out_dir = out_dir
        self.fixture = {}
        self.meta = {}
        self.measured = {}
        self.asked = set()
        self.missing = []
        self.stale = []
        self.conflicts = []
        if mode == "record":
            if not out_dir or not os.path.isdir(out_dir):
                raise ValueError("record mode needs DASH_CERT_TRUTH_OUT, an "
                                 "existing folder (got %r)" % (out_dir,))
            return
        with open(self.path, encoding="utf-8") as fh:
            doc = json.load(fh)
        self.meta = doc.get("_meta", {})
        self.fixture = doc.get("answers", {})

    def live(self):
        """Whether this run asks twoway (remeasure, record)."""
        return self.mode in ("remeasure", "record")

    def put(self, kind, command, value):
        """Twoway's answer *value* to *command*, measured in this run."""
        key = make_key(kind, command)
        value = canon(value)
        self.asked.add(key)
        if key in self.measured:
            if self.measured[key] != value and key not in self.conflicts:
                self.conflicts.append(key)
            return
        self.measured[key] = value
        if self.mode == "remeasure":
            if key not in self.fixture:
                self.missing.append(key)
            elif self.fixture[key] != value:
                self.stale.append(key)

    def get(self, kind, command):
        """The fixture's answer to *command*, or None (noted) when it has
        none."""
        key = make_key(kind, command)
        self.asked.add(key)
        if key not in self.fixture:
            if key not in self.missing:
                self.missing.append(key)
                # Said at once as well: a script that stops on the gap
                # (a serset never written, say) never reaches its close.
                print("TRUTH FAIL %s holds no answer to %s: run %s"
                      % (fixture_name(self.name), _show(key), EXTRACTOR))
            return None
        return self.fixture[key]

    def problems(self):
        """What makes this run fail, one line each; empty when it may
        pass."""
        out = []
        for key in self.conflicts:
            out.append("twoway answered %s twice, differently" % _show(key))
        for key in self.missing:
            out.append("%s holds no answer to %s" % (fixture_name(self.name),
                                                    _show(key)))
        for key in self.stale:
            out.append("twoway's answer to %s is no longer the fixture's"
                       % _show(key))
        if self.mode == "remeasure":
            for key in sorted(set(self.fixture) - self.asked):
                out.append("%s answers %s, which this run never asked"
                           % (fixture_name(self.name), _show(key)))
        return out

    def close(self):
        """Finish the run: write the answers in record mode, and return
        the problems (after which the script fails, naming the
        extractor)."""
        probs = self.problems()
        if self.mode == "record" and not probs:
            path = os.path.join(self.out_dir, self.name + ".json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(self.measured, fh, indent=1, sort_keys=True,
                          ensure_ascii=True)
                fh.write("\n")
        return probs


def _show(key, width=160):
    """A key, cut to *width* characters, with control characters shown as
    escapes: for a message, never for a comparison."""
    s = key.encode("unicode_escape").decode("ascii")
    return s if len(s) <= width else s[:width] + "..."


# ---------------------------------------------------------------------------
# What cert_truth.do and the scripts call.  Every argument but the context
# label is the NAME of a Stata local, read and written through sfi.Macro,
# so no command, answer or path is ever expanded as a macro.  One session
# holds one Truth at a time: cert_truth_init makes it, and every call below
# answers for the script that made it.
# ---------------------------------------------------------------------------

_state = {"truth": None, "ctx": ""}


def _macro():
    from sfi import Macro
    return Macro


def open_truth(name, testdir, env_mode, out_dir):
    """Start a script's truth (cert_truth_init); returns its mode."""
    _state["truth"] = Truth(name, testdir, mode_of(env_mode), out_dir)
    _state["ctx"] = ""
    return _state["truth"].mode


def current():
    if _state["truth"] is None:
        raise RuntimeError("cert_truth_init was not run in this session")
    return _state["truth"]


def ctx(label):
    """Name the case group the next questions belong to: the same command
    asked in two groups -- with other data in memory -- is two questions."""
    _state["ctx"] = str(label)


def _q(cmd):
    """The question: the context and the command text of local *cmd*."""
    return _state["ctx"] + "|" + _macro().getLocal(cmd)


def flag(out):
    """Local *out* is 1 when this run asks twoway, else 0."""
    _macro().setLocal(out, "1" if current().live() else "0")


def rc_put(cmd, rc):
    """Twoway's return code (local *rc*) for the command in local *cmd*."""
    current().put("rc", _q(cmd), int(_macro().getLocal(rc)))


def rc_get(cmd, rc):
    """Local *rc* is the recorded return code, or empty when none is."""
    v = current().get("rc", _q(cmd))
    _macro().setLocal(rc, "" if v is None else str(int(v)))


def log_put(cmd, rc, path):
    """Twoway's return code and the output its log (local *path*) holds."""
    m = _macro()
    with open(m.getLocal(path), encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    current().put("log", _q(cmd), {"rc": int(m.getLocal(rc)),
                                   "log": log_body(text)})


def log_get(cmd, path, rc):
    """Write the recorded output to the log at local *path* (empty when
    there is none) and set local *rc* to the return code (or empty)."""
    m = _macro()
    v = current().get("log", _q(cmd))
    with open(m.getLocal(path), "w", encoding="utf-8") as fh:
        fh.write("" if v is None else v["log"])
    m.setLocal(rc, "" if v is None else str(int(v["rc"])))


def val_put(kind, cmd, val):
    """An answer read off twoway's drawing -- a count, a checksum, a mean
    -- as the text of local *val*, for the command in local *cmd*."""
    current().put("val:" + kind, _q(cmd), _macro().getLocal(val))


def val_get(kind, cmd, val):
    """Local *val* is the recorded answer, or empty when none is."""
    v = current().get("val:" + kind, _q(cmd))
    _macro().setLocal(val, "" if v is None else str(v))


def data_put(cmd):
    """The dataset in memory -- a serset twoway drew -- for the command in
    local *cmd*: its variables' names and values, a missing value None."""
    from sfi import Data
    names = [Data.getVarName(j) for j in range(Data.getVarCount())]
    rows = Data.get(None, None, None, missingval=None) if names else []
    current().put("data", _q(cmd), {"names": names,
                                    "rows": [list(r) for r in rows]})


def data_get(cmd, ok):
    """Put the recorded dataset of the command in local *cmd* in memory,
    which must be empty, every variable a double; local *ok* is 1, or
    empty when nothing is recorded."""
    from sfi import Data, Missing
    v = current().get("data", _q(cmd))
    if v is None:
        _macro().setLocal(ok, "")
        return
    rows = v["rows"]
    Data.setObsTotal(len(rows))
    for name in v["names"]:
        Data.addVarDouble(name)
    if rows and v["names"]:
        miss = Missing.getValue()
        Data.store(None, None, [[miss if x is None else x for x in r]
                                for r in rows])
    _macro().setLocal(ok, "1")


def finish(out):
    """End the script's run: print each problem, and set local *out* to
    how many there are (0 when the run may pass)."""
    t = current()
    probs = t.close()
    for p in probs:
        print("TRUTH FAIL " + p)
    if probs:
        print("TRUTH FAIL %d problem(s) with %s: run %s to write it again "
              "from twoway (DASH_CERT_REMEASURE=1 asks twoway in the run)"
              % (len(probs), fixture_name(t.name), EXTRACTOR))
    _macro().setLocal(out, str(len(probs)))
