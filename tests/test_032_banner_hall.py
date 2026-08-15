"""032: the banner hall — a faction's home behind the Guildhall.

The engine renders THE HALL and its six areas from worldd's injected
fac["hall"] and w["hall_board"], emits the six hall effects plus the
existing faction/armory ones, and degrades to the 010 Guildhall panel
when the keys are absent (an older worldd) — test_faction_hall.py keeps
covering that degraded path unchanged."""

from plugin_linear_ascent import economy
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


def forge_slug():
    """A real, priced piece — donatable to the chest."""
    return next(k for k, g in sorted(economy.FORGE.items())
                if g.price > 0)


def hall_board():
    return {"week": 12, "kind": "cull",
            "standings": [
                {"name": "Ember Pact", "banner": "wolf_howl",
                 "progress": 12, "target": 100},
                {"name": "Night Ledger", "banner": "watch_owl",
                 "progress": 80, "target": 100}],
            "banners": [
                {"name": "Ember Pact", "banner": "wolf_howl", "wins": 3,
                 "members": 2, "room_tier": 2},
                {"name": "Night Ledger", "banner": "watch_owl", "wins": 1,
                 "members": 4, "room_tier": 1}]}


def the_hall(**kw):
    h = {"room_tier": 2, "room_name": "a hall of your own",
         "coffer": {"bal": 140, "cap": 600, "tier": 2},
         "chest": {"used": 1, "cap": 4, "tier": 1},
         "beds": {"count": 2, "tonight": []},
         "notes": [{"day": 3, "player": "Brynn",
                    "line": "web spinners eat arrows"}],
         "works": [
             {"kind": "room", "tier": 3, "price": 2000,
              "label": "buy up the hall — the long hall",
              "affordable": False},
             {"kind": "bed", "tier": 3, "price": 250,
              "label": "a bed for the bunks — 3 of 6",
              "affordable": True}]}
    h.update(kw)
    return h


def member_world(role="member", entered=False, hall_kw=None, **wkw):
    slug = forge_slug()
    g = economy.FORGE[slug]
    w = {"social": True,
         "armory": [{"id": 7, "slug": slug, "name": g.name,
                     "slot": g.slot, "donor": "Brynn", "frac": 1.0}],
         "armory_cap": 4,
         "armory_took_today": False,
         "hall_board": hall_board(),
         "faction": {
             "name": "Ember Pact", "banner": "wolf_howl",
             "join_fee": 25, "dues": 5, "store": 140, "role": role,
             "pending_requests": 0,
             "members": [
                 {"name": "Hally", "role": role, "level": 3,
                  "arrears": False, "days": 3, "required": 4},
                 {"name": "Brynn",
                  "role": "member" if role == "steward" else "steward",
                  "level": 5, "arrears": False, "days": 1, "required": 4},
             ],
             "week": {"kind": "cull", "target": 100, "entered": entered,
                      "progress": 12, "entry_cost": 10, "attended": 4,
                      "required": 8, "multiplier": 0.5, "base_pct": 0.15},
             "ledger": [], "last_week": "",
             "hall": the_hall(**(hall_kw or {}))}}
    w.update(wkw)
    return w


def seeker_world():
    """No banner of your own — the civic floor and the public pages."""
    return {"social": True,
            "factions": [{"name": "Ember Pact", "banner": "wolf_howl",
                          "join_fee": 25, "weekly_dues": 5, "members": 2}],
            "factions_total": 2,
            "faction_banners": ["wolf_howl", "watch_owl"],
            "hall_board": hall_board()}


def member(role="member", **kw):
    p = playing(world=member_world(role=role, **kw))
    p["guild"] = "Ember Pact"
    return p


def fx(p, kind):
    return [e for e in p.get("_effects", []) if e["kind"] == kind]


def enter_hall(p):
    core.apply_choice(p, "hall")
    return core.current_scene(p)


# ── The door on the square ───────────────────────────────────────────────

def test_square_grows_your_hall_door_for_members():
    p = member()
    s = core.apply_choice(p, "town")
    door = next(o for o in s.options if o.id == "hall")
    assert door.label == "YOUR FACTION'S HALL"
    assert door.hint == "Ember Pact"


def test_no_hall_key_means_no_door_old_worldd():
    p = member()
    del p["_world"]["faction"]["hall"]
    s = core.apply_choice(p, "town")
    assert not any(o.id == "hall" for o in s.options)


