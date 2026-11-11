"""WP-30 P1.34: the Stata runners are portable.

The runners named the maintainer's checkout and forced the arm64 slice by
hand, so ``make cert`` in a worktree or a copy tested the main checkout
(a broken copy could pass) and no other machine could run them.  Now:

* ``scripts/stata_batch.sh`` is the one place Stata is started from:
  ``STATA_BIN`` (default ``/usr/local/bin/stata-mp``, never searched for),
  console binaries only, the arm64 slice exactly when the machine reports
  ``hw.optional.arm64`` and the binary holds an arm64 slice -- also under an
  x86_64 parent process, where ``uname -m`` is wrong.
* ``test/run_all_cscripts.do`` and every extractor read the tree under test
  from ``DASH_REPO``, else the current directory when it is a dash tree.
* No file under ``scripts/`` or ``test/``, and not the Makefile, names a
  home directory or the fixed slice flag.  The needles below are built by
  concatenation, because this file is scanned too.

Every test that executes a runner or a generator first asserts, statically,
that it routes through the wrapper or refuses at the top, so that on a tree
without the fix nothing real is started and no ``dash.ado`` is written.
"""

import os
import platform
import re
import shutil
import stat
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_WRAPPER = os.path.join(_ROOT, "scripts", "stata_batch.sh")
sys.path.insert(0, _HERE)

#: The slice program and its flag, never written whole in this file.
_ARCH = "ar" + "ch"
_ARM = "-" + "arm64"
_X86 = "-" + "x86_64"

#: A home directory: macOS's or Linux's per-user directory, or Windows's.
_HOME = re.compile("/" + "Users/" + r"[^/\s]+/" + "|/" + "home/" + r"[^/\s]+/"
                   + r"|C:\\" + "Users" + r"\\")
#: The fixed slice, in shell or argv form.
_FIXED_ARCH = re.compile(r"\b" + _ARCH + r"\s+" + _ARM + r"\b|\"" + _ARCH
                         + r"\",\s*\"" + _ARM + "\"")

_SUFFIXES = {".py", ".do", ".cscript", ".sh", ".md", ".txt", ".ado", ".mata"}

_SHELLS = [s for s in ("/bin/sh", "/bin/dash") if os.path.exists(s)]


def _read(*parts):
    with open(os.path.join(_ROOT, *parts), encoding="utf-8",
              errors="replace") as fh:
        return fh.read()


def _scan_set():
    """Every text file the guard reads, relative to the repository root:
    by type, never by a per-file exemption (JSON, CSV, PNG and SVG files
    are records of where a measurement ran)."""
    out = []
    for top in ("scripts", "test"):
        for dp, dns, fns in os.walk(os.path.join(_ROOT, top)):
            dns[:] = sorted(d for d in dns
                            if d != "__pycache__" and not d.startswith("."))
            for f in fns:
                if f.startswith("."):
                    continue
                ext = os.path.splitext(f)[1]
                if ext in _SUFFIXES or (top == "scripts" and ext == ""):
                    out.append(os.path.relpath(os.path.join(dp, f), _ROOT))
    out.append("Makefile")
    return sorted(out)


def _hits(pattern):
    return sorted(p for p in _scan_set() if pattern.search(_read(p)))


def _script(path, body):
    path.write_text("#!/bin/sh\n" + body)
    path.chmod(0o755)
    return path


def _run(argv, env, cwd=None):
    return subprocess.run(argv, env=env, cwd=cwd, capture_output=True,
                          text=True, timeout=30)


def _is_arm64_mac():
    if platform.system() != "Darwin" or not os.path.exists("/usr/bin/" + _ARCH):
        return False
    r = subprocess.run(["/usr/sbin/sysctl", "-n", "hw.optional.arm64"],
                       capture_output=True, text=True, timeout=30)
    return r.stdout.strip() == "1"


_ARM64_MAC = _is_arm64_mac()
_REAL_STATA = "/usr/local/bin/stata-mp"


# ---------------------------------------------------------------------------
# The guard: no home path and no fixed slice anywhere it reads
# ---------------------------------------------------------------------------

class TestNoMaintainerPaths:

    def test_no_home_directory_path(self):
        assert _hits(_HOME) == []

    def test_no_arch_literal(self):
        assert _hits(_FIXED_ARCH) == []

    def test_the_scan_covers_every_runner(self):
        scanned = set(_scan_set())
        need = {"scripts/stata_slot.sh", "scripts/run_cert_suite.sh",
                "scripts/run_release_gate.sh", "scripts/stata_python_exec.sh",
                "Makefile", "test/run_all_cscripts.do",
                "scripts/measure_stata_coverage.py",
                "test/fixtures/twoway_corpus.do",
                "scripts/git-hooks/pre-push"}
        need |= {os.path.join("scripts", f)
                 for f in os.listdir(os.path.join(_ROOT, "scripts"))
                 if f.startswith("extract_") and f.endswith(".do")}
        assert need <= scanned, sorted(need - scanned)
        assert not [p for p in scanned if p.endswith(".json")]


