import datetime
from config import TIMEZONE
import pytz

def get_slot_info():
    """
    Returns (day_name, slot, category) based on current IST time.
    3 uploads per day (Morning 08:00 IST, Afternoon 13:00 IST, Evening 18:00 IST).
    """
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")  # Mon, Tue, etc.
    hour = ist_now.hour
    
    morning_categories = {
        "Mon": "🤖 AI Demystified & Future Tech",
        "Tue": "🤖 Practical AI Tools & Jobs",
        "Wed": "🤖 AI Demystified & Future Tech",
        "Thu": "🤖 Practical AI Tools & Jobs",
        "Fri": "🤖 AI Demystified & Future Tech",
        "Sat": "🤖 Practical AI Tools & Jobs",
        "Sun": "🤖 AI Demystified & Future Tech"
    }
    
    afternoon_categories = {
        "Mon": "🤖 Practical AI Tools & Jobs",
        "Tue": "🤖 Simple AI Hacks for Everyone",
        "Wed": "🤖 Practical AI Tools & Jobs",
        "Thu": "🤖 Simple AI Hacks for Everyone",
        "Fri": "🤖 Practical AI Tools & Jobs",
        "Sat": "🤖 Simple AI Hacks for Everyone",
        "Sun": "🤖 Practical AI Tools & Jobs"
    }
    
    evening_categories = {
        "Mon": "🤖 Simple AI Hacks for Everyone",
        "Tue": "🤖 AI Demystified & Future Tech",
        "Wed": "🤖 Simple AI Hacks for Everyone",
        "Thu": "🤖 Practical AI Tools & Jobs",
        "Fri": "🤖 Simple AI Hacks for Everyone",
        "Sat": "🤖 Simple AI Hacks for Everyone",
        "Sun": "🤖 Simple AI Hacks for Everyone"
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = morning_categories.get(day_name, "🤖 AI Demystified & Future Tech")
    elif hour < 16:
        slot = "Slot B (Afternoon)"
        category = afternoon_categories.get(day_name, "🤖 Practical AI Tools & Jobs")
    else:
        slot = "Slot C (Evening)"
        category = evening_categories.get(day_name, "🤖 Simple AI Hacks for Everyone")
        
    # Load performance insights for dynamic strategy boosting
    import os
    import json
    
    insights_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "performance_insights.json")
    if os.path.exists(insights_path):
        try:
            with open(insights_path, 'r', encoding='utf-8') as f:
                insights = json.load(f)
                top_categories_raw = insights.get("top_categories", [])
                
                category_mapping = {
                    "simple_ai": "🤖 Simple AI Hacks for Everyone",
                    "practical_ai": "🤖 Practical AI Tools & Jobs",
                    "future_ai": "🤖 AI Demystified & Future Tech"
                }
                
                top_mapped = []
                for cat in top_categories_raw:
                    mapped = category_mapping.get(cat.lower().split()[0]) or category_mapping.get(cat.lower())
                    if not mapped:
                        for k, v in category_mapping.items():
                            if k in cat.lower() or cat.lower() in k:
                                mapped = v
                                break
                    if mapped and mapped not in top_mapped:
                        top_mapped.append(mapped)
                        
                top_mapped = [c for c in top_mapped if c.startswith("🤖")]
                if top_mapped and category not in top_mapped:
                    boosted_cat = top_mapped[0]
                    print(f"📈 [ecosystem] Boosting category priority: Overriding '{category}' with top-performer '{boosted_cat}'")
                    category = boosted_cat
        except Exception as e:
            print(f"⚠️ Failed to apply category boosting: {e}")
            
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "அறிவியல் & விண்வெளி ரகசியங்கள்! Science & Space Secrets!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "ஆச்சரியமான உண்மைகள்! Mind-Blowing Unknown Facts!"},
    "Slot C": {"name": "Simple Tips by VJ", "tagline": "தினசரி லைஃப் ஹேக்ஸ் & டிப்ஸ்! Daily Life Hacks & Tips!"},
}

def get_series_identity(slot):
    for key, val in SERIES_MAP.items():
        if key in slot:
            return val
    return {"name": "Simple Tips by VJ", "tagline": "தினசரி பயனுள்ள குறிப்புகள்! Simple & Useful Tips!"}

