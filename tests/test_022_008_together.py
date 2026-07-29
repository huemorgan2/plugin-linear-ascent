"""022/008 — together, card side.

The flare (gating, cost, the startle round, the rescue's free
disengage), the answer option on the floor card, assist strikes (the
linked-log bonus, gold only, structurally no rested double-dip), and
the lodge's long fire. The server half (flare row races, the pay, the
kill-log ring, stew letters) lives in worldd's test_together.py.
"""

import datetime as dt

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh():
    return state.new_player("test-user-022-008")


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


def world(p, **kw):
    w = {"frontier": 3, "census": {"total": 4, "by_floor": {"1": 2}},
         "presence": {"by_floor": {}, "torches": {}},
         "flare": None, "recent_kills": [], "fire": []}
    w.update(kw)
    p["_world"] = w
    return p


def start_fight(p, floor_no=1):
    fl = schema.get_floor(floor_no)
    combat.start_encounter(p, fl, fl.encounters[0], "wilds")
    return fl


def effects(p, kind):
    return [e for e in p.get("_effects", []) if e["kind"] == kind]


# ── The flare, dying side ────────────────────────────────────────────────

def test_flare_option_only_below_the_quarter_bar_in_world_mode():
    p = world(create_character(fresh()))
    fl = start_fight(p)
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "flare" for o in s.options)
    p["hp"] = round(state.max_hp(p) * economy.FLARE_HP_PCT)
    s = combat.fight_scene(p, fl)
    assert any(o.id == "flare" for o in s.options)


def test_no_flare_without_a_world():
    p = create_character(fresh())
    fl = start_fight(p)
    p["hp"] = 1
    s = combat.fight_scene(p, fl)
    assert not any(o.id == "flare" for o in s.options)


def test_flare_burns_aether_emits_once_and_startles():
    p = world(create_character(fresh()))
    start_fight(p)
    p["hp"] = 1
    p["xp"] = economy.FLARE_AETHER + 3
    s = choose(p, "flare")
    assert "The flare goes up" in "\n".join(s.body_lines)
    assert p["xp"] == 3
    assert p["encounter"]["flared"] is True
    assert p["encounter"]["flare_guard"] is True
    fx = effects(p, "flare")
    assert len(fx) == 1 and fx[0]["floor"] == 1 and fx[0]["slug"]
    # once per fight: the option is gone and a re-tap is a no-op
    s = choose(p, "flare")
    assert p["xp"] == 3
    assert len(effects(p, "flare")) == 1


def test_flare_needs_the_aether():
    p = world(create_character(fresh()))
    start_fight(p)
    p["hp"] = 1
    p["xp"] = economy.FLARE_AETHER - 1
    s = choose(p, "flare")
    assert "don't have it to burn" in "\n".join(s.body_lines)
    assert not effects(p, "flare")


