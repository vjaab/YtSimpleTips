import json
import os
from datetime import datetime
from rapidfuzz import fuzz
from config import TRACKER_FILE

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
    
    # 1. Exact URL Check
    if new_url:
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            if entry.get('source_url') == new_url or entry.get('news_source_url') == new_url:
                return False, f"Exact URL already covered: {new_url}"

    # 2. Semantic Title & Headline Check
    from config import SIMILARITY_THRESHOLD
    headlines_to_check = (tracker.get('used_titles', []) or []) + (tracker.get('last_7_days_stories', []) or [])
    
    search_titles = [new_title]
    if new_headline: 
        search_titles.append(new_headline)
    
    for existing_title in set(headlines_to_check):
        if not existing_title: continue
        for st in search_titles:
            if not st: continue
            score = fuzz.token_set_ratio(st.lower(), existing_title.lower())
            if score > SIMILARITY_THRESHOLD: 
                return False, f"Semantic match found (score {score}): '{existing_title}'"
            
    # 3. Keyword Overlap Check (Batch Deduplication)
    if new_keywords:
        recent_keywords = []
        for entry in tracker.get('history', [])[-10:]: # Look at last 10 stories
            recent_keywords.extend([k.lower() for k in entry.get('keywords', []) if k])
        
        new_k_set = set([k.lower() for k in new_keywords if k])
        old_k_set = set(recent_keywords)
        intersection = new_k_set.intersection(old_k_set)
        
        # If > 70% of keywords overlap with recent stories, it's likely redundant
        if len(new_k_set) > 0:
            overlap_pct = (len(intersection) / len(new_k_set)) * 100
            if overlap_pct > 70:
                return False, f"High keyword overlap ({overlap_pct:.0f}%) with recent stories."
                
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

def record_story(title, news_headline, category, keywords, voice_used, youtube_url, source_url, tracker_file=TRACKER_FILE):
    tracker = load_tracker(tracker_file)
    today = datetime.now().strftime("%Y-%m-%d")
    
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
        "source_url": source_url
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
