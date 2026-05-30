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
        "Mon": "📦 Delivery & Shopping Apps",            # Blinkit, Zepto, Zomato, Swiggy
        "Tue": "🎬 Photo & Video Editors",             # CapCut, VN Editor, Canva
        "Wed": "💳 FinTech & Payment Apps",             # GPay, PhonePe, Paytm, CRED
        "Thu": "✈️ Travel & Booking Apps",              # IRCTC, MakeMyTrip, Uber, Ola
        "Fri": "🤖 AI & Productivity Tools",            # ChatGPT, Gemini, Notion
        "Sat": "🌐 Government & Utility Websites",      # EPFO portal, Passport Seva, Aadhaar portal
        "Sun": "📱 Social Media & Tech Hacks"           # WhatsApp, Telegram, Instagram
    }
    
    if hour < 12:
        slot = "Slot A (Morning)"
        category = daily_categories.get(day_name, "📦 Delivery & Shopping Apps")
    else:
        slot = "Slot B (Evening)"
        # Alternate category for evening slots to keep audience engaged
        evening_categories = {
            "Mon": "📱 Social Media & Tech Hacks",
            "Tue": "📦 Delivery & Shopping Apps",
            "Wed": "🎬 Photo & Video Editors",
            "Thu": "💳 FinTech & Payment Apps",
            "Fri": "✈️ Travel & Booking Apps",
            "Sat": "🤖 AI & Productivity Tools",
            "Sun": "🌐 Government & Utility Websites"
        }
        category = evening_categories.get(day_name, "📦 Delivery & Shopping Apps")
        
    return day_name, slot, category

SERIES_MAP = {
    "Slot A": {"name": "Simple Tips by VJ", "tagline": "How to Use Trending Apps & Websites!"},
    "Slot B": {"name": "Simple Tips by VJ", "tagline": "Daily Tech Tips & Digital Hacks!"},
}

def get_series_identity(slot):
    for key, val in SERIES_MAP.items():
        if key in slot:
            return val
    return {"name": "Simple Tips by VJ", "tagline": "How to Use Trending Apps & Websites!"}

def get_category_prompt_enhancement(category, slot):
    """
    Returns specific instructions and formatting for the given Tamil tutorial category.
    """
    base_instructions = "FOCUS: High engagement, helpful digital tutorials. The hook must immediately address a common user goal or problem. Keep the tone friendly, helpful, and highly conversational (Tanglish)."
    
    enhancements = {
        "📦 Delivery & Shopping Apps": f"""
            {base_instructions}
            CATEGORY: Delivery & Shopping Apps (e.g. Blinkit, Zepto, Zomato, Swiggy)
            GOAL: Teach how to login, find products/discounts, and place a fast delivery order.
            HOOK TEMPLATE (Tamil): "உங்களுக்கு Blinkit-ல 10 minutes-ல grocery order பண்ணணுமா? அப்போ இந்த video-வை பாருங்க!..."
        """,
        "🎬 Photo & Video Editors": f"""
            {base_instructions}
            CATEGORY: Photo & Video Editors (e.g. CapCut, VN Editor, Canva)
            GOAL: Explain step-by-step how to login, import video, apply a trending effect/transition, and export it.
            HOOK TEMPLATE (Tamil): "CapCut-ல trending video transitions edit பண்ணுறது இவ்வளவு easy-ஆ? வாங்க பார்க்கலாம்!..."
        """,
        "💳 FinTech & Payment Apps": f"""
            {base_instructions}
            CATEGORY: FinTech & Payment Apps (e.g. GPay, PhonePe, Paytm, CRED)
            GOAL: Guide users on setting up accounts, linking banks, scanning QR codes safely, or paying utility bills.
            HOOK TEMPLATE (Tamil): "GPay-ல bank account link பண்ணும்போது error வருதா? இந்த quick solution-ஐ பாருங்க!..."
        """,
        "✈️ Travel & Booking Apps": f"""
            {base_instructions}
            CATEGORY: Travel & Booking Apps (e.g. IRCTC, Uber, Ola, MakeMyTrip)
            GOAL: Teach how to register, login, enter destinations, pick seats/rides, and book tickets.
            HOOK TEMPLATE (Tamil): "IRCTC website-ல tatkal ticket phone-லேயே book பண்ணுறது எப்படின்னு தெரியுமா?!..."
        """,
        "🤖 AI & Productivity Tools": f"""
            {base_instructions}
            CATEGORY: AI & Productivity Tools (e.g. ChatGPT, Gemini, Notion)
            GOAL: Guide the audience through prompt engineering, starting a chat, using templates, and automating daily work.
            HOOK TEMPLATE (Tamil): "ChatGPT-யை வச்சு உங்களோட daily office work-ஐ 10x speed-ஆ மாத்தலாம்! எப்படின்னு பாருங்க!..."
        """,
        "🌐 Government & Utility Websites": f"""
            {base_instructions}
            CATEGORY: Government & Utility Websites (e.g. EPFO portal, Passport Seva, Aadhaar portal)
            GOAL: Provide clear guidance on accessing services, registering, logging in via OTP, and downloading documents.
            HOOK TEMPLATE (Tamil): "உங்களோட Aadhaar card-ல address change பண்ணணுமா? இந்த simple website-ஐ பாருங்க!..."
        """,
        "📱 Social Media & Tech Hacks": f"""
            {base_instructions}
            CATEGORY: Social Media & Tech Hacks (e.g. WhatsApp, Telegram, Instagram)
            GOAL: Teach hidden features, custom settings, registration/login, privacy configurations, or group setups.
            HOOK TEMPLATE (Tamil): "WhatsApp-ல யாருக்கும் தெரியாத 3 secret settings! உடனே try பண்ணி பாருங்க!..."
        """
    }
    
    return enhancements.get(category, enhancements.get("📦 Delivery & Shopping Apps"))

