"""Dojo helper: teleport the qa007 'owner' player to a floor with the
design's at-level reference loadout (level = floor, current-tier gear,
hone 2 floors behind, full HP).  Mirrors reference_player in
tests/test_017_damage_types.py so dojo fights match the sim gates."""

import json
import subprocess
import sys

sys.path.insert(0, ".")
from plugin_linear_ascent import economy  # noqa: E402

floor = int(sys.argv[1])
clazz = sys.argv[2] if len(sys.argv) > 2 else "warrior"

tier = economy.gear_tier_for_floor(floor)
w = next(g for g in economy.weapon_line(clazz) if g.rung == tier).slug
sh = next(g for g in economy.gear_rungs("shield") if g.rung == tier).slug
ar = next(g for g in economy.gear_rungs("armor") if g.rung == tier).slug
hone = {s: economy.reference_hone(floor) for s in economy.HONE_SLOTS}

sql = f"""UPDATE ascent_players SET doc = jsonb_set(jsonb_set(jsonb_set(
 jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(jsonb_set(doc,
 '{{level}}', '{floor}'),
 '{{unlocked_floor}}', '{floor}'),
 '{{hp}}', '{economy.player_max_hp(floor)}'),
 '{{clazz}}', '"{clazz}"'),
 '{{gear,weapon}}', '"{w}"'),
 '{{gear,shield}}', '"{sh}"'),
 '{{gear,armor}}', '"{ar}"'),
 '{{hone}}', '{json.dumps(hone)}'),
 '{{encounter}}', 'null')
 WHERE tenant='qa007' AND player='owner'"""
r = subprocess.run(["docker", "exec", "ascent-postgres", "psql", "-U",
                    "ascent", "-d", "ascent_world", "-c", sql],
                   capture_output=True, text=True)
print(r.stdout.strip() or r.stderr.strip())
print(f"owner -> {clazz} floor {floor}, {w}/{sh}/{ar}, hone {hone}")
