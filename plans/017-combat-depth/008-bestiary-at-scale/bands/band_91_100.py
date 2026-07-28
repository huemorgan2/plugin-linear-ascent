# 008 band 91-100 — The Crown. The citadel endgame: cast-glass and
# taken champions carry the last armor_highs, the tempter and the
# court's uncanny carry resist (one resist_high at the door), the
# queue veteran is the bulwark, and the fast things are courtiers.
SPEC = {
    91: {
        "lore": {
            "stair_sentinel": (
                "The Crown does not garrison its doorstep with "
                "soldiers. It casts them, and glass casts thick."),
            "reflection_wrong": (
                "It wears your stance, your gear, and a much better "
                "night's sleep. Spells recognize themselves in it and "
                "hesitate."),
            "court_page": (
                "Refusing a royal summons is death. Accepting is "
                "death with better lighting. It waits, "
                "professionally, while you choose."),
        },
        "traits": {
            "stair_sentinel": ["armor_med"],
            "reflection_wrong": ["resist_med"],
        },
        "new": [{
            "id": "mirror_moth", "name": "Mirror moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It lays its eggs in reflections. The stair-keepers "
                "polish against it, and lose ground yearly."),
            "prose": (
                "A moth with wings of near-perfect mirror lifts off "
                "the balustrade, and as it circles you it flashes "
                "back small crooked pieces of your own climb."),
        }],
    },
    92: {
        "lore": {
            "gallery_duelist": (
                "A century against its own reflection, and the "
                "reflection finally let it win. Dueling here is how "
                "the court says hello."),
            "orphan_reflection": (
                "Its owner died at some forgotten intrigue. It has "
                "found a body it likes, and spells slide off the "
                "glass it lives behind."),
            "whisper_courtier": (
                "All silk and sympathy until the third sentence, when "
                "the sympathy runs out and the silk turns out to be "
                "wire."),
        },
        "traits": {
            "gallery_duelist": ["fast"],
            "orphan_reflection": ["resist_med"],
            "whisper_courtier": ["resist_low"],
        },
        "new": [{
            "id": "sconce_imp", "name": "Sconce imp", "weight": 2,
            "lore": (
                "It tends the gallery lamps and taxes every shadow "
                "they throw. Yours arrived unregistered."),
            "prose": (
                "An imp swings down from a lamp-sconce with a "
                "taper-snuffer held like a halberd, counts your "
                "reflections in the black glass, and presents the "
                "bill."),
        }],
    },
    93: {
        "lore": {
            "lead_crowned": (
                "Interruptions to the great work are bled off like "
                "excess pressure. Under the lead and the smoked "
                "glass, almost nothing gets through."),
            "light_leak": (
                "A thread of the heart's light that learned to move "
                "against the draft, feeling for something to be "
                "inside."),
            "coil_demon": (
                "Jaw wired straight into the shielding, radiant with "
                "theft. It should not be here either, which makes "
                "you a witness."),
        },
        "traits": {
            "lead_crowned": ["armor_high"],
            "light_leak": ["flying", "resist_med"],
            "coil_demon": ["resist_med"],
        },
        "new": [{
            "id": "sluice_rat", "name": "Sluice rat", "weight": 2,
            "lore": (
                "It nests in the reactor shielding, warm and "
                "half-bright, and defends the warmth like a "
                "birthright."),
            "prose": (
                "A rat with a faint glow under its skin slips out of "
                "a shielding seam, whiskers reading the gallery hum, "
                "and stands its ground on the warm plate you need to "
                "cross."),
        }],
    },
    94: {
        "lore": {
            "queue_veteran": (
                "It has waited so long it became part of the "
                "protocol — robes fused to the stone, token worn "
                "smooth. You will tire before it does; everyone "
                "has."),
            "chamberlain": (
                "Your paperwork is fatally out of order. The regret "
                "is genuine. The fatality is procedural."),
            "token_swarm": (
                "A century of the queue, voided, and the recalled "
                "tokens want their holders. Yours is getting "
                "warmer."),
        },
        "traits": {
            "queue_veteran": ["bulwark", "slow"],
            "chamberlain": ["resist_med"],
            "token_swarm": ["fast"],
        },
        "new": [{
            "id": "petitioners_hound", "name": "Petitioner's hound",
            "weight": 2,
            "lore": (
                "Its master's number was never called. It holds the "
                "bench, and the grudge, on his behalf."),
            "prose": (
                "A hound rises from beneath an empty bench where "
                "somebody's robes still sit, stretches a century out "
                "of its joints, and crosses the anteroom to explain "
                "what it thinks of queue-jumpers."),
        }],
    },
    95: {
        "lore": {
            "vault_curator": (
                "It knows the provenance of everything in the "
                "vaults, including the piece the empty plinth is "
                "waiting for."),
            "exhibit_awake": (
                "A realm's champion, taken whole, armor and all. Its "
                "terrible question: which side of a plinth are you "
                "on?"),
            "appraiser_imp": (
                "Your gear disappoints it. Your defiance, it says, "
                "brightening, will mount beautifully."),
        },
        "traits": {
            "vault_curator": ["resist_med"],
            "exhibit_awake": ["armor_high"],
            "appraiser_imp": ["fast"],
        },
        "new": [{
            "id": "case_moth", "name": "Case moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It eats the exhibits — tapestry first, provenance "
                "second. The curator has posted a bounty in three "
                "scripts."),
            "prose": (
                "A moth the grey of old banners lifts off a drowned "
                "realm's colors with a mouthful of history, and "
                "makes for the freshest fabric in the vaults, which "
                "is what you are wearing."),
        }],
    },
    96: {
        "lore": {
            "graft_horror": (
                "Somewhere inside it is a cutting of the forest from "
                "floor twenty-three, and it remembers you passing. "
                "The graft drinks spellwork like lamp-oil."),
            "garden_keeper": (
                "You are standing on the floor-one turf. It is very "
                "rare. It is very rare because of people like you."),
            "pollen_shade": (
                "What it pollinates, the gardeners harvest. Do not "
                "inhale the future."),
        },
        "traits": {
            "graft_horror": ["resist_med"],
            "pollen_shade": ["flying", "resist_low"],
        },
        "new": [{
            "id": "rose_beetle", "name": "Iron-rose beetle", "weight": 2,
            "traits": ["armor_med"],
            "lore": (
                "It feeds on the dwarven iron-roses and grows its "
                "shell from the clippings. The gardeners call it a "
                "pest with tenure."),
            "prose": (
                "A beetle armored in overlapping rose-iron petals "
                "drops off a grafted trellis, lands with a clank on "
                "the rare turf, and advances on you like a small "
                "opinionated fortress."),
        }],
    },
    97: {
        "lore": {
            "way_herald": (
                "Processions require rank, and rank requires "
                "patents, and you have neither — only, it allows, a "
                "certain momentum."),
            "banner_wraith": (
                "The flag of a dead realm flying itself, looking for "
                "hands to carry it right side up. Yours are "
                "occupied. It intends to free them."),
            "procession_guard": (
                "They have drilled the arrest of an unauthorized "
                "walker every day for a thousand years. You can "
                "tell — and the plate has drilled with them."),
        },
        "traits": {
            "way_herald": ["resist_med"],
            "banner_wraith": ["flying", "resist_med"],
            "procession_guard": ["armor_high"],
        },
        "new": [{
            "id": "kingsway_hound", "name": "Kingsway hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "The road-watch runs hounds down the avenue between "
                "processions. Unauthorized walkers are their whole "
                "diet."),
            "prose": (
                "From an alcove a hound in road-watch livery takes "
                "the avenue's black glass at a sprint that never "
                "slips, and its line ends precisely where you are "
                "standing."),
        }],
    },
    98: {
        "lore": {
            "lower_court_champion": (
                "It salutes the royal box first, you second — "
                "protocol, and also a tell. It has never once been "
                "allowed to lose."),
            "blood_arbiter": (
                "No patents, no second, no grave-plot reserved — "
                "irregular. The penalty is assessed in the "
                "traditional currency, on the spot."),
            "gallery_wager": (
                "It stands to lose a province on how far you get, "
                "and it has come over the rail to adjust the outcome "
                "personally."),
        },
        "traits": {
            "lower_court_champion": ["armor_med"],
            "blood_arbiter": ["resist_med"],
            "gallery_wager": ["fast"],
        },
        "new": [{
            "id": "chalk_page", "name": "Chalk page", "weight": 2,
            "lore": (
                "It scores the measures into the glass before every "
                "duel. The floor's thousand years of lines are its "
                "one work."),
            "prose": (
                "A page crouched at the floor's edge finishes "
                "chalking your measure, checks it twice against your "
                "reach, and takes up its scoring-iron to defend the "
                "accuracy of the line."),
        }],
    },
    99: {
        "lore": {
            "doubting_knight": (
                "If you knock, its hundred years of not-knocking "
                "become cowardice. It cannot allow the redefinition. "
                "The plate has camped as long as the doubt."),
            "last_tempter": (
                "The offer is genuine. That is the trap — there is "
                "nothing dishonest to push against, and spells find "
                "nothing dishonest to bite."),
            "door_acolyte": (
                "The door must not be touched by the unworthy, and "
                "its test of worth is administered by hand, "
                "immediately."),
        },
        "traits": {
            "doubting_knight": ["armor_high"],
            "last_tempter": ["resist_high"],
        },
        "new": [{
            "id": "threshold_raven", "name": "Threshold raven",
            "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It has watched the camp not-knock for a century, "
                "and it heckles every new arrival's resolve."),
            "prose": (
                "A raven drops from the door's distant hardware and "
                "lands between you and the camp, head cocked, "
                "delivering a verdict on your chances in one dry "
                "syllable, twice."),
        }],
    },
    100: {
        "lore": {
            "court_assembled": (
                "They fight the way courts do: all at once, and each "
                "hoping the others die doing it."),
            "kings_shadow": (
                "A younger King, and hungrier, and it does not "
                "answer to the one on the throne."),
            "crown_regalia": (
                "Scepter, orb, and chain of office in slow orbit. "
                "They have outlasted four bearers and are "
                "auditioning the fifth, armed."),
        },
        "traits": {
            "kings_shadow": ["fast", "resist_med"],
            "crown_regalia": ["flying", "armor_med"],
        },
        "new": [{
            "id": "witness_shade", "name": "Mirror witness", "weight": 2,
            "traits": ["resist_low"],
            "lore": (
                "Every conquered realm watches the throne room "
                "through its mirrors. One of them could not keep "
                "watching quietly."),
            "prose": (
                "A shape presses out of the nearest watching mirror "
                "— a witness from some drowned realm, worn thin by "
                "the view, determined that whatever happens to the "
                "King happens through it first."),
        }],
    },
}
