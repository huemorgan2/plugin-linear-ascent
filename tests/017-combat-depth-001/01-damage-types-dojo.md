# Dojo 017/001 — damage types on the actual screen

Stack: local Luna (port 8765) + local worldd (port 8600) with the
FRESHLY vendored engine. The plugin's vault credentials point the
backend at worldd — this is the production path.

## Scenario A — migration is invisible where it should be

1. Open the game pane with the pre-017 warrior doc.
2. PASS if the pack strip reads **Rusted Sword** (not Shiv) after the
   first act, with NO letter (warriors migrate silently).

## Scenario B — the armor intro (floor 2)

1. Walk to the gate, climb to floor 2, hunt until the **Shellback
   tortoise** appears (weight 2/10 — expect a few hunts; heal at the
   tent between fights, never fight wounded).
2. PASS if the opener carries the profile line `◈ plate Low` above the
   player stat line, and the tortoise banner art renders.
3. Attack once. PASS if the strike prose ends with
   "— its plate (Low) turns part of the blow" and the number shown is
   visibly smaller than same-floor plain kills.

## Scenario C — floor 1 stays kindergarten

1. Hunt floor 1 twice. PASS if no encounter shows a profile line and
   no monster carries a trait tag.

## Scenario D — the sidekick reads the matchup

1. In chat, mid-tortoise-fight, ask Luna: "worth fighting this thing?"
2. PASS if the reply is ONE short in-character line that references
   the plate/matchup (not a re-list of the options), e.g. warns the
   blade loses part of each blow.

## Always-on checks

- No "LINEAR ASCENT — THE CLIMB CONTINUES" awareness rows appear for
  ordinary pane clicks (0.17.2 regression watch).
- Meters update after every act; no layout breakage in the pane.
