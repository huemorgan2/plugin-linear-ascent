"""Single source for the version string.

Three stamps must stay in sync: this constant, PluginManifest.version in
__init__.py (imports this), and luna-plugin.toml. Bump all together.
"""

VERSION = "0.1.0"
