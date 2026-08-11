# Plan 049 — full creature roster

Every encounter and warden on every shipped floor, built from
`plugin_linear_ascent/content/floors/floor_*.yaml`.
**100 floors, 525 images to remake (encounters + wardens).**


Size comes from the body archetype trait (economy.py BODY_TAG):
frail = small · lean = medium · no body trait = at-floor peer ·
sturdy = large · hulking = enormous.

Origin (world-lore.md §5): **Native** = the land's own animal, grown
wrong under the fever — the `was:` line names the original smaller
animal. **Pressed** = a conscripted person (goblin, kobold, orc, imp)
— not an infected animal. **Wrongmade** = manufactured by the tower —
made, not infected. Floors 11–100 predate the 038 tagging; their kind
is marked *untagged* (per world-lore §9, untagged headline animals
default to Native, but no original-animal line was ever written).

## Floor 1 — The Fencerows (biome: Men, tier 1, gate town: Lamplit Steading)

**Landscape:** Stolen meadowland rolls out under the tower's floodlights. Hedgerows still stand in their old lines, fencing fields no farmer will cut again. Somewhere out in the grass, something is moving.

### Grey wolf (`grey_wolf`)
- **Size:** at-floor peer (medium)
- **Description:** A grey wolf slides out of the hedgerow, ribs showing under a dull coat. It has learned that climbers carry meat.
- **Lore:** Farm dogs once kept them past the fences. The dogs are gone; the wolves remember the gap in the third hedge.
- **Origin:** Native — an infected animal of the stolen land. Originally the shy grey wolf the farm dogs kept past the fences.

### Feral boar (`feral_boar`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A boar the size of a cart tears up the turf between you and the path, tusks yellowed and one ear ragged from old fights.
- **Lore:** Sty stock gone wild in two generations. It charges first and decides why later.
- **Origin:** Native — an infected animal of the stolen land. Originally an ordinary sty boar, escaped, under the fever.

### Hedgerow rat (`hedge_rat`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Something the size of a dog bursts from the fencerow in a spray of leaves — a rat grown fat on abandoned granaries, teeth first.
- **Lore:** Granary doors stood open the night the farms fell. What ate its fill in the dark kept growing.
- **Origin:** Native — an infected animal of the stolen land. Originally a granary rat that ate its fill in the dark and kept growing.

### The last pack (`lane_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** Shapes fold out of the hedges on every side — the steading's own sheepdogs, feral and silent, working you the way they once worked sheep.
- **Lore:** The steading's sheepdogs, feral now, hunting in a silent ring. One of them still turns its head at a whistle.
- **Origin:** Native — an infected animal of the stolen land. Originally one of the steading's own sheepdogs — the very dogs that once kept the wolves out.

### Goblin straggler (`goblin_straggler`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A lone goblin in a stitched rag-coat drags a notched longsword through the grass, too heavy for it by half. It sees you, sets its feet behind the sword anyway, and grins.
- **Lore:** Marched down from the warrens to hold the low gate, then left behind sick when the war-band climbed on. Nobody pays its wage.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### Hedge-wight (`ember_shade`)
- **Size:** enormous — it fills the path — traits: hulking
- **Description:** At the floodlights' flicker a man-shape stands up out of the hedge — blackthorn snarled into shoulders and arms, walking the fence line it grew from.
- **Lore:** Spilled aether soaked into a rotten stile. Nothing living was ever in it.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Brackjaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The stair-lift hums behind a beast of wolf and welded plate. Brackjaw circles once, servos ticking, and lowers its head to charge.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 2 — The Rustwater Adit (biome: Giants, tier 1, gate town: Lampfall)

**Landscape:** A slab of mountainside ends at a mine-mouth still weeping orange iron-water. Ore-carts sit loaded on rails that run off the cut edge into open air. Somewhere down the dark drift, water is moving.

### Rust hound (`marsh_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean
- **Description:** A hound coated in rust-scale comes down the rails at a working trot, jaws locked half-open. It has run this line all its life. Now it runs it at you.
- **Lore:** Iron-scale coats it and its jaws lock half-open. The packs still run the rails, hauling nothing.
- **Origin:** Native — an infected animal of the stolen land. Originally a pit-dog that hauled carts and slept warm by the forge.

### Cave cricket (`cave_cricket`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The roof rustles and a fist-sized cricket lands on your pack, then another — springing shapes that strip leather, wick, anything that once was soft.
- **Lore:** Fist-sized now, it springs man-high and strips leather and lamp-wick down to nothing.
- **Origin:** Native — an infected animal of the stolen land. Originally a harmless roof-cricket of the entrance hall.

### Shellback tortoise (`shellback_tortoise`)
- **Size:** enormous — it fills the path — traits: hulking, armoured
- **Description:** Something the width of a cart door drags itself out of the orange water — a tortoise in a shell of rust-crusted plate, older than the flood and slower than patience.
- **Lore:** Grown door-broad in the flooded drift, shell crusted to rust-plate. It holds the narrow ways like a gate.
- **Origin:** Native — an infected animal of the stolen land. Originally a sump-pool tortoise the pit crews kept for luck.

### Kobold digger (`kobold_digger`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A kobold in a collar swings its mattock at your lamp, half-blind from years in the dark. It was never asked whether it wanted to dig.
- **Lore:** First-taken from the warrens far below and set to cut the giants' seams. The collar does the deciding.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### Red Orc outrider (`orc_overseer`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A scarred Red Orc steps from the drift with a drover's whip and an underfed look. It hates this posting, this mine, and whatever interrupts the count. Today that is you.
- **Lore:** A pressed veteran of Skarn's warcamp, sent down to keep the diggers digging. No one pays the wage it kills for.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### The Seep (`rust_seep`)
- **Size:** thick through the shoulders (large) — traits: sturdy
- **Description:** An orange stain crawls up the drift wall against the run of the water, spreading fingers. Where it has passed, the rock is eaten smooth.
- **Lore:** Spilled aether pooled in the rust-water. It was never alive; it only moves.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Rustmaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The flooded main drift goes quiet. Then the water heaves and Rustmaw stands up in it — a pit hound welded into a war-engine, an ore-crusher's jaw grafted over its head, dragging the rails behind.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 3 — The Drowned Pasture (biome: Men, tier 1, gate town: Weirsend)

**Landscape:** A pasture taken mid-flood and never drained — grey water to the horizon, hedge-tops and half-drowned fences breaking the surface. Hay-ricks stand as islands. Somewhere a sluice still turns, keeping the wrong things wet.

### Marsh wolf (`sluice_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean
- **Description:** A wolf breasts the grey water between two hay-ricks, web-footed and low, only its eyes and shoulders showing. It has learned that punts tip.
- **Lore:** Web-footed now, wading the channels between the ricks. It swims better than you pole.
- **Origin:** Native — an infected animal of the stolen land. Originally a fen-edge wolf that hunted the drier islands.

### Marsh adder (`reed_adder`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The sedge parts without wind. A marsh adder rides the shallow water in slow curves, tongue reading your warmth, no longer shy of anything.
- **Lore:** Fever-bold now, striking from the reed at anything warm.
- **Origin:** Native — an infected animal of the stolen land. Originally a shy grass-snake of the banks.

### Mire boar (`mire_boar`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** The reed-bank explodes and a boar comes through it mud-armored to the eyes, throwing a bow-wave. It heard your pole touch bottom.
- **Lore:** Mud-armored to the eyes, it beds in the reed and bursts out at a punt's shadow.
- **Origin:** Native — an infected animal of the stolen land. Originally a pasture boar that fed along the drowned hay.

### Fence-wire pike (`wire_eel`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, armoured
- **Description:** What looks like drowned fence-wire moves — a white fish grown through the barbs until steel and muscle are one length, sawing the water toward your legs.
- **Lore:** Grown long through the drowned fence-wire until steel and muscle are one barbed length.
- **Origin:** Native — an infected animal of the stolen land. Originally a blind white fish the flood carried up from some deep cellar.

### Drowned lantern (`windfall_haunt`)
- **Size:** thick through the shoulders (large) — traits: sturdy, magic_resist
- **Description:** A cold light drifts over the water, patient as a ferryman, and swings your way. There is no hand carrying it. There never was.
- **Lore:** A trapper's lamp lost in the flood, aether soaked into the dead flame. It calls punts onto the black reed.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Sedgeback (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The mill-pool heaves and Sedgeback wades out of it — a mire boar under a weir-iron carapace of green bronze, shedding water like a roof. It charges the shallows in a bow-wave that hides its feet.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 4 — The Lightless Glade (biome: Elves, tier 1, gate town: Lanternroot)

**Landscape:** An elf-wood whose trees once lit themselves, snuffed in a single night. The sap runs dark, the glimmer-moss is ash-grey, and past the first branches the floodlights fail. Whatever moves in there moves by sound.

### Pale stag (`glade_stag`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Antlers the color of bone swing out of the black — a stag gone blind-white, head cocked to your footfall. It charges the sound, and the sound is you.
- **Lore:** Colorless and blind-white, it walks the dark by sound and gores at light.
- **Origin:** Native — an infected animal of the stolen land. Originally a wood-stag that grazed the lit glades.

### Dusk-hare (`dusk_hare`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Something small and quick circles you in the black, closer with each pass. A hare — fearless, fever-fast, aimed at your eyes.
- **Lore:** Fever-fast and fearless, it bolts from the dark straight at the eyes.
- **Origin:** Native — an infected animal of the stolen land. Originally a shy twilight hare of the wood's edge.

### Lamp newt (`glare_moth`)
- **Size:** small and slight — traits: frail, fly
- **Description:** Your lamp gutters as something wet climbs the glass — a newt broad as two hands, starving for the light, smothering the flame with its own body.
- **Lore:** It slept in lamplight once. Hand-span and starving now, it smothers any flame.
- **Origin:** Native — an infected animal of the stolen land. Originally a glade-newt that dozed in the moss under the wick-flowers.

### Wick-owl (`wick_owl`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** The dark above you goes soft with wingbeat — an owl broad as a door, silent past sense, riding your lamp-heat down.
- **Lore:** Silent and over-large now, hunting warmth instead of watching flames.
- **Origin:** Native — an infected animal of the stolen land. Originally a lamplighter's companion owl that watched for guttering lamps.

