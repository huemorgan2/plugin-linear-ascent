"""034 §2 — the bar is the bar.

XP behaves like energy below LEVEL_CAP: it fills to full and stops, and
buying the level empties it. `gain_xp` already capped engine-side gains;
what leaked was `guild_train` subtracting the need (carrying any surplus
into the next bar) and worldd paying raw `doc["xp"] += …`.

At LEVEL_CAP there is no bar — training is refused and XP is pure
currency for the bench and the field — so the cap deliberately lifts.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, social, state


def _trainee(name, level=3):
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", text=name)
    p["level"] = level
    p["xp"] = economy.xp_need(level)
    p["gold"] = 1_000_000
    return p


# ── the level empties the bar ───────────────────────────────────────────

def test_training_empties_the_bar():
    p = _trainee("emptied")
    social.guild_train(p)
    assert p["level"] == 4
    assert p["xp"] == 0


def test_a_bar_overfilled_by_the_world_does_not_carry():
    """The hole this closes: worldd used to pay a milestone's 1,500 into
    a bar that holds 758, and `xp -= need` carried the surplus into the
    next level for free."""
    p = _trainee("overfilled")
    p["xp"] = economy.xp_need(p["level"]) * 3        # as if worldd paid raw
    social.guild_train(p)
    assert p["xp"] == 0


def test_an_empty_bar_still_refuses_the_drill():
    p = _trainee("short")
    p["xp"] = economy.xp_need(p["level"]) - 1
    before = p["level"]
    s = social.guild_train(p)
    assert p["level"] == before
    assert any("Earn the bar first" in ln for ln in s.body_lines)


# ── nothing fills past full ─────────────────────────────────────────────

def test_a_full_bar_takes_nothing_more():
    p = _trainee("brimming")
    assert state.gain_xp(p, 10_000) == 0
    assert p["xp"] == economy.xp_need(p["level"])


def test_a_gain_is_clipped_to_what_fits():
    p = _trainee("nearly")
    need = economy.xp_need(p["level"])
    p["xp"] = need - 5
    assert state.gain_xp(p, 1_000) == 5
    assert p["xp"] == need


def test_the_level_cap_keeps_its_uncapped_pool():
    """No bar, no cap: at LEVEL_CAP the Guildhall refuses training and
    XP is the currency the bench and the spells spend. Capping here
    would strand a capped climber from the sinks XP exists for."""
    p = _trainee("veteran", level=economy.LEVEL_CAP)
    p["xp"] = 0
    assert state.xp_room(p) is None
    assert state.gain_xp(p, 10_000) == 10_000
    s = social.guild_train(p)
    assert p["level"] == economy.LEVEL_CAP
    assert any("the whole drill" in ln for ln in s.body_lines)


# ── the card says what the bar could not take ───────────────────────────

def test_a_clipped_share_is_named_on_the_kill_card():
    from plugin_linear_ascent.engine import combat
    lines = combat.kill_receipt_lines(
        {"xp": 758, "gold": 4_000, "shared": True, "xp_clipped": 742})
    assert any("742" in ln and "full bar" in ln for ln in lines)


def test_an_unclipped_share_says_nothing_about_bars():
    from plugin_linear_ascent.engine import combat
    lines = combat.kill_receipt_lines(
        {"xp": 758, "gold": 4_000, "shared": True})
    assert not any("full bar" in ln for ln in lines)
