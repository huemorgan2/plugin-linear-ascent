"""081 phase-5 — gear clarity: the item numbers ride the click path
(data-params → popup), the pawn broker names what he refuses instead of
quoting ◈ 0 or ignoring the tap, and held-slot pack rows say the move."""

from plugin_linear_ascent import economy, render
from plugin_linear_ascent.engine import core, state


def playing(name="Clarity"):
    p = state.new_player(f"t:{name}")
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    core.apply_choice(p, "", name)
    return p


def test_starter_weapon_cell_ships_params_on_the_click_path():
    p = playing("params")
    s = core.current_scene(p)
    html = render.render_scene_fragment(s)
    assert "data-params=" in html
    assert "ATK 5" in html          # rusted sword, level-1 hand
    # the popup prints them — template and styling both shipped
    assert "item.dataset.params" in render.INTERACT_JS
    assert '<div class="pstat">' in render.INTERACT_JS


def test_popup_action_labels_wear_brackets():
    assert '<span class="key">' in render.INTERACT_JS
    assert '.pmenu .pact .key::before{content:"[";' \
        in render.SCENE_CSS.replace("\n", "")


def test_the_broker_names_what_he_waves_off():
    p = playing("waved")
    p["inventory"] = {"rusted_shiv": 1, "gate_jerkin": 1}
    s = core.apply_choice(p, "pawn")
    text = " ".join(s.body_lines)
    assert "waves off" in text
    assert "Rusted Shiv" in text and "Gate-Issue Jerkin" in text
    assert "never lost to you" in text
    # no sell rows, no ◈ 0 offers for the refused pieces
    assert not any(o.id in ("sell_rusted_shiv", "sell_gate_jerkin")
                   for o in s.options)
    assert "◈ 0" not in text


def test_a_stale_sell_click_answers_with_the_waves_off_note():
    # a click from a scene rendered before the piece was refused (old
    # tab, old deploy) — _pawn_action answers with the note, not silence
    p = playing("stale")
    p["inventory"] = {"gate_jerkin": 1}
    core.apply_choice(p, "pawn")
    gold = p["gold"]
    s = core._pawn_action(p, "sell_gate_jerkin")
    assert "waves off" in (s.shard_note or "")
    assert p["gold"] == gold
    assert p["inventory"].get("gate_jerkin") == 1


def test_sellable_gear_still_gets_its_row():
    p = playing("seller")
    p["inventory"] = {"scrap_dagger": 1}
    s = core.apply_choice(p, "pawn")
    assert any(o.id == "sell_scrap_dagger" for o in s.options)
    assert not any("waves off" in ln for ln in s.body_lines)


def test_pack_weapon_hint_says_move_to_hand():
    p = playing("holder")
    p["gear"]["weapon"] = None
    p["inventory"]["scrap_dagger"] = 1
    acts, why = core.pack_actions(p, "scrap_dagger")
    assert acts and acts[0].label == "Hold"
    assert acts[0].hint.startswith("move to hand"), acts[0].hint
    # a worn piece keeps the swap-out phrasing
    p["gear"]["weapon"] = "rusted_sword"
    acts, _ = core.pack_actions(p, "scrap_dagger")
    assert acts[0].hint.startswith("swap out the Rusted Sword"), acts[0].hint
