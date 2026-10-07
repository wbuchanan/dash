*! release_gate_venv.do -- the venv-linked sessions of the release gate (WP-29 P0.19)
*!
*! Usage (through scripts/run_release_gate.sh, two fresh sessions, each run
*! from <work dir> so that the second links Stata by a RELATIVE path):
*!
*!     do release_gate_venv.do <work dir> <ado dir> <mode> <phase>
*!
*! <mode> plus: <ado dir> is the scratch PLUS the gate net installed dash
*! into; dev: <ado dir> is a source tree, put first on the ado-path.
*!
*! Phase venvmake: makes gatevenv from the linked interpreter, with a .pth
*! that lets it see that interpreter's packages (nothing is downloaded; the
*! runner sets PIP_NO_INDEX=1), then runs dash_setup, venv("gatevenv"),
*! which installs into it, verifies it and returns its link line.
*!
*! Phase venvuse, a fresh session: links Stata to gatevenv/bin/python by a
*! relative path before anything else runs Python (the link is for this
*! session only), runs dash_setup, venv("gatevenv") again, which must find
*! Stata linked to it, then builds a saved page and serves the app, asking
*! /health while dash serve blocks.
*!
*! Every result is one line starting "GATE ", which is all
*! release_verdict.venv_verdict reads.

version 18
args work adodir mode phase
set linesize 255
global dash_nobrowser 1

if "`phase'" == "venvuse" {
    quietly cd "`work'"
    capture noisily python set exec "gatevenv/bin/python"
    local lrc = _rc
    display "GATE venv-link rc=`lrc'"
    capture noisily python: import sys, sfi; sfi.Macro.setLocal("gv_ver", "%d.%d.%d" % tuple(sys.version_info[:3]))
    display "GATE venv-python rc=`=_rc' ver=`gv_ver'"
}
else {
    quietly cd "`work'"
}

if "`mode'" == "plus" {
    sysdir set PLUS "`adodir'"
    mata: st_global("S_ADO", "BASE;SITE;PLUS")
}
else {
    adopath ++ "`adodir'"
}

if "`phase'" == "venvmake" {
    local mkrc 1
    capture noisily python: import os, subprocess, sys, sysconfig, sfi; _g_r = subprocess.run([sys.executable, "-m", "venv", "gatevenv"], capture_output=True); _g_l = subprocess.run([os.path.join("gatevenv", "bin", "python"), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"], capture_output=True, text=True).stdout.strip() if _g_r.returncode == 0 else ""; (open(os.path.join(_g_l, "dash_base.pth"), "w").write(sysconfig.get_paths()["purelib"] + chr(10)) if _g_l else None); sfi.Macro.setLocal("mkrc", str(_g_r.returncode) if _g_l else "1")
    display "GATE venv-made rc=`mkrc'"
    capture noisily dash_setup, venv("gatevenv")
    local rc = _rc
    mata: st_local("ready", strofreal(st_global("r(venv_python)") != ""))
    display "GATE venv-setup rc=`rc' ready=`ready' linked=`r(venv_linked)'"
    display "GATE venv-done"
    exit
}

// Phase venvuse: Stata is linked to gatevenv above.
capture noisily dash_setup, venv("gatevenv")
local rc = _rc
display "GATE venv-setup2 rc=`rc' linked=`r(venv_linked)'"

sysuse auto, clear
capture erase "gatevenv.html"
capture noisily dash scatter mpg weight, saving("gatevenv.html") replace nobrowser
local rc = _rc
capture confirm file "gatevenv.html"
local html = (_rc == 0)
display "GATE venv-saved rc=`rc' html=`html'"

// The served app: a thread asks /health on a free port until it answers,
// while dash serve blocks; timeout(1) ends the run after a minute.
dash clear
dash scatter mpg weight, name(g1)
python:
import socket, threading, time, urllib.request
from sfi import Macro
_gv_s = socket.socket()
_gv_s.bind(("127.0.0.1", 0))
_gv_port = _gv_s.getsockname()[1]
_gv_s.close()
Macro.setGlobal("gv_port", str(_gv_port))
_gv_seen = {"status": None, "body": ""}
def _gv_poll():
    deadline = time.time() + 150
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(
                    "http://127.0.0.1:%d/health" % _gv_port, timeout=2) as r:
                _gv_seen["status"] = r.status
                _gv_seen["body"] = r.read().decode("utf-8", "replace")
                return
        except Exception:
            time.sleep(0.25)
_gv_thread = threading.Thread(target=_gv_poll, daemon=True)
_gv_thread.start()
end
capture noisily dash serve, port(${gv_port}) timeout(1) nobrowser
local rc = _rc
python:
_gv_thread.join(5)
Macro.setGlobal("gv_health", "1" if _gv_seen["status"] == 200 and '"status": "ok"' in _gv_seen["body"] else "0")
end
display "GATE venv-served rc=`rc' health=${gv_health}"
macro drop gv_*
display "GATE venv-done"
