"""012 — the pack has a size: six slots for everyone, larger packs at
the Forge (level 3/6/9/12 → 9/12/15/18), shops refuse a NEW stack in a
full pack before gold moves, loot still lands, and the grid draws the
capacity."""

from plugin_linear_ascent import economy, render, unlocks
from plugin_linear_ascent.engine import core, state
from plugin_linear_ascent.engine.scene import Scene

from tests.test_019_shop_rows import create_character


def _fill(p, n):
    """Open n distinct stacks of relics (never bought — direct loot)."""
    for i in range(n):
        p["inventory"][f"loot_{i}"] = 1


# ── state ────────────────────────────────────────────────────────────────

def test_new_character_has_six_slots():
    p = create_character("six")
    assert core.pack_cap(p) == 6
    assert p["pack_slots"] == economy.PACK_BASE_SLOTS == 6


def test_old_doc_without_key_heals_to_six():
    p = create_character("heal")
    del p["pack_slots"]
    state.ensure_current(p)
    assert p["pack_slots"] == 6


def test_a_slot_is_a_stack():
    p = create_character("stack")
    p["inventory"] = {"medgel": 5, "trauma_kit": 0}
    assert core.pack_used(p) == 1
    assert core.pack_can_take(p, "medgel")
    assert core.pack_can_take(p, "salve")


def test_tiers():
    assert economy.PACK_TIERS == ((3, 9, 40), (6, 12, 120),
                                  (9, 15, 300), (12, 18, 600))
    assert economy.pack_next_tier(6) == (3, 9, 40)
    assert economy.pack_next_tier(9) == (6, 12, 120)
    assert economy.pack_next_tier(18) is None


# ── shops refuse a NEW stack in a full pack, before gold moves ───────────

def test_medlab_refuses_when_full_but_stacks_onto_owned():
    p = create_character("med-full")
    p["gold"] = 10_000
    _fill(p, 5)
    p["inventory"]["medgel"] = 1               # 6th stack — full
    core.apply_choice(p, "medlab")
    gold = p["gold"]
    s = core.apply_choice(p, "buy_trauma_kit")
    assert s.refusal and "pack full (6/6" in s.refusal
    assert p["gold"] == gold
    assert "trauma_kit" not in p["inventory"]
    core.apply_choice(p, "buy_medgel")         # stacks — allowed
    assert p["inventory"]["medgel"] == 2
    assert p["gold"] < gold


def test_medlab_energy_cell_ignores_the_pack():
    p = create_character("cell")
    p["gold"] = 10_000
    _fill(p, 6)
    core.apply_choice(p, "medlab")
    s = core.apply_choice(p, "buy_energy_cell")
    assert not s.refusal


def test_forge_spare_refused_when_full():
    p = create_character("spare-full")
    p["gold"] = 10_000
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_scrap_dagger")   # rusted_sword → pack (1)
    _fill(p, 5)                                # 6/6
    gold = p["gold"]
    s = core.apply_choice(p, "buy_scrap_dagger")
    assert s.refusal and "pack full" in s.refusal
    assert p["gold"] == gold
    assert "scrap_dagger" not in p["inventory"]


def test_forge_upgrade_refused_when_old_piece_has_no_room():
    p = create_character("old-full")
    p["gold"], p["level"] = 10_000, 2
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_scrap_dagger")   # rusted_sword → pack (1)
    _fill(p, 5)                                # 6/6
    gold, worn = p["gold"], p["gear"]["weapon"]
    s = core.apply_choice(p, "buy_notched_cleaver")
    assert s.refusal and "pack full" in s.refusal
    assert p["gold"] == gold and p["gear"]["weapon"] == worn