### The lamp-eater (`lamp_eater`)
- **Size:** thick through the shoulders (large) — traits: sturdy, magic_resist
- **Description:** The dark ahead is darker than it should be, and crawling. A shape of black lichen drags itself toward your flame — not to warm itself. To drink it.
- **Lore:** The black lichen that drinks light, gathered into a slow crawling shape. Nothing living is in it.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Glade-wight (`lamptree_wight`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, armoured
- **Description:** A snarl of black branch unbends from the treeline, tall as two men, lit from inside by a cold false glow. The light shows nothing. That is its purpose.
- **Lore:** A dead lamp-tree, aether pooled in its rot. It walks with a cold false glow.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Palegleam (warden)
- **Size:** boss — fills the stair-gate
- **Description:** A pale stag crowned in a welded lamp-cage steps into its own cold blue glare — light that shows nothing and blinds everything near it. Palegleam stalks the edge of the light it carries, and charges out of it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 5 — The Flooded Mine (biome: Giants, tier 1, gate town: Pumpstead)

**Landscape:** Gallery after gallery runs down into dead-black water. The great pumps that held it back are drowned with the deep they kept dry, and drowned gear hangs on drowned pegs. The flat water goes down further than any lamp will show.

### Blind cave-fish (`blind_shoal`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The water around your boots begins to boil — a shoal of pallid, eyeless fish, massed and biting at the first warmth this gallery has known in years.
- **Lore:** Massed and biting, they boil the surface wherever warmth touches it.
- **Origin:** Native — an infected animal of the stolen land. Originally a shoal of pallid fish from the drowned galleries.

### Sump lamprey (`drift_eel`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** The dead-flat water breaks without warning — a blind fish long as a hoist-rope, striking up at your lamp's reflection with your face behind it.
- **Lore:** Fever-long now, it strikes up from the flat black at a lamp's reflection.
- **Origin:** Native — an infected animal of the stolen land. Originally a blind cave-fish of the deep water.

### Drift courser (`downs_courser`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fly
- **Description:** Claws hammer the dry gallery behind you, gaining — a mine-hound running its old message-route at fever pace, and you are standing on the route.
- **Lore:** It still runs the dry drifts end to end, fever-fast, coursing anything that carries a light.
- **Origin:** Native — an infected animal of the stolen land. Originally a winder's hound that ran messages between the galleries.

### Sump-crawler (`coolant_crab`)
- **Size:** thick through the shoulders (large) — traits: sturdy, armoured
- **Description:** The floor of the flooded drift moves under your boot — a pale salamander the size of a cart-wheel, hauling up out of the black with its mouth open.
- **Lore:** Soft-skinned once. Shield-backed and many-legged now, it scuttles the drowned floors underfoot.
- **Origin:** Native — an infected animal of the stolen land. Originally a pale cave salamander of the flooded drifts.

### Bilge kobold (`bailer_kobold`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A kobold stands waist-deep in the black water with a bailing-hook, wet to the bone, collared. It swings at your lamp because the lamp found it.
- **Lore:** First-taken from the warrens and set to bail the deep by hand. The collar keeps it at it.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### Drowned-miner husk (`miner_husk`)
- **Size:** enormous — it fills the path — traits: hulking, magic_resist
- **Description:** A lamp comes wading up the flooded gallery at shift-pace, hung on a shape like a working man. The shape is water and old gear. The lamp is real.
- **Lore:** A drift-crew's lost lamp and gear, aether pooled in the flood over them. It wades in the shape of a working man.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Sumplock (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The flood stands dead-flat, then jets — Sumplock, a giant sump-eel welded through with a pump-valve maw, takes the gallery's water in and fires it back hard enough to sweep your feet, striking from the wave.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 6 — The Threshold Dark (biome: Deep, tier 1, gate town: Lastlight)

**Landscape:** The floodlights fail at the last terrace and the true dark begins — a cavern country floored a thousand years deep in guano, silk in the high corners, cold that has never known a season. Bring your own light or bring nothing.

### Grave-rat (`grave_moth`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** Something soft drops onto your shoulder in the dark, then clings — a palm-broad rat drawn to your breathing, kicking blinding grave-dust into your eyes.
- **Lore:** Drawn to warm breath even then. Palm-broad now, it powders the eyes with grave-dust.
- **Origin:** Native — an infected animal of the stolen land. Originally a pallid rat-pup of the guano beds.

### Guano vole (`guano_vole`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The soft floor humps and splits at your boot — a blind vole, bloated and bold, already gnawing at your laces as if you were rope.
- **Lore:** Bloated and bold, it gnaws boots, rope, and whatever the rope holds.
- **Origin:** Native — an infected animal of the stolen land. Originally a blind vole of the roost-floor.

### Cave broodling (`silk_broodling`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A thread brushes your face in the dark. Then the thread pulls — a dog-sized broodling riding its own line down, forelegs first.
- **Lore:** Dog-sized and hunting in threads — the first of many broods above.
- **Origin:** Native — an infected animal of the stolen land. Originally a spiderling of the corner-silk.

### Sentinel spider (`vault_weaver`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, armoured
- **Description:** Your lamp's glow finds eight points of light in the roof, arranged in a pattern, descending. The vault's old ambush-weaver has your lamp — and you — marked.
- **Lore:** Fever-quick now, it drops on a shielded lamp from the unseen roof.
- **Origin:** Native — an infected animal of the stolen land. Originally the vault's big ambush-weaver.

### Vault boar (`lane_boar`)
- **Size:** at-floor peer (medium) — traits: bulwark
- **Description:** The crawl ahead is stopped by a wall of crusted bristle — a blind boar grown into the passage it guards, front-on, going nowhere. Neither are you, until it does.
- **Lore:** Blind and guano-crusted, it plugs the narrow ways and gives you only its front. The one road on is through.
- **Origin:** Native — an infected animal of the stolen land. Originally a drover's boar that followed the delver road down and never came back up.

### Silk-wrapped husk (`wrapped_husk`)
- **Size:** thick through the shoulders (large) — traits: sturdy, magic_resist
- **Description:** From the dark comes a man's voice calling for help, word-perfect. The shape that walks out wearing it is a cocoon of silk, and it is empty.
- **Lore:** A delver lost to the silk, aether pooled in the bundle. It mimics a caught man's voice.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Duskspin (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The stair-lift arch is webbed shut with steel silk, and the roof above it is alive. Duskspin drops without a sound — a sentinel spider welded huge, spinnerets laying cable for thread, cutting lamps first.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 7 — The Orchard Rows (biome: Men, tier 1, gate town: Cider Cross)

**Landscape:** Mile on mile of planted rows gone to rot, the ground ankle-deep in windfall fermenting under the floodlights. The air is thick, sweet, and drunk; wasps hang in it like sparks. Nine generations pruned these trees. Nobody will pick them.

### Orchard wolf (`orchard_wolfpack`)
- **Size:** lean and quick-ribbed (medium) — traits: lean
- **Description:** Grey shapes flow between the trunks on both sides, keeping your pace — an orchard pack, drunk-bold on the haze, herding you toward the deeper rows.
- **Lore:** It hunts the rows in silent packs, drunk-bold on the haze.
- **Origin:** Native — an infected animal of the stolen land. Originally a wolf that denned in the windbreak rows.

### Cider-mad boar (`rabid_boar`)
- **Size:** enormous — it fills the path — traits: hulking, savage, armoured
- **Description:** A boar the size of a hay-wain reels out of the windfall, soaked in rot-cider, furious at nothing and now at you. It does not feel the branches it breaks.
- **Lore:** Reeling, furious, and fearless on fermented mush.
- **Origin:** Native — an infected animal of the stolen land. Originally a windfall-fed boar of the rows.

### Mouse-tide (`hornet_swarm`)
- **Size:** small and slight — traits: frail, fierce, fly
- **Description:** The rustle you took for the presses sharpens and turns toward you — a boiling carpet of mice the size of a cart, moving as one mind, reading your sweat on the sweet air.
- **Lore:** The wrongness would not let one small thing stay one. It follows warmth and sweat as a hundred now.
- **Origin:** Native — an infected animal of the stolen land. Originally a single field mouse from under the press-house floor.

### Windfall dormouse (`windfall_crow`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** Something heavy drops out of the high forks and comes reeling across the windfall — a dormouse bloated on rot, going for the eyes.
- **Lore:** Bloated on rot, reeling in drunk spirals, going for the eyes.
- **Origin:** Native — an infected animal of the stolen land. Originally a fat dormouse that slept in the high forks.

### Orchard hare (`orchard_hare`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Something small tears down the row at shin height, fever-swift, and does not swerve. It has stopped swerving for anything.
- **Lore:** Fever-swift, bolting between the rows into shins and ankles.
- **Origin:** Native — an infected animal of the stolen land. Originally a bark-nibbling hare of the rows.

### Windfall haunt (`windfall_wight`)
- **Size:** thick through the shoulders (large) — traits: sturdy, magic_resist
- **Description:** A reeling, dripping figure waits between the rows, black cider running from it like sweat. One hand offers a cup. Watch the other hand.
- **Lore:** A presser drowned in a vat, aether soaked into the black cider. It offers a cup.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Applewrath (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The deep windfall heaves and Applewrath comes up out of it charging — a cider-mad boar under press-iron and barrel-hoops, black cider dripping from the seams, the haze thick around it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 8 — The Ashline (biome: Waste, tier 1, gate town: Greywell)

**Landscape:** Grey ash dunes to the horizon — the burned frontier no crown ever wanted. The wind moves the ash in slow sheets, jackals work the dune-shadows, and the first hot floor of the climb bakes under floodlights that only add glare. Water here is a secret.

### Ashline jackal (`cinder_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Lean shapes rise out of the dune-shadows one by one, ash sliding from their backs — jackals coursing your warmth, pack-bold and patient no longer.
- **Lore:** Pack-bold and fever-lean, coursing warmth across the flats.
- **Origin:** Native — an infected animal of the stolen land. Originally a dune scavenger that followed the caravans.

### Glass-hare (`dune_hare`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A pale blur crosses the flat in a spray of glass-dust, doubles, and comes through your legs — a hare running strike-glass at a speed no fever should allow.
- **Lore:** Razor-swift over the fulgurite, kicking up glass-dust.
- **Origin:** Native — an infected animal of the stolen land. Originally a pale desert hare of the strike-fields.

### Ash salamander (`cinder_salamander`)
- **Size:** thick through the shoulders (large) — traits: sturdy, magic_resist
- **Description:** The warm ash you were about to cross opens an orange eye. A salamander unbeds itself, ember-veined, tail dragging a line of smoke.
- **Lore:** Ember-veined, it beds in warm ash and lashes with a scalding tail.
- **Origin:** Native — an infected animal of the stolen land. Originally a heat-loving rock salamander.

### Cinder vulture (`cinder_vulture`)
- **Size:** small and slight — traits: frail, fly
- **Description:** A shadow crosses you twice. The vulture riding it is ash-caked and huge, and it has decided you are slowing.
- **Lore:** Huge and ash-caked, it stoops on anything that slows.
- **Origin:** Native — an infected animal of the stolen land. Originally a carrion bird of the frontier.

### Dune adder (`ash_adder`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** The dune's surface pours toward your boot — an adder swimming the ash just under the crust, striking at the footfall before the foot has landed.
- **Lore:** Fever-fast, it strikes from under the ash at a footfall.
- **Origin:** Native — an infected animal of the stolen land. Originally a sand-swimming viper of the dunes.

### Dune ogre (`greywell_ogre`)
- **Size:** enormous — it fills the path — traits: hulking, savage, armoured
- **Description:** An ogre stands up from the spring-mouth with an ash-glass boulder on its shoulder, sun-mad, collared. It was born to these dunes. The collar holds it to the cruelest posting on them.
- **Lore:** Waste-born and collared, set to hold the one deep spring against the nomads it once shared water with.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### Warden Cinderhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The ash-bowl before the lift stirs and Cinderhide stands out of it — a dune ogre welded into slag-plate and ash-glass, collar fused to its skull, a molten boulder already in hand. The tower made this one un-savable.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 9 — The Beacon Field (biome: Men, tier 1, gate town: Pylon Rest)

**Landscape:** A night signal-heath — miles of humming aether-pylons flickering against the dark, their knife-edged shadows sliding across the heather until the whole moor strobes. Every light out there says come here. None of them means safety.

### Glare vole (`beacon_moth`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** Something runs the heather at your feet — a vole broad as a plate, blinding-pale, climbing for your lamp at the exact moment the field goes black.
- **Lore:** It came to the beacons for warmth. Plate-broad and blinding-pale now, it smothers lamps.
- **Origin:** Native — an infected animal of the stolen land. Originally a heath-vole that nested warm at the pylon-feet.

### Bog-cotton hare (`moor_hare`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A hare bolts through the strobing light in blind zigzags, straight across you — maddened past any sense of what it is running from.
- **Lore:** Strobe-maddened, bolting in blind zigzags.
- **Origin:** Native — an infected animal of the stolen land. Originally a moor hare of the heather.

### Night-shrew (`night_hawk`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Between one flash and the next, something crosses the gap — a shrew grown wrong and huge, lunging silent out of the strobe with its mouth open.
- **Lore:** Over-large now, lunging silent out of the strobe.
- **Origin:** Native — an infected animal of the stolen land. Originally a dusk-hunting shrew of the heather.

### Shadow-line wolf (`shadow_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, armoured
- **Description:** A pylon-shadow slides across the heather and something keeps pace inside it, using the dark like cover. You see the wolf only when the light moves.
- **Lore:** It hunts inside the moving shadows, unseen until it crosses a light.
- **Origin:** Native — an infected animal of the stolen land. Originally a heath wolf that hunted the pylon-shadows.

### Pylon adder (`pylon_adder`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** The cable-run beside the path spits a blue spark, and the spark has a body — an adder charged from years on the lines, striking faster than the light changes.
- **Lore:** Charged and fever-bold, striking from the cable-runs.
- **Origin:** Native — an infected animal of the stolen land. Originally a warmth-seeking adder that basked on the cables.

### Flicker-wight (`flicker_wight`)
- **Size:** at-floor peer (medium) — traits: magic_resist
- **Description:** In the dark between two flashes there is a man-shape at the junction box. In the light there is nothing. The dark comes again, and the shape is closer.
- **Lore:** A keeper electrocuted at a junction, aether caught in the arc. It exists only between flashes.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Warden Glarefang (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The field goes black and stays black. Glarefang is already moving — a shadow-line wolf maned in pylon-lamps that strobe blinding-bright, seen only in the dark between its own flashes, rushing when the light dies.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 10 — The Kingsfield (biome: Men, tier 1, gate town: Bannerline)

**Landscape:** A great muster-meadow drowned in banners — the field where Men gathered their armies, cut off mid-muster, a hundred standards rotting on their poles. The banners hang colorless in the dead air. They crowned a goblin to guard it. They know you're coming.

### Goblin guard (`kings_guard`)
- **Size:** at-floor peer (medium) — traits: armoured
- **Description:** A goblin of the honor-watch bars the path in overlapped tower plate, collared, better armed than anything below. It guards a king it despises, and old arrows lie snapped where its plate turned them.
- **Lore:** Goblins have no business on a muster-meadow of Men. Gnarl's honor-watch was posted here as mockery doubled, and knows it.
- **Origin:** Pressed — a conscripted person, NOT an infected animal.

### Banner-broken wolf (`banner_wolf`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A wolf comes down the tent-lane dragging six feet of rotted standard tangled at its neck, half-starved and past caring what the colors used to mean.
- **Lore:** Tangled in dragging colors, it hunts the tent-lanes.
- **Origin:** Native — an infected animal of the stolen land. Originally a camp-follower wolf of the muster.

### Courier-hound (`courier_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A courier-hound rounds the horse-lines at a dead run, satchel long rotted off its harness. Its route runs through where you stand. It does not reroute.
- **Lore:** It runs its dead routes forever, savaging what it finds on them.
- **Origin:** Native — an infected animal of the stolen land. Originally a message-dog of the muster line.

### Parade-horse (`parade_horse`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A war-horse stands riderless among the muster-tents, tack rotted to straps, eyes white. It has waited eighty years for a rider, and it has stopped wanting one.
- **Lore:** Riderless and fever-wild, it tramples the churned field.
- **Origin:** Native — an infected animal of the stolen land. Originally a war-horse of the line.

### Banner-kite (`bunting_kite`)
- **Size:** small and slight — traits: frail, fly
- **Description:** A kite drops off a banner-pole and opens wide over you — a scavenger grown king-sized in the standards, stooping at the brightest thing on the field.
- **Lore:** Nesting in the standards, it stoops on anything bright.
- **Origin:** Native — an infected animal of the stolen land. Originally a scavenging kite of the camps.

### Muster-wight (`muster_wight`)
- **Size:** at-floor peer (medium) — traits: magic_resist
- **Description:** Across the churned field a rank of half-there soldiers forms up out of the mire, dresses its line on a rotted standard, and wheels toward you, marching nowhere else.
- **Lore:** The field's dead, aether pooled in the trampled mire. A rank that forms and marches nowhere.
- **Origin:** Wrongmade — MADE by the tower, NOT infected; nothing living was ever in it.

### Gnarl, the Goblin King (warden)
- **Size:** boss — fills the stair-gate
- **Description:** On a throne of banner-poles and broken spears slouches Gnarl, crowned as the tower's own joke, a notched sword too big for him across his knees. He raises a hand, and the field goes quiet enough to hear the lift humming behind the throne.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 11 — The Rustwater Adit (biome: Ironvale, tier 2, gate town: Lampfall)

**Landscape:** The meadows end against mountain-root bolted to the tower's ribs. A mine mouth breathes cold air and rust-red water, and the dwarf lamps over the adit still burn, tended by nobody. Small clawed tracks stitch every path going in.

### Kobold scavenger (`kobold_scavenger`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A kobold backs out of a side-shaft dragging a sack of stripped copper. It weighs the sack against its life, sets it down gently, and picks up a pry-bar.
- **Lore:** It has survived every collapse this mine has offered by being the first thing out. The pry-bar is for slower questions.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rust hound (`rust_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Something bred to guard this mine still guards it — a hound of wire and hide, joints weeping orange, nose down to the rust-water as it comes.
- **Lore:** Bred to run down thieves in the galleries. The rust never reached the part that wants your heels.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc outrider (`orc_outrider`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, armoured
- **Description:** An orc in half a warframe rounds the tailings heap, one arm bare and one arm hydraulic. It marks you down for the warband's ledger and doesn't wait for an answer.
- **Lore:** Half a warframe still turns half the blows. The ledger it keeps is short on mercy.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Adit bat (`adit_bat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** The dwarf lamps flicker as something drops from the adit's arch — a bat broad as a cloak, wings papering the cold updraft, circling your light once before it commits.
- **Lore:** It roosts in the lamp-warmth over the mine mouth and takes its meals off whatever the lamps draw in.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Rustmaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The stair is walled behind a rockfall, and the rockfall moves. Rustmaw unfolds — a tunneling engine grown teeth, ore-crusher jaws dripping red water while it takes your measure.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 12 — The Flooded Mine (biome: Ironvale, tier 2, gate town: Pumpstead)

**Landscape:** The dwarves drowned this mine on purpose, to stop what was digging up at them. When the tower took it, the pumps came back on halfway. Now the galleries stand waist-deep and black, and the water is never quite still.

### Bilge kobold (`bilge_kobold`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A kobold poles past on a raft of crate-lids, spear in hand. It has fished these galleries long enough to know that climbers float face down, eventually.
- **Lore:** It poles the flooded galleries by lamp-hiss and habit. Climbers float face down eventually; it just keeps the schedule.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drowned hauler (`drowned_hauler`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** An ore-hauler wades out of the flood on six seized legs, lamps shorting under a skin of silt. Its bed is empty. It has decided you are ore.
- **Lore:** Dwarf-plate seized over six legs of ore-cart iron. Slow as the flood and about as easy to argue with.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc salvage-diver (`orc_diver`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, armoured
- **Description:** An orc surfaces in a sealed warframe, water sheeting off the plate. It was down there stripping dwarf-steel, but a climber pays better than salvage.
- **Lore:** A sealed warframe keeps the water out and some of the steel in. Salvage pays; you pay better.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sump eel (`sump_eel`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** The black water folds and something long crosses the gallery at knee depth — a pale-bellied eel thick as a hawser, mouthing the current for the taste of you.
- **Lore:** It came up the pump-lines when the water came back, and it has been growing ever since.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Sumplock (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the drowned stair the water climbs a shape that should not stand — Sumplock, pump-iron and pale weed knotted over old bone, holding the lift gate shut with the patience of the flood.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 13 — The Counting Halls (biome: Ironvale, tier 2, gate town: Ledgerstone)

**Landscape:** Every ounce that left the mines was weighed here, in halls of brass and slate. The tally-engines still run on habit, counting shipments that stopped coming years ago. Kobolds have learned to read just enough to argue with them.

### Kobold coin-sifter (`coin_sifter`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A kobold sits in a drift of worthless scrip, sorting it by color. It takes your arrival as a bid on its hoard and reaches for the weighing-hammer.
- **Lore:** It cannot read the scrip it hoards, but it knows exactly what a hand reaching for the pile means.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Haywire tally-engine (`tally_engine`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce, armoured
- **Description:** A brass engine unbolts itself from the counting bench, arms still flicking beads on a broken frame. It has found an error in the ledger, and the error is you.
- **Lore:** Brass casing, broken arithmetic. It has been counting to the same wrong number for years.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc debt-collector (`debt_collector`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** An orc in a warframe painted with tally-marks blocks the aisle. The warband taxes this floor, it explains, and you have walked in carrying assets.
- **Lore:** The warband taxes everything that walks this floor. The plate is company property; the enthusiasm is its own.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ledger wisp (`ledger_wisp`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** A pale figure of dust and lamplight rises off the grand ledger — a wisp in the shape of a column of figures, drifting toward you to be balanced.
- **Lore:** The Counting Halls remember every unpaid ounce. Some of that memory has come loose and drifts.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Scrip rat (`scrip_rat`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A rat surfaces from a drift of colored scrip, cheeks packed with paper, and decides the shortest way to its next nest runs straight through you.
- **Lore:** It nests in worthless money and defends it like treasure, which on this floor passes for wisdom.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Brassbone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Brassbone hangs above the grand scales, a skeleton of counting-rods and weight-plates. It drops onto the pans, balances perfectly, and waits to weigh you out.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 14 — The Gear Galleries (biome: Ironvale, tier 2, gate town: Sprocket Row)

**Landscape:** Whole halls of gearing, floor to unseen ceiling, that once turned the mines' lifts and hammers. Half of it still creeps, tooth by tooth, fed by some deep spring nobody has found and shut off. The sound gets into your back teeth.

### Kobold gear-thief (`gear_kobold`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A kobold rides a slow-turning wheel down from the dark, wrench in its belt, prying off cogs as it goes. It hops off at your level and sizes up your kneecaps.
- **Lore:** It strips cogs the way other things strip carcasses — patiently, from the edges in, wrench-first.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Runaway flywheel (`loose_flywheel`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A flywheel the size of a millstone has shaken off its axle and rolls the gallery lengthwise, hunting by echo. It has worn its own road into the floor.
- **Lore:** A millstone of drive-iron that shook off its axle years ago. It only knows one direction at a time.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc pit-fighter (`pit_fighter`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** Between two meshing wheels an orc has chalked out a fighting ring. It steps over the line, cracks its warframe's knuckles, and waits for you to be polite about it.
- **Lore:** Chalk ring, house rules, no plate above the waist. It wins bets here, and you are the odds.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Belt-runner (`belt_runner`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A sleek shape flickers along the moving belts overhead, riding the machinery like a current, and comes off the last pulley at your chest, all claws and momentum.
- **Lore:** Something marten-quick lives on the drive belts and has never once touched the floor.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Gearhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Gearhide walks on four legs of stacked cogs, plates of clutch-iron for a hide. Every step re-meshes; every step is louder. The stair turns behind it like one more wheel.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 15 — The Fusion Vaults (biome: Ironvale, tier 2, gate town: Half-Light)

**Landscape:** The heart of dwarf-country: vaults where they split atoms the way their grandfathers split stone. The great cores still glow behind yard-thick doors, and the light through the seams is the only dawn this floor gets.

### Glow-sick kobold (`glow_sick_kobold`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, magic_resist
- **Description:** A kobold that has slept too close to the vault doors comes at you shedding faint light, fur out in patches, eyes wrong. It is past fear, which is worse.
- **Lore:** The vault-light got into it years back. Fear burned away first, and spells find little left to grip.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc fuel-thief (`fuel_thief`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** An orc hauls a lead-lined pannier of stolen core-rods, warframe straining. Dropping the load would mean doing this run twice, so it means to go through you.
- **Lore:** Two runs a night, lead pannier full, and every climber met is time lost. It has no plans to lose time politely.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Forge remnant (`forge_remnant`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A dwarven vault-tender, headless since the fall, still walks its rounds on magnetic feet. It cannot find its checklist, so it has simplified the job: nothing passes.
- **Lore:** A vault-tender in dwarf-plate, headless and thorough. The checklist is gone; the round continues.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rod-wisp (`rod_wisp`)
- **Size:** at-floor peer (medium) — traits: savage, fly
- **Description:** Between the vault doors the air brightens wrong — a figure of bare glow drifting the seam-light, carrying nothing, casting no shadow, coming to see yours.
- **Lore:** Light that leaked from a cracked core and learned the shape of a lantern-bearer. Spells pass through it like more light.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Coreburn (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Coreburn stands where the vault light is brightest, a furnace-beast with a cracked core for a heart, seams glowing brighter as it moves. The dwarves built the doors thick for a reason.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 16 — The Anvil Commons (biome: Ironvale, tier 2, gate town: Hammerhome)

**Landscape:** A hundred family forges around one great communal anvil, the way dwarves have always worked: alone, together. The plasma feeds still run hot. The Red Orcs use the Commons now, and what they make is cruder and works fine.

### Red Orc armorer (`orc_armorer`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** An orc at a stolen forge beats a dent out of a warframe pauldron, sees you, and considers the time saved by taking yours off you instead.
- **Lore:** It hammers warframes for the warband and wears its best work to the job. Trade-ins accepted, forcibly.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kobold hammer-carrier (`hammer_kobold`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A kobold staggers past under a smith's hammer twice its height, apprenticed to the orcs by force of habit. It decides you are the day's first lesson.
- **Lore:** Apprenticed by habit to whoever holds the forge. The hammer is twice its height; it has learned exactly one swing.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Half-forged thing (`half_forged`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** Something left on the great anvil mid-making has finished itself. It walks on tong-legs, still cherry-hot down one side, looking for its maker or a substitute.
- **Lore:** Left on the great anvil mid-making, it finished itself. One side is still cooling; the temper never set right.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Bellows hound (`bellows_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A hound comes through the forge-smoke at a flat sprint, coat singed to wire, and does not slow — the Commons taught it that everything worth having is taken at speed.
- **Lore:** Forge-hounds were bred to run messages between family fires. The families are gone; the running is not.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Anvilback (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Anvilback carries the old communal anvil fused into its spine, and a lifetime of hammer-blows has gone into its temper. It sets its feet at the stair like a work-piece being clamped.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 17 — The Smelterworks (biome: Ironvale, tier 2, gate town: Crucible Gate)

**Landscape:** The great smelters have not been fired in years, but the slag-runs never cooled all the way. Heat shimmers over black glass channels, and the ladles hang overhead like church bells nobody dares ring.

### Slag rat (`slag_rat`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A rat the size of a hound noses out of a cooled ladle, coat shingled with flakes of black glass. Generations in the warm dark have not made it timid.
- **Lore:** Generations in the warm dark under the ladles made it big, and none of them made it timid.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kobold ladle-crew (`ladle_crew`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Three kobolds work a hand-crank to swing a full ladle over the walkway you are on. They wave down at you, helpfully, so you know whose fault it is about to be.
- **Lore:** Three kobolds, one crank, and a firm belief that whatever the ladle lands on had it coming.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Red Orc smelter-boss (`smelter_boss`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** The orc who claims this floor's metal wears a warframe caked in spatter and carries a tapping-rod like a spear. Quota is short. You are made of salvage, technically.
- **Lore:** Quota is short and the plate is thick with spatter no chisel will shift. Everything here is salvage to it, you included.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Heat-haunt (`heat_haunt`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, magic_resist
- **Description:** The air over the slag channel gathers into a standing shimmer, man- shaped and patient, warping the gallery behind it. It closes the distance without seeming to cross it.
- **Lore:** The shimmer over the slag-runs sometimes stands up and walks. The old smelter crews would not work alone.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Smeltjaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Smeltjaw drags itself out of the main channel, a beast of half-set slag with a seam of live melt for a throat. Where it walks the floor smokes, and the stair stands just past it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 18 — The Deep Drifts (biome: Ironvale, tier 2, gate town: Ropewalk)

**Landscape:** Below the halls, below the vaults, the drifts where the dwarves dug last and quietest. The winch-ropes still hang down the shafts, taut under loads nobody signed for. Lamps are scarce here, and the dark has had years to settle in.

### Blind kobold digger (`blind_digger`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A kobold pale as candle-wax feels its way along the drift, pick swinging in easy time. It stops. It heard you breathe, and down here that is all the introduction it needs.
- **Lore:** Wax-pale and eyeless three generations down. In the dark you are the one at the disadvantage, and it knows it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Winch-crawler (`winch_crawler`)
- **Size:** small and slight — traits: frail, fierce, armoured
- **Description:** A winch head has pulled itself off its mounts and climbs the drift on its own cable, hand over iron hand. It pays out a loop toward your ankles, patient as machinery.
- **Lore:** A winch head climbing on its own cable, hand over iron hand. It has never hurried and never let go.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pit hound (`pit_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** The rust hounds that went down the shafts bred stranger — longer, quieter, eyes gone milky and ears gone huge. This one has been pacing you for three turnings.
- **Lore:** The deep shafts bred the rust hounds longer and quieter. By the time you hear it, it has counted your paces.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drift moth (`drift_moth`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** Your lamp gutters as a moth the span of two hands settles out of the drift's ceiling dark, wings shedding grey powder, drawn to the flame you cannot afford to put out.
- **Lore:** It feeds on lamp-oil and dust, and it likes its meals lit. Miners learned to work dark for a reason.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Deepwinch (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the last shaft the ropes all run to one drum, and the drum has grown a body. Deepwinch reels itself upright, cables singing, and the lift behind it moves only when it says so.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 19 — The Broken Doors (biome: Ironvale, tier 2, gate town: Last Lantern)

**Landscape:** This is where the dwarves made their stand: vault doors a yard thick, blown off their hinges and lying where they fell. The scorch-marks climb three stories. Nobody has moved the doors. Nobody could.

### Red Orc door-breaker (`door_breaker`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A veteran of the breach, warframe scarred by dwarf-fire, patrols the fallen doors it helped fell. It remembers this floor costing blood, and means to be repaid.
- **Lore:** It was in the breach when the doors came down, and the warframe still carries the dwarf-fire scars. It is owed, it feels.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kobold powder-boy (`powder_kobold`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A kobold in a scorched apron trots past with a keg under each arm, fuse-cord looped around its neck like a scarf. It grins and sets one keg down between you.
- **Lore:** A keg under each arm and a fuse for a scarf. It has outlived every crew it ever served, which should worry the crews.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Doorward remnant (`doorward_remnant`)
- **Size:** at-floor peer (medium) — traits: bulwark, fierce
- **Description:** One dwarven door-engine survived the breach, and it has not accepted the news. It holds a doorway with no door, halberd-arms crossed, and will not be reasoned past.
- **Lore:** One door-engine survived the breach and never accepted it. It cannot be argued past — only outlasted.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Breach crow (`breach_crow`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** A crow the size of a dog drops off a fallen door-slab and beats up into the scorched dark, circling — it has watched enough battles here to know to wait for the middle.
- **Lore:** It followed the Red Orcs up-tower the way crows have always followed armies. The breach was the best day of its life.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Scorch rat (`scorch_rat`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A rat with burn-bald patches works the seam of a fallen door, prying at old rations. It looks up with the flat calm of a survivor and comes over to try you instead.
- **Lore:** The breach cooked everything in the hall but the rats, and the rats took notes.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Gatebone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Gatebone was built from the breach's wreckage — hinge-plates for shoulders, a slab of blown door for a shield. It fights like the last argument of a people who built things to hold.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 20 — The Red Warcamp (biome: Ironvale, tier 2, gate town: Shieldwall)

**Landscape:** The last hall before the lift is a warcamp now — cookfires in ore carts, warframes racked like cordwood, the Red Orcs' banner hung from the dwarves' own crane. Drums somewhere deeper keep a slow time. They are not for you. They are for him.

### Red Orc honor guard (`honor_guard`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** Two orcs of Skarn's own guard, warframes polished to a dull red shine, cross their glaives without a word. Getting this posting cost them both something. It shows.
- **Lore:** Skarn's own, in plate polished to a dull red shine. The posting cost them blood, and they intend it to cost you more.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warframe champion (`warframe_champion`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, armoured
- **Description:** A pit champion in a full salvaged warframe rolls its shoulders, plates ringing. It fought its way up from the gear galleries for the honor of being the one you meet.
- **Lore:** It fought up from the gear galleries pit by pit for the honor of meeting you first. The salvaged frame fits like a reputation.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warcamp hound (`camp_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** The Red Orcs kennel their rust hounds on short chain and shorter rations. This one has slipped both, and the camp watches with professional interest to see how you do.
- **Lore:** Short chain, shorter rations, and it slipped both. The camp is betting on the hound.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drum kobold (`drum_kobold`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A kobold with a war-drum bigger than itself plants its sticks mid- beat when it sees you. Protocol is clear: the beat must not stop, and you must.
- **Lore:** It keeps the warcamp's slow time. The drums are not for you — but a dropped beat brings the whole camp's eyes.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Camp looter (`camp_looter`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A scarred goblin picks along the racked warframes with a sack of lifted buckles, sees you, and weighs the sack against the bounty Skarn posts on climbers. The sack loses.
- **Lore:** Every army drags a tail of things that fight for the leavings. This one has done well by the Red Orcs.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warlord Skarn (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Skarn of the Red Orcs takes the field in a warframe built from the best of three dead clans, dwarf-steel over orc muscle. He gives you a nod, one professional to another, and picks up his axe.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 21 — The Mirefields (biome: The Barrows, tier 3, gate town: Cairnside)

**Landscape:** The mine air gives way to marsh air, which is not an improvement. Drowned fields run to a grey horizon under a lid of fog, studded with burial cairns older than any war you have heard of. The mud holds footprints going in. Fewer coming out.

### Mire ghoul (`mire_ghoul`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A ghoul rises out of the standing water without hurry, grave-mud sliding off its shoulders. It has eaten well since the tower came, and it looks at you like more of the same.
- **Lore:** It has eaten better since the tower came than its whole line ate before it. It sees no reason the run should end.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Bog hound (`bog_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Something that used to be a hound follows the old towpath, coat slicked black, too many joints working. It died loyal to somebody. It is not loyal now.
- **Lore:** It died loyal to somebody on the old towpath. What runs it now keeps the route and lost the loyalty.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cairn-light (`cairn_wisp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** A soft light drifts off a cairn and comes across the water toward you, warm as a lodge window. The locals had one rule about the lights, and this is exactly the wrong direction.
- **Lore:** The locals had one rule about the cairn-lights: never follow. Nobody made a rule for when the light follows you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mire leech (`mire_leech`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** The water between two cairns humps and slides — a leech long as a rowboat, back crusted with old coins that stuck, homing in on the warmth of you.
- **Lore:** The drowned fields feed everything slowly except the leeches, which have never once been patient.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Mirebone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The causeway to the stair runs through one great cairn, and the cairn stands up. Mirebone wears the stones of a dozen graves like a shell, and under them, something drowned keeps walking.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 22 — The Tithe Barrows (biome: The Barrows, tier 3, gate town: Wakewater)

**Landscape:** Rows of low barrows with toppled offering-posts, where the marsh folk once paid their dead in bread and tin. The tower tore the land up with the graves still in it, and the dead noticed. The offering-bowls have been licked clean.

### Tithe-wight (`tithe_wight`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A wight in the rags of a tithe-priest stands at a barrow door, holding out a bowl of green-scaled tin. The custom is older than it is. Pay, or be paid.
- **Lore:** The custom is older than the priest: the dead are owed bread and tin. The bowl has been empty a long time.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Barrow ghoul (`barrow_ghoul`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** This ghoul has dug clean through a barrow and out the other side, and wears somebody's torc pushed up its forearm. It is proud of the torc. It comes on all fours.
- **Lore:** It dug clean through a king's barrow and came out proud, wearing his torc. Rank, among ghouls, is worn on the forearm.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Grave beetle (`grave_beetle`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A beetle the size of a shield surfaces through the turf of a barrow roof, mandibles working wetly. The old dead fed a whole economy down there, and you count as a delivery.
- **Lore:** The old dead fed a whole economy under the turf. Its shell is the marsh's answer to a shield wall.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Barrow rat (`barrow_rat`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A rat noses out of a toppled offering-post, sleek on a century of bread left for the dead, and takes your arrival for the next delivery.
- **Lore:** It lives on offerings and offal, and it has learned that climbers carry both.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Tithegrim (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Tithegrim keeps the stair the way its order kept the barrows — a wight in a verdigris mask, ledger-chains wound to the elbow. It counts you among the arrears and moves to collect.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 23 — The Lightless Glade (biome: The Barrows, tier 3, gate town: Lanternroot)

**Landscape:** The elves' stolen forest, sunk hip-deep in the marsh it was welded to. The bio-lights that once lit the deep woods hang dark on every bough, like a city with the power cut. Older elves in Roothollow will not say what walks here. You are about to find out.

### Pale stag (`pale_stag`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A stag comes through the dead lights, white as root-flesh, antlers hung with dark lamp-vines. The elves bred them to carry the forest light. It remembers the weight of it, and hates you fresh.
- **Lore:** The elves bred it to carry the forest light through the deep woods. It remembers the weight of it, and hates you fresh.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Glade-wight (`glade_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** An elf did not leave when the lights died. What is left of her tends a dark lamp-tree, and turns at your step with pruning-hook raised — the garden does not take visitors now.
- **Lore:** She stayed when the lights died, and the garden kept her. Spells slide off what is left like rain off wax leaves.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Lamp-eater (`lamp_ghoul`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A ghoul has learned to crack the dead bio-lamps for the marrow of light left in them, and its belly glows faint through the skin. It drops the husk it was working on.
- **Lore:** It cracks the dead bio-lamps for the marrow of light inside, and its belly glows faint through the skin.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Lamp moth (`lamp_moth`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Wings the grey of dead leaves open on a bough above you — a moth grown huge on lamp-marrow, drawn off its dark tree by the smallest light you carry.
- **Lore:** When the bio-lights went dark the moths did not leave. They just got hungrier about what light remains.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Palegleam (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the heart of the glade one tree still burns with the old forest light, and Palegleam is coiled around it — root and grave-cloth and a crown of stolen lamps. It will not share the last of the light.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 24 — The Rig Graves (biome: The Barrows, tier 3, gate town: Rustwake)

**Landscape:** A war was fought over this marsh once, by soldiers in exo-rigs built to keep them dry. The rigs are still here, rusted to the hips in bog water, and the marsh has been patiently finishing what the war started. Some of the rigs still stand watch.

### Rig-wight (`rig_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** An exo-rig hauls itself out of the bog with its soldier still strapped in, dead these many years and still on duty. The rig whines. The soldier salutes. Then it charges.
- **Lore:** The soldier is dead these many years and still on duty. The rig keeps the watch; the salute is muscle memory.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rig-stripper ghoul (`marsh_ghoul_crew`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A ghoul has spent years learning to open exo-rigs like oysters, and its knuckles are capped with salvaged plate. It looks at your armor the way it looks at rigs.
- **Lore:** Years of opening exo-rigs like oysters capped its knuckles with salvaged plate. Your armor reads as shell.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drowned beacon (`drowned_light`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, magic_resist
- **Description:** A rig's distress beacon still blinks under a foot of bog water, and something has learned to sit beside it and wait. The light draws rescuers. The waiting thing eats them.
- **Lore:** The beacon still blinks under a foot of bog water. The thing beside it learned that light draws rescuers.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Marsh adder (`marsh_adder`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A black adder pours off a rusted rig's shoulder and writes a fast line through the bog water toward your boots, jaw already wide.
- **Lore:** It dens in a flooded rig's chest cavity, which tells you everything about the neighborhood.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Rigrot (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Rigrot is what the marsh made of a command rig and its whole crew — four rigs rusted into one shape, walking on borrowed legs. Somewhere in it a speaking-horn still crackles orders no one gives.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 25 — The Processional Way (biome: The Barrows, tier 3, gate town: Mourngate)

**Landscape:** A raised stone road runs arrow-straight through the marsh, built for funerals and nothing else. Every slab is a name. The processions stopped when the tower came, but the road remembers its purpose, and things line the verges waiting for the next one.

### Procession-wight (`procession_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A wight in mourning-grey walks the center of the road, bell in hand, leading a procession of nobody. It stops. It has been short one mourner for a very long time.
- **Lore:** It has led ten thousand funerals and been short one mourner for a century. Grief that old stops taking no.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Verge ghoul (`verge_ghoul`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Ghouls learned generations ago that funerals mean fresh graves, and this one still works the road out of habit. It paces you in the reeds, keeping polite funeral distance.
- **Lore:** Funerals mean fresh graves; the road taught it that generations ago. It keeps polite funeral distance until it doesn't.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Passing-bell light (`bell_wisp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** A light drifts ahead of you tolling like a small bell, keeping just at the edge of sight. It is ringing a passing-bell, you realize. It is ringing it for you.
- **Lore:** It rings a passing-bell for the about-to-die. It is rarely wrong, and it is ringing now.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Coffin-bearer (`coffin_bearer`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, armoured
- **Description:** Up the center of the road comes a shape of two bearers grown into one iron-bound coffin, step by processional step. It sets its burden down. It opens the lid for you.
- **Lore:** Two bearers fused to one iron-bound coffin, still walking the route. Nobody has looked inside and reported back.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Mournhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Where the road meets the stair stands the hearse-beast Mournhide, still in its rotted funeral harness, plumes and all. It has carried every name on this road, and it stamps once, ready to carry yours.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 26 — The Peat Cuts (biome: The Barrows, tier 3, gate town: Turfside)

**Landscape:** Generations of marsh folk cut fuel here, and the cuts run like black canals to the fog line. Peat keeps what it takes — the diggers used to find old kings in the banks, leather-brown and sleeping. The tower's theft shook the banks loose. The kings are up.

### Peat-cured king (`peat_king`)
- **Size:** at-floor peer (medium) — traits: bulwark, savage, magic_resist
- **Description:** A bog king climbs from the cut-bank, tanned black by a thousand years of peat, torc still bright. He was somebody once, and being dead has not talked him out of it.
- **Lore:** A thousand years in the peat tanned him tough as boat leather. Every wound closes with a wet brown sound — outlast him if you can.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cutter ghoul (`cutter_ghoul`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A ghoul works a peat-cutter's blade along the bank with terrible patience, harvesting things the diggers missed. It marks where you stand as its next cut.
- **Lore:** It works the banks with a peat-cutter's blade and a harvester's patience. You are standing on its next cut.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Turf hound (`turf_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A hound of packed peat and root shakes itself apart and back together, coming up the cut. Thrown stones just improve it.
- **Lore:** Packed peat and root in the shape of loyalty. Thrown stones just improve it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Midge cloud (`midge_cloud`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** The fog line detaches a piece of itself and hums toward you — a midge cloud thick enough to blot the cut-banks, moving with one slow appetite.
- **Lore:** Marsh midges in a swarm dense enough to have opinions. The cuts breed them by the ton.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Peatlock (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Peatlock holds the stair-cut, a giant of black turf with an old king's torc sunk in its chest like a keel-mark. Every wound you open closes with a wet brown sound.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 27 — The Bone Garths (biome: The Barrows, tier 3, gate town: Garthend)

**Landscape:** Walled yards where the marsh folk laid out their dead for the birds, as their custom asked. The walls still stand, the gates still latch, and the yards are still in use — but nothing has flown over this floor in years, and the dead are not being taken up.

### Garth-keeper (`garth_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The keeper of the yards still makes its rounds, keys at its belt, little more than vestments and wind. It finds a gate you left unlatched. There is no arguing about the fine.
- **Lore:** Little more than vestments and wind, still making its rounds. The fines are old law, and old law does not haggle.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Yard ghoul (`yard_ghoul`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** With the birds gone, the ghouls have taken over the work, and they resent the workload. This one comes over the garth wall lean, quick, and behind on quota.
- **Lore:** With the birds gone the ghouls took over the sky-burial work. This one is lean, fast, and behind on quota.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Restless heap (`bone_heap`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** One of the laid-out dead has grown tired of waiting for the sky and gathered its neighbors for company. The heap moves like a crowd that has just found its voice.
- **Lore:** The laid-out dead grew tired of waiting for a sky that never comes. Together they are patient, and slow, and many.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Picker rat (`picker_rat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A rat the size of a terrier works along a burial platform with a tradesman's confidence, sees you watch, and takes offense at the audience.
- **Lore:** The rats do the birds' old work now, badly. The garths have never been so crowded.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Garthbone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Garthbone is the yards' answer to the missing birds — a rook of bone and grave-iron the size of a hay barn, wings creaking wide. It will take the dead up itself, and you qualify.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 28 — The Sunken Chantry (biome: The Barrows, tier 3, gate town: Bellmarsh)

**Landscape:** A chantry to the old river gods, taken with the marsh and settling ever since — nave flooded to the pews, tower leaning like a man asleep on his feet. The bells still ring the hours. Nobody winds them. The hours they ring are wrong.

### Chantry cantor (`chantry_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A wight stands waist-deep at the altar, keeping the offices in a voice like water in a crypt. You have interrupted. The congregation, surfacing behind you, agrees.
- **Lore:** It keeps the offices in a voice like water in a crypt. The old river gods may even still be listening.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Font ghoul (`font_ghoul`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A ghoul crouches in the great stone font like a bird bath gone wrong, cracking something against the rim. It has claimed sanctuary here for years. It does not extend it.
- **Lore:** It claimed sanctuary in the great font years ago. Sanctuary, it has decided, does not extend to visitors.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Vigil light (`vigil_light`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** A votive flame floats up the flooded nave toward you, its little brass boat long since sunk. Each pew it passes, something under the water sits up.
- **Lore:** A votive flame that outlived its brass boat. Each pew it passes, something under the water sits up.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drowned congregant (`drowned_congregant`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A pew shifts and one of the congregation stands up through the black water, hymnal still in hand, and wades into the aisle to greet the interruption.
- **Lore:** The congregation never left the pews when the nave flooded. Attendance, in fact, has improved.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Bellrot (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Bellrot hangs in the drowned belfry, grown into the great bell like a hermit crab into its shell. When it rings itself, the water in the nave jumps — and so does everything sleeping in it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 29 — The Doorstone Moor (biome: The Barrows, tier 3, gate town: Stonewake)

**Landscape:** The moor before the Kingsbarrow is set with standing stones, each one a sealed door in the old tongue. The marsh folk raised them to keep something in, and maintained them for a thousand years. Maintenance has lapsed. Some of the doors stand ajar.

### Doorstone warder (`door_wight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A wight in rusted mail leans against its stone the way it has for centuries, spear planted. It was set here to challenge whatever comes off the moor. That is you.
- **Lore:** Set at its stone a thousand years ago to challenge whatever comes off the moor. The mail rusted; the orders didn't.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Moor ghoul (`moor_ghoul`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** This far in, the ghouls are old and careful and fat on what leaks through the doors. One shadows you between the stones, waiting to see whether the moor kills you first.
- **Lore:** This far in, the ghouls are old and careful and fat on what leaks through the doors. It can afford to wait.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Something unsealed (`unsealed_thing`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** From a stone standing ajar comes something the old folk went to real trouble over — half shadow, half smell of deep earth. It pours itself upright and takes a shape roughly yours.
- **Lore:** The old folk went to real trouble sealing it. It is half out of the world still, and spells reach only the half that isn't here.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Moor hound (`moor_hound`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** Between two standing stones a hound breaks from a flat-out run to a stalk — moor-grey, low, and already closer than the fog said it was.
- **Lore:** It courses the stone rows at night. What it was bred to keep in, it now keeps company.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Doorstone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The largest stone on the moor is the Warden — Doorstone, a slab of grey granite that walks when it must, graven with every seal the marsh folk knew. The stair lies behind it. It is a door, and it is shut.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 30 — The Kingsbarrow (biome: The Barrows, tier 3, gate town: Wakesend)

**Landscape:** One barrow the size of a hill, ringed by a moat of black water and a century of tribute — swords, crowns, exo-rigs, all sinking slow. Every dead thing on this floor answers to what sleeps here, and the ground over it rises and falls like something breathing.

### Herald of the barrow (`kings_herald`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A wight in the wreck of royal livery bars the tribute-road, horn raised. It winds a note you feel in your fillings, and announces you, which is worse than an ambush.
- **Lore:** It announces you to the barrow in a note you feel in your fillings, which is worse than an ambush.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Tribute-bearer (`tribute_ghoul`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** A ghoul struggles toward the moat under a dead soldier in full rig, tribute for the King. Dropping the offering would shame it. It sets the body down carefully, first.
- **Lore:** Dropping the offering would shame it before the King. It sets the body down carefully, first.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kingsbarrow guard (`barrow_guard`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** The King's own guard wear the mail they were buried in and the exo-rigs they were buried with, rust and bone moving as one thing. Two of them peel off the barrow's flank toward you.
- **Lore:** Buried in their mail, buried with their rigs. Rust and bone move as one thing, and the plate remembers its trade.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Moat watcher (`moat_watcher`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** The moat's skin of black water bulges and a watcher rises draped in sunken tribute — crowns, sword-belts, rig-plate — wearing the hoard it is about to defend.
- **Lore:** A century of tribute sank into the black moat, and something grew fond of the collection.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The Barrow King (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The barrow opens like an eye and the King comes out crowned, robed in grave-mist, tall as the stones that failed to hold him. Every name in this marsh was once sworn to him. He has come to collect yours.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 31 — The Threshold Dark (biome: Webdeep, tier 4, gate town: Lastlight)

**Landscape:** The marsh fog ends at a cave mouth, and the cave mouth ends the light. Beyond the gate town's lamps the dark is total, older than the tower, and strung corner to corner with silk. The first rule of the Webdeep is written over the gate: touch nothing that hums.

### Cave broodling (`cave_broodling`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A spider the size of a dog drops from nowhere on a thread you never saw, legs finding your shoulders like an old friend. Its thousand siblings are audible, faintly, above.
- **Lore:** It has a thousand siblings audible above, and every one of them learned to drop before it learned to walk.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Silk-wrapped husk (`silk_husk`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A cocooned shape hangs at eye level across the path, and as your lamp touches it, it starts to struggle. That is the trap. The floor under it is not floor.
- **Lore:** The struggling cocoon is the lure. The floor under it is not floor, and it has all day.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Grave-moth (`blind_moth`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** A moth with a wingspan like a cloak blunders into your lamplight, eyeless and frantic. It is not dangerous. What follows it, hunting by the dust it sheds, is.
- **Lore:** Harmless itself — but what hunts by the dust it sheds is not, and the moth knows exactly whom to lead it to.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Threshold beetle (`threshold_beetle`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A beetle the size of a hound works along the base of the first webs, jaws crunching through old husks, and swings its lamp-bright eyes up at the fresher thing walking in.
- **Lore:** It cleans the webs of whatever the spiders leave, and it has stopped waiting for them to finish.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Duskspin (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The last lit yard of the threshold belongs to Duskspin, a spider old enough to have named the dark. It hangs over the stair in a web strung with lamps of other climbers, and dims them one by one.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 32 — The Cable Roots (biome: Webdeep, tier 4, gate town: Wiregate)

**Landscape:** The tower's veins run through this cavern — cables thick as oaks, branching down into the dark, carrying power to the floors above. Everything here lives off the leakage. The spiders' webs are woven copper-and-silk, and they carry a charge.

### Wire-weaver (`wire_weaver`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A spider picks its way down a live cable, abdomen glowing faint with stolen charge. Its web is half metal, and the flies it catches die before they finish landing.
- **Lore:** Its web is half copper and carries a charge. The flies die before they finish landing; climbers take a moment longer.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cable troll (`cable_troll`)
- **Size:** small and slight — traits: frail, fierce, armoured
- **Description:** A deep troll has chewed into a trunk cable and sits wearing it over its shoulders like a stole, jaw sparking. The leakage has done things to its temper.
- **Lore:** It wears a chewed trunk cable like a stole, and the leakage has done things to its temper the dark never managed.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Jittering husk (`sparked_husk`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A cocooned husk hangs tangled in the copper web, twitching in time with the current. When your shadow crosses it, it twitches toward you instead.
- **Lore:** It twitches in time with the current that keeps it. Cut the web and it just twitches toward you instead.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Charge-wisp (`charge_wisp`)
- **Size:** at-floor peer (medium) — traits: savage, fly
- **Description:** A bead of St. Elmo's light detaches from a cable joint and drifts down the aisle of webs toward you, swelling as it comes, the copper silk chiming under it.
- **Lore:** Leakage that pooled long enough to want things. Spells feed it more than they hurt it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Wirefang (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Where the cables converge, Wirefang has made itself the junction — a spider re-strung with copper sinew, fangs like stripped leads. It tests them once against the dark, and the whole web lights up.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 33 — The Broodwarrens (biome: Webdeep, tier 4, gate town: Silkstead)

**Landscape:** Warrens dug tight as honeycomb, every wall padded white with brood silk. The air is warm here, the only warm air in the Webdeep, and it smells of milk and vinegar. Things hatch in the walls as you pass. Try not to take it personally.

### Broodling swarm (`brood_swarm`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A patch of wall-silk sloughs off and becomes forty small spiders with one opinion. Individually they are nothing. They have never once been individually.
- **Lore:** Forty small spiders with one opinion. They have never once been individually.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warren troll (`warren_troll`)
- **Size:** at-floor peer (medium) — traits: bulwark, feeble
- **Description:** A deep troll has been silk-blinded and kept as a nursery guard, fed just enough. It fills the tunnel wall to wall, and it hears your heartbeat change.
- **Lore:** Silk-blinded and kept as a nursery guard, fed just enough. It fills the tunnel wall to wall — you will not go around it, only through.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Brood-midwife (`midwife_spider`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A long-legged spider tends a row of egg-sacs, turning each with terrible gentleness. It puts itself between you and the clutch before you have decided anything.
- **Lore:** It turns each egg-sac with terrible gentleness, and it put itself between you and the clutch before you decided anything.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warren bat (`warren_bat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Something leathery cuts through the milk-warm air of the warrens, shoulder-high and fast, riding the heat off the brood walls straight at your lamp.
- **Lore:** It nests in the one warm cavern of the Webdeep and pays rent in whatever it knocks from the air.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Cradlesilk (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The deepest warren belongs to Cradlesilk, swollen pale and near blind, the mother of every small horror you have met today. She does not leave the clutch. You will have to come to her.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 34 — The Troll Delvings (biome: Webdeep, tier 4, gate town: Delvers' Rest)

**Landscape:** Before the spiders, trolls dug here — crude, enormous galleries shouldered out of raw stone, ceilings lost to your lamp. The trolls are still digging. Nobody knows toward what, and the one time a climber asked, the answer took a week to bury.

### Delving troll (`delving_troll`)
- **Size:** small and slight — traits: frail, feeble, armoured
- **Description:** A deep troll comes up the gallery dragging a hand-sledge of rubble, knuckles first. You are standing on its spoil-heap. This is, by troll law, the whole of the case against you.
- **Lore:** You are standing on its spoil-heap. This is, by troll law, the whole of the case against you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Troll whelp (`troll_whelp`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** A young troll the size of an ox practices its digging against the gallery wall. It has just learned that soft things dig easier, and you are the softest thing it has seen all week.
- **Lore:** It has just learned that soft things dig easier, and you are the softest thing it has seen all week.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gallery stalker (`gallery_spider`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** The spiders follow the troll digs the way gulls follow a plow. This one keeps to the ceiling seam above you, matching your pace, patient as arithmetic.
- **Lore:** It follows the troll digs the way gulls follow a plow, and it keeps to the ceiling seam, patient as arithmetic.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rubble borer (`rubble_borer`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** The spoil-heap shifts and a borer surfaces — a segmented thing in plates of polished basalt, mouthparts turning like a drill-head as it corrects course toward you.
- **Lore:** A chitin engine the trolls' digging woke. It eats stone; everything else it bores through on principle.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Mossmaul (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Mossmaul is the oldest digger, grown into the stone until you cannot say where troll ends and gallery begins. It pulls its arm out of the wall it was becoming, and the whole delving shakes.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 35 — The Signal Deeps (biome: Webdeep, tier 4, gate town: Faintlight)

**Landscape:** The caverns here are stacked with the tower's thinking-engines, racks of them running down into the dark, warm to the touch and muttering. The spiders web the aisles for the heat. Whatever the engines are computing, they have been at it since the theft.

### Rack-weaver (`rack_spider`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, magic_resist
- **Description:** A spider has webbed an entire engine-rack into its nest and grown strange on the warmth. Its eyes reflect your lamp in rows, like little status lights.
- **Lore:** It webbed a whole engine-rack into its nest and grew strange on the warmth. Its eyes reflect your lamp in rows, like little status lights.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Signal husk (`signal_husk`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A husk hangs wired into the racks, and the engines have been using it — it walks toward you with a purpose nothing dead should have, trailing neat bundles of cable.
- **Lore:** The engines have been using it. It walks with a purpose nothing dead should have, and spells blur against whatever is being computed inside.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Heat-drunk troll (`heat_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A deep troll sleeps pressed against the warmest rack like a cat against a stove. Your footstep lands wrong. It is not asleep anymore.
- **Lore:** It sleeps pressed to the warmest rack like a cat against a stove. Your footstep landed wrong.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Aisle-runner (`aisle_runner`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** Down the long aisle every rack flickers in sequence, faster and faster — and then the spider making them flicker is already at your knee, all legs and momentum.
- **Lore:** Bred lean by generations of hunting the warm aisles. The racks light up as it passes, row by row.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Echobone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Echobone keeps the deepest aisle, a thing of rack-iron and troll bone that speaks in playback — your own voice, your own footsteps, everything the engines have heard you do since the threshold.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 36 — The Hanging City (biome: Webdeep, tier 4, gate town: Skeinside)

**Landscape:** A city hangs over the chasm, built entirely of silk — streets, towers, bridges, swaying in air that does not move. Something lived in it before the spiders; the shape of the doorways says so. The doorways are the wrong shape for spiders too.

### Bridge-weaver (`bridge_weaver`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A spider re-strings a sagging silk bridge ahead of you, working backward, watching you the whole time. You realize it is not repairing the bridge. It is adjusting the load rating.
- **Lore:** It is not repairing the bridge you are standing on. It is adjusting the load rating.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Citizen husk (`city_husk`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** A husk sits at a silk window in a silk chair, arranged with care, one arm raised in something like a wave. As you pass, the arm finishes the gesture.
- **Lore:** Arranged at a silk window with care, one arm raised. As you pass, the arm finishes the gesture.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Chasm troll (`chasm_troll`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, armoured
- **Description:** A deep troll climbs the city's underside, too heavy for any street, tearing handholds in other people's architecture. It surfaces through the floor ahead of you, apologizing to no one.
- **Lore:** Too heavy for any street, it climbs the city's underside, tearing handholds in other people's architecture.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Silk drifter (`silk_drifter`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** Above the swaying street a small shape casts a thread to the wind that does not blow, and rides it down toward your shoulders with the confidence of long practice.
- **Lore:** It balloons between the silk towers on threads of its own casting, and it boards passing climbers like cargo.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Skeinback (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The city's heart is a plaza of taut silk, and Skeinback walks it like a landlord — a spider carrying the whole city's tension in its web-lines. When it plucks one, somewhere a street goes slack.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 37 — The Trapdoor Fields (biome: Webdeep, tier 4, gate town: Latchlight)

**Landscape:** A cavern floor flat as a threshing yard, which should have been the first warning. Every few paces a hinge of silk, dusted to match the stone. The locals walk this floor like it is checkered, and only step on white.

### Trapdoor spider (`trapdoor_spider`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** The stone in front of you is a lid, and the lid is already open. What comes out is mostly forelegs, faster than an apology, dragging you toward a hole exactly your size.
- **Lore:** Mostly forelegs, faster than an apology. The hole it drags toward is exactly your size.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sprung trap (`sprung_husk`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A husk lies beside an open trapdoor, one boot still down the hole — a trap that fired and lost. As you edge past, the husk gets up, still fighting the fight it remembers.
- **Lore:** A trap that fired and lost, still fighting the fight it remembers. It gets up when you edge past.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Field-wise troll (`field_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, armoured
- **Description:** A deep troll crosses the fields by memory, stepping sure as a dancer, and it has noticed that you are watching its feet. It does not like sharing the route map.
- **Lore:** It crosses the fields by memory, sure as a dancer, and it does not like sharing the route map.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Dust moth (`dust_moth`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A moth works low over the field ahead of you, dusting each silk hinge grey — then rises at your lamp, wings shedding the same dust across your eyes.
- **Lore:** It powders the trapdoor lids to match the stone. The spiders tolerate it the way farmers tolerate crows.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Latchjaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The stair sits in plain sight on open ground, which tells you everything. Latchjaw's door is the size of a threshing floor, and Latchjaw is the size of what needs a door that size.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 38 — The Silk Vaults (biome: Webdeep, tier 4, gate town: Spoolgate)

**Landscape:** The spiders store their wealth here: vault after vault of wrapped shapes, hung in rows by size, catalogued by scent. Some bundles are provisions. Some are prisoners. The economy of the Webdeep does not distinguish, and the vault-keepers resent an audit.

### Vault-keeper (`vault_keeper`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A gaunt spider moves down the rows, touching each bundle once, counting. It reaches you — unlabeled, unwrapped, unaccounted for — and begins to correct the inventory.
- **Lore:** It counts by touch, bundle by bundle. You are unlabeled, unwrapped, unaccounted for — an error it was made to correct.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Fresh bundle (`fresh_bundle`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** One of the hanging shapes is still warm and very determined. It has worked one arm free, and what the arm is holding is a knife, and what the knife wants is anything that moves.
- **Lore:** Still warm and very determined. One arm free, one knife, and no questions left about how to use either.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Vault-breaker troll (`vault_troll`)
- **Size:** at-floor peer (medium) — traits: bulwark, fierce
- **Description:** A deep troll has broken into the vaults the honest way, through the wall, and is eating its way down a row like a man at a market stall. It regards you as queue-jumping.
- **Lore:** It came in the honest way, through the wall, and it eats down the rows like a man at a market stall. It will take a while to stop.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Vault rat (`vault_rat`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A rat drops from a hanging bundle with somebody's dried rations in its teeth, lands between you and the row, and declines — visibly — to share the territory.
- **Lore:** A vault of catalogued provisions is, from a rat's side of the ledger, simply a granary with opinions.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Spoolhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Spoolhide guards the vault door wound in its own product, layer on layer of silk over something you never quite see. Every cut you land unwinds a little more. You may not want to reach the middle.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 39 — The Egg Galleries (biome: Webdeep, tier 4, gate town: Palewatch)

**Landscape:** The approach to the Broodthrone runs through galleries of eggs, each sac tall as a door and lit faintly from inside. The light moves. The locals call this floor the nursery and will not say it above a whisper — everything here is Vyx's, and Vyx counts.

### Gallery sentinel (`gallery_sentinel`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** The spiders here do not hunt; they garrison. A sentinel drops into the aisle with drilled precision, mouthparts moving in what is unmistakably a challenge phrase.
- **Lore:** The spiders here do not hunt; they garrison. The challenge phrase is real, and there is no right answer.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hatching sac (`hatching_sac`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** An egg-sac beside you splits with a sound like wet canvas. What spills out is newborn and knee-high and already knows the two facts of its life: it is hungry, and you are near.
- **Lore:** Newborn and knee-high, it knows the two facts of its life: it is hungry, and you are near.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Brood-fed troll (`broodfed_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A deep troll has been given the run of the galleries in exchange for guard duty, paid in whatever fails inspection. It takes its work seriously. Its work is you.
- **Lore:** Paid for guard duty in whatever fails inspection. It takes the work seriously; the work is you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sac-light (`sac_light`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** One of the egg-glows slips its sac and drifts the gallery like a lantern looking for its keeper, and whatever it lights leans toward you in its shell.
- **Lore:** The glow that moves inside the eggs sometimes moves outside them. Vyx counts those too.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Husklight (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Husklight paces the last gallery wearing the drained shells of old challengers laced into armor. Inside it something glows the way the eggs glow, and it stands between you and the throne like an elder sibling.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 40 — The Broodthrone (biome: Webdeep, tier 4, gate town: Threadneedle)

**Landscape:** The heart of the Webdeep is one vast chamber, and the chamber is a web, and the web is a throne room. Every thread in the Deep ends here. The dark overhead is not empty — it is occupied, and it has been reading your footsteps since floor thirty-one.

### Throne-web guard (`throne_guard`)
- **Size:** small and slight — traits: frail, feeble, armoured
- **Description:** The Matriarch's guard are bred big and patient, and they hold the anchor-lines of the throne itself. This one lets you see it coming. The lesson is the point.
- **Lore:** Bred big and patient, holding the throne's own anchor-lines. It lets you see it coming — the lesson is the point.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Wrapped knight (`silk_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A climber in good plate got this far once, and Vyx kept him — webbed upright, armed, walking the perimeter on her threads like a puppet on patrol. The armor still works fine.
- **Lore:** A climber in good plate got this far once. The armor still works fine; the man inside works for Vyx now.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pale consort (`consort_spider`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A slender white spider descends with courtly slowness, one of the Matriarch's consorts. It has outlived all its rivals by being exactly this careful.
- **Lore:** It has outlived every rival by being exactly this careful, and it is faster than careful looks.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Thread-page (`thread_page`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A small spider drops to the floor ahead of you, taps out something quick on a taut anchor-line, and squares up — the message is sent, and the messenger has orders too.
- **Lore:** It runs messages along the throne-lines. What it reports, the whole chamber hears.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Tribute husk (`tribute_husk`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A husk climbs the great web hand over hand with a wrapped bundle roped to its back, tribute-bound for the dark overhead — and turns its dry face toward the obstacle you have just become.
- **Lore:** The Deep sends its rent up to the throne walking. Interfering with the post is taken poorly.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Matriarch Vyx (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The dark comes down. Vyx fills the chamber the way a hand fills a glove — the throne, the web, the ceiling, all one animal, eyes opening in constellations. She thanks you, in a dry whisper, for walking the whole way into her mouth.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 41 — The Ashline (biome: The Scorch, tier 5, gate town: Greywell)

**Landscape:** You come up out of the dark into heat like a hand on your face. Ash desert runs flat to a shimmering horizon, grey over the buried slag of some reactor the tower broke in the taking. The locals paint their roofs white, and their deep wells still come up warm.

### Ash salamander (`ash_salamander`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, magic_resist
- **Description:** A salamander surfaces through the ash like a swimmer, black- scaled, trailing heat-shimmer. Where it rests its chin, the ground glazes over.
- **Lore:** It swims the ash the way fish swim water, and heat rolls off it in welcome. Fire is where it lives; spells of it are a compliment.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Dune ogre (`dune_ogre`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** An ogre plods the ashline with a wagon axle for a walking stick, skin baked to crockery. It is crossing to somewhere cooler and has decided your water skin is community property.
- **Lore:** Skin baked to crockery, patience baked harder. Your water skin became community property on sight.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cinder vulture (`ash_vulture`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** Vultures out here roost on the warm vents and have gone strange with it, feathers singed to wire. One lands ahead of you at a polite distance, which out here is a diagnosis.
- **Lore:** It roosts on the warm vents and has gone strange with it. A polite landing distance, out here, is a diagnosis.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ashline jackal (`ashline_jackal`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A jackal the grey of the ash it walks steps out of your own heat- shimmer, close enough to have counted your steps for a while, and stops pretending to be shimmer.
- **Lore:** It works the line between the wells and the waste, living off what turns back too late.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Cinderhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Cinderhide waits at the stair buried to the shoulders in warm ash, patient as a stone in a hearth. When it rises, the grey slides off a hide of banked coals, and the day gets hotter.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 42 — The Glass Flats (biome: The Scorch, tier 5, gate town: Shardside)

**Landscape:** Something burned hot enough here to turn a mile of desert to glass. The flats are black and smooth and sing underfoot, crazed with cracks that catch the light wrong. The locals cross at dawn, when the glass is quiet. It is not dawn.

### Glass salamander (`glass_salamander`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A salamander suns itself under the surface of the flats, visible through a yard of black glass like a fish under ice. The cracks around it are fresh. It has seen you.
- **Lore:** It suns itself under a yard of black glass like a fish under ice. The fresh cracks are how it says it has seen you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Shard-picker ogre (`shard_ogre`)
- **Size:** small and slight — traits: frail, fierce, armoured
- **Description:** An ogre works the flats with a hammer, prying up sheets of glass to sell at the gate towns. Its hands are past scarring. It sets the hammer down, which is not an improvement.
- **Lore:** Its hands are past scarring and its hide has gone the way of its hands. Setting the hammer down is not an improvement.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Heat-ghost (`mirage_wisp`)
- **Size:** at-floor peer (medium) — traits: fierce, fly
- **Description:** Out on the flats the heat makes shapes, and one of the shapes has stopped obeying the wind. It walks toward you across the glass, and it does not shimmer.
- **Lore:** The heat makes shapes, and this one stopped obeying the wind. Spells warp around it like more heat.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Flat-skitter (`flat_skitter`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** Something crosses the flats toward you in a sound like a struck wineglass — a lizard low to the glass, legs a blur, riding its own noise in past your guard.
- **Lore:** A lizard that hunts on the singing glass, faster than the cracks it causes.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Glassjaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Glassjaw came out of the melt the day the flats were made — a beast of smoked glass, seams glowing like a kiln left open. Every step it takes rings the whole floor like a struck bowl.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 43 — The Slag Barrens (biome: The Scorch, tier 5, gate town: Clinker Row)

**Landscape:** The reactor's spoil was dumped here in ridges, and the ridges never quite cooled. Slag country: black hills that tick as they settle, seams of dull red glowing in the cuts, air that tastes of struck matches. Things den in the warm hills. Big things.

### Slag salamander (`slag_salamander`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, magic_resist
- **Description:** A salamander has denned in a red seam and grown fat on the heat, scales gone the color of cooling iron. It comes out annoyed, which for a salamander is most of the way to violence.
- **Lore:** Denned in a red seam, fat on the heat, scales gone the color of cooling iron. Annoyed is most of the way to violence.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ridge ogre (`ridge_ogre`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** An ogre clan works the barrens for half-smelted metal, and this one has struck a good seam. It stands up on the ridgeline, backlit red, and claims the whole hill with one bellow.
- **Lore:** It struck a good seam and claimed the hill with one bellow. The claim, as it understands things, includes you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Clinker hound (`clinker_hound`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A hound-shaped clot of slag and cinder trots the ridge road, cooling as it comes. By the time it reaches you it will be hard as a bell. It knows this. It is not hurrying.
- **Lore:** It cools as it comes, and by arrival it is hard as a bell. It knows this. It is not hurrying.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cinder bat (`cinder_bat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Off the glowing cut-face a bat unfolds, wings edged in ember-light, and banks down the ridge road at head height — yours.
- **Lore:** It dens in the warm hills with everything else big enough to matter, and hunts the ridge roads by heat.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Slagbone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Slagbone hauls itself off the hottest ridge, a skeleton of rebar and half-melt with slag for muscle. It leaves the shape of itself burned into the hill behind it, and comes down at a run.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 44 — The Vent Country (biome: The Scorch, tier 5, gate town: Steamgate)

**Landscape:** The buried reactor breathes through this desert — vents tall as chimneys, exhaling steam and ash on a schedule the locals set their clocks by. Between eruptions the country is almost peaceful. Check the schedule.

### Vent salamander (`vent_salamander`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Salamanders ride the vent-blasts for sport, and one lands ahead of you, steaming, in the loose easy way of an animal that has never once been cold.
- **Lore:** It rides the vent-blasts for sport and lands loose and easy, the way of an animal that has never once been cold.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Scalded ogre (`steam_ogre`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** An ogre stands where a vent caught it, bright pink down one side and in a mood about it. It has decided somebody is to blame, and you have the misfortune of being available.
- **Lore:** A vent caught it, bright pink down one side and in a mood. Somebody is to blame, and you are available.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ash wyrmling (`ash_wyrmling`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** A wyrmling noses out of a dormant vent, no longer than a skiff, wings still wet. It is a long way from the Cindermouth nest, and it is exactly as dangerous as a lost child with a furnace in it.
- **Lore:** A long way from the Cindermouth nest, wings still wet — exactly as dangerous as a lost child with a furnace in it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Vent crab (`vent_crab`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** A crab wide as a cart squats over a breathing vent, shell fumed black, and sidles into your path with the unbothered weight of a thing the desert boils daily.
- **Lore:** It grew its shell against the eruption schedule. Nothing on that schedule was ever in a hurry.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Ventmaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The largest vent on the floor is not a vent. Ventmaw rises out of its own crater, throat glowing down past sight, and the eruption schedule turns out to have been a feeding schedule all along.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 45 — The Ogre Steps (biome: The Scorch, tier 5, gate town: Kilnrest)

**Landscape:** The ogres terraced this slope generations ago, hauling slag blocks into steps a giant could climb, and they farm heat here — kilns on every terrace, each clan's fire banked and never let die. Strangers on the Steps are fuel until proven otherwise.

### Terrace ogre (`step_warden_ogre`)
- **Size:** at-floor peer (medium) — traits: bulwark, savage
- **Description:** The ogre who keeps this terrace comes to the edge of its kiln light, a rake of welded rebar over one shoulder. It points at you, then at the fire, and lets you do the arithmetic.
- **Lore:** The terrace is its charge and the kiln is its clock. It does not tire, it does not move fast, and it does not need to — the fire does the waiting.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kiln salamander (`kiln_salamander`)
- **Size:** at-floor peer (medium) — traits: feeble
- **Description:** The ogres keep salamanders the way farmers keep barn cats, and this one is somebody's prize mouser — collared in copper, sleek with heat, and off its rope.
- **Lore:** Somebody's prize mouser, collared in copper, sleek with heat, and off its rope. Spells break on it like spray on a kiln door.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kiln vulture (`firebreak_vulture`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** A cinder vulture squats on a cold kiln, working out why the fire died and whether the answer is edible. It turns its scorched head all the way around to keep you in view.
- **Lore:** It is working out why the fire died and whether the answer is edible. Its head keeps you in view all the way around.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kiln goat (`kiln_goat`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A goat with singed horns and a chewed copper collar takes the terrace steps in two jumps and lowers its head — the clans breed them mean, and this one is off the tether.
- **Lore:** The clans keep goats on the terraces for milk and temper. Mostly temper.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Kilnfist (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the top step burns the mother-kiln, and Kilnfist tends it — an ogre-shaped thing of firebrick and mortar, hands worn round from centuries of stoking. It picks up a glowing brand like a fork at dinner.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 46 — The Ember Dunes (biome: The Scorch, tier 5, gate town: Duneshade)

**Landscape:** Wind-built dunes of ash and cinder, still holding last year's heat a hand's depth down. At night the dune faces glow in long slow bands, and the whole desert breathes orange. It is beautiful. Almost everything beautiful out here is a mouth.

### Dune-swimmer salamander (`dune_swimmer`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The wake comes first — a ridge of disturbed ash running at you through the dune, quick as a skipped stone. The salamander breaches at the last moment, jaws open, gloriously happy.
- **Lore:** The wake comes first, quick as a skipped stone. The breach comes last, jaws open, gloriously happy.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ember-blind ogre (`ember_ogre`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** An ogre wanders the dunes at night with its eyes wrapped, blind from staring into too many years of ember-glow. It navigates by smell now, and stops, and turns toward yours.
- **Lore:** Blind from staring into too many years of ember-glow. It navigates by smell now, and it has found yours.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ember moths (`glow_moth_swarm`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** A drift of moths rises off a glowing dune face, each one carrying a live cinder in its belly. They are drawn to anything warmer than the desert. You are much warmer than the desert.
- **Lore:** Each one carries a live cinder in its belly, drawn to anything warmer than the desert. You qualify.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Dune adder (`dune_adder`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** Between two slow bands of dune-glow a length of shadow uncoils — an adder the color of cold cinder, head up, reading the heat of you against the orange.
- **Lore:** It hunts the glowing dune faces at night, striking at whatever blocks the light.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Emberback (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The largest dune on the floor stands up, and the ember-bands you were admiring turn out to be ribs. Emberback shakes off a hundred tons of ash, spreads a mane of live coals, and inhales.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 47 — The Reactor Scar (biome: The Scorch, tier 5, gate town: Scarwatch)

**Landscape:** Here the reactor comes up for air: a canyon torn open in the taking, walls of fused ash, and at the bottom the machine itself — cracked, half-alive, shedding a light with no color you can name. The locals will sell you lead-lined cloaks. Buy one.

### Scar-born salamander (`scar_salamander`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The salamanders that nest in the canyon come out changed — translucent, bright inside, wrong in the joints. This one moves like its shadow is a half-second behind it.
- **Lore:** The canyon nests come out changed — translucent, bright inside, wrong in the joints. Its shadow runs a half-second behind.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Canyon hermit (`canyon_ogre`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** An ogre lives alone in the scar wall, cloaked head to foot in hammered lead sheeting. It has stayed alive down here by tolerating no visitors, and its record is unbroken.
- **Lore:** Cloaked head to foot in hammered lead sheeting. It has stayed alive by tolerating no visitors, and its record is unbroken.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Colorless flame (`pale_fire`)
- **Size:** at-floor peer (medium) — traits: savage, fly
- **Description:** A flame the color of nothing walks up the canyon path, burning without fuel, casting shadows in the wrong directions. The heat of it arrives before it does, and after it should have gone.
- **Lore:** A flame with no color and no fuel, casting shadows in the wrong directions. Spells go into it and do not come out.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Scar rat (`scar_rat`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A rat comes up the lead-lined path with patchy fur and too many teeth, dragging a hind leg that has healed twice its size, entirely unafraid of the light.
- **Lore:** Everything in the canyon is a little wrong, and the rats are wrong in the direction of bigger.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Palescorch (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Palescorch climbs out of the reactor breach itself, a beast lit from inside like a lamp of skin and bone, too bright to look at in the middle. The stair is behind it, and your cloak is not that good.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 48 — The Char Forest (biome: The Scorch, tier 5, gate town: Stumpwell)

**Landscape:** A forest stood here when the realm was taken, and it burned standing. The trunks remain — miles of black pillars, branchless, holding up nothing. When the wind moves through, they sound a low note like a pipe organ with one key held down.

### Charcoal salamander (`char_salamander`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A salamander has gone black to match the forest, invisible until it opens its mouth. It hunts by holding still against the trunks and being, briefly, the wrong tree.
- **Lore:** It hunts by holding still against the trunks and being, briefly, the wrong tree.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rooter ogre (`rooter_ogre`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** An ogre works the forest floor, ripping stumps for the charcoal trade. It uses no rope and no wedge, only opinion. It transfers the opinion to you.
- **Lore:** It rips stumps with no rope and no wedge, only opinion. The opinion transfers.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hollow trunk (`standing_dead`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, armoured
- **Description:** One of the burned trunks is not a trunk. It has stood in the row long enough to fool the birds, waiting with the patience of wood, and it steps out of line behind you.
- **Lore:** It has stood in the row long enough to fool the birds. Burned wood does not hurry, and does not bruise.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Soot owl (`soot_owl`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** The low pipe-note of the wind cuts off — an owl the color of burned paper is already over you, wings spread wider than the trunks it slipped between.
- **Lore:** It nests in the hollow trunks and hunts the organ-note wind. Silent, except for the forest holding its breath.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Charspine (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Charspine drags itself up from the root-cellar dark, a stag-shape of burned timber with heartwood coals for eyes. Where its antlers rake the dead trunks, the forest catches its breath and burns again, briefly, in memory.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 49 — The Wyrmroad (biome: The Scorch, tier 5, gate town: Moltgate)

**Landscape:** The last stretch before the Cindermouth is a highway melted by use — a channel of glassed ash, polished by the belly of something that commutes. Shed scales the size of doors lean against the banks, still warm. The locals harvest them on the quiet days.

### Road wyrmling (`road_wyrmling`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A wyrmling practices its glide down the melted channel, wings hissing on the glass. It bowls into you more than it attacks you, but it weighs what a boat weighs, and it is teething.
- **Lore:** It practices its glide down the melted channel. It bowls into you more than it attacks you, but it weighs what a boat weighs, and it is teething.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Scale-picker ogre (`scale_picker`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** An ogre pries a shed scale off the bank with a whole tree for a lever. The scale trade has made it rich by ogre standards, and rich things hire fewer witnesses.
- **Lore:** The scale trade made it rich by ogre standards, and it wears its stock — shed wyrm-plate lapped like roof tiles. Rich things hire fewer witnesses.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Molt-fat salamander (`molt_salamander`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, magic_resist
- **Description:** The salamanders follow the Wyrmroad eating shed skin, and this one is glutted, gleaming, slow — right up until it is none of those things.
- **Lore:** Glutted on shed skin: gleaming, slow — right up until it is none of those things.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Glass hare (`glass_hare`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** Something small takes the melted channel at a speed that should not corner — a hare with glass-worn claws, banking off the banks, using you as the next turn.
- **Lore:** It runs the polished channel for the speed of it, and it has learned to use climbers as corner-posts.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Moltcrown (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Moltcrown was made from the wyrm's castoffs — a rearing shape armored in shed scales, crested with old fang. It holds the last gate before the nest, and it fights like something auditioning for its maker.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 50 — The Cindermouth (biome: The Scorch, tier 5, gate town: Lastwater)

**Landscape:** The center of the Scorch is a caldera of fused ash, and the caldera is a nest. Half-melted tribute rings the rim — armor, wagons, a gate town that stood too close. The heat rises in slow beats, like a pulse. Halfway up the tower, and the tower keeps a dragon.

### Nest wyrmling (`nest_wyrmling`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** A wyrmling the size of a river barge suns itself on the caldera rim. It is the runt. It has a runt's temper about visitors, and a keel of muscle that says the word runt is doing heavy work.
- **Lore:** The runt of the nest, barge-sized, with a runt's temper about visitors. The word runt is doing heavy work.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Tribute ogre (`rim_ogre`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** An ogre clan hauls a wagon of scrap-steel up the rim road, tribute to keep the wyrm off their terraces. The wagon sheds a wheel. The clan decides you are lighter than the wagon.
- **Lore:** The clan hauls tribute to keep the wyrm off their terraces. The wagon shed a wheel; you are lighter than the wagon.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Caldera salamander (`caldera_salamander`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** In the nest's shadow the salamanders grow to the size of oxen and fear nothing that walks. This one does not stalk you. It simply turns, and the turning is the whole announcement.
- **Lore:** In the nest's shadow they grow to the size of oxen and fear nothing that walks. The turning is the whole announcement.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rim jackal (`rim_jackal`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A jackal picks along the caldera rim between half-melted offerings, lean and businesslike, and cuts your line of march with the confidence of a toll-keeper.
- **Lore:** It works the tribute-road for what falls off the wagons, and climbers count as falling off.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cindermaw the Wyrm (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The caldera floor unwinds. Cindermaw rises in coils that redraw the horizon, wings shaking ash-fall over the whole floor, throat lit like the reactor the tower buried. She looks down at you the way a bonfire looks at a moth.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 51 — The Moraine Gates (biome: Frosthold, tier 6, gate town: Coldquay)

**Landscape:** The heat of the Scorch dies in a single doorway. Frosthold opens onto a valley of blue ice under a sunless glare, boulder-fields raked into walls by a glacier with somewhere to be. The cold is not weather. It is policy — the Jarl's, and it is enforced.

### Rime wolf (`rime_wolf`)
- **Size:** small and slight — traits: frail, fierce
- **Description:** A wolf comes over the moraine wall furred in frost, breath hanging behind it in a long unbroken banner. It has run down warmer things than you and eaten them mid-stride.
- **Lore:** It has run down warmer things than you and eaten them mid-stride. The frost coat is from never slowing.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Moraine troll (`gate_troll`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, armoured
- **Description:** An ice troll sits in the boulder-field being one of the boulders, a toll practice older than the tower. It stands up with the patience of a thing that has never lost this game.
- **Lore:** Being a boulder is a toll practice older than the tower, and it has never lost this game.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Frozen scout (`frozen_scout`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, magic_resist
- **Description:** A climber stands off the path, mid-stride, ice to the bone — one of last winter's. As you pass, the frost on it cracks along the shoulders, and it finishes the stride.
- **Lore:** One of last winter's climbers, ice to the bone. The cold in it drinks spellwork like it drank the man.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Glare hawk (`glare_hawk`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** Off the moraine wall a hawk drops out of the white glare with its shadow folded under it, talons first, committed from a height you never checked.
- **Lore:** It hunts down-sun of the sunless glare, and it has learned that climbers look up too late.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Coldjaw (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Coldjaw holds the valley's neck, a wolf-shape of blue ice around something older that drowned in the glacier and kept its temper. Its breath reaches you a full minute before it does.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 52 — The Frozen Sea (biome: Frosthold, tier 6, gate town: Floeside)

**Landscape:** The tower's coolant was pumped through this realm once, a sea of it, and when the pumps died the sea froze mid-swell. Waves stand overhead in green-white glass. The locals cut roads through the crests and post the ice depth at every bend, in fresh paint.

### Floe wolf pack-leader (`floe_wolf`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The wolves out on the sea hunt by ear, listening for footsteps through the ice. Somewhere under you, one has matched your pace. The pack is above, politely driving you along.
- **Lore:** It hunts by ear, through the ice, from below. The pack above is only there to steer you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Swell troll (`swell_troll`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** An ice troll has hollowed a standing wave into a den and hangs in the green glass like a fly in amber, watching the road. The wave's face is cracked. Recently.
- **Lore:** It hangs in the green glass of its wave like a fly in amber, wearing the sea itself for plate.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Coolant wight (`coolant_wight`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** Something that drowned in the sea before it froze walks under the ice, upside down, matching your route. At the next thin patch it stops. So should you not.
- **Lore:** It drowned before the sea froze and walks under the ice, upside down. Spells refract somewhere on the way through.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Brine gull (`brine_gull`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** A gull the size of a dog lifts off a standing wave crest, wings stiff with rime, and comes down the road cut at mast height, screaming its claim.
- **Lore:** It works the frozen swells for whatever the wolves leave, and it has stopped waiting for the wolves.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Floeback (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The road ends at a breach where the sea never froze, and Floeback owns the open water — a whale-bulk of pack ice and pale meat that surfaces without a ripple. The stair is on the far shore. It knows.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 53 — The Rime Forest (biome: Frosthold, tier 6, gate town: Firwatch)

**Landscape:** A pine forest sealed in clear ice, every needle cased in glass. When the wind comes down off the glacier the whole forest rings, a million small bells with no church. The Jarl's folk log it with hammers. What lives in it prefers the quiet, and enforces it.

### Glass-antlered stag (`rime_stag`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, armoured
- **Description:** A stag steps through the ringing trees with antlers of solid ice, grown that way, points refreshed nightly by the cold. It has stopped running from things. The antlers are why.
- **Lore:** Its antlers are solid ice, grown that way, points refreshed nightly. It has stopped running from things — the antlers are why.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hammer-logger troll (`forest_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** An ice troll works a stand of frozen pines with a maul, filling a sledge with shattered timber. Your footsteps ring the forest like an alarm, and the maul comes up.
- **Lore:** It logs the frozen pines with a maul and gang-rules it ate. Your footsteps ring the forest like an alarm.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Bell-wise wolf (`bell_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** The wolves here have learned to walk without ringing the trees, and it has made them soft-footed beyond nature. The first you hear of this one is its weight arriving.
- **Lore:** It learned to walk without ringing the trees, and it made the wolf soft-footed beyond nature. The first you hear is its weight arriving.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Chime sprite (`chime_sprite`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** The bells of the iced needles gather into one clear tone, and the tone comes down the row of pines toward you — a small bright blur that the trees ring for as it passes.
- **Lore:** When the forest rings, something in the ringing answers. It prefers the quiet, and enforces it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Rimehide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Rimehide is the forest's oldest bear, sealed alive in the great freeze and improved by it — a hide of ringing icicles over meat that no longer feels the maul. It rises on two legs, and the forest goes silent out of respect.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 54 — The Troll Bridges (biome: Frosthold, tier 6, gate town: Bridgeward)

**Landscape:** A gorge country of blue crevasses, crossed by bridges of living ice that the trolls grow, own, and lease. Every span has its bridge-troll and every bridge-troll has its price. The rates are fair. The exceptions are memorable.

### Bridge-troll (`bridge_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce, armoured
- **Description:** The troll under the third span has doubled its rates for the season and glued the detour shut with new ice. It comes up over the rail with the deed in one fist, in case you argue.
- **Lore:** It doubled its rates for the season and glued the detour shut. The deed is in one fist, in case you argue.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Toll-runner wolf (`toll_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** The wolves cross without paying, which the trolls tolerate because catching them is undignified. This one has learned to shake bridges until paying customers fall off.
- **Lore:** It crosses without paying and shakes the spans until paying customers fall off. The trolls call it undignified. It calls it lunch.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Crevasse climber (`crevasse_wight`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, magic_resist
- **Description:** Not everyone who fell short on the toll hit the bottom. Something climbs out of the blue depth on fingers of ice, carrying its grudge in both hands.
- **Lore:** Not everyone who fell short on the toll hit the bottom. It climbs with its grudge in both hands.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gorge raven (`gorge_raven`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A raven drops off the underside of the bridge and hangs on the gorge wind at your eye level, head tilted, deciding whether you are traffic or windfall.
- **Lore:** It nests under the spans and audits every crossing. Whatever falls, it files.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Spanbreak (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The last gorge has no bridge, because Spanbreak ate it. A troll grown to the width of the crossing itself, it lies across the gap and lets you choose which end to argue with.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 55 — The Giant Steadings (biome: Frosthold, tier 6, gate town: Thanesrest)

**Landscape:** Farms, if farms were built by things four men tall — fences of whole pines, cattle the size of barns. The frost giants hold these steadings as the Jarl's freeholders, and they do not care for trespass across land it takes a day to walk.

### Freeholder giant (`steading_giant`)
- **Size:** at-floor peer (medium) — traits: bulwark, feeble
- **Description:** A frost giant straightens up from mending a fence of whole trees, hammer dangling. You are on the near field. The near field is posted. The post is the hammer.
- **Lore:** The near field is posted and the post is the hammer. Freeholders this size do not lose arguments on their own land — they last them out.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Steading hound (`giant_hound`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The giants breed their hounds to giant scale, and this one clears the pine fence without touching it. It is not angry. It is doing its job, at the size it was bred to do it.
- **Lore:** Bred to giant scale, it clears the pine fence without touching it. It is not angry. It is on the clock.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rick-thief troll (`hayrick_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** An ice troll is stealing hay by the armload, pursued by nobody yet. Your arrival gives it a better idea than hay, and it drops the armload where it stands.
- **Lore:** It was stealing hay until you arrived and became the better idea.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Steading bull (`steading_bull`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A bull the size of a barn door tears free of the near-field herd with a fence rail still roped to one horn, and commits to the argument at a canter.
- **Lore:** Cattle bred for owners four men tall. It does not recognize fences, seasons, or you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Fencewright (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The Jarl's reeve for the steadings is Fencewright, a giant of fence-posts and frozen wire who walks the property lines by night. You are the property line's problem now, and it unhooks its mallet without hurry.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 56 — The Ice Quarries (biome: Frosthold, tier 6, gate town: Hewnstone)

**Landscape:** The Jarl builds in ice the way kings below built in granite, and the blocks come from here — quarries cut in terraces into the glacier's blue heart. The deeper terraces are older than the Jarl, and their blocks were not left unfinished by accident.

### Quarry-gang troll (`quarry_troll`)
- **Size:** small and slight — traits: frail, feeble, armoured
- **Description:** An ice troll works a two-troll saw alone, which is against the gang rules, which it ate. It leaves the saw singing in the cut and picks up the breaking-bar instead.
- **Lore:** It works a two-troll saw alone, which is against the gang rules, which it ate.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Quarried thing (`block_wight`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** One of the deep blocks has a shape inside it, and the shape has been sawing from its side. Your lamp is the first light it has had to work by in an age, and it is grateful, and nearly out.
- **Lore:** The deep blocks were not left unfinished by accident. It has been sawing from its side, and it is nearly out.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gantry wolf (`gantry_wolf`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A wolf patrols the top gantry like a foreman, looking down the terraces at you. It starts down the ramps at a trot, unhurried, collecting the pack as it comes.
- **Lore:** It patrols the top gantry like a foreman and comes down the ramps collecting the pack as it comes.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Quarry crow (`quarry_crow`)
- **Size:** small and slight — traits: frail, fierce, fly
- **Description:** A crow lifts off the idle gantry crane and rides the cold down the terraces toward you, wings set, calling the count of you to the whole cut.
- **Lore:** Every work site feeds its crows. This quarry's crows have opinions about who counts as site waste.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Hewnheart (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The quarry's last terrace is a single block the old cutters refused to finish, and Hewnheart is why. It shears itself free along their abandoned cut-lines, a giant of building-grade ice, edges still true.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 57 — The Coolant Falls (biome: Frosthold, tier 6, gate town: Milkwater)

**Landscape:** A cataract of coolant, milk-white and dead cold, falling from a cracked main above the clouds and freezing as it lands — a waterfall growing its own mountain. The spray coats everything in white glass, and the locals chip their doors open every morning.

### Glass-coat wolf (`spray_wolf`)
- **Size:** at-floor peer (medium) — traits: fierce
- **Description:** A wolf that hunts the spray-line wears a coat of frozen coolant like white armor. It shatters its own casing to charge, and arrives in a burst of glass.
- **Lore:** Its coat of frozen coolant is white armor. It shatters its own casing to charge, and arrives in a burst of glass.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Falls troll (`falls_troll`)
- **Size:** at-floor peer (medium) — traits: bulwark, feeble
- **Description:** An ice troll stands under the cataract for pleasure, growing a second hide. It steps out of the white curtain at you, steaming cold, twice the size the silhouette promised.
- **Lore:** It stands under the cataract for pleasure, growing a second hide. The silhouette under-promises.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### White pilgrim (`frozen_pilgrim`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, magic_resist
- **Description:** People come to see the Falls, and some stand too long in the spray. One of the white statues along the viewing path turns its head as you pass, patient under a finger of glass.
- **Lore:** People come to see the Falls, and some stand too long in the spray. This one is still patient under a finger of glass.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ice marten (`ice_marten`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A marten flows out from behind the white curtain, coat beaded with frozen spray, and cuts across the path with its eyes already on the food in your pack.
- **Lore:** It dens in the dry pocket behind the cataract and robs the viewing path at its leisure.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Whitefall (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Whitefall lives inside the cataract, a long serpent-shape visible only when the falling white bends around it. It comes out with the current still on its back, and the cold arrives like a verdict.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 58 — The Wind Walls (biome: Frosthold, tier 6, gate town: Shuttergate)

**Landscape:** The glacier funnels the floor's whole weather through one pass, and the wind through it has been sharpened for centuries. The Wind Walls break it — ramparts of ice block, slotted and singing. Crossings are done at a sprint, by bell signal, or not at all.

### Wall-warden giant (`wall_giant`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A frost giant leans into the gale at the third wall, holding a shield the size of a barn door for travelers to shelter behind — for a fee. You are past due before you reach it.
- **Lore:** It leans into the gale holding a shield the size of a barn door — shelter for travelers, for a fee. You are past due.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gale-running wolf (`wind_wolf`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** The wolves here have learned to run with the gale at their backs, arriving at twice a wolf's honest speed. The bell rings once. That is all the warning the system has.
- **Lore:** It runs with the gale at its back and arrives at twice a wolf's honest speed. The bell rings once.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Shutter troll (`shutter_troll`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** An ice troll operates the storm shutters at the crossing, paid in fish heads and deference. Today it has decided the shutters stay down, and it puts its back against them to make the point.
- **Lore:** Paid in fish heads and deference. Today the shutters stay down, and its back is against them.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gale kite (`gale_kite`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** Something rides the pass wind without a single wingbeat — a kite- shape holding station over the crossing slot, waiting for the sprint the bell is about to ask of you.
- **Lore:** It is the only thing that flies the pass by choice, and it uses the wind the way an angler uses a river.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Galebone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Past the last wall the wind has had time to become someone. Galebone is the pass's oldest gale wearing a skeleton of hoarded ice, and it holds the stair door shut the way it holds everything shut — from every direction at once.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 59 — The Jarl's Road (biome: Frosthold, tier 6, gate town: Horncall)

**Landscape:** A processional road of fitted ice blocks, wide enough for six giants abreast, lit by whale-oil lamps that never gutter. The Jarl's own approach, swept daily, patrolled hourly. You are expected. That is not a comfort.

### Thane of the road (`road_thane`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A frost giant in the Jarl's colors bars the road with a halberd of ice and iron. Custom entitles you to give your name and have it spoken at your defeat. The custom is observed.
- **Lore:** Custom entitles you to give your name and have it spoken at your defeat. The custom is observed; so is the plate.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Jarl's herald-wolf (`herald_wolf`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A white wolf in a silver road-collar has been sent down to look at you. Whatever it reports back will decide how much of the garrison you meet. It circles once, taking notes.
- **Lore:** Whatever it reports back decides how much of the garrison you meet. It circles once, taking notes.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Lamplighter troll (`lamp_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** The troll that tends the road-lamps has held the post for nine generations of trolls, all of them it. It sets down the oil pail with ceremony. Brawling on the road is its second duty.
- **Lore:** Nine generations of trolls have held the lamp post, all of them it. Brawling on the road is its second duty.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Post raven (`post_raven`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A raven in a small silver road-band drops from lamp to lamp ahead of you, keeping exact pace, and finally lands in your path with the unhurried authority of the postal service.
- **Lore:** The Jarl's road-post flies ahead of every traveler. Interfering with the mail is a listed offense.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Hallmarch (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The Jarl's gatekeeper Hallmarch stands where the road meets the stair, a giant in parade armor of blue ice, unmoved for years at a stretch. It steps down off its plinth, and the road reports the weight of every step.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 60 — The Frosthall (biome: Frosthold, tier 6, gate town: Hearthold)

**Landscape:** The Jarl's citadel is a glacier carved into a mead-hall, rafters of blue ice, a fire-trench down the middle burning cold white. The tables are set for a thousand, and the thousand are here. The horn by the door is for challengers. It is not decorative.

### Hall-thane (`hall_thane`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A thane of the Jarl's table stands from the bench, formally, and asks the room's leave to answer the horn. The room grants it with a sound like an avalanche starting.
- **Lore:** It asked the room's leave to answer the horn, formally, and the room granted it like an avalanche starting.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mead-bearer troll (`mead_troll`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** The troll that carries the hall's mead barrels has been given leave to warm up before the main event. It sets down the barrel it was carrying. The barrel was for you. It is not, now.
- **Lore:** The barrel it set down was for you. It is not, now.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hearth-wolf (`hearth_wolf`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** The Jarl's own wolf uncurls from beside the cold fire, white as the hall and nearly as large. It has first claim on challengers by right of seniority, and no thane disputes it.
- **Lore:** The Jarl's own, with first claim on challengers by right of seniority. No thane disputes it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ice skald (`ice_skald`)
- **Size:** at-floor peer (medium) — traits: savage, magic_resist
- **Description:** A skald rises from the bench nearest the cold fire, beard hung with hoarfrost bells, and begins the verse that turns the fire-trench white — your name is already in the second line.
- **Lore:** It sings the hall's cold fire brighter, and verses this old shrug off newer magic.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Jarl Hrimgar (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Hrimgar comes down the hall with a step that rings the rafters, crowned in hoarfrost, bearing an axe of core-ice older than his line. He salutes you with it, once, correctly. The hall wants a good fight. The Jarl intends to provide one.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 61 — The Cloudline (biome: Stormreach, tier 7, gate town: Skyfoot)

**Landscape:** The stair opens onto open sky. Peaks rise out of a cloud deck that goes to every horizon, and the wind arrives with no memory of ever being stopped. The locals rope themselves to their own houses, and will lend you a line for a fair price.

### Cloudline harpy (`cloudline_harpy`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A harpy rides the updraft along the cliff face, keeping pace with you at arm's length, insulting your footwork in fluent trade-tongue. The insults are a range-finding exercise.
- **Lore:** The insults in fluent trade-tongue are a range-finding exercise. The stoop comes on the punchline.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Squall drake (`young_drake`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce, fly
- **Description:** A young storm drake breaks out of the cloud deck below you, static crawling on its wing edges. It has not learned to aim its lightning yet. It does not especially need to.
- **Lore:** It has not learned to aim its lightning yet. It does not especially need to.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Fallen rigger (`rigger_ghast`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A sky-ship crewman in a rotted harness climbs over the trail's edge, dragging a length of frayed safety line. It clips the line to your belt with terrible courtesy. Its ship is down there somewhere.
- **Lore:** It clips its frayed line to your belt with terrible courtesy. Its ship is down there somewhere, and it means to introduce you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cliff goat (`cliff_goat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A goat with storm-tattered wool rounds the cliff corner at a trot, sees you on its ledge, and lowers a boss of horn worn smooth by better arguments than yours.
- **Lore:** It holds the trail ledges against all comers, and the drop has never once been its problem.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Thermal (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The updraft at the stair peak is permanent, and Warden Thermal is why — a broad-winged thing that has ridden one column of air for a hundred years, circling. It folds its wings, once, and the whole sky comes down with it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 62 — The Wreckfields (biome: Stormreach, tier 7, gate town: Hullside)

**Landscape:** Sky-ships died here in numbers — a whole trade fleet, caught between the tower's theft and the storm it made. The hulls lie broken across three peaks, keels to the sky. Salvage is the floor's whole economy, and the previous owners have opinions.

### Salvage harpy (`wreck_harpy`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** A harpy clan has stripped this hull to the ribs, and the clan matriarch lands on the keel above you wearing three captains' coats at once. Everything on this peak is claimed, including, as of now, your gear.
- **Lore:** The clan matriarch wears three captains' coats at once. Everything on this peak is claimed, including, as of now, your gear.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hold-nesting drake (`hold_drake`)
- **Size:** at-floor peer (medium) — traits: feeble
- **Description:** A storm drake has nested in a cargo hold, brooding a clutch on a bed of trade silver. The hull groans under it as it comes out — possessive, charged, and recently a parent.
- **Lore:** Brooding a clutch on a bed of trade silver — possessive, charged, and recently a parent.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Crew of the wreck (`dead_crew`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** Below decks, the crew never left their stations. They rise from the ribs of the hull in harness and oilskin, moving with the roll of a deck that stopped rolling years ago.
- **Lore:** They rise in harness and oilskin, moving with the roll of a deck that stopped rolling years ago.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hull borer (`hull_borer`)
- **Size:** at-floor peer (medium) — traits: bulwark, savage
- **Description:** The keel above you flexes and a borer backs out of the timber — a grub gone the size of a longboat, plated in the iron it could not digest, blind and unbothered and between you and the path.
- **Lore:** It ate through the fleet's timber for years and grew a back of lapped ship-iron doing it. Cutting it down is a shipwright's job, not a soldier's.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Keelhaul (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The biggest wreck's anchor still hangs from its chain down the cliff, and Keelhaul climbs it to meet you — a drowned-air giant of hull timber and chain, the fleet's grievance walking. It swings the anchor like a censer.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 63 — The Rookeries (biome: Stormreach, tier 7, gate town: Rookwall)

**Landscape:** Every ledge of these crags is built up with harpy nests — driftwood, rigging, one entire church roof — stacked into a city without streets. The harpies are not hostile so much as governed by an etiquette you cannot see, and the fines are paid in blood.

### Rookery matron (`rookery_warden_harpy`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A matron harpy drops onto the path with the weight of office — wing-feathers banded in salvaged brass. You have walked under somebody's nest, which is either a toll or a proposal, and she is here to settle which.
- **Lore:** You walked under somebody's nest, which is either a toll or a proposal. She is here to settle which.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Fledgling mob (`fledgling_mob`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A crowd of half-grown harpies has been dared to touch you. Individually they would not. There are eleven of them, and the arithmetic of being twelve is the whole of harpy education.
- **Lore:** Eleven of them, dared to touch you. The arithmetic of being twelve is the whole of harpy education.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rookery drake (`nest_drake`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** The harpies keep a storm drake the way a town keeps a bull — penned, resented, and prayed to. The pen is rigging. The rigging is old. It steps through it like mist.
- **Lore:** Penned like a town bull, resented, and prayed to. The prayers soaked in; spells break against them.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rook marten (`rook_marten`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A marten pours down a nest-pole with somebody's brass band still in its teeth, hits the path in front of you, and decides you are between it and the exit.
- **Lore:** It raids the nests for eggs and trinkets, and it has learned to work while the owners are out on you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Shrikewind (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The rookery's law is Shrikewind, an ancient harpy gone white at the pinions, who impales the convicted on the summit spar for the wind to read. She lands between you and the stair holding the writ. Your name is on it, phonetically.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 64 — The Anchor Chains (biome: Stormreach, tier 7, gate town: Chainrest)

**Landscape:** The chains that hold this realm into the tower run overhead — links the size of houses, climbing into cloud, humming with load. Whole communities live on the links, farming moss, netting birds. Twice a day the chains move a few feet. Everyone holds on.

### Chain-walker harpy (`chain_harpy`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A harpy patrols the great link you are crossing, wings folded, walking like a landlord. Flying here is for amateurs, she explains, kicking your handhold loose to illustrate the point.
- **Lore:** Flying here is for amateurs, she explains, kicking your handhold loose to illustrate the point.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Link-coiled drake (`link_drake`)
- **Size:** small and slight — traits: frail, fierce, fly
- **Description:** A storm drake has coiled through three links overhead to sleep, and your footsteps carry up the chain like a knock. It pours down through the links with the grace of something that has never needed a floor.
- **Lore:** Your footsteps carry up the chain like a knock. It pours down through the links, and it has never needed a floor.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Moss-farmer's remnant (`moss_ghast`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A chain-farmer who missed a handhold years ago still works a link ledge, grey and weightless-thin, harvesting moss nobody collects. It gestures you over to help with the netting. The net is for you.
- **Lore:** It missed a handhold years ago and still works its ledge, weightless-thin. The net it waves you toward is for you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Chain tick (`chain_tick`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** What you took for a rivet head the size of a shield unclamps from the link, legs unfolding from under an iron-grey shell, and crabs down the chain's curve toward the warm thing crossing its metal.
- **Lore:** It clamps to the great links and drinks the hum of the load. Its shell is chain-grade by adoption.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Shacklewise (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Where the master chain meets the peak, Shacklewise keeps the coupling — a thing assembled from failed links and climbers' carabiners, jointed everywhere. It takes hold of the stair door, the cliff, and you, all with different hands.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 65 — The Updrafts (biome: Stormreach, tier 7, gate town: Kitegate)

**Landscape:** Between two ranges the whole floor's air goes up. The locals ride barn-sized kites between the towns, and the wildlife has organized around the free lift. Nothing here fights on the ground if it can help it. You are the only thing that cannot help it.

### Updraft duelist (`updraft_harpy`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A harpy rises past you going straight up, flips at the top of the column, and stoops. This is the local dueling form — three passes, honor satisfied. Nobody has explained what satisfies it.
- **Lore:** Three passes, honor satisfied — the local dueling form. Nobody has explained what satisfies it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kite-line cutter (`kite_pirate`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Something with shears for a beak works the kite-lines above the pass, dropping travelers into the valley for the things below. It has noticed that you are not even attached to a line. Free lunch.
- **Lore:** It drops travelers into the valley for the things below. You are not even attached to a line. Free lunch.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Column drake (`column_drake`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** A storm drake hangs in the updraft's core, wings barely moving, asleep on the wind. Your scent goes up the column ahead of you. Its eyes open at your altitude exactly.
- **Lore:** Asleep on the wind in the updraft's core. Your scent goes up the column ahead of you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pass boar (`pass_boar`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** Under the kite-lines a boar roots the pass gravel, deaf to the whole sky economy, and takes your landing on its floor as the day's first trespass.
- **Lore:** The only local that never took the free lift. It holds the valley floor out of pure principle.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Galecrest (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Galecrest owns the top of the lift — a vast kite-shaped raptor that has not landed in living memory, ribs of ship-spar grown into wing. It stalls the whole updraft with one beat, and the floor's traffic falls out of the sky to watch.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 66 — The Mast Forest (biome: Stormreach, tier 7, gate town: Sparside)

**Landscape:** A summit plateau where the fleet's masts were driven in like fence-posts — hundreds of them, full-rigged, sails long gone to harpy nests, shrouds still singing. Walking here means walking under a century of standing rigging. Look up more than you look down.

### Shroud-runner harpy (`shroud_harpy`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A harpy runs the rigging between masts without touching wing to air, herding you gently off the path. Somewhere ahead is the net stretch, and her whole clan is waiting at it.
- **Lore:** She runs the rigging without touching wing to air, herding you toward the net stretch where the clan waits.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Crowsnest drake (`mast_drake`)
- **Size:** small and slight — traits: frail, fierce, fly
- **Description:** A storm drake has taken the tallest crow's nest as a roost and grown into it — spars through the wing membrane, at home. It unwinds down the mast in a spiral, ringing every stay on the way.
- **Lore:** Grown into the tallest crow's nest, spars through the wing membrane. It rings every stay on the way down.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Tangled topman (`rigging_ghast`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A topman hangs in the shrouds where his line caught him, swinging all these years. As you pass beneath, the swinging stops — against the wind — and the line starts paying out.
- **Lore:** A topman hanging where his line caught him. The swinging stops against the wind, and the line starts paying out.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Shroud crab (`shroud_crab`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** A crab the size of a capstan picks its way down a shroud on point- tipped legs, shell barnacled with brass, and drops the last fathom onto the path with a sound like a dropped anchor.
- **Lore:** It climbed up from some hold with the fleet and never left the rigging. The shell has out-lasted three hulls.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Mastwrack (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The forest's heart is a mast thicker than the rest, and Mastwrack is rigged to it — a figurehead grown a body of spar and shroud, sailing a fixed point in a permanent gale. It comes about to face you, canvas thundering where its voice should be.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 67 — The Lightning Fields (biome: Stormreach, tier 7, gate town: Copperpole)

**Landscape:** A high moor where the storm grounds itself, all day, every day. The old folk farmed the lightning with copper poles, and the poles still stand, singing before every strike. The safe lanes are marked in white stone. The stones get moved. Not by the wind.

### Charge-thief harpy (`charge_harpy`)
- **Size:** at-floor peer (medium) — traits: feeble, fly
- **Description:** A harpy lands on a live pole, takes the strike across her banded feathers like applause, and comes down at you glowing at the wingtips. The locals call them spark-drunk. She is several strikes in.
- **Lore:** She takes the strike across her banded feathers like applause. Spark-drunk, several strikes in, and spells just read as more applause.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Fieldborn drake (`field_drake`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A storm drake hatched on this moor and never left — why would it. It walks the pole rows like an heir touring the estate, and every pole it passes fires in salute.
- **Lore:** Hatched on this moor and never left — why would it. Every pole it passes fires in salute.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Lane-stone mover (`stone_mover`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** You find the thing that moves the white stones: a bent figure in a farmer's storm coat, rearranging the safe lane with slow care. It turns, and under the hood is old lightning, coiled and patient. It has been farming climbers.
- **Lore:** The thing that moves the white lane-stones. Under the hood is old lightning, coiled and patient. It has been farming climbers.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Copper rat (`copper_rat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A rat with a coat gone verdigris-green works the base of a singing pole, whiskers smoking faintly, and breaks off its meal to defend the whole grid from you.
- **Lore:** It gnaws the pole-farm's wiring for the taste and has been struck more times than the poles.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Groundstrike (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the field's center the storm has struck one spot so long it has made something. Groundstrike stands up out of the fused moor-glass, a giant of branching burn-scar and live charge, and every pole on the floor bends toward it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 68 — The Drake Aeries (biome: Stormreach, tier 7, gate town: Scalewatch)

**Landscape:** The high crags belong to the storm drakes outright — aeries on every summit, each one a hoard of wreck-metal and old charge. The drakes keep the Queen's law as aristocrats keep any law. Climbers rank somewhere between trespass and sport.

### Aerie heir (`aerie_drake`)
- **Size:** small and slight — traits: frail, feeble, fly
- **Description:** A drake in its first adult molt drops from the home crag to look you over. It is young enough to want a story worth telling and old enough to make one out of you.
- **Lore:** Young enough to want a story worth telling, old enough to make one out of you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Harpy drake-groom (`drake_harrier`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** The harpies that serve the aeries wear drake-scale livery and airs to match. Two of them decide removing you before the master wakes is the kind of initiative that gets noticed.
- **Lore:** Drake-scale livery and airs to match. Removing you before the master wakes is the kind of initiative that gets noticed.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Deposed tyrant (`old_tyrant`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** An old drake beaten off its crag by a younger rival haunts the lower ledges, wings scarred, charge gone grey. It has nothing left but seniority, and it means to spend it on you.
- **Lore:** Beaten off its crag, wings scarred, charge gone grey. It has nothing left but seniority, and it means to spend it on you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hoard lizard (`hoard_lizard`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A lizard long as a skiff slides off a heap of charge-blackened salvage, tongue reading the air, and squares up over the hoard like a creditor at a will-reading.
- **Lore:** It lives in the aeries' wreck-metal hoards and defends them harder than the owners do.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Stoopfall (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The stair crag belongs to Stoopfall, the aeries' duelmaster — a lean drake with a wingspan like weather, who has killed on this ledge for three dynasties. It gives you the first move. It always gives the first move.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 69 — The Eye Wall (biome: Stormreach, tier 7, gate town: Lullside)

**Landscape:** The Queen's storm stands over the last peak like a crown, and this floor is its wall — a ring of black weather you can lean on. Inside, the air is still and bright and wrong. The locals call the calm the Lull, and they whisper, because the wall listens.

### Eye-wall sentinel (`wall_sentinel`)
- **Size:** at-floor peer (medium) — traits: feeble, fly
- **Description:** A shape peels off the inside of the storm wall — a drake of cloud and charge, half weather itself, one of the Queen's own watch. It does not roar. Thunder does that for it, on cue.
- **Lore:** One of the Queen's own watch, half weather itself. It does not roar; thunder does that for it, on cue.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Lull courtier (`lull_harpy`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A harpy in the Queen's white lands ahead of you, formal as an invitation. Her Majesty knows you are here, she says. What remains to be decided is the manner of your arrival — walking, or delivered.
- **Lore:** Her Majesty knows you are here. What remains to be decided is the manner of your arrival — walking, or delivered.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pressure-ghost (`pressure_ghast`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** In the Lull your ears keep popping, and one of the pops is a figure arriving beside you — a climber the storm took, worn down to a pressure change with a grudge. Your lungs notice it before your eyes do.
- **Lore:** A climber the storm took, worn down to a pressure change with a grudge. Your lungs notice it before your eyes do.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rain hound (`rain_hound`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A hound made of moving rain slips the eye-wall and crosses the Lull at a sprint, its paws printing wet on dry stone, gone and arrived in the same breath.
- **Lore:** The Queen kennels the squalls that behave. This one behaves right up until the leash comes off.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Stillmark (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Between you and the stair the calm thickens into Stillmark, the Queen's doorkeeper — a giant of dense, motionless air wearing rain like chainmail. It does not block the path. It simply declines, entirely, to move.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 70 — The Tempest Court (biome: Stormreach, tier 7, gate town: Galesend)

**Landscape:** Inside the eye the Queen keeps court on a floating ring of wrecked flagships, rigging strung with captured lightning. Harpies in livery, drakes on perches, weather bowing in and out. On the throne of masthead and storm-glass, someone is expecting you.

### Queen's champion drake (`court_champion`)
- **Size:** at-floor peer (medium) — traits: fierce, fly
- **Description:** The Queen's champion descends from the high perch without hurry, storm-glass gorget flashing. It fights before the throne, which means it fights beautifully, which does not mean it fights fair.
- **Lore:** It fights before the throne, which means it fights beautifully, which does not mean it fights fair.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Court guard harpy (`livery_harpy`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** Two of the court guard cross pikes of ship-spar in front of you. Protocol, one explains, requires all challengers to arrive bleeding. The court dislikes ambiguity.
- **Lore:** Protocol requires all challengers to arrive bleeding. The court dislikes ambiguity; the pike and the plate remove it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Unbottled gale (`bottled_gale`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A courtier drops a lantern-globe as you pass, accidentally, the way courts do accidents. What gets out has been bottled since the fleet fell, and it holds you personally responsible.
- **Lore:** Bottled since the fleet fell, dropped the way courts do accidents. It holds you personally responsible.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Perch squire (`perch_squire`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A young harpy in half-livery vaults the perch rail with the champion's spare gorget banging on its chest, determined to be noticed doing something about you.
- **Lore:** A groom of the court perches, armed with the champion's second-best gorget and none of its patience.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Zephyra, the Storm Queen (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Zephyra rises from the throne and the whole eye tightens by a mile. Wings of front-line weather, a crown of continuous lightning, and under it a face that has outlasted every storm it ever started. She bids you welcome. The pressure drops like a curtsy.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 71 — The Eaves (biome: The Gloom, tier 8, gate town: Lastlamp)

**Landscape:** Above the storm the tower goes quiet. A forest floor with no sky — black boughs closing overhead, and under them a dusk that never ripens into night. The gate town keeps one lamp lit facing the trees, and the trees keep their distance. Mostly.

### Eaves shade (`eaves_shade`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** Your shadow arrives before you do — thrown ahead on the path by no light at all. It waits for you to catch up, and when you stop, it keeps walking.
- **Lore:** It is thrown ahead of you by no light at all, and when you stop, it keeps walking. Spells pass through what isn't there.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gloom hound (`gloom_hound`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A hound the color of the space between trees crosses the path, soundless. The Huntsman's stock run loose out here between hunts, keeping themselves fed. It circles downwind, from habit it does not need.
- **Lore:** The Huntsman's stock run loose between hunts, keeping themselves fed. The downwind circle is habit it does not need.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Dead signal (`dead_signal`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, magic_resist
- **Description:** A voice you almost know calls your name from off the path — the exact tone of someone in Roothollow, worn thin by distance. The old realm's transmissions never died here. They just kept walking.
- **Lore:** The old realm's transmissions never died here. They just kept walking, and one of them knows your name.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Dusk boar (`dusk_boar`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A boar built low and wide comes out from under the black boughs, tusks catching the last of the town's lamp, and takes one deliberate step onto the path you wanted.
- **Lore:** It roots the treeline where the lamplight fails, and it has decided the failing light is its property.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Duskhide (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Duskhide holds the treeline where the last lamplight fails — a stag-shadow with no stag in it, antlers of pure absence. Arrows go through. The dark between the trees does not.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 72 — The Whisperwood (biome: The Gloom, tier 8, gate town: Hushfall)

**Landscape:** The trees here carry sound the way wires carry charge. Every word spoken here keeps traveling, trunk to trunk, for years — the wood is full of conversations that outlived both parties. The locals trade in whispers and go armed against being quoted.

### Quoted shade (`whisper_shade`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A shade steps out of a trunk mid-sentence, finishing something said here long ago, in your voice. It knows things you said three floors down. It has had time to take them personally.
- **Lore:** It finishes sentences said here long ago in your voice, and it knows things you said three floors down. It has had time to take them personally.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Echo hound (`echo_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A gloom hound hunts these woods by throwing its own footfalls ahead of itself. You hear it pass on the left. That is where it is not.
- **Lore:** It throws its own footfalls ahead of itself. You hear it pass on the left. That is where it is not.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Stray nightmare (`night_mare`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, armoured
- **Description:** A black mare stands riderless in the trees, saddled in cobweb, patient. Everyone in the gate town knows somebody who got on. It waits with the confidence of a thing that has never needed to chase.
- **Lore:** Saddled in cobweb, patient. It has never needed to chase — everyone in the gate town knows somebody who got on.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gall wasps (`gall_wasp_swarm`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** A seam in the nearest trunk hums open and the wasps come out in a ribbon, riding the sound of your own footsteps back at you.
- **Lore:** They nest in the talking trees and sting whatever raises its voice. The wood has opinions about being quoted.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Hearsay (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The wood's oldest rumor has been repeated so long it has a body now. Hearsay comes through the trunks sideways, made of everything the forest heard and kept — and it knows exactly which whisper will make you turn around.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 73 — The Grey Rides (biome: The Gloom, tier 8, gate town: Bridlerest)

**Landscape:** Long straight avenues cut through the black forest, grassed in grey. These are the Huntsman's rides, and everything in the Gloom knows their calendar. On hunt nights the towns bar their doors. Between hunts, the rides are the fastest road north.

### Ride-warden hound (`ride_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A gloom hound stands at the ride's edge, marking the verge the way a gamekeeper marks a covert. You are game, walking the master's ride. It sounds one note, low, to log the flush.
- **Lore:** You are game, walking the master's ride. The one low note is it logging the flush.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Grey outrider (`grey_rider`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce, armoured
- **Description:** A rider comes up the ride at a canter that makes no hoofbeats — one of the Huntsman's whips, grey from hat to boot, face lost in it. It leans down as it passes. It is measuring you for the next hunt's card.
- **Lore:** One of the Huntsman's whips, grey from hat to boot. The lean as it passes is a fitting — for the next hunt's card.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Verge-runner shade (`verge_shade`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, magic_resist
- **Description:** Something that was once quarry still runs the verge on hunt nights, unable to stop. It bursts past you in rags of shadow, and behind it the ride goes cold, remembering.
- **Lore:** Once quarry, still running the verge on hunt nights, unable to stop. Behind it the ride goes cold, remembering.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ride crow (`ride_crow`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A crow drops from the black canopy to the ride's grey turf ahead of you, checks the empty avenue both ways like a connoisseur, and decides the hunt has come early this week.
- **Lore:** It follows the hunts the way its kind follow armies, and it has learned the calendar better than the towns.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Tallyhorn (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Where the rides cross stands Tallyhorn, the Huntsman's counter — a figure of grey livery and antler, keeping the game-book of the whole forest. It looks at you, licks its thumb, and turns a page. The stair is behind it, past the counting.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 74 — The Echo Glades (biome: The Gloom, tier 8, gate town: Fainthollow)

**Landscape:** Clearings open in the forest, and each one holds a moment that will not finish — a wedding dance, a skirmish, played over in grey light with the sound worn off. The realm's last transmissions pooled in these glades when the signal died. Walk around them.

### The dancers (`glade_dancers`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The wedding glade needs a partner tonight — a gap in the round where someone used to be. The dancers stop. Every grey face turns to you with the same polite, starving expectation.
- **Lore:** The round has a gap where someone used to be, and every grey face turns to you with the same polite, starving expectation.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Skirmish remnant (`skirmish_shade`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, armoured
- **Description:** In the battle glade one soldier has noticed, after all these years, that the enemy stopped coming. It walks out of the replay toward you, sword grey with disuse, relieved beyond words to have somebody real.
- **Lore:** After all these years it has noticed the enemy stopped coming. It is relieved beyond words to have somebody real.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Glade-shy hound (`glade_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** The gloom hounds will not enter the glades, which tells you something. This one has learned to drive travelers into them instead, and it works you toward the wedding light with the patience of a sheepdog.
- **Lore:** The hounds will not enter the glades, which tells you something. It drives travelers in instead, patient as a sheepdog.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Glade moth (`glade_moth`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** A moth the grey of the wedding light lifts off the glade's edge and makes for you in slow spirals, wings printed with a pattern that is almost faces.
- **Lore:** It feeds on the grey light of the replays, and it resents every shadow that dims the show.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Encore (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The largest glade holds the realm's last broadcast — a farewell, looped. Encore is its keeper, a conductor-shape in frayed grey formalwear, and it will not let the performance end short of an audience. You have arrived. The overture starts over.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 75 — The Black Meadows (biome: The Gloom, tier 8, gate town: Wickstead)

**Landscape:** The forest opens onto meadows of black grass under a paper-grey sky, and the meadows are pasture. The Huntsman's nightmares graze between hunts — a herd, coal-dark, cropping grass that whispers. The herd-boys of Wickstead never, under anything, run.

### Grazing nightmare (`pasture_mare`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, magic_resist
- **Description:** A nightmare lifts its head from the black grass and considers you with eyes like banked coals. Whatever it dreams while it grazes, you have just walked into it, and it objects.
- **Lore:** Whatever it dreams while it grazes, you have just walked into it, and it objects.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Herd stallion (`herd_stallion`)
- **Size:** at-floor peer (medium) — traits: bulwark, feeble
- **Description:** The stallion comes over at a walk, which the herd-boys will tell you is the bad sign — a tower of black muscle and slow smoke, putting itself between you and the herd, hoping you will insist.
- **Lore:** A tower of black muscle and slow smoke. It puts itself between you and the herd and hopes you will insist — you will not wear it down before dark.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pasture hound (`meadow_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** The hounds that mind the herd are chosen for patience, and this one has been watching you cross the meadow for half a mile without once moving. Now it moves.
- **Lore:** Chosen for patience. It watched you cross half a mile of meadow without moving. Now it moves.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Black crake (`black_crake`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** The black grass detonates a wingspan from your boot — a crake going up in a clatter of dark feathers, circling back at head height to scream you to the whole meadow.
- **Lore:** It nests in the whispering grass and screams the herd's alarms. The herd-boys hate it more than the herd.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Nightbridle (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The first nightmare ever broken to harness was never quite broken. Nightbridle grazes apart, bridled in cold iron it has chewed thin, waiting out the terms of an old bargain. It sees you, and decides the bargain is paid.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 76 — The Shade Walks (biome: The Gloom, tier 8, gate town: Candlerow)

**Landscape:** An avenue of statues runs through the forest — the realm's heroes in bronze, every one missing its shadow. The shadows walk the avenue on their own now, trading plinths. The gate town sells candles by the dozen: a lit candle owns its shadow. Yours.

### Unfixed shadow (`statue_shade`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** The shadow of a swordsman detaches from an empty plinth and takes its stance — flawless, drilled into the bronze for a century. It fights like the statue's better memory of itself.
- **Lore:** A century drilled into the bronze made the stance flawless. It fights like the statue's better memory of itself, and blows ring on it like metal.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Candle-thief shade (`candle_thief`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** Something slim and quick moves down the avenue pinching out flames, and your circle of light is next on the round. Fight in the dark, or fight it at the candle — the etiquette guides disagree.
- **Lore:** It pinches out flames down the avenue, and your circle of light is next on the round.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Avenue hound (`walks_hound`)
- **Size:** small and slight — traits: frail, feeble, magic_resist
- **Description:** A gloom hound pads the avenue with a shadow that does not match — too big, walking on the walls. When the hound stops, the shadow keeps coming.
- **Lore:** Its shadow does not match — too big, walking on the walls. When the hound stops, the shadow keeps coming.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Avenue rat (`avenue_rat`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A rat trots the plinth-line with a guttering candle stub in its jaws like a trophy, drops it at the sight of you, and elects to defend the whole avenue's supply.
- **Lore:** It eats the candle-stubs the pilgrims leave and has grown bold enough to prefer them lit.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Palewick (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the avenue's end burns one candle taller than you, and its keeper is Palewick — a shade grown solid on a hundred years of stolen light, holding the flame that owns every shadow on this floor. Including, as of the treeline, yours.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 77 — The Kennel Courts (biome: The Gloom, tier 8, gate town: Stillhorn)

**Landscape:** The Huntsman kennels his pack in a ruined manor court, and the court has grown to fit the pack — gates of black bone, a mews where winged things shift in the dark. The kennel-shades keep the feeding book fastidiously. Do not read the entries.

### Kennel-master shade (`kennel_master`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The kennel-master comes out wiping its hands on a leather apron that has seen use. It looks you over as stock, checks something in the feeding book, and unclips the first lead.
- **Lore:** It looks you over as stock, checks the feeding book, and unclips the first lead. The apron has seen use.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Pack matron (`pack_matron`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The oldest hound in the kennels does not run with the hunts anymore; she trains what does. She comes off her stone bench joint by joint, and every run in the court goes quiet to watch the lesson.
- **Lore:** She does not run with the hunts anymore; she trains what does. The whole court goes quiet to watch the lesson.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mews-kept nightmare (`mews_mare`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A nightmare is stabled here for re-breaking, and it has gotten the door open again. It comes across the court trailing a snapped rope, wearing its freedom like a dare.
- **Lore:** Stabled for re-breaking, and the door is open again. It wears its freedom like a dare.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mews owl (`mews_owl`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Something leaves the mews' dark through a gap no wider than a hymnal — an owl in a torn hood, climbing fast, and the first stoop is for whoever opened the court gate.
- **Lore:** The winged things in the mews are hooded for a reason. This one worked its hood off.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Leashbone (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Leashbone holds the kennels' inner gate, a tall shade wound in every lead the pack has ever slipped. It does not fight so much as handle you — and it has handled things with far more legs and far worse manners.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 78 — The Snare Woods (biome: The Gloom, tier 8, gate town: Brambleside)

**Landscape:** The forest here has been dressed — every path a lane, every lane a funnel, every funnel ending somewhere prepared. Snares of shadow and wire, a tree that is a trigger. The Huntsman does not always ride his quarry down. Sometimes he prefers it delivered.

### Snare-setter (`snare_shade`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A shade works a new snare into the path ahead, weaving shadow through wire with a craftsman's absorption. It does not stop when it sees you. You are the test of the workmanship.
- **Lore:** It weaves shadow through wire with a craftsman's absorption. You are the test of the workmanship.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The caught thing (`caught_thing`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** Something big hangs in a canopy snare, wrapped and furious, swinging in short arcs. Cutting it down is mercy. Mercy, out here, has a survival rate.
- **Lore:** Cutting it down is mercy. Mercy, out here, has a survival rate.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Funnel hound (`funnel_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce
- **Description:** A gloom hound appears behind you on the lane, then another on the left, then the right — never closing, only steering. Ahead the trees narrow. You are being delivered, on schedule.
- **Lore:** Never closing, only steering. Ahead the trees narrow. You are being delivered, on schedule.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Wire beetle (`wire_beetle`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** A beetle in a shell of wound wire works along a dressed lane, stripping a snare with its jaws, and rounds on you with the loyalty of a thing defending its larder.
- **Lore:** It eats the Huntsman's snare-wire and armors itself with the leavings. The snare-setters bill it as an occupational hazard.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Springtrap (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The floor's last funnel closes on a clearing, and the clearing is Springtrap — soil, trees, and all, one patient mechanism wearing a forest for camouflage. You are inside it when it introduces itself.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 79 — The Quarry Runs (biome: The Gloom, tier 8, gate town: Bayhollow)

**Landscape:** The last stretch before the Pale Court is where the Huntsman runs his best game, and the forest has been worn into racecourse — banked turns of black turf, hides for an audience. Tonight's card has one name on it. Bayhollow has already placed its bets.

### Pacing hound (`pacer_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A gloom hound falls in beside you at an easy lope, matching you stride for stride. It is not hunting. It is pacing you, for the handicap, and it keeps glancing at your knees.
- **Lore:** It is not hunting. It is pacing you, for the handicap, and it keeps glancing at your knees.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rival quarry (`rival_quarry`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Something else is on tonight's card — a grey elk with three hunts' worth of broken snares hanging off it. It has decided the field is not big enough for two, and thinning the competition counts as strategy.
- **Lore:** Three hunts' worth of broken snares hang off it. Thinning the competition counts as strategy.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Course steward (`course_steward`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** A shade in a steward's sash steps onto the turf and raises a grey flag. You are, it indicates, off the marked course. Rejoining is compulsory. The flag is not a request.
- **Lore:** You are off the marked course. Rejoining is compulsory. The flag is not a request.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Stand crow (`stand_crow`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A crow flaps up from the master of hounds' stand with a betting slip in its beak, takes one lap of the course over your head, and marks you down as tonight's long odds.
- **Lore:** It works the audience hides for dropped stakes and settles bets nobody survived to collect.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Foxglove (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The course ends at the master of hounds' stand, where Foxglove waits — the only quarry that ever finished the run, retired into staff. It wears its old snare-scars like service ribbons, and it knows every line you might take, having taken them all.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 80 — The Pale Court (biome: The Gloom, tier 8, gate town: Hornsend)

**Landscape:** The forest ends at a hall with no walls — pale columns of birch bone, a floor of grey turf, a sky the color of a held breath. Hounds in their hundreds sit the perimeter in silence. The hunt is assembled, and at its head, horn in hand, waits the master.

### The first whip (`first_whip`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The Huntsman's first whip rides out to meet you at a walk, grey coat immaculate, face a smudge. It uncoils its lash with the boredom of long practice. Precedence must be observed — nobody reaches the master unbloodied.
- **Lore:** Precedence must be observed — nobody reaches the master unbloodied. The lash uncoils with the boredom of long practice.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Brace of pale hounds (`pale_hound_brace`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** Two hounds from the master's own couple rise from the perimeter, white as the columns, moving in mirrored arcs. They have opened every hunt for a century. They open yours.
- **Lore:** White as the columns, moving in mirrored arcs. They have opened every hunt for a century. They open yours.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The master's remount (`honored_mare`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, magic_resist
- **Description:** The Huntsman's spare nightmare stands at the rail, saddle empty. It has carried him through every season and considers the vacancy an insult. It comes at you to fill the time.
- **Lore:** The master's spare, saddle empty. It considers the vacancy an insult and comes to fill the time.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Unblooded hound (`unblooded_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** One hound of the assembled hundreds cannot hold the silence — young, white-pawed, quivering — and it comes off the perimeter line at you before the horn grants anyone leave.
- **Lore:** Too young for the perimeter's silence, it breaks rank for you — its first hunt, and it wants it perfect.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The Pale Huntsman (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The Huntsman raises the horn and does not blow it — that courtesy is the whole of his mercy. Pale from hat to boot, patient as winter, he draws a knife that has ended every hunt since the forest was stolen. The pack holds its breath. So does the sky.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 81 — The First Outwork (biome: Hellmarch, tier 9, gate town: Sappersrest)

**Landscape:** The Gloom's last trees stand against a wall of black iron, and the wall goes up out of sight. The King's first outwork: ramparts of welded plate, gun-slits that breathe, a gate scaled for siege engines. Some of this wall was not built. It grew.

### Outwork imp (`outwork_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** An imp scuttles along the rampart top with a rivet gun and a quota. Maintenance doubles as sentry duty out here, and it has just found something worth reporting. It reports you with the rivet gun.
- **Lore:** Maintenance doubles as sentry duty out here. It reports you with the rivet gun.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Hellknight of the gate (`gate_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A hellknight steps out of a wall-niche where it has stood since the outwork was raised — armor welded shut a lifetime ago, engine-heart idling up through the plate. It lowers a halberd that is part of its arm.
- **Lore:** Armor welded shut a lifetime ago, engine-heart idling up through the plate. The halberd is part of the arm.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Wall-flesh (`wall_growth`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A patch of rampart peels itself off the wall and comes at you — plate and sinew in equal parts, the outwork's living mortar. The wall behind it heals over before it has crossed half the distance.
- **Lore:** The outwork's living mortar. The wall behind it heals over before it has crossed half the distance.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Outwork crow (`outwork_crow`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A crow with soot-slicked feathers lifts off a gun-slit's lip, rides the wall's warm exhalation over your head, and calls you in to whatever keeps the ledger inside.
- **Lore:** Iron walls still feed crows. The gun-slits breathe out, and something always rides the warm draft.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Rivetgrim (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The gatehouse is Rivetgrim's body — portcullis teeth, murder-hole eyes, and a foreman's temper spot-welded through the whole assembly. The gate does not open. The gate stands up.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 82 — The Chain Yards (biome: Hellmarch, tier 9, gate town: Linkside)

**Landscape:** The chains that bind every stolen realm were forged here, and the yards never stopped — acre after acre of anvils, quench-pits of black oil, chain running overhead. The hammer rhythm is constant. The locals set their hearts by it, having no choice.

### Chain-gang imp (`chain_imp_gang`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A gang of imps hauls a new-forged link toward the lift-heads, and the foreman imp has spotted a way to lighten the load — you look sturdy, and the harness is adjustable.
- **Lore:** The foreman has spotted a way to lighten the load — you look sturdy, and the harness is adjustable.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Quench-tempered knight (`quench_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A hellknight climbs out of the quench-pit trailing black oil, armor still ticking with heat. It is fresh from tempering and has been issued nothing yet but the need to test itself.
- **Lore:** Fresh from tempering, issued nothing yet but the need to test itself.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Living chain (`loose_chain`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A length of chain slides off its overhead run and pools on the yard floor, then rears like something with a spine. The forge puts a little of the fire into everything it makes, and this one got a temper.
- **Lore:** The forge puts a little of the fire into everything it makes. This one got a temper.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Quench-pit eel (`pit_eel`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, magic_resist
- **Description:** The quench-pit's skin of oil parts without a sound and an eel pours itself over the lip, black on black, tasting the yard-floor heat for the shape of you.
- **Lore:** It swims the black oil between temperings and eats what the quench rejects. Spellwork slicks off it with the oil.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Anchorwrath (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the master forge hangs the first link ever made for the tower, and Anchorwrath wears it as a collar — a smith-shape of scar tissue and forge plate, hammer grown into fist. It has chained up ninety-nine realms. It sizes you for a link.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 83 — The Furnace Roads (biome: Hellmarch, tier 9, gate town: Stokegate)

**Landscape:** Roads of grated iron run between the outworks, laid over open furnace channels — the March's blood-heat, piped floor to floor. Walking them means walking on light. The furnaces below are fed by chute, and it is bad luck to ask what the chutes are fed.

### Stoker imp (`stoker_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A stoker imp rides its coal-chute up onto the road, shovel first. The furnace below is running lean, the schedule says feed it, and you are standing on the hatch — which the imp counts as volunteering.
- **Lore:** The furnace is running lean, the schedule says feed it, and you are standing on the hatch — which counts as volunteering.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Road-warden knight (`road_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A hellknight patrols the grate-road barefoot, plate soles glowing dull red. Heat discipline is a point of pride in the March. It means to teach you the standard.
- **Lore:** It patrols the grate barefoot, soles glowing dull red. Heat discipline is a point of pride, and it means to teach the standard.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Under-grate thing (`grate_thing`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** Fingers come up through the grate ahead of you — too many, too long, comfortable in the light of the channel. Something lives between the furnaces, eating what the chutes deliver, and it has learned the sound of footsteps stopping.
- **Lore:** It lives between the furnaces, eating what the chutes deliver. It has learned the sound of footsteps stopping, and spells cook off before they reach it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Cinder swift (`cinder_swift`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A swift snaps up out of the channel-light between two grates, wings trailing threads of smoke, and carves a hot circle around your head, herding you off its nesting run.
- **Lore:** It nests in the road grating and hunts the updraft. Nothing else on the March flies this low on purpose.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Cindergrate (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Where the roads converge the grating rises into a figure — Cindergrate, the junction itself gone upright, furnace-light pouring through its lattice. Every road on the floor is part of its body, and you have been walking on it since the gate.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 84 — The Welding Halls (biome: Hellmarch, tier 9, gate town: Seamside)

**Landscape:** This is where the King's army is made, and it is not recruited. Halls of surgical gantries run to the horizon, arc-light flickering off hanging plate. Flesh goes in at one door. What comes out the other door marches. The halls are always working.

### Seam-checker imp (`seam_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A quality-imp moves down the line tapping welds with a little hammer, listening. It taps you twice, frowns at the sound of unmodified meat, and flags you for the gantries.
- **Lore:** It taps you twice, frowns at the sound of unmodified meat, and flags you for the gantries.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Fresh-welded soldier (`fresh_welded`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** Something newly finished sits up on the line, seams still smoking, and swings its legs down. It does not know its own name yet. It knows its function, and its function is walking toward you.
- **Lore:** It does not know its own name yet. It knows its function, and its function is walking toward you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The rejected lot (`rejected_lot`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** Behind the halls is the scrap-yard of what failed inspection, and the failures have organized. A committee of them comes over the fence — wrong joints, extra arms, grievances in writing.
- **Lore:** The failures have organized — wrong joints, extra arms, grievances in writing.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Arc moth (`arc_moth`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble, fly
- **Description:** A moth with wings like smoked mica detaches from a gantry lamp and beats down the line toward the brightest thing on the floor, which — between arcs — is your lamp.
- **Lore:** It drinks the welding light. The gantry crews bill the King for what it costs them in torches.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Seamwright (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The halls' master artisan never stopped improving itself — Seamwright is a cathedral of its own best work, four gantry arms, a torso of perfect welds. It looks at you the way a sculptor looks at quarry stone, and lights the torch.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 85 — The Imp Warrens (biome: Hellmarch, tier 9, gate town: Sootside)

**Landscape:** Between the great works, the March's labor force lives in a city of its own making — a slum of flue-pipes and stolen plate, stacked twelve deep, riddled with markets and feuds. A million imps, more or less. Everything is for sale, including the etiquette.

### Warren tough (`warren_tough`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** An imp twice imp-size — a glandular marvel, the locals say — collects protection along this flue-street. You are new custom, walking unprotected. It cracks knuckles like a string of firecrackers.
- **Lore:** A glandular marvel, the locals say. You are new custom, walking unprotected.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warren press-gang (`press_gang`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** Three imps with a length of net and one with a clipboard block the alley. The Welding Halls pay a bounty per body, the clipboard explains, and yours is worth a month of quota. It is nothing personal. It is documented.
- **Lore:** The Welding Halls pay a bounty per body, and yours is worth a month of quota. It is nothing personal. It is documented.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Off-duty hellknight (`slumlord_knight`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A hellknight has retired into the warrens as a slumlord, rent collected in teeth. It fills the whole street when it steps out, engine-heart knocking, sure beyond argument that you owe it something.
- **Lore:** Retired into the warrens, rent collected in teeth. It is sure beyond argument that you owe it something.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Flue bat (`flue_bat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** Something drops out of the nearest flue-pipe in a puff of soot and takes the alley at head height — a bat fat on market scraps, indignant that the airspace is occupied.
- **Lore:** A million chimneys, one bat per flue. The warrens sell the guano and lose the arguments.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Fluegrim (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The warrens' true landlord lives in the master chimney — Fluegrim, an old fire that has worn the flue so long it has the shape of one, soot-black and slow. When it leans out over the rooftops, a million imps find somewhere else to be.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 86 — The Bastion Line (biome: Hellmarch, tier 9, gate town: Wallrest)

**Landscape:** Nine bastions in echelon, each one a fortress that would anchor a kingdom's border below, here just a rung. The garrisons drill day and night against an enemy the officers will not name. It is you. The drill instructors use your description.

### Drill-square knight (`drill_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A hellknight steps off the drill square mid-exercise, given leave at last to work the live version of the problem. It has rehearsed this fight so long it starts with your counter.
- **Lore:** It has rehearsed this fight so long it starts with your counter.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Ballista crew (`bastion_imp_crew`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** An imp crew swings a wall-ballista around with drilled speed, bickering about windage the whole way. Their record on moving targets is chalked on the bastion wall. It is embarrassing, and they know you can read it.
- **Lore:** Their record on moving targets is chalked on the wall. It is embarrassing, and they know you can read it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Parade hulk (`parade_hulk`)
- **Size:** at-floor peer (medium) — traits: bulwark, fierce
- **Description:** The garrison keeps one welded hulk polished for parades, and it has been standing at attention for a decade waiting for an order worth having. Your arrival is an order. It falls out with a sound like a drawbridge.
- **Lore:** Polished for parades, at attention for a decade, waiting for an order worth having. Your arrival is an order — and it was built to be impossible to stop.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Rampart falcon (`rampart_falcon`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage, fly
- **Description:** A falcon in a message-harness checks its line between bastions, folds, and stoops at you instead — the standing orders, it turns out, define interceptor generously.
- **Lore:** The garrisons fly messages between bastions. The falcons have standing orders about interceptors.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sally hound (`sally_hound`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** A sally port cracks and a hound comes through it flat and silent, taking the drill square's diagonal — the one line no formation covers — straight to you.
- **Lore:** Kenneled at the sally ports and fed on drill-square mistakes. It knows the gap in every formation.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Bastionheart (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The ninth bastion's keep is not garrisoned; it is inhabited. Bastionheart pulls its limbs out of the four corner towers and stands, the whole keep re-arranging into shoulders. The garrison salutes. You are the graduation exercise.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 87 — The Siege Gardens (biome: Hellmarch, tier 9, gate town: Ramside)

**Landscape:** The King grows his siege engines. Rows of them stand planted in beds of bone-meal and engine oil — rams budding off trellises, trebuchets ripening on the stem. Imp gardeners work the rows. The harvest is scheduled for the war after this one.

### Pruning-torch imp (`gardener_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A gardener imp is grafting a fresh arm onto a young ram when you interrupt. Contamination of the beds is the one sin the head gardener flogs for, and you are tracking in pollen from ninety floors of elsewhere.
- **Lore:** Contamination of the beds is the one sin the head gardener flogs for, and you are tracking in pollen from ninety floors of elsewhere.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Unripe engine (`unripe_engine`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, fierce
- **Description:** A ram not due for another season tears loose of its trellis at your scent, dragging root-cables. It is green, unbalanced, and eager — a colt with a battering head, ruining the rows to reach you.
- **Lore:** Green, unbalanced, and eager — a colt with a battering head, ruining the rows to reach you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Garden scarecrow (`scarecrow_knight`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** What keeps the carrion birds off the beds is a hellknight crucified on a trellis, still running. The gardeners forgot to tell it the war it fell in is over. It comes off the frame with the nails still in.
- **Lore:** The gardeners forgot to tell it the war it fell in is over. It comes off the frame with the nails still in.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Carrion kite (`carrion_kite`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A kite wheels down off the trellis-rows where the scarecrow cannot reach, bone-meal dust in its primaries, and makes its approach run at the softest thing in the garden.
- **Lore:** What the scarecrow is for. It has been testing the scarecrow's patience for years, and yours looks shorter.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Rootram (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The oldest thing in the gardens is the mother-stock, and it did not care to be pruned. Rootram heaves out of the central bed — the trunk every engine was cut from, walking on a root-ball of soil and cabling — and the gardeners drop their torches and run.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 88 — The Iron Chantries (biome: Hellmarch, tier 9, gate town: Chantside)

**Landscape:** The March keeps its faith in chapels of riveted iron, and the faith is the King. Bells of engine-block, choirs of exhaust, litanies in a script that moves when read. The furnace-priests preach the Ascent in reverse: everything descends, eventually.

### Furnace-priest (`furnace_priest`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A priest of the down-going faith turns from its altar, censer streaming coal-smoke, firebox heart glowing through the cassock of chain. It has preached your arrival for years. It would hate to waste the congregation.
- **Lore:** It has preached your arrival for years and would hate to waste the congregation. The litany turns spellwork back like heat off a firebox.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Choir imp (`choir_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** The choir loft empties as one — a dozen imps in singed surplices, still holding the note. Heresy duty is the only part of the liturgy they enjoy, and you are unmistakably not in the hymnal.
- **Lore:** Heresy duty is the only part of the liturgy they enjoy, and you are unmistakably not in the hymnal.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Penitent hellknight (`penitent_knight`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A hellknight kneels in the nave doing penance for some sin no one will name, chained to the pew by its own request. It looks up at you with terrible hope. Absolution, in the March, is worked off in single combat.
- **Lore:** Chained to the pew by its own request. Absolution, in the March, is worked off in single combat.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Censer haunt (`smoke_haunt`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, fly
- **Description:** The censer-smoke over the nave stops rising and starts deciding — a haunt of grey coils drifting down the aisle toward you, keeping liturgical time.
- **Lore:** Enough coal-smoke has been swung at the King's name that some of it stayed to listen.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Vespergrim (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The chantry's great bell rings itself, and what climbs down the bell-rope after the last stroke is Vespergrim — the floor's high priest, a tower of vestments over a body of organ-pipe and grate. It opens its arms in welcome. The arms keep opening.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 89 — The Herald's Road (biome: Hellmarch, tier 9, gate town: Clarionfall)

**Landscape:** The last road is a triumphal way built for one commuter: Malgrim, the King's voice, whose processions descend when a realm is to be told it has fallen. The road is lined with the honor guard, at their posts tonight. You are the procession now.

### Honor guard knight (`honor_knight`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** A hellknight of the Herald's own guard steps into the road, armor chased in speech-runes that mutter as it moves. It has held this post through nine climbers. It recites their names at you, as introduction and as warning.
- **Lore:** Nine climbers' names recited as introduction and warning. The speech-runed plate has turned everything they tried.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Banner-bearer imp (`banner_imp`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** An imp staggers under a procession banner three times its height and refuses, absolutely, to set it down — the banner is the post. It comes at you swinging the whole assembly like a sail in a gale.
- **Lore:** It refuses, absolutely, to set the banner down — the banner is the post.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Proclamation hulk (`voice_hulk`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, savage
- **Description:** A welded hulk built as a walking loudspeaker wheels onto the road and opens every horn on its chassis. The proclamation is your death notice, read in advance, at a volume that loosens rivets.
- **Lore:** The proclamation is your death notice, read in advance, at a volume that loosens rivets.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Horn bat (`horn_bat`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** When the horns fall silent a bat spills out of the largest bell- mouth, flying by memory instead of ear, and its memory says the road belongs to the horns.
- **Lore:** It roosts in the proclamation horns between readings. The readings have made it deaf and fearless.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Trumpetsteel (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The Herald's gatekeeper is Trumpetsteel, a knight-shape built around a single great horn where the head should be. It sounds your arrival up the stair to its master — one long note, correct to protocol — then lowers itself like the last word of a sentence.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 90 — The Herald's Gate (biome: Hellmarch, tier 9, gate town: Lastmuster)

**Landscape:** The March ends at a gate of black iron scaled for a god, and before it, a parade ground where the King's herald holds court over the Marshals of the March. The banners are silent. Malgrim has dismissed the guard — a courtesy, to you and to the guard.

### Marshal of the March (`marshal_knight`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A Marshal in campaign plate leaves the reviewing line without leave — an ambitious breach. Presenting the Herald with your head might be worth the flogging. It has done the arithmetic, visibly, and closed the ledger.
- **Lore:** Presenting the Herald with your head might be worth the flogging. It has done the arithmetic, visibly, and closed the ledger.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The Herald's secretary (`herald_imp`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** Malgrim's personal secretary is an imp grown fat and precise on state secrets. It meets you with a writ of execution, pre-signed, requiring only a date. It carries the pen like a dagger, and the dagger like a pen.
- **Lore:** Fat and precise on state secrets, carrying a pre-signed writ of execution. Spells blur against what it knows and will not say.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Gate-tender hulk (`gate_hulk`)
- **Size:** at-floor peer (medium) — traits: bulwark, fierce
- **Description:** The hulk that tends the great gate has one duty and no discretion — nothing passes while the Herald holds court. It plants itself with the finality of architecture and waits for you to test the point.
- **Lore:** One duty and no discretion — nothing passes while the Herald holds court. It has the patience and the build of architecture.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Muster hound (`muster_hound`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A hound in a studded muster-collar breaks from the reviewing line's shadow, taking the parade ground in a flat arc that ends, by old training, at the throat of whatever stands where you are standing.
- **Lore:** It runs the parade ground's edge at every muster. Dismissing the guard did not dismiss the dog.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Drummer imp (`drummer_imp`)
- **Size:** enormous — it fills the path — traits: hulking, fierce
- **Description:** One imp on the empty parade ground keeps the muster-beat on a drum of gate-iron, eyes shut, and when your footfall breaks its rhythm it opens them on you like a grievance.
- **Lore:** The muster-beat must be kept while the gate stands. Nobody told it the muster was over.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Malgrim, Herald of the King (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Malgrim descends the gate-stair unarmored, which is the whole message — a tall grace of scar and engine, the King's voice in a throat of brass. He announces you to the tower, floor by floor, and by the time he reaches your name he has drawn his sword.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 91 — The Obsidian Stair (biome: The Crown, tier 10, gate town: Firststep)

**Landscape:** Above the March there is no more pretense of country. The Crown is one building — black glass grown around the tower's reactor-heart — and this floor is its doorstep: a stair of obsidian, polished mirror-deep. Your reflection arrives first. It reports.

### Obsidian sentinel (`stair_sentinel`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** A figure detaches from the balustrade — black glass in the shape of a swordsman, faceless, flawless. The Crown does not garrison its doorstep with soldiers. It casts them.
- **Lore:** The Crown does not garrison its doorstep with soldiers. It casts them, and glass casts thick.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Your reflection (`reflection_wrong`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The climber in the polished riser ahead has stopped matching you. It steps out of the glass wearing your stance and your gear and a much better night's sleep, and it has clearly been studying.
- **Lore:** It wears your stance, your gear, and a much better night's sleep. Spells recognize themselves in it and hesitate.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Court page (`court_page`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** An imp in Crown livery — silk, not soot — descends the stair with a silver tray and a summons. Refusing a royal summons is death. Accepting is death with better lighting. The page waits, professionally, while you choose.
- **Lore:** Refusing a royal summons is death. Accepting is death with better lighting. It waits, professionally, while you choose.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mirror moth (`mirror_moth`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A moth with wings of near-perfect mirror lifts off the balustrade, and as it circles you it flashes back small crooked pieces of your own climb.
- **Lore:** It lays its eggs in reflections. The stair-keepers polish against it, and lose ground yearly.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Firstriser (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The top step is occupied and has been for a thousand years. Firstriser unfolds from its seat — the stair's own mass in the shape of a kneeling knight, rising joint by black glass joint. It has let no one past without a fight worth watching.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 92 — The Mirror Galleries (biome: The Crown, tier 10, gate town: Sheenrest)

**Landscape:** The citadel's outer halls are walled in polished obsidian, and the court uses them the way courts use mirrors — for vanity, and for watching behind themselves. Every surface holds a crowd of reflections, and not all of them have owners present.

### Gallery duelist (`gallery_duelist`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A demon of the lesser court has been practicing against its own reflection for a century, and the reflection finally let it win. It needs a fresh opponent and you have no standing to refuse — dueling here is how the court says hello.
- **Lore:** A century against its own reflection, and the reflection finally let it win. Dueling here is how the court says hello.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Orphaned reflection (`orphan_reflection`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A reflection whose owner died at some forgotten intrigue still walks the black glass, hall to hall, looking out. It has found a body it likes. It presses against the inside of the mirror nearest you, testing.
- **Lore:** Its owner died at some forgotten intrigue. It has found a body it likes, and spells slide off the glass it lives behind.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Whispering courtier (`whisper_courtier`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, magic_resist
- **Description:** A courtier falls into step beside you, all silk and sympathy, trading rumors you did not ask for. Somewhere in the third sentence the sympathy runs out, and the silk turns out to be wire.
- **Lore:** All silk and sympathy until the third sentence, when the sympathy runs out and the silk turns out to be wire.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sconce imp (`sconce_imp`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** An imp swings down from a lamp-sconce with a taper-snuffer held like a halberd, counts your reflections in the black glass, and presents the bill.
- **Lore:** It tends the gallery lamps and taxes every shadow they throw. Yours arrived unregistered.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Backglass (warden)
- **Size:** boss — fills the stair-gate
- **Description:** At the galleries' heart the reflections pool, and Backglass is what they pooled into — everything the court's mirrors kept, in one tall body of layered images. It fights you seven duels at once, one for every angle you have ever been seen from.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 93 — The Reactor Galleries (biome: The Crown, tier 10, gate town: Coreside)

**Landscape:** The citadel's walls go translucent here, and you see what the Crown is built around: the reactor-heart, a column of caged light climbing the floors like a spine. Its hum is in your teeth. The keepers wear crowns of lead and do not take questions.

### Lead-crowned engineer (`lead_crowned`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** One of the reactor's keepers turns from its console of levers, lead crown low over a face gone bright behind smoked glass. Interruptions to the great work are bled off like excess pressure. It reaches for the valve that is you.
- **Lore:** Interruptions to the great work are bled off like excess pressure. Under the lead and the smoked glass, almost nothing gets through.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Light-leak (`light_leak`)
- **Size:** at-floor peer (medium) — traits: feeble, fly
- **Description:** A hairline crack in the gallery wall lets a thread of the heart's light through, and the thread has learned to move against the draft. It comes across the floor like a slow lightning, feeling for something to be inside.
- **Lore:** A thread of the heart's light that learned to move against the draft, feeling for something to be inside.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Coil-fed demon (`coil_demon`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** A demon of the middle court has tapped the reactor's coils to feed on, jaw wired straight into the shielding, radiant with theft. It should not be here either, which makes you a witness.
- **Lore:** Jaw wired straight into the shielding, radiant with theft. It should not be here either, which makes you a witness.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Sluice rat (`sluice_rat`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** A rat with a faint glow under its skin slips out of a shielding seam, whiskers reading the gallery hum, and stands its ground on the warm plate you need to cross.
- **Lore:** It nests in the reactor shielding, warm and half-bright, and defends the warmth like a birthright.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Halflight (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Halflight guards the gallery sluice, a warden cast half of obsidian and half of the heart's own glow, split down the middle like an eclipse. The dark half blocks. The bright half burns. They take turns.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 94 — The Antechambers (biome: The Crown, tier 10, gate town: Doorward)

**Landscape:** A floor of waiting rooms, because even a demon court runs on waiting. Petitioners from a hundred conquered realms sit the benches — some for decades, some past being alive, all holding numbered tokens of black glass. A token is issued. The token is warm.

### Queue veteran (`queue_veteran`)
- **Size:** at-floor peer (medium) — traits: bulwark, fierce
- **Description:** The thing on the bench beside the door has waited so long it has become part of the protocol — robes fused to the stone, token worn smooth. It has decided, watching you walk in, that you intend to jump the line.
- **Lore:** It has waited so long it became part of the protocol — robes fused to the stone, token worn smooth. You will tire before it does; everyone has.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Under-chamberlain (`chamberlain`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** An under-chamberlain sweeps toward you, a demon of ledgers and closed doors, robes hissing on the glass floor. Your paperwork, it regrets, is fatally out of order. The regret is genuine. The fatality is procedural.
- **Lore:** Your paperwork is fatally out of order. The regret is genuine. The fatality is procedural.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Recalled tokens (`token_swarm`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Somewhere a clerk voids a century of the queue, and the recalled tokens come looking for their holders — a drift of black glass chips moving with intent. Yours, in your pocket, is getting warmer.
- **Lore:** A century of the queue, voided, and the recalled tokens want their holders. Yours is getting warmer.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Petitioner's hound (`petitioners_hound`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A hound rises from beneath an empty bench where somebody's robes still sit, stretches a century out of its joints, and crosses the anteroom to explain what it thinks of queue-jumpers.
- **Lore:** Its master's number was never called. It holds the bench, and the grudge, on his behalf.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Anteroom (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The last waiting room is the Warden. Anteroom closes its doors around you — benches, ceiling, and patience all one creature that has digested ten thousand petitioners at their most docile. The far door is its heart. It has agreed to see you now.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 95 — The Trophy Vaults (biome: The Crown, tier 10, gate town: Relicgate)

**Landscape:** The King keeps what he takes, curated: the crown jewels of drowned realms, a carousel from somewhere that surrendered too late. Every exhibit is labeled, honestly, in the court script. Near the stair stands an empty plinth, pre-labeled.

### The curator (`vault_curator`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** A demon in archivist's grey moves down the gallery straightening labels. It knows the provenance of everything in the vaults, including, it mentions without turning around, the piece the empty plinth is waiting for.
- **Lore:** It knows the provenance of everything in the vaults, including the piece the empty plinth is waiting for.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Exhibit, awake (`exhibit_awake`)
- **Size:** at-floor peer (medium) — traits: feeble, armoured
- **Description:** One of the exhibits — a realm's champion, taken whole, armor and all — has been on its plinth long enough to work one foot loose. It steps down stiffly and looks at you with a terrible question: which side of a plinth are you on?
- **Lore:** A realm's champion, taken whole, armor and all. Its terrible question: which side of a plinth are you on?
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Court appraiser (`appraiser_imp`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** An imp with a jeweler's glass screwed into each eye circles you twice, muttering valuations. Your gear disappoints it. Your defiance, it says, brightening, will mount beautifully.
- **Lore:** Your gear disappoints it. Your defiance, it says, brightening, will mount beautifully.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Case moth (`case_moth`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A moth the grey of old banners lifts off a drowned realm's colors with a mouthful of history, and makes for the freshest fabric in the vaults, which is what you are wearing.
- **Lore:** It eats the exhibits — tapestry first, provenance second. The curator has posted a bounty in three scripts.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Plinthguard (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The vaults' keeper was itself the first exhibit — a conquered realm's guardian colossus, re-labeled into staff. Plinthguard steps off its pedestal, leaving its outline in the dust, and takes up a halberd from a realm that also thought it would win.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 96 — The Night Gardens (biome: The Crown, tier 10, gate town: Bloomshade)

**Landscape:** The court takes its air in gardens grown from every realm the King broke — elven lamp-trees grafted onto dwarven iron-roses, meadow turf from floor one. Nothing here grows the way it did at home. Everything grows.

### Grafted horror (`graft_horror`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A lamp-tree crossed with something that once had opinions pulls its roots and comes at you glowing, half bio-light and half bramble. Somewhere inside it is a cutting of the forest you walked on floor twenty-three, and it remembers you passing.
- **Lore:** Somewhere inside it is a cutting of the forest from floor twenty- three, and it remembers you passing. The graft drinks spellwork like lamp-oil.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Keeper of the beds (`garden_keeper`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** A demon gardener straightens up among the iron-roses, shears in hand, apron full of clippings that will not hold still. You are standing on the floor-one turf. It is very rare, it says, advancing. It is very rare because of people like you.
- **Lore:** You are standing on the floor-one turf. It is very rare. It is very rare because of people like you.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Night-pollen drift (`pollen_shade`)
- **Size:** thick through the shoulders (large) — traits: sturdy, fierce, fly
- **Description:** The gardens pollinate after dark, and the drift finds you — a golden cloud with a slow, deliberate shape to its drifting. What it pollinates, the gardeners harvest. Do not inhale the future.
- **Lore:** What it pollinates, the gardeners harvest. Do not inhale the future.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Iron-rose beetle (`rose_beetle`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** A beetle armored in overlapping rose-iron petals drops off a grafted trellis, lands with a clank on the rare turf, and advances on you like a small opinionated fortress.
- **Lore:** It feeds on the dwarven iron-roses and grows its shell from the clippings. The gardeners call it a pest with tenure.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Thornglass (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The gardens' oldest rootstock has grown a warden — Thornglass, a trellis-shape of obsidian bramble, flowering in small hot lights. Every realm in the beds contributed a thorn. It knows which one is yours, and saves it for last.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 97 — The Kingsway (biome: The Crown, tier 10, gate town: Waygate)

**Landscape:** The processional road to the throne begins here — an avenue of black glass lined with the banners of every realm, hung upside down. Court law says the Kingsway may be walked only in procession. It has waited ninety-six floors for you to break it.

### Herald of precedence (`way_herald`)
- **Size:** at-floor peer (medium) — traits: fierce, magic_resist
- **Description:** A court herald plants its staff in your path with a crack like ice. Processions require rank, and rank requires patents, and you have neither — only, it allows, a certain momentum. It calls the challenge in High Court speech, then translates.
- **Lore:** Processions require rank, and rank requires patents, and you have neither — only, it allows, a certain momentum.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Banner-wraith (`banner_wraith`)
- **Size:** at-floor peer (medium) — traits: feeble, fly
- **Description:** One of the inverted banners unhooks itself and comes down the avenue — the flag of a dead realm flying itself, looking for hands to carry it right side up. Yours are occupied. It intends to free them.
- **Lore:** The flag of a dead realm flying itself, looking for hands to carry it right side up. Yours are occupied. It intends to free them.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kingsway guard (`procession_guard`)
- **Size:** at-floor peer (medium) — traits: savage, armoured
- **Description:** Two archdemons of the road-watch descend from their alcoves in step, glaives crossing with ceremonial precision. They have drilled the arrest of an unauthorized walker every day for a thousand years. You can tell.
- **Lore:** They have drilled the arrest of an unauthorized walker every day for a thousand years. You can tell — and the plate has drilled with them.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Kingsway hound (`kingsway_hound`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** From an alcove a hound in road-watch livery takes the avenue's black glass at a sprint that never slips, and its line ends precisely where you are standing.
- **Lore:** The road-watch runs hounds down the avenue between processions. Unauthorized walkers are their whole diet.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Waymarshal (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The Kingsway's marshal has organized every procession the Crown ever held, and it receives your one-person parade with professional interest. Waymarshal draws a baton of black glass, taps the road twice for order, and the whole avenue falls in behind it.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 98 — The Dueling Floor (biome: The Crown, tier 10, gate town: Measure)

**Landscape:** The court settles everything here, on a floor of black glass scored with a thousand years of measured paces. The galleries are full — word of you has climbed faster than you have. Tonight's card was cleared by royal order. The court has bet heavily anyway.

### Champion of the lower court (`lower_court_champion`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** The lower court's champion steps onto the glass and salutes the royal box first, you second — protocol, and also a tell. It fights for an audience of one, and it has never once been allowed to lose.
- **Lore:** It salutes the royal box first, you second — protocol, and also a tell. It has never once been allowed to lose.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The arbiter (`blood_arbiter`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** The dueling floor's arbiter descends in robes of chainmail silk to review your standing. It finds no patents, no second, no grave-plot reserved — irregular. The penalty for irregularity is assessed in the traditional currency, on the spot.
- **Lore:** No patents, no second, no grave-plot reserved — irregular. The penalty is assessed in the traditional currency, on the spot.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### A settled wager (`gallery_wager`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** Two archdemons in the gallery have bet on how far you get, and one of them has just realized it stands to lose a province. It comes over the rail mid-argument, resolving to adjust the outcome personally.
- **Lore:** It stands to lose a province on how far you get, and it has come over the rail to adjust the outcome personally.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Chalk page (`chalk_page`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage
- **Description:** A page crouched at the floor's edge finishes chalking your measure, checks it twice against your reach, and takes up its scoring-iron to defend the accuracy of the line.
- **Lore:** It scores the measures into the glass before every duel. The floor's thousand years of lines are its one work.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Fairpoint (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The floor's own warden fights every challenger whose paperwork survives — Fairpoint, a fencer of black glass with a blade grown from its arm, correct to the last inch of the measure. It offers you the salute it has offered a thousand dead duelists.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 99 — The Last Door (biome: The Crown, tier 10, gate town: Thresholme)

**Landscape:** One floor remains, and it is mostly door — the King's own, tall enough that clouds form against it. Before it camps the court's conscience — all the demons who came this far meaning to knock, and did not. They watch you cross their camp in silence.

### Knight of the threshold camp (`doubting_knight`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** An archdemon knight who camped here a century ago rather than knock stands up from its fire. If you knock, its hundred years of not-knocking become cowardice. It cannot allow the redefinition. It is almost apologetic about the logic.
- **Lore:** If you knock, its hundred years of not-knocking become cowardice. It cannot allow the redefinition. The plate has camped as long as the doubt.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The last tempter (`last_tempter`)
- **Size:** at-floor peer (medium) — traits: feeble, magic_resist
- **Description:** A silk-voiced demon falls in beside you with the Crown's final offer: everything below floor ninety-nine, governorship, history rewritten in your favor. The offer is genuine. That is the trap — there is nothing dishonest to push against.
- **Lore:** The offer is genuine. That is the trap — there is nothing dishonest to push against, and spells find nothing dishonest to bite.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Acolyte of the door (`door_acolyte`)
- **Size:** lean and quick-ribbed (medium) — traits: lean, feeble
- **Description:** Some of the campers have been here so long they worship the door itself. An acolyte in door-black robes bars your way: the door must not be touched by the unworthy, and its test of worth is administered by hand, immediately.
- **Lore:** The door must not be touched by the unworthy, and its test of worth is administered by hand, immediately.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Threshold raven (`threshold_raven`)
- **Size:** enormous — it fills the path — traits: hulking, fierce, fly
- **Description:** A raven drops from the door's distant hardware and lands between you and the camp, head cocked, delivering a verdict on your chances in one dry syllable, twice.
- **Lore:** It has watched the camp not-knock for a century, and it heckles every new arrival's resolve.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Warden Knocker (warden)
- **Size:** boss — fills the stair-gate
- **Description:** The great door's knocker is a demon bound into the iron — Knocker, a ring of black metal held in a fist the size of a house. Whoever would knock must first take the ring from it. No one ever has. It tells you this with something like hope.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.

## Floor 100 — The Reactor Throne (biome: The Crown, tier 10, gate town: Vigil)

**Landscape:** The throne room is the reactor, and the reactor is the throne — one chamber where the stolen world's weight hangs in chains of light from a single black seat. The court is assembled. The realms watch through every mirror. The King rises to meet you himself.

### The assembled court (`court_assembled`)
- **Size:** small and slight — traits: frail, feeble
- **Description:** The court closes ranks before the dais — archdemons of every rank, silk and plate and grievance, none willing to be seen letting you pass unopposed. They fight the way courts do: all at once, and each hoping the others die doing it.
- **Lore:** They fight the way courts do: all at once, and each hoping the others die doing it.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The King's shadow (`kings_shadow`)
- **Size:** at-floor peer (medium) — traits: feeble, fly
- **Description:** Vharuk's shadow leaves him and comes down the throne-steps alone, wearing the shape he wore the day he tore the first realm out of the earth. It is a younger King, and hungrier, and it does not answer to the one on the throne.
- **Lore:** A younger King, and hungrier, and it does not answer to the one on the throne.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### The living regalia (`crown_regalia`)
- **Size:** at-floor peer (medium) — traits: fierce, armoured
- **Description:** The King's regalia defend themselves — scepter, orb, and chain of office rising off their cushions in a slow orbit. They have outlasted four bearers. They are auditioning the fifth, and the audition is armed.
- **Lore:** Scepter, orb, and chain of office in slow orbit. They have outlasted four bearers and are auditioning the fifth, armed.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Mirror witness (`witness_shade`)
- **Size:** thick through the shoulders (large) — traits: sturdy, savage, magic_resist
- **Description:** A shape presses out of the nearest watching mirror — a witness from some drowned realm, worn thin by the view, determined that whatever happens to the King happens through it first.
- **Lore:** Every conquered realm watches the throne room through its mirrors. One of them could not keep watching quietly.
- **Origin:** untagged (pre-038 floor) — defaults to Native per world-lore §9; original animal not recorded.

### Vharuk, the Demon King (warden)
- **Size:** boss — fills the stair-gate
- **Description:** Vharuk steps down from the throne and the chamber dims — the tower's heart-light gathering into him like breath drawn before a word. He stole a world and stacked it into a ladder, and you have climbed it to his floor. He is not angry. He is interested.
- **Origin:** Wrongmade — the Wardens are the tower's own manufacture (world-lore §5); made, not infected.
