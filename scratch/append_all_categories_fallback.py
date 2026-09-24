import json

FALLBACK_FILE = "fallback_scripts.json"

with open(FALLBACK_FILE, "r", encoding="utf-8") as f:
    scripts = json.load(f)

additional_scripts = [
    # ── Category: 🧠 Mind-Blowing Science Curiosities ──
    {
        "title": "தண்ணீரில் உப்பு போட்டா சீக்கிரம் கொதிக்குமா? Boiling Secret! 🧂",
        "description": "Does adding salt to water make it boil faster? Science myth vs reality explained in Nellai Tamil dialect by VJ. #ScienceTamil #SimpleTipsByVJ",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Boiling-point_elevation",
        "original_news_headline": "தண்ணீரில் உப்பு போட்டா சீக்கிரம் கொதிக்குமா? Boiling Secret! 🧂",
        "original_news_url": "https://en.wikipedia.org/wiki/Boiling-point_elevation",
        "relevant_links": ["https://en.wikipedia.org/wiki/Boiling-point_elevation"],
        "hook": "தண்ணீரில் உப்பு போட்டா சீக்கிரம் கொதிக்குமா தெர்யுமா? 🧂",
        "summary": "Salt increases boiling point so water actually takes longer to boil, but cooks food faster.",
        "sub_category": "🧠 Mind-Blowing Science Curiosities",
        "breaking_news_level": 9,
        "keywords": ["Boiling point", "Salt water science", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#ScienceCuriosity", "#KitchenScience", "#NellaiTamil", "#SimpleTipsByVJ"],
        "comment_bait_question": "நீங்க சமையல் பண்றப்ப தண்ணி கொதிக்கிறதுக்கு முன்னாடியே உப்பு போடுவீங்களா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே சமையல் பண்றப்ப", "on_screen_text": "KITCHEN HABIT", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian kitchen with stone hearth and polished brass utensils, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "தண்ணி சீக்கிரம் கொதிக்கணும்னு", "on_screen_text": "BOILING WATER", "visual_type": "Cinematic", "visual_prompt": "Heavy copper pot filled with water resting on flame with rising steam, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 3, "narration": "உப்பு அள்ளி போடுவீங்க இல்லியா?", "on_screen_text": "ADDING SALT", "visual_type": "Cinematic", "visual_prompt": "Coarse white sea salt crystals falling through air in macro slow motion, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 4, "narration": "அட போங்கோ! உண்மை என்னா தெர்யுமா?", "on_screen_text": "REAL TRUTH", "visual_type": "Cinematic", "visual_prompt": "Dramatic amber kitchen candlelight highlighting bubbling water surface, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "உப்பு போட்டா தண்ணி சீக்கிரம் கொதிக்காது!", "on_screen_text": "BOILING MYTH", "visual_type": "Cinematic", "visual_prompt": "Macro shot of salt crystals dissolving in hot water forming swirling refraction ripples, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 6, "narration": "இன்னும் லேட்டா தான் கொதிக்கும்!", "on_screen_text": "TAKES LONGER", "visual_type": "Cinematic", "visual_prompt": "Vintage metal thermometer dipping into steaming water indicating rising temperature, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 7, "narration": "Physics-ல இதுக்கு பேரு", "on_screen_text": "PHYSICS LAW", "visual_type": "Cinematic", "visual_prompt": "Old scientific brass barometer with calligraphic formulas inscribed on parchment, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 8, "narration": "Boiling Point Elevation-னு சொல்வாங்க பாருங்கோ.", "on_screen_text": "ELEVATION", "visual_type": "Cinematic", "visual_prompt": "Glowing microscopic water molecules binding tightly around salt sodium ions, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 9, "narration": "சாதாரண தண்ணீர் 100 டிகிரில கொதிக்கும்னா,", "on_screen_text": "100 DEGREES", "visual_type": "Cinematic", "visual_prompt": "Crystal clear water boiling smoothly in glass laboratory flask over blue flame, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 10, "narration": "உப்பு போட்டா 102 டிகிரி தேவைப்படும்.", "on_screen_text": "102 DEGREES", "visual_type": "Cinematic", "visual_prompt": "Intense micro bubbles bursting violently at hot bottom of bronze cooking vessel, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual shift: A heavy traditional uruli vessel with fresh vegetable cuts, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Morph"},
            {"scene_number": 12, "narration": "தண்ணி கொதிக்க நேரம் ஆனாலும்,", "on_screen_text": "HOTTER WATER", "visual_type": "Cinematic", "visual_prompt": "Dense aromatic steam rising gracefully against warm dark kitchen background, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 13, "narration": "அதிக வெப்பத்துல காய்கறி போட்டா", "on_screen_text": "COOKS FASTER", "visual_type": "Cinematic", "visual_prompt": "Fresh green drumsticks and carrots boiling rapidly in hot spiced broth, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 14, "narration": "சாப்பாடு ரொம்ப சீக்கிரமா வெந்துடும்!", "on_screen_text": "QUICK MEAL", "visual_type": "Cinematic", "visual_prompt": "Traditional banana leaf feast spread with aromatic sambar and side dishes, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 15, "narration": "அதனால சுவையும் கொஞ்சூம் கூடும் பாருங்கோ!", "on_screen_text": "BETTER TASTE", "visual_type": "Cinematic", "visual_prompt": "Clay pot filled with steaming fragrant South Indian curry on red oxide floor, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 16, "narration": "நீங்க சமையல் பண்றப்ப உப்பு எப்போ போடுவீங்க?", "on_screen_text": "WHEN DO YOU ADD?", "visual_type": "Cinematic", "visual_prompt": "Rustic terracotta salt container with wooden scoop under golden morning ray, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 17, "narration": "கமெண்ட்ல உங்க பதிலை சொல்லுங்கோ!", "on_screen_text": "COMMENT BELOW", "visual_type": "Cinematic", "visual_prompt": "Traditional brass oil lamp flickering gently beside ancient temple stone pillars, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 18, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Deep red silk drape with ornate golden temple border glowing under dramatic spotlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    },

    # ── Category: 🧬 Human Body & Dark Psychology ──
    {
        "title": "ரூம்குள்ள போனதும் ஏன் விஷயம் மறந்து போகுது? Doorway Effect! 🚪",
        "description": "Why we forget things when entering another room explained by Doorway Effect psychology in Nellai Tamil by VJ. #PsychologyTamil #SimpleTipsByVJ",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Doorway_effect",
        "original_news_headline": "ரூம்குள்ள போனதும் ஏன் விஷயம் மறந்து போகுது? Doorway Effect! 🚪",
        "original_news_url": "https://en.wikipedia.org/wiki/Doorway_effect",
        "relevant_links": ["https://en.wikipedia.org/wiki/Doorway_effect"],
        "hook": "ஒரு ரூம்ல இருந்து இன்னொரு ரூம்க்கு போனா ஏன் மறக்குது தெர்யுமா? 🚪",
        "summary": "The Doorway Effect is a psychological event boundary where the brain flushes working memory.",
        "sub_category": "🧬 Human Body & Dark Psychology",
        "breaking_news_level": 9,
        "keywords": ["Doorway effect", "Human brain psychology", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#BrainPsychology", "#HumanBody", "#DoorwayEffect", "#SimpleTipsByVJ"],
        "comment_bait_question": "உங்களுக்கும் ரூம்குள்ள போனதும் விஷயம் மறந்து போயிருக்கா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே கிச்சன்ல இருந்து", "on_screen_text": "LEAVING ROOM", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian home wooden corridor with sunlight streaming through carved doorways, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "ஏதோ எடுக்க பெட்ரூமுக்கு போவீங்க,", "on_screen_text": "WALKING INSIDE", "visual_type": "Cinematic", "visual_prompt": "Ornate antique rosewood doorway opening into a dimly lit courtyard, 9:16 vertical, no humans.", "camera_motion": "Tracking shot", "transition": "Match cut"},
            {"scene_number": 3, "narration": "ஆனா உள்ள போனதும் அப்புடியே நின்னுடுவீங்க!", "on_screen_text": "SUDDEN BLANK", "visual_type": "Cinematic", "visual_prompt": "Old ticking grandfather clock standing silently against weathered limestone wall, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 4, "narration": "என்னா எடுக்க வந்தோம்னு மறந்து போய்டும்!", "on_screen_text": "FORGOT WHAT?", "visual_type": "Cinematic", "visual_prompt": "Empty wooden study table with solitary candle flame flickering in breeze, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 5, "narration": "அட போங்கோ! இது உங்களுக்கு மட்டும் இல்ல,", "on_screen_text": "EVERYONE FEELS", "visual_type": "Cinematic", "visual_prompt": "Intricate brass astrolabe and optical lenses resting on velvet cloth, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 6, "narration": "உலகத்துல எல்லாருக்கும் நடக்குற விந்தை!", "on_screen_text": "UNIVERSAL", "visual_type": "Cinematic", "visual_prompt": "Ancient celestial map carved on polished dark granite, warm lantern glow, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 7, "narration": "Science-ல இதுக்கு பேரு என்னா தெர்யுமா?", "on_screen_text": "WHAT NAME?", "visual_type": "Cinematic", "visual_prompt": "Leather-bound medical journal open under magnifying glass on oak desk, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 8, "narration": "Doorway Effect-னு சொல்வாங்க பாருங்கோ!", "on_screen_text": "DOORWAY EFFECT", "visual_type": "Cinematic", "visual_prompt": "Dramatic glowing threshold doorway silhouetted with volumetric golden rays, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 9, "narration": "நம்ம மூளை ஒரு கதவை தாண்டும் போது,", "on_screen_text": "CROSSING DOOR", "visual_type": "Cinematic", "visual_prompt": "Macro shot of antique brass door handle reflecting glowing golden lights, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 10, "narration": "பழைய chapter முடிஞ்சு புது chapter ஆரம்பிக்குதுன்னு", "on_screen_text": "NEW CHAPTER", "visual_type": "Cinematic", "visual_prompt": "A heavy book turning pages automatically in soft ambient library light, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual break: A pulsing glowing brain neural network refreshing its memory cache, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Morph"},
            {"scene_number": 12, "narration": "முந்தைய அறை நினைவுகளை அப்புடியே erase பண்ணிடும்!", "on_screen_text": "CACHE CLEAR", "visual_type": "Cinematic", "visual_prompt": "Digital data stream dissolving into soft smoke over ancient stone tiles, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 13, "narration": "புது இடத்துக்கு தயாரா இருக்க இந்த reset பண்ணுது.", "on_screen_text": "SYSTEM RESET", "visual_type": "Cinematic", "visual_prompt": "Balanced stone pyramid sculpture in calm Zen sand garden, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 14, "narration": "இதை சரி பண்ண ஒரே ஒரு சிம்பிள் டிப் சொல்றேங்,", "on_screen_text": "SIMPLE FIX", "visual_type": "Cinematic", "visual_prompt": "Small traditional brass oil lamp glowing with clear warm steady flame, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 15, "narration": "மறுபடியும் பழைய ரூமுக்கு போய் நில்லுங்கோ பாருங்கோ!", "on_screen_text": "STEP BACK", "visual_type": "Cinematic", "visual_prompt": "View looking back through carved wooden archway into warm sunlit verandah, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 16, "narration": "அப்புடியே மறந்துபோன விஷயம் சட்டுன்னு நியாபகம் வரும்!", "on_screen_text": "MEMORY BACK", "visual_type": "Cinematic", "visual_prompt": "Golden spark igniting in center of dark crystalline sphere, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 17, "narration": "உங்களுக்கும் இந்த மாதிரி மறதி அனுபவம் உண்டா?", "on_screen_text": "HAPPENED TO YOU?", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian brass bell hanging from carved temple ceiling, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 18, "narration": "கமெண்ட்ல மறக்காம சொல்லுங்கோ பாப்போம்!", "on_screen_text": "COMMENT NOW", "visual_type": "Cinematic", "visual_prompt": "South Indian stone courtyard lit by warm evening oil lamps, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 19, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Vibrant maroon silk banner with gold trim illuminated under warm cinematic stage lights, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    },

    # ── Category: 💰 Money-Saving & Smart Living Tricks ──
    {
        "title": "AC 24 டிகிரில வச்சா கரண்ட் பில் 25% குறையும்! Power Saving Hack! ⚡",
        "description": "AC 24 degrees electricity power saving calculation explained in Nellai Tamil dialect by VJ. #MoneySavingTamil #SimpleTipsByVJ",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Air_conditioning#Energy_consumption",
        "original_news_headline": "AC 24 டிகிரில வச்சா கரண்ட் பில் 25% குறையும்! Power Saving Hack! ⚡",
        "original_news_url": "https://en.wikipedia.org/wiki/Air_conditioning#Energy_consumption",
        "relevant_links": ["https://en.wikipedia.org/wiki/Air_conditioning#Energy_consumption"],
        "hook": "AC 24 டிகிரில வச்சா கரண்ட் பில் 25% குறையும் தெர்யுமா? ⚡",
        "summary": "Setting AC to 24C saves 6% power per degree compared to running at 18C.",
        "sub_category": "💰 Money-Saving & Smart Living Tricks",
        "breaking_news_level": 9,
        "keywords": ["AC power saving", "Electricity bill hack", "Nellai Tamil", "Simple Tips by VJ"],
        "hashtags": ["#MoneySaving", "#ElectricityBill", "#LifeHackTamil", "#SimpleTipsByVJ"],
        "comment_bait_question": "உங்க வீட்டு AC-யை எத்தன டிகிரில வைப்பீங்க? 18-ஆ இல்ல 24-ஆ? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே வெயில் காலத்துல", "on_screen_text": "SUMMER HEAT", "visual_type": "Cinematic", "visual_prompt": "Sunlight glaring intensely through woven palm leaf window blinds, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "AC போட்டதும் சில்லுனு இருக்கணும்னு", "on_screen_text": "CHILL AIR", "visual_type": "Cinematic", "visual_prompt": "Sleek modern AC vent blowing subtle visible cool air mist with blue ambient lighting, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 3, "narration": "ரிமோட்ல 18 டிகிரில வச்சுடுவீங்க இல்லியா?", "on_screen_text": "18 DEGREES", "visual_type": "Cinematic", "visual_prompt": "Modern sleek AC remote display glowing brightly with digital number 18, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 4, "narration": "அட போங்கோ! மாசம் கடைசில கரண்ட் பில்", "on_screen_text": "BIG BILL", "visual_type": "Cinematic", "visual_prompt": "Electricity bill document resting on teak table beside an ancient brass coin purse, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "வந்து நிக்கிறப்ப கண்ணுல தண்ணியே வந்துடும்!", "on_screen_text": "SHOCKING COST", "visual_type": "Cinematic", "visual_prompt": "Digital electric meter display spinning with red warning indicator lights, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 6, "narration": "BEE அதாவது இந்திய அரசு ஆய்வுல", "on_screen_text": "GOVT STUDY", "visual_type": "Cinematic", "visual_prompt": "Official energy star rating certificate sticker on sleek appliance surface, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 7, "narration": "என்ன தெரியுமா சொல்றாங்க?", "on_screen_text": "SECRET FACT", "visual_type": "Cinematic", "visual_prompt": "Warm volumetric beam illuminating clean wooden desk with energy charts, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 8, "narration": "நீங்க AC-ல ஒரு டிகிரி கூட்ட கூட்ட,", "on_screen_text": "EACH DEGREE", "visual_type": "Cinematic", "visual_prompt": "Digital thermostat knob clicking upward from 20 to 24 with golden light, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 9, "narration": "6% கரண்ட் மிச்சமாகும் பாருங்கோ!", "on_screen_text": "SAVE 6%", "visual_type": "Cinematic", "visual_prompt": "Stack of fresh Indian currency notes tied with golden thread on brass tray, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 10, "narration": "அப்போ 18-ல இருந்து 24 டிகிரில வெச்சா,", "on_screen_text": "SET 24C", "visual_type": "Cinematic", "visual_prompt": "Digital temperature reading 24C in calming emerald green font on sleek wall unit, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual shift: A wooden ceiling fan spinning smoothly with gentle rhythmic breeze, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Morph"},
            {"scene_number": 12, "narration": "மொத்தமா 25% கரண்ட் பில் அப்புடியே குறையும்!", "on_screen_text": "25% SAVINGS", "visual_type": "Cinematic", "visual_prompt": "Glowing 3D pie chart showing 25% energy reduction sliced cleanly, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 13, "narration": "கூடவே ஒரு சீலிங் ஃபேனை கொஞ்சூம்", "on_screen_text": "CEILING FAN", "visual_type": "Cinematic", "visual_prompt": "Traditional South Indian wooden ceiling fan circulating cool air across verandah, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 14, "narration": "slow speed-ல ஓட விட்டீங்கன்னா,", "on_screen_text": "SLOW SPEED", "visual_type": "Cinematic", "visual_prompt": "White linen curtains fluttering softly in cool indoor breeze, warm afternoon sun, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 15, "narration": "குளிர்ச்சி ரூம் முழுக்க சமமா பரவிடும்!", "on_screen_text": "EVEN COOLING", "visual_type": "Cinematic", "visual_prompt": "Comfortable South Indian bedroom setting with terracotta floor tiles and cool ambiance, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 16, "narration": "உடம்புக்கும் சளி பிடிக்காம ஆரோக்கியமா இருக்கும் பாருங்கோ!", "on_screen_text": "HEALTHY SLEEP", "visual_type": "Cinematic", "visual_prompt": "Neat cotton pillows and brass water jug on teak bedside table, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 17, "narration": "உங்க வீட்ல AC எத்தன டிகிரில வைப்பீங்க?", "on_screen_text": "YOUR SETTING?", "visual_type": "Cinematic", "visual_prompt": "Close-up of sleek AC remote on wooden bedside table, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 18, "narration": "கமெண்ட்ல மறக்காம உங்க பதிலை சொல்லுங்கோ!", "on_screen_text": "COMMENT NOW", "visual_type": "Cinematic", "visual_prompt": "Traditional brass oil lamp flickering beside temple stone steps, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 19, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Vibrant maroon silk banner with gold trim illuminated under warm cinematic stage lights, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    },

    # ── Category: 🌍 Mysterious History & Culture Secrets ──
    {
        "title": "தஞ்சை பெரிய கோவில் நிழல் தரையில் விழாதா? Thanjavur Mystery! 🏛️",
        "description": "Thanjavur Brihadisvara temple shadow and 80-tonne capstone architectural mystery explained in Nellai Tamil by VJ. #ThanjavurTamil #SimpleTipsByVJ",
        "use_case_evidence_url": "https://en.wikipedia.org/wiki/Brihadisvara_Temple,_Thanjavur#Architecture",
        "original_news_headline": "தஞ்சை பெரிய கோவில் நிழல் தரையில் விழாதா? Thanjavur Mystery! 🏛️",
        "original_news_url": "https://en.wikipedia.org/wiki/Brihadisvara_Temple,_Thanjavur#Architecture",
        "relevant_links": ["https://en.wikipedia.org/wiki/Brihadisvara_Temple,_Thanjavur#Architecture"],
        "hook": "தஞ்சை பெரிய கோவில் நிழல் தரையில் விழாதா தெர்யுமா? 🏛️",
        "summary": "The vimana shadow falls on the temple structure itself, not ground outside, a 1000-year Chola marvel.",
        "sub_category": "🌍 Mysterious History & Culture Secrets",
        "breaking_news_level": 9,
        "keywords": ["Thanjavur temple", "Brihadisvara mystery", "Chola architecture", "Nellai Tamil"],
        "hashtags": ["#ThanjavurTemple", "#TamilHistory", "#CholaEmpire", "#SimpleTipsByVJ"],
        "comment_bait_question": "தஞ்சை பெரிய கோவிலை நேர்ல போய் பாத்திருக்கீங்களா? கமெண்ட்ல சொல்லுங்கோ!",
        "storyboard": [
            {"scene_number": 1, "narration": "நெல்லை மக்களே ஆயிரம் வருஷங்களுக்கு முன்னாடி", "on_screen_text": "1000 YEARS AGO", "visual_type": "Cinematic", "visual_prompt": "Majestic granite temple vimana towering into warm golden hour sky with drifting clouds, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 2, "narration": "ராஜராஜ சோழன் கட்டிய தஞ்சை பெரிய கோவில்", "on_screen_text": "CHOLA PRIDE", "visual_type": "Cinematic", "visual_prompt": "Intricate stone carvings on ancient temple wall glowing with warm golden sunlight, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 3, "narration": "உலக அதிசயங்களை விட பெரிய மர்மம் தெர்யுமா?", "on_screen_text": "GREAT MYSTERY", "visual_type": "Cinematic", "visual_prompt": "Wide courtyard of ancient granite stone temple with dramatic perspective lines, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 4, "narration": "கோவிலின் கோபுர நிழல் தரையில", "on_screen_text": "TEMPLE SHADOW", "visual_type": "Cinematic", "visual_prompt": "Golden hour sun casting sharp geometric shadows along massive stone base, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 5, "narration": "எப்போதுமே விழாதுன்னு பல பேர் சொல்லுவாங்க!", "on_screen_text": "NO SHADOW MYTH", "visual_type": "Cinematic", "visual_prompt": "Pristine temple stone platform basking in midday solar brightness, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 6, "narration": "அட போங்கோ! உண்மை என்னான்னு சொல்றேங் பாருங்கோ,", "on_screen_text": "REAL FACT", "visual_type": "Cinematic", "visual_prompt": "Ancient bronze architectural scale ruler and measuring thread on granite block, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 7, "narration": "நிழல் கண்டிப்பா விழும்,", "on_screen_text": "SHADOW FALLS", "visual_type": "Cinematic", "visual_prompt": "Soft evening shadow draping over the lower terraced levels of stone vimana, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 8, "narration": "ஆனா வெளி வளாக தரையில விழாம,", "on_screen_text": "ON THE BASE", "visual_type": "Cinematic", "visual_prompt": "Massive monolithic granite plinth stepping upward with precision interlocking joints, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 9, "narration": "கோவிலின் பிரம்மாண்ட அடித்தளத்து மேலேயே விழும்!", "on_screen_text": "CHOLA DESIGN", "visual_type": "Cinematic", "visual_prompt": "Aerial view of temple base absorbing geometry of shadow within its own perimeter, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 10, "narration": "அப்புடி ஒரு துல்லியமான கட்டட கலை விந்தை!", "on_screen_text": "PERFECT MATH", "visual_type": "Cinematic", "visual_prompt": "Sacred geometry diagrams etched into ancient palm leaf manuscript with gold ink, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 11, "narration": "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!", "on_screen_text": "PATTERN INTERRUPT", "visual_type": "PATTERN_INTERRUPT", "visual_prompt": "Sudden visual shift: The 80-tonne monolithic cupola stone glowing against a star-studded night sky, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Morph"},
            {"scene_number": 12, "narration": "கோபுர உச்சி மேல இருக்கிற கும்பக்கல்", "on_screen_text": "80 TON STONE", "visual_type": "Cinematic", "visual_prompt": "Extreme low angle view of monolithic spherical capstone perched 216 feet high, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 13, "narration": "ஒரே பாறையில செதுக்கப்பட்ட 80 டன் எடை!", "on_screen_text": "SINGLE GRANITE", "visual_type": "Cinematic", "visual_prompt": "Raw unpolished dark granite rock showing rich mineral veining under spotlight, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 14, "narration": "கிரேன் எதுவுமே இல்லாத காலத்துல", "on_screen_text": "NO CRANES", "visual_type": "Cinematic", "visual_prompt": "Rope-tied timber scaffolding and stone rollers resting on earthen ramp, 9:16 vertical, no humans.", "camera_motion": "Orbit", "transition": "Match cut"},
            {"scene_number": 15, "narration": "6 கிலோமீட்டர் தூரத்துக்கு மண் பாதை அமைச்சு", "on_screen_text": "6 KM RAMP", "visual_type": "Cinematic", "visual_prompt": "Historic rendering of gradual incline earthen ramp leading to temple height, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 16, "narration": "யானைகளை வெச்சு உருட்டி கொண்டுபோய் வெச்சாங்களாம்!", "on_screen_text": "HISTORIC FEAT", "visual_type": "Cinematic", "visual_prompt": "Ancient bronze temple bell tolling with golden reverberations across stone corridor, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 17, "narration": "நம்ம தமிழர்களின் இந்த அறிவியல் திறமை வியப்பா இருக்கு இல்லியா?", "on_screen_text": "TAMIL PRIDE", "visual_type": "Cinematic", "visual_prompt": "Traditional brass oil lamps glowing continuously in ancient sanctum corridor, 9:16 vertical, no humans.", "camera_motion": "Dolly-in", "transition": "Match cut"},
            {"scene_number": 18, "narration": "நீங்க தஞ்சை பெரிய கோவில் போயிருக்கீங்களா?", "on_screen_text": "HAVE YOU VISITED?", "visual_type": "Cinematic", "visual_prompt": "Wide vista of temple gopuram illuminated at twilight with deep blue sky, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"},
            {"scene_number": 19, "narration": "கமெண்ட்ல மறக்காம உங்க பதிலை சொல்லுங்கோ!", "on_screen_text": "COMMENT NOW", "visual_type": "Cinematic", "visual_prompt": "South Indian temple stone courtyard lit by warm evening oil lamps, 9:16 vertical, no humans.", "camera_motion": "Pan", "transition": "Match cut"},
            {"scene_number": 20, "narration": "மறக்காம Simple Tips by VJ Subscribe தட்டுங்கோ!", "on_screen_text": "SUBSCRIBE VJ", "visual_type": "Cinematic", "visual_prompt": "Vibrant maroon silk banner with gold trim illuminated under warm cinematic stage lights, 9:16 vertical, no humans.", "camera_motion": "Slow zoom", "transition": "Match cut"}
        ]
    }
]

for item in additional_scripts:
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
        "PATTERN": "pat-urn"
    }

# Append the new scripts
scripts = additional_scripts + scripts

with open(FALLBACK_FILE, "w", encoding="utf-8") as f:
    json.dump(scripts, f, indent=2, ensure_ascii=False)

print(f"✅ Successfully appended scripts! Total scripts now: {len(scripts)}")
for i, s in enumerate(scripts):
    wc = len(s.get("script", "").split())
    chunks = len(s.get("subtitle_chunks", []))
    sub = s.get("sub_category", "")
    title = s.get("title", "")
    print(f"[{i:02d}] Category: {sub:40s} | Words: {wc:3d} | Chunks: {chunks:2d} | Title: {title[:40]}")
