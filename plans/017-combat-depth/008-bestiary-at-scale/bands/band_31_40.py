# 008 band 31-40 — Webdeep. Cave-dark and silk: spiders bring speed,
# trolls bring bulk (both bulwarks live here), the wired dead and
# charge-fed things carry resist, and the flyers are moths and lights.
SPEC = {
    31: {
        "lore": {
            "cave_broodling": (
                "It has a thousand siblings audible above, and every one "
                "of them learned to drop before it learned to walk."),
            "silk_husk": (
                "The struggling cocoon is the lure. The floor under it "
                "is not floor, and it has all day."),
            "blind_moth": (
                "Harmless itself — but what hunts by the dust it sheds "
                "is not, and the moth knows exactly whom to lead it "
                "to."),
        },
        "traits": {
            "cave_broodling": ["fast"],
            "silk_husk": ["slow"],
            "blind_moth": ["flying"],
        },
        "new": [{
            "id": "threshold_beetle", "name": "Threshold beetle",
            "weight": 2,
            "lore": (
                "It cleans the webs of whatever the spiders leave, and "
                "it has stopped waiting for them to finish."),
            "prose": (
                "A beetle the size of a hound works along the base of "
                "the first webs, jaws crunching through old husks, and "
                "swings its lamp-bright eyes up at the fresher thing "
                "walking in."),
        }],
    },
    32: {
        "lore": {
            "wire_weaver": (
                "Its web is half copper and carries a charge. The flies "
                "die before they finish landing; climbers take a moment "
                "longer."),
            "cable_troll": (
                "It wears a chewed trunk cable like a stole, and the "
                "leakage has done things to its temper the dark never "
                "managed."),
            "sparked_husk": (
                "It twitches in time with the current that keeps it. "
                "Cut the web and it just twitches toward you instead."),
        },
        "traits": {
            "wire_weaver": ["resist_low"],
            "cable_troll": ["slow", "armor_low"],
        },
        "new": [{
            "id": "charge_wisp", "name": "Charge-wisp", "weight": 2,
            "traits": ["flying", "resist_med"],
            "lore": (
                "Leakage that pooled long enough to want things. Spells "
                "feed it more than they hurt it."),
            "prose": (
                "A bead of St. Elmo's light detaches from a cable joint "
                "and drifts down the aisle of webs toward you, swelling "
                "as it comes, the copper silk chiming under it."),
        }],
    },
    33: {
        "lore": {
            "brood_swarm": (
                "Forty small spiders with one opinion. They have never "
                "once been individually."),
            "warren_troll": (
                "Silk-blinded and kept as a nursery guard, fed just "
                "enough. It fills the tunnel wall to wall — you will "
                "not go around it, only through."),
            "midwife_spider": (
                "It turns each egg-sac with terrible gentleness, and it "
                "put itself between you and the clutch before you "
                "decided anything."),
        },
        "traits": {
            "brood_swarm": ["fast"],
            "warren_troll": ["bulwark", "slow"],
        },
        "new": [{
            "id": "warren_bat", "name": "Warren bat", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It nests in the one warm cavern of the Webdeep and "
                "pays rent in whatever it knocks from the air."),
            "prose": (
                "Something leathery cuts through the milk-warm air of "
                "the warrens, shoulder-high and fast, riding the heat "
                "off the brood walls straight at your lamp."),
        }],
    },
    34: {
        "lore": {
            "delving_troll": (
                "You are standing on its spoil-heap. This is, by troll "
                "law, the whole of the case against you."),
            "troll_whelp": (
                "It has just learned that soft things dig easier, and "
                "you are the softest thing it has seen all week."),
            "gallery_spider": (
                "It follows the troll digs the way gulls follow a plow, "
                "and it keeps to the ceiling seam, patient as "
                "arithmetic."),
        },
        "traits": {
            "delving_troll": ["armor_low"],
        },
        "new": [{
            "id": "rubble_borer", "name": "Rubble borer", "weight": 2,
            "traits": ["armor_high", "slow"],
            "lore": (
                "A chitin engine the trolls' digging woke. It eats "
                "stone; everything else it bores through on "
                "principle."),
            "prose": (
                "The spoil-heap shifts and a borer surfaces — a segmented "
                "thing in plates of polished basalt, mouthparts turning "
                "like a drill-head as it corrects course toward you."),
        }],
    },
    35: {
        "lore": {
            "rack_spider": (
                "It webbed a whole engine-rack into its nest and grew "
                "strange on the warmth. Its eyes reflect your lamp in "
                "rows, like little status lights."),
            "signal_husk": (
                "The engines have been using it. It walks with a purpose "
                "nothing dead should have, and spells blur against "
                "whatever is being computed inside."),
            "heat_troll": (
                "It sleeps pressed to the warmest rack like a cat "
                "against a stove. Your footstep landed wrong."),
        },
        "traits": {
            "rack_spider": ["resist_low"],
            "signal_husk": ["resist_med"],
            "heat_troll": ["slow"],
        },
        "new": [{
            "id": "aisle_runner", "name": "Aisle-runner", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "Bred lean by generations of hunting the warm aisles. "
                "The racks light up as it passes, row by row."),
            "prose": (
                "Down the long aisle every rack flickers in sequence, "
                "faster and faster — and then the spider making them "
                "flicker is already at your knee, all legs and "
                "momentum."),
        }],
    },
    36: {
        "lore": {
            "bridge_weaver": (
                "It is not repairing the bridge you are standing on. It "
                "is adjusting the load rating."),
            "city_husk": (
                "Arranged at a silk window with care, one arm raised. "
                "As you pass, the arm finishes the gesture."),
            "chasm_troll": (
                "Too heavy for any street, it climbs the city's "
                "underside, tearing handholds in other people's "
                "architecture."),
        },
        "traits": {
            "city_husk": ["slow"],
            "chasm_troll": ["armor_low"],
        },
        "new": [{
            "id": "silk_drifter", "name": "Silk drifter", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It balloons between the silk towers on threads of its "
                "own casting, and it boards passing climbers like "
                "cargo."),
            "prose": (
                "Above the swaying street a small shape casts a thread "
                "to the wind that does not blow, and rides it down "
                "toward your shoulders with the confidence of long "
                "practice."),
        }],
    },
    37: {
        "lore": {
            "trapdoor_spider": (
                "Mostly forelegs, faster than an apology. The hole it "
                "drags toward is exactly your size."),
            "sprung_husk": (
                "A trap that fired and lost, still fighting the fight "
                "it remembers. It gets up when you edge past."),
            "field_troll": (
                "It crosses the fields by memory, sure as a dancer, and "
                "it does not like sharing the route map."),
        },
        "traits": {
            "trapdoor_spider": ["fast"],
            "field_troll": ["armor_low"],
        },
        "new": [{
            "id": "dust_moth", "name": "Dust moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It powders the trapdoor lids to match the stone. The "
                "spiders tolerate it the way farmers tolerate crows."),
            "prose": (
                "A moth works low over the field ahead of you, dusting "
                "each silk hinge grey — then rises at your lamp, wings "
                "shedding the same dust across your eyes."),
        }],
    },
    38: {
        "lore": {
            "vault_keeper": (
                "It counts by touch, bundle by bundle. You are "
                "unlabeled, unwrapped, unaccounted for — an error it "
                "was made to correct."),
            "fresh_bundle": (
                "Still warm and very determined. One arm free, one "
                "knife, and no questions left about how to use "
                "either."),
            "vault_troll": (
                "It came in the honest way, through the wall, and it "
                "eats down the rows like a man at a market stall. It "
                "will take a while to stop."),
        },
        "traits": {
            "vault_keeper": ["resist_med"],
            "vault_troll": ["bulwark", "slow"],
        },
        "new": [{
            "id": "vault_rat", "name": "Vault rat", "weight": 2,
            "lore": (
                "A vault of catalogued provisions is, from a rat's "
                "side of the ledger, simply a granary with opinions."),
            "prose": (
                "A rat drops from a hanging bundle with somebody's "
                "dried rations in its teeth, lands between you and the "
                "row, and declines — visibly — to share the territory."),
        }],
    },
    39: {
        "lore": {
            "gallery_sentinel": (
                "The spiders here do not hunt; they garrison. The "
                "challenge phrase is real, and there is no right "
                "answer."),
            "hatching_sac": (
                "Newborn and knee-high, it knows the two facts of its "
                "life: it is hungry, and you are near."),
            "broodfed_troll": (
                "Paid for guard duty in whatever fails inspection. It "
                "takes the work seriously; the work is you."),
        },
        "traits": {
            "gallery_sentinel": ["armor_med"],
        },
        "new": [{
            "id": "sac_light", "name": "Sac-light", "weight": 2,
            "traits": ["flying", "resist_low"],
            "lore": (
                "The glow that moves inside the eggs sometimes moves "
                "outside them. Vyx counts those too."),
            "prose": (
                "One of the egg-glows slips its sac and drifts the "
                "gallery like a lantern looking for its keeper, and "
                "whatever it lights leans toward you in its shell."),
        }],
    },
    40: {
        "lore": {
            "throne_guard": (
                "Bred big and patient, holding the throne's own "
                "anchor-lines. It lets you see it coming — the lesson "
                "is the point."),
            "silk_knight": (
                "A climber in good plate got this far once. The armor "
                "still works fine; the man inside works for Vyx now."),
            "consort_spider": (
                "It has outlived every rival by being exactly this "
                "careful, and it is faster than careful looks."),
        },
        "traits": {
            "throne_guard": ["armor_low"],
            "silk_knight": ["armor_med"],
            "consort_spider": ["fast"],
        },
        "new": [{
            "id": "thread_page", "name": "Thread-page", "weight": 2,
            "lore": (
                "It runs messages along the throne-lines. What it "
                "reports, the whole chamber hears."),
            "prose": (
                "A small spider drops to the floor ahead of you, taps "
                "out something quick on a taut anchor-line, and squares "
                "up — the message is sent, and the messenger has "
                "orders too."),
        }, {
            "id": "tribute_husk", "name": "Tribute husk", "weight": 2,
            "traits": ["slow"],
            "lore": (
                "The Deep sends its rent up to the throne walking. "
                "Interfering with the post is taken poorly."),
            "prose": (
                "A husk climbs the great web hand over hand with a "
                "wrapped bundle roped to its back, tribute-bound for "
                "the dark overhead — and turns its dry face toward the "
                "obstacle you have just become."),
        }],
    },
}
