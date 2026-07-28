# 008 band 51-60 — Frosthold. The Jarl's ice: wolves are the speed of
# the band, giants and cataract-trolls the bulk, glass-cased and
# parade-armored things the plate, and the frozen dead carry resist.
SPEC = {
    51: {
        "lore": {
            "rime_wolf": (
                "It has run down warmer things than you and eaten them "
                "mid-stride. The frost coat is from never slowing."),
            "gate_troll": (
                "Being a boulder is a toll practice older than the "
                "tower, and it has never lost this game."),
            "frozen_scout": (
                "One of last winter's climbers, ice to the bone. The "
                "cold in it drinks spellwork like it drank the man."),
        },
        "traits": {
            "rime_wolf": ["fast"],
            "gate_troll": ["armor_low"],
            "frozen_scout": ["slow", "resist_low"],
        },
        "new": [{
            "id": "glare_hawk", "name": "Glare hawk", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It hunts down-sun of the sunless glare, and it has "
                "learned that climbers look up too late."),
            "prose": (
                "Off the moraine wall a hawk drops out of the white "
                "glare with its shadow folded under it, talons first, "
                "committed from a height you never checked."),
        }],
    },
    52: {
        "lore": {
            "floe_wolf": (
                "It hunts by ear, through the ice, from below. The pack "
                "above is only there to steer you."),
            "swell_troll": (
                "It hangs in the green glass of its wave like a fly in "
                "amber, wearing the sea itself for plate."),
            "coolant_wight": (
                "It drowned before the sea froze and walks under the "
                "ice, upside down. Spells refract somewhere on the way "
                "through."),
        },
        "traits": {
            "floe_wolf": ["fast"],
            "swell_troll": ["armor_med"],
            "coolant_wight": ["resist_med"],
        },
        "new": [{
            "id": "brine_gull", "name": "Brine gull", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It works the frozen swells for whatever the wolves "
                "leave, and it has stopped waiting for the wolves."),
            "prose": (
                "A gull the size of a dog lifts off a standing wave "
                "crest, wings stiff with rime, and comes down the road "
                "cut at mast height, screaming its claim."),
        }],
    },
    53: {
        "lore": {
            "rime_stag": (
                "Its antlers are solid ice, grown that way, points "
                "refreshed nightly. It has stopped running from "
                "things — the antlers are why."),
            "forest_troll": (
                "It logs the frozen pines with a maul and gang-rules it "
                "ate. Your footsteps ring the forest like an alarm."),
            "bell_wolf": (
                "It learned to walk without ringing the trees, and it "
                "made the wolf soft-footed beyond nature. The first "
                "you hear is its weight arriving."),
        },
        "traits": {
            "rime_stag": ["armor_low"],
            "bell_wolf": ["fast"],
        },
        "new": [{
            "id": "chime_sprite", "name": "Chime sprite", "weight": 2,
            "traits": ["flying", "resist_low"],
            "lore": (
                "When the forest rings, something in the ringing "
                "answers. It prefers the quiet, and enforces it."),
            "prose": (
                "The bells of the iced needles gather into one clear "
                "tone, and the tone comes down the row of pines toward "
                "you — a small bright blur that the trees ring for as "
                "it passes."),
        }],
    },
    54: {
        "lore": {
            "bridge_troll": (
                "It doubled its rates for the season and glued the "
                "detour shut. The deed is in one fist, in case you "
                "argue."),
            "toll_wolf": (
                "It crosses without paying and shakes the spans until "
                "paying customers fall off. The trolls call it "
                "undignified. It calls it lunch."),
            "crevasse_wight": (
                "Not everyone who fell short on the toll hit the "
                "bottom. It climbs with its grudge in both hands."),
        },
        "traits": {
            "bridge_troll": ["armor_low"],
            "toll_wolf": ["fast"],
            "crevasse_wight": ["slow", "resist_low"],
        },
        "new": [{
            "id": "gorge_raven", "name": "Gorge raven", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It nests under the spans and audits every crossing. "
                "Whatever falls, it files."),
            "prose": (
                "A raven drops off the underside of the bridge and "
                "hangs on the gorge wind at your eye level, head "
                "tilted, deciding whether you are traffic or "
                "windfall."),
        }],
    },
    55: {
        "lore": {
            "steading_giant": (
                "The near field is posted and the post is the hammer. "
                "Freeholders this size do not lose arguments on their "
                "own land — they last them out."),
            "giant_hound": (
                "Bred to giant scale, it clears the pine fence without "
                "touching it. It is not angry. It is on the clock."),
            "hayrick_troll": (
                "It was stealing hay until you arrived and became the "
                "better idea."),
        },
        "traits": {
            "steading_giant": ["bulwark", "slow"],
            "giant_hound": ["fast"],
        },
        "new": [{
            "id": "steading_bull", "name": "Steading bull", "weight": 2,
            "lore": (
                "Cattle bred for owners four men tall. It does not "
                "recognize fences, seasons, or you."),
            "prose": (
                "A bull the size of a barn door tears free of the "
                "near-field herd with a fence rail still roped to one "
                "horn, and commits to the argument at a canter."),
        }],
    },
    56: {
        "lore": {
            "quarry_troll": (
                "It works a two-troll saw alone, which is against the "
                "gang rules, which it ate."),
            "block_wight": (
                "The deep blocks were not left unfinished by accident. "
                "It has been sawing from its side, and it is nearly "
                "out."),
            "gantry_wolf": (
                "It patrols the top gantry like a foreman and comes "
                "down the ramps collecting the pack as it comes."),
        },
        "traits": {
            "quarry_troll": ["armor_low"],
            "block_wight": ["slow", "resist_med"],
            "gantry_wolf": ["fast"],
        },
        "new": [{
            "id": "quarry_crow", "name": "Quarry crow", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "Every work site feeds its crows. This quarry's crows "
                "have opinions about who counts as site waste."),
            "prose": (
                "A crow lifts off the idle gantry crane and rides the "
                "cold down the terraces toward you, wings set, calling "
                "the count of you to the whole cut."),
        }],
    },
    57: {
        "lore": {
            "spray_wolf": (
                "Its coat of frozen coolant is white armor. It "
                "shatters its own casing to charge, and arrives in a "
                "burst of glass."),
            "falls_troll": (
                "It stands under the cataract for pleasure, growing a "
                "second hide. The silhouette under-promises."),
            "frozen_pilgrim": (
                "People come to see the Falls, and some stand too long "
                "in the spray. This one is still patient under a "
                "finger of glass."),
        },
        "traits": {
            "spray_wolf": ["armor_med"],
            "falls_troll": ["bulwark", "slow"],
            "frozen_pilgrim": ["slow", "resist_low"],
        },
        "new": [{
            "id": "ice_marten", "name": "Ice marten", "weight": 2,
            "lore": (
                "It dens in the dry pocket behind the cataract and "
                "robs the viewing path at its leisure."),
            "prose": (
                "A marten flows out from behind the white curtain, "
                "coat beaded with frozen spray, and cuts across the "
                "path with its eyes already on the food in your "
                "pack."),
        }],
    },
    58: {
        "lore": {
            "wall_giant": (
                "It leans into the gale holding a shield the size of a "
                "barn door — shelter for travelers, for a fee. You are "
                "past due."),
            "wind_wolf": (
                "It runs with the gale at its back and arrives at "
                "twice a wolf's honest speed. The bell rings once."),
            "shutter_troll": (
                "Paid in fish heads and deference. Today the shutters "
                "stay down, and its back is against them."),
        },
        "traits": {
            "wall_giant": ["armor_med"],
            "wind_wolf": ["fast"],
        },
        "new": [{
            "id": "gale_kite", "name": "Gale kite", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It is the only thing that flies the pass by choice, "
                "and it uses the wind the way an angler uses a "
                "river."),
            "prose": (
                "Something rides the pass wind without a single "
                "wingbeat — a kite-shape holding station over the "
                "crossing slot, waiting for the sprint the bell is "
                "about to ask of you."),
        }],
    },
    59: {
        "lore": {
            "road_thane": (
                "Custom entitles you to give your name and have it "
                "spoken at your defeat. The custom is observed; so is "
                "the plate."),
            "herald_wolf": (
                "Whatever it reports back decides how much of the "
                "garrison you meet. It circles once, taking notes."),
            "lamp_troll": (
                "Nine generations of trolls have held the lamp post, "
                "all of them it. Brawling on the road is its second "
                "duty."),
        },
        "traits": {
            "road_thane": ["armor_med"],
            "herald_wolf": ["fast"],
        },
        "new": [{
            "id": "post_raven", "name": "Post raven", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "The Jarl's road-post flies ahead of every traveler. "
                "Interfering with the mail is a listed offense."),
            "prose": (
                "A raven in a small silver road-band drops from lamp "
                "to lamp ahead of you, keeping exact pace, and finally "
                "lands in your path with the unhurried authority of "
                "the postal service."),
        }],
    },
    60: {
        "lore": {
            "hall_thane": (
                "It asked the room's leave to answer the horn, "
                "formally, and the room granted it like an avalanche "
                "starting."),
            "mead_troll": (
                "The barrel it set down was for you. It is not, now."),
            "hearth_wolf": (
                "The Jarl's own, with first claim on challengers by "
                "right of seniority. No thane disputes it."),
        },
        "traits": {
            "hall_thane": ["armor_med"],
            "hearth_wolf": ["fast"],
        },
        "new": [{
            "id": "ice_skald", "name": "Ice skald", "weight": 2,
            "traits": ["resist_med"],
            "lore": (
                "It sings the hall's cold fire brighter, and verses "
                "this old shrug off newer magic."),
            "prose": (
                "A skald rises from the bench nearest the cold fire, "
                "beard hung with hoarfrost bells, and begins the verse "
                "that turns the fire-trench white — your name is "
                "already in the second line."),
        }],
    },
}
