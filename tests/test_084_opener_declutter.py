"""084 — the opener is the sheet: no headline/◇ plate/prose/You-line/
whisper on encounter openers; the [i] rides the stat slab, the name
rides the eyebrow; round cards keep their surfaces."""

from types import SimpleNamespace

from plugin_linear_ascent import render
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


def _arm(p, weapons, training):
    held = [weapons] if isinstance(weapons, str) else list(weapons)
    p["training"] = dict(training)
    p["slots"] = len(held)
    p["held"] = held
    p["gear"]["weapon"] = held[0]
    return p


def _enc(traits, name="Test Beast"):
    return SimpleNamespace(id="test_beast", name=name,
                           prose="It waits.", weight=1,
                           traits=tuple(traits), kind="", was="")


def _opener(p, traits=()):
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, _enc(traits), "wilds")
    e = p["encounter"]
    e["range"] = "at_range"
    e["gap"] = 1
    return combat.fight_scene(p, fl, opener=True), fl


def test_the_opener_is_the_sheet_and_nothing_else():
    p = _arm(_classless("084-op-1"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s, fl = _opener(p)
    # the scene itself sheds the prose surfaces
    assert s.support == ""
    assert s.shard_note == ""
    assert not any("You — ATK" in ln for ln in s.body_lines)
    assert not any("It waits." in ln for ln in s.body_lines)
    html = render.render_scene_fragment(s)
    assert 'class="foesheet"' in html
    assert 'class="headline' not in html
    assert 'class="ehead"' not in html
    # (the ◇ verdicts survive only inside the [i] dossier attributes)
    assert "It is between you and the way forward." not in html
    assert "hits harder than you do" not in html


def test_the_i_rides_the_slab_and_the_name_rides_the_eyebrow():
    p = _arm(_classless("084-op-2"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s, fl = _opener(p)
    html = render.render_scene_fragment(s)
    slab = html.split('class="estat"')[1].split("</div>")[0]
    assert 'class="info"' in slab
    eyebrow = html.split('class="eyebrow type">')[1].split("</div>")[0]
    # the specimen tag may ride after the name ("Test Beast — runt")
    assert "Test Beast" in eyebrow
    # no headline — the eyebrow is the card's only visible name line
    # (the dossier attributes and data-foe3d may still carry it)
    assert 'class="headline' not in html


def test_cells_share_one_row_with_white_text():
    p = _arm(_classless("084-op-3"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    s, fl = _opener(p, ("fly",))
    html = render.render_scene_fragment(s)
    css = render.SCENE_CSS
    assert ".foesheet{display:flex;" in css
    assert "grid-template-columns" not in css.split(".foesheet{")[1][:200]
    cell_css = css.split(".foesheet .fscell{")[1].split("}")[0]
    assert "border" not in cell_css
    assert "background:#26241f" in cell_css
    # labels no longer carry per-type inline ink — white via CSS
    assert '<span class="fsbig">' in html


def test_foehint_x_is_wired_in_the_pane():
    # R-0055-1: the ✕ posts foehint_close — it must sit in the pane's
    # delegated data-opt wiring or it is a dead button in the browser.
    from plugin_linear_ascent import pane
    assert "button.x[data-opt]" in pane._JS


def test_round_cards_keep_their_surfaces():
    p = _arm(_classless("084-op-4"), "rusted_sword",
             {"blade": 6, "bow": 0, "staff": 0})
    _opener(p)
    core.apply_choice(p, "attack")
    if p.get("encounter"):
        s = core.current_scene(p)
        if s.foe_sheet is None:  # a real round card
            assert s.support == "It is between you and the way forward."
