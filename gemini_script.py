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

# ── PROMPT TEMPLATES (TAMIL SHORTS AGENTIC LOOP) ──────────────────────────────────

TOPIC_SELECTOR_PROMPT = """You are a Tamil AI education content strategist for YouTube Shorts.

Generate 1 viral-worthy AI concept topic for a 45-60 second Tamil/Tanglish Short targeting:
- Students (school/college) curious about AI
- Working professionals wanting to understand AI tools they use daily
- Elders (50+) who hear about AI on news and want to understand it

TOPIC RULES:
- Must connect to something the audience already experiences (phone, WhatsApp, Google, Swiggy, bank, hospital, etc.)
- Must be explainable in 60 seconds without math
- Must have a surprising or counterintuitive hook
- Avoid: "Top 5 AI tools", "ChatGPT tricks", news-based topics
- Focus on: HOW things work, WHY AI behaves certain ways, WHAT concepts mean in real life

OUTPUT FORMAT (JSON only, no preamble):
{
  "topic": "short topic name in English",
  "tamil_title": "YouTube title in Tanglish (max 60 chars, curiosity-driven)",
  "hook_question": "opening question in Tanglish that makes viewer stop scrolling",
  "core_concept": "the actual AI concept being taught (e.g. overfitting, attention, embeddings)",
  "real_world_example": "specific Tamil-relatable example to explain it",
  "surprising_fact": "one counterintuitive or wow fact about this concept",
  "difficulty": "beginner/intermediate",
  "target_segment": "students/professionals/elders/all"
}"""

SCRIPT_GENERATION_PROMPT = """You are a Tamil AI education YouTuber who makes complex AI concepts simple and fun.

Write a YouTube Shorts script in Tanglish (Tamil + English mix, natural spoken style) for this topic:

TOPIC: {topic}
HOOK QUESTION: {hook_question}
CORE CONCEPT: {core_concept}
REAL WORLD EXAMPLE: {real_world_example}
SURPRISING FACT: {surprising_fact}
TARGET AUDIENCE: {target_segment}

SCRIPT RULES:
1. DURATION: 260-350 words max (approx 103-138 seconds at normal pace, ~90-120s at 1.15x speed)
2. LANGUAGE: Natural Tanglish — Tamil sentences with English technical terms inline. NOT translated English. NOT pure Tamil.
   Good: "Ungal phone face unlock panna, oru neural network realtime-la ungal face-a 128 different points-la analyze pannum"
   Bad: "Your phone uses artificial intelligence to recognize your face using neural network technology"
3. STRUCTURE (strict):
   - Hook (0-5 sec): Surprising question or statement. Start with "Oru vishayam theriyuma?" or similar
   - Concept body (5-35 sec): Explain using the real world example. Use simple analogy.
   - Wow moment (35-45 sec): The surprising fact that reframes everything
   - CTA (45-50 sec): "Ithu pathi innum therinja comment pannunga" or similar
4. TONE: Like an excited friend explaining something cool, not a teacher lecturing
5. NO: Statistics, percentages, named researchers, paper citations
6. YES: Specific product names (Swiggy, GPT, Google Maps), relatable situations, conversational fillers (aama, illaya, paarunga)

OUTPUT: Script text only, no labels, no timestamps, ready for text-to-speech."""

TITLE_TAGS_PROMPT = """You are a Tamil YouTube SEO expert specializing in AI education content.

Generate metadata for this Tamil AI education Short:

TOPIC: {topic}
CORE CONCEPT: {core_concept}
SCRIPT SUMMARY: {first_two_sentences_of_script}

OUTPUT FORMAT (JSON only):
{{
  "title": "Tanglish title, max 60 chars, must include curiosity gap or number, avoid clickbait",
  "description": "3-4 sentences in Tanglish explaining what viewer will learn. End with 'Comment pannunga - innum theriyanum-na!'",
  "hashtags": ["#AITamil", "#TechTamil", 8 more relevant tags in English and Tamil],
  "thumbnail_text": "3-5 bold words in Tanglish for thumbnail overlay (creates curiosity)",
  "thumbnail_visual_concept": "describe what the thumbnail should show in one sentence"
}}

TITLE FORMULAS THAT WORK:
- "Ungal [daily thing] ethana AI use pannudhu theriyuma?"
- "[AI concept] - Simple-a explain pannuren!"
- "Yen [AI tool] ungalai [behavior]? - Unmai theriyuma"
- "[Number] seconds-la [concept] purinju vidunga!"
"""

PIPELINE_PROMPTS = {
    "topic_selector": TOPIC_SELECTOR_PROMPT,
    "script_writer": SCRIPT_GENERATION_PROMPT,
    "metadata": TITLE_TAGS_PROMPT,
}

TOPIC_CATEGORIES = [
    "how_daily_apps_work",      # Swiggy, Google Maps, YouTube
    "ai_concepts_simplified",   # overfitting, embeddings, attention
    "ai_myths_busted",          # "AI thinks", "AI is dangerous"
    "ai_in_india_context",      # UPI fraud detection, Aadhaar, IRCTC
    "career_and_future",        # what skills matter, what jobs change
]


