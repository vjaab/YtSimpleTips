from google import genai
from google.genai import types
import json
import os
from datetime import datetime
from config import GEMINI_API_KEY, TRACKER_FILE, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS
from topic_tracker import check_story_uniqueness

# Best-effort trending signal integration
try:
    from trending_boost import get_trending_context, boost_articles_with_trending
    _TRENDING_AVAILABLE = True
except ImportError:
    _TRENDING_AVAILABLE = False

def fetch_facts_from_llm_fallback(category, avoid_titles):
    """
    Generates 5 fresh, unique facts for a category using standard Gemini without Search Grounding,
    explicitly avoiding a list of already used titles.
    """
    print(f"🔮 [fetch_topics] Attempting LLM generation fallback (without search grounding) for category '{category}'...")
    client = get_gemini_client()
    if not client:
        print("⚠️ Gemini API Client missing! Cannot run LLM fallback.")
        return []
    
    avoid_list_str = "\n".join([f"- {t}" for t in avoid_titles if t])
    avoid_instruction = f"CRITICAL: DO NOT generate any tips or hacks related to the following recently covered topics:\n{avoid_list_str}\n" if avoid_list_str else ""
    
    prompt = f"""
    Generate 5 highly viral, trending, practical, and true life hacks, tips, or settings/shortcuts related to the category: "{category}".
    These tips must be highly actionable, surprising, and optimized for a 45-55 second faceless Tamil infotainment YouTube Short titled "Simple Tips by VJ".
    
    DEMOGRAPHIC & TRENDING CRITERIA:
    1. The tip must have high appeal and immediate utility for parents, middle-aged, or young people in daily life.
    2. Strongly prioritize tech-infused tips, digital settings, phone/smart-device hacks, app shortcuts, or simple sports/fitness routines that simplify life or improve health.
    
    {avoid_instruction}
    
    CRITICAL REQUIREMENT: For each tip/hack, you MUST provide a real, active source URL (like Wikipedia, official guide, or reputable publication) that supports this tip. We will capture a live screenshot of this website for the video, so the URL MUST be active and precise!
    
    Return ONLY a JSON object containing a "tips" array matching this schema:
    {{
      "tips": [
        {{
          "title": "Short descriptive English title of the tip (e.g. WhatsApp Screen Lock Setup)",
          "description": "A rich, detailed 2-3 sentence explanation of the tip/hack in English...",
          "source_url": "Direct URL to Wikipedia, official guide, or reputable source",
          "source_name": "Name of the source",
          "keywords": ["keyword1", "keyword2", "keyword3"],
          "category": "{category}"
        }}
      ]
    }}
    
    Do NOT wrap in markdown tags like ```json.
    """
    
    attempts = 0
    while attempts < 3:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7
                )
            )
            raw = response.text.strip()
            if "```json" in raw:
                raw = raw[raw.find("```json")+7:raw.rfind("```")]
            elif "```" in raw:
                raw = raw[raw.find("```")+3:raw.rfind("```")]
            raw = raw.strip()
            if raw.startswith("["):
                facts = json.loads(raw)
            else:
                data = json.loads(raw)
                facts = data.get("tips", []) if isinstance(data, dict) else data
            
            # Filter unique facts
            unique_facts = []
            for fact in facts:
                title = fact.get("title", "")
                url = fact.get("source_url", "")
                is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
                if is_unique:
                    unique_facts.append(fact)
                else:
                    print(f"⏭️ [fetch_topics fallback] Skipping non-unique fact: {title}. Reason: {reason}")
            
            if unique_facts:
                print(f"✅ [fetch_topics fallback] Successfully generated {len(unique_facts)} unique facts via LLM.")
                return unique_facts
            
            print("⚠️ [fetch_topics fallback] All LLM generated facts were duplicates. Retrying fallback generation...")
            attempts += 1
        except Exception as e:
            print(f"⚠️ [fetch_topics fallback] LLM fallback failed: {e}. Retrying...")
            attempts += 1
            
    print("🚨 [fetch_topics fallback] Gemini API failed all attempts. Attempting non-Gemini fallback models (Groq/OpenAI/etc)...")
    try:
        from gemini_script import call_fallback_model
        fallback_res = call_fallback_model(prompt)
        if fallback_res:
            facts = fallback_res.get("tips", []) if isinstance(fallback_res, dict) else fallback_res
            unique_facts = []
            for fact in facts:
                title = fact.get("title", "")
                url = fact.get("source_url", "")
                is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
                if is_unique:
                    unique_facts.append(fact)
                else:
                    print(f"⏭️ [fetch_topics fallback models] Skipping non-unique fact: {title}. Reason: {reason}")
            
            if unique_facts:
                print(f"✅ [fetch_topics fallback models] Successfully generated {len(unique_facts)} unique facts via fallback models.")
                return unique_facts
    except Exception as e:
        print(f"⚠️ [fetch_topics fallback models] Non-Gemini fallback also failed: {e}")
        
    return []

