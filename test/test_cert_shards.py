"""The certification suite split into shards (WP-30 test performance, C).

test/run_all_cscripts.do runs every script in one Stata session; with
DASH_CERT_SHARD=k/N only the scripts of shard k of N, from the shard table
scripts/cert_shards.py writes between its ``shards`` markers, and with
DASH_CERT_ONLY only the scripts it names.  scripts/run_cert_suite.sh runs N
sessions side by side (test_runner_portability.py) and
scripts/cert_verdict.py judges their logs together (test_cert_verdict.py).

These tests hold the table to its rules -- every registered script has a
row; the scripts that serve on a fixed port are marked, and share a shard
for every N; each N's assignment is the balanced one for the seconds -- and
the runner to running a block only when its script is selected.
"""
import os
import re
import shutil
import subprocess
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_ROOT, "scripts"))

import cert_shards as S  # noqa: E402
import cert_verdict as V  # noqa: E402


def _runner():
    with open(S.RUNNER, encoding="utf-8") as fh:
        return fh.read()


class TestTheRealTable:

    def test_the_table_has_no_problem(self):
        assert S.check(_runner()) == []

    def test_every_registered_script_has_one_row(self):
        rows = S.read_table(_runner())
        names = [r[0] for r in rows]
        assert sorted(names) == sorted(V.registered_scripts(_runner()))
        assert len(names) == len(set(names)) == 71  # 70 -> 71: test_wp34_truth.cscript (WP-34 W0); 68 -> 69: test_wp31_truth.cscript (WP-31 S01); 69 -> 70: test_wp33_truth.cscript (WP-33 33-01)

    def test_the_fixed_port_scripts_share_a_shard_for_every_n(self):
        rows = S.read_table(_runner())
        port = [r for r in rows if r[2]]
        # Measured 07oct2026 with the rule in cert_shards.py: the eight
        # scripts that run dash serve on 5006, 5097, 5098 or 5099.
        assert sorted(r[0] for r in port) == [
            "test_bug_regressions.cscript", "test_e2e_serve.cscript",
            "test_env_guards.cscript", "test_help_claims_4.cscript",
            "test_render_locate.cscript", "test_serve_browser.cscript",
            "test_serve_launch.cscript", "test_wp29_truth.cscript"]
        for n in S.COUNTS:
            assert len({r[3][n] for r in port}) == 1, n

    def test_every_shard_is_used_and_the_loads_are_balanced(self):
        # Flipped: the release tier (22oct2026) -- the balance that matters
        # is the default tier's, which make cert and make test-all run; the
        # release-tier scripts are placed on top of it.
        rows = S.read_table(_runner())
        release = set(S.read_release(_runner()))
        rows = [r for r in rows if r[0] not in release]
        seconds = {r[0]: r[1] for r in rows}
        for n in S.COUNTS:
            shards = {r[0]: r[3][n] for r in rows}
            assert set(shards.values()) - {S.EVERY} == set(range(1, n + 1))
            ld = S.loads(seconds, shards, n)
            # Within a tenth of each other: the longest single unit (the
            # fixed-port scripts, about 110 s) is under a shard's share.
            assert max(ld) <= 1.1 * min(ld), (n, ld)

    def test_the_closed_truth_scripts_are_the_release_tier(self):
        assert S.read_release(_runner()) == [
            "test_wp29_truth.cscript", "test_wp30_truth.cscript",
            "test_wp31_truth.cscript"]

    def test_three_default_sessions_finish_close_together(self):
        # The batch-end gate runs three sessions: their loads within 5 % of
        # each other, so that none waits long on another.
        rows = S.read_table(_runner())
        release = set(S.read_release(_runner()))
        seconds = {r[0]: r[1] for r in rows if r[0] not in release}
        shards = {r[0]: r[3][3] for r in rows if r[0] not in release}
        ld = S.loads(seconds, shards, 3)
        assert max(ld) <= 1.05 * min(ld), ld


    def test_the_wp30_script_runs_in_every_shard_split_by_its_blocks(self):
        rows = {r[0]: r[3] for r in S.read_table(_runner())}
        assert rows["test_wp30_truth.cscript"] == {n: S.EVERY
                                                   for n in S.COUNTS}
        # ["test_wp30_truth.cscript"] -> plus test_wp31_truth.cscript:
        # WP-31 S01 adds the second script that splits itself; plus
        # test_wp33_truth.cscript: WP-33 33-01 adds the third.
        # old -> new: plus test_wp34_truth.cscript (WP-34 W0)
        assert [s for s, k in rows.items() if S.EVERY in k.values()] == [
            "test_wp30_truth.cscript", "test_wp31_truth.cscript",
            "test_wp33_truth.cscript", "test_wp34_truth.cscript"]
        with open(S.WP30, encoding="utf-8") as fh:
            text = fh.read()
        secs = S.wp30_seconds(text)
        ids = set(re.findall(r"^\* ==== (S\d+) ", text, re.M))
        assert ids == {"S%02d" % i for i in range(1, 58)}
        for n in S.COUNTS:
            parts = S.wp30_parts(text, n)
            # Every block in exactly one part; every part a timed block.
            assert set(parts) == ids
            assert {k for b, k in parts.items() if secs.get(b, 0) > 0} == \
                set(range(1, n + 1)), n
            ld = [sum(secs.get(b, 0) for b in parts if parts[b] == k)
                  for k in range(1, n + 1)]
            assert max(ld) <= 1.1 * min(ld), (n, ld)


