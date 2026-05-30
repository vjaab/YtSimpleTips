from google import genai
from google.genai import types
import json
import os
from datetime import datetime
import time
import random
from config import GEMINI_API_KEY, LOGS_DIR
from topic_tracker import load_tracker, check_story_uniqueness, check_cooldowns
from ecosystem_logic import get_slot_info, get_category_prompt_enhancement

# ── PROMPT TEMPLATES (TAMIL SHORTS AGENTIC LOOP) ──────────────────────────────────

SYSTEM_PERSONA = """Role: You are an expert Tamil Educational & Tech Content Creator ("Simple Tips by VJ") specialized in viral, high-retention YouTube Shorts for the Tamil audience (1.7k+ subscribers already!).
Your goal is to teach and educate everyday viewers on how to use new, popular, and trending apps and websites in a super clear, step-by-step, engaging, conversational way that hooks them instantly.
Tone: High-energy, helpful, friendly, and practical. You are the knowledgeable friend who guides the viewer step-by-step through a process.
Target Audience: Tamil-speaking audience worldwide (India, Sri Lanka, Singapore, Malaysia).
Language Rules:
1. Voiceover Script (`script`, `hook_script`, `problem_context`, `solution_tech`, `retention_loop`, `outro_cta`): Write in TANGLISH (Tamil words in Tamil script, mixed with English words in English alphabet where natural, e.g. "login page", "OTP", "search bar", "add to cart", "checkout", "export button"). This is exactly how young Tamil speakers talk and ensures the TTS handles the pronunciation naturally.
   Example: "உங்களுக்கு Blinkit-ல 10 minutes-ல grocery order பண்ணணுமா? அப்போ இந்த video-வை பாருங்க! முதல்ல app open பண்ணி..."
2. Subtitles (`subtitle_chunks` text): Write in clean TAMIL script for Tamil words and plain English for English terms so the captions look highly premium and professional. Keep each subtitle chunk very short (1 to 3 words maximum!).
3. Visual prompts (`nano_visual_prompt`): MUST be written in English so Imagen 4.0 understands it perfectly. Specify highly detailed user interface (UI) mockups, mobile screens, or desktop app screens showing the specific steps. Use terms like: "A premium mobile app UI mockup of [App Name] showing the [Specific Step e.g. login screen with phone input / search screen / payment checkout], modern clean interface design, realistic high-quality vertical 9:16 aspect ratio screenshot representation." No generic photos or faces unless it relates to using the app. This is critical to visually guide the viewer step-by-step!
Constraint Checklist:
- No Fluff: Do not say "வணக்கம் நண்பர்களே", "In this video", "Today we talk about". Start immediately with the hook!
- VOCAL DYNAMICS: Use heavy punctuation (commas, ellipses '...', exclamation marks, italics, ALL CAPS) to guide pronunciation emphasis.
- CTAs: At the end of every script, ask a practical question in Tanglish to drive comments (e.g. "Blinkit service உங்க ஊர்ல இருக்கா? கமெண்ட் பண்ணுங்க!"). Do NOT tell or ask the viewer to subscribe, follow, or share in the spoken voiceover script. End the script strictly on the question.
"""

RESEARCH_AGENT_TEMPLATE = """{persona}

RESEARCH AGENT TASK:
Review the following app/website tutorial details.
Identify the exact step-by-step workflow:
1. Registration / Login / Entry step.
2. Core Navigation / Initial setup step.
3. Execution / Core Action step.
4. Completion / Payment / Save step.
Extract the key tips, steps, and highly useful features that the viewer must know.
Do NOT write a script. Just extract the core steps.

APP/WEBSITE CONTEXT:
{news_context}

Return ONLY a JSON object:
{{
  "facts": ["Step 1: Open app and enter phone number for OTP", "Step 2: Search for items and add to cart", "Step 3: Apply coupons or discounts", "Step 4: Choose payment method and order"],
  "mind_blow_angle": "The single most useful tip, trick or shortcut in this app/website",
  "implications": ["Why this app is useful or how much time/money it saves"],
  "core_narrative": "A one paragraph step-by-step summary of the tutorial"
}}"""

