"""008 — combat pace & variance: derived wilds HP, specimens, stew,
the dawn heal law (022/004), wardens untouched."""

from plugin_linear_ascent import economy
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh():
    return state.new_player("test-user-008")


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


def force_specimen(monkeypatch, specimen):
    """rng_pick returns `specimen` for specimen tables, real roll else."""
    real = state.rng_pick

    def fake(p, table):
        if any(k in economy.SPECIMENS for _, k in table):
            return specimen
        return real(p, table)
    monkeypatch.setattr(state, "rng_pick", fake)


# ── Derived wilds HP ─────────────────────────────────────────────────────

def test_wilds_hp_derived_from_rounds_budget():
    # floor 1: at-level damage budget × 2.5 rounds — a quick kill
    atk, dfs, hp = economy.monster_stats(1)
    assert (atk, dfs) == (5, 3)               # ATK/DEF curve untouched
    assert hp == 18                            # was 37 pre-008
    # HP grows with the floor — 046 exception: the reference hone is
    # frozen (lag 2) over the first floors of each band while m_def rides
    # the pillar, so the rounds-derived HP relaxes ≤ ~15% off the band
    # seam's spike before the climb resumes; steeper is a regression
    hps = [economy.monster_stats(f)[2] for f in range(1, 101)]
    assert all(b >= a * 0.85 for a, b in zip(hps, hps[1:]))
    assert hps[-1] == max(hps)                 # the climb still wins
    assert economy.wilds_rounds(1) == 2.5
    assert economy.wilds_rounds(50) == 7.0


def test_warden_baseline_unchanged_by_008():
    # 017: floors ≥ 21 wardens carry low/low defense tiers, so the
    # reference damage (and thus the ATK budget) re-tunes.  022/002:
    # the reference player is gear-carried and armor feeds HP, so ATK
    # re-derives once more — the HP column is pinned UNCHANGED from the
    # pre-022 curve: the retune moved who the warden is tuned against,
    # never how big a boss is.
    # 025 §4: band 1 sells a rung per level, so the at-level climber on
    # floors 2-10 is measurably better armed than the pre-025 reference
    # and the wardens there hit harder to match. The HP column is still
    # pinned unchanged — a boss's SIZE has never moved.
    # 046: re-pinned ON PURPOSE — every stat rides the pillar now, and
    # the rise (1.02) lives in the HP column. Floor 1 is byte-identical.
    baseline = {1: (15, 3, 70), 5: (52, 9, 217), 10: (176, 32, 891),
                15: (381, 118, 3652), 30: (16201, 6046, 251604),
                50: (1875077, 1149067, 71053914),
                75: (1304270270, 810829097, 82257613638),
                100: (913470296403, 572154256377, 95227900133612)}
    for f, want in baseline.items():
        assert economy.warden_stats(f) == want


# ── Specimens ────────────────────────────────────────────────────────────

def test_specimen_table_is_expectation_neutral():
    total = sum(s["weight"] for s in economy.SPECIMENS.values())
    assert total == 100
    hp_e = sum(s["weight"] * s["hp"]
               for s in economy.SPECIMENS.values()) / total
    gold_e = sum(s["weight"] * s["gold"]
                 for s in economy.SPECIMENS.values()) / total
    assert abs(hp_e - 1) <= 0.05
    assert abs(gold_e - 1) <= 0.05


def test_alpha_specimen_visible_and_buffed(monkeypatch):
    force_specimen(monkeypatch, "alpha")
    p = at_gate_town(create_character(fresh()))
    s = choose(p, "hunt")
    e = p["encounter"]
    assert e["specimen"] == "alpha"
    # 025: the floor's flat line is only the baseline now — the specimen
    # multiplies THIS creature's own archetype stats.
    fl = schema.get_floor(1)
    base_atk, _, base_hp = economy.creature_stats(fl.floor, e["traits"])
    assert e["atk"] == round(base_atk * 1.2)
    assert e["hp"] == round(base_hp * 2.0)
    # the tag is on the opener — fighting an alpha is an informed choice
    # (084: the eyebrow carries it now; the opener body is empty)
    from plugin_linear_ascent import render
    html = render.render_scene_fragment(s)
    eyebrow = html.split('class="eyebrow type">')[1].split("</div>")[0]
    assert "alpha" in eyebrow


