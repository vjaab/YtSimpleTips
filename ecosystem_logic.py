import datetime
from config import TIMEZONE
import pytz

def get_slot_info():
    """
    Returns (day_name, slot, category) based on current IST time.
    2 uploads per day (Morning 08:00 IST, Evening 18:00 IST).
    Slot A (Morning) uses the daily rotating category.
    Slot B (Evening) uses "Random Amazing Facts" or "Fascinating Inventions".
    """
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")  # Mon, Tue, etc.
    hour = ist_now.hour
    
    daily_categories = {
        "Mon": "🧪 Science & Space",      # Black holes, DNA, quantum physics
        "Tue": "🏛️ History & Culture",   # Ancient Tamil history, world wonders
        "Wed": "💊 Health & Body",        # Why we yawn, brain facts, human body
        "Thu": "🌍 World & Geography",   # Oceans, strange countries, climate
        "Fri": "💻 Technology & AI",      # Internet, AI, futuristic tech
        "Sat": "🧠 Psychology & Mind",    # Brain tricks, illusions, memory
        "Sun": "🎲 Random Amazing Facts"   # Mind-blowing miscellaneous facts
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = daily_categories.get(day_name, "🎲 Random Amazing Facts")
    else:
        slot = "Slot B (Evening)"
        # Alternate category for evening slots to keep audience engaged
        evening_categories = {
            "Mon": "🎲 Random Amazing Facts",
            "Tue": "🧪 Science & Space",
            "Wed": "🏛️ History & Culture",
            "Thu": "💊 Health & Body",
            "Fri": "🌍 World & Geography",
            "Sat": "💻 Technology & AI",
            "Sun": "🧠 Psychology & Mind"
        }
        category = evening_categories.get(day_name, "🎲 Random Amazing Facts")
        
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "உங்களுக்கு தெரியுமா? Amazing Daily Facts!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "ஆச்சரியமான தகவல்கள்! Mind-Blowing Facts!"},
}

def get_series_identity(slot):
    for key, val in SERIES_MAP.items():
        if key in slot:
            return val
    return {"name": "Simple Tips by VJ", "tagline": "உங்களுக்கு தெரியுமா? Amazing Daily Facts!"}

def get_category_prompt_enhancement(category, slot):
    """
    Returns specific instructions and formatting for the given Tamil fact category.
    """
    base_instructions = "FOCUS: High engagement, curiosity-inducing facts. The hook must immediately grab the Tamil viewer's attention. Keep the tone friendly and conversational (Tanglish)."
    
    enhancements = {
        "🧪 Science & Space": f"""
            {base_instructions}
            CATEGORY: Science & Space
            GOAL: Explain a mind-blowing science or space fact in simple, engaging Tanglish. E.g., black holes, gravity anomalies, or DNA secrets.
            HOOK TEMPLATE (Tamil): "உங்களுக்கு தெரியுமா? இந்த ஒரு விஷயம் gravity-யையே cheat பண்ணும்! [Topic] பத்தி இந்த shocking fact..."
        """,
        "🏛️ History & Culture": f"""
            {base_instructions}
            CATEGORY: History & Culture
            GOAL: Share an intriguing fact about ancient Tamil history, lost kingdoms, or world monuments with high historical significance.
            HOOK TEMPLATE (Tamil): "நம்ம தமிழ் வரலாற்றிலேயே யாருக்கும் தெரியாத ஒரு பெரிய ரகசியம்... [Topic] பத்தி உங்களுக்கு தெரியுமா?"
        """,
        "💊 Health & Body": f"""
            {base_instructions}
            CATEGORY: Health & Body
            GOAL: Share a fascinating biology or health hack/fact. Why we yawn, how our brain works under stress, or a mysterious body response.
            HOOK TEMPLATE (Tamil): "நம்ம உடம்புல நடக்குற இந்த ஒரு விஷயம், doctors-க்கே ஒரு பெரிய mystery-ஆ இருக்கு! [Topic] பத்தி உங்களுக்கு தெரியுமா?"
        """,
        "🌍 World & Geography": f"""
            {base_instructions}
            CATEGORY: World & Geography
            GOAL: Focus on mysterious locations, bizarre islands, geographical wonders, or climate secrets around the globe.
            HOOK TEMPLATE (Tamil): "உலகத்திலேயே இப்படி ஒரு இடம் இருக்குனு உங்களுக்கு தெரியுமா? இங்க நடக்குறது எல்லாமே magic மாதிரி..."
        """,
        "💻 Technology & AI": f"""
            {base_instructions}
            CATEGORY: Technology & AI
            GOAL: Present futuristic tech, how the internet works in deep oceans, AI breakthroughs, or legendary inventions that changed the world.
            HOOK TEMPLATE (Tamil): "இனிமேல் நம்ம mobile-ல screen-ஏ தேவைப்படாது! [Topic] பத்தி ஒரு mind-blowing tech update..."
        """,
        "🧠 Psychology & Mind": f"""
            {base_instructions}
            CATEGORY: Psychology & Mind
            GOAL: Share psychology facts, cognitive biases, memory tricks, or visual illusion explanations.
            HOOK TEMPLATE (Tamil): "நம்ம brain நம்மளையே எப்படி ஏமாத்துதுனு உங்களுக்கு தெரியுமா? இந்த psychology trick-ஐ பாருங்க..."
        """,
        "🎲 Random Amazing Facts": f"""
            {base_instructions}
            CATEGORY: Random Amazing Facts
            GOAL: Highlight an incredibly bizarre, highly viral miscellaneous fact from anywhere in the world.
            HOOK TEMPLATE (Tamil): "உலகத்திலேயே ரொம்ப விசித்திரமான ஒரு விஷயம்... இத கேட்டா நீங்க கண்டிப்பா நம்ப மாட்டீங்க!"
        """
    }
    
    return enhancements.get(category, enhancements.get("🎲 Random Amazing Facts"))