# ---------------------------------------------------------------------------
# One way to start Stata
# ---------------------------------------------------------------------------

def _invokes_arch(rel, text):
    ext = os.path.splitext(rel)[1]
    if ext in (".sh", "") or rel == "Makefile":
        code = "\n".join(l.split("#", 1)[0] for l in text.splitlines())
        return re.search(r"(^|[\s;&|(])" + _ARCH + r"\s", code, re.M)
    if ext == ".py":
        return re.search("[\"']" + _ARCH + "[\"']", text)
    if ext == ".do":
        return re.search(r"\b(shell|!)\s*" + _ARCH + r"\b", text)
    return None


def _recipe(makefile, target):
    m = re.search(r"^%s:[^\n]*\n((?:\t[^\n]*\n?)+)" % re.escape(target),
                  makefile, re.M)
    assert m, target
    return m.group(1)


def _copy_runner(tree, *names):
    (tree / "scripts").mkdir(parents=True)
    for n in names:
        shutil.copy(os.path.join(_ROOT, "scripts", n), tree / "scripts" / n)


def _fake_stata(bindir, body):
    bindir.mkdir(parents=True, exist_ok=True)
    return _script(bindir / "stata-mp", body)


_RECORD = ('{ printf "DASH_REPO=%s\\n" "${DASH_REPO-}"; '
           'printf "STATATMP=%s\\n" "${STATATMP-}"; '
           'for a in "$@"; do printf "ARG=%s\\n" "$a"; done; } > "$FAKE_OUT"\n')


