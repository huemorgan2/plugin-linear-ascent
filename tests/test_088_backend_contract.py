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


@pytest.mark.skipif(not os.environ.get("ASCENT_LOCAL_TEST_DATABASE_URL"), reason="Requires isolated local PostgreSQL test database")
def test_existing_integer_ledger_widens_without_losing_history():
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from plugin_linear_ascent.plugin import _widen_local_ledger
    async def run():
        engine = create_async_engine(os.environ["ASCENT_LOCAL_TEST_DATABASE_URL"])
        try:
            async with engine.begin() as conn:
                schema = "collection_ledger_" + uuid.uuid4().hex
                await conn.execute(text(f"CREATE SCHEMA {schema}"))
                await conn.execute(text(f"SET LOCAL search_path TO {schema}"))
                await conn.execute(text("CREATE TABLE ascent_ledger (gold INTEGER, xp INTEGER)"))
                await conn.execute(text("INSERT INTO ascent_ledger VALUES (27, 13)"))
                await conn.run_sync(_widen_local_ledger)
                await conn.run_sync(_widen_local_ledger)
                await conn.execute(text("INSERT INTO ascent_ledger VALUES (:n, :n)"), {"n": 2**40})
                assert (await conn.execute(text("SELECT gold,xp FROM ascent_ledger ORDER BY gold"))).all() == [(27,13),(2**40,2**40)]
        finally:
            await engine.dispose()
    asyncio.run(run())


@pytest.mark.skipif(not os.environ.get('ASCENT_LOCAL_TEST_DATABASE_URL'),reason='Requires isolated local PostgreSQL test database')
def test_local_final_group_settlement_is_atomic(monkeypatch):
    from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
    from plugin_linear_ascent.backend.local import Base,LocalBackend
    from plugin_linear_ascent.engine import bestiary,collection,groups
    from plugin_linear_ascent.content import schema
    monkeypatch.setenv('ASCENT_RULESET',collection.RULESET)
    async def run():
        engine=create_async_engine(os.environ['ASCENT_LOCAL_TEST_DATABASE_URL'])
        try:
            async with engine.begin() as conn:await conn.run_sync(Base.metadata.create_all)
            sf=async_sessionmaker(engine,expire_on_commit=False)
            a,b=LocalBackend(sf),LocalBackend(sf)
            key='group-local:'+uuid.uuid4().hex
            p=state.new_player(key)
            p.update(stage='playing',name='Localgroup',race='human',location='gate_town',floor=1,training=dict(blade=10,bow=10,staff=10))
            core.current_scene(p)
            ms=[bestiary.rolled_member(p,1,schema.get_floor(1).encounters[0].id,opening=True) for _ in range(2)]
            for m in ms:
                m.update(hp=1,hp_max=1,defense=0,gap=3)
                m['rewards']=dict(gold=12,xp=2,materials={'Raw Metal':1},weapon=None)
            groups.open_group(p,members=ms)
            bow=p['deck'][1];core.apply_choice(p,'strike:'+bow)
            p.pop('_ledger',None);await a.save(key,p,[])
            scene=f"s{p['act_seq']}"
            def final(doc):return core.apply_choice(doc,'strike:'+bow,expected_scene=scene)
            result=await asyncio.gather(a.run(key,final),b.run(key,final))
            stored=await a.load(key)
            assert stored['gold']==p['gold']+24 and stored['materials']['Raw Metal']==2
            assert sum(bool(s.refusal) for s in result)==1
        finally:await engine.dispose()
    asyncio.run(run())
