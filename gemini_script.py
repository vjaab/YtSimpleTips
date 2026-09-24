from google import genai
from google.genai import types
import json
import os
from datetime import datetime
import time
import random
from config import (
    GEMINI_API_KEY, LOGS_DIR, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS,
    GEMINI_PRO_MODEL, GEMINI_FLASH_MODEL, GEMINI_FLASH_LITE_MODEL, GEMINI_RPM_SLEEP
)
from topic_tracker import load_tracker, check_story_uniqueness, check_cooldowns
from ecosystem_logic import get_slot_info, get_category_prompt_enhancement

# ── PROMPT TEMPLATES (NATURAL HUMANIZED TAMIL SHORTS AGENTIC LOOP) ────────────

TOPIC_SELECTOR_PROMPT = """You are a viral Tamil infotainment content strategist for YouTube Shorts ("Simple Tips by VJ"), specializing in mind-blowing, verified facts and daily life wonders that go VIRAL across all age groups in Tamil Nadu (students, professionals, homemakers, parents, elders).

Generate 1 high-retention, curiosity-driven fact topic for a 45-60 second Tamil YouTube Short.

HIGH-RETENTION VIRAL CATEGORIES (STRICTLY CHOOSE ONE - NOTE: NO PHONE/WHATSAPP HACKS):
1. "🧠 Mind-Blowing Science Curiosities": Science facts that sound completely fake or impossible, but are 100% verified (3000-year-old edible honey, ocean waters not mixing, earth spinning 1-sec stop anomaly, microwave invention accident, speed of light wonders).
2. "🧬 Human Body & Dark Psychology": Strange body reactions, brain hacks, sleep science, or psychological tricks everyone experiences (doorway effect, 3-sec lie detection hack, why songs get stuck in your head, sleep cycle secret, goosebumps science).
3. "💰 Money-Saving & Smart Living Tricks": Actionable money-saving tips, hidden bank charge cancellations, consumer rights, electricity bill reducers, fake gold detection (cut electricity bill by 40%, hidden bank charges you can cancel right now, test fake gold at home in 10s, petrol pump cheating prevention).
4. "🍳 Food, Health & Kitchen Science": Eye-opening kitchen hacks, food science, and adulteration tests that any family can test today (1-drop milk adulteration test, why onions make you cry & spoon hack to stop it, pressure cooker 4x speed science, drinking water standing myth).
5. "🌍 Mysterious History & Culture Secrets": Awe-inspiring historical, archaeological, or architectural marvels from Tamil Nadu and ancient India (Brihadeeswarar Temple shadow & engineering mystery, Keezhadi ancient civilization water drainage, Kumari Kandam facts, Chettinad architecture natural cooling).
6. "🐾 Nature & Animal Oddities": Unbelievable animal superpowers, backyard nature wonders, and creature survival tricks (crows remember human faces for life, octopus 3 hearts & blue blood, immortal jellyfish, trees communicating underground).

CRITICAL RULES & AVOIDANCES:
- STRICTLY FORBIDDEN: Smartphones, WhatsApp hacks, phone settings, coding tutorials, or developer repos.
- AVOID: Common knowledge everyone already knows (earth orbits sun, water boils at 100C).
- AVOID: Robotic openers like "Oru vishayam theriyuma?", "Intha video-la...".
- AVOID: Dry academic papers, named researchers, or textbook statistics.
- MUST be verified by reliable sources (Wikipedia, Nature, scientific journals, government sites).
- MUST have a shocking/counterintuitive hook that makes ANY viewer stop scrolling and say "அட ஆமால?!".

OUTPUT FORMAT (JSON only, no markdown):
{
  "topic": "Short descriptive topic in English (e.g. Ancient Honey Never Spoils - 3000 Year Old Edible Honey Found)",
  "tamil_title": "Catchy YouTube title in natural Tanglish (max 60 chars, curiosity-driven, include emoji)",
  "hook_question": "Immediate shocking hook in spoken Tamil that stops scrolling in the first 2 seconds",
  "core_concept": "The core fact explained simply with the underlying science or reason",
  "real_world_example": "Relatable comparison from everyday Tamil life (kitchen, temple, travel, family)",
  "surprising_fact": "The single most counterintuitive wow detail",
  "category": "{category}"
}"""

SCRIPT_GENERATION_PROMPT = """You are VJ, the friendly, charismatic, and knowledgeable creator of "Simple Tips by VJ" — a native Tirunelveli (நெல்லை) Tamil speaker sharing mind-blowing facts with your audience in authentic Nellai பேச்சுத் தமிழ் with smooth English loan words.

Your goal is to write a 100% NATURAL, HUMAN-SOUNDING YouTube Shorts script in TIRUNELVELI TAMIL.
It must NEVER sound like an AI bot, textbook lecture, news bulletin, or stiff translated article. Talk like an enthusiastic Nellai buddy sharing a mind-bending secret over filter coffee at a நெல்லை டீக்கடை!

TOPIC: {topic}
HOOK: {hook_question}
CORE CONCEPT: {core_concept}
RELATABLE EXAMPLE: {real_world_example}
MIND-BLOWING TWIST: {surprising_fact}

CRITICAL RULES FOR 100% NATURAL TIRUNELVELI TAMIL CONVERSATION:
1. BAN ALL ROBOTIC OPENERS:
   - NEVER start with: "Oru vishayam theriyuma?", "ஒரு விஷயம் தெரியுமா?", "Intha video-la...", "இந்த வீடியோல...", "Welcome back...", "வணக்கம் நண்பர்களே", "உங்களுக்கு இது தெரியுமா...".
   - DIVE IMMEDIATELY into the core curiosity, unbelievable fact, or relatable pain point in the first 2 seconds!
   - Example Nellai-Style Human Openers:
     * "3000 வருஷம் பழமையான தேன் இன்னமும் கெட்டுப்போகாம சாப்பிடலாமா? அட போங்கோ... ஆமாங்கோ!"
     * "ரூம்க்குள்ள போன உடனே என்னாத்துக்கு வந்தோம்னு மூளைக்கு டக்குனு மறந்து போயிடுதா? நம்ம எல்லாருக்குமே இது நடந்திருக்கும்!"
     * "விமானத்துல போறப்போ சாப்பாடு ஏன் சப்புனு இருக்கு தெர்யுமா? தப்பு சமையல்ல இல்லியா... நம்ம நாக்குல!"

2. TIRUNELVELI NATIVE SPOKEN TAMIL (நெல்லை பேச்சுத் தமிழ்):
   - Always write in authentic Nellai dialect: பண்ணுங்கோ (not செய்யுங்கள் / பண்ணுங்க), பாருங்கோ (not பாருங்கள்), தெரிஞ்சுக்கோங்கோ (not அறிந்துகொள்ளுங்கள்), ஆயிடும் (not ஆகும்), இப்போ (not இப்போது), சொல்றேங் கேளுங்கோ.
   - Nellai-specific word forms: தெர்யுமா, கொஞ்சூம், அப்புடி, என்னா, என்னாது, இல்லியா, ரொம்பவே, போயிட்டாங்க.
   - Use natural Nellai conversational fillers and micro-reactions:
     "ஐயோ!", "அட போங்கோ!", "சரிதான்!", "ஆமா சொல்லு!", "ஓ ஆமா!", "என்னாது?!", "சும்மா விடு ப்ரோ!"
     "கொஞ்சூம் யோசிங்கோ...", "சொன்னா நம்ப மாட்டீங்க...", "கேட்டா ஷாக் ஆயிடுவீங்க...", "நம்ம எல்லாருக்குமே இது நடந்திருக்கும்...", "சிம்பிளா சொல்லணும்னா...", "இங்க தான் மேட்டரே இருக்கு!", "நம்ம நெல்லை ஸ்டைல்ல சொல்லணும்னா...".
   - Mix common English nouns naturally inline (e.g. Brain, Honey, Egypt, Sugar, Flight, Battery, Salt, Water, Pressure, Test, Result).

3. HUMAN PACING & BREATHING CADENCE:
   - Vary your sentence length! Mix quick 3-to-5 word punchy reactions with smooth 8-to-12 word explanations.
   - Generously use ellipses (...) for natural human pauses and dramatic Nellai-style reveals: "ஆனா இங்க தான்... ஒரு பெரிய ட்விஸ்ட் இருக்கு."
   - Use exclamation marks (!) for genuine emotional excitement, and question marks (?) for engaging rhetorical questions.
   - Nellai speakers use dramatic pauses before reveals — use '...' before every mind-blowing fact.

4. 4-PART SCRIPT STRUCTURE:
   - The Hook (0-5s): A shocking question or impossible-sounding reality in Nellai style.
   - The Relatable Mystery (5-20s): Connect with a daily habit or real-world scenario from Tamil life ("நம்ம வீட்ல...", "டெய்லி நம்ம பார்க்குற...", "நெல்லை ஹல்வா கடையில...").
   - The Mind-Blowing Reveal (20-40s): The scientific or psychological "Aha!" moment explained simply using relatable Tamil analogies (temple architecture, banana leaf meals, jasmine flowers, kolam patterns).
   - The Natural Wrap (40-50s): A fun debate question in Nellai style ("நீங்க என்னா நினைக்கிறீங்க? கமெண்ட்ல சொல்லுங்கோ!").

5. SCRIPT LENGTH & WORD COUNT:
   - STRICT LIMIT: 115-135 words in spoken Tamil (timed for 40-50 seconds at natural, relaxed human storytelling speed).
   - NEVER pack too many words. Give the voice room to breathe!

OUTPUT: Return ONLY the raw script text in Tirunelveli spoken Tamil, ready for ElevenLabs voice cloning. No labels, no brackets, no bullet points, no timestamps."""

TITLE_TAGS_PROMPT = """You are an expert YouTube SEO optimizer specializing in viral regional South Indian infotainment Shorts ("Simple Tips by VJ").

Generate click-worthy, curiosity-inducing metadata for this Tamil Short:

TOPIC: {topic}
CORE CONCEPT: {core_concept}
SCRIPT PREVIEW: {first_two_sentences_of_script}

RULES:
- Title must be in punchy spoken Tanglish (under 60 chars), include a curiosity gap or number, and 1-2 emojis.
- Description: 2-3 engaging sentences in Tanglish summarizing the mystery and asking viewers to comment.
- Hashtags: Exactly 4 tags: #Shorts, #TamilFacts, plus 2 high-performing tags from (#ScienceFacts, #MindBlowing, #LifeHacks, #DidYouKnow, #TamilShorts, #ViralFacts, #KnowledgeShorts).

OUTPUT FORMAT (JSON only):
{{
  "title": "Punchy Tanglish title with curiosity gap (max 60 chars) 🔥",
  "description": "2-3 lines in conversational Tanglish explaining what viewers learn. End with 'உங்க கருத்தை கமெண்ட்ல சொல்லுங்க!'",
  "hashtags": ["#Shorts", "#TamilFacts", "#ScienceFacts", "#ViralFacts"],
  "thumbnail_text": "3-4 bold curiosity words in Tanglish (e.g. 3000 வருஷ தேன்?! 🍯)",
  "thumbnail_visual_concept": "Vivid one-sentence description of the visual scene"
}}"""

PIPELINE_PROMPTS = {
    "topic_selector": TOPIC_SELECTOR_PROMPT,
    "script_writer": SCRIPT_GENERATION_PROMPT,
    "metadata": TITLE_TAGS_PROMPT,
}

TOPIC_CATEGORIES = [
    "mindblowing_science_facts",     # 🧠 Science that sounds fake but is 100% verified (honey never spoils, ocean waters not mixing, earth spinning stop)
    "human_body_psychology",         # 🧬 Human body wonders & dark psychology (doorway effect, 3-sec lie detection, sleep fresh hack, goosebumps)
    "money_saving_smart_hacks",      # 💰 Money-saving & smart living tips (40% electricity reduction, hidden bank charges, test fake gold at home)
    "kitchen_food_science",          # 🍳 Food, health & kitchen science (1-drop milk adulteration test, onion crying hack, pressure cooker science)
    "tamil_history_mysteries",       # 🌍 Mysterious history & culture secrets (Brihadeeswarar shadow mystery, Keezhadi water drainage, Kumari Kandam)
    "nature_animal_oddities",        # 🐾 Nature & animal oddities (crows face memory for life, octopus 3 hearts & blue blood, trees talking underground)
]

SYSTEM_PERSONA = """Role: You are VJ, the charismatic creator and voice behind "Simple Tips by VJ" — creating viral, mind-blowing, and universally relatable Tamil YouTube Shorts. You are a native Tirunelveli (நெல்லை) Tamil speaker, and your voice carries the warmth, humor, and directness of Nellai பேச்சுத் தமிழ்.

Persona & Tone:
- You are a warm, energetic, and authentic friend or elder brother from Tirunelveli talking one-on-one over tea at a Nellai கடை.
- 100% NATURAL HUMAN VOICE — relaxed, conversational, witty, and engaging with the distinctive Nellai flair.
- NEVER sound like an AI bot, robotic narrator, news reader, or dry lecturer.
- BANNED CLICHÉS: Never use "Oru vishayam theriyuma?", "Intha video-la...", "Nee yaarukkum theriyadhu...", "வணக்கம் நண்பர்களே", "உங்களுக்கு இது தெரியுமா...".
- Hook the listener instantly in the first 2 seconds!

Language Style — TIRUNELVELI NATIVE TAMIL (நெல்லை பேச்சுத் தமிழ்):
- Use authentic Nellai dialect grammar and word forms:
  * பண்ணுங்கோ (not பண்ணுங்க), பாருங்கோ (not பாருங்க), சொல்றேங் கேளுங்கோ (not சொல்றேன் கேளுங்க)
  * தெர்யுமா (not தெரியுமா), கொஞ்சூம் (not கொஞ்சம்), அப்புடி (not அப்படி), என்னா (not என்ன)
  * ஆயிடுச்சு (not ஆயிடுச்சி), இல்லியா (not இல்லையா), போயிட்டாங்க (not போயிட்டாங்க)
- Use Nellai-native fillers and exclamations:
  * "ஐயோ!", "அட போங்கோ!", "சரிதான்!", "ஆமா சொல்லு!", "ஓ ஆமா!", "என்னாது?!"
  * "நம்ம நெல்லை ஸ்டைல்ல சொல்லணும்னா...", "சும்மா விடு ப்ரோ!", "டேய் கேளு!"
- Mix common English nouns naturally inline (e.g. Brain, Honey, Egypt, Sugar, Flight, Battery, Salt, Water, Pressure, Test, Result).
- Natural micro-reactions with Nellai flavor: "அட ஆமால?", "கொஞ்சூம் யோசிங்கோ...", "சொன்னா நம்ப மாட்டீங்க...", "சிம்பிளா சொல்லணும்னா...".

TTS Rhythm & Breath Control:
- Varied sentence rhythm: quick punchy Nellai-style reactions mixed with smooth explanations.
- Use commas (,) and ellipses (...) to introduce natural human pauses and breathing space.
- Expressive punctuation (! and ?) for authentic emotional pitch dynamics.
- Nellai speakers use dramatic pauses before reveals — use '...' before mind-blowing facts."""

