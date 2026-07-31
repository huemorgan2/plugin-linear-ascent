"""030 — the world you can see.

The plan's acceptance list, phase by phase: painted amounts, derived pip
icons, the armour-keyed portrait, tall room art, the shard's face, the
gate's floor tiles, the vault strip, the Morning Crier, the enemy plate,
drop odds, NPC voices, and the floor arrival reel. Numbers stay honest in
`to_text()` on every surface — the card paints, the words keep parity.
"""

import pytest

from plugin_linear_ascent import economy, icons, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.scene import Meters, Option, Scene


def _playing(name: str) -> dict:
    p = state.new_player(name)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", text="Seer")
    return p


# ── Phase 1: one coin, one colour ───────────────────────────────────────

def test_paint_amounts_colours_the_three_currencies():
    html = render._paint_amounts("◈ 1,240 and 3 ⚡ and 120 XP")
    assert html.count('class="amt"') == 3
    assert render.GOLD in html and render.VIOLET_SOFT in html \
        and render.AETHER in html


def test_to_text_keeps_the_glyph_characters():
    s = Scene(eyebrow="E", headline="H",
              body_lines=["◈ 1,240 in the vault", "+120 XP"])
    txt = s.to_text()
    assert "◈ 1,240" in txt and "120 XP" in txt
    assert "span" not in txt


def test_win_card_and_vault_share_the_coin_mask():
    coin_url = icons.icon_data_url("coin")
    assert coin_url in render._coin(37)
    assert coin_url in render._paint_amounts("◈ 1,240")
    assert coin_url in render._strip_band_html(
        {"art": "vault_interior", "text": "DEPOSITED: ◈ 1,240"})


# ── Phase 2: pips from one grid ─────────────────────────────────────────

def test_icon_modes_are_three_distinct_urls_from_one_grid():
    full = icons.icon_data_url("sword", "full")
    half = icons.icon_data_url("sword", "half")
    outline = icons.icon_data_url("sword", "outline")
    assert len({full, half, outline}) == 3


def test_outline_is_a_strict_subset_of_full():
    for key in ("sword", "armor"):
        grid = icons._GRIDS[key]
        full = icons._painted(grid)
        rim = icons._rimmed(grid)
        assert any(any(row) for row in rim)
        for y in range(16):
            for x in range(16):
                if rim[y][x]:
                    assert full[y][x], (key, x, y)
        assert sum(map(sum, rim)) < sum(map(sum, full)), key


def test_pip_math_thirds():
    full = icons.icon_data_url("armor", "full")
    half = icons.icon_data_url("armor", "half")
    outline = icons.icon_data_url("armor", "outline")

    def counts(stat):
        html = render._pip_row("armor", "DEF", stat, render.DIM, "tip")
        # each pip carries the url twice (-webkit-mask + mask) — count one
        return tuple(html.count(f"-webkit-mask-image:url('{u}')")
                     for u in (full, half, outline))

    assert counts(0) == (0, 0, 10)      # bare
    assert counts(3) == (0, 1, 9)       # every 3 points = half an icon
    assert counts(6) == (1, 0, 9)
    assert counts(61) == (10, 0, 0)     # over 60: full row…
    assert "DEF 61" in render._pip_row("armor", "DEF", 61, render.DIM, "t")
    # …and the numeral always prints


def test_enemy_head_is_one_hp_atk_def_line():
    # the user's redo: "just the HP attack defense in one line on the
    # top. nothing more." — icons yes, pips/range/mods no.
    enemy = render._enemy_head_html(
        {"name": "X", "hp": 5, "hp_max": 5, "atk": 12, "def": 0})
    assert "HP 5/5" in enemy and "ATK 12" in enemy and "DEF 0" in enemy
    assert icons.icon_data_url("sword") in enemy
    assert icons.icon_data_url("armor") in enemy
    assert "piprow" not in enemy
    assert enemy.count('class="echip"') == 1


# ── Phase 2: the armour-keyed portrait ──────────────────────────────────

def _scene_with_armor(slug):
    inv = ([{"slug": slug, "kind": "armor", "equipped": True}]
           if slug else [])
    return Scene(eyebrow="E", headline="H", inventory=inv)


def test_portrait_slug_buckets():
    assert render._portrait_slug(_scene_with_armor(None)) == "rags"
    buckets = {(1, 2): "leather", (3, 4): "chain", (5, 6): "scale",
               (7, 8): "plate", (9, 10): "aegis"}
    armors = [g for g in economy.FORGE.values() if g.slot == "armor"]
    assert armors
    for g in armors:
        want = next((b for (lo, hi), b in buckets.items()
                     if lo <= g.tier <= hi), "rags")
        assert render._portrait_slug(_scene_with_armor(g.slug)) == want, g.slug