class TestEveryRunnerUsesTheWrapper:

    def test_only_the_wrapper_invokes_arch(self):
        found = {p for p in _scan_set() if _invokes_arch(p, _read(p))}
        assert found == {"scripts/stata_batch.sh"}

    def _routes(self, name):
        script = _read("scripts", name)
        assert 'sh "$REPO/scripts/stata_batch.sh" -b do' in script, name
        assert not _invokes_arch(name, script), name
        assert os.path.isfile(_WRAPPER)
        return script

    def test_run_cert_suite_hands_stata_its_own_tree(self, tmp_path):
        # One session (DASH_CERT_SESSIONS=1): the run as it always was.
        self._routes("run_cert_suite.sh")
        tree = tmp_path / "tree"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        fake = _fake_stata(tmp_path / "bin", _RECORD)
        out = tmp_path / "fake.out"
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(out),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path),
               "DASH_CERT_SESSIONS": "1"}
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode != 0, r.stdout + r.stderr
        lines = out.read_text().splitlines()
        real = os.path.realpath(str(tree))
        assert os.path.realpath(lines[0].split("=", 1)[1]) == real, lines
        assert lines[1].startswith("STATATMP=") and lines[1].endswith("/tmp/")
        args = [l.split("=", 1)[1] for l in lines[2:]]
        assert args[:2] == ["-b", "do"] and len(args) == 3, args
        assert os.path.realpath(args[2]) == os.path.join(
            real, "test", "run_all_cscripts.do")
        assert "testing" in r.stdout
        assert r.stdout.count("certification log: ") == 1

    #: A fake Stata that records, per shard, where and how it was started.
    _SHARD_RECORD = (
        'f="$FAKE_OUT.$(printf "%s" "${DASH_CERT_SHARD-none}" | tr / _)"\n'
        '{ printf "DASH_REPO=%s\\n" "${DASH_REPO-}"; '
        'printf "STATATMP=%s\\n" "${STATATMP-}"; '
        'printf "SHARD=%s\\n" "${DASH_CERT_SHARD-}"; '
        'printf "PYX=%s\\n" "${DASH_PYTHON_EXEC-unset}"; '
        'printf "TIER=%s\\n" "${DASH_CERT_TIER-unset}"; '
        'printf "PWD=%s\\n" "$(pwd)"; '
        'for a in "$@"; do printf "ARG=%s\\n" "$a"; done; } > "$f"\n')

    @pytest.mark.parametrize("sessions", ["2", "3", "4", "8", None])
    def test_run_cert_suite_runs_its_shards_side_by_side(self, tmp_path,
                                                         sessions):
        # WP-30 test performance, C: N sessions (default 3), session k
        # running shard k/N in its own folder with its own STATATMP (ending
        # in /, not the folder its log is written to), and the verdict
        # handed every shard's log.
        self._routes("run_cert_suite.sh")
        tree = tmp_path / "tree"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        fake = _fake_stata(tmp_path / "bin", self._SHARD_RECORD)
        out = tmp_path / "fake.out"
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(out),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path),
               "DASH_PYTHON_EXEC": "/x/python3"}
        if sessions:
            env["DASH_CERT_SESSIONS"] = sessions
        n = int(sessions or 3)
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode == 1, r.stdout + r.stderr
        assert "%d sessions side by side" % n in r.stdout
        real = os.path.realpath(str(tree))
        tmps, pwds = set(), set()
        for k in range(1, n + 1):
            rec = dict(l.split("=", 1) for l in tmp_path.joinpath(
                "fake.out.%d_%d" % (k, n)).read_text().splitlines()
                if not l.startswith("ARG="))
            args = [l.split("=", 1)[1] for l in tmp_path.joinpath(
                "fake.out.%d_%d" % (k, n)).read_text().splitlines()
                if l.startswith("ARG=")]
            assert os.path.realpath(rec["DASH_REPO"]) == real
            assert rec["SHARD"] == "%d/%d" % (k, n)
            assert rec["PYX"] == "/x/python3"
            # The release tier (22oct2026): unset, the default tier.
            assert rec["TIER"] == "default"
            assert rec["STATATMP"].endswith("/s%d/tmp/" % k)
            assert os.path.realpath(rec["PWD"]) == os.path.realpath(
                rec["STATATMP"][:-len("tmp/")])
            assert args[:2] == ["-b", "do"] and len(args) == 3
            assert os.path.realpath(args[2]) == os.path.join(
                real, "test", "run_all_cscripts.do")
            tmps.add(rec["STATATMP"])
            pwds.add(rec["PWD"])
        assert len(tmps) == len(pwds) == n
        assert not tmp_path.joinpath("fake.out.none").exists()
        logs = [l for l in r.stdout.splitlines()
                if l.startswith("certification log: ")]
        assert len(logs) == n
        assert all(l.endswith("/s%d/run_all_cscripts.log" % k)
                   for k, l in enumerate(logs, 1))
        assert "no log to judge" in r.stdout

    @pytest.mark.parametrize("var,value", [
        ("DASH_CERT_SESSIONS", "0"), ("DASH_CERT_SESSIONS", "9"),
        ("DASH_CERT_SESSIONS", "x"), ("DASH_CERT_SESSIONS", "3 "),
        ("DASH_CERT_ONLY", "test_a;rm"), ("DASH_CERT_ONLY", "a\tb"),
        ("DASH_CERT_ONLY", "$HOME"), ("DASH_CERT_TIER", "nightly"),
        ("DASH_CERT_TIER", "release;rm"), ("DASH_CERT_TIER", "Release")])
    def test_run_cert_suite_refuses_a_bad_setting_before_stata(
            self, tmp_path, var, value):
        tree = tmp_path / "tree"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        fake = _fake_stata(tmp_path / "bin", self._SHARD_RECORD)
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(tmp_path / "fake.out"),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path), var: value}
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode == 2, r.stdout + r.stderr
        assert var in r.stderr
        assert not [p for p in os.listdir(tmp_path)
                    if p.startswith("fake.out")]

    def test_run_cert_suite_hands_dash_cert_only_to_the_verdict(self,
                                                                 tmp_path):
        tree = tmp_path / "tree"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        (tree / "test").mkdir()
        (tree / "test" / "run_all_cscripts.do").write_text(
            'capture noisily {\n    do "test_a.cscript"\n}\n'
            'capture noisily {\n    do "test_b.cscript"\n}\n')
        body = ('printf "[SHARD] 1/1: 1 of 2 scripts\\n[ PASS] '
                'test_a.cscript\\nALL TESTS PASSED (1 passed, 0 skipped)\\n" '
                '> run_all_cscripts.log\n'
                'printf "ONLY=%s\\n" "${DASH_CERT_ONLY-}" > "$FAKE_OUT"\n')
        fake = _fake_stata(tmp_path / "bin", body)
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(tmp_path / "fake.out"),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path),
               "DASH_CERT_SESSIONS": "1", "DASH_CERT_ONLY": "test_a"}
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "1 of 1 registered scripts passed" in r.stdout
        assert (tmp_path / "fake.out").read_text() == "ONLY=test_a\n"

    @pytest.mark.parametrize("tier", ["release", "all"])
    def test_run_cert_suite_hands_the_tier_to_every_session_and_verdict(
            self, tmp_path, tier):
        tree = tmp_path / "tree"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        (tree / "test").mkdir()
        (tree / "test" / "run_all_cscripts.do").write_text(
            'capture noisily {\n    do "test_a.cscript"\n}\n'
            'capture noisily {\n    do "test_r.cscript"\n}\n'
            "local _cert_release test_r.cscript\n")
        # Each session reports the release script (shard 1) and, in the
        # all tier, test_a (shard 2), and records the tier it was handed.
        body = ('k="${DASH_CERT_SHARD%%/*}"\n'
                'printf "TIER=%s\\n" "${DASH_CERT_TIER-unset}" '
                '> "$FAKE_OUT.$k"\n'
                'if [ "$k" = 1 ]; then r="[ PASS] test_r.cscript"; '
                'elif [ "$DASH_CERT_TIER" = all ]; then '
                'r="[ PASS] test_a.cscript"; else r=""; fi\n'
                'n=0; [ -n "$r" ] && n=1\n'
                'printf "[ TIER] %s\\n[SHARD] %s: x\\n%s\\n'
                'ALL TESTS PASSED (%s passed, 0 skipped)\\n" '
                '"$DASH_CERT_TIER" "$DASH_CERT_SHARD" "$r" "$n" '
                '> run_all_cscripts.log\n')
        fake = _fake_stata(tmp_path / "bin", body)
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(tmp_path / "fake.out"),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path),
               "DASH_CERT_SESSIONS": "2", "DASH_PYTHON_EXEC": "/x/python3",
               "DASH_CERT_TIER": tier}
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode == 0, r.stdout + r.stderr
        n = {"release": 1, "all": 2}[tier]
        assert "%d of %d registered scripts passed" % (n, n) in r.stdout
        assert "%s tier" % tier in r.stdout
        for k in (1, 2):
            assert (tmp_path / ("fake.out.%d" % k)).read_text() == \
                "TIER=%s\n" % tier

    def test_run_cert_suite_refuses_a_tree_stata_cannot_be_handed(self,
                                                                  tmp_path):
        self._routes("run_cert_suite.sh")
        tree = tmp_path / "co$py"
        _copy_runner(tree, "run_cert_suite.sh", "stata_batch.sh",
                     "cert_verdict.py")
        fake = _fake_stata(tmp_path / "bin", _RECORD)
        out = tmp_path / "fake.out"
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "FAKE_OUT": str(out),
               "PYTHON": sys.executable, "TMPDIR": str(tmp_path)}
        r = _run(["/bin/sh", str(tree / "scripts" / "run_cert_suite.sh")], env)
        assert r.returncode == 2, r.stdout + r.stderr
        assert "Stata cannot be handed" in r.stderr
        assert not out.exists()

    def test_stata_python_exec_reads_through_the_wrapper(self, tmp_path):
        self._routes("stata_python_exec.sh")
        tree = tmp_path / "tree"
        _copy_runner(tree, "stata_python_exec.sh", "stata_batch.sh")
        fake = _fake_stata(tmp_path / "bin",
                           'printf "/fake/python" > pyexec.txt\n')
        env = {"PATH": "/usr/bin:/bin", "STATA_BIN": str(fake),
               "STATA_ARCH": "none", "TMPDIR": str(tmp_path)}
        r = _run(["/bin/sh", str(tree / "scripts" / "stata_python_exec.sh")],
                 env)
        assert r.returncode == 0, r.stderr
        assert r.stdout == "/fake/python\n"

    def test_the_makefile_names_stata_bin(self):
        mk = _read("Makefile")
        assert re.search(r"^STATA_BIN\s*\?=\s*/usr/local/bin/stata-mp\s*$",
                         mk, re.M)
        assert not re.search(r"^STATA\s*\?=", mk, re.M)
        for target in ("test", "cert", "gate"):
            assert "STATA_BIN='$(STATA_BIN)'" in _recipe(mk, target), target
        assert "ifeq ($(origin STATA),command line)" in mk
        assert re.search(r"^\$\(error STATA was renamed STATA_BIN", mk, re.M)

    def test_make_refuses_the_old_variable(self):
        # Where make is installed it is run (dry); elsewhere the guard's
        # text is all there is to check.  Never a skip: a skip fails
        # DASH_STRICT=1.
        if not shutil.which("make"):
            assert "ifeq ($(origin STATA),command line)" in _read("Makefile")
            return
        r = _run(["make", "-n", "-C", _ROOT, "cert", "STATA=/x"],
                 dict(os.environ))
        assert r.returncode == 2, r.stdout + r.stderr
        assert "STATA_BIN" in r.stdout + r.stderr
        r = _run(["make", "-n", "-C", _ROOT, "cert"], dict(os.environ))
        assert r.returncode == 0, r.stderr
        assert "STATA_BIN='/usr/local/bin/stata-mp'" in r.stdout


