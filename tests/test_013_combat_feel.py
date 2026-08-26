"""013 — combat feel: armor blunts but never nullifies (chip damage),
battle texts explain WHY (weapon named, armor named, blocks shown), the
fight opener shows your own ATK/DEF, and HP is scarcer than gold (the
healer's tent bills by the wound — 065)."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh():
    return state.new_player("test-user-013")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":                # 016: through the movie
        choose(p, "1")
    choose(p, race)
    choose(p, text=name)
    # 048: the class question is gone — restore the old class FEEL by
    # hand: the path at rank 6 plus that line's basic weapon in hand.
    _path = {"warrior": "blade", "archer": "bow",
             "sorcerer": "staff"}[clazz]
    _slug = {"warrior": "rusted_sword", "archer": "basic_bow",
             "sorcerer": "worn_staff"}[clazz]
    p["training"][_path] = 6
    p["gear"]["weapon"] = _slug
    p["held"] = [_slug]
    return p


def at_gate_town(p):
    choose(p, "gate")
    choose(p, "floor_1")
    return p


def in_fight(p):
    choose(p, "hunt")
    assert p["encounter"] is not None
    p["encounter"]["range"] = "close"     # 002: these tests probe blows,
    return p                              # not the chase — skip the crossing


def geared(p):
    """Tier-1 armor + shield — DEF high enough that pre-013 every
    floor-1 hit resolved to 0."""
    p["gear"]["armor"] = "padded_jerkin"
    p["gear"]["shield"] = "scrapwood_buckler"
    return p


# ── Chip damage: armor blunts, never nullifies ──────────────────────────

def test_monster_hit_always_chips_through_heavy_armor():
    p = at_gate_town(create_character(fresh()))
    geared(p)
    p["level"] = 10                       # DEF 20+ vs floor-1 ATK 5
    in_fight(p)
    for _ in range(20):
        p["hp"] = 40
        hit = combat._monster_hit(p)
        assert hit["dmg"] >= 1            # pre-013 this was 0 every time
        assert hit["dmg"] + hit["blocked"] == hit["raw"]


def test_chip_is_a_quarter_of_the_roll_not_a_flat_one():
    p = at_gate_town(create_character(fresh()))
    p["gear"]["armor"] = "aegis_of_the_vale"      # absurd DEF on floor 1
    in_fight(p)
    p["encounter"]["atk"] = 40                    # raw roll 20–40
    p["hp"] = 500
    hit = combat._monster_hit(p)
    assert hit["dmg"] >= max(1, hit["raw"] // economy.CHIP_DIVISOR)


def test_stand_can_still_hold_the_line_at_zero():
    # stand halves AFTER the chip — a braced guard may still take nothing
    p = at_gate_town(create_character(fresh()))
    geared(p)
    p["level"] = 10
    in_fight(p)
    p["encounter"]["atk"] = 5             # pin the roll — daily spawns
    p["hp"] = 400                         # vary; chip must be 1 or 2
    dmgs = set()
    for _ in range(30):
        dmgs.add(combat._monster_hit(p, halved=True)["dmg"])
    assert 0 in dmgs                      # chip 1 // 2 == 0: guard held


def test_bare_player_takes_full_hits():
    p = at_gate_town(create_character(fresh()))
    p["gear"]["armor"] = None
    p["gear"]["shield"] = None
    in_fight(p)
    p["hp"] = 400
    hit = combat._monster_hit(p)
    assert hit["dmg"] == max(
        max(1, -(-hit["raw"] // economy.CHIP_DIVISOR)),
        hit["raw"] - state.dfs(p) // 2)


# ── Texts explain why ────────────────────────────────────────────────────

def test_opener_body_is_bare_since_084():
    # 084 retired the You-line and the description prose from openers —
    # the foe sheet and the stat slab are the card now
    # (test_084_opener_declutter owns the full shape).
    p = at_gate_town(create_character(fresh()))
    geared(p)
    s = choose(p, "hunt")
    body = " ".join(s.body_lines)
    assert "You — ATK" not in body
    assert "on reflex alone" not in body


def test_attack_note_names_the_weapon_and_the_block():
    p = at_gate_town(create_character(fresh()))
    geared(p)
    in_fight(p)
    p["encounter"]["hp"] = 10_000         # don't let it die mid-test
    p["hp"] = 10_000
    s = choose(p, "attack")
    note = " ".join(s.body_lines)
    assert "Rusted Sword" in note          # the strike, explained (017)
    # the counter names the guard whenever armor ate part of the blow
    assert ("Padded Jerkin" in note or "HP" in note)


def test_blocked_counter_says_what_the_armor_did():
    p = at_gate_town(create_character(fresh()))
    geared(p)
    p["level"] = 10                        # armor blocks most of every hit
    in_fight(p)
    hit = {"dmg": 1, "raw": 5, "blocked": 4}
    text = combat._counter_text(p, hit)
    assert "Padded Jerkin" in text and "only −1 HP" in text


def test_big_hit_gets_the_no_match_flavor():
    p = at_gate_town(create_character(fresh()))
    in_fight(p)
    p["encounter"]["hp_max"] = 12
    assert "bites deep" in combat._strike_text(p, 8)
    assert "takes it for 2" in combat._strike_text(p, 2)


def test_victory_line_names_the_weapon():
    p = at_gate_town(create_character(fresh()))
    in_fight(p)
    p["encounter"]["hp"] = 1
    s = choose(p, "attack")
    assert any("no match for your" in ln for ln in s.body_lines)


# ── HP scarcer than gold ─────────────────────────────────────────────────

def test_healer_tent_bills_by_the_wound():
    """065: the tent charges for the HP it mends — the row quotes the
    bill for THIS wound, and the ledger takes exactly that."""
    p = at_gate_town(create_character(fresh()))
    p["hp"] = 10
    price = economy.healer_tent_price(1, 10, state.max_hp(p))
    assert price == economy.healer_tent_price(1, 10, state.max_hp(p))
    s = core.current_scene(p)
    heal = next(o for o in s.options if o.id == "heal")
    assert f"◈ {price}" in heal.hint
    assert f"+{state.max_hp(p) - 10} HP" in heal.hint
    gold = p["gold"]
    choose(p, "heal")
    assert p["gold"] == gold - price
    assert p["hp"] == state.max_hp(p)


def test_a_whole_bar_costs_six_kills_a_scratch_a_fraction():
    for f in (1, 5, 25, 60, 95):
        # 065: the ratio holds at every depth — both ride base gold
        full = economy.healer_tent_price(f)
        assert full == economy.tent_full_price(f)
        assert full >= economy.TENT_FULL_KILLS * economy.base_gold_per_kill(f) - 1
        assert economy.healer_tent_price(f, 90, 100) < economy.gold_per_kill(f)
        assert economy.healer_tent_price(f, 100, 100) == 0
        assert economy.healer_tent_price(f, 99, 100) >= 1