def test_portrait_missing_art_degrades_to_bare_rail():
    s = Scene(eyebrow="E", headline="H",
              meters=Meters(10, 10, 5, 24, 0, 100, 0, atk=12, dfs=6))
    assert render._portrait_data_url("no_such_bucket") is None
    html = render._profile_html(s)
    assert "piprow" in html            # pips ride even without a portrait


def test_profile_block_holds_portrait_meters_and_pips():
    s = Scene(eyebrow="E", headline="H",
              meters=Meters(10, 10, 5, 24, 0, 100, 0, atk=12, dfs=6),
              inventory=[])
    html = render._profile_html(s)
    assert 'class="profile"' in html   # portraits shipped with 030
    assert html.count('class="piprow"') == 2   # ATK and DEF rows


def test_pack_rides_the_profile_right_column_not_below():
    # the redo: the pack sits to the RIGHT of the portrait, inside the
    # profile block's column — never as a strip under the image.
    s = Scene(eyebrow="E", headline="H",
              meters=Meters(10, 10, 5, 24, 0, 100, 0, atk=12, dfs=6),
              inventory=[{"slug": "rusty_sword", "kind": "weapon",
                          "equipped": True, "name": "Rusty Sword"}])
    html = render._profile_html(s)
    pcol = html.split('class="pcol"')[1]
    assert 'class="inv later"' in pcol
    frag = render.render_scene_fragment(s)
    assert frag.count('class="inv later"') == 1   # only inside the profile


# ── Phase 3: rooms are pictures, the shard has a face ───────────────────

def test_every_visited_room_resolves_tall_art():
    for slug in ("forge", "lodge", "vault", "medlab", "relay", "guildhall",
                 "stone", "gate", "arcanum", "roothollow", "greenreach",
                 "town_lamplit_steading"):
        art = render._banner_data_url(slug)
        assert art is not None, slug
        _url, w, h = art
        assert (w, h) == (320, 200), (slug, w, h)


def test_deep_floor_zones_still_resolve_via_fallback():
    for n in (11, 40, 100):
        slug = schema.get_floor(n).banner
        art = render._banner_data_url(slug)
        assert art is not None, (n, slug)


def test_shard_note_wears_the_shard_mask():
    assert "shard" in icons.ICON_KEYS
    html = render._shard_html("the wind smells of coin")
    assert icons.icon_data_url("shard") in html
    txt = Scene(eyebrow="E", headline="H", shard_note="x").to_text()
    assert "◆" in txt


def test_gate_floor_rows_carry_fields_and_warden_art():
    html = render._floor_tile_art("floor_1", False)
    assert html.count("fart") >= 2     # fields + warden, two masks
    assert render._floor_tile_art("hunt", False) == ""


# ── Phase 4: the vault strip ────────────────────────────────────────────

def test_strip_round_trips_the_wire():
    s = Scene(eyebrow="E", headline="H",
              strip={"art": "vault_interior", "text": "DEPOSITED: ◈ 1,240"})
    back = Scene.from_dict(s.to_dict())
    assert back.strip == {"art": "vault_interior",
                          "text": "DEPOSITED: ◈ 1,240"}
    assert "DEPOSITED: ◈ 1,240" in s.to_text()
    assert Scene.from_dict(
        Scene(eyebrow="E", headline="H").to_dict()).strip is None


def test_strip_band_renders_art_and_gold_coin():
    html = render._strip_band_html(
        {"art": "vault_interior", "text": "DEPOSITED: ◈ 1,240"})
    assert "stripband" in html and "bart" in html
    assert render.GOLD in html
    assert render._strip_band_html({"art": "vault_interior"}) == ""


def test_vault_scene_sends_the_strip():
    p = _playing("030-vault")
    p["bank"] = 1_240
    s = core.apply_choice(p, "vault")
    assert s.strip and s.strip["art"] == "vault_interior"
    assert "1,240" in s.strip["text"]


def test_paper_card_clamps_to_the_sheet():
    paper = {"headline": "Day 1", "closable": True,
             "items": [f"item number {n}" for n in range(1, 8)]}
    html = render._paper_html(paper)
    # the sheet is a fixed 320×150 — four 2-line items is what fits;
    # gossip (the tail of the priority order) yields first
    assert html.count('class="pit"') == 4
    assert "item number 5" not in html
    assert "aspect-ratio:320/150" in render.SCENE_CSS