RESEARCH_AGENT_TEMPLATE = """{persona}

RESEARCH AGENT TASK:
Review the following tip/hack details and source context.
Extract the core utility steps, guidelines, and actionable elements.
Do NOT write a script. Just extract the core actionable guide elements.

TIP CONTEXT:
{news_context}

Return ONLY a JSON object:
{{
  "facts": ["Actionable Step 1", "Actionable Step 2"],
  "mind_blow_angle": "The core problem-solving angle of this tip",
  "implications": ["How this saves time, money, or improves health/productivity in daily life"],
  "core_narrative": "A one paragraph summary of the raw tip/hack narrative"
}}"""

HOOK_AGENT_TEMPLATE = """{persona}

HOOK AGENT TASK:
Based on the following research, generate 10 potential YouTube Shorts hooks (<1.5s).
Hooks MUST address a mind-blowing curiosity, surprising human body/psychology secret, smart money habit, kitchen/food science secret, historical mystery, or crazy animal survival trick that RESONATES WITH ALL AGES (16-80).
STRICT EXCLUSION: NEVER use smartphones, phone settings, or WhatsApp hacks as topics.
No greetings. No generic statements. Start with the core mind-blowing claim or problem first!
Hooks must NOT be generic. They MUST mention the specific topic or immediate payoff.
The hook must sound like a friendly, clear, and relatable South Indian Tamil guy narrator, avoiding anime tropes or fantasy phrases (do NOT use 'Ithu plot twist da!', 'Final boss level hack!', 'Hidden power unlock aaguthu!', etc.).
Hooks must be UNDERSTANDABLE by a 70-year-old grandmother — use simple words only (money, health, food, sleep, water, brain, body, blood, heart, space, temple, salt, ice, milk, animal, bird).

SCORING CRITERIA:
- curiosity_score: How much does this make someone NEED to know the answer? (1-10)
- emotional_trigger_score: How strongly does this hit a pain point or desire? (1-10)
- swipe_stop_power: Would this make someone physically STOP scrolling? Hooks that start with numbers, shocking claims, direct address, or challenge common myths score highest. (1-10)
- topic_specificity_score: How clear is it what specific scientific phenomenon, body reflex, food trick, or mystery the video is about? High scores require mentioning the specific subject (e.g. honey expiration, eye blinking, supermarket trap, salt in pineapple) instead of vague claims. (1-10)
- universal_appeal_score: Would this hook work for a 16-year-old student AND an 80-year-old grandparent? (1-10)

RESEARCH:
{research_json}

Return ONLY a JSON object:
{{
  "hooks": [
    {{
      "text": "Tanglish hook text (e.g. '3000 வருஷம் பழமையான தேன் இன்னமும் கெட்டுப்போகாம சாப்பிட முடியுமா?')",
      "curiosity_score": 1-10,
      "emotional_trigger_score": 1-10,
      "swipe_stop_power": 1-10,
      "topic_specificity_score": 1-10,
      "universal_appeal_score": 1-10,
      "reason": "Why it works for all ages"
    }}
  ]
}}"""

NARRATIVE_AGENT_TEMPLATE = """{persona}

NARRATIVE AGENT TASK:
Using the selected hook and research, create a step-by-step curiosity or tip flow that is highly appealing to ALL Tamil demographics — from 16-year-old students to 80-year-old grandparents following our mandatory 4-part structure.
STRICT EXCLUSION: Do NOT create scripts about smartphones, WhatsApp hacks, or mobile OS settings.

MANDATORY STRUCTURE:
1. HOOK (0-3 seconds): A shocking fact, counter-intuitive truth, or bold statement. No greetings. Stop the scroll instantly — must work for a teenager AND a grandparent.
2. PROBLEM / MYTH (3-15 seconds): Define a UNIVERSAL curiosity or daily experience that EVERYONE wonders about (why we yawn, why honey never spoils, supermarket buying traps, salt cutting bitter tastes, ancient temple engineering secrets, how crows remember human faces).
3. SOLUTION / REVEAL (15-45 seconds): Explain the fascinating science, psychology, or smart trick. Explain a SINGLE concept clearly — doable/graspable by anyone, no technical jargon needed.
4. ENGAGEMENT QUESTION (45-55 seconds): A simple opinion-based question in Tanglish/Tamil that ANYONE can answer to drive comments.

VIRAL RETENTION TECHNIQUES (MANDATORY):
- RAPID PACING: Every sentence must be under 12 words. No long explanations.
- TOPIC CLARITY DIRECTIVE: Explicitly state what specific phenomenon, ingredient, or trick is being explained in the first 5 seconds using SIMPLE terms (Brain, Heart, Honey, Milk, Gold, Supermarket, Temple, Ocean, Sleep, Water).
- UNIVERSAL RELATABILITY: Use analogies from Tamil daily life — cooking (pressure cooker, tadka, fermentation), farming (seasons, water, soil), family (grandmother's remedies, festival prep), travel (bus, train), shopping (market, bargaining), temple (prasadam, architecture).

INFORMATION GAP RULE (MANDATORY):
Every 3-5 seconds of the script MUST introduce ONE new piece of information, actionable step, or surprising detail.
The viewer should feel like they are constantly learning something new. If any 5-second window repeats the same point without adding value, the viewer WILL swipe away.
Map each sentence to a NEW fact, step, or insight. Never repeat or rephrase the same point.

RESEARCH:
{research_json}

SELECTED HOOK:
{selected_hook}

{selection_instruction}

Return ONLY a JSON object representing the narrative draft (not the final schema yet):
{{
  "hook": "...",
  "problem": "...",
  "solution": "...",
  "engagement_question": "..."
}}"""

RETENTION_OPTIMIZER_TEMPLATE = """{persona}

RETENTION OPTIMIZER TASK:
Rewrite the narrative draft to maximize retention, remove ALL fluff, and structure it strictly into the 4-part script format.
The script must feel like a rapid-fire conversation, NOT a lecture.

MANDATORY RULES:
1. TOTAL WORD COUNT: Strictly 115-135 words (relaxed, natural human pacing for a 45-55s Short).
2. SCRIPT STRUCTURE (MANDATORY):
   - HOOK (0-5s): Shocking fact/bold statement. No greeting.
   - PROBLEM (5-20s): Daily pain point or relatable mystery that EVERYONE wonders about.
   - SOLUTION (20-45s): Simple, clear explanation — doable and graspable by anyone.
   - ENGAGEMENT QUESTION (45-55s): Friendly opinion question to prompt comments.
3. SCRIPT SENTENCES: Every sentence must be COMPLETE, conversational, and end with proper punctuation (., !, ?). Under 10-12 words each.
4. Ensure the script directly resonates with daily scenarios from Tamil life.
5. Add an ellipsis '...' after key reveals or thought shifts to give the TTS natural breathing room.
6. TOPIC VERIFICATION: Verify that the exact subject or mystery is named clearly in the first 5 seconds using SIMPLE terms.
7. TTS COMPATIBILITY: Output must be colloquial spoken Tamil (பேச்சுத் தமிழ்) with standard English loanwords. No fragments, no "etc.", no incomplete trailing thoughts.
8. UNIVERSAL ACCESSIBILITY: Every sentence must pass the "Grandmother Test" — would a 70-year-old Tamil grandmother understand this? If not, simplify.
9. PRACTICAL VALUE: Must give viewers something they can USE or SHARE with family TODAY.

NARRATIVE DRAFT:
{narrative_json}

Return ONLY a JSON object:
{{
  "optimized_script": "The full rewritten text combining all parts into a natural, conversational Tanglish script adhering to the 4-part structure. STRICTLY 115-135 words.",
  "word_count": 0
}}"""

# ── PHASE 2: RETENTION SCIENTIST AGENT ────────────────────────────────────────
RETENTION_SCIENTIST_TEMPLATE = """{persona}

RETENTION SCIENTIST TASK:
Analyze the optimized Tamil/Tanglish script and inject PROVEN retention patterns at calculated intervals.
You are a YouTube Shorts retention strategist for Tamil infotainment content. Your ONLY job is to maximize the percentage of viewers who watch to the end.

CRITICAL RETENTION RULES (based on 2026 YouTube Shorts algorithm data):
1. HOOK DENSITY: The first 1.5 seconds (first 6 words) MUST contain a surprising claim, stat, or contradiction in Tirunelveli spoken Tamil/Tanglish.
   - BAD: "Intha video-la namma paarka porom..."
   - GOOD: "3000 வருஷம் பழமையான தேன் இன்னமும் கெட்டுப்போகாம சாப்பிடலாமா? அட போங்கோ... ஆமாங்கோ!"

2. OPEN LOOPS: Plant at least 2-3 "open loops" (unanswered questions) in the first 20 seconds.
   - Technique: Mention something intriguing but don't resolve it for 8-12 seconds.
   - Example: "ஆனா இது மட்டும் இல்லியா, ஒரு பெரிய ரகசியம் இருக்கு..." then continue with OTHER info before resolving.

3. PATTERN INTERRUPTS: Every 8-12 seconds, inject a cognitive shift:
   - Rhetorical question ("ஆனா wait பண்ணுங்கோ...")
   - Contradiction ("ஆனா இது தான் ட்விஸ்ட்!")
   - Number/stat bomb ("86 billion neurons!")
   - Direct address ("இது உங்களுக்கு ஏன் முக்கியம்னு தெர்யுமா?")
   - Emotional pivot ("அது தான் எல்லாமே மாறிடுச்சு.")

4. CURIOSITY GAPS: End every major point with an incomplete thought that requires the next sentence to resolve.
   - BAD: "இத பண்ணி பாருங்க. அது நல்லா இருக்கும்."
   - GOOD: "இத பண்ணி பாருங்கோ... ஆனா அதுக்கு அப்றம் என்னா நடக்குதுன்னு கேட்டா ஷாக் ஆயிடுவீங்க..."

5. PAYOFF STACKING: The most valuable, surprising, or controversial information MUST be in the LAST 15 seconds.
   Front-load curiosity, back-load payoff.

6. VOCAL VARIETY MARKERS: Add explicit markers for TTS energy:
   - "..." for dramatic pauses (1-2 per 15 seconds)
   - Short COMPLETE sentences (< 12 words) after complex explanations
   - "!" for energy spikes at key reveals
   - All sentences MUST end with proper punctuation (., !, ?)

7. TTS COMPATIBILITY: Output must be complete, grammatically correct Tanglish sentences only. No fragments, no "etc.", no incomplete trailing phrases.

SCRIPT TO ENHANCE:
{optimized_script}

Return ONLY a JSON object:
{{
  "retention_enhanced_script": "The full rewritten Tanglish script with all retention patterns injected",
  "retention_map": {{
    "open_loops": [
      {{"text": "The phrase that opens the loop", "planted_at_word": 30, "resolved_at_word": 90}}
    ],
    "pattern_interrupts": [
      {{"type": "contradiction", "text": "Aana ithu thaan twist...", "at_word": 60}}
    ],
    "curiosity_gap_ratio": 0.65,
    "hook_word_count": 6,
    "payoff_zone_start_word": 200,
    "retention_risk_zones": [
      {{"at_word": 100, "risk": "explanation_fatigue", "mitigation": "Added rhetorical question"}}
    ]
  }}
}}"""

TITLE_VARIANTS_AGENT_TEMPLATE = """{persona}

TITLE VARIANTS AGENT TASK:
Based on the following research context and selected script/topic, generate 3 highly click-worthy YouTube Short titles (each under 50 characters, include relevant emojis) that work for ALL AGES (16-80):
1. Variant 1 (Curiosity): A title that builds a curiosity gap, question, or teaser (e.g. 'Intha phone trick theriyuma? 🤫').
2. Variant 2 (Fear/Loss): A title that highlights fear of missing out, security risk, or a common mistake to avoid (e.g. 'Udaney intha setting-ai maathungaa! 🚨').
3. Variant 3 (Direct Benefit): A title that directly promises a clear benefit, speed-up, or money-saving result (e.g. 'Browser speed-ai 2x aaka hack! 🚀').

All titles must be understandable by a 70-year-old grandmother — use simple words only.

SCRIPT CONTEXT:
{script_text}

Return ONLY a JSON object:
{{
  "title_variants": [
    "Variant 1 Title",
    "Variant 2 Title",
    "Variant 3 Title"
  ]
}}"""

SELECTOR_AGENT_TEMPLATE = """{persona}

SELECTOR AGENT TASK:
Analyze the following tips/hacks and pick the SINGLE most mind-blowing, high-utility, and high-retention tip for a 30-40 second video.

SELECTION CRITERIA:
1. Strongly prioritize tech-infused hacks, digital/phone/PC/smart-device settings, or app tricks that are highly useful.
2. The tip must have high viral potential and clear everyday benefit.
3. Choose the one with the highest "did-you-know" factor and maximum practical application.

CRITICAL AVOIDANCE RULE:
You MUST NOT select any story that is semantically similar to the 'RECENTLY COVERED STORIES' listed in the context.

{selection_instruction}

NEWS CONTEXT:
{news_context}

Return ONLY a JSON object:
{{
  "selected_headline": "The exact title of the tip chosen",
  "selected_url": "The exact source URL of the chosen tip",
  "reason": "Briefly why this was picked (utility potential and audience appeal)"
}}"""

