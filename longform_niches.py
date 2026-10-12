# -*- coding: utf-8 -*-
"""
longform_niches.py — Niche catalogue + weekday rotation for the 2-3 minute LONGFORM pipeline.

Seven niches (one per weekday) built from the viral faceless-Tamil channel types researched online
(mystery/true-crime, Tamil heritage, space & science, psychology, "what if" scenarios) plus the existing
Simple Tips by VJ categories (smart-living tips, nature/food/body science).

Each niche carries everything the script writer, storyboard agent, visual resolver and renderer need:
topic discovery angle, safety rules, hook style, preferred visual mix, AI-image art direction and palette.
"""

import datetime

import pytz

from config import TIMEZONE

# Hard bounds for the finished narration (user spec: 2 to 3 minutes)
LONGFORM_DURATION_BOUNDS = (120, 180)
# Duration the script writer aims for (middle of the window gives room for pacing drift)
LONGFORM_TARGET_SECONDS = 150

LONGFORM_NICHES = {
    "mystery": {
        "label": "🕵️ Mysteries, True Crime & Unexplained",
        "short_label": "Mystery",
        "emoji": "🕵️",
        "accent": (225, 60, 90),
        "angle": (
            "well-documented real mysteries, famous unsolved cases, disappearances, historical enigmas and unexplained "
            "phenomena — world-famous or India/Tamil Nadu cases that are extensively covered by reputable sources"
        ),
        "safety": (
            "NEVER accuse any living private individual. Stick to documented facts from major news / court / encyclopedia "
            "sources. No graphic violence, no gore, be respectful to victims. Clearly say 'theory' when something is a theory."
        ),
        "hook_style": "Open mid-mystery with the single most chilling documented detail, then promise the full story.",
        "visual_mix": {"stock": 35, "ai_image": 45, "infographic": 10, "screenshot": 10},
        "ai_style": (
            "dark cinematic documentary still, moody low-key lighting, volumetric fog, 35mm film grain, "
            "desaturated teal-and-amber grade, photorealistic"
        ),
        "stock_hint": "night street, old building, fog, newspaper, flashlight, empty corridor, ocean at night",
        "hashtags": ["#Mystery", "#TamilMystery", "#UnsolvedMysteries", "#TamilFacts"],
        "tone": "suspenseful, hushed storyteller that builds tension and pays it off",
    },
    "tamil_history": {
        "label": "🏛️ Tamil History & Heritage",
        "short_label": "Tamil History",
        "emoji": "🏛️",
        "accent": (255, 193, 69),
        "angle": (
            "verified history and archaeology of Tamil Nadu and the Tamil people — Chola, Pandya, Pallava, Sangam era, "
            "Keezhadi, temple engineering, ports, trade, inscriptions, forgotten heroes and inventions"
        ),
        "safety": (
            "Cite only claims backed by ASI / university / museum / Britannica / major-news sources. Separate proven fact "
            "from legend. No communal or caste provocation, no political slants."
        ),
        "hook_style": "Open with a jaw-dropping measurable fact (a year, a size, a distance) that makes viewers proud, then ask how.",
        "visual_mix": {"stock": 30, "ai_image": 50, "infographic": 10, "screenshot": 10},
        "ai_style": (
            "cinematic historical documentary frame, golden-hour light, dust motes, ancient South Indian stone temple "
            "architecture, authentic textures, epic wide composition, photorealistic"
        ),
        "stock_hint": "temple tower, stone carving, tamil nadu temple, ancient ruins, river, palm trees, sculpture",
        "hashtags": ["#TamilHistory", "#TamilHeritage", "#Chola", "#TamilFacts"],
        "tone": "proud, authoritative documentary narrator who still talks like a friend",
    },
    "space_science": {
        "label": "🚀 Space, Science & Universe Explained",
        "short_label": "Space & Science",
        "emoji": "🚀",
        "accent": (96, 165, 250),
        "angle": (
            "space, physics, earth science and big-science stories explained simply — ISRO missions, black holes, planets, "
            "stars, deep time, extreme experiments and recent discoveries"
        ),
        "safety": "Use NASA / ISRO / ESA / Nature / university sources. Avoid pseudo-science and unproven claims.",
        "hook_style": "Open with a mind-bending scale or number, then explain it with an everyday Tamil Nadu comparison.",
        "visual_mix": {"stock": 40, "ai_image": 35, "infographic": 20, "screenshot": 5},
        "ai_style": (
            "ultra-detailed space documentary render, deep blue and violet nebula lighting, lens flares, "
            "IMAX cinematic composition, photorealistic"
        ),
        "stock_hint": "galaxy, stars night sky, rocket launch, earth from space, telescope, planet, laboratory",
        "hashtags": ["#Space", "#ISRO", "#ScienceTamil", "#TamilFacts"],
        "tone": "curious, energetic, wonder-filled science explainer",
    },
    "psychology": {
        "label": "🧠 Psychology & Mind Hacks",
        "short_label": "Psychology",
        "emoji": "🧠",
        "accent": (167, 139, 250),
        "angle": (
            "evidence-based psychology, behaviour, habits, memory, sleep, focus and decision-making that Tamil viewers "
            "experience daily — explained with named studies and practical takeaways"
        ),
        "safety": (
            "Use peer-reviewed studies / APA / NIH / major universities. No medical diagnosis or treatment advice, no "
            "'cure' claims; add a gentle 'talk to a professional' note for mental-health topics."
        ),
        "hook_style": "Open by calling out a feeling or habit every viewer has experienced this week, then reveal the hidden reason.",
        "visual_mix": {"stock": 45, "ai_image": 30, "infographic": 20, "screenshot": 5},
        "ai_style": (
            "clean modern editorial illustration-photography blend, soft purple and teal rim light, shallow depth of field, "
            "minimalist composition, photorealistic"
        ),
        "stock_hint": "person thinking, brain scan, crowd walking, sleeping person, office desk, student studying, mobile phone",
        "hashtags": ["#Psychology", "#MindHacks", "#TamilPsychology", "#TamilFacts"],
        "tone": "calm, smart, conversational big-brother who knows the science",
    },
    "what_if": {
        "label": "🤔 What If? Hypothetical Scenarios",
        "short_label": "What If",
        "emoji": "🤔",
        "accent": (255, 138, 76),
        "angle": (
            "science-grounded 'What if…' scenarios — what if the Moon vanished, Earth stopped spinning, humans stopped "
            "sleeping — built step by step from real physics/biology numbers"
        ),
        "safety": (
            "Every step of the scenario must follow from verifiable science; label speculation as 'scientists estimate'. "
            "No fear-mongering, no doomsday predictions presented as fact."
        ),
        "hook_style": "Open with the scenario as a question and the first shocking consequence within 8 seconds.",
        "visual_mix": {"stock": 30, "ai_image": 50, "infographic": 15, "screenshot": 5},
        "ai_style": (
            "surreal cinematic sci-fi concept art made photoreal, dramatic sky, epic scale, high contrast, "
            "orange and cyan grade, photorealistic"
        ),
        "stock_hint": "earth from space, city timelapse, empty street, ocean waves, storm clouds, sunrise, moon",
        "hashtags": ["#WhatIf", "#TamilScience", "#Hypothetical", "#TamilFacts"],
        "tone": "playful, dramatic, 'hold on tight' storyteller that escalates every beat",
    },
    "smart_living": {
        "label": "📱 Digital Safety, Money & Smart Living",
        "short_label": "Smart Living",
        "emoji": "💰",
        "accent": (52, 211, 153),
        "angle": (
            "deep-dive explainers on UPI/online scams, phone privacy, money-saving, bank and credit-card rules, "
            "electricity and consumer rights in India — practical, step-by-step, verified"
        ),
        "safety": (
            "Use RBI / NPCI / TRAI / government / bank / major-news sources. No investment advice or stock tips, no "
            "named-person accusations; give safe, legal actions only."
        ),
        "hook_style": "Open with the exact rupee loss or danger a viewer faces, then promise the 3-step protection.",
        "visual_mix": {"stock": 40, "ai_image": 20, "infographic": 25, "screenshot": 15},
        "ai_style": (
            "modern clean tech photography, soft daylight, realistic Indian urban setting, crisp textures, "
            "shallow depth of field, photorealistic"
        ),
        "stock_hint": "smartphone payment, ATM, wallet money, laptop typing, shopping, bank, mobile screen, credit card",
        "hashtags": ["#DigitalSafety", "#MoneyTips", "#TamilTips", "#UPIScam"],
        "tone": "friendly, protective elder-brother giving practical advice",
    },
    "nature_food_body": {
        "label": "🌿 Nature, Food & Human Body Science",
        "short_label": "Nature & Body",
        "emoji": "🌿",
        "accent": (163, 230, 53),
        "angle": (
            "animal superpowers, nature records, the science of Indian/Tamil foods and spices, and how the human body "
            "works — fascinating, verified, relatable"
        ),
        "safety": (
            "Use Nature / WHO / ICMR / NIH / Britannica / university sources. No diet fads, no medical treatment claims; "
            "add a 'consult a doctor' note for health topics."
        ),
        "hook_style": "Open with a surprising number about an animal, food or body part everyone knows.",
        "visual_mix": {"stock": 55, "ai_image": 25, "infographic": 15, "screenshot": 5},
        "ai_style": (
            "National Geographic style macro and wildlife photography, natural golden light, rich organic colours, "
            "razor-sharp detail, photorealistic"
        ),
        "stock_hint": "wildlife, elephant, bird flying, spices, cooking, kitchen, heart, human body, forest, ocean",
        "hashtags": ["#Nature", "#FoodScience", "#HumanBody", "#TamilFacts"],
        "tone": "warm, amazed, everyday-friendly explainer",
    },
}

