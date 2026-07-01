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

# Cloudflare Workers AI
CLOUDFLARE_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

# Other API Keys
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "8Oo4d9mNNwK369qOwl")
KAGGLE_USERNAME = os.getenv("KAGGLE_USERNAME", "")
KAGGLE_KEY = os.getenv("KAGGLE_KEY", "") or os.getenv("KAGGLE_API_TOKEN", "")
YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")
VEO_MODEL_ID = "veo-3.1-generate-preview"

# Trending Engine API Keys (Phase 1)
YOUTUBE_DATA_API_KEY = os.getenv("YOUTUBE_DATA_API_KEY", "")
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
VIDIQ_API_KEY = os.getenv("VIDIQ_API_KEY", "")

# X.com (Twitter) API Credentials
X_API_KEY = os.getenv("X_API_KEY", "")
X_API_SECRET = os.getenv("X_API_SECRET", "")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET", "")
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN", "")

# Text Generation Models (LLMs)
CLOUDFLARE_TEXT_MODELS = [
    # Latest flagship models
    "@cf/meta/llama-3.3-70b-instruct",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/meta/llama-3.1-70b-instruct",
    "@cf/meta/llama-3.1-8b-instruct",
    "@cf/meta/llama-3.1-8b-instruct-fp8",
    "@cf/meta/llama-3.1-8b-instruct-fast",
    "@cf/meta/llama-3.2-1b-instruct",
    "@cf/meta/llama-3.2-3b-instruct",
    "@cf/meta/llama-3.2-11b-vision-instruct",
    "@cf/meta/llama-4-scout-17b-16e-instruct",
    "@cf/meta/llama-guard-3-8b",
    
    # Qwen models
    "@cf/qwen/qwen2.5-72b-instruct",
    "@cf/qwen/qwen2.5-coder-32b-instruct",
    "@cf/qwen/qwq-32b",
    "@cf/qwen/qwen3-30b-a3b-fp8",
    
    # Mistral models
    "@cf/mistral/mistral-7b-instruct-v0.1",
    "@cf/mistral/mistral-7b-instruct-v0.2",
    "@cf/mistral/mistral-small-3.1-24b-instruct",
    
    # Google Gemma
    "@cf/google/gemma-7b-it",
    "@cf/google/gemma-3-12b-it",
    "@cf/google/gemma-4-26b-a4b-it",
    "@cf/google/gemma-2b-it-lora",
    "@cf/google/gemma-7b-it-lora",
    
    # Z.ai GLM
    "@cf/zai/glm-4.7-flash",
    "@cf/zai/glm-5.2",
    
    # Moonshot Kimi
    "@cf/moonshotai/kimi-k2.5",
    "@cf/moonshotai/kimi-k2.6",
    "@cf/moonshotai/kimi-k2.7-code",
    
    # NVIDIA Nemotron
    "@cf/nvidia/nemotron-3-120b-a12b",
    
    # DeepSeek
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    
    # OpenAI
    "@cf/openai/gpt-oss-120b",
    "@cf/openai/gpt-oss-20b",
    
    # Others
    "@cf/baai/bge-reranker-base",
    "@cf/ibm/granite-4.0-h-micro",
    "@cf/aisingapore/gemma-sea-lion-v4-27b-it",
    "@cf/nousresearch/hermes-2-pro-mistral-7b",
    "@cf/defog/sqlcoder-7b-2",
    "@cf/microsoft/phi-2",
    "@cf/meta/bart-large-cnn",
    "@cf/meta/m2m100-1.2b",
]

# Text-to-Image Models
CLOUDFLARE_TEXT_TO_IMAGE_MODELS = [
    "@cf/blackforestlabs/flux-2-dev",
    "@cf/blackforestlabs/flux-2-klein-4b",
    "@cf/blackforestlabs/flux-2-klein-9b",
    "@cf/blackforestlabs/flux-1-schnell",
    "@cf/runwayml/stable-diffusion-v1-5-img2img",
    "@cf/runwayml/stable-diffusion-v1-5-inpainting",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0",
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/lykon/dreamshaper-8-lcm",
    "@cf/leonardo/lucid-origin",
    "@cf/leonardo/phoenix-1.0",
]

# Text-to-Video Models (if available)
CLOUDFLARE_TEXT_TO_VIDEO_MODELS = [
    # Note: Cloudflare Workers AI currently doesn't have native text-to-video models
    # These would need to be accessed via other providers or APIs
]

# Image-to-Text / Vision Models
CLOUDFLARE_IMAGE_TO_TEXT_MODELS = [
    "@cf/meta/llama-3.2-11b-vision-instruct",
    "@cf/llava-hf/llava-1.5-7b-hf",
    "@cf/unum/uform-gen2-qwen-500m",
]

# Text-to-Speech Models
CLOUDFLARE_TEXT_TO_SPEECH_MODELS = [
    "@cf/deepgram/aura-1",
    "@cf/deepgram/aura-2-en",
    "@cf/deepgram/aura-2-es",
    "@cf/myshell/melotts",
]

# Automatic Speech Recognition (Speech-to-Text)
CLOUDFLARE_SPEECH_TO_TEXT_MODELS = [
    "@cf/openai/whisper",
    "@cf/openai/whisper-large-v3-turbo",
    "@cf/openai/whisper-tiny-en",
    "@cf/deepgram/nova-3",
    "@cf/deepgram/flux",
]