SYSTEM_PERSONA = """Role: You are a viral Tamil YouTube Shorts scriptwriter specializing in infotainment ("Simple Tips by VJ").
Your goal is to explain extremely useful, trending tech/smart life hacks, study tricks, phone settings, health tips, and financial hacks in a super engaging, conversational way that helps everyday people improve their lives.
Tone: Relatable, friendly, clear, and engaging South Indian Tamil guy (like a tech/lifestyle creator or a local RJ/VJ). Natural, enthusiastic, and easy to follow. Speak clearly and articulate every word so that Tamil viewers all over the world can understand easily. Speak with high-energy, fast-paced, direct, and enthusiastic conversational delivery (pacing, tone, and inflection should sound exactly like a high-retention popular infotainment short). Avoid overly dramatic anime narrator style, shouting, or hyper-reactive shouting. Maintain a clean, professional yet friendly creator tone.
Target Audience: Tamil-speaking viewers aged 16–35 who love tech, hacks, and smart life tips, spanning:
1) Parents (cares about screen safety, child learning, budgeting, and home convenience).
2) Middle-aged (cares about smartphone utility, WhatsApp/finance security, spam blocking, and daily efficiency).
3) Young People (cares about AI tools, phone/PC customization, study hacks, fast tricks, and speed).
Language Rules:
1. Voiceover Script (`script`, `hook_script`, `problem_context`, `solution_tech`, `retention_loop`, `outro_cta`): Write in colloquial, day-to-day spoken Tamil (Tanglish) mixed with common English words as naturally spoken in conversation (e.g. "phone settings", "shortcut", "verify", "memory" written in their English alphabet or phonetic forms where appropriate). Do NOT use overly formal, literary, or archaic Tamil words (e.g., use standard spoken words like 'பண்ணுங்க' instead of 'செய்யுங்கள்'). Enforce clean and universally understandable Tanglish/colloquial vocabulary, avoiding obscure local dialects or heavy slang that would confuse Tamil speakers globally.
   Example: "உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க! உங்க browser speed-ஐ boost பண்ண ஒரு simple hack..."
   Style Reference Example (Use this exact spoken tone and structure flow):
   "உங்க போனை ராக்கெட் வேகத்துல மாத்தணுமா? போன் ரொம்ப ஸ்லோவா இருக்கா? ஆப்ஸ் ஓபன் ஆக லேட் ஆகுதா? ஸ்கிரீன் ட்ரான்சிஷன் லேக் ஆகுதா? டெய்லி யூஸ் கஷ்டமா இருக்கா? அப்போ உங்க ஆண்ட்ராய்டு போன்ல செட்டிங்ஸ் போங்க. கீழே ஸ்க்ரோல் பண்ணி அபௌட் போன கிளிக் பண்ணுங்க. அங்க பில்ட் நம்பரை செவன் தடவை டாப் பண்ணுங்க. டெவலப்பர் ஆப்ஷன்ஸ் உடனே எனேபிள் ஆகும். ஆனா வெயிட் பண்ணுங்க. இதுல ஒரு ட்விஸ்ட் இருக்கு. இப்போ செட்டிங்ஸ்ல டெவலப்பர் ஆப்ஷன்ஸ்குள்ள போங்க. கீழ ஸ்க்ரோல் பண்ணீங்கன்னா விண்டோ அனிமேஷன் ஸ்கேல், ட்ரான்சிஷன் அனிமேஷன் ஸ்கேல், அனிமேட்டர் டுரேஷன் ஸ்கேல் இந்த மூணு செட்டிங்ஸையும் ஜீரோ. இல்லன்னா ஆஃப் பண்ணிடுங்க. அவ்வளவுதான். உங்க போன் இப்போ புதுசா வாங்குன மாதிரி படு வேகமா இருக்கும். இந்த ஹேக் யூஸ்ஃபுல்லா இருந்ததா? உங்க போன் ஸ்பீட் எப்படி இருக்கு? கமெண்ட்ஸ்ல சொல்லுங்க. மறக்காம ஷேர் பண்ணுங்க."
2. Subtitles & Captions (`subtitle_chunks`):
   - The `text` field MUST contain the spoken Tanglish segment for that chunk to ensure perfect audio-to-text alignment.
   - The `english_caption` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words in English in uppercase, e.g., "PHONE SETTING", "BOOST SPEED", "5-SECOND RULE", "FOCUS HACK") representing the central concept spoken in that chunk. Do NOT write Tamil text or complete sentences in `english_caption`. These will be displayed as bold, clean English captions on screen to highlight important takeaways.
3. Spacing Guard: Ensure proper spaces are placed between words. Never concatenate Tamil and English words together (e.g. write 'Replacement இருக்கு' instead of 'Replacementஇருக்கு'), never concatenate distinct English words (e.g. write 'shortcut code' instead of 'shortcutcode', 'time save' instead of 'timesave'), and never concatenate distinct Tamil words (e.g. write 'இதை பாருங்க' instead of 'இதைபாருங்க'). Always verify word boundaries.
4. Visual prompts (`nano_visual_prompt`): MUST be written in English. CRITICAL: AI/TECH VISUAL STYLE ONLY.
   - ART STYLE: Photorealistic 8K, cinematic lighting, 9:16 vertical format. AI/TECH AESTHETIC ONLY.
   - ALLOWED: Neural network visualizations, glowing data streams, code terminal interfaces, holographic UI panels, fiber optic cables, server racks with blinking LEDs, quantum circuit diagrams, abstract geometric data flows, futuristic control rooms, clean minimalist tech environments.
   - COLOR PALETTE: Deep blues, electric cyan, emerald green, amber gold on dark backgrounds.
   - LIGHTING: Volumetric lighting, depth of field, ray-traced reflections. Professional keynote presentation quality (Apple WWDC / Google I/O / NVIDIA GTC style).
   - FORBIDDEN: NO human faces, NO cartoon characters, NO Pixar/Disney style, NO clay textures, NO expressive eyes, NO anatomical figures, NO distorted eyes, NO asymmetrical objects, NO floating nonsense geometry, NO people of any ethnicity.
   - CAMERA: Smooth, intentional movements (slow dolly, subtle orbit, gentle zoom). NO rapid spinning, NO intense panning, NO dramatic tilts.
   - CONTINUITY: Each prompt MUST reference the SCENE ID and maintain consistent environment, lighting, and key visual elements with other chunks in the same scene.
Constraint Checklist:
- SCRIPT STRUCTURE (MANDATORY 4-PART FORMAT):
  1. HOOK (0–5 seconds / ~15 words): A shocking fact or bold statement to stop scrolling immediately. Do NOT use greetings (like "வணக்கம்" or "நமஸ்காரம்").
  2. PROBLEM (5–20 seconds / ~50-70 words): Highlight a daily pain point that the viewer feels directly. Make them feel "this is my problem too!".
  3. SOLUTION (20–100 seconds / ~150-220 words): Explain a single, simple, and clear tip or hack. Very easy to understand.
  4. ENGAGEMENT QUESTION (100–115 seconds / ~25-35 words): End with a simple, opinion-based question that anyone can answer, driving them to comment.
- SCRIPT WORD COUNT: Strictly 260-350 words in Tanglish (to fit the 90-120 second total duration).
- SCRIPT SENTENCES: Every sentence must be COMPLETE and end with proper punctuation (., !, ?). Under 12 words each for fast-paced delivery. NO sentence fragments or trailing incomplete thoughts.
- EARLY TOPIC CLARITY: In the first 3-5 seconds of the narration (within the hook/problem transition), explicitly name the topic, app, or setting.
- PATTERN_INTERRUPT STORYBOARD BEAT: You must include a storyboard scene labeled exactly "PATTERN_INTERRUPT" in its visual_type field at exactly the midpoint (50% position) of the storyboard array. This scene should have a clear visual transition and use spoken phrases like "aana wait pannunga, ithula oru twist irukku!" (highly recommended to match VJ's style), "oru second wait pannunga...", or "ithai parunga..." to break the pattern and regain interest.
- VOCAL DYNAMICS: Use heavy punctuation (commas, ellipses '...', exclamation marks) to guide pronunciation emphasis and standard pauses. Maintain a clear, steady, and engaging delivery suitable for clear narration. Avoid extreme emotional shouting.
- TTS COMPATIBILITY: Write complete sentences only. No bullet points, no sentence fragments, no "etc." endings. Each sentence must be grammatically complete in Tanglish.
"""

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
Hooks MUST address a highly relatable everyday frustration or surprise, and promise an immediate, easy solution (especially tech-based settings/apps/shortcuts), creating extreme curiosity in Tamil/Tanglish.
No greetings. No generic statements. Start with the core problem/result first!
Hooks must NOT be generic (e.g., 'Change this setting'). They MUST mention the specific topic or immediate payoff.
The hook must sound like a friendly, clear, and relatable South Indian Tamil guy narrator, avoiding anime tropes or fantasy phrases (do NOT use 'Ithu plot twist da!', 'Final boss level hack!', 'Hidden power unlock aaguthu!', etc.).

