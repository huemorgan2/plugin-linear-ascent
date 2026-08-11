"""045 — hold and endure.

§2 gear promotes itself from the pack (one weapon held, one shield, one
armour — the pack cell popup grows the Forge's wear verb); §3 endurance
is a number the player can read; §4 the floor's full menu comes back
after a fight.
"""

import copy

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def _character(name, clazz="warrior"):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    return p


def _gear(slot, line=None, style=""):
    return next(g for g in sorted(economy.FORGE.values(),
                                  key=lambda g: (g.rung, g.slug))
                if g.slot == slot and g.style == style and g.price > 0
                and (line is None or g.line == line))


# ── §2: promote from the pack ────────────────────────────────────────────

def test_pack_shield_offers_use_as_shield_and_equips():
    p = _character("Sten")
    g = next(x for x in sorted(economy.FORGE.values(),
                               key=lambda x: (x.rung, x.slug))
             if x.slot == "shield" and x.line != "sorcerer"
             and x.price > 0 and not x.style)
    p["inventory"][g.slug] = 1
    p["durability_pack"] = {g.slug: 77}
    acts, why = core.pack_actions(p, g.slug)
    assert [o.id for o in acts] == [f"wear_{g.slug}"]
    assert acts[0].label == "Use as shield"
    s = core.apply_choice(p, f"wear_{g.slug}")
    assert p["gear"]["shield"] == g.slug
    assert p["inventory"].get(g.slug) is None
    assert p["durability"]["shield"] == 77          # wear travels
    assert f"+ {g.name}" in "\n".join(s.body_lines)


def test_pack_weapon_offers_use_this_and_swaps_old_to_pack():
    p = _character("Bren")
    w1 = _gear("weapon", line="warrior")
    w2 = next(g for g in sorted(economy.FORGE.values(),
                                key=lambda g: (g.rung, g.slug))
              if g.slot == "weapon" and g.line == "warrior"
              and g.price > 0 and g.slug != w1.slug and not g.style)
    p["gear"]["weapon"] = w1.slug
    p["durability"]["weapon"] = economy.item_pool(w1)
    p["inventory"][w2.slug] = 1
    acts, _ = core.pack_actions(p, w2.slug)
    assert acts[0].label == "Use this"
    core.apply_choice(p, f"wear_{w2.slug}")
    assert p["gear"]["weapon"] == w2.slug
    assert p["inventory"][w1.slug] == 1              # old piece goes back
    assert p["hone"]["weapon"] == 0


def test_no_promotion_mid_fight():
    p = _character("Kel")
    g = _gear("shield")
    p["inventory"][g.slug] = 1
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    acts, why = core.pack_actions(p, g.slug)
    assert not any(o.id.startswith("wear_") for o in acts)
    # 048 phase 3: the refusal now speaks — a scene with the reason,
    # and NOTHING on the body moves.
    s = core._pack_use(p, f"wear_{g.slug}")
    assert s is not None
    assert "mid-fight" in (s.shard_note or "").lower()
    assert p["gear"].get(g.slot) != g.slug


def test_equipped_slug_refuses_with_a_reason():
    p = _character("Ori")
    g = _gear("shield")
    p["gear"]["shield"] = g.slug
    p["inventory"][g.slug] = 1                       # a spare of the same
    acts, why = core.pack_actions(p, g.slug)
    assert acts == []
    assert "Already" in why


# ── §3: endurance is a number ────────────────────────────────────────────

def test_endurance_rises_with_price_within_each_ladder():
    """The 'numbers work' guarantee: inside one ladder (slot+line, plain
    steel) the costlier rung always endures more."""
    for slot in ("shield", "armor"):
        ladders = {}
        for g in economy.FORGE.values():
            if g.slot == slot and not g.style and g.price > 0:
                ladders.setdefault(g.line, []).append(g)
        for line, items in ladders.items():
            items.sort(key=lambda g: g.price)
            ends = [economy.endurance(g) for g in items]
            assert ends == sorted(ends), (slot, line)


