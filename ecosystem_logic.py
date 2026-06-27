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
        "Tue": "🤖 AI Demystified & Future Tech",
        "Wed": "⚡ Everyday Science Facts",
        "Thu": "🧠 Amazing Science & Space",
        "Fri": "🤖 AI Demystified & Future Tech",
        "Sat": "⚡ Everyday Science Facts",
        "Sun": "🤖 AI Demystified & Future Tech"
    }
    
    afternoon_categories = {
        "Mon": "🏺 Mysteries & Unknown History",
        "Tue": "💡 Life Hacks & Smart Tips",
        "Wed": "🤖 Practical AI Tools & Jobs",
        "Thu": "🏺 Mysteries & Unknown History",
        "Fri": "💡 Life Hacks & Smart Tips",
        "Sat": "🤖 Practical AI Tools & Jobs",
        "Sun": "🤖 Practical AI Tools & Jobs"
    }
    
    evening_categories = {
        "Mon": "🤖 Simple AI Hacks for Everyone",
        "Tue": "💰 Money & Wealth Secrets",
        "Wed": "💡 Life Hacks & Smart Tips",
        "Thu": "🤖 Simple AI Hacks for Everyone",
        "Fri": "💰 Money & Wealth Secrets",
        "Sat": "🤖 Simple AI Hacks for Everyone",
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
                    "money": "💰 Money & Wealth Secrets",
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
            GOAL: Demystify an AI concept (how neural nets work, how LLMs think, how deepfakes are made) or share a future tech update. Make it extremely simple for everyday Tamil people of all ages to understand. Keep it fascinating and highly visual to drive maximum views. Include tips on AI safety (e.g. avoiding audio/video deepfake scams).
            HOOK TEMPLATE (Tamil): "விஞ்ஞான உலகத்துல அடுத்ததா வரப்போற இந்த ஒரு மிரட்டலான AI விஷயம் பத்தி தெரியுமா?"
        """,
        "🤖 Practical AI Tools & Jobs": f"""
            {base_instructions}
            CATEGORY: Practical AI Tools & Jobs
            GOAL: Show students, job seekers, and office workers how to use free AI tools (ChatGPT, Claude, Gamma, slides AI) to write, learn, automate tasks, or prepare for interviews. Pacing must be extremely practical and step-by-step.
            HOOK TEMPLATE (Tamil): "உங்க study அல்லது office work-ஐ 10 மடங்கு வேகமாக்க இந்த ஒரு free AI tool-ஐ உடனே use பண்ணுங்க..."
        """,
        "🤖 Simple AI Hacks for Everyone": f"""
            {base_instructions}
            CATEGORY: Simple AI Hacks for Everyone
            GOAL: Share simple AI features built into everyday tools like WhatsApp, Google search, keyboard apps, or phone settings (e.g. Google Lens, Live Translate) that kids, parents, and grandmas can easily use to make daily life simpler. Avoid all jargon.
            HOOK TEMPLATE (Tamil): "உங்க phone-ல WhatsApp-ல இருக்குற இந்த ஒரு ரகசிய AI feature பத்தி தெரியுமா?"
        """,
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
    return None



