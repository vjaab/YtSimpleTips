from google import genai
from google.genai import types
import json
import os
import requests
from datetime import datetime
from config import GEMINI_API_KEY, TRACKER_FILE, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS
from topic_tracker import check_story_uniqueness
from gemini_script import _OFFLINE_MODE_ACTIVE

# Best-effort trending signal integration
try:
    from trending_boost import get_trending_context, boost_articles_with_trending
    _TRENDING_AVAILABLE = True
except ImportError:
    _TRENDING_AVAILABLE = False

def validate_github_url(url, timeout=10):
    """
    Validate a GitHub URL by making a HEAD request.
    Returns True if URL returns 200, False otherwise.
    """
    if not url or "github.com" not in url:
        return False
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ URL validation failed for {url}: {e}")
        return False

def fetch_facts_from_llm_fallback(category, avoid_titles):
    """
    Generates 5 fresh, unique facts for a category using standard Gemini without Search Grounding,
    explicitly avoiding a list of already used titles.
    """
    # Check offline mode first
    if _OFFLINE_MODE_ACTIVE:
        print("🔴 [OFFLINE MODE] Skipping LLM fallback generation. Returning empty.")
        return []
    
    print(f"🔮 [fetch_topics] Attempting LLM generation fallback (without search grounding) for category '{category}'...")
    client = get_gemini_client()
    
    avoid_list_str = "\n".join([f"- {t}" for t in avoid_titles if t])
    avoid_instruction = f"CRITICAL: DO NOT generate any tips or hacks related to the following recently covered topics:\n{avoid_list_str}\n" if avoid_list_str else ""
    
    prompt = f"""
    Generate 5 highly viral, trending or popular GitHub repositories that common people or developers would find fascinating, related to coding, AI, tools, utility scripts, or software hacks.
    These topics MUST be actual popular GitHub repositories.
    Category focus: "{category}"
    These topics must align with high-performing infotainment trends in YouTube Shorts history for global Tamil audiences.
    They must be surprising, accurate, and optimized for a 45-55 second faceless Tamil infotainment YouTube Short titled "Simple Tips by VJ".
    
    GITHUB TRENDING CRITERIA:
    1. Every topic MUST be a popular or trending GitHub repository (e.g., vxcontrol/pentagi, lowlighter/metrics).
    2. Focus on high "curiosity gap" or "utility" hooks: "This free GitHub tool can do X", "This insane GitHub repository changes how you write code", "Why everyone is talking about this GitHub project".
    
    {avoid_instruction}
    
    CRITICAL REQUIREMENT: For each topic, you MUST provide its real, active GitHub URL (e.g., https://github.com/username/repository) as the source_url. This URL must be active and correct!
    
    Return ONLY a JSON object containing a "tips" array matching this schema:
    {{
      "tips": [
        {{
          "title": "Short descriptive English title of the GitHub topic (e.g. lowlighter/metrics - Generate Infographics for GitHub Profile)",
          "description": "A rich, detailed 2-3 sentence explanation of the GitHub repository in English, explaining what it does and why it is useful or trending.",
          "source_url": "Direct GitHub URL of the repository (e.g. https://github.com/lowlighter/metrics)",
          "source_name": "GitHub",
          "keywords": ["GitHub", "repository", "open-source"],
          "category": "{category}"
        }}
      ]
    }}
    
    Do NOT wrap in markdown tags like ```json.
    """
    
    if client:
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
                    if not is_unique:
                        print(f"⏭️ [fetch_topics fallback] Skipping non-unique fact: {title}. Reason: {reason}")
                        continue
                    
                    # Validate GitHub URL
                    if "github.com" in url.lower():
                        print(f"🔍 Validating GitHub URL: {url}")
                        if not validate_github_url(url):
                            print(f"⚠️ GitHub URL returned 404 or unreachable: {url}. Skipping.")
                            continue
                        print(f"✅ GitHub URL validated: {url}")
                    else:
                        print(f"⏭️ [fetch_topics fallback] Skipping non-GitHub URL: {url}")
                        continue
                        
                    unique_facts.append(fact)
                
                if unique_facts:
                    print(f"✅ [fetch_topics fallback] Successfully generated {len(unique_facts)} unique facts via LLM.")
                    return unique_facts
                
                print("⚠️ [fetch_topics fallback] All LLM generated facts were duplicates. Retrying fallback generation...")
                attempts += 1
            except Exception as e:
                err_str = str(e).lower()
                is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
                if is_depleted_or_429:
                    from config import disable_gemini
                    disable_gemini()
                    print("🚨 [fetch_topics fallback] Globally disabling Gemini after 429/credit depletion. Breaking to use non-Gemini fallback.")
                    break
                print(f"⚠️ [fetch_topics fallback] LLM fallback failed: {e}. Retrying...")
                attempts += 1
    else:
        print("⚠️ Gemini API Client missing/disabled. Skipping Gemini LLM fallback.")
            
    print("🚨 [fetch_topics fallback] Attempting non-Gemini fallback models (Groq/OpenAI/etc)...")
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
                if not is_unique:
                    print(f"⏭️ [fetch_topics fallback models] Skipping non-unique fact: {title}. Reason: {reason}")
                    continue
                
                # Validate GitHub URL
                if "github.com" in url.lower():
                    print(f"🔍 Validating GitHub URL: {url}")
                    if not validate_github_url(url):
                        print(f"⚠️ GitHub URL returned 404 or unreachable: {url}. Skipping.")
                        continue
                    print(f"✅ GitHub URL validated: {url}")
                else:
                    print(f"⏭️ [fetch_topics fallback models] Skipping non-GitHub URL: {url}")
                    continue
                    
                unique_facts.append(fact)
            
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
    # Check offline mode first
    if _OFFLINE_MODE_ACTIVE:
        print("🔴 [OFFLINE MODE] Skipping search grounding. Returning historical fallback only.")
        return get_historical_fallback(category)
    
    # Load avoid titles early to support early fallback routing
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

    # Fetch VidIQ topics for this category
    vidiq_topics = []
    try:
        # Map category to a clean category for VidIQ
        vidiq_category_map = {
            "🧠 Amazing Science Facts": "Science",
            "🌍 World & History Secrets": "History",
            "🔬 Tech & Innovation Wonders": "Technology",
            "🌌 Space & Universe Mysteries": "Space",
            "🧬 Human Body & Psychology": "Health",
            "🐾 Nature & Animal Oddities": "Nature",
            "💡 Mind-Blowing Did You Know": "Education"
        }
        vidiq_category = vidiq_category_map.get(category, "Education")
            
        from vidiq_trending import get_pipeline_topics
        vidiq_raw = get_pipeline_topics(category=vidiq_category)
        for item in vidiq_raw:
            title = item.get("title", "")
            url = item.get("url", "")
            if not title:
                continue
            is_unique, reason = check_story_uniqueness(new_title=title, new_url=url)
            if is_unique:
                vidiq_topics.append({
                    "title": title,
                    "description": f"vidIQ Opportunity Score: {item.get('score', 60)} (Volume: {item.get('search_volume', 5000)}, Competition: {item.get('competition', 35)})",
                    "source_url": url,
                    "source_name": "vidIQ",
                    "keywords": ["vidIQ", vidiq_category],
                    "category": category
                })
                if len(vidiq_topics) >= 3:
                    break
        print(f"📈 [fetch_topics] Fetched {len(vidiq_topics)} unique, high-signal VidIQ topics.")
    except Exception as e:
        print(f"⚠️ [fetch_topics] VidIQ integration failed (non-fatal): {e}")

    client = get_gemini_client()
    if not client:
        print("⚠️ Gemini API Client missing/disabled. Skipping Search Grounding and attempting LLM fallback directly.")
        unique_fallback_facts = fetch_facts_from_llm_fallback(category, avoid_titles)
        if unique_fallback_facts:
            return unique_fallback_facts + vidiq_topics
        return get_historical_fallback(category) + vidiq_topics

    # Fetch trending signals to inject into the search query
    trending_context = ""
    if _TRENDING_AVAILABLE:
        try:
            trending_context = get_trending_context(category)
            if trending_context:
                trending_context = f"\n    {trending_context}"
        except Exception as e:
            print(f"  ⚠️ [fetch_topics] Trending boost skipped: {e}")

    prompt = f"""
    Search the web for 5 highly viral, surprising "Did You Know" facts that Tamil audiences would find fascinating, related to {category}.
    These topics MUST be verified, accurate facts from reliable sources (Wikipedia, scientific journals, reputable news, encyclopedias).
    They must be surprising, counter-intuitive, or mind-blowing - optimized for a 45-60 second Tamil/Tanglish YouTube Short titled "Simple Tips by VJ".
    
    FACT CRITERIA:
    1. Every topic MUST be a verified fact with a credible source URL (Wikipedia, Britannica, Nature, Science journals, reputable news sites).
    2. Focus on high "curiosity gap" hooks: "Did you know...", "Most people don't know...", "This will change how you see...".
    3. Avoid common knowledge - pick facts that make people say "Wait, really?!".
    {trending_context}
    
    CRITICAL REQUIREMENT: For each topic, you MUST search for and provide its real, verifiable source URL as the source_url. This URL must be active and correct!
    
    Return ONLY a JSON list of 5 tips matching this schema:
    [
      {{
        "title": "Short descriptive English title of the fact (e.g. Honey Never Spoils - 3000 Year Old Edible Honey Found)",
        "description": "A rich, detailed 2-3 sentence explanation of the fact in English, explaining why it's surprising and the science/history behind it.",
        "source_url": "Direct source URL (e.g. https://en.wikipedia.org/wiki/Honey#Preservation)",
        "source_name": "Wikipedia / Scientific Journal / News Site",
        "keywords": ["did you know", "fact", "science"],
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
                if not is_unique:
                    print(f"⏭️ Skipping non-unique fact: {title}. Reason: {reason}")
                    continue
                    
                # Validate GitHub URL to prevent 404 errors later
                if "github.com" in url.lower():
                    print(f"🔍 Validating GitHub URL: {url}")
                    if not validate_github_url(url):
                        print(f"⚠️ GitHub URL returned 404 or unreachable: {url}. Skipping.")
                        continue
                    print(f"✅ GitHub URL validated: {url}")
                else:
                    print(f"⏭️ Skipping non-GitHub URL: {url}")
                    continue
                    
                unique_facts.append(fact)
                    
            # Keep ONLY github topics
            unique_facts = [f for f in unique_facts if "github.com" in f.get("source_url", "").lower()]
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
            
            if is_depleted_or_429:
                if len(GEMINI_API_KEYS) > 1:
                    rotate_gemini_api_key()
                    client = get_gemini_client()
                    print("🔄 [fetch_topics] Successfully rotated API key after 429 / credit depletion. Retrying immediately...")
                    attempts += 1
                    continue
                else:
                    from config import disable_gemini
                    disable_gemini()
                    print("🚨 [fetch_topics] Only 1 key available or exhausted. Globally disabling Gemini after 429/credit depletion. Breaking to fallback.")
                    break
                
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
    unique_fallback_facts = [f for f in unique_fallback_facts if "github.com" in f.get("source_url", "").lower()]
    if unique_fallback_facts:
        return unique_fallback_facts
        
    print("🚨 [fetch_topics] LLM fallback failed. Loading historical backup as absolute last resort...")
    hist_fallback = get_historical_fallback(category)
    hist_fallback = [f for f in hist_fallback if "github.com" in f.get("source_url", "").lower()]
    if hist_fallback:
        return hist_fallback
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
                    validated = []
                    for s in selected:
                        url = s.get("source_url", "")
                        if "github.com" in url.lower() and validate_github_url(url):
                            validated.append({
                                "title": s.get("title"),
                                "description": s.get("news_headline", "Fascinating facts fallback."),
                                "source_url": url,
                                "source_name": "Historical Backup",
                                "keywords": s.get("keywords", []),
                                "category": category
                            })
                        else:
                            print(f"⚠️ Skipping historical fact with invalid URL: {url}")
                    if validated:
                        return validated
        except Exception as e:
            print(f"⚠️ Failed to load fallback from tracker: {e}")
            
    # Absolute minimum fallback to ensure pipeline never crashes
    print("🚨 Absolute fallback: Generating GitHub repository fallback...")
    return [{
        "title": "lowlighter/metrics - Generate Infographics for GitHub Profile",
        "description": "A popular GitHub repository that generates gorgeous infographics, anime characters, coding habits, and music playlist metrics directly onto your GitHub profile page using simple markdown integrations.",
        "source_url": "https://github.com/lowlighter/metrics",
        "source_name": "GitHub",
        "keywords": ["GitHub", "metrics", "infographics", "profile"],
        "category": category
    }]