# ---------------------------------------------------------------------------
# The wrapper, every branch, under every shell present
# ---------------------------------------------------------------------------

def _tools(tmp_path):
    """Fake uname, sysctl, file and the slice program, ahead on PATH."""
    fb = tmp_path / "fakebin"
    fb.mkdir()
    _script(fb / "uname",
            'printf "%s\\n" "$*" >> "$TOOLS_LOG.uname"\n'
            'case "${1-}" in -m) echo x86_64 ;; *) echo "$FAKE_UNAME_S" ;; esac\n')
    _script(fb / "sysctl",
            'printf "%s\\n" "$*" >> "$TOOLS_LOG.sysctl"\n'
            '[ "$FAKE_SYSCTL_RC" = 0 ] || exit "$FAKE_SYSCTL_RC"\n'
            'echo "$FAKE_ARM64"\n')
    _script(fb / "file",
            'for a in "$@"; do p="$a"; done\n'
            'printf "%s: Mach-O 64-bit executable %s\\n" "$p" "$FAKE_SLICE"\n')
    _script(fb / _ARCH,
            'out=ARCH; for a in "$@"; do out="$out <$a>"; done\n'
            'printf "%s\\n" "$out" > "$FAKE_OUT"\n')
    return fb


_STATA_BODY = ('out=STATA; for a in "$@"; do out="$out <$a>"; done\n'
               'printf "%s\\n" "$out" > "$FAKE_OUT"\n: > "$FAKE_MARK"\n')


