"""007 — forced multiplayer: shared frontier Warden + the Morning Crier."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import core, state


def playing(name="Sosa", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    core.apply_choice(p, "begin")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def warden_world(floor=1, hp=None, hp_max=None, strikers=None, **extra):
    hp_max = hp_max or economy.world_warden_hp(floor)
    return {"social": True, "frontier": floor,
            "warden": {"floor": floor, "hp": hp if hp is not None
                       else hp_max, "hp_max": hp_max,
                       "strikers": strikers or []},
            **extra}


# ── Shared frontier Warden ───────────────────────────────────────────────

def test_frontier_keep_is_the_shared_warden():
    p = playing(world=warden_world(1))
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "keep")
    assert p["location"] == "warden_keep"
    assert "whole world" in s.support
    assert any(o.id == "strike" for o in s.options)
    assert s.headline.startswith(schema.get_floor(1).warden_name)


def test_strike_pays_energy_and_emits_damage_effect():
    p = playing(world=warden_world(1))
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    e_before = state.energy_now(p)
    hp_before = p["_world"]["warden"]["hp"]
    s = core.apply_choice(p, "strike")
    assert state.energy_now(p) == e_before - economy.COST_WARDEN_ATTEMPT
    fx = [e for e in p["_effects"] if e["kind"] == "warden_strike"]
    assert fx and fx[0]["floor"] == 1 and fx[0]["damage"] >= 1
    # optimistic display: shown HP dropped by exactly the strike damage
    assert p["_world"]["warden"]["hp"] == hp_before - fx[0]["damage"]
    body = " ".join(s.body_lines)
    assert "your blow lands" in body
    # optimistic display: the striker sees their own name at once, never
    # "no blade has touched it yet" right after their blow landed
    assert p["name"] in body
    assert "no blade has touched it" not in body


def test_strike_without_energy_is_refused():
    p = playing(world=warden_world(1))
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    p["energy_val"] = 0.0
    p["energy_ts"] = state.now().isoformat()
    core.apply_choice(p, "strike")
    assert not any(e["kind"] == "warden_strike"
                   for e in p.get("_effects", []))


def test_below_frontier_keep_is_a_solo_echo_bout():
    p = playing(world=warden_world(3))
    p["unlocked_floor"] = 3
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    assert p["encounter"] and p["encounter"]["kind"] == "warden"
    assert p["location"] != "warden_keep"


def test_local_mode_keeps_the_solo_warden_fight():
    p = playing()                      # no _world — dev/local play
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    assert p["encounter"] and p["encounter"]["kind"] == "warden"


def test_stale_warden_scene_reports_the_fall():
    p = playing(world=warden_world(1))
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "keep")
    # the world moved on: frontier now 2, warden lives on floor 2
    p["_world"]["warden"]["floor"] = 2
    s = core.current_scene(p)
    assert "already fallen" in s.headline
    assert p["location"] == "gate_town"


# ── The Morning Crier ────────────────────────────────────────────────────

def crier_world(**kw):
    w = warden_world(2, hp=economy.world_warden_hp(2) // 2)
    w["census"] = {"total": 7, "by_floor": {"2": 3, "1": 4}}
    w["gossip"] = ["Mara fell to a marsh wolf on floor 2"]
    w.update(kw)
    return w


def test_crier_delivered_once_per_day():
    p = playing(world=crier_world())
    p["news_day"] = -1
    s = core.current_scene(p)
    assert "MORNING CRIER" in s.eyebrow
    assert s.event_kind == "news"
    assert any("7 climbers" in l for l in s.body_lines)
    assert any("3 at the frontier" in l for l in s.body_lines)
    assert any("marsh wolf" in l for l in s.body_lines)
    assert p["news_day"] == state.world_day()
    s2 = core.current_scene(p)
    assert "MORNING CRIER" not in s2.eyebrow


def test_crier_advice_respects_level_gates():
    w = crier_world()
    w["frontier"] = 20
    w["warden"] = None
    p = playing(world=w)
    p["news_day"] = -1
    s = core.current_scene(p)
    # level 1 vs floor_level_req(20)=10: advice must NOT send them there
    assert "level 10 legs" in s.shard_note
    assert "hunt floor 1" in s.shard_note.lower()


def test_crier_advice_points_at_wounded_warden():
    p = playing(world=crier_world())
    p["news_day"] = -1
    p["level"] = 5
    s = core.current_scene(p)
    assert "wounded" in s.shard_note


def test_crier_skipped_without_world_or_census():
    p = playing()                      # local play: no crier ever
    p["news_day"] = -1
    s = core.current_scene(p)
    assert "MORNING CRIER" not in s.eyebrow


def test_new_player_skips_todays_crier():
    p = playing(world=crier_world())
    assert p["news_day"] == state.world_day()
    s = core.current_scene(p)
    assert "MORNING CRIER" not in s.eyebrow


# ── Mandatory world (runtime) ────────────────────────────────────────────

def test_offline_scene_when_world_unreachable(monkeypatch):
    import asyncio

    from plugin_linear_ascent import runtime
    monkeypatch.delenv("ASCENT_DEV_LOCAL", raising=False)
    monkeypatch.setitem(runtime.state, "remote", None)
    monkeypatch.setitem(runtime.state, "ctx", None)   # enroll can't run
    monkeypatch.setitem(runtime.state, "enroll_ts", 0.0)
    s = asyncio.run(runtime.scene_for("owner"))
    assert "LIFT IS DOWN" in s.eyebrow
    assert any(o.id == "retry" for o in s.options)
    # a click on any option while offline stays honest too
    s2 = asyncio.run(runtime.act_for("owner", "retry"))
    assert "LIFT IS DOWN" in s2.eyebrow


def test_dev_flag_plays_local(monkeypatch):
    import asyncio

    from plugin_linear_ascent import runtime

    class FakeLocal:
        def __init__(self):
            self.docs = {}

        async def load(self, user):
            return self.docs.get(user) or state.new_player(user)

        async def save(self, user, doc, ledger):
            self.docs[user] = doc

    monkeypatch.setenv("ASCENT_DEV_LOCAL", "1")
    monkeypatch.setitem(runtime.state, "remote", None)
    monkeypatch.setitem(runtime.state, "local", FakeLocal())
    s = asyncio.run(runtime.scene_for("owner"))
    assert "LINEAR ASCENT" in s.eyebrow      # the intro card, not an outage
