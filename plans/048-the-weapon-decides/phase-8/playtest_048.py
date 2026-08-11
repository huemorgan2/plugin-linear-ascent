"""048 phase 8 — hand playtest floors 1-12, dojo-style engine drive.

The intended-first-ten script: classless open (Rusted Sword, blade 2),
bow by floor 3, 2nd slot by 4, staff by 6, ranks 2/2/2, blade 4 by 8.
Meet all three signs (shellback_tortoise f2, windfall_haunt f3,
glare_moth f4), one deliberate wrong-weapon defeat (blade vs
glare_moth). Every scene is logged; anything surprising is flagged
CONFUSED for the human read.
"""
import re
import sys

sys.path.insert(0, "tests")
import conftest  # noqa: F401

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state

LOG = open(sys.argv[1] if len(sys.argv) > 1 else "playtest.log", "w")

BOW1 = economy.weapon_line("archer")[0].slug
STAFF1 = economy.weapon_line("sorcerer")[0].slug


def log(*a):
    print(*a, file=LOG)


def show(s, tag=""):
    log(f"\n──[{tag}] {s.eyebrow} · {s.headline}")
    if s.support:
        log(f"   ({s.support})")
    if getattr(s, "shard_note", ""):
        log(f"   ✦ shard: {s.shard_note}")
    for ln in s.body_lines:
        log(f"   {ln}")
    for o in s.options:
        sub = f" — {o.sub}" if getattr(o, "sub", "") else ""
        lock = " 🔒" if getattr(o, "locked", False) else ""
        log(f"   [{o.id}]{lock} {o.label}{sub}")
    return s


def scene(p, tag=""):
    return show(core.current_scene(p), tag)


def choose(p, oid, tag="", text=""):
    s = core.apply_choice(p, oid, text)
    return show(s, tag or oid)


def pick(p, s, pattern, tag=""):
    for o in s.options:
        if re.fullmatch(pattern, o.id):
            return choose(p, o.id, tag or o.id)
    log(f"   !! CONFUSED: no option matching /{pattern}/ on "
        f"'{s.headline}' — ids: {[o.id for o in s.options]}")
    return s


def drain(p, tag="drain"):
    """Skip movies and pending event cards until a real menu shows."""
    s = core.current_scene(p)
    guard = 0
    while guard < 20:
        guard += 1
        ids = {o.id for o in s.options}
        if p.get("movie_floor") and "skip" in ids:
            s = choose(p, "skip", f"{tag}-skip")
        elif ids and ids <= {"next", "skip", "town", "so_be_it"} \
                and p.get("pending_events"):
            s = choose(p, next(iter(ids)), f"{tag}-event")
        elif ids <= {"next", "skip"} and ids:
            s = choose(p, "skip" if "skip" in ids else "next",
                       f"{tag}-beat")
        else:
            return show(s, f"{tag}-done")
    return s


def fight_out(p, fl, tag, action="attack"):
    rounds = 0
    s = core.current_scene(p)
    while p.get("encounter") is not None and rounds < 40:
        rounds += 1
        s = combat.resolve_fight_action(p, fl, action)
        show(s, f"{tag} r{rounds}")
        if s.event_kind == "death" or p["hp"] <= 0:
            break
    return s


def top_up(p, gold=None, energy=25, hp=True):
    p["energy"] = energy
    if gold is not None and p["gold"] < gold:
        p["gold"] = gold
    if hp:
        p["hp"] = state.max_hp(p)


def equip(p, slug):
    p["gear"]["weapon"] = slug
    held = p.setdefault("held", [])
    if slug in held:
        held.remove(slug)
    held.insert(0, slug)
    del held[max(1, int(p.get("slots", 1))):]


def targeted(p, floor_no, enc_id, tag, action="attack"):
    fl = schema.get_floor(floor_no)
    enc = next(e for e in fl.encounters if e.id == enc_id)
    p["floor"] = floor_no
    p["location"] = "gate_town"
    combat.start_encounter(p, fl, enc)
    log(f"\n   verdict for {enc_id}:")
    for ln in combat._verdict(p):
        log(f"     {ln}")
    scene(p, f"{tag} opener")
    return fight_out(p, fl, tag, action)


# ── 1. the classless open ────────────────────────────────────────────
log("=" * 70)
log("BEAT 1 — creation: race → name, no class question")
p = state.new_player("playtest-048")
s = scene(p, "open")
guard = 0
while p["stage"] == "intro" and guard < 12:
    guard += 1
    s = pick(p, s, "next|begin", "intro")
s = pick(p, s, "elf", "race")
if p["stage"] == "creation_name":
    s = choose(p, "", "name", text="Handtest")
log(f"\n   post-creation: stage={p['stage']} weapon={p['gear']['weapon']}"
    f" held={p.get('held')} training={p.get('training')}"
    f" slots={p.get('slots')} gold={p['gold']}")
if p["gear"]["weapon"] != "rusted_sword" or p["training"].get("blade") != 2:
    log("   !! CONFUSED: classless open kit wrong")
drain(p, "post-creation")

# ── 2. town doors: in and out once ───────────────────────────────────
log("\n" + "=" * 70)
log("BEAT 2 — every unlocked town door opens and its exit returns")
p["location"] = "town"
s = scene(p, "town")
doors = [o.id for o in s.options
         if o.id not in ("gate", "sleep_menu") and not o.locked]
for door in doors:
    s = scene(p, "town")
    s = choose(p, door, f"enter-{door}")
    if p["location"] == "town":
        log(f"   (the {door} door refused — see its note above)")
        continue
    back = next((o.id for o in s.options
                 if o.id in ("town", "back")), None)
    if back is None:
        log(f"   !! CONFUSED: no way back from {door} — "
            f"{[o.id for o in s.options]}")
        p["location"] = "town"
    else:
        choose(p, back, f"exit-{door}")
        if p["location"] != "town" and not p.get("encounter"):
            log(f"   !! CONFUSED: back from {door} landed in "
                f"{p['location']}")
            p["location"] = "town"

