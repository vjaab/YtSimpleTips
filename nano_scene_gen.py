"""
nano_scene_gen.py — Per-Sentence "Nano-Scene" Visual Generation Engine.
Generates one Imagen 4.0 background image per subtitle chunk (sentence) for high-retention Shorts.
"""

import os
import time
import random
from datetime import datetime
from google import genai
from config import GEMINI_API_KEY, OUTPUT_DIR, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS

TODAY = datetime.now().strftime("%Y%m%d_%H%M%S")

def _get_client():
    return get_gemini_client()

def _generate_missing_prompts(chunks, headline, style_guide, aspect_ratio="9:16"):
    """
    For chunks that don't have a nano_visual_prompt, use Gemini Flash to batch-generate
    visual prompts for all of them in one call.
    """
    missing = [c for c in chunks if not c.get("nano_visual_prompt")]
    if not missing:
        return chunks

    print(f"  🎨 Generating nano-scene prompts for {len(missing)} chunks without prompts...")

    chunk_list = "\n".join([
        f"[{c.get('chunk_id', i+1)}] \"{c.get('text', '')}\""
        for i, c in enumerate(missing)
    ])

    format_desc = "16:9 landscape format" if aspect_ratio == "16:9" else "9:16 vertical format"
    prompt = f"""You are a cinematic visual director for YouTube Shorts.

HEADLINE/FACT: {headline}
VISUAL STYLE: {style_guide}

For each sentence below, generate a specific, cinematic IMAGE PROMPT in English that visually represents
EXACTLY what is being spoken in that sentence. The image will be used as a fullscreen background.

RULES:
- Each prompt must be SPECIFIC to the sentence content (not generic)
- NO text in images. NO faces of real people. NO watermarks.
- Photorealistic, cinematic lighting, {format_desc}, 8K quality
- Include relevant objects, environments, or symbolic imagery
- Keep each prompt under 80 words
- If the prompt describes or portrays people, they MUST look like South Indian Tamil people from Tamil Nadu, India.
- If the prompt describes or portrays locations, streets, houses, buildings, or landscapes, they MUST resemble typical environments in Tamil Nadu, India.

SENTENCES:
{chunk_list}

Return ONLY a JSON array of objects, one per sentence, in order:
[
  {{"chunk_id": 1, "prompt": "Cinematic close-up of..."}},
  ...
]"""

    attempts = 0
    max_attempts = 4
    prompts = []
    while attempts < max_attempts:
        try:
            client = _get_client()
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(temperature=0.7)
            )
            raw = response.text.strip()
            if "[" in raw and "]" in raw:
                raw = raw[raw.find("["):raw.rfind("]") + 1]

            import json
            prompts = json.loads(raw)
            break
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(
                k in err_str
                for k in ["503", "429", "unavailable", "rate limit", "resource exhausted", "demand", "temporary"]
            )
            is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
            
            if is_depleted_or_429 and len(GEMINI_API_KEYS) > 1:
                rotate_gemini_api_key()
                print("🔄 [nano_scene_gen] Rotated key. Retrying immediately...")
                attempts += 1
                continue
                
            sleep_time = int(8 * (1.8 ** attempts) + random.uniform(1, 3)) if is_rate_limit else 5
            print(f"  ⚠️ [nano_scene_gen] Prompt generation failed: {e}. Retrying in {sleep_time}s...")
            time.sleep(sleep_time)
            attempts += 1

    if prompts:
        try:
            prompt_map = {p.get("chunk_id", i + 1): p.get("prompt", "") for i, p in enumerate(prompts)}
            for c in missing:
                cid = c.get("chunk_id", 0)
                if cid in prompt_map and prompt_map[cid]:
                    c["nano_visual_prompt"] = prompt_map[cid]
                else:
                    c["nano_visual_prompt"] = (
                        f"Cinematic visualization of: {c.get('text', 'amazing fact')[:60]}, set in Tamil Nadu, India. "
                        f"Photorealistic, {aspect_ratio} format, {style_guide}, portraying South Indian Tamil people and environments, no text, no faces."
                    )
            print(f"  ✅ Generated {len(prompts)} nano-scene prompts via Gemini Flash.")
        except Exception as e:
            print(f"  ⚠️ Failed mapping prompts: {e}")
            prompts = []  # Trigger fallback loop below
            
    if not prompts:
        print("  ⚠️ Using fallback visual prompts for all missing chunks.")
        for c in missing:
            c["nano_visual_prompt"] = (
                f"Cinematic visualization of: {c.get('text', 'amazing fact')[:60]}, set in Tamil Nadu, India. "
                f"Photorealistic, {aspect_ratio} format, {style_guide}, portraying South Indian Tamil people and environments, no text, no faces."
            )

    return chunks


def _generate_pollinations_image(prompt, output_path, aspect_ratio="9:16"):
    """Free, no-key AI image generation fallback if Imagen and Veo fail."""
    width, height = (1080, 1920) if aspect_ratio == "9:16" else (1920, 1080)
    import requests
    import urllib.parse
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&private=true"
    
    max_attempts = 3
    base_delay = 3  # seconds
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"     → Attempting Pollinations AI fallback (attempt {attempt}/{max_attempts})...")
            resp = requests.get(url, timeout=15)
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


