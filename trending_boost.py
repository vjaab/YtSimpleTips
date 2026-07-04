"""
trending_boost.py — Lightweight Trending Signal Integration for Simple Tips by VJ.
Fetches trending signals from YouTube Shorts and Reddit to cross-reference with
Gemini Search Grounding results, boosting topics that align with current trends.
"""

import os
import re
import time
import requests
from datetime import datetime, timedelta, timezone

# Optional API keys — trending features are best-effort
YOUTUBE_DATA_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")


def _fetch_youtube_trending_keywords(category="tech tips"):
    """Fetches trending keywords from high-performing YouTube Shorts in the last 48h."""
    if not YOUTUBE_DATA_API_KEY:
        return []

    search_queries = {
        "🤖 AI Demystified & Future Tech": ["AI explained simple", "how AI works daily life", "AI future technology 2026", "deepfake detection tips"],
        "🤖 Practical AI Tools & Jobs": ["free AI tools for students", "AI tools for office work", "ChatGPT tricks beginners", "AI job skills 2026"],
        "🤖 Simple AI Hacks for Everyone": ["WhatsApp AI features", "Google Lens AI tricks", "phone AI hidden settings", "AI apps for parents"],
    }

    queries = search_queries.get(category, ["tech tips hidden features", "finance hacks"])
    trending_keywords = []

    for query in queries[:2]:  # Limit to 2 queries to save API quota
        try:
            published_after = (datetime.now(timezone.utc) - timedelta(hours=48)).strftime("%Y-%m-%dT%H:%M:%SZ")
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": query,
                "type": "video",
                "videoDuration": "short",
                "order": "viewCount",
                "publishedAfter": published_after,
                "maxResults": 5,
                "key": YOUTUBE_DATA_API_KEY,
                "relevanceLanguage": "en"
            }

            r = requests.get(url, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("items", []):
                    title = item.get("snippet", {}).get("title", "")
                    # Extract meaningful keywords from titles
                    words = re.findall(r'[A-Za-z]{3,}', title.lower())
                    trending_keywords.extend(words)
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ [trending_boost] YouTube keyword fetch failed: {e}")

    # Deduplicate and remove common stopwords
    stopwords = {"the", "this", "that", "with", "from", "what", "how", "why", "for", "and", "you", "your",
                 "are", "not", "can", "will", "all", "has", "have", "but", "just", "most", "new", "more",
                 "than", "get", "got", "use", "one", "two", "about", "video", "shorts", "short"}
    unique = list(set(w for w in trending_keywords if w not in stopwords))
    print(f"  📺 [trending_boost] Extracted {len(unique)} trending YouTube keywords")
    return unique[:20]


def _fetch_reddit_trending_keywords():
    """Fetches trending keywords from tech/tips subreddits using OAuth."""
    subreddits = ["LifeProTips", "Android", "iphone", "technology"]
    trending_keywords = []

    # Reddit API requires OAuth for reliable access
    if REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET:
        try:
            # Obtain OAuth token
            auth = requests.auth.HTTPBasicAuth(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)
            token_data = {"grant_type": "client_credentials"}
            token_headers = {"User-Agent": "SimpleTipsByVJ/1.0"}
            token_resp = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth, data=token_data, headers=token_headers, timeout=10
            )
            if token_resp.status_code != 200:
                print(f"  ⚠️ [trending_boost] Reddit OAuth token failed: {token_resp.status_code}")
                return []
            access_token = token_resp.json().get("access_token", "")
            if not access_token:
                print("  ⚠️ [trending_boost] Reddit OAuth returned empty token")
                return []
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "SimpleTipsByVJ/1.0"
            }
            
            for sub in subreddits[:2]:
                try:
                    url = f"https://oauth.reddit.com/r/{sub}/hot?limit=10"
                    r = requests.get(url, headers=headers, timeout=10)
                    if r.status_code == 200:
                        data = r.json()
                        for post in data.get("data", {}).get("children", []):
                            title = post.get("data", {}).get("title", "")
                            words = re.findall(r'[A-Za-z]{3,}', title.lower())
                            trending_keywords.extend(words)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ [trending_boost] Reddit fetch failed for r/{sub}: {e}")
        except Exception as e:
            print(f"  ⚠️ [trending_boost] Reddit OAuth setup failed: {e}")
    else:
        # Fallback: try unauthenticated (may return limited results)
        headers = {"User-Agent": "SimpleTipsByVJ/1.0"}
        for sub in subreddits[:2]:
            try:
                url = f"https://www.reddit.com/r/{sub}/hot.json?limit=10"
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    data = r.json()
                    for post in data.get("data", {}).get("children", []):
                        title = post.get("data", {}).get("title", "")
                        words = re.findall(r'[A-Za-z]{3,}', title.lower())
                        trending_keywords.extend(words)
                time.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ [trending_boost] Reddit fetch failed for r/{sub}: {e}")

    stopwords = {"the", "this", "that", "with", "from", "what", "how", "why", "for", "and", "you", "your",
                 "are", "not", "can", "will", "all", "has", "have", "but", "just", "most", "new", "more"}
    unique = list(set(w for w in trending_keywords if w not in stopwords))
    print(f"  🔴 [trending_boost] Extracted {len(unique)} trending Reddit keywords")
    return unique[:20]


def get_trending_context(category="🧠 Amazing Science & Space"):
    """
    Returns a formatted string of trending keywords and topics that can be
    injected into the Gemini Search Grounding query for higher relevance.
    """
    print("🔥 [trending_boost] Fetching real-time trending signals...")
    all_keywords = []

    try:
        yt_keywords = _fetch_youtube_trending_keywords(category)
        all_keywords.extend(yt_keywords)
    except Exception as e:
        print(f"  ⚠️ YouTube trending skipped: {e}")

    try:
        reddit_keywords = _fetch_reddit_trending_keywords()
        all_keywords.extend(reddit_keywords)
    except Exception as e:
        print(f"  ⚠️ Reddit trending skipped: {e}")

    if not all_keywords:
        print("  ℹ️ [trending_boost] No trending signals available. Using base topics only.")
        return ""

    # Count frequency to find strongest signals
    from collections import Counter
    freq = Counter(all_keywords)
    top_keywords = [kw for kw, count in freq.most_common(10)]

    context = f"TRENDING TOPICS RIGHT NOW: {', '.join(top_keywords)}"
    print(f"  🔥 [trending_boost] Top trending keywords: {', '.join(top_keywords[:5])}")
    return context


def boost_articles_with_trending(articles, category="🧠 Amazing Science & Space"):
    """
    Cross-references fetched articles/facts with trending signals.
    Articles matching trending keywords get a 2x priority boost.
    Returns the re-sorted articles list.
    """
    trending_context = get_trending_context(category)
    if not trending_context:
        return articles

    # Extract trending keywords
    trending_keywords = set(re.findall(r'[A-Za-z]{3,}', trending_context.lower()))

    for art in articles:
        title = art.get("title", "").lower()
        desc = art.get("description", "").lower()
        combined = title + " " + desc

        # Count keyword matches
        matches = sum(1 for kw in trending_keywords if kw in combined)

        if matches >= 2:
            art["_trending_boost"] = True
            art["_trending_matches"] = matches
            print(f"  🔥 Trending boost applied to: {art.get('title', '')[:50]}... ({matches} keyword matches)")

    # Sort: trending-boosted articles first, then by original order
    boosted = [a for a in articles if a.get("_trending_boost")]
    non_boosted = [a for a in articles if not a.get("_trending_boost")]

    return boosted + non_boosted