def test_alpha_kill_drops_extra_loot(monkeypatch):
    force_specimen(monkeypatch, "alpha")
    p = at_gate_town(create_character(fresh()))
    choose(p, "hunt")
    p["training"]["blade"] = 10               # 084: no miss-roll flake
    p["encounter"]["range"] = "close"         # 002: skip the crossing
    p["encounter"]["hp"] = 1                  # next hit kills
    s = choose(p, "attack")
    assert p["encounter"] is None
    assert any("alpha spoils" in line for line in s.body_lines)
    assert p["inventory"].get("medgel") or p["inventory"].get("luck_charm")


def test_runt_pays_less_gold(monkeypatch):
    force_specimen(monkeypatch, "runt")
    monkeypatch.setattr(state, "rng_jitter", lambda p, base, pct: base)
    p = at_gate_town(create_character(fresh()))
    choose(p, "hunt")
    p["training"]["blade"] = 10               # 084: no miss-roll flake
    p["encounter"]["range"] = "close"         # 002: skip the crossing
    p["encounter"]["hp"] = 1
    gold_before = p["gold"]
    traits = p["encounter"]["traits"]
    choose(p, "attack")
    # 043: pay keys off the creature's bar; the specimen rides on top
    bar = economy.creature_bar(1, traits)
    expect = max(1, round(economy.gold_per_kill(bar)
                          * economy.SPECIMENS["runt"]["gold"]))
    assert p["gold"] - gold_before == expect


def test_wardens_never_roll_specimens():
    p = at_gate_town(create_character(fresh()))
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, None, "warden")
    e = p["encounter"]
    assert e["specimen"] == "common"
    assert (e["atk"], e["def"], e["hp"]) == economy.warden_stats(1)


# ── Hunter's stew ────────────────────────────────────────────────────────

def test_stew_heals_five_for_two_gold():
    p = at_gate_town(create_character(fresh()))
    p["hp"] = state.max_hp(p) - 20
    s = core.current_scene(p)
    assert any(o.id == "stew" for o in s.options)
    gold, hp = p["gold"], p["hp"]
    choose(p, "stew")
    assert p["gold"] == gold - economy.STEW_PRICE
    assert p["hp"] == hp + economy.STEW_HEAL_HP


def test_stew_caps_at_max_hp_and_needs_gold():
    p = at_gate_town(create_character(fresh()))
    p["hp"] = state.max_hp(p) - 2
    choose(p, "stew")
    assert p["hp"] == state.max_hp(p)          # capped, not overhealed
    p["hp"] = 10
    p["gold"] = 1
    s = choose(p, "stew")
    assert p["hp"] == 10 and p["gold"] == 1    # refused
    assert s.shard_note


def test_stew_available_at_the_lodge():
    p = create_character(fresh())
    p["hp"] = 10
    choose(p, "lodge")
    s = core.current_scene(p)
    assert any(o.id == "stew" for o in s.options)
    gold = p["gold"]
    choose(p, "stew")
    assert p["hp"] == 10 + economy.STEW_HEAL_HP
    assert p["gold"] == gold - economy.STEW_PRICE


# ── The dawn law (022/004 — replaced the Lodge's +20 special case) ───────

def test_dawn_heals_to_full_wherever_you_slept():
    p = create_character(fresh())
    p["hp"] = 10
    p["lodged_until_day"] = state.world_day() - 3   # rough sleep
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == state.max_hp(p)
    assert p["daily"]["dawn_healed"] is True


def test_lodge_adds_no_extra_healing_over_dawn():
    p = create_character(fresh())
    p["hp"] = 10
    p["lodged_until_day"] = state.world_day()  # slept inside last night
    p["daily"]["day"] = state.world_day() - 1
    state.touch_daily(p)
    assert p["hp"] == state.max_hp(p)          # same as the fields


def test_mid_day_hp_holds_until_dawn():
    p = create_character(fresh())
    p["hp"] = 6
    state.touch_daily(p)                       # same day — no boundary
    assert p["hp"] == 6


def test_lodge_copy_sells_safety_not_health():
    p = create_character(fresh())
    s = choose(p, "lodge")
    body = " ".join(s.body_lines)
    assert "Dawn closes wounds" in body
    assert "+20" not in body
