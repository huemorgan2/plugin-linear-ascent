"""Actual PostgreSQL local transactions and transport retry identities."""
import asyncio
from copy import deepcopy
import os
import uuid

import httpx
import pytest

from plugin_linear_ascent.backend.remote import WorldClient
from plugin_linear_ascent.engine import core, state

pytestmark = pytest.mark.reel


def test_timeout_reuses_the_exact_request_identity():
    class CommittedButTimedOut(WorldClient):
        def __init__(self):
            self.sent = []
        async def _post(self, path, payload):
            self.sent.append(deepcopy(payload))
            if len(self.sent) == 1:
                raise httpx.ReadTimeout("The server committed but the response timed out")
            return {"scene": {"headline": "Paid once"}}
    async def run():
        client = CommittedButTimedOut()
        out = await client.act("a", "upgrade", "", expected_scene="s17")
        assert out == {"headline": "Paid once"}
        assert client.sent[0] == client.sent[1]
        assert client.sent[0]["scene_id"] == "s17"
    asyncio.run(run())


@pytest.mark.skipif(not os.environ.get("ASCENT_LOCAL_TEST_DATABASE_URL"), reason="Requires isolated local PostgreSQL test database")
def test_local_two_clients_cannot_spend_the_same_scene_twice():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from plugin_linear_ascent.backend.local import Base, LocalBackend
    async def run():
        engine = create_async_engine(os.environ["ASCENT_LOCAL_TEST_DATABASE_URL"])
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            sf = async_sessionmaker(engine, expire_on_commit=False)
            a, b = LocalBackend(sf), LocalBackend(sf)
            key = "parallel-local:" + uuid.uuid4().hex
            p = state.new_player(key)
            p.update(stage="playing", name="Local", race="human", location="vault", gold=1000)
            await a.save(key, p, [])
            def act(doc):
                return core.apply_choice(doc, "deposit_half", expected_scene="s0")
            results = await asyncio.gather(a.run(key, act), b.run(key, act))
            saved = await a.load(key)
            assert saved["gold"] == saved["bank"] == 500
            assert saved["act_seq"] == 1
            assert sum(bool(r.refusal) for r in results) == 1
        finally:
            await engine.dispose()
    asyncio.run(run())
