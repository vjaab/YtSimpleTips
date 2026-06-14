import os
import requests
import random
import time
from config import PEXELS_API_KEY, OUTPUT_DIR, ENABLE_VEO_VIDEO
from nano_scene_gen import _generate_imagen_image

TODAY = time.strftime("%Y%m%d_%H%M%S")

def fetch_pexels_media(query, media_type="video", aspect_ratio="9:16"):
    """
    Queries Pexels API for vertical stock videos or photos.
    Returns local path to downloaded file or None.
    """
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
    """Free, no-key AI image generation fallback if Imagen and Veo fail."""
    try:
        width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        print(f"     → Attempting Pollinations AI fallback...")
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path
    except Exception as e:
        print(f"  ⚠️ [pollinations] Generation failed: {e}")
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
        
        # Formulate a search query from the English prompt or subtitle text
        clean_query = ""
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
        
        # Define search query suffix for Pexels
        pexels_query = f"{clean_query} whiteboard animation"

        # ── PRIORITY 1: Veo 3.1 AI Video (if enabled) ──
        if veo_generate and prompt and veo_consecutive_fails < 2:
            print("     → Attempting Veo 3.1 video generation...")
            enhanced_prompt = (
                f"{prompt}. Whiteboard animation style, hand drawing sketch on a clean off-white whiteboard background, "
                f"no text overlays, no watermarks, clean 2D vector line art illustration, {aspect_ratio} aspect ratio."
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
            if "whiteboard" not in prompt.lower():
                enhanced_imagen_prompt = f"{prompt}. Whiteboard animation style, hand drawing sketch on a clean off-white whiteboard background, clean 2D vector line art, vibrant color accents."
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
        if not visual_path and prompt:
            output_jpg = os.path.join(OUTPUT_DIR, f"pollinations_scene_{cid}_{TODAY}.jpg")
            enhanced_pollinations_prompt = prompt
            if "whiteboard" not in prompt.lower():
                enhanced_pollinations_prompt = f"{prompt}. Whiteboard animation style, hand drawing sketch on a clean off-white whiteboard background, clean 2D vector line art, vibrant color accents."
            visual_path = _generate_pollinations_image(enhanced_pollinations_prompt, output_jpg, aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Pollinations AI"

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