HOOK_AGENT_TEMPLATE = """{persona}

HOOK AGENT TASK:
Based on the following research, generate 10 potential YouTube Shorts hooks (<1.5s).
Hooks MUST create extreme surprise, curiosity, or address a key pain point regarding this app/website in Tamil/Tanglish.
No greetings. No generic statements.

RESEARCH:
{research_json}

Return ONLY a JSON object:
{{
  "hooks": [
    {{
      "text": "Tanglish hook text (e.g. 'Blinkit app-ல 10 minutes-ல groceries order பண்ணுறது எப்படின்னு தெரியுமா?!')",
      "curiosity_score": 1-10,
      "emotional_trigger_score": 1-10,
      "reason": "Why it works"
    }}
  ]
}}"""

NARRATIVE_AGENT_TEMPLATE = """{persona}

NARRATIVE AGENT TASK:
Using the selected hook and research, create a storytelling flow and step-by-step guide.
Include:
1. Hook (The selected hook)
2. Context (3-10s) - Setting up the app/website and signing in / logging in. Approx 20 words in Tanglish.
3. Escalation (10-40s) - The step-by-step tutorial covering search, configuration, and final ordering/exporting. Ensure the guide is complete from login to final steps. Approx 80 words.
4. Retention Loop (40-48s) - A pro-tip or shortcut, and a bridge that leads back to the start of the video. Approx 15 words.
5. Outro CTA (48-55s) - Provincial Tamil comment-driving question related to the app. Approx 15 words.

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
Rewrite the narrative draft to remove fluff, shorten sentences, add pacing breaks, and ensure a highly clear, fast-paced step-by-step tutorial.
Fast sentence pacing. Every sentence must create tension-release.
Add an ellipsis '...' after complex app terms or options to force the TTS to pause.

NARRATIVE DRAFT:
{narrative_json}

Return ONLY a JSON object:
{{
  "optimized_script": "The full rewritten text combining all parts into a fast-paced Tanglish script."
}}"""

SELECTOR_AGENT_TEMPLATE = """{persona}

SELECTOR AGENT TASK:
Analyze the following app/website tutorial topics and pick the SINGLE most useful, trending, and high-retention tutorial for a 50-second video.

CRITICAL AVOIDANCE RULE:
You MUST NOT select any topic that is semantically similar to the 'RECENTLY COVERED STORIES' listed in the context.

{selection_instruction}

NEWS CONTEXT:
{news_context}

Return ONLY a JSON object:
{{
  "selected_headline": "The exact title of the tutorial chosen",
  "selected_url": "The exact source URL of the chosen app/website",
  "reason": "Briefly why this was picked (viral potential and user utility)"
}}"""

HUMANIZER_AGENT_TEMPLATE = """{persona}

HUMANIZER AGENT TASK:
This is the final step. Fix any robotic phrasing. Ensure the speech is highly conversational Tanglish (natural, friendly, high-energy).
Format the output EXACTLY matching the required schema below.

OPTIMIZED SCRIPT:
{optimized_script}

SCHEMA REQUIREMENTS:
{schema_requirements}

CRITICAL SUBTITLE RULE:
The `subtitle_chunks` array MUST break the script down into extremely small chunks of EXACTLY 1 to 3 words maximum.
The `text` field MUST be written in clean Tamil Unicode characters (where appropriate) mixed with basic English words.
The timestamps `start` and `end` are placeholders (set `start` to 0.0 and `end` to 0.0 — they will be aligned dynamically by stable-whisper).
`nano_visual_prompt` MUST be in English and specify a highly detailed mobile app or website UI mockup/screenshot representation for Imagen, illustrating the exact step of the tutorial being spoken.
Example prompts:
- "A premium mobile app UI mockup of Blinkit login screen, showing phone number input and 'Get OTP' button, vertical 9:16 aspect ratio screenshot representation, modern clean layout, no human faces."
- "A premium mobile app UI mockup of CapCut editing timeline, showing a video clip being split and trimmed, vertical 9:16 aspect ratio screenshot representation, clean dark mode editor."
Ensure that the prompts visually show the step-by-step progression of the tutorial from login to final steps.

Return ONLY the final JSON object matching the schema. No markdown wrapping. No explanations."""

FACT_EXTRACTOR_TEMPLATE = """{persona}

TASK: Extract ONLY the step-by-step instructions, essential settings, and core actions for the specific tutorial requested below.
Focus on providing the 'isolated truth' for this one app/website tutorial.

TARGET STORY: {target_headline}

CONTEXT:
{context}

Return ONLY a JSON object:
{{
  "facts": ["Step 1 Detail", "Step 2 Detail"],
  "mind_blow_angle": "The core helpful tip or hack",
  "implications": ["Why this app is useful"],
  "core_narrative": "A one paragraph summary focusing ONLY on this tutorial."
}}"""

