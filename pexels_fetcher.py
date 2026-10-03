import os
import requests
import random
import time
from config import PEXELS_API_KEY, OUTPUT_DIR, ENABLE_VEO_VIDEO, ENABLE_STOCK_FOOTAGE, ENABLE_EVIDENCE_SCREENSHOTS
from nano_scene_gen import _generate_imagen_image
from config import (
    GEMINI_API_KEY, CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID,
    DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY
)

TODAY = time.strftime("%Y%m%d_%H%M%S")

# Pexels asset IDs already used in the current video (reset per fetch_all_chunk_visuals run)
_USED_PEXELS_IDS = set()

def _pick_unused(items, top_n=8):
    """Prefer a random unused result from the top-N most relevant; fall back to any if all used."""
    top = items[:top_n]
    fresh = [it for it in top if it.get("id") not in _USED_PEXELS_IDS]
    choice = random.choice(fresh or top)
    if choice.get("id") is not None:
        _USED_PEXELS_IDS.add(choice.get("id"))
    return choice

def enhance_prompt_for_documentary(prompt, category=""):
    """
    Enhance visual prompt for Photorealistic 8K Documentary aesthetic (National Geographic / IMAX style).
    Removes cartoon, Pixar, and clay references and injects rich, high-fidelity cinematic realism.
    """
    import re
    clean = re.sub(r'\b(cartoon|pixar|disney|clay|claymation|clay textures|expressive eyes|character with)\b', '', prompt or "", flags=re.IGNORECASE).strip()
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    cat_lower = str(category or "").lower()
    
    if any(k in cat_lower for k in ["animal", "nature"]):
        style_suffix = "National Geographic 8K wildlife documentary photograph, sharp telephoto lens, natural golden hour lighting, authentic micro textures, rich organic colors, atmospheric depth, 9:16 vertical."
    elif any(k in cat_lower for k in ["food", "health", "kitchen"]):
        style_suffix = "Culinary science macro cinematography, 8K ultra-detailed food photography, warm appetizing rim lighting, steam and crystalline textures, crisp focus, commercial studio lighting, 9:16 vertical."
    elif any(k in cat_lower for k in ["history", "culture", "ancient"]):
        style_suffix = "Cinematic historical documentary style, 35mm film aesthetic, authentic archaeological textures, atmospheric golden hour dust motes, dramatic lighting, 8K photorealistic, 9:16 vertical."
    elif any(k in cat_lower for k in ["body", "psychology", "human", "brain"]):
        style_suffix = "Cinematic 8K medical documentary aesthetic, dramatic chiaroscuro lighting, high-precision anatomical and neural detail, moody atmospheric haze, photorealistic, 9:16 vertical."
    elif any(k in cat_lower for k in ["money", "living", "smart"]):
        style_suffix = "Modern architectural photography, sleek clean minimalist aesthetic, crisp morning daylight, premium realistic textures, photorealistic 8K, 9:16 vertical."
    else:  # Science / Technology / General
        style_suffix = "Photorealistic 8K National Geographic science documentary style, hyper-detailed microscopic and cosmological elements, volumetric lighting, Octane render quality, IMAX cinema camera, shallow depth of field, dramatic rim lighting, razor-sharp focus, 9:16 vertical."
        
    return f"{clean}. {style_suffix} No text overlays, no watermarks, no logos, no distorted anatomy."

