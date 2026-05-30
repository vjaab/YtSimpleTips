import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
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
UPLOAD_TIMES = ["08:00", "18:00"]  # 2/day schedule (08:00 AM and 06:00 PM IST)
MAX_RETRY_ATTEMPTS = 10
SIMILARITY_THRESHOLD = 70
CATEGORY_COOLDOWN_DAYS = 3
BGM_VOLUME = 0.08
TARGET_AUDIO_DURATION = (40, 55)  # Optimized for Tamil Shorts audience

# Global Feature Flags
ENABLE_LONGFORM = False

# Engagement & Retention Pillars (Faceless Info Channels 2026)
ENABLE_KINETIC_CAPTIONS = False
ENABLE_WATERMARK = True
ENABLE_AUDIO_DUCKING = True
ENABLE_PERIODIC_CUTS = True
ENABLE_EVIDENCE_SCREENSHOTS = True
ENABLE_HORMOZI_STYLING = True
