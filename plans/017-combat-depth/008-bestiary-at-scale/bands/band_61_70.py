# 008 band 61-70 — Stormreach. Open sky: the flyers live here, so
# every floor keeps two grounded full-damage targets for the blade.
# Drakes and the Queen's court carry resist, drake-scale livery and
# rigging crabs carry armor, the hull-borer is the band's bulwark.
SPEC = {
    61: {
        "lore": {
            "cloudline_harpy": (
                "The insults in fluent trade-tongue are a range-finding "
                "exercise. The stoop comes on the punchline."),
            "young_drake": (
                "It has not learned to aim its lightning yet. It does "
                "not especially need to."),
            "rigger_ghast": (
                "It clips its frayed line to your belt with terrible "
                "courtesy. Its ship is down there somewhere, and it "
                "means to introduce you."),
        },
        "traits": {
            "cloudline_harpy": ["flying"],
            "young_drake": ["flying", "resist_low"],
            "rigger_ghast": ["slow"],
        },
        "new": [{
            "id": "cliff_goat", "name": "Cliff goat", "weight": 2,
            "lore": (
                "It holds the trail ledges against all comers, and the "
                "drop has never once been its problem."),
            "prose": (
                "A goat with storm-tattered wool rounds the cliff "
                "corner at a trot, sees you on its ledge, and lowers a "
                "boss of horn worn smooth by better arguments than "
                "yours."),
        }],
    },
    62: {
        "lore": {
            "wreck_harpy": (
                "The clan matriarch wears three captains' coats at "
                "once. Everything on this peak is claimed, including, "
                "as of now, your gear."),
            "hold_drake": (
                "Brooding a clutch on a bed of trade silver — "
                "possessive, charged, and recently a parent."),
            "dead_crew": (
                "They rise in harness and oilskin, moving with the "
                "roll of a deck that stopped rolling years ago."),
        },
        "traits": {
            "wreck_harpy": ["flying"],
            "hold_drake": ["resist_med"],
            "dead_crew": ["slow"],
        },
        "new": [{
            "id": "hull_borer", "name": "Hull borer", "weight": 2,
            "traits": ["bulwark", "slow"],
            "lore": (
                "It ate through the fleet's timber for years and "
                "grew a back of lapped ship-iron doing it. Cutting it "
                "down is a shipwright's job, not a soldier's."),
            "prose": (
                "The keel above you flexes and a borer backs out of "
                "the timber — a grub gone the size of a longboat, "
                "plated in the iron it could not digest, blind and "
                "unbothered and between you and the path."),
        }],
    },
    63: {
        "lore": {
            "rookery_warden_harpy": (
                "You walked under somebody's nest, which is either a "
                "toll or a proposal. She is here to settle which."),
            "fledgling_mob": (
                "Eleven of them, dared to touch you. The arithmetic "
                "of being twelve is the whole of harpy education."),
            "nest_drake": (
                "Penned like a town bull, resented, and prayed to. "
                "The prayers soaked in; spells break against them."),
        },
        "traits": {
            "rookery_warden_harpy": ["flying"],
            "fledgling_mob": ["fast"],
            "nest_drake": ["resist_med"],
        },
        "new": [{
            "id": "rook_marten", "name": "Rook marten", "weight": 2,
            "lore": (
                "It raids the nests for eggs and trinkets, and it has "
                "learned to work while the owners are out on you."),
            "prose": (
                "A marten pours down a nest-pole with somebody's brass "
                "band still in its teeth, hits the path in front of "
                "you, and decides you are between it and the exit."),
        }],
    },
    64: {
        "lore": {
            "chain_harpy": (
                "Flying here is for amateurs, she explains, kicking "
                "your handhold loose to illustrate the point."),
            "link_drake": (
                "Your footsteps carry up the chain like a knock. It "
                "pours down through the links, and it has never "
                "needed a floor."),
            "moss_ghast": (
                "It missed a handhold years ago and still works its "
                "ledge, weightless-thin. The net it waves you toward "
                "is for you."),
        },
        "traits": {
            "link_drake": ["flying", "resist_low"],
            "moss_ghast": ["slow"],
        },
        "new": [{
            "id": "chain_tick", "name": "Chain tick", "weight": 2,
            "traits": ["armor_high", "slow"],
            "lore": (
                "It clamps to the great links and drinks the hum of "
                "the load. Its shell is chain-grade by adoption."),
            "prose": (
                "What you took for a rivet head the size of a shield "
                "unclamps from the link, legs unfolding from under an "
                "iron-grey shell, and crabs down the chain's curve "
                "toward the warm thing crossing its metal."),
        }],
    },
    65: {
        "lore": {
            "updraft_harpy": (
                "Three passes, honor satisfied — the local dueling "
                "form. Nobody has explained what satisfies it."),
            "kite_pirate": (
                "It drops travelers into the valley for the things "
                "below. You are not even attached to a line. Free "
                "lunch."),
            "column_drake": (
                "Asleep on the wind in the updraft's core. Your scent "
                "goes up the column ahead of you."),
        },
        "traits": {
            "updraft_harpy": ["flying"],
            "kite_pirate": ["fast"],
            "column_drake": ["flying", "resist_low"],
        },
        "new": [{
            "id": "pass_boar", "name": "Pass boar", "weight": 2,
            "lore": (
                "The only local that never took the free lift. It "
                "holds the valley floor out of pure principle."),
            "prose": (
                "Under the kite-lines a boar roots the pass gravel, "
                "deaf to the whole sky economy, and takes your "
                "landing on its floor as the day's first trespass."),
        }],
    },
    66: {
        "lore": {
            "shroud_harpy": (
                "She runs the rigging without touching wing to air, "
                "herding you toward the net stretch where the clan "
                "waits."),
            "mast_drake": (
                "Grown into the tallest crow's nest, spars through "
                "the wing membrane. It rings every stay on the way "
                "down."),
            "rigging_ghast": (
                "A topman hanging where his line caught him. The "
                "swinging stops against the wind, and the line starts "
                "paying out."),
        },
        "traits": {
            "shroud_harpy": ["fast"],
            "mast_drake": ["flying", "resist_low"],
            "rigging_ghast": ["slow"],
        },
        "new": [{
            "id": "shroud_crab", "name": "Shroud crab", "weight": 2,
            "traits": ["armor_med", "slow"],
            "lore": (
                "It climbed up from some hold with the fleet and "
                "never left the rigging. The shell has out-lasted "
                "three hulls."),
            "prose": (
                "A crab the size of a capstan picks its way down a "
                "shroud on point-tipped legs, shell barnacled with "
                "brass, and drops the last fathom onto the path with "
                "a sound like a dropped anchor."),
        }],
    },
    67: {
        "lore": {
            "charge_harpy": (
                "She takes the strike across her banded feathers like "
                "applause. Spark-drunk, several strikes in, and "
                "spells just read as more applause."),
            "field_drake": (
                "Hatched on this moor and never left — why would it. "
                "Every pole it passes fires in salute."),
            "stone_mover": (
                "The thing that moves the white lane-stones. Under "
                "the hood is old lightning, coiled and patient. It "
                "has been farming climbers."),
        },
        "traits": {
            "charge_harpy": ["flying", "resist_med"],
            "stone_mover": ["slow", "resist_med"],
        },
        "new": [{
            "id": "copper_rat", "name": "Copper rat", "weight": 2,
            "lore": (
                "It gnaws the pole-farm's wiring for the taste and "
                "has been struck more times than the poles."),
            "prose": (
                "A rat with a coat gone verdigris-green works the base "
                "of a singing pole, whiskers smoking faintly, and "
                "breaks off its meal to defend the whole grid from "
                "you."),
        }],
    },
    68: {
        "lore": {
            "aerie_drake": (
                "Young enough to want a story worth telling, old "
                "enough to make one out of you."),
            "drake_harrier": (
                "Drake-scale livery and airs to match. Removing you "
                "before the master wakes is the kind of initiative "
                "that gets noticed."),
            "old_tyrant": (
                "Beaten off its crag, wings scarred, charge gone "
                "grey. It has nothing left but seniority, and it "
                "means to spend it on you."),
        },
        "traits": {
            "aerie_drake": ["flying", "resist_low"],
            "drake_harrier": ["armor_med"],
            "old_tyrant": ["slow"],
        },
        "new": [{
            "id": "hoard_lizard", "name": "Hoard lizard", "weight": 2,
            "lore": (
                "It lives in the aeries' wreck-metal hoards and "
                "defends them harder than the owners do."),
            "prose": (
                "A lizard long as a skiff slides off a heap of "
                "charge-blackened salvage, tongue reading the air, "
                "and squares up over the hoard like a creditor at a "
                "will-reading."),
        }],
    },
    69: {
        "lore": {
            "wall_sentinel": (
                "One of the Queen's own watch, half weather itself. "
                "It does not roar; thunder does that for it, on cue."),
            "lull_harpy": (
                "Her Majesty knows you are here. What remains to be "
                "decided is the manner of your arrival — walking, or "
                "delivered."),
            "pressure_ghast": (
                "A climber the storm took, worn down to a pressure "
                "change with a grudge. Your lungs notice it before "
                "your eyes do."),
        },
        "traits": {
            "wall_sentinel": ["flying", "resist_med"],
            "pressure_ghast": ["resist_med"],
        },
        "new": [{
            "id": "rain_hound", "name": "Rain hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "The Queen kennels the squalls that behave. This one "
                "behaves right up until the leash comes off."),
            "prose": (
                "A hound made of moving rain slips the eye-wall and "
                "crosses the Lull at a sprint, its paws printing wet "
                "on dry stone, gone and arrived in the same breath."),
        }],
    },
    70: {
        "lore": {
            "court_champion": (
                "It fights before the throne, which means it fights "
                "beautifully, which does not mean it fights fair."),
            "livery_harpy": (
                "Protocol requires all challengers to arrive "
                "bleeding. The court dislikes ambiguity; the pike and "
                "the plate remove it."),
            "bottled_gale": (
                "Bottled since the fleet fell, dropped the way courts "
                "do accidents. It holds you personally responsible."),
        },
        "traits": {
            "court_champion": ["flying", "resist_med"],
            "livery_harpy": ["armor_med"],
            "bottled_gale": ["fast", "resist_low"],
        },
        "new": [{
            "id": "perch_squire", "name": "Perch squire", "weight": 2,
            "lore": (
                "A groom of the court perches, armed with the "
                "champion's second-best gorget and none of its "
                "patience."),
            "prose": (
                "A young harpy in half-livery vaults the perch rail "
                "with the champion's spare gorget banging on its "
                "chest, determined to be noticed doing something "
                "about you."),
        }],
    },
}
