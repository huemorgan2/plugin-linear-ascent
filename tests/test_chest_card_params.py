"""011 (workspace plan): a piece leaving the pack says what it is.

The chest's PUT wall and the pawn shop's donate rows used to show only
the tenure line "no coin — the faction keeps it" — a fresh Wolfbite and
one worn to 40% read identically on the very scene whose support line
says the wear rides with the piece. One shared fragment
(`economy.gear_card_stats`) now leads every such hint: stat, durability
(worn pieces say left-of-full), style word."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state

from tests.test_032_banner_hall import member, enter_hall


LAW = "no coin — the faction keeps it"


def _first(pred):
    return next(g for _, g in sorted(economy.FORGE.items()) if pred(g))


def test_gear_card_stats_speaks_each_slots_unit():
    w = _first(lambda g: g.slot == "weapon" and g.price > 0)
    s = _first(lambda g: g.slot == "shield" and g.price > 0)
    a = _first(lambda g: g.slot == "armor" and g.price > 0)
    sh = _first(lambda g: g.slot == "shoes" and g.price > 0)
    assert f"+{w.bonus} ATK" in economy.gear_card_stats(w)
    assert f"+{s.bonus} DEF" in economy.gear_card_stats(s)
    assert f"+{a.bonus} DEF" in economy.gear_card_stats(a)
    assert f"+{sh.speed} spd" in economy.gear_card_stats(sh)
    assert (f"durability {economy.endurance(w):,}"
            in economy.gear_card_stats(w))


def test_gear_card_stats_worn_says_left_of_full():
    g = _first(lambda g: g.slot == "weapon" and g.price > 0)
    half = economy.item_pool(g) // 2
    frag = economy.gear_card_stats(g, half)
    assert (f"durability {economy.endurance(g, half):,} "
            f"of {economy.endurance(g):,}") in frag


def test_gear_card_stats_styled_piece_wears_its_word():
    g = _first(lambda g: g.style == "keen")
    assert "keen" in economy.gear_card_stats(g).split(" · ")


def test_chest_put_card_shows_stat_and_durability():
    g = _first(lambda g: g.slot == "weapon" and g.price > 0)
    p = member()
    p["inventory"][g.slug] = 1
    enter_hall(p)
    core.apply_choice(p, "hall_chest")
    s = core.apply_choice(p, "chest_put")
    row = next(o for o in s.options if o.id == f"put_{g.slug}")
    assert f"+{g.bonus} ATK" in row.hint
    assert f"durability {economy.endurance(g):,}" in row.hint
    assert row.hint.endswith(LAW)                 # 017: the EV law holds


def test_chest_put_card_shows_the_wear_it_carries():
    g = _first(lambda g: g.slot == "weapon" and g.price > 0)
    half = economy.item_pool(g) // 2
    p = member()
    p["inventory"][g.slug] = 1
    p.setdefault("durability_pack", {})[g.slug] = half
    enter_hall(p)
    core.apply_choice(p, "hall_chest")
    s = core.apply_choice(p, "chest_put")
    row = next(o for o in s.options if o.id == f"put_{g.slug}")
    assert (f"durability {economy.endurance(g, half):,} "
            f"of {economy.endurance(g):,}") in row.hint


def test_pawn_donate_row_carries_the_same_fragment():
    g = _first(lambda g: g.slot == "weapon" and g.price > 0
               and g.slug not in economy.BASIC_WEAPONS)
    p = member()
    p["inventory"][g.slug] = 1
    s = core.apply_choice(p, "pawn")
    row = next(o for o in s.options if o.id == f"donate_{g.slug}")
    assert f"+{g.bonus} ATK" in row.hint
    assert f"durability {economy.endurance(g):,}" in row.hint
    assert row.hint.endswith(LAW)
