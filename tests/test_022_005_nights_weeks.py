"""022/005 — nights & weeks: the night slot and the weekly strongbox.

One decision per night; one chosen reward per week. The tests pin the
enforcement (one action a night, one pick a week), the caps, the
kill-XP-only law for rested aether, and the fallback that never lets
an earned week rot to nothing.
"""

from plugin_linear_ascent import economy, unlocks
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, contracts, core, state, weekly


def fresh():
    return state.new_player("test-user-022-005")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def _advance_days(monkeypatch, n):
    day = state.world_day() + n
    monkeypatch.setattr(state, "world_day", lambda: day)
    return day


def _win_a_fight(p, floor_no=1, enc=None):
    fl = schema.get_floor(floor_no)
    combat.start_encounter(p, fl, enc or fl.encounters[0], "wilds")
    s = None
    for _ in range(6):
        if p["encounter"] is None:
            break
        p["encounter"]["hp"] = 1
        p["hp"] = state.max_hp(p)
        s = choose(p, "attack")
    assert p["encounter"] is None
    return s


# ── The ladder: below the level, only the NEXT line ──────────────────────

def test_level_5_sees_the_night_slot_only_as_a_next_line():
    p = create_character(fresh())
    p["level"] = economy.NIGHT_SLOT_LEVEL - 1
    s = choose(p, "lodge")
    assert not any(o.id.startswith("night_") for o in s.options)
    assert not any("Tonight" in ln for ln in s.body_lines)
    line = unlocks.next_line({"level": economy.NIGHT_SLOT_LEVEL - 1,
                              "unlocked_floor": 1})
    assert "night slot" in line


def test_level_9_vault_has_no_strongbox():
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL - 1
    s = choose(p, "vault")
    assert not any("strongbox" in ln for ln in s.body_lines)
    assert not any(o.id.startswith("pick_") for o in s.options)


# ── The night slot ───────────────────────────────────────────────────────

def _at_lodge(p):
    p["level"] = economy.NIGHT_SLOT_LEVEL
    return choose(p, "lodge")


def test_night_work_pays_at_dawn_and_only_once(monkeypatch):
    p = create_character(fresh())
    s = _at_lodge(p)
    assert any(o.id == "night_work" for o in s.options)
    choose(p, "night_work")
    gold = p["gold"]
    _advance_days(monkeypatch, 1)
    state.touch_daily(p)
    pay = economy.night_work_gold(max(1, p["unlocked_floor"]))
    assert p["gold"] == gold + pay
    assert p["night"] is None
    assert p["daily"]["night_yield"] == {"kind": "work", "gold": pay}
    state.touch_daily(p)                    # same day — no double shift
    assert p["gold"] == gold + pay


def test_switching_the_plan_still_resolves_one_action(monkeypatch):
    p = create_character(fresh())
    _at_lodge(p)
    choose(p, "night_rest")
    choose(p, "night_work")                 # changed their mind
    gold, rested = p["gold"], p.get("rested", 0)
    _advance_days(monkeypatch, 1)
    state.touch_daily(p)
    assert p["gold"] > gold                 # the shift paid
    assert p.get("rested", 0) == rested     # the rest never happened