SCORING CRITERIA:
- curiosity_score: How much does this make someone NEED to know the answer? (1-10)
- emotional_trigger_score: How strongly does this hit a pain point or desire? (1-10)
- swipe_stop_power: Would this make someone physically STOP scrolling on their phone? Hooks that start with numbers, shocking claims, direct address, or challenge assumptions score highest. (1-10)
- topic_specificity_score: How clear is it what specific setting, app, or daily problem the video is about? High scores require mentioning the specific target (e.g. battery, WhatsApp, Wi-Fi speed) instead of general 'tricks' or 'hacks'. (1-10)

RESEARCH:
{research_json}

Return ONLY a JSON object:
{{
  "hooks": [
    {{
      "text": "Tanglish hook text (e.g. 'உங்க phone battery-ஐ டபுள் ஆக்க இந்த ஒரு secret setting போதும்!')",
      "curiosity_score": 1-10,
      "emotional_trigger_score": 1-10,
      "swipe_stop_power": 1-10,
      "topic_specificity_score": 1-10,
      "reason": "Why it works"
    }}
  ]
}}"""

NARRATIVE_AGENT_TEMPLATE = """{persona}

NARRATIVE AGENT TASK:
Using the selected hook and research, create a step-by-step tutorial or tip flow that is highly appealing to our target demographics (parents, middle-aged, and youth) following our mandatory 4-part structure.

MANDATORY STRUCTURE:
1. HOOK (0-3 seconds): A shocking fact or bold statement. No greetings. Stop the scroll instantly.
2. PROBLEM (3-15 seconds): Define a daily pain point that the viewer experiences directly.
3. SOLUTION (15-45 seconds): Explain the simple, clear tip or hack. Explain a single idea clearly.
4. ENGAGEMENT QUESTION (45-55 seconds): A simple opinion-based question in Tanglish to drive comments.