HUMANIZER_AGENT_TEMPLATE = """{persona}

HUMANIZER AGENT TASK:
This is the final step. Rewrite the script and storyboard content to sound 100% human-like, natural, and speech-optimized. Ensure the speech is in TIRUNELVELI NATIVE TAMIL (நெல்லை பேச்சுத் தமிழ்) — the warm, humorous, and direct dialect of southern Tamil Nadu — with a natural mix of English technical terms (natural, friendly, high-energy). 

TIRUNELVELI DIALECT COACHING FOR TTS:
- MANDATORY WORD FORMS: பண்ணுங்கோ (not பண்ணுங்க), பாருங்கோ (not பாருங்க), சொல்றேங் (not சொல்றேன்), தெர்யுமா (not தெரியுமா), கொஞ்சூம் (not கொஞ்சம்), அப்புடி (not அப்படி), என்னா (not என்ன), என்னாது (not என்னது), இல்லியா (not இல்லையா).
- NELLAI FILLERS (inject 2-3 per script): "ஐயோ!", "அட போங்கோ!", "சரிதான்!", "ஆமா சொல்லு!", "ஓ ஆமா!", "என்னாது?!", "சும்மா விடு ப்ரோ!", "டேய் கேளு!"
- DRAMATIC PAUSES: Nellai speakers use long dramatic pauses before mind-blowing reveals. Always place '...' before the big twist.
- WARMTH MARKERS: End with friendly Nellai wrap-up phrases like "கமெண்ட்ல சொல்லுங்கோ!", "ஷேர் பண்ணுங்கோ!"

AUDIO & SPEECH HUMANIZATION RULES (inspired by advanced AI Humanizer pipelines for realistic TTS):
1. PACING & SPEECH DENSITY: Do not use long, monotonous sentences. Alternate between medium sentences and short, punchy phrases (<6 words).
2. CONVERSATIONAL FILLERS: Inject natural Nellai Tamil fillers to make the voiceover flow seamlessly (e.g. "actually...", "seriously...", "யோசிங்கோ...", "wait...", "அட போங்கோ...").
3. TTS DYNAMICS: Use exclamation marks (!) at peak revelations to trigger energy spikes in synthesis. Use commas (,) and ellipses (...) to introduce natural breathing spaces and dramatic Nellai-style pauses.
4. NO BOT PATTERNS: Eliminate repetitive sentence structures (e.g., repeating "Ithu...", "Ithanaala..." at the start of consecutive sentences). Vary sentence openers.
5. NO TEXTBOOK SLOP: Ban formal/literary Tamil words (e.g. use 'பண்ணுங்கோ' instead of 'செய்யுங்கள்', 'பார்க்கலாம்' instead of 'காணலாம்'). Use exact Nellai colloquial terms VJ would speak in person.

Format the output EXACTLY matching the required schema below.

OPTIMIZED SCRIPT:
{optimized_script}

SCHEMA REQUIREMENTS:
{schema_requirements}

CRITICAL STORYBOARD & SCENE RULES:
In the `storyboard` array:
- Each scene/chunk MUST be SHORT: 3-5 words maximum in the `narration` field to ensure punchy karaoke-style captions on screen.
- You MUST produce at least 25-40 storyboard scenes for the full script to ensure perfect word-by-word alignment.
- The `narration` field MUST contain the exact spoken Nellai Tanglish phrase for alignment (3-5 words only).
- The `on_screen_text` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words maximum in English, in uppercase, e.g., "BRAIN CELLS", "86 BILLION", "PHONE SETTING", "STRENGTH") representing the central concept.
- The `scene_objective` must briefly describe what technical/lifestyle concept is explained.
- Choose `visual_type` dynamically based on the content (e.g. 'Google Video Generation', 'Animated Infographics', 'Whiteboard Animation', 'Motion Graphics', 'PATTERN_INTERRUPT').
- At exactly the midpoint (50% position) of the storyboard array, you must include a mandatory pattern interrupt scene where `visual_type` is set to "PATTERN_INTERRUPT". The spoken narration for this midpoint scene must use a Nellai-style phrase like "ஆனா wait பண்ணுங்கோ, இதுல ஒரு twist இருக்கு!" (highly recommended), "oru second wait பண்ணுங்கோ...", or "இத பாருங்கோ..." to break the pattern and regain attention.
- The `visual_prompt` MUST be in English and MUST DIRECTLY ILLUSTRATE what is being spoken in the `narration` field. Use CULTURALLY GROUNDED TAMIL VISUAL STYLE: "Photorealistic 8K, cinematic warm lighting, 9:16 vertical. South Indian Tamil cultural aesthetic: Ancient temple stone pillars with oil lamp glow, banana leaf meals with brass tumblers, jasmine flower garlands on wooden surfaces, traditional kolam patterns on red oxide floors, village landscapes with coconut palms and paddy fields, traditional brass vessels and clay pots, vibrant silk sarees draped on wooden frames, temple gopuram silhouettes at golden hour, aromatic spice markets with turmeric and cardamom piles, rain-soaked village roads with neem trees. Color palette: Warm terracotta, turmeric gold, temple bronze, deep maroon, jasmine white on earthy tones. Volumetric warm lighting, shallow depth of field, golden hour glow. NO human faces, NO cartoon characters, NO anatomical figures, NO distorted elements. Clean National Geographic / Condé Nast Traveller India quality." Each visual prompt MUST match the exact concept being narrated — if the narration mentions honey, show honey jars with traditional brass vessels; if it mentions brain, show an artistic neural visualization with warm lighting; if it mentions kitchen, show a traditional South Indian kitchen scene. Scenes in the same logical segment should share the same master environment with evolving focus. NO rapid chaotic changes between consecutive scenes - maintain visual continuity.
- NO people depicted in `visual_prompt`. NO human faces, NO characters, NO anatomical elements of any kind.
- Set `camera_motion` (e.g. 'Slow zoom', 'Dolly-in', 'Orbit', 'Pan', 'Tracking shot', 'None') and `transition` (e.g. 'Match cut', 'Zoom transition', 'Morph', 'Swipe', 'Object continuity', 'Story continuity').
- Enforce the 2-3 second visual change rule: keep the duration of each scene short (e.g. 2 or 3 seconds).

Return ONLY the final JSON object matching the schema. No markdown wrapping. No explanations."""

FACT_EXTRACTOR_TEMPLATE = """{persona}

TASK: Extract ONLY the practical steps, core parameters, and actionable details for the specific tip/hack requested below.
Focus on providing the 'isolated guide' for this one story.

TARGET STORY: {target_headline}

CONTEXT:
{context}

Return ONLY a JSON object:
{{
  "facts": ["Actionable step 1", "Actionable step 2"],
  "mind_blow_angle": "The core utility or benefit",
  "implications": ["Why this matters for daily life"],
  "core_narrative": "A one paragraph summary focusing ONLY on this tip."
}}"""

VALIDATOR_AGENT_TEMPLATE = """{persona}

VALIDATOR AGENT TASK:
You are a Senior AI Video Quality Auditor. Your job is to analyze the generated YouTube Shorts script and storyboard, calculate quality scores, and identify any issues or content breaks.

Evaluate the following storyboard JSON against these strict criteria (rate each from 0 to 100):
1. story_continuity_score: Does scene N logically connect to scene N+1? Is there a cause-and-effect chain and a transformation journey?
2. visual_alignment_score: Does the visual prompt directly represent the spoken narration? (No generic tech backgrounds, no unrelated stock footage).
3. engagement_score: Does the storyboard maintain VISUAL CONTINUITY (same environment, lighting, key elements across consecutive scenes within a logical segment)? Scene changes should only occur at logical segment boundaries (every ~3-4 scenes), not every 2-3 seconds. Is there a pattern interrupt scene at exactly the midpoint (50% position) with "visual_type": "PATTERN_INTERRUPT" and an engaging break phrase like "oru second wait pannunga" or "ithai parunga"?
4. transition_score: Do transitions feel connected (match cuts, zoom transitions, morphs, object/story continuity) instead of hard-cuts?
5. subtitle_timing_score: Are narration segments short and punchy (3-5 words) for fast-paced subtitles?
6. comment_bait_score: Rate the quality of the 'comment_bait_question'. It must be a highly polarizing, debate-inducing question in Tanglish/Tamil that naturally drives engagement. Generic CTAs like "Comment below" or "Save this video" must be scored 0.
7. hook_strength_score: Does the hook (the first 3-5 seconds of narration) use a strong curiosity hook (e.g., '3000 வருஷம் பழமையான தேன் கெட்டுப்போகாதா? 🍯') or a bold counter-intuitive question (e.g., 'நம்ம மூளை ஏன் தூங்கும்போது இவ்ளோ வேலை செய்யுது?')? It must strictly avoid introductions/greetings like 'இன்னைக்கு நாம பாக்க போற...' or 'வணக்கம்'. Introductory fluff receives a score of 0. Direct curiosity hooks or highly engaging questions score 90-100.
8. universal_accessibility_score: Can EVERY sentence be understood by a 70-year-old Tamil grandmother? Are all English words simple (money, health, food, sleep, water, brain, body, blood, heart, milk, animal, bird)? No complex jargon? Score 0 if fails.
9. practical_value_score: Does the video give viewers something they can USE or SHARE with family TODAY? Score 0 if purely entertainment with no practical takeaway.

TAMIL VOICE & STYLE COMPLIANCE CHECK CRITERIA:
- Does the hook and script sound like a friendly, clear, and relatable South Indian Tamil guy (no anime tropes or fantasy phrasing like 'plot twist da' or 'final boss' in the voiceover script)?
- Is the script easily understandable by Tamil speakers globally (clear pronunciation, standard vocabulary, no obscure slang)?
- Are all sentences short and punchy (under 12 words)?
- Does the script strictly follow the 4-part structure: HOOK (0-5s), PROBLEM (5-20s), SOLUTION (20-100s), and ENGAGEMENT QUESTION (100-115s)?
- Does the script avoid generic phrases like "intha video-la"?
- Is the CTA/Question natural, not forced?
- UNIVERSAL APPEAL: Does the content resonate with students, professionals, homemakers, shopkeepers, auto drivers, parents, AND grandparents equally?

STORYBOARD TO EVALUATE:
{storyboard_json}

Return ONLY a JSON object:
{{
  "story_continuity_score": 0-100,
  "visual_alignment_score": 0-100,
  "engagement_score": 0-100,
  "transition_score": 0-100,
  "subtitle_timing_score": 0-100,
  "comment_bait_score": 0-100,
  "hook_strength_score": 0-100,
  "universal_accessibility_score": 0-100,
  "practical_value_score": 0-100,
  "passes_validation": true|false,
  "feedback": "Detailed feedback on what is wrong and which scenes need improvement/regeneration."
}}"""

# ── GOOGLE TRENDS INTEGRATION ─────────────────────────────────────────────────

def get_hottest_tech_topic(client, avoid_list=""):
    """Uses Gemini Search grounding to find today's most VIRAL fact/tip trending in India for Tamil audience."""
    from config import is_gemini_disabled
    if is_gemini_disabled():
        print("⚠️ Gemini is globally disabled. Skipping Google Trends analysis.")
        return None
    print(f"🔥 Fetching hottest trending topic for today in India (Google Trends Analysis)...")
    
    avoid_prompt = f"\n\nCRITICAL: DO NOT pick any topics related to the following recently covered stories:\n{avoid_list}" if avoid_list else ""
    
    attempts = 0
    while attempts < 3:
        try:
            response = client.models.generate_content(
                model=GEMINI_FLASH_MODEL,
                contents=(
                    "Analyze today's Google Trends and viral content in India. "
                    "What is the single most trending topic right now that would work as a Tamil infotainment YouTube Short? "
                    "Look for: fascinating science facts, mind-blowing biology/human body facts, "
                    "hidden phone settings, life hacks, smart money tips, historical mysteries, "
                    "everyday science anomalies, cooking/food science, health tips, government schemes, "
                    "or any fact going viral on social media in India. "
                    "CRITICAL: The topic must appeal to Tamil-speaking audiences aged 16-80 in India and globally. "
                    "Focus on universal curiosity-gap themes: science wonders, body mysteries, phone/tech hacks, "
                    "money-saving tips, health tips, cooking hacks, government schemes, or surprising everyday facts. "
                    "Do NOT choose developer news, programming tutorials, API releases, or corporate tech updates. "
                    f"{avoid_prompt}\n\n"
                    "Return ONLY a JSON object with two fields: "
                    "'topic' (3-6 word phrase in English, e.g. 'human brain sleep mystery') and "
                    "'keywords' (list of 6-8 specific search keywords). No markdown, no explanation."
                ),
                config=types.GenerateContentConfig(
                    tools=[{'google_search': {}}]
                )
            )
            raw = response.text.strip()
            if "{" in raw and "}" in raw:
                raw = raw[raw.find("{"):raw.rfind("}")+1]
            
            data = json.loads(raw)
            print(f"📈 Google Trends Hot Topic (India): {data.get('topic', 'N/A')}")
            return data
        except Exception as e:
            err_str = str(e).upper()
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                print(f"⚠️ [google_trends] Google Search grounding rate limited: {e}. Proceeding without trending signal.")
                return None
            print(f"⚠️ Could not fetch Google Trends topic: {e}. Proceeding without trending signal.")
            return None
    
    print("⚠️ Google Trends exhausted after retries. Proceeding without trending signal.")
    return None

def apply_cta_rotation(final_script):
    """
    Loads CTA magnets from cta_magnets.json and randomly selects one to rotate.
    Sets 'cta' and 'comment_bait_question' fields.
    """
    if not final_script:
        return final_script
    cta_list = [
        "இந்த இன்ட்ரஸ்டிங் ஃபேக்ட் உங்களுக்கு பிடிச்சிருந்தா, மறக்காம நம்ம Simple Tips by VJ சேனலை சப்ஸ்கிரைப் பண்ணுங்க!",
        "இதை பத்தி நீங்க என்ன நினைக்கிறீங்கன்னு கண்டிப்பா கமெண்ட்ல சொல்லுங்க! டெய்லி இந்த மாதிரி சுவாரஸ்யமான தகவல்களுக்கு Subscribe பண்ணுங்க!",
        "உங்க பிரண்ட்ஸ் மற்றும் ஃபேமிலிக்கும் இந்த ஆச்சரியமான விஷயத்தை உடனே ஷேர் பண்ணுங்க! மறக்காம Subscribe பண்ணுங்க!",
        "நாளைக்கு இதைவிட ஒரு பயனுள்ள தகவலோட சந்திக்கிறேன். Simple Tips by VJ-க்கு சப்ஸ்கிரைப் பண்ண மறந்துடாதீங்க!",
        "இதுல உங்களுக்கு எந்த விஷயம் புதுசா இருந்ததுன்னு கமெண்ட்ல சொல்லுங்க! மறக்காம Subscribe தட்டி விடுங்க!"
    ]
    cta_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cta_magnets.json")
    try:
        if os.path.exists(cta_path):
            with open(cta_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, list) and loaded:
                    cta_list = loaded
    except Exception as e:
        print(f"⚠️ Failed to load cta_magnets.json: {e}. Using fallback CTAs.")
        
    selected_cta = random.choice(cta_list)
    final_script["cta"] = selected_cta
    final_script["comment_bait_question"] = selected_cta
    print(f"🔄 CTA Rotation: Assigned selected CTA: '{selected_cta}'")
    return final_script

