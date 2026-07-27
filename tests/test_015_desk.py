"""015: the faction desk — founding gate, request flow, panel badges,
pane surface. Engine-side unit tests; worldd owns the DB half."""

from plugin_linear_ascent import pane
from plugin_linear_ascent.engine import core, social

from tests.test_faction_hall import fx, hall_world, member_world, playing


# ── Founding is a rank privilege ─────────────────────────────────────────

def test_no_founding_option_below_level_four():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, 3
    s = core.apply_choice(p, "guildhall")
    assert not any(o.id == "found_guild" for o in s.options)
    assert any("level 4+" in ln for ln in s.body_lines)


def test_founding_option_appears_at_level_four():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, social.FOUND_MIN_LEVEL
    s = core.apply_choice(p, "guildhall")
    assert any(o.id == "found_guild" for o in s.options)


def test_found_action_refused_below_level_even_if_forced():
    """A stale card / typed option can't dodge the gate."""
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, 1
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "found_guild")
    assert "founding_guild" not in p
    assert any("level 4+" in ln for ln in s.body_lines)


def test_local_dev_mode_gate_matches():
    p = playing(world={"social": True})       # no factions key → legacy
    p["gold"], p["level"] = 600, 1
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "found_guild")
    assert any("level 4+" in ln for ln in s.body_lines)


# ── The member panel wears the desk ──────────────────────────────────────

def test_panel_marks_founder_and_admin():
    w = member_world(role="steward")
    w["faction"]["members"][0]["founder"] = True
    p = playing(world=w)
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    body = " ".join(s.body_lines)
    assert "★ founder" in body
    # the non-founder steward reads as admin
    w2 = member_world(role="member")           # Brynn is the steward
    p2 = playing(world=w2)
    p2["guild"] = "Ember Pact"
    s2 = core.apply_choice(p2, "guildhall")
    assert "· admin" in " ".join(s2.body_lines)


def test_admin_sees_requests_waiting_at_the_desk():
    w = member_world(role="steward")
    w["faction"]["pending_requests"] = 2
    p = playing(world=w)
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    assert any("2 requests wait at the desk" in ln for ln in s.body_lines)
    # members don't get the admin line
    w2 = member_world(role="member")
    w2["faction"]["pending_requests"] = 2
    p2 = playing(world=w2)
    p2["guild"] = "Ember Pact"
    s2 = core.apply_choice(p2, "guildhall")
    assert not any("wait at the desk" in ln for ln in s2.body_lines)


def test_hall_points_at_the_full_ledger_when_deep():
    w = hall_world()
    w["factions"] = [dict(w["factions"][0], name=f"Banner {i}")
                     for i in range(8)]
    p = playing(world=w)
    s = core.apply_choice(p, "guildhall")
    assert any("full ledger" in ln for ln in s.body_lines)
    assert sum(o.id.startswith("join_") for o in s.options) == 5


# ── The pane carries the desk UI ─────────────────────────────────────────

def test_pane_ships_the_desk_surface():
    html = pane.render_pane()
    for marker in ("THE GUILDHALL", "FACTION DESK",       # game-tab bar
                   "/pane/factions", "/pane/faction/detail",
                   "/pane/faction/rename", 'data-desk="approve"',
                   'data-desk="reject"', 'data-desk="kick"',
                   'data-desk="promote"', "ledgerlist", "ADMIN", "FOUNDER"):
        assert marker in html, marker


def test_pane_has_no_popups():
    html = pane.render_pane()
    for banned in ("alert(", "confirm(", "prompt(", "window.open"):
        assert banned not in html, banned