VIRAL RETENTION TECHNIQUES (MANDATORY):
- RAPID PACING: Every sentence must be under 12 words. No long explanations.
- TOPIC CLARITY DIRECTIVE: Explicitly state what specific tool, settings page, or technique is being used in the first 5 seconds.

Include:
1. HOOK (0-3s)
2. PROBLEM (3-15s)
3. SOLUTION (15-45s)
4. ENGAGEMENT QUESTION (45-55s)

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
1. TOTAL WORD COUNT: Strictly 260-350 words.
2. SCRIPT STRUCTURE (MANDATORY):
   - HOOK (0-5s): Shocking fact/bold statement. No greeting.
   - PROBLEM (5-20s): Daily pain point.
   - SOLUTION (20-100s): Simple, clear tip/hack (single idea).
   - ENGAGEMENT QUESTION (100-115s): Simple opinion-based question to prompt comments.
3. SCRIPT SENTENCES: Every sentence must be COMPLETE, grammatically correct, and end with proper punctuation (., !, ?). Under 12 words each. NO fragments.
4. Ensure the script directly resonates with daily scenarios.
5. Add an ellipsis '...' after key settings or complex terms to force the TTS to pause naturally.
6. TOPIC VERIFICATION: Verify that the exact setting, app name, or topic is named clearly and explicitly in the first 5 seconds.
7. TTS COMPATIBILITY: Every sentence must be a complete grammatical unit in Tanglish. No "etc.", no bullet-style fragments, no trailing incomplete thoughts.

NARRATIVE DRAFT:
{narrative_json}

Return ONLY a JSON object:
{{
  "optimized_script": "The full rewritten text combining all parts into a fast-paced Tanglish script adhering to the 4-part structure. STRICTLY 260-350 words.",
  "word_count": 0
}}"""

# ── PHASE 2: RETENTION SCIENTIST AGENT ────────────────────────────────────────
RETENTION_SCIENTIST_TEMPLATE = """{persona}

RETENTION SCIENTIST TASK:
Analyze the optimized Tamil/Tanglish script and inject PROVEN retention patterns at calculated intervals.
You are a YouTube Shorts retention strategist for Tamil infotainment content. Your ONLY job is to maximize the percentage of viewers who watch to the end.

CRITICAL RETENTION RULES (based on 2026 YouTube Shorts algorithm data):
1. HOOK DENSITY: The first 1.5 seconds (first 6 words) MUST contain a surprising claim, stat, or contradiction in Tanglish.
   - BAD: "Intha video-la namma paarka porom..."
   - GOOD: "Ungka phone-la irukura intha setting ungkalai spy panudhu!"

2. OPEN LOOPS: Plant at least 2-3 "open loops" (unanswered questions) in the first 20 seconds.
   - Technique: Mention something intriguing but don't resolve it for 8-12 seconds.
   - Example: "Aana ithu mattum illa, oru periya problem irukku..." then continue with OTHER info before resolving.

3. PATTERN INTERRUPTS: Every 8-12 seconds, inject a cognitive shift:
   - Rhetorical question ("Aana wait pannunga...")
   - Contradiction ("Aana ithu thaan twist!")
   - Number/stat bomb ("86 billion neurons!")
   - Direct address ("Ithu ungkalukku yen mukkiyam-nu theriyuma?")
   - Emotional pivot ("Athu thaan yellaam maariduchu.")

4. CURIOSITY GAPS: End every major point with an incomplete thought that requires the next sentence to resolve.
   - BAD: "Intha setting-ai maaththunga. Adhula ungka phone fast aagum."
   - GOOD: "Intha setting-ai maaththunga. Aana adhukku apram nadapadhu thaan unmaiyaana surprise..."

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
Based on the following research context and selected script/topic, generate 3 highly click-worthy YouTube Short titles (each under 50 characters, include relevant emojis):
1. Variant 1 (Curiosity): A title that builds a curiosity gap, question, or teaser (e.g. 'Intha phone trick theriyuma? 🤫').
2. Variant 2 (Fear/Loss): A title that highlights fear of missing out, security risk, or a common mistake to avoid (e.g. 'Udaney intha setting-ai maathungaa! 🚨').
3. Variant 3 (Direct Benefit): A title that directly promises a clear benefit, speed-up, or money-saving result (e.g. 'Browser speed-ai 2x aaka hack! 🚀').

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
This is the final step. Fix any robotic phrasing or overly formal/literary Tamil words. Ensure the speech is in highly colloquial, day-to-day spoken Tamil (Tanglish) with a natural mix of English words (natural, friendly, high-energy).
Format the output EXACTLY matching the required schema below.

OPTIMIZED SCRIPT:
{optimized_script}

SCHEMA REQUIREMENTS:
{schema_requirements}

