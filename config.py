import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
# API Keys
GEMINI_API_KEYS_RAW = os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS = [k.strip() for k in GEMINI_API_KEYS_RAW.split(",") if k.strip()]

# Check other env variables as well: GEMINI_API_KEY_1, GEMINI_API_KEY_2, GEMINI_API_KEY_3, etc.
_key_idx = 1
while True:
    alt_key = os.getenv(f"GEMINI_API_KEY_{_key_idx}", "")
    if alt_key:
        if alt_key.strip() not in GEMINI_API_KEYS:
            GEMINI_API_KEYS.append(alt_key.strip())
        _key_idx += 1
    else:
        if _key_idx > 10:
            break
        _key_idx += 1

# If still empty, check the base GEMINI_API_KEY
if not GEMINI_API_KEYS and os.getenv("GEMINI_API_KEY"):
    GEMINI_API_KEYS = [os.getenv("GEMINI_API_KEY").strip()]

# Remove duplicates while preserving order
_seen = set()
GEMINI_API_KEYS = [x for x in GEMINI_API_KEYS if not (x in _seen or _seen.add(x))]

# For backward compatibility
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

def get_gemini_client(refresh=False):
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
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "8Oo4d9mNNwK369qOwl")  # VJ Voice Clone ID
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "")
YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

# Model IDs
VEO_MODEL_ID = "veo-3.1-generate-preview"

# Directory Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
FONTS_DIR = os.path.join(ASSETS_DIR, "fonts")
MUSIC_DIR = os.path.join(ASSETS_DIR, "music")
TRACKER_FILE = os.path.join(BASE_DIR, "facts_log.json")

# Create required directories
for d in [OUTPUT_DIR, LOGS_DIR, FONTS_DIR, MUSIC_DIR]:
    os.makedirs(d, exist_ok=True)

# Application Settings
TIMEZONE = "Asia/Kolkata"
UPLOAD_TIMES = ["08:00", "13:00", "18:00"]  # 3/day schedule for maximum algorithm exposure
MAX_RETRY_ATTEMPTS = 10
SIMILARITY_THRESHOLD = 75
CATEGORY_COOLDOWN_DAYS = 3
BGM_VOLUME = 0.08
TARGET_AUDIO_DURATION = (20, 45)  # Shorter Shorts = higher completion rate = algorithm boost

# Global Feature Flags
ENABLE_LONGFORM = False

# Engagement & Retention Pillars (Faceless Info Channels 2026)
ENABLE_KINETIC_CAPTIONS = False
ENABLE_WATERMARK = True
ENABLE_AUDIO_DUCKING = False
ENABLE_PERIODIC_CUTS = False
ENABLE_EVIDENCE_SCREENSHOTS = True
ENABLE_HORMOZI_STYLING = True
ENABLE_FLASH_TRANSITIONS = True
ENABLE_EMOJI_OVERLAYS = True             # Reaction emojis at hook/reveal moments boost energy

# Visual Upgrade V2 Feature Flags (2026)
ENABLE_VEO_VIDEO = True              # Use Veo 3.1 AI video clips as primary B-roll
ENABLE_DUAL_CAPTIONS = False           # Show Tanglish + English keyword captions simultaneously
ENABLE_ADVANCED_TRANSITIONS = True   # Zoom burst, RGB glitch, shake, cross dissolve transitions
ENABLE_CATEGORY_COLORS = False        # Category-specific color palettes per video
ENABLE_FACT_COUNTER = False          # "FACT #N" badge creates series loyalty and FOMO
ENABLE_COUNTDOWN_TIMER = True        # Circular countdown timer in top-right
ENABLE_SOUND_ON_INDICATOR = False    # "Sound ON" flash boosts audio engagement by 15-20%
ENABLE_SEAMLESS_LOOP = False          # Cross-dissolve last 3s with opening visual for loop
