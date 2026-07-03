"""
nano_scene_gen.py — Per-Scene Visual Generation Engine with Continuity.
Generates consistent background images per SCENE (group of chunks) for high-retention Shorts.
Focus: AI/Tech visualizations - neural networks, data flows, code terminals, futuristic UI.
"""

import os
import time
import random
import hashlib
from datetime import datetime
from google import genai
from config import GEMINI_API_KEY, OUTPUT_DIR, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS

TODAY = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── VISUAL CONTINUITY: Scene definitions ─────────────────────────────────
# Each scene spans multiple chunks. Consistent character/environment per scene.
SCENE_DURATION_TARGET = 8.0  # seconds per scene (roughly 3-4 chunks)
CHUNKS_PER_SCENE = 3         # target chunks per scene

# AI-focused visual style guide - NO cartoons, NO characters with anatomy issues
AI_VISUAL_STYLE = (
    "Photorealistic 8K, cinematic lighting, 9:16 vertical format. "
    "AI/TECH AESTHETIC ONLY: Neural network visualizations, glowing data streams, "
    "code terminal interfaces, holographic UI panels, fiber optic cables, "
    "server racks with blinking LEDs, quantum circuit diagrams, "
    "abstract geometric data flows, futuristic control rooms, "
    "clean minimalist tech environments. "
    "Color palette: Deep blues, electric cyan, emerald green, amber gold on dark backgrounds. "
    "Volumetric lighting, depth of field, ray-traced reflections. "
    "NO human faces, NO cartoon characters, NO anatomical figures, "
    "NO distorted eyes, NO asymmetrical objects, NO floating nonsense geometry. "
    "Clean, professional, Apple/Google keynote visual quality."
)

def _get_client():
    return get_gemini_client()

def _assign_scene_groups(chunks):
    """
    Group chunks into scenes for visual continuity.
    Each scene gets a consistent visual theme across its chunks.
    """
    if not chunks:
        return chunks
    
    scene_id = 1
    current_scene_chunks = 0
    
    for i, chunk in enumerate(chunks):
        current_scene_chunks += 1
        
        # Assign scene ID
        chunk["scene_id"] = scene_id
        
        # Check if we should start a new scene
        should_split = False
        
        if current_scene_chunks >= CHUNKS_PER_SCENE:
            should_split = True
        elif i > 0:
            # Check for topic shift via text similarity (simple heuristic)
            prev_text = chunks[i-1].get("text", "").lower()
            curr_text = chunk.get("text", "").lower()
            prev_words = set(prev_text.split())
            curr_words = set(curr_text.split())
            overlap = len(prev_words & curr_words) / max(len(prev_words), 1)
            if overlap < 0.15 and current_scene_chunks >= 2:
                should_split = True
        
        if should_split and i < len(chunks) - 1:
            scene_id += 1
            current_scene_chunks = 0
    
    # Ensure last chunk gets a scene_id
    if chunks:
        chunks[-1]["scene_id"] = scene_id
    
    total_scenes = scene_id
    print(f"  📚 Visual Continuity: Grouped {len(chunks)} chunks into {total_scenes} scenes")
    
    return chunks

