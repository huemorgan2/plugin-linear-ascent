# 008 band 71-80 — The Gloom. The Huntsman's forest: shades carry
# resist, hounds carry speed, the herd stallion is the bulwark, and
# armor is rare and strange (a bronze-drilled shadow, a wire-fed
# beetle). Flyers are the small things of a dark wood.
SPEC = {
    71: {
        "lore": {
            "eaves_shade": (
                "It is thrown ahead of you by no light at all, and when "
                "you stop, it keeps walking. Spells pass through what "
                "isn't there."),
            "gloom_hound": (
                "The Huntsman's stock run loose between hunts, keeping "
                "themselves fed. The downwind circle is habit it does "
                "not need."),
            "dead_signal": (
                "The old realm's transmissions never died here. They "
                "just kept walking, and one of them knows your name."),
        },
        "traits": {
            "eaves_shade": ["resist_med"],
            "gloom_hound": ["fast"],
            "dead_signal": ["resist_low"],
        },
        "new": [{
            "id": "dusk_boar", "name": "Dusk boar", "weight": 2,
            "lore": (
                "It roots the treeline where the lamplight fails, and "
                "it has decided the failing light is its property."),
            "prose": (
                "A boar built low and wide comes out from under the "
                "black boughs, tusks catching the last of the town's "
                "lamp, and takes one deliberate step onto the path "
                "you wanted."),
        }],
    },
    72: {
        "lore": {
            "whisper_shade": (
                "It finishes sentences said here long ago in your "
                "voice, and it knows things you said three floors "
                "down. It has had time to take them personally."),
            "echo_hound": (
                "It throws its own footfalls ahead of itself. You hear "
                "it pass on the left. That is where it is not."),
            "night_mare": (
                "Saddled in cobweb, patient. It has never needed to "
                "chase — everyone in the gate town knows somebody who "
                "got on."),
        },
        "traits": {
            "whisper_shade": ["resist_med"],
            "echo_hound": ["fast"],
            "night_mare": ["slow", "resist_low"],
        },
        "new": [{
            "id": "gall_wasp_swarm", "name": "Gall wasps", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "They nest in the talking trees and sting whatever "
                "raises its voice. The wood has opinions about being "
                "quoted."),
            "prose": (
                "A seam in the nearest trunk hums open and the wasps "
                "come out in a ribbon, riding the sound of your own "
                "footsteps back at you."),
        }],
    },
    73: {
        "lore": {
            "ride_hound": (
                "You are game, walking the master's ride. The one low "
                "note is it logging the flush."),
            "grey_rider": (
                "One of the Huntsman's whips, grey from hat to boot. "
                "The lean as it passes is a fitting — for the next "
                "hunt's card."),
            "verge_shade": (
                "Once quarry, still running the verge on hunt nights, "
                "unable to stop. Behind it the ride goes cold, "
                "remembering."),
        },
        "traits": {
            "ride_hound": ["fast"],
            "grey_rider": ["fast", "armor_low"],
            "verge_shade": ["resist_low"],
        },
        "new": [{
            "id": "ride_crow", "name": "Ride crow", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It follows the hunts the way its kind follow armies, "
                "and it has learned the calendar better than the "
                "towns."),
            "prose": (
                "A crow drops from the black canopy to the ride's "
                "grey turf ahead of you, checks the empty avenue both "
                "ways like a connoisseur, and decides the hunt has "
                "come early this week."),
        }],
    },
    74: {
        "lore": {
            "glade_dancers": (
                "The round has a gap where someone used to be, and "
                "every grey face turns to you with the same polite, "
                "starving expectation."),
            "skirmish_shade": (
                "After all these years it has noticed the enemy "
                "stopped coming. It is relieved beyond words to have "
                "somebody real."),
            "glade_hound": (
                "The hounds will not enter the glades, which tells you "
                "something. It drives travelers in instead, patient as "
                "a sheepdog."),
        },
        "traits": {
            "glade_dancers": ["resist_med"],
            "skirmish_shade": ["resist_low"],
            "glade_hound": ["fast"],
        },
        "new": [{
            "id": "glade_moth", "name": "Glade moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It feeds on the grey light of the replays, and it "
                "resents every shadow that dims the show."),
            "prose": (
                "A moth the grey of the wedding light lifts off the "
                "glade's edge and makes for you in slow spirals, "
                "wings printed with a pattern that is almost "
                "faces."),
        }],
    },
    75: {
        "lore": {
            "pasture_mare": (
                "Whatever it dreams while it grazes, you have just "
                "walked into it, and it objects."),
            "herd_stallion": (
                "A tower of black muscle and slow smoke. It puts "
                "itself between you and the herd and hopes you will "
                "insist — you will not wear it down before dark."),
            "meadow_hound": (
                "Chosen for patience. It watched you cross half a "
                "mile of meadow without moving. Now it moves."),
        },
        "traits": {
            "pasture_mare": ["resist_low"],
            "herd_stallion": ["bulwark"],
            "meadow_hound": ["fast"],
        },
        "new": [{
            "id": "black_crake", "name": "Black crake", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It nests in the whispering grass and screams the "
                "herd's alarms. The herd-boys hate it more than the "
                "herd."),
            "prose": (
                "The black grass detonates a wingspan from your boot "
                "— a crake going up in a clatter of dark feathers, "
                "circling back at head height to scream you to the "
                "whole meadow."),
        }],
    },
    76: {
        "lore": {
            "statue_shade": (
                "A century drilled into the bronze made the stance "
                "flawless. It fights like the statue's better memory "
                "of itself, and blows ring on it like metal."),
            "candle_thief": (
                "It pinches out flames down the avenue, and your "
                "circle of light is next on the round."),
            "walks_hound": (
                "Its shadow does not match — too big, walking on the "
                "walls. When the hound stops, the shadow keeps "
                "coming."),
        },
        "traits": {
            "statue_shade": ["armor_med"],
            "candle_thief": ["fast"],
            "walks_hound": ["resist_low"],
        },
        "new": [{
            "id": "avenue_rat", "name": "Avenue rat", "weight": 2,
            "lore": (
                "It eats the candle-stubs the pilgrims leave and has "
                "grown bold enough to prefer them lit."),
            "prose": (
                "A rat trots the plinth-line with a guttering candle "
                "stub in its jaws like a trophy, drops it at the "
                "sight of you, and elects to defend the whole "
                "avenue's supply."),
        }],
    },
    77: {
        "lore": {
            "kennel_master": (
                "It looks you over as stock, checks the feeding book, "
                "and unclips the first lead. The apron has seen use."),
            "pack_matron": (
                "She does not run with the hunts anymore; she trains "
                "what does. The whole court goes quiet to watch the "
                "lesson."),
            "mews_mare": (
                "Stabled for re-breaking, and the door is open again. "
                "It wears its freedom like a dare."),
        },
        "traits": {
            "kennel_master": ["resist_med"],
            "pack_matron": ["slow"],
            "mews_mare": ["fast"],
        },
        "new": [{
            "id": "mews_owl", "name": "Mews owl", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "The winged things in the mews are hooded for a "
                "reason. This one worked its hood off."),
            "prose": (
                "Something leaves the mews' dark through a gap no "
                "wider than a hymnal — an owl in a torn hood, "
                "climbing fast, and the first stoop is for whoever "
                "opened the court gate."),
        }],
    },
    78: {
        "lore": {
            "snare_shade": (
                "It weaves shadow through wire with a craftsman's "
                "absorption. You are the test of the workmanship."),
            "caught_thing": (
                "Cutting it down is mercy. Mercy, out here, has a "
                "survival rate."),
            "funnel_hound": (
                "Never closing, only steering. Ahead the trees "
                "narrow. You are being delivered, on schedule."),
        },
        "traits": {
            "snare_shade": ["resist_med"],
            "funnel_hound": ["fast"],
        },
        "new": [{
            "id": "wire_beetle", "name": "Wire beetle", "weight": 2,
            "traits": ["armor_med", "slow"],
            "lore": (
                "It eats the Huntsman's snare-wire and armors itself "
                "with the leavings. The snare-setters bill it as an "
                "occupational hazard."),
            "prose": (
                "A beetle in a shell of wound wire works along a "
                "dressed lane, stripping a snare with its jaws, and "
                "rounds on you with the loyalty of a thing defending "
                "its larder."),
        }],
    },
    79: {
        "lore": {
            "pacer_hound": (
                "It is not hunting. It is pacing you, for the "
                "handicap, and it keeps glancing at your knees."),
            "rival_quarry": (
                "Three hunts' worth of broken snares hang off it. "
                "Thinning the competition counts as strategy."),
            "course_steward": (
                "You are off the marked course. Rejoining is "
                "compulsory. The flag is not a request."),
        },
        "traits": {
            "pacer_hound": ["fast"],
            "course_steward": ["resist_med"],
        },
        "new": [{
            "id": "stand_crow", "name": "Stand crow", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It works the audience hides for dropped stakes and "
                "settles bets nobody survived to collect."),
            "prose": (
                "A crow flaps up from the master of hounds' stand "
                "with a betting slip in its beak, takes one lap of "
                "the course over your head, and marks you down as "
                "tonight's long odds."),
        }],
    },
    80: {
        "lore": {
            "first_whip": (
                "Precedence must be observed — nobody reaches the "
                "master unbloodied. The lash uncoils with the boredom "
                "of long practice."),
            "pale_hound_brace": (
                "White as the columns, moving in mirrored arcs. They "
                "have opened every hunt for a century. They open "
                "yours."),
            "honored_mare": (
                "The master's spare, saddle empty. It considers the "
                "vacancy an insult and comes to fill the time."),
        },
        "traits": {
            "first_whip": ["resist_med"],
            "pale_hound_brace": ["fast"],
            "honored_mare": ["resist_low"],
        },
        "new": [{
            "id": "unblooded_hound", "name": "Unblooded hound",
            "weight": 2,
            "lore": (
                "Too young for the perimeter's silence, it breaks "
                "rank for you — its first hunt, and it wants it "
                "perfect."),
            "prose": (
                "One hound of the assembled hundreds cannot hold the "
                "silence — young, white-pawed, quivering — and it "
                "comes off the perimeter line at you before the horn "
                "grants anyone leave."),
        }],
    },
}
