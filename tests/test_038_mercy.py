"""038 — the mercy at the center of the game (world-lore §5): a kill
FREES what it strikes. The kill card, the kill animation, and the [i]
dossier all speak per kind — a Native is CURED, a Pressed conscript
DIES (plainly, no triumph), a Wrongmade is EVICTED. Legacy floors
(kind == "") keep the old card word for word.

These tests inject `breed`/`was` into the runtime encounter directly so
they hold no matter where the floor-YAML rewrite stands.
"""

import dataclasses
from types import SimpleNamespace

import pytest

from plugin_linear_ascent.content import schema
from plugin_linear_ascent.engine import combat, core, state


def fresh(user="test-user-038"):
    return state.new_player(user)


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
    p["encounter"]["range"] = "close"
    return p


def slay(p):
    """Land the kill whatever the dice say — pin the monster to 1 HP
    and the player to plenty until the victory card comes back."""
    for _ in range(30):
        p["hp"] = 500
        p["encounter"]["hp"] = 1
        p["encounter"]["atk"] = 1
        p["encounter"]["range"] = "close"
        s = choose(p, "attack")
        if p["encounter"] is None:
            return s
    raise AssertionError("the kill never landed")


def kinded_fight(p, breed, was=""):
    in_fight(p)
    p["encounter"]["breed"] = breed
    p["encounter"]["was"] = was
    return p


def card_text(s):
    return " ".join([s.headline, s.support] + list(s.body_lines)).lower()


# ── the kill card speaks per kind ───────────────────────────────────────

def test_native_kill_is_a_cure():
    p = at_gate_town(create_character(fresh("038-native")))
    kinded_fight(p, "native", was="a plain granary rat")
    name = p["encounter"]["name"]
    s = slay(p)
    assert s.headline == f"{name} — freed"
    assert "A plain granary rat" in s.support          # the `was` walks off
    assert "fever" in s.support.lower()
    assert "defeated" not in card_text(s)
    assert "slain" not in card_text(s)


def test_native_without_was_still_reads_as_a_cure():
    p = at_gate_town(create_character(fresh("038-native-bare")))
    kinded_fight(p, "native", was="")
    name = p["encounter"]["name"]
    s = slay(p)
    assert s.headline == f"{name} — freed"
    assert "cured" in s.support
    assert "defeated" not in card_text(s)


def test_pressed_kill_is_a_death_and_takes_no_bow():
    p = at_gate_town(create_character(fresh("038-pressed")))
    kinded_fight(p, "pressed")
    name = p["encounter"]["name"]
    s = slay(p)
    assert s.headline == f"{name} falls"
    assert "conscript" in s.support.lower()
    assert "no ghost" in s.support.lower()
    for word in ("defeated", "slain", "triumph", "glory", "victory"):
        assert word not in card_text(s)
    assert "!" not in s.headline + s.support


def test_wrongmade_kill_is_an_eviction():
    p = at_gate_town(create_character(fresh("038-wrongmade")))
    kinded_fight(p, "wrongmade")
    name = p["encounter"]["name"]
    s = slay(p)
    assert s.headline == f"{name} — evicted"
    assert "comes apart" in s.support
    assert "drains downward" in s.support               # it leaves, it
    assert "defeated" not in card_text(s)               # doesn't die


def test_legacy_kind_keeps_todays_copy_word_for_word():
    p = at_gate_town(create_character(fresh("038-legacy")))
    in_fight(p)
    p["encounter"]["breed"] = ""                        # floors 11-100
    p["encounter"]["was"] = ""
    name = p["encounter"]["name"]
    s = slay(p)
    assert s.headline == f"{name} defeated"
    assert s.support == "The wilds go quiet around you."


# ── the Warden is Wrongmade by definition ───────────────────────────────

@pytest.mark.reel   # the kill arms the 033 fall reel — keep the
def test_warden_victory_is_an_eviction_and_keeps_the_first_clear_reel():
    # auto-stepper from clicking past the victory card
    p = at_gate_town(create_character(fresh("038-warden")))
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, None, kind="warden")
    assert p["encounter"]["breed"] == "wrongmade"
    s = slay(p)
    assert s.headline == f"{fl.warden_name} — evicted — the floor is opened"
    assert "veil" in s.support and "brightens" in s.support
    assert "defeated" not in card_text(s)
    # 033's fall-reel machinery is intact
    assert s.fx == "ascent_open"
    assert [o.id for o in s.options] == ["next", "skip"]
    assert p["movie_floor"] == 2 and p["movie_beat"] == -2
    assert p["kill_receipt"]["gold"] and p["kill_receipt"]["loot"]
    assert p["unlocked_floor"] == 2


@pytest.mark.reel
def test_repeat_warden_kill_stays_eviction_without_the_reel():
    p = at_gate_town(create_character(fresh("038-warden-again")))
    p["unlocked_floor"] = 5                             # not a first clear
    fl = schema.get_floor(1)
    combat.start_encounter(p, fl, None, kind="warden")
    s = slay(p)
    assert s.headline == f"{fl.warden_name} — evicted"
    # 049: the warden slug is rebuilt from the floor, so the fx ladder
    # finds the typed floor-1 eviction reel for this race and weapon line
    assert s.fx == "warden_001_evicted_human_blade"


# ── kind and was thread from content to the runtime encounter ───────────

