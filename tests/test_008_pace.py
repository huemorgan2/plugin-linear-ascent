"""008 — combat pace & variance: derived wilds HP, specimens, stew,
lodge night heal, wardens untouched."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh():
    return state.new_player("test-user-008")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    choose(p, "begin")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def at_gate_town(p):
    choose(p, "gate")
    choose(p, "floor_1")
    return p


def force_specimen(monkeypatch, specimen):
    """rng_pick returns `specimen` for specimen tables, real roll else."""
    real = state.rng_pick

    def fake(p, table):
        if any(k in economy.SPECIMENS for _, k in table):
            return specimen
        return real(p, table)
    monkeypatch.setattr(state, "rng_pick", fake)


# ── Derived wilds HP ─────────────────────────────────────────────────────

def test_wilds_hp_derived_from_rounds_budget():
    # floor 1: at-level damage budget × 2.5 rounds — a quick kill
    atk, dfs, hp = economy.monster_stats(1)
    assert (atk, dfs) == (5, 3)               # ATK/DEF curve untouched
    assert hp == 18                            # was 37 pre-008
    # HP grows monotonically and the rounds budget caps at 7
    hps = [economy.monster_stats(f)[2] for f in range(1, 101)]
    assert all(b >= a for a, b in zip(hps, hps[1:]))
    assert economy.wilds_rounds(1) == 2.5
    assert economy.wilds_rounds(50) == 7.0


def test_warden_baseline_unchanged_by_008():
    baseline = {1: (14, 3, 70), 5: (28, 15, 162), 10: (47, 30, 276),
                15: (60, 45, 390), 30: (111, 90, 732), 50: (185, 150, 1782),
                75: (297, 225, 3736), 100: (445, 300, 6402)}
    for f, want in baseline.items():
        assert economy.warden_stats(f) == want


# ── Specimens ────────────────────────────────────────────────────────────

def test_specimen_table_is_expectation_neutral():
    total = sum(s["weight"] for s in economy.SPECIMENS.values())
    assert total == 100
    hp_e = sum(s["weight"] * s["hp"]
               for s in economy.SPECIMENS.values()) / total
    gold_e = sum(s["weight"] * s["gold"]
                 for s in economy.SPECIMENS.values()) / total
    assert abs(hp_e - 1) <= 0.05
    assert abs(gold_e - 1) <= 0.05


def test_alpha_specimen_visible_and_buffed(monkeypatch):
    force_specimen(monkeypatch, "alpha")
    p = at_gate_town(create_character(fresh()))
    s = choose(p, "hunt")
    e = p["encounter"]
    assert e["specimen"] == "alpha"
    fl = schema.get_floor(1)
    assert e["atk"] == round(fl.monster_atk * 1.2)
    assert e["hp"] == round(fl.monster_hp * 2.0)
    # the tag is on the opener — fighting an alpha is an informed choice
    assert any("alpha" in line for line in s.body_lines)


def test_alpha_kill_drops_extra_loot(monkeypatch):
    force_specimen(monkeypatch, "alpha")
    p = at_gate_town(create_character(fresh()))
    choose(p, "hunt")
    p["encounter"]["hp"] = 1                  # next hit kills
    s = choose(p, "attack")
    assert p["encounter"] is None
    assert any("alpha spoils" in line for line in s.body_lines)
    assert p["inventory"].get("medgel") or p["inventory"].get("luck_charm")


def test_runt_pays_less_gold(monkeypatch):
    force_specimen(monkeypatch, "runt")
    monkeypatch.setattr(state, "rng_jitter", lambda p, base, pct: base)
    p = at_gate_town(create_character(fresh()))
    choose(p, "hunt")
    p["encounter"]["hp"] = 1
    gold_before = p["gold"]
    choose(p, "attack")
    assert p["gold"] - gold_before == round(
        economy.gold_per_kill(1) * economy.SPECIMENS["runt"]["gold"])


def test_wardens_never_roll_specimens():
    p = at_gate_town(create_character(fresh()))
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, None, "warden")
    e = p["encounter"]
    assert e["specimen"] == "common"
    assert (e["atk"], e["def"], e["hp"]) == economy.warden_stats(1)


# ── Hunter's stew ────────────────────────────────────────────────────────

def test_stew_heals_five_for_two_gold():
    p = at_gate_town(create_character(fresh()))
    p["hp"] = state.max_hp(p) - 20
    s = core.current_scene(p)
    assert any(o.id == "stew" for o in s.options)
    gold, hp = p["gold"], p["hp"]
    choose(p, "stew")
    assert p["gold"] == gold - economy.STEW_PRICE
    assert p["hp"] == hp + economy.STEW_HEAL_HP


def test_stew_caps_at_max_hp_and_needs_gold():
    p = at_gate_town(create_character(fresh()))
    p["hp"] = state.max_hp(p) - 2
    choose(p, "stew")
    assert p["hp"] == state.max_hp(p)          # capped, not overhealed
    p["hp"] = 10
    p["gold"] = 1
    s = choose(p, "stew")
    assert p["hp"] == 10 and p["gold"] == 1    # refused
    assert s.shard_note


def test_stew_available_at_the_lodge():
    p = create_character(fresh())
    p["hp"] = 10
    choose(p, "lodge")
    s = core.current_scene(p)
    assert any(o.id == "stew" for o in s.options)
    gold = p["gold"]
    choose(p, "stew")
    assert p["hp"] == 10 + economy.STEW_HEAL_HP
    assert p["gold"] == gold - economy.STEW_PRICE


# ── Lodge night heal ─────────────────────────────────────────────────────

def test_lodge_night_heals_20_at_rollover():
    p = create_character(fresh())
    p["hp"] = 10
    p["lodged_until_day"] = state.world_day()  # slept inside last night
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == 10 + economy.LODGE_NIGHT_HEAL_HP


def test_rough_sleep_heals_nothing():
    p = create_character(fresh())
    p["hp"] = 10
    p["lodged_until_day"] = state.world_day() - 3
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == 10


def test_lodge_night_heal_caps_at_max():
    p = create_character(fresh())
    p["hp"] = state.max_hp(p) - 5
    p["lodged_until_day"] = state.world_day()
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == state.max_hp(p)


def test_lodge_copy_mentions_the_night_heal():
    p = create_character(fresh())
    s = choose(p, "lodge")
    assert any(str(economy.LODGE_NIGHT_HEAL_HP) in line
               for line in s.body_lines)