def test_paper_is_light_newsprint_with_dark_ink():
    # the redo: newsprint is LIGHT, the ink is dark — no more grain
    # fighting dark text over a dark panel.
    assert (".paper{position:relative;margin:0 0 10px;background:"
            + render.TEXT) in render.SCENE_CSS
    assert f".paper .pbody{{position:absolute;inset:0;z-index:1;" \
           in render.SCENE_CSS


# ── Phase 6: a voice in every fields ────────────────────────────────────

def test_floors_1_to_10_have_npcs_and_the_lint_holds():
    for n in range(1, 11):
        npc = schema.get_floor(n).npc
        assert npc is not None, n
        assert npc.name and npc.role and npc.greet and npc.lore and npc.warn
    assert not [e for e in schema.lint_floors() if "missing npc" in e]


def test_npc_talk_names_the_warden_shape():
    p = _playing("030-npc")
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "talk")
    fl = schema.get_floor(1)
    body = "\n".join(s.body_lines)
    assert fl.npc.warn in body
    assert f"ATK {fl.warden_atk}" in body
    assert any(o.id == "talk" for o in s.options)


def test_keeper_tells_stories_of_glory():
    # the redo: not rate sheets — stories of climbers who earned their
    # fortunes over time under this roof, numbers woven in.
    p = _playing("030-keeper-glory")
    core.apply_choice(p, "lodge")
    text = " ".join(
        line for _ in range(4)
        for line in core.apply_choice(p, "talk").body_lines)
    for name in ("Okko", "Brand", "Asha", "Vell"):
        assert name in text
    assert "◈" in text and "✦" in text     # the coin is still real


def test_keeper_rotates_tellings():
    p = _playing("030-keeper")
    core.apply_choice(p, "lodge")
    s1 = core.apply_choice(p, "talk")
    s2 = core.apply_choice(p, "talk")
    assert s1.body_lines != s2.body_lines
    assert any(o.id == "talk" for o in s2.options)


# ── Phase 7: the fight tells its odds ───────────────────────────────────

def test_enemy_payload_promises_what_victory_pays():
    p = _playing("030-drops")
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "hunt")
    drops = (s.enemy or {}).get("drops")
    assert drops and drops["gold"][0] <= drops["gold"][1]
    assert drops["xp"][0] >= 1
    txt = s.to_text()
    assert "coins ◈" in txt and "XP ✦" in txt
    assert s.enemy.get("story")


# ── Phase 8: the arrival reel ───────────────────────────────────────────

@pytest.mark.reel
def test_first_floor_entry_plays_two_beats_then_arrival():
    p = _playing("030-reel")
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    assert p.get("movie_floor") == 1
    assert s.eyebrow.endswith("· I")
    assert [o.id for o in s.options] == ["next", "skip"]
    s = core.apply_choice(p, "next")
    assert s.eyebrow.endswith("· II")
    assert schema.get_floor(1).warden_name in s.headline
    s = core.apply_choice(p, "next")
    assert not p.get("movie_floor")
    assert p["flags"].get("floor_seen_1") is True
    assert any(o.id == "hunt" for o in s.options)


@pytest.mark.reel
def test_reel_plays_once_per_floor():
    p = _playing("030-reel-once")
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    core.apply_choice(p, "next")
    core.apply_choice(p, "next")
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    assert not p.get("movie_floor")
    assert any(o.id == "hunt" for o in s.options)


@pytest.mark.reel
def test_skip_cuts_the_reel_to_the_arrival_card():
    p = _playing("030-reel-skip")
    core.apply_choice(p, "gate")
    s = core.apply_choice(p, "floor_1")
    assert any(o.id == "skip" for o in s.options)   # skip on every beat
    s = core.apply_choice(p, "skip")
    assert not p.get("movie_floor")
    assert p["flags"].get("floor_seen_1") is True   # skipped still counts
    assert any(o.id == "hunt" for o in s.options)


@pytest.mark.reel
def test_stray_click_advances_the_reel_instead_of_erroring():
    p = _playing("030-reel-stray")
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    s = core.apply_choice(p, "hunt")          # early, mid-reel
    assert s.eyebrow.endswith("· II")         # it stepped, no shard scold
    assert not s.shard_note


@pytest.mark.reel
def test_fallen_keep_beat_names_the_war_party():
    p = _playing("030-reel-fallen")
    p["unlocked_floor"] = 2
    p["_world"] = {"frontier": 3,
                   "warden": {"fallen_by": {"2": "Asha, Brand"}}}
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_2")
    s = core.apply_choice(p, "next")
    body = "\n".join([s.headline] + s.body_lines)
    assert "has already fallen" in s.headline
    assert "Asha, Brand" in body
