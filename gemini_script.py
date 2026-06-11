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
   - Explicit style: Specify a photorealistic, 8K, highly detailed cinematic look with dramatic lighting, volumetric glow, and high color contrast.
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

RESEARCH:
{research_json}

Return ONLY a JSON object:
{{
  "hooks": [
    {{
      "text": "Tanglish hook text (e.g. 'உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க!')",
      "curiosity_score": 1-10,
      "emotional_trigger_score": 1-10,
      "reason": "Why it works"
    }}
  ]
}}"""

NARRATIVE_AGENT_TEMPLATE = """{persona}

NARRATIVE AGENT TASK:
Using the selected hook and research, create a step-by-step tutorial or tip flow that is highly appealing to our target demographics (parents, middle-aged, and youth).
Include:
1. Hook (The selected problem-solving hook - must instantly capture attention)
2. Context (3-10s) - Define the common daily problem or mistake parents, middle-aged, or youth face. Approx 20 words in Tanglish.
3. Escalation (10-40s) - Step-by-step simple instructions on how to apply the tip/setting/hack. Keep sentences very short, direct, and actionable. Approx 80 words.
4. Retention Loop (40-48s) - End with a loop trigger or a seamless bridge/phrase that connects perfectly back to the exact opening words of the hook for a continuous loop. Approx 15 words.
5. Outro CTA (48-55s) - A provocative question in Tanglish about this tip to drive high comment engagement. Approx 15 words.

RESEARCH:
{research_json}

SELECTED HOOK:
{selected_hook}

{selection_instruction}

Return ONLY a JSON object representing the narrative draft (not the final schema yet):
{{
  "hook": "...",
  "context": "...",
  "escalation": "...",
  "retention_loop": "...",
  "outro_cta": "..."
}}"""

RETENTION_OPTIMIZER_TEMPLATE = """{persona}

RETENTION OPTIMIZER TASK:
Rewrite the narrative draft to maximize retention, remove fluff, shorten sentences, and increase curiosity density.
Ensure the script directly resonates with daily scenarios for parents, middle-aged, or young people.
Fast sentence pacing is mandatory. Use highly visual everyday analogies.
Add an ellipsis '...' after key settings or complex terms to force the TTS to pause naturally.
Make sure the last sentence merges seamlessly back into the very first sentence to make a perfect 100% looping short.

NARRATIVE DRAFT:
{narrative_json}

Return ONLY a JSON object:
{{
  "optimized_script": "The full rewritten text combining all parts into a fast-paced Tanglish script."
}}"""

SELECTOR_AGENT_TEMPLATE = """{persona}

SELECTOR AGENT TASK:
Analyze the following tips/hacks and pick the SINGLE most mind-blowing, high-utility, and high-retention tip for a 50-second video.

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

