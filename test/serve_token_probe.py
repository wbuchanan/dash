"""serve_token_probe.py -- the served dashboard's key in tests (WP-29 P0.12a).

The suite's one shared test key (``TEST_TOKEN``), the request arguments that
carry it, a fake child's stdin that records the key line the launcher hands
over (``FakeStdin``), the readers of a link file and of the announcement
that names it, and ``main``: TOK-02's out-of-process probe, which
``test_serve_launch.cscript`` runs against a real ``dash serve``.  The probe
is handed the link file's PATH, never the key, and writes ``key=value``
lines that never hold the key.

It imports nothing from pytest, so a script, Stata's Python and every test
file can import it.
"""
import os
import re
import stat
import sys

#: The shared key: 48 characters of the form the app accepts.
TEST_TOKEN = "dashTestKey_0123456789abcdefghijklmnopqrstuvwxyz"

#: A link the app writes or prints: host, port, path and a 43-character key.
LINK_RE = re.compile(
    r"http://(127\.0\.0\.1|\[::1\]):(\d+)(/[^?\"'<>\s]*)\?token="
    r"([A-Za-z0-9_-]{43})")

#: A literal copy of ``dash_render._DASH_LINK_SAID`` (TOK-02's child cannot
#: import dash_render without the repository on its path);
#: ``test_the_probe_knows_the_announcement`` keeps the two equal.
LINK_SAID = ("dash: the dashboard opens only through its link, which "
             "holds a key made for this run; the link is in this file, "
             "which only you can read:")


def token_args(token=TEST_TOKEN):
    """The request arguments Tornado gives a request carrying *token*."""
    return {"token": [token.encode("ascii")]}


class FakeStdin:
    """A fake child's stdin: every write is recorded as given (bytes on the
    launcher's binary pipe).  No ``buffer``, so ``_dash_child_stdin``
    returns it as it is.  *broken* makes every write raise BrokenPipeError;
    *break_after* makes every write after that many raise it."""

    def __init__(self, broken=False, break_after=None):
        self.writes = []
        self.closed = False
        self.broken = broken
        self.break_after = break_after

    def write(self, b):
        if self.broken or (self.break_after is not None
                           and len(self.writes) >= self.break_after):
            raise BrokenPipeError(32, "Broken pipe")
        self.writes.append(b)
        return len(b)

    def key_line(self):
        """The last write, decoded, without its one trailing newline, when
        it is bytes ending in exactly one newline; else None."""
        if not self.writes:
            return None
        last = self.writes[-1]
        if not isinstance(last, (bytes, bytearray)) or \
                not last.endswith(b"\n") or last.endswith(b"\n\n"):
            return None
        try:
            return bytes(last[:-1]).decode("ascii")
        except UnicodeDecodeError:
            return None

    def flush(self):
        pass

    def close(self):
        self.closed = True


def link_path_in(text):
    """The stripped line that follows the first line equal to
    ``LINK_SAID``, or None."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == LINK_SAID and i + 1 < len(lines):
            return lines[i + 1].strip()
    return None


def read_link(path):
    """``(mode, folder_mode, host, port, app_path, key)`` of a link file;
    the modes as the last three octal digits."""
    mode = oct(stat.S_IMODE(os.stat(path).st_mode))[-3:]
    dmode = oct(stat.S_IMODE(os.stat(os.path.dirname(path)).st_mode))[-3:]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = LINK_RE.search(text)
    if not m:
        return (mode, dmode, None, None, None, None)
    return (mode, dmode, m.group(1), int(m.group(2)), m.group(3), m.group(4))


def drop_holder():
    """Forget the ``bokeh serve`` process key (``_dash_serve_key``)."""
    sys.modules.pop("_dash_serve_key", None)


def _status(url):
    import urllib.error
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except OSError as e:
        return type(e).__name__


def main(argv):
    """TOK-02's probe: ``serve_token_probe.py <port> <link file> <result>``.
    Reads the key from the link file, checks the link names this port on
    127.0.0.1, and records what the server gives without, with a near miss
    of and with the key.  Never writes the key."""
    port, link, res = int(argv[1]), argv[2], argv[3]
    out = []
    with open(link, encoding="utf-8") as fh:
        text = fh.read()
    m = LINK_RE.search(text)
    key = m.group(4) if m else None
    out.append("link_port=%s" % ("ok" if m and m.group(1) == "127.0.0.1"
                                 and int(m.group(2)) == port else "bad"))
    base = "http://127.0.0.1:%d" % port
    out.append("health=%s" % _status(base + "/health"))
    out.append("root_without_key=%s" % _status(base + "/"))
    if key:
        near = key[:-1] + ("A" if key[-1] != "A" else "B")
        out.append("near_miss=%s" % _status(base + "/?token=" + near))
        out.append("page_with_key=%s" % _status(base + "/?token=" + key))
    import warnings
    from bokeh.client import pull_session
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            with pull_session(url=base + "/") as s:
                s.document.roots
            out.append("pull_without_key=served")
        except Exception:
            out.append("pull_without_key=refused")
        if key:
            try:
                with pull_session(url=base + "/",
                                  arguments={"token": key}) as s:
                    n = 0
                    for m2 in s.document.select({}):
                        data = getattr(m2, "data", None)
                        if isinstance(data, dict) and "mpg" in data:
                            n = max(n, len(data["mpg"]))
                out.append("pull_with_key_rows=%d" % n)
            except Exception as e:
                out.append("pull_with_key_error=%s" % type(e).__name__)
    with open(res, "a", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
