import os
import requests
import random
import time
from config import PEXELS_API_KEY, OUTPUT_DIR, ENABLE_VEO_VIDEO, ENABLE_STOCK_FOOTAGE, ENABLE_EVIDENCE_SCREENSHOTS
from nano_scene_gen import _generate_imagen_image

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
    Priority chain: Veo 3.1 → Imagen → Pollinations AI → Pexels Video → Pexels Photo → Reuse.
    """
    print(f"\n🎬 VISUAL RESOLVER ENGINE: Processing {len(chunks)} chunks...")
    
    aspect_ratio = "16:9" if is_longform else "9:16"
    
    last_successful_path = None
    last_successful_type = "photo"
    
    # Circuit breakers to skip APIs if they consistently fail (e.g. rate limit quota reached)
    veo_consecutive_fails = 0
    imagen_consecutive_fails = 0
    pollinations_consecutive_fails = 0
    
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
            print("  ⚠️ Veo module not found. Falling back to Imagen/Pexels.")
    
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

        # ── PRIORITY 1: Veo 3.1 AI Video (if enabled) ──
        if veo_generate and prompt and veo_consecutive_fails < 2:
            print("     → Attempting Veo 3.1 video generation...")
            enhanced_prompt = (
                f"{prompt}. Art style: 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting. "
                f"Color grading: Vibrant colors, depth of field, warm volume lighting, no dialogue or text overlays, "
                f"no watermarks, stylized 3D cartoon style character, smooth camera movement, "
                f"9:16 aspect ratio, vertical video format, highly dynamic."
            )
            output_mp4 = os.path.join(OUTPUT_DIR, f"veo_scene_{cid}_{TODAY}.mp4")
            visual_path = veo_generate(enhanced_prompt, output_mp4, aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "video"
                source = "Veo 3.1 AI"
                veo_consecutive_fails = 0
                time.sleep(10)  # rate limit cooling
            else:
                veo_consecutive_fails += 1
                if veo_consecutive_fails >= 2:
                    print("     🚨 Veo 3.1 failed twice consecutively. Disabling Veo for remaining chunks.")

        # ── PRIORITY 2: Imagen AI Image (if Veo failed/unavailable) ──
        if not visual_path and prompt and imagen_consecutive_fails < 2:
            print("     → Generating Imagen image...")
            output_jpg = os.path.join(OUTPUT_DIR, f"nano_scene_{cid}_{TODAY}.jpg")
            enhanced_imagen_prompt = prompt
            if not any(w in prompt.lower() for w in ["cartoon", "pixar", "claymation", "3d"]):
                enhanced_imagen_prompt = (
                    f"{prompt}. 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting, "
                    f"depth of field, vibrant colors, high contrast."
                )
            visual_path = _generate_imagen_image(enhanced_imagen_prompt, output_jpg, aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Imagen AI"
                imagen_consecutive_fails = 0
                time.sleep(5)  # rate limit cooling
            else:
                imagen_consecutive_fails += 1
                if imagen_consecutive_fails >= 2:
                    print("     🚨 Imagen failed twice consecutively. Disabling Imagen for remaining chunks.")
                    
        # ── PRIORITY 2.5: Pollinations AI Image (Free AI fallback) ──
        if not visual_path and prompt and pollinations_consecutive_fails < 4:
            output_jpg = os.path.join(OUTPUT_DIR, f"pollinations_scene_{cid}_{TODAY}.jpg")
            enhanced_pollinations_prompt = prompt
            if not any(w in prompt.lower() for w in ["cartoon", "pixar", "claymation", "3d"]):
                enhanced_pollinations_prompt = (
                    f"{prompt}. 3D Pixar/Disney cartoon style, clay textures, expressive eyes, warm volume lighting, "
                    f"depth of field, vibrant colors, high contrast."
                )
            visual_path = _generate_pollinations_image(enhanced_pollinations_prompt, output_jpg, aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Pollinations AI"
                pollinations_consecutive_fails = 0
            else:
                pollinations_consecutive_fails += 1
                if pollinations_consecutive_fails >= 4:
                    print("     🚨 Pollinations failed twice consecutively. Disabling Pollinations for remaining chunks.")
            # Always add delay after Pollinations call to respect rate limits
            time.sleep(3)

        # ── PRIORITY 3: Pexels Stock Video ──
        if not visual_path:
            visual_path = fetch_pexels_media(pexels_query, media_type="video", aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "video"
                source = "Pexels Video"
                
        # ── PRIORITY 4: Pexels Stock Photo ──
        if not visual_path:
            visual_path = fetch_pexels_media(pexels_query, media_type="photo", aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Pexels Photo"
                
        # ── PRIORITY 4.5: Fallback to Screenshot ──
        if ENABLE_EVIDENCE_SCREENSHOTS and not visual_path and script_data and script_data.get("screenshot_path") and os.path.exists(script_data["screenshot_path"]):
            print("     → Visual resolved: Falling back to evidence screenshot.")
            visual_path = script_data["screenshot_path"]
            visual_type = "photo"
            source = "Fallback Screenshot"
                
        # ── PRIORITY 5: Graceful degradation — reuse last visual ──
        if not visual_path:
            if last_successful_path:
                print(f"     → Visual resolved: Reusing predecessor asset.")
                visual_path = last_successful_path
                visual_type = last_successful_type
                source = "Reused Visual"
            else:
                print("     🚨 Critical visual fetch failure. No visual assigned.")
                
        if visual_path:
            chunk["visual_path"] = visual_path
            chunk["visual_type"] = visual_type
            chunk["source"] = source
            last_successful_path = visual_path
            last_successful_type = visual_type
            
    # Forward-fill any initial gaps
    _fill_visual_gaps(chunks)
    
    return chunks

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
