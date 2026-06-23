import json
import os
import re
from datetime import datetime
from rapidfuzz import fuzz
from config import TRACKER_FILE

def normalize_url(url):
    if not url:
        return ""
    url = url.strip().lower()
    # Remove protocol
    if url.startswith("https://"):
        url = url[8:]
    elif url.startswith("http://"):
        url = url[7:]
    # Remove www.
    if url.startswith("www."):
        url = url[4:]
    # Remove query parameters
    if "?" in url:
        url = url.split("?")[0]
    # Remove fragment
    if "#" in url:
        url = url.split("#")[0]
    # Remove trailing slash
    if url.endswith("/"):
        url = url[:-1]
    return url

def clean_title_for_comparison(title):
    if not title:
        return ""
    # Lowercase
    title = title.lower()
    # Remove punctuation
    title = re.sub(r'[^\w\s]', '', title)
    # Remove common English and Tamil stopwords
    stopwords = {
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'on', 'in', 'at', 'to', 'for', 'with', 
        'of', 'and', 'or', 'but', 'if', 'then', 'else', 'than', 'this', 'that', 'these', 'those',
        'from', 'by', 'about', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 
        'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'once', 'here', 
        'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
        'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'too', 
        'very', 's', 't', 'can', 'will', 'just', 'should', 'now',
        # Tamil stopwords/fillers (transliterated & Tamil script)
        'oru', 'indha', 'andha', 'enru', 'aana', 'irundhu', 'muthal', 'vazhi', 'moolam',
        'ஒரு', 'இந்த', 'அந்த', 'என்று', 'ஆனா', 'இருந்து', 'முதல்', 'வழி', 'மூலம்', 'மற்றும்'
    }
    words = title.split()
    filtered_words = [w for w in words if w not in stopwords]
    return " ".join(filtered_words)

def load_tracker(tracker_file=TRACKER_FILE):
    if not os.path.exists(tracker_file):
        return {
            "used_titles": [],
            "used_keywords": [],
            "used_categories": {},
            "last_7_days_stories": [],
            "total_uploaded": 0,
            "last_upload": None,
            "history": []
        }
    try:
        with open(tracker_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            "used_titles": [],
            "used_keywords": [],
            "used_categories": {},
            "last_7_days_stories": [],
            "total_uploaded": 0,
            "last_upload": None,
            "history": []
        }

def save_tracker(tracker_data, tracker_file=TRACKER_FILE):
    with open(tracker_file, 'w', encoding='utf-8') as f:
        json.dump(tracker_data, f, indent=4, ensure_ascii=False)

def check_story_uniqueness(new_title, new_headline=None, new_keywords=None, new_url=None, tracker_file=TRACKER_FILE):
    tracker = load_tracker(tracker_file)
    if not tracker:
        return True, "Unique (Empty tracker)"
    
    # 0. EXACT title match (fast, case-insensitive) — catches obvious repeats immediately
    if new_title:
        lower_new = new_title.strip().lower()
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            for field in ('title', 'news_headline'):
                old = entry.get(field)
                if old and old.strip().lower() == lower_new:
                    return False, f"Exact title match in history: '{old}'"
        for old_t in tracker.get('used_titles', []):
            if old_t and old_t.strip().lower() == lower_new:
                return False, f"Exact title match in used_titles: '{old_t}'"
    if new_headline:
        lower_hl = new_headline.strip().lower()
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            for field in ('title', 'news_headline'):
                old = entry.get(field)
                if old and old.strip().lower() == lower_hl:
                    return False, f"Exact headline match in history: '{old}'"
    
    # 1. URL Check (Normalized)
    if new_url:
        norm_new_url = normalize_url(new_url)
        # Skip checking google search grounding redirects because they are dynamic
        if "grounding-api-redirect" not in norm_new_url:
            for entry in tracker.get('history', []):
                if not isinstance(entry, dict): continue
                old_url = entry.get('source_url') or entry.get('news_source_url')
                if old_url:
                    if normalize_url(old_url) == norm_new_url:
                        return False, f"URL already covered: {new_url}"

    # 2. Semantic Title & Headline Check (with stopword removal)
    from config import SIMILARITY_THRESHOLD
    
    # Check used_titles, last_7_days_stories, and all history titles/news_headlines
    headlines_to_check = set(
        (tracker.get('used_titles', []) or []) + 
        (tracker.get('last_7_days_stories', []) or [])
    )
    for entry in tracker.get('history', []):
        if not isinstance(entry, dict): continue
        t = entry.get('title')
        h = entry.get('news_headline')
        if t: headlines_to_check.add(t)
        if h: headlines_to_check.add(h)
    
    search_titles = [new_title]
    if new_headline: 
        search_titles.append(new_headline)
    
    for existing_title in headlines_to_check:
        if not existing_title: continue
        for st in search_titles:
            if not st: continue
            
            # Clean both titles before calculating ratio
            cleaned_st = clean_title_for_comparison(st)
            cleaned_ext = clean_title_for_comparison(existing_title)
            
            if cleaned_st and cleaned_ext:
                score = fuzz.token_set_ratio(cleaned_st, cleaned_ext)
                if score > SIMILARITY_THRESHOLD: 
                    return False, f"Semantic match found (score {score:.1f}): '{existing_title}'"
            
    # 3. Keyword Overlap Check (across all historical stories)
    if new_keywords:
        historical_keywords = []
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            historical_keywords.extend([k.lower() for k in entry.get('keywords', []) if k])
        
        new_k_set = set([k.lower() for k in new_keywords if k])
        old_k_set = set(historical_keywords)
        intersection = new_k_set.intersection(old_k_set)
        
        # If > 70% of keywords overlap with history, it's likely redundant
        if len(new_k_set) > 0:
            overlap_pct = (len(intersection) / len(new_k_set)) * 100
            if overlap_pct > 70:
                return False, f"High keyword overlap ({overlap_pct:.0f}%) with historical stories."
                
    return True, "Unique"

