"""019 §2–§3 — every faction door is a row: founding shows locked below
level 4 (◈ 300, one banner per climber), the hall's "Join a banner" row
carries the world total and walks to the Community tab, and the pane
ships the CTA + inline join surfaces."""

from plugin_linear_ascent import pane
from plugin_linear_ascent.engine import core, social, state


def playing(name="Doors", world=None):
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


def hall_world(**kw):
    w = {"social": True,
         "factions": [{"name": "Ember Pact", "banner": "wolf_howl",
                       "join_fee": 25, "weekly_dues": 5, "members": 3}],
         "factions_total": 533,
         "faction_banners": ["wolf_howl", "iron_heart", "gear_sword"]}
    w.update(kw)
    return w


# ── the founding row ─────────────────────────────────────────────────────

def test_fee_is_three_hundred_in_the_engine():
    assert social.GUILD_FOUND_FEE == 300


def test_found_row_locked_below_rank_and_click_refuses():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, 3
    s = core.apply_choice(p, "guildhall")
    row = next(o for o in s.options if o.id == "found_guild")
    assert row.locked
    assert row.hint == "🔒 level 4 · ◈ 300"
    s = core.apply_choice(p, "found_guild")
    assert "founding_guild" not in p
    assert any("level 4" in ln for ln in s.body_lines)


def test_found_row_open_at_rank_and_broke_click_names_the_fee():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 100, 4
    s = core.apply_choice(p, "guildhall")
    row = next(o for o in s.options if o.id == "found_guild")
    assert not row.locked and "◈ 300" in row.hint
    s = core.apply_choice(p, "found_guild")
    assert "founding_guild" not in p
    assert any("◈ 300" in ln and "◈ 100" in ln for ln in s.body_lines)


def test_member_never_sees_the_found_row_and_a_forced_click_refuses():
    w = {"social": True, "faction": {
        "name": "Ember Pact", "banner": "wolf_howl", "join_fee": 25,
        "dues": 5, "store": 42, "role": "member", "members": [],
        "week": {}, "ledger": []}}
    p = playing("Member", world=w)
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    assert not any(o.id == "found_guild" for o in s.options)
    # the id isn't offered, so a forged click dies at the door; the
    # action-layer guard behind it names the table you'd have to leave
    s = social.guildhall_action(p, "found_guild")
    assert "founding_guild" not in p
    assert any("Ember Pact" in ln and "leave" in ln
               for ln in s.body_lines)


def test_local_dev_hall_shows_the_same_locked_row():
    p = playing("Dev", world={"social": True, "guilds": []})
    p["gold"], p["level"] = 600, 3
    s = core.apply_choice(p, "guildhall")
    row = next(o for o in s.options if o.id == "found_guild")
    assert row.locked and "level 4" in row.hint


# ── the "Join a banner" door ─────────────────────────────────────────────

def test_hall_ledger_row_counts_the_world_and_opens_the_directory():
    p = playing(world=hall_world())
    s = core.apply_choice(p, "guildhall")
    row = next(o for o in s.options if o.id == "hall_ledger")
    assert "533" in row.hint and "directory" in row.hint
    s = core.apply_choice(p, "hall_ledger")
    assert p["location"] == "guildhall"        # a sub-state, not a warp
    assert p["guild_dir"] == {"page": 0, "q": ""}
    assert s.headline == "Every banner that flies"


def test_no_ledger_row_when_no_banners_fly():
    p = playing("Empty", world=hall_world(factions=[], factions_total=0))
    s = core.apply_choice(p, "guildhall")
    assert not any(o.id == "hall_ledger" for o in s.options)
    assert any("first" in ln for ln in s.body_lines)


# ── the pane ships the surfaces ──────────────────────────────────────────

def test_pane_ships_the_cta_join_buttons_and_tab_walks():
    html = pane.render_pane()
    assert "renderCta" in html                 # the pitch to the unbannered
    assert "ASK TO JOIN" in html               # inline on the ledger rows
    assert "ctahall" in html                   # CTA → the Guildhall card
    # 042: hall_ledger is a real door now (the in-game directory) —
    # the pane must NOT hijack it into a tab switch.
    assert "hall_ledger" not in html
    assert "switchTab('community')" in html    # the topbar walk survives
