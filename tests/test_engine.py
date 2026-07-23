"""Engine flows: creation gates, combat, death, vault, regen."""

import datetime as dt

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state


def fresh():
    return state.new_player("test-user")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def test_creation_flow_and_gates():
    p = fresh()
    s = core.current_scene(p)
    assert "shard" in s.headline.lower() or s.options
    # skipping ahead is refused with a steering hint
    s = choose(p, "gate")
    assert p["stage"] == "creation_race"
    assert s.shard_note                      # steering hint present
    choose(p, "elf")
    assert p["stage"] == "creation_class"
    choose(p, "sorcerer")
    assert p["stage"] == "creation_name"
    s = choose(p, text="x")                  # too short
    assert p["stage"] == "creation_name"
    s = choose(p, text="Nyx of the Vale")
    assert p["stage"] == "playing"
    assert "Nyx of the Vale" in s.headline


def test_numbered_fallback_resolves_positionally():
    p = fresh()
    core.current_scene(p)
    s = choose(p, "1")                       # first race option
    assert p["stage"] == "creation_class"


def test_wilds_fight_costs_energy_and_resolves():
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    e_before = state.energy_now(p)
    s = choose(p, "hunt")
    assert p["encounter"] is not None
    assert state.energy_now(p) == e_before - 1
    # fight until it ends, attacking every round
    for _ in range(60):
        if p["encounter"] is None:
            break
        s = choose(p, "attack")
    assert p["encounter"] is None            # somebody won


def test_death_consequences_and_death_save():
    p = create_character(fresh())
    p["daily"]["death_save"] = True          # spend the save first
    p["gold"] = 500
    p["gear"]["armor"] = "padded_jerkin"
    p["gear"]["shield"] = "scrapwood_buckler"
    p["gear"]["weapon"] = "pigsticker"
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999              # guaranteed lethal
    s = choose(p, "stand")
    assert p["gold"] == 0                    # carried gold gone
    assert p["gear"]["armor"] is None        # armor destroyed
    assert p["gear"]["shield"] is None       # shield destroyed
    assert p["gear"]["weapon"] == "pigsticker"   # weapon survives
    assert p["location"] == "town"
    assert s.event_kind == "death"


def test_death_save_fires_once_per_day():
    p = create_character(fresh())
    choose(p, "gate")
    choose(p, "floor_1")
    choose(p, "hunt")
    p["hp"] = 1
    p["encounter"]["atk"] = 999
    s = choose(p, "attack")
    assert p["hp"] == 1                      # saved at 1 HP
    assert p["daily"]["death_save"] is True
    assert s.event_kind == "death"
    assert p["gold"] > 0                     # nothing lost


def test_vault_interest_compounds_and_credits_once():
    p = create_character(fresh())
    p["bank"] = 1000
    p["bank_day"] = state.world_day() - 2
    choose(p, "vault")
    assert p["bank"] == round(1000 * 1.05 ** 2)   # 1102, credited on visit
    assert p["bank_day"] == state.world_day()
    # re-entering the vault the same day credits nothing more
    choose(p, "back")
    choose(p, "vault")
    assert p["bank"] == 1102


def test_forge_buy_equips_and_pawns_old():
    p = create_character(fresh())
    p["gold"] = 1500
    choose(p, "forge")
    choose(p, "buy_pigsticker")
    assert p["gear"]["weapon"] == "pigsticker"
    assert p["gold"] == 1250
    s = choose(p, "buy_pigsticker")          # buy again: old one to pack
    assert p["inventory"].get("pigsticker") == 1
    choose(p, "back")
    choose(p, "pawn")
    s = choose(p, "sell_pigsticker")
    assert p["gold"] == 1250 - 250 + 100     # 40% buyback
    assert "pigsticker" not in p["inventory"]


def test_energy_regen_is_lazy_and_timestamped():
    p = create_character(fresh())
    p["energy_val"] = 0.0
    p["energy_ts"] = (state.now() - dt.timedelta(minutes=90)).isoformat()
    assert state.energy_now(p) == 2          # 90min / 45min per point


def test_lodge_and_medlab_daily_caps():
    p = create_character(fresh())
    p["gold"] = 1000
    choose(p, "lodge")
    choose(p, "sleep")
    assert p["lodged_until_day"] == state.world_day() + 1
    choose(p, "back")
    choose(p, "medlab")
    choose(p, "buy_energy_cell")
    assert p["daily"]["energy_cell"] is True
    gold_after = p["gold"]
    s = choose(p, "buy_energy_cell")         # second cell refused
    assert p["gold"] == gold_after
    assert s.shard_note


def test_scene_is_idempotent():
    p = create_character(fresh())
    a = core.current_scene(p).to_dict()
    b = core.current_scene(p).to_dict()
    assert a["options"] == b["options"]
    assert p["encounter"] is None
