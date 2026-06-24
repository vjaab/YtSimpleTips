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
        "Mon": "🧠 Amazing Science & Space",
        "Tue": "🧬 Biology & Human Body",
        "Wed": "⚡ Everyday Science Facts",
        "Thu": "🧠 Amazing Science & Space",
        "Fri": "🧬 Biology & Human Body",
        "Sat": "⚡ Everyday Science Facts",
        "Sun": "🧠 Amazing Science & Space"
    }
    
    afternoon_categories = {
        "Mon": "🏺 Mysteries & Unknown History",
        "Tue": "💡 Life Hacks & Smart Tips",
        "Wed": "🧬 Biology & Human Body",
        "Thu": "🏺 Mysteries & Unknown History",
        "Fri": "💡 Life Hacks & Smart Tips",
        "Sat": "🧠 Amazing Science & Space",
        "Sun": "🏺 Mysteries & Unknown History"
    }
    
    evening_categories = {
        "Mon": "📱 Tech & Smart Device Hacks",
        "Tue": "💰 Money & Wealth Secrets",
        "Wed": "💡 Life Hacks & Smart Tips",
        "Thu": "📱 Tech & Smart Device Hacks",
        "Fri": "💰 Money & Wealth Secrets",
        "Sat": "💡 Life Hacks & Smart Tips",
        "Sun": "🏺 Mysteries & Unknown History"
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = morning_categories.get(day_name, "🧠 Amazing Science & Space")
    elif hour < 16:
        slot = "Slot B (Afternoon)"
        category = afternoon_categories.get(day_name, "🏺 Mysteries & Unknown History")
    else:
        slot = "Slot C (Evening)"
        category = evening_categories.get(day_name, "📱 Tech & Smart Device Hacks")
        
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
                    "science": "🧠 Amazing Science & Space",
                    "biology": "🧬 Biology & Human Body",
                    "everyday": "⚡ Everyday Science Facts",
                    "mysteries": "🏺 Mysteries & Unknown History",
                    "life": "💡 Life Hacks & Smart Tips",
                    "tech": "📱 Tech & Smart Device Hacks",
                    "money": "💰 Money & Wealth Secrets"
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
        "🧠 Amazing Science & Space": f"""
            {base_instructions}
            CATEGORY: Amazing Science & Space
            GOAL: Share a mind-blowing, true scientific discovery, cosmic secret, or space fact. Keep it highly intriguing and generic.
            HOOK TEMPLATE (Tamil): "விண்வெளியில இருக்குற இந்த ஒரு விசித்திரமான ரகசியம் பத்தி உங்களுக்கு தெரியுமா?"
        """,
        "🧬 Biology & Human Body": f"""
            {base_instructions}
            CATEGORY: Biology & Human Body
            GOAL: Share an unbelievable biological mystery, human body function trivia, brain quirk, or psychology fact.
            HOOK TEMPLATE (Tamil): "நம்ம உடம்புல நடக்குற இந்த ஒரு விசித்திரமான விஷயம் பத்தி உங்களுக்கு தெரியுமா?"
        """,
        "⚡ Everyday Science Facts": f"""
            {base_instructions}
            CATEGORY: Everyday Science Facts
            GOAL: Explain the chemistry or physics behind a simple daily occurrence or DIY magic-style trick.
            HOOK TEMPLATE (Tamil): "நம்ம தினசரி வாழ்க்கையில நடக்குற இந்த விஷயத்துக்கு பின்னாடி இருக்கிற அறிவியல் தெரியுமா?"
        """,
        "🏺 Mysteries & Unknown History": f"""
            {base_instructions}
            CATEGORY: Mysteries & Unknown History
            GOAL: Expose an unsolved mystery, historical anomaly, or archeological discovery (e.g. Bermuda, Keeladi).
            HOOK TEMPLATE (Tamil): "வரலாற்றுல இதுவரைக்கும் யாராலும் தீர்க்க முடியாத இந்த ஒரு மர்மம் பத்தி தெரியுமா?"
        """,
        "💡 Life Hacks & Smart Tips": f"""
            {base_instructions}
            CATEGORY: Life Hacks & Smart Tips
            GOAL: Provide quick, life-simplifying tips (e.g., kitchen hacks, study hacks, daily life optimizations).
            HOOK TEMPLATE (Tamil): "உங்க தினசரி வேலையை 10 மடங்கு சுலபமாக்க இந்த ஒரு simple life hack-ஐ use பண்ணுங்க..."
        """,
        "📱 Tech & Smart Device Hacks": f"""
            {base_instructions}
            CATEGORY: Tech & Smart Device Hacks
            GOAL: Unveil hidden device settings, safety configurations, UPI tips, or useful app shortcuts.
            HOOK TEMPLATE (Tamil): "உங்க phone-ல இருக்கிற இந்த ஒரு secret setting-ஐ உடனே மாத்துங்க..."
        """,
        "💰 Money & Wealth Secrets": f"""
            {base_instructions}
            CATEGORY: Money & Wealth Secrets
            GOAL: Share smart wealth concepts, passive saving rules, or financial tricks (e.g., compound interest, roundups).
            HOOK TEMPLATE (Tamil): "உங்க பணத்தை சேமிக்க இந்த ஒரு simple money-saving hack-ஐ follow பண்ணுங்க..."
        """
    }
    
    return enhancements.get(category, enhancements.get("🧠 Amazing Science & Space"))

