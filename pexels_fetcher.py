import os
import requests
import random
import time
from config import PEXELS_API_KEY, OUTPUT_DIR
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

def fetch_all_chunk_visuals(chunks, topic_context="", script_data=None, is_longform=False):
    """
    Orchestrates the retrieval of visuals for all chunks.
    Uses Playwright screenshots for the opening app/web steps, custom Imagen-3 UI mockups,
    and falls back to Pexels stock media when necessary.
    """
    print(f"\n🎬 VISUAL RESOLVER ENGINE: Processing {len(chunks)} chunks...")
    
    aspect_ratio = "16:9" if is_longform else "9:16"
    
    screenshot_path = script_data.get("screenshot_path") if script_data else None
    evidence_url = script_data.get("use_case_evidence_url") if script_data else None
    
    last_successful_path = None
    last_successful_type = "photo"
    
    # Extract keywords from topic context for generic search fallback
    generic_keywords = [w.lower() for w in topic_context.split() if len(w) > 3][:3]
    generic_query = " ".join(generic_keywords) if generic_keywords else "technology app"
    
    for i, chunk in enumerate(chunks):
        cid = chunk.get("chunk_id", i + 1)
        text = chunk.get("text", "")
        prompt = chunk.get("nano_visual_prompt", "")
        
        # Formulate a search query from the English prompt or subtitle text
        clean_query = "technology"
        if prompt:
            # Take first 3 descriptive words from English prompt
            words = [w.strip(",.!?\"'") for w in prompt.split() if w.lower() not in ["a", "the", "cinematic", "photorealistic", "detailed", "in", "of", "and", "9:16", "vertical"]]
            clean_query = " ".join(words[:3])
        else:
            clean_query = generic_query
            
        print(f"  [{i+1}/{len(chunks)}] Resolving visuals for: '{text[:40]}...' (Query: '{clean_query}')")
        
        visual_path = None
        visual_type = None
        source = "Failed"
        
        # 1. First Priority for Step 2 (i == 1): Real Playwright Screenshot of app landing/login screen
        if i == 1 and screenshot_path and os.path.exists(screenshot_path):
            visual_path = screenshot_path
            visual_type = "photo"
            source = "Playwright Screenshot"
            chunk["source_url"] = evidence_url
            print(f"     → Visual resolved: Using Playwright app screenshot.")
            
        # 2. Second Priority: custom Imagen step-by-step UI mockup generation
        if not visual_path and prompt:
            print("     → Generating custom Imagen step UI mockup...")
            output_jpg = os.path.join(OUTPUT_DIR, f"nano_scene_{cid}_{TODAY}.jpg")
            visual_path = _generate_imagen_image(prompt, output_jpg, aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Imagen AI"
                time.sleep(2)  # rate limit cooling
                
        # 3. Third Priority: Fallback to Pexels Stock Video
        if not visual_path:
            visual_path = fetch_pexels_media(clean_query, media_type="video", aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "video"
                source = "Pexels Video"
                
        # 4. Fourth Priority: Fallback to Pexels Stock Photo
        if not visual_path:
            visual_path = fetch_pexels_media(clean_query, media_type="photo", aspect_ratio=aspect_ratio)
            if visual_path:
                visual_type = "photo"
                source = "Pexels Photo"
                
        # 5. Fifth Priority: Reuse the previous visual asset to keep visual continuity
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
