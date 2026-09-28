import json
import os
import re
from datetime import datetime
from rapidfuzz import fuzz
from config import TRACKER_FILE

GENERIC_DOMAINS = {
    "en.wikipedia.org", "wikipedia.org", "github.com", "google.com", "youtube.com",
    "youtu.be", "vjaab/ytsimpletips", "support.google.com"
}

TOPIC_CLUSTERS = [
    {"name": "honey", "terms": {"honey", "ancient honey", "honey science", "தேன", "தேன்"}},
    {"name": "jellyfish", "terms": {"jellyfish", "turritopsis", "immortal jellyfish", "ஜெல்லிஃபிஷ்"}},
    {"name": "banana", "terms": {"banana", "bananas", "வாழைப்பழம்"}},
    {"name": "eiffel_tower", "terms": {"eiffel", "tower", "15cm", "ஈபிள்"}},
    {"name": "doorway_effect", "terms": {"doorway", "room", "மறந்து", "doorway effect"}},
    {"name": "crow_memory", "terms": {"crow", "crows", "face memory", "காகம்"}},
    {"name": "octopus", "terms": {"octopus", "3 hearts", "blue blood", "ஆக்டோபஸ்"}},
    {"name": "two_oceans", "terms": {"two oceans", "oceans dont mix", "oceans mix", "density difference", "கடல் கலக்க", "பெருங்கடல்"}},
    {"name": "salt_boil", "terms": {"salt", "boiling", "உப்பு", "கொதி"}},
    {"name": "ac_electricity", "terms": {"ac 24", "electricity bill", "மின்சார", "கரண்ட் பில்"}},
    {"name": "thanjavur_temple", "terms": {"thanjavur", "brihadeeswarar", "தஞ்சை", "பெரிய கோவில்", "shadow", "நிழல்"}},
    {"name": "pyramid_mammoths", "terms": {"mammoth", "mammoths", "pyramid", "pyramids", "மேமத்", "பிரமிடு"}},
    {"name": "bubble_wrap", "terms": {"bubble wrap", "wallpaper", "பப்பிள்"}},
    {"name": "microwave_melt", "terms": {"microwave", "chocolate bar", "chocolate melt", "மைக்ரோவேவ்"}},
    {"name": "roman_concrete", "terms": {"roman concrete", "self-healing concrete", "ரோமன் கான்கிரீட்"}},
    {"name": "ai_voice_scam", "terms": {"voice clone", "voice cloning", "relative in distress", "குரல் குளோனிங்"}},
    {"name": "battery_charging", "terms": {"airplane mode charging", "battery hack", "developer options battery", "பேட்டரி சேவர்"}},
    {"name": "moravec", "terms": {"moravec", "moravec's paradox"}},
    {"name": "overfitting", "terms": {"overfitting", "mugapadi"}},
    {"name": "gboard_typing", "terms": {"gboard", "predictive text"}},
    {"name": "google_maps_live", "terms": {"google maps live view", "live view directions"}},
    {"name": "five_second_rule", "terms": {"5 second rule", "five second rule", "5 செகண்ட்ஸ் ரூல்"}},
    {"name": "stellarium_sky", "terms": {"stellarium", "planetarium", "night sky pc"}},
    {"name": "brain_computer_interface", "terms": {"openbci", "mind control computer", "மூளையால் computer"}},
    {"name": "tn_e_governance", "terms": {"tamil nadu e governance", "தமிழ்நாட்டில் ai", "tnega"}},
    {"name": "ai_ethics_future", "terms": {"ai எதிர்காலம்", "ethics of artificial intelligence", "ai future what to do"}}
]

