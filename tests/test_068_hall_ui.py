"""068: the faction hall, read at a glance — the chest sells its own
upgrade, leaving asks first in red, colours wear a swatch, the banner
flies the faction's ink, the works read as improvements, every hall row
has an [i], and an unentered week is a promotion, not an empty goal."""

from plugin_linear_ascent import colors, render
from plugin_linear_ascent.engine import core, tips
from plugin_linear_ascent.engine.scene import Scene

from tests.test_032_banner_hall import enter_hall, fx, member, the_hall


def _opts(s):
    return {o.id: o for o in s.options}


def _hall_with_chest_work(role="member", price=150, bal=140):
    h = the_hall(works=[
        {"kind": "chest", "tier": 2, "price": price,
         "label": "a bigger chest — 8 slots", "affordable": bal >= price}])
    h["coffer"]["bal"] = bal
    return member(role=role, hall_kw=h)


# ── 1. the chest buys itself ─────────────────────────────────────────────

def test_chest_offers_the_bigger_chest_locked_for_members():
    p = _hall_with_chest_work(role="member", price=150, bal=400)
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    row = _opts(s)["work_chest"]
    assert row.label == "Buy a bigger chest"
    assert row.locked and "the steward buys it" in row.hint
    assert "The works sell" not in " ".join(s.body_lines)


def test_steward_buys_the_bigger_chest_in_place():
    p = _hall_with_chest_work(role="steward", price=150, bal=400)
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    row = _opts(s)["work_chest"]
    assert not row.locked and row.hint == "8 slots · ◈ 150 of ◈ 400"
    s = core.apply_choice(p, "work_chest")
    assert fx(p, "hall_chest_up")
    assert s.eyebrow == "EMBER PACT · THE CHEST"          # stayed in the chest
    assert "8 slots" in s.headline                       # 4 → 8, optimistic
    assert "work_chest" not in _opts(s)                  # row consumed


def test_short_coffer_locks_the_chest_row_for_the_steward():
    p = _hall_with_chest_work(role="steward", price=150, bal=20)
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    row = _opts(s)["work_chest"]
    assert row.locked and "the coffer holds ◈ 20" in row.hint


# ── 2. leaving is red and asks ───────────────────────────────────────────

def test_hall_leave_is_red_and_asks_first():
    p = member()
    s = enter_hall(p)
    row = _opts(s)["guild_leave"]
    assert row.danger and row.label == "Leave the faction"
    s = core.apply_choice(p, "guild_leave")
    assert s.headline == "Leave Ember Pact?"
    body = " ".join(s.body_lines)
    assert "no longer be part of it" in body
    assert "no access to the faction hall" in body
    ids = [o.id for o in s.options]
    assert ids == ["leave_confirm", "hall_cancel", "town"]
    assert _opts(s)["leave_confirm"].danger
    assert _opts(s)["hall_cancel"].label == "Back to the faction hall"
    assert _opts(s)["town"].label.startswith("Don't leave the faction")
    assert not fx(p, "guild_leave")


def test_hall_leave_back_returns_to_the_table_unchanged():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "guild_leave")
    s = core.apply_choice(p, "hall_cancel")
    assert s.headline == "The Ember Pact table"
    assert p.get("guild") == "Ember Pact" and not fx(p, "guild_leave")
    assert "hall_leaving" not in p


def test_hall_leave_town_walks_out_without_leaving():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "guild_leave")
    core.apply_choice(p, "town")
    assert p["location"] == "town"
    assert p.get("guild") == "Ember Pact" and not fx(p, "guild_leave")
    assert "hall_leaving" not in p


def test_hall_leave_confirm_folds_the_colors():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "guild_leave")
    s = core.apply_choice(p, "leave_confirm")
    assert fx(p, "guild_leave") and p.get("guild") is None
    assert s.headline == "You fold your colors"


def test_danger_rides_beside_the_options_on_the_wire():
    p = member()
    s = enter_hall(p)
    d = s.to_dict()
    assert d["option_danger"] == ["guild_leave"]
    assert "danger" not in d["options"][0]
    back = Scene.from_dict(d)
    assert _opts(back)["guild_leave"].danger
    assert render.render_scene_fragment(s).count('class="opt danger"') == 1


# ── 3/4. colours: swatch and the way back ────────────────────────────────