def fetch_pexels_media(query, media_type="video", aspect_ratio="9:16"):
    """
    Queries Pexels API for vertical stock videos or photos.
    Returns local path to downloaded file or None.
    """
    if not ENABLE_STOCK_FOOTAGE:
        return None
    if not PEXELS_API_KEY or "XXX" in PEXELS_API_KEY or not PEXELS_API_KEY.strip():
        print("⚠️ Pexels API Key missing or invalid. Skipping stock search.")
        return None
        
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        if media_type == "video":
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=15&orientation=portrait"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                videos = data.get("videos", [])
                if videos:
                    # Pick an unused clip from the most relevant results for quality and variety
                    video = _pick_unused(videos)
                    video_files = video.get("video_files", [])
                    
                    # Filter for vertical SD/HD mp4 files
                    valid_files = [
                        vf for vf in video_files 
                        if vf.get("file_type") == "video/mp4" and vf.get("width", 0) < vf.get("height", 0)
                    ]
                    
                    if not valid_files:
                        valid_files = video_files
                        
                    if valid_files:
                        # Prefer crisp vertical HD (700p to 1080p width) for pristine mobile display
                        hd_candidates = [vf for vf in valid_files if 700 <= vf.get("width", 0) <= 1080]
                        if hd_candidates:
                            hd_candidates.sort(key=lambda x: x.get("width", 0), reverse=True)
                            selected_file = hd_candidates[0]
                        else:
                            # Fallback: pick closest to 1080 width
                            valid_files.sort(key=lambda x: abs(x.get("width", 0) - 1080))
                            selected_file = valid_files[0]
                            
                        download_url = selected_file.get("link")
                        
                        output_path = os.path.join(OUTPUT_DIR, f"pexels_video_{TODAY}_{random.randint(1000, 9999)}.mp4")
                        print(f"📥 [pexels] Downloading HD vertical stock video ({selected_file.get('width')}x{selected_file.get('height')}) for '{query}'...")
                        
                        resp = requests.get(download_url, stream=True, timeout=30)
                        if resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                for chunk in resp.iter_content(chunk_size=1024*1024):
                                    if chunk: f.write(chunk)
                            return output_path
        else:
            url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=15&orientation=portrait"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                photos = data.get("photos", [])
                if photos:
                    photo = _pick_unused(photos)
                    download_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                    
                    if download_url:
                        output_path = os.path.join(OUTPUT_DIR, f"pexels_photo_{TODAY}_{random.randint(1000, 9999)}.jpg")
                        print(f"📥 [pexels] Downloading stock photo for '{query}': {download_url[:60]}...")
                        
                        resp = requests.get(download_url, timeout=20)
                        if resp.status_code == 200:
                            with open(output_path, "wb") as f:
                                f.write(resp.content)
                            return output_path
    except Exception as e:
        print(f"⚠️ [pexels] Search or download failed for '{query}': {e}")
        
    return None

def _generate_pollinations_image(prompt, output_path, aspect_ratio="9:16"):
    """Free, no-key AI image generation fallback if Imagen and Veo fail. With robust retry logic."""
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    encoded_prompt = requests.utils.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    max_attempts = 3
    base_delay = 3  # seconds
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"     → Attempting Pollinations AI fallback (attempt {attempt}/{max_attempts})....")
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                return output_path
            elif resp.status_code == 429:
                print(f"  ⚠️ [pollinations] Attempt {attempt} rate limited (429). Backing off...")
            else:
                print(f"  ⚠️ [pollinations] Attempt {attempt} returned status: {resp.status_code}")
        except Exception as e:
            print(f"  ⚠️ [pollinations] Attempt {attempt} failed: {e}")
        
        if attempt < max_attempts:
            delay = base_delay * (2 ** (attempt - 1))  # exponential backoff: 3s, 6s
            print(f"     ⏳ Waiting {delay}s before retry...")
            time.sleep(delay)
            
    return None

TECH_KEYWORDS = [
    "langgraph", "langchain", "pytorch", "tensorflow", "fastapi", "flask", 
    "django", "react", "nextjs", "vue", "angular", "git", "github", 
    "docker", "kubernetes", "sql", "sqlite", "mongodb", "postgresql", 
    "mysql", "redis", "pandas", "numpy", "scikit-learn", "keras", 
    "opencv", "huggingface", "transformers", "gemini", "openai", 
    "claude", "llama", "deepseek", "qwen", "groq", "api", "vector database", 
    "chromadb", "pinecone", "weaviate", "milvus", "qdrant", "faiss", 
    "rag", "llm", "neural network", "python", "javascript", "typescript", 
    "html", "css", "agent", "agents"
]