class _Rig:
    def __init__(self, tmp_path, shell, name="stata-mp"):
        self.tmp, self.shell = tmp_path, shell
        self.fb = _tools(tmp_path)
        self.bindir = tmp_path / "W" / "bin"
        self.bindir.mkdir(parents=True)
        self.bin = _script(self.bindir / name, _STATA_BODY)
        self.out = tmp_path / "out.txt"
        self.mark = tmp_path / "ran.mark"
        self.log = tmp_path / "tools"

    def run(self, *args, uname_s="Darwin", arm64="1", sysctl_rc="0",
            slice_="arm64", stata_bin=None, **extra):
        env = {"PATH": "%s:/usr/bin:/bin" % self.fb,
               "STATA_BIN": str(stata_bin or self.bin),
               "FAKE_OUT": str(self.out), "FAKE_MARK": str(self.mark),
               "TOOLS_LOG": str(self.log), "FAKE_UNAME_S": uname_s,
               "FAKE_ARM64": arm64, "FAKE_SYSCTL_RC": sysctl_rc,
               "FAKE_SLICE": slice_}
        env.update(extra)
        assert os.path.isfile(_WRAPPER), "scripts/stata_batch.sh is missing"
        return _run([self.shell, _WRAPPER] + list(args or ("-b", "do",
                                                           "my file.do")), env)

    def said(self):
        return self.out.read_text().strip() if self.out.exists() else None

    def tool_log(self, tool):
        p = self.tmp / ("tools." + tool)
        return p.read_text() if p.exists() else ""


@pytest.fixture(params=_SHELLS)
def rig(request, tmp_path):
    return _Rig(tmp_path, request.param)


