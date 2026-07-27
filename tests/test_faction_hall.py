"""010: the Guildhall is where faction life happens — join/found with the
purse numbers, the store panel, donations, the weekly entry, kicks. The
engine renders from w["faction"]/w["factions"] and emits effects; worldd
is the single writer."""

from plugin_linear_ascent.engine import core, state


def playing(name="Hally", world=None):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
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
         "faction_banners": ["wolf_howl", "iron_heart", "gear_sword",
                             "watch_owl", "web_star", "mecha_dragon",
                             "chained_sun", "storm_fist", "circuit_tree"]}
    w.update(kw)
    return w


def member_world(role="member", store=42, entered=False, arrears=False):
    return {"social": True, "faction": {
        "name": "Ember Pact", "banner": "wolf_howl",
        "join_fee": 25, "dues": 5, "store": store, "role": role,
        "members": [
            {"name": "Hally", "role": role, "level": 3, "arrears": False,
             "days": 3, "required": 4},
            {"name": "Brynn", "role": "member" if role == "steward"
             else "steward", "level": 5, "arrears": arrears,
             "days": 1, "required": 4},
        ],
        "week": {"kind": "cull", "target": 100, "entered": entered,
                 "progress": 12, "entry_cost": 10, "attended": 4,
                 "required": 8, "multiplier": 0.5, "base_pct": 0.15},
        "ledger": [], "last_week": "won the CULL — +26% hardier hides",
    }}


def fx(p, kind):
    return [e for e in p.get("_effects", []) if e["kind"] == kind]


# ── The hall list (no banner yet) ────────────────────────────────────────
# 015: joining is a REQUEST — no gold moves until an admin accepts it.

def test_hall_lists_fees_up_front_and_join_files_a_request():
    p = playing(world=hall_world())
    p["gold"], p["bank"] = 10, 40
    core.apply_choice(p, "guildhall")
    s = core.current_scene(p)
    join = next(o for o in s.options if o.id == "join_Ember Pact")
    assert join.label == "Ask to join Ember Pact"
    assert "join ◈ 25" in join.hint and "dues ◈ 5/wk" in join.hint
    s = core.apply_choice(p, "join_Ember Pact")
    # nothing charged, no colors yet — the admins decide at the desk
    assert (p["gold"], p["bank"]) == (10, 40)
    assert p.get("guild") is None
    assert not fx(p, "guild_join")
    assert fx(p, "faction_request")[0]["guild"] == "Ember Pact"
    assert any("admins" in ln for ln in s.body_lines)


def test_broke_climber_can_still_ask_fee_charged_on_accept():
    p = playing(world=hall_world())
    p["gold"], p["bank"] = 0, 0
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "join_Ember Pact")
    assert fx(p, "faction_request")
    assert any("charged if they take you" in ln for ln in s.body_lines)


def test_pending_request_shows_instead_of_the_join_option():
    p = playing(world=hall_world(faction_requested="Ember Pact"))
    core.apply_choice(p, "guildhall")
    s = core.current_scene(p)
    assert not any(o.id == "join_Ember Pact" for o in s.options)
    assert any("request waits at their desk" in ln for ln in s.body_lines)


# ── Founding: name → sigil → join fee → dues ─────────────────────────────

def test_founding_flow_sets_the_purse_numbers():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, 4          # 015: founding takes rank
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "found_guild")
    assert "Name your banner" in s.headline
    s = core.apply_choice(p, "", "Night Ledger")
    assert "sigil" in s.headline.lower()
    sig = next(o.id for o in s.options if o.id.startswith("sig_"))
    s = core.apply_choice(p, sig)
    assert "join fee" in s.headline.lower()
    s = core.apply_choice(p, "", "25")
    assert "dues" in s.headline.lower()
    s = core.apply_choice(p, "", "5")
    assert p["guild"] == "Night Ledger"
    assert p["gold"] == 100
    e = fx(p, "guild_found")[0]
    assert e["guild"] == "Night Ledger"
    assert e["banner"] == sig.removeprefix("sig_")
    assert e["join_fee"] == 25 and e["weekly_dues"] == 5
    assert "founding_guild" not in p


def test_founding_validates_the_numbers_and_can_cancel():
    p = playing(world=hall_world())
    p["gold"], p["level"] = 600, 4
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "found_guild")
    core.apply_choice(p, "", "Night Ledger")
    s = core.current_scene(p)
    sig = next(o.id for o in s.options if o.id.startswith("sig_"))
    core.apply_choice(p, sig)
    s = core.apply_choice(p, "", "9999")          # fee over the cap
    assert "0 to 500" in " ".join(s.body_lines)
    s = core.apply_choice(p, "cancel_found")
    assert "founding_guild" not in p and p.get("guild") is None
    assert p["gold"] == 600                        # nothing charged


# ── The member panel ─────────────────────────────────────────────────────

def test_member_panel_shows_store_pips_and_arrears():
    p = playing(world=member_world(arrears=True))
    p["guild"] = "Ember Pact"
    s = core.apply_choice(p, "guildhall")
    body = " ".join(s.body_lines)
    assert "STORE ◈ 42" in body and "dues ◈ 5/week" in body
    assert "▪▪▪▫▫▫▫ 3/4" in body                  # attendance pips
    assert "▲ arrears" in body
    assert "the Ascent demands a CULL" in body
    ids = {o.id for o in s.options}
    assert "donate" in ids and "guild_leave" in ids
    # member, not steward: no entry, no kick
    assert "enter_week" not in ids and "kick" not in ids


def test_donation_is_typed_carried_gold_and_emits_effect():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    p["gold"] = 80
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "donate")
    assert "How much" in s.headline
    s = core.apply_choice(p, "", "30")
    assert p["gold"] == 50
    assert fx(p, "faction_donate")[0]["amount"] == 30
    assert any("◈ 72 now" in ln for ln in s.body_lines)   # 42 + 30
    # over-donation bounces, nothing emitted twice
    core.apply_choice(p, "donate")
    s = core.apply_choice(p, "", "999")
    assert p["gold"] == 50 and len(fx(p, "faction_donate")) == 1


def test_steward_enters_the_week_from_the_store():
    p = playing(world=member_world(role="steward", store=42))
    p["guild"] = "Ember Pact"
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "enter_week")
    assert fx(p, "faction_enter")
    body = " ".join(s.body_lines)
    assert "the CULL is on" in body
    assert "entered" in body                      # optimistic panel update
    # already in the lists — a second click is refused
    s = core.apply_choice(p, "enter_week")
    assert len(fx(p, "faction_enter")) == 1


def test_entry_refused_with_shortfall_when_store_is_short():
    p = playing(world=member_world(role="steward", store=3))
    p["guild"] = "Ember Pact"
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "enter_week")
    assert not fx(p, "faction_enter")
    assert any("◈ 7 short" in ln for ln in s.body_lines)  # 10 − 3


def test_steward_kick_picks_from_the_member_list():
    p = playing(world=member_world(role="steward"))
    p["guild"] = "Ember Pact"
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "kick")
    assert "Who leaves the table" in s.headline
    ids = {o.id for o in s.options}
    assert "kick_Brynn" in ids and "kick_Hally" not in ids  # never self
    s = core.apply_choice(p, "kick_Brynn")
    assert fx(p, "faction_kick")[0]["name"] == "Brynn"
    assert not any("Brynn" in ln and "▪" in ln for ln in s.body_lines)


def test_leave_emits_and_folds_the_colors():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "guild_leave")
    assert p.get("guild") is None
    assert fx(p, "guild_leave")
