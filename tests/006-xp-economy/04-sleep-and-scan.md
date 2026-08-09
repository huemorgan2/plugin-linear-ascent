# Scenario 04 — Sleep Spell burns experience

(045: the shard scan and Scout optics were removed — the free `[i]`
dossier carries the enemy numbers. This scenario now covers Sleep only.)

## Setup
A sorcerer with a small XP pool.

## Steps
1. Hunt floor 1 until a fight card is up. Read the class option hint.
   - **Expect:** `Sleep spell` hint shows the XP price (`✦ 12` on floor 1 —
     one kill's worth), not "2 ✦" mana.
2. With pool ≥ cost, cast Sleep.
   - **Expect:** fight ends, **no XP awarded** ("you step past it" — no
     `+ N experience` line), pool reduced by the cost, level unchanged.
3. Hunt again with pool < cost and cast Sleep.
   - **Expect:** refusal note quoting the ✦ shortfall; fight continues;
     pool unchanged.
4. Read the fight card's rows and the Medlab shelf.
   - **Expect:** no "Ask the shard to scan it" row anywhere; no Scout
     optics on the shelf; the `[i]` dossier still shows ATK/DEF/HP free.

## Pass
Sleep = skip-for-its-price with zero award; refusals never end the
fight or charge anything; no scan row or optics item exists.
