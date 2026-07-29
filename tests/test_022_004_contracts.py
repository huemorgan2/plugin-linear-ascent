"""022/004 — dawn & contracts: the dawn heal law and the contract board.

The dawn law's state mechanics live in test_008_pace (they replaced the
lodge-heal tests there); this file covers the Crier's dawn line, the
board's determinism, kill-credit off the real victory path, claiming,
expiry, and the sink check (paid healing survives the free dawn).
"""

from plugin_linear_ascent import economy, unlocks
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, contracts, core, state


def fresh():
    return state.new_player("test-user-022-004")


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


# ── The dawn line (noticed, never taught) ────────────────────────────────

def test_crier_reads_the_dawn_line_after_a_heal():
    p = create_character(fresh())
    p["daily"]["dawn_healed"] = True
    w = {"census": {"total": 3, "by_floor": {"1": 3}}, "frontier": 1}
    s = core._news_scene(p, w, state.world_day())
    assert any("dawn — your wounds have closed" in ln for ln in s.body_lines)
    p["daily"]["dawn_healed"] = False
    s2 = core._news_scene(p, w, state.world_day())
    assert not any("wounds have closed" in ln for ln in s2.body_lines)


def test_dawn_fires_exactly_once_per_world_day():
    p = create_character(fresh())
    p["hp"] = 6
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == state.max_hp(p)
    p["hp"] = 6
    state.touch_daily(p)          # same day again — nothing moves
    assert p["hp"] == 6


# ── Board determinism ────────────────────────────────────────────────────

def test_same_day_same_board_for_everyone():
    a = contracts.board(137, 20)
    b = contracts.board(137, 20)
    assert a == b
    assert len(a) == economy.BOARD_JOBS_PER_DAY
    assert {j["kind"] for j in a} == {"cull", "class", "warden"}


def test_different_days_turn_the_board_over():
    ids = {tuple(j["id"] for j in contracts.board(d, 20))
           for d in range(100, 110)}
    assert len(ids) > 1


def test_cull_names_a_real_creature_near_the_frontier():
    for day in range(200, 220):
        job = next(j for j in contracts.board(day, 15) if j["kind"] == "cull")
        assert 13 <= job["floor"] <= 15
        fl = schema.get_floor(job["floor"])
        assert job["enc"] in {e.id for e in fl.encounters}
        assert job["gold"] > 0 and job["xp"] > 0 and 3 <= job["need"] <= 5


def test_some_days_carry_a_repair_token():
    tokened = [d for d in range(300, 340)
               if any(j.get("token") for j in contracts.board(d, 10))]
    assert tokened, "no token job in 40 days — CONTRACT_TOKEN_CHANCE broken"


# ── Credit off the real victory path ─────────────────────────────────────

def _win_a_fight(p, floor_no, enc):
    fl = schema.get_floor(floor_no)
    combat.start_encounter(p, fl, enc, "wilds")
    # steel opens at range (017 §2.4) — the first swing may only close in
    for _ in range(6):
        if p["encounter"] is None:
            break
        p["encounter"]["hp"] = 1
        p["hp"] = state.max_hp(p)
        s = choose(p, "attack")
    assert p["encounter"] is None, "the one-HP target should have died"
    return s


def test_cull_credit_from_a_normal_hunt():
    p = create_character(fresh())
    job = next(j for j in contracts.board_for(p) if j["kind"] == "cull")
    fl = schema.get_floor(job["floor"])
    enc = next(e for e in fl.encounters if e.id == job["enc"])
    _win_a_fight(p, job["floor"], enc)
    assert contracts.got(p, job) == 1


def test_wrong_creature_earns_no_cull_credit():
    p = create_character(fresh())
    job = next(j for j in contracts.board_for(p) if j["kind"] == "cull")
    fl = schema.get_floor(job["floor"])
    other = next((e for e in fl.encounters if e.id != job["enc"]), None)
    if other is None:      # single-encounter floor — nothing to miss with
        return
    _win_a_fight(p, job["floor"], other)
    assert contracts.got(p, job) == 0


