"""0.29.4 — the broker's law, enforced: the pawn buys ANYTHING (006
§3.8), potions and repair tokens included; and the repair token finally
spends at the Forge as the free mend its name promised."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.tips import item_tip


def playing(name="Pawner"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    return p


def test_the_broker_quotes_the_repair_token():
    p = playing("token")
    p["inventory"]["repair_token"] = 2
    s = core.apply_choice(p, "pawn")
    assert any(o.id == "sell_repair_token" for o in s.options)
    assert any("repair token ×2" in ln for ln in s.body_lines)
    assert not any("Empty pack" in ln for ln in s.body_lines)
    gold = p["gold"]
    core.apply_choice(p, "sell_repair_token")
    assert p["gold"] > gold
    assert p["inventory"]["repair_token"] == 1


def test_the_broker_quotes_potions_too():
    p = playing("gel")
    p["inventory"]["medgel"] = 1
    s = core.apply_choice(p, "pawn")
    assert any(o.id == "sell_medgel" for o in s.options)
    gold = p["gold"]
    core.apply_choice(p, "sell_medgel")
    rate = economy.pawn_rate(state.world_day())
    assert p["gold"] - gold == max(1, int(25 * rate))
    assert "medgel" not in p["inventory"]


def test_an_actually_empty_pack_reads_as_empty_not_refusal():
    p = playing("broke")
    p["inventory"] = {}
    s = core.apply_choice(p, "pawn")
    assert any("buys ANYTHING" in ln for ln in s.body_lines)


def test_repair_token_mends_at_the_forge_for_free():
    p = playing("smith")
    # a PAID, worn weapon (starter steel doesn't wear) and one token
    g = economy.FORGE["pigsticker"]
    p["gear"]["weapon"] = g.slug
    pool = economy.item_pool(g)
    p.setdefault("durability", {})["weapon"] = max(0, pool - 3)
    p["inventory"]["repair_token"] = 1
    gold, xp = p["gold"], p["xp"]
    s = core.apply_choice(p, "forge")
    row = next(o for o in s.options if o.id == "token_weapon")
    assert "free" in row.hint
    core.apply_choice(p, "token_weapon")
    assert p["durability"]["weapon"] == pool
    assert p["gold"] == gold and p["xp"] == xp      # truly free
    assert "repair_token" not in p["inventory"]


def test_no_token_no_free_row():
    p = playing("rowless")
    g = economy.FORGE["pigsticker"]
    p["gear"]["weapon"] = g.slug
    p.setdefault("durability", {})["weapon"] = 1
    s = core.apply_choice(p, "forge")
    assert not any(o.id == "token_weapon" for o in s.options)
    assert any(o.id == "repair_weapon" for o in s.options)


def test_token_tip_no_longer_lies():
    tip = item_tip("repair_token")
    assert "Forge" in tip and "free" in tip.lower()
