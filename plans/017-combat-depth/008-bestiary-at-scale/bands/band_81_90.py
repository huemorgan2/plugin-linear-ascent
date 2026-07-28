# 008 band 81-90 — Hellmarch. The King's iron: hellknights and hulks
# carry the March's plate (the first armor_high lives on the Herald's
# honor guard), imps carry the speed, priests and secretaries the
# resist, and the parade and gate hulks are the bulwarks.
SPEC = {
    81: {
        "lore": {
            "outwork_imp": (
                "Maintenance doubles as sentry duty out here. It "
                "reports you with the rivet gun."),
            "gate_knight": (
                "Armor welded shut a lifetime ago, engine-heart idling "
                "up through the plate. The halberd is part of the "
                "arm."),
            "wall_growth": (
                "The outwork's living mortar. The wall behind it heals "
                "over before it has crossed half the distance."),
        },
        "traits": {
            "outwork_imp": ["fast"],
            "gate_knight": ["armor_med"],
            "wall_growth": ["slow"],
        },
        "new": [{
            "id": "outwork_crow", "name": "Outwork crow", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "Iron walls still feed crows. The gun-slits breathe "
                "out, and something always rides the warm draft."),
            "prose": (
                "A crow with soot-slicked feathers lifts off a "
                "gun-slit's lip, rides the wall's warm exhalation "
                "over your head, and calls you in to whatever keeps "
                "the ledger inside."),
        }],
    },
    82: {
        "lore": {
            "chain_imp_gang": (
                "The foreman has spotted a way to lighten the load — "
                "you look sturdy, and the harness is adjustable."),
            "quench_knight": (
                "Fresh from tempering, issued nothing yet but the "
                "need to test itself."),
            "loose_chain": (
                "The forge puts a little of the fire into everything "
                "it makes. This one got a temper."),
        },
        "traits": {
            "chain_imp_gang": ["fast"],
            "quench_knight": ["armor_med"],
            "loose_chain": ["slow"],
        },
        "new": [{
            "id": "pit_eel", "name": "Quench-pit eel", "weight": 2,
            "traits": ["resist_low"],
            "lore": (
                "It swims the black oil between temperings and eats "
                "what the quench rejects. Spellwork slicks off it "
                "with the oil."),
            "prose": (
                "The quench-pit's skin of oil parts without a sound "
                "and an eel pours itself over the lip, black on "
                "black, tasting the yard-floor heat for the shape of "
                "you."),
        }],
    },
    83: {
        "lore": {
            "stoker_imp": (
                "The furnace is running lean, the schedule says feed "
                "it, and you are standing on the hatch — which "
                "counts as volunteering."),
            "road_knight": (
                "It patrols the grate barefoot, soles glowing dull "
                "red. Heat discipline is a point of pride, and it "
                "means to teach the standard."),
            "grate_thing": (
                "It lives between the furnaces, eating what the "
                "chutes deliver. It has learned the sound of "
                "footsteps stopping, and spells cook off before they "
                "reach it."),
        },
        "traits": {
            "stoker_imp": ["fast"],
            "road_knight": ["armor_med"],
            "grate_thing": ["resist_med"],
        },
        "new": [{
            "id": "cinder_swift", "name": "Cinder swift", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It nests in the road grating and hunts the updraft. "
                "Nothing else on the March flies this low on "
                "purpose."),
            "prose": (
                "A swift snaps up out of the channel-light between "
                "two grates, wings trailing threads of smoke, and "
                "carves a hot circle around your head, herding you "
                "off its nesting run."),
        }],
    },
    84: {
        "lore": {
            "seam_imp": (
                "It taps you twice, frowns at the sound of unmodified "
                "meat, and flags you for the gantries."),
            "fresh_welded": (
                "It does not know its own name yet. It knows its "
                "function, and its function is walking toward you."),
            "rejected_lot": (
                "The failures have organized — wrong joints, extra "
                "arms, grievances in writing."),
        },
        "traits": {
            "seam_imp": ["fast"],
            "fresh_welded": ["armor_med"],
            "rejected_lot": ["slow"],
        },
        "new": [{
            "id": "arc_moth", "name": "Arc moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It drinks the welding light. The gantry crews bill "
                "the King for what it costs them in torches."),
            "prose": (
                "A moth with wings like smoked mica detaches from a "
                "gantry lamp and beats down the line toward the "
                "brightest thing on the floor, which — between "
                "arcs — is your lamp."),
        }],
    },
    85: {
        "lore": {
            "warren_tough": (
                "A glandular marvel, the locals say. You are new "
                "custom, walking unprotected."),
            "press_gang": (
                "The Welding Halls pay a bounty per body, and yours "
                "is worth a month of quota. It is nothing personal. "
                "It is documented."),
            "slumlord_knight": (
                "Retired into the warrens, rent collected in teeth. "
                "It is sure beyond argument that you owe it "
                "something."),
        },
        "traits": {
            "press_gang": ["fast"],
            "slumlord_knight": ["armor_med"],
        },
        "new": [{
            "id": "flue_bat", "name": "Flue bat", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "A million chimneys, one bat per flue. The warrens "
                "sell the guano and lose the arguments."),
            "prose": (
                "Something drops out of the nearest flue-pipe in a "
                "puff of soot and takes the alley at head height — a "
                "bat fat on market scraps, indignant that the "
                "airspace is occupied."),
        }],
    },
    86: {
        "lore": {
            "drill_knight": (
                "It has rehearsed this fight so long it starts with "
                "your counter."),
            "bastion_imp_crew": (
                "Their record on moving targets is chalked on the "
                "wall. It is embarrassing, and they know you can "
                "read it."),
            "parade_hulk": (
                "Polished for parades, at attention for a decade, "
                "waiting for an order worth having. Your arrival is "
                "an order — and it was built to be impossible to "
                "stop."),
        },
        "traits": {
            "drill_knight": ["armor_high"],
            "parade_hulk": ["bulwark", "slow"],
        },
        "new": [{
            "id": "rampart_falcon", "name": "Rampart falcon", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "The garrisons fly messages between bastions. The "
                "falcons have standing orders about interceptors."),
            "prose": (
                "A falcon in a message-harness checks its line "
                "between bastions, folds, and stoops at you instead "
                "— the standing orders, it turns out, define "
                "interceptor generously."),
        }, {
            "id": "sally_hound", "name": "Sally hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "Kenneled at the sally ports and fed on drill-square "
                "mistakes. It knows the gap in every formation."),
            "prose": (
                "A sally port cracks and a hound comes through it "
                "flat and silent, taking the drill square's diagonal "
                "— the one line no formation covers — straight to "
                "you."),
        }],
    },
    87: {
        "lore": {
            "gardener_imp": (
                "Contamination of the beds is the one sin the head "
                "gardener flogs for, and you are tracking in pollen "
                "from ninety floors of elsewhere."),
            "unripe_engine": (
                "Green, unbalanced, and eager — a colt with a "
                "battering head, ruining the rows to reach you."),
            "scarecrow_knight": (
                "The gardeners forgot to tell it the war it fell in "
                "is over. It comes off the frame with the nails "
                "still in."),
        },
        "traits": {
            "gardener_imp": ["fast"],
            "scarecrow_knight": ["armor_high", "slow"],
        },
        "new": [{
            "id": "carrion_kite", "name": "Carrion kite", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "What the scarecrow is for. It has been testing the "
                "scarecrow's patience for years, and yours looks "
                "shorter."),
            "prose": (
                "A kite wheels down off the trellis-rows where the "
                "scarecrow cannot reach, bone-meal dust in its "
                "primaries, and makes its approach run at the softest "
                "thing in the garden."),
        }],
    },
    88: {
        "lore": {
            "furnace_priest": (
                "It has preached your arrival for years and would "
                "hate to waste the congregation. The litany turns "
                "spellwork back like heat off a firebox."),
            "choir_imp": (
                "Heresy duty is the only part of the liturgy they "
                "enjoy, and you are unmistakably not in the hymnal."),
            "penitent_knight": (
                "Chained to the pew by its own request. Absolution, "
                "in the March, is worked off in single combat."),
        },
        "traits": {
            "furnace_priest": ["resist_med"],
            "choir_imp": ["fast"],
            "penitent_knight": ["armor_med"],
        },
        "new": [{
            "id": "smoke_haunt", "name": "Censer haunt", "weight": 2,
            "traits": ["flying", "resist_low"],
            "lore": (
                "Enough coal-smoke has been swung at the King's name "
                "that some of it stayed to listen."),
            "prose": (
                "The censer-smoke over the nave stops rising and "
                "starts deciding — a haunt of grey coils drifting "
                "down the aisle toward you, keeping liturgical "
                "time."),
        }],
    },
    89: {
        "lore": {
            "honor_knight": (
                "Nine climbers' names recited as introduction and "
                "warning. The speech-runed plate has turned "
                "everything they tried."),
            "banner_imp": (
                "It refuses, absolutely, to set the banner down — "
                "the banner is the post."),
            "voice_hulk": (
                "The proclamation is your death notice, read in "
                "advance, at a volume that loosens rivets."),
        },
        "traits": {
            "honor_knight": ["armor_high"],
            "voice_hulk": ["slow"],
        },
        "new": [{
            "id": "horn_bat", "name": "Horn bat", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It roosts in the proclamation horns between "
                "readings. The readings have made it deaf and "
                "fearless."),
            "prose": (
                "When the horns fall silent a bat spills out of the "
                "largest bell-mouth, flying by memory instead of "
                "ear, and its memory says the road belongs to the "
                "horns."),
        }],
    },
    90: {
        "lore": {
            "marshal_knight": (
                "Presenting the Herald with your head might be worth "
                "the flogging. It has done the arithmetic, visibly, "
                "and closed the ledger."),
            "herald_imp": (
                "Fat and precise on state secrets, carrying a "
                "pre-signed writ of execution. Spells blur against "
                "what it knows and will not say."),
            "gate_hulk": (
                "One duty and no discretion — nothing passes while "
                "the Herald holds court. It has the patience and the "
                "build of architecture."),
        },
        "traits": {
            "marshal_knight": ["armor_high"],
            "herald_imp": ["resist_med"],
            "gate_hulk": ["bulwark", "slow"],
        },
        "new": [{
            "id": "muster_hound", "name": "Muster hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "It runs the parade ground's edge at every muster. "
                "Dismissing the guard did not dismiss the dog."),
            "prose": (
                "A hound in a studded muster-collar breaks from the "
                "reviewing line's shadow, taking the parade ground "
                "in a flat arc that ends, by old training, at the "
                "throat of whatever stands where you are standing."),
        }, {
            "id": "drummer_imp", "name": "Drummer imp", "weight": 2,
            "lore": (
                "The muster-beat must be kept while the gate stands. "
                "Nobody told it the muster was over."),
            "prose": (
                "One imp on the empty parade ground keeps the "
                "muster-beat on a drum of gate-iron, eyes shut, "
                "and when your footfall breaks its rhythm it opens "
                "them on you like a grievance."),
        }],
    },
}