def normalize_storyboard(raw_storyboard):
    """
    Normalizes storyboard into a standard list of scene dictionaries.
    Ensures every scene is a dict with 'narration' and 'scene_number'.
    Safely handles:
    - Dict of scenes: {"scene_1": {...}, "scene_2": {...}} or {"scenes": [...]} or {"items": [...]}
    - List of strings: ["Scene 1: Narration text", "Scene 2: Narration text"]
    - List of dicts (standard)
    - Mixed lists
    - JSON-encoded strings
    - Plain text blocks
    """
    if not raw_storyboard:
        return []

    # If it's a JSON string, try to parse it
    if isinstance(raw_storyboard, str):
        raw_storyboard = raw_storyboard.strip()
        if (raw_storyboard.startswith("{") and raw_storyboard.endswith("}")) or (raw_storyboard.startswith("[") and raw_storyboard.endswith("]")):
            try:
                raw_storyboard = json.loads(raw_storyboard)
            except Exception:
                pass

    # If it's still a string, split into non-empty lines
    if isinstance(raw_storyboard, str):
        lines = [line.strip() for line in raw_storyboard.splitlines() if line.strip()]
        raw_storyboard = lines if lines else [raw_storyboard]

    # If it's a dict, extract the scene list or dict values
    if isinstance(raw_storyboard, dict):
        for key in ["scenes", "storyboard", "shots", "items", "data"]:
            if key in raw_storyboard and isinstance(raw_storyboard[key], (list, dict)):
                raw_storyboard = raw_storyboard[key]
                break
        if isinstance(raw_storyboard, dict):
            raw_storyboard = list(raw_storyboard.values())

    if not isinstance(raw_storyboard, list):
        return []

    normalized = []
    for idx, item in enumerate(raw_storyboard):
        if isinstance(item, dict):
            # If this dict wraps another dict e.g. {"scene_1": {"narration": ...}}
            if len(item) == 1 and not any(k in item for k in ["narration", "text", "script"]):
                inner_val = next(iter(item.values()))
                if isinstance(inner_val, dict):
                    item = inner_val
                elif isinstance(inner_val, str):
                    item = {"narration": inner_val}

            narration = item.get("narration") or item.get("text") or item.get("dialogue") or item.get("script") or ""
            if not isinstance(narration, str):
                narration = str(narration or "")
            item["narration"] = narration
            if "scene_number" not in item:
                item["scene_number"] = idx + 1
            normalized.append(item)
        elif isinstance(item, str):
            clean_text = item.strip()
            if clean_text:
                words = [w.strip(",.!?\"'") for w in clean_text.split() if len(w) > 3]
                stock_query = " ".join(words[:3]) if words else "technology"
                caption = " ".join(clean_text.split()[:3]).upper()
                normalized.append({
                    "scene_number": idx + 1,
                    "narration": clean_text,
                    "visual_type": "Google Video Generation",
                    "visual_prompt": clean_text,
                    "stock_search_query": stock_query,
                    "on_screen_text": caption,
                    "camera_motion": "None",
                    "transition": "Match cut",
                    "duration": 3
                })
        elif isinstance(item, (list, tuple)):
            str_parts = [str(x) for x in item if str(x).strip()]
            if str_parts:
                clean_text = " ".join(str_parts)
                words = [w.strip(",.!?\"'") for w in clean_text.split() if len(w) > 3]
                stock_query = " ".join(words[:3]) if words else "technology"
                caption = " ".join(clean_text.split()[:3]).upper()
                normalized.append({
                    "scene_number": idx + 1,
                    "narration": clean_text,
                    "visual_type": "Google Video Generation",
                    "visual_prompt": clean_text,
                    "stock_search_query": stock_query,
                    "on_screen_text": caption,
                    "camera_motion": "None",
                    "transition": "Match cut",
                    "duration": 3
                })

    return normalized

def sanitize_script_against_ai_cliches(text: str) -> str:
    """
    Cleans up stubborn AI clichés, repetitive bot phrases, and stiff senthamizh
    words so the script sounds 100% natural, human, and conversational like VJ.
    """
    if not text:
        return ""
    import re
    # Strip common robotic AI openers completely instead of substituting with other cliches
    banned_openers = [
        (r'^(?:Oru vishayam theriyuma|ஒரு விஷயம் தெரியுமா)[\s?!.,-]*', ''),
        (r'^(?:Nee yaarukkum theriyadhu|யாருக்கும் தெரியாது)[\s?!.,-]*', ''),
        (r'^(?:Ungalukku idhu theriyuma|உங்களுக்கு இது தெரியுமா)[\s?!.,-]*', ''),
        (r'^(?:Nammil pala perukku theriyaadha|நம்மில் பல பேருக்கு தெரியாத)[\s?!.,-]*', ''),
        (r'^(?:Intha video-la namma paarkalaam|இந்த வீடியோல நம்ம பார்க்க போறோம்)[\s?!.,-]*', ''),
        (r'^(?:Intha video-la|இந்த வீடியோல)[\s?!.,-]*', ''),
        (r'^(?:Welcome back to Simple Tips by VJ|வணக்கம் நண்பர்களே|வணக்கம்)[\s?!.,-]*', ''),
        (r'^(?:Today we are going to see|இன்னைக்கு நாம பார்க்க போறது)[\s?!.,-]*', ''),
        (r'^(?:Did you know that|Did you know)[\s?!.,-]*', ''),
    ]
    # Iteratively strip stacked openers
    for _ in range(4):
        original = text
        for pattern, replacement in banned_openers:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE).strip()
        if text == original:
            break
        
    # Replace bookish/formal/stiff Tamil with TIRUNELVELI native spoken Tamil (நெல்லை பேச்சுத் தமிழ்)
    # Phase 1: Standard formal → colloquial replacements
    colloquial_replacements = [
        ('செய்யுங்கள்', 'பண்ணுங்கோ'),
        ('செய்ய வேண்டும்', 'பண்ணனும்'),
        ('செய்து பாருங்கள்', 'பண்ணி பாருங்கோ'),
        ('காணலாம்', 'பார்க்கலாம்'),
        ('காணப்படும்', 'இருக்கும்'),
        ('அறிந்துகொள்ளுங்கள்', 'தெரிஞ்சுக்கோங்கோ'),
        ('தெரிந்து கொள்ளுங்கள்', 'தெரிஞ்சுக்கோங்கோ'),
        ('பதிவிறக்கம்', 'டவுன்லோடு'),
        ('செயலி', 'ஆப்'),
        ('நினைவில் கொள்ளுங்கள்', 'மறந்துடாதீங்கோ'),
        ('முடிவாக', 'கடைசியா'),
        ('முடிவுரை', 'கடைசியா'),
        ('முதலாவதாக', 'முதல்ல'),
        ('இரண்டாவதாக', 'அடுத்ததா'),
        ('பயன்படுத்துங்கள்', 'யூஸ் பண்ணுங்கோ'),
        ('பயன்படுத்தலாம்', 'யூஸ் பண்ணலாம்'),
        ('ஆகும்', 'ஆயிடும்'),
        ('சாத்தியமாகும்', 'சாத்தியம் தான்'),
        ('சாத்தியம்', 'சாத்தியமா'),
        ('சாப்பிடக்கூடும்', 'சாப்பிடலாம்'),
        ('என்றால்', 'அப்புடின்னா'),
        ('எனவே', 'அதனால'),
        ('ஆகையால்', 'அதனால'),
        ('மட்டுமல்லாமல்', 'மட்டும் இல்லாம'),
        ('அதேபோல்', 'அதே மாதிரி'),
        ('மிகவும்', 'ரொம்பவே'),
        ('அதிகமாக', 'நெறைய'),
        ('இப்போது', 'இப்போ'),
        ('எப்போது', 'எப்போ'),
        ('அப்போது', 'அப்போ'),
        ('உடனடியாக', 'டக்குனு'),
    ]
    for target, replacement in colloquial_replacements:
        text = text.replace(target, replacement)
    
    # Phase 2: Nellai dialect upgrades — convert generic colloquial Tamil to Tirunelveli native forms
    nellai_dialect_upgrades = [
        # Standard colloquial → Nellai native
        ('பண்ணுங்க', 'பண்ணுங்கோ'),
        ('பாருங்க', 'பாருங்கோ'),
        ('கேளுங்க', 'கேளுங்கோ'),
        ('சொல்லுங்க', 'சொல்லுங்கோ'),
        ('வாங்க', 'வாங்கோ'),
        ('சொல்றேன்', 'சொல்றேங்'),
        ('தெரியுமா', 'தெர்யுமா'),
        ('கொஞ்சம்', 'கொஞ்சூம்'),
        ('அப்படி', 'அப்புடி'),
        ('என்ன', 'என்னா'),
        ('என்னது', 'என்னாது'),
        ('இல்லையா', 'இல்லியா'),
        ('அப்படின்னா', 'அப்புடின்னா'),
        ('தெரிஞ்சுக்கோங்க', 'தெரிஞ்சுக்கோங்கோ'),
        ('மறந்துடாதீங்க', 'மறந்துடாதீங்கோ'),
    ]
    for target, replacement in nellai_dialect_upgrades:
        text = re.sub(r'(?<![\u0b80-\u0bff])' + re.escape(target) + r'(?![\u0b80-\u0bff])', replacement, text)
        
    # Tanglish word replacements (use \b for Latin strings)
    tanglish_replacements = [
        (r'\bseyyungal\b', 'pannungo'),
        (r'\bpannunga\b', 'pannungo'),
        (r'\bpaarunga\b', 'paarungo'),
        (r'\bpaarkalaam\b', 'paapom'),
        (r'\bparkalam\b', 'paapom'),
        (r'\bkavanikkavum\b', 'gavaningo'),
        (r'\bninaivil kollungal\b', 'maranthudatheengo'),
        (r'\baagum\b', 'aayidum'),
        (r'\bippodhu\b', 'ippo'),
        (r'\beppodhu\b', 'eppo'),
        (r'\bappodhu\b', 'appo'),
        (r'\btheriyuma\b', 'theryuma'),
        (r'\bkonjam\b', 'konjoom'),
        (r'\bappadi\b', 'appudi'),
        (r'\benna\b', 'ennaa'),
        (r'\billaiya\b', 'illiya'),
    ]
    for pattern, replacement in tanglish_replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
    return text.strip()