class TestTheWrapper:

    def test_an_arm64_machine_gets_the_arm64_slice(self, rig):
        r = rig.run()
        assert r.returncode == 0, r.stderr
        assert rig.said() == "ARCH <%s> <%s> <-b> <do> <my file.do>" % (
            _ARM, rig.bin)

    def test_an_x86_64_parent_still_gets_the_arm64_slice(self, rig):
        r = rig.run()
        assert r.returncode == 0, r.stderr
        assert rig.said().startswith("ARCH <%s> " % _ARM)
        assert "-m" not in rig.tool_log("uname").split()

    def test_an_intel_mac_gets_no_prefix(self, rig):
        r = rig.run(arm64="", sysctl_rc="1")
        assert r.returncode == 0, r.stderr
        assert rig.said() == "STATA <-b> <do> <my file.do>"

    def test_linux_gets_no_prefix_and_never_asks_sysctl(self, rig):
        r = rig.run(uname_s="Linux")
        assert r.returncode == 0, r.stderr
        assert rig.said() == "STATA <-b> <do> <my file.do>"
        assert rig.tool_log("sysctl") == ""

    def test_an_x86_only_binary_gets_no_prefix(self, rig):
        r = rig.run(slice_="x86_64")
        assert r.returncode == 0, r.stderr
        assert rig.said() == "STATA <-b> <do> <my file.do>"

    def test_stata_arch_forces_a_slice_or_none(self, rig):
        rig.run(STATA_ARCH="none")
        assert rig.said() == "STATA <-b> <do> <my file.do>"
        rig.run(STATA_ARCH="arm64", uname_s="Linux")
        assert rig.said().startswith("ARCH <%s> " % _ARM)
        rig.run(STATA_ARCH="x86_64")
        assert rig.said().startswith("ARCH <%s> " % _X86)

    def test_a_bad_stata_arch_is_refused(self, rig):
        r = rig.run(STATA_ARCH="ppc")
        assert r.returncode == 2
        assert "STATA_ARCH must be" in r.stderr
        assert rig.said() is None

    def test_gui_binaries_are_refused_and_never_run(self, rig, tmp_path):
        bins = []
        for k, name in enumerate(("StataMP", "stataMP", "xstata-mp")):
            d = tmp_path / ("gui%d" % k)
            d.mkdir()
            bins.append(_script(d / name, _STATA_BODY))
        d = tmp_path / "link"
        d.mkdir()
        os.symlink(str(bins[0]), str(d / "stata-mp"))
        bins.append(d / "stata-mp")
        for b in bins:
            r = rig.run(stata_bin=b)
            assert r.returncode == 2, b
            assert "is not a console Stata" in r.stderr, b
        assert not rig.mark.exists() and rig.said() is None

    def test_a_missing_binary_is_refused(self, rig, tmp_path):
        r = rig.run(stata_bin=tmp_path / "none" / "stata-mp")
        assert r.returncode == 2
        assert "is not an executable file" in r.stderr
        assert rig.said() is None

    def test_arguments_pass_through_unchanged(self, rig):
        r = rig.run("-b", "do", 'a"b', "$HOME", "c`d", STATA_ARCH="none")
        assert r.returncode == 0, r.stderr
        assert rig.said() == 'STATA <-b> <do> <a"b> <$HOME> <c`d>'

    def test_print_mode_runs_nothing(self, rig):
        r = rig.run(STATA_BATCH_PRINT="1")
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == "<%s> <%s> <%s> <-b> <do> <my file.do>" % (
            _ARCH, _ARM, rig.bin)
        assert rig.said() is None and not rig.mark.exists()

    def test_the_default_is_the_console_binary_and_never_searched_for(self):
        text = _read("scripts", "stata_batch.sh")
        assert "STATA_BIN:-/usr/local/bin/stata-mp" in text
        for bad in (r"/Applications", r"\beval\b", r"\bls\s", r"\bfind\s",
                    "`"):
            assert not re.search(bad, text), bad
        assert os.stat(_WRAPPER).st_mode & stat.S_IXUSR

    def test_the_real_tools_choose_arm64_from_an_x86_64_parent(self,
                                                               tmp_path):
        # The real uname, sysctl and file; a copy of true named stata-mp;
        # a fake slice program that records its arguments.  On arm64 macOS
        # it is run under an x86_64 parent, and the arm64 slice is still
        # chosen; on any other machine no slice is added.
        assert os.path.isfile(_WRAPPER), "scripts/stata_batch.sh is missing"
        fb = tmp_path / "fakebin"
        fb.mkdir()
        _script(fb / _ARCH,
                'out=ARCH; for a in "$@"; do out="$out <$a>"; done\n'
                'printf "%s\\n" "$out" > "$FAKE_OUT"\n')
        b = tmp_path / "bin" / "stata-mp"
        b.parent.mkdir()
        shutil.copy("/usr/bin/true" if os.path.exists("/usr/bin/true")
                    else "/bin/true", b)
        out = tmp_path / "out.txt"
        env = {"PATH": "%s:/usr/bin:/bin:/usr/sbin:/sbin" % fb,
               "STATA_BIN": str(b), "FAKE_OUT": str(out)}
        if _ARM64_MAC:
            r = _run(["/usr/bin/" + _ARCH, _X86, "/bin/sh", "-c",
                      'test "$(uname -m)" = x86_64 || exit 7; '
                      'exec /bin/sh "$0" -b do x.do', _WRAPPER], env)
            assert r.returncode == 0, r.stderr
            assert out.read_text().strip() == \
                "ARCH <%s> <%s> <-b> <do> <x.do>" % (_ARM, b)
        else:
            env["STATA_BATCH_PRINT"] = "1"
            r = _run(["/bin/sh", _WRAPPER, "-b", "do", "x.do"], env)
            assert r.returncode == 0, r.stderr
            assert r.stdout.strip() == "<%s> <-b> <do> <x.do>" % b

    def test_this_macs_effective_command_is_unchanged(self):
        # On this Mac (arm64, /usr/local/bin/stata-mp) the command is the
        # arm64 slice of the console binary, natively and from an x86_64
        # parent.  Elsewhere: no slice off arm64 macOS, and a missing
        # default binary is refused, never searched for.
        assert os.path.isfile(_WRAPPER), "scripts/stata_batch.sh is missing"
        env = {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
               "STATA_BATCH_PRINT": "1"}
        argv = ["/bin/sh", _WRAPPER, "-b", "do", "x.do"]
        if not os.path.exists(_REAL_STATA):
            r = _run(argv, env)
            assert r.returncode == 2
            assert "is not an executable file" in r.stderr
            return
        if not _ARM64_MAC:
            r = _run(argv, env)
            assert r.returncode == 0, r.stderr
            assert r.stdout.strip() == "<%s> <-b> <do> <x.do>" % _REAL_STATA
            return
        want = "<%s> <%s> <%s> <-b> <do> <x.do>" % (_ARCH, _ARM, _REAL_STATA)
        for pre in ([], ["/usr/bin/" + _ARCH, _X86]):
            r = _run(pre + argv, env)
            assert r.returncode == 0, (pre, r.stderr)
            assert r.stdout.strip() == want, pre