def test_steward_gets_the_unentered_week_notice_on_the_square():
    p = member(role="steward")
    s = core.apply_choice(p, "town")
    texts = [n["text"] for n in s.notices]
    assert "the week stands unentered at your hall" in texts
    # the badge projection agrees with the sentence
    door = next(o for o in s.options if o.id == "hall")
    assert door.badge == 1


def test_members_and_entered_weeks_get_no_notice():
    p = member(role="member")
    s = core.apply_choice(p, "town")
    assert not any("unentered" in n["text"] for n in s.notices)
    p2 = member(role="steward", entered=True)
    s2 = core.apply_choice(p2, "town")
    assert not any("unentered" in n["text"] for n in s2.notices)


# ── The hall home ────────────────────────────────────────────────────────

def test_hall_home_wears_the_colors_and_the_room():
    p = member()
    s = enter_hall(p)
    assert s.eyebrow == "EMBER PACT · A HALL OF YOUR OWN"
    assert s.banner == "wolf_howl"
    assert s.strip == {"art": "hall_room_2", "text": "a hall of your own"}
    ids = {o.id for o in s.options}
    for door in ("hall_coffer", "hall_chest", "hall_board", "hall_bunks",
                 "hall_works"):
        assert door in ids
    assert "hall_desk" not in ids                 # members have no desk
    body = " ".join(s.body_lines)
    assert "THIS WEEK THE ASCENT DEMANDS A CULL" in body
    assert "the steward signs the faction in" in body
    assert "DAY 3 · Brynn — web spinners eat arrows" in body
    assert "▪▪▪▫▫▫▫ 3/4" in body                  # the roster still reads
    assert "guild_leave" in ids and "town" in ids


def test_entered_week_shows_progress_pips_and_projection():
    p = member(entered=True)
    s = enter_hall(p)
    body = " ".join(s.body_lines)
    assert "THE WEEK — CULL · 12 / 100" in body
    assert "▪▪▪▪▫▫▫▫ 4/8" in body                 # attendance
    assert "on pace for ×0.50" in body
    assert not any(o.id == "enter_week" for o in s.options)


def test_steward_enters_the_week_from_the_coffer():
    p = member(role="steward")
    s = enter_hall(p)
    row = next(o for o in s.options if o.id == "enter_week")
    assert "◈ 10 from the coffer (◈ 140)" in row.hint
    s = core.apply_choice(p, "enter_week")
    assert fx(p, "faction_enter")
    assert p["_world"]["faction"]["hall"]["coffer"]["bal"] == 130
    assert "the CULL is on" in " ".join(s.body_lines)
    core.apply_choice(p, "enter_week")            # stray re-click
    assert len(fx(p, "faction_enter")) == 1


def test_entry_shortfall_reads_from_the_coffer():
    p = member(role="steward", hall_kw={"coffer": {"bal": 3, "cap": 600}})
    enter_hall(p)
    s = core.apply_choice(p, "enter_week")
    assert not fx(p, "faction_enter")
    assert any("the coffer holds ◈ 3 — ◈ 7 short" in ln
               for ln in s.body_lines)


# ── THE COFFER ───────────────────────────────────────────────────────────

def test_coffer_shows_bal_of_cap_with_presets():
    p = member()
    enter_hall(p)
    s = core.apply_choice(p, "hall_coffer")
    assert s.eyebrow == "EMBER PACT · THE COFFER"
    assert any("◈ 140 of ◈ 600" in ln for ln in s.body_lines)
    ids = {o.id for o in s.options}
    assert {"donate_10", "donate_50", "donate_100",
            "donate_custom", "hall_home"} <= ids


def test_preset_donation_moves_carried_gold():
    p = member()
    p["gold"] = 80
    enter_hall(p)
    core.apply_choice(p, "hall_coffer")
    s = core.apply_choice(p, "donate_50")
    assert p["gold"] == 30
    assert fx(p, "faction_donate")[0]["amount"] == 50
    assert any("◈ 190 of ◈ 600" in ln for ln in s.body_lines)


def test_custom_donation_is_an_inline_ask():
    p = member()
    p["gold"] = 80
    enter_hall(p)
    core.apply_choice(p, "hall_coffer")
    s = core.apply_choice(p, "donate_custom")
    assert s.ask and s.ask["kind"] == "number"    # 027: no popups
    s = core.apply_choice(p, "", "25")
    assert p["gold"] == 55
    assert fx(p, "faction_donate")[0]["amount"] == 25


