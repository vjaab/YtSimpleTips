import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEYS_RAW = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS = [k.strip() for k in GEMINI_API_KEYS_RAW.split(",") if k.strip() and "dummy" not in k.lower()]

_key_idx = 1
while True:
    alt_key = os.getenv(f"GEMINI_API_KEY_{_key_idx}", "")
    if alt_key:
        cleaned_key = alt_key.strip()
        if "dummy" not in cleaned_key.lower():
            if cleaned_key not in GEMINI_API_KEYS:
                GEMINI_API_KEYS.append(cleaned_key)
        _key_idx += 1
    else:
        if _key_idx > 10:
            break
        _key_idx += 1

if not GEMINI_API_KEYS and os.getenv("GEMINI_API_KEY"):
    val = os.getenv("GEMINI_API_KEY").strip()
    if "dummy" not in val.lower():
        GEMINI_API_KEYS = [val]

_seen = set()
GEMINI_API_KEYS = [x for x in GEMINI_API_KEYS if not (x in _seen or _seen.add(x))]

GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

_current_key_idx = 0

def get_gemini_api_key():
    global _current_key_idx
    if not GEMINI_API_KEYS:
        return ""
    _current_key_idx = _current_key_idx % len(GEMINI_API_KEYS)
    return GEMINI_API_KEYS[_current_key_idx]

def rotate_gemini_api_key():
    global _current_key_idx
    if not GEMINI_API_KEYS or len(GEMINI_API_KEYS) <= 1:
        return False
    _old_idx = _current_key_idx
    _current_key_idx = (_current_key_idx + 1) % len(GEMINI_API_KEYS)
    print(f"🔄 [config] Rotating Gemini API Key: Index {_old_idx+1} -> {_current_key_idx+1} (Total: {len(GEMINI_API_KEYS)} keys)")
    return True

_GEMINI_COOLDOWN = False

def is_gemini_disabled():
    return _GEMINI_COOLDOWN

def disable_gemini():
    global _GEMINI_COOLDOWN
    _GEMINI_COOLDOWN = True
    print("🚨 [config] Gemini API has been globally disabled due to 429/Resource Exhausted. Using fallback models directly.")

def get_gemini_client(refresh=False):
    global _current_key_idx
    if _GEMINI_COOLDOWN:
        print("🚨 [config] Gemini API globally disabled due to cooldown/rate limits.")
        return None
    from google import genai
    key = get_gemini_api_key()
    if not key:
        print("⚠️ [config] No Gemini API key available!")
        return None
    return genai.Client(api_key=key)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "8Oo4d9mNNwK369qOwl")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "") or os.getenv("KAGGLE_API_TOKEN", "")
YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

# Trending Engine API Keys (Phase 1)
YOUTUBE_DATA_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

# X.com (Twitter) API Credentials
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")

# Model IDs
VEO_MODEL_ID = "veo-3.1-generate-preview"

# Model Configurations
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "gemini-2.5-pro")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
GEMINI_FLASH_LITE_MODEL = os.getenv("GEMINI_FLASH_LITE_MODEL", "gemini-2.5-flash-lite")

# API Call Spacing Delay to prevent rate-limiting on Free Tier keys
GEMINI_RPM_SLEEP = float(os.getenv("GEMINI_RPM_SLEEP", "2.0"))

# Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
SFX_DIR = os.path.join(ASSETS_DIR, "sfx")
TRACKER_FILE = os.path.join(BASE_DIR, "facts_log.json")

for d in [OUTPUT_DIR, LOGS_DIR, FONTS_DIR, MUSIC_DIR, SFX_DIR]:
    os.makedirs(d, exist_ok=True)

# Application Settings
TIMEZONE = "Asia/Kolkata"
UPLOAD_TIMES = ["08:00", "13:00", "18:00"]
MAX_RETRY_ATTEMPTS = 10
SIMILARITY_THRESHOLD = 75
CATEGORY_COOLDOWN_DAYS = 3
BGM_VOLUME = 0.12
VOICE_SPEED = 1.15
TARGET_AUDIO_DURATION = (35, 55)

# Global Feature Flags
ENABLE_LONGFORM = False
ENABLE_TRENDING_ENGINE = True    # Phase 1: YouTube/Reddit/GitHub trending aggregation

# Engagement & Retention Pillars (Production Spec 2026)
ENABLE_KINETIC_CAPTIONS = True
ENABLE_AUDIO_DUCKING = True
ENABLE_PERIODIC_CUTS = True
ENABLE_EVIDENCE_SCREENSHOTS = False

ENABLE_HORMOZI_STYLING = True

# Visual Upgrade V2 Feature Flags (2026)
ENABLE_VEO_VIDEO = True              
ENABLE_DUAL_CAPTIONS = True           
ENABLE_ADVANCED_TRANSITIONS = True   
ENABLE_CATEGORY_COLORS = True         
ENABLE_FACT_COUNTER = False          
ENABLE_COUNTDOWN_TIMER = True        
ENABLE_SOUND_ON_INDICATOR = False    
ENABLE_SEAMLESS_LOOP = False          
ENABLE_WATERMARK = True               # Channel watermark overlay on video
ENABLE_FLASH_TRANSITIONS = True       # Flash transition effects between scenes
ENABLE_EMOJI_OVERLAYS = False         # Emoji overlays on video
ENABLE_STOCK_FOOTAGE = False          # Control whether to include stock footage (Pexels)

# Retention Engine Settings
VISUAL_CUT_TARGET_SECONDS = 2.0
ENABLE_CINEMATIC_TRANSITIONS = True
ENABLE_STRATEGIC_SFX = True
ENABLE_DYNAMIC_BGM_CURVE = True
TRENDING_NICHE_BIAS = 0.15

# YouTube Partner Program (YPP) compliance settings
DEFAULT_PRIVACY_STATUS = "private"
ENABLE_TTS_FALLBACK = False