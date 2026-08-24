"""Unit tests run without a Luna checkout — stub luna_sdk before imports."""

import os
import sys
import types

# 007: the world is mandatory for players; tests play the local engine.
os.environ.setdefault("ASCENT_DEV_LOCAL", "1")


def _stub_luna_sdk() -> None:
    if "luna_sdk" in sys.modules:
        return
    m = types.ModuleType("luna_sdk")

    class LunaPlugin:
        pass

    class PluginManifest:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class ToolDef:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class PluginContext:
        pass

    class SettingsTab:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class SidebarSection:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    def declarative_base():
        try:
            from sqlalchemy.orm import declarative_base as real
            return real()
        except ImportError:
            class FakeBase:
                metadata = types.SimpleNamespace(sorted_tables=[])
            return FakeBase

    try:
        from sqlalchemy.dialects.postgresql import JSONB
    except ImportError:
        JSONB = object

    async def get_current_user(request):
        # Stand-in for luna.auth's FastAPI dependency. `request` is
        # required, exactly like the real one: a bare call must raise so
        # runtime.player_key() falls back to "owner". Route tests override
        # this per-app.
        return None

    m.LunaPlugin = LunaPlugin
    m.SettingsTab = SettingsTab
    m.SidebarSection = SidebarSection
    m.PluginManifest = PluginManifest
    m.ToolDef = ToolDef
    m.PluginContext = PluginContext
    m.declarative_base = declarative_base
    m.JSONB = JSONB
    m.get_current_user = get_current_user
    sys.modules["luna_sdk"] = m


_stub_luna_sdk()


import pytest  # noqa: E402  (after the stub — pytest imports nothing of ours)


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "reel: test drives the 030 floor reel itself — "
                   "the auto-stepper stays out of its way")


@pytest.fixture(autouse=True)
def _step_the_reel(request, monkeypatch):
    """030 Phase 8: first entry to a floor plays a two-beat reel.

    Every contract written before 030 picks a floor and acts in the same
    breath. The reel is presentation, not rules — so the harness clicks
    through it the way a player would, and the old contracts keep reading
    exactly as written. Tests OF the reel mark themselves with @reel.
    """
    if request.node.get_closest_marker("reel"):
        yield
        return
    from plugin_linear_ascent.engine import core
    real = core.apply_choice

    def step(p, option_id, text=""):
        s = real(p, option_id, text)
        while p.get("movie_floor"):
            s = real(p, "1")
        return s

    monkeypatch.setattr(core, "apply_choice", step)
    yield


@pytest.fixture(autouse=True)
def _inline_art_by_default():
    """078: register_routes points render at static /art URLs — a process-
    global switch. Tests assume the inline-art default unless they opt in
    (test_078_static_art), so restore whatever was set after each test."""
    from plugin_linear_ascent import render
    before = render.ART_BASE
    yield
    if render.ART_BASE != before:
        render.set_art_base(before)


# ── 048: the canonical creation helper ─────────────────────────────────
# ~30 test files carry a local copy of this walk; new tests use this one
# and the local copies fold into it during the phase-4 sweep.

def make_character(p, race="human", clazz="warrior", name="Testa"):
    """Walk the intro movie and the creation flow to a live climber."""
    from plugin_linear_ascent.engine import core
    core.current_scene(p)
    while p["stage"] == "intro":
        core.apply_choice(p, "1", "")
    core.apply_choice(p, race, "")
    core.apply_choice(p, clazz, "")
    core.apply_choice(p, "", name)
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
