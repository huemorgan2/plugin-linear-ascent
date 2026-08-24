"""0.29.2 — collect badges: a count on a town door means something inside
is WAITING (a finished claim, a held letter, a night still unplanned)
— never mere availability. Last week's reward (070) is a notice-board
box, not a Vault door chip.

027: the count is `Option.badge` now (a blue chip, not prose glued into the
label) and every count also gets a sentence on the notice board. The rules
about WHEN a door badges are unchanged, and the plain-text surface still
writes "(n)" after the label.
"""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import contracts, core, notices, state, weekly


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


def badge(scene, oid):
    return next(o.badge for o in scene.options if o.id == oid)


def test_board_badges_claimable_jobs_only():
    p = playing("board")
    p["level"] = economy.BOARD_LEVEL
    s = core.current_scene(p)
    assert badge(s, "board") == 0                      # nothing done yet
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.sync(p)["got"][job["id"]] = job["need"]
    s = core.current_scene(p)
    assert badge(s, "board") == 1
    assert label(s, "board") == "The contract board"    # the count is a chip
    core.apply_choice(p, "board")
    core.apply_choice(p, f"claim_{job['id']}")
    s = core.apply_choice(p, "back")
    assert badge(s, "board") == 0                      # paid — badge gone


def test_the_text_surface_still_says_the_count_in_words():
    """The agent and the plain-text fallback read a number, not a chip."""
    p = playing("board-text")
    p["level"] = economy.BOARD_LEVEL
    job = next(j for j in contracts.board_for(p) if j["kind"] == "warden")
    contracts.sync(p)["got"][job["id"]] = job["need"]
    text = core.current_scene(p).to_text()
    assert "The contract board (1)" in text


def test_locked_board_never_badges():
    p = playing("board-locked")
    p["level"] = economy.BOARD_LEVEL - 1
    s = core.current_scene(p)
    assert badge(s, "board") == 0


def test_lodge_badges_the_unplanned_night():
    p = playing("night")
    p["level"] = economy.NIGHT_SLOT_LEVEL
    s = core.current_scene(p)
    assert badge(s, "lodge") == 1
    core.apply_choice(p, "lodge")
    core.apply_choice(p, "night_rest")
    s = core.apply_choice(p, "back")
    assert badge(s, "lodge") == 0                      # planned — gone


def test_lodge_badge_explains_the_sleep_choice():
    p = playing("night-tip")
    p["level"] = economy.NIGHT_SLOT_LEVEL
    html = render.render_scene_fragment(core.current_scene(p))
    assert 'class="badge"' in html
    assert "chosen where to sleep" in html


def test_badge_tips_are_plain_english():
    lodge = notices.badge_tip("lodge")
    hall = notices.badge_tip("hall")
    assert "sleep" in lodge.lower()
    assert "challenge" in hall.lower()
    assert "aether" not in lodge.lower()


def test_below_night_level_lodge_never_badges():
    p = playing("night-low")
    p["level"] = economy.NIGHT_SLOT_LEVEL - 1
    s = core.current_scene(p)
    assert badge(s, "lodge") == 0


def test_vault_does_not_badge_a_pending_week_reward():
    """070: last week's reward lives on the notice board, not the Vault door."""
    p = playing("boxer")
    p["level"] = economy.STRONGBOX_LEVEL
    s = core.current_scene(p)
    assert badge(s, "vault") == 0
    p["strongbox"] = {"week": weekly.week_no(), "kills": 0, "wardens": 0,
                      "floor0": 1,
                      "pending": {"week": weekly.week_no() - 1, "slots": 2}}
    s = core.current_scene(p)
    assert badge(s, "vault") == 0
    assert any(n.get("kind") == "weekpick" for n in s.notices)


def test_relay_badges_held_letters():
    p = playing("post", world={"social": True, "inbox_count": 2})
    p["level"] = economy.RELAY_LEVEL
    s = core.current_scene(p)
    assert badge(s, "relay") == 2
    p["_world"]["inbox_count"] = 0
    s = core.current_scene(p)
    assert badge(s, "relay") == 0
