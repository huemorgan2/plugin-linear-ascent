"""042 — guilds, players here, looting: the presence grid, the profile
page and its four actions, the warden boards, the guild directory."""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, presence, social, state


def playing(name="Vex", world=None):
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


def tile(name, level=3, sleeping=False, **kw):
    return {"opt": f"pv:{name}", "name": name, "level": level,
            "race": "human", "armor": "leather", "sleeping": sleeping,
            "gold": 40, "energy": 9, **kw}


def prof(name, **kw):
    base = {"name": name, "level": 4, "race": "elf", "clazz": "ranger",
            "gold": 120, "energy": 8, "atk": 6, "dfs": 4,
            "hp": 30, "hp_max": 30, "sleeping": False,
            "same_guild": False, "protected": False, "lootable": False,
            "gear": [], "inventory": [], "armor": "leather"}
    base.update(kw)
    return base


# ── the presence layer ───────────────────────────────────────────────────

def test_room_keys_scope_floors_halls_and_sleepers():
    p = playing()
    assert presence.room_key(p) == "town"
    p["location"], p["floor"] = "warden_keep", 4
    assert presence.room_key(p) == "warden_keep:4"
    p["location"] = "hall"
    p["guild"] = "Ember Pact"
    assert presence.room_key(p) == "hall:Ember Pact"
    p["location"] = "sleeping"
    p["sleeping"] = {"where": "fields"}
    assert presence.room_key(p) == "fields"


def test_grid_excludes_self_sorts_awake_first_and_caps_at_seventy():
    crowd = [tile(f"Z{i:03d}", level=i % 9 + 1) for i in range(75)]
    crowd.append(tile("Vex"))                      # the viewer's own face
    crowd.append(tile("Aay", level=2, sleeping=True))
    p = playing(world={"social": True, "rooms": {"town": crowd}})
    tiles = presence.players_here(p)
    assert len(tiles) == presence.ROOM_CAP
    assert all(t["name"] != "Vex" for t in tiles)
    assert not tiles[0]["sleeping"]                # awake outrank sleepers


def test_town_card_mounts_the_grid_but_fights_stay_clean():
    p = playing(world={"social": True,
                       "rooms": {"town": [tile("Bo")]}})
    s = core.current_scene(p)
    assert s.players_here and s.players_title == "PLAYERS HERE"
    from plugin_linear_ascent.engine.scene import Scene
    fight = Scene(eyebrow="", headline="", support="",
                  enemy={"name": "wolf"})
    presence.mount(p, fight)
    assert not fight.players_here, "fights stay clean"


def test_scene_wire_carries_the_grid_top_level():
    p = playing(world={"social": True, "rooms": {"town": [tile("Bo")]}})
    d = core.current_scene(p).to_dict()
    assert d["players_here"][0]["opt"] == "pv:Bo"
    assert d["players_title"] == "PLAYERS HERE"


# ── the profile page ─────────────────────────────────────────────────────

def world_with(profile, rooms=None):
    return {"social": True, "rooms": rooms or {},
            "profiles": {profile["name"]: profile}}


def test_tile_click_opens_the_profile_and_back_returns():
    p = playing(world=world_with(prof("Bo"),
                                 rooms={"town": [tile("Bo")]}))
    s = core.apply_choice(p, "pv:Bo")
    assert p["location"] == "profile" and p["profile_view"] == "Bo"
    assert "LEVEL 4" in s.headline
    assert not any("bank" in ln.lower() or "vault ◈" in ln.lower()
                   for ln in s.body_lines), "the bank stays private"
    s = core.apply_choice(p, "back")
    assert p["location"] == "town"
    assert "profile_view" not in p


def test_send_money_walks_the_grants_law():
    p = playing(world=world_with(prof("Bo")))
    p["location"], p["profile_view"] = "profile", "Bo"
    p["gold"] = 1000
    core.apply_choice(p, "pf_pay")
    core.apply_choice(p, "pf_pay_100")
    assert p["gold"] == 900
    assert p["daily"]["granted"] == 100
    fx = [e for e in p["_effects"] if e["kind"] == "grant"]
    assert fx == [{"kind": "grant", "to_name": "Bo",
                   "net": 90, "gross": 100}]


def test_gift_leaves_the_pack_and_rides_an_effect():
    p = playing(world=world_with(prof("Bo")))
    p["location"], p["profile_view"] = "profile", "Bo"
    p["inventory"] = {"tonic": 2}
    core.apply_choice(p, "pf_gift")
    core.apply_choice(p, "pf_gift_tonic")
    assert p["inventory"]["tonic"] == 1
    assert {"kind": "gift_item", "to_name": "Bo",
            "slug": "tonic"} in p["_effects"]


def test_loot_locked_for_guildmates_and_the_protected():
    for flag in ("same_guild", "protected"):
        p = playing(world=world_with(prof("Bo", **{flag: True})))
        p["location"], p["profile_view"] = "profile", "Bo"
        s = core.current_scene(p)
        row = next(o for o in s.options if o.id == "pf_loot")
        assert row.locked


