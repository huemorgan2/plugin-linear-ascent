"""037 — active sleep, the fast clock.

Awake, ⚡ ticks every 45 minutes and wounds wait for dawn. Turning in
runs both clocks: the fields free at ×1.5 with a full HP bar in ~4 h,
the Lodge paid, palisaded, and exactly DOUBLE the waking pace with a
full bar in ~2 h. The sleep menu names both places and both rates; the
sleeping scene carries the per-class animation slug; waking banks
everything the clocks earned.
"""

import datetime as dt

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state, tips


def fresh(name):
    return state.new_player(name)


def _dry(p):
    """040: the Sleep door only shows on a dry bar — drain it first."""
    p["energy_val"] = 0.0
    p["energy_ts"] = state.now().isoformat()
    return p


def create_character(p, race="human", clazz="warrior", name="Nap"):
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, race)
    core.apply_choice(p, clazz)
    core.apply_choice(p, "", text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def _later(iso, minutes):
    return dt.datetime.fromisoformat(iso) + dt.timedelta(minutes=minutes)


# ── the constants ────────────────────────────────────────────────────────

def test_lodge_is_exactly_double_the_waking_pace():
    assert economy.SLEEP_ENERGY_MULT["lodge"] == 2.0
    assert economy.SLEEP_ENERGY_MULT["fields"] == 1.5
    assert economy.SLEEP_HP_FULL_MIN["lodge"] * 2 == \
        economy.SLEEP_HP_FULL_MIN["fields"]


# ── the energy clock ─────────────────────────────────────────────────────

def _metered(where):
    p = create_character(fresh(f"e-{where or 'awake'}"), name="Metered")
    p["energy_val"] = 0.0
    if where:
        p["sleeping"] = {"where": where, "since": p["energy_ts"],
                         "hp_ts": p["energy_ts"]}
    return p


def _energy_after(where, minutes):
    p = _metered(where)
    return state.energy_now(p, at=_later(p["energy_ts"], minutes))


def test_energy_regen_runs_faster_asleep():
    minutes = economy.ENERGY_REGEN_MIN * 4          # four waking points
    assert _energy_after("", minutes) == 4
    assert _energy_after("fields", minutes) == 6     # ×1.5
    assert _energy_after("lodge", minutes) == 8      # ×2 — double


def test_sleep_snapshot_keeps_the_fast_rate_off_waking_time():
    p = _metered("")
    t0 = dt.datetime.fromisoformat(p["energy_ts"])
    # 90 waking minutes, then lie down: the snapshot banks 2 points at
    # the waking rate before the multiplier starts.
    state.start_sleep(p, "lodge", at=t0 + dt.timedelta(minutes=90))
    assert p["energy_val"] == 2.0
    # 90 slept minutes more at ×2 = 4 points on top.
    at = t0 + dt.timedelta(minutes=180)
    assert state.energy_now(p, at=at) == 6
    state.wake_up(p, at=at)
    assert "sleeping" not in p
    assert p["energy_val"] == 6.0


# ── the HP clock ─────────────────────────────────────────────────────────

def test_hp_mends_only_while_sleeping():
    p = create_character(fresh("hp-awake"), name="Bruised")
    p["hp"] = 1
    assert state.apply_sleep_healing(p) == 0        # awake: dawn law holds
    assert p["hp"] == 1


def test_a_full_bar_mends_on_the_posted_schedule():
    for where in ("fields", "lodge"):
        p = create_character(fresh(f"hp-{where}"), name="Mender")
        p["hp"] = 1
        state.start_sleep(p, where)
        full = economy.SLEEP_HP_FULL_MIN[where]
        at = _later(p["sleeping"]["since"], full)
        state.apply_sleep_healing(p, at=at)
        assert p["hp"] == state.max_hp(p)


def test_healing_fractions_are_never_lost():
    p = create_character(fresh("hp-frac"), name="Patient")
    p["hp"] = 1
    state.start_sleep(p, "lodge")
    # far too short a nap for a whole point — the stamp must NOT move
    at = _later(p["sleeping"]["since"], 1)
    assert state.apply_sleep_healing(p, at=at) == 0
    assert p["sleeping"]["hp_ts"] == p["sleeping"]["since"]


# ── the menu ─────────────────────────────────────────────────────────────

def test_the_square_has_a_sleep_door_and_the_menu_names_both_rates():
    p = create_character(fresh("menu"), name="Drowsy")
    # 042: the door is always on the square — rested or dry.
    s = core.current_scene(p)
    assert any(o.id == "sleep_menu" for o in s.options)
    p["energy_val"] = 0.0
    p["energy_ts"] = state.now().isoformat()
    s = core.current_scene(p)
    assert any(o.id == "sleep_menu" for o in s.options)
    s = core.apply_choice(p, "sleep_menu")
    ids = [o.id for o in s.options]
    assert ids[:2] == ["sleep_lodge", "sleep_fields"]
    text = " ".join(s.body_lines)
    assert "×2" in text and "×1.5" in text          # energy speeds
    assert "2 hours" in text and "4 hours" in text  # HP speeds
    assert str(economy.ENERGY_REGEN_MIN) in text    # the waking baseline


def test_the_lodge_offers_turning_in():
    p = create_character(fresh("lodge-door"), name="Bunkward")
    core.apply_choice(p, "lodge")
    s = core.current_scene(p)
    assert any(o.id == "lie_down" for o in s.options)


# ── the flows ────────────────────────────────────────────────────────────

def test_sleeping_in_the_fields_is_free_and_animated():
    p = create_character(_dry(fresh("fields-flow")), clazz="archer", name="Rough")
    core.apply_choice(p, "sleep_menu")
    s = core.apply_choice(p, "sleep_fields")
    assert p["location"] == "sleeping"
    assert p["sleeping"]["where"] == "fields"
    assert s.fx == "sleep_fields_archer"            # per-class animation
    assert any(o.id == "wake" for o in s.options)
    s = core.apply_choice(p, "wake")
    assert "sleeping" not in p
    assert p["location"] == "town"


def test_the_lodge_bunk_is_paid_once_and_wakes_in_the_lodge():
    p = create_character(_dry(fresh("lodge-flow")), name="Paid")
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    p["gold"] = price
    core.apply_choice(p, "sleep_menu")
    s = core.apply_choice(p, "sleep_lodge")
    assert p["location"] == "sleeping"
    assert p["gold"] == 0                            # the bunk was bought
    assert p["lodged_until_day"] >= state.world_day() + 1
    assert s.fx == "sleep_lodge_warrior"
    s = core.apply_choice(p, "wake")
    assert p["location"] == "lodge"
    # already lodged: turning in again charges nothing
    core.apply_choice(p, "lie_down")
    assert p["location"] == "sleeping" and p["gold"] == 0


def test_a_broke_climber_is_turned_toward_the_fields():
    p = create_character(_dry(fresh("broke")), name="Skint")
    p["gold"] = 0
    core.apply_choice(p, "sleep_menu")
    s = core.apply_choice(p, "sleep_lodge")
    assert p["location"] == "sleep_menu"             # refused, not asleep
    assert "sleeping" not in p
    assert "fields" in s.shard_note


def test_dozing_applies_the_accrued_healing():
    p = create_character(_dry(fresh("doze")), name="Dozer")
    p["gold"] = 0
    core.apply_choice(p, "sleep_menu")
    core.apply_choice(p, "sleep_fields")
    p["hp"] = 1
    # backdate the stamp a full schedule and let "Sleep on" collect it
    early = _later(p["sleeping"]["hp_ts"],
                   -economy.SLEEP_HP_FULL_MIN["fields"])
    p["sleeping"]["hp_ts"] = early.isoformat()
    core.apply_choice(p, "doze")
    assert p["hp"] == state.max_hp(p)


# ── the tips ─────────────────────────────────────────────────────────────

def test_every_sleep_option_has_a_tip():
    for oid in ("sleep_menu", "sleep_lodge", "sleep_fields",
                "lie_down", "wake", "doze"):
        assert tips.option_tip(oid), f"no tip for {oid}"
