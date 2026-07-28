"""022 phase 003 — presence: the grounds feel inhabited.

Roy's rule: HOT = acted on this floor within 3 minutes — the only tier
that counts as "with you"; CAMPED = within the hour — texture, never
company. The engine only READS `_world["presence"]` (worldd computes
it); these tests seed the injection and pin every surface: the gate
list, the floor card's torch block, the story deltas, the fight-round
refresh, the peek contract — and the silence of local dev.
"""

import asyncio
import time

from plugin_linear_ascent import runtime
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(name):
    return state.new_player(name)


def choose(p, oid="", text=""):
    return core.apply_choice(p, oid, text=text)


def create_character(p, race="human", clazz="warrior", name="Torchy"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, "", text=name)
    return p


def wire_presence(p, by_floor, torches=None):
    """Seed the doc the way worldd's injection does. Keys go through
    JSON on the wire, so string floor keys must be tolerated — seed
    them as strings ON PURPOSE."""
    w = p.setdefault("_world", {})
    w["presence"] = {
        "by_floor": {str(k): v for k, v in by_floor.items()},
        "torches": {str(k): v for k, v in (torches or {}).items()},
    }
    p["news_day"] = state.world_day()          # keep the Crier out of shot


def at_floor(p, n=1):
    choose(p, "gate")
    return choose(p, f"floor_{n}")


# ── the gate list ────────────────────────────────────────────────────────

def test_gate_list_carries_hot_and_camp_counts():
    p = create_character(fresh("gate-counts"))
    p["unlocked_floor"] = 3
    wire_presence(p, {2: {"hot": 3, "camped": 2}, 3: {"hot": 0, "camped": 1}})
    s = choose(p, "gate")
    hints = {o.id: o.hint for o in s.options}
    assert "3 hot · 2 camps" in hints["floor_2"]
    assert "hot" not in hints["floor_1"]       # empty floor stays quiet
    assert "1 camp" in hints["floor_3"]


# ── the floor card ───────────────────────────────────────────────────────

def test_floor_card_counts_blades_and_names_torches():
    p = create_character(fresh("torches"), name="Selfie")
    wire_presence(
        p, {1: {"hot": 2, "camped": 0}},
        {1: [{"name": "Selfie", "status": "hunting"},
             {"name": "Kettle", "status": "at the keep"}]})
    s = at_floor(p, 1)
    text = "\n".join(s.body_lines)
    assert "2 blades hot on this floor" in text
    assert "Kettle's torch — at the keep" in text
    assert "Selfie's torch" not in text        # your own torch is not news


def test_camped_only_floor_reads_as_embers():
    p = create_character(fresh("embers"))
    wire_presence(p, {1: {"hot": 0, "camped": 3}})
    s = at_floor(p, 1)
    assert any("3 camps within the hour" in ln for ln in s.body_lines)


# ── deltas are story ─────────────────────────────────────────────────────

def test_presence_deltas_fold_in_as_story():
    p = create_character(fresh("deltas"))
    wire_presence(p, {1: {"hot": 1, "camped": 0}})
    at_floor(p, 1)                              # watermark: hot = 1
    wire_presence(p, {1: {"hot": 3, "camped": 0}})
    s = core.current_scene(p)
    assert any("2 more torches" in ln for ln in s.body_lines)
    wire_presence(p, {1: {"hot": 2, "camped": 0}})
    s = core.current_scene(p)
    assert any("guttered out" in ln for ln in s.body_lines)
    # unchanged count: no delta line repeats
    s = core.current_scene(p)
    assert not any("torch" in ln and "since you last looked" in ln
                   for ln in s.body_lines)


# ── the fight refreshes it every round ───────────────────────────────────

def test_fight_rounds_refresh_the_number():
    p = create_character(fresh("fight-pres"))
    wire_presence(p, {1: {"hot": 2, "camped": 0}})
    fl = schema.get_floor(1)
    enc = next(e for e in fl.encounters if not e.traits)
    combat.start_encounter(p, fl, enc)
    p["hp"] = 10_000
    s = combat.resolve_fight_action(p, fl, "attack")
    if p["encounter"] is not None:
        assert any("2 blades hot" in ln for ln in s.body_lines)
        wire_presence(p, {1: {"hot": 3, "camped": 0}})
        s = combat.resolve_fight_action(p, fl, "attack")
        if p["encounter"] is not None:
            text = "\n".join(s.body_lines)
            assert "3 blades hot" in text
            assert "Another torch" in text


# ── local dev shows no ghosts ────────────────────────────────────────────

def test_local_dev_shows_no_ghosts():
    p = create_character(fresh("no-world"))
    s = choose(p, "gate")
    assert not any("hot" in (o.hint or "") for o in s.options)
    s = choose(p, "floor_1")
    assert not any("torch" in ln or "blades hot" in ln
                   for ln in s.body_lines)


# ── the peek contract (grade-2 liveness) ─────────────────────────────────

class _FakeRemote:
    def __init__(self):
        self.calls = 0

    async def presence(self, user):
        self.calls += 1
        return {"floor": 1, "hot": self.calls, "camped": 0}


def test_floor_presence_caches_and_refreshes_once_a_minute(monkeypatch):
    remote = _FakeRemote()
    monkeypatch.setitem(runtime.state, "remote", remote)
    monkeypatch.setitem(runtime.state, "presence", {})
    t = [1000.0]
    monkeypatch.setattr(runtime.time, "monotonic", lambda: t[0])
    # the hot path: two peeks inside the window = ONE world round trip
    assert asyncio.run(runtime.floor_presence("u")) == 1
    assert asyncio.run(runtime.floor_presence("u")) == 1
    assert remote.calls == 1
    # window expires → one refresh, monotonic with the served count
    t[0] += runtime.PRESENCE_REFRESH_S + 1
    assert asyncio.run(runtime.floor_presence("u")) == 2
    assert remote.calls == 2


def test_floor_presence_is_zero_without_a_world(monkeypatch):
    monkeypatch.setitem(runtime.state, "remote", None)
    monkeypatch.setitem(runtime.state, "presence", {})
    assert asyncio.run(runtime.floor_presence("u")) == 0


def test_failed_refresh_keeps_the_last_honest_number(monkeypatch):
    class Flaky:
        def __init__(self):
            self.calls = 0

        async def presence(self, user):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError("world down")
            return {"floor": 1, "hot": 4, "camped": 0}

    remote = Flaky()
    monkeypatch.setitem(runtime.state, "remote", remote)
    monkeypatch.setitem(runtime.state, "presence", {})
    t = [0.0]
    monkeypatch.setattr(runtime.time, "monotonic", lambda: t[0])
    assert asyncio.run(runtime.floor_presence("u")) == 4
    t[0] += runtime.PRESENCE_REFRESH_S + 1
    assert asyncio.run(runtime.floor_presence("u")) == 4