CRITICAL CAPTION RULE:
In the `subtitle_chunks` array:
- The `text` field MUST contain the exact spoken Tanglish phrase for alignment.
- The `english_caption` field MUST contain ONLY the most important key phrase or keyword in English (1 to 3 words maximum in English, in uppercase, e.g., "BRAIN CELLS", "86 BILLION", "UNIFIED FORCE", "STRENGTH") representing the central concept.
The timestamps `start` and `end` are placeholders (set `start` to 0.0 and `end` to 0.0 — they will be aligned dynamically by stable-whisper).
`nano_visual_prompt` MUST be in English. To maximize viewer retention throughout the video, each prompt MUST describe a unique, highly dynamic, and visually shocking scene that changes rapidly. Avoid static or boring descriptions. E.g., camera motion ("extreme macro zoom on screen", "rapid low-angle pan"), rich emotional expressions ("shocked expression with eyes wide open", "amazed gasping"), or visual metaphors ("glowing data streams flowing into phone", "lock breaking in half with digital sparks"). Specify a photorealistic, 8K, highly detailed cinematic shot with dramatic volumetric lighting, vibrant colors, and high contrast. CRITICAL: Any people depicted must look like they are from Tamil Nadu, India (South Indian Tamil ethnicity), and locations must resemble settings in Tamil Nadu, India.

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
            return get_offline_fallback_script(category)

    selection_instruction = (
        f"Analyze the facts and select the SINGLE most mind-blowing fact to convert into a 45-55s Tanglish YouTube Short.\n"
        f"CATEGORY: {category}\n"
        f"{strategy_enhancement}\n"
        "STRICT LIMIT: Total word count MUST be between 110-130 words to guarantee natural, high-retention pacing inside 55 seconds."
    )

    prompt_requirements = """Return ONLY this exact JSON (no markdown):
{
  "title_options": ["Curiosity Gap Title 1", "Curiosity Gap Title 2"],
  "description": "Full SEO friendly video description including Tamil tags #தெரியுமா #FactsInTamil #VJVideos",
  "use_case_evidence_url": "Direct source url of the fact to take a screenshot of.",
  "title": "Main punchy YouTube title (max 50 chars)",
  "hook_script": "The Hook (<1.5s): A shocking Result-First statement in Tanglish. Approx 6 words.",
  "problem_context": "The Context (3-10s): Introduce the mystery or setup in Tanglish. Approx 20 words.",
  "solution_tech": "The Fact Escalation (10-40s): Explain the mind-blowing science or detail in Tanglish. Under 80 words.",
  "retention_loop": "The Retention Loop (40-48s): Seamless bridge/cliffhanger back to start. Approx 15 words.",
  "outro_cta": "CTA: Provocative question to drive comments in Tanglish. Approx 15 words. STRICTLY DO NOT mention subscribe, follow or share.",
  "script": "The FULL unified voiceover script in Tanglish combining all parts. Approx 110-130 words. STRICT MAXIMUM 130 words.",
  "hook_text": "The first 5-8 words of the script.",
  "relevant_links": ["Source url"],
  "phonetic_pronunciation_map": {"NVIDIA": "In-vid-yah"},
  "hook": "Matches the first sentence of the script",
  "summary": "One line English summary",
  "sub_category": "{category}",
  "breaking_news_level": 8,
  "retention_cues": [{"timestamp": 2.0, "effect": "zoom_in", "reason": "hook_impact"}],
  "subtitle_chunks": [{
      "chunk_id": 1,
      "text": "The exact Tanglish words spoken in this chunk (e.g., 'namma brain-la almost')",
      "english_caption": "1-3 IMPORTANT English words representing the key concept of this chunk in uppercase (e.g., '86 BILLION NEURONS')",
      "start": 0.0, "end": 0.0,
      "has_infographic": false, "infographic_type": "none",
      "infographic_data": {},
      "nano_visual_prompt": "Cinematic photorealistic shot description in English for Imagen. E.g., 'Cinematic photorealistic shot of a glowing human brain...'. 9:16 aspect ratio."
  }],
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
            return get_offline_fallback_script(category)
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
                return get_offline_fallback_script(category)
        
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
        return get_offline_fallback_script(category)

    # ── AGENT 2: HOOK ──
    print("🪝 [AGENT 2] Hook Agent: Generating Tanglish hooks...")
    hook_prompt = HOOK_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        research_json=json.dumps(research)
    )
    hooks_data = call_gemini_api(client, hook_prompt)
    if not hooks_data or "hooks" not in hooks_data:
        print("⚠️ Hook Agent failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category)
    
    # Pick highest curiosity score hook
    best_hook = max(hooks_data["hooks"], key=lambda h: h.get("curiosity_score", 0) + h.get("emotional_trigger_score", 0))
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
        return get_offline_fallback_script(category)

    # ── AGENT 4: RETENTION OPTIMIZER ──
    print("⚡ [AGENT 4] Pacing Optimizer: Shortening sentences...")
    retention_prompt = RETENTION_OPTIMIZER_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        narrative_json=json.dumps(narrative)
    )
    optimized = call_gemini_api(client, retention_prompt)
    if not optimized:
        print("⚠️ Pacing Optimizer failed. Attempting offline fallback script...")
        return get_offline_fallback_script(category)

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
    
    if not final_script:
        print("⚠️ [gemini_script] Agent pipeline failed. Attempting offline fallback script...")
        final_script = get_offline_fallback_script(category)
        
    if final_script:
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

def get_offline_fallback_script(category):
    """
    Loads a pre-packaged script from fallback_scripts.json matching the category.
    Avoids already used titles if possible.
    """
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

    # Load tracker to check used titles
    tracker = load_tracker()
    used_titles = tracker.get("used_titles", [])

    # Filter matching category
    matching = [s for s in scripts if s.get("sub_category") == category]
    if not matching:
        # Try finding using loose matching or just use all scripts
        matching = scripts

    # Find unused scripts
    unused = [s for s in matching if s.get("title") not in used_titles]
    if not unused:
        # If all are used, reuse any matching
        unused = matching

    selected = random.choice(unused) if unused else None
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

def call_gemini_api(client_arg, prompt, model='gemini-2.5-flash'):
    """
    Helper to execute Gemini API call with robust exponential backoff retries for 503/429 errors.
    Automatically rotates Gemini API key and retries immediately if multiple keys exist.
    Also falls back to alternate models on rate limits/overloads.
    """
    client = client_arg or get_gemini_client()
    if not client:
        client = get_gemini_client()

    attempts = 0
    max_attempts = max(8, len(GEMINI_API_KEYS) * 3)
    keys_rotated_in_a_row = 0

    # Define model list to cycle/fallback through
    models_to_try = [model]
    for m in ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-pro']:
        if m not in models_to_try:
            models_to_try.append(m)
    
    model_idx = 0

    while attempts < max_attempts:
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
                
                # If we tried all keys or only have 1 key, rotate the model
                keys_rotated_in_a_row = 0
                model_idx += 1
                next_model = models_to_try[model_idx % len(models_to_try)]
                print(f"🔄 Rotated through keys. Switching model to fallback: {next_model}. Retrying immediately...")
                
                # Exponential backoff with jitter if we have rotated through all models too
                if model_idx % len(models_to_try) == 0:
                    sleep_time = int(10 * (1.5 ** (attempts // len(models_to_try))) + random.uniform(1, 4))
                    print(f"   Waiting {sleep_time} seconds (attempt {attempts+1}/{max_attempts}) before retrying...")
                    time.sleep(sleep_time)
            else:
                sleep_time = 5 + attempts * 5
                print(f"⚠️ Agent call failed: {e}. Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            attempts += 1
            
    print("🚨 Agent failed all attempts.")
    return None