class TestTheRules:

    @pytest.mark.parametrize("text,serves", [
        ("dash serve, port(5098) timeout(1) nobrowser\n", True),
        ("capture noisily dash serve, port(5097) timeout(1)\n", True),
        ("capture dash serve\n", True),
        ("    dash serve, nobrowser timeout(1)\n", True),
        ("quietly _dash_serve, nobrowser\n", True),
        ("dash serve, port( 05006 )\n", True),
        ("dash serve, ///\n    port(5099) nobrowser\n", True),
        ("capture dash serve, port(1234;)\n", False),
        ("capture noisily dash serve, port(${hc4_port}) timeout(1)\n", False),
        ("_dash_serve_spec, specpath(a) datapath(b) port(5006)\n", False),
        ('display "dash serve, port(5006)"\n', False),
        ("// dash serve, port(5006)\n", False),
        ("* dash serve\n", False),
        ("foreach p in dash _dash_plot ///\n    _dash_serve {\n", False),
    ])
    def test_what_serves_on_a_fixed_port(self, text, serves):
        assert S.serves_on_a_fixed_port(text) is serves

    @pytest.mark.parametrize("text,splits", [
        ("local w30_sh : environment DASH_CERT_SHARD\n", True),
        ("    local k : env DASH_CERT_SHARD\n", True),
        ("// local k : env DASH_CERT_SHARD\n", False),
        ("local k : env DASH_CERT_SHARDS\n", False),
        ('display "DASH_CERT_SHARD"\n', False),
    ])
    def test_what_splits_itself(self, text, splits):
        assert S.splits_itself(text) is splits

    def test_a_split_script_is_in_every_shard_its_seconds_shared(self):
        seconds = {"a": 10, "w": 6, "b": 4, "c": 2}
        got = S.assign(seconds, set(), 2, {"w"})
        # w (3 a shard) first; a (10) to 1, b (4) to 2, c (2) to 2.
        assert got == {"w": "*", "a": 1, "b": 2, "c": 2}
        assert S.loads(seconds, got, 2) == [13, 9]

    def test_the_release_tier_is_placed_on_the_default_balance(self):
        seconds = {"a": 10, "b": 8, "c": 6, "p": 3, "q": 2, "r": 20,
                   "w": 12, "x": 7}
        port, every, release = {"p", "q"}, {"w"}, {"r", "w", "x", "q"}
        got = S.assign(seconds, port, 2, every, release)
        # The default tier (a, b, c, p) as if alone ...
        assert {s: got[s] for s in "abcp"} == S.assign(
            {s: seconds[s] for s in "abcp"}, {"p"}, 2)
        # ... then the release tier on top: w in every shard, q with the
        # fixed-port unit's p, r and x longest first onto the lighter.
        assert got["w"] == S.EVERY and got["q"] == got["p"]
        assert got == {"a": 1, "b": 2, "c": 2, "p": 1, "w": "*", "q": 1,
                       "r": 2, "x": 1}
        # No release tier: the assignment as before.
        assert S.assign(seconds, port, 2, every) == S.assign(
            seconds, port, 2, every, frozenset())

    def test_logical_lines(self):
        text = ("* a comment\nlocal a 1 // note\nlocal b ///\n  2 ///\n"
                "  3\n// gone\n")
        assert S.logical_lines(text) == ["local a 1", "local b 2 3"]

    def test_assign_is_longest_first_onto_the_least_loaded(self):
        seconds = {"a": 10, "b": 8, "c": 6, "d": 5, "e": 1}
        assert S.assign(seconds, set(), 2) == {"a": 1, "b": 2, "c": 2,
                                                "d": 1, "e": 2}
        assert S.loads(seconds, S.assign(seconds, set(), 2), 2) == [15, 15]

    def test_the_fixed_port_scripts_are_one_unit(self):
        seconds = {"a": 10, "p": 4, "q": 4, "c": 6}
        got = S.assign(seconds, {"p", "q"}, 2)
        assert got["p"] == got["q"]
        # a (10) to 1, p and q (8 together) to 2, c (6) to 2, the lighter.
        assert got == {"a": 1, "p": 2, "q": 2, "c": 2}

    def test_ties_go_to_the_lowest_shard_and_by_name(self):
        assert S.assign({"b": 1, "a": 1}, set(), 3) == {"a": 1, "b": 2}

    def test_seconds_from_a_timed_log(self):
        log = ("[ TIME] test_a.cscript timer=    2.500s wall=     3s\n"
               "[ TIME] test_b.cscript timer=        .s wall=     8s\n"
               ". display as text \"[ TIME] test_c.cscript timer=\"\n"
               # A split script, timed in two shards' logs: their sum.
               "[ TIME] test_b.cscript timer=    1.000s wall=     1s\n")
        assert S.seconds_from_log(log) == {"test_a.cscript": 2.5,
                                           "test_b.cscript": 9.0}

    def test_the_table_reads_back(self):
        seconds = {"test_a.cscript": 3.0, "test_b.cscript": 1.5,
                   "test_p.cscript": 2.0}
        text = (S.render_table(seconds, {"test_p.cscript"}, "a run")
                + S.END + "\n")
        rows = S.read_table(text)
        assert [r[0] for r in rows] == sorted(seconds)
        assert {r[0]: r[1] for r in rows} == seconds
        assert [r[0] for r in rows if r[2]] == ["test_p.cscript"]
        for n in S.COUNTS:
            assert {r[0]: r[3][n] for r in rows} == S.assign(
                seconds, {"test_p.cscript"}, n)
        assert "// Seconds: a run" in text
        # Every row but the last continues the local.
        body = [l for l in text.splitlines() if l.startswith("    test_")]
        assert all(l.endswith(" ///") for l in body[:-1])
        assert not body[-1].endswith("///")

    def test_the_release_list_reads_back(self):
        seconds = {"test_a.cscript": 3.0, "test_b.cscript": 1.5,
                   "test_r.cscript": 9.0}
        text = (S.render_table(seconds, set(), "a run",
                               release={"test_r.cscript"}) + S.END + "\n")
        assert S.read_release(text) == ["test_r.cscript"]
        assert "local _cert_release test_r.cscript" in text
        assert [r[0] for r in S.read_table(text)] == sorted(seconds)
        for n in S.COUNTS:
            assert {r[0]: r[3][n] for r in S.read_table(text)} == S.assign(
                seconds, set(), n, frozenset(), {"test_r.cscript"})
        # No release tier, no line.
        assert "_cert_release" not in S.render_table(seconds, set(), "a run")

    def test_a_runner_without_one_table_is_refused(self):
        with pytest.raises(ValueError):
            S.read_table("no table here")
        assert S.check("no table here") == ["the runner has no single "
                                            "shard table"]


