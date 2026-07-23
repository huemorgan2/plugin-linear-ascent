"""StateBackend — the phase-3 seam.

Local mode: the engine runs in-process against these two methods.
Remote mode (worldd) swaps in an HTTP client with the same surface; the
same contract tests run against both.
"""

from __future__ import annotations

from typing import Protocol


class StateBackend(Protocol):
    async def load(self, luna_user: str) -> dict:
        """Return the player document, creating a fresh one if absent."""
        ...

    async def save(self, luna_user: str, doc: dict,
                   ledger: list[dict]) -> None:
        """Persist the document and append ledger rows atomically."""
        ...
