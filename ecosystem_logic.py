import datetime
from config import TIMEZONE
import pytz

def get_slot_info():
    """
    Returns (day_name, slot, category) based on current IST time.
    2 uploads per day (Morning 08:00 IST, Evening 18:00 IST).
    Slot A (Morning) uses the daily rotating life tip category.
    Slot B (Evening) uses "🏠 Daily Life & Home Hacks".
    """
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")  # Mon, Tue, etc.
    hour = ist_now.hour
    
    daily_categories = {
        "Mon": "📱 Tech & Phone Hacks",        # Keyboard shortcuts, hidden phone features, productivity apps
        "Tue": "🧠 Study & Memory Tips",       # How to study fast, memorization tricks, focus techniques
        "Wed": "💊 Health & Body Hacks",       # Sleep hacks, posture tips, brain boosters, hydration tricks
        "Thu": "💰 Money & Finance Tips",      # Saving money hacks, smart shopping tips, compound interest simply
        "Fri": "🚀 Productivity & Time Tips",  # Time management hacks, procrastination solutions, focus tips
        "Sat": "🗣️ Communication & Social Hacks", # Body language tips, conversation starters, confidence hacks
        "Sun": "🏠 Daily Life & Home Hacks"     # Clever kitchen tricks, organization hacks, DIY life hacks
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = daily_categories.get(day_name, "🏠 Daily Life & Home Hacks")
    else:
        slot = "Slot B (Evening)"
        # Alternate category for evening slots to keep audience engaged
        evening_categories = {
            "Mon": "🏠 Daily Life & Home Hacks",
            "Tue": "📱 Tech & Phone Hacks",
            "Wed": "🧠 Study & Memory Tips",
            "Thu": "💊 Health & Body Hacks",
            "Fri": "💰 Money & Finance Tips",
            "Sat": "🚀 Productivity & Time Tips",
            "Sun": "🗣️ Communication & Social Hacks"
        }
        category = evening_categories.get(day_name, "🏠 Daily Life & Home Hacks")
        
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "தினசரி பயனுள்ள குறிப்புகள்! Simple & Useful Tips!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "சூப்பர் லைஃப் ஹேக்ஸ்! Life-Changing Hacks!"},
}

def get_series_identity(slot):
    for key, val in SERIES_MAP.items():
        if key in slot:
            return val
    return {"name": "Simple Tips by VJ", "tagline": "தினசரி பயனுள்ள குறிப்புகள்! Simple & Useful Tips!"}

def get_category_prompt_enhancement(category, slot):
    """
    Returns specific instructions and formatting for the given Tamil tip/hack category.
    """
    base_instructions = "FOCUS: High utility, actionable value, and curiosity-inducing tips. The hook must immediately state a common problem and promise a simple solution in Tanglish. Keep the tone friendly and conversational (Tanglish)."
    
    enhancements = {
        "📱 Tech & Phone Hacks": f"""
            {base_instructions}
            CATEGORY: Tech & Phone Hacks
            GOAL: Share an incredibly useful, actionable phone or laptop hack (shortcuts, hidden settings, clean-up tips) in simple Tanglish.
            HOOK TEMPLATE (Tamil): "உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க! உங்க phone speed-ஐ boost பண்ண ஒரு simple hack..."
        """,
        "🧠 Study & Memory Tips": f"""
            {base_instructions}
            CATEGORY: Study & Memory Tips
            GOAL: Share a scientific study tip, concentration hack, or memory trick (e.g., Feynman technique, Pomodoro, active recall) in Tamil/Tanglish.
            HOOK TEMPLATE (Tamil): "எந்த ஒரு விஷயத்தையும் 10 மடங்கு வேகமா மனப்பாடம் பண்ண இந்த ஒரு science trick-ஐ follow பண்ணுங்க..."
        """,
        "💊 Health & Body Hacks": f"""
            {base_instructions}
            CATEGORY: Health & Body Hacks
            GOAL: Share an actionable wellness, posture, sleep, or energy hack (e.g., military sleep method, eye relief rule, hydration hacks).
            HOOK TEMPLATE (Tamil): "அடுத்த 2 நிமிடத்துல தூங்கணுமா? US military யூஸ் பண்ற இந்த simple hack-ஐ ட்ரை பண்ணுங்க..."
        """,
        "💰 Money & Finance Tips": f"""
            {base_instructions}
            CATEGORY: Money & Finance Tips
            GOAL: Give actionable money-saving hacks, smart shopping rules, or simple concepts to grow wealth.
            HOOK TEMPLATE (Tamil): "உங்க பணத்தை சேமிக்க இந்த ஒரு 50/30/20 rule-ஐ follow பண்ணுங்க! உங்க savings-ஐ double பண்ண ஒரு simple hack..."
        """,
        "🚀 Productivity & Time Tips": f"""
            {base_instructions}
            CATEGORY: Productivity & Time Tips
            GOAL: Provide actionable productivity routines, how to beat procrastination, or manage time effectively.
            HOOK TEMPLATE (Tamil): "Procrastination-ஐ 5 வினாடியில நிறுத்த இந்த ஒரு simple rule-ஐ follow பண்ணுங்க..."
        """,
        "🗣️ Communication & Social Hacks": f"""
            {base_instructions}
            CATEGORY: Communication & Social Hacks
            GOAL: Share communication hacks, body language tricks, confidence tips, or conversation starters.
            HOOK TEMPLATE (Tamil): "யார் கூட பேசினாலும் உங்க மேல ஒரு நல்ல impression வர இந்த ஒரு body language hack-ஐ follow பண்ணுங்க..."
        """,
        "🏠 Daily Life & Home Hacks": f"""
            {base_instructions}
            CATEGORY: Daily Life & Home Hacks
            GOAL: Share clever household organization hacks, clean-up shortcuts, kitchen tricks, or DIY solutions.
            HOOK TEMPLATE (Tamil): "உங்க வீட்ல இருக்குற இந்த ஒரு பொருளை வச்சு, இந்த பெரிய தொல்லையை ஈஸியா தீர்க்கலாம்..."
        """
    }
    
    return enhancements.get(category, enhancements.get("🏠 Daily Life & Home Hacks"))

