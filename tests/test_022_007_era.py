"""022/007 — the era, card side.

Prestige is written server-side at doc creation; the plugin only READS
it: the convenience doors (Arcanum, Relay) open from level 1 for a
reincarnated hand, the glyph rides the sheet, and the Stone shows the
Stone of Eras. Power is untouched — that's the law, and it's tested.
"""

from plugin_linear_ascent import economy, sheet
from plugin_linear_ascent.engine import core, state


def fresh():
    return state.new_player("test-user-022-007")


def choose(p, option="", text=""):
    return core.apply_choice(p, option, text)


def create_character(p, race="human", clazz="warrior", name="Testa"):
    core.current_scene(p)
    while p["stage"] == "intro":
        choose(p, "1")
    choose(p, race)
    choose(p, clazz)
    choose(p, text=name)
    return p


def reincarnated(p, points=1, tiers=("final_blow",)):
    p["prestige"] = {"points": points, "eras": [1], "tiers": list(tiers)}
    return p


def test_prestige_reads_zero_on_a_first_era_doc():
    p = create_character(fresh())
    assert state.prestige(p) == 0


def test_arcanum_opens_at_level_one_for_reincarnated_hands():
    p = reincarnated(create_character(fresh()))
    assert p["level"] < economy.ARCANUM_LEVEL
    s = core.current_scene(p)
    arc = next(o for o in s.options if o.id == "arcanum")
    assert not arc.locked
    s = choose(p, "arcanum")
    assert "ARCANUM" in s.eyebrow.upper()


def test_relay_opens_at_level_one_for_reincarnated_hands():
    p = reincarnated(create_character(fresh()))
    p["_world"] = {"frontier": 3, "inbox_count": 0,
                   "census": {"total": 1, "by_floor": {}}}
    assert p["level"] < economy.RELAY_LEVEL
    s = core.current_scene(p)
    relay = next(o for o in s.options if o.id == "relay")
    assert not relay.locked


def test_doors_stay_locked_without_prestige():
    p = create_character(fresh())
    p["_world"] = {"frontier": 3, "inbox_count": 0,
                   "census": {"total": 1, "by_floor": {}}}
    s = core.current_scene(p)
    assert next(o for o in s.options if o.id == "arcanum").locked
    assert next(o for o in s.options if o.id == "relay").locked
    s = choose(p, "arcanum")
    assert "wants" in s.shard_note        # bounced with the reason


def test_prestige_grants_no_power():
    a = create_character(fresh())
    b = reincarnated(create_character(fresh()), points=3)
    assert state.atk(a) == state.atk(b)
    assert state.dfs(a) == state.dfs(b)
    assert state.max_hp(a) == state.max_hp(b)
    assert state.energy_cap_of(a) == state.energy_cap_of(b)


def test_sheet_glyph_one_per_era_capped_at_three():
    p = create_character(fresh(), name="Kettle")
    assert sheet.character_sheet(p)["name"] == "Kettle"
    reincarnated(p, points=2)
    assert sheet.character_sheet(p)["name"] == "Kettle ✦✦"
    reincarnated(p, points=7)
    assert sheet.character_sheet(p)["name"] == "Kettle ✦✦✦"


def test_stone_shows_the_stone_of_eras():
    p = create_character(fresh())
    p["_world"] = {"frontier": 4, "census": {"total": 1, "by_floor": {}},
                   "stone": ["Floor 1 — cleared"],
                   "eras": ["ERA 1 — fell on day 212 to Kettle and "
                            "11 blades"]}
    s = choose(p, "stone")
    text = "\n".join(s.body_lines)
    assert "THE STONE OF ERAS" in text
    assert "ERA 1 — fell on day 212 to Kettle" in text


def test_stone_hides_the_section_in_a_first_era_world():
    p = create_character(fresh())
    p["_world"] = {"frontier": 4, "census": {"total": 1, "by_floor": {}},
                   "stone": ["Floor 1 — cleared"], "eras": []}
    s = choose(p, "stone")
    assert "STONE OF ERAS" not in "\n".join(s.body_lines)