def get_category_prompt_enhancement(category, slot):
    """
    Returns specific instructions and formatting for the given Tamil infotainment category.
    """
    base_instructions = (
        "FOCUS: High curiosity gap, mind-blowing and true facts, or extremely viral daily hacks. The hook must immediately "
        "trigger curiosity or state a highly relatable daily convenience problem, promising a simple solution in Tanglish. "
        "Keep the tone friendly, conversational, and energetic (Tanglish).\n"
        "To get millions of views, start with a massive hook, keep script pacing fast, and end with a seamless loop back to the hook."
    )
    
    enhancements = {
        "🤖 AI Demystified & Future Tech": f"""
            {base_instructions}
            CATEGORY: AI Demystified & Future Tech
            GOAL: Demystify an AI concept (how neural nets work, how LLMs think, how deepfakes are made) or share a future tech update. Make it extremely simple for everyday Tamil people of all ages to understand. Keep it fascinating and highly visual to drive maximum views. Include tips on AI safety (e.g. avoiding audio/video deepfake scams). Connect the concept to something they already use daily (phone, Google, YouTube, ATM).
            VIRAL HOOK FOR COMMON PEOPLE: "Ungal phone camera-la irukura AI brain — ithu enna pannum theriyuma?"
            HOOK TEMPLATE (Tamil): "விஞ்ஞான உலகத்துல அடுத்ததா வரப்போற இந்த ஒரு மிரட்டலான AI விஷயம் பத்தி தெரியுமா?"
        """,
        "🤖 Practical AI Tools & Jobs": f"""
            {base_instructions}
            CATEGORY: Practical AI Tools & Jobs
            GOAL: Show students, job seekers, homemakers, and office workers how to use free AI tools (ChatGPT, Claude, Gamma, Google Gemini) to study, learn, automate tasks, earn money, or prepare for interviews. Focus on tools that even a non-tech person can use immediately. Pacing must be extremely practical and step-by-step.
            VIRAL HOOK FOR COMMON PEOPLE: "Intha free AI tool use panna, ungal kid homework 5 minutes-la mudiyum!"
            HOOK TEMPLATE (Tamil): "உங்க study அல்லது office work-ஐ 10 மடங்கு வேகமாக்க இந்த ஒரு free AI tool-ஐ உடனே use பண்ணுங்க..."
        """,
        "🤖 Simple AI Hacks for Everyone": f"""
            {base_instructions}
            CATEGORY: Simple AI Hacks for Everyone
            GOAL: Share simple AI features built into everyday tools like WhatsApp, Google search, keyboard apps, or phone settings (e.g. Google Lens, Live Translate, spam detection) that kids, parents, shopkeepers, and grandmas can easily use to make daily life simpler. Avoid ALL jargon. Explain like you're telling your neighborhood uncle.
            VIRAL HOOK FOR COMMON PEOPLE: "Ungal WhatsApp-la AI already irukku — ithu enna pannum theriyuma?"
            HOOK TEMPLATE (Tamil): "உங்க phone-ல WhatsApp-ல இருக்குற இந்த ஒரு ரகசிய AI feature பத்தி தெரியுமா?"
        """
    }
    
    return enhancements.get(category, enhancements.get("🤖 AI Demystified & Future Tech"))

# Curated Category Color Palette System
_CATEGORY_PALETTES = {
    "🤖 AI Demystified & Future Tech": {
        "name": "Electric Purple",
        "primary": (180, 80, 255),
        "secondary": (15, 10, 30),
        "caption_highlight": (200, 120, 255),
        "progress_bar": (180, 80, 255),
        "thumbnail_accent": (180, 80, 255),
        "emoji": "🤖",
    },
    "🤖 Practical AI Tools & Jobs": {
        "name": "Neon Cyan",
        "primary": (0, 255, 230),
        "secondary": (8, 25, 30),
        "caption_highlight": (80, 255, 240),
        "progress_bar": (0, 255, 230),
        "thumbnail_accent": (0, 255, 230),
        "emoji": "🤖",
    },
    "🤖 Simple AI Hacks for Everyone": {
        "name": "Bright Amber",
        "primary": (255, 170, 0),
        "secondary": (25, 15, 5),
        "caption_highlight": (255, 190, 50),
        "progress_bar": (255, 170, 0),
        "thumbnail_accent": (255, 170, 0),
        "emoji": "🤖",
    },
}

# Default palette
_DEFAULT_PALETTE = _CATEGORY_PALETTES["🤖 AI Demystified & Future Tech"]

def get_category_color_palette(category):
    """
    Returns the category-specific color palette dict.
    Falls back to Amazing Science & Space for unknown categories.
    """
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)

def get_session_length_cap():
    return None



