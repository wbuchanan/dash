"""test_server_rate_limit.py — the rate limiter was bypassable by a header.

``_client_ip_from_request`` trusted ``X-Forwarded-For`` unconditionally, and
that value is the sole bucket key for both limiters — the /health limiter and
the session limiter that guards the expensive path.

Measured against a real running server, 700 requests each:

    no header                599 x 200, then 101 x 429   (first 429 at #600)
    varying spoofed header   700 x 200, zero 429

So one line of curl defeats the control entirely. A constant spoofed value
*did* get limited, which proves the header was the bucket key rather than
merely ignored.

Two further consequences of trusting it:

* the value was never validated, so an arbitrary attacker-chosen string such
  as ``evil`` became a bucket key;
* ``_RateLimiter`` caps itself at 10,000 tracked IPs and evicts with
  ``next(iter(self._store))`` — insertion order, not least-recently-used — so
  spraying 10,000 header values also evicts the attacker's own accumulated
  record, turning the cap itself into an eviction primitive.

The header handling is **not** removed. ``BUGS.md`` records that it was added
deliberately: behind a reverse proxy, ``remote_ip`` collapses every end user
into one bucket. It is gated on an explicit opt-in instead, off by default,
because a server that is not behind a proxy you control must not believe the
header at all.
"""
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, ".."))
sys.path.insert(0, _HERE)

from dash_render import ServerAppBuilder

from conftest import make_spec, make_data_json


class _Req:
    def __init__(self, remote_ip="10.0.0.1", **headers):
        self.remote_ip = remote_ip
        self.headers = headers


@pytest.fixture(scope="module")
def app_module():
    """The generated app, imported as a module."""
    d = tempfile.mkdtemp()
    df = pd.DataFrame({"mpg": np.linspace(12.0, 41.0, 8),
                       "weight": np.linspace(1760.0, 4840.0, 8)})
    spec = make_spec([{"type": "scatter", "yvar": "mpg", "xvar": "weight",
                       "options": {}}])
    sp = os.path.join(d, "s.json")
    dp = os.path.join(d, "d.json")
    op = os.path.join(d, "app.py")
    with open(sp, "w") as f:
        json.dump(spec, f)
    with open(dp, "w") as f:
        json.dump(make_data_json(df), f)
    ServerAppBuilder(sp, dp).build(op)
    with open(op, encoding="utf-8") as fh:
        src = fh.read()
    ns: dict = {"__name__": "dash_app_under_test"}
    exec(compile(src.split("if __name__ !=")[0], op, "exec"), ns)
    return ns


class TestTheHeaderIsNotTrustedByDefault:

    def test_the_flag_exists_and_is_off(self, app_module):
        assert "_TRUST_FORWARDED_FOR" in app_module, (
            "there is no way to say whether the proxy header may be trusted"
        )
        assert app_module["_TRUST_FORWARDED_FOR"] is False, (
            "a server that is not behind a proxy you control must not "
            "believe X-Forwarded-For"
        )

    def test_the_header_is_ignored(self, app_module):
        ip = app_module["_client_ip_from_request"](
            _Req("10.0.0.1", **{"X-Forwarded-For": "203.0.113.55"}))
        assert ip.endswith("10.0.0.1"), (
            f"the spoofable header decided the bucket key: {ip!r}"
        )

    def test_remote_ip_is_still_the_fallback(self, app_module):
        assert app_module["_client_ip_from_request"](
            _Req("10.0.0.9")).endswith("10.0.0.9")

    def test_a_missing_request_does_not_raise(self, app_module):
        assert app_module["_client_ip_from_request"](object()) == "0.0.0.0"


class TestSpoofingDoesNotCreateNewBuckets:
    """The defect in one assertion, with no socket."""

    def test_many_spoofed_values_share_one_bucket(self, app_module):
        lim = app_module["_RateLimiter"](max_rpm=3)
        allowed = 0
        for i in range(20):
            ip = app_module["_client_ip_from_request"](
                _Req("10.0.0.1", **{"X-Forwarded-For": "203.0.113.%d" % i}))
            if lim.is_allowed(ip):
                allowed += 1
        assert allowed == 3, (
            f"{allowed} of 20 requests were allowed through a limit of 3; "
            f"each spoofed header value got its own bucket"
        )

    def test_genuinely_different_clients_still_get_their_own_bucket(
            self, app_module):
        lim = app_module["_RateLimiter"](max_rpm=3)
        allowed = 0
        for i in range(6):
            ip = app_module["_client_ip_from_request"](_Req("10.0.0.%d" % i))
            if lim.is_allowed(ip):
                allowed += 1
        assert allowed == 6, allowed


class TestTrustingItIsStillPossible:
    """BUGS.md records why the header handling exists; it is kept."""

    def test_the_proxied_client_is_used_when_trusted(self, app_module):
        app_module["_TRUST_FORWARDED_FOR"] = True
        try:
            ip = app_module["_client_ip_from_request"](
                _Req("10.0.0.1", **{"X-Forwarded-For": "203.0.113.55"}))
            assert "203.0.113.55" in ip
        finally:
            app_module["_TRUST_FORWARDED_FOR"] = False

    def test_a_value_that_is_not_an_ip_is_refused(self, app_module):
        """Otherwise any attacker-chosen string becomes a bucket key."""
        app_module["_TRUST_FORWARDED_FOR"] = True
        try:
            ip = app_module["_client_ip_from_request"](
                _Req("10.0.0.1", **{"X-Forwarded-For": "evil, 10.0.0.1"}))
            assert "evil" not in ip, ip
        finally:
            app_module["_TRUST_FORWARDED_FOR"] = False

    def test_a_trusted_key_cannot_collide_with_a_real_remote_ip(
            self, app_module):
        """A spoofed 10.0.0.1 must not land in the real 10.0.0.1's bucket."""
        direct = app_module["_client_ip_from_request"](_Req("10.0.0.1"))
        app_module["_TRUST_FORWARDED_FOR"] = True
        try:
            proxied = app_module["_client_ip_from_request"](
                _Req("172.16.0.1", **{"X-Forwarded-For": "10.0.0.1"}))
        finally:
            app_module["_TRUST_FORWARDED_FOR"] = False
        assert direct != proxied, (
            "a forwarded value and a real peer address share a bucket key"
        )

    def test_the_launcher_can_turn_it_on(self, app_module):
        """A real proxy deployment must not have to edit the file."""
        import inspect
        src = app_module.get("__dash_source__")
        assert src is None or "--trust-forwarded-for" in src


class TestTheCapIsNotAnEvictionPrimitive:
    """Insertion-order eviction lets a sprayer evict a real record."""

    def test_eviction_drops_the_least_recently_seen(self, app_module):
        """A blocked call does not refresh recency, so the limit is left
        generous here: the point is which key is evicted, not the limit."""
        import time

        lim = app_module["_RateLimiter"](max_rpm=100)
        lim._MAX_IPS = 4
        for i in range(4):
            lim.is_allowed("seed%d" % i)
            time.sleep(0.002)
        # seed0 becomes the most recently seen; seed1 the least.
        lim.is_allowed("seed0")
        time.sleep(0.002)
        lim.is_allowed("spray")
        assert "seed0" in lim._store, (
            "the most recently seen client was evicted; eviction is "
            "insertion-order, not least-recently-used, so a spray of fresh "
            "keys can evict an active client's record"
        )
        assert "seed1" not in lim._store, (
            f"the least recently seen key was not the one evicted: "
            f"{sorted(lim._store)}"
        )