# ── CATEGORY COLOR PALETTE SYSTEM ──────────────────────────────────────────────

# Each category has a curated color scheme for brand consistency
_CATEGORY_PALETTES = {
    "📱 Tech & Phone Hacks": {
        "name": "Electric Cyan",
        "primary": (0, 212, 255),        # Main accent color
        "secondary": (10, 22, 40),       # Dark background tint
        "caption_highlight": (0, 230, 255),  # Active word highlight
        "progress_bar": (0, 212, 255),
        "thumbnail_accent": (0, 200, 255),
        "emoji": "📱",
    },
    "🧠 Study & Memory Tips": {
        "name": "Warm Gold",
        "primary": (255, 184, 0),
        "secondary": (26, 16, 0),
        "caption_highlight": (255, 200, 40),
        "progress_bar": (255, 184, 0),
        "thumbnail_accent": (255, 184, 0),
        "emoji": "🧠",
    },
    "💊 Health & Body Hacks": {
        "name": "Neon Mint",
        "primary": (0, 255, 136),
        "secondary": (13, 31, 13),
        "caption_highlight": (50, 255, 160),
        "progress_bar": (0, 255, 136),
        "thumbnail_accent": (0, 230, 120),
        "emoji": "💊",
    },
    "💰 Money & Finance Tips": {
        "name": "Ocean Blue",
        "primary": (0, 150, 255),
        "secondary": (10, 18, 35),
        "caption_highlight": (60, 180, 255),
        "progress_bar": (0, 150, 255),
        "thumbnail_accent": (0, 150, 255),
        "emoji": "💰",
    },
    "🚀 Productivity & Time Tips": {
        "name": "Hot Pink",
        "primary": (255, 0, 128),
        "secondary": (30, 10, 20),
        "caption_highlight": (255, 60, 160),
        "progress_bar": (255, 0, 128),
        "thumbnail_accent": (255, 0, 128),
        "emoji": "🚀",
    },
    "🗣️ Communication & Social Hacks": {
        "name": "Cosmic Purple",
        "primary": (179, 136, 255),
        "secondary": (13, 10, 26),
        "caption_highlight": (200, 160, 255),
        "progress_bar": (179, 136, 255),
        "thumbnail_accent": (179, 136, 255),
        "emoji": "🗣️",
    },
    "🏠 Daily Life & Home Hacks": {
        "name": "Electric Lime",
        "primary": (204, 255, 0),
        "secondary": (15, 15, 10),
        "caption_highlight": (204, 255, 0),
        "progress_bar": (204, 255, 0),
        "thumbnail_accent": (204, 255, 0),
        "emoji": "🏠",
    },
}

# Default palette (Electric Lime — original brand color)
_DEFAULT_PALETTE = _CATEGORY_PALETTES["🏠 Daily Life & Home Hacks"]

def get_category_color_palette(category):
    """
    Returns the category-specific color palette dict.
    Falls back to Electric Lime (the original brand color) for unknown categories.
    """
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)
