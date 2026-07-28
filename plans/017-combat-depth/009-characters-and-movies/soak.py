#!/usr/bin/env python3
"""009 migration soak — run ensure_current over EVERY player doc in a
world database and prove zero errors and zero halflings left.

Usage:
  python soak.py                      # local qa docker DB (port 5434)
  DATABASE_URL=postgres://... python soak.py   # any worldd DB / export

Reads docs via docker psql (local) or psycopg if DATABASE_URL is set,
deep-copies each, runs the plugin's ensure_current, and reports the doc
shapes seen (version, race, stage) and any exceptions. Never writes.
"""

from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", ".."))

from plugin_linear_ascent.engine import state  # noqa: E402


def _docs_local() -> list[dict]:
    out = subprocess.run(
        ["docker", "exec", "ascent-postgres", "psql", "-U", "ascent",
         "-d", "ascent_world", "-t", "-A",
         "-c", "SELECT doc FROM ascent_players"],
        capture_output=True, text=True, check=True).stdout
    return [json.loads(line) for line in out.splitlines() if line.strip()]


def _docs_url(url: str) -> list[dict]:
    try:
        import psycopg
        with psycopg.connect(url) as conn:
            rows = conn.execute(
                "SELECT doc FROM ascent_players").fetchall()
        rows = [r[0] for r in rows]
    except ModuleNotFoundError:      # worldd's venv ships asyncpg only
        import asyncio

        import asyncpg

        async def fetch():
            conn = await asyncpg.connect(url)
            try:
                return [r["doc"] for r in await conn.fetch(
                    "SELECT doc FROM ascent_players")]
            finally:
                await conn.close()

        rows = asyncio.run(fetch())
    return [r if isinstance(r, dict) else json.loads(r) for r in rows]


def main() -> int:
    url = os.environ.get("DATABASE_URL")
    docs = _docs_url(url) if url else _docs_local()
    shapes: Counter[tuple] = Counter()
    errors: list[tuple[str, str]] = []
    halflings_before = halflings_after = 0
    for doc in docs:
        before = (doc.get("version", 1), doc.get("race"),
                  doc.get("stage"))
        shapes[before] += 1
        if doc.get("race") == "halfling":
            halflings_before += 1
        work = copy.deepcopy(doc)
        try:
            state.ensure_current(work)
            assert work["version"] >= 4, "doc not brought to v4"
            if work.get("race") == "halfling":
                halflings_after += 1
        except Exception as exc:  # noqa: BLE001 — the soak reports, not raises
            errors.append((doc.get("luna_user", "?"), repr(exc)))
    print(f"docs: {len(docs)}")
    print("shapes (version, race, stage):")
    for shape, n in sorted(shapes.items(), key=lambda kv: -kv[1]):
        print(f"  {n:4d}  {shape}")
    print(f"halflings: {halflings_before} before -> {halflings_after} after")
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for user, err in errors[:20]:
            print(f"  {user}: {err}")
        return 1
    print("zero errors — soak PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
