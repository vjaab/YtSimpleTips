import datetime
from config import TIMEZONE
import pytz

def get_slot_info():
    """
    Returns (day_name, slot, category) based on current IST time.
    3 uploads per day (Morning 08:00 IST, Afternoon 13:00 IST, Evening 18:00 IST).
    Heavily weighted toward Tech & Phone Hacks for maximum viral potential.
    """
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")  # Mon, Tue, etc.
    hour = ist_now.hour
    
    # Morning slot: Tech-heavy (5/7 days = Tech)
    morning_categories = {
        "Mon": "📱 Tech & Phone Hacks",
        "Tue": "📱 Tech & Phone Hacks",
        "Wed": "📱 Tech & Phone Hacks",
        "Thu": "💰 Money & Finance Tips",
        "Fri": "📱 Tech & Phone Hacks",
        "Sat": "📱 Tech & Phone Hacks",
        "Sun": "🏠 Daily Life & Home Hacks"
    }
    
    # Afternoon slot: Variety + Trending Reaction
    afternoon_categories = {
        "Mon": "🔥 Trending Reaction",
        "Tue": "🧠 Study & Memory Tips",
        "Wed": "🔥 Trending Reaction",
        "Thu": "📱 Tech & Phone Hacks",
        "Fri": "🔥 Trending Reaction",
        "Sat": "🏅 Sports & Fitness Tips",
        "Sun": "🗣️ Communication & Social Hacks"
    }
    
    # Evening slot: Tech + secondary variety
    evening_categories = {
        "Mon": "📱 Tech & Phone Hacks",
        "Tue": "📱 Tech & Phone Hacks",
        "Wed": "🧠 Study & Memory Tips",
        "Thu": "📱 Tech & Phone Hacks",
        "Fri": "💰 Money & Finance Tips",
        "Sat": "📱 Tech & Phone Hacks",
        "Sun": "🗣️ Communication & Social Hacks"
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = morning_categories.get(day_name, "📱 Tech & Phone Hacks")
    elif hour < 16:
        slot = "Slot B (Afternoon)"
        category = afternoon_categories.get(day_name, "📱 Tech & Phone Hacks")
    else:
        slot = "Slot C (Evening)"
        category = evening_categories.get(day_name, "📱 Tech & Phone Hacks")
        
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
        "📱 Tech & Phone Hacks": f"""
            {base_instructions}
            CATEGORY: Tech & Phone Hacks
            GOAL: Share a game-changing, hidden setting, app shortcut, or trick on Android/iOS/Windows/Mac. Ensure it is highly actionable for at least two demographics (e.g., parents locking screen for kids, young people boosting gaming speed, or middle-aged blocking spam/scams).
            HOOK TEMPLATE (Tamil): "உங்க phone-ல இந்த secret setting-ஐ உடனே மாத்துங்க! உங்க phone speed-ஐ boost பண்ண ஒரு simple hack..."
        """,
        "🧠 Study & Memory Tips": f"""
            {base_instructions}
            CATEGORY: Study & Memory Tips
            GOAL: Share a highly effective, scientifically-backed study tip, concentration hack, or memory technique (e.g. Feynman method, active recall, AI study tools). Frame it to be useful for young students as well as parents trying to help their kids study better.
            HOOK TEMPLATE (Tamil): "எந்த ஒரு விஷயத்தையும் 10 மடங்கு வேகமா மனப்பாடம் பண்ண இந்த ஒரு science trick-ஐ follow பண்ணுங்க..."
        """,
        "💊 Health & Body Hacks": f"""
            {base_instructions}
            CATEGORY: Health & Body Hacks
            GOAL: Share an actionable physical/mental health hack. Prefer tech-infused tips (e.g., screen glare eye-relief apps, smart posture trackers) or high-impact wellness habits (military sleep method, hydration hacks) that apply to young geeks, working parents, or middle-aged people feeling tired.
            HOOK TEMPLATE (Tamil): "அடுத்த 2 நிமிடத்துல தூங்கணுமா? US military யூஸ் பண்ற இந்த simple hack-ஐ ட்ரை பண்ணுங்க..."
        """,
        "💰 Money & Finance Tips": f"""
            {base_instructions}
            CATEGORY: Money & Finance Tips
            GOAL: Give actionable money-saving hacks, smart shopping rules, or simple wealth tips. Prefer tech-related financial safety tips (e.g., UPI fraud prevention, auto-subscription cancels, budget apps) that protect middle-aged folks, save money for parents, and build wealth for youth.
            HOOK TEMPLATE (Tamil): "உங்க பணத்தை சேமிக்க இந்த ஒரு 50/30/20 rule-ஐ follow பண்ணுங்க! உங்க savings-ஐ double பண்ண ஒரு simple hack..."
        """,
        "🚀 Productivity & Time Tips": f"""
            {base_instructions}
            CATEGORY: Productivity & Time Tips
            GOAL: Provide actionable productivity routines, focus techniques, or time management hacks. Highlight how apps or smart settings (e.g. Do Not Disturb setup, screen time limits) help youth focus, middle-aged manage work-life balance, and parents regain free time.
            HOOK TEMPLATE (Tamil): "Procrastination-ஐ 5 வினாடியில நிறுத்த இந்த ஒரு simple rule-ஐ follow பண்ணுங்க..."
        """,
        "🗣️ Communication & Social Hacks": f"""
            {base_instructions}
            CATEGORY: Communication & Social Hacks
            GOAL: Share psychological triggers, body language hacks, or communication tricks. Relate it to interview success for youth, office politics for middle-aged, or managing family conversations for parents.
            HOOK TEMPLATE (Tamil): "யார் கூட பேசினாலும் உங்க மேல ஒரு நல்ல impression வர இந்த ஒரு body language hack-ஐ follow பண்ணுங்க..."
        """,
        "🏠 Daily Life & Home Hacks": f"""
            {base_instructions}
            CATEGORY: Daily Life & Home Hacks
            GOAL: Share clever household organization hacks, clean-up shortcuts, kitchen tricks, or DIY solutions. Blend in smart home gadget tips or appliance settings that save energy and time for parents and middle-aged homeowners.
            HOOK TEMPLATE (Tamil): "உங்க வீட்ல இருக்குற இந்த ஒரு பொருளை வச்சு, இந்த பெரிய தொல்லையை ஈஸியா தீர்க்கலாம்..."
        """,
        "🔥 Trending Reaction": f"""
            {base_instructions}
            CATEGORY: Trending Reaction
            GOAL: React to whatever is trending RIGHT NOW in India — a new phone feature, app update, viral tech news, or social media controversy. Ride the existing search volume wave. The tip MUST be timely and reference the trending topic directly. This category has the highest viral potential because it piggybacks on existing search demand.
            HOOK TEMPLATE (Tamil): "இன்னைக்கு India-வே இதை பத்தி பேசுது... உங்களுக்கு இது தெரியுமா?"
        """,
        "🏅 Sports & Fitness Tips": f"""
            {base_instructions}
            CATEGORY: Sports & Fitness Tips
            GOAL: Share an actionable physical fitness, sports technique, or recovery hack. Prefer tips that anyone can apply, like athletic recovery tricks, stamina building, or simple sports science hacks that apply to youth playing sports, middle-aged wanting fitness, or parents managing kids' health.
            HOOK TEMPLATE (Tamil): "விளையாடும் போது சீக்கிரம் டயர்ட் ஆகுறீங்களா? Sports players use பண்ற இந்த simple hack-ஐ ட்ரை பண்ணுங்க..."
        """
    }
    
    return enhancements.get(category, enhancements.get("📱 Tech & Phone Hacks"))

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
    "🔥 Trending Reaction": {
        "name": "Fire Orange",
        "primary": (255, 100, 0),
        "secondary": (30, 12, 0),
        "caption_highlight": (255, 140, 40),
        "progress_bar": (255, 100, 0),
        "thumbnail_accent": (255, 100, 0),
        "emoji": "🔥",
    },
    "🏅 Sports & Fitness Tips": {
        "name": "Athletic Red",
        "primary": (255, 50, 50),
        "secondary": (30, 10, 10),
        "caption_highlight": (255, 100, 100),
        "progress_bar": (255, 50, 50),
        "thumbnail_accent": (255, 50, 50),
        "emoji": "🏅",
    },
}

# Default palette (Electric Cyan — optimized for tech-heavy content)
_DEFAULT_PALETTE = _CATEGORY_PALETTES["📱 Tech & Phone Hacks"]

def get_category_color_palette(category):
    """
    Returns the category-specific color palette dict.
    Falls back to Electric Cyan (tech-focused brand color) for unknown categories.
    """
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)