def fetch_facts_for_category(category):
    """
    Uses Gemini Search Grounding to find 5 fresh, high-utility, actionable tips/hacks
    for the selected category.
    Returns a list of structured tip articles.
    """
    print(f"📡 [fetch_topics] Fetching trending tips and hacks for category '{category}' using Gemini Search Grounding...")
    
    client = get_gemini_client()
    if not client:
        print("⚠️ Gemini API Client missing! Cannot fetch tips.")
        return []
    
    # Fetch trending signals to inject into the search query
    trending_context = ""
    if _TRENDING_AVAILABLE:
        try:
            trending_context = get_trending_context(category)
            if trending_context:
                trending_context = f"\n    {trending_context}"
        except Exception as e:
            print(f"  ⚠️ [fetch_topics] Trending boost skipped: {e}")
        
    # Load avoid titles to pass to standard LLM fallback
    from topic_tracker import load_tracker
    tracker = load_tracker()
    headlines_to_avoid = set(
        (tracker.get('used_titles', []) or []) + 
        (tracker.get('last_7_days_stories', []) or [])
    )
    for entry in tracker.get('history', []):
        if not isinstance(entry, dict): continue
        t = entry.get('title')
        h = entry.get('news_headline')
        if t: headlines_to_avoid.add(t)
        if h: headlines_to_avoid.add(h)
    avoid_titles = list(headlines_to_avoid)
    
    prompt = f"""
    Search the web for 5 highly viral, trending, practical, and true life hacks, tips, or settings/shortcuts related to the category: "{category}".
    These tips must be highly actionable, surprising, and optimized for a 30-40 second faceless Tamil infotainment YouTube Short titled "Simple Tips by VJ".
    
    DEMOGRAPHIC & TRENDING CRITERIA:
    1. The tip must have high appeal and immediate utility for at least one of these groups:
       - Parents: Kid-safety features, smart home efficiency, budgeting/saving on bills.
       - Middle-aged: Phone settings, WhatsApp tips, UPI/online security, daily life convenience, spam blocking.
       - Young People: Focus/study apps, tech shortcuts, productivity tools, sports/fitness hacks, hidden settings.
    2. Strongly prioritize tech-infused tips, digital settings, phone/smart-device hacks, app shortcuts, or athletic/fitness hacks that simplify life.
    3. Focus on tips that are NEW or recently updated (2025-2026 relevance).
    {trending_context}
    
    CRITICAL REQUIREMENT: For each tip/hack, you MUST search for and provide a real, active source URL (like a reputable news article, Wikipedia page, life hack publication, scientific study, or official guide) that supports this tip. We will capture a live screenshot of this website for the video, so the URL MUST be active and precise!
    
    Return ONLY a JSON list of 5 tips matching this schema:
    [
      {{
        "title": "Short descriptive English title of the tip (e.g. WhatsApp Screen Lock Setup)",
        "description": "A rich, detailed 2-3 sentence explanation of the tip/hack in English, explaining exactly how it works, how to apply it, and the direct benefit to parents, middle-aged, or young people.",
        "source_url": "Direct URL to Wikipedia, a reputable article, or official source documenting this specific tip",
        "source_name": "Name of the source (e.g. Wikipedia, Healthline, Medium)",
        "keywords": ["keyword1", "keyword2", "keyword3"],
        "category": "{category}"
      }}
    ]
    
    Do NOT wrap in markdown tags like ```json. Return ONLY the raw JSON string starting with [ and ending with ].
    """
    
    attempts = 0
    while attempts < 3:
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{'google_search': {}}],
                    temperature=0.7
                )
            )
            raw = response.text.strip()
            
            # Robust JSON extraction
            if "[" in raw and "]" in raw:
                raw = raw[raw.find("["):raw.rfind("]")+1]
                
            facts = json.loads(raw)
            print(f"✅ [fetch_topics] Successfully fetched {len(facts)} facts from search grounding.")
            
            # Filter unique facts
            unique_facts = []
            for fact in facts:
                title = fact.get("title", "")
                url = fact.get("source_url", "")
                
                is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
                if is_unique:
                    unique_facts.append(fact)
                else:
                    print(f"⏭️ Skipping non-unique fact: {title}. Reason: {reason}")
                    
            if unique_facts:
                # Apply trending boost scoring if available
                if _TRENDING_AVAILABLE:
                    try:
                        unique_facts = boost_articles_with_trending(unique_facts, category)
                    except Exception as e:
                        print(f"  ⚠️ [fetch_topics] Trending boost failed (non-fatal): {e}")
                return unique_facts
            else:
                print("⚠️ All fetched facts were duplicates. Retrying fetch...")
                attempts += 1
                
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(
                k in err_str
                for k in ["503", "429", "unavailable", "rate limit", "resource exhausted", "demand", "temporary"]
            )
            is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
            
            if is_depleted_or_429 and len(GEMINI_API_KEYS) > 1:
                rotate_gemini_api_key()
                client = get_gemini_client()
                print("🔄 [fetch_topics] Successfully rotated API key after 429 / credit depletion. Retrying immediately...")
                attempts += 1
                continue
                
            if is_rate_limit:
                import random
                sleep_time = int(10 * (1.8 ** attempts) + random.uniform(1, 4))
                print(f"⚠️ [fetch_topics] Gemini API high demand/rate limit. Waiting {sleep_time}s...")
            else:
                sleep_time = 5 + attempts * 5
                print(f"⚠️ [fetch_topics] Fact fetch failed: {e}. Retrying in {sleep_time}s...")
            import time
            time.sleep(sleep_time)
            attempts += 1
            
    # Fallback if search grounding completely fails or returns only duplicates
    print("🚨 [fetch_topics] All search grounding attempts failed or returned duplicates. Attempting LLM fallback...")
    unique_fallback_facts = fetch_facts_from_llm_fallback(category, avoid_titles)
    if unique_fallback_facts:
        return unique_fallback_facts
        
    print("🚨 [fetch_topics] LLM fallback failed. Loading historical backup as absolute last resort...")
    return get_historical_fallback(category)

