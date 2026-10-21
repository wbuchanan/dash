# Section 36-03: Function points of named graphs kept off the macro

> Part of: WP-36 (Python discovery and environment) · Items: plat:PT-4 · Risk: yellow · Batch: 36.1 · Depends on: none · Blocks: none · Tasks: 3, 1 commit · Case-id prefix: Q3603

## Overview

**What is wrong today.** The audit (package 2, plat:PT-4, audit :94-96 and appendix :2262-2267): "Named graphs with function layers are capped by c(macrolen)". `twoway (function y=sin(x), range(0 10) n(10000)) (function y=cos(x), range(0 10) n(10000))` draws, rc 0. With `name()`, dash keeps a named graph's function points in one global, `$dash_fpts_<name>` (dash.ado:11399), and refuses a graph whose points are longer than `c(macrolen)` (dash.ado:11366-11377): measured at `c(macrolen)` 264,392 the two layers are refused r(134), "holds 408,235 characters of function points, more than the 264392 one Stata macro holds ... or raise c(macrolen) with set maxvar" -- one 10,000-point layer is 203,324 characters, so four such layers are refused at the default 645,200 too, the limit is printed unformatted, and the advice does not always help. The one-line form keeps the same points in a temporary string scalar and draws them.

**What will be true after.** Ruling M8 / Q35 and DECISIONS A-7: a named graph's function points live in a private file of dash's temporary folder, one file per graph keyed by its name -- `fp-<hex of the name>.txt` in this Stata session's folder `c(tmpdir)dash-<uid>/points-<pid>/` (0700; the file 0600, made by the same private writer as every other copy dash keeps) -- reached through five small Mata functions (path, put, get, drop, clear). Nothing about them is bounded by `c(macrolen)`, so the refusal, its message and the help sentence that advises `set maxvar` are gone. A file outlives `clear all`, as the registry's globals do, so a function graph registered before a `clear all` is built with its points (a string scalar would have been dropped: REVIEW R2-48). The build reads the file where it read the global; replacing, retiring or clearing a graph removes it, as it dropped the global; the folder of a Stata session that has ended is swept as dash's stale run folders are.

**Test order and commit rule.** Task 36-03-01 writes the failing tests and the S03 truth block and saves the failure text, no commit; 36-03-02 moves the points; 36-03-03 flips the pins, edits the help, closes the item and commits once with the subject ending `(WP-36 plat:PT-4)`.

### Section decisions

- **D-36-03.a A private file, keyed by graph name (DECISIONS A-7).** The points of graph `<name>` are the file `fp-<h>.txt`, `<h>` the name's bytes in two hex digits each (Mata `invtokens(inbase(16, ascii(name)), "")`; a name is letters, digits and underscores, every byte 0x30-0x7a, so always two digits), in the session folder `<root>/points-<pid>`: `<root>` is dash's private root as `_dash_private_root(c(tmpdir))` gives it (`dash-<uid>`, or its fallback, with its note), `<pid>` the Stata process's id (`os.getpid()` in Stata's Python). The hex name keeps `G` and `g` apart on a case-insensitive file system (macOS's default); the pid keeps two Stata sessions of one account apart. The folder's path is held in the one global `$dash__fpdir`, which survives `clear all` as the folder does; a new Stata session starts with no such global and makes its own folder.
- **D-36-03.b One accessor family.** Python makes the folder (0700) and each file (empty, 0600) -- dash's privacy rule, "every copy is created 0600 by `_dash_private_write`" (test/test_private_files.py's docstring); Mata writes, reads and removes the file's contents, so the points (a strL in a string scalar) never cross a macro or `sfi`. Every reader and writer goes through `_dash_fpts_path(name)`, `_dash_fpts_put(name, text)`, `_dash_fpts_get(name)`, `_dash_fpts_drop(name)` and `_dash_fpts_clear()` in dash_parse.mata and the ado program `_dash_fpts_open name` (the one that calls Python); no ado line or test reads `$dash_fpts_*` afterwards. Certification scripts that set or read the points (test_parser.cscript FX-07..09 and FN-02..05, test_conformance.cscript:217-249, test_wp29_truth.cscript:1292 and :1513-1515, test_wp30_truth.cscript:473 and :6435) are flipped to the accessors.
- **D-36-03.c The session folder's life.** Made on the first function graph a session registers (`_dash_fpts_open`), kept for the session, emptied by `dash clear` (Mata, no Python needed: `dash clear` works without Python today and keeps doing so), and removed by the sweep once its Stata session has ended: `_dash_points_sweep(root)` drops a `points-<pid>` folder whose pid is dead (POSIX) or, on Windows, where liveness is never probed, one not modified for `_DASH_STALE_AGE_S` (a day), the rule `_dash_run_sweep` applies to run folders -- but never the folder of the running process (run folders of the running process are swept; points folders are not). The sweep runs from `_dash_fpts_dir` and from `dash clear`'s `_dash_tmp_clear`.
- **D-36-03.d Size.** No size check is added: P4-3 (33-15, batch 33.1) removed `$dash_max_bytes`, the page-size cap the function points were counted against at 090d928 (dash.ado:13410-13424).

## Risk: [yellow] -- every function graph's points change their home

**Why.** Registration, build, retire and `dash clear` all read or remove the points; a missed reader drops a function layer silently; a wrong path writes outside dash's private folder.

**Risk factors.** 1. The twelve certification sites of Evidence read or forge `$dash_fpts_*` directly. 2. `_dash_item_globals` (dash_parse.mata:6022-6049) lists `dash_fpts_<name>` among the globals it retires. 3. `dash clear` drops `dash_fpts_*` with `macro drop` (dash.ado:11985) and must keep working with no Python and no Mata library. 4. The one-line route already uses a tempname scalar and must not change. 5. Registration of a function graph now starts Python (to make the folder and the file). 6. A sweep must never remove a live session's points.

**Mitigation.** 1. Task 01 greps every reader into `<scratch>/36-03-readers.txt`; the verify greps `dash_fpts_` outside the accessors to zero. 2-3. TR-36-03.4 lists each site; `dash clear` calls `capture mata: _dash_fpts_clear()` (a missing library leaves the files, which nothing reads once the registry is empty). 4. `_dash_fn_spec_tail`'s `sc` branch (the one-line route) is untouched. 5. Registration runs after the dispatcher's `_dash_require_deps`, and `_dash_xm_load` keeps the renderer module for the session, so the cost is paid once and the build that follows pays nothing more. 6. The sweep keeps `os.getpid()`'s folder and every live pid's; TestTheSweep pins both.