CRITICAL STORYBOARD & SCENE RULES:
In the `storyboard` array:
- Each scene/chunk MUST be SHORT: 3-5 words maximum in the `narration` field to ensure punchy karaoke-style captions on screen.
- You MUST produce at least 25-40 storyboard scenes for the full script to ensure perfect word-by-word alignment.
- The `narration` field MUST contain the exact spoken Tanglish phrase for alignment (3-5 words only).
- The `on_screen_text` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words maximum in English, in uppercase, e.g., "BRAIN CELLS", "86 BILLION", "PHONE SETTING", "STRENGTH") representing the central concept.
- The `scene_objective` must briefly describe what technical/lifestyle concept is explained.
- Choose `visual_type` dynamically based on the content (e.g. 'Google Video Generation', 'Animated Infographics', 'Whiteboard Animation', 'Motion Graphics', 'PATTERN_INTERRUPT').
- At exactly the midpoint (50% position) of the storyboard array, you must include a mandatory pattern interrupt scene where `visual_type` is set to "PATTERN_INTERRUPT". The spoken narration for this midpoint scene must use a phrase like "aana wait pannunga, ithula oru twist irukku!" (highly recommended), "oru second wait pannunga...", or "ithai parunga..." to break the pattern and regain attention.
- The `visual_prompt` MUST be in English and specify AI/TECH VISUAL STYLE: "Photorealistic 8K, cinematic lighting, 9:16 vertical. AI/Tech aesthetic: Neural network visualizations, glowing data streams, code terminals, holographic UI, fiber optics, server racks, quantum circuits, abstract geometric data flows. Color palette: Deep blues, electric cyan, emerald green, amber gold on dark. Volumetric lighting, depth of field, ray-traced reflections. NO human faces, NO cartoon characters, NO anatomical figures, NO distorted eyes, NO asymmetrical objects. Clean Apple/Google/NVIDIA keynote quality." To maximize viewer retention, each prompt MUST describe a cohesive scene within a consistent environment. Scenes in the same logical segment should share the same master environment with evolving focus. E.g., camera motion ("slow dolly into neural network layers", "gentle pan across data stream particles", "subtle zoom on code terminal"), focus shifts ("attention heatmap on transformer blocks", "token embeddings flowing as light particles", "GPU cluster training curves updating"). NO rapid chaotic changes between consecutive scenes - maintain visual continuity.
- NO people depicted in `visual_prompt`. NO human faces, NO characters, NO anatomical elements of any kind. Environments must be clean tech spaces (labs, server rooms, control centers, abstract data spaces).
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

TAMIL VOICE & STYLE COMPLIANCE CHECK CRITERIA:
- Does the hook and script sound like a friendly, clear, and relatable South Indian Tamil guy (no anime tropes or fantasy phrasing like 'plot twist da' or 'final boss' in the voiceover script)?
- Is the script easily understandable by Tamil speakers globally (clear pronunciation, standard vocabulary, no obscure slang)?
- Are all sentences short and punchy (under 12 words)?
- Does the script strictly follow the 4-part structure: HOOK (0-5s), PROBLEM (5-20s), SOLUTION (20-100s), and ENGAGEMENT QUESTION (100-115s)?
- Does the script avoid generic phrases like "intha video-la"?
- Is the CTA/Question natural, not forced?

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
                    "everyday science anomalies, or any fact going viral on social media in India. "
                    "CRITICAL: The topic must appeal to Tamil-speaking audiences aged 16-35 in India and globally. "
                    "Focus on universal curiosity-gap themes: science wonders, body mysteries, phone/tech hacks, "
                    "money-saving tips, or surprising everyday facts. "
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
                print("🚨 [google_trends] Gemini API rate limited / exhausted during Google Trends query. Disabling Gemini.")
                from config import disable_gemini
                disable_gemini()
                return None
            print(f"⚠️ Could not fetch Google Trends topic: {e}. Proceeding without trending signal.")
            return None
    
    print("⚠️ Google Trends exhausted after retries. Proceeding without trending signal.")
    return None

