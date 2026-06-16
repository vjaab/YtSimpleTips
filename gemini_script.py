from google import genai
from google.genai import types
import json
import os
from datetime import datetime
import time
import random
from config import GEMINI_API_KEY, LOGS_DIR, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS
from topic_tracker import load_tracker, check_story_uniqueness, check_cooldowns
from ecosystem_logic import get_slot_info, get_category_prompt_enhancement

# ── PROMPT TEMPLATES (TAMIL SHORTS AGENTIC LOOP) ──────────────────────────────────

SYSTEM_PERSONA = """Role: You are an expert Tamil Infotainment Content Creator ("Simple Tips by VJ") specialized in viral, high-retention YouTube Shorts for the Tamil audience (1.7k+ subscribers already!).
Your goal is to explain extremely useful, trending tech/smart life hacks, study tricks, phone settings, health tips, and financial hacks in a super engaging, conversational way that helps everyday people improve their lives.
Tone: Highly energetic, emotional, passionate, friendly, helpful, and enthusiastic. You are the knowledgeable friend who shares game-changing hacks with a very expressive and dramatic delivery.
Target Audience: Multi-generational Tamil-speaking audience worldwide (India, Sri Lanka, Singapore, Malaysia) spanning:
1) Parents (cares about screen safety, child learning, budgeting, and home convenience).
2) Middle-aged (cares about smartphone utility, WhatsApp/finance security, spam blocking, and daily efficiency).
3) Young People (cares about AI tools, phone/PC customization, study hacks, fast tricks, and speed).
Language Rules:
1. Voiceover Script (`script`, `hook_script`, `problem_context`, `solution_tech`, `retention_loop`, `outro_cta`): Write in TANGLISH (Tamil words in Tamil script, mixed with English words in English alphabet where natural, e.g. "shortcut", "setting", "battery", "focus", "memory"). This is exactly how young Tamil speakers talk and ensures the TTS handles the pronunciation naturally.
   Example: "உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க! உங்க browser speed-ஐ boost பண்ண ஒரு simple hack..."
2. Subtitles & Captions (`subtitle_chunks`):
   - The `text` field MUST contain the spoken Tanglish segment for that chunk to ensure perfect audio-to-text alignment.
   - The `english_caption` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words in English in uppercase, e.g., "PHONE SETTING", "BOOST SPEED", "5-SECOND RULE", "FOCUS HACK") representing the central concept spoken in that chunk. Do NOT write Tamil text or complete sentences in `english_caption`. These will be displayed as bold, clean English captions on screen to highlight important takeaways.
3. Visual prompts (`nano_visual_prompt`): MUST be written in English. To maximize viewer retention throughout the video, each prompt MUST describe a unique, highly dynamic, and visually shocking scene that changes rapidly. Avoid static or boring descriptions. Focus on high-retention elements:
   - Dynamic motion/camera angles (e.g., "rapid macro zoom in", "high-speed tracking shot", "intense panning", "dramatic low-angle tilt", "camera spinning").
   - Emotional resonance (e.g., depicting individuals with highly expressive, exaggerated emotions: shocked face, amazed look, gasping in surprise, intense focus).
   - Rich metaphors and vibrant colors (e.g., glowing neon connections, holographic interfaces, gold coins popping out of a screen, lock snapping in half).
   - Explicit style: Specify a whiteboard animation style (clean 2D vector line art illustration drawing on a clean off-white whiteboard background, hand drawing sketch animation style, vibrant lime/primary accent colors, no photorealism).
   - Ethnicity & Local Context: Any people depicted must look like they are from Tamil Nadu, India (South Indian Tamil ethnicity), and any locations/backgrounds must resemble typical settings in Tamil Nadu, India where applicable.
Constraint Checklist:
- No Fluff: Do not say "வணக்கம் நண்பர்களே", "In this video", "Today we talk about". Start immediately with a highly relatable, emotional problem hook for the target demographics!
- VOCAL DYNAMICS: Use heavy punctuation (commas, ellipses '...', exclamation marks, italics, ALL CAPS) to guide pronunciation emphasis. Add intense emotional cues where natural to make the delivery highly dramatic and energetic.
- SEAMLESS LOOP: Ensure the script's final sentence flows perfectly back into the hook's opening sentence to create an infinite, high-retention loop.
- CTAs: At the end of every script, ask a provocative question in Tanglish to drive comments. Do NOT tell or ask the viewer to subscribe, follow, or share in the spoken voiceover script. End the script strictly on the question.
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
Hooks MUST address a highly relatable everyday frustration or surprise for parents, middle-aged people, or young people, and promise an immediate, easy solution (especially tech-based settings/apps/shortcuts), creating extreme curiosity in Tamil/Tanglish.
No greetings. No generic statements. Start with the core problem/result first!

SCORING CRITERIA:
- curiosity_score: How much does this make someone NEED to know the answer? (1-10)
- emotional_trigger_score: How strongly does this hit a pain point or desire? (1-10)
- swipe_stop_power: Would this make someone physically STOP scrolling on their phone? Hooks that start with numbers, shocking claims, direct address ("உங்க phone-ல..."), or challenge assumptions score highest. (1-10)

RESEARCH:
{research_json}

Return ONLY a JSON object:
{{
  "hooks": [
    {{
      "text": "Tanglish hook text (e.g. 'உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க!')",
      "curiosity_score": 1-10,
      "emotional_trigger_score": 1-10,
      "swipe_stop_power": 1-10,
      "reason": "Why it works"
    }}
  ]
}}"""