def test_start_encounter_threads_kind_and_was():
    p = at_gate_town(create_character(fresh("038-thread")))
    fl = schema.get_floor(1)
    enc = dataclasses.replace(fl.encounters[0], kind="native",
                              was="a marsh hare")
    combat.start_encounter(p, fl, enc)
    assert p["encounter"]["breed"] == "native"
    assert p["encounter"]["was"] == "a marsh hare"
    s = combat.fight_scene(p, fl)
    assert s.enemy["breed"] == "native"                 # additive payload
    assert s.enemy["was"] == "a marsh hare"             # keys (wire law)


# ── _kill_fx: per-creature, then the kind's generic, then nothing ───────

def test_kill_fx_native_prefers_the_creatures_own_freed_gif(monkeypatch):
    have = {"hedge_rat_freed", "native_freed"}
    monkeypatch.setattr(combat, "_event_art", lambda s: s in have)
    e = {"id": "hedge_rat", "breed": "native"}
    assert combat._kill_fx(e, "Hedge Rat", False) == "hedge_rat_freed"
    have.discard("hedge_rat_freed")
    assert combat._kill_fx(e, "Hedge Rat", False) == "native_freed"
    have.clear()
    assert combat._kill_fx(e, "Hedge Rat", False) == ""


def test_kill_fx_pressed_and_wrongmade_verbs(monkeypatch):
    have = set()
    monkeypatch.setattr(combat, "_event_art", lambda s: s in have)
    have.update({"goblin_straggler_fall", "pressed_fall"})
    e = {"id": "goblin_straggler", "breed": "pressed"}
    assert combat._kill_fx(e, "Goblin", False) == "goblin_straggler_fall"
    have.discard("goblin_straggler_fall")
    assert combat._kill_fx(e, "Goblin", False) == "pressed_fall"
    have.update({"rust_shade_evicted", "wrongmade_evicted"})
    e = {"id": "rust_shade", "breed": "wrongmade"}
    assert combat._kill_fx(e, "Rust Shade", False) == "rust_shade_evicted"
    have.discard("rust_shade_evicted")
    assert combat._kill_fx(e, "Rust Shade", False) == "wrongmade_evicted"


def test_kill_fx_never_falls_back_to_the_kill_families(monkeypatch):
    # a death reel on a cured Native tells the wrong story — kinded
    # creatures resolve to "" rather than borrow rat_kill
    monkeypatch.setattr(combat, "_event_art",
                        lambda s: s == "rat_kill")
    e = {"id": "hedge_rat", "breed": "native"}
    assert combat._kill_fx(e, "Hedge Rat", False) == ""


def test_kill_fx_first_clear_overrides_kinded_art(monkeypatch):
    monkeypatch.setattr(combat, "_event_art", lambda s: True)
    e = {"id": "rust_shade", "breed": "wrongmade"}
    assert combat._kill_fx(e, "Rust Shade", True) == "ascent_open"


def test_kill_fx_legacy_family_logic_is_untouched():
    # floors 11-100 carry no kind — the 009/011 family table holds,
    # including the family gif winning even on a first clear
    assert combat._kill_fx({"id": "feral_boar", "breed": ""},
                           "Feral Boar", False) == "boar_kill"
    assert combat._kill_fx({"id": ""}, "Warden Brackjaw",
                           True) == "brackjaw_kill"
    assert combat._kill_fx({"id": "rust_shade"}, "Rust Shade",
                           True) == "ascent_open"
    assert combat._kill_fx({"id": "rust_shade"}, "Rust Shade",
                           False) == ""


# ── content contract: `was` is a bare singular noun phrase ──────────────
# The kill card splices it mid-sentence ("{Was} shakes itself loose…"),
# so a trailing period or a leading capital reads as a broken sentence.

def test_was_values_are_bare_noun_phrases():
    for n in range(1, 11):
        fl = schema.get_floor(n)
        for enc in fl.encounters:
            w = getattr(enc, "was", "") or ""
            if not w:
                continue
            assert not w.rstrip().endswith("."), (n, enc.id, w)
            assert not w[:1].isupper(), (n, enc.id, w)


# ── the [i] dossier names what the thing is ─────────────────────────────

def test_dossier_lines_per_kind():
    floor = SimpleNamespace(encounters=[])
    native = combat._lore({"id": "x", "breed": "native",
                           "was": "a river otter"}, floor)
    assert native == "Fevered — a possession riding a river otter."
    pressed = combat._lore({"id": "x", "breed": "pressed"}, floor)
    assert pressed == ("A conscript of the tower. Killing it is a death, "
                       "not a cure.")
    wrong = combat._lore({"id": "x", "breed": "wrongmade"}, floor)
    assert wrong == "A made thing. Breaking it is eviction, not killing."
    for line in (native, pressed, wrong):
        assert len(line) <= 90


def test_dossier_appends_after_the_authored_lore():
    floor = SimpleNamespace(
        encounters=[SimpleNamespace(id="x", lore="Old line.")])
    got = combat._lore({"id": "x", "breed": "pressed"}, floor)
    assert got.startswith("Old line. ")
    assert "conscript" in got
    # legacy: no kind, the authored lore alone — unchanged
    assert combat._lore({"id": "x", "breed": ""}, floor) == "Old line."
    assert combat._lore({"id": "x"}, floor) == "Old line."
