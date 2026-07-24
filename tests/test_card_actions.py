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


def test_act_route_runs_engine_and_posts_next_card(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    r = client.post("/api/p/plugin-linear-ascent/act", json={
        "option": "begin", "conversation_id": "conv-9",
        "message_id": "old-card"})
    assert r.status_code == 200
    d = r.json()
    assert d["ok"] is True and d["message_id"] == "msg-1"
    html, conv = ctx.posted[0]
    assert conv == "conv-9"
    assert "THE TOWER GATE" in html          # the NEXT scene, as a card
    assert fake_local.docs["owner"]["stage"] == "creation_race"
    assert ctx.muted == []                   # ordinary beat → agent silent


def test_act_route_stale_option_posts_steering_card(fake_local):
    ctx = RouteCtx()
    client = make_client(ctx)
    r = client.post("/api/p/plugin-linear-ascent/act",
                    json={"option": "no-such-thing"})
    assert r.status_code == 200
    html, _ = ctx.posted[0]
    assert "isn&#x27;t one of the paths" in html or \
        "isn't one of the paths" in html


def test_act_route_503_when_host_cannot_post_cards(fake_local):
    ctx = RouteCtx(post_result=None)
    client = make_client(ctx)
    r = client.post("/api/p/plugin-linear-ascent/act", json={"option": "begin"})
    assert r.status_code == 503


# ── Agent nudges: moment on big beats, awareness on loot-tier, else off ──

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


@pytest.mark.parametrize("kind,channel", [
    ("death", "moment"), ("boss", "moment"),
    ("present", "awareness"), ("letter", "awareness"), ("loot", "awareness"),
])
def test_big_beats_nudge_the_agent(kind, channel):
    ctx = RouteCtx()
    _notify(kind, ctx)
    (title, got_channel, conv, content), = ctx.muted
    assert got_channel == channel
    assert conv == "conv-1"
    assert kind in title
    assert "never repeat, summarize, or re-list" in content  # voice rules


def test_ordinary_scenes_do_not_nudge_the_agent():
    ctx = RouteCtx()
    _notify("", ctx)
    assert ctx.muted == []
