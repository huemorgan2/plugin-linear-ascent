"""Apply the v5 amnesty to live documents now, instead of waiting for each
climber to next open the game.

`ensure_current` already heals a document on load, so this script is only
an accelerator — it runs the exact same function and writes the result
back. It is safe to skip, and safe to run twice.

    PROD_DB=... python writeback.py            # dry run, prints the plan
    PROD_DB=... python writeback.py --apply    # writes

Every UPDATE is guarded on the document it read (`AND doc = $old::jsonb`)
inside one transaction per row, so a turn played between the read and the
write is never clobbered — that row is reported as skipped and heals
itself on load anyway. Nothing is ever deleted.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import asyncpg                                   # noqa: E402

from plugin_linear_ascent import economy         # noqa: E402
from plugin_linear_ascent.engine import state    # noqa: E402


def name_of(slug):
    g = economy.FORGE.get(slug or "")
    return g.name if g else "—"


async def main():
    dsn = os.environ["PROD_DB"]
    apply = "--apply" in sys.argv
    conn = await asyncpg.connect(dsn)

    rows = await conn.fetch(
        "SELECT tenant, player, doc FROM ascent_players "
        "ORDER BY tenant, player")

    print(f"{'tenant/player':34} {'weapon before':22} {'weapon after':22} "
          "result")
    print("─" * 100)
    changed = skipped = same = 0

    for r in rows:
        who = f"{r['tenant']}/{r['player']}"
        old = json.loads(r["doc"])
        new = json.loads(r["doc"])
        state.ensure_current(new)

        before = name_of(old["gear"].get("weapon"))
        if new == old:
            same += 1
            print(f"{who:34} {before:22} {'—':22} already current")
            continue

        after = name_of(new["gear"].get("weapon"))
        line = f"{who:34} {before:22} {after:22} "
        if not apply:
            changed += 1
            print(line + "would update")
            continue

        async with conn.transaction():
            ok = await conn.fetchval(
                "UPDATE ascent_players SET doc = $3::jsonb, "
                "updated_at = now() "
                "WHERE tenant = $1 AND player = $2 AND doc = $4::jsonb "
                "RETURNING 1",
                r["tenant"], r["player"], json.dumps(new), r["doc"])
        if ok:
            changed += 1
            print(line + "updated")
        else:
            skipped += 1
            print(line + "SKIPPED — row changed under us; heals on load")

    print("─" * 100)
    verb = "updated" if apply else "would update"
    print(f"{len(rows)} docs — {changed} {verb}, {same} already current, "
          f"{skipped} skipped")
    if not apply:
        print("\ndry run — re-run with --apply to write")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