def _generate_imagen_image(prompt, output_path, aspect_ratio="9:16"):
    """Generate a single image via Imagen 4.0."""
    models_to_try = [
        "imagen-4.0-generate-001",
        "imagen-4.0-fast-generate-001",
    ]

    attempts = 0
    while attempts < 2:
        client = _get_client()
        for model_name in models_to_try:
            try:
                result = client.models.generate_images(
                    model=model_name,
                    prompt=prompt,
                    config=genai.types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio,
                        output_mime_type="image/jpeg",
                    ),
                )
                for gen_img in result.generated_images:
                    with open(output_path, "wb") as f:
                        f.write(gen_img.image.image_bytes)
                    return output_path
            except Exception as e:
                err_str = str(e).lower()
                is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
                
                if is_depleted_or_429 and len(GEMINI_API_KEYS) > 1:
                    rotate_gemini_api_key()
                    print("🔄 [nano_scene_gen] Rotated key for Imagen. Retrying immediately...")
                    break  # Break out of model loop to retry with fresh client
                    
                if "429" in err_str:
                    sleep_time = 10 + attempts * 5
                    print(f"  ⏳ Imagen rate limited (429) on {model_name}. Retrying attempt {attempts+1}/2 in {sleep_time}s...")
                    time.sleep(sleep_time)
                    break  # Break out of model loop to retry after sleeping
                else:
                    print(f"  ⚠️ Imagen failed ({model_name}): {e}")
                    continue  # Try next model
        else:
            # Completed the model loop without breaking (no 429 encountered)
            break
        attempts += 1

    return None

def generate_nano_scene_visuals(chunks, headline, style_guide="photorealistic, 8K resolution, highly detailed cinematic shot, dramatic volumetric lighting, vibrant colors, Unreal Engine 5 render style", aspect_ratio="9:16"):
    """
    Main entry point: generates one Imagen background image per chunk.
    """
    if not chunks:
        return chunks

    total = len(chunks)
    print(f"\n🎬 NANO-SCENE ENGINE: Generating {total} per-sentence backgrounds...")

    chunks = _generate_missing_prompts(chunks, headline, style_guide, aspect_ratio=aspect_ratio)

    last_successful_path = None
    generated_count = 0
    reused_count = 0
    pollinations_consecutive_fails = 0

    for i, chunk in enumerate(chunks):
        cid = chunk.get("chunk_id", i + 1)
        prompt = chunk.get("nano_visual_prompt", "")

        if not prompt:
            if last_successful_path:
                chunk["visual_path"] = last_successful_path
                chunk["visual_type"] = "photo"
                chunk["source"] = "Nano-Scene (reused)"
                reused_count += 1
            continue

        output_path = os.path.join(OUTPUT_DIR, f"nano_scene_{cid}_{TODAY}.jpg")
        print(f"  [{i + 1}/{total}] Generating: {prompt[:70]}...")

        path = _generate_imagen_image(prompt, output_path, aspect_ratio=aspect_ratio)

        if not path:
            # Circuit breaker: skip Pollinations if it's consistently failing (rate limited)
            if pollinations_consecutive_fails >= 2:
                print(f"  [{i + 1}/{total}] ⚠️ Pollinations rate limited (2+ consecutive failures). Skipping Pollinations fallback.")
                path = None
            else:
                # Fallback to Pollinations AI
                print(f"  [{i + 1}/{total}] Imagen failed, trying Pollinations AI fallback...")
                path = _generate_pollinations_image(prompt, output_path, aspect_ratio=aspect_ratio)
                if path:
                    pollinations_consecutive_fails = 0
                else:
                    pollinations_consecutive_fails += 1
                source_name = "Nano-Scene (Pollinations)"
                relevance = 9
                # Always add delay after Pollinations call to respect rate limits
                time.sleep(3)
        else:
            source_name = "Nano-Scene (Imagen)"
            relevance = 10

        if path:
            chunk["visual_path"] = path
            chunk["visual_type"] = "photo"
            chunk["source"] = source_name
            chunk["relevance_score"] = relevance
            last_successful_path = path
            generated_count += 1
        elif last_successful_path:
            chunk["visual_path"] = last_successful_path
            chunk["visual_type"] = "photo"
            chunk["source"] = "Nano-Scene (reused)"
            chunk["relevance_score"] = 7
            reused_count += 1
        else:
            chunk["visual_path"] = None
            chunk["visual_type"] = None
            chunk["source"] = "Failed"
            chunk["relevance_score"] = 0

        # Small sleep to throttle requests
        if i < total - 1 and path:
            time.sleep(3)

    print(f"\n  ✅ Nano-Scene Generation Complete: {generated_count} generated, {reused_count} reused.")
    _fill_visual_gaps(chunks)

    return chunks

def _fill_visual_gaps(chunks):
    """Forward-fill: propagate the last successful visual to any gap chunks."""
    last_path = None
    last_type = "photo"
    for c in chunks:
        if c.get("visual_path"):
            last_path = c["visual_path"]
            last_type = c.get("visual_type", "photo")
        elif last_path:
            c["visual_path"] = last_path
            c["visual_type"] = last_type
            c["source"] = c.get("source", "Nano-Scene (gap-filled)")