class TestTheCommandLine:

    def _tree(self, tmp_path):
        """A copy of the scripts, a runner of three scripts and the
        scripts themselves, one serving on 5098."""
        (tmp_path / "scripts").mkdir()
        for f in ("cert_shards.py", "cert_verdict.py"):
            shutil.copy(os.path.join(_ROOT, "scripts", f),
                        tmp_path / "scripts" / f)
        test = tmp_path / "test"
        test.mkdir()
        blocks = "".join('capture noisily {\n    do "%s"\n}\n' % s for s in
                         ("test_a.cscript", "test_b.cscript",
                          "test_p.cscript"))
        (test / "run_all_cscripts.do").write_text(
            "* runner\n" + S.BEGIN + "\n" + S.END + "\n" + blocks)
        (test / "test_a.cscript").write_text("dash scatter mpg weight\n")
        (test / "test_b.cscript").write_text("display 1\n")
        (test / "test_p.cscript").write_text(
            "capture dash serve, port(5098) nobrowser\n")
        log = tmp_path / "timed.log"
        log.write_text("[ TIME] test_a.cscript timer=   10.000s wall=  10s\n"
                       "[ TIME] test_b.cscript timer=    1.000s wall=   1s\n"
                       "[ TIME] test_p.cscript timer=    4.000s wall=   4s\n")
        return tmp_path, log

    def _run(self, tree, *args):
        return subprocess.run(
            [sys.executable, str(tree / "scripts" / "cert_shards.py"), *args],
            capture_output=True, text=True, timeout=60)

    def test_write_then_check(self, tmp_path):
        tree, log = self._tree(tmp_path)
        r = self._run(tree, "check")
        assert r.returncode == 1 and "no row for" in r.stdout
        r = self._run(tree, "write", str(log), "the test's run")
        assert r.returncode == 0, r.stdout + r.stderr
        r = self._run(tree, "check")
        assert r.returncode == 0, r.stdout
        text = (tree / "test" / "run_all_cscripts.do").read_text()
        rows = S.read_table(text)
        assert [(r[0], r[1], r[2]) for r in rows] == [
            ("test_a.cscript", 10.0, False), ("test_b.cscript", 1.0, False),
            ("test_p.cscript", 4.0, True)]
        assert text.endswith('do "test_p.cscript"\n}\n')
        r = self._run(tree, "show")
        assert r.returncode == 0 and "N=2: 1: 10 s  2: 5 s" in r.stdout

    def test_check_finds_a_hand_edited_shard(self, tmp_path):
        tree, log = self._tree(tmp_path)
        assert self._run(tree, "write", str(log)).returncode == 0
        path = tree / "test" / "run_all_cscripts.do"
        text = path.read_text()
        bad = re.sub(r"(test_b\.cscript\s+1\.0 0  )(\d)", lambda m: m.group(1)
                     + ("1" if m.group(2) == "2" else "2"), text)
        assert bad != text
        path.write_text(bad)
        r = self._run(tree, "check")
        assert r.returncode == 1
        assert "not the balanced assignment" in r.stdout

    def test_check_finds_a_wrong_port_mark(self, tmp_path):
        tree, log = self._tree(tmp_path)
        assert self._run(tree, "write", str(log)).returncode == 0
        (tree / "test" / "test_b.cscript").write_text("dash serve\n")
        r = self._run(tree, "check")
        assert r.returncode == 1 and "fixed-port marks" in r.stdout

    def test_check_finds_a_wrong_every_mark(self, tmp_path):
        tree, log = self._tree(tmp_path)
        (tree / "test" / "test_b.cscript").write_text(
            "local k : environment DASH_CERT_SHARD\n")
        assert self._run(tree, "write", str(log)).returncode == 0
        path = tree / "test" / "run_all_cscripts.do"
        assert re.search(r"test_b\.cscript\s+1\.0 0  \* \* \* ///$",
                         path.read_text(), re.M)
        assert self._run(tree, "check").returncode == 0
        (tree / "test" / "test_b.cscript").write_text("display 1\n")
        r = self._run(tree, "check")
        assert r.returncode == 1 and "* marks" in r.stdout

    def test_write_keeps_the_release_tier_and_its_seconds(self, tmp_path):
        # A default run times no release-tier script: write keeps the
        # list and those scripts' seconds from the table it replaces.
        tree, log = self._tree(tmp_path)
        assert self._run(tree, "write", str(log)).returncode == 0
        path = tree / "test" / "run_all_cscripts.do"
        path.write_text(path.read_text().replace(
            S.END, "local _cert_release test_a.cscript\n" + S.END))
        log.write_text("[ TIME] test_b.cscript timer=    2.000s wall=   2s\n"
                       "[ TIME] test_p.cscript timer=    5.000s wall=   5s\n")
        r = self._run(tree, "write", str(log))
        assert r.returncode == 0, r.stdout + r.stderr
        text = path.read_text()
        assert S.read_release(text) == ["test_a.cscript"]
        assert {r[0]: r[1] for r in S.read_table(text)} == {
            "test_a.cscript": 10.0, "test_b.cscript": 2.0,
            "test_p.cscript": 5.0}
        assert self._run(tree, "check").returncode == 0
        r = self._run(tree, "show")
        assert "N=2 default: 1: 5 s  2: 2 s" in r.stdout, r.stdout

    def test_check_finds_a_release_script_the_runner_does_not_run(
            self, tmp_path):
        tree, log = self._tree(tmp_path)
        assert self._run(tree, "write", str(log)).returncode == 0
        path = tree / "test" / "run_all_cscripts.do"
        path.write_text(path.read_text().replace(
            S.END, "local _cert_release test_z.cscript\n" + S.END))
        r = self._run(tree, "check")
        assert r.returncode == 1
        assert "the release tier names a script the runner does not run: " \
            "test_z.cscript" in r.stdout

    def test_write_needs_every_script_timed(self, tmp_path):
        tree, log = self._tree(tmp_path)
        log.write_text("[ TIME] test_a.cscript timer=   10.000s wall=  10s\n")
        r = self._run(tree, "write", str(log))
        assert r.returncode == 1 and "times no run of" in r.stdout

    def test_usage(self, tmp_path):
        tree, _ = self._tree(tmp_path)
        assert self._run(tree).returncode == 2
        assert self._run(tree, "bogus").returncode == 2