## Dependencies

- **Depends on:** none in WP-36. It builds on 33-15 (batch 33.1, P4-3): the function points are no longer counted against a page-size cap.
- **Blocks:** none.
- **Parallel batch:** 36.1 with 36-01 and 36-02; merge order 36-01, 36-02, 36-03.
- **Can run with:** both. 36-01 edits dash.ado's Python programs (:270-410) and the harness gates (including test_parser.cscript :3517, :3743); 36-02 edits dash_render.py's figure backend (`_make_figure_body`, the served literals, two helpers after `_dash_overhangs`). This section edits `_dash_register_graph` (:11366-11402), `_dash_clear` (:11985), `_dash_drop_item` (:10261-10269), dash_parse.mata's `_dash_fn_spec_tail` (:6301-6340) and `_dash_item_globals` (:6022-6049), dash_render.py's private-folder helpers (after `_dash_tmp_write_text` :4202 and inside `_dash_tmp_clear` :4216), and test_parser.cscript :3295-3630. Shared lists: `_needed` and the dash_parse.mata `*!` header index (36-01, earlier in this batch's merge order, adds `_dash_pyname` on a new line directly before the list's last line, dash.ado:506): this section adds the four accessors dash.ado calls on one new continuation line of its own directly after the `_needed` line that holds `_dash_fn_spec_tail` (dash.ado:486 at 090d928; re-read), so its insertion and 36-01's are twenty lines apart and a cherry-pick never meets them in one hunk, and appends its five `*!` entries directly after the `_dash_fn_spec_tail` entry, touching no existing line (REVIEW R2-22); test/function_test_map.py: its two entries go after `'_dash_tmp_write_text'` (:672), 36-02's after `'_dash_overhangs.<locals>.raise_to'` (:614).

## Evidence

### Registration (dash.ado, re-read)

