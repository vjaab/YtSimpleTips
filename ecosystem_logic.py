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
        "Mon": "🧠 Mind-Blowing Science Curiosities",
        "Tue": "🧬 Human Body & Dark Psychology",
        "Wed": "💰 Money-Saving & Smart Living Tricks",
        "Thu": "🍳 Food, Health & Kitchen Science",
        "Fri": "🌍 Mysterious History & Culture Secrets",
        "Sat": "🐾 Nature & Animal Oddities",
        "Sun": "🧠 Mind-Blowing Science Curiosities"
    }
    
    afternoon_categories = {
        "Mon": "🧬 Human Body & Dark Psychology",
        "Tue": "💰 Money-Saving & Smart Living Tricks",
        "Wed": "🍳 Food, Health & Kitchen Science",
        "Thu": "🌍 Mysterious History & Culture Secrets",
        "Fri": "🐾 Nature & Animal Oddities",
        "Sat": "🧠 Mind-Blowing Science Curiosities",
        "Sun": "🧬 Human Body & Dark Psychology"
    }
    
    evening_categories = {
        "Mon": "💰 Money-Saving & Smart Living Tricks",
        "Tue": "🍳 Food, Health & Kitchen Science",
        "Wed": "🌍 Mysterious History & Culture Secrets",
        "Thu": "🐾 Nature & Animal Oddities",
        "Fri": "🧠 Mind-Blowing Science Curiosities",
        "Sat": "🧬 Human Body & Dark Psychology",
        "Sun": "💰 Money-Saving & Smart Living Tricks"
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = morning_categories.get(day_name, "🧠 Mind-Blowing Science Curiosities")
    elif hour < 16:
        slot = "Slot B (Afternoon)"
        category = afternoon_categories.get(day_name, "🧬 Human Body & Dark Psychology")
    else:
        slot = "Slot C (Evening)"
        category = evening_categories.get(day_name, "💰 Money-Saving & Smart Living Tricks")
        
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "அறிவியல் & இயற்கை ஆச்சரியங்கள்! Science & Nature Wonders!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "மனித உடல் & மன மர்மங்கள்! Human Body & Mind Mysteries!"},
    "Slot C": {"name": "Simple Tips by VJ", "tagline": "பணம் சேமிப்பு & வீட்டு குறிப்புகள்! Money & Smart Life Hacks!"},
}

def get_series_identity(slot):
    for key, val in SERIES_MAP.items():
        if key in slot:
            return val
    return {"name": "Simple Tips by VJ", "tagline": "தினசரி பயனுள்ள குறிப்புகள்! Simple & Useful Tips!"}