class TestTheRunnerRunsOnlyItsShard:
    """The runner's text: the selection reads the two settings by value and
    refuses a bad one before anything runs, and every script's block runs
    only when that script is selected."""

    def test_every_block_is_guarded_by_its_own_name(self):
        src = _runner()
        lines = src.splitlines()
        for name in V.registered_scripts(src):
            i = next(j for j, l in enumerate(lines)
                     if re.match(r'^\s*do "(?:test/)?%s"\s*$' % re.escape(name),
                                 l))
            guard = 'local _cert_go : list posof "%s" in _cert_run' % name
            g = max(j for j in range(i) if lines[j].startswith(
                "local _cert_go : list posof"))
            assert lines[g] == guard, (name, lines[g])
            assert lines[g + 1] == "if `_cert_go' {", name
            assert lines[g + 2] == 'display as text "[ RUN ] %s"' % name

    def test_each_guard_closes_after_its_verdict(self):
        src = _runner()
        for name in V.registered_scripts(src):
            fail = '    display as error "[ FAIL] %s  (rc=`rc\')"' % name
            assert src.count(fail) == 1, name
            tail = src[src.index(fail):].split("\n")[1:4]
            assert tail == ["    local n_fail = `n_fail' + 1", "}", "}"], \
                (name, tail)

    def test_the_settings_are_read_and_checked_by_value_first(self):
        src = _runner()
        sel = src[src.index("// ---- selection: begin"):
                  src.index("// ---- selection: end ----")]
        assert "local _cert_sh : environment DASH_CERT_SHARD" in sel
        assert '"^[1-4]/[1-4]$"' in sel
        assert "local _cert_only : environment DASH_CERT_ONLY" in sel
        assert '"^[ A-Za-z0-9_.]*$"' in sel
        # Checked in Mata, on the local's value, before either is expanded.
        assert sel.index('st_local("_cert_sh")') < sel.index('"`_cert_sh\'"')
        assert sel.index('st_local("_cert_only")') < \
            sel.index('"`_cert_only\'"')
        # 3 -> 4: the release tier's DASH_CERT_TIER is checked the same way
        assert sel.count("exit 198") == 4
        assert "local _cert_tier : environment DASH_CERT_TIER" in sel
        assert '"^(default|release|all)?$"' in sel
        assert sel.index('st_local("_cert_tier")') < \
            sel.index('"`_cert_tier\'"')
        # Before the first script.
        assert src.index("// ---- selection: end ----") < \
            src.index('display as text "[ RUN ]')

    def test_the_tier_picks_the_scripts_unless_only_names_them(self):
        sel = _runner()
        sel = sel[sel.index("// ---- selection: begin"):
                  sel.index("// ---- selection: end ----")]
        assert 'if "`_cert_tier\'" == "default" local _cert_run : list ' \
            "_cert_run - _cert_release" in sel
        assert 'if "`_cert_tier\'" == "release" local _cert_run : list ' \
            "_cert_run & _cert_release" in sel
        # DASH_CERT_ONLY picks by name from every script, whatever the tier.
        assert sel.index('if "`_cert_only\'" != "" {') < sel.index(
            'if "`_cert_tier\'" == "default"')
        assert 'display as text "[ TIER] `_cert_tier\'"' in _runner()

    def test_a_star_row_runs_in_every_shard(self):
        sel = _runner()
        assert ('    if "`_cert_at\'" == "*" | "`_cert_at\'" == "`_cert_k\'" '
                "local _cert_run `_cert_run' `_cert_s'") in sel

    def test_the_log_says_which_shard_and_plan(self):
        src = _runner()
        assert ('display as text "[SHARD] `_cert_k\'/`_cert_N\': '
                '`_cert_nrun\' of `_cert_nall\' scripts"') in src
        assert src.index("[SHARD]") < src.index('display as text "[ RUN ]')
        # A shard with nothing planned (a DASH_CERT_ONLY subset) passes.
        assert "else if `n_pass' == 0 & `_cert_nrun' > 0 {" in src


class TestTheTableIsOneStataCommand:
    """Batch 34.1's gate (22oct2026): a row added after the table's last
    row, which had no `///', made Stata read the new row as a command
    (r(199)) and no certification script ran; the Python reader took it."""

    def test_every_row_but_the_last_continues_the_command(self):
        assert S.continuation_problems(_runner()) == []

    def test_a_row_after_an_unfinished_last_row_is_named(self):
        text = (S.BEGIN + "\nlocal _cert_shards ///\n"
                "    test_a.cscript    1.0 0  1 1 1 ///\n"
                "    test_b.cscript    1.0 0  1 1 1\n"
                "    test_c.cscript    1.0 0  1 1 1\n" + S.END + "\n")
        assert S.continuation_problems(text) == [
            "test_b.cscript's row ends the table's command, but "
            "test_c.cscript's row follows it"]
        good = text.replace("1 1 1\n    test_c", "1 1 1 ///\n    test_c")
        assert S.continuation_problems(good) == []
        bad = good.replace("test_c.cscript    1.0 0  1 1 1\n",
                           "test_c.cscript    1.0 0  1 1 1 ///\n")
        assert S.continuation_problems(bad) == [
            "the table's last row, test_c.cscript's, continues "
            "into the next line"]
