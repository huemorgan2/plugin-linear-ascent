# We have to continue this

Everything the 022 run deliberately skipped or shipped as a stopgap.
Nothing here is optional — it's deferred. Add to this file every time a
phase cuts a corner; strike items through when they land.

## Tuning (the big one)

- **Deep tuning is floors 1–20 only.** Formulas exist for all 100
  floors, and cheap arithmetic smoke checks run at 31/50/100, but no
  play-tested validation past floor 20. Before real players reach the
  30s, the whole 21–100 band needs the full tuning pass (the last one
  took ~20 hours — budget for it).
- **Floors 31–39 solo-grindable under the 001 stopgap.** The
  regen-vs-sustained-output gate only flips at ~F40. 002's curve should
  fix it; verify it actually did, on real numbers.
- **Banked-bar burst.** One player with a full energy bar out-damages
  the 4× world pool at any floor (a fight lasts until flee/death, so a
  bar ≈ 9 fights ≈ 1.6–1.9× solo warden HP each). 002 must size pools
  against bursts, not sustained rates — and after 002, re-check with a
  burst sim.

## Deferred by agreement

- **Version bump + publish + worldd deploy:** once, at the end of the
  022 run, not per phase.
- **Browser walkthroughs per phase:** replaced by one
  agent-live-walkthrough pass at the end of the run.

## Watch list

- Echo rewards (0.5×) are a guess — nobody has measured whether echoes
  become the dominant XP farm at some level band.
- Local dev "world of one" keeps the personal unlock path alive in
  `combat._victory`. When multiplayer is the only mode that matters,
  delete it and give dev mode a fake world instead.