def test_donation_clips_at_the_brim():
    p = member(hall_kw={"coffer": {"bal": 590, "cap": 600}})
    p["gold"] = 80
    enter_hall(p)
    core.apply_choice(p, "hall_coffer")
    s = core.apply_choice(p, "donate_50")
    assert fx(p, "faction_donate")[0]["amount"] == 10
    assert p["gold"] == 70                        # only the clip charged
    assert any("takes ◈ 10 of your ◈ 50" in ln for ln in s.body_lines)


def test_full_coffer_refuses_in_words():
    p = member(hall_kw={"coffer": {"bal": 600, "cap": 600}})
    p["gold"] = 80
    enter_hall(p)
    core.apply_choice(p, "hall_coffer")
    s = core.apply_choice(p, "donate_10")
    assert not fx(p, "faction_donate")
    assert any("The coffer is full" in ln for ln in s.body_lines)


# ── THE CHEST ────────────────────────────────────────────────────────────

def test_chest_is_a_card_wall_with_visible_slots():
    p = member()
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    assert s.eyebrow == "EMBER PACT · THE CHEST"
    assert s.grid is True                         # 031 §14 card wall
    take = next(o for o in s.options if o.id == "take_arm_7")
    assert "from Brynn" in take.hint
    assert s.option_art["take_arm_7"] == forge_slug()
    assert any("3 open sockets of 4" in ln for ln in s.body_lines)


def test_chest_take_emits_and_locks_the_day():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "hall_chest")
    s = core.apply_choice(p, "take_arm_7")
    assert fx(p, "armory_take")[0]["item_id"] == 7
    assert "Brynn put it there" in " ".join(s.body_lines)
    assert p["_world"]["armory_took_today"] is True


def test_chest_put_flow_rides_the_pack():
    slug = forge_slug()
    p = member()
    p["inventory"][slug] = 1
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    assert any(o.id == "chest_put" for o in s.options)
    s = core.apply_choice(p, "chest_put")
    row = next(o for o in s.options if o.id == f"put_{slug}")
    assert "no coin" in row.hint                  # 017: the EV law
    s = core.apply_choice(p, f"put_{slug}")
    e = fx(p, "armory_deposit")[0]
    assert e["slug"] == slug
    assert p["inventory"].get(slug) is None
    assert "your name on the socket" in " ".join(s.body_lines)


def test_chest_full_locks_the_put_row():
    slug = forge_slug()
    p = member(hall_kw={"chest": {"used": 1, "cap": 1}})
    p["inventory"][slug] = 1
    enter_hall(p)
    s = core.apply_choice(p, "hall_chest")
    row = next(o for o in s.options if o.id == "chest_put")
    assert row.locked and "every socket filled" in row.hint


# ── THE BULLETIN BOARD ───────────────────────────────────────────────────

def test_board_lists_notes_and_takes_a_line():
    p = member()
    enter_hall(p)
    s = core.apply_choice(p, "hall_board")
    assert s.eyebrow == "EMBER PACT · THE BULLETIN BOARD"
    assert any("DAY 3 · Brynn — web spinners eat arrows" in ln
               for ln in s.body_lines)
    s = core.apply_choice(p, "write_note")
    assert s.ask and s.ask["max"] == 64
    s = core.apply_choice(p, "", "x" * 80)
    e = fx(p, "hall_note")[0]
    assert len(e["line"]) == 64                   # clipped, never refused
    assert any("your line is pinned" in ln for ln in s.body_lines)


def test_writing_again_replaces_todays_line():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "hall_board")
    core.apply_choice(p, "write_note")
    core.apply_choice(p, "", "first word")
    core.apply_choice(p, "hall_board")
    core.apply_choice(p, "write_note")
    core.apply_choice(p, "", "second word")
    notes = p["_world"]["faction"]["hall"]["notes"]
    mine = [n for n in notes if n["player"] == "Hally"]
    assert len(mine) == 1 and mine[0]["line"] == "second word"


# ── THE BUNKS ────────────────────────────────────────────────────────────

