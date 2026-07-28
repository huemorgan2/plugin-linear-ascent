"""A restarting Postgres must not make the plugin un-upgradeable.

Luna rolls an upgrade back whenever on_load raises, and hosted Luna shares
one Postgres cluster between tenants — so "the database system is in
recovery mode" (57P03) used to surface to the player as "Couldn't update
plugin-linear-ascent". Table setup now rides the restart out, and never
fails the load.
"""

import asyncio
import sys
import types

import pytest

from plugin_linear_ascent import plugin as plugmod


class _Conn:
    def __init__(self, made):
        self._made = made

    async def run_sync(self, fn, **kw):
        self._made.append(fn)


class _Begin:
    def __init__(self, engine):
        self._e = engine

    async def __aenter__(self):
        self._e.attempts += 1
        if self._e.attempts <= self._e.fail_times:
            raise self._e.error
        return _Conn(self._e.made)

    async def __aexit__(self, *exc):
        return False


class _Engine:
    """Fails the first `fail_times` transactions with `error`."""

    def __init__(self, error=None, fail_times=0):
        self.error, self.fail_times = error, fail_times
        self.attempts, self.made = 0, []

    def begin(self):
        return _Begin(self)


class _Ctx:
    def __init__(self, engine):
        self.engine = engine


def _recovering():
    return OSError("the database system is in recovery mode")


@pytest.fixture(autouse=True)
def _no_waiting(monkeypatch):
    monkeypatch.setattr(plugmod, "_DDL_BACKOFF", 0.0)
    # The table module needs SQLAlchemy, which unit tests run without; the
    # retry loop is what's under test, not the DDL itself.
    fake = types.ModuleType("plugin_linear_ascent.backend.local")
    fake.Base = types.SimpleNamespace(
        metadata=types.SimpleNamespace(sorted_tables=[
            types.SimpleNamespace(create="ascent_players"),
            types.SimpleNamespace(create="ascent_ledger"),
        ]))
    monkeypatch.setitem(
        sys.modules, "plugin_linear_ascent.backend.local", fake)


def test_tables_created_when_the_database_is_healthy():
    eng = _Engine()
    assert asyncio.run(plugmod._ensure_local_tables(_Ctx(eng))) is True
    assert eng.attempts == 1
    assert eng.made, "expected the tables to be created"


def test_survives_a_database_that_is_still_recovering():
    eng = _Engine(error=_recovering(), fail_times=2)
    assert asyncio.run(plugmod._ensure_local_tables(_Ctx(eng))) is True
    assert eng.attempts == 3          # two refusals, then it comes back


def test_never_raises_when_the_database_stays_down():
    # raising here is what rolls the whole upgrade back
    eng = _Engine(error=_recovering(), fail_times=99)
    assert asyncio.run(plugmod._ensure_local_tables(_Ctx(eng))) is False
    assert eng.attempts == plugmod._DDL_ATTEMPTS


def test_a_real_error_fails_fast_without_retrying():
    eng = _Engine(error=ValueError("column does not exist"), fail_times=99)
    assert asyncio.run(plugmod._ensure_local_tables(_Ctx(eng))) is False
    assert eng.attempts == 1


def test_recovery_mode_is_recognised_as_transient():
    assert plugmod._is_transient_db(_recovering())
    assert plugmod._is_transient_db(
        OSError("connection refused"))
    assert not plugmod._is_transient_db(ValueError("syntax error at or near"))
