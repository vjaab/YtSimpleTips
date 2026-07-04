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
                    # Pick a random video from the top results for variety
                    video = random.choice(videos[:5])
                    video_files = video.get("video_files", [])
                    
                    # Filter for vertical SD/HD mp4 files
                    valid_files = [
                        vf for vf in video_files 
                        if vf.get("file_type") == "video/mp4" and vf.get("width", 0) < vf.get("height", 0)
                    ]
                    
                    if not valid_files:
                        valid_files = video_files
                        
                    if valid_files:
                        # Sort by width to get good resolution but not too large
                        valid_files.sort(key=lambda x: x.get("width", 0))
                        # Take standard HD (around 720p or 1080p width < height)
                        selected_file = valid_files[0]
                        download_url = selected_file.get("link")
                        
                        output_path = os.path.join(OUTPUT_DIR, f"pexels_video_{TODAY}_{random.randint(1000, 9999)}.mp4")
                        print(f"📥 [pexels] Downloading stock video for '{query}': {download_url[:60]}...")
                        
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
                    photo = random.choice(photos[:5])
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

def fetch_all_chunk_visuals(chunks, topic_context="", script_data=None, is_longform=False):
    """
    Orchestrates the retrieval of visuals for all chunks.
    Priority chain (per-chunk, independent): Veo 3.1 → Imagen → Cloudflare FLUX → Pollinations → DeepAI → Pexels Video → Pexels Photo → Reuse.
    """
    print(f"\n🎬 VISUAL RESOLVER ENGINE: Processing {len(chunks)} chunks...")
    
    aspect_ratio = "16:9" if is_longform else "9:16"
    
    last_successful_path = None
    last_successful_type = "photo"
    
    # Extract keywords from topic context for generic search fallback
    generic_keywords = [w.lower() for w in topic_context.split() if len(w) > 3][:3]
    generic_query = " ".join(generic_keywords) if generic_keywords else "amazing fact"

    # Lazy import Veo only if enabled
    veo_generate = None
    if ENABLE_VEO_VIDEO:
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

        # Build provider list for this chunk (each provider is tried independently per chunk)
        providers = []
        
        # Priority 1: Veo 3.1 AI Video
        if veo_generate and prompt:
            providers.append(("Veo 3.1 AI", lambda: _try_veo(veo_generate, prompt, cid, aspect_ratio)))
        
        # Priority 2: Imagen AI Image
        if has_gemini and prompt:
            providers.append(("Imagen AI", lambda: _try_imagen(prompt, cid, aspect_ratio)))
        
        # Priority 3: Cloudflare Workers AI (FLUX.1 Schnell)
        if has_cloudflare and prompt:
            providers.append(("Cloudflare FLUX", lambda: _try_cloudflare_flux(prompt, cid, aspect_ratio)))
        
        # Priority 4: Pollinations AI (Free, no key required)
        if prompt:
            providers.append(("Pollinations AI", lambda: _try_pollinations(prompt, cid, aspect_ratio)))
        
        # Priority 5: DeepAI (Free tier, optional)
        if has_deepseek and prompt:
            providers.append(("DeepAI", lambda: _try_deepai(prompt, cid, aspect_ratio)))
        
        # Priority 6: Pexels Stock Video
        if has_pexels:
            providers.append(("Pexels Video", lambda: fetch_pexels_media(pexels_query, media_type="video", aspect_ratio=aspect_ratio)))
        
        # Priority 7: Pexels Stock Photo
        if has_pexels:
            providers.append(("Pexels Photo", lambda: fetch_pexels_media(pexels_query, media_type="photo", aspect_ratio=aspect_ratio)))
        
        # Priority 8: Fallback to Screenshot
        if ENABLE_EVIDENCE_SCREENSHOTS and not visual_path and script_data and script_data.get("screenshot_path") and os.path.exists(script_data["screenshot_path"]):
            providers.append(("Fallback Screenshot", lambda: script_data["screenshot_path"]))
        
        # Priority 9: Reuse last successful visual
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


def _try_veo(veo_generate, prompt, cid, aspect_ratio):
    """Try Veo 3.1 video generation."""
    enhanced_prompt = (
        f"{prompt}. Art style: 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting. "
        f"Color grading: Vibrant colors, depth of field, warm volume lighting, no dialogue or text overlays, "
        f"no watermarks, stylized 3D cartoon style character, smooth camera movement, "
        f"9:16 aspect ratio, vertical video format, highly dynamic."
    )
    output_mp4 = os.path.join(OUTPUT_DIR, f"veo_scene_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.mp4")
    return veo_generate(enhanced_prompt, output_mp4, aspect_ratio=aspect_ratio)


def _try_imagen(prompt, cid, aspect_ratio):
    """Try Imagen AI image generation."""
    output_jpg = os.path.join(OUTPUT_DIR, f"nano_scene_{cid}_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
    enhanced_imagen_prompt = prompt
    if not any(w in prompt.lower() for w in ["cartoon", "pixar", "claymation", "3d"]):
        enhanced_imagen_prompt = (
            f"{prompt}. 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting, "
            f"depth of field, vibrant colors, high contrast."
        )
    return _generate_imagen_image(enhanced_imagen_prompt, output_jpg, aspect_ratio=aspect_ratio)


def _try_cloudflare_flux(prompt, cid, aspect_ratio):
    """Try Cloudflare Workers AI FLUX.1 Schnell image generation."""
    if not CLOUDFLARE_API_TOKEN or not CLOUDFLARE_ACCOUNT_ID:
        return None
    
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "width": width, "height": height, "num_inference_steps": 4}
    
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


def _try_pollinations(prompt, cid, aspect_ratio):
    """Try Pollinations AI image generation."""
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    encoded_prompt = requests.utils.quote(prompt)
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