def test_bed_claim_is_free_and_sets_the_lodge_flag():
    p = member()
    enter_hall(p)
    core.apply_choice(p, "hall_bunks")
    gold = p["gold"]
    s = core.apply_choice(p, "bed_claim")
    assert fx(p, "hall_bed_claim")
    assert p["gold"] == gold                      # free — the dues bought it
    assert p["lodged_until_day"] == state.world_day() + 1
    assert "nothing finds you" in " ".join(s.body_lines)
    # one claim a night — the second is refused in words
    core.apply_choice(p, "hall_bunks")
    s = core.apply_choice(p, "bed_claim")
    assert len(fx(p, "hall_bed_claim")) == 1
    assert any("one claim a night" in ln for ln in s.body_lines)


def test_full_bunks_point_at_the_lodge():
    p = member(hall_kw={"beds": {"count": 2,
                                 "tonight": ["Brynn", "Ald"]}})
    enter_hall(p)
    core.apply_choice(p, "hall_bunks")
    s = core.apply_choice(p, "bed_claim")
    assert not fx(p, "hall_bed_claim")
    assert any("The Lodge still sells walls" in ln for ln in s.body_lines)


def test_bunks_locked_below_a_hall_of_your_own():
    p = member(hall_kw={"room_tier": 1})
    s = enter_hall(p)
    row = next(o for o in s.options if o.id == "hall_bunks")
    assert row.locked and "🔒" in row.hint
    s = core.apply_choice(p, "hall_bunks")        # 019: asking why works
    assert p.get("hall_area") is None
    assert any("a hall of your own" in ln for ln in s.body_lines)


# ── THE WORKS ────────────────────────────────────────────────────────────

def test_works_are_priced_rows_locked_when_short():
    p = member(role="steward")
    enter_hall(p)
    s = core.apply_choice(p, "hall_works")
    assert s.eyebrow == "EMBER PACT · THE WORKS"
    room = next(o for o in s.options if o.id == "work_room")
    assert room.locked
    assert "🔒 ◈ 2,000 — the coffer holds ◈ 140" in room.hint
    bed = next(o for o in s.options if o.id == "work_bed")
    assert not bed.locked and "◈ 250 from the coffer" in bed.hint


def test_steward_buys_a_bed_from_the_coffer():
    p = member(role="steward",
               hall_kw={"coffer": {"bal": 400, "cap": 600}})
    enter_hall(p)
    core.apply_choice(p, "hall_works")
    s = core.apply_choice(p, "work_bed")
    assert fx(p, "hall_bed_buy")
    h = p["_world"]["faction"]["hall"]
    assert h["coffer"]["bal"] == 150
    assert h["beds"]["count"] == 3                # optimistic bump
    assert "gone to the world" in " ".join(s.body_lines)


def test_works_answer_to_the_steward_only():
    p = member(role="member",
               hall_kw={"coffer": {"bal": 400, "cap": 600}})
    enter_hall(p)
    core.apply_choice(p, "hall_works")
    s = core.apply_choice(p, "work_bed")
    assert not fx(p, "hall_bed_buy")
    assert any("answer to the steward" in ln for ln in s.body_lines)


# ── THE DESK ─────────────────────────────────────────────────────────────

def test_desk_is_steward_only_with_a_badge():
    p = member(role="steward")
    p["_world"]["faction"]["pending_requests"] = 2
    s = enter_hall(p)
    desk = next(o for o in s.options if o.id == "hall_desk")
    assert desk.badge == 2 and "2 ask to join" in desk.hint


def test_desk_settles_injected_requests():
    p = member(role="steward")
    p["_world"]["faction"]["pending_requests"] = 1
    p["_world"]["faction"]["requests"] = [
        {"tenant": "t2", "player": "u9", "name": "Vex", "level": 6,
         "requested_day": 4}]
    enter_hall(p)
    s = core.apply_choice(p, "hall_desk")
    ids = {o.id for o in s.options}
    assert "req_ok_0" in ids and "req_no_0" in ids
    s = core.apply_choice(p, "req_ok_0")
    e = fx(p, "faction_approve")[0]
    assert e["tenant"] == "t2" and e["player"] == "u9"
    assert p["_world"]["faction"]["pending_requests"] == 0
    assert "Vex gets a chair" in " ".join(s.body_lines)


def test_desk_rename_is_an_ask_and_renames_everywhere():
    p = member(role="steward")
    enter_hall(p)
    core.apply_choice(p, "hall_desk")
    s = core.apply_choice(p, "rename_banner")
    assert s.ask and s.ask["max"] == 24
    s = core.apply_choice(p, "", "Iron Dawn")
    assert fx(p, "faction_rename")[0]["name"] == "Iron Dawn"
    assert s.eyebrow.startswith("IRON DAWN ·")


