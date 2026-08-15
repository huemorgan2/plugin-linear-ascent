"""059 — the faction block under the profile, and one word: faction.

The wire carries the faction's banner, table size and online count (or,
for the unaffiliated, how many factions fly); the renderer hangs a block
under the profile — member: banner, name, counts, a door into the
Playing panel's faction tab; no faction: JOIN A FACTION with the count,
opening the ledger, and the founding lock under level 4. The Guildhall
says faction, offers Join a faction always, and wears the new header.
"""

from plugin_linear_ascent import pane, render
from plugin_linear_ascent.engine import combat, core, state
from plugin_linear_ascent.render import render_scene_fragment


def playing(name="Blk", world=None):
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


def member_world(online=2):
    members = [{"name": "Hally", "role": "steward", "founder": True,
                "level": 5, "arrears": False, "days": 3, "required": 4,
                "online": True},
               {"name": "Brynn", "role": "member", "founder": False,
                "level": 3, "arrears": False, "days": 1, "required": 4,
                "online": online > 1},
               {"name": "Ola", "role": "member", "founder": False,
                "level": 2, "arrears": False, "days": 0, "required": 4,
                "online": False}]
    return {"social": True,
            "faction": {"name": "Ember Pact", "banner": "wolf_howl",
                        "join_fee": 25, "dues": 5, "store": 100,
                        "role": "member", "members": members,
                        "members_count": 3, "online": online,
                        "week": {"kind": "cull", "target": 100,
                                 "entered": False, "progress": 0,
                                 "entry_cost": 15, "attended": 0,
                                 "required": 12, "multiplier": 0,
                                 "base_pct": 0.15}}}


def loner_world(total=7):
    return {"social": True, "factions": [], "factions_total": total,
            "faction_banners": ["wolf_howl"], "hall_board": {"banners": []}}


# ── the wire ─────────────────────────────────────────────────────────────

def test_meters_carry_the_faction_block_fields():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    m = combat.meters(p)
    assert m.faction == "Ember Pact"
    assert m.faction_banner == "wolf_howl"
    assert m.faction_members == 3
    assert m.faction_online == 2
    assert m.factions_total == -1          # members aren't sent the count

    q = playing(world=loner_world(7))
    m = combat.meters(q)
    assert m.faction == ""
    assert m.factions_total == 7

    r = playing()                          # no world at all — old wire
    m = combat.meters(r)
    assert m.factions_total == -1 and m.faction_banner == ""


# ── the block ────────────────────────────────────────────────────────────

def test_member_block_shows_banner_name_counts_and_the_door():
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    frag = render_scene_fragment(core.current_scene(p))
    blk = frag.split('class="facblk')[1]
    assert 'data-fac="Ember Pact"' in blk
    assert '<img class="facsig"' in blk          # wolf_howl art exists
    assert "3 climbers" in blk and "2 online now" in blk
    assert 'data-opt="go:hall"' in blk           # banner + name = the door
    assert "FACTION ACTIVITY" not in blk
    assert "\u25ba" not in blk                    # no arrow glyph
    assert "JOIN A FACTION" not in blk


def test_loner_block_offers_join_with_the_count_and_the_found_lock():
    p = playing(world=loner_world(7))
    p["level"] = 2
    frag = render_scene_fragment(core.current_scene(p))
    blk = frag.split('class="facblk')[1]
    assert "JOIN A FACTION" in blk
    assert "7 factions" in blk
    assert 'data-tab="community"' in blk
    assert "found your own" in blk and "level 4" in blk
    assert "\U0001f512" not in blk               # the lock is a glyph

    p["level"] = 4
    frag = render_scene_fragment(core.current_scene(p))
    blk = frag.split('class="facblk')[1]
    assert "found your own" not in blk

    q = playing(world=loner_world(0))
    frag = render_scene_fragment(core.current_scene(q))
    assert "no faction flies yet" in frag


def test_old_wire_still_gets_a_join_row_without_a_count():
    p = playing()
    frag = render_scene_fragment(core.current_scene(p))
    blk = frag.split('class="facblk')[1]
    assert "JOIN A FACTION" in blk and "factions" not in blk.split("</button>")[0]


# ── the pane wires both doors ────────────────────────────────────────────

def test_pane_opens_the_playing_faction_tab_and_the_ledger():
    html = pane.render_pane()
    assert "window.__laPlaying" in html
    assert "[data-play]" in html
    assert "[data-tab]" in html
    assert "all the factions" in html            # the ledger's new eyebrow
    assert "no faction</div>" in html
    assert "unbannered" not in html


# ── the guildhall says faction ───────────────────────────────────────────

def test_guildhall_header_and_doors():
    p = playing(world=loner_world(7))
    s = core.apply_choice(p, "guildhall")
    assert s.eyebrow == "ROOTHOLLOW · THE GUILDHALL — home of all the factions"
    ids = [o.id for o in s.options]
    assert "hall_ledger" in ids and "found_guild" in ids
    join = next(o for o in s.options if o.id == "hall_ledger")
    assert join.label == "Join a faction" and "7 factions" in join.hint
    found = next(o for o in s.options if o.id == "found_guild")
    assert found.label == "Found a new faction"
    for o in s.options:
        assert "banner" not in o.label.lower()


# ── 061: the bar is the old desk bar's shape, and the CTA founds ─────────

def test_the_faction_bar_is_one_full_width_door():
    p = playing(world=loner_world(3))
    frag = render_scene_fragment(core.current_scene(p))
    blk = frag.split('class="facblk')[1].split("</div>")[0]
    assert 'class="facdoor join" data-tab="community"' in blk
    assert "\u25ba" not in blk                   # 062: no arrow glyph
    html = render.render_scene(core.current_scene(p))
    # 062: no box — the card's dotted rule cuts the strip off; the door
    # (banner + name) lights gold on hover
    assert f"border-top:1px dashed {render.BORDER}" in html.split(".facblk{")[1]
    assert ".facblk .facdoor:hover .facname" in html
    assert "deskbar" not in pane.render_pane()  # the old bar is gone


def test_a_member_walks_into_the_hall_from_any_room_on_the_square():
    from tests.test_032_banner_hall import the_hall
    p = playing(world=member_world())
    p["guild"] = "Ember Pact"
    p["_world"]["faction"]["hall"] = the_hall()
    p["location"] = "forge"
    s = core.apply_choice(p, "go:hall")
    assert p["location"] == "hall"
    assert not s.refusal
    # from the wilds the door stays shut (a fight is a fight)
    q = playing(world=member_world())
    q["guild"] = "Ember Pact"
    q["location"] = "wilds"
    q["floor"] = 1
    s = core.apply_choice(q, "go:hall")
    assert q["location"] == "wilds" and s.refusal


def test_the_feed_colors_kills_and_levelups_and_links_the_actor():
    html = pane.render_pane()
    assert f".plyrow.kill .pline{{color:{render.RED};}}" in html
    assert f".plyrow.levelup .pline{{color:{render.AETHER};}}" in html
    assert 'data-pv=' in html and "function plyLine" in html


def test_the_death_and_levelup_happenings_carry_a_tag():
    import inspect
    from plugin_linear_ascent.engine import combat as cmb, social as soc
    assert '"tag": "kill"' in inspect.getsource(cmb._death)
    assert 'tag="levelup"' in inspect.getsource(soc.guild_train)


def test_the_community_desk_founds_a_faction():
    html = pane.render_pane()
    assert "/pane/faction/found" in html
    assert 'data-desk="found"' in html
    assert "fd-name" in html and "fd-fee" in html and "fd-dues" in html
    assert "bpick" in html                     # the sigil picker
