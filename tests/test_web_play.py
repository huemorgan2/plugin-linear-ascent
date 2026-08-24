"""005 web play — the plugin's half: a pane that plays from the website
and a registrar that recognizes a name the door already carved.

The web pane is the SAME HTML as the Luna pane with three switches
flipped (API base, cookie auth, 401 → the site's door). The engine
skips the name ask entirely when the doc booted with a name — a web
account's username was claimed at signup, so the gate has nothing left
to ask.
"""

from plugin_linear_ascent import pane
from plugin_linear_ascent.engine import core, state


def at_the_race_pick(pid="t:webber", name=""):
    # 048: the class question is gone — the race pick is the last
    # choice before the registrar (or the welcome, if prenamed).
    p = state.new_player(pid)
    if name:
        p["name"] = name
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1")
    return p


# ── the registrar recognizes the door's name ─────────────────────────────

def test_a_prenamed_doc_skips_the_name_ask_entirely():
    p = at_the_race_pick(name="Webprobe")
    s = core.apply_choice(p, "elf")
    assert p["stage"] == "playing"
    assert p["name"] == "Webprobe"
    assert "Welcome to Roothollow, Webprobe" in s.headline
    assert not s.awaits_text


def test_an_unnamed_doc_still_meets_the_registrar():
    p = at_the_race_pick()
    s = core.apply_choice(p, "elf")
    assert p["stage"] == "creation_name"
    assert s.awaits_text


def test_the_prenamed_welcome_matches_the_typed_one():
    """One welcome, both doors: the pre-carved path and the typed path
    land on the same scene grammar (town, shard note, headline form)."""
    typed = at_the_race_pick(pid="t:typer")
    core.apply_choice(typed, "elf")
    st = core.apply_choice(typed, "", text="Typer")
    web = at_the_race_pick(pid="t:webber2", name="Webber")
    sw = core.apply_choice(web, "elf")
    assert st.eyebrow == sw.eyebrow
    assert st.shard_note == sw.shard_note
    assert typed["location"] == web["location"] == "town"


# ── the pane, parametrized ───────────────────────────────────────────────

def test_luna_pane_output_is_unchanged_by_default():
    html = pane.render_pane()
    assert "'/api/p/plugin-linear-ascent'" in html
    assert "const WEB = false;" in html
    assert "luna-request-auth" in html
    assert "luna-auth" in html
    assert "<title>" not in html


def test_web_pane_points_at_the_web_api_and_the_door():
    html = pane.render_pane(api_base="/play/api", web=True)
    assert "'/play/api'" in html
    assert "const WEB = true;" in html
    assert "'/#door-signin'" in html
    assert "<title>LINEAR ASCENT</title>" in html
    # the Luna base path must not survive into the web build
    assert "'/api/p/plugin-linear-ascent'" not in html


def test_both_panes_share_the_same_tabs_and_grammar():
    luna, web = pane.render_pane(), pane.render_pane(web=True)
    for chunk in ('data-tab="game"', 'data-tab="score"',
                  'data-tab="community"', "waking the lift"):
        assert chunk in luna and chunk in web


def test_labs_control_stays_reachable_on_a_phone():
    html = pane.render_pane(web=True)
    assert 'id="labsbtn"' in html
    assert "@media (max-width:520px)" in html
    assert ".sndbtn{flex:1 1 0;min-width:0" in html
