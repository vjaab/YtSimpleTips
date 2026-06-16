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
        "Mon": "💰 Finance Quick Tips",
        "Tue": "📱 Tech & AI Quick Facts",
        "Wed": "🚀 Motivation Bites",
        "Thu": "💰 Finance Quick Tips",
        "Fri": "📱 Tech & AI Quick Facts",
        "Sat": "🧠 Facts & Trivia",
        "Sun": "🛠️ How-To Tutorials"
    }
    
    afternoon_categories = {
        "Mon": "📱 Tech & AI Quick Facts",
        "Tue": "💰 Finance Quick Tips",
        "Wed": "🧠 Facts & Trivia",
        "Thu": "📱 Tech & AI Quick Facts",
        "Fri": "🚀 Motivation Bites",
        "Sat": "🛠️ How-To Tutorials",
        "Sun": "🤖 AI/ML Quick Learn"
    }
    
    evening_categories = {
        "Mon": "🚀 Motivation Bites",
        "Tue": "🛠️ How-To Tutorials",
        "Wed": "💰 Finance Quick Tips",
        "Thu": "🧠 Facts & Trivia",
        "Fri": "💰 Finance Quick Tips",
        "Sat": "📱 Tech & AI Quick Facts",
        "Sun": "🤖 AI/ML Quick Learn"
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = morning_categories.get(day_name, "💰 Finance Quick Tips")
    elif hour < 16:
        slot = "Slot B (Afternoon)"
        category = afternoon_categories.get(day_name, "📱 Tech & AI Quick Facts")
    else:
        slot = "Slot C (Evening)"
        category = evening_categories.get(day_name, "🚀 Motivation Bites")
        
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "தினசரி பயனுள்ள குறிப்புகள்! Simple & Useful Tips!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "சூப்பர் லைஃப் ஹேக்ஸ்! Life-Changing Hacks!"},
    "Slot C": {"name": "Simple Tips by VJ", "tagline": "இன்றைய டிரெண்டிங் டிப்! Today's Trending Tip!"},
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
    base_instructions = (
        "FOCUS: High utility, actionable value, and curiosity-inducing tips. The hook must immediately state a common problem "
        "and promise a simple solution in Tanglish. Keep the tone friendly and conversational (Tanglish).\n"
        "TARGET DEMOGRAPHICS & RETENTION:\n"
        "1. Young People (students/professionals): Focus on efficiency, speed, productivity hacks, and modern tools.\n"
        "2. Middle-aged (working class): Focus on daily utility, phone settings, WhatsApp/UPI security, time-saving, and stress reduction.\n"
        "3. Parents: Focus on kid's screen safety, money-saving, household convenience, smart parenting, and home automation.\n"
        "To get millions of views, start with a highly emotional, relatable problem hook and end with a seamless retention loop."
    )
    
    enhancements = {
        "💰 Finance Quick Tips": f"""
            {base_instructions}
            CATEGORY: Finance Quick Tips
            GOAL: Give actionable money-saving hacks, stock tips, investment facts, or crypto news. Prefer tech-related financial safety tips or wealth building hacks.
            HOOK TEMPLATE (Tamil): "உங்க பணத்தை சேமிக்க இந்த ஒரு 50/30/20 rule-ஐ follow பண்ணுங்க..."
        """,
        "📱 Tech & AI Quick Facts": f"""
            {base_instructions}
            CATEGORY: Tech & AI Quick Facts
            GOAL: Share AI tools, app tips, gadget facts, or tech news. Ensure it is highly actionable and surprising.
            HOOK TEMPLATE (Tamil): "உங்க phone-ல இருக்குற இந்த secret AI tool பத்தி உங்களுக்கு தெரியுமா?"
        """,
        "🚀 Motivation Bites": f"""
            {base_instructions}
            CATEGORY: Motivation Bites
            GOAL: Share 1-line quotes, success stories, or life lessons. Relate it to career success, tech entrepreneurship, or daily motivation.
            HOOK TEMPLATE (Tamil): "வாழ்க்கையில ஜெயிக்கணும்னு நினைக்கிறீங்களா? இந்த ஒரு விஷயத்தை மட்டும் follow பண்ணுங்க..."
        """,
        "🧠 Facts & Trivia": f"""
            {base_instructions}
            CATEGORY: Facts & Trivia
            GOAL: Share top 3-5 lists, mysterious facts, or quick knowledge bites. Keep it fast-paced and highly curious.
            HOOK TEMPLATE (Tamil): "உலகத்துலயே யாருக்கும் தெரியாத 3 facts பத்தி இன்னைக்கு பாக்க போறோம்..."
        """,
        "🛠️ How-To Tutorials": f"""
            {base_instructions}
            CATEGORY: How-To Tutorials
            GOAL: Provide quick tips, 1-minute tutorials, or skill hacks (e.g., excel shortcuts, daily life skills).
            HOOK TEMPLATE (Tamil): "Excel-ல 1 மணி நேரம் ஆகுற வேலையை 1 நிமிடத்துல முடிக்க இந்த shortcut-ஐ use பண்ணுங்க..."
        """,
        "🤖 AI/ML Quick Learn": f"""
            {base_instructions}
            CATEGORY: AI/ML Quick Learn
            GOAL: Explain AI concepts, ML tips, or coding hacks for a tech audience in 30-40 seconds. (e.g. Transformers, Python tricks).
            HOOK TEMPLATE (Tamil): "ChatGPT எப்படி வேலை செய்யுதுன்னு 30 seconds-ல புரிஞ்சிக்கலாமா?"
        """
    }
    
    return enhancements.get(category, enhancements.get("💰 Finance Quick Tips"))

# ── CATEGORY COLOR PALETTE SYSTEM ──────────────────────────────────────────────

# Each category has a curated color scheme for brand consistency
_CATEGORY_PALETTES = {
    "💰 Finance Quick Tips": {
        "name": "Ocean Blue",
        "primary": (0, 150, 255),
        "secondary": (10, 18, 35),
        "caption_highlight": (60, 180, 255),
        "progress_bar": (0, 150, 255),
        "thumbnail_accent": (0, 150, 255),
        "emoji": "💰",
    },
    "📱 Tech & AI Quick Facts": {
        "name": "Electric Cyan",
        "primary": (0, 212, 255),
        "secondary": (10, 22, 40),
        "caption_highlight": (0, 230, 255),
        "progress_bar": (0, 212, 255),
        "thumbnail_accent": (0, 200, 255),
        "emoji": "📱",
    },
    "🚀 Motivation Bites": {
        "name": "Hot Pink",
        "primary": (255, 0, 128),
        "secondary": (30, 10, 20),
        "caption_highlight": (255, 60, 160),
        "progress_bar": (255, 0, 128),
        "thumbnail_accent": (255, 0, 128),
        "emoji": "🚀",
    },
    "🧠 Facts & Trivia": {
        "name": "Warm Gold",
        "primary": (255, 184, 0),
        "secondary": (26, 16, 0),
        "caption_highlight": (255, 200, 40),
        "progress_bar": (255, 184, 0),
        "thumbnail_accent": (255, 184, 0),
        "emoji": "🧠",
    },
    "🛠️ How-To Tutorials": {
        "name": "Electric Lime",
        "primary": (204, 255, 0),
        "secondary": (15, 15, 10),
        "caption_highlight": (204, 255, 0),
        "progress_bar": (204, 255, 0),
        "thumbnail_accent": (204, 255, 0),
        "emoji": "🛠️",
    },
    "🤖 AI/ML Quick Learn": {
        "name": "Cosmic Purple",
        "primary": (179, 136, 255),
        "secondary": (13, 10, 26),
        "caption_highlight": (200, 160, 255),
        "progress_bar": (179, 136, 255),
        "thumbnail_accent": (179, 136, 255),
        "emoji": "🤖",
    }
}

# Default palette
_DEFAULT_PALETTE = _CATEGORY_PALETTES["💰 Finance Quick Tips"]

def get_category_color_palette(category):
    """
    Returns the category-specific color palette dict.
    Falls back to Finance Quick Tips for unknown categories.
    """
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)
