"""0.29.2 — collect badges: a (n) after a town door's name means
something inside is WAITING (a finished claim, a held letter, an open
strongbox, a night still unplanned) — never mere availability."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import contracts, core, state, weekly


def playing(name="Badgy", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    if world is not None:
        p["_world"] = world
    return p


def label(scene, oid):
    return next(o.label for o in scene.options if o.id == oid)


def test_board_badges_claimable_jobs_only():
    p = playing("board")
    p["level"] = economy.BOARD_LEVEL
    s = core.current_scene(p)
    assert label(s, "board") == "The contract board"   # nothing done yet
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.sync(p)["got"][job["id"]] = job["need"]
    s = core.current_scene(p)
    assert label(s, "board") == "The contract board (1)"
    core.apply_choice(p, "board")
    core.apply_choice(p, f"claim_{job['id']}")
    s = core.apply_choice(p, "back")
    assert label(s, "board") == "The contract board"   # paid — badge gone


def test_locked_board_never_badges():
    p = playing("board-locked")
    p["level"] = economy.BOARD_LEVEL - 1
    s = core.current_scene(p)
    assert "(" not in label(s, "board")


def test_lodge_badges_the_unplanned_night():
    p = playing("night")
    p["level"] = economy.NIGHT_SLOT_LEVEL
    s = core.current_scene(p)
    assert label(s, "lodge") == "The Lodge (1)"
    core.apply_choice(p, "lodge")
    core.apply_choice(p, "night_rest")
    s = core.apply_choice(p, "back")
    assert label(s, "lodge") == "The Lodge"            # planned — gone


def test_below_night_level_lodge_never_badges():
    p = playing("night-low")
    p["level"] = economy.NIGHT_SLOT_LEVEL - 1
    s = core.current_scene(p)
    assert label(s, "lodge") == "The Lodge"


def test_vault_badges_a_pending_strongbox():
    p = playing("boxer")
    p["level"] = economy.STRONGBOX_LEVEL
    s = core.current_scene(p)
    assert label(s, "vault") == "The Vault"
    p["strongbox"] = {"week": weekly.week_no(), "kills": 0, "wardens": 0,
                      "floor0": 1,
                      "pending": {"week": weekly.week_no() - 1, "slots": 2}}
    s = core.current_scene(p)
    assert label(s, "vault") == "The Vault (1)"


def test_relay_badges_held_letters():
    p = playing("post", world={"social": True, "inbox_count": 2})
    p["level"] = economy.RELAY_LEVEL
    s = core.current_scene(p)
    assert label(s, "relay") == "The Relay Office (2)"
    p["_world"]["inbox_count"] = 0
    s = core.current_scene(p)
    assert label(s, "relay") == "The Relay Office"
