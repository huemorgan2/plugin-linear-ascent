"""One name, one world — the naming law, in one place.

A climber's name IS their username: one word, unique across the whole
world. The rule lives in the engine because both sides need exactly the
same one — worldd enforces it (the name registry, the site's door) and the
engine asks for it. Two copies of a naming law is one law and one bug.

Spaces are JOINED, never refused: someone who types "Master Chief" means
MasterChief, and stopping them at the gate to explain the alphabet is a
worse welcome than carving it. Case is kept — the name is a legend, and
MasterChief carves better than masterchief — while uniqueness is
case-blind, so nobody gets to be the *other* masterchief.
"""

from __future__ import annotations

NAME_MIN = 2
NAME_MAX = 24


def _carves(c: str) -> bool:
    """The mason's alphabet: letters and numbers in ANY script (Криер carves
    as well as Kettle), plus - and _. Nothing else — no spaces, no
    punctuation, nothing a chat line or a URL would have to escape."""
    return c.isalnum() or c in "-_"


def canonical(raw) -> str:
    """The name as the world will hold it: one word, mason's alphabet."""
    return "".join(c for c in str(raw or "").strip()
                   if _carves(c))[:NAME_MAX]


def is_legal(name: str) -> bool:
    return NAME_MIN <= len(name) <= NAME_MAX and all(map(_carves, name))


def joined_words(raw, name: str) -> bool:
    """True when canonicalizing did more than trim — the card should say so
    rather than quietly hand the player a different name than they typed."""
    return str(raw or "").strip() != name