```stata
11366     // A function graph's points are kept in one global, which holds
11367     // c(macrolen) characters; st_global() past that truncates in silence
...
11373     if `_fp_len' > c(macrolen) {
11374         _dash_count_fmt _fp_len_s `_fp_len'
11375         display as error "dash: graph '`name'' holds `_fp_len_s' characters of function points, more than the `c(macrolen)' one Stata macro holds."
11376         display as error "      Use a smaller n(), put the function layers in separate graphs, or raise c(macrolen) with set maxvar."
11377         exit 134
...
11397     if `_fp_len' {
11398         mata: st_global("dash_fpts_" + st_local("name"), st_strscalar(st_local("fp_sc")))
11399     }
11400     else {
11401         capture macro drop dash_fpts_`name'
```
(the line number in the audit, :11399, is the store.) The points arrive in the string scalar named by `fp_sc`, built in `_dash_plot` (:8843-8892) and passed through `_dash_register_graph`'s arguments. The store follows the retire (`_dash_drop_item` :11389) and the spec/JSON globals (:11393-11394).

### Build, retire and clear

- dash.ado:13410-13424 at 090d928: `foreach _fpn of local _fp_names { local _fp_l : strlen global dash_fpts_`_fpn' ...}` then the `dash_max_bytes` refusal "characters of function points" -- removed with the page-size cap by 33-15 (P4-3); re-read at the batch base.
- dash.ado:13446: `mata: _dash_fn_spec_tail(st_local("specpath"), st_local("_fp_names"), "")`.
- dash_parse.mata:6321-6333: `txt = st_global("dash_fpts_" + nm[i])`, `_dash_fn_points_ok` check and note "the function points stored for graph '...' are not dash's".
- dash.ado:11985 `capture macro drop dash_fpts_*` in `_dash_clear`, then `capture _dash_tmp_clear` (:11994); dash.ado:10261-10269 `_dash_drop_item` drops the names `_dash_item_globals` returns; dash_parse.mata:6032 lists `"dash_fpts_" + nm`.

### dash's private folder (dash_render.py, re-read)

`_dash_private_root(tmpdir, create=True)` (:3745) returns `(root, note)` (`<tmpdir>dash-<uid>`, made 0700; a planted root replaced by a fallback root with a note); `_dash_private_dir_ok(path)` (:3623); `_dash_private_write(path, text, exclusive=False)` (:3799-3860: `O_CREAT|O_NOFOLLOW|O_NONBLOCK`, regular file of this account with one link, `ftruncate`, `fchmod 0600`); `_dash_pid_alive(pid)` (:3863); `_dash_run_sweep(root, now=None)` (:3888; `_DASH_RUN_RE` :3519, `_DASH_STALE_AGE_S = 86400` :3515); `_dash_run_open` (:3932; its OSError message "dash: dash could not make its temporary folder in %s: %s."); `_dash_tmp_write_text(path, text)` (:4202, `_dash_private_write` returning ""); `_dash_tmp_clear(tmpdir)` (:4216, compiled for `dash clear` by `dash_setup_lib.stdlib_entry` with the standard library alone, so everything it reaches must use only the standard library). dash.ado `_dash_tmp_open` (:7721-7754) shows the ado side: `_dash_require_python`, `_dash_xm_load`, one `python:` line per step, the note through `_dash_note`, an `err` ending r(603).

### Help

- dash.sthlp:3713-3716 (n() on function): "one graph's function points must fit in one Stata macro, c(macrolen) characters (645,200 by default, about 21 a point; set maxvar raises it), or the graph is refused with r(134)".
- dash.sthlp:884 ("and a function graph's points in $dash_fpts_name") and :1509-1511 (`dash clear` drops "$dash_fpts_*").

### Pins on today's behaviour (flip)

- test/test_parser.cscript FX-07 (:3295-3340): four 10,000-point layers with `name(fx07)` → r(134), log holds "n()" and `c(macrolen)`, `${dash_fpts_fx07}` empty. Its second half (one-line form rc 0) stays; its `dash_max_bytes 1000` refusal went with 33-15 (re-read).
- FX-08 (:3344-3375): reads and forges `${dash_fpts_fx08}`, `${dash_fpts_fx08g}`; FX-09 (:3385); FN-02..05 (:3571-3630: `macro drop dash_fpts_fn02`, `st_global("dash_fpts_fn04", ...)`, `macro drop dash_fpts_fn05`).
- test/test_conformance.cscript:217-249 (`st_global("dash_fpts_ctl", ...)`).
- test/test_wp29_truth.cscript:1292 (`st_global("dash_fpts_" + st_local("name"))`) and :1513-1515 (FX-23 reads `${dash_fpts_fx23_1}`, `${dash_fpts_fx23_2}`); :1269 is a comment only.
- test/test_wp30_truth.cscript:473 and :6435 (`st_global("dash_fpts_" + ...)`).
- test/program_coverage_map.py entries naming FX-07.

## User stories

- US-36-03.1 As a Stata user with an existing twoway command, I want `(function y=sin(x), range(0 10) n(10000)) (function y=cos(x), range(0 10) n(10000)), name(g)` registered and built, so that a named graph takes what twoway draws.
- US-36-03.2 As a Stata user whose do-file says `clear all` between registering graphs and `dash build`, I want my function graphs built with their points, so that `clear all` costs me nothing it did not cost before.

## Business requirements

- BR-36-03.1 A named graph with function layers of any length that twoway draws is registered and built; no message mentions `c(macrolen)` or `set maxvar`.
- BR-36-03.2 Replacing a function graph with another item and `dash clear` remove its points, as before; `clear all` keeps them, as it keeps the registry.
- BR-36-03.3 The help no longer tells the user to raise `c(macrolen)`, and says where the points are kept.
- BR-36-03.4 The points are readable only by the user's own account, like every other copy dash keeps.

## Technical requirements

- **TR-36-03.1 Python** (dash_render.py, standard library only, directly after `_dash_tmp_write_text`; module-level, not served -- the served app never reads them):
  ```python
  #: A Stata session's folder of named graphs' function points (WP-36
  #: plat:PT-4, DECISIONS A-7): <root>/points-<pid>.
  _DASH_POINTS_RE = re.compile(r"^points-(\d+)$")


  def _dash_points_sweep(root, now=None):
      """Remove the points folders of Stata sessions that have ended; return
      how many.  A ``points-<pid>`` folder goes when its pid is dead
      (POSIX) or, on Windows, where liveness is never probed, when it was
      last modified more than ``_DASH_STALE_AGE_S`` ago -- never the running
      process's own folder, whose files the session's graphs still need.
      Links and non-folders at such a name are unlinked, never followed.
      Every OSError is ignored."""
      now = time.time() if now is None else now
      try:
          names = os.listdir(root)
      except OSError:
          return 0
      removed = 0
      for name in names:
          m = _DASH_POINTS_RE.match(name)
          if not m:
              continue
          path = os.path.join(root, name)
          try:
              pid = int(m.group(1))
              if pid == os.getpid():
                  continue
              lst = os.lstat(path)
              if os.name == "nt":
                  drop = now - lst.st_mtime > _DASH_STALE_AGE_S
              else:
                  drop = not _dash_pid_alive(pid)
              if not drop:
                  continue
              if stat.S_ISDIR(lst.st_mode):
                  shutil.rmtree(path, ignore_errors=True)
              else:
                  os.unlink(path)
              removed += 1
          except OSError:
              continue
      return removed


  def _dash_fpts_dir(tmpdir):
      """This Stata session's points folder; the dict dash.ado reads.

      ``{"dir", "err", "note"}``: ``<root>/points-<pid>`` (0700), the root as
      ``_dash_private_root`` gives it, the root's ended sessions' folders
      swept first.  ``note`` and ``err`` are built as ``_dash_run_open``
      builds them (an OSError gives ``dir`` "" and ``err`` the reason, which
      dash.ado ends with r(603)); a ``_DashUnsafePath`` from the folder's own
      check is not caught (r(7102))."""
      out = {"dir": "", "err": "", "note": ""}
      note = ""
      try:
          root, note = _dash_private_root(tmpdir)
          _dash_points_sweep(root)
          d = os.path.join(root, "points-%d" % os.getpid())
          try:
              os.mkdir(d, 0o700)
          except FileExistsError:
              pass
          why = _dash_private_dir_ok(d)
          if why and "could not be made private" not in note:
              note = "  ".join(x for x in (note, _DASH_NOTE_LOOSE % (d, why))
                               if x)
      except OSError as exc:
          out["err"] = ("dash: dash could not make its temporary folder in "
                        "%s: %s." % (tmpdir, getattr(exc, "strerror", None)
                                     or exc))
          out["note"] = ("dash: note: " + note) if note else ""
          return out
      out.update(dir=d, note=("dash: note: " + note) if note else "")
      return out
  ```
  `_dash_tmp_clear` (:4216) calls `_dash_points_sweep(root)` right after its `_dash_run_sweep(root)` line (stdlib only, so `stdlib_entry` still compiles the closure). test/function_test_map.py, after `'_dash_tmp_write_text'` (:672): `'_dash_fpts_dir': 'test/test_function_points_file.py::TestTheFolder::test_made_0700_for_this_pid'`, `'_dash_points_sweep': 'test/test_function_points_file.py::TestTheSweep::test_ended_sessions_go_and_this_one_stays'`.
- **TR-36-03.2 Mata accessors** (dash_parse.mata, directly above `_dash_fn_spec_tail`; one `*!` entry each, the five directly after the `*!   _dash_fn_spec_tail(path, names, sc)` entry, dash_parse.mata:208-213 at 090d928, and before `*!   _dash_by_scan(scname)`, :215; re-read). `_needed` names the functions dash.ado calls, both ways (test/test_program_coverage_map.py::TestTheMataLibraryCheckNamesEveryFunctionDashCalls, REVIEW R2-47): dash.ado calls `_dash_fpts_path`, `_dash_fpts_put`, `_dash_fpts_drop` and `_dash_fpts_clear`, while `_dash_fpts_get` is reached only from `_dash_fn_spec_tail` inside Mata once 33-15 has removed the bytes check (TR-33-15.5). So one new continuation line `        _dash_fpts_path _dash_fpts_put _dash_fpts_drop _dash_fpts_clear ///` goes directly after the `_needed` line that holds `_dash_fn_spec_tail` (dash.ado:486 at 090d928; re-read), touching no existing line; `_dash_fpts_get` joins that line only under TR-36-03.4's last bullet:
  ```mata
  // A named graph's function points (WP-36 plat:PT-4, DECISIONS A-7): the
  // file fp-<hex of the name>.txt in this Stata session's points folder,
  // $dash__fpdir, which dash.ado's _dash_fpts_open makes (0700) and in
  // which it makes the file (0600, empty) through Python.  A file holds any
  // length -- a global holds c(macrolen) characters, and two 10,000-point
  // layers are twice that -- and outlives clear all, as the registry's
  // globals do.  Only these five read, write or remove it.
  string scalar _dash_fpts_path(string scalar nm)
  {
      string scalar d

      d = st_global("dash__fpdir")
      if (d == "" | nm == "") return("")
      return(pathjoin(d, "fp-" + invtokens(inbase(16, ascii(nm)), "") + ".txt"))
  }

  // Replaces the contents of the file _dash_fpts_open made; a graph with no
  // file (none made, or the folder gone) is left without points.
  void _dash_fpts_put(string scalar nm, string scalar txt)
  {
      string scalar p
      real scalar   fh

      p = _dash_fpts_path(nm)
      if (p == "") return
      if (!fileexists(p)) return
      fh = fopen(p, "rw")
      ftruncate(fh)
      if (txt != "") fwrite(fh, txt)
      fclose(fh)
  }

  string scalar _dash_fpts_get(string scalar nm)
  {
      string scalar p, txt, s
      real scalar   fh

      p = _dash_fpts_path(nm)
      if (p == "") return("")
      if (!fileexists(p)) return("")
      fh = fopen(p, "r")
      txt = ""
      while ((s = fread(fh, 1048576)) != J(0, 0, "")) txt = txt + s
      fclose(fh)
      return(txt)
  }

  void _dash_fpts_drop(string scalar nm)
  {
      string scalar p

      p = _dash_fpts_path(nm)
      if (p == "") return
      if (fileexists(p)) (void) _unlink(p)
  }

  void _dash_fpts_clear()
  {
      string colvector f
      string scalar    d
      real scalar      i

      d = st_global("dash__fpdir")
      if (d == "") return
      f = dir(d, "files", "fp-*.txt")
      for (i = 1; i <= rows(f); i++) (void) _unlink(pathjoin(d, f[i]))
  }
  ```
  (`fopen(p, "rw")` opens an existing file at its start without changing its mode; `ftruncate(fh)` empties it from the current position; `fread` returns `J(0, 0, "")` at the end; `_unlink` returns a code and never stops the program. Task 01 checks each on StataNow 19.5 with Q3603-1.)
- **TR-36-03.3 `_dash_fpts_open name`** (dash.ado, new program after `_dash_tmp_clear`, version 19): `args name`; first, always, `_dash_require_python`, `_dash_xm_load` (the renderer module is kept for the session, so this costs nothing after the first call) and the three lines `python: import sys` / `python: from sfi import Macro as _dash_M` / `python: _dash_xm = sys.modules["_dash_render_export"]`; then, when `$dash__fpdir` is empty or Mata `direxists(st_global("dash__fpdir"))` is 0: `local _fo_tmp `"`c(tmpdir)'"'` and one `python:` line per step as `_dash_tmp_open` (:7721-7754) has them -- `_dash_fo = _dash_xm._dash_fpts_dir(_dash_M.getLocal("_fo_tmp"))`, `setLocal("_fo_err", ...)`, `setLocal("_fo_note", ...)`, `setLocal("_fo_dir", ...)`; a non-empty note through `mata: _dash_note("", st_local("_fo_note"), "")`; a non-empty err through `mata: _dash_say("err", "", st_local("_fo_err"), "")` and `exit 603`; then `mata: st_global("dash__fpdir", st_local("_fo_dir"))`. Always then: `mata: st_local("_fo_path", _dash_fpts_path(st_local("name")))` and `python: _dash_fo = _dash_xm._dash_tmp_write_text(_dash_M.getLocal("_fo_path"), "")` (the empty 0600 file; a link or a foreign file at the name is refused r(7102), as for every copy). program_coverage_map.py: `"_dash_fpts_open": ("test_wp36_truth.cscript:Q3603-2",)`.
- **TR-36-03.4 Registration, readers and droppers.**
  - `_dash_register_graph` (dash.ado:11366-11402): delete the comment :11366-11368 and the `c(macrolen)` refusal :11373-11378, keeping the `_fp_len` computation; replace the store :11397-11402 with:
    ```stata
    // The graph's function points (WP-29 P0.6), off the macro (WP-36
    // plat:PT-4, DECISIONS A-7): the file _dash_fpts_path names, made
    // empty and private by _dash_fpts_open, written by Mata from the
    // string scalar.  A graph that replaced a function graph keeps no
    // points of it.  A $dash_fpts_<name> an older dash left is dropped.
    mata: _dash_fpts_drop(st_local("name"))
    if `_fp_len' {
        _dash_fpts_open `name'
        mata: _dash_fpts_put(st_local("name"), st_strscalar(st_local("fp_sc")))
    }
    capture macro drop dash_fpts_`name'
    ```
  - `_dash_fn_spec_tail` (dash_parse.mata:6323): `txt = st_global("dash_fpts_" + nm[i])` → `txt = _dash_fpts_get(nm[i])`; its comment (:6286-6300) and its `*!` entry (:208-212) name the file instead of `$dash_fpts_<name>`.
  - `_dash_item_globals` (dash_parse.mata:6032): remove `"dash_fpts_" + nm` from `own` (the points are not a global) and say so in its comment (:6002); `_dash_drop_item` (dash.ado:10261-10269) gains `mata: _dash_fpts_drop(st_local("name"))` after its loop (a KPI that replaces a function graph takes its points away, :12266).
  - `_dash_clear` (dash.ado:11985): keep `capture macro drop dash_fpts_*` (globals an older dash left), and add before `capture _dash_tmp_clear` the line `capture mata: _dash_fpts_clear()` with the comment `// The function graphs' point files (WP-36 plat:PT-4); with no Mata library loaded they stay, and nothing reads them once the registry is empty.`
  - Build: if the batch base still holds any `strlen global dash_fpts_` read (the bytes check 33-15 removed), it becomes `mata: st_local("_fp_l", strofreal(strlen(_dash_fpts_get(st_local("_fpn")))))` and `_dash_fpts_get` is added at the end of TR-36-03.2's new `_needed` line (dash.ado then calls it); otherwise nothing changes there and `_dash_fpts_get` stays off `_needed`.
- **TR-36-03.5 Maps (R6).** test/program_coverage_map.py: `_dash_register_graph`'s and `_dash_clear`'s entries gain `"test_wp36_truth.cscript:Q3603-2"`; the FX-07 reference stays (FX-07 is flipped, not removed); under `"dash.ado"`, `"_dash_fpts_open": ("test_wp36_truth.cscript:Q3603-2",),` (TR-36-03.3). Under `"dash_parse.mata"`, directly after the `"_dash_fn_spec_tail"` entry (test/program_coverage_map.py:706-707 at 090d928; re-read), five entries, each `("test_wp36_truth.cscript:Q3603-1",)`: `"_dash_fpts_path"`, `"_dash_fpts_put"`, `"_dash_fpts_get"`, `"_dash_fpts_drop"`, `"_dash_fpts_clear"` -- test_program_coverage_map.py::TestTheMapCoversEveryUnit::test_every_unit_has_an_entry requires an entry for every dash_parse.mata function.
- **TR-36-03.6 Help (R3).** dash.sthlp:3713-3716: delete "; one graph's {cmd:function} points must fit in one Stata macro, {cmd:c(macrolen)} characters (645,200 by default, about 21 a point; {cmd:set maxvar} raises it), or the graph is refused with {cmd:r(134)}" (the sentence ends after "over {cmd:range()}"). :884: "(and a {cmd:function} graph's points in {cmd:$dash_fpts_}{it:name})" → "(and a {cmd:function} graph's points in a private file of {cmd:dash}'s temporary folder, kept until the graph is replaced, {cmd:dash clear} runs or Stata exits; {cmd:clear all} keeps it, as it keeps the globals)". :1509-1511: drop "{cmd:$dash_fpts_*}" from the globals list and add, after the list, "and the function graphs' point files".
- **TR-36-03.7 Both modes.** No renderer change: the spec still carries `"function_points"` (`_dash_attach_function_points`, dash_render.py:5119), written by `_dash_fn_spec_tail` the same way.

## Boundaries

- Do not change the one-line route's `_fp_sc` (dash.ado:8843-8892) or `_dash_fn_spec_tail`'s `sc` branch.
- Do not change the n() bound 1-10,000 (a documented count cap, 40-02); add no size check (P4-3).
- Do not move the graph JSON (`$dash_json_<name>`) off the macro: not in this item.
- Do not change `_dash_run_sweep`, `_dash_run_open` or the previews; the points folder has its own sweep.
- No edition text (R14): the message and help lose the `set maxvar` advice entirely.

## Stata truth

No fixture: twoway draws the probe (rc 0, measured by the audit, `probe3.do` F2) and the block measures it live (R1), above the marker of test/test_wp36_truth.cscript:
```
* ==== S03 plat:PT-4: function points of a named graph off the macro ====
```
- Q3603-1: the accessors on a scratch folder: `global dash__fpdir` set to a fresh folder under the block's work dir; `_dash_fpts_open q1` (makes the file); `_dash_fpts_put("q1", "abc")`, `_dash_fpts_get("q1") == "abc"`, `_dash_fpts_put("q1", "x")`, `_dash_fpts_get("q1") == "x"` (a shorter text replaces a longer one), `_dash_fpts_path("Q1") != _dash_fpts_path("q1")`, `_dash_fpts_drop("q1")`, `_dash_fpts_get("q1") == ""`, `_dash_fpts_drop("q1")` again is no error, and `_dash_fpts_clear()` on a folder holding two files leaves none; the global is put back afterwards.
- Q3603-2: at the session's own `c(macrolen)` (printed; 645,200 here), four layers `(function y = sin(x)/x, range(-100 100) n(10000))` -- about 813,000 characters, past one macro, FX-07's probe: `capture noisily twoway <four layers>, nodraw` rc 0 beside `capture noisily dash <four layers>, name(q2)` rc 0, then `dash build, saving(<tmp>.html) replace nobrowser` rc 0 and the page's spec carries 40,000 function points (a `python:` helper parsing the page's document JSON counts the `y` lists of the four function layers). No `set maxvar` is used.
- Q3603-3: `dash scatter mpg weight, name(q2, replace)` leaves no file `_dash_fpts_path("q2")`; `dash function y = x, name(q3)` then `dash clear` leaves no `fp-*.txt` in `$dash__fpdir`.