def get_custom_tech_visual(keyword, text):
    """
    Returns (infographic_type, infographic_data) for a matched tech keyword.
    """
    keyword_lower = keyword.lower()
    
    # ── CODE BLOCK CASES ──
    if keyword_lower in ["python", "pandas", "numpy", "scikit-learn"]:
        return "code_block", {
            "filename": "process_data.py",
            "code": "import pandas as pd\nimport numpy as np\n\n# Load and clean dataset\ndf = pd.read_csv('data.csv')\nclean_df = df.dropna()\n\n# Calculate core metrics\nresult = clean_df.mean()\nprint(f'Average: {result}')"
        }
    elif keyword_lower in ["langgraph", "langchain", "agents", "agent"]:
        return "code_block", {
            "filename": "ai_agent.py",
            "code": "from langgraph import StateGraph\n\n# Create agent workflow graph\nbuilder = StateGraph(State)\nbuilder.add_node('model', call_model)\nbuilder.add_node('tools', call_tool)\n\n# Compile and invoke agent\nagent = builder.compile()\nagent.invoke({'input': 'hello'})"
        }
    elif keyword_lower in ["fastapi", "flask", "django", "api"]:
        return "code_block", {
            "filename": "main.py",
            "code": "from fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get('/api/v1/resource')\ndef read_root():\n    return {\n        'status': 'success',\n        'data': 'Hello from FastAPI!'\n    }"
        }
    elif keyword_lower in ["react", "nextjs", "vue", "angular", "html", "javascript", "typescript", "css"]:
        return "code_block", {
            "filename": "Component.jsx",
            "code": "import React, { useState } from 'react';\n\nexport default function Counter() {\n  const [count, setCount] = useState(0);\n  return (\n    <button onClick={() => setCount(count + 1)}>\n      Clicked {count} times\n    </button>\n  );\n}"
        }
    elif keyword_lower in ["git", "github"]:
        return "code_block", {
            "filename": "git_workflow.sh",
            "code": "# Save your current progress\ngit add .\ngit commit -m 'feat: add ai agent'\n\n# Push code to remote repository\ngit push origin main\ngit status"
        }
    elif keyword_lower in ["docker", "kubernetes"]:
        return "code_block", {
            "filename": "Dockerfile",
            "code": "FROM python:3.10-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install -r requirements.txt\nCOPY . .\nCMD ['python', 'main.py']"
        }
    
    # ── DIAGRAM CASES ──
    elif keyword_lower in ["vector database", "chromadb", "pinecone", "weaviate", "milvus", "qdrant", "faiss", "rag"]:
        return "diagram", {
            "title": "VECTOR DB / RAG FLOW",
            "nodes": ["Document", "Embedding Model", "Vector Database", "Context Injection"]
        }
    elif keyword_lower in ["llm", "gemini", "openai", "claude", "llama", "deepseek", "qwen", "groq"]:
        return "diagram", {
            "title": "LLM INFERENCE PIPELINE",
            "nodes": ["User Prompt", "LLM Processing", "Response Generation"]
        }
    elif keyword_lower in ["neural network", "deep learning", "machine learning"]:
        return "diagram", {
            "title": "NEURAL NETWORK ARCHITECTURE",
            "nodes": ["Input Layer", "Hidden Layers (AI Brain)", "Output Prediction"]
        }
    elif keyword_lower in ["database", "sql", "sqlite", "mongodb", "postgresql", "mysql", "redis"]:
        return "diagram", {
            "title": "DATABASE REPLICA FLOW",
            "nodes": ["Write Query", "Primary DB", "Secondary DBs (Replica)"]
        }
    
    # Default diagram fallback
    return "diagram", {
        "title": f"{keyword.upper()} SYSTEM DESIGN",
        "nodes": ["User Input", f"Core {keyword.upper()}", "Output Result"]
    }

