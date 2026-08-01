# 031 — the second punch list

The user checked 0.36.0 against their eye and filed fourteen more items.
Every one ships in 0.37.0. Scope: UI/render + engine tuning; tuning
verified to floor 10 as agreed; code changes apply everywhere.

## The items

1. **No left accent lines.** Every colored `border-left` vertical bar on
   boxes goes. Boxes keep their fill and (where needed) a full hairline
   border — never a colored left spine.

2. **Portraits without glow.** Regenerate all six armour-tier portraits:
   shaded charcoal figure against pure flat black — no radial glow, no
   halo, no backlight. (Prompt edited in `tools/generate_030_art.py`.)

3. **The pack is a slot grid.** Minecraft-style: a row of fixed square
   slots (empty slots visible as dark sockets), items fill them with
   their 16×16 icons + count. Above the grid, two promoted boxes:
   **WEAPON** (in hand) and **SHIELD/ARMOUR** (worn). Buying a better
   weapon auto-promotes it; owning several weapons gives a choice
   (equip option in the forge/pack context).

4. **A proper header.** Top of the profile block, one line:
   left — player name bold + "an elf archer" (race + class, dim);
   right — **LEVEL 5** and **COINS ◈xxx**, bold. Coins/level leave the
   meter pile; the meters keep HP/XP/energy.

5. **Warden energy: pay per swing only.** Travelling to the keep: free.
   Joining the fight: free. Every attack of any kind on the warden:
   3 ⚡. (Currently travel and entry charge 3 and swings ride free —
   exactly backwards.)

6. **Warden [i] declares its drops.** The warden dossier gets the same
   coin/XP drop bullets every monster has: strike pay, the kill purse,
   first-blade bonus — whatever the economy actually pays.

7. **Ranged honesty.** Attacking from range must not draw full
   retaliation — no counter (or a low-chance graze at most) while the
   gap is open. Opening the gap is the move that eats a hit. And you
   cannot open distance from an enemy as fast as you or faster.

8. **Death costs something.** Dying is taxed: from level 1, at least
   half the coin on hand; past the agreed pardon level, no mercy —
   ~90% of carried coin and a random carried item can be lost. Vaulted
   coin stays safe (that is what the vault is for).

9. **A face in the lodge.** A named NPC — portrait 100×200 left of the
   text — who explains the lodge, bores you with his life story, and
   colors the lore. Option reads "Talk with <name>". The keeper's
   glory stories fold into this character.

10. **JOB OFFER, in plain words.** The night-job line becomes
    "JOB OFFER: the palisade watch — stand guard tonight, paid ◈ at
    dawn (no HP recovery tonight)". No poetry that hides the deal.

11. **The lodge states your evening.** Under the lodge options, a
    colored box (fill, no outline): "ACTIVITY IN THE LODGE: no
    activity selected" → updates to the chosen one. Options carry
    their trade-offs: "JOB OFFER: … (no HP recovery tonight)",
    "ACTIVITY: rest by the fire — rested XP bonus".

12. **Town news wears newsprint.** The war lines in the Roothollow
    body move into the same light newsprint box with the ✕
    close-for-the-day — one news surface, one look.

13. **Hunt/warden art moves inside the floor.** The scene art belongs
    on the choice between hunting the fields and walking to the keep —
    not on the floor-list rows. Floor rows calm down; the in-floor
    choice gets the pictures.

14. **Card-grid selection UI.** A new option-render mode: a grid of
    cards — large image on top, name + cost + line under it, [i] badge
    kept on the card. The forge uses it for its stock; the forge's
    top wall of text goes entirely.

## Order of work

Engine first (5, 7, 8, 6), then render structure (1, 4, 3, 12, 13),
then lodge content (9, 10, 11), then the card grid + forge (14), then
art landing (2 + NPC portrait), tests all the way, QA shots, ship.

## Verification

- Full pytest suite + ASCENT_FULL_SIMS sims.
- QA harness `tools/qa_030_shots.py` — new scenes added for lodge
  evening state, forge grid, in-floor choice, warden dossier.
- Screenshot review of every touched surface before publish.
