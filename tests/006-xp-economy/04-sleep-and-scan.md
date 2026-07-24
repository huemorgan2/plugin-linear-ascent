# Scenario 04 — Sleep Spell and shard scan burn experience

## Setup
A sorcerer with a small XP pool; scout optics NOT purchased.

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
4. In a fight with 0 optics charges, find the scan option.
   - **Expect:** scan offered with a `✦` price (half a kill). Using it
     spends pool XP and prints the enemy stat line. With pool short, it
     refuses and the fight continues.
5. Buy Scout optics at the Medlab, fight again.
   - **Expect:** scan hint shows charges; using it consumes a charge and
     spends NO XP.

## Pass
Sleep = skip-for-its-price with zero award; scan prefers charges, falls
back to XP; refusals never end the fight or charge anything.