def fetch_all_chunk_visuals(chunks, topic_context="", script_data=None, is_longform=False):
    """
    Orchestrates the retrieval of visuals for all chunks.
    Priority chain (per-chunk, independent): Veo 3.1 → Imagen → Cloudflare FLUX → Pollinations → DeepAI → Pexels Video → Pexels Photo → Reuse.
    """
    print(f"\n🎬 VISUAL RESOLVER ENGINE: Processing {len(chunks)} chunks...")
    
    aspect_ratio = "16:9" if is_longform else "9:16"
    _USED_PEXELS_IDS.clear()
    
    # Stock-only mode (e.g. "Did You Know" format): real Pexels footage only, no AI generation
    stock_only = bool(script_data and script_data.get("visual_mode") == "stock_only")
    visual_subjects = [s for s in ((script_data or {}).get("visual_subjects") or []) if isinstance(s, str) and s.strip()]
    if stock_only:
        print("  📼 Stock-only visual mode: Pexels footage only (AI image/video providers disabled).")
    
    last_successful_path = None
    last_successful_type = "photo"
    
    # Extract keywords from topic context for generic search fallback
    generic_keywords = [w.lower() for w in topic_context.split() if len(w) > 3][:3]
    generic_query = " ".join(generic_keywords) if generic_keywords else "amazing fact"

    # Lazy import Veo only if enabled
    veo_generate = None
    if ENABLE_VEO_VIDEO and not stock_only:
        try:
            from veo_scene_gen import generate_veo_clip
            veo_generate = generate_veo_clip
            print("  🎬 Veo 3.1 enabled as primary video source.")
        except ImportError:
            print("  ⚠️ Veo module not found. Falling back to other providers.")
    
    # Check which providers are configured
    has_gemini = bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and "XXX" not in GEMINI_API_KEY)
    has_cloudflare = bool(CLOUDFLARE_API_TOKEN and CLOUDFLARE_API_TOKEN.strip())
    has_deepseek = bool(DEEPSEEK_API_KEY and DEEPSEEK_API_KEY.strip() and "XXX" not in DEEPSEEK_API_KEY)
    has_pexels = bool(PEXELS_API_KEY and PEXELS_API_KEY.strip() and "XXX" not in PEXELS_API_KEY)
    
    print(f"  🔑 Provider availability: Gemini={has_gemini} Cloudflare={has_cloudflare} DeepSeek={has_deepseek} Pexels={has_pexels}")

    for i, chunk in enumerate(chunks):
        cid = chunk.get("chunk_id", i + 1)
        text = chunk.get("text", "")
        prompt = chunk.get("nano_visual_prompt", "")
        
        # Formulate a search query from the LLM-generated stock_search_query or English prompt
        clean_query = chunk.get("stock_search_query", "")
        if not clean_query:
            if prompt:
                fillers = {
                    "a", "the", "cinematic", "photorealistic", "detailed", "in", "of", "and", "9:16", "vertical",
                    "premium", "app", "ui", "mockup", "screenshot", "design", "vector", "realistic", "illustration",
                    "photo", "image", "representing", "representation", "showing", "displays", "displaying", "screen",
                    "mockups", "template", "concept", "close-up", "close", "up", "person", "man", "woman", "human", "face"
                }
                words = [w.strip(",.!?\"'") for w in prompt.split() if w.lower() not in fillers]
                clean_query = " ".join(words[:3])
            
        if not clean_query or len(clean_query.strip()) < 3:
            clean_query = generic_query
            
        print(f"  [{i+1}/{len(chunks)}] Resolving visuals for: '{text[:40]}...' (Query: '{clean_query}')")
        
        visual_path = None
        visual_type = None
        source = "Failed"
        
        # Define search query for Pexels (use the clean query directly to match real stock footage)
        pexels_query = clean_query

        # ── PRIORITY 0: Evidence Screenshot (Assigned to chunk index 1, context/evidence) ──
        if ENABLE_EVIDENCE_SCREENSHOTS and i == 1 and script_data and script_data.get("screenshot_path") and os.path.exists(script_data["screenshot_path"]):
            print("     → Assigning captured evidence screenshot to context chunk...")
            visual_path = script_data["screenshot_path"]
            visual_type = "photo"
            source = "Evidence Screenshot"

        # ── STOCK-ONLY MODE: Pexels video (scene query → subject → topic subjects) → Pexels photo → reuse ──
        if stock_only and not visual_path:
            queries = [pexels_query]
            first_word = pexels_query.split()[0] if pexels_query.split() else ""
            if len(first_word) > 3:
                queries.append(first_word)
            if visual_subjects:
                queries.append(visual_subjects[i % len(visual_subjects)])
            queries.append(generic_query)
            queries = [q for q in dict.fromkeys(q.strip() for q in queries if q and q.strip())]
            
            stock_providers = [(f"Pexels Video '{q}'", (lambda q=q: fetch_pexels_media(q, media_type="video", aspect_ratio=aspect_ratio))) for q in queries]
            stock_providers.append((f"Pexels Photo '{pexels_query}'", lambda: fetch_pexels_media(pexels_query, media_type="photo", aspect_ratio=aspect_ratio)))
            stock_providers.append(("Reused Visual", lambda: last_successful_path if last_successful_path else None))
            
            for provider_name, provider_fn in stock_providers:
                print(f"     → Attempting {provider_name}...")
                try:
                    result = provider_fn()
                except Exception as e:
                    print(f"     ❌ {provider_name} failed: {e}")
                    result = None
                if result:
                    visual_path = result
                    if provider_name.startswith("Pexels Video"):
                        visual_type = "video"
                    elif provider_name == "Reused Visual":
                        visual_type = last_successful_type
                    else:
                        visual_type = "photo"
                    source = provider_name.split(" '")[0]
                    print(f"     ✅ Visual resolved: {provider_name}")
                    break
            
            if visual_path:
                chunk["visual_path"] = visual_path
                chunk["visual_type"] = visual_type
                chunk["source"] = source
                last_successful_path = visual_path
                last_successful_type = visual_type
            else:
                print(f"     🚨 Stock-only visual fetch failure. Will gap-fill.")
            continue

        # ── PRIORITY 0.5: Programmatic settings UI simulation ──
        if not visual_path:
            settings_keywords = ["gboard", "keyboard", "settings", "correct", "glide", "shortcut", "dictionary", "preferences", "theme", "tap on", "turn on", "click on", "toggle"]
            is_settings_tutorial = any(kw in text.lower() or (prompt and kw in prompt.lower()) for kw in settings_keywords)
            if is_settings_tutorial:
                print("     → Settings tutorial detected! Attempting to generate Programmatic UI simulation...")
                try:
                    import settings_ui_gen
                    out_name = f"settings_sim_chunk_{cid}_{TODAY}.mp4"
                    out_path = os.path.join(OUTPUT_DIR, out_name)
                    chunk_dur = chunk.get("duration", 3.0)
                    sim_path = settings_ui_gen.generate_settings_clip(text, chunk_dur, out_path)
                    if sim_path and os.path.exists(sim_path):
                        visual_path = sim_path
                        visual_type = "video"
                        source = "Settings UI Simulator"
                        print(f"     ✅ Settings UI Simulation generated successfully!")
                except Exception as sim_err:
                    print(f"     ❌ Settings UI Simulation generation failed: {sim_err}")

        # ── PRIORITY 0.7: Custom Tech Infographic match ──
        if not visual_path:
            text_lower = text.lower()
            sorted_keywords = sorted(TECH_KEYWORDS, key=len, reverse=True)
            for kw in sorted_keywords:
                if kw in text_lower:
                    info_type, info_data = get_custom_tech_visual(kw, text)
                    chunk["has_infographic"] = True
                    chunk["infographic_type"] = info_type
                    chunk["infographic_data"] = info_data
                    visual_path = os.path.join(OUTPUT_DIR, f"tech_visual_{kw}_{cid}_{TODAY}.png")
                    visual_type = "photo"
                    source = "Tech Visual Agent"
                    print(f"     ✅ Tech Visual Agent: Mentions '{kw}'. Assigned {info_type} infographic.")
                    break

        # Build provider list for this chunk (Smart Hybrid strategy)
        category_name = script_data.get("sub_category", "") if script_data else ""
        
        # Determine if this chunk is a motion candidate (where real video b-roll shines)
        v_type_lower = str(chunk.get("visual_type", "")).lower()
        cam_motion = str(chunk.get("camera_motion", "")).lower()
        has_cam_motion = cam_motion not in ("", "none", "still")
        is_video_hint = any(t in v_type_lower for t in ["video", "cinematic", "b-roll", "clip"])
        
        # Action/nature keywords that look vastly superior in real motion video
        action_keywords = [
            "water", "ocean", "sea", "swim", "dive", "wave", "shark", "fish", "animal", "bird", "fly",
            "sky", "cloud", "star", "galaxy", "space", "sun", "rain", "storm", "boil", "steam",
            "fire", "flame", "ice", "heat", "cook", "food", "plant", "tree", "forest", "city",
            "car", "traffic", "run", "speed", "light", "screen", "phone", "lab", "microscope"
        ]
        text_lower = text.lower()
        prompt_lower = (prompt or "").lower()
        has_action_subject = any(w in text_lower or w in prompt_lower for w in action_keywords)
        
        # Smart Hybrid Strategy: Motion candidates & alternating chunks prioritize real HD stock video
        # Conceptual / abstract candidates prioritize 8K AI generation
        is_motion_candidate = has_pexels and (is_video_hint or has_cam_motion or has_action_subject or (i % 2 == 0))
        
        providers = []
        if is_motion_candidate:
            # ── MOTION FIRST: Real HD Stock Video -> 8K AI Image -> Fallbacks ──
            if has_pexels and pexels_query:
                providers.append(("Pexels Video", lambda: fetch_pexels_media(pexels_query, media_type="video", aspect_ratio=aspect_ratio)))
            if veo_generate and prompt:
                providers.append(("Veo 3.1 AI", lambda: _try_veo(veo_generate, prompt, cid, aspect_ratio, category=category_name)))
            if has_gemini and prompt:
                providers.append(("Imagen AI", lambda: _try_imagen(prompt, cid, aspect_ratio, category=category_name)))
            if has_cloudflare and prompt:
                providers.append(("Cloudflare FLUX", lambda: _try_cloudflare_flux(prompt, cid, aspect_ratio, category=category_name)))
            if prompt:
                providers.append(("Pollinations AI", lambda: _try_pollinations(prompt, cid, aspect_ratio, category=category_name)))
            if has_pexels and pexels_query:
                providers.append(("Pexels Photo", lambda: fetch_pexels_media(pexels_query, media_type="photo", aspect_ratio=aspect_ratio)))
        else:
            # ── CONCEPT FIRST: 8K AI Image -> Real Stock Video -> Fallbacks ──
            if veo_generate and prompt:
                providers.append(("Veo 3.1 AI", lambda: _try_veo(veo_generate, prompt, cid, aspect_ratio, category=category_name)))
            if has_gemini and prompt:
                providers.append(("Imagen AI", lambda: _try_imagen(prompt, cid, aspect_ratio, category=category_name)))
            if has_cloudflare and prompt:
                providers.append(("Cloudflare FLUX", lambda: _try_cloudflare_flux(prompt, cid, aspect_ratio, category=category_name)))
            if has_pexels and pexels_query:
                providers.append(("Pexels Video", lambda: fetch_pexels_media(pexels_query, media_type="video", aspect_ratio=aspect_ratio)))
            if prompt:
                providers.append(("Pollinations AI", lambda: _try_pollinations(prompt, cid, aspect_ratio, category=category_name)))
            if has_pexels and pexels_query:
                providers.append(("Pexels Photo", lambda: fetch_pexels_media(pexels_query, media_type="photo", aspect_ratio=aspect_ratio)))
        
        # Priority 5: DeepAI (Free tier, optional)
        if has_deepseek and prompt:
            providers.append(("DeepAI", lambda: _try_deepai(prompt, cid, aspect_ratio)))
        
        # Priority: Fallback to Screenshot
        if ENABLE_EVIDENCE_SCREENSHOTS and not visual_path and script_data and script_data.get("screenshot_path") and os.path.exists(script_data["screenshot_path"]):
            providers.append(("Fallback Screenshot", lambda: script_data["screenshot_path"]))
        
        # Priority: Reuse last successful visual
        providers.append(("Reused Visual", lambda: last_successful_path if last_successful_path else None))

        # Try each provider in order, stop at first success
        for provider_name, provider_fn in providers:
            if visual_path:
                break
            print(f"     → Attempting {provider_name}...")
            try:
                result = provider_fn()
                if result:
                    visual_path = result
                    visual_type = "video" if provider_name in ["Veo 3.1 AI", "Pexels Video"] else "photo"
                    source = provider_name
                    print(f"     ✅ Visual resolved: {source}")
                    break
                else:
                    print(f"     ⚠️ {provider_name} returned no result")
            except Exception as e:
                print(f"     ❌ {provider_name} failed: {e}")
        
        if not visual_path:
            print(f"     🚨 Critical visual fetch failure. No visual assigned.")

        if visual_path:
            chunk["visual_path"] = visual_path
            chunk["visual_type"] = visual_type
            chunk["source"] = source
            last_successful_path = visual_path
            last_successful_type = visual_type
            
    # Forward-fill any initial gaps
    _fill_visual_gaps(chunks)
    
    return chunks