def test_styles_price_their_endurance_honestly():
    g = _gear("shield")
    styles = {v.style: v for v in economy.gear_styles(g)}
    if not styles:
        return
    assert economy.endurance(styles["keen"]) < economy.endurance(g) \
        < economy.endurance(styles["warded"])
    assert styles["warded"].price > g.price          # patience is paid for


def test_displayed_end_falls_by_the_damage_turned():
    p = _character("Vess")
    g = _gear("shield")
    p["gear"]["shield"] = g.slug
    p["durability"]["shield"] = economy.item_pool(g)
    p["level"] = 5
    p["hp"] = economy.player_max_hp(5)
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if e.id == "feral_boar")
    combat.start_encounter(p, fl, enc)
    for _ in range(30):
        before = p["durability"]["shield"]
        hit = combat._monster_hit(p, False, False, True)
        if hit["blocked"] <= 0:
            continue
        drop = (economy.endurance(g, before)
                - economy.endurance(g, p["durability"]["shield"]))
        share = hit["blocked"] * g.bonus / state.dfs(p)
        assert abs(drop - share) <= g.bonus, (drop, share)
        return
    raise AssertionError("no blocked blow in 30 swings")


def test_forge_cards_show_def_and_end():
    p = _character("Tam")
    s = core.apply_choice(p, "forge")
    gear_hints = [o.hint for o in s.options
                  if o.id.startswith("buy_") and "DEF" in (o.hint or "")]
    assert gear_hints, "no guard rows on the rack"
    assert all("END" in h for h in gear_hints), gear_hints
    repair_free = [o for o in s.options if o.id.startswith("repair_")]
    assert repair_free == []                         # fresh gear: no rows


# ── §4: the floor comes back after a fight ───────────────────────────────

def _hunt_victory(p, floor_n):
    """Walk to floor_n, start a hunt, pin the kill, swing once."""
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, f"floor_{floor_n}")
    if any(o.id == "skip" for o in s.options):       # arrival reel
        s = core.apply_choice(p, "skip")
    core.apply_choice(p, "hunt")
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    p["encounter"]["traits"] = []
    p["encounter"]["profile"] = {}                   # no flying/bulwark
    return core.apply_choice(p, "attack")


def test_after_fight_menu_is_the_floor_menu():
    p = _character("Rue")
    p["unlocked_floor"] = 4                          # frontier == floor
    p["level"] = 8
    p["hp"] = economy.player_max_hp(8) - 25          # hurt → heal rows
    p["inventory"]["medgel"] = 1
    s = _hunt_victory(p, 4)
    ids = [o.id for o in s.options]
    for want in ("hunt", "hunt_deep", "stew", "heal",
                 "use_medgel", "keep", "talk", "town"):
        assert want in ids, (want, ids)
    assert "gate" not in ids                         # frontier floor
    hunt = next(o for o in s.options if o.id == "hunt")
    assert hunt.label == "Hunt the wilds again"
    fl = schema.get_floor(4)
    assert s.option_art.get("hunt") == fl.banner     # tiles ride along


def test_gate_row_and_monument_keep_below_the_frontier():
    p = _character("Wren")
    p["unlocked_floor"] = 5                          # floor 4 is conquered
    p["level"] = 8
    p["hp"] = economy.player_max_hp(8)
    s = _hunt_victory(p, 4)
    ids = [o.id for o in s.options]
    assert ids.index("gate") == ids.index("hunt") + 1
    keep = next(o for o in s.options if o.id == "keep")
    assert "fell" in keep.label                      # monument, not a swing
    assert "monument" in keep.hint
    assert "⚡" not in keep.hint


def test_every_offered_id_survives_apply_choice():
    p = _character("Nix")
    p["unlocked_floor"] = 5
    p["level"] = 8
    p["hp"] = economy.player_max_hp(8) - 25
    p["inventory"]["medgel"] = 1
    s = _hunt_victory(p, 4)
    for o in s.options:
        q = copy.deepcopy(p)
        out = core.apply_choice(q, o.id)
        assert out is not None and out.headline, o.id