# ---------------------------------------------------------------------------
# The certification runner's root
# ---------------------------------------------------------------------------

_BEGIN = "// ---- root: begin (WP-30 P1.34) ----"
_END = "// ---- root: end ----"
_SIX = "(char(34), char(36), char(39), char(96), char(10), char(13))"


def _runner_block():
    src = _read("test", "run_all_cscripts.do")
    assert src.count(_BEGIN) == 1 and src.count(_END) == 1
    return src, src[src.index(_BEGIN):src.index(_END)]


class TestTheRunnerRoot:

    def test_the_runner_reads_its_root_from_dash_repo(self):
        src, block = _runner_block()
        assert "local dashdir : environment DASH_REPO" in block
        assert ("if `\"`macval(dashdir)'\"' == \"\" "
                "local dashdir `\"`c(pwd)'\"'") in block
        adds = re.findall(r"^\s*adopath \+\+ .*$", src, re.M)
        assert adds == ["adopath ++ \"`dashdir'/\""], adds
        assert not re.search(r'^\s*local dashdir "', src, re.M)

    def test_the_root_block_refuses_what_stata_cannot_be_handed(self):
        _src, block = _runner_block()
        assert _SIX in block
        for need in ("exit 198", "exit 601", "quietly findfile dash.ado",
                     "exit 9"):
            assert need in block, need
        assert block.index("exit 601") < block.index("adopath ++")

    def test_the_header_comment_names_the_wrapper(self):
        head = "\n".join(_read("test", "run_all_cscripts.do").splitlines()[:15])
        assert "sh scripts/stata_batch.sh -b do test/run_all_cscripts.do" in head
        assert "DASH_REPO" in head


# ---------------------------------------------------------------------------
# The extractors and the corpus
# ---------------------------------------------------------------------------

_STANZA = "local repo : environment DASH_REPO"
_CONVERTED = {
    "scripts/extract_abbrev_truth.do": "ZQ_REPO",
    "scripts/extract_date_truth.do": "ZQ_REPO",
    "scripts/extract_axis_truth.do": "ZA_REPO",
    "scripts/extract_text_truth.do": "ZA_REPO",
    "scripts/extract_unlabelled_truth.do": "ZU_REPO",
    "scripts/extract_format_truth.do": "ZF_REPO",
    "scripts/extract_function_truth.do": "ZF_REPO",
    "scripts/extract_stat_truth.do": "ZQ_REPO",
    "scripts/extract_svg_truth_smoke.do": "ZS_REPO",
    "scripts/extract_filter_truth.do": "ZA_REPO",
    "scripts/extract_embedded_rows_truth.do": "ZA_REPO",
    "scripts/extract_join_order_truth.do": None,
    "scripts/extract_colorvar_truth.do": "ZS_REPO",
    "scripts/extract_colorvar_qualifier_truth.do": "ZQ_REPO",
    "scripts/extract_emptied_layer_truth.do": "ZE_REPO",
    "test/fixtures/twoway_corpus.do": None,
}