STOPWORDS = {
    'a', 'an', 'the', 'is', 'are', 'was', 'were', 'on', 'in', 'at', 'to', 'for', 'with', 
    'of', 'and', 'or', 'but', 'if', 'then', 'else', 'than', 'this', 'that', 'these', 'those',
    'from', 'by', 'about', 'as', 'into', 'through', 'during', 'before', 'after', 'above', 
    'below', 'up', 'down', 'out', 'off', 'over', 'under', 'again', 'further', 'once', 'here', 
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'too', 
    'very', 's', 't', 'can', 'will', 'just', 'should', 'now', 'what', 'which', 'who', 'whom',
    'did', 'you', 'know', 'secret', 'hack', 'hacks', 'tips', 'trick', 'tricks', 'video', 'simple',
    'tamil', 'tanglish', 'shorts', 'vj', 'vjvideos', 'facts', 'fact', 'amazing', 'mind', 'blowing',
    'science', 'world', 'daily', 'life', 'true', 'really',
    # Tamil stopwords / particles
    'oru', 'indha', 'andha', 'enru', 'aana', 'irundhu', 'muthal', 'vazhi', 'moolam', 'theriyuma',
    'unmai', 'unmaiyave', 'ippadi', 'appadi', 'enna', 'ethu', 'eppadi', 'yenga', 'yenna',
    'ஒரு', 'இந்த', 'அந்த', 'என்று', 'ஆனா', 'இருந்து', 'முதல்', 'வழி', 'மூலம்', 'மற்றும்',
    'தெரியுமா', 'உண்மை', 'என்ன', 'எப்படி', 'ரகசியம்', 'ஹேக்', 'டிப்ஸ்'
}

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

def is_substantive_url(norm_url):
    if not norm_url:
        return False
    if norm_url in GENERIC_DOMAINS:
        return False
    parts = norm_url.split("/")
    if len(parts) <= 1 or not parts[1].strip():
        return False
    if parts[0] in GENERIC_DOMAINS and len(parts[1]) <= 2:
        return False
    return True

def clean_title_for_comparison(title):
    if not title:
        return ""
    title = title.lower()
    # Preserve Tamil characters (\u0B80-\u0BFF), English alphanumeric and spaces
    title = re.sub(r'[^\w\s\u0B80-\u0BFF]', ' ', title)
    words = title.split()
    filtered_words = [w for w in words if w not in STOPWORDS]
    return " ".join(filtered_words)

def extract_distinctive_tokens(text):
    if not text:
        return set()
    cleaned = clean_title_for_comparison(text)
    return set(w for w in cleaned.split() if len(w) >= 3 and w not in STOPWORDS)