def check_cooldowns(category, tracker_file=TRACKER_FILE):
    tracker = load_tracker(tracker_file)
    history = tracker.get('history', [])
    
    if len(history) < 2:
        return True, "Cooldowns OK"
        
    # Prevent consecutive category runs if possible
    last_categories = [entry.get('category') for entry in history[-2:] if entry.get('category')]
    if category in last_categories:
        return False, f"Category '{category}' covered too recently."
        
    return True, "Cooldowns OK"

def record_story(title, news_headline, category, keywords, voice_used, youtube_url, source_url, avatar_used=None, tracker_file=TRACKER_FILE):
    tracker = load_tracker(tracker_file)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Guard: refuse to record if this exact title already exists in history
    lower_title = (title or "").strip().lower()
    for entry in tracker.get('history', []):
        if not isinstance(entry, dict): continue
        if entry.get('title', '').strip().lower() == lower_title:
            print(f"⚠️ [record_story] Skipping duplicate record: '{title}' already in history.")
            return
    
    tracker.setdefault("used_titles", []).append(title)
    if news_headline:
        tracker.setdefault("used_titles", []).append(news_headline)
    
    if keywords:
        tracker.setdefault("used_keywords", []).extend(keywords)
        tracker["used_keywords"] = list(set(tracker["used_keywords"]))
        
    tracker.setdefault("used_categories", {})
    tracker["used_categories"][category] = tracker["used_categories"].get(category, 0) + 1
    
    tracker.setdefault("last_7_days_stories", []).append(title)
    if len(tracker["last_7_days_stories"]) > 7:
        tracker["last_7_days_stories"].pop(0)
        
    tracker["total_uploaded"] = tracker.get("total_uploaded", 0) + 1
    tracker["last_upload"] = today
    
    history_entry = {
        "date": today,
        "title": title,
        "news_headline": news_headline or title,
        "category": category,
        "keywords": keywords or [],
        "voice_used": voice_used,
        "youtube_url": youtube_url,
        "source_url": source_url,
        "avatar_used": avatar_used
    }
    tracker.setdefault("history", []).append(history_entry)
    save_tracker(tracker, tracker_file)

def update_youtube_url(title, youtube_url, tracker_file=TRACKER_FILE):
    tracker = load_tracker(tracker_file)
    for entry in tracker.get("history", []):
        if entry.get("title") == title or entry.get("news_headline") == title:
            entry["youtube_url"] = youtube_url
            break
    save_tracker(tracker, tracker_file)

def get_fact_count(tracker_file=TRACKER_FILE):
    """Returns the total number of facts uploaded so far (for the FACT #N badge)."""
    tracker = load_tracker(tracker_file)
    return tracker.get("total_uploaded", 0)

def get_next_avatar(intro_videos, tracker_file=TRACKER_FILE):
    """
    Selects the next avatar from the list of intro videos,
    ensuring we rotate through all of them before repeating.
    """
    if not intro_videos:
        return None
        
    tracker = load_tracker(tracker_file)
    history = tracker.get("history", [])
    
    # Sort intro_videos to guarantee consistent indexing across runs
    sorted_videos = sorted(intro_videos)
    
    # Find the last used avatar path in history
    last_avatar = None
    for entry in reversed(history):
        if not isinstance(entry, dict):
            continue
        av = entry.get("avatar_used")
        if av in sorted_videos:
            last_avatar = av
            break
            
    if not last_avatar:
        return sorted_videos[0]
        
    try:
        idx = sorted_videos.index(last_avatar)
        next_idx = (idx + 1) % len(sorted_videos)
        return sorted_videos[next_idx]
    except ValueError:
        return sorted_videos[0]