def pick_and_generate_script(articles=None, extra_instruction="", forced_article=None, topic_type="research", failed_topics=[]):
    """
    Orchestrates the multi-agent pipeline to generate a high-retention Tanglish fact script.
    """
    if not GEMINI_API_KEY:
        print("⚠️ Gemini API Key missing! Cannot run multi-agent script generation.")
        return None
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
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
        if articles:
            for idx, art in enumerate(articles[:10]):
                title = art.get('title', '')
                desc = art.get('description', '')
                url = art.get('source_url', '')
                news_context += f"\n[{idx+1}] Title: {title}\nDescription: {desc}\nURL: {url}\n"
        else:
            print("⚠️ No input facts provided. Fetching fresh facts for selection...")
            from fetch_topics import fetch_facts_for_category
            fresh_facts = fetch_facts_for_category(category)
            for idx, art in enumerate(fresh_facts[:10]):
                title = art.get('title', '')
                desc = art.get('description', '')
                url = art.get('source_url', '')
                news_context += f"\n[{idx+1}] Title: {title}\nDescription: {desc}\nURL: {url}\n"

    selection_instruction = (
        f"Analyze the facts and select the SINGLE most mind-blowing fact to convert into a 45-55s Tanglish YouTube Short.\n"
        f"CATEGORY: {category}\n"
        f"{strategy_enhancement}\n"
        "STRICT LIMIT: Total word count MUST be between 110-130 words to guarantee natural, high-retention pacing inside 55 seconds."
    )

    prompt_requirements = f"""Return ONLY this exact JSON (no markdown):
{{
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
  "phonetic_pronunciation_map": {{"NVIDIA": "In-vid-yah"}},
  "hook": "Matches the first sentence of the script",
  "summary": "One line English summary",
  "sub_category": "{category}",
  "breaking_news_level": 8,
  "retention_cues": [{{"timestamp": 2.0, "effect": "zoom_in", "reason": "hook_impact"}}],
  "subtitle_chunks": [{{
      "chunk_id": 1, "text": "1-3 Tamil words", "start": 0.0, "end": 0.0,
      "has_infographic": false, "infographic_type": "none",
      "infographic_data": {{}},
      "nano_visual_prompt": "Cinematic vertical visual description in English for Imagen. 9:16 aspect ratio."
  }}],
  "original_news_headline": "Fact Title",
  "original_news_url": "Direct source url",
  "keywords": ["Tamil Facts", "Did You Know"],
  "hashtags": ["#தெரியுமா", "#TamilFacts", "#VJVideos"],
  "comment_hook": "Provocative question in Tanglish to drive comments."
}}"""

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
            print("⚠️ Selector Agent failed. Using fallback.")
            return None
        selected_headline = selection["selected_headline"]
        selected_url = selection["selected_url"]
        
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
    if not research: return None

    # ── AGENT 2: HOOK ──
    print("🪝 [AGENT 2] Hook Agent: Generating Tanglish hooks...")
    hook_prompt = HOOK_AGENT_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        research_json=json.dumps(research)
    )
    hooks_data = call_gemini_api(client, hook_prompt)
    if not hooks_data or "hooks" not in hooks_data: return None
    
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
    if not narrative: return None

    # ── AGENT 4: RETENTION OPTIMIZER ──
    print("⚡ [AGENT 4] Pacing Optimizer: Shortening sentences...")
    retention_prompt = RETENTION_OPTIMIZER_TEMPLATE.format(
        persona=SYSTEM_PERSONA,
        narrative_json=json.dumps(narrative)
    )
    optimized = call_gemini_api(client, retention_prompt)
    if not optimized: return None

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
    
    final_script = call_gemini_api(client, humanizer_prompt, model='gemini-2.0-flash')
    
    if final_script:
        # Override metadata to match selected fact
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

def call_gemini_api(client, prompt, model='gemini-2.0-flash'):
    """
    Helper to execute Gemini API call with retries and JSON parsing.
    """
    attempts = 0
    while attempts < 3:
        try:
            response = client.models.generate_content(
                model=model,
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
            print(f"⚠️ Agent call failed: {e}. Retrying in {5 + attempts * 5}s...")
            time.sleep(5 + attempts * 5)
            attempts += 1
            
    print("🚨 Agent failed all attempts.")
    return None