NARRATIVE_AGENT_TEMPLATE = """{persona}

NARRATIVE AGENT TASK:
Using the selected hook and research, create a step-by-step tutorial or tip flow that is highly appealing to our target demographics (parents, middle-aged, and youth).

VIRAL RETENTION TECHNIQUES (MANDATORY):
- OPEN LOOP: In the first 5 seconds, plant an unresolved curiosity (e.g., "ஆனா இதுல ஒரு catch இருக்கு...", "ஆனா most people இந்த mistake பண்றாங்க...") that only gets resolved at the 25-30 second mark. This is the #1 retention driver.
- PATTERN INTERRUPTS: Every 8-10 seconds, inject a micro-hook phrase to prevent drop-off. Use phrases like: "ஆனா wait பண்ணுங்க...", "இது தான் twist...", "இப்போ கவனமா கேளுங்க...", "ஆனா இது மட்டும் இல்ல..."
- RAPID PACING: Every sentence must be under 10 words. No long explanations. Punch, punch, punch.

Include:
1. Hook (The selected problem-solving hook - must instantly capture attention + plant open loop)
2. Context (2-6s) - Define the common daily problem. Approx 12 words in Tanglish.
3. Escalation (6-28s) - Step-by-step instructions with pattern interrupts. Keep sentences VERY short. Approx 55 words.
4. Retention Loop (28-33s) - Seamless bridge back to the exact opening words of the hook. Approx 10 words.
5. Outro CTA (33-38s) - A provocative question in Tanglish to drive comments. Approx 10 words.

RESEARCH:
{research_json}

SELECTED HOOK:
{selected_hook}

{selection_instruction}

Return ONLY a JSON object representing the narrative draft (not the final schema yet):
{{
  "hook": "...",
  "open_loop_tease": "The unresolved curiosity planted in hook/context",
  "context": "...",
  "escalation": "...",
  "pattern_interrupts_used": ["phrase1", "phrase2"],
  "retention_loop": "...",
  "outro_cta": "..."
}}"""

RETENTION_OPTIMIZER_TEMPLATE = """{persona}

RETENTION OPTIMIZER TASK:
Rewrite the narrative draft to maximize retention, remove ALL fluff, and increase curiosity density.
The script must feel like a rapid-fire conversation, NOT a lecture.

MANDATORY RULES:
1. TOTAL WORD COUNT: Strictly 90-110 words. NOT more. Count carefully.
2. Every sentence MUST be under 10 words.
3. Ensure the script directly resonates with daily scenarios for parents, middle-aged, or young people.
4. PATTERN INTERRUPTS: There must be at least 2 pattern interrupt phrases (e.g., "ஆனா wait பண்ணுங்க...", "இது தான் twist...", "இப்போ கவனமா கேளுங்க...") at approximately the 8-second and 18-second marks.
5. Add an ellipsis '...' after key settings or complex terms to force the TTS to pause naturally.
6. Make sure the last sentence merges seamlessly back into the very first sentence to make a perfect 100% looping short.
7. The OPEN LOOP planted in the hook must be resolved around the 25-30 second mark.

NARRATIVE DRAFT:
{narrative_json}

Return ONLY a JSON object:
{{
  "optimized_script": "The full rewritten text combining all parts into a fast-paced Tanglish script. STRICTLY 90-110 words.",
  "word_count": 0,
  "pattern_interrupt_timestamps": ["~8s", "~18s"]
}}"""