def get_historical_fallback(category):
    """
    Loads historical facts from the topic tracker log as a last-resort backup.
    """
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, 'r', encoding='utf-8') as f:
                tracker = json.load(f)
                history = tracker.get("history", [])
                
                # Try to find recent entries with matching category
                backup = [h for h in history if h.get("category") == category]
                if not backup:
                    backup = history
                    
                if backup:
                    selected = backup[-5:]  # Use last 5 as backup
                    print(f"✅ Loaded {len(selected)} historical backup facts.")
                    return [{
                        "title": s.get("title"),
                        "description": s.get("news_headline", "Fascinating facts fallback."),
                        "source_url": s.get("source_url", ""),
                        "source_name": "Historical Backup",
                        "keywords": s.get("keywords", []),
                        "category": category
                    } for s in selected]
        except Exception as e:
            print(f"⚠️ Failed to load fallback from tracker: {e}")
            
    # Absolute minimum fallback to ensure pipeline never crashes
    print("🚨 Absolute fallback: Generating generic fact...")
    return [{
        "title": "Quantum Entanglement",
        "description": "Quantum entanglement is a phenomenon where two particles remain connected, meaning actions performed on one affect the other immediately, regardless of distance. Albert Einstein called this 'spooky action at a distance'.",
        "source_url": "https://en.wikipedia.org/wiki/Quantum_entanglement",
        "source_name": "Wikipedia",
        "keywords": ["quantum", "physics", "einstein"],
        "category": category
    }]