class TestTheExtractorRoot:

    @pytest.mark.parametrize("rel", sorted(_CONVERTED))
    def test_each_converted_file_reads_dash_repo(self, rel):
        src = _read(rel)
        assert "* Root (WP-30 P1.34): DASH_REPO, else the current" in src
        assert src.count(_STANZA) == 1, rel
        name = os.path.basename(rel)
        assert 'display as error "%s: DASH_REPO may not hold' % name in src
        at = src.index(_STANZA)
        g = _CONVERTED[rel]
        if g:
            line = "global %s \"`repo'\"" % g
            assert line in src and src.index(line) > at, rel
            assert not re.search(r"^\s*global %s \"/" % g, src, re.M), rel
        else:
            assert src.index("`repo'", at + len(_STANZA)) > at
        assert not re.search(r"^\s*adopath \+\+ \"/", src, re.M), rel

    def test_every_root_stanza_is_whole(self):
        files = []
        for top in ("scripts", os.path.join("test", "fixtures")):
            for f in sorted(os.listdir(os.path.join(_ROOT, top))):
                if f.endswith(".do"):
                    rel = os.path.join(top, f)
                    if _STANZA in _read(rel):
                        files.append(rel)
        assert len(files) >= 16, files
        for rel in files:
            src = _read(rel)
            assert ("if `\"`macval(repo)'\"' == \"\" "
                    "local repo `\"`c(pwd)'\"'") in src, rel
            assert _SIX in src, rel
            assert "exit 198" in src and "exit 601" in src, rel

    def test_extract_date_truth_reads_jsonio_from_the_environment(self):
        src = _read("scripts", "extract_date_truth.do")
        assert "local sj : environment STATAJSON_DIR" in src
        assert "Programs/Java/StataJSON" not in src


# ---------------------------------------------------------------------------
# The two option generators are retired
# ---------------------------------------------------------------------------

class TestTheRetiredGenerators:

    @pytest.mark.parametrize("name", ["regen_option_surface.py",
                                      "wire_option_reporting.py"])
    def test_each_refuses_before_reading_or_writing(self, name, tmp_path):
        src = _read("scripts", name)
        assert not _HOME.search(src), name
        assert "sys.exit(" in src and "open(" in src
        assert src.index("sys.exit(") < src.index("open("), name
        (tmp_path / "scripts").mkdir()
        (tmp_path / "test" / "fixtures").mkdir(parents=True)
        shutil.copy(os.path.join(_ROOT, "scripts", name),
                    tmp_path / "scripts" / name)
        (tmp_path / "dash.ado").write_text("ORIGINAL\n")
        (tmp_path / "test" / "fixtures" / "abbrev_truth.json").write_text("{}")
        r = _run([sys.executable, str(tmp_path / "scripts" / name)],
                 {"PATH": "/usr/bin:/bin"}, cwd=str(tmp_path))
        assert r.returncode != 0
        assert "historical, do not run" in r.stderr
        assert (tmp_path / "dash.ado").read_text() == "ORIGINAL\n"


# ---------------------------------------------------------------------------
# Stata's install tree in the pytest suite
# ---------------------------------------------------------------------------

class TestTheStataTree:

    def test_DASH_STATA_BASE_overrides_the_default(self, monkeypatch):
        import conftest
        monkeypatch.setenv("DASH_STATA_BASE", "/x/base")
        assert conftest.stata_base() == "/x/base"

    def test_DASH_STATA_PLUS_overrides_the_default(self, monkeypatch):
        import conftest
        monkeypatch.setenv("DASH_STATA_PLUS", "~/p")
        assert conftest.stata_plus() == os.path.expanduser("~/p")

    def test_unset_or_empty_gives_the_default(self, monkeypatch):
        import conftest
        for v in (None, ""):
            for k in ("DASH_STATA_BASE", "DASH_STATA_PLUS"):
                if v is None:
                    monkeypatch.delenv(k, raising=False)
                else:
                    monkeypatch.setenv(k, v)
            assert conftest.stata_base() == "/Applications/StataNow/ado/base"
            assert conftest.stata_plus() == os.path.expanduser(
                "~/Library/Application Support/Stata/ado/plus")

    def test_every_reader_uses_it(self):
        import conftest
        import test_help_claims_1 as h1
        import test_help_claims_8 as h8
        assert h1._STATA_BASE == conftest.stata_base()
        assert h1._STATA_PLUS == conftest.stata_plus()
        assert h8._STATA_BASE == conftest.stata_base()
        sch = _read("test", "test_scheme.py")
        assert "stata_base()" in sch and "Stata 15" not in sch
