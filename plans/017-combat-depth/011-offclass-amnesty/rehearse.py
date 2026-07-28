"""Doc v5 rehearsal — run ensure_current over a dump of every live doc and
report what it changes, before anything is written back.

    psql "$PROD_DB" -At -c "SELECT json_build_object('tenant',tenant,
        'player',player,'doc',doc)::text FROM ascent_players" > docs.jsonl
    python rehearse.py docs.jsonl

Reports per player: doc version, class, the equipped weapon before and
after, whether it is off-class either side, and any pending letter added.
Exits non-zero if any doc ends the pass still holding another class's
weapon, or if a second pass is not a no-op.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from plugin_linear_ascent import economy          # noqa: E402
from plugin_linear_ascent.engine import state     # noqa: E402


def off_class(doc):
    g = economy.FORGE.get(doc["gear"].get("weapon") or "")
    line = getattr(g, "line", "") if g else ""
    return bool(line) and bool(doc.get("clazz")) and line != doc["clazz"]


def name_of(slug):
    g = economy.FORGE.get(slug or "")
    return g.name if g else (slug or "—")


def main(path):
    rows = [json.loads(ln) for ln in Path(path).read_text().splitlines() if ln]
    bad = []
    print(f"{'tenant/player':34} {'class':9} {'v':>2}→{'v':<2} "
          f"{'weapon before':22} {'weapon after':22} note")
    print("─" * 118)
    for r in rows:
        doc = r["doc"]
        who = f"{r['tenant']}/{r['player']}"
        v0, w0, off0 = doc.get("version", 1), doc["gear"].get("weapon"), \
            off_class(doc)
        letters0 = len(doc.get("pending_events") or [])

        state.ensure_current(doc)

        v1, w1, off1 = doc.get("version", 1), doc["gear"].get("weapon"), \
            off_class(doc)
        letters1 = len(doc.get("pending_events") or [])

        # a second pass must change nothing
        snapshot = json.dumps(doc, sort_keys=True)
        state.ensure_current(doc)
        idempotent = json.dumps(doc, sort_keys=True) == snapshot

        notes = []
        if off0 and not off1:
            notes.append("OFF-CLASS HEALED")
        if letters1 > letters0:
            notes.append(f"+{letters1 - letters0} letter")
        if off1:
            notes.append("STILL OFF-CLASS")
            bad.append(who)
        if not idempotent:
            notes.append("NOT IDEMPOTENT")
            bad.append(who)

        print(f"{who:34} {doc.get('clazz') or '—':9} {v0:>2}→{v1:<2} "
              f"{name_of(w0):22} {name_of(w1):22} {', '.join(notes)}")

    print("─" * 118)
    print(f"{len(rows)} docs, {len(set(bad))} needing attention")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "docs.jsonl"))
