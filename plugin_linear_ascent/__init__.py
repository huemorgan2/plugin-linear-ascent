"""Linear Ascent — a LORD-style multiplayer text RPG for Luna.

The agent is the player's shardmind sidekick. The engine is the only
source of game truth: tools expose the current scene and accept a choice;
out-of-order calls are refused with steering hints.

The engine/content/render modules are Luna-free on purpose: worldd (the
shared-world service) imports them as its game core. The Luna plugin
class only exists when luna_sdk is installed.
"""

from .version import VERSION  # noqa: F401

try:
    from .plugin import LinearAscentPlugin  # noqa: F401

    # Luna's loader resolves manifest.routes_module relative to the plugin
    # CLASS's __module__ (it appends ".routes"). The class lives in plugin.py,
    # so point __module__ at the package or routes would resolve to
    # "<pkg>.plugin.routes".
    LinearAscentPlugin.__module__ = __name__
except ImportError:
    # Running outside Luna (worldd or bare tests): engine-only import path.
    pass