def test_recolor_rows_wear_a_swatch_and_name_the_way_back():
    p = member(role="steward")
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    s = core.apply_choice(p, "recolor_banner")
    back = _opts(s)["hall_cancel"]
    assert back.label == "Back to the desk without changing color"
    html = render.render_scene_fragment(s)
    assert html.count('class="swatch"') == len(colors.FACTION_COLORS)
    for slug, (_nm, ink) in colors.FACTION_COLORS.items():
        assert f'style="background:{ink}"' in html
    s = core.apply_choice(p, "hall_cancel")
    assert s.eyebrow == "EMBER PACT · THE DESK"
    assert not fx(p, "faction_recolor")


# ── 5. the banner flies the faction's ink ────────────────────────────────

def test_hall_banner_is_painted_in_the_faction_ink():
    p = member()
    p["_world"]["faction"]["color"] = "ember-red"
    s = enter_hall(p)
    assert s.banner == "wolf_howl"
    assert s.banner_ink == colors.faction_ink("ember-red")
    html = render.render_scene_fragment(s)
    assert (f'class="banner" style="background-color:'
            f'{colors.faction_ink("ember-red")}') in html
    d = s.to_dict()
    assert Scene.from_dict(d).banner_ink == s.banner_ink


def test_unpainted_faction_keeps_the_violet():
    p = member()
    s = enter_hall(p)
    assert s.banner_ink == colors.faction_ink("")


# ── 6. the works read as improvements, no icon ───────────────────────────

def test_works_door_is_named_for_what_it_does_and_has_no_icon():
    p = member()
    s = enter_hall(p)
    row = _opts(s)["hall_works"]
    assert row.label == "Improve the faction's hall"
    assert "hall_works" not in s.option_art
    assert "hall_coffer" in s.option_art                  # the others keep art
    s = core.apply_choice(p, "hall_works")
    assert s.headline == "Improve the faction's hall"


# ── 7. every hall row has an [i] ─────────────────────────────────────────

def test_every_hall_row_carries_a_tip():
    p = member(role="steward", hall_kw=the_hall(works=[
        {"kind": "chest", "tier": 2, "price": 150,
         "label": "a bigger chest — 8 slots", "affordable": True}]))
    s = enter_hall(p)
    seen = {}
    seen.update({o.id: s for o in s.options})
    for door in ("hall_coffer", "hall_chest", "hall_board", "hall_bunks",
                 "hall_works", "hall_desk"):
        core.apply_choice(p, "hall_home")
        sub = core.apply_choice(p, door)
        seen.update({o.id: sub for o in sub.options})
    core.apply_choice(p, "hall_home")
    core.apply_choice(p, "hall_desk")
    sub = core.apply_choice(p, "recolor_banner")
    seen.update({o.id: sub for o in sub.options})
    core.apply_choice(p, "hall_cancel")
    core.apply_choice(p, "hall_home")
    sub = core.apply_choice(p, "promote")
    seen.update({o.id: sub for o in sub.options})
    missing = [oid for oid in seen if not tips.option_tip(oid)]
    assert not missing, missing


# ── 8. the unentered week is a promotion ─────────────────────────────────

def test_unentered_week_promotes_the_challenge_and_prices_the_door():
    p = member(role="steward")
    s = enter_hall(p)
    body = " ".join(s.body_lines)
    assert "▜ ENTER THIS WEEK'S CHALLENGE — CULL — win up to +26% HP" in body
    assert "your faction would need to fell 100 monsters together" in body
    assert "goal completed" not in body and "0%" not in body
    row = _opts(s)["enter_week"]
    assert row.label == "Pay to enter this week's challenge"
    assert row.hint == "◈ 10 of ◈ 140 in the coffer"
    s = core.apply_choice(p, "enter_week")
    body = " ".join(s.body_lines)
    assert "▜ THIS WEEK'S GOAL — CULL" in body
    assert "ENTER THIS WEEK'S CHALLENGE" not in body
    assert "goal completed" in body
    assert "enter_week" not in _opts(s)


def test_member_sees_the_promotion_and_the_nudge_not_the_door():
    p = member()
    s = enter_hall(p)
    body = " ".join(s.body_lines)
    assert "ENTER THIS WEEK'S CHALLENGE" in body
    assert "the steward signs the faction in" in body
    assert "enter_week" not in _opts(s)