def test_class_kills_count_anywhere(monkeypatch):
    # pin a day whose weapon-class job asks for steel (the warrior's type)
    day = next(d for d in range(1, 400)
               if next(j for j in contracts.board(d, 1)
                       if j["kind"] == "class")["dtype"] == "melee")
    monkeypatch.setattr(state, "world_day", lambda: day)
    p = create_character(fresh())
    job = next(j for j in contracts.board_for(p) if j["kind"] == "class")
    fl = schema.get_floor(1)
    _win_a_fight(p, 1, fl.encounters[0])
    assert contracts.got(p, job) == 1


def test_warden_engagement_counts_at_the_open():
    p = create_character(fresh())
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, None, "warden")
    assert contracts.got(p, job) == 1
    p["encounter"] = None


def test_progress_never_overshoots_the_need():
    p = create_character(fresh())
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    for _ in range(5):
        contracts.note_warden(p)
    assert contracts.got(p, job) == job["need"] == 1


# ── The board scene: gate, claim, stamp, expiry ──────────────────────────

def test_board_locked_below_level_4():
    p = create_character(fresh())
    assert p["level"] < economy.BOARD_LEVEL
    s = choose(p, "board")
    assert s.eyebrow.endswith("THE SQUARE")
    assert s.shard_note and str(economy.BOARD_LEVEL) in s.shard_note
    row = next(o for o in s.options if o.id == "board")
    assert row.locked


def test_next_line_carries_the_board_before_level_4():
    line = unlocks.next_line({"level": 3, "unlocked_floor": 1})
    assert "contract board" in line


def test_claim_pays_gold_and_xp_minus_the_stamp():
    p = create_character(fresh())
    p["level"] = economy.BOARD_LEVEL
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.note_warden(p)
    gold, xp = p["gold"], p["xp"]
    choose(p, "board")
    s = choose(p, f"claim_{job['id']}")
    assert p["gold"] == gold + max(0, job["gold"] - economy.BOARD_PRICE)
    assert p["xp"] == xp + job["xp"]
    assert any("PAID" in ln for ln in s.body_lines)
    if job.get("token"):
        assert p["inventory"]["repair_token"] >= 1


def test_a_job_pays_only_once():
    p = create_character(fresh())
    p["level"] = economy.BOARD_LEVEL
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.note_warden(p)
    choose(p, "board")
    choose(p, f"claim_{job['id']}")
    gold = p["gold"]
    s = choose(p, f"claim_{job['id']}")
    assert p["gold"] == gold
    assert not any(o.id.startswith("claim_") for o in s.options)
    # a kill after payment doesn't reopen the job
    contracts.note_warden(p)
    assert job["id"] in contracts.sync(p)["claimed"]


def test_unfinished_work_expires_at_the_tick(monkeypatch):
    p = create_character(fresh())
    day = state.world_day()
    contracts.note_warden(p)
    assert contracts.sync(p)["got"]
    monkeypatch.setattr(state, "world_day", lambda: day + 1)
    assert contracts.sync(p)["got"] == {}
    assert contracts.sync(p)["claimed"] == []


# ── Sink check: paid healing survives the free dawn ──────────────────────

def test_mid_session_healing_still_costs_the_pre_phase_rates():
    assert economy.STEW_PRICE == 2 and economy.STEW_HEAL_HP == 5
    assert economy.HEALER_TENT_PER_FLOOR == 5
    p = create_character(fresh())
    p["hp"] = 6
    state.touch_daily(p)                    # mid-day: dawn does nothing
    assert p["hp"] == 6
    choose(p, "lodge")
    gold = p["gold"]
    choose(p, "stew")                       # the sink still routes gold
    assert p["hp"] == 6 + economy.STEW_HEAL_HP
    assert p["gold"] == gold - economy.STEW_PRICE
