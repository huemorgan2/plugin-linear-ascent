"""Local StateBackend — plugin-owned tables in Luna's database.

Solo play (phases 0–2) runs entirely here; phase 3 swaps in the worldd
client. Tables are namespaced ascent_*.
"""

from __future__ import annotations

import datetime as dt

from luna_sdk import JSONB, declarative_base
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, select, text

from ..engine import state as pstate

Base = declarative_base()


class AscentPlayer(Base):
    __tablename__ = "ascent_players"
    luna_user = Column(String(128), primary_key=True)
    doc = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: dt.datetime.now(dt.timezone.utc))


class AscentLedger(Base):
    __tablename__ = "ascent_ledger"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    luna_user = Column(String(128), nullable=False, index=True)
    kind = Column(String(32), nullable=False)
    gold = Column(BigInteger, nullable=False, default=0)
    xp = Column(BigInteger, nullable=False, default=0)
    note = Column(String(256), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False,
                        default=lambda: dt.datetime.now(dt.timezone.utc))


class LocalBackend:
    def __init__(self, session_factory):
        self._sf = session_factory

    async def run(self, luna_user: str, operation):
        """Read, resolve and persist under one PostgreSQL transaction."""
        async with self._sf() as s:
            async with s.begin():
                await s.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"),
                                {"key": "ascent-local:" + luna_user})
                row = (await s.execute(select(AscentPlayer).where(
                    AscentPlayer.luna_user == luna_user).with_for_update())).scalar_one_or_none()
                doc = dict(row.doc) if row else pstate.new_player(luna_user)
                from ..engine import collection
                if collection.enrollment_open() and not collection.enabled(doc) and not doc.get("encounter"):
                    receipts = (await s.execute(select(AscentLedger).where(
                        AscentLedger.luna_user == luna_user,
                        AscentLedger.kind == "train",
                        AscentLedger.note.in_(("carry 2", "carry 3"))).order_by(AscentLedger.id))).scalars()
                    doc["school_slot_receipts"] = [dict(kind=r.kind, note=r.note, gold=r.gold, xp=r.xp)
                                                    for r in receipts]
                scene = operation(doc)
                ledger = doc.pop("_ledger", [])
                doc["scene"] = scene.to_dict()
                if row is None:
                    s.add(AscentPlayer(luna_user=luna_user, doc=doc))
                else:
                    row.doc = doc
                    row.updated_at = dt.datetime.now(dt.timezone.utc)
                for entry in ledger:
                    s.add(AscentLedger(luna_user=luna_user, kind=entry.get("kind", ""),
                        gold=int(entry.get("gold", 0)), xp=int(entry.get("xp", 0)),
                        note=str(entry.get("note", ""))[:256]))
                return scene

    async def load(self, luna_user: str) -> dict:
        async with self._sf() as s:
            row = (await s.execute(
                select(AscentPlayer).where(
                    AscentPlayer.luna_user == luna_user))).scalar_one_or_none()
            if row is None:
                return pstate.new_player(luna_user)
            return dict(row.doc)

    async def save(self, luna_user: str, doc: dict,
                   ledger: list[dict]) -> None:
        async with self._sf() as s:
            row = (await s.execute(
                select(AscentPlayer).where(
                    AscentPlayer.luna_user == luna_user))).scalar_one_or_none()
            if row is None:
                s.add(AscentPlayer(luna_user=luna_user, doc=doc))
            else:
                row.doc = doc
                row.updated_at = dt.datetime.now(dt.timezone.utc)
            for entry in ledger:
                s.add(AscentLedger(
                    luna_user=luna_user, kind=entry.get("kind", ""),
                    gold=int(entry.get("gold", 0)), xp=int(entry.get("xp", 0)),
                    note=str(entry.get("note", ""))[:256]))
            await s.commit()
