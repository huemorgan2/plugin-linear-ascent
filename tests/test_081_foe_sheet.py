"""081 phase-6 — the encounter card reads at a glance: foe_sheet type
block replaces the verdict prose, the swap hint dismisses server-side,
and a pack weapon equips during the sizing-up (and only then)."""

from types import SimpleNamespace

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def _classless(uid):
    p = state.new_player(uid)
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1", "")
    core.apply_choice(p, "human", "")
    core.apply_choice(p, "", "Testa")
    return p


def _arm(p, weapons, training, slots=None):
    held = [weapons] if isinstance(weapons, str) else list(weapons)
    p["training"] = dict(training)
    p["slots"] = slots or len(held)
    p["held"] = held
    p["gear"]["weapon"] = held[0]
    return p


def _enc(traits, name="Test Beast"):
    return SimpleNamespace(id="test_beast", name=name,
                           prose="It waits.", weight=1,
                           traits=tuple(traits), kind="", was="")


def _start(p, traits, rng="at_range"):
    fl = schema.get_floor(1)
    s = combat.start_encounter(p, fl, _enc(traits), "wilds")
    e = p["encounter"]
    e["range"] = rng
    e["gap"] = 1 if rng == "at_range" else 0
    return combat.fight_scene(p, fl, opener=True)


# ── the sheet's payload, per type ──────────────────────────────────────

def test_foe_sheet_per_type():
    cases = {
        (): ("plain", 0, False),
        ("fly",): ("fly", 0, True),
        ("armoured",): ("armoured", 0, False),
        ("magic_resist",): ("magic_resist", 98, False),
    }
    for i, (traits, (t, pct, fly)) in enumerate(cases.items()):
        p = _arm(_classless(f"081-fs-{i}"), "rusted_sword",
                 {"blade": 6, "bow": 0, "staff": 0})
        s = _start(p, traits)
        fs = s.foe_sheet
        assert fs["type"] == t, traits
        assert fs["fly"]["yes"] is fly, traits
        assert fs["resist"]["pct"] == pct, traits
        assert fs["def"]["n"] == p["encounter"]["def"], traits
        assert fs["speed"]["n"] == economy.TYPE_SPEED[t], traits
        # the derivation stays honest to TYPE_MULT
        if t == "magic_resist":
            assert pct == round(
                (1 - economy.TYPE_MULT["magic_resist"]["staff"]) * 100)