def test_rest_banks_aether_and_the_pool_caps(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.NIGHT_SLOT_LEVEL
    per = economy.night_rest_aether(p["level"])
    cap = economy.rested_pool_cap(p["level"])
    for _ in range(economy.RESTED_POOL_CAP_NIGHTS + 2):
        choose(p, "town")
        choose(p, "lodge")
        choose(p, "night_rest")
        _advance_days(monkeypatch, 1)
        state.touch_daily(p)
    assert cap == economy.RESTED_POOL_CAP_NIGHTS * per
    assert p["rested"] == cap               # never over


def test_no_plan_no_yield(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.NIGHT_SLOT_LEVEL
    gold = p["gold"]
    _advance_days(monkeypatch, 1)
    state.touch_daily(p)
    assert p["gold"] == gold
    assert p["daily"]["night_yield"] is None


def test_work_scales_with_002_and_never_touches_the_cell():
    for fl in (1, 5, 10, 20):
        assert economy.night_work_gold(fl) == max(
            1, round(economy.NIGHT_WORK_INCOME_PCT * economy.daily_income(fl)))
    p = create_character(fresh())
    p["daily"]["day"] = state.world_day() - 1
    p["night"] = {"day": state.world_day() - 1, "choice": "work"}
    p["level"] = economy.NIGHT_SLOT_LEVEL
    state.touch_daily(p)
    assert p["daily"]["energy_cell"] is False   # the 1/day ceiling holds


# ── Rested aether pays on kills ONLY ─────────────────────────────────────

def test_rested_bonus_rides_a_kill_and_drains_the_pool():
    p = create_character(fresh())
    # floor-1 kill XP is 3–5, so the 25% bonus is exactly 1 point
    p["rested"] = 2
    xp = p["xp"]
    s = _win_a_fight(p)
    assert p["rested"] == 1                 # one point drawn, one left
    assert p["xp"] - xp == p["_ledger"][-1]["xp"]   # rode the same kill
    assert any("XP rested" in ln for ln in s.body_lines)


def test_rested_never_touches_a_contract_payout():
    p = create_character(fresh())
    p["level"] = economy.BOARD_LEVEL
    p["rested"] = 500
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.note_warden(p)
    xp = p["xp"]
    choose(p, "board")
    choose(p, f"claim_{job['id']}")
    assert p["xp"] == xp + job["xp"]        # flat — no rested rider
    assert p["rested"] == 500               # pool untouched


def test_empty_pool_pays_nothing():
    p = create_character(fresh())
    assert state.rested_bonus(p, 40) == 0


# ── The weekly strongbox ─────────────────────────────────────────────────

def test_thresholds_open_slots():
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL
    weekly.sync(p)
    assert weekly.slots(p) == 0
    for _ in range(2):
        weekly.note(p, "kills")
    assert weekly.slots(p) == 1
    for _ in range(2):
        weekly.note(p, "wardens")
    assert weekly.slots(p) == 2
    box = weekly.sync(p)
    p["unlocked_floor"] = box["floor0"] + 2     # floors gained count too
    assert weekly.points(p) == 6 and weekly.slots(p) == 3


def test_week_tick_opens_the_box_and_one_pick_closes_it(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL
    weekly.sync(p)
    for _ in range(4):
        weekly.note(p, "kills")
    _advance_days(monkeypatch, 7)
    choose(p, "town")
    s = choose(p, "vault")
    picks = [o.id for o in s.options if o.id.startswith("pick_")]
    assert set(picks) == {"pick_gold", "pick_aether"}   # 2 slots at 4 pts
    rested = p.get("rested", 0)
    s = choose(p, "pick_aether")
    assert p["rested"] == rested + economy.strongbox_aether(p["level"])
    assert weekly.sync(p)["pending"] is None
    assert not any(o.id.startswith("pick_") for o in s.options)


def test_pick_beyond_the_open_slots_is_refused(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL
    weekly.sync(p)
    for _ in range(2):
        weekly.note(p, "kills")             # 2 points — slot 1 only
    _advance_days(monkeypatch, 7)
    assert weekly.pick(p, "pick_relic") == ""
    assert weekly.sync(p)["pending"] is not None
    gold = p["gold"]
    assert weekly.pick(p, "pick_gold")
    assert p["gold"] == gold + economy.strongbox_gold(
        max(1, p["unlocked_floor"]))


def test_unpicked_weeks_fall_back_to_the_lowest_slot(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL
    weekly.sync(p)
    for _ in range(3):
        weekly.note(p, "kills")
    _advance_days(monkeypatch, 7)
    weekly.sync(p)                          # pending opens — never picked
    gold = p["gold"]
    _advance_days(monkeypatch, 7)
    weekly.sync(p)                          # fallback law fires
    assert p["gold"] == gold + economy.strongbox_gold(
        max(1, p["unlocked_floor"]))
    assert p.get("strongbox_note")


def test_an_idle_week_earns_nothing(monkeypatch):
    p = create_character(fresh())
    p["level"] = economy.STRONGBOX_LEVEL
    weekly.sync(p)
    _advance_days(monkeypatch, 7)
    gold = p["gold"]
    box = weekly.sync(p)
    assert box["pending"] is None and p["gold"] == gold