def test_loot_go_spends_energy_sets_cooldown_and_emits_the_attempt():
    p = playing(world=world_with(prof("Bo", lootable=True)))
    p["location"], p["profile_view"] = "profile", "Bo"
    e0 = state.energy_now(p)
    s = core.apply_choice(p, "pf_loot")
    assert "quarter" in " ".join(s.body_lines)     # cold-camp odds shown
    core.apply_choice(p, "pf_loot_go")
    assert state.energy_now(p) == e0 - economy.COST_PVP_ATTACK
    assert "Bo" in p["loot_cd"]
    assert {"kind": "loot_attempt", "target_name": "Bo"} in p["_effects"]
    # the pair cooldown bites for a full hour
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "pf_loot")
    assert row.locked and "again in" in row.hint


def test_active_target_warns_of_double_retaliation():
    p = playing(world=world_with(prof("Bo", lootable=False,
                                      last_seen_min=5)))
    p["location"], p["profile_view"] = "profile", "Bo"
    s = core.apply_choice(p, "pf_loot")
    assert any("TWICE" in ln for ln in s.body_lines)


# ── the warden boards ────────────────────────────────────────────────────

def test_live_board_aggregates_strikers_and_shows_taken():
    strikes = [
        {"name": "Ash", "dmg": 10, "taken": 4, "level": 3,
         "race": "human", "armor": "chain"},
        {"name": "Ash", "dmg": 15, "taken": 2, "level": 4,
         "race": "human", "armor": "chain"},
        {"name": "Bel", "dmg": 20, "taken": 0, "level": 2,
         "race": "elf", "armor": "rags"},
    ]
    board = social._striker_board(strikes)
    assert [t["name"] for t in board] == ["Ash", "Bel"]  # 25 dmg > 20
    assert board[0]["sub"] == "6 taken"
    assert board[0]["level"] == 4                  # newest shape wins


def test_memorial_ranks_the_fallen_by_damage_dealt():
    roll = [{"name": "Ash", "dmg": 900, "level": 5, "race": "human",
             "armor": "plate"},
            {"name": "Bel", "dmg": 400, "level": 3, "race": "elf",
             "armor": "chain"}]
    p = playing(world={"social": True, "frontier": 3,
                       "fallen": {"1": {"day": 1, "names": "Ash, Bel",
                                        "roll": roll}}})
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "keep")
    assert s.players_title == "THE HONORED FALLEN"
    assert s.players_here[0]["rank"] == 1
    assert s.players_here[0]["sub"] == "900 dealt"


# ── the guild directory ──────────────────────────────────────────────────

def dir_world(rows, total=None, **kw):
    w = {"social": True, "factions": [], "factions_total": len(rows),
         "guild_dir": {"rows": rows, "total": total or len(rows)}}
    w.update(kw)
    return w


def drow(name, fee=0, members=3, req=None):
    return {"name": name, "banner": "wolf_howl", "join_fee": fee,
            "members": members, "requirements": req or {}}


def test_directory_join_charges_the_fee_and_emits_faction_join():
    p = playing(world=dir_world([drow("Ember Pact", fee=25)]))
    p["gold"] = 100
    core.apply_choice(p, "guildhall")
    core.apply_choice(p, "hall_ledger")
    s = core.apply_choice(p, "gjoin_Ember Pact")
    assert "banner takes you" in s.headline
    assert p["guild"] == "Ember Pact" and p["gold"] == 75
    assert {"kind": "faction_join",
            "guild": "Ember Pact"} in p["_effects"]


def test_directory_gates_level_cap_and_invite_only():
    rows = [drow("High Table", req={"min_level": 10}),
            drow("Full House", members=5, req={"member_cap": 5}),
            drow("Closed Door", req={"invite_only": True})]
    p = playing(world=dir_world(rows))
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "hall_ledger")
    subs = {g["label"]: g["sub"] for g in s.gallery}
    assert "REQUIRES L10" in subs["High Table"]
    assert "FULL" in subs["Full House"]
    assert "invite only" in subs["Closed Door"]
    core.apply_choice(p, "gjoin_High Table")
    assert not p.get("guild"), "the level gate holds"
    core.apply_choice(p, "gjoin_Closed Door")
    assert not p.get("guild")
    assert {"kind": "faction_request",
            "guild": "Closed Door"} in p["_effects"]


def test_directory_search_filters_and_pages_turn():
    rows = [drow(f"Banner {i:02d}") for i in range(45)]
    p = playing(world=dir_world(rows))
    core.apply_choice(p, "guildhall")
    s = core.apply_choice(p, "hall_ledger")
    assert len(s.gallery) == 20
    assert any(o.id == "gdir_next" for o in s.options)
    s = core.apply_choice(p, "gdir_next")
    assert s.gallery[0]["label"] == "Banner 20"
    core.apply_choice(p, "gdir_search")
    s = core.apply_choice(p, "", "Banner 42")
    assert [g["label"] for g in s.gallery] == ["Banner 42"]


# ── the renderer ships the grid ──────────────────────────────────────────

def test_fragment_renders_ptiles_with_tooltip_and_zzz():
    p = playing(world={"social": True,
                       "rooms": {"town": [tile("Bo", sleeping=True)]}})
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    assert 'data-opt="pv:Bo"' in html
    assert "pzzz" in html                          # the sleeping chip
    assert "◈ 40" in html and "⚡ 9" in html       # the hover tooltip
    assert "button.ptile" in render.SCENE_CSS or "ptile" in html