def get_matching_clusters(text):
    if not text:
        return set()
    norm = clean_title_for_comparison(text)
    norm_words = set(norm.split())
    matched = set()
    for cluster in TOPIC_CLUSTERS:
        for term in cluster["terms"]:
            term_clean = clean_title_for_comparison(term)
            term_words = term_clean.split()
            if len(term_words) == 1:
                if term_clean in norm_words:
                    matched.add(cluster["name"])
                    break
            elif len(term_words) > 1:
                if f" {term_clean} " in f" {norm} ":
                    matched.add(cluster["name"])
                    break
    return matched

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
    
    clean_new_title = clean_title_for_comparison(new_title)
    clean_new_hl = clean_title_for_comparison(new_headline) if new_headline else ""
    norm_new_url = normalize_url(new_url) if new_url else ""
    
    new_combined_text = f"{new_title or ''} {new_headline or ''}"
    new_tokens = extract_distinctive_tokens(new_combined_text)
    new_clusters = get_matching_clusters(new_combined_text)
    
    # 0. EXACT normalized title/headline match across all history and used_titles
    if clean_new_title:
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            for field in ('title', 'news_headline'):
                old = entry.get(field)
                if old and clean_title_for_comparison(old) == clean_new_title:
                    return False, f"Exact normalized title match in history: '{old}'"
        for old_t in tracker.get('used_titles', []):
            if old_t and clean_title_for_comparison(old_t) == clean_new_title:
                return False, f"Exact normalized title match in used_titles: '{old_t}'"
                
    if clean_new_hl:
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            for field in ('title', 'news_headline'):
                old = entry.get(field)
                if old and clean_title_for_comparison(old) == clean_new_hl:
                    return False, f"Exact normalized headline match in history: '{old}'"

    # 1. Substantive URL Match
    if norm_new_url and is_substantive_url(norm_new_url):
        if "grounding-api-redirect" not in norm_new_url:
            for entry in tracker.get('history', []):
                if not isinstance(entry, dict): continue
                old_url = entry.get('source_url') or entry.get('news_source_url')
                if old_url:
                    old_norm_url = normalize_url(old_url)
                    if is_substantive_url(old_norm_url) and old_norm_url == norm_new_url:
                        return False, f"Substantive URL already covered: {new_url}"

    # 2. Topic Concept Cluster Match
    if new_clusters:
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            old_combined = f"{entry.get('title', '')} {entry.get('news_headline', '')}"
            old_clusters = get_matching_clusters(old_combined)
            overlap = new_clusters.intersection(old_clusters)
            if overlap:
                cluster_name = list(overlap)[0]
                return False, f"Core topic concept '{cluster_name}' already covered: '{entry.get('title')}'"

    # 3. Distinctive Token Overlap Check
    if new_tokens:
        for entry in tracker.get('history', []):
            if not isinstance(entry, dict): continue
            old_combined = f"{entry.get('title', '')} {entry.get('news_headline', '')}"
            old_tokens = extract_distinctive_tokens(old_combined)
            token_overlap = new_tokens.intersection(old_tokens)
            if len(token_overlap) >= 2:
                overlap_words = ", ".join(list(token_overlap)[:3])
                return False, f"Distinctive keywords ({overlap_words}) overlap with: '{entry.get('title')}'"

    # 4. Semantic RapidFuzz Match
    from config import SIMILARITY_THRESHOLD
    effective_threshold = min(SIMILARITY_THRESHOLD, 68)  # Strict gate
    
    all_historical_titles = set(
        (tracker.get('used_titles', []) or []) + 
        (tracker.get('last_7_days_stories', []) or [])
    )
    for entry in tracker.get('history', []):
        if not isinstance(entry, dict): continue
        t = entry.get('title')
        h = entry.get('news_headline')
        if t: all_historical_titles.add(t)
        if h: all_historical_titles.add(h)

    search_titles = [new_title]
    if new_headline:
        search_titles.append(new_headline)

    for existing_title in all_historical_titles:
        if not existing_title: continue
        clean_ext = clean_title_for_comparison(existing_title)
        if not clean_ext: continue
        
        for st in search_titles:
            if not st: continue
            clean_st = clean_title_for_comparison(st)
            if not clean_st: continue
            
            score_ts = fuzz.token_set_ratio(clean_st, clean_ext)
            score_sort = fuzz.token_sort_ratio(clean_st, clean_ext)
            if score_ts >= effective_threshold or score_sort >= 70:
                return False, f"Semantic match found (score {max(score_ts, score_sort):.1f}): '{existing_title}'"

    # 5. Keyword Overlap Check against individual historical entries
    if new_keywords and isinstance(new_keywords, list):
        clean_new_kw = set(k.lower().strip() for k in new_keywords if k and len(k.strip()) >= 3 and k.lower().strip() not in STOPWORDS)
        if len(clean_new_kw) >= 2:
            for entry in tracker.get('history', []):
                if not isinstance(entry, dict): continue
                old_kw = entry.get('keywords', [])
                if not old_kw or not isinstance(old_kw, list): continue
                clean_old_kw = set(k.lower().strip() for k in old_kw if k and len(k.strip()) >= 3 and k.lower().strip() not in STOPWORDS)
                common_kw = clean_new_kw.intersection(clean_old_kw)
                if len(common_kw) >= 2 and (len(common_kw) / len(clean_new_kw)) >= 0.5:
                    return False, f"Keyword overlap ({', '.join(list(common_kw)[:3])}) with story: '{entry.get('title')}'"

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
    
    # Pre-record uniqueness verification
    is_unique, reason = check_story_uniqueness(
        new_title=title,
        new_headline=news_headline,
        new_keywords=keywords,
        new_url=source_url,
        tracker_file=tracker_file
    )
    if not is_unique:
        print(f"⚠️ [record_story] Refusing to record duplicate story in history: '{title}'. Reason: {reason}")
        return False
    
    tracker.setdefault("used_titles", []).append(title)
    if news_headline and news_headline != title:
        tracker.setdefault("used_titles", []).append(news_headline)
    
    if keywords:
        tracker.setdefault("used_keywords", []).extend(keywords)
        tracker["used_keywords"] = list(set(tracker["used_keywords"]))
        
    tracker.setdefault("used_categories", {})
    tracker["used_categories"][category] = tracker["used_categories"].get(category, 0) + 1
    
    tracker.setdefault("last_7_days_stories", []).append(title)
    if len(tracker["last_7_days_stories"]) > 14:
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
    print(f"✅ [record_story] Successfully recorded unique story: '{title}'")
    return True

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


