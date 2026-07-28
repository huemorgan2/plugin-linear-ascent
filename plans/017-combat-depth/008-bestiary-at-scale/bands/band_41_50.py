# 008 band 41-50 — The Scorch. Ash desert over a broken reactor:
# salamanders and fire-things carry resist (the first resist_high on
# 47's colorless flame), lead-cloaked and scale-plated ogres carry
# armor, the terrace-keeper is the bulwark, and the sky has wings.
SPEC = {
    41: {
        "lore": {
            "ash_salamander": (
                "It swims the ash the way fish swim water, and heat "
                "rolls off it in welcome. Fire is where it lives; "
                "spells of it are a compliment."),
            "dune_ogre": (
                "Skin baked to crockery, patience baked harder. Your "
                "water skin became community property on sight."),
            "ash_vulture": (
                "It roosts on the warm vents and has gone strange with "
                "it. A polite landing distance, out here, is a "
                "diagnosis."),
        },
        "traits": {
            "ash_salamander": ["resist_low"],
            "dune_ogre": ["slow"],
            "ash_vulture": ["flying"],
        },
        "new": [{
            "id": "ashline_jackal", "name": "Ashline jackal", "weight": 2,
            "lore": (
                "It works the line between the wells and the waste, "
                "living off what turns back too late."),
            "prose": (
                "A jackal the grey of the ash it walks steps out of "
                "your own heat-shimmer, close enough to have counted "
                "your steps for a while, and stops pretending to be "
                "shimmer."),
        }],
    },
    42: {
        "lore": {
            "glass_salamander": (
                "It suns itself under a yard of black glass like a fish "
                "under ice. The fresh cracks are how it says it has "
                "seen you."),
            "shard_ogre": (
                "Its hands are past scarring and its hide has gone the "
                "way of its hands. Setting the hammer down is not an "
                "improvement."),
            "mirage_wisp": (
                "The heat makes shapes, and this one stopped obeying "
                "the wind. Spells warp around it like more heat."),
        },
        "traits": {
            "glass_salamander": ["resist_low"],
            "shard_ogre": ["armor_low"],
            "mirage_wisp": ["resist_med"],
        },
        "new": [{
            "id": "flat_skitter", "name": "Flat-skitter", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "A lizard that hunts on the singing glass, faster than "
                "the cracks it causes."),
            "prose": (
                "Something crosses the flats toward you in a sound like "
                "a struck wineglass — a lizard low to the glass, legs a "
                "blur, riding its own noise in past your guard."),
        }],
    },
    43: {
        "lore": {
            "slag_salamander": (
                "Denned in a red seam, fat on the heat, scales gone the "
                "color of cooling iron. Annoyed is most of the way to "
                "violence."),
            "ridge_ogre": (
                "It struck a good seam and claimed the hill with one "
                "bellow. The claim, as it understands things, includes "
                "you."),
            "clinker_hound": (
                "It cools as it comes, and by arrival it is hard as a "
                "bell. It knows this. It is not hurrying."),
        },
        "traits": {
            "slag_salamander": ["resist_low"],
            "clinker_hound": ["armor_high", "slow"],
        },
        "new": [{
            "id": "cinder_bat", "name": "Cinder bat", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It dens in the warm hills with everything else big "
                "enough to matter, and hunts the ridge roads by heat."),
            "prose": (
                "Off the glowing cut-face a bat unfolds, wings edged in "
                "ember-light, and banks down the ridge road at head "
                "height — yours."),
        }],
    },
    44: {
        "lore": {
            "vent_salamander": (
                "It rides the vent-blasts for sport and lands loose and "
                "easy, the way of an animal that has never once been "
                "cold."),
            "steam_ogre": (
                "A vent caught it, bright pink down one side and in a "
                "mood. Somebody is to blame, and you are available."),
            "ash_wyrmling": (
                "A long way from the Cindermouth nest, wings still wet "
                "— exactly as dangerous as a lost child with a furnace "
                "in it."),
        },
        "traits": {
            "vent_salamander": ["fast"],
            "ash_wyrmling": ["flying", "resist_low"],
        },
        "new": [{
            "id": "vent_crab", "name": "Vent crab", "weight": 2,
            "traits": ["armor_med", "slow"],
            "lore": (
                "It grew its shell against the eruption schedule. "
                "Nothing on that schedule was ever in a hurry."),
            "prose": (
                "A crab wide as a cart squats over a breathing vent, "
                "shell fumed black, and sidles into your path with the "
                "unbothered weight of a thing the desert boils daily."),
        }],
    },
    45: {
        "lore": {
            "step_warden_ogre": (
                "The terrace is its charge and the kiln is its clock. "
                "It does not tire, it does not move fast, and it does "
                "not need to — the fire does the waiting."),
            "kiln_salamander": (
                "Somebody's prize mouser, collared in copper, sleek "
                "with heat, and off its rope. Spells break on it like "
                "spray on a kiln door."),
            "firebreak_vulture": (
                "It is working out why the fire died and whether the "
                "answer is edible. Its head keeps you in view all the "
                "way around."),
        },
        "traits": {
            "step_warden_ogre": ["bulwark", "slow"],
            "kiln_salamander": ["resist_med"],
            "firebreak_vulture": ["flying"],
        },
        "new": [{
            "id": "kiln_goat", "name": "Kiln goat", "weight": 2,
            "lore": (
                "The clans keep goats on the terraces for milk and "
                "temper. Mostly temper."),
            "prose": (
                "A goat with singed horns and a chewed copper collar "
                "takes the terrace steps in two jumps and lowers its "
                "head — the clans breed them mean, and this one is off "
                "the tether."),
        }],
    },
    46: {
        "lore": {
            "dune_swimmer": (
                "The wake comes first, quick as a skipped stone. The "
                "breach comes last, jaws open, gloriously happy."),
            "ember_ogre": (
                "Blind from staring into too many years of ember-glow. "
                "It navigates by smell now, and it has found yours."),
            "glow_moth_swarm": (
                "Each one carries a live cinder in its belly, drawn to "
                "anything warmer than the desert. You qualify."),
        },
        "traits": {
            "dune_swimmer": ["fast"],
            "glow_moth_swarm": ["flying"],
        },
        "new": [{
            "id": "dune_adder", "name": "Dune adder", "weight": 2,
            "lore": (
                "It hunts the glowing dune faces at night, striking at "
                "whatever blocks the light."),
            "prose": (
                "Between two slow bands of dune-glow a length of "
                "shadow uncoils — an adder the color of cold cinder, "
                "head up, reading the heat of you against the orange."),
        }],
    },
    47: {
        "lore": {
            "scar_salamander": (
                "The canyon nests come out changed — translucent, "
                "bright inside, wrong in the joints. Its shadow runs a "
                "half-second behind."),
            "canyon_ogre": (
                "Cloaked head to foot in hammered lead sheeting. It has "
                "stayed alive by tolerating no visitors, and its "
                "record is unbroken."),
            "pale_fire": (
                "A flame with no color and no fuel, casting shadows in "
                "the wrong directions. Spells go into it and do not "
                "come out."),
        },
        "traits": {
            "scar_salamander": ["resist_high"],  # 010: was resist_med — felt by 0.05x drag only
            "canyon_ogre": ["armor_med"],
            "pale_fire": ["resist_high"],
        },
        "new": [{
            "id": "scar_rat", "name": "Scar rat", "weight": 2,
            "lore": (
                "Everything in the canyon is a little wrong, and the "
                "rats are wrong in the direction of bigger."),
            "prose": (
                "A rat comes up the lead-lined path with patchy fur "
                "and too many teeth, dragging a hind leg that has "
                "healed twice its size, entirely unafraid of the "
                "light."),
        }],
    },
    48: {
        "lore": {
            "char_salamander": (
                "It hunts by holding still against the trunks and "
                "being, briefly, the wrong tree."),
            "rooter_ogre": (
                "It rips stumps with no rope and no wedge, only "
                "opinion. The opinion transfers."),
            "standing_dead": (
                "It has stood in the row long enough to fool the "
                "birds. Burned wood does not hurry, and does not "
                "bruise."),
        },
        "traits": {
            "char_salamander": ["resist_low"],
            "standing_dead": ["slow", "armor_low"],
        },
        "new": [{
            "id": "soot_owl", "name": "Soot owl", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It nests in the hollow trunks and hunts the organ-note "
                "wind. Silent, except for the forest holding its "
                "breath."),
            "prose": (
                "The low pipe-note of the wind cuts off — an owl the "
                "color of burned paper is already over you, wings "
                "spread wider than the trunks it slipped between."),
        }],
    },
    49: {
        "lore": {
            "road_wyrmling": (
                "It practices its glide down the melted channel. It "
                "bowls into you more than it attacks you, but it "
                "weighs what a boat weighs, and it is teething."),
            "scale_picker": (
                "The scale trade made it rich by ogre standards, and it "
                "wears its stock — shed wyrm-plate lapped like roof "
                "tiles. Rich things hire fewer witnesses."),
            "molt_salamander": (
                "Glutted on shed skin: gleaming, slow — right up until "
                "it is none of those things."),
        },
        "traits": {
            "road_wyrmling": ["flying"],
            "scale_picker": ["armor_med"],
            "molt_salamander": ["slow", "resist_low"],
        },
        "new": [{
            "id": "glass_hare", "name": "Glass hare", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "It runs the polished channel for the speed of it, and "
                "it has learned to use climbers as corner-posts."),
            "prose": (
                "Something small takes the melted channel at a speed "
                "that should not corner — a hare with glass-worn claws, "
                "banking off the banks, using you as the next turn."),
        }],
    },
    50: {
        "lore": {
            "nest_wyrmling": (
                "The runt of the nest, barge-sized, with a runt's "
                "temper about visitors. The word runt is doing heavy "
                "work."),
            "rim_ogre": (
                "The clan hauls tribute to keep the wyrm off their "
                "terraces. The wagon shed a wheel; you are lighter "
                "than the wagon."),
            "caldera_salamander": (
                "In the nest's shadow they grow to the size of oxen "
                "and fear nothing that walks. The turning is the whole "
                "announcement."),
        },
        "traits": {
            "nest_wyrmling": ["flying", "resist_low"],
            "caldera_salamander": ["resist_med"],
        },
        "new": [{
            "id": "rim_jackal", "name": "Rim jackal", "weight": 2,
            "lore": (
                "It works the tribute-road for what falls off the "
                "wagons, and climbers count as falling off."),
            "prose": (
                "A jackal picks along the caldera rim between "
                "half-melted offerings, lean and businesslike, and "
                "cuts your line of march with the confidence of a "
                "toll-keeper."),
        }],
    },
}
