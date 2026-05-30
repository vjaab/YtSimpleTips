from google import genai
from google.genai import types
import json
import os
from datetime import datetime
from config import GEMINI_API_KEY, TRACKER_FILE
from topic_tracker import check_story_uniqueness

def fetch_facts_for_category(category):
    """
    Uses Gemini Search Grounding to find 5 fresh, high-engagement, true facts
    for the selected category.
    Returns a list of structured fact articles.
    """
    print(f"📡 [fetch_topics] Fetching trending facts for category '{category}' using Gemini Search Grounding...")
    
    if not GEMINI_API_KEY:
        print("⚠️ Gemini API Key missing! Cannot fetch facts.")
        return []
        
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = f"""
    Search the web for 5 highly engaging, trending, and useful tutorial topics about how to use popular apps or websites in the category: "{category}".
    Each topic must focus on a specific, popular app or website (e.g., "How to use Blinkit", "How to use CapCut for transitions", "How to book train tickets on IRCTC website", etc.) that is highly relevant to Indian/global viewers and suitable for a 45-55 second educational Tamil YouTube Short tutorial.
    
    CRITICAL REQUIREMENT: For each tutorial topic, you MUST provide the real, active official landing/login URL of that app or website (e.g., https://blinkit.com, https://www.capcut.com, or https://www.irctc.co.in) to use as the source. We will capture a live screenshot of this website for the video, so the URL MUST be active, direct, and precise!
    
    Return ONLY a JSON list of 5 tutorial topics matching this schema:
    [
      {{
        "title": "Short descriptive English title of the tutorial (e.g. How to use Blinkit)",
        "description": "A step-by-step summary in English of how to use this app/website (login, search, select, checkout/complete), optimized for a quick 45-55s educational guide.",
        "source_url": "Direct official landing/login URL of the app/website (e.g. https://blinkit.com)",
        "source_name": "Name of the app/website (e.g. Blinkit, CapCut, IRCTC)",
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
                model='gemini-2.0-flash',
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
                return unique_facts
            else:
                print("⚠️ All fetched facts were duplicates. Retrying fetch...")
                attempts += 1
                
        except Exception as e:
            print(f"⚠️ [fetch_topics] Fact fetch failed: {e}. Retrying in 5s...")
            import time
            time.sleep(5)
            attempts += 1
            
    # Fallback if search grounding completely fails or returns only duplicates
    print("🚨 [fetch_topics] All search grounding attempts failed or returned duplicates. Loading historical backup...")
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
