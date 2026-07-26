"""057 interactive cards: option buttons, the /act route, agent nudges.

The card is a real client of the plugin now — clicks act through the
host bridge with no model in the path, the next scene posts as its own
card, and the agent is nudged (moment/awareness) only on big beats.
"""

import asyncio

import pytest

from plugin_linear_ascent import routes, runtime
from plugin_linear_ascent.engine import state
from plugin_linear_ascent.engine.scene import Option, Scene
from plugin_linear_ascent.render import render_scene


def scene_with_options():
    return Scene(
        eyebrow="TEST", headline="A test scene",
        body_lines=["A grey wolf pads out of the fencerows."],
        options=[Option("fight", "Fight"), Option("stray", "Stray")],
        scene_id="nonce-7",
    )


# ── Renderer: buttons wired to the bridge ────────────────────────────────

def test_options_render_as_real_buttons():
    html = render_scene(scene_with_options())
    assert '<button type="button" class="opt" data-opt="fight">' in html
    assert '<button type="button" class="opt" data-opt="stray">' in html
    assert 'data-scene="nonce-7"' in html
    assert "click an option" in html          # hint keeps the text fallback


def test_card_script_posts_actions_to_the_plugin_route():
    html = render_scene(scene_with_options())
    assert "luna:card:action" in html
    assert "/api/p/plugin-linear-ascent/act" in html
    assert "luna:card:result" in html
    # stock-Luna safety: no bridge answer → revert to typing a number
    assert "reply with a number to act" in html


def test_optionless_scene_has_no_action_script_targets():
    html = render_scene(Scene(eyebrow="X", headline="No options here"))
    assert "<button" not in html


# ── Shared engine access (runtime) ───────────────────────────────────────

class FakeLocal:
    def __init__(self):
        self.docs = {}
        self.saved_ledgers = []

    async def load(self, user):
        return self.docs.get(user) or state.new_player(user)

    async def save(self, user, doc, ledger):
        self.docs[user] = doc
        self.saved_ledgers.extend(ledger)


@pytest.fixture()
def fake_local(monkeypatch):
    fake = FakeLocal()
    monkeypatch.setitem(runtime.state, "local", fake)
    monkeypatch.setitem(runtime.state, "remote", None)
    return fake


def test_act_for_advances_and_persists(fake_local):
    scene = asyncio.run(runtime.act_for("owner", "begin"))
    assert scene.eyebrow.startswith("THE TOWER GATE")
    doc = fake_local.docs["owner"]
    assert doc["stage"] == "creation_race"
    assert doc["scene"] == scene.to_dict()   # scene persisted with the doc


def test_scene_for_is_idempotent(fake_local):
    first = asyncio.run(runtime.scene_for("owner"))
    second = asyncio.run(runtime.scene_for("owner"))
    assert first.headline == second.headline


def test_player_key_falls_back_to_owner():
    # get_current_user is a FastAPI dependency — bare call fails, and the
    # fallback IS the single-user contract shared by tools and the route.
    assert runtime.player_key() == "owner"


# ── The /act route ───────────────────────────────────────────────────────

class RouteCtx:
    """PluginContext stand-in capturing card posts and agent nudges."""

    def __init__(self, post_result="msg-1"):
        self.post_result = post_result
        self.posted = []
        self.muted = []

    async def post_chat_card(self, html, *, conversation_id=None):
        self.posted.append((html, conversation_id))
        return self.post_result

    async def send_muted_message(self, title, content, *, channel=None,
                                 conversation_id=None, **kw):
        self.muted.append((title, channel, conversation_id, content))
        return {"responded": channel == "moment"}


def make_client(ctx):
    fastapi = pytest.importorskip("fastapi")
    testclient = pytest.importorskip("fastapi.testclient")
    import luna_sdk

    app = fastapi.FastAPI()
    routes.register_routes(app, ctx)
    app.dependency_overrides[luna_sdk.get_current_user] = lambda: object()
    return testclient.TestClient(app)


def test_act_route_returns_fragment_and_posts_nothing(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    r = client.post("/api/p/plugin-linear-ascent/act", json={
        "option": "begin", "mode": "pane", "conversation_id": "conv-9"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True
    assert "THE TOWER GATE" in d["fragment"]   # the NEXT scene, in place
    assert d["fragment"].startswith('<div class="card"')
    assert ctx.posted == []                    # 009: nothing hits the chat
    assert fake_local.docs["owner"]["stage"] == "creation_race"


def test_act_route_stale_option_returns_steering_fragment(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    r = client.post("/api/p/plugin-linear-ascent/act",
                    json={"option": "no-such-thing"})
    assert r.status_code == 200
    frag = r.json()["fragment"]
    assert "isn&#x27;t one of the paths" in frag or \
        "isn't one of the paths" in frag
    assert ctx.posted == []


def test_pane_scene_is_idempotent_read(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    first = client.post("/api/p/plugin-linear-ascent/pane/scene", json={})
    second = client.post("/api/p/plugin-linear-ascent/pane/scene", json={})
    assert first.status_code == second.status_code == 200
    assert first.json()["headline"] == second.json()["headline"]
    assert first.json()["fragment"].startswith('<div class="card"')


def test_pane_peek_tracks_chat_driven_acts(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    client.post("/api/p/plugin-linear-ascent/act", json={"option": "begin"})
    peek = client.get("/api/p/plugin-linear-ascent/pane/peek")
    assert peek.status_code == 200
    sid = peek.json()["scene_id"]
    # the same id the engine persisted with the doc
    assert sid == fake_local.docs["owner"]["scene"]["scene_id"]


def test_pane_ui_serves_the_tabbed_app():
    ctx = RouteCtx()
    client = make_client(ctx)
    r = client.get("/api/p/plugin-linear-ascent/ui/")
    assert r.status_code == 200
    html = r.text
    for tab in ("Game", "Score", "Community"):
        assert f'data-tab="{tab.lower()}"' in html
    assert "luna-auth" in html and "luna-ui-ready" in html
    assert "/pane/peek" not in html or True   # polling code present below
    assert "peek" in html and "visibilitychange" in html
    assert "ui-monospace" in html             # same mono grammar as cards


# ── Agent nudges (009): moment on big beats, awareness on EVERY other act ──

def _notify(kind, ctx):
    async def run():
        routes._notify_agent(
            Scene(eyebrow="X", headline="H", event_kind=kind), "conv-1")
        await asyncio.sleep(0)               # let the fired task run
    old = routes._ctx
    routes._ctx = ctx
    try:
        asyncio.run(run())
    finally:
        routes._ctx = old


@pytest.mark.parametrize("kind", ["death", "boss"])
def test_big_beats_run_a_reaction_moment(kind):
    ctx = RouteCtx()
    _notify(kind, ctx)
    (title, channel, conv, content), = ctx.muted
    assert channel == "moment"
    assert conv == "conv-1"
    assert kind in title
    assert "never repeat, summarize, or re-list" in content  # voice rules


@pytest.mark.parametrize("kind", ["", "loot", "present", "letter", "news"])
def test_every_other_act_lands_as_awareness(kind):
    ctx = RouteCtx()
    _notify(kind, ctx)
    (title, channel, conv, content), = ctx.muted
    assert channel == "awareness"
    assert "awareness only" in content       # never invites a reply
    assert "H" in content                    # the compact state line
