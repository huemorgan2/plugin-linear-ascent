"""041 — the second batch of live-play rules.

1. One door to a bunk: the Lodge's "Pay for the night" row is gone —
   "Turn in" pays the night itself.
2. Money talks plainly: a row that charges says "pay ◈ …", a row that
   pays out says "receive ◈ …".
3. The enemy sheet reads the moment the scene lands — no `later` class.
4. The pane's script carries the new interactions: digit keys press the
   menu, a click quadruples the pen, mobile scrolls back to the art,
   and a tap toggles the [i] tips.
(The sliced vault interest is law-tested in test_023_interest.py.)
"""

from plugin_linear_ascent import economy, pane, render
from plugin_linear_ascent.engine import core, state


def playing(name="Qol"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    return p


# ── 1. one door to a bunk ────────────────────────────────────────────────

def test_the_lodge_offers_exactly_one_way_to_sleep():
    p = playing("bunk")
    s = core.apply_choice(p, "lodge")
    ids = [o.id for o in s.options]
    assert "sleep" not in ids
    assert ids.count("lie_down") == 1


def test_turning_in_still_pays_the_bunk():
    p = playing("payer")
    price = economy.LODGE_PRICE_PER_LEVEL * p["level"]
    p["gold"] = price
    core.apply_choice(p, "lodge")
    core.apply_choice(p, "lie_down")
    assert p["gold"] == 0
    assert p["lodged_until_day"] >= state.world_day() + 1


# ── 2. pay ◈ / receive ◈ ─────────────────────────────────────────────────

def _hint(s, oid):
    return next(o.hint for o in s.options if o.id == oid)


def test_charging_rows_say_pay():
    p = playing("payhints")
    s = core.current_scene(p)
    assert _hint(s, "lodge").startswith("pay ◈")
    s = core.apply_choice(p, "forge")
    buys = [o for o in s.options if o.id.startswith("buy_") and not o.locked]
    assert buys and all("pay ◈" in o.hint for o in buys)
    core.apply_choice(p, "back")
    p["hp"] = 1
    s = core.apply_choice(p, "lodge")
    assert _hint(s, "stew").startswith("pay ◈")
    assert "pay ◈" in _hint(s, "lie_down")


def test_paying_rows_say_receive():
    p = playing("recvhints")
    p["bank"] = 1000
    p["bank_day"] = state.world_day_f() - 1
    s = core.apply_choice(p, "vault")
    assert _hint(s, "collect_interest").startswith("receive ◈")
    core.apply_choice(p, "back")
    p["gold"] = 100
    p["inventory"]["repair_token"] = 1
    s = core.apply_choice(p, "pawn")
    sells = [o for o in s.options if o.id.startswith("sell_")]
    assert sells and all(o.hint.startswith("receive ◈") for o in sells)


def test_the_night_job_says_receive():
    p = playing("nightpay")
    p["level"] = economy.NIGHT_SLOT_LEVEL
    s = core.apply_choice(p, "lodge")
    assert _hint(s, "night_work").startswith("receive ◈")


# ── 3. the enemy sheet lands with the scene ──────────────────────────────

def test_enemy_head_is_not_deferred_by_the_typewriter():
    html = render._enemy_head_html(
        {"hp": 10, "hp_max": 10, "atk": 3, "def": 1})
    assert 'class="ehead"' in html
    assert "later" not in html


# ── 4. the pane script carries the new interactions ──────────────────────

def test_pane_script_has_digit_keys_fast_pen_and_scroll():
    js = pane._JS
    assert "keydown" in js and "'1'" in js and "'9'" in js
    assert "fast ? 2 : 7" in js                  # click → 4× typewriter
    assert "scrollIntoView" in js                # mobile walks up to the art
    assert "max-width: 520px" in js


def test_tipbox_answers_touch():
    assert "pointerdown" in render.TIP_JS
    assert "touch" in render.TIP_JS
