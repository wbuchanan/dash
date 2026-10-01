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

TR-19.5 (ROADMAP.md WP-19, GAPS.md I2): evicting the least-recently-seen key
instead was still an eviction primitive. With the header trusted, behind a
proxy that passes it through, one machine cycling 10,000 forged values got
10,120 sessions in 60 s against a nominal 60, and the flood evicted the real
client's own key, so it got 120 of 120. The limiter now has three bounds --
per key, ONE shared first-contact window for keys it is not tracking, and a
total -- holds at most ``_MAX_IPS`` keys, and never evicts a live key. The
classes from ``TestTheForwardedKeyCycleIsHeldToTheNominalRate`` on drive the
generated app's own limiter through ``_client_ip_from_request`` with a fake
clock.
"""
import argparse
import bisect
import copy
import json
import logging
import os
import subprocess
import sys
import tempfile
import types

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
    # The launcher tests read the whole file and run it as a script.
    ns["__dash_source__"] = src
    ns["__dash_app_path__"] = op
    return ns


def _launch_as_script(src, monkeypatch, *flags):
    """Run the generated app as ``python app.py *flags`` does -- its own
    ``__main__`` block: parse the flags, apply them, build the server,
    start it -- with bokeh's Server replaced by a recorder whose loop
    returns at once, so nothing listens.  Returns the app's namespace as
    the launcher left it."""
    import warnings
    import bokeh.server.server as bss

    class _Loop:
        def add_callback(self, *a):
            pass

        def call_later(self, *a):
            pass

        def start(self):
            pass

        def stop(self):
            pass

    class _Server:
        def __init__(self, apps, **kw):
            self.io_loop = _Loop()

        def start(self):
            pass

        def show(self, *a):
            pass

        def stop(self):
            pass

    monkeypatch.setattr(bss, "Server", _Server)
    monkeypatch.setattr(sys, "argv", ["app.py", *flags])
    ns = {"__name__": "__main__"}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        exec(compile(src, "app.py", "exec"), ns)
    return ns


def _open_sessions(ns, peer, forwarded):
    """Open one session through the app's make_document for each address
    in *forwarded*, every request coming from *peer* with that address in
    X-Forwarded-For; return, per session, whether it was admitted (a
    refused session's document is the one 429 Div)."""
    import warnings
    from bokeh.document import Document
    from bokeh.models import Div
    admitted = []
    for xff in forwarded:
        req = _Req(peer, **{"X-Forwarded-For": xff})

        class _Doc(Document):
            session_context = property(
                lambda self, _r=req: types.SimpleNamespace(request=_r))

        doc = _Doc()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            ns["make_document"](doc)
        refused = [r for r in doc.roots
                   if isinstance(r, Div) and "429" in r.text]
        # Admitted is the dashboard itself: roots, none of them the 429.
        assert doc.roots and (not refused or len(doc.roots) == 1), (
            [type(r).__name__ for r in doc.roots])
        admitted.append(not refused)
    return admitted


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
        """Six real peers, each with a budget of its own.

        Restated for TR-19.5. This built ``_RateLimiter(max_rpm=3)`` and
        expected six new peers to be admitted. First contact is now charged
        to ONE shared new-client window, ``max_rpm`` wide by default -- that
        window is what holds a key-cycling attacker to one client's budget --
        so a limit of 3 admits three new peers a minute. The window is sized
        here to admit six. What this guards is unchanged, and now asserted
        in full: each peer gets its whole budget of 3, whatever the others
        spend.
        """
        lim = app_module["_RateLimiter"](max_rpm=3, new_clients=6)
        per_client = []
        for i in range(6):
            ip = app_module["_client_ip_from_request"](_Req("10.0.0.%d" % i))
            per_client.append(sum(lim.is_allowed(ip) for _ in range(4)))
        assert per_client == [3] * 6, per_client


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

    def test_the_launcher_can_turn_it_on(self, app_module, monkeypatch):
        """A real proxy deployment must not have to edit the file: with
        ``--trust-forwarded-for`` the session limiter keys on the forwarded
        address, and without it on the peer.

        This asserted ``src is None or "--trust-forwarded-for" in src`` --
        src is never None, and the flag's name is in the argparse
        declaration whatever the flag does.  Measured 24sep2026: with the
        launcher's ``if _a.trust_xff:`` branch made a no-op, so the flag
        parsed and changed nothing, it passed, and so did the three tests
        above, which set ``_TRUST_FORWARDED_FOR`` themselves.  Now the app
        runs as the script a user launches (bokeh's Server replaced by a
        recorder, so nothing listens) and six sessions open through
        make_document from ONE peer on behalf of two forwarded clients,
        with a budget of two sessions a client.
        """
        forwarded = ["198.51.100.7"] * 3 + ["198.51.100.8"] * 3
        trusted = _launch_as_script(
            app_module["__dash_source__"], monkeypatch,
            "--trust-forwarded-for", "--sessions-per-client", "2")
        assert trusted["_TRUST_FORWARDED_FOR"] is True
        assert _open_sessions(trusted, PEER, forwarded) == [
            True, True, False, True, True, False], (
            "with the flag, each forwarded client should have a budget of "
            "its own")
        assert sorted(trusted["_SESSION_LIMITER"]._store) == [
            "xff:198.51.100.7", "xff:198.51.100.8"]

        untrusted = _launch_as_script(
            app_module["__dash_source__"], monkeypatch,
            "--sessions-per-client", "2")
        assert untrusted["_TRUST_FORWARDED_FOR"] is False
        assert _open_sessions(untrusted, PEER, forwarded) == [
            True, True, False, False, False, False], (
            "without the flag, every request is the peer's and shares its "
            "one budget")
        assert list(untrusted["_SESSION_LIMITER"]._store) == [PEER]

    def test_the_launcher_flag_keys_health_on_the_forwarded_address(
            self, app_module, monkeypatch):
        """/health's limiter derives its key the same way: with the flag,
        a second forwarded client behind a peer whose first client spent
        its 600 probes is answered; without it, it is refused with the
        first."""
        for flags, second in ((("--trust-forwarded-for",), None),
                              ((), 429)):
            ns = _launch_as_script(app_module["__dash_source__"],
                                   monkeypatch, *flags)
            first = [_health_status(ns, PEER, **{
                "X-Forwarded-For": "198.51.100.7"}) for _ in range(601)]
            assert first.count(None) == 600 and first[-1] == 429, (
                flags, first.count(None), first[-1])
            got = _health_status(ns, PEER, **{
                "X-Forwarded-For": "198.51.100.8"})
            assert got == second, (flags, got)


class TestAForwardedTokenIsOneBoundedKeyPerAddress:
    """With the header trusted, the token became the key after
    ``ipaddress.ip_address`` accepted it -- and it accepts an IPv6 zone
    (``fe80::1%<anything>``) of any length and content: a 60,012-character
    key and a control character were both taken, found in WP-19's review.
    And it keeps the token's own spelling, so ``2001:db8::1`` and
    ``2001:0db8:0::1`` -- one address -- were two clients.  Neither gets past
    the limiter since WP-19, but each multiplies what it must remember: up
    to 6,000 live /health keys of up to 64 KB apiece.  A key is now the
    address's one canonical spelling, at most 45 characters, never a zone.
    """

    def _key(self, app_module, xff):
        app_module["_TRUST_FORWARDED_FOR"] = True
        try:
            return app_module["_client_ip_from_request"](
                _Req("10.0.0.1", **{"X-Forwarded-For": xff}))
        finally:
            app_module["_TRUST_FORWARDED_FOR"] = False

    def test_a_zone_of_any_length_is_not_a_key(self, app_module):
        assert self._key(app_module, "fe80::1%" + "a" * 60000) == "10.0.0.1"
        assert self._key(app_module, "fe80::1%eth0") == "10.0.0.1"

    def test_a_control_character_is_not_a_key(self, app_module):
        assert self._key(app_module, "fe80::1%\x01") == "10.0.0.1"
        assert self._key(app_module, "10.0.0.2\x00") == "10.0.0.1"

    def test_nothing_longer_than_an_address_is_a_key(self, app_module):
        longest = "ffff:ffff:ffff:ffff:ffff:ffff:255.255.255.255"
        assert len(longest) == 45
        assert self._key(app_module, longest).startswith("xff:")
        assert self._key(app_module, " " + longest + "0") == "10.0.0.1"

    def test_one_address_is_one_key_however_it_is_spelled(self, app_module):
        spellings = ["2001:db8::1", "2001:0db8::1", "2001:db8:0::1",
                     "2001:DB8::0:1", "2001:0db8:0000:0000:0000:0000:0000:0001"]
        keys = {self._key(app_module, s) for s in spellings}
        assert keys == {"xff:2001:db8::1"}, keys

    def test_an_ipv4_mapped_address_is_the_ipv4_client(self, app_module):
        assert self._key(app_module, "::ffff:203.0.113.9") == \
            self._key(app_module, "203.0.113.9") == "xff:203.0.113.9"

    def test_ordinary_addresses_are_still_keys(self, app_module):
        assert self._key(app_module, "198.51.100.7") == "xff:198.51.100.7"
        assert self._key(app_module, "a, 2001:db8::7") == "xff:2001:db8::7"


# ---------------------------------------------------------------------------
# Fake-clock harness for the limiter tests below.
# ---------------------------------------------------------------------------

PEER = "203.0.113.9"        # the one machine limiter.py attacks from
REAL_XFF = "198.51.100.7"   # a real client behind the same proxy


class _Clock:
    """A monotonic clock that moves only when a test moves it."""

    def __init__(self, t=1000.0):
        self.t = float(t)

    def monotonic(self):
        return self.t

    def time(self):
        return self.t


def _forged(i):
    """The i-th X-Forwarded-For value limiter.py cycles through."""
    return "10.%d.%d.%d" % (i // 65536, (i // 256) % 256, i % 256)


def _key(ns, peer, xff=None):
    """The bucket key the app derives for a request from ``peer``."""
    headers = {"X-Forwarded-For": xff} if xff else {}
    return ns["_client_ip_from_request"](_Req(peer, **headers))


def _ask(ns, limiter, peer, xff=None):
    """One request, through the app's own key derivation and limiter."""
    return limiter.is_allowed(_key(ns, peer, xff))


@pytest.fixture
def served(app_module, monkeypatch):
    """The app with a fake clock, fresh limiters and the header untrusted.

    The clock, both limiters, the legacy alias and the trust flag are all
    set through monkeypatch, so each is restored after the test however it
    ends -- including a rebinding by ``_dash_apply_limits``. The limiters
    are copies of the ones the app built, so they carry its configuration.
    """
    for name in ("_SESSION_LIMITER", "_HEALTH_LIMITER"):
        assert not app_module[name]._store, (
            f"a test spent the module's own {name}; use this fixture's copy")
    clock = _Clock()
    monkeypatch.setitem(app_module, "_time", types.SimpleNamespace(
        monotonic=clock.monotonic, time=clock.time))
    session = copy.deepcopy(app_module["_SESSION_LIMITER"])
    monkeypatch.setitem(app_module, "_SESSION_LIMITER", session)
    monkeypatch.setitem(app_module, "_LIMITER", session)
    monkeypatch.setitem(app_module, "_HEALTH_LIMITER",
                        copy.deepcopy(app_module["_HEALTH_LIMITER"]))
    monkeypatch.setitem(app_module, "_TRUST_FORWARDED_FOR", False)
    return types.SimpleNamespace(ns=app_module, clock=clock)


class TestTheCapIsNotAnEvictionPrimitive:
    """A cap that evicts a live key lets a sprayer reset a real record."""

    def test_eviction_drops_no_live_key(self, served):
        """Restated for TR-19.5 (ROADMAP.md WP-19, GAPS.md I2).

        This was ``test_eviction_drops_the_least_recently_seen`` and asserted
        that a full table evicted its least-recently-seen key (seed1) rather
        than its first-inserted one (seed0). That LRU eviction was itself the
        defect: with the header trusted, 10,000 forged keys took 10,120
        sessions in 60 s against a nominal 60, and evicted the real client's
        own key, which then got 120 of 120. No live key is evicted now -- not
        the least recently seen, not the most -- and the new key is served
        from the shared first-contact window without being tracked.

        The same scenario as before, on the fake clock instead of sleeps.
        """
        ns, clock = served.ns, served.clock
        lim = ns["_RateLimiter"](max_rpm=100)
        lim._MAX_IPS = 4
        for i in range(4):
            assert lim.is_allowed("seed%d" % i)
            clock.t += 0.002
        # seed0 becomes the most recently seen; seed1 the least.
        assert lim.is_allowed("seed0")
        clock.t += 0.002
        assert lim.is_allowed("spray"), (
            "a full table must still serve a new key from the first-contact "
            "window")
        assert "seed0" in lim._store and "seed1" in lim._store, (
            f"a live key was evicted to make room: {sorted(lim._store)}")
        assert "spray" not in lim._store, (
            "the new key was tracked in a table full of live keys, so "
            "something live had to go")
        assert sorted(lim._store) == ["seed0", "seed1", "seed2", "seed3"]


class TestTheForwardedKeyCycleIsHeldToTheNominalRate:
    """AC-19.4: limiter.py's 10,000-key cycle, against the session limiter
    the app serves with (60 per client, 60 new clients, 600 in all, a
    minute).

    One machine (PEER) cycles forged X-Forwarded-For values. A real client
    behind the same proxy spends its 60 first and asks 60 more times after
    the cycle, and the whole run fits in one 60-second window. Measured
    before the fix, with the header trusted: the cycle got 10,000 sessions,
    and the real client 120 of 120 because the flood evicted its key.
    """

    N_KEYS = 10_000

    def _cycle(self, served, trust):
        ns, clock = served.ns, served.clock
        ns["_TRUST_FORWARDED_FOR"] = trust      # the fixture restores it
        lim = ns["_SESSION_LIMITER"]
        first = sum(_ask(ns, lim, PEER, REAL_XFF) for _ in range(60))
        # 59 s for the whole run, so nothing leaves the window before the
        # real client asks again: no boundary for float rounding to cross.
        step = 59.0 / (self.N_KEYS + 60)
        attack = 0
        for i in range(self.N_KEYS):
            clock.t += step
            attack += _ask(ns, lim, PEER, _forged(i))
        again = 0
        for _ in range(60):
            clock.t += step
            again += _ask(ns, lim, PEER, REAL_XFF)
        assert clock.t - 1000.0 < 60.0
        return first, attack, again

    def test_trusted_the_cycle_gets_at_most_the_nominal_rate(self, served):
        first, attack, again = self._cycle(served, trust=True)
        ns = served.ns
        assert first == 60
        assert attack <= 60, (
            f"10,000 forged keys got {attack} sessions in one window against "
            f"a nominal 60 (10,000 before the fix)")
        # The cycle shares the first-contact window with the real client's
        # first grant, so together they are held to that one window.
        assert attack + 1 <= ns["_NEW_CLIENTS_RPM"], attack
        assert len(ns["_SESSION_LIMITER"]._store) <= 60, (
            "keys refused at first contact are being tracked")

    def test_trusted_the_flood_does_not_reset_the_real_client(self, served):
        first, attack, again = self._cycle(served, trust=True)
        assert (first, again) == (60, 0), (
            f"the real client got {first}, then {again} more in the same "
            f"window; before the fix the flood evicted its key and it got 60 "
            f"more")

    def test_trusted_the_real_client_has_its_budget_back_after_the_window(
            self, served):
        self._cycle(served, trust=True)
        ns, clock = served.ns, served.clock
        clock.t = 1000.0 + 61.0      # a window after every grant above
        lim = ns["_SESSION_LIMITER"]
        after = sum(_ask(ns, lim, PEER, REAL_XFF) for _ in range(61))
        assert after == 60, (
            f"once the window has passed the real client should have its "
            f"full 60 again, and no more; it got {after}")

    def test_untrusted_the_cycle_is_one_key_held_to_60(self, served):
        first, attack, again = self._cycle(served, trust=False)
        assert first + attack + again == 60, (first, attack, again)
        assert list(served.ns["_SESSION_LIMITER"]._store) == [PEER], (
            "with the header untrusted every request is the peer's own key")


class TestReusedKeysAreHeldToTheTotal:
    """Bound 3: keys established at the first-contact rate, then reused.

    Bounds 1 and 2 alone let an attacker add up to 60 keys a minute and
    spend 60 sessions on each of them -- 3,600 a minute after one minute,
    and growing. The total bound holds every window to
    ``_SESSIONS_TOTAL_RPM``.
    """

    def test_reuse_is_held_to_the_total_in_every_window(self, served):
        ns, clock = served.ns, served.clock
        ns["_TRUST_FORWARDED_FOR"] = True
        lim = ns["_SESSION_LIMITER"]
        total = ns["_SESSIONS_TOTAL_RPM"]
        established, grants, attempts, fresh = [], [], 0, 0
        for tick in range(300):                  # five windows, 1 s apart
            clock.t = 1000.0 + tick
            for xff in established:              # reuse every key it has
                attempts += 1
                if _ask(ns, lim, PEER, xff):
                    grants.append(clock.t)
            for _ in range(2):                   # twice the first-contact rate
                xff = _forged(fresh)
                fresh += 1
                attempts += 1
                if _ask(ns, lim, PEER, xff):
                    established.append(xff)
                    grants.append(clock.t)
        # The limiter's window at time g is [g - 60, g], both ends in.
        worst = max(bisect.bisect_right(grants, g)
                    - bisect.bisect_left(grants, g - 60.0) for g in grants)
        assert worst <= total, (
            f"{worst} sessions in one window against a total of {total}")
        # The attacker asked for far more, and bounds 1 and 2 alone would
        # have let it through, so the total is the bound that held.
        assert attempts > 10 * total, attempts
        assert len(established) * ns["_RATE_LIMIT_RPM"] > total
        assert worst == total, worst


class TestTheStoreIsBounded:
    """Memory: at most ``_MAX_IPS`` tracked keys, and stale keys swept."""

    def _flood(self, served, n=20_000, seconds=90.0):
        ns, clock = served.ns, served.clock
        # First contact and the total opened wide, so every key is granted
        # and the table itself is what is tested: 222 new keys a second is
        # 13,333 live keys a window against a cap of 10,000.
        lim = ns["_RateLimiter"](60, new_clients=1_000_000,
                                 total_rpm=1_000_000)
        biggest = 0
        for i in range(n):
            clock.t = 1000.0 + i * (seconds / n)
            lim.is_allowed(_key(ns, _forged(i)))   # n distinct peers
            biggest = max(biggest, len(lim._store))
        return lim, biggest

    def test_twenty_thousand_keys_never_exceed_the_cap(self, served):
        lim, biggest = self._flood(served)
        assert lim._MAX_IPS == 10_000
        assert biggest <= lim._MAX_IPS, biggest
        assert biggest == lim._MAX_IPS, (
            "the table never filled, so the cap was not exercised")

    def test_stale_keys_are_swept_and_live_keys_kept(self, served):
        lim, _ = self._flood(served)
        ns, clock = served.ns, served.clock
        end = clock.t
        live = ["192.0.2.1", "192.0.2.2", "192.0.2.3"]
        # 150 s of traffic from three live clients and none from the flood:
        # well over a window after the flood's last grant, and over two
        # windows, so at least one once-a-window sweep falls after every
        # flood key went stale.
        for k in range(1, 31):
            clock.t = end + 5.0 * k
            for ip in live:
                assert lim.is_allowed(_key(ns, ip))
            assert len(lim._store) <= lim._MAX_IPS
        assert sorted(lim._store) == sorted(live), (
            f"{len(lim._store) - len(live)} flood keys with no grant for over "
            f"a window are still tracked")

    def test_the_sweep_deletes_only_keys_with_no_grant_in_the_window(
            self, served):
        ns, clock = served.ns, served.clock
        lim = ns["_RateLimiter"](60)
        for ip in ("10.0.0.1", "10.0.0.2"):
            assert lim.is_allowed(ip)
        clock.t += 30.0
        assert lim.is_allowed("10.0.0.3")
        clock.t += 31.0          # 61 s after the first two, 31 s after .3
        lim._sweep(clock.t - lim._window)
        assert list(lim._store) == ["10.0.0.3"]

    def test_the_oldest_first_sweep_stops_at_the_first_live_key(self, served):
        """_store is kept in order of each key's latest grant, so the stale
        keys are the ones at the front, and a full table can be relieved
        without reading every key."""
        ns, clock = served.ns, served.clock
        lim = ns["_RateLimiter"](60)
        for ip in ("10.0.0.1", "10.0.0.2", "10.0.0.3"):
            assert lim.is_allowed(ip)
            clock.t += 10.0
        assert lim.is_allowed("10.0.0.1")        # a grant moves it to the end
        assert list(lim._store) == ["10.0.0.2", "10.0.0.3", "10.0.0.1"]
        clock.t = 1000.0 + 10.0 + 60.5           # .2 is stale; .3 and .1 live
        lim._sweep_oldest(clock.t - lim._window)
        assert list(lim._store) == ["10.0.0.3", "10.0.0.1"]


class TestAFullTableEvictsNoLiveKey:
    """TR-19.5: evicting a live key -- the LRU cap's only move when full --
    is what reset the real client's budget under the flood."""

    def test_a_fifth_key_is_not_tracked_and_the_four_live_keys_remain(
            self, served):
        ns, clock = served.ns, served.clock
        lim = ns["_RateLimiter"](60)
        lim._MAX_IPS = 4
        live = [_key(ns, "10.0.0.%d" % i) for i in range(1, 5)]
        for k in live:
            assert sum(lim.is_allowed(k) for _ in range(3)) == 3
            clock.t += 1.0
        before = {k: list(ts) for k, ts in lim._store.items()}
        fifth = _key(ns, "10.0.0.5")
        lim.is_allowed(fifth)
        assert fifth not in lim._store
        assert {k: list(ts) for k, ts in lim._store.items()} == before, (
            "a live key was evicted or its record changed")

    def test_a_flood_of_fresh_keys_leaves_every_live_count_intact(
            self, served):
        ns, clock = served.ns, served.clock
        ns["_TRUST_FORWARDED_FOR"] = True
        lim = ns["_RateLimiter"](60)
        lim._MAX_IPS = 4
        live = ["198.51.100.%d" % i for i in range(1, 5)]
        for xff in live:
            assert sum(_ask(ns, lim, PEER, xff) for _ in range(3)) == 3
        for i in range(10_000):
            clock.t += 0.001
            _ask(ns, lim, PEER, _forged(i))
        assert sorted(lim._store) == sorted(_key(ns, PEER, x) for x in live)
        # The first live client has 57 of its 60 left, not a fresh 60.
        assert sum(_ask(ns, lim, PEER, live[0]) for _ in range(60)) == 57


class TestAFullTableStillServesNewClients:
    """A table full of live keys refuses to TRACK a new key, not to serve
    it: the new key is served from the shared first-contact window."""

    def _full(self, served):
        ns = served.ns
        lim = ns["_RateLimiter"](60, new_clients=6)
        lim._MAX_IPS = 4
        tracked = [_key(ns, "10.0.0.%d" % i) for i in range(1, 5)]
        for k in tracked:
            assert lim.is_allowed(k)             # four of six first contacts
        return lim, tracked

    def test_a_new_key_is_served_until_the_first_contact_window_is_spent(
            self, served):
        ns = served.ns
        lim, tracked = self._full(served)
        newcomer = _key(ns, "10.0.1.1")
        assert lim.is_allowed(newcomer)          # the fifth first contact
        assert newcomer not in lim._store
        assert lim.is_allowed(newcomer)          # untracked, so the sixth
        assert not lim.is_allowed(newcomer)      # the window is spent
        assert not lim.is_allowed(_key(ns, "10.0.1.2"))
        assert sorted(lim._store) == sorted(tracked)
        assert lim.is_allowed(tracked[0]), (
            "a tracked client lost its own budget to the newcomers")

    def test_the_new_key_is_tracked_once_the_window_has_passed(self, served):
        ns, clock = served.ns, served.clock
        lim, tracked = self._full(served)
        newcomer = _key(ns, "10.0.1.1")
        assert lim.is_allowed(newcomer)
        clock.t += 61.0                          # every key above is stale
        assert lim.is_allowed(newcomer)
        assert list(lim._store) == [newcomer]


def _health_status(ns, remote_ip, **headers):
    """What ``_HealthHandler.prepare`` does with a request from
    ``remote_ip`` carrying ``headers``: the status it set, or None when it
    let it through."""
    seen = {}

    class _Handler(ns["_HealthHandler"]):
        def set_status(self, code, reason=None):
            seen["status"] = code

        def set_header(self, name, value):
            pass

        def finish(self, chunk=None):
            seen["finished"] = True

    handler = object.__new__(_Handler)
    handler.request = _Req(remote_ip, **headers)
    handler.prepare()
    return seen.get("status")


class TestHealthAndSessionsHaveSeparateBudgets:
    """Probes must never spend the session budget, nor sessions the
    probes'."""

    def test_spending_the_sessions_does_not_refuse_health(self, served):
        ns = served.ns
        k = _key(ns, "10.0.0.7")
        assert sum(ns["_SESSION_LIMITER"].is_allowed(k)
                   for _ in range(100)) == 60
        assert ns["_HEALTH_LIMITER"].is_allowed(k)
        assert _health_status(ns, "10.0.0.7") is None

    def test_spending_health_does_not_refuse_sessions(self, served):
        ns = served.ns
        statuses = [_health_status(ns, "10.0.0.8") for _ in range(601)]
        assert statuses.count(None) == 600 and statuses[-1] == 429, (
            statuses.count(None), statuses[-1])
        assert ns["_SESSION_LIMITER"].is_allowed(_key(ns, "10.0.0.8"))


class TestRefusalsAreLoggedOncePerWindow:
    """BR-19.2 and CLAUDE.md rule 14: a refusal logs the bound that refused,
    that bound's value and the flag that raises it -- once per window per
    bound, so a flood cannot flood the log."""

    @staticmethod
    def _lines(caplog):
        return [r.getMessage() for r in caplog.records
                if r.name == "dash.serve" and r.levelno == logging.WARNING]

    def test_the_per_client_bound(self, served, caplog):
        caplog.set_level(logging.WARNING, logger="dash.serve")
        ns = served.ns
        lim, k = ns["_SESSION_LIMITER"], _key(ns, "10.0.0.9")
        assert sum(lim.is_allowed(k) for _ in range(60)) == 60
        assert not any(lim.is_allowed(k) for _ in range(10_000))
        lines = self._lines(caplog)
        assert len(lines) == 1, lines
        assert "per-client" in lines[0], lines[0]
        assert " 60 " in lines[0], lines[0]
        assert "--sessions-per-client" in lines[0], lines[0]

    def test_the_new_client_bound(self, served, caplog):
        caplog.set_level(logging.WARNING, logger="dash.serve")
        ns = served.ns
        lim = ns["_SESSION_LIMITER"]
        granted = sum(_ask(ns, lim, _forged(i)) for i in range(10_060))
        assert granted == 60
        lines = self._lines(caplog)
        assert len(lines) == 1, lines
        assert "new-client" in lines[0], lines[0]
        assert " 60 " in lines[0], lines[0]
        assert "--new-clients-per-minute" in lines[0], lines[0]

    def test_the_all_sessions_bound(self, served, caplog):
        caplog.set_level(logging.WARNING, logger="dash.serve")
        ns = served.ns
        lim = ns["_SESSION_LIMITER"]
        peers = [_forged(i) for i in range(60)]
        granted = sum(_ask(ns, lim, p) for _ in range(60) for p in peers)
        assert granted == 600
        lines = self._lines(caplog)
        assert len(lines) == 1, lines
        assert "all clients" in lines[0], lines[0]
        assert " 600 " in lines[0], lines[0]
        assert "--sessions-per-minute" in lines[0], lines[0]

    def test_once_per_window_for_each_bound(self, served, caplog):
        caplog.set_level(logging.WARNING, logger="dash.serve")
        ns, clock = served.ns, served.clock
        lim, k = ns["_SESSION_LIMITER"], _key(ns, "10.0.0.10")
        for window in range(2):
            clock.t = 1000.0 + 61.0 * window
            assert sum(lim.is_allowed(k) for _ in range(5_000)) == 60
        lines = self._lines(caplog)
        assert len(lines) == 2, lines
        assert all("--sessions-per-client" in s for s in lines), lines
        # The second line says how many the first one stood for.
        assert "4939" in lines[1], lines[1]
        # A different bound in the same window gets a line of its own.
        granted = sum(_ask(ns, lim, _forged(i)) for i in range(5_000))
        assert granted == 59
        lines = self._lines(caplog)
        assert len(lines) == 3, lines
        assert "--new-clients-per-minute" in lines[2], lines[2]

    def test_health_refusals_are_logged_without_a_flag(self, served, caplog):
        caplog.set_level(logging.WARNING, logger="dash.serve")
        ns = served.ns
        lim, k = ns["_HEALTH_LIMITER"], _key(ns, "10.0.0.11")
        assert sum(lim.is_allowed(k) for _ in range(600)) == 600
        assert not any(lim.is_allowed(k) for _ in range(10_000))
        lines = self._lines(caplog)
        assert len(lines) == 1, lines
        assert "/health" in lines[0] and "per-client" in lines[0], lines[0]
        assert " 600 " in lines[0], lines[0]
        assert "--" not in lines[0], (
            f"/health has no flag to raise its limit, so none may be named: "
            f"{lines[0]}")


_NEW_FLAGS = [
    ("--sessions-per-client", "sessions_per_client", 60),
    ("--new-clients-per-minute", "new_clients_per_minute", 60),
    ("--sessions-per-minute", "sessions_per_minute", 600),
]


class TestTheLauncherFlags:
    """The three limits reach the command line, checked by argparse, and
    the parsed values reach the limiter make_document consults."""

    def test_the_new_flags_default_to_the_served_limits(self, served):
        ns = served.ns
        a = ns["_dash_arg_parser"]().parse_args([])
        got = tuple(getattr(a, dest) for _, dest, _d in _NEW_FLAGS)
        assert got == tuple(d for _, _dest, d in _NEW_FLAGS)
        assert got == (ns["_RATE_LIMIT_RPM"], ns["_NEW_CLIENTS_RPM"],
                       ns["_SESSIONS_TOTAL_RPM"])

    @pytest.mark.parametrize("flag,dest,_default", _NEW_FLAGS)
    @pytest.mark.parametrize("text,value", [
        ("1", 1), ("250", 250), ("1000000", 1_000_000)])
    def test_each_new_flag_parses(self, served, flag, dest, _default,
                                  text, value):
        a = served.ns["_dash_arg_parser"]().parse_args([flag, text])
        assert getattr(a, dest) == value

    @pytest.mark.parametrize("flag,dest,_default", _NEW_FLAGS)
    @pytest.mark.parametrize("bad", [
        "0", "-1", "abc", "2.5", "1e3", "1000001"])
    def test_each_new_flag_refuses_a_value_outside_1_to_1000000(
            self, served, capsys, flag, dest, _default, bad):
        with pytest.raises(SystemExit) as exc:
            served.ns["_dash_arg_parser"]().parse_args([flag, bad])
        assert exc.value.code == 2
        err = capsys.readouterr().err
        assert flag in err and "1 to 1,000,000" in err, err

    def test_the_value_check_names_the_range(self, served):
        check = served.ns["_dash_limit_value"]
        assert (check("1"), check("60"), check("1000000")) == (
            1, 60, 1_000_000)
        # int() alone would take the last three: '1_000', ' 60' and
        # Arabic-Indic digits.
        for bad in ("0", "-1", "abc", "2.5", "1000001", "", "1_000", " 60",
                    "٦٠"):
            with pytest.raises(argparse.ArgumentTypeError,
                               match="1 to 1,000,000"):
                check(bad)

    def test_the_parsed_values_reach_the_session_limiter(self, served):
        ns = served.ns
        a = ns["_dash_arg_parser"]().parse_args([
            "--sessions-per-client", "2", "--new-clients-per-minute", "3",
            "--sessions-per-minute", "5"])
        old = ns["_SESSION_LIMITER"]
        new = ns["_dash_apply_limits"](a)
        assert ns["_SESSION_LIMITER"] is new and new is not old
        assert ns["_LIMITER"] is new, "the legacy alias was left behind"
        assert new._max == 2

        def ask(ip):
            return new.is_allowed(_key(ns, ip))

        assert [ask("10.0.0.1") for _ in range(3)] == [True, True, False]
        assert ask("10.0.0.2") and ask("10.0.0.3")   # three new clients...
        assert not ask("10.0.0.4")                   # ...and not a fourth
        assert ask("10.0.0.2")                       # five sessions in all...
        assert not ask("10.0.0.3")                   # ...and not a sixth

    def test_apply_limits_checks_the_values_again(self, served):
        """A caller need not have come through the parser."""
        for bad in (0, -1, 1_000_001, 2.5, True):
            values = {"sessions_per_client": 60,
                      "new_clients_per_minute": 60,
                      "sessions_per_minute": 600}
            for dest in values:
                args = types.SimpleNamespace(**dict(values, **{dest: bad}))
                with pytest.raises(argparse.ArgumentTypeError):
                    served.ns["_dash_apply_limits"](args)

    def test_make_document_reads_the_rebuilt_limiter(self, served):
        """make_document looks ``_SESSION_LIMITER`` up as each session
        opens, so rebinding the global is enough."""
        from bokeh.document import Document
        from bokeh.models import Div

        ns = served.ns
        lim = ns["_dash_apply_limits"](ns["_dash_arg_parser"]().parse_args(
            ["--sessions-per-client", "1"]))
        assert lim.is_allowed(_key(ns, "10.4.4.4"))   # its one session

        class _Doc(Document):
            session_context = property(lambda self: types.SimpleNamespace(
                request=_Req("10.4.4.4")))

        doc = _Doc()
        ns["make_document"](doc)
        assert any(isinstance(r, Div) and "429" in r.text
                   for r in doc.roots), doc.roots

    def test_the_old_flags_still_parse(self, served):
        ns = served.ns
        p = ns["_dash_arg_parser"]()
        d = p.parse_args([])
        assert (d.port, d.address, d.origins, d.trust_xff, d.show,
                d.timeout) == (ns["_port"], None, None, False, False, 0)
        a = p.parse_args([
            "--port", "5007", "--address", "0.0.0.0",
            "--allow-websocket-origin", "a.example:1",
            "--allow-websocket-origin", "b.example:2",
            "--trust-forwarded-for", "--show", "--timeout", "5"])
        assert (a.port, a.address, a.origins, a.trust_xff, a.show,
                a.timeout) == (5007, "0.0.0.0",
                               ["a.example:1", "b.example:2"], True, True, 5)

    def test_the_launcher_applies_the_limits_before_it_serves(self, served):
        src = served.ns["__dash_source__"]
        main = src[src.index("if __name__ == '__main__':"):]
        code = "\n".join(l.split("#", 1)[0] for l in main.splitlines())
        # GAPS2 F1 kept the parser object (_p) so it can raise the port
        # error through _p.error(), splitting what used to be one chained
        # call into two statements.
        assert "_p = _dash_arg_parser()" in code
        assert "_a = _p.parse_args()" in code
        assert code.index("_p = _dash_arg_parser()") < code.index(
            "_a = _p.parse_args()")
        assert (code.index("_dash_apply_limits(_a)")
                < code.index("_dash_server_app(")), (
            "the launcher starts serving before it applies the limits")

    def _run(self, served, *args):
        app = served.ns["__dash_app_path__"]
        return subprocess.run([sys.executable, app, *args],
                              capture_output=True, text=True, timeout=180,
                              cwd=os.path.dirname(app))

    def test_the_launcher_help_lists_every_flag(self, served):
        r = self._run(served, "--help")
        assert r.returncode == 0, r.stderr[-2000:]
        # --parent-watch: WP-29 P0.13 F2, the server stops with the Stata
        # that started it.
        for flag in ["--port", "--address", "--allow-websocket-origin",
                     "--trust-forwarded-for", "--show", "--timeout",
                     "--parent-watch"] + [
                         f for f, _dest, _d in _NEW_FLAGS]:
            assert flag in r.stdout, (flag, r.stdout)

    def test_the_launcher_refuses_a_bad_limit_before_serving(self, served):
        r = self._run(served, "--sessions-per-client", "0")
        assert r.returncode == 2, (r.returncode, r.stderr[-2000:])
        assert "1 to 1,000,000" in r.stderr, r.stderr[-2000:]
        assert "Bokeh Server running" not in r.stdout
