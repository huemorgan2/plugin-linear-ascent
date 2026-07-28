# 008 band 11-20 — Ironvale. Mine-and-forge country: armor favored
# (dwarf-plate, warframes), wisps off the fusion cores carry resist,
# hounds run fast, engines run slow, and one door-engine won't die.
SPEC = {
    11: {
        "lore": {
            "kobold_scavenger": (
                "It has survived every collapse this mine has offered by "
                "being the first thing out. The pry-bar is for slower "
                "questions."),
            "rust_hound": (
                "Bred to run down thieves in the galleries. The rust never "
                "reached the part that wants your heels."),
            "orc_outrider": (
                "Half a warframe still turns half the blows. The ledger it "
                "keeps is short on mercy."),
        },
        "traits": {
            "rust_hound": ["fast"],
            "orc_outrider": ["armor_low"],
        },
        "new": [{
            "id": "adit_bat", "name": "Adit bat", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It roosts in the lamp-warmth over the mine mouth and "
                "takes its meals off whatever the lamps draw in."),
            "prose": (
                "The dwarf lamps flicker as something drops from the "
                "adit's arch — a bat broad as a cloak, wings papering the "
                "cold updraft, circling your light once before it "
                "commits."),
        }],
    },
    12: {
        "lore": {
            "bilge_kobold": (
                "It poles the flooded galleries by lamp-hiss and habit. "
                "Climbers float face down eventually; it just keeps the "
                "schedule."),
            "drowned_hauler": (
                "Dwarf-plate seized over six legs of ore-cart iron. Slow "
                "as the flood and about as easy to argue with."),
            "orc_diver": (
                "A sealed warframe keeps the water out and some of the "
                "steel in. Salvage pays; you pay better."),
        },
        "traits": {
            "drowned_hauler": ["slow", "armor_high"],
            "orc_diver": ["armor_low"],
        },
        "new": [{
            "id": "sump_eel", "name": "Sump eel", "weight": 2,
            "lore": (
                "It came up the pump-lines when the water came back, and "
                "it has been growing ever since."),
            "prose": (
                "The black water folds and something long crosses the "
                "gallery at knee depth — a pale-bellied eel thick as a "
                "hawser, mouthing the current for the taste of you."),
        }],
    },
    13: {
        "lore": {
            "coin_sifter": (
                "It cannot read the scrip it hoards, but it knows exactly "
                "what a hand reaching for the pile means."),
            "tally_engine": (
                "Brass casing, broken arithmetic. It has been counting to "
                "the same wrong number for years."),
            "debt_collector": (
                "The warband taxes everything that walks this floor. The "
                "plate is company property; the enthusiasm is its own."),
        },
        "traits": {
            "tally_engine": ["armor_low"],
            "debt_collector": ["armor_med"],
        },
        "new": [{
            "id": "ledger_wisp", "name": "Ledger wisp", "weight": 2,
            "traits": ["flying", "resist_low"],
            "lore": (
                "The Counting Halls remember every unpaid ounce. Some of "
                "that memory has come loose and drifts."),
            "prose": (
                "A pale figure of dust and lamplight rises off the grand "
                "ledger — a wisp in the shape of a column of figures, "
                "drifting toward you to be balanced."),
        }, {
            "id": "scrip_rat", "name": "Scrip rat", "weight": 2,
            "lore": (
                "It nests in worthless money and defends it like "
                "treasure, which on this floor passes for wisdom."),
            "prose": (
                "A rat surfaces from a drift of colored scrip, cheeks "
                "packed with paper, and decides the shortest way to its "
                "next nest runs straight through you."),
        }],
    },
    14: {
        "lore": {
            "gear_kobold": (
                "It strips cogs the way other things strip carcasses — "
                "patiently, from the edges in, wrench-first."),
            "loose_flywheel": (
                "A millstone of drive-iron that shook off its axle years "
                "ago. It only knows one direction at a time."),
            "pit_fighter": (
                "Chalk ring, house rules, no plate above the waist. It "
                "wins bets here, and you are the odds."),
        },
        "traits": {
            "loose_flywheel": ["slow", "armor_high"],
        },
        "new": [{
            "id": "belt_runner", "name": "Belt-runner", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "Something marten-quick lives on the drive belts and has "
                "never once touched the floor."),
            "prose": (
                "A sleek shape flickers along the moving belts overhead, "
                "riding the machinery like a current, and comes off the "
                "last pulley at your chest, all claws and momentum."),
        }],
    },
    15: {
        "lore": {
            "glow_sick_kobold": (
                "The vault-light got into it years back. Fear burned away "
                "first, and spells find little left to grip."),
            "fuel_thief": (
                "Two runs a night, lead pannier full, and every climber "
                "met is time lost. It has no plans to lose time "
                "politely."),
            "forge_remnant": (
                "A vault-tender in dwarf-plate, headless and thorough. "
                "The checklist is gone; the round continues."),
        },
        "traits": {
            "glow_sick_kobold": ["resist_low"],
            "forge_remnant": ["slow", "armor_high"],
        },
        "new": [{
            # 009: resist_med sat AT the 1.6x drag bar for sorcerers and
            # flapped with the day seed — resist_high makes the wall real.
            "id": "rod_wisp", "name": "Rod-wisp", "weight": 2,
            "traits": ["flying", "resist_high"],
            "lore": (
                "Light that leaked from a cracked core and learned the "
                "shape of a lantern-bearer. Spells pass through it like "
                "more light."),
            "prose": (
                "Between the vault doors the air brightens wrong — a "
                "figure of bare glow drifting the seam-light, carrying "
                "nothing, casting no shadow, coming to see yours."),
        }],
    },
    16: {
        "lore": {
            "orc_armorer": (
                "It hammers warframes for the warband and wears its best "
                "work to the job. Trade-ins accepted, forcibly."),
            "hammer_kobold": (
                "Apprenticed by habit to whoever holds the forge. The "
                "hammer is twice its height; it has learned exactly one "
                "swing."),
            "half_forged": (
                "Left on the great anvil mid-making, it finished itself. "
                "One side is still cooling; the temper never set right."),
        },
        "traits": {
            "orc_armorer": ["armor_med"],
            "half_forged": ["slow"],
        },
        "new": [{
            "id": "bellows_hound", "name": "Bellows hound", "weight": 2,
            "traits": ["fast"],
            "lore": (
                "Forge-hounds were bred to run messages between family "
                "fires. The families are gone; the running is not."),
            "prose": (
                "A hound comes through the forge-smoke at a flat sprint, "
                "coat singed to wire, and does not slow — the Commons "
                "taught it that everything worth having is taken at "
                "speed."),
        }],
    },
    17: {
        "lore": {
            "slag_rat": (
                "Generations in the warm dark under the ladles made it "
                "big, and none of them made it timid."),
            "ladle_crew": (
                "Three kobolds, one crank, and a firm belief that "
                "whatever the ladle lands on had it coming."),
            "smelter_boss": (
                "Quota is short and the plate is thick with spatter no "
                "chisel will shift. Everything here is salvage to it, "
                "you included."),
        },
        "traits": {
            "smelter_boss": ["armor_med"],
        },
        "new": [{
            "id": "heat_haunt", "name": "Heat-haunt", "weight": 2,
            "traits": ["resist_low"],
            "lore": (
                "The shimmer over the slag-runs sometimes stands up and "
                "walks. The old smelter crews would not work alone."),
            "prose": (
                "The air over the slag channel gathers into a standing "
                "shimmer, man-shaped and patient, warping the gallery "
                "behind it. It closes the distance without seeming to "
                "cross it."),
        }],
    },
    18: {
        "lore": {
            "blind_digger": (
                "Wax-pale and eyeless three generations down. In the dark "
                "you are the one at the disadvantage, and it knows it."),
            "winch_crawler": (
                "A winch head climbing on its own cable, hand over iron "
                "hand. It has never hurried and never let go."),
            "pit_hound": (
                "The deep shafts bred the rust hounds longer and quieter. "
                "By the time you hear it, it has counted your paces."),
        },
        "traits": {
            "winch_crawler": ["slow", "armor_low"],
            "pit_hound": ["fast"],
        },
        "new": [{
            "id": "drift_moth", "name": "Drift moth", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It feeds on lamp-oil and dust, and it likes its meals "
                "lit. Miners learned to work dark for a reason."),
            "prose": (
                "Your lamp gutters as a moth the span of two hands "
                "settles out of the drift's ceiling dark, wings shedding "
                "grey powder, drawn to the flame you cannot afford to "
                "put out."),
        }],
    },
    19: {
        "lore": {
            "door_breaker": (
                "It was in the breach when the doors came down, and the "
                "warframe still carries the dwarf-fire scars. It is "
                "owed, it feels."),
            "powder_kobold": (
                "A keg under each arm and a fuse for a scarf. It has "
                "outlived every crew it ever served, which should worry "
                "the crews."),
            "doorward_remnant": (
                "One door-engine survived the breach and never accepted "
                "it. It cannot be argued past — only outlasted."),
        },
        "traits": {
            "door_breaker": ["armor_med"],
            "doorward_remnant": ["bulwark", "slow"],
        },
        "new": [{
            "id": "breach_crow", "name": "Breach crow", "weight": 2,
            "traits": ["flying"],
            "lore": (
                "It followed the Red Orcs up-tower the way crows have "
                "always followed armies. The breach was the best day of "
                "its life."),
            "prose": (
                "A crow the size of a dog drops off a fallen door-slab "
                "and beats up into the scorched dark, circling — it has "
                "watched enough battles here to know to wait for the "
                "middle."),
        }, {
            "id": "scorch_rat", "name": "Scorch rat", "weight": 2,
            "lore": (
                "The breach cooked everything in the hall but the rats, "
                "and the rats took notes."),
            "prose": (
                "A rat with burn-bald patches works the seam of a fallen "
                "door, prying at old rations. It looks up with the flat "
                "calm of a survivor and comes over to try you instead."),
        }],
    },
    20: {
        "lore": {
            "honor_guard": (
                "Skarn's own, in plate polished to a dull red shine. The "
                "posting cost them blood, and they intend it to cost you "
                "more."),
            "warframe_champion": (
                "It fought up from the gear galleries pit by pit for the "
                "honor of meeting you first. The salvaged frame fits "
                "like a reputation."),
            "camp_hound": (
                "Short chain, shorter rations, and it slipped both. The "
                "camp is betting on the hound."),
        },
        "traits": {
            "honor_guard": ["armor_high"],  # 010: was armor_med — felt by 0.03x drag only
            "warframe_champion": ["armor_low"],
            "camp_hound": ["fast"],
        },
        "new": [{
            "id": "drum_kobold", "name": "Drum kobold", "weight": 2,
            "lore": (
                "It keeps the warcamp's slow time. The drums are not for "
                "you — but a dropped beat brings the whole camp's eyes."),
            "prose": (
                "A kobold with a war-drum bigger than itself plants its "
                "sticks mid-beat when it sees you. Protocol is clear: "
                "the beat must not stop, and you must."),
        }, {
            "id": "camp_looter", "name": "Camp looter", "weight": 2,
            "lore": (
                "Every army drags a tail of things that fight for the "
                "leavings. This one has done well by the Red Orcs."),
            "prose": (
                "A scarred goblin picks along the racked warframes with "
                "a sack of lifted buckles, sees you, and weighs the sack "
                "against the bounty Skarn posts on climbers. The sack "
                "loses."),
        }],
    },
}