def pick_and_generate_script(articles=None, extra_instruction="", forced_article=None, topic_type="research", failed_topics=[]):
    """
    Orchestrates the multi-agent pipeline to generate a high-retention Tanglish fact script.
    """
    from config import is_gemini_disabled
    client = get_gemini_client()
    if not client and not is_gemini_disabled():
        print("⚠️ Gemini API Client missing! Cannot run multi-agent script generation.")
        return None
    
    day_name, slot, category = get_slot_info()
    strategy_enhancement = get_category_prompt_enhancement(category, slot)
    
    # Check for session length cap from performance insights
    from ecosystem_logic import get_session_length_cap
    session_length_cap = get_session_length_cap()
    
    local_persona = globals()["SYSTEM_PERSONA"]
    local_optimizer = globals()["RETENTION_OPTIMIZER_TEMPLATE"]
    
    if session_length_cap:
        print(f"📉 [gemini_script] Applying session length cap of {session_length_cap} words.")
        local_persona = local_persona.replace("260-350", f"50-{session_length_cap}")
        local_optimizer = local_optimizer.replace("260-350", f"50-{session_length_cap}")
        word_count_limit_str = f"STRICT LIMIT: Total word count MUST be between 50-{session_length_cap} words."
    else:
        word_count_limit_str = "STRICT LIMIT: Total word count MUST be between 260-350 words."

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
      "visual_prompt": "A detailed image/video prompt in English. Must specify '3D Pixar/Disney cartoon style, clay textures, expressive eyes' style, e.g., 'A young South Indian Tamil guy sitting late at night scrolling on smartphone, phone screen glowing on face, 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting, depth of field, dramatic low-angle tilt'. Avoid generic backgrounds.",
      "stock_search_query": "A simple 2-3 word English search query to find relevant real-world B-roll stock video footage on Pexels (e.g., 'spirit level', 'iphone settings', 'crooked frame', 'measuring tape', 'wall shelf'). Do NOT include stylistic keywords like '3D', 'Pixar', 'cartoon', 'claymation', 'realistic', 'detailed'.",
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
  "comment_bait_question": "A polarizing debate question in Tanglish or Tamil about the topic to spark discussion/arguments in comments (e.g. 'Ethu best-nu neenga neneikiringa?', 'WhatsApp call record panrathu right-a thapa?'). Avoid generic CTAs like 'Comment below'."
}""".replace("{category}", category)

    # ── AI EDUCATION CUSTOM PATH ──
    is_ai_slot = True
    if is_ai_slot:
        print("🤖 [AI Education Path] Initializing 3-stage AI Shorts pipeline...")
        selected_category = random.choice(TOPIC_CATEGORIES)
        
        # Step 1: Select a topic using TOPIC_SELECTOR_PROMPT
        selector_prompt = PIPELINE_PROMPTS["topic_selector"] + f"\nRotate / Focus on Category: {selected_category}\n"
        print("🕵️ [AGENT 0] Topic Selector Agent: Generating AI topic...")
        topic_data_res = call_gemini_api(client, selector_prompt, prefer_fallback=True)
        
        if topic_data_res and "topic" in topic_data_res:
            selected_headline = topic_data_res.get("topic")
            selected_url = "https://github.com/vjaab/YtSimpleTips"
            
            # Step 2: Generate script using SCRIPT_GENERATION_PROMPT
            script_writer_prompt = PIPELINE_PROMPTS["script_writer"].format(
                topic=topic_data_res.get("topic"),
                hook_question=topic_data_res.get("hook_question"),
                core_concept=topic_data_res.get("core_concept"),
                real_world_example=topic_data_res.get("real_world_example"),
                surprising_fact=topic_data_res.get("surprising_fact"),
                target_segment=topic_data_res.get("target_segment", "all")
            )
            print("📝 [AGENT 1] Script Writer Agent: Generating script...")
            script_text = None
            try:
                # Direct generation without JSON constraints
                response = client.models.generate_content(
                    model=GEMINI_FLASH_MODEL,
                    contents=script_writer_prompt
                )
                script_text = response.text.strip()
            except Exception as e:
                print(f"⚠️ Script Writer Agent failed: {e}")
                
            if script_text:
                # Step 3: Generate Title, tags and metadata using TITLE_TAGS_PROMPT
                sentences = [s.strip() for s in script_text.split(".") if s.strip()]
                summary_sentences = " ".join(sentences[:2]) if len(sentences) >= 2 else script_text
                
                metadata_prompt = PIPELINE_PROMPTS["metadata"].format(
                    topic=topic_data_res.get("topic"),
                    core_concept=topic_data_res.get("core_concept"),
                    first_two_sentences_of_script=summary_sentences
                )
                print("🏷️ [AGENT 2] Metadata Agent: Generating Title & Tags...")
                metadata_res = call_gemini_api(client, metadata_prompt, prefer_fallback=True)
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
Given the following AI education script, break it down into a sequence of short narration segments (5-8 words each) and generate a detailed visual storyboard.
You must produce exactly 30-45 storyboard scenes to align with the 260-350 words script length.

SCRIPT:
{script_text}

Return ONLY a JSON object matching the required schema:
{refined_requirements}
"""
                print("🎬 [AGENT 3] Storyboard Agent: Generating storyboard layout...")
                final_script = call_gemini_api(client, storyboard_prompt, model='gemini-2.5-flash')
                
                if final_script and "storyboard" in final_script:
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
                        scene_num = scene.get("scene_number", len(subtitle_chunks) + 1)
                        narration_text = scene.get("narration", "")
                        rebuilt_script_parts.append(narration_text)
                        
                        v_type = scene.get("visual_type", "")
                        info_type = scene.get("infographic_type", "none").lower()
                        if "infographic" in v_type.lower() and info_type in ("none", ""):
                            info_type = "stat"
                        
                        has_info = info_type not in ("none", "")
                        info_data = scene.get("infographic_data", {})
                        
                        vis_prompt = scene.get("visual_prompt", "")
                        stock_query = scene.get("stock_search_query", "").strip()
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
                    
                    print("🎉 [AI Education Path] Script and storyboard generated successfully!")
                    return final_script
                    
        print("⚠️ [AI Education Path] Custom generation failed/incomplete. Falling back to default generation path...")

    # ── AGENT 0: SELECTOR ──
    if not forced_article:
        print("🕵️ [AGENT 0] Selector Agent: Choosing top fact candidate...")
        selector_prompt = SELECTOR_AGENT_TEMPLATE.format(
            persona=SYSTEM_PERSONA,
            selection_instruction=selection_instruction,
            news_context=news_context
        )
        selection = call_gemini_api(client, selector_prompt)
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
    sharpened_data = call_gemini_api(client, sharpener_prompt, prefer_fallback=True)
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if sharpened_data:
        isolated_context += f"\nSharpened Facts: {json.dumps(sharpened_data)}"

    # ── AGENT 1: RESEARCH ──
    print("🕵️ [AGENT 1] Research Agent: Structuring narrative elements...")
    research_prompt = RESEARCH_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        news_context=isolated_context
    )
    research = call_gemini_api(client, research_prompt)
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
    hooks_data = call_gemini_api(client, hook_prompt, prefer_fallback=True)
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
    narrative = call_gemini_api(client, narrative_prompt)
    if GEMINI_RPM_SLEEP > 0: time.sleep(GEMINI_RPM_SLEEP)
    if not narrative:
        print("⚠️ Narrative Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 4: RETENTION OPTIMIZER ──
    print("⚡ [AGENT 4] Pacing Optimizer: Shortening sentences...")
    retention_prompt = RETENTION_OPTIMIZER_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        narrative_json=json.dumps(narrative)
    )
    optimized = call_gemini_api(client, retention_prompt, prefer_fallback=True)
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
    retention_result = call_gemini_api(client, retention_sci_prompt, model=GEMINI_PRO_MODEL)
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
    
    final_script = call_gemini_api(client, humanizer_prompt, model='gemini-2.5-flash')
    
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
            validation_result = call_gemini_api(client, validator_prompt, model='gemini-2.5-flash')
            
            if not validation_result:
                print("⚠️ Validator Agent failed to respond. Proceeding with current storyboard.")
                break
                
            print(f"   📈 Storyboard Quality Audit (Attempt {validation_attempts+1}):")
            print(f"      - Story Continuity Score: {validation_result.get('story_continuity_score', 0)}%")
            print(f"      - Visual Alignment: {validation_result.get('visual_alignment_score', 0)}%")
            print(f"      - Engagement: {validation_result.get('engagement_score', 0)}%")
            print(f"      - Transitions: {validation_result.get('transition_score', 0)}%")
            print(f"      - Subtitle Timing: {validation_result.get('subtitle_timing_score', 0)}%")
            
            # Check if all scores are >= 90%
            scores = [
                validation_result.get('story_continuity_score', 0),
                validation_result.get('visual_alignment_score', 0),
                validation_result.get('engagement_score', 0),
                validation_result.get('transition_score', 0),
                validation_result.get('subtitle_timing_score', 0),
                validation_result.get('comment_bait_score', 0)
            ]
            
            if all(score >= 90 for score in scores) or validation_result.get('passes_validation') is True:
                print("   ⭐ Storyboard passed all quality checks (>90% scores)!")
                final_script["quality_scores"] = {
                    "story_continuity": validation_result.get('story_continuity_score'),
                    "visual_alignment": validation_result.get('visual_alignment_score'),
                    "engagement": validation_result.get('engagement_score'),
                    "transitions": validation_result.get('transition_score'),
                    "subtitle_timing": validation_result.get('subtitle_timing_score'),
                    "comment_bait": validation_result.get('comment_bait_score')
                }
                break
            else:
                feedback = validation_result.get('feedback', 'Improve storyboard flow, transition logic and visual alignment.')
                print(f"   ⚠️ Storyboard failed quality checks. Feedback: {feedback}")
                print("   🔄 Triggering self-correction loop in Humanizer Agent...")
                
                correction_prompt = HUMANIZER_AGENT_TEMPLATE.format(
                    persona=SYSTEM_PERSONA,
                    optimized_script=optimized.get("optimized_script", ""),
                    schema_requirements=refined_requirements
                ) + f"\n\nCRITICAL FEEDBACK FROM AUDITOR (YOU MUST CORRECT THESE ISSUES AND RETRY):\n{feedback}"
                
                corrected_script = call_gemini_api(client, correction_prompt, model='gemini-2.5-flash')
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
            title_variants_res = call_gemini_api(client, title_variants_prompt, prefer_fallback=True)
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
            subtitle_chunks = []
            rebuilt_script_parts = []
            for scene in final_script["storyboard"]:
                scene_num = scene.get("scene_number", len(subtitle_chunks) + 1)
                narration_text = scene.get("narration", "")
                rebuilt_script_parts.append(narration_text)
                
                # Check visual type for infographic
                v_type = scene.get("visual_type", "")
                info_type = scene.get("infographic_type", "none").lower()
                
                # Check for visual type compatibility
                if "infographic" in v_type.lower() and info_type in ("none", ""):
                    info_type = "stat"
                
                has_info = info_type not in ("none", "")
                info_data = scene.get("infographic_data", {})
                
                # Extract stock_search_query from storyboard or fall back to visual_prompt
                vis_prompt = scene.get("visual_prompt", "")
                stock_query = scene.get("stock_search_query", "").strip()
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

    # Filter matching category
    matching = [s for s in scripts if s.get("sub_category") == category]
    if not matching:
        matching = scripts

    # Find scripts that pass full uniqueness check (not just title list)
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
                    
        if is_unique:
            unused.append(s)
    
    if not unused:
        print("🚨 [gemini_script] FATAL: All offline fallback scripts are duplicates or failed. Cannot proceed without repeating content. Failing pipeline.")
        return None

    selected = random.choice(unused)
    if selected:
        print(f"✅ [gemini_script] Offline fallback script selected: '{selected.get('title')}'")
        
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