# ── 3. floor 1 hunts — young-tower bounty on the kill card ──────────
log("\n" + "=" * 70)
log("BEAT 3 — floor 1: hunt twice, read the kill cards")
top_up(p)
p["location"] = "town"
s = scene(p, "town")
s = pick(p, s, "gate", "gate")
s = pick(p, s, "floor_1", "lift")
drain(p, "f1-movie")
for i in range(2):
    s = drain(p, f"pre-hunt{i}")
    s = pick(p, s, "hunt", f"hunt{i}")
    fl = schema.get_floor(1)
    fight_out(p, fl, f"f1 hunt{i}")
    top_up(p)

# ── 4. the Forge counter: the first bow ─────────────────────────────
log("\n" + "=" * 70)
log(f"BEAT 4 — Forge: the first bow ({BOW1}), the rank voice on rows")
drain(p, "pre-forge")
p["location"] = "town"
top_up(p, gold=300)
s = choose(p, "forge", "forge")
s = pick(p, s, f"buy_{BOW1}", "buy-bow")
log(f"   inventory now: {p.get('inventory')}")

# ── 5. the School: train bow 2, learn the 2nd slot ──────────────────
log("\n" + "=" * 70)
log("BEAT 5 — School at floor 3's gate town: bow 2, 2nd slot")
top_up(p, gold=600)
p["xp"] += 300
p["unlocked_floor"] = max(p["unlocked_floor"], 4)
p["floor"] = 3
p["location"] = "gate_town"
s = drain(p, "f3-arrive")
s = pick(p, s, "school", "school-door")
s = pick(p, s, "train_bow", "bow-1")
s = pick(p, s, "train_bow", "bow-2")
s = pick(p, s, "buy_carry2", "carry2")
log(f"   training={p['training']} slots={p['slots']}")
s = pick(p, s, "back", "school-back")
if p["location"] != "gate_town":
    log(f"   !! CONFUSED: School back → {p['location']}")

# ── 6. the three signs, fair hands ──────────────────────────────────
log("\n" + "=" * 70)
log("BEAT 6 — the staircase: one sign at a time, fair weapon in hand")
p["level"] = 4
top_up(p)
equip(p, "rusted_sword")
targeted(p, 2, "shellback_tortoise", "f2 ⛨ blade-vs-plate")
top_up(p)
targeted(p, 3, "windfall_haunt", "f3 ✧ blade-vs-spellguard")
top_up(p)
equip(p, BOW1)
targeted(p, 4, "glare_moth", "f4 ⚡ bow-vs-wings")

# ── 7. the deliberate wrong-weapon defeat: blade vs glare_moth ──────
log("\n" + "=" * 70)
log("BEAT 7 — blade vs the moth, on purpose; read the defeat card")
top_up(p)
p["daily"]["death_save"] = True          # let the death be a real death
equip(p, "rusted_sword")
targeted(p, 4, "glare_moth", "WRONG blade-vs-moth")
log(f"   after: hp={p['hp']} location={p['location']} "
    f"gold={p['gold']}")

# ── 8. staff by 6, ranks to script ──────────────────────────────────
log("\n" + "=" * 70)
log(f"BEAT 8 — staff at the Arcanum ({STAFF1}), staff 2, blade to 4")
if p.get("encounter"):
    p["encounter"] = None
p["level"] = 6
top_up(p, gold=3000, energy=25)
p["hp"] = max(p["hp"], 1)
p["xp"] += 1500
p["location"] = "town"
s = choose(p, "arcanum", "arcanum")
s = pick(p, s, f"buy_{STAFF1}", "buy-staff")
p["floor"] = 6
p["unlocked_floor"] = max(p["unlocked_floor"], 6)
p["location"] = "gate_town"
s = drain(p, "f6-arrive")
s = pick(p, s, "school", "school-f6")
s = pick(p, s, "train_staff", "staff-1")
s = pick(p, s, "train_staff", "staff-2")
s = pick(p, s, "train_blade", "blade-3")
s = pick(p, s, "train_blade", "blade-4")
log(f"   training={p['training']}")

# ── 9. floors 5-12: one targeted fight each, the fair hand ──────────
log("\n" + "=" * 70)
log("BEAT 9 — floors 5-12, first roster monster, fair weapon")
FAIR_WEAPON = {"fly": BOW1, "armoured": STAFF1,
               "magic_resist": "rusted_sword", "plain": "rusted_sword"}
p["level"] = 12
p["slots"] = 3
p["held"] = ["rusted_sword", BOW1, STAFF1]
for f in range(5, 13):
    p["unlocked_floor"] = max(p["unlocked_floor"], f)
    fl = schema.get_floor(f)
    enc = fl.encounters[0]
    t = economy.type_of(enc.traits)
    equip(p, FAIR_WEAPON[t])
    top_up(p)
    targeted(p, f, enc.id, f"f{f} {t}")

# ── 10. migration wording: a legacy sorcerer wakes up ───────────────
log("\n" + "=" * 70)
log("BEAT 10 — legacy doc (clazz=sorcerer, v6) reads its School letter")
q = state.new_player("playtest-048-legacy")
q.update(stage="playing", clazz="sorcerer", name="Oldhand",
         location="town", version=6)
q.pop("training", None)
s = scene(q, "legacy-load")
log(f"   legacy training after load: {q.get('training')}")
if q.get("training", {}).get("staff") != 6:
    log("   !! CONFUSED: legacy sorcerer not honored at staff 6")

log("\nDONE")
LOG.close()
print("playtest complete")