def _generate_scene_prompts(chunks, headline, aspect_ratio="9:16"):
    """
    Generate ONE prompt per SCENE (not per chunk).
    Each scene gets a consistent visual theme with evolving details per chunk.
    """
    # Group chunks by scene_id
    scenes = {}
    for c in chunks:
        sid = c.get("scene_id", 1)
        if sid not in scenes:
            scenes[sid] = []
        scenes[sid].append(c)
    
    scene_prompts = {}
    
    for sid, scene_chunks in scenes.items():
        # Build combined context for this scene
        scene_text = " | ".join([c.get("text", "") for c in scene_chunks])
        
        # Determine scene focus from text
        text_lower = scene_text.lower()
        if any(kw in text_lower for kw in ["neural", "network", "model", "train", "weight", "layer"]):
            scene_focus = "neural network architecture visualization"
        elif any(kw in text_lower for kw in ["data", "dataset", "token", "embed", "vector"]):
            scene_focus = "data flow and token embedding visualization"
        elif any(kw in text_lower for kw in ["attention", "transformer", "context", "head"]):
            scene_focus = "attention mechanism and transformer architecture"
        elif any(kw in text_lower for kw in ["code", "python", "script", "function", "api"]):
            scene_focus = "code terminal and development environment"
        elif any(kw in text_lower for kw in ["gpu", "compute", "train", "batch", "epoch"]):
            scene_focus = "GPU compute cluster and training visualization"
        elif any(kw in text_lower for kw in ["prompt", "llm", "chat", "generate", "output"]):
            scene_focus = "LLM prompt engineering and generation flow"
        else:
            scene_focus = "AI system architecture and data pipeline"
        
        format_desc = "16:9 landscape format" if aspect_ratio == "16:9" else "9:16 vertical format"
        
        prompt = f"""You are a senior AI visualization artist for top-tier tech keynotes (Apple WWDC, Google I/O, NVIDIA GTC).

HEADLINE: {headline}
SCENE FOCUS: {scene_focus}
SCENE TEXT: {scene_text[:200]}
VISUAL STYLE: {AI_VISUAL_STYLE}

Create a MASTER SCENE PROMPT that establishes a consistent visual environment.
This scene will be used for {len(scene_chunks)} consecutive shots with minor variations.

REQUIREMENTS:
- Single cohesive environment (e.g., "futuristic AI research lab with holographic neural network display")
- Consistent lighting, camera angle, color grading across all shots in scene
- Establish key visual elements that persist: main display, ambient lighting, background elements
- NO humans, NO faces, NO characters, NO anatomical elements
- Professional keynote presentation quality - clean, impressive, technically accurate
- {format_desc}

Return ONLY a JSON object:
{{
  "scene_id": {sid},
  "master_prompt": "Complete cinematic prompt for the scene environment",
  "key_elements": ["element1", "element2", "element3"],
  "camera_base": "Camera position/angle description",
  "lighting_base": "Lighting setup description"
}}"""
        
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            try:
                client = _get_client()
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(temperature=0.5)
                )
                raw = response.text.strip()
                if "{" in raw and "}" in raw:
                    raw = raw[raw.find("{"):raw.rfind("}") + 1]
                import json
                scene_data = json.loads(raw)
                scene_prompts[sid] = scene_data
                print(f"  ✅ Scene {sid} master prompt generated")
                break
            except Exception as e:
                err_str = str(e).lower()
                is_depleted = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
                if is_depleted and len(GEMINI_API_KEYS) > 1:
                    rotate_gemini_api_key()
                    print("🔄 Rotated key. Retrying...")
                    attempts += 1
                    continue
                time.sleep(3)
                attempts += 1
        
        # Fallback if LLM fails
        if sid not in scene_prompts:
            scene_prompts[sid] = {
                "scene_id": sid,
                "master_prompt": f"Professional AI visualization: {scene_focus}. Futuristic dark tech environment with glowing cyan/emerald data streams, holographic displays showing neural network architectures. Cinematic volumetric lighting, 8K, {format_desc}. Clean Apple keynote aesthetic.",
                "key_elements": ["holographic neural display", "data stream particles", "ambient cyan lighting"],
                "camera_base": "Slight low angle, centered on main display",
                "lighting_base": "Dark ambient with volumetric cyan/emerald rim lights"
            }
    
    # Now assign chunk-specific variations based on master scene prompt
    for c in chunks:
        sid = c.get("scene_id", 1)
        scene_data = scene_prompts.get(sid, {})
        master = scene_data.get("master_prompt", "")
        elements = scene_data.get("key_elements", [])
        
        # Create chunk-specific prompt that varies slightly but maintains continuity
        chunk_text = c.get("text", "")
        text_lower = chunk_text.lower()
        
        if "neural" in text_lower or "layer" in text_lower:
            variation = "zoom into neural network layers, glowing connections activating"
        elif "attention" in text_lower or "context" in text_lower:
            variation = "attention heatmap visualization on transformer blocks"
        elif "data" in text_lower or "token" in text_lower:
            variation = "token embeddings flowing as light particles through pipeline"
        elif "code" in text_lower or "python" in text_lower:
            variation = "code terminal close-up with syntax highlighting, executing"
        elif "gpu" in text_lower or "train" in text_lower:
            variation = "GPU cluster racks, temperature gauges, training curves"
        elif "prompt" in text_lower or "generate" in text_lower:
            variation = "prompt input field, generation streaming token by token"
        else:
            variation = "subtle camera drift, data particles flowing"
        
        c["nano_visual_prompt"] = f"{master}. Shot variation: {variation}. Maintain exact same environment, lighting, and key elements: {', '.join(elements)}."
        c["scene_master_prompt"] = master
        c["scene_elements"] = elements
    
    return chunks

def _generate_missing_prompts(chunks, headline, style_guide, aspect_ratio="9:16"):
    """
    OPTIMIZED: Generate prompts per SCENE for visual continuity, not per chunk.
    """
    # First assign scene groups
    chunks = _assign_scene_groups(chunks)
    
    # Then generate scene-based prompts
    chunks = _generate_scene_prompts(chunks, headline, aspect_ratio=aspect_ratio)
    
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


def generate_nano_scene_visuals(chunks, headline, style_guide=AI_VISUAL_STYLE, aspect_ratio="9:16"):
    """
    Main entry point: generates one Imagen background image per chunk.
    Uses scene-based visual continuity.
    """
    if not chunks:
        return chunks

    total = len(chunks)
    print(f"\n🎬 NANO-SCENE ENGINE: Generating {total} per-sentence backgrounds with scene continuity...")

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
            if pollinations_consecutive_fails >= 4:
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