def get_category_prompt_enhancement(category, slot):
    """
    Returns specific instructions and viral formatting for the given high-yield Tamil infotainment category.
    """
    base_instructions = (
        "FOCUS: High curiosity gap, mind-blowing and verified facts, or extremely high-utility daily hacks.\n"
        "HOOK RULE: Start with the shocking result, pain point, or mind-bending question in the first 2 seconds. "
        "NO robotic clichés (BAN: 'Oru vishayam theriyuma?', 'Intha video-la...', 'Nee yaarukkum theriyadhu...').\n"
        "TONE: Energetic, friendly, conversational elder-brother/friend (VJ style). Spoken Tamil with natural English terms.\n"
        "PACING: Rapid, punchy sentences (under 10 words). Use commas and ellipses for breathing pauses."
    )
    
    enhancements = {
        "🧠 Mind-Blowing Science Curiosities": f"""
            {base_instructions}
            CATEGORY: 🧠 Mind-Blowing Science Curiosities
            GOAL: Explain a mind-bending science fact that sounds completely fake or impossible, but is 100% verified.
            TOPICS: Ancient edible honey, ocean waters not mixing, earth spinning stop anomaly, speed of light, microwave invention accident, sound in space.
            VIRAL HOOK STYLE: State the impossible-sounding fact directly with shock:
            Example: "3000 வருஷம் பழமையான தேனை இன்னமும் கெட்டுப்போகாம சாப்பிட முடியுமா? அட ஆமாங்க!"
        """,
        "🧬 Human Body & Dark Psychology": f"""
            {base_instructions}
            CATEGORY: 🧬 Human Body & Dark Psychology
            GOAL: Share a fascinating human body reaction, brain trick, sleep hack, or psychological behavior that viewers experience daily.
            TOPICS: Why we forget why we entered a room (doorway effect), 3-second lie detection hack, why songs get stuck in your head, sleep cycle trick, goosebumps science.
            VIRAL HOOK STYLE: Call out the exact daily phenomenon everyone experiences:
            Example: "ஒரு ரூம்க்குள்ள நுழைஞ்ச உடனே எதுக்கு வந்தோம்னு மூளைக்கு மறந்து போகுதா? இதுக்கு பின்னாடி ஒரு செம சயின்ஸ் இருக்கு!"
        """,
        "💰 Money-Saving & Smart Living Tricks": f"""
            {base_instructions}
            CATEGORY: 💰 Money-Saving & Smart Living Tricks
            GOAL: Deliver an immediate, actionable money-saving tip, hidden bank charge cancellation, electricity bill reducer, or consumer protection hack.
            TOPICS: 40% electricity bill reduction, hidden bank SMS/ATM charges you can turn off, fake gold detection at home, petrol pump cheat prevention, free government welfare schemes.
            VIRAL HOOK STYLE: Immediate wallet saving or loss prevention:
            Example: "உங்க கரண்ட் பில்லை 40% வரைக்கும் குறைக்க இந்த ஒரு சின்ன பழக்கத்தை மாத்துங்க போதும்!"
        """,
        "🍳 Food, Health & Kitchen Science": f"""
            {base_instructions}
            CATEGORY: 🍳 Food, Health & Kitchen Science
            GOAL: Explain fascinating everyday food science, kitchen cooking hacks, or food adulteration tests that any family can try today.
            TOPICS: 1-drop milk adulteration test, why onions make you cry and the spoon hack to stop it, pressure cooker 4x speed science, drinking water standing myth, fermentation secrets.
            VIRAL HOOK STYLE: Household test or eye-opening kitchen revelation:
            Example: "நீங்க குடிக்கிற பால்ல கலப்படம் இருக்கான்னு வெறும் 1 சொட்டு தண்ணில ஈஸியா கண்டுபிடிச்சிடலாம்!"
        """,
        "🌍 Mysterious History & Culture Secrets": f"""
            {base_instructions}
            CATEGORY: 🌍 Mysterious History & Culture Secrets
            GOAL: Reveal a mind-blowing historical, archaeological, or architectural marvel from Tamil Nadu or ancient India.
            TOPICS: Brihadeeswarar Temple shadow & engineering mystery, Keezhadi ancient civilization water drainage, Kumari Kandam facts, Chettinad houses natural cooling, floating stones of Rameshwaram.
            VIRAL HOOK STYLE: Ancient mystery that modern science is still studying:
            Example: "1000 வருஷத்துக்கு முன்னாடி எந்த சிமெண்ட்டும் இல்லாம கட்டப்பட்ட தஞ்சை பெரிய கோவில் நிழல் தரையில விழாதா? உண்மை என்ன தெரியுமா?"
        """,
        "🐾 Nature & Animal Oddities": f"""
            {base_instructions}
            CATEGORY: 🐾 Nature & Animal Oddities
            GOAL: Unveil an unbelievable animal ability, strange creature survival trick, or backyard nature wonder.
            TOPICS: Crows remember human faces for life, octopus with 3 hearts and blue blood, the immortal jellyfish, trees communicating underground through fungal networks.
            VIRAL HOOK STYLE: Unbelievable superpower in animals:
            Example: "நம்ம வீட்டு வாசல்ல வர்ற காகத்துக்கு மனுஷங்களோட முகத்தை ஆயுசுக்கும் ஞாபகம் வச்சுக்கிற பவர் இருக்குன்னு சொன்னா நம்புவீங்களா?"
        """
    }
    
    return enhancements.get(category, enhancements.get("🧠 Mind-Blowing Science Curiosities"))

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