The `clear all` case cannot run inside a certification script (it drops the script's own helper programs); it is a release-tier pytest that starts one console Stata through `scripts/stata_slot.sh` (TDD stubs, TestClearAll).

## TDD test stubs

Failing first (task 01):
- Test: no macro holds points -- test/test_function_points_file.py::TestOffTheMacro::test_no_ado_line_stores_points_in_a_global (dash.ado code: no `st_global("dash_fpts_"` and no `strlen global dash_fpts_`), ::test_no_macrolen_refusal (no `c(macrolen)` in `_dash_register_graph`'s body), ::test_the_accessors_exist (dash_parse.mata defines the five accessors and dash.ado defines the program `_dash_fpts_open`; it asserts nothing about `_needed`, which test_program_coverage_map.py checks in both directions, REVIEW R2-47).
- Test: the folder -- test/test_function_points_file.py::TestTheFolder::test_made_0700_for_this_pid (`_dash_fpts_dir(str(tmp_path))["dir"]` ends `points-<os.getpid()>` under `dash-<uid>` and is 0700 under umask 022 and 002), ::test_a_planted_link_is_refused (a link at the folder's name raises `_DashUnsafePath`).
- Test: the sweep -- test/test_function_points_file.py::TestTheSweep::test_ended_sessions_go_and_this_one_stays (folders `points-<dead pid>` (from a finished subprocess), `points-<os.getpid()>` and `points-<os.getppid()>`: only the first goes), ::test_tmp_clear_sweeps_them (`_dash_tmp_clear` removes an ended session's folder), ::test_stdlib_entry_still_compiles (`dash_setup_lib.stdlib_entry("dash_render.py", "_dash_tmp_clear")` is not None).
- Test: the help -- test/test_function_points_file.py::TestTheHelp::test_no_macrolen_advice (the n() paragraph holds neither `c(macrolen)` nor `set maxvar`), ::test_the_points_home_is_named (the "What a name may be" sub-point names the private file and `clear all`).
- Test (release tier; a guard, green at the base and after): test/test_function_points_file.py::TestClearAll::test_points_survive_clear_all (`@pytest.mark.release`; one Stata run through `sh <repo>/scripts/stata_slot.sh <tmp> clearall.do` (`<repo>` the absolute folder holding dash.ado, `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))`; `clearall.do` is written into `<tmp>`, where the slot script runs it), timeout 900: `adopath ++ "<repo>"`, `global dash_nobrowser 1`, `sysuse auto, clear`, `dash function y = x, n(5) name(ca)`, `clear all`, `_dash_serve_spec, specpath("spec.json") datapath("data.json")` (the spec seam test_wp31_truth.cscript U46-04 uses); the test reads spec.json's `function_points.ca."1".y` and asserts five values; skipped with its reason only when `STATA_BIN` is not an executable file, which `make test-release` (strict) fails).
- cscript: Q3603-1..3 (S03).

Pins flipped (task 03):
- test_parser.cscript FX-07: the four-layer `name(fx07)` → rc 0 and `_dash_fpts_get("fx07") != ""`; its "c(macrolen)" needles removed, comment `// Flipped (WP-36 plat:PT-4): a named graph's points are a private file, unbounded by c(macrolen).`
- FX-08, FX-09, FN-02..05, test_conformance.cscript:217-249, test_wp29_truth.cscript:1292 and :1513-1515, test_wp30_truth.cscript:473 and :6435: `${dash_fpts_x}` → `mata: st_local("_p", _dash_fpts_get("x"))` then the same comparison on `_p` (where the text may pass `c(macrolen)`, compare inside Mata instead: `mata: st_local("_ok", strofreal(strpos(_dash_fpts_get("x"), <needle>) > 0))`); `st_global("dash_fpts_x", T)` → `_dash_fpts_open x` (when the graph was registered without function layers, so no file exists) then `mata: _dash_fpts_put("x", T)`; `macro drop dash_fpts_x` → `mata: _dash_fpts_drop("x")`; each with a `// Flipped (WP-36 plat:PT-4): ...` comment.

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| no global, no macrolen refusal, accessors present | pytest TestOffTheMacro | -- | n/a |
| folder 0700 per pid, sweep keeps live sessions | pytest TestTheFolder, TestTheSweep | -- | n/a |
| accessors replace, read, drop, clear | cscript S03 Q3603-1 | -- | n/a |
| four 10,000-point layers past one macro | cscript S03 Q3603-2 (twoway beside dash) | -- | saved build (the served build reads the same spec) |
| retire and clear remove the file | Q3603-3; FX-08 flipped | -- | n/a |
| `clear all` keeps the points | release pytest TestClearAll | -- | spec (both renderers read it) |
| help sentences | pytest TestTheHelp | -- | n/a |
| no plain plat:PT-4 ledger or known-differences row; guard verdicts unchanged or regenerated | pytest test_corpus_ledger.py; `python3 test/known_differences.py plat:PT-4` and its hygiene command; S09 block of test_wp33_truth.cscript (`WP33_ONLY=S09`) | corpus_ledger.json, corpus_guard_truth.json | n/a |

- AC-36-03.1 Q3603-2 passes: twoway rc 0 and dash rc 0 with 40,000 points embedded.
- AC-36-03.2 `grep -n 'dash_fpts_' dash.ado dash_parse.mata` hits only the accessors, `_dash_fpts_open`, their comments and the two legacy `capture macro drop` lines.
- AC-36-03.3 TestClearAll passes: five points after `clear all`.

## Tasks

**Commit boundary.** One commit by 36-03-03, subject `Keep a named graph's function points in a private file, not a macro (WP-36 plat:PT-4)`, staging dash.ado, dash_parse.mata, dash_render.py, dash.sthlp, test/test_function_points_file.py, test/test_parser.cscript, test/test_conformance.cscript, test/test_wp29_truth.cscript, test/test_wp30_truth.cscript, test/program_coverage_map.py, test/function_test_map.py, the S03 block, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, GAPS4.md, CHANGELOG.md, test/test_tracking_documents.py, plus scripts/corpus/ledger.tsv and test/fixtures/corpus_ledger.json (and test/fixtures/corpus_guard_truth.json) when 36-03-03's ledger step changes them, and each test file whose `*_KNOWN` or `*_DELIBERATE` table its known-differences step edits (BRIEF "The corpus ledger and the known-differences tables"). `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp36-s03` (BRIEF "Pull form": every command names the worktree by this absolute path; `scripts/stata_slot.sh` runs `cd <scratch>` before Stata starts, so a relative path is not found).

<task type="auto" id="36-03-01">
  <name>Write the failing point-storage tests</name>
  <files>test/test_function_points_file.py, test/test_wp36_truth.cscript</files>
  <action><![CDATA[
    In $WT, run `grep -rn 'dash_fpts_' dash.ado dash_parse.mata dash_render.py dash.sthlp test/ > <scratch>/36-03-readers.txt` and compare with Evidence; add any new reader to TR-36-03.4's list in the hand-back. Re-read dash.ado:11360-11410, :10255-10270, :11975-11996, :13400-13450 (what 33-15 left of the bytes check), dash_parse.mata:6000-6050 and :6286-6340, and dash_render.py:3880-3970 and :4200-4250. Run `node .gitnexus/run.cjs impact "<name>" --direction upstream --repo .` for `_dash_register_graph`, `_dash_drop_item`, `_dash_clear`, `_dash_fn_spec_tail`, `_dash_item_globals` and `_dash_tmp_clear`, writing callers and risk to `<scratch>/36-03/anchors.txt` (HIGH, CRITICAL or UNKNOWN named in the hand-back; an UNKNOWN confirmed with `grep -n` before editing). Create test/test_function_points_file.py with TestOffTheMacro, TestTheFolder, TestTheSweep, TestTheHelp and TestClearAll as in the stubs (ado/Mata/help read as text, comments dropped as test_cscript_hygiene.py's `_code` does; the Python helpers reached with `getattr` inside each test, so a tree without them fails on an assertion, never at collection). Append the S03 block (Q3603-1..3) above the marker of test/test_wp36_truth.cscript. Run `python3 -m pytest test/test_function_points_file.py -q -n0 -p no:cacheprovider -rf > <scratch>/36-03-01.log` (the file named, so TestClearAll runs) and S03 through the driver with `WP36_ONLY=S03`; save failing nodes and FAIL lines to `<scratch>/36-03-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/36-03-01.log` prints 9 (TestOffTheMacro 3, TestTheFolder 2, TestTheSweep 2 -- test_stdlib_entry_still_compiles passes at the base --, TestTheHelp 2); TestClearAll passes at the base (a global survives clear all) and is the guard that the move keeps that behaviour (REVIEW R2-48); the log has no `skipped`; `grep -c "Q3603-1 FAIL\|Q3603-2 FAIL" <scratch>/run_test_wp36_truth.log` prints 2 (no accessor; dash refuses r(134) where twoway draws); `test -s <scratch>/36-03-01-failure.txt`.]]></verify>
  <done>The point-storage tests and certification cases existed and were shown failing on the unmodified tree, with twoway's rc 0 measured beside dash's r(134).</done>
</task>

<task type="auto" id="36-03-02">
  <name>Move the points to a private file</name>
  <files>dash.ado, dash_parse.mata, dash_render.py</files>
  <action><![CDATA[
    Add `_DASH_POINTS_RE`, `_dash_points_sweep` and `_dash_fpts_dir` after `_dash_tmp_write_text`, and the `_dash_points_sweep(root)` call in `_dash_tmp_clear` (TR-36-03.1), with the two test/function_test_map.py entries after `'_dash_tmp_write_text'`. Add the five Mata accessors above `_dash_fn_spec_tail`, their header-index entries after the `_dash_fn_spec_tail` entry and the one new `_needed` continuation line of the four accessors dash.ado calls, directly after the `_needed` line holding `_dash_fn_spec_tail` (TR-36-03.2). Add `_dash_fpts_open` (TR-36-03.3). Apply TR-36-03.4 in `_dash_register_graph`, `_dash_fn_spec_tail`, `_dash_item_globals`, `_dash_drop_item`, `_dash_clear` and, if present, the build's bytes read (with `_dash_fpts_get` then on the new `_needed` line); and TR-36-03.5's test/program_coverage_map.py entries, the five Mata ones included. Run `python3 -m pytest test/test_function_points_file.py test/test_private_files.py test/test_program_coverage_map.py test/test_function_test_map.py test/test_file_headers.py -q -n0 -p no:cacheprovider` and S03 through the driver.
  ]]></action>
  <verify><![CDATA[test_function_points_file.py passes except TestTheHelp (fixed in 36-03-03), TestClearAll included; test_private_files.py passes; `grep -c "Q3603-[1-3] PASS" <scratch>/run_test_wp36_truth.log` prints 3; `grep -n 'st_global("dash_fpts_\|strlen global dash_fpts_' dash.ado dash_parse.mata | wc -l` prints 0; `diff <(git show HEAD:dash.ado | sed -n '/^    local _needed /,/[^\/]$/p') <(sed -n '/^    local _needed /,/[^\/]$/p' dash.ado) | grep -c '^<'` prints 0 (no base line of the `_needed` list is removed or changed; the check reads the list alone, since this task also deletes the c(macrolen) refusal's `        _dash_count_fmt _fp_len_s ...` line, dash.ado:11374) and the same command with `grep -c '^>'` prints 1 (the section's one new continuation line); test_program_coverage_map.py (TestTheMataLibraryCheckNamesEveryFunctionDashCalls and TestTheMapCoversEveryUnit included), test_function_test_map.py and test_file_headers.py pass.]]></verify>
  <done>Named graphs' function points were stored, read, retired and cleared as private files of the session's points folder, kept through clear all, and the c(macrolen) refusal was gone.</done>
</task>

<task type="auto" id="36-03-03">
  <name>Flip the point pins, fix the help, commit</name>
  <files>test/test_parser.cscript, test/test_conformance.cscript, dash.sthlp</files>
  <action><![CDATA[
    Flip FX-07, FX-08, FX-09, FN-02..05 (test/test_parser.cscript), test/test_conformance.cscript:217-249, test/test_wp29_truth.cscript:1292 and :1513-1515 and test/test_wp30_truth.cscript:473/:6435 as in the stubs, each with its `// Flipped (WP-36 plat:PT-4): ...` comment. Apply TR-36-03.6 (dash.sthlp :3713-3716, :884, :1509-1511). Append to TWOWAY_COVERAGE_AUDIT.md's function row (:100, re-read) `[WP-36 plat:PT-4: corrected -- a named graph's function points are no longer bounded by c(macrolen)]` (REVIEW R2-9). Run through the driver test_parser.cscript, test_conformance.cscript, test_wp29_truth.cscript and test_wp30_truth.cscript with `WP29_ONLY`/`WP30_ONLY` set to the blocks holding the flipped lines (read their headers), plus S03; run `python3 -m pytest test/test_function_points_file.py test/test_help_conformance.py test/test_help_claims_1.py test/test_tracking_documents.py -q -p no:cacheprovider`. Close the BUGS.md entry 33-01 opened for plat:PT-4 (`grep -n 'WP-36 section 36-03 has not landed' BUGS.md`) in PD-4's closed form (Pinned by test/test_function_points_file.py::TestOffTheMacro, ::TestClearAll, Q3603-1..3; no fixture); rewrite GAPS4.md's plat:PT-4 Tracked line (`commit pending`); delete plat:PT-4 from `GAPS4_OPEN`; CHANGELOG `### Changed behaviour (may need your do-files changed)`: `- A named graph whose function points exceeded c(macrolen) was refused r(134); it is registered and built, its points kept in a private file of dash's temporary folder, which clear all keeps (WP-36, plat:PT-4)`. The corpus ledger and the known-differences tables (BRIEF "The corpus ledger and the known-differences tables", steps 1-3; D-33-05.i, D-33-10.h): (1) run `awk -F'\t' '$1 == "plat:PT-4" {print NR ": " $0}' scripts/corpus/ledger.tsv` and delete every line it prints (the item's plain rows; a `plat:PT-4 (documented)` or `plat:PT-4 (residual)` row stays, A-10), rerun `python3 scripts/corpus/ledger.py` (33-05; no run folder: `_meta` is kept, TR-33-05.3), `git add -f test/fixtures/corpus_ledger.json` (when no row was deleted the fixture is unchanged and nothing is staged) and run `python3 -m pytest test/test_corpus_ledger.py -q -n0 -p no:cacheprovider`; (2) run `python3 test/known_differences.py plat:PT-4` (33-10) and delete every `<file>:<line>` row it prints from its `*_KNOWN` table -- a difference this item's ruling keeps moves instead into that table's deliberate dict, the companion dict 33-10 names for it (`DELIBERATE` in test/value_truth_known.py for `VALUE_KNOWN`, `ABBREV_DELIBERATE` in test/test_abbreviations.py for `ABBREV_KNOWN`, and beside 33-11..33-13's tables `SCALE_FRAME_DELIBERATE`, `BY_TYPES_DELIBERATE`, `BY_POSITION_DELIBERATE`, `STAT_COMBOS_DELIBERATE`, `COLORVAR_DELIBERATE`), as `"<key>": "<ruling id>: <what is kept>"` with a DECISIONS or index ruling id (P4-n, A-n, Q-n, M-n); no ruling keeps a plat:PT-4 difference on purpose (M8, Q35, A-7), so none is expected -- then run the hygiene command it prints (`python3 -m pytest <files> -q -n0 -k every_known_difference_is_open`), which passes, and stage each table file the step edited, by the path the printed row names; (3) run the corpus guard block (`WP33_ONLY=S09 sh $WT/scripts/stata_slot.sh <scratch> <scratch>/run_test_wp33_truth.do`, the driver of BRIEF "Running one cscript" written for test/test_wp33_truth.cscript with `<repo>` = `$WT`) and, if Q3309-1 reports any change for a guard example -- an improved verdict (`<id> improved from ...`) or a changed field (`<id>: <field> was <old> now <new>`) -- regenerate test/fixtures/corpus_guard_truth.json with `DASH_REPO=$WT sh $WT/scripts/stata_slot.sh <scratch>/s09 $WT/scripts/extract_corpus_guard_truth.do` (33-09), `git add -f` it, rerun the S09 block (it passes), and put each Q3309-1 message and the fixture's `Fixture:` line in the commit body (a worse verdict this item's change does not explain is a regression: fix the code first, CLAUDE.md rule 2). Before committing, in `$WT`: `git pull --ff-only . main` (CLAUDE.md rule 4; at the batch base it prints `Already up to date.` -- if it refuses, stop and report to the orchestrator, never a merge commit on a section branch) and `node .gitnexus/run.cjs detect-changes --scope all --repo .` (a `partial` or `truncated` result is run again; HIGH or CRITICAL risk named in the hand-back). Grep the message for `claude|anthropic`, commit, grep again.
  ]]></action>
  <verify><![CDATA[Each driver log ends with its pass line; `grep -c "FX-07 PASS" <scratch>/run_test_parser.log` prints 1; the pytest run's last line reads `<n> passed in ...` with no `failed`, `error` or `skipped`; `awk -F'\t' '$1 == "plat:PT-4"' scripts/corpus/ledger.tsv | wc -l` prints 0, test/test_corpus_ledger.py passes, `python3 test/known_differences.py plat:PT-4` prints no `<file>:<line>` row and the hygiene command it prints passes, and the S09 guard block ends with its pass line; `git log -1 --format=%s | grep -c "(WP-36 plat:PT-4)"` prints 1; `grep -c "plat:PT-4 Tracked:\*\* Closed in WP-36.*commit pending" GAPS4.md` prints 1.]]></verify>
  <done>plat:PT-4 was closed: named function graphs of any length were registered and built and kept their points through clear all, every certification site used the accessors, the help no longer advised raising c(macrolen), the corpus ledger kept no plain plat:PT-4 row, and the commit landed on wp36-s03.</done>
</task>

## Section completion criteria

- Points live only in `fp-<hex>.txt` files of the session's `points-<pid>` folder, through the five accessors and `_dash_fpts_open`; no `c(macrolen)` refusal or advice remains; ended sessions' folders are swept, the running one's never.
- Q3603-1..3 and TestClearAll pass; FX-07..09, FN-02..05 and the other flipped sites pass; BUGS/GAPS4/CHANGELOG/GAPS4_OPEN and the coverage-audit row updated in the one commit.
- No plain `plat:PT-4` row is left in scripts/corpus/ledger.tsv or in any `*_KNOWN` table (`python3 test/known_differences.py plat:PT-4` prints none); test/fixtures/corpus_ledger.json is regenerated from the ledger by `scripts/corpus/ledger.py`; test/test_corpus_ledger.py, the hygiene command and the S09 guard block pass; corpus_guard_truth.json is regenerated by its extract script if Q3309-1 reported any change for a guard example.

## Notes

- **Traps.** (1) No case changes `set maxvar` (it would need `clear` and changes the session); the four-layer probe already passes the default `c(macrolen)`. (2) A legacy `$dash_fpts_<name>` global from an older session is ignored by the build (it reads the file) and dropped by registration and `dash clear`; say so in the commit body. (3) `_dash_tmp_clear` is compiled with the standard library alone (`stdlib_entry`): `_dash_points_sweep` uses only `os`, `re`, `shutil`, `stat` and `time`, and TestTheSweep::test_stdlib_entry_still_compiles pins it. (4) A cscript that sets `$dash__fpdir` for Q3603-1 puts the session's value back before the block ends, or later blocks write into the scratch folder. (5) `fopen(p, "rw")` on a missing file is an error: `_dash_fpts_put` checks `fileexists` first.
- **GitNexus and rule 4.** `impact` on every function this section edits before its first edit (36-03-01); `git pull --ff-only . main` (in `$WT`, BRIEF "Pull form") and `detect-changes --scope all` before the commit (36-03-03); HIGH, CRITICAL or UNKNOWN risk goes in the hand-back (REVIEW R2-8).
- **The corpus ledger and the known-differences tables (BRIEF, from WP-34 on).** 36-03-03 deletes plat:PT-4's plain rows of scripts/corpus/ledger.tsv and regenerates test/fixtures/corpus_ledger.json with `scripts/corpus/ledger.py` (D-33-05.i), deletes every row `python3 test/known_differences.py plat:PT-4` prints and runs the hygiene command it prints (D-33-10.h; no ruling keeps a plat:PT-4 difference on purpose, so no deliberate-dict entry), and regenerates corpus_guard_truth.json with its extract script if Q3309-1 reports any change for a guard example (33-09).
- **Help paragraphs owned (R3):** dash.sthlp :3713-3716 (function n() clause), :884 (the points' home), :1509-1511 (`dash clear`'s list).
- **Merge rules touched:** R1 (S03), R6 (five Mata functions in the header index and program_coverage_map.py; the four dash.ado calls on one new `_needed` line after the `_dash_fn_spec_tail` line, `_dash_fpts_get` only if dash.ado reads it; one program version 19, mapped; function_test_map.py for the two Python helpers), R9 (FX-07 flipped, others moved to the accessors), R14 (no edition text: the `set maxvar` advice is removed).
- **For 37-03:** 37-03 runs `twoway__contour_gen` at export (M9), not at registration, and carries its polygons in the spec through an external Mata table; it does not copy this storage.
- **Commit-body line forms:** `Regression: test/test_function_points_file.py::TestOffTheMacro::test_no_macrolen_refusal -- failed at <base> with <text>`; `Flipped: test/test_parser.cscript FX-07 -- r(134) past c(macrolen) was wrong because twoway draws any n() and the one-line form already kept the points off the macro`; `Fixture: test/fixtures/corpus_ledger.json (scripts/corpus/ledger.py)` and `Fixture: test/fixtures/corpus_guard_truth.json (scripts/extract_corpus_guard_truth.do)` only when 36-03-03's ledger step changed them; `BUGS.md: "<title>" (closed)`; `GAPS4: plat:PT-4 Tracked`; `TWOWAY_COVERAGE_AUDIT.md: function row corrected`.
