# 008 band 21-30 — The Barrows. Grave-marsh: resist favored (wights,
# lights, things half out of the world), exo-rig dead carry the armor,
# the peat-cured king is the band's bulwark, ghouls and hounds run.
SPEC = {
    21: {
        "lore": {
            "mire_ghoul": (
                "It has eaten better since the tower came than its whole "
                "line ate before it. It sees no reason the run should "
                "end."),
            "bog_hound": (
                "It died loyal to somebody on the old towpath. What runs "
                "it now keeps the route and lost the loyalty."),
            "cairn_wisp": (
                "The locals had one rule about the cairn-lights: never "
                "follow. Nobody made a rule for when the light follows "
                "you."),
        },
        "traits": {
            "bog_hound": ["fast"],
            "cairn_wisp": ["flying", "resist_low"],
        },
        "new": [{
            "id": "mire_leech", "name": "Mire leech", "weight": 2,
            "lore": (
                "The drowned fields feed everything slowly except the "
                "leeches, which have never once been patient."),
            "prose": (
                "The water between two cairns humps and slides — a leech "
                "long as a rowboat, back crusted with old coins that "
                "stuck, homing in on the warmth of you."),
        }],
    },
    22: {
        "lore": {
            "tithe_wight": (
                "The custom is older than the priest: the dead are owed "
                "bread and tin. The bowl has been empty a long time."),
            "barrow_ghoul": (
                "It dug clean through a king's barrow and came out proud, "
                "wearing his torc. Rank, among ghouls, is worn on the "
                "forearm."),
            "grave_beetle": (
                "The old dead fed a whole economy under the turf. Its "
                "shell is the marsh's answer to a shield wall."),
        },
        "traits": {
            "tithe_wight": ["resist_low"],
            "grave_beetle": ["armor_high", "slow"],
        },
        "new": [{
            "id": "barrow_rat", "name": "Barrow rat", "weight": 2,
            "lore": (
                "It lives on offerings and offal, and it has learned that "
                "climbers carry both."),
            "prose": (
                "A rat noses out of a toppled offering-post, sleek on a "
                "century of bread left for the dead, and takes your "
                "arrival for the next delivery."),
        }],
    },
    23: {
        "lore": {
            "pale_stag": (
                "The elves bred it to carry the forest light through the "
                "deep woods. It remembers the weight of it, and hates "
                "you fresh."),
            "glade_wight": (
                "She stayed when the lights died, and the garden kept "
                "her. Spells slide off what is left like rain off wax "
                "leaves."),
            "lamp_ghoul": (
                "It cracks the dead bio-lamps for the marrow of light "
                "inside, and its belly glows faint through the skin."),
        },
        "traits": {
            "pale_stag": ["fast"],
            "glade_wight": ["resist_med"],
        },
        "new": [{
            "id": "lamp_moth", "name": "Lamp moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "When the bio-lights went dark the moths did not leave. "
                "They just got hungrier about what light remains."),
            "prose": (
                "Wings the grey of dead leaves open on a bough above you "
                "— a moth grown huge on lamp-marrow, drawn off its "
                "dark tree by the smallest light you carry."),
        }],
    },
    24: {
        "lore": {
            "rig_wight": (
                "The soldier is dead these many years and still on duty. "
                "The rig keeps the watch; the salute is muscle memory."),
            "marsh_ghoul_crew": (
                "Years of opening exo-rigs like oysters capped its "
                "knuckles with salvaged plate. Your armor reads as "
                "shell."),
            "drowned_light": (
                "The beacon still blinks under a foot of bog water. The "
                "thing beside it learned that light draws rescuers."),
        },
        "traits": {
            "rig_wight": ["armor_med"],
            "marsh_ghoul_crew": ["armor_low"],
            "drowned_light": ["resist_low"],
        },
        "new": [{
            "id": "marsh_adder", "name": "Marsh adder", "weight": 2,
            "lore": (
                "It dens in a flooded rig's chest cavity, which tells "
                "you everything about the neighborhood."),
            "prose": (
                "A black adder pours off a rusted rig's shoulder and "
                "writes a fast line through the bog water toward your "
                "boots, jaw already wide."),
        }],
    },
    25: {
        "lore": {
            "procession_wight": (
                "It has led ten thousand funerals and been short one "
                "mourner for a century. Grief that old stops taking no."),
            "verge_ghoul": (
                "Funerals mean fresh graves; the road taught it that "
                "generations ago. It keeps polite funeral distance until "
                "it doesn't."),
            "bell_wisp": (
                "It rings a passing-bell for the about-to-die. It is "
                "rarely wrong, and it is ringing now."),
        },
        "traits": {
            "procession_wight": ["resist_med"],
            "bell_wisp": ["flying", "resist_low"],
        },
        "new": [{
            "id": "coffin_bearer", "name": "Coffin-bearer", "weight": 2,
            "traits": ["slow", "armor_low"],
            "lore": (
                "Two bearers fused to one iron-bound coffin, still "
                "walking the route. Nobody has looked inside and "
                "reported back."),
            "prose": (
                "Up the center of the road comes a shape of two bearers "
                "grown into one iron-bound coffin, step by processional "
                "step. It sets its burden down. It opens the lid for "
                "you."),
        }],
    },
    26: {
        "lore": {
            "peat_king": (
                "A thousand years in the peat tanned him tough as boat "
                "leather. Every wound closes with a wet brown sound — "
                "outlast him if you can."),
            "cutter_ghoul": (
                "It works the banks with a peat-cutter's blade and a "
                "harvester's patience. You are standing on its next "
                "cut."),
            "turf_hound": (
                "Packed peat and root in the shape of loyalty. Thrown "
                "stones just improve it."),
        },
        "traits": {
            "peat_king": ["bulwark", "slow"],
        },
        "new": [{
            "id": "midge_cloud", "name": "Midge cloud", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "Marsh midges in a swarm dense enough to have opinions. "
                "The cuts breed them by the ton."),
            "prose": (
                "The fog line detaches a piece of itself and hums toward "
                "you — a midge cloud thick enough to blot the cut-banks, "
                "moving with one slow appetite."),
        }],
    },
    27: {
        "lore": {
            "garth_wight": (
                "Little more than vestments and wind, still making its "
                "rounds. The fines are old law, and old law does not "
                "haggle."),
            "yard_ghoul": (
                "With the birds gone the ghouls took over the sky-burial "
                "work. This one is lean, fast, and behind on quota."),
            "bone_heap": (
                "The laid-out dead grew tired of waiting for a sky that "
                "never comes. Together they are patient, and slow, and "
                "many."),
        },
        "traits": {
            "garth_wight": ["resist_med"],
            "yard_ghoul": ["fast"],
            "bone_heap": ["slow"],
        },
        "new": [{
            "id": "picker_rat", "name": "Picker rat", "weight": 2,
            "lore": (
                "The rats do the birds' old work now, badly. The garths "
                "have never been so crowded."),
            "prose": (
                "A rat the size of a terrier works along a burial "
                "platform with a tradesman's confidence, sees you watch, "
                "and takes offense at the audience."),
        }],
    },
    28: {
        "lore": {
            "chantry_wight": (
                "It keeps the offices in a voice like water in a crypt. "
                "The old river gods may even still be listening."),
            "font_ghoul": (
                "It claimed sanctuary in the great font years ago. "
                "Sanctuary, it has decided, does not extend to "
                "visitors."),
            "vigil_light": (
                "A votive flame that outlived its brass boat. Each pew "
                "it passes, something under the water sits up."),
        },
        "traits": {
            "chantry_wight": ["resist_med"],
            "vigil_light": ["flying", "resist_low"],
        },
        "new": [{
            "id": "drowned_congregant", "name": "Drowned congregant",
            "weight": 2, "traits": ["slow"],
            "lore": (
                "The congregation never left the pews when the nave "
                "flooded. Attendance, in fact, has improved."),
            "prose": (
                "A pew shifts and one of the congregation stands up "
                "through the black water, hymnal still in hand, and "
                "wades into the aisle to greet the interruption."),
        }],
    },
    29: {
        "lore": {
            "door_wight": (
                "Set at its stone a thousand years ago to challenge "
                "whatever comes off the moor. The mail rusted; the "
                "orders didn't."),
            "moor_ghoul": (
                "This far in, the ghouls are old and careful and fat on "
                "what leaks through the doors. It can afford to wait."),
            "unsealed_thing": (
                "The old folk went to real trouble sealing it. It is "
                "half out of the world still, and spells reach only the "
                "half that isn't here."),
        },
        "traits": {
            "door_wight": ["armor_med"],
            "unsealed_thing": ["resist_med"],
        },
        "new": [{
            "id": "moor_hound", "name": "Moor hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "It courses the stone rows at night. What it was bred "
                "to keep in, it now keeps company."),
            "prose": (
                "Between two standing stones a hound breaks from a "
                "flat-out run to a stalk — moor-grey, low, and already "
                "closer than the fog said it was."),
        }],
    },
    30: {
        "lore": {
            "kings_herald": (
                "It announces you to the barrow in a note you feel in "
                "your fillings, which is worse than an ambush."),
            "tribute_ghoul": (
                "Dropping the offering would shame it before the King. "
                "It sets the body down carefully, first."),
            "barrow_guard": (
                "Buried in their mail, buried with their rigs. Rust and "
                "bone move as one thing, and the plate remembers its "
                "trade."),
        },
        "traits": {
            "kings_herald": ["resist_low"],
            "barrow_guard": ["armor_med"],
        },
        "new": [{
            "id": "moat_watcher", "name": "Moat watcher", "weight": 2,
            "traits": ["slow"],
            "lore": (
                "A century of tribute sank into the black moat, and "
                "something grew fond of the collection."),
            "prose": (
                "The moat's skin of black water bulges and a watcher "
                "rises draped in sunken tribute — crowns, sword-belts, "
                "rig-plate — wearing the hoard it is about to defend."),
        }],
    },
}