def test_flare_guard_halves_exactly_one_hit():
    p = world(create_character(fresh()))
    start_fight(p)
    e = p["encounter"]
    e["range"] = "close"
    e["flare_guard"] = True
    p["hp"] = 10_000
    hit = combat._monster_hit(p)
    while hit.get("dodged"):
        hit = combat._monster_hit(p)   # a dodged swing leaves the guard up
    assert "flare_guard" not in e      # consumed by the first landed swing
    if hit["raw"]:
        chip = max(1, -(-hit["raw"] // economy.CHIP_DIVISOR))
        expect = max(chip, hit["raw"] - state.dfs(p) // 2) // 2
        assert hit["dmg"] == expect


def test_answered_flare_grants_one_free_disengage():
    p = world(create_character(fresh()))
    fl = start_fight(p)
    e = p["encounter"]
    e["flared"] = True
    e["range"] = "close"
    e["profile"]["speed"] = economy.SPEED_FAST + 2   # flight would fail
    p["_world"]["flare"] = {"name": "Testa", "own": True,
                            "answered_by": "Brakka", "slug": e["id"]}
    s = combat.fight_scene(p, fl)
    assert "Brakka answered your flare" in "\n".join(s.body_lines)
    assert e["rescued"] is True
    s = choose(p, "run")
    assert s.headline == "You break away"
    assert p["encounter"] is None


# ── The answer, rescuer side ─────────────────────────────────────────────

def _at_gate_town(p, floor_no=1):
    p["location"] = "gate_town"
    p["floor"] = floor_no
    return p


def test_the_floor_card_shows_a_live_flare():
    p = world(create_character(fresh()),
              flare={"name": "Moss", "monster": "gully rat",
                     "slug": "", "answered_by": None, "own": False})
    _at_gate_town(p)
    s = core._gate_town_scene(p)
    assert "RED FLARE" in "\n".join(s.body_lines)
    assert any(o.id == "answer_flare" for o in s.options)


def test_own_or_answered_flares_offer_no_option():
    p = world(create_character(fresh()),
              flare={"name": "Testa", "monster": "gully rat",
                     "slug": "", "answered_by": None, "own": True})
    _at_gate_town(p)
    s = core._gate_town_scene(p)
    assert not any(o.id == "answer_flare" for o in s.options)
    p["_world"]["flare"] = {"name": "Moss", "monster": "gully rat",
                            "slug": "", "answered_by": "Kettle",
                            "own": False}
    s = core._gate_town_scene(p)
    assert not any(o.id == "answer_flare" for o in s.options)


def test_answering_starts_the_rescuer_round_on_the_same_prey():
    fl = schema.get_floor(1)
    slug = fl.encounters[0].id
    p = world(create_character(fresh()),
              flare={"name": "Moss", "monster": fl.encounters[0].name,
                     "slug": slug, "answered_by": None, "own": False})
    _at_gate_town(p)
    s = choose(p, "answer_flare")
    assert p["encounter"] is not None
    assert p["encounter"]["id"] == slug
    assert "rescuer's round" in s.support
    fx = effects(p, "flare_answer")
    assert len(fx) == 1 and fx[0]["floor"] == 1


# ── Assist strikes ───────────────────────────────────────────────────────

def _win(p, floor_no=1):
    fl = schema.get_floor(floor_no)
    combat.start_encounter(p, fl, fl.encounters[0], "wilds")
    s = None
    for _ in range(6):
        if p["encounter"] is None:
            break
        p["encounter"]["hp"] = 1
        p["hp"] = state.max_hp(p)
        s = choose(p, "attack")
    assert p["encounter"] is None
    return s


def test_assist_bonus_on_a_floor_mates_recent_kill():
    fl = schema.get_floor(1)
    slug = fl.encounters[0].id
    p = world(create_character(fresh()),
              recent_kills=[{"slug": slug, "by": "Brakka",
                             "ts": state.now().isoformat()}])
    s = _win(p)
    text = "\n".join(s.body_lines)
    assert "Brakka's blade bit first" in text
    row = next(r for r in p["_ledger"] if r["kind"] == "assist")
    kill = next(r for r in p["_ledger"] if r["kind"] == "kill")
    assert row["gold"] == max(1, round(kill["gold"]
                                       * economy.ASSIST_BONUS_PCT))
    assert row["xp"] == 0            # gold only — XP never rides assists
    assert effects(p, "kill_note")   # and the floor hears about OUR kill


def test_no_assist_from_own_stale_or_other_prey():
    fl = schema.get_floor(1)
    slug = fl.encounters[0].id
    old = (state.now()
           - dt.timedelta(minutes=economy.ASSIST_WINDOW_MIN + 2)).isoformat()
    p = world(create_character(fresh()),
              recent_kills=[
                  {"slug": slug, "by": "Testa",
                   "ts": state.now().isoformat()},          # own
                  {"slug": slug, "by": "Brakka", "ts": old},  # stale
                  {"slug": "not-this-one", "by": "Moss",
                   "ts": state.now().isoformat()}])          # other prey
    s = _win(p)
    assert "bit first" not in "\n".join(s.body_lines)
    assert not any(r["kind"] == "assist" for r in p["_ledger"])


def test_rested_pool_never_pays_on_the_assist():
    fl = schema.get_floor(1)
    slug = fl.encounters[0].id
    p = world(create_character(fresh()),
              recent_kills=[{"slug": slug, "by": "Brakka",
                             "ts": state.now().isoformat()}])
    p["rested"] = 2
    _win(p)
    # the pool paid against the KILL's XP (1–2 points) and nothing else;
    # the assist row carries zero XP so there is nothing to double-dip
    assert p["rested"] < 2
    assist = next(r for r in p["_ledger"] if r["kind"] == "assist")
    assert assist["xp"] == 0


# ── The long fire ────────────────────────────────────────────────────────

def test_the_long_fire_renders_and_speaks_canned_words():
    p = world(create_character(fresh()),
              fire=[{"name": "Brakka", "word": "Long day. Good fire."}])
    p["location"] = "lodge"
    s = core._lodge_scene(p)
    text = "\n".join(s.body_lines)
    assert "THE LONG FIRE" in text and "Brakka" in text
    assert any(o.id == "fire_word" for o in s.options)
    assert any(o.id == "fire_stew" for o in s.options)
    s = choose(p, "fire_word")
    fx = effects(p, "fire_word")
    assert len(fx) == 1 and fx[0]["word"] in economy.FIRE_WORDS


def test_the_stew_costs_gold_and_names_a_stranger():
    p = world(create_character(fresh()),
              fire=[{"name": "Brakka", "word": "Long day. Good fire."}])
    p["location"] = "lodge"
    p["gold"] = economy.FIRE_STEW_GOLD
    choose(p, "fire_stew")
    assert p["gold"] == 0
    fx = effects(p, "fire_stew")
    assert len(fx) == 1 and fx[0]["to_name"] == "Brakka"
    # broke: refused with the price named
    p["gold"] = 0
    s = choose(p, "fire_stew")
    assert "you don't carry" in s.shard_note
    assert len(effects(p, "fire_stew")) == 1


def test_no_stew_option_alone_at_the_fire():
    p = world(create_character(fresh()),
              fire=[{"name": "Testa", "word": "Long day. Good fire."}])
    p["location"] = "lodge"
    s = core._lodge_scene(p)
    assert not any(o.id == "fire_stew" for o in s.options)