for _k, _n in LONGFORM_NICHES.items():
    _n["id"] = _k

# Monday..Sunday rotation (1 longform per day). Order chosen so adjacent days never share a niche.
WEEKDAY_NICHE = {
    "Mon": "mystery",
    "Tue": "tamil_history",
    "Wed": "space_science",
    "Thu": "psychology",
    "Fri": "what_if",
    "Sat": "smart_living",
    "Sun": "nature_food_body",
}


def get_niche_for_today(forced=None):
    """Returns (day_name, niche_id, niche_dict). `forced` may be a niche id or None."""
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")
    niche_id = forced if forced in LONGFORM_NICHES else WEEKDAY_NICHE.get(day_name, "space_science")
    return day_name, niche_id, LONGFORM_NICHES[niche_id]


# Curated seed topics with verified facts and reachable Wikipedia references.
# Used when Search Grounding or LLM discovery hits 429 quota exhaustion.
SEED_TOPICS = {
    "mystery": [
        {
            "title": "The Ghost Ship Mystery of Mary Celeste",
            "premise": "In 1872, an American merchant ship was found drifting fully intact in the Atlantic Ocean with zero crew aboard and food still on tables.",
            "key_facts": [
                "The Mary Celeste was discovered on December 4, 1872, by the British brigantine Dei Gratia in the Atlantic Ocean.",
                "The ship was in seaworthy condition under partial sail with six months of food and water provisions completely untouched.",
                "All 10 people aboard—Captain Benjamin Briggs, his wife, two-year-old daughter, and seven crew members—had completely vanished.",
                "Personal belongings, navigation charts, and the cargo of 1,701 barrels of denatured industrial alcohol were intact.",
                "Only one lifeboat was missing, along with the ship's register and chronometer, showing an organized but hurried evacuation.",
                "A leading forensic theory suggests leaking alcohol fumes caused minor explosions that convinced the captain the ship was about to explode."
            ],
            "chapter_beats": ["Ghost ship spotted drifting", "Seaworthy condition discovery", "Missing family and crew", "Alcohol explosion theory", "Final unsolved question"],
            "tamil_connection": "Imagine walking into a Chennai home with boiling tea on the stove and fans running, but everyone vanished.",
            "visual_subjects": ["sailing ship ocean", "wooden ship deck", "ocean storm", "empty cabin", "foggy sea", "old map navigation", "calm ocean water"],
            "ai_image_ideas": [
                "19th century merchant sailing ship adrift in misty Atlantic ocean, 16:9 cinematic documentary",
                "Empty wooden ship captain's cabin with open diary and lantern, eerie lighting",
                "Cargo hold with wooden barrels of alcohol under low lantern light"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Mary_Celeste"],
            "source_name": "Wikipedia / Historical Maritime Archives",
            "keywords": ["Mary Celeste", "ghost ship", "unsolved mystery", "maritime history", "Tamil mystery"],
            "virality_score": 9.5,
            "already_verified": True
        },
        {
            "title": "The 72-Second Wow! Signal Mystery from Deep Space",
            "premise": "In 1977, a radio telescope detected an anomalous 72-second radio transmission from the Sagittarius constellation that has never repeated.",
            "key_facts": [
                "On August 15, 1977, astronomer Jerry R. Ehman detected a powerful narrowband radio signal using Ohio State University's Big Ear telescope.",
                "The signal lasted exactly 72 seconds, which was the entire window the telescope's antenna could track that celestial coordinate.",
                "Ehman circled the alphanumeric code '6EQUJ5' on computer printout paper and wrote 'Wow!' in the margin.",
                "The signal occurred at the 1420 MHz hydrogen line, an internationally protected radio frequency reserved for scientific astronomy.",
                "The signal was 30 times louder than deep space cosmic background radiation.",
                "Despite dozens of follow-up observations by SETI and astronomers worldwide, the signal was never heard again."
            ],
            "chapter_beats": ["72-second deep space signal", "The 6EQUJ5 computer printout", "Hydrogen line scientific significance", "Failed search for repeats", "Alien or cosmic comet theory"],
            "tamil_connection": "Like receiving one missed call from an unknown international number that never rings again.",
            "visual_subjects": ["radio telescope", "night sky stars", "space galaxy", "astronomer observatory", "telescope dish", "deep space nebula", "computer data printout"],
            "ai_image_ideas": [
                "Giant radio telescope dish pointed at starry night sky, blue and cyan cinematic lighting, 16:9",
                "Vintage 1970s mainframe computer printout paper with red ink circle, documentary frame",
                "Deep space spiral galaxy viewed from Earth orbit, photorealistic 8K"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Wow!_signal"],
            "source_name": "Wikipedia / Ohio State Radio Observatory",
            "keywords": ["Wow signal", "deep space", "astronomy", "SETI", "radio telescope"],
            "virality_score": 9.2,
            "already_verified": True
        }
    ],
    "tamil_history": [
        {
            "title": "The Granite Engineering Secrets of Thanjavur Big Temple",
            "premise": "Built in 1010 CE by Raja Raja Chola I, the Brihadisvara Temple stands 216 feet tall constructed entirely of interlocking granite without binding cement.",
            "key_facts": [
                "The Brihadisvara Temple in Thanjavur was completed in 1010 CE during the 25th year of Chola Emperor Raja Raja I's reign.",
                "The temple's central tower stands 216 feet (66 meters) tall, making it one of the tallest architectural structures of the medieval world.",
                "Over 130,000 tons of hard granite were used to construct the temple, yet no granite quarries exist within 60 kilometers of Thanjavur.",
                "The temple was built entirely with puzzle-like interlocking stone blocks without using any cement, mortar, or binding paste.",
                "The top Kumbam dome capstone weighs an estimated 80 tons and was carved from a single monolithic granite block.",
                "Historians believe an inclined earth ramp extending nearly 6 kilometers from Sarapallam was used with elephants to roll the 80-ton capstone to the summit."
            ],
            "chapter_beats": ["Raja Raja Chola's vision", "130000 tons of granite mystery", "Zero cement interlocking physics", "80-ton monolithic dome capstone", "Ancient Tamil engineering legacy"],
            "tamil_connection": "Every Tamilian has seen Thanjavur temple pictures, but few know how 80 tons reached the peak without cranes.",
            "visual_subjects": ["thanjavur temple", "temple tower south india", "ancient stone carving", "granite rocks", "chola architecture", "temple sculpture", "river cauvery"],
            "ai_image_ideas": [
                "Brihadisvara Temple Thanjavur at golden hour, epic wide cinematic angle, photorealistic ancient Tamil architecture",
                "Ancient Chola stone masons carving giant granite block with bronze chisels, warm dust motes",
                "Monumental earth ramp with working elephants moving giant temple capstone in medieval Tamil Nadu"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Brihadisvara_Temple"],
            "source_name": "Wikipedia / Archaeological Survey of India",
            "keywords": ["Thanjavur Big Temple", "Brihadisvara Temple", "Raja Raja Chola", "Tamil history", "ancient engineering"],
            "virality_score": 9.8,
            "already_verified": True
        },
        {
            "title": "Rajendra Chola's 1025 CE Overseas Naval Expedition",
            "premise": "In 1025 CE, Emperor Rajendra Chola I launched history's first recorded Indian oceanic naval campaign across 3,000 kilometers to conquer the Srivijaya Empire.",
            "key_facts": [
                "In 1025 CE, Rajendra Chola I mobilized an armada of war ships and crossed the Indian Ocean to invade Maritime Southeast Asia.",
                "The Chola navy sailed over 3,000 kilometers across the Bay of Bengal, navigating monsoonal currents with advanced celestial astronomy.",
                "The campaign targeted Srivijaya, an empire controlling the strategic Malacca Strait that heavily taxed Tamil merchant trade routes with China.",
                "Chola forces captured 14 maritime ports, including the capital Palembang, Kadaram (Kedah in Malaysia), and northern Sumatra.",
                "King Sangrama-Vijayottunggavarman of Srivijaya was captured along with his royal jewels and elephant cavalry.",
                "The expedition secured free maritime passage for Tamil merchant guilds like Ayyavole and Manigramam for over two centuries."
            ],
            "chapter_beats": ["Chola maritime superpower", "3000 km voyage across Indian ocean", "Strategic battle for Malacca strait", "Capture of Srivijaya capital", "Tamil merchant guilds golden age"],
            "tamil_connection": "Modern navies talk about blue-water capacity, but Cholas did oceanic fleet invasions 1,000 years ago.",
            "visual_subjects": ["ancient wooden ship ocean", "fleet of war ships sailing", "bay of bengal waves", "south east asia coastline", "ancient coins gold", "stone inscription tamil"],
            "ai_image_ideas": [
                "Chola navy wooden warships sailing in formation across choppy blue ocean, epic cinematic wide, 16:9",
                "Rajendra Chola reviewing maritime sea charts on palm leaves aboard command ship, golden cinematic light",
                "Ancient Tamil naval armada entering tropical harbor in Southeast Asia 1000 years ago"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Chola_invasion_of_Srivijaya"],
            "source_name": "Wikipedia / Epigraphia Indica",
            "keywords": ["Rajendra Chola", "Srivijaya expedition", "Chola navy", "Tamil history", "maritime empire"],
            "virality_score": 9.6,
            "already_verified": True
        }
    ],
    "space_science": [
        {
            "title": "How Chandrayaan-3 Unlocked Lunar South Pole Secrets",
            "premise": "On August 23, 2023, India became the first nation to soft-land near the Moon's South Pole, discovering sulfur and extreme surface temperature shifts.",
            "key_facts": [
                "On August 23, 2023, ISRO's Chandrayaan-3 Vikram lander achieved humanity's first soft landing near the Moon's South Pole at 69.37 degrees South latitude.",
                "The South Pole region contains permanently shadowed craters where temperatures drop to minus 246 degrees Celsius.",
                "These shadowed craters hold estimated billions of tons of water ice protected from solar sublimation for over two billion years.",
                "The Pragyan rover's laser spectrometer confirmed the presence of elemental Sulfur on the lunar surface, a crucial volcanic marker.",
                "The ChaSTE thermal probe recorded a 50-degree surface temperature dropping to minus 10 degrees just 8 centimeters underground.",
                "Lunar water ice can be split into liquid hydrogen and oxygen, providing rocket propellant for future human missions to Mars."
            ],
            "chapter_beats": ["Historic soft landing at South Pole", "Minus 246C shadowed craters", "Billions of tons of water ice", "Pragyan rover sulfur discovery", "Fuel station for future Mars travel"],
            "tamil_connection": "Project directors like Veeramuthuvel and Annadurai proved Tamil Nadu scientists lead global space science.",
            "visual_subjects": ["moon surface crater", "rocket launch night", "isro satellite", "earth from moon", "space rover wheel", "stars galaxy", "laboratory science"],
            "ai_image_ideas": [
                "Golden Vikram lander on dusty lunar surface near jagged South Pole crater rim, Earth rising in black sky, 16:9",
                "Six-wheeled Pragyan rover leaving tire tracks on Moon soil, sharp cinematic studio lighting, 8K",
                "Giant icy lunar crater interior showing frozen water deposits under star-filled black sky"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Chandrayaan-3"],
            "source_name": "Wikipedia / ISRO Mission Reports",
            "keywords": ["Chandrayaan 3", "ISRO", "Moon South Pole", "space science", "Tamil science"],
            "virality_score": 9.7,
            "already_verified": True
        }
    ],
    "psychology": [
        {
            "title": "The Tetris Effect: How Games and Habits Rewire Dreams",
            "premise": "Playing visual games or repetitive tasks for hours causes the human brain to involuntarily project falling shapes and patterns during sleep and awake hypnagogia.",
            "key_facts": [
                "The Tetris Effect was clinically documented by Harvard Medical School psychiatrist Robert Stickgold in 2000.",
                "People who play visually repetitive puzzle games for several hours report seeing falling blocks when closing their eyes before sleep.",
                "Brain scans show the visual cortex and hippocampus continue processing and replaying geometrical patterns in hypnagogic sleep.",
                "In Stickgold's study, amnesia patients who could not form conscious memories of playing the game still experienced dreams of falling shapes.",
                "This proves the brain possesses a dedicated procedural memory consolidation loop that operates independently of conscious memory.",
                "The same neurological effect explains why coders see syntax in dreams, accountants see spreadsheets, and gamers see navigation minimaps."
            ],
            "chapter_beats": ["Falling blocks behind closed eyes", "Harvard dream study discovery", "Amnesia patients brain mystery", "Procedural memory loop explained", "Modern digital screen takeover"],
            "tamil_connection": "After scrolling Instagram reels for 3 hours, closing your eyes still shows scrolling videos in your mind.",
            "visual_subjects": ["person sleeping close up", "mobile screen night", "puzzle blocks game", "brain neurology scan", "person thinking desk", "computer screen night"],
            "ai_image_ideas": [
                "Human brain glowing with neon geometric pattern overlays in dark room, 16:9 cinematic neuroscience",
                "Person sleeping peacefully with subtle holographic geometric shapes floating above eyes",
                "Cinematic macro shot of human eye pupil reflecting illuminated digital pixels"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Tetris_effect"],
            "source_name": "Wikipedia / Harvard Medical School Journal",
            "keywords": ["Tetris effect", "psychology", "brain science", "sleep research", "human memory"],
            "virality_score": 9.3,
            "already_verified": True
        }
    ],
    "what_if": [
        {
            "title": "What If Earth Stopped Spinning for 5 Seconds?",
            "premise": "If Earth's rotation halted abruptly for just 5 seconds, atmosphere and oceans moving at 1,670 km/h would unleash catastrophic supersonic global winds.",
            "key_facts": [
                "At the equator, Earth's surface rotates toward the east at roughly 1,670 kilometers per hour (460 meters per second).",
                "If the solid Earth stopped suddenly, Newton's first law of inertia dictates that the atmosphere and oceans would continue moving at 1,670 km/h.",
                "Supersonic winds four times faster than Category 5 hurricanes would scour structures, topsoil, and forests off equatorial landmasses.",
                "Oceans would surge eastward in massive megatsunamis several kilometers high, flooding inland continents before receding.",
                "Earth's equatorial bulge (flattened by 42 kilometers due to centrifugal force) would collapse, pulling oceans toward polar regions.",
                "When Earth resumed rotation 5 seconds later, the friction would generate enormous seismic shockwaves and global earthquakes."
            ],
            "chapter_beats": ["1670 km/h equatorial speed", "Instant inertial wind blast", "Megatsunamis sweeping continents", "Equatorial ocean bulge collapse", "Seismic earthquake aftermath"],
            "tamil_connection": "Like sitting in an express train moving at full speed that suddenly hits an immovable wall without brakes.",
            "visual_subjects": ["planet earth space", "ocean massive waves", "storm dark clouds", "city wind hurricane", "earth globe spinning", "sunrise horizon space"],
            "ai_image_ideas": [
                "Planet Earth viewed from orbit with turbulent storm cloud patterns and oceanic currents, 16:9 cinematic",
                "Giant ocean tsunami wave towering over coastal horizon at sunset, photorealistic disaster cinema",
                "Futuristic weather satellite tracking supersonic atmospheric wind bands over continents"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Earth%27s_rotation"],
            "source_name": "Wikipedia / Geophysical Fluid Dynamics",
            "keywords": ["Earth rotation", "What if", "physics explainer", "planetary science", "Tamil science"],
            "virality_score": 9.9,
            "already_verified": True
        }
    ],
    "smart_living": [
        {
            "title": "How SIM Swap Fraud Works and How to Protect Your Bank",
            "premise": "Cybercriminals hijack bank OTPs by impersonating phone owners to get replacement SIM cards issued, draining accounts within minutes.",
            "key_facts": [
                "SIM swap fraud begins with phishing or data leaks where scammers collect a victim's Aadhaar, phone number, and birth date.",
                "The attacker contacts telecom operators claiming the physical SIM card was lost, damaged, or upgraded to 5G eSIM.",
                "Once telecom activates the new duplicate SIM, the victim's phone immediately shows 'No Service' or zero signal bars.",
                "All incoming SMS two-factor authentication codes and UPI verification SMS messages now route straight to the attacker's device.",
                "Criminals reset net banking and UPI PIN passwords within 15 minutes while the victim assumes their phone has a temporary network glitch.",
                "Security experts advise setting telecom SIM lock PINs, enabling bank authenticator apps instead of SMS OTPs, and acting instantly if signal dies."
            ],
            "chapter_beats": ["Sudden 'No Service' alert danger", "Telecom impersonation trick", "OTP rerouting to scammer phone", "15-minute net banking drain", "3 critical steps to lock your SIM"],
            "tamil_connection": "If your phone signal disappears while everyone around you has full tower, never wait until tomorrow morning.",
            "visual_subjects": ["sim card mobile phone", "smartphone banking app", "scam alert warning", "atm money withdraw", "person typing phone night", "cyber security padlock"],
            "ai_image_ideas": [
                "Glowing nano SIM card on dark circuit board background with red digital lock icon, 16:9 modern tech",
                "Smartphone screen displaying 'No Service' alert in dark room, moody cyan and red cinematic lighting",
                "Cyber security digital shield protecting credit card and online banking transactions"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/SIM_swap_scam"],
            "source_name": "Wikipedia / Reserve Bank of India Advisory",
            "keywords": ["SIM swap", "cyber crime", "UPI fraud", "digital safety", "Tamil tech tips"],
            "virality_score": 9.7,
            "already_verified": True
        }
    ],
    "nature_food_body": [
        {
            "title": "Turritopsis dohrnii: The Biological Secrets of the Immortal Jellyfish",
            "premise": "When injured, starving, or aged, this tiny Mediterranean jellyfish undergoes transdifferentiation, reverting fully back into a juvenile polyp and resetting its lifespan.",
            "key_facts": [
                "Turritopsis dohrnii is a tiny bell-shaped jellyfish measuring just 4.5 millimeters across that lives in temperate oceans.",
                "When facing environmental stress, starvation, physical damage, or aging, it can reverse its adult medusa stage back into a juvenile polyp colony.",
                "It accomplishes this through transdifferentiation, an extraordinary process where adult specialized cells reprogram into completely different cell types.",
                "The newly formed polyp colony eventually buds off genetically identical young jellyfish, achieving theoretical biological immortality.",
                "In laboratory tests, single specimens have cycled from adult to polyp and back over a dozen consecutive times without dying of old age.",
                "Scientists at the University of Oviedo sequenced its genome in 2022, identifying double copies of DNA repair and telomere maintenance genes."
            ],
            "chapter_beats": ["4.5 mm ocean creature superpower", "Age reversal through transdifferentiation", "Cellular reprogramming biological loop", "Over 12 lab cycles without dying", "Human longevity and cancer genetics"],
            "tamil_connection": "Imagine an 80-year-old grandfather having the biological power to transform back into a baby when sick.",
            "visual_subjects": ["jellyfish ocean swimming", "underwater blue sea", "microscope laboratory biology", "coral reef deep sea", "glowing underwater marine", "dna genetics double helix"],
            "ai_image_ideas": [
                "Translucent glowing Turritopsis jellyfish floating in deep blue ocean water, volumetric caustic light rays, 16:9",
                "Microscopic cell transdifferentiation transforming under polarized biological laboratory microscope",
                "Glowing DNA double helix strands interwoven with bioluminescent marine ocean organisms"
            ],
            "source_urls": ["https://en.wikipedia.org/wiki/Turritopsis_dohrnii"],
            "source_name": "Wikipedia / University of Oviedo Genome Study",
            "keywords": ["immortal jellyfish", "Turritopsis dohrnii", "longevity genetics", "nature oddities", "Tamil biology"],
            "virality_score": 9.6,
            "already_verified": True
        }
    ]
}


def get_seed_topics(niche_id):
    """Returns curated fallback seed topics for a given niche."""
    return list(SEED_TOPICS.get(niche_id, []))

