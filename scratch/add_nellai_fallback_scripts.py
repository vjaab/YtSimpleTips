import json
import os
import re

FALLBACK_FILE = "fallback_scripts.json"

with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
    scripts = json.load(f)

# 1. Fix Script [3] - Expand to ~95 words in Nellai dialect
script_3_chunks = [
    {
        "chunk_id": 1,
        "text": "நெல்லை மக்களே ஒரு நிமிஷம் கேளுங்கோ!",
        "english_caption": "LISTEN UP",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Glowing holographic circuit board glowing with warm temple lamp lights, 9:16 vertical, cinematic aesthetic, no humans."
    },
    {
        "chunk_id": 2,
        "text": "Artificial Intelligence-னு ஊரே பேசுது இல்லியா?",
        "english_caption": "TALK OF TOWN",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Modern server rack glowing in dark room, golden indicator lights, high tech cinematic, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 3,
        "text": "ஆனா உண்மை என்னா தெர்யுமா?",
        "english_caption": "REAL TRUTH",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Ancient South Indian palm leaf manuscript next to glowing neon fiber optic cables on rustic wooden desk, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 4,
        "text": "இதுக்கு சொந்தமா மூளையே கெடையாது!",
        "english_caption": "NO REAL BRAIN",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Artistic golden mechanical gear brain sculpture illuminated with warm side-lighting, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 5,
        "text": "அட போங்கோ! seriously சொல்றேங்!",
        "english_caption": "SERIOUS FACT",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Macro shot of a glowing microchip resting on traditional banana leaf texture, warm bronze tone, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 6,
        "text": "நம்ம மூளை மாதிரி யோசிக்காது,",
        "english_caption": "CANNOT THINK",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Neural network pulses glowing like starry constellations over dark red oxide background, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 7,
        "text": "வெறும் pattern matching மட்டும்தான் பண்ணும்.",
        "english_caption": "PATTERN MATCH",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Digital data cubes aligning neatly into rows, glowing turmeric gold and deep blue light, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 8,
        "text": "லட்சக்கணக்கான data-வை பாத்து,",
        "english_caption": "BILLIONS DATA",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Endless digital archives of glowing scroll papers stacked inside a high-tech vault, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 9,
        "text": "அடுத்த வார்த்தை என்னான்னு guess பண்ணுது.",
        "english_caption": "NEXT WORD",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Glowing letters forming in air like sparks over an ancient Tamil stone inscription, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 10,
        "text": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!",
        "english_caption": "PATTERN INTERRUPT",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": True,
        "infographic_type": "stat",
        "infographic_data": {"title": "TWIST", "stat": "99.9%", "label": "Guessing Accuracy"},
        "nano_visual_prompt": "Dramatic split lighting on a massive bronze balance scale tilting rapidly, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 11,
        "text": "Chess-ல world champion-ஐயே ஜெயிக்கும்,",
        "english_caption": "CHESS MASTER",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Handcrafted rosewood chess pieces on an ornate brass chessboard with deep shadows, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 12,
        "text": "ஆனா சின்ன காக்கா படம் கேட்டா தப்பு பண்ணிடும்!",
        "english_caption": "SIMPLE ERRORS",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Traditional clay bird statue resting on wooden table with digital pixel distortion, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 13,
        "text": "அதனால பயப்படாம உங்க வேலையில",
        "english_caption": "DONT FEAR",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Traditional brass oil lamp glowing steadily amidst flowing digital streams, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 14,
        "text": "இதை smart-ஆ use பண்ணுங்கோ!",
        "english_caption": "WORK SMART",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Modern smartphone open to an AI assistant tool on a clean wooden desk with filter coffee cup, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 15,
        "text": "AI நம்ம வேலையை தூக்கிடுமுன்னு நினைக்றீங்களா?",
        "english_caption": "TAKE JOBS?",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "Close-up of a glowing digital clock ticking with dramatic amber lighting, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 16,
        "text": "கமெண்ட்ல உங்க பதிலை சொல்லுங்கோ!",
        "english_caption": "COMMENT BELOW",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "South Indian temple bronze bell ringing with glowing reverberations, 9:16 vertical, no humans."
    },
    {
        "chunk_id": 17,
        "text": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!",
        "english_caption": "SUBSCRIBE NOW",
        "start": 0.0,
        "end": 0.0,
        "has_infographic": False,
        "infographic_type": "none",
        "infographic_data": {},
        "nano_visual_prompt": "A warm red silk banner with golden embroidery glowing under cinematic spotlight, 9:16 vertical, no humans."
    }
]

