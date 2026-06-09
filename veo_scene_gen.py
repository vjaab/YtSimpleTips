"""
veo_scene_gen.py — Veo 3.1 AI Video Clip Generation Engine.
Generates short cinematic video clips per subtitle chunk using Google's Veo 3.1 model.
Falls back to Imagen image generation if Veo fails or is unavailable.
"""

import os
import time
from datetime import datetime
from google import genai
from google.genai import types
from config import GEMINI_API_KEY, OUTPUT_DIR, VEO_MODEL_ID, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS

TODAY = datetime.now().strftime("%Y%m%d_%H%M%S")

def _get_client():
    return get_gemini_client()


def generate_veo_clip(prompt, output_path, aspect_ratio="9:16", max_wait_seconds=120):
    """
    Generates a single AI video clip via Veo 3.1.
    Uses async polling pattern — submits request then polls until complete.
    
    Args:
        prompt: Text prompt describing the desired video clip
        output_path: Path to save the generated .mp4 file
        aspect_ratio: "9:16" for vertical Shorts or "16:9" for longform
        max_wait_seconds: Maximum time to wait for generation before timing out
    
    Returns:
        output_path on success, None on failure
    """
    attempts = 0
    max_attempts = 2
    while attempts < max_attempts:
        try:
            client = _get_client()
            print(f"  🎬 [Veo] Generating video clip (attempt {attempts + 1}/{max_attempts})...")

            operation = client.models.generate_videos(
                model=VEO_MODEL_ID,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_videos=1,
                ),
            )

            # Poll until complete or timeout
            start_time = time.time()
            while not operation.done:
                elapsed = time.time() - start_time
                if elapsed > max_wait_seconds:
                    print(f"  ⏰ [Veo] Timed out after {max_wait_seconds}s. Falling back.")
                    return None
                time.sleep(10)
                operation = client.operations.get(operation)

            # Extract and save the generated video
            if operation.response and operation.response.generated_videos:
                generated_video = operation.response.generated_videos[0]
                client.files.download(file=generated_video.video)
                generated_video.video.save(output_path)
                print(f"  ✅ [Veo] Video clip saved: {output_path}")
                return output_path
            else:
                print(f"  ⚠️ [Veo] No video returned in response.")
                return None

        except Exception as e:
            err_str = str(e).lower()
            is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
            
            if is_depleted_or_429 and len(GEMINI_API_KEYS) > 1:
                rotate_gemini_api_key()
                print("🔄 [veo_scene_gen] Rotated key. Retrying immediately...")
                continue
                
            if "429" in err_str:
                import random
                sleep_time = int(15 + (attempts * 10) + random.uniform(1, 3))
                print(f"  ⏳ [Veo] Rate limited (429). Waiting {sleep_time}s (attempt {attempts+1}/{max_attempts})...")
                time.sleep(sleep_time)
                attempts += 1
            elif "not found" in err_str or "not supported" in err_str:
                print(f"  ❌ [Veo] Model unavailable: {e}. Skipping Veo entirely.")
                return None
            else:
                print(f"  ⚠️ [Veo] Generation failed: {e}")
                attempts += 1

    print("  🚨 [Veo] All attempts failed.")
    return None


def generate_veo_scene_visuals(chunks, headline, style_guide="cinematic, photorealistic", aspect_ratio="9:16"):
    """
    Main entry point: generates one Veo video clip per chunk.
    Falls back to None for chunks that fail (caller handles fallback to Imagen/Pexels).
    
    Args:
        chunks: List of subtitle chunk dicts with 'nano_visual_prompt'
        headline: The fact headline for context
        style_guide: Visual style description
        aspect_ratio: "9:16" or "16:9"
    
    Returns:
        chunks with 'visual_path' and 'visual_type' set for successful generations
    """
    if not chunks:
        return chunks

    total = len(chunks)
    print(f"\n🎬 VEO 3.1 ENGINE: Generating {total} video clips...")

    generated_count = 0
    failed_count = 0
    last_successful_path = None

    for i, chunk in enumerate(chunks):
        cid = chunk.get("chunk_id", i + 1)
        prompt = chunk.get("nano_visual_prompt", "")

        if not prompt:
            # No prompt available — skip, let fallback handle it
            continue

        # Enhance prompt with cinematic quality markers
        enhanced_prompt = (
            f"{prompt}. "
            f"Cinematic {style_guide}, no text overlays, no faces, no watermarks, "
            f"smooth camera movement, {aspect_ratio} aspect ratio."
        )

        output_path = os.path.join(OUTPUT_DIR, f"veo_scene_{cid}_{TODAY}.mp4")
        print(f"  [{i + 1}/{total}] Veo: {prompt[:70]}...")

        path = generate_veo_clip(enhanced_prompt, output_path, aspect_ratio=aspect_ratio)

        if path:
            chunk["visual_path"] = path
            chunk["visual_type"] = "video"
            chunk["source"] = "Veo 3.1 AI"
            chunk["relevance_score"] = 10
            last_successful_path = path
            generated_count += 1
        else:
            failed_count += 1
            # Leave visual_path unset — caller will fallback to Imagen/Pexels

        # Throttle between requests to avoid rate limits (cooldown between clips)
        if i < total - 1:
            sleep_time = 20 if path else 5
            time.sleep(sleep_time)

    print(f"\n  ✅ Veo Generation: {generated_count} clips generated, {failed_count} need fallback.")
    return chunks