SELECTOR_AGENT_TEMPLATE = """{persona}

SELECTOR AGENT TASK:
Analyze the following tips/hacks and pick the SINGLE most mind-blowing, high-utility, and high-retention tip for a 30-40 second video.

SELECTION CRITERIA:
1. Strongly prioritize tech-infused hacks, digital/phone/PC/smart-device settings, or app tricks that are highly useful.
2. The tip must have high viral potential and clear everyday benefit for parents (safety/home/money), middle-aged (efficiency/security/spam blocking), or young people (productivity/shortcuts/customization).
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
This is the final step. Fix any robotic phrasing. Ensure the speech is highly conversational Tanglish (natural, friendly, high-energy).
Format the output EXACTLY matching the required schema below.

OPTIMIZED SCRIPT:
{optimized_script}

SCHEMA REQUIREMENTS:
{schema_requirements}

CRITICAL STORYBOARD & SCENE RULES:
In the `storyboard` array:
- Each scene/chunk MUST be SHORT: 3-5 words maximum in the `narration` field to ensure punchy karaoke-style captions on screen.
- You MUST produce at least 15-25 storyboard scenes for the full script to ensure perfect word-by-word alignment.
- The `narration` field MUST contain the exact spoken Tanglish phrase for alignment (3-5 words only).
- The `on_screen_text` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words maximum in English, in uppercase, e.g., "BRAIN CELLS", "86 BILLION", "PHONE SETTING", "STRENGTH") representing the central concept.
- The `scene_objective` must briefly describe what technical/lifestyle concept is explained.
- Choose `visual_type` dynamically based on the content (e.g. 'Google Video Generation', 'Animated Infographics', 'Whiteboard Animation', 'Motion Graphics').
- The `visual_prompt` MUST be in English. To maximize viewer retention throughout the video, each prompt MUST describe a unique, highly dynamic, and visually shocking scene that changes rapidly. Avoid static or boring descriptions. E.g., camera motion ("extreme macro zoom on screen", "rapid low-angle pan"), rich emotional expressions ("shocked expression with eyes wide open", "amazed gasping"), or visual metaphors ("glowing data streams flowing into phone", "lock breaking in half with digital sparks").
- Any people depicted in `visual_prompt` must look like they are from Tamil Nadu, India (South Indian Tamil ethnicity), and locations must resemble settings in Tamil Nadu, India.
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
1. story_continuity_score: Does scene N logically connect to scene N+1? Is there a clear cause-and-effect chain and a transformation journey?
2. visual_alignment_score: Does the visual prompt directly represent the spoken narration? (No generic tech backgrounds, no unrelated stock footage).
3. engagement_score: Are there visual changes every 2-3 seconds? Are hook visuals optimized? Are there curiosity triggers and pattern interrupts?
4. transition_score: Do transitions feel connected (match cuts, zoom transitions, morphs, object/story continuity) instead of hard-cuts?
5. subtitle_timing_score: Are narration segments short and punchy (3-5 words) for fast-paced subtitles?

STORYBOARD TO EVALUATE:
{storyboard_json}

Return ONLY a JSON object:
{{
  "story_continuity_score": 0-100,
  "visual_alignment_score": 0-100,
  "engagement_score": 0-100,
  "transition_score": 0-100,
  "subtitle_timing_score": 0-100,
  "passes_validation": true|false,
  "feedback": "Detailed feedback on what is wrong and which scenes need improvement/regeneration."
}}"""