def call_fallback_model(prompt):
    """
    Attempts to call non-Gemini fallback APIs in sequence:
    Groq (OpenAI Free Model -> Qwen -> Llama) -> OpenAI -> Anthropic (Claude) -> DeepSeek -> OpenRouter.
    Returns the parsed JSON response dict or None.
    """
    import os
    import json
    import requests

    def clean_and_parse_json(content):
        raw = content.strip()
        if "```json" in raw:
            raw = raw[raw.find("```json")+7:raw.rfind("```")]
        elif "```" in raw:
            raw = raw[raw.find("```")+3:raw.rfind("```")]
        return json.loads(raw.strip())

    # 1. Cerebras (Llama 3.3 70B)
    cerebras_key = os.getenv("CEREBRAS_API_KEY")
    if cerebras_key:
        headers = {
            "Authorization": f"Bearer {cerebras_key}",
            "Content-Type": "application/json"
        }
        cerebras_models = ["zai-glm-4.7", "gpt-oss-120b"]
        for model_name in cerebras_models:
            print(f"🔮 Gemini failed. Falling back to Cerebras ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7
                }
                r = requests.post("https://api.cerebras.ai/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    return clean_and_parse_json(content)
                else:
                    print(f"⚠️ Cerebras API ({model_name}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ Cerebras ({model_name}) fallback failed: {e}")

    # 2. Groq (with model preference order: llama-3.3-70b-versatile -> mixtral-8x7b-32768)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        groq_models = ["llama-3.3-70b-versatile", "llama-4-scout", "llama-3.1-8b-instant", "qwen/qwen3-32b", "openai/gpt-oss-120b"]
        for model_name in groq_models:
            print(f"🔮 Gemini failed. Falling back to Groq ({model_name})...")
            try:
                payload = {
                    "model": model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7
                }
                r = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    return clean_and_parse_json(content)
                else:
                    print(f"⚠️ Groq ({model_name}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ Groq ({model_name}) fallback failed: {e}")

    # 2. OpenAI
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
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            r = requests.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                return clean_and_parse_json(content)
            else:
                print(f"⚠️ OpenAI API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ OpenAI fallback failed: {e}")

    # 3. Anthropic (Claude)
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
                return clean_and_parse_json(content)
            else:
                print(f"⚠️ Anthropic API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ Anthropic fallback failed: {e}")

    # 4. DeepSeek
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
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            r = requests.post("https://api.deepseek.com/chat/completions", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                return clean_and_parse_json(content)
            else:
                print(f"⚠️ DeepSeek API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ DeepSeek fallback failed: {e}")

    # 5. OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json"
        }
        openrouter_models = [
            "qwen/qwen-2.5-72b-instruct",
            "meta-llama/llama-3.3-70b-instruct:free",
            "moonshotai/kimi-k2.6",
            "nvidia/nemotron-3-ultra:free",
            "google/gemini-2.5-flash",
            "deepseek/deepseek-chat:free",
            "nvidia/llama-3.1-nemotron-70b-instruct:free"
        ]
        for or_model in openrouter_models:
            print(f"🔮 Falling back to OpenRouter ({or_model})...")
            try:
                payload = {
                    "model": or_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7,
                    "max_tokens": 4096
                }
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers, timeout=30)
                if r.status_code == 200:
                    content = r.json()["choices"][0]["message"]["content"].strip()
                    return clean_and_parse_json(content)
                else:
                    print(f"⚠️ OpenRouter API ({or_model}) failed with code {r.status_code}: {r.text}")
            except Exception as e:
                print(f"⚠️ OpenRouter ({or_model}) fallback failed: {e}")

    return None