def pick_and_generate_script(articles=None, extra_instruction="", forced_article=None, topic_type="research", failed_topics=[]):
    """
    Orchestrates the multi-agent pipeline to generate a high-retention Tanglish fact script.
    """
    from config import is_gemini_disabled
    
    day_name, slot, category = get_slot_info()
    
    # ── OFFLINE MODE CHECK ──
    # If all LLM providers are exhausted, immediately use offline fallback
    if _OFFLINE_MODE_ACTIVE:
        print("🔴 [OFFLINE MODE] All LLM providers exhausted. Using offline fallback script immediately.")
        return get_offline_fallback_script(category, failed_topics)
    
    # Check if all providers are exhausted at config level (no API keys)
    check_all_providers_exhausted()
    if _OFFLINE_MODE_ACTIVE:
        print("🔴 [OFFLINE MODE] No LLM API keys configured. Using offline fallback script immediately.")
        return get_offline_fallback_script(category, failed_topics)
    
    client = get_gemini_client()
    if not client and not is_gemini_disabled():
        print("⚠️ Gemini API Client missing! Cannot run multi-agent script generation.")
        return None
    strategy_enhancement = get_category_prompt_enhancement(category, slot)
    
    # Check for session length cap from performance insights
    from ecosystem_logic import get_session_length_cap
    session_length_cap = get_session_length_cap()
    
    local_persona = globals()["SYSTEM_PERSONA"]
    local_optimizer = globals()["RETENTION_OPTIMIZER_TEMPLATE"]
    
    if session_length_cap:
        print(f"📉 [gemini_script] Applying session length cap of {session_length_cap} words.")
        local_persona = local_persona.replace("115-135", f"50-{session_length_cap}")
        local_optimizer = local_optimizer.replace("115-135", f"50-{session_length_cap}")
        word_count_limit_str = f"STRICT LIMIT: Total word count MUST be between 50-{session_length_cap} words."
    else:
        word_count_limit_str = "STRICT LIMIT: Total word count MUST be between 115-135 words."

    SYSTEM_PERSONA = local_persona
    RETENTION_OPTIMIZER_TEMPLATE = local_optimizer
    
    # ── REP AVOIDANCE ──
    tracker = load_tracker()
    recent_history = tracker.get("history", [])[-15:]
    recent_titles = tracker.get("used_titles", [])[-30:]
    avoid_items = [h.get('news_headline', h.get('title')) for h in recent_history] + recent_titles
    if failed_topics:
        avoid_items += failed_topics
    combined_avoid = list(set(avoid_items))
    avoid_list_str = "\n".join([f"- {t}" for t in combined_avoid if t])
    avoid_instruction = f"CRITICAL: RECENTLY COVERED TOPICS (DO NOT REPEAT THESE):\n{avoid_list_str}\n\n" if avoid_list_str else ""

    # ── GOOGLE TRENDS SIGNAL ──
    hot_topic = get_hottest_tech_topic(client, avoid_list=avoid_list_str)
    hot_keywords = [kw.lower() for kw in hot_topic.get("keywords", [])] if hot_topic else []
    hot_topic_str = hot_topic.get("topic", "") if hot_topic else ""
    if hot_topic_str:
        trending_signal = f"\n📈 TRENDING SIGNAL (India): Today's hottest topic is '{hot_topic_str}'. If any of the provided facts align with this trend, STRONGLY PREFER it.\n\n"
    else:
        trending_signal = ""

    news_context = avoid_instruction + trending_signal
    
    if forced_article:
        print(f"🎯 Forced Topic selected: {forced_article.get('title')}")
        selected_headline = forced_article.get("title")
        selected_url = forced_article.get("source_url")
        isolated_context = f"Title: {selected_headline}\nDescription: {forced_article.get('description')}\nURL: {selected_url}"
        news_context += f"FORCED FACT TO COVER:\n{isolated_context}\n"
    else:
        # Programmatically filter out duplicate facts before passing to Selector Agent
        if articles:
            unique_articles = []
            for art in articles:
                title = art.get('title', '')
                url = art.get('source_url', '')
                is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
                
                if is_unique and failed_topics:
                    for ft in failed_topics:
                        if ft and (ft.lower() in title.lower() or title.lower() in ft.lower()):
                            is_unique = False
                            reason = f"Topic failed in a previous attempt: {ft}"
                            break
                            
                if is_unique:
                    unique_articles.append(art)
                else:
                    print(f"⏭️ [pick_and_generate_script] Filtering out duplicate article: {title}. Reason: {reason}")
            articles = unique_articles
            
        # If articles is empty (all duplicates), trigger LLM fallback to fetch unique ones
        if not articles:
            print("⚠️ [pick_and_generate_script] No unique articles available. Generating fresh facts via LLM fallback...")
            from fetch_topics import fetch_facts_from_llm_fallback
            articles = fetch_facts_from_llm_fallback(category, combined_avoid)
            
        # If still empty or no articles were provided initially
        if not articles:
            print("⚠️ No input facts provided. Fetching fresh facts for selection...")
            from fetch_topics import fetch_facts_for_category
            fresh_facts = fetch_facts_for_category(category)
            unique_fresh = []
            for art in fresh_facts:
                title = art.get('title', '')
                url = art.get('source_url', '')
                is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
                if is_unique:
                    unique_fresh.append(art)
                else:
                    print(f"⏭️ [pick_and_generate_script] Filtering out duplicate fresh fact: {title}. Reason: {reason}")
            articles = unique_fresh

        if articles:
            for idx, art in enumerate(articles[:10]):
                title = art.get('title', '')
                desc = art.get('description', '')
                url = art.get('source_url', '')
                news_context += f"\n[{idx+1}] Title: {title}\nDescription: {desc}\nURL: {url}\n"
        else:
            print("🚨 [pick_and_generate_script] No unique articles could be fetched or generated!")
            return get_offline_fallback_script(category, failed_topics)

    selection_instruction = (
        f"Analyze the facts and select the SINGLE most mind-blowing fact to convert into a 30-40s Tanglish YouTube Short.\n"
        f"CATEGORY: {category}\n"
        f"{strategy_enhancement}\n"
        f"{word_count_limit_str}"
    )

    prompt_requirements = """Return ONLY this exact JSON (no markdown):
{
  "title": "Main punchy YouTube title (max 80 chars, include emoji)",
  "hook": "The Hook (<1.5s): A shocking Result-First statement in Tanglish. Approx 6 words.",
  "narration": [
    "First sentence in Tanglish",
    "Second sentence in Tanglish",
    "Third sentence in Tanglish"
  ],
  "storyboard": [
    {
      "scene_number": 1,
      "narration": "The exact spoken Tanglish phrase for this scene (3-5 words maximum for punchy subtitles, e.g. 'namma brain-la almost')",
      "scene_objective": "Explain the concept visually, not just verbally",
      "visual_type": "Google Video Generation|Animated Infographics|Whiteboard Animation|Motion Graphics",
      "visual_prompt": "A detailed image/video prompt in English that DIRECTLY ILLUSTRATES the spoken narration. Use culturally grounded South Indian Tamil visual style: warm terracotta tones, temple bronze lighting, traditional brass vessels, jasmine garlands, kolam patterns, banana leaf settings, village coconut palms, spice market colors. E.g., 'Close-up of golden honey dripping from a traditional brass spoon into a clay pot, warm turmeric-gold lighting, shallow depth of field, photorealistic 8K, 9:16 vertical' or 'Ancient South Indian temple stone corridor with oil lamp shadows, warm bronze lighting, volumetric fog, cinematic golden hour'. NO human faces, NO cartoon characters, NO anatomical figures. National Geographic India quality.",
      "stock_search_query": "A simple 2-3 word English search query to find relevant real-world B-roll stock video footage on Pexels with Indian/Tamil context when possible (e.g., 'honey jar', 'temple lamp', 'indian kitchen', 'spice market', 'banana leaf', 'jasmine flowers', 'brass vessel'). Do NOT include stylistic keywords like '3D', 'Pixar', 'cartoon', 'claymation', 'realistic', 'detailed'.",
      "camera_motion": "Slow zoom|Dolly-in|Orbit|Pan|Tracking shot|None",
      "transition": "Match cut|Zoom transition|Morph|Swipe|Object continuity|Story continuity",
      "on_screen_text": "1-3 IMPORTANT key English words representing the central concept of this scene in uppercase (e.g., '86 BILLION NEURONS')",
      "emotion": "Curiosity|Surprise|Fear|Excitement|Focus|Confusion",
      "duration": 3,
      "infographic_type": "stat|comparison|timeline|definition|ranking|growth|slide|process|none",
      "infographic_data": {
        "term": "Required only if type is 'definition' (e.g. 'Mirroring')",
        "definition": "Required only if type is 'definition' (e.g. 'Subtly copying body language to build rapport.')",
        "example": "Optional if type is 'definition' (e.g. 'Matching their speech rate.')",
        "headline": "Required only if type is 'stat' or 'growth' (e.g. 'PHONE SPEED')",
        "subtext": "Required only if type is 'stat' or 'growth' (e.g. '100%' or 'Information')",
        "context": "Optional if type is 'stat' (e.g. 'Speed multiplier increased')",
        "title": "Required if type is 'comparison', 'timeline', 'ranking', 'slide', or 'process' (e.g. 'STEPS')",
        "item1": "Required if type is 'comparison' (e.g. 'Perfect')",
        "val1": "Required if type is 'comparison' (e.g. 'Unapproachable')",
        "item2": "Required if type is 'comparison' (e.g. 'Imperfect')",
        "val2": "Required if type is 'comparison' (e.g. 'Friendly & Likeable')",
        "events": [{"date": "Step 1", "desc": "Go to Settings"}, {"date": "Step 2", "desc": "About Phone"}],
        "items": [{"name": "Rank 1", "val": "First Item"}],
        "percent": "Growth percent (e.g. '+50%')",
        "steps": ["Step 1 description", "Step 2 description"]
      }
    }
  ],
  "title_options": ["Curiosity Gap Title 1", "Curiosity Gap Title 2"],
  "description": "Full SEO friendly video description including Tamil tags #தெரியுமா #FactsInTamil #VJVideos",
  "unique_angle": "One sentence explaining what makes THIS specific video different from other videos on the same topic. Focus on the specific insight, angle, or approach that is unique to this tip. This is used for YouTube monetization originality signals.",
  "use_case_evidence_url": "Direct source url of the fact to take a screenshot of.",
  "relevant_links": ["Source url"],
  "phonetic_pronunciation_map": {"NVIDIA": "In-vid-yah"},
  "summary": "One line English summary",
  "sub_category": "{category}",
  "breaking_news_level": 8,
  "original_news_headline": "Fact Title",
  "original_news_url": "Direct source url",
  "keywords": ["Tamil Facts", "Did You Know"],
  "hashtags": ["#தெரியுமா", "#TamilFacts", "#VJVideos"],
  "comment_hook": "Provocative question in Tanglish to drive comments.",
  "comment_bait_question": "A polarizing debate question in Tanglish or Tamil about the topic to spark discussion/arguments in comments (e.g. 'Ethu unmaiyave nadakkum-nu neneikiringala?', 'Ithai pathi unga karuthu enna?'). Avoid generic CTAs like 'Comment below'."
}""".replace("{category}", category)

    # ── FACT SHORTS CUSTOM PATH ──
    is_fact_slot = True
    if is_fact_slot:
        print("🧠 [Fact Shorts Path] Initializing fact pipeline...")
        selected_category = random.choice(TOPIC_CATEGORIES)
        
        # Step 1: Select a topic using TOPIC_SELECTOR_PROMPT
        selector_prompt = PIPELINE_PROMPTS["topic_selector"] + f"\nRotate / Focus on Category: {selected_category}\n"
        print(f"🕵️ [AGENT 0] Topic Selector Agent: Generating fact topic for '{selected_category}'...")
        topic_data_res = call_gemini_api(client, selector_prompt, prefer_fallback=True, category=selected_category, task_type="reasoning")
        
        if topic_data_res and "topic" in topic_data_res:
            selected_headline = topic_data_res.get("topic")
            selected_url = topic_data_res.get("source_url", "https://en.wikipedia.org")
            
            # Step 2: Generate script using standard SCRIPT_GENERATION_PROMPT
            script_writer_prompt = PIPELINE_PROMPTS["script_writer"].format(
                topic=topic_data_res.get("topic"),
                hook_question=topic_data_res.get("hook_question"),
                core_concept=topic_data_res.get("core_concept"),
                real_world_example=topic_data_res.get("real_world_example"),
                surprising_fact=topic_data_res.get("surprising_fact"),
                target_segment=topic_data_res.get("target_segment", "all")
            )
            print("📝 [AGENT 1] Script Writer Agent: Generating script via prioritized models...")
            script_text = None
            try:
                # Prioritized generation: P1 (nemotron) or specialized P2/P4 -> P3 fallback -> P5 Gemini
                script_raw = call_gemini_api(
                    client,
                    script_writer_prompt,
                    model=GEMINI_FLASH_MODEL,
                    prefer_fallback=True,
                    category=selected_category,
                    task_type="script_writer",
                    expect_json=False
                )
                if isinstance(script_raw, str):
                    script_text = script_raw.strip()
                elif isinstance(script_raw, dict):
                    script_text = script_raw.get("script") or script_raw.get("text") or str(script_raw)
            except Exception as e:
                print(f"⚠️ Script Writer Agent failed: {e}")
                
            if script_text:
                script_text = sanitize_script_against_ai_cliches(script_text)
                # Step 3: Generate Title, tags and metadata using TITLE_TAGS_PROMPT
                sentences = [s.strip() for s in script_text.split(".") if s.strip()]
                summary_sentences = " ".join(sentences[:2]) if len(sentences) >= 2 else script_text
                
                metadata_prompt = PIPELINE_PROMPTS["metadata"].format(
                    topic=topic_data_res.get("topic"),
                    core_concept=topic_data_res.get("core_concept"),
                    first_two_sentences_of_script=summary_sentences
                )
                print("🏷️ [AGENT 2] Metadata Agent: Generating Title & Tags...")
                metadata_res = call_gemini_api(client, metadata_prompt, prefer_fallback=True, category=selected_category, task_type="metadata")
                if not metadata_res:
                    metadata_res = {}
                
                # Step 4: Generate storyboard for the script using Storyboard Agent
                import site
                sp = site.getsitepackages()[0]
                refined_requirements = prompt_requirements
                refined_requirements = refined_requirements.replace('"original_news_headline": "Fact Title"', f'"original_news_headline": "{selected_headline}"')
                refined_requirements = refined_requirements.replace('"original_news_url": "Direct source url"', f'"original_news_url": "{selected_url}"')
                refined_requirements = refined_requirements.replace('"use_case_evidence_url": "Direct source url of the fact to take a screenshot of."', f'"use_case_evidence_url": "{selected_url}"')
                
                storyboard_prompt = f"""{SYSTEM_PERSONA}

STORYBOARD AGENT TASK:
Given the following fact script, break it down into a sequence of short narration segments (4-6 words each) and generate a detailed visual storyboard.
You must produce 18-28 storyboard scenes to align with the 115-135 words script length.

SCRIPT:
{script_text}

Return ONLY a JSON object matching the required schema:
{refined_requirements}
"""
                print("🎬 [AGENT 3] Storyboard Agent: Generating storyboard layout...")
                final_script = call_gemini_api(client, storyboard_prompt, model=GEMINI_FLASH_MODEL, category=selected_category, task_type="reasoning")
                
                try:
                    if final_script and "storyboard" in final_script:
                        storyboard = normalize_storyboard(final_script.get("storyboard"))
                        final_script["storyboard"] = storyboard
                        total_words = sum(len(s.get("narration", "").split()) for s in storyboard if isinstance(s, dict))
                        scene_count = len(storyboard)
                        length_ok = scene_count >= 15 and total_words >= 80
                        
                        if not length_ok:
                            print(f"⚠️ [Fact Shorts Path] Storyboard too short: {scene_count} scenes / {total_words} words. Need 18-28 scenes / 80+ words. Retrying...")
                            # Trigger self-correction by re-calling storyboard agent with feedback
                            correction_prompt = f"""{SYSTEM_PERSONA}

STORYBOARD AGENT TASK:
Given the following fact script, break it down into a sequence of short narration segments (4-6 words each) and generate a detailed visual storyboard.
You must produce 18-28 storyboard scenes to align with the 115-135 words script length.

SCRIPT:
{script_text}

PREVIOUS ATTEMPT FAILED: Only produced {scene_count} scenes with {total_words} total words.
CRITICAL REQUIREMENT: You MUST produce 18-28 scenes. Each scene's narration field must be 4-6 words.
Total word count across all narration fields must be 80+ words.

Return ONLY a JSON object matching the required schema:
{refined_requirements}
"""
                            print("🔄 [Fact Shorts Path] Retrying Storyboard Agent with length correction...")
                            final_script = call_gemini_api(client, correction_prompt, model=GEMINI_FLASH_MODEL, category=selected_category, task_type="reasoning")
                            if not final_script or "storyboard" not in final_script:
                                print("⚠️ [Fact Shorts Path] Correction retry failed. Falling back to default generation path...")
                            else:
                                # Re-check length after correction
                                storyboard = normalize_storyboard(final_script.get("storyboard"))
                                final_script["storyboard"] = storyboard
                                total_words = sum(len(s.get("narration", "").split()) for s in storyboard if isinstance(s, dict))
                                scene_count = len(storyboard)
                                length_ok = scene_count >= 20 and total_words >= 90
                                if not length_ok:
                                    print(f"⚠️ [Fact Shorts Path] Still too short after retry: {scene_count} scenes / {total_words} words. Falling back...")
                                    final_script = None
                        
                        if final_script and "storyboard" in final_script and length_ok:
                            final_script["storyboard"] = normalize_storyboard(final_script.get("storyboard"))
                            final_script["title"] = metadata_res.get("title") or topic_data_res.get("tamil_title") or final_script.get("title")
                            final_script["description"] = metadata_res.get("description") or final_script.get("description")
                            final_script["hashtags"] = metadata_res.get("hashtags") or final_script.get("hashtags")
                            final_script["comment_bait_question"] = metadata_res.get("thumbnail_text") or final_script.get("comment_bait_question")
                            final_script["original_news_headline"] = topic_data_res.get("topic")
                            final_script["original_news_url"] = selected_url
                            final_script["use_case_evidence_url"] = selected_url
                            final_script["script"] = script_text
                            
                            subtitle_chunks = []
                            rebuilt_script_parts = []
                            for scene in final_script["storyboard"]:
                                if not isinstance(scene, dict):
                                    continue
                                scene_num = scene.get("scene_number", len(subtitle_chunks) + 1)
                                narration_text = sanitize_script_against_ai_cliches(str(scene.get("narration", "")))
                                scene["narration"] = narration_text
                                rebuilt_script_parts.append(narration_text)
                                
                                v_type = str(scene.get("visual_type", ""))
                                info_type = str(scene.get("infographic_type", "none")).lower()
                                if "infographic" in v_type.lower() and info_type in ("none", ""):
                                    info_type = "stat"
                                
                                has_info = info_type not in ("none", "")
                                info_data = scene.get("infographic_data", {})
                                
                                vis_prompt = str(scene.get("visual_prompt", ""))
                                stock_query = str(scene.get("stock_search_query", "")).strip()
                                if not stock_query:
                                    words = [w.strip(",.!?\"'") for w in vis_prompt.split() if len(w) > 3][:3]
                                    stock_query = " ".join(words) if words else "tech"
                                
                                chunk = {
                                    "chunk_id": scene_num,
                                    "text": narration_text,
                                    "english_caption": scene.get("on_screen_text", ""),
                                    "start": 0.0,
                                    "end": 0.0,
                                    "has_infographic": has_info,
                                    "infographic_type": info_type,
                                    "infographic_data": info_data,
                                    "stock_search_query": stock_query,
                                    "nano_visual_prompt": vis_prompt,
                                    "visual_type": "photo" if "image" in v_type.lower() or "photo" in v_type.lower() else "video",
                                    "camera_motion": scene.get("camera_motion", "None"),
                                    "transition": scene.get("transition", "Match cut")
                                }
                                subtitle_chunks.append(chunk)
                            
                            final_script["subtitle_chunks"] = subtitle_chunks
                            final_script["title_variants"] = [
                                final_script.get("title", "Secret Trick!"),
                                final_script.get("title", "Secret Trick!") + " 🤫",
                                "Don't Miss This! 🚨"
                            ]
                            
                            final_script = apply_cta_rotation(final_script)
                            print("🎉 [Fact Shorts Path] Script and storyboard generated successfully!")
                            return final_script
                except Exception as e:
                    print(f"⚠️ [Fact Shorts Path] Error parsing storyboard: {e}. Falling back to default generation path...")
                    
        print("⚠️ [Fact Shorts Path] Custom generation failed/incomplete. Falling back to default generation path...")

    # ── AGENT 0: SELECTOR ──
    if not forced_article:
        print("🕵️ [AGENT 0] Selector Agent: Choosing top fact candidate...")
        selector_prompt = SELECTOR_AGENT_TEMPLATE.format(
            persona=SYSTEM_PERSONA,
            selection_instruction=selection_instruction,
            news_context=news_context
        )
        selection = call_gemini_api(client, selector_prompt, category=category, task_type="reasoning")
        if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
        if not selection or "selected_headline" not in selection:
            print("⚠️ Selector Agent failed. Attempting offline fallback script...")
            return get_offline_fallback_script(category, failed_topics)
        selected_headline = selection["selected_headline"]
        selected_url = selection["selected_url"]
        
        # Verify the uniqueness of the Selector Agent's choice
        is_unique, reason = check_story_uniqueness(new_title=selected_headline, new_url=selected_url)
        if not is_unique:
            print(f"⚠️ [pick_and_generate_script] Selector Agent selected a duplicate topic: {selected_headline}. Reason: {reason}")
            # Try to find a match in our unique articles list to fallback on
            fallback_found = False
            if articles:
                for art in articles:
                    art_title = art.get("title", "")
                    art_url = art.get("source_url", "")
                    if check_story_uniqueness(new_title=art_title, new_url=art_url)[0]:
                        selected_headline = art_title
                        selected_url = art_url
                        fallback_found = True
                        print(f"🔄 [pick_and_generate_script] Fell back to first verified unique article: {selected_headline}")
                        break
            if not fallback_found:
                print("🚨 [pick_and_generate_script] No verified unique article fallback available. Loading offline fallback...")
                return get_offline_fallback_script(category, failed_topics)
        
    print(f"✅ Selected Fact: {selected_headline}")
    
    # Isolate context for fact extraction
    isolated_context = f"Fact Title: {selected_headline}\nSource: {selected_url}\n"
    if articles:
        for art in articles:
            if art.get("source_url") == selected_url or art.get("title") == selected_headline:
                isolated_context += f"Description: {art.get('description')}\n"
                break

    # ── AGENT 0.5: CONTEXT SHARPENER ──
    print("🔬 [AGENT 0.5] Context Sharpener: Extracting isolated details...")
    sharpener_prompt = FACT_EXTRACTOR_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        target_headline=selected_headline,
        context=isolated_context
    )
    sharpened_data = call_gemini_api(client, sharpener_prompt, prefer_fallback=True, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if sharpened_data:
        isolated_context += f"\nSharpened Facts: {json.dumps(sharpened_data)}"

    # ── AGENT 1: RESEARCH ──
    print("🕵️ [AGENT 1] Research Agent: Structuring narrative elements...")
    research_prompt = RESEARCH_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        news_context=isolated_context
    )
    research = call_gemini_api(client, research_prompt, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if not research:
        print("⚠️ Research Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 2: HOOK ──
    print("🪝 [AGENT 2] Hook Agent: Generating Tanglish hooks...")
    hook_prompt = HOOK_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        research_json=json.dumps(research)
    )
    hooks_data = call_gemini_api(client, hook_prompt, prefer_fallback=True, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if not hooks_data or "hooks" not in hooks_data:
        print("⚠️ Hook Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)
    
    # Pick highest curiosity score hook
    best_hook = max(hooks_data["hooks"], key=lambda h: h.get("curiosity_score", 0) + h.get("emotional_trigger_score", 0) + h.get("swipe_stop_power", 0) + h.get("topic_specificity_score", 0))
    print(f"🎯 Selected Hook: {best_hook.get('text')}")

    # ── AGENT 3: NARRATIVE ──
    print("📖 [AGENT 3] Narrative Agent: Creating script draft...")
    narrative_prompt = NARRATIVE_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        research_json=json.dumps(research),
        selected_hook=best_hook.get("text"),
        selection_instruction=selection_instruction
    )
    narrative = call_gemini_api(client, narrative_prompt, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if not narrative:
        print("⚠️ Narrative Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 4: RETENTION OPTIMIZER ──
    print("⚡ [AGENT 4] Pacing Optimizer: Shortening sentences...")
    retention_prompt = RETENTION_OPTIMIZER_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        narrative_json=json.dumps(narrative),
        word_count_limit_str=word_count_limit_str,
        best_hook=best_hook.get("text")
    )
    optimized = call_gemini_api(client, retention_prompt, prefer_fallback=True, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if not optimized:
        print("⚠️ Pacing Optimizer failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 4.5: RETENTION SCIENTIST ──
    print("🧬 [AGENT 4.5] Retention Scientist: Injecting proven retention patterns...")
    retention_sci_prompt = RETENTION_SCIENTIST_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        optimized_script=optimized.get("optimized_script", "")
    )
    retention_result = call_gemini_api(client, retention_sci_prompt, model=GEMINI_PRO_MODEL, category=category, task_type="reasoning")
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    
    retention_map = {}
    if retention_result and "retention_enhanced_script" in retention_result:
        optimized["optimized_script"] = retention_result["retention_enhanced_script"]
        retention_map = retention_result.get("retention_map", {})
        cgr = retention_map.get("curiosity_gap_ratio", 0)
        loops = len(retention_map.get("open_loops", []))
        interrupts = len(retention_map.get("pattern_interrupts", []))
        print(f"   ✅ Retention: {loops} open loops, {interrupts} pattern interrupts, {cgr:.0%} curiosity gap ratio")
    else:
        print("   ⚠️ Retention Scientist failed (non-fatal). Using optimizer output directly.")

    # ── AGENT 5: HUMANIZER & SCHEMATIZER ──
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    print("🗣️ [AGENT 5] Humanizer: Structuring final Tamil schema...")
    refined_requirements = prompt_requirements
    refined_requirements = refined_requirements.replace('"original_news_headline": "Fact Title"', f'"original_news_headline": "{selected_headline}"')
    refined_requirements = refined_requirements.replace('"original_news_url": "Direct source url"', f'"original_news_url": "{selected_url}"')
    refined_requirements = refined_requirements.replace('"use_case_evidence_url": "Direct source url of the fact to take a screenshot of."', f'"use_case_evidence_url": "{selected_url}"')

    humanizer_prompt = HUMANIZER_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        optimized_script=optimized.get("optimized_script", ""),
        schema_requirements=refined_requirements
    )
    
    final_script = call_gemini_api(client, humanizer_prompt, model=GEMINI_FLASH_MODEL, category=category, task_type="reasoning")
    
    if final_script and "storyboard" in final_script:
        # ── AGENT 6: VALIDATOR & SELF-CORRECTION LOOP ──
        print("🔍 [AGENT 6] Validator Agent: Checking storyboard quality and continuity...")
        validation_attempts = 0
        max_validation_attempts = 2
        
        while validation_attempts < max_validation_attempts:
            validator_prompt = VALIDATOR_AGENT_TEMPLATE.format(
                persona=SYSTEM_PERSONA,
                storyboard_json=json.dumps(final_script, ensure_ascii=False)
            )
            validation_result = call_gemini_api(client, validator_prompt, model=GEMINI_FLASH_MODEL, category=category, task_type="reasoning")
            
            if not validation_result:
                print("⚠️ Validator Agent failed to respond. Proceeding with current storyboard.")
                break
                
            print(f"   📈 Storyboard Quality Audit (Attempt {validation_attempts+1}):")
            print(f"      - Story Continuity Score: {validation_result.get('story_continuity_score', 0)}%")
            print(f"      - Visual Alignment: {validation_result.get('visual_alignment_score', 0)}%")
            print(f"      - Engagement: {validation_result.get('engagement_score', 0)}%")
            print(f"      - Transitions: {validation_result.get('transition_score', 0)}%")
            print(f"      - Subtitle Timing: {validation_result.get('subtitle_timing_score', 0)}%")
            print(f"      - Comment Bait: {validation_result.get('comment_bait_score', 0)}%")
            print(f"      - Hook Strength: {validation_result.get('hook_strength_score', 0)}%")
            
            def _to_int(score):
                if isinstance(score, int):
                    return score
                if isinstance(score, str):
                    word_to_num = {
                        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
                        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
                        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
                        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
                        'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
                        'eighty': 80, 'ninety': 90, 'hundred': 100
                    }
                    score_lower = score.lower().strip('%')
                    if score_lower in word_to_num:
                        return word_to_num[score_lower]
                    digits = ''.join(filter(str.isdigit, score))
                    return int(digits) if digits else 0
                return 0

            # Check if all scores are >= 90%
            scores = [
                _to_int(validation_result.get('story_continuity_score', 0)),
                _to_int(validation_result.get('visual_alignment_score', 0)),
                _to_int(validation_result.get('engagement_score', 0)),
                _to_int(validation_result.get('transition_score', 0)),
                _to_int(validation_result.get('subtitle_timing_score', 0)),
                _to_int(validation_result.get('comment_bait_score', 0)),
                _to_int(validation_result.get('hook_strength_score', 0))
            ]
            
            # Length/scene-count gate: ensure storyboard has enough scenes/words for minimum duration
            storyboard = normalize_storyboard(final_script.get("storyboard", []))
            final_script["storyboard"] = storyboard
            total_words = sum(len(s.get("narration", "").split()) for s in storyboard if isinstance(s, dict))
            scene_count = len(storyboard)
            length_ok = scene_count >= 20 and total_words >= 90  # headroom above 76-word / 25s gate
            
            if all(score >= 90 for score in scores) and length_ok:
                print("   ⭐ Storyboard passed all quality checks (>90% scores)!")
                final_script["quality_scores"] = {
                    "story_continuity": _to_int(validation_result.get('story_continuity_score')),
                    "visual_alignment": _to_int(validation_result.get('visual_alignment_score')),
                    "engagement": _to_int(validation_result.get('engagement_score')),
                    "transitions": _to_int(validation_result.get('transition_score')),
                    "subtitle_timing": _to_int(validation_result.get('subtitle_timing_score')),
                    "comment_bait": _to_int(validation_result.get('comment_bait_score')),
                    "hook_strength": _to_int(validation_result.get('hook_strength_score', 0))
                }
                break
            else:
                feedback = validation_result.get('feedback', 'Improve storyboard flow, transition logic and visual alignment.')
                if not length_ok:
                    feedback += f"\nCRITICAL: Storyboard only has {scene_count} scenes / {total_words} words — you MUST produce 25-40 scenes to meet the required script length."
                print(f"   ⚠️ Storyboard failed quality checks. Feedback: {feedback}")
                print("   🔄 Triggering self-correction loop in Humanizer Agent...")
                
                correction_prompt = HUMANIZER_AGENT_TEMPLATE.format(
                    persona=SYSTEM_PERSONA,
                    optimized_script=optimized.get("optimized_script", ""),
                    schema_requirements=refined_requirements
                ) + f"\n\nCRITICAL FEEDBACK FROM AUDITOR (YOU MUST CORRECT THESE ISSUES AND RETRY):\n{feedback}"
                
                corrected_script = call_gemini_api(client, correction_prompt, model=GEMINI_FLASH_MODEL, category=category, task_type="reasoning")
                if corrected_script:
                    final_script = corrected_script
                validation_attempts += 1

        # ── AGENT 7: TITLE VARIANTS ──
        if final_script:
            print("🧠 [AGENT 7] Title Variants Agent: Generating 3 click-worthy title options...")
            title_variants_prompt = TITLE_VARIANTS_AGENT_TEMPLATE.format(
                persona=SYSTEM_PERSONA,
                script_text=final_script.get("script") or final_script.get("optimized_script") or optimized.get("optimized_script", "")
            )
            title_variants_res = call_gemini_api(client, title_variants_prompt, prefer_fallback=True, category=category, task_type="metadata")
            if title_variants_res and "title_variants" in title_variants_res:
                final_script["title_variants"] = title_variants_res["title_variants"]
            else:
                final_script["title_variants"] = [
                    final_script.get("title", "Secret Trick!"),
                    final_script.get("title", "Secret Trick!") + " 🤫",
                    "Don't Miss This! 🚨"
                ]

    if not final_script:
        print("⚠️ [gemini_script] Agent pipeline failed. Attempting offline fallback script...")
        final_script = get_offline_fallback_script(category, failed_topics)
        
    if final_script:
        # Map storyboard to subtitle_chunks for compatibility with main.py and downstream video gen
        if "storyboard" in final_script:
            final_script["storyboard"] = normalize_storyboard(final_script.get("storyboard"))
            subtitle_chunks = []
            rebuilt_script_parts = []
            for scene in final_script["storyboard"]:
                if not isinstance(scene, dict):
                    continue
                scene_num = scene.get("scene_number", len(subtitle_chunks) + 1)
                narration_text = sanitize_script_against_ai_cliches(str(scene.get("narration", "")))
                scene["narration"] = narration_text
                rebuilt_script_parts.append(narration_text)
                
                # Check visual type for infographic
                v_type = str(scene.get("visual_type", ""))
                info_type = str(scene.get("infographic_type", "none")).lower()
                
                # Check for visual type compatibility
                if "infographic" in v_type.lower() and info_type in ("none", ""):
                    info_type = "stat"
                
                has_info = info_type not in ("none", "")
                info_data = scene.get("infographic_data", {})
                
                # Extract stock_search_query from storyboard or fall back to visual_prompt
                vis_prompt = str(scene.get("visual_prompt", ""))
                stock_query = str(scene.get("stock_search_query", "")).strip()
                if not stock_query:
                    words = [w.strip(",.!?\"'") for w in vis_prompt.split() if len(w) > 3][:3]
                    stock_query = " ".join(words) if words else str(final_script.get("topic_category", "mystery fact"))
                
                chunk = {
                    "chunk_id": scene_num,
                    "text": narration_text,
                    "english_caption": scene.get("on_screen_text", ""),
                    "start": 0.0,
                    "end": 0.0,
                    "has_infographic": has_info,
                    "infographic_type": info_type,
                    "infographic_data": info_data,
                    "stock_search_query": stock_query,
                    "nano_visual_prompt": vis_prompt,
                    "visual_type": "photo" if "image" in v_type.lower() or "photo" in v_type.lower() else "video",
                    "camera_motion": scene.get("camera_motion", "None"),
                    "transition": scene.get("transition", "Match cut")
                }
                subtitle_chunks.append(chunk)
            
            final_script["subtitle_chunks"] = subtitle_chunks
            if not final_script.get("script"):
                final_script["script"] = "  ".join(rebuilt_script_parts)

        # Override metadata to match selected fact only if it was a generated template
        if final_script.get("original_news_headline") == "Fact Title" or not final_script.get("original_news_headline"):
            final_script["original_news_headline"] = selected_headline
            final_script["original_news_url"] = selected_url
            final_script["use_case_evidence_url"] = selected_url
        
        # Populate fallback fields if missing (robustness checks)
        if "title_variants" not in final_script:
            final_script["title_variants"] = [
                final_script.get("title", "Secret Trick!"),
                final_script.get("title", "Secret Trick!") + " 🤫",
                "Don't Miss This! 🚨"
            ]
        if "comment_bait_question" not in final_script:
            final_script["comment_bait_question"] = final_script.get("comment_hook") or "Ethu best-nu neenga neneikiringa?"
        
        # Attach Retention Scientist data and trending signal to output
        if retention_map:
            final_script["retention_map"] = retention_map
        if hot_topic_str:
            final_script["trending_topic"] = hot_topic_str
            
        final_script = apply_cta_rotation(final_script)
        
        # Save output in logs for debug
        os.makedirs(LOGS_DIR, exist_ok=True)
        log_path = os.path.join(LOGS_DIR, f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(final_script, f, indent=4, ensure_ascii=False)
            
        print(f"⭐ [PIPELINE] Multi-agent Tanglish script generation complete! Saved log: {log_path}")
        
    return final_script

def get_offline_fallback_script(category, failed_topics=None):
    """
    Loads a pre-packaged script from fallback_scripts.json matching the category.
    Avoids already used titles and previously failed topics if possible.
    Ensures script meets minimum word count (103+ words for 35s at 2.67 wps).
    """
    if failed_topics is None:
        failed_topics = []
        
    fallback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fallback_scripts.json")
    if not os.path.exists(fallback_path):
        print(f"⚠️ [gemini_script] fallback_scripts.json not found at {fallback_path}")
        return None
        
    try:
        with open(fallback_path, 'r', encoding='utf-8') as f:
            scripts = json.load(f)
    except Exception as e:
        print(f"⚠️ [gemini_script] Failed to load fallback_scripts.json: {e}")
        return None

    # Normalize category for matching (handle emoji prefixes and variations)
    def normalize_cat(cat):
        return cat.replace("🤖 ", "").replace("📱 ", "").strip().lower()
    
    norm_category = normalize_cat(category)
    
    # Filter matching category - try exact match first, then normalized match
    matching = [s for s in scripts if s.get("sub_category") == category]
    if not matching:
        matching = [s for s in scripts if normalize_cat(s.get("sub_category", "")) == norm_category]
    if not matching:
        # Broader match: check if category keywords are in sub_category
        cat_keywords = norm_category.split()
        matching = [s for s in scripts if any(kw in normalize_cat(s.get("sub_category", "")) for kw in cat_keywords)]
    if not matching:
        matching = scripts  # Fallback to all scripts

    # Calculate word count for each script
    for s in matching:
        script_text = s.get("script", "")
        s["_word_count"] = len(script_text.split()) if script_text else 0

    # Minimum word count for 25s at 2.55 wps = ~65-70 words
    MIN_WORDS = 70
    
    # Find scripts that pass full uniqueness check AND meet minimum word count
    unused = []
    for s in matching:
        s_title = s.get("title", "")
        s_news = s.get("original_news_headline", "")
        is_unique, _ = check_story_uniqueness(
            new_title=s_title,
            new_url=s.get("original_news_url") or s.get("use_case_evidence_url", "")
        )
        
        # Check against failed topics
        if is_unique and failed_topics:
            for ft in failed_topics:
                if ft and (ft.lower() in s_title.lower() or ft.lower() in s_news.lower()):
                    is_unique = False
                    break
                    
        # Check minimum word count
        word_count = s.get("_word_count", 0)
        if is_unique and word_count >= MIN_WORDS:
            unused.append(s)
        elif is_unique and word_count < MIN_WORDS:
            print(f"⚠️ [offline_fallback] Script '{s_title}' has only {word_count} words (min {MIN_WORDS}). Skipping.")
    
    # If no scripts meet word count, relax the requirement
    if not unused:
        print(f"⚠️ [offline_fallback] No scripts meet strict {MIN_WORDS} words with uniqueness. Checking all matching...")
        for s in matching:
            s_title = s.get("title", "")
            s_news = s.get("original_news_headline", "")
            is_unique, _ = check_story_uniqueness(
                new_title=s_title,
                new_url=s.get("original_news_url") or s.get("use_case_evidence_url", "")
            )
            
            if is_unique and failed_topics:
                for ft in failed_topics:
                    if ft and (ft.lower() in s_title.lower() or ft.lower() in s_news.lower()):
                        is_unique = False
                        break
                        
            if is_unique:
                unused.append(s)
    
    # Absolute safety fallback: if every pre-packaged script was covered in history,
    # generate a unique rotated variant so the pipeline NEVER crashes!
    if not unused:
        print("⚠️ [offline_fallback] All pre-packaged scripts were recently used. Creating fresh rotated variant to ensure pipeline completion.")
        import copy, time
        base_script = random.choice(matching or scripts)
        selected = copy.deepcopy(base_script)
        ts = int(time.time())
        date_str = datetime.now().strftime("%d %b")
        selected["title"] = f"{selected.get('title', 'Simple Tip')} ({date_str})"
        selected["original_news_headline"] = selected["title"]
        selected["original_news_url"] = f"https://en.wikipedia.org/wiki/Special:Random?v={ts}"
        selected["use_case_evidence_url"] = selected["original_news_url"]
        selected["relevant_links"] = [selected["original_news_url"]]
        return selected

    # Prefer scripts with higher word count
    unused.sort(key=lambda s: s.get("_word_count", 0), reverse=True)
    selected = random.choice(unused[:min(3, len(unused))])  # Pick from top longest scripts
    
    if selected:
        print(f"✅ [gemini_script] Offline fallback script selected: '{selected.get('title')}' ({selected.get('_word_count', 0)} words)")
        
        # Save output in logs for debug
        try:
            os.makedirs(LOGS_DIR, exist_ok=True)
            log_path = os.path.join(LOGS_DIR, f"script_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(selected, f, indent=4, ensure_ascii=False)
            print(f"⭐ [PIPELINE] Saved offline fallback script log: {log_path}")
        except Exception as e:
            print(f"⚠️ Failed to save fallback log: {e}")
            
    return selected

# Module-level cache for failed Cloudflare models (permanent errors like 400/403/404)
_FAILED_CLOUDFLARE_MODELS = set()

# Track if all LLM providers are exhausted to enable offline mode
_ALL_LLM_PROVIDERS_EXHAUSTED = False
_OFFLINE_MODE_ACTIVE = False

def is_offline_mode_active():
    """Return whether offline fallback mode is currently active."""
    global _OFFLINE_MODE_ACTIVE
    return _OFFLINE_MODE_ACTIVE

def set_offline_mode_active(val=True):
    """Set offline fallback mode status."""
    global _OFFLINE_MODE_ACTIVE, _ALL_LLM_PROVIDERS_EXHAUSTED
    _OFFLINE_MODE_ACTIVE = bool(val)
    if not val:
        _ALL_LLM_PROVIDERS_EXHAUSTED = False

def reset_offline_mode():
    """Reset provider exhaustion and offline mode for next retry attempt."""
    global _ALL_LLM_PROVIDERS_EXHAUSTED, _OFFLINE_MODE_ACTIVE
    _ALL_LLM_PROVIDERS_EXHAUSTED = False
    _OFFLINE_MODE_ACTIVE = False
    print("🔄 [gemini_script] Reset offline mode state for fresh attempt.")

def check_all_providers_exhausted():
    """Check if all LLM providers are exhausted based on config state."""
    global _ALL_LLM_PROVIDERS_EXHAUSTED, _OFFLINE_MODE_ACTIVE
    from config import is_gemini_disabled, CEREBRAS_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, DEEPSEEK_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID, SAMBANOVA_API_KEY, HUGGINGFACE_API_KEY
    
    # Check if Gemini is disabled
    gemini_disabled = is_gemini_disabled()
    
    # Check if other providers have keys configured
    cerebras_available = bool(CEREBRAS_API_KEY)
    groq_available = bool(GROQ_API_KEY)
    openrouter_available = bool(OPENROUTER_API_KEY)
    openai_available = bool(OPENAI_API_KEY)
    anthropic_available = bool(ANTHROPIC_API_KEY)
    deepseek_available = bool(DEEPSEEK_API_KEY)
    cloudflare_available = bool(CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID)
    sambanova_available = bool(SAMBANOVA_API_KEY)
    huggingface_available = bool(HUGGINGFACE_API_KEY)
    
    # If Gemini is disabled AND no other providers have keys, we're in offline mode
    if gemini_disabled and not any([cerebras_available, groq_available, openrouter_available, openai_available, anthropic_available, deepseek_available, cloudflare_available, sambanova_available, huggingface_available]):
        _ALL_LLM_PROVIDERS_EXHAUSTED = True
        _OFFLINE_MODE_ACTIVE = True
        print("🔴 [OFFLINE MODE] No LLM API keys configured. Switching to offline fallback scripts only.")
        return True
    
    return _ALL_LLM_PROVIDERS_EXHAUSTED

def set_providers_exhausted():
    """Mark all providers as exhausted (called when runtime failures occur)."""
    global _ALL_LLM_PROVIDERS_EXHAUSTED, _OFFLINE_MODE_ACTIVE
    if not _ALL_LLM_PROVIDERS_EXHAUSTED:
        _ALL_LLM_PROVIDERS_EXHAUSTED = True
        _OFFLINE_MODE_ACTIVE = True
        print("🔴 [OFFLINE MODE] All LLM providers exhausted at runtime. Switching to offline fallback scripts only.")

def call_fallback_model(prompt, category="", task_type="reasoning", expect_json=True):
    """
    Attempts to call fallback APIs according to the repository priority hierarchy:
    Priority 1: nvidia/nemotron-3-ultra-550b-a55b:free (Main content generation / reasoning)
    Priority 2: poolside/laguna-s-2.1:free (Coding + technical topics)
    Priority 3: nvidia/nemotron-3.5-lightning:free (Fast high-volume fallback)
    Priority 4: inclusionai/ling-3.0-flash-fin:free (Finance/business topics)
    Priority 5: Existing Gemini (handled upstream or as secondary fallback)
    followed by generic OpenRouter fallbacks -> Groq -> Cloudflare Workers AI -> OpenAI -> Anthropic (Claude) -> DeepSeek -> Cerebras -> SambaNova -> HuggingFace.
    Returns parsed JSON dict (if expect_json=True) or string response (if expect_json=False) or None.
    """
    import os
    import json
    import requests
    import time
    from config import get_ordered_models_for_category

    def clean_and_parse_json(content):
        raw = content.strip()
        if "```json" in raw:
            raw = raw[raw.find("```json")+7:raw.rfind("```")]
        elif "```" in raw:
            raw = raw[raw.find("```")+3:raw.rfind("```")]
        raw = raw.strip()
        try:
            return json.loads(raw)
        except Exception:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(raw[start:end+1])
            raise

    # 0. OpenRouter with prioritized models based on category & task
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        
        # Priority 1 to 4 models tailored by category/domain
        openrouter_models = get_ordered_models_for_category(category, task_type)
        
        # Extended fallback routers if top priorities are rate-limited
        for extra_model in [
            "openrouter/free",
            "qwen/qwen-2.5-72b-instruct",
            "moonshotai/kimi-k2.6",
            "google/gemini-2.5-flash",
        ]:
            if extra_model not in openrouter_models:
                openrouter_models.append(extra_model)

        for or_model in openrouter_models:
            print(f"🔮 Calling OpenRouter ({or_model}) [Domain: {category or 'General'}]...")
            try:
                payload = {
                    "model": or_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
                if expect_json:
                    payload["response_format"] = {"type": "json_object"}

                r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=30)
                
                # If json_object format was rejected (400), retry without it
                if r.status_code == 400 and expect_json:
                    payload.pop("response_format", None)
                    r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=30)

                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    if expect_json:
                        return clean_and_parse_json(content)
                    return content
                elif r.status_code == 429:
                    err_text = r.text.lower()
                    if "free-models-per-day" in err_text or "daily" in err_text:
                        print("🚫 OpenRouter daily free tier limit reached. Skipping remaining OpenRouter models.")
                        break
                    print(f"⚠️ OpenRouter ({or_model}) rate limited (429). Retrying next priority model...")
                    time.sleep(1)
                    continue
                elif r.status_code == 402:
                    print(f"⚠️ OpenRouter insufficient credits (402). Skipping remaining paid OpenRouter models.")
                    break
                else:
                    print(f"⚠️ OpenRouter API ({or_model}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ OpenRouter ({or_model}) fallback failed: {e}")

    # 1. Groq (current developer-plan models with 429 retry logic)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        groq_models = [
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3.8-27b",
        ]
        for model_name in groq_models:
            print(f"🔮 Falling back to Groq ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                if expect_json:
                    payload["response_format"] = {"type": "json_object"}

                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    if expect_json:
                        return clean_and_parse_json(content)
                    return content
                elif r.status_code == 429:
                    print(f"⚠️ Groq ({model_name}) rate limited (429). Retrying after delay...")
                    time.sleep(5)
                    continue
                else:
                    print(f"⚠️ Groq ({model_name}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ Groq ({model_name}) fallback failed: {e}")

    # 2. Cloudflare Workers AI (with daily quota check)
    cloudflare_token = os.getenv("CLOUDFLARE_API_TOKEN")
    cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    if cloudflare_token and cloudflare_account_id:
        from config import CLOUDFLARE_MODELS
        headers = {
            "Authorization": f"Bearer {cloudflare_token}",
            "Content-Type": "application/json"
        }
        gpt_oss_models = {"@cf/openai/gpt-oss-120b", "@cf/openai/gpt-oss-20b"}
        for model_name in CLOUDFLARE_MODELS:
            if model_name in _FAILED_CLOUDFLARE_MODELS:
                print(f"⏭️ Skipping known-bad Cloudflare model: {model_name}")
                continue
            print(f"🔮 Falling back to Cloudflare ({model_name})...")
            try:
                payload = {
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
                if expect_json:
                    payload["response_format"] = {"type": "json_object"}

                r = requests.post(
                    f"https://api.cloudflare.com/client/v4/accounts/{cloudflare_account_id}/ai/run/{model_name}",
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                if r.status_code == 200:
                    result = r.json()["result"]
                    if model_name in gpt_oss_models:
                        raw_content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    elif isinstance(result, dict) and "choices" in result and result["choices"]:
                        raw_content = result["choices"][0].get("message", {}).get("content", "")
                    else:
                        raw_content = result.get("response", "") if isinstance(result, dict) else ""
                    if isinstance(raw_content, dict):
                        return raw_content if expect_json else json.dumps(raw_content)
                    content = raw_content.strip() if isinstance(raw_content, str) else ""
                    if content:
                        if expect_json:
                            return clean_and_parse_json(content)
                        return content
                    else:
                        print(f"⚠️ Cloudflare ({model_name}) returned empty content")
                else:
                    err_text = r.text.lower()
                    print(f"⚠️ Cloudflare ({model_name}) failed with code {r.status_code}: {r.text}")
                    if "daily free allocation" in err_text or "neurons" in err_text:
                        print("🚫 Cloudflare daily quota exhausted. Skipping all remaining CF models.")
                        break
                    if r.status_code in (400, 403, 404):
                        _FAILED_CLOUDFLARE_MODELS.add(model_name)
                        print(f"🚫 Caching {model_name} as permanently failed for this run")
            except Exception as e:
                print(f"⚠️ Cloudflare ({model_name}) fallback failed: {e}")

    # 3. OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("🔮 Falling back to OpenAI (gpt-4o-mini)...")
        try:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            if expect_json:
                payload["response_format"] = {"type": "json_object"}

            r = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                if expect_json:
                    return clean_and_parse_json(content)
                return content
            else:
                print(f"⚠️ OpenAI API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ OpenAI fallback failed: {e}")

    # 4. Anthropic (Claude)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print("🔮 Falling back to Anthropic (claude-3-5-haiku-20241022)...")
        try:
            headers = {
                "x-api-key": anthropic_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 4000,
                "messages": [{"role": "user", "content": prompt}]
            }
            r = requests.post("https://api.anthropic.com/v1/messages", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["content"][0]["text"].strip()
                if expect_json:
                    return clean_and_parse_json(content)
                return content
            else:
                print(f"⚠️ Anthropic API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ Anthropic fallback failed: {e}")

    # 5. DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    if deepseek_key:
        print("🔮 Falling back to DeepSeek (deepseek-chat)...")
        try:
            headers = {
                "Authorization": f"Bearer {deepseek_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
            if expect_json:
                payload["response_format"] = {"type": "json_object"}

            r = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                if expect_json:
                    return clean_and_parse_json(content)
                return content
            else:
                print(f"⚠️ DeepSeek API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ DeepSeek fallback failed: {e}")

    # 6. Cerebras (lower priority, documented production models)
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    if cerebras_key:
        headers = {
            "Authorization": f"Bearer {cerebras_key}",
            "Content-Type": "application/json"
        }
        cerebras_models = ["llama3.1-8b", "gpt-oss-120b"]
        for model_name in cerebras_models:
            print(f"🔮 Falling back to Cerebras ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
                if expect_json:
                    payload["response_format"] = {"type": "json_object"}

                r = requests.post("https://api.cerebras.ai/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    if expect_json:
                        return clean_and_parse_json(content)
                    return content
                else:
                    print(f"⚠️ Cerebras API ({model_name}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ Cerebras ({model_name}) fallback failed: {e}")

    # 7. SambaNova (fast Llama/DeepSeek inference — OpenAI-compatible API)
    sambanova_key = os.getenv("SAMBANOVA_API_KEY")
    if sambanova_key:
        headers = {
            "Authorization": f"Bearer {sambanova_key}",
            "Content-Type": "application/json"
        }
        sambanova_models = [
            "Meta-Llama-3.3-70B-Instruct",
            "DeepSeek-V3.2",
            "MiniMax-M3",
            "gpt-oss-120b"
        ]
        for model_name in sambanova_models:
            print(f"🔮 Falling back to SambaNova ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
                if expect_json:
                    payload["response_format"] = {"type": "json_object"}

                r = requests.post("https://api.sambanova.ai/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    if expect_json:
                        return clean_and_parse_json(content)
                    return content
                elif r.status_code == 429:
                    print(f"⚠️ SambaNova ({model_name}) rate limited (429). Trying next model...")
                    time.sleep(2)
                    continue
                elif r.status_code == 402:
                    print(f"⚠️ SambaNova requires payment method / balance (402). Skipping remaining SambaNova models.")
                    break
                else:
                    print(f"⚠️ SambaNova ({model_name}) failed with code {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"⚠️ SambaNova ({model_name}) fallback failed: {e}")

    # 8. HuggingFace Inference API (free serverless — OpenAI-compatible router)
    hf_key = os.getenv("HUGGINGFACE_API_KEY")
    if hf_key:
        headers = {
            "Authorization": f"Bearer {hf_key}",
            "Content-Type": "application/json"
        }
        hf_models = [
            "meta-llama/Llama-3.3-70B-Instruct",
            "Qwen/Qwen2.5-72B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct"
        ]
        for model_name in hf_models:
            print(f"🔮 Falling back to HuggingFace ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "stream": False
                }
                # Modern HF router endpoint (OpenAI compatible)
                r = requests.post("https://router.huggingface.co/hf-inference/v1/chat/completions", json=payload, headers=headers, timeout=60)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    if expect_json:
                        return clean_and_parse_json(content)
                    return content
                elif r.status_code == 429:
                    print(f"⚠️ HuggingFace ({model_name}) rate limited (429). Trying next model...")
                    time.sleep(2)
                    continue
                elif r.status_code == 503:
                    print(f"⚠️ HuggingFace ({model_name}) model loading (503). Trying next model...")
                    continue
                else:
                    print(f"⚠️ HuggingFace ({model_name}) failed with code {r.status_code}: {r.text[:200]}")
            except Exception as e:
                print(f"⚠️ HuggingFace ({model_name}) fallback failed: {e}")

    # All fallbacks exhausted
    print("🚨 All fallback models exhausted. Setting offline mode.")
    set_providers_exhausted()
    return None

def call_gemini_api(client_arg, prompt, model=None, prefer_fallback=False, category="", task_type="reasoning", expect_json=True):
    """
    Helper to execute pipeline model calls according to the 5-tier priority hierarchy:
    Priority 1: nvidia/nemotron-3-ultra-550b-a55b:free (Main content generation / reasoning)
    Priority 2: poolside/laguna-s-2.1:free (Coding + technical topics)
    Priority 3: nvidia/nemotron-3.5-lightning:free (Fast high-volume fallback)
    Priority 4: inclusionai/ling-3.0-flash-fin:free (Finance/business topics)
    Priority 5: Google Gemini API (gemini-3.8-flash, gemini-3.5-flash-lite, gemini-3.1-pro-preview, with Gemini 2.5 legacy fallbacks)
    """
    from config import is_gemini_disabled
    
    # Check if we're already in offline mode
    if _OFFLINE_MODE_ACTIVE:
        print("🔴 [OFFLINE MODE] Skipping all LLM API calls. Using offline fallback.")
        return None
    
    if is_gemini_disabled():
        print("🚨 Gemini is currently disabled due to rate limit/depletion. Proceeding directly to fallback models.")
        return call_fallback_model(prompt, category=category, task_type=task_type, expect_json=expect_json)

    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if prefer_fallback or openrouter_key:
        print(f"💡 Attempting prioritized model (P1-P4) for '{category or 'main content'}'...")
        fallback_res = call_fallback_model(prompt, category=category, task_type=task_type, expect_json=expect_json)
        if fallback_res:
            print("   ✅ Handled successfully by prioritized model!")
            return fallback_res
        print("   🔄 Prioritized OpenRouter models exhausted or rate-limited. Routing to Priority 5 (Gemini API)...")

    client = client_arg or get_gemini_client()
    if not client:
        client = get_gemini_client()

    attempts = 0
    max_attempts = max(16, len(GEMINI_API_KEYS) * 4)
    keys_rotated_in_a_row = 0

    # Define model list to cycle/fallback through: Gemini 3 primary, then supported Gemini 2.5 legacy
    target_model = model or GEMINI_FLASH_MODEL
    models_to_try = [target_model]
    for m in [
        GEMINI_FLASH_MODEL,          # gemini-3.8-flash (Current default workhorse)
        GEMINI_FLASH_LITE_MODEL,     # gemini-3.5-flash-lite (Fast/microtasks)
        GEMINI_PRO_MODEL,            # gemini-3.1-pro-preview (Deep reasoning)
        "gemini-2.5-flash",          # Maintained legacy tier
        "gemini-2.5-pro",            # Maintained legacy reasoning
        "gemini-2.5-flash-lite",     # Maintained legacy budget
    ]:
        if m not in models_to_try:
            models_to_try.append(m)
    
    model_idx = 0

    while attempts < max_attempts and models_to_try:
        current_model = models_to_try[model_idx % len(models_to_try)]
        try:
            print(f"🔮 Calling Gemini API with model {current_model} (Priority 5)...")
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json" if expect_json else "text/plain"
                )
            )
            raw = response.text.strip()
            if not expect_json:
                return raw
            # Clean possible markdown wrapping
            if "```json" in raw:
                raw = raw[raw.find("```json")+7:raw.rfind("```")]
            elif "```" in raw:
                raw = raw[raw.find("```")+3:raw.rfind("```")]
            
            raw = raw.strip()
            try:
                return json.loads(raw)
            except Exception:
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1 and end > start:
                    return json.loads(raw[start:end+1])
                raise
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit_or_overload = any(
                keyword in err_str 
                for keyword in ["503", "429", "unavailable", "rate limit", "resource exhausted", "demand", "temporary"]
            )
            is_credit_depleted = "prepayment credits" in err_str or "depleted" in err_str
            
            if is_rate_limit_or_overload or is_credit_depleted:
                print(f"⚠️ [Gemini API Overload/Rate-Limit/Depleted] {e}")
                
                # Check key rotation first
                if len(GEMINI_API_KEYS) > 1 and keys_rotated_in_a_row < len(GEMINI_API_KEYS):
                    rotate_gemini_api_key()
                    client = get_gemini_client()
                    keys_rotated_in_a_row += 1
                    print(f"🔄 Rotated key to attempt next API key. Retrying immediately (attempt {attempts+1}/{max_attempts})...")
                    attempts += 1
                    continue
                
                # If we tried all keys or only have 1 key, remove the model
                print(f"🚫 Model {current_model} failed on all keys. Removing from rotation.")
                models_to_try.pop(model_idx % len(models_to_try))
                keys_rotated_in_a_row = 0
                
                if models_to_try:
                    next_model = models_to_try[model_idx % len(models_to_try)]
                    print(f"🔄 Switching model to fallback: {next_model}. Retrying immediately...")
            else:
                print(f"⚠️ Agent call failed: {e}. Removing {current_model} from rotation.")
                models_to_try.pop(model_idx % len(models_to_try))
                keys_rotated_in_a_row = 0
                
                if models_to_try:
                    next_model = models_to_try[model_idx % len(models_to_try)]
                    print(f"🔄 Switching model to fallback: {next_model}. Retrying immediately...")
                    
            attempts += 1
            
    print("🚨 All Gemini models depleted or failed. Attempting secondary fallback models...")
    fallback_res = call_fallback_model(prompt, category=category, task_type=task_type, expect_json=expect_json)
    if fallback_res:
        return fallback_res

    print("🚨 All fallback models failed or not configured. Setting offline mode.")
    set_providers_exhausted()
    return None

