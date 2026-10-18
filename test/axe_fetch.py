"""axe_fetch.py -- axe-core for the accessibility checker, fetched by the
test into a scratch directory, never into a page dash writes (WP-31 K6,
D-54d).

``axe_source()`` downloads axe-core 4.12.1's ``axe.min.js`` from cdnjs once
per process into ``<tmp>/dash_axe_4.12.1/axe.min.js``, checks its SHA-256
against ``AXE_SHA256`` and returns its text, which the tests hand to
Chrome; Python never imports or runs it.  Without the network the reason is
returned instead (``AxeUnavailable``), and the tests skip with it.
"""
import hashlib
import os
import tempfile
import urllib.request

AXE_VERSION = "4.12.1"
AXE_URL = ("https://cdnjs.cloudflare.com/ajax/libs/axe-core/%s/axe.min.js"
           % AXE_VERSION)

#: Measured on the first fetch (18oct2026, 572,599 bytes) and agreeing with
#: cdnjs's published SRI hash for axe-core/4.12.1/axe.min.js
#: (api.cdnjs.com/libraries/axe-core/4.12.1?fields=sri), which is
#: ``AXE_SRI`` below; both are checked (REVIEW-4 R4-37).
AXE_SHA256 = "66a8aaa95a8b044a7fd74a5435873bf04ff65a1ca75567c921b7509742085a14"
AXE_SRI = ("sha512-7Y+2K9ZP/j7Cahfb4lm6+HC7pkGsAf9i2sI2FzHKQwFBzoUXC0is8UXc"
           "m5o05wgsSCSnbwvkn/G0aoXbJDKRwQ==")


class AxeUnavailable(RuntimeError):
    """axe-core could not be fetched or did not match its pin."""


def _sri(data):
    import base64
    return "sha512-" + base64.b64encode(
        hashlib.sha512(data).digest()).decode("ascii")


def check(data):
    """Raise AxeUnavailable unless *data* is the pinned file."""
    got = hashlib.sha256(data).hexdigest()
    if got != AXE_SHA256:
        raise AxeUnavailable("axe.min.js sha256 %s is not the pinned %s"
                             % (got, AXE_SHA256))
    if _sri(data) != AXE_SRI:
        raise AxeUnavailable("axe.min.js does not match cdnjs's SRI hash")


def axe_path():
    return os.path.join(tempfile.gettempdir(), "dash_axe_" + AXE_VERSION,
                        "axe.min.js")


def axe_source(timeout=30):
    """axe-core's text, fetched once and checked, or AxeUnavailable."""
    path = axe_path()
    if os.path.isfile(path):
        with open(path, "rb") as fh:
            data = fh.read()
        try:
            check(data)
            return data.decode("utf-8")
        except AxeUnavailable:
            os.remove(path)
    try:
        with urllib.request.urlopen(AXE_URL, timeout=timeout) as resp:
            data = resp.read()
    except Exception as exc:  # offline, refused, timed out
        raise AxeUnavailable("axe-core not fetched: %s" % exc) from exc
    check(data)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".part"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)
    return data.decode("utf-8")
