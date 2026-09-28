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
        "PACING: Rapid, punchy sentences (under 10 words). Use commas and ellipses for breathing pauses.\n"
        "CRITICAL UNIQUENESS: You MUST NEVER repeat previously covered facts or topics from the avoid list. "
        "Choose a completely novel, verified, unexpected phenomenon."
    )
    
    enhancements = {
        "🧠 Mind-Blowing Science Curiosities": f"""
            {base_instructions}
            CATEGORY: 🧠 Mind-Blowing Science Curiosities
            GOAL: Explain a mind-bending science fact that sounds completely fake or impossible, but is 100% verified.
            TOPICS: Sharks predate Saturn's rings, water triple point boiling and freezing at once, fulgurite lightning glass tubes, cosmic radiation television static, glass amorphous solid physics.
            VIRAL HOOK STYLE: State the impossible-sounding fact directly with shock.
        """,
        "🧬 Human Body & Dark Psychology": f"""
            {base_instructions}
            CATEGORY: 🧬 Human Body & Dark Psychology
            GOAL: Share a fascinating human body reaction, brain trick, sleep hack, or psychological behavior that viewers experience daily.
            TOPICS: Photic sneeze reflex from bright sunlight, Tetris effect visual dreams, phantom vibration syndrome, stomach acid mucus barrier, eye saccadic masking.
            VIRAL HOOK STYLE: Call out the exact daily phenomenon everyone experiences.
        """,
        "💰 Money-Saving & Smart Living Tricks": f"""
            {base_instructions}
            CATEGORY: 💰 Money-Saving & Smart Living Tricks
            GOAL: Deliver an immediate, actionable money-saving tip, hidden bank charge cancellation, electricity bill reducer, or consumer protection hack.
            TOPICS: Inverter AC compressor variable speed power savings, supermarket dairy placement psychology, credit card 50-day billing cycle float, sealing door air leaks.
            VIRAL HOOK STYLE: Immediate wallet saving or loss prevention.
        """,
        "🍳 Food, Health & Kitchen Science": f"""
            {base_instructions}
            CATEGORY: 🍳 Food, Health & Kitchen Science
            GOAL: Explain fascinating everyday food science, kitchen cooking hacks, or food adulteration tests that any family can try today.
            TOPICS: Fresh pineapple bromelain enzyme eating you back, raw cashew urushiol oil toxicity, coffee adenosine receptor blocking, searing meat flavor myth.
            VIRAL HOOK STYLE: Household test or eye-opening kitchen revelation.
        """,
        "🌍 Mysterious History & Culture Secrets": f"""
            {base_instructions}
            CATEGORY: 🌍 Mysterious History & Culture Secrets
            GOAL: Reveal a mind-blowing historical, archaeological, or architectural marvel from Tamil Nadu or ancient India.
            TOPICS: Keezhadi ancient civilization terracotta underground drainage, Delhi iron pillar 1600-year misawite rust resistance, Antikythera mechanism 2000-year analog computer.
            VIRAL HOOK STYLE: Ancient mystery that modern science is still studying.
        """,
        "🐾 Nature & Animal Oddities": f"""
            {base_instructions}
            CATEGORY: 🐾 Nature & Animal Oddities
            GOAL: Unveil an unbelievable animal ability, strange creature survival trick, or backyard nature wonder.
            TOPICS: Mantis shrimp punch cavitation speed, tardigrades space vacuum survival, sloths 40-minute underwater breath hold, woodpecker tongue concussion wrap.
            VIRAL HOOK STYLE: Unbelievable superpower in animals.
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