def test_relic_refused_when_full():
    p = create_character("relic-full")
    p["gold"] = 10_000
    _fill(p, 6)
    core.apply_choice(p, "medlab")
    slug = next(s for s, r in economy.RELICS.items()
                if r.shop == "apothecary" and not r.line)
    p["unlocked_floor"] = max(p["unlocked_floor"], economy.RELICS[slug].floor)
    gold = p["gold"]
    s = core.apply_choice(p, f"buy_{slug}")
    assert s.refusal and "pack full" in s.refusal
    assert p["gold"] == gold


def test_loot_still_lands_over_capacity_and_the_wire_says_so():
    p = create_character("over")
    _fill(p, 8)                                # loot, not a shop
    assert core.pack_used(p) == 8
    s = core.current_scene(p)
    assert s.pack_slots == 6
    html = render._inventory_html(s)
    assert "pack 8/6 · over" in html
    assert html.count("slot item act over") == 2
    d = Scene.from_dict(s.to_dict())
    assert d.pack_slots == 6


# ── the Forge sells larger packs ────────────────────────────────────────

def test_forge_row_locked_below_level_3():
    p = create_character("lock")
    p["level"] = 2
    s = core.apply_choice(p, "forge")
    row = next(o for o in s.options if o.id == "buy_pack")
    assert row.locked and "🔒 level 3" in row.hint and "9 slots" in row.label
    gold = p["gold"] = 1_000
    s = core.apply_choice(p, "buy_pack")
    assert s.refusal and "level 3" in s.refusal
    assert p["gold"] == gold and core.pack_cap(p) == 6


def test_forge_sells_tiers_in_order():
    p = create_character("tiers")
    p["level"], p["gold"] = 12, 10_000
    core.apply_choice(p, "forge")
    for slots, gold in ((9, 40), (12, 120), (15, 300), (18, 600)):
        before = p["gold"]
        s = core.apply_choice(p, "buy_pack")
        assert not s.refusal, s.refusal
        assert core.pack_cap(p) == slots and p["gold"] == before - gold
        assert any(f"{slots} slots now" in ln for ln in s.body_lines)
    s = core.current_scene(p)
    assert not any(o.id == "buy_pack" for o in s.options)
    assert core._forge_pack(p).refusal and "largest" in \
        core._forge_pack(p).refusal


def test_second_tier_gated_at_level_6():
    p = create_character("gate6")
    p["level"], p["gold"] = 5, 10_000
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_pack")
    assert core.pack_cap(p) == 9
    s = core.current_scene(p)
    row = next(o for o in s.options if o.id == "buy_pack")
    assert row.locked and "🔒 level 6" in row.hint and "12 slots" in row.label


def test_bigger_pack_reopens_the_shops():
    p = create_character("reopen")
    p["level"], p["gold"] = 3, 10_000
    _fill(p, 6)
    core.apply_choice(p, "medlab")
    assert core.apply_choice(p, "buy_trauma_kit").refusal
    core.apply_choice(p, "back")
    core.apply_choice(p, "forge")
    core.apply_choice(p, "buy_pack")
    core.apply_choice(p, "back")
    core.apply_choice(p, "medlab")
    assert not core.apply_choice(p, "buy_trauma_kit").refusal
    assert p["inventory"]["trauma_kit"] == 1


def test_unlock_legend_lists_the_tiers():
    ids = {u.id for u in unlocks.registry()}
    assert {"pack9", "pack12", "pack15", "pack18"} <= ids


# ── the grid ─────────────────────────────────────────────────────────────

def test_grid_draws_capacity_and_flows():
    p = create_character("grid")
    p["inventory"] = {"medgel": 2}
    s = core.current_scene(p)
    html = render._inventory_html(s)
    assert "pack 1/6" in html
    assert html.count('class="slot empty"></span>') == 5
    src = open(render.__file__, encoding="utf-8").read()
    assert ".slotgrid{{display:flex;flex-wrap:wrap" in src
    assert ".slot{{position:relative;width:60px;height:60px" in src
    # 069: the hand row is gone — the gear map draws its own slots
    assert ".hcell" not in src
    assert ".gearmap{{display:grid" in src