# Curated Category Color Palette System
_CATEGORY_PALETTES = {
    "🧠 Amazing Science & Space": {
        "name": "Warm Gold",
        "primary": (255, 184, 0),
        "secondary": (26, 16, 0),
        "caption_highlight": (255, 200, 40),
        "progress_bar": (255, 184, 0),
        "thumbnail_accent": (255, 184, 0),
        "emoji": "🧠",
    },
    "🧬 Biology & Human Body": {
        "name": "Hot Pink",
        "primary": (255, 0, 128),
        "secondary": (30, 10, 20),
        "caption_highlight": (255, 60, 160),
        "progress_bar": (255, 0, 128),
        "thumbnail_accent": (255, 0, 128),
        "emoji": "🧬",
    },
    "⚡ Everyday Science Facts": {
        "name": "Electric Cyan",
        "primary": (0, 212, 255),
        "secondary": (10, 22, 40),
        "caption_highlight": (0, 230, 255),
        "progress_bar": (0, 212, 255),
        "thumbnail_accent": (0, 200, 255),
        "emoji": "⚡",
    },
    "🏺 Mysteries & Unknown History": {
        "name": "Cosmic Purple",
        "primary": (179, 136, 255),
        "secondary": (13, 10, 26),
        "caption_highlight": (200, 160, 255),
        "progress_bar": (179, 136, 255),
        "thumbnail_accent": (179, 136, 255),
        "emoji": "🏺",
    },
    "💡 Life Hacks & Smart Tips": {
        "name": "Electric Lime",
        "primary": (204, 255, 0),
        "secondary": (15, 15, 10),
        "caption_highlight": (204, 255, 0),
        "progress_bar": (204, 255, 0),
        "thumbnail_accent": (204, 255, 0),
        "emoji": "💡",
    },
    "📱 Tech & Smart Device Hacks": {
        "name": "Ocean Blue",
        "primary": (0, 150, 255),
        "secondary": (10, 18, 35),
        "caption_highlight": (60, 180, 255),
        "progress_bar": (0, 150, 255),
        "thumbnail_accent": (0, 150, 255),
        "emoji": "📱",
    },
    "💰 Money & Wealth Secrets": {
        "name": "Emerald Green",
        "primary": (0, 230, 115),
        "secondary": (10, 25, 15),
        "caption_highlight": (0, 255, 128),
        "progress_bar": (0, 230, 115),
        "thumbnail_accent": (0, 230, 115),
        "emoji": "💰",
    }
}

# Default palette
_DEFAULT_PALETTE = _CATEGORY_PALETTES["🧠 Amazing Science & Space"]

def get_category_color_palette(category):
    """
    Returns the category-specific color palette dict.
    Falls back to Amazing Science & Space for unknown categories.
    """
    return _CATEGORY_PALETTES.get(category, _DEFAULT_PALETTE)

def get_session_length_cap():
    """
    Checks performance_insights.json. If the average script length of top performers 
    is under 60 words, returns 60, otherwise returns None.
    """
    import os
    import json
    insights_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "performance_insights.json")
    if os.path.exists(insights_path):
        try:
            with open(insights_path, 'r', encoding='utf-8') as f:
                insights = json.load(f)
                avg_len = insights.get("average_script_length", 60)
                if avg_len < 60:
                    return 60
        except Exception as e:
            print(f"⚠️ Failed to read performance_insights.json: {e}")
    return None
