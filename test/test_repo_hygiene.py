"""Repository hygiene (WP-31 I6, S60 D-60g/D-60h): logs are ignored by the
tracked .gitignore, a CI workflow runs make test-dev and make lint, make
lint exists and is clean, and the Pages workflow publishes the package and
the gallery from main once CI has passed (17nov2026)."""
import os
import re
import shutil
import subprocess
import sys

import pytest

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _read(*parts):
    with open(os.path.join(_REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


def test_gitignore_excludes_logs():
    lines = [l.strip() for l in _read(".gitignore").splitlines()]
    assert "*.log" in lines


def test_the_workflow_runs_test_dev_and_lint():
    wf = _read(".github", "workflows", "test.yml")
    on = wf.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert re.search(r"^  push:\n    branches: \[s3-bugs, main\]$", on, re.M)
    assert re.search(r"^  pull_request:$", on, re.M)
    assert re.search(r"^  workflow_dispatch:$", on, re.M)
    assert "runs-on: ubuntu-latest" in wf
    assert 'python-version: "3.11"' in wf
    assert re.search(r"run: make test-dev PYTHON=python\b", wf)
    assert re.search(r"run: make lint PYTHON=python\b", wf)
    assert "macOS" in wf and "stata-mp" not in wf
    assert "secrets." not in wf


def test_the_workflow_fits_the_runner():
    """The first run (14nov2026) started pyproject's eight workers on a
    2-CPU, 8 GB runner: it ran out of memory 17 minutes in, at 21%, on
    pace for more than its hour.  Two workers a job, the suite in four
    jobs (DASH_SHARD), each job inside its time limit."""
    wf = _read(".github", "workflows", "test.yml")
    assert re.search(r'run: make test-dev PYTHON=python DEV_STRICT=0 '
                     r'DEV_BASELINE=py311 PYTEST_ARGS="-n 2"$', wf, re.M)
    assert re.search(r"^        shard: \[1, 2, 3, 4\]$", wf, re.M)
    assert re.search(r"^      DASH_SHARD: \$\{\{ matrix\.shard \}\}/4$", wf,
                     re.M)
    assert "fail-fast: false" in wf
    assert re.search(r"^    timeout-minutes: 40$", wf, re.M)
    assert re.search(r"^  cancel-in-progress: true$", wf, re.M)
    # Node.js 20 actions are retired (GitHub's warning on the first run).
    assert "actions/checkout@v5" in wf and "actions/setup-python@v6" in wf
    assert "@v4" not in wf and "setup-python@v5" not in wf


def _pages_assembly_script(wf):
    """The shell lines of pages.yml's "Assemble the site" step."""
    m = re.search(r"^      - name: Assemble the site\n        run: \|\n"
                  r"((?:          .*(?:\n|$))+)", wf, re.M)
    assert m, "pages.yml has no 'Assemble the site' step"
    return "".join(l[10:] + "\n" for l in m.group(1).splitlines())


def _pkg_files():
    return [l.split()[1] for l in _read("dash.pkg").splitlines()
            if l.startswith("f ")]


def test_the_pages_workflow_publishes_main_after_ci():
    """GitHub Pages is the net install host (test_readme.INSTALL_URL) and
    the gallery's: published from main, and only once the test workflow
    has passed on the very commit published."""
    wf = _read(".github", "workflows", "pages.yml")
    on = wf.split("\non:\n", 1)[1].split("\n\n", 1)[0]
    assert on.splitlines() == ["  workflow_run:", "    workflows: [test]",
                               "    types: [completed]",
                               "    branches: [main]", "  workflow_dispatch:"]
    assert re.search(r"^name: test$", _read(".github", "workflows",
                                            "test.yml"), re.M)
    assert ("if: github.event_name == 'workflow_dispatch' || "
            "github.event.workflow_run.conclusion == 'success'") in wf
    assert ("ref: ${{ github.event.workflow_run.head_sha || github.sha }}"
            in wf)
    for perm in ("contents: read", "pages: write", "id-token: write"):
        assert re.search(rf"^  {perm}$", wf, re.M), perm
    assert re.search(r"^          path: _site$", wf, re.M)
    for action in ("checkout@v5", "configure-pages@v6",
                   "upload-pages-artifact@v5", "deploy-pages@v5"):
        assert f"uses: actions/{action}" in wf, action
    assert "secrets." not in wf


@pytest.mark.skipif(shutil.which("bash") is None, reason="needs bash")
def test_the_pages_site_holds_the_package_and_the_gallery(tmp_path):
    """The step run as GitHub runs it (bash -e): the site's root holds
    stata.toc, dash.pkg and every file dash.pkg lists, as files, the
    landing page built from README.md, gallery/ is docs/gallery, and
    guide/ holds the guide built from docs/guide with each example's page
    and do-file (not BUILD.md); a listed file missing fails the step, so a
    broken package is never published.  The step's python3 is this test's
    interpreter."""
    script = _pages_assembly_script(_read(".github", "workflows",
                                          "pages.yml"))
    work = tmp_path / "repo"
    (work / "docs" / "gallery" / "svg").mkdir(parents=True)
    (work / "docs" / "gallery" / "index.html").write_text("<p>g</p>")
    (work / "docs" / "gallery" / "svg" / "a.svg").write_text("<svg/>")
    (work / "docs" / "guide" / "examples").mkdir(parents=True)
    (work / "docs" / "guide" / "guide.md").write_text(
        "# Guide\n\nLead.\n\n## Part\n\n@example demo 300\n")
    (work / "docs" / "guide" / "examples" / "demo.do").write_text("* Demo: x\n")
    (work / "docs" / "guide" / "examples" / "demo.html").write_text("<p>d</p>")
    (work / "docs" / "guide" / "examples" / "BUILD.md").write_text("# rows\n")
    (work / "scripts").mkdir()
    os.symlink(os.path.join(_REPO, "scripts", "pages_index.py"),
               work / "scripts" / "pages_index.py")
    os.symlink(os.path.join(_REPO, "README.md"), work / "README.md")
    shipped = ["stata.toc", "dash.pkg", *_pkg_files()]
    for name in shipped:
        os.symlink(os.path.join(_REPO, name), work / name)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    os.symlink(sys.executable, bin_dir / "python3")
    env = dict(os.environ, PATH=str(bin_dir) + os.pathsep + os.environ["PATH"])

    def assemble():
        return subprocess.run(["bash", "-e", "-c", script], cwd=work, env=env,
                              capture_output=True, text=True)

    p = assemble()
    assert p.returncode == 0, p.stderr
    site = work / "_site"
    assert sorted(os.listdir(site)) == sorted(shipped + ["gallery", "guide", "index.html"])
    assert sorted(os.listdir(site / "guide")) == ["examples", "index.html"]
    assert sorted(os.listdir(site / "guide" / "examples")) == ["demo.do", "demo.html"]
    assert 'src="examples/demo.html"' in (site / "guide" / "index.html").read_text()
    for name in shipped:
        assert not (site / name).is_symlink(), name
        assert (site / name).read_bytes() == (work / name).read_bytes()
    assert (site / "gallery" / "index.html").read_text() == "<p>g</p>"
    assert (site / "gallery" / "svg" / "a.svg").read_text() == "<svg/>"
    assert '<a class="cta" href="gallery/">' in (site / "index.html").read_text()

    shutil.rmtree(site)
    os.remove(work / shipped[-1])
    assert assemble().returncode != 0


def _ruff():
    if os.environ.get("RUFF"):
        return os.environ["RUFF"].split()
    p = subprocess.run([sys.executable, "-m", "ruff", "--version"],
                       capture_output=True)
    if p.returncode == 0:
        return [sys.executable, "-m", "ruff"]
    exe = shutil.which("ruff")
    return [exe] if exe else None


def test_make_lint_target_exists():
    mk = _read("Makefile")
    m = re.search(r"^lint:\n((?:\t.*\n)+)", mk, re.M)
    assert m, "the Makefile has no lint: target"
    assert "check $(LINT_PATHS) --config ruff.toml" in m.group(1)
    assert "exit 2" in m.group(1)
    assert re.search(r"^LINT_PATHS = dash_render\.py dash_setup_lib\.py "
                     r"test scripts$", mk, re.M)
    assert re.search(r"^\.PHONY:.*\blint\b", mk, re.M)
    toml = _read("ruff.toml")
    assert re.search(r'^select = \["E4", "E7", "E9", "F"\]$', toml, re.M)


def test_ruff_findings_are_zero_or_skip():
    cmd = _ruff()
    if cmd is None:
        pytest.skip("ruff is not installed (make lint says how to install it)")
    p = subprocess.run(cmd + ["check", "dash_render.py", "dash_setup_lib.py",
                              "test", "scripts", "--config", "ruff.toml"],
                       cwd=_REPO, capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stdout[-3000:] + p.stderr[-1000:]