def _try_veo(veo_generate, prompt, cid, aspect_ratio, category=""):
    """Try Veo 3.1 video generation with Photorealistic 8K documentary direction."""
    enhanced_prompt = enhance_prompt_for_documentary(prompt, category=category)
    output_mp4 = os.path.join(OUTPUT_DIR, f"veo_scene_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
    return veo_generate(enhanced_prompt, output_mp4, aspect_ratio=aspect_ratio)


def _try_imagen(prompt, cid, aspect_ratio, category=""):
    """Try Imagen AI image generation with Photorealistic 8K documentary direction."""
    output_jpg = os.path.join(OUTPUT_DIR, f"nano_scene_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
    enhanced_imagen_prompt = enhance_prompt_for_documentary(prompt, category=category)
    return _generate_imagen_image(enhanced_imagen_prompt, output_jpg, aspect_ratio=aspect_ratio)


def _try_cloudflare_flux(prompt, cid, aspect_ratio, category=""):
    """Try Cloudflare Workers AI FLUX.1 Schnell image generation with 8K documentary direction."""
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        return None
    
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    enhanced_prompt = enhance_prompt_for_documentary(prompt, category=category)
    payload = {"prompt": enhanced_prompt, "width": width, "height": height, "num_inference_steps": 4}
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("result") and data["result"].get("image"):
                import base64
                image_data = base64.b64decode(data["result"]["image"])
                output_jpg = os.path.join(OUTPUT_DIR, f"cf_flux_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
                with open(output_jpg, "wb") as f:
                    f.write(image_data)
                return output_jpg
    except Exception:
        pass
    return None


def _try_pollinations(prompt, cid, aspect_ratio, category=""):
    """Try Pollinations AI image generation with 8K documentary direction."""
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    enhanced_prompt = enhance_prompt_for_documentary(prompt, category=category)
    encoded_prompt = requests.utils.quote(enhanced_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            output_jpg = os.path.join(OUTPUT_DIR, f"pollinations_scene_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
            with open(output_jpg, "wb") as f:
                f.write(resp.content)
            return output_jpg
    except Exception:
        pass
    return None


def _try_deepai(prompt, cid, aspect_ratio):
    """Try DeepAI image generation."""
    # DeepAI requires an API key, using DEEPSEEK_API_KEY as placeholder
    api_key = DEEPSEEK_API_KEY or os.getenv("DEEP_AI_API_KEY", "")
    if not api_key or "XXX" in api_key:
        return None
    
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    url = "https://api.deepai.org/api/text2img"
    headers = {"api-key": api_key}
    data = {"text": prompt, "width": width, "height": height}
    
    try:
        resp = requests.post(url, headers=headers, data=data, timeout=60)
        if resp.status_code == 200:
            result = resp.json()
            if result.get("output_url"):
                img_resp = requests.get(result["output_url"], timeout=30)
                if img_resp.status_code == 200:
                    output_jpg = os.path.join(OUTPUT_DIR, f"deepai_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
                    with open(output_jpg, "wb") as f:
                        f.write(img_resp.content)
                    return output_jpg
    except Exception:
        pass
    return None

def _fill_visual_gaps(chunks):
    # 1. Forward-fill
    last_path = None
    last_type = "photo"
    for c in chunks:
        if c.get("visual_path"):
            last_path = c["visual_path"]
            last_type = c.get("visual_type", "photo")
        elif last_path:
            c["visual_path"] = last_path
            c["visual_type"] = last_type
            c["source"] = c.get("source", "Gap-filled fallback")

    # 2. Backward-fill (for any initial chunks that missed forward-fill)
    first_path = None
    first_type = "photo"
    for c in chunks:
        if c.get("visual_path"):
            first_path = c["visual_path"]
            first_type = c.get("visual_type", "photo")
            break

    if first_path:
        for c in chunks:
            if not c.get("visual_path"):
                c["visual_path"] = first_path
                c["visual_type"] = first_type
                c["source"] = c.get("source", "Back-filled fallback")