script_3_full_text = " ".join(c["text"] for c in script_3_chunks)
scripts[3]["script"] = script_3_full_text
scripts[3]["subtitle_chunks"] = script_3_chunks
scripts[3]["storyboard"] = [
    {
        "scene_number": i + 1,
        "narration": c["text"],
        "on_screen_text": c["english_caption"],
        "scene_objective": f"Scene {i+1}",
        "visual_type": "PATTERN_INTERRUPT" if "twist" in c["text"] else "South Indian Cinematic",
        "visual_prompt": c["nano_visual_prompt"],
        "camera_motion": "Slow zoom",
        "transition": "Match cut",
        "infographic_type": c.get("infographic_type", "none"),
        "infographic_data": c.get("infographic_data", {})
    }
    for i, c in enumerate(script_3_chunks)
]

# 2. Add New Fallback Scripts for Active Categories
new_scripts = [
    # ── Category 1: 🐾 Nature & Animal Oddities (Story A: Crow Face Memory) ──
    {
        "title": "காகம் உங்க முகத்தை வாழ்நாள் முழுக்க மறக்காது! Crow Face Memory! 🦅",
        "description": "Crow face memory scientific discovery explained in Nellai Tamil dialect by VJ. #NatureTamil #SimpleTipsByVJ #AnimalOddities",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Crow#Intelligence",
        "original_news_headline": "காகம் உங்க முகத்தை வாழ்நாள் முழுக்க மறக்காது! Crow Face Memory! 🦅",
        "original_news_url": "https://en.wikipedia.org/wiki/Crow#Intelligence",
        "relevant_links": ["https://en.wikipedia.org/wiki/Crow#Intelligence"],
        "hook": "காகம் உங்க முகத்தை வாழ்நாள் முழுக்க மறக்காது தெர்யுமா? 🦅",
        "summary": "Crows recognize and remember individual human faces for years and teach their young.",
        "sub_category": "🐾 Nature & Animal Oddities",
        "breaking_news_level": 9,
        "keywords": ["Crow memory", "Animal intelligence", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#NatureTamil", "#AnimalFacts", "#CrowMemory", "#SimpleTipsByVJ"],
        "comment_bait_question": "உங்க வீட்டு காகம் உங்களை அடையாளம் கண்டு சாப்பாடு கேக்குமா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நம்ம வீட்டு மொட்டை மாடில", "on_screen_text": "TERRACE CROWS", "visual_type": "Cinematic", "visual_prompt": "Red oxide terrace floor with terracotta pots and morning sunlight casting sharp shadows, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "தினமும் சாதம் திங்குற காகம்", "on_screen_text": "DAILY VISITOR", "visual_type": "Cinematic", "visual_prompt": "Traditional brass plate with white rice grains on rustic wooden surface, warm morning glow, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 3, "narration": "உங்களை பத்தி என்னா நினைக்றாங்க தெர்யுமா?", "on_screen_text": "BIRD SECRETS", "visual_type": "Cinematic", "visual_prompt": "Lush neem tree branches silhouetted against sunrise sky with morning mist, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 4, "narration": "அட போங்கோ! Washington University research-ல", "on_screen_text": "SCIENCE STUDY", "visual_type": "Cinematic", "visual_prompt": "Scientific research papers and leather bound magnifying glass on dark wooden table, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "என்ன கண்டுபிடிச்சாங்க தெரியுமா?", "on_screen_text": "BIG REVEAL", "visual_type": "Cinematic", "visual_prompt": "Dramatic beam of sunlight highlighting an ancient stone courtyard, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 6, "narration": "காகங்களுக்கு மனித முகத்தை", "on_screen_text": "HUMAN FACES", "visual_type": "Cinematic", "visual_prompt": "Artistic clay mask sculpture on temple wall lit by soft oil lamp flame, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 7, "narration": "துல்லியமா அடையாளம் பாக்க முடியுமாம்!", "on_screen_text": "SHARP MEMORY", "visual_type": "Cinematic", "visual_prompt": "Extreme macro of detailed biometric grid lines projected on black volcanic stone, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 8, "narration": "அதாவது நீங்க அதுக்கு கொஞ்சூம்", "on_screen_text": "KINDNESS", "visual_type": "Cinematic", "visual_prompt": "Clay water bowl for birds resting on red brick ledge with blooming jasmine flowers, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 9, "narration": "அன்பா சோறு வெச்சா வாழ்நாள் முழுக்க", "on_screen_text": "LIFELONG BOND", "visual_type": "Cinematic", "visual_prompt": "Traditional brass container filled with golden grains on hand-woven coir mat, 9:16 vertical, no humans.", "camera_motion": "Tracking shot", "transition": "Match cut"},
            {"scene_number": 10, "narration": "நம்ம முகத்தை ஞாபகம் வெச்சுக்குமாம்!", "on_screen_text": "REMEMBERED", "visual_type": "Cinematic", "visual_prompt": "Old family heirloom photo album resting on teak wood table with warm lantern light, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden dramatic lighting shift: dark thunderstorm clouds over ancient banyan tree, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Morph"},
            {"scene_number": 12, "narration": "நீங்க கல்லை தூக்கி", "on_screen_text": "IF ATTACKED", "visual_type": "Cinematic", "visual_prompt": "Smooth river stones scattered near red soil pathway under dramatic low light, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 13, "narration": "ஒரு காகத்தை விரட்டினா கூட,", "on_screen_text": "DANGER CALL", "visual_type": "Cinematic", "visual_prompt": "Dense tree canopy silhouetted against vivid orange dusk sky, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 14, "narration": "அப்புடியே 5 வருஷம் கழிச்சு பாத்தாலும்", "on_screen_text": "5 YEARS LATER", "visual_type": "Cinematic", "visual_prompt": "Ancient temple stone sundial marking the passage of years, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 15, "narration": "உங்களை பழிவாங்க மத்த காகங்களையும் கூப்பிடுமாம்!", "on_screen_text": "MOB DEFENSE", "visual_type": "Cinematic", "visual_prompt": "Multiple bird silhouettes resting along old village roof tiles against sunset, 9:16 vertical, no humans.", "camera_motion": "Tracking shot", "transition": "Match cut"},
            {"scene_number": 16, "narration": "தன்னோட குஞ்சுகளுக்கும் சொல்லி குடுக்குமாம்!", "on_screen_text": "NEXT GEN", "visual_type": "Cinematic", "visual_prompt": "A delicate natural twig nest tucked securely in dense green foliage, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 17, "narration": "இன்னாரு கெட்டவன்னு alert பண்ணிடுமாம்!", "on_screen_text": "ALERT SYSTEM", "visual_type": "Cinematic", "visual_prompt": "Glowing network map of connected tree branches like neural synapses, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 18, "narration": "அதனால காகத்துக்கு சோறு போடுறப்ப", "on_screen_text": "DAILY FEED", "visual_type": "Cinematic", "visual_prompt": "Polished bronze cup of fresh water surrounded by scattered grain, warm temple setting, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 19, "narration": "மரியாதையா நில்லுங்கோ பாருங்கோ!", "on_screen_text": "RESPECT BIRDS", "visual_type": "Cinematic", "visual_prompt": "Red oxide verandah floor with kolam patterns glowing in morning sunlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 20, "narration": "உங்க வீட்டு காகம் உங்களை அடையாளம் கண்டு", "on_screen_text": "YOUR CROWS?", "visual_type": "Cinematic", "visual_prompt": "South Indian clay water pots lined up neatly along garden fence, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 21, "narration": "சாப்பாடு கேக்குமான்னு கமெண்ட்ல சொல்லுங்கோ!", "on_screen_text": "COMMENT NOW", "visual_type": "Cinematic", "visual_prompt": "Ornate brass temple bell hanging in front of stone temple pillar, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 22, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Vibrant maroon silk banner with gold trim illuminated under warm cinematic stage lights, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    },

    # ── Category 1: 🐾 Nature & Animal Oddities (Story B: Octopus Superpowers) ──
    {
        "title": "ஆக்டோபஸுக்கு 3 இதயம் & நீல நிற ரத்தம்! Octopus Superpowers! 🐙",
        "description": "Octopus three hearts and blue blood bizarre nature facts in Nellai Tanglish by VJ. #OctopusTamil #SimpleTipsByVJ #NatureOddities",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Octopus#Circulatory_system",
        "original_news_headline": "ஆக்டோபஸுக்கு 3 இதயம் & நீல நிற ரத்தம்! Octopus Superpowers! 🐙",
        "original_news_url": "https://en.wikipedia.org/wiki/Octopus#Circulatory_system",
        "relevant_links": ["https://en.wikipedia.org/wiki/Octopus#Circulatory_system"],
        "hook": "கடலுக்கு அடியில 3 இதயம் இருக்கிற விசித்திர பிராணி தெர்யுமா? 🐙",
        "summary": "Octopuses have 3 hearts, blue copper blood, and 9 brains distributed across arms.",
        "sub_category": "🐾 Nature & Animal Oddities",
        "breaking_news_level": 9,
        "keywords": ["Octopus blood", "Three hearts", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#NatureOddities", "#OctopusTamil", "#DeepSea", "#SimpleTipsByVJ"],
        "comment_bait_question": "ஆக்டோபஸுக்கு 9 மூளை இருக்கிற விஷயம் உங்களுக்கு முன்னாடியே தெர்யுமா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே கடலுக்கு அடியில", "on_screen_text": "DEEP OCEAN", "visual_type": "Cinematic", "visual_prompt": "Deep indigo underwater ocean abyss with sunbeams piercing translucent water, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "ஒரு ஏலியன் பிராணி வாழுது தெர்யுமா?", "on_screen_text": "ALIEN CREATURE", "visual_type": "Cinematic", "visual_prompt": "Bioluminescent coral reef glowing with deep emerald and azure light, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 3, "narration": "அட போங்கோ! அதுதான் ஆக்டோபஸ்!", "on_screen_text": "OCTOPUS", "visual_type": "Cinematic", "visual_prompt": "Macro view of textured sea floor with pearlescent shells and smooth corals, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 4, "narration": "நமக்கு ஒரு இதயம் தான் இருக்கு,", "on_screen_text": "ONE HEART", "visual_type": "Cinematic", "visual_prompt": "Glowing anatomical red heart holographic representation in high tech dark space, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "ஆனா ஆக்டோபஸுக்கு மூணு இதயம்!", "on_screen_text": "3 HEARTS", "visual_type": "Cinematic", "visual_prompt": "Three glowing crystalline heart chambers pulsing together in deep blue ocean void, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 6, "narration": "ரெண்டு இதயம் gills-க்கு ரத்தம் அனுப்பும்,", "on_screen_text": "GILL HEARTS", "visual_type": "Cinematic", "visual_prompt": "Flowing microfluidic stream of glowing cyan fluids branching smoothly, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 7, "narration": "ஒண்ணு உடம்பு முழுக்க ரத்தம் பாய்ச்சும்.", "on_screen_text": "BODY PUMP", "visual_type": "Cinematic", "visual_prompt": "Central glowing sapphire core radiating concentric energy rings, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 8, "narration": "இன்னொரு அதிரடி உண்மை சொல்றேங் பாருங்கோ,", "on_screen_text": "SHOCKING FACT", "visual_type": "Cinematic", "visual_prompt": "Deep underwater cavern with shimmering crystals reflecting cyan light, 9:16 vertical, no humans.", "camera_motion": "Tracking shot", "transition": "Match cut"},
            {"scene_number": 9, "narration": "இதோட ரத்தத்தின் கலர் சிவப்பு இல்ல!", "on_screen_text": "NOT RED BLOOD", "visual_type": "Cinematic", "visual_prompt": "Clear glass beaker containing deep azure glowing liquid on black slate laboratory table, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 10, "narration": "பளிச்சுன்னு நீல கலர்ல இருக்கும்!", "on_screen_text": "BLUE BLOOD", "visual_type": "Cinematic", "visual_prompt": "Vibrant electric blue fluid swirling inside an elegant crystal vial with warm side highlights, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual break: Dramatic copper ore nuggets reflecting intense golden amber spotlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Morph"},
            {"scene_number": 12, "narration": "நம்ம ரத்தத்துல iron இருக்குறதால சிவப்பு,", "on_screen_text": "IRON VS COPPER", "visual_type": "Cinematic", "visual_prompt": "Deep crimson ruby stone contrasted against polished raw copper metal block, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 13, "narration": "ஆக்டோபஸ் ரத்தத்துல copper நிறஞ்சிருக்கு!", "on_screen_text": "HEMOCYANIN", "visual_type": "Cinematic", "visual_prompt": "Glowing metallic copper dust floating in deep sea brine like luminous stars, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 14, "narration": "குளிர்ந்த ஆழ்கடலில் ஆக்சிஜன் கொண்டுபோக", "on_screen_text": "DEEP FREEZE", "visual_type": "Cinematic", "visual_prompt": "Glacial underwater ice caves illuminated by blue ambient light, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 15, "narration": "இந்த தாமிர சத்துதான் ரொம்ப உதவுதாம்!", "on_screen_text": "SUPER SURVIVAL", "visual_type": "Cinematic", "visual_prompt": "Microscopic molecular structure glowing with sapphire nodes and golden bonds, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 16, "narration": "அதுமட்டுமில்ல, ஆக்டோபஸ் கைகள் ஒவ்வொண்ணுக்கும்", "on_screen_text": "8 ARMS", "visual_type": "Cinematic", "visual_prompt": "Eight concentric geometric ripples expanding on still dark water surface, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 17, "narration": "தனித்தனி mini brain உண்டு!", "on_screen_text": "9 BRAINS", "visual_type": "Cinematic", "visual_prompt": "Nine interconnected glowing nodal points across a dark neural network matrix, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 18, "narration": "மொத்தம் ஒன்பது மூளை இருக்கு பாருங்கோ!", "on_screen_text": "DISTRIBUTED MIND", "visual_type": "Cinematic", "visual_prompt": "Polished brass astrolabe reflecting warm lamplight in an ancient scholar library, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 19, "narration": "இதுல எந்த விஷயம் உங்களுக்கு புதுசுன்னு", "on_screen_text": "WHICH FACT?", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian bronze bowl on weathered timber table under warm light, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 20, "narration": "மறக்காம கமெண்ட்ல சொல்லுங்கோ!", "on_screen_text": "COMMENT BELOW", "visual_type": "Cinematic", "visual_prompt": "Temple stone courtyard lit by evening brass oil lamps with gentle flickering flames, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 21, "narration": "இதே மாதிரி சுவாரசியமான குறிப்புகளுக்கு", "on_screen_text": "MORE FACTS", "visual_type": "Cinematic", "visual_prompt": "Ancient palm leaf manuscript scroll tied with sacred saffron thread, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 22, "narration": "Simple Tips by VJ சேனலை Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Deep red silk drape with ornate golden temple border glowing under dramatic spotlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    },

    # ── Category 2: 🍳 Food, Health & Kitchen Science (Honey 3000 Years) ──
    {
        "title": "3000 வருஷம் பழமையான தேன் கெட்டுப்போகாதா? Honey Science! 🍯",
        "description": "Honey never spoils science explained in Nellai Tamil dialect by VJ. #KitchenScience #HoneyHack #SimpleTipsByVJ",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Honey#Preservation",
        "original_news_headline": "3000 வருஷம் பழமையான தேன் கெட்டுப்போகாதா? Honey Science! 🍯",
        "original_news_url": "https://en.wikipedia.org/wiki/Honey#Preservation",
        "relevant_links": ["https://en.wikipedia.org/wiki/Honey#Preservation"],
        "hook": "3000 வருஷம் பழமையான தேன் கெட்டுப்போகாதா? 🍯",
        "summary": "Pure honey never spoils due to zero water content and natural hydrogen peroxide acidity.",
        "sub_category": "🍳 Food, Health & Kitchen Science",
        "breaking_news_level": 9,
        "keywords": ["Honey science", "Kitchen secrets", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#HoneyScience", "#FoodHacks", "#NellaiTamil", "#SimpleTipsByVJ"],
        "comment_bait_question": "உங்க வீட்ல தேன் சர்க்கரையா உறைஞ்சு போயிருக்கா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே உங்க சமையலறையில", "on_screen_text": "KITCHEN SECRET", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian kitchen with stone grinding slab and brass ladles, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "இருக்கிற இந்த ஒரு பொருள்", "on_screen_text": "ONE ITEM", "visual_type": "Cinematic", "visual_prompt": "A heavy vintage glass jar containing thick golden amber honey, warm morning light, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 3, "narration": "உலகத்துலேயே எக்ஸ்பைரி டேட்டே இல்லாத பொருள்!", "on_screen_text": "NO EXPIRY", "visual_type": "Cinematic", "visual_prompt": "Close-up of golden honey dripping slowly from a wooden dipper into a brass vessel, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 4, "narration": "அட போங்கோ! அதுதான் சுத்தமான தேன்!", "on_screen_text": "PURE HONEY", "visual_type": "Cinematic", "visual_prompt": "Natural golden honeycomb section backlit with golden hour sunlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "எகிப்து பிரமிடுகள்ல 3000 வருஷம் முன்னாடி", "on_screen_text": "EGYPT TOMBS", "visual_type": "Cinematic", "visual_prompt": "Ancient terracotta amphora urn resting in a sand-dusted stone tomb chamber, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 6, "narration": "வெச்ச தேன் பானையை திறந்து பாத்தா கூட,", "on_screen_text": "3000 YEARS OLD", "visual_type": "Cinematic", "visual_prompt": "Clay pot sealed with beeswax lid covered in hieroglyphic engravings, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 7, "narration": "இன்னைக்கு வரைக்கும் சாப்பிடக்கூடிய நிலையில இருக்கு!", "on_screen_text": "STILL EDIBLE", "visual_type": "Cinematic", "visual_prompt": "Pristine clear amber honey glistening under beam of warm temple sunlight, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 8, "narration": "இது எப்படி சாத்தியம்னு யோசிங்கோ?", "on_screen_text": "HOW POSSIBLE?", "visual_type": "Cinematic", "visual_prompt": "Ancient bronze balances with weights on teak table near open window, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 9, "narration": "தேன்ல தண்ணீர் சத்து 17% க்கும் குறைவு,", "on_screen_text": "NO WATER", "visual_type": "Cinematic", "visual_prompt": "Dry micro-surface crystals reflecting pure amber glow with zero moisture, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 10, "narration": "பாக்டீரியா வளர ஈரப்பதமே கெடையாது பாருங்கோ!", "on_screen_text": "NO BACTERIA", "visual_type": "Cinematic", "visual_prompt": "Sterile microscopic molecular lattice structure glowing with golden warmth, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual shift: A steel spoon stirring hot tea with turbulent steam rising, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Morph"},
            {"scene_number": 12, "narration": "ஈரமான கரண்டியை உள்ள போட்டீங்கன்னா,", "on_screen_text": "WET SPOON RISK", "visual_type": "Cinematic", "visual_prompt": "Water droplet splashing into a jar of viscous liquid under crisp high speed lighting, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 13, "narration": "கொஞ்சூம் ஈரத்துலையும் பூஞ்சான் பிடிச்சு வீணாகிடும்!", "on_screen_text": "MOLD WARNING", "visual_type": "Cinematic", "visual_prompt": "Dry wooden spoon resting safely next to sealed airtight glass jar, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 14, "narration": "அதுமட்டுமில்ல, தேனை பிரிட்ஜ்ல வைக்காதீங்க!", "on_screen_text": "NO FRIDGE", "visual_type": "Cinematic", "visual_prompt": "Cold frost condensation on glass surface with warning symbol, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 15, "narration": "குளிர்ல அது சர்க்கரை மாதிரி உறைஞ்சுடும்.", "on_screen_text": "CRYSTAL HONEY", "visual_type": "Cinematic", "visual_prompt": "Golden crystalline sugar granules forming naturally inside raw honey jar, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 16, "narration": "அப்புடி உறைஞ்சா வெந்நீர் கிண்ணத்துல", "on_screen_text": "WARM WATER FIX", "visual_type": "Cinematic", "visual_prompt": "Traditional brass tumbler placed gently in a bowl of warm steaming water, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 17, "narration": "கொஞ்சூம் நேரம் வச்சா பழையபடி உருகிடும்!", "on_screen_text": "EASY RESTORE", "visual_type": "Cinematic", "visual_prompt": "Golden honey melting smoothly into translucent syrup in warm bowl, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 18, "narration": "உங்க வீட்டு தேன் உறைஞ்சு போயிருக்கா?", "on_screen_text": "YOUR HONEY?", "visual_type": "Cinematic", "visual_prompt": "Rustic kitchen wooden shelf with spice jars and honey bottle, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 19, "narration": "கமெண்ட்ல உங்க அனுபவத்தை சொல்லுங்கோ!", "on_screen_text": "COMMENT BELOW", "visual_type": "Cinematic", "visual_prompt": "Traditional brass oil lamp glowing warmly on terracotta ledge, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 20, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Vibrant maroon silk banner with gold embroidery illuminated under warm spotlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    }
]

# Convert new scripts to matching subtitle_chunks and ensure word counts
for item in new_scripts:
    sb = item["storyboard"]
    full_script_text = " ".join(scene["narration"] for scene in sb)
    item["script"] = full_script_text
    
    sub_chunks = []
    for sc in sb:
        sub_chunks.append({
            "chunk_id": sc["scene_number"],
            "text": sc["narration"],
            "english_caption": sc["on_screen_text"],
            "start": 0.0,
            "end": 0.0,
            "has_infographic": sc.get("infographic_type", "none") != "none",
            "infographic_type": sc.get("infographic_type", "none"),
            "infographic_data": sc.get("infographic_data", {}),
            "nano_visual_prompt": sc["visual_prompt"]
        })
    item["subtitle_chunks"] = sub_chunks
    item["phonetic_pronunciation_map"] = {
        "Simple Tips": "sim-pl tips",
        "Subscribe": "sub-skribe",
        "PATTERN": "pat-urn",
        "Washington": "wash-ing-ton",
        "University": "yu-ni-ver-si-ti",
        "research": "ree-serch"
    }

# Prepend the new scripts so matching prefers them
scripts = new_scripts + scripts

with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
    json.dump(scripts, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully updated {FALLBACK_FILE} with {len(scripts)} total scripts.")
for i, s in enumerate(scripts):
    wc = len(s.get("script", "").split())
    chunks = len(s.get("subtitle_chunks", []))
    sub = s.get("sub_category", "")
    title = s.get("title", "")
    print(f"[{i:02d}] Category: {sub:35s} | Words: {wc:3d} | Chunks: {chunks:2d} | Title: {title[:40]}")
