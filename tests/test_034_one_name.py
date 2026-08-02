"""004 — one name, one world.

The door asked for a username, the gate asked for a name, and the game
printed both as if they were the same person. They are one string now: one
word, unique in the world, and the words in "Master Chief" are joined
rather than refused.

worldd is the only judge of who already holds a name (it claims the row
before the engine runs and leaves the verdict on `_world`); these tests
cover the law itself and what the card says about each verdict.
"""

from plugin_linear_ascent.engine import core, names, state


def at_the_registrar(pid="t:namer", world=None):
    p = state.new_player(pid)
    if world is not None:
        p["_world"] = world
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    core.apply_choice(p, "human")
    core.apply_choice(p, "warrior")
    assert p["stage"] == "creation_name"
    return p


# ── the law ──────────────────────────────────────────────────────────────

def test_a_space_is_joined_not_refused():
    assert names.canonical("Master Chief") == "MasterChief"
    assert names.canonical("  Nyx of the Vale  ") == "NyxoftheVale"


def test_the_case_a_player_typed_is_the_case_that_carves():
    """Uniqueness is case-blind (worldd's index), but the legend keeps its
    capitals: MasterChief reads better on granite than masterchief."""
    assert names.canonical("MasterChief") == "MasterChief"


def test_only_what_granite_holds():
    assert names.canonical("Br@ck·jaw!") == "Brckjaw"
    assert names.canonical("iron_heart-3") == "iron_heart-3"
    assert names.canonical("«»") == ""                 # nothing left to carve


def test_every_script_carves():
    """The world is one world. A name in Cyrillic is a name — the alphabet
    the rule bans is punctuation and gaps, not other people's letters."""
    assert names.canonical("Криер") == "Криер"
    assert names.is_legal(names.canonical("Криер Два")) is True
    assert names.canonical("Криер Два") == "КриерДва"


def test_the_mason_stops_at_twenty_four():
    assert len(names.canonical("A" * 40)) == 24
    assert names.is_legal("A" * 24) and not names.is_legal("A" * 25)
    assert not names.is_legal("x") and not names.is_legal("")


# ── the gate ─────────────────────────────────────────────────────────────

def test_the_gate_asks_for_a_username_and_says_it_is_the_name():
    s = core.current_scene(at_the_registrar())
    said = " ".join([s.headline, s.support, s.shard_note])
    assert "username" in said.lower()
    assert "one word" in said.lower()          # the rule, before they type
    assert s.ask["label"] == "your username"
    assert s.awaits_text                       # the chat path still stands


def test_two_words_typed_become_one_name_and_the_card_says_so():
    p = at_the_registrar()
    s = core.apply_choice(p, "", "Master Chief")
    assert p["name"] == "MasterChief" and p["stage"] == "playing"
    assert "MasterChief" in s.headline
    # a silently different name is a worse welcome than an explained one
    assert any("MasterChief" in line and "gaps" in line
               for line in s.body_lines)


def test_a_name_the_world_already_holds_sends_you_back_to_the_registrar():
    p = at_the_registrar(world={"social": True, "name_claim": "taken"})
    s = core.apply_choice(p, "", "Fleet")
    assert p["stage"] == "creation_name" and not p.get("name")
    assert "Fleet already climbs" in s.shard_note
    assert "one name, one world" in s.shard_note
    assert s.ask                               # and the box is still there


def test_a_free_name_is_carved_and_nothing_is_said_about_it():
    p = at_the_registrar(world={"social": True, "name_claim": "created"})
    s = core.apply_choice(p, "", "Fleet")
    assert p["name"] == "Fleet" and p["stage"] == "playing"
    assert not any("gaps" in line for line in s.body_lines)


def test_a_name_of_nothing_but_punctuation_is_refused_by_the_engine_alone():
    """worldd never even claims this one — there is nothing to claim."""
    p = at_the_registrar()
    s = core.apply_choice(p, "", "«»")
    assert p["stage"] == "creation_name"
    assert "strokes" in s.shard_note


def test_offline_play_needs_no_registry():
    """A lone climber with no world (local backend) still gets a name."""
    p = at_the_registrar()
    assert not p.get("_world")
    core.apply_choice(p, "", "Solo")
    assert p["name"] == "Solo" and p["stage"] == "playing"