# Embedding Models
CLOUDFLARE_EMBEDDING_MODELS = [
    "@cf/baai/bge-large-en-v1.5",
    "@cf/baai/bge-base-en-v1.5",
    "@cf/baai/bge-small-en-v1.5",
    "@cf/baai/bge-m3",
    "@cf/google/embeddinggemma-300m",
    "@cf/qwen/qwen3-embedding-0.6b",
    "@cf/pfnet/plamo-embedding-1b",
]

# Translation Models
CLOUDFLARE_TRANSLATION_MODELS = [
    "@cf/ai4bharat/indictrans2-en-indic-1b",
    "@cf/meta/m2m100-1.2b",
]

# Classification / Other Models
CLOUDFLARE_CLASSIFICATION_MODELS = [
    "@cf/huggingface/distilbert-sst-2-int8",
    "@cf/meta/detr-resnet-50",
    "@cf/microsoft/resnet-50",
]

# Voice Activity Detection
CLOUDFLARE_VAD_MODELS = [
    "@cf/pipecat/smart-turn-v2",
]

# Legacy/Deprecated models (kept for compatibility)
CLOUDFLARE_LEGACY_MODELS = [
    "@cf/meta/llama-2-7b-chat-fp16",
    "@cf/meta/llama-2-7b-chat-int8",
    "@cf/meta/llama-2-7b-chat-hf-lora",
    "@cf/meta/llama-3-8b-instruct",
    "@cf/meta/llama-3-8b-instruct-awq",
    "@cf/meta/meta-llama-3-8b-instruct",
    "@cf/meta/llama-3.1-8b-instruct-awq",
    "@cf/mistral/mistral-7b-instruct-v0.2-lora",
]

# Default model list for fallback (prioritized by capability)
CLOUDFLARE_MODELS = [
    # Top tier - best for reasoning/complex tasks
    "@cf/meta/llama-3.3-70b-instruct",
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/zai/glm-4.7-flash",
    "@cf/openai/gpt-oss-120b",
    "@cf/nvidia/nemotron-3-120b-a12b",
    "@cf/meta/llama-4-scout-17b-16e-instruct",
    "@cf/qwen/qwq-32b",
    "@cf/deepseek-ai/deepseek-r1-distill-qwen-32b",
    
    # High quality - good balance
    "@cf/meta/llama-3.1-70b-instruct",
    "@cf/qwen/qwen2.5-72b-instruct",
    "@cf/qwen/qwen3-30b-a3b-fp8",
    "@cf/qwen/qwen2.5-coder-32b-instruct",
    "@cf/mistral/mistral-small-3.1-24b-instruct",
    "@cf/google/gemma-4-26b-a4b-it",
    "@cf/moonshotai/kimi-k2.7-code",
    "@cf/moonshotai/kimi-k2.6",
    
    # Fast/Efficient
    "@cf/meta/llama-3.1-8b-instruct",
    "@cf/meta/llama-3.1-8b-instruct-fp8",
    "@cf/meta/llama-3.1-8b-instruct-fast",
    "@cf/meta/llama-3.2-3b-instruct",
    "@cf/mistral/mistral-7b-instruct-v0.1",
    "@cf/mistral/mistral-7b-instruct-v0.2",
    "@cf/google/gemma-3-12b-it",
    "@cf/google/gemma-7b-it",
    "@cf/zai/glm-5.2",
    
    # Lightweight
    "@cf/meta/llama-3.2-1b-instruct",
    "@cf/openai/gpt-oss-20b",
    "@cf/ibm/granite-4.0-h-micro",
]

# All models combined for reference
CLOUDFLARE_ALL_MODELS = (
    CLOUDFLARE_TEXT_MODELS + 
    CLOUDFLARE_TEXT_TO_IMAGE_MODELS + 
    CLOUDFLARE_TEXT_TO_VIDEO_MODELS + 
    CLOUDFLARE_IMAGE_TO_TEXT_MODELS + 
    CLOUDFLARE_TEXT_TO_SPEECH_MODELS + 
    CLOUDFLARE_SPEECH_TO_TEXT_MODELS + 
    CLOUDFLARE_EMBEDDING_MODELS + 
    CLOUDFLARE_TRANSLATION_MODELS + 
    CLOUDFLARE_CLASSIFICATION_MODELS + 
    CLOUDFLARE_VAD_MODELS
)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")

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
BGM_VOLUME = 0.08
VOICE_SPEED = 1.05
AVATAR_SYNC_OFFSET = float(os.getenv("AVATAR_SYNC_OFFSET", "0.16"))
TARGET_AUDIO_DURATION = (90, 120)

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
ENABLE_AI_DISCLOSURE_LABEL = True     # AI Human-in-the-loop production label (YPP compliance)
ENABLE_FLASH_TRANSITIONS = True       # Flash transition effects between scenes
ENABLE_EMOJI_OVERLAYS = False         # Emoji overlays on video (DISABLED - caused clutter)
ENABLE_STOCK_FOOTAGE = False          # Control whether to include stock footage (Pexels)
ENABLE_AI_DISCLOSURE_LABEL = True     # YouTube AI-generated content disclosure label

# Retention Engine Settings
VISUAL_CUT_TARGET_SECONDS = 2.0
ENABLE_CINEMATIC_TRANSITIONS = True
ENABLE_STRATEGIC_SFX = True
ENABLE_DYNAMIC_BGM_CURVE = True
TRENDING_NICHE_BIAS = 0.15

# YouTube Partner Program (YPP) compliance settings
DEFAULT_PRIVACY_STATUS = "public"
ENABLE_TTS_FALLBACK = False