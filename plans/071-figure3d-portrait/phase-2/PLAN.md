# Phase 2 — the 1-bit portrait stage

## Goal
`/play` loads `figure3d.js` from its own folder. With Labs on, the
canvas shows the climber's race rig, 1-bit Bayer, calm idle, family
weapons held by the grammar (staff hand / blade hip / bow back).
Labs off is unchanged. Does not import fight3d.

## Steps
- `worldd/static/site/figure3d/` — `figure3d.js`, `vendor/GLTFLoader.js`
  (copy), `models/players/{human,elf,giant}.glb` (copy from fight3d),
  `models/items/{blade,bow,staff}.glb` (copy, family fallbacks).
- `webplay.py`: `FIGURE3D_URL`, inject the module after arena3d.
- JS: own Bayer post (no scenery), native 100×200 / 140×260, pixelated
  CSS already in place. Observer on `canvas.figure3d`. Rebuild when
  the payload JSON changes. Degrade: unhide the fallback `<img>`.
- Hold attach + idle breathe.

## Verification
- `node --check figure3d.js`.
- `/play` HTML contains `src="…/figure3d/figure3d.js`.
- Local harness `figure3d/test.html` shows human / elf / giant
  breathing in 1-bit at the portrait grid.
- Labs off: no canvas.

## Rollback
Revert. Delete the folder. The canvas attribute is inert.

## Execution status
2026-08-24 — Complete in the working tree. The isolated module, vendored
GLTF loader, copied race rigs, family fallbacks, Bayer/depth post pass,
idle/breathe motion, and WebGL-to-PNG degradation path are present.
`node --check` passed. The local harness now covers human, elf, and giant;
its visual browser run remains part of the blocked authenticated dojo work.