def pick_and_generate_script(articles=None, extra_instruction="", forced_article=None, topic_type="research", failed_topics=[]):
    """
    Orchestrates the multi-agent pipeline to generate a high-retention Tanglish fact script.
    """
    client = get_gemini_client()
    if not client:
        print("⚠️ Gemini API Client missing! Cannot run multi-agent script generation.")
        return None
    
    day_name, slot, category = get_slot_info()
    strategy_enhancement = get_category_prompt_enhancement(category, slot)
    
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

    news_context = avoid_instruction
    
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
        "STRICT LIMIT: Total word count MUST be between 90-110 words to guarantee fast-paced, high-retention delivery inside 40 seconds."
    )

    prompt_requirements = """Return ONLY this exact JSON (no markdown):
{
  "title": "Main punchy YouTube title (max 40 chars, include emoji)",
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
      "visual_prompt": "A detailed image/video prompt in English (e.g., 'A young Indian professional sitting late at night scrolling endlessly on smartphone, dark room illuminated by phone screen, realistic cinematic lighting, shallow depth of field, emotional expression, slow camera push-in, ultra realistic, vertical video format'). Avoid generic backgrounds.",
      "camera_motion": "Slow zoom|Dolly-in|Orbit|Pan|Tracking shot|None",
      "transition": "Match cut|Zoom transition|Morph|Swipe|Object continuity|Story continuity",
      "on_screen_text": "1-3 IMPORTANT key English words representing the central concept of this scene in uppercase (e.g., '86 BILLION NEURONS')",
      "emotion": "Curiosity|Surprise|Fear|Excitement|Focus|Confusion",
      "duration": 3
    }
  ],
  "title_options": ["Curiosity Gap Title 1", "Curiosity Gap Title 2"],
  "description": "Full SEO friendly video description including Tamil tags #தெரியுமா #FactsInTamil #VJVideos",
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
  "comment_hook": "Provocative question in Tanglish to drive comments."
}""".replace("{category}", category)

    # ── AGENT 0: SELECTOR ──
    if not forced_article:
        print("🕵️ [AGENT 0] Selector Agent: Choosing top fact candidate...")
        selector_prompt = SELECTOR_AGENT_TEMPLATE.format(
            persona=SYSTEM_PERSONA,
            selection_instruction=selection_instruction,
            news_context=news_context
        )
        selection = call_gemini_api(client, selector_prompt)
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
    sharpened_data = call_gemini_api(client, sharpener_prompt)
    if sharpened_data:
        isolated_context += f"\nSharpened Facts: {json.dumps(sharpened_data)}"

    # ── AGENT 1: RESEARCH ──
    print("🕵️ [AGENT 1] Research Agent: Structuring narrative elements...")
    research_prompt = RESEARCH_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        news_context=isolated_context
    )
    research = call_gemini_api(client, research_prompt)
    if not research:
        print("⚠️ Research Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 2: HOOK ──
    print("🪝 [AGENT 2] Hook Agent: Generating Tanglish hooks...")
    hook_prompt = HOOK_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        research_json=json.dumps(research)
    )
    hooks_data = call_gemini_api(client, hook_prompt)
    if not hooks_data or "hooks" not in hooks_data:
        print("⚠️ Hook Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)
    
    # Pick highest curiosity score hook
    best_hook = max(hooks_data["hooks"], key=lambda h: h.get("curiosity_score", 0) + h.get("emotional_trigger_score", 0) + h.get("swipe_stop_power", 0))
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
    if not narrative:
        print("⚠️ Narrative Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 4: RETENTION OPTIMIZER ──
    print("⚡ [AGENT 4] Pacing Optimizer: Shortening sentences...")
    retention_prompt = RETENTION_OPTIMIZER_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        narrative_json=json.dumps(narrative)
    )
    optimized = call_gemini_api(client, retention_prompt)
    if not optimized:
        print("⚠️ Pacing Optimizer failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category, failed_topics)

    # ── AGENT 5: HUMANIZER & SCHEMATIZER ──
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
                validation_result.get('subtitle_timing_score', 0)
            ]
            
            if all(score >= 90 for score in scores) or validation_result.get('passes_validation') is True:
                print("   ⭐ Storyboard passed all quality checks (>90% scores)!")
                final_script["quality_scores"] = {
                    "story_continuity": validation_result.get('story_continuity_score'),
                    "visual_alignment": validation_result.get('visual_alignment_score'),
                    "engagement": validation_result.get('engagement_score'),
                    "transitions": validation_result.get('transition_score'),
                    "subtitle_timing": validation_result.get('subtitle_timing_score')
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
                has_info = False
                info_type = "none"
                if "infographic" in v_type.lower():
                    has_info = True
                    info_type = "stat_callout" # default type
                
                # Extract stock_search_query from visual_prompt or narration
                vis_prompt = scene.get("visual_prompt", "")
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
                    "infographic_data": {},
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
        print("🔮 Gemini failed. Falling back to Cerebras (llama-3.3-70b)...")
        try:
            headers = {
                "Authorization": f"Bearer {cerebras_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "llama-3.3-70b", # Llama 3.3 70B is available on Cerebras
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0.7
            }
            r = requests.post("https://api.cerebras.ai/v1/chat/completions", json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                content = r.json()["choices"][0]["message"]["content"].strip()
                return clean_and_parse_json(content)
            else:
                print(f"⚠️ Cerebras API failed with code {r.status_code}: {r.text}")
        except Exception as e:
            print(f"⚠️ Cerebras fallback failed: {e}")

    # 2. Groq (with model preference order: llama-3.3-70b-versatile -> mixtral-8x7b-32768)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
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
        openrouter_models = ["meta-llama/llama-3.3-70b-instruct:free", "google/gemini-2.5-flash:free", "qwen/qwen-2.5-72b-instruct:free"]
        for or_model in openrouter_models:
            print(f"🔮 Falling back to OpenRouter ({or_model})...")
            try:
                payload = {
                    "model": or_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.7
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

def call_gemini_api(client_arg, prompt, model='gemini-2.5-flash'):
    """
    Helper to execute Gemini API call with robust fallback to alternate models and APIs.
    Automatically rotates Gemini API keys. If a model fails on all keys, it is removed 
    from rotation and we immediately proceed to the next fallback without waiting.
    """
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

