"""045 — hold and endure.

§2 gear promotes itself from the pack (one weapon held, one shield, one
armour — the pack cell popup grows the Forge's wear verb); §3 endurance
is a number the player can read; §4 the floor's full menu comes back
after a fight.
"""

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
    assert core._pack_use(p, f"wear_{g.slug}") is None


def test_equipped_slug_refuses_with_a_reason():
    p = _character("Ori")
    g = _gear("shield")
    p["gear"]["shield"] = g.slug
    p["inventory"][g.slug] = 1                       # a spare of the same
    acts, why = core.pack_actions(p, g.slug)
    assert acts == []
    assert "Already" in why
