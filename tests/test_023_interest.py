"""023 — collect the interest: daily stubs, lazy, bounded, badged.

The law under test: collectables materialize when the doc loads (absent
players cost nothing), every pile has a cap, and an uncollected pile is
SIMPLE interest — collecting re-banks it, so daily hands still compound.
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


def test_each_absent_day_is_one_stub_priced_off_the_principal():
    p = playing("stubs")
    p["bank"] = 200
    p["bank_day"] = state.world_day() - 10
    stubs = state.interest_sync(p)
    assert len(stubs) == 10
    assert all(s["gold"] == 10 for s in stubs)     # simple, not compound
    assert p["bank_day"] == state.world_day()
    assert state.interest_sync(p) == stubs         # idempotent within a day


def test_the_clerk_keeps_a_month_of_stubs_no_more():
    p = playing("cap")
    p["bank"] = 100
    p["bank_day"] = state.world_day() - 400
    stubs = state.interest_sync(p)
    assert len(stubs) == economy.INTEREST_STUB_CAP
    # the idle ceiling: a month of simple interest, never 400 days compound
    assert sum(s["gold"] for s in stubs) == 5 * economy.INTEREST_STUB_CAP


def test_collect_banks_the_pile_so_daily_hands_compound():
    p = playing("compound")
    p["bank"] = 1000
    p["bank_day"] = state.world_day() - 1
    assert state.interest_collect(p) == 50
    assert p["bank"] == 1050
    # the NEXT day's stub prices off the grown principal
    p["bank_day"] = state.world_day() - 1
    assert state.interest_sync(p)[0]["gold"] == round(1050 * 0.05)


def test_town_vault_door_badges_the_stub_count():
    p = playing("badge")
    p["bank"] = 200
    p["bank_day"] = state.world_day() - 10
    s = core.current_scene(p)
    assert label(s, "vault") == "The Vault (10)"
    core.apply_choice(p, "vault")
    s = core.apply_choice(p, "collect_interest")
    assert p["bank"] == 300
    s = core.apply_choice(p, "back")
    assert label(s, "vault") == "The Vault"


def test_an_empty_bank_earns_no_stubs():
    p = playing("empty")
    p["bank"] = 0
    p["bank_day"] = state.world_day() - 30
    assert state.interest_sync(p) == []
    s = core.current_scene(p)
    assert label(s, "vault") == "The Vault"


def test_vault_card_shows_the_pile_capped_at_five_lines():
    p = playing("card")
    p["bank"] = 200
    p["bank_day"] = state.world_day() - 8
    s = core.apply_choice(p, "vault")
    shown = [ln for ln in s.body_lines if "interest, uncollected" in ln]
    assert len(shown) == 5
    assert any("3 older interest stubs" in ln for ln in s.body_lines)
    assert "8 stubs" in label(s, "collect_interest")
