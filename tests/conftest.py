"""Unit tests run without a Luna checkout — stub luna_sdk before imports."""

import sys
import types


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
    m.PluginManifest = PluginManifest
    m.ToolDef = ToolDef
    m.PluginContext = PluginContext
    m.declarative_base = declarative_base
    m.JSONB = JSONB
    m.get_current_user = get_current_user
    sys.modules["luna_sdk"] = m


_stub_luna_sdk()