def call_gemini_api(client_arg, prompt, model='gemini-2.5-flash', prefer_fallback=False):
    """
    Helper to execute Gemini API call with robust fallback to alternate models and APIs.
    Automatically rotates Gemini API keys. If a model fails on all keys, it is removed 
    from rotation and we immediately proceed to the next fallback without waiting.
    """
    from config import is_gemini_disabled
    if is_gemini_disabled():
        print("🚨 Gemini is currently disabled due to rate limit/depletion. Proceeding directly to fallback models.")
        return call_fallback_model(prompt)

    if prefer_fallback:
        print("💡 Lighter/cheaper task detected. Attempting fallback model first to conserve Gemini quota...")
        fallback_res = call_fallback_model(prompt)
        if fallback_res:
            print("   ✅ Handled successfully by fallback model!")
            return fallback_res
        print("   🔄 Fallback failed or not configured. Routing back to Gemini API.")

    client = client_arg or get_gemini_client()
    if not client:
        client = get_gemini_client()

    attempts = 0
    max_attempts = max(16, len(GEMINI_API_KEYS) * 4)
    keys_rotated_in_a_row = 0

    # Define model list to cycle/fallback through
    models_to_try = [model]
    for m in ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-pro']:
        if m not in models_to_try:
            models_to_try.append(m)
    
    model_idx = 0

    while attempts < max_attempts and models_to_try:
        current_model = models_to_try[model_idx % len(models_to_try)]
        try:
            print(f"🔮 Calling Gemini API with model {current_model}...")
            response = client.models.generate_content(
                model=current_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            raw = response.text.strip()
            # Clean possible markdown wrapping
            if "```json" in raw:
                raw = raw[raw.find("```json")+7:raw.rfind("```")]
            elif "```" in raw:
                raw = raw[raw.find("```")+3:raw.rfind("```")]
            
            return json.loads(raw.strip())
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
            
    print("🚨 All Gemini models depleted or failed. Attempting fallback models...")
    fallback_res = call_fallback_model(prompt)
    if fallback_res:
        return fallback_res

    print("🚨 All fallback models failed or not configured.")
    return None