def test_speed_cell_says_who_closes():
    p = _arm(_classless("081-fs-spd"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ("fly",))              # SPD 7 vs human base
    assert s.foe_sheet["speed"]["closes"] is True
    assert "closes distance fast" in s.to_text()


def test_round_cards_carry_no_sheet():
    p = _arm(_classless("081-fs-round"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    _start(p, ())
    fl = schema.get_floor(1)
    s = combat.fight_scene(p, fl)        # a round card, not the opener
    assert s.foe_sheet is None


def test_opener_body_keeps_prose_and_you_line_drops_verdict():
    p = _arm(_classless("081-fs-body"), "rusted_sword",
             {"blade": 4, "bow": 0, "staff": 0})
    s = _start(p, ("armoured",))
    text = " ".join(s.body_lines)
    assert "It waits." in text
    assert "You — ATK" in text
    # the old prose is gone from the body
    assert "Your Rusted Sword:" not in text
    assert "steel: half" not in text


def test_the_fragment_draws_the_sheet_big():
    p = _arm(_classless("081-fs-html"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ("fly",))
    html = render.render_scene_fragment(s)
    assert 'class="foesheet"' in html
    assert "FLY — YES" in html
    assert "best: bows and magic" in html
    assert 'class="foehint"' in html
    assert 'data-opt="foehint_close"' in html


def test_the_sheet_survives_the_dict_round_trip():
    # R-0053-1: worldd's pane rebuilds every scene from to_dict() —
    # a field the pair forgets never reaches a real player.
    from plugin_linear_ascent.engine.scene import Scene
    p = _arm(_classless("081-fs-trip"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ("fly",))
    back = Scene.from_dict(s.to_dict())
    assert back.foe_sheet == s.foe_sheet
    html = render.render_scene_fragment(back)
    assert 'class="foesheet"' in html
    assert 'class="foehint"' in html
    # a round card keeps None through the trip
    fl = schema.get_floor(1)
    r = combat.fight_scene(p, fl)
    assert Scene.from_dict(r.to_dict()).foe_sheet is None


def test_a_reload_during_the_sizing_up_keeps_the_opener():
    # R-0053-1 (second cause): the idempotent rebuild answered with a
    # bare round card while the player was still sizing up.
    p = _arm(_classless("081-fs-rebuild"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    _start(p, ("fly",))
    s = core.current_scene(p)
    assert s.foe_sheet is not None
    # once the fight has begun, the rebuild is a round card again
    core.apply_choice(p, "attack")
    if p.get("encounter"):
        assert core.current_scene(p).foe_sheet is None


# ── the dismissable swap hint ──────────────────────────────────────────

def test_foehint_close_is_a_doc_flag():
    p = _arm(_classless("081-fs-hint"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s = _start(p, ())
    assert s.foe_sheet["hint"] is True
    s = core.apply_choice(p, "foehint_close")
    assert p["foehint_done"] is True
    assert s.foe_sheet["hint"] is False
    assert "foehint" not in render.render_scene_fragment(s)


# ── the swap at the sizing-up ──────────────────────────────────────────

def _with_bow_in_pack(uid, rng="at_range"):
    p = _arm(_classless(uid), "rusted_sword",
             {"blade": 6, "bow": 2, "staff": 0})
    p["inventory"]["basic_bow"] = 1
    s = _start(p, ("fly",), rng=rng)
    return p, s


def test_pack_weapon_equips_at_the_sizing_up():
    p, s = _with_bow_in_pack("081-fs-swap")
    assert any(o.id == "pack" for o in s.options)
    acts, why = core.pack_actions(p, "basic_bow")
    assert acts and acts[0].id == "wear_basic_bow"
    assert "swap before the steel meets" in acts[0].hint
    rng_before = p.get("rng_counter", 0)
    s2 = core.apply_choice(p, "wear_basic_bow")
    assert p["gear"]["weapon"] == "basic_bow"
    assert p.get("encounter"), "the fight must survive the swap"
    assert s2.foe_sheet is not None      # the rebuilt opener card
    assert "Basic Bow" in " ".join(s2.body_lines)
    # replay determinism: the swap consumes no RNG draw
    assert p.get("rng_counter", 0) == rng_before


def test_swap_durability_stashes_like_a_road_swap():
    p, _ = _with_bow_in_pack("081-fs-dur")
    p.setdefault("durability", {})["weapon"] = 3     # worn sword
    core.apply_choice(p, "wear_basic_bow")
    assert p["durability_pack"]["rusted_sword"] == 3
    assert p["durability"]["weapon"] == economy.item_pool(
        economy.FORGE["basic_bow"])


def test_swap_refused_once_the_fight_has_begun():
    for i, spoil in enumerate(("attacked", "shot_used")):
        p, _ = _with_bow_in_pack(f"081-fs-late-{i}")
        p["encounter"][spoil] = True
        acts, why = core.pack_actions(p, "basic_bow")
        assert not acts
        assert "middle of this" in why
        s = core.apply_choice(p, "wear_basic_bow")
        assert p["gear"]["weapon"] == "rusted_sword"
        assert "re-rig" in (s.shard_note or "")
    # close quarters closes the window too
    p, s = _with_bow_in_pack("081-fs-close", rng="close")
    assert not any(o.id == "pack" for o in s.options)
    acts, _ = core.pack_actions(p, "basic_bow")
    assert not acts


def test_pack_row_answers_without_spending_a_round():
    p, _ = _with_bow_in_pack("081-fs-packrow")
    hp = p["hp"]
    fl = schema.get_floor(1)
    s = combat.resolve_fight_action(p, fl, "pack")
    assert "tap a weapon" in (s.shard_note or "")
    assert p["hp"] == hp
    assert not p["encounter"].get("attacked")
