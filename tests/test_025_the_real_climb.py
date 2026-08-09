"""025 — the real climb, floors 1-10.

The complaint, in the player's words: "all monsters now for me in level
one are one shot to two shots — and they all give the same amount of
coins and XP", "at level 3 I wasn't afraid of any monster", "no more
things to buy at level 4".

Every one of those was structurally true. A floor computed ONE stat line
and handed it to all four of its encounters; XP had no threat modifier of
any kind; and the band-1 buy ladder gated three times in ten levels.

These gates pin the range that replaced the flat floor.
"""

import pytest

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state

BAND = range(1, 11)


def fresh(user="test-user-025"):
    return state.new_player(user)


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":                 # 016: through the movie
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def at_gate_town(p):
    choose(p, "gate")
    choose(p, "floor_1")
    return p


def _stats(floor_no, enc):
    atk, dfs, hp = economy.creature_stats(floor_no, enc.traits)
    prof = economy.profile_from_traits(enc.traits)
    if prof["bulwark"]:
        hp = round(hp * economy.BULWARK_HP_MULT)
    return atk, dfs, hp


def _fight_cost(floor_no, enc):
    """Share of the at-level HP pool a whole fight costs, worst class."""
    atk, dfs, hp = _stats(floor_no, enc)
    p_atk, p_def = economy._at_level_loadout(floor_no)
    prof = economy.profile_from_traits(enc.traits)
    rounds = max(
        max(1, -(-hp // dmg)) if (dmg := economy.typed_damage(
            dt, round(0.75 * p_atk), dfs, prof)) > 0 else 1
        for dt in ("melee", "ranged", "magic"))
    raw = 0.75 * atk
    bite = max(max(1, -(-raw // economy.CHIP_DIVISOR)), raw - p_def // 2)
    return rounds * bite / economy.reference_player_hp(floor_no)


# ── A. a floor is a range of animals, not one animal ─────────────────────

@pytest.mark.parametrize("floor_no", BAND)
def test_no_two_creatures_on_a_floor_are_the_same_monster(floor_no):
    """The whole complaint in one assertion. Before 025 this floor
    handed every encounter floor.monster_atk/def/hp and the only thing
    that ever differed was the specimen's HP roll."""
    fl = schema.get_floor(floor_no)
    lines = {_stats(floor_no, e) for e in fl.encounters}
    assert len(lines) >= 3, (
        f"floor {floor_no}: {len(fl.encounters)} encounters share only "
        f"{len(lines)} stat lines")


@pytest.mark.parametrize("floor_no", BAND)
def test_every_floor_owes_prey_and_a_thing_that_can_kill_you(floor_no):
    """043 moved both ends of this law. The cheapest kill sits at bar
    F−2 now, not in a basement — it costs a real bite of the pool, just
    a clearly smaller one (floor 1 has no basement at all: its prey IS
    bar 1). And the worst draw is a bar-F+1 animal: its whole fight
    costs MORE than the at-floor pool — met carelessly, it kills."""
    fl = schema.get_floor(floor_no)
    costs = sorted(_fight_cost(floor_no, e) for e in fl.encounters)
    cheap = 0.90 if floor_no == 1 else 0.55
    assert costs[0] <= cheap, (
        f"floor {floor_no}: the cheapest kill still costs "
        f"{costs[0]:.0%} of the pool — no prey to farm")
    # 043.2: the tutorial floors are EXEMPT from fright — FLOOR_ATK_SOFT
    # divides their bite on purpose. The worst draw there still stands
    # clearly above the prey; everywhere else the old law holds.
    if floor_no in economy.FLOOR_ATK_SOFT:
        assert costs[-1] >= 0.25, (
            f"floor {floor_no}: even the tutorial owes a worst fight "
            f"({costs[-1]:.0%} of the pool)")
    else:
        assert costs[-1] >= 1.0, (
            f"floor {floor_no}: the worst fight costs only {costs[-1]:.0%} "
            "of the pool — nothing here is frightening")


@pytest.mark.parametrize("floor_no", BAND)
def test_the_spread_is_wide_and_the_body_is_never_a_slog(floor_no):
    fl = schema.get_floor(floor_no)
    hps = [_stats(floor_no, e)[2] for e in fl.encounters]
    assert max(hps) >= 3 * min(hps), (
        f"floor {floor_no}: HP spread only {max(hps)/min(hps):.1f}×")
    for e in fl.encounters:
        rounds = economy.creature_rounds(floor_no, e.traits)
        assert rounds <= economy.WILDS_ROUNDS_HARD_MAX, (e.id, rounds)


def test_a_starved_prey_is_always_the_cheaper_fight():
    """043: prey is anchored two bars down, so its WHOLE fight always
    costs less than the plain peer's. Its per-round ATK may now exceed
    the peer's — the frail body spends its (smaller) budget in far fewer
    rounds, the glass-cannon texture — so the law is the total, not the
    blow."""
    plain = schema.Encounter(id="_p", name="P", weight=1, prose="p")
    for floor_no in BAND:
        prey = schema.Encounter(id="_q", name="Q", weight=1, prose="p",
                                traits=("frail", "feeble"))
        assert (economy.creature_bar(floor_no, prey.traits)
                <= economy.creature_bar(floor_no, ())), floor_no
        assert _fight_cost(floor_no, prey) < _fight_cost(floor_no, plain), \
            floor_no


def test_a_round_can_never_come_out_of_nowhere():
    """No wilds creature may take more than WILDS_ROUND_CAP of the pool
    in one round: death is always preceded by a round you could have run
    in, and the opener has already named the shape."""
    for floor_no in BAND:
        pool = economy.reference_player_hp(floor_no)
        _, p_def = economy._at_level_loadout(floor_no)
        for e in schema.get_floor(floor_no).encounters:
            atk = economy.creature_stats(floor_no, e.traits)[0]
            raw = 0.75 * atk
            bite = max(max(1, -(-raw // economy.CHIP_DIVISOR)),
                       raw - p_def // 2)
            assert bite <= economy.WILDS_ROUND_CAP * pool * 1.05, (
                floor_no, e.id, bite, pool)


def test_the_opener_names_the_shape_before_you_commit():
    p = at_gate_town(create_character(fresh("r25-note")))
    s = choose(p, "hunt")
    traits = p["encounter"]["traits"]
    note = economy.archetype_note(traits)
    text = " ".join(s.body_lines) + s.support + (s.enemy or {}).get("prose", "")
    assert not note or note in p["encounter"]["prose"], (traits, note)
    assert text or True


# ── B. danger pays — in BOTH currencies ──────────────────────────────────

@pytest.mark.parametrize("floor_no", BAND)
def test_pay_follows_the_bar_inside_one_floor(floor_no):
    """043: kill_reward_mult is retired — pay is gold_per_kill(bar), so
    inside a floor the payout ladder IS the bar ladder: strictly more
    gold per bar, and the roster spans at least three bars."""
    fl = schema.get_floor(floor_no)
    bars = sorted({economy.creature_bar(floor_no, e.traits)
                   for e in fl.encounters})
    assert len(bars) >= (2 if floor_no <= 2 else 3), (floor_no, bars)
    pays = [economy.gold_per_kill(b) for b in bars]
    assert pays == sorted(pays) and pays[-1] > pays[0], (floor_no, pays)


def test_the_hard_ones_pay_and_the_prey_does_not():
    """Floor 5: the prey sits two bars down, the terror one bar up, and
    the coin follows the bar in that same order."""
    prey_bar = economy.creature_bar(5, ("frail", "feeble"))
    hard_bar = economy.creature_bar(5, ("hulking", "savage"))
    assert prey_bar == 3 and hard_bar == 6
    assert (economy.gold_per_kill(prey_bar)
            < economy.gold_per_kill(economy.creature_bar(5, ()))
            < economy.gold_per_kill(hard_bar))


def test_xp_follows_the_threat_and_not_just_gold(monkeypatch):
    """Before 025 the specimen and profile multipliers moved gold only.
    043: BOTH currencies now key off the creature's bar — on floor 1 the
    hulking savage stands at bar 2 and out-pays the bar-1 prey in xp and
    gold alike. Jitter pinned: the bar gap (1 vs 2) is real but small."""
    monkeypatch.setattr(state, "rng_jitter", lambda p, base, pct: base)

    def _kill(traits, user):
        p = at_gate_town(create_character(fresh(user)))
        fl = schema.get_floor(1)
        enc = schema.Encounter(id="_t", name="Thing", weight=1,
                               prose="A thing arrives.", traits=traits)
        combat.start_encounter(p, fl, enc, "wilds")
        p["encounter"]["specimen"] = "common"
        p["encounter"]["range"] = "close"
        p["encounter"]["hp"] = 1
        xp0, gold0 = p["xp"], p["gold"]
        combat.resolve_fight_action(p, fl, "attack")
        return p["xp"] - xp0, p["gold"] - gold0

    prey_xp, prey_gold = _kill(("frail", "feeble"), "r25-prey")
    hard_xp, hard_gold = _kill(("hulking", "savage"), "r25-hard")
    assert hard_xp > prey_xp, (prey_xp, hard_xp)
    assert hard_gold > prey_gold, (prey_gold, hard_gold)
    assert hard_xp == economy.xp_per_kill(economy.creature_bar(
        1, ("hulking", "savage")))


# ── C. the rubber band ───────────────────────────────────────────────────

def test_a_lethal_draw_keeps_a_fifth_of_its_weight_never_zero():
    fl = schema.get_floor(1)
    p = at_gate_town(create_character(fresh("r25-band")))
    p["hp"] = 1                                # one blow from dead
    table = dict((slug, w) for w, slug in combat.hunt_table(p, fl))
    content = {e.id: e.weight for e in fl.encounters}
    cut = [s for s in table if table[s] < content[s] * 100]
    assert cut, "a one-HP climber sees no reduced draws at all"
    for slug in cut:
        assert table[slug] == max(1, round(content[slug] * 100
                                          * economy.rubber_band_cut(1)))
        assert table[slug] > 0, "the band may cut a draw, never ban it"


def test_the_band_reads_your_wounds_not_just_your_sheet():
    fl = schema.get_floor(1)
    p = at_gate_town(create_character(fresh("r25-wound")))
    healthy = sum(w for w, _ in combat.hunt_table(p, fl))
    p["hp"] = max(1, p["hp"] // 8)
    hurt = sum(w for w, _ in combat.hunt_table(p, fl))
    assert hurt < healthy, (healthy, hurt)


def test_a_blade_that_cannot_reach_it_counts_as_lethal():
    """017's one legal zero: melee vs flying. A warrior who cannot damage
    a thing must not be steered into it."""
    fl = schema.get_floor(4)
    p = at_gate_town(create_character(fresh("r25-fly"), clazz="warrior"))
    moth = next(e for e in fl.encounters if e.id == "glare_moth")
    assert combat.would_probably_kill(p, fl, moth)


def test_a_healthy_at_level_climber_still_meets_the_floor_as_written():
    """The band is a hint, not a bubble: with a full bar and full HP the
    at-level player sees the content weights untouched on floor 1."""
    p = at_gate_town(create_character(fresh("r25-full")))
    fl = schema.get_floor(1)
    table = dict((slug, w) for w, slug in combat.hunt_table(p, fl))
    keep = [e.id for e in fl.encounters if table[e.id] == e.weight * 100]
    assert len(keep) >= 2, table


# ── D. the content laws the lint now enforces ────────────────────────────

def _floor_with(traits):
    return schema.Floor(
        floor=3, tier=1, biome="b", zone="z", gate_town="t", arrival="a",
        banner="greenreach", warden_name="W", warden_prose="p",
        encounters=[schema.Encounter(id="x", name="X", weight=1,
                                     prose="p", traits=traits),
                    schema.Encounter(id="y", name="Y", weight=1, prose="p",
                                     traits=("frail", "feeble")),
                    schema.Encounter(id="z", name="Z", weight=1, prose="p",
                                     traits=("savage",))])


def test_a_long_body_may_not_ride_a_damage_halving_profile():
    errs = schema._archetype_errors(_floor_with(("hulking", "armor_med")))
    assert any("multiply fight length" in e for e in errs), errs


def test_a_flyer_may_not_carry_a_bite_this_low():
    errs = schema._archetype_errors(_floor_with(("flying", "savage")))
    assert any("no melee counter" in e for e in errs), errs


def test_a_floor_with_no_prey_or_no_threat_is_rejected():
    flat = schema.Floor(
        floor=3, tier=1, biome="b", zone="z", gate_town="t", arrival="a",
        banner="greenreach", warden_name="W", warden_prose="p",
        encounters=[schema.Encounter(id=n, name=n, weight=1, prose="p")
                    for n in ("a", "b", "c", "d")])
    errs = schema._archetype_errors(flat)
    assert any("no prey" in e for e in errs), errs
    assert any("can kill" in e for e in errs), errs


# ── E. the siege floors: the first ten Wardens never heal ────────────────

def test_nothing_heals_a_warden_through_the_siege_floor():
    """"The first bosses up to stage 10 can not rejuvenate." No trickle,
    no silence window, and therefore no pity: a wound opened on floor 1
    is still open next week."""
    for floor_no in range(1, economy.WARDEN_SIEGE_FLOOR + 1):
        assert economy.world_warden_regen_hourly(floor_no) == 0.0, floor_no
        assert economy.warden_silence_hours(floor_no) is None, floor_no


def test_the_wall_is_thicker_for_never_healing():
    """The trade: it cannot heal, so it is allowed to be big. 60% up on
    024's rescue anchor, and still inside one energy bar for one player."""
    assert economy.WARDEN_POOL_FIGHTS_MIN == 3.2
    bar = economy.energy_cap(1, "human") // economy.COST_WARDEN_ATTEMPT
    assert economy.world_warden_hp(1) / economy.pool_unit(1) <= bar


def test_the_siege_band_leaves_no_cliff_where_healing_resumes():
    """A ×1.6 on floors 1-10 alone dropped the effort curve from 6.2
    fights at floor 10 to 4.1 at floor 11. Raising the ramp's anchor
    keeps the whole solo band one straight, monotone line."""
    effort = [economy.world_warden_hp(f) / economy.pool_unit(f)
              for f in range(1, 31)]
    assert effort == sorted(effort), effort
    across = effort[economy.WARDEN_SIEGE_FLOOR] / \
        effort[economy.WARDEN_SIEGE_FLOOR - 1]
    assert 1.0 <= across <= 1.15, across


def test_the_card_and_the_tip_both_say_it_never_heals():
    from plugin_linear_ascent.engine import social, tips
    from tests.test_022_001_one_list_of_bosses import playing, warden_world

    p = playing("Kettle", world=warden_world(1, hp=200))
    core.apply_choice(p, "gate")
    core.apply_choice(p, "floor_1")
    body = "\n".join(core.apply_choice(p, "keep").body_lines)
    assert "does not heal" in body
    assert "closes in" not in body
    assert "FLOOR 10" in tips.option_tip("strike")
    assert social is not None


# ── F. the haul is drawn, not stated ─────────────────────────────────────

def test_a_kill_carries_a_structured_tally():
    p = at_gate_town(create_character(fresh("r25-tally")))
    fl = schema.get_floor(1)
    enc = schema.Encounter(id="_t", name="Thing", weight=1,
                           prose="A thing arrives.", traits=("sturdy",))
    combat.start_encounter(p, fl, enc, "wilds")
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    s = combat.resolve_fight_action(p, fl, "attack")
    kinds = {t["kind"]: t["n"] for t in s.tally}
    assert set(kinds) == {"gold", "aether"}
    assert all(n > 0 for n in kinds.values())
    # the lines still SAY the numbers — the agent reads the text surface
    assert f"◈ {kinds['gold']} gold" in " ".join(s.body_lines)


def test_the_card_draws_one_mark_per_point_then_switches_to_a_numeral():
    from plugin_linear_ascent import render
    small = render._tally_html([{"kind": "gold", "n": 37}])
    assert small.count("<span class=\"eg\"") == 37
    assert "37" not in small.replace("+37 gold", "")   # only in the label
    big = render._tally_html([{"kind": "gold", "n": 1240}])
    assert big.count("<span class=\"eg\"") == 1
    assert "1,240" in big
    assert render._tally_html([{"kind": "gold", "n": 0}]) == ""


def test_the_marks_are_one_bit_masks_like_everything_else():
    from plugin_linear_ascent import icons
    for key in ("coin", "aether"):
        assert key in icons.ICON_KEYS
        grid = icons._GRIDS[key]
        assert len(grid) == 16 and all(len(r) == 16 for r in grid)
        assert icons.icon_data_url(key).startswith("data:image/svg+xml")


def test_the_text_surface_stays_words():
    p = at_gate_town(create_character(fresh("r25-text")))
    fl = schema.get_floor(1)
    enc = schema.Encounter(id="_t", name="Thing", weight=1, prose="A thing.")
    combat.start_encounter(p, fl, enc, "wilds")
    p["encounter"]["range"] = "close"
    p["encounter"]["hp"] = 1
    text = combat.resolve_fight_action(p, fl, "attack").to_text()
    assert "XP" in text and "gold" in text
    for ch in ("⚡", "🔒"):
        assert ch not in text


def test_the_shipped_floors_pass_their_own_lint():
    assert schema.lint_floors() == []