# ── The Guildhall's civic floor (032 §3) ────────────────────────────────

def test_guildhall_leads_with_your_hall_and_the_walls():
    p = member()
    s = core.apply_choice(p, "guildhall")
    assert s.options[0].id == "hall"
    assert s.options[0].label == "YOUR FACTION'S HALL — the Ember Pact table"
    assert s.headline == "Where the factions fly"
    body = s.body_lines
    assert any("THIS WEEK — THE ASCENT DEMANDS A CULL" in ln
               for ln in body)
    nl = next(i for i, ln in enumerate(body) if "NIGHT LEDGER" in ln)
    ep = next(i for i, ln in enumerate(body)
              if ln.startswith("▪ EMBER PACT"))
    assert nl < ep                                # sorted by completion
    # the member panel is gone — its acts live at the hall now
    assert "STORE ◈" not in " ".join(body)
    ids = {o.id for o in s.options}
    assert "donate" not in ids and "enter_week" not in ids
    # the hall of banners: reigning first, tap-to-page tiles
    assert s.gallery[0]["opt"] == "page_Ember Pact"
    assert s.gallery[0]["label"].startswith("★")
    assert "2 at the table" in s.gallery[0]["sub"]
    assert "a hall of your own" in s.gallery[0]["sub"]


def test_your_hall_row_walks_into_the_hall():
    p = member()
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "hall")
    assert p["location"] == "hall"
    assert s.eyebrow == "EMBER PACT · A HALL OF YOUR OWN"


def test_seeker_gets_the_gallery_and_the_founding_row():
    p = playing(world=seeker_world())
    s = core.apply_choice(p, "guildhall")
    assert [g["opt"] for g in s.gallery] == ["page_Ember Pact",
                                             "page_Night Ledger"]
    ids = {o.id for o in s.options}
    assert "found_guild" in ids and "hall_ledger" in ids
    found = next(o for o in s.options if o.id == "found_guild")
    assert found.locked and "🔒" in found.hint     # level 1 — locked row


def test_banner_page_scores_room_and_the_ask():
    p = playing(world=seeker_world())
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "page_Ember Pact")
    assert s.headline == "The Ember Pact faction"
    assert s.banner == "wolf_howl"
    assert s.strip["art"] == "hall_room_2"
    body = " ".join(s.body_lines)
    assert "3 weeks won all-time" in body
    assert "2 at the table" in body and "a hall of your own" in body
    assert "this week's CULL" in body
    join = next(o for o in s.options if o.id == "join_Ember Pact")
    assert "◈ 25 if they take you" in join.hint
    s = core.apply_choice(p, "join_Ember Pact")
    assert fx(p, "faction_request")[0]["guild"] == "Ember Pact"
    # the page now holds the cancel instead
    cancel = next(o for o in s.options if o.id == "cancel_request")
    assert "waits at their desk" in cancel.hint
    s = core.apply_choice(p, "cancel_request")
    assert fx(p, "faction_request_cancel")
    assert any(o.id == "join_Ember Pact" for o in s.options)
    # and the way back is the floor, not the square
    s = core.apply_choice(p, "guildhall")
    assert s.headline == "Where the factions fly"
    assert "banner_page" not in p


def test_members_page_reads_but_never_asks():
    p = member()
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "page_Night Ledger")
    ids = {o.id for o in s.options}
    assert "join_Night Ledger" not in ids and "cancel_request" not in ids


# ── The wire law and the degrade ─────────────────────────────────────────

def test_hall_data_rides_top_level_keys_only():
    """0.33.0's lesson: option dicts carry exactly the shipped keys."""
    p = member()
    s = enter_hall(p)
    d = s.to_dict()
    for o in d["options"]:
        assert set(o) <= {"id", "label", "hint", "aether", "locked"}
    assert "option_art" in d and "strip" in d     # top-level riders


def test_old_worldd_keeps_the_010_guildhall():
    p = member()
    del p["_world"]["faction"]["hall"]
    p["_world"].pop("hall_board", None)
    s = core.apply_choice(p, "guildhall")
    body = " ".join(s.body_lines)
    assert "STORE ◈ 140" in body                  # the old member panel
    ids = {o.id for o in s.options}
    assert "donate" in ids and "hall" not in ids
    # a doc parked at the hall walks back to the Guildhall
    p["location"] = "hall"
    s = core.current_scene(p)
    assert p["location"] == "guildhall"
