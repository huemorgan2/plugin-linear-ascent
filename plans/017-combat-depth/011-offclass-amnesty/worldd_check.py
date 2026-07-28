"""End-to-end worldd check for the v5 amnesty.

Seeds a scratch worldd database with real player documents (the same
JSONL the rehearsal reads) and drives them through `game.run_scene` —
the exact path a live turn takes: load, migrate, render, persist. Then
re-reads the stored doc and asserts the weapon really changed on disk.

    DATABASE_URL=postgresql://.../ascent_v5_check \
        python worldd_check.py docs.jsonl
"""

import asyncio
import json
import os
import sys
from pathlib import Path

WORLDD = Path(__file__).resolve().parents[4] / "worldd"
sys.path.insert(0, str(WORLDD))
sys.path.insert(0, str(WORLDD / "vendor"))

from app import db, game                              # noqa: E402
from plugin_linear_ascent import economy              # noqa: E402


def name_of(slug):
    g = economy.FORGE.get(slug or "")
    return g.name if g else (slug or "—")


async def main(path):
    rows = [json.loads(ln) for ln in Path(path).read_text().splitlines() if ln]
    await db.init_db(os.environ["DATABASE_URL"])
    pool = await db.get_pool()

    for r in rows:
        await pool.execute(
            "INSERT INTO ascent_tenants (tenant, secret) VALUES ($1,$2) "
            "ON CONFLICT DO NOTHING", r["tenant"], "seed-secret")
        await pool.execute(
            "INSERT INTO ascent_players (tenant, player, doc) "
            "VALUES ($1,$2,$3) ON CONFLICT (tenant, player) DO UPDATE "
            "SET doc = EXCLUDED.doc",
            r["tenant"], r["player"], json.dumps(r["doc"]))

    failures = []
    print(f"{'tenant/player':34} {'class':9} {'weapon on disk after a turn':28} "
          f"{'v':>2} off-class?")
    print("─" * 96)
    for r in rows:
        await game.run_scene(r["tenant"], r["player"])
        stored = json.loads(await pool.fetchval(
            "SELECT doc FROM ascent_players WHERE tenant=$1 AND player=$2",
            r["tenant"], r["player"]))
        slug = stored["gear"].get("weapon")
        g = economy.FORGE.get(slug or "")
        line = getattr(g, "line", "") if g else ""
        off = bool(line) and bool(stored.get("clazz")) \
            and line != stored["clazz"]
        if off or stored.get("version", 1) < 5:
            failures.append(f"{r['tenant']}/{r['player']}")
        print(f"{r['tenant'] + '/' + r['player']:34} "
              f"{stored.get('clazz') or '—':9} {name_of(slug):28} "
              f"{stored.get('version', 1):>2} {'YES' if off else 'no'}")

    print("─" * 96)
    if failures:
        print(f"FAIL — {len(failures)} doc(s) still wrong: {failures}")
        return 1
    print(f"PASS — {len(rows)} docs at v5, none off-class")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("ASCENT_SHARED_SECRET", "seed-secret")
    sys.exit(asyncio.run(main(sys.argv[1])))
