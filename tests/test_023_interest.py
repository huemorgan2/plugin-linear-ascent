"""023/041 — collect the interest: sliced stubs, lazy, bounded, badged.

The law under test: the 5%-a-day rate drips in BANK_INTEREST_TICKS
slices (1% every 24/5 hours), each slice a stub priced off the
principal as it stood, materialized when the doc loads. Fractions
carry between slices so small banks lose nothing. Every pile has a
cap, and an uncollected pile is SIMPLE interest — collecting re-banks
it, so frequent hands still compound.
"""

from plugin_linear_ascent import economy
from plugin_linear_ascent.engine import core, state


def playing(name="Banker"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    return p


def label(scene, oid):
    return next(o.label for o in scene.options if o.id == oid)


def badge(scene, oid):
    """027: the waiting count is a field on the row, not text in its label."""
    return next(o.badge for o in scene.options if o.id == oid)


def _backdate(p, days):
    p["bank_day"] = state.world_day_f() - days


def test_each_absent_slice_is_one_stub_priced_off_the_principal():
    p = playing("stubs")
    p["bank"] = 200
    _backdate(p, 10)
    stubs = state.interest_sync(p)
    # 10 days × 5 slices, each 1% of 200 = ◈ 2 — simple, not compound
    assert len(stubs) == 10 * economy.BANK_INTEREST_TICKS
    assert all(s["gold"] == 2 for s in stubs)
    assert sum(s["gold"] for s in stubs) == 100    # the full 5%/day
    assert state.interest_sync(p) == stubs         # idempotent within a slice


def test_a_partial_day_already_pays_its_elapsed_slices():
    # 041: "each time you load" — 24/5 hours banked is one slice, not zero
    p = playing("partial")
    p["bank"] = 1000
    _backdate(p, 1 / economy.BANK_INTEREST_TICKS)
    stubs = state.interest_sync(p)
    assert len(stubs) == 1
    assert stubs[0]["gold"] == 10                  # 1% of 1000


def test_fractions_carry_so_small_banks_lose_nothing():
    p = playing("small")
    p["bank"] = 30                                 # 1% = 0.3 — under a coin
    _backdate(p, 2)
    stubs = state.interest_sync(p)
    # 10 slices × 0.3 = 3 whole coins, landing as the carry fills
    assert sum(s["gold"] for s in stubs) == 3


def test_the_clerk_keeps_a_month_of_slices_no_more():
    p = playing("cap")
    p["bank"] = 100
    _backdate(p, 400)
    stubs = state.interest_sync(p)
    assert len(stubs) == economy.INTEREST_STUB_CAP
    # the idle ceiling: a month of simple interest, never 400 days compound
    assert sum(s["gold"] for s in stubs) == economy.INTEREST_STUB_CAP * 1


def test_collect_banks_the_pile_so_frequent_hands_compound():
    p = playing("compound")
    p["bank"] = 1000
    _backdate(p, 1)
    assert state.interest_collect(p) == 50         # 5 slices × ◈ 10
    assert p["bank"] == 1050
    # the NEXT day's slices price off the grown principal
    _backdate(p, 1)
    stubs = state.interest_sync(p)
    assert sum(s["gold"] for s in stubs) == int(1050 * 0.05)


def test_town_vault_door_badges_the_stub_count():
    p = playing("badge")
    p["bank"] = 200
    _backdate(p, 2)
    s = core.current_scene(p)
    assert badge(s, "vault") == 10                 # 2 days × 5 slices
    core.apply_choice(p, "vault")
    s = core.apply_choice(p, "collect_interest")
    assert p["bank"] == 220
    s = core.apply_choice(p, "back")
    assert badge(s, "vault") == 0


def test_an_empty_bank_earns_no_stubs():
    p = playing("empty")
    p["bank"] = 0
    _backdate(p, 30)
    assert state.interest_sync(p) == []
    s = core.current_scene(p)
    assert badge(s, "vault") == 0


def test_vault_card_shows_the_pile_capped_at_five_lines():
    p = playing("card")
    p["bank"] = 200
    _backdate(p, 8)                                # 40 slices
    s = core.apply_choice(p, "vault")
    shown = [ln for ln in s.body_lines if "interest, uncollected" in ln]
    assert len(shown) == 5
    assert any("35 older interest stubs" in ln for ln in s.body_lines)
    assert "40 stubs" in label(s, "collect_interest")


def test_old_whole_day_marks_still_read():
    # pre-041 docs stamped an int day number — the float mark reads it
    p = playing("legacy")
    p["bank"] = 1000
    p["bank_day"] = state.world_day() - 1
    stubs = state.interest_sync(p)
    assert stubs                                   # at least the full day
    assert sum(s["gold"] for s in stubs) >= 50
