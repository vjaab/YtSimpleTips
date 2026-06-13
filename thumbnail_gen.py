"""
thumbnail_gen.py — Premium Faceless Infotainment Thumbnail Generator V2.
Generates highly click-worthy Tamil thumbnails using Imagen-4 and Noto Sans Tamil.
Features 4 layout variants with category-specific color palettes for A/B testing.
"""

import os
import random
import time
import math
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from google import genai
from config import GEMINI_API_KEY, OUTPUT_DIR, ASSETS_DIR, ENABLE_CATEGORY_COLORS, get_gemini_client, rotate_gemini_api_key, GEMINI_API_KEYS
from infographic_gen import get_font_for_text

THUMB_W, THUMB_H = 1280, 720  # Standard YouTube 16:9 Thumbnail size

# ── DEFAULT COLOR PALETTE ──
_DEFAULT_ACCENT = (204, 255, 0)  # Electric Lime (original brand)
_DEFAULT_SECONDARY = (15, 15, 10)

def _get_accent_colors(script_json):
    """Resolves accent colors from category palette or falls back to defaults."""
    if ENABLE_CATEGORY_COLORS:
        try:
            from ecosystem_logic import get_category_color_palette
            category = script_json.get("sub_category", "")
            if category:
                palette = get_category_color_palette(category)
                return palette.get("thumbnail_accent", _DEFAULT_ACCENT), palette.get("secondary", _DEFAULT_SECONDARY), palette.get("emoji", "🤯")
        except Exception:
            pass
    return _DEFAULT_ACCENT, _DEFAULT_SECONDARY, "🤯"


def _generate_pexels_background(prompt_context):
    """Fetches a high-quality landscape stock photo from Pexels as a fallback."""
    import requests
    from config import PEXELS_API_KEY
    if not PEXELS_API_KEY or not PEXELS_API_KEY.strip() or "XXX" in PEXELS_API_KEY:
        print("⚠️ [thumbnail] Pexels API Key missing or invalid. Skipping stock search fallback.")
        return None
        
    try:
        print(f"🎨 [thumbnail] Attempting Pexels landscape stock photo fallback for: {prompt_context[:50]}...")
        headers = {"Authorization": PEXELS_API_KEY}
        
        # Clean query: extract keywords to make the search generic and highly relevant
        fillers = {"a", "the", "cinematic", "photorealistic", "detailed", "in", "of", "and", "landscape", "aspect", "ratio", "no", "text", "watermarks", "faces"}
        words = [w.strip(",.!?\"'") for w in prompt_context.split() if w.lower() not in fillers]
        query = " ".join(words[:4]) if words else "infotainment"
        
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=15&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            photos = data.get("photos", [])
            if photos:
                photo = random.choice(photos[:5])
                download_url = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
                if download_url:
                    print(f"📥 [thumbnail] Downloading landscape stock photo: {download_url[:60]}...")
                    resp = requests.get(download_url, timeout=20)
                    if resp.status_code == 200:
                        from io import BytesIO
                        img = Image.open(BytesIO(resp.content))
                        print("✅ [thumbnail] Background retrieved from Pexels")
                        return img
    except Exception as e:
        print(f"⚠️ [thumbnail] Pexels stock fallback failed: {e}")
    return None


def _generate_pollinations_background(prompt_context):
    """Generates an image via Pollinations AI as a fallback."""
    import requests
    try:
        print("🎨 [thumbnail] Attempting Pollinations AI fallback for background...")
        prompt = (
            f"A striking, highly detailed, high-contrast background image related to: {prompt_context}. "
            "Cinematic studio lighting, rich colors, photorealistic, 8k, landscape 16:9 aspect ratio. "
            "No text, no watermarks, no faces."
        )
        encoded_prompt = requests.utils.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1280&height=720&nologo=true"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            from io import BytesIO
            img = Image.open(BytesIO(resp.content))
            print("✅ [thumbnail] Background generated with Pollinations AI")
            return img
    except Exception as e:
        print(f"⚠️ [thumbnail] Pollinations AI fallback failed: {e}")
    return None


def _generate_imagen_background(prompt_context):
    """Generates an eye-catching background image via Imagen 4.0."""
    print(f"🎨 [thumbnail] Generating background for context: {prompt_context[:50]}...")
    
    prompt = (
        f"A striking, highly detailed, high-contrast background image related to: {prompt_context}. "
        "Cinematic studio lighting, rich colors, photorealistic, 8k, landscape 16:9 aspect ratio. "
        "No text, no watermarks, no faces."
    )
    
    models_to_try = [
        "imagen-4.0-generate-001",
        "imagen-4.0-fast-generate-001",
    ]
    
    attempts = 0
    while attempts < 3:
        client = get_gemini_client()
        if not client:
            print("⚠️ [thumbnail] Client missing! Skipping Imagen background generation.")
            break
        for model_name in models_to_try:
            try:
                result = client.models.generate_images(
                    model=model_name,
                    prompt=prompt,
                    config=genai.types.GenerateImagesConfig(
                        number_of_images=1,
                        aspect_ratio="16:9",
                        output_mime_type="image/jpeg",
                    )
                )
                for gen_img in result.generated_images:
                    img_data = gen_img.image.image_bytes
                    temp_path = os.path.join(OUTPUT_DIR, f"temp_thumb_bg_{int(time.time())}.jpg")
                    with open(temp_path, "wb") as f:
                        f.write(img_data)
                    print(f"✅ [thumbnail] Background generated with {model_name}")
                    return Image.open(temp_path)
            except Exception as e:
                err_str = str(e).lower()
                is_depleted_or_429 = "prepayment credits" in err_str or "429" in err_str or "resource exhausted" in err_str
                
                if is_depleted_or_429 and len(GEMINI_API_KEYS) > 1:
                    rotate_gemini_api_key()
                    print("🔄 [thumbnail] Rotated key for Imagen background. Retrying immediately...")
                    break  # Break out of model loop to retry with fresh client
                    
                if "429" in err_str:
                    sleep_time = 15 + attempts * 10
                    print(f"⏳ [thumbnail] Rate limited (429) on {model_name}. Retrying attempt {attempts+1}/3 in {sleep_time}s...")
                    time.sleep(sleep_time)
                    break  # Break out of model loop to retry after sleeping
                else:
                    print(f"⚠️ [thumbnail] {model_name} failed: {e}. Trying next...")
                    continue
        else:
            # Completed the model loop without breaking (no 429/rotation encountered)
            break
        attempts += 1
        
    print("⚠️ [thumbnail] All Imagen models failed. Trying Pexels stock photo fallback...")
    pexels_bg = _generate_pexels_background(prompt_context)
    if pexels_bg:
        return pexels_bg
        
    print("⚠️ [thumbnail] Pexels fallback failed. Trying Pollinations AI fallback...")
    pollinations_bg = _generate_pollinations_background(prompt_context)
    if pollinations_bg:
        return pollinations_bg
        
    print("⚠️ [thumbnail] All backends failed. Using solid dark fallback.")
    return Image.new("RGB", (THUMB_W, THUMB_H), (15, 15, 22))


# ══════════════════════════════════════════════════════════════════════════════
# ── LAYOUT A: "MYSTERY BOX" (Original style, refined) ───────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _layout_mystery_box(canvas, draw, title, headline, accent_color, secondary_color, cat_emoji):
    """Giant emoji + short Tamil hook + red badge. High curiosity gap."""
    
    # Apply a semi-translucent dark vignette over the background
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    for x in range(0, THUMB_W):
        alpha = int(240 * (1.0 - (x / THUMB_W)))
        o_draw.line([x, 0, x, THUMB_H], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    
    # "தெரியுமா?" badge
    badge_text = "தெரியுமா?"
    font_badge = get_font_for_text(badge_text, 45, "extrabold")
    bbox = font_badge.getbbox(badge_text)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx, by = 80, 80
    draw.rounded_rectangle([bx-25, by-15, bx+bw+25, by+bh+15], radius=20, fill=(220, 20, 60, 255))
    draw.rounded_rectangle([bx-25, by-15, bx+bw+25, by+bh+15], radius=20, outline=(255, 215, 0, 255), width=3)
    draw.text((bx, by-2), badge_text, fill=(255, 255, 255, 255), font=font_badge)
    
    # Tamil title text with backing plate
    hook_lines = [title]
    if len(title) > 20:
        words = title.split()
        mid = len(words) // 2
        hook_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        
    y = 200
    r, g, b = accent_color
    for line in hook_lines[:2]:
        font_title = get_font_for_text(line, 65, "extrabold")
        bbox = font_title.getbbox(line)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rounded_rectangle([60, y-10, 80+lw, y+lh+20], radius=15, fill=(10, 10, 15, 200))
        for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2), (0,3)]:
            draw.text((80+ox, y+oy), line, fill=(0,0,0,255), font=font_title)
        draw.text((80, y), line, fill=(r, g, b, 255), font=font_title)
        y += lh + 50
        
    # Trending fire badge (top-right)
    try:
        badge_fire = "🔥 TRENDING"
        font_fire = get_font_for_text(badge_fire, 32, "extrabold")
        fb = font_fire.getbbox(badge_fire)
        fbw, fbh = fb[2] - fb[0], fb[3] - fb[1]
        fx, fy = THUMB_W - fbw - 100, 80
        draw.rounded_rectangle([fx-20, fy-10, fx+fbw+20, fy+fbh+10], radius=15, fill=(255, 69, 0, 240))
        draw.text((fx, fy-2), badge_fire, fill=(255, 255, 255, 255), font=font_fire)
    except Exception:
        pass
    
    # Shocked emoji overlay (bottom right)
    try:
        font_emoji = get_font_for_text("😱", 130, "bold")
        ex, ey = THUMB_W - 250, THUMB_H - 220
        draw.text((ex+5, ey+5), "😱", fill=(0,0,0,180), font=font_emoji)
        draw.text((ex, ey), "😱", fill=(255,255,255,255), font=font_emoji)
    except Exception:
        pass
    
    return canvas


# ══════════════════════════════════════════════════════════════════════════════
# ── LAYOUT B: "NUMBER SHOCK" ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _layout_number_shock(canvas, draw, title, headline, accent_color, secondary_color, cat_emoji):
    """Split background with huge stat/number in center. High impact."""
    
    # Dark overlay on left half, accent tint on right half
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    # Left side: dark overlay
    o_draw.rectangle([0, 0, THUMB_W // 2, THUMB_H], fill=(0, 0, 0, 180))
    # Right side: accent-tinted overlay
    r, g, b = accent_color
    o_draw.rectangle([THUMB_W // 2, 0, THUMB_W, THUMB_H], fill=(r, g, b, 40))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    
    # Extract a number or key stat from the title (if any digits exist)
    import re
    numbers = re.findall(r'\d[\d,\.]*', title)
    stat_text = numbers[0] if numbers else cat_emoji
    
    # Giant stat number in center
    font_stat = get_font_for_text(stat_text, 180, "extrabold")
    bbox = font_stat.getbbox(stat_text)
    sw, sh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    sx = (THUMB_W - sw) // 2
    sy = (THUMB_H - sh) // 2 - 40
    
    # Shadow
    draw.text((sx+4, sy+4), stat_text, fill=(0, 0, 0, 200), font=font_stat)
    draw.text((sx, sy), stat_text, fill=(r, g, b, 255), font=font_stat)
    
    # Title below the stat
    hook_lines = [title]
    if len(title) > 25:
        words = title.split()
        mid = len(words) // 2
        hook_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    
    y = sy + sh + 30
    for line in hook_lines[:2]:
        font_title = get_font_for_text(line, 48, "extrabold")
        bbox = font_title.getbbox(line)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lx = (THUMB_W - lw) // 2
        # Dark backing plate
        draw.rounded_rectangle([lx - 20, y - 5, lx + lw + 20, y + lh + 10], radius=10, fill=(10, 10, 15, 220))
        draw.text((lx+2, y+2), line, fill=(0, 0, 0, 200), font=font_title)
        draw.text((lx, y), line, fill=(255, 255, 255, 255), font=font_title)
        y += lh + 25
    
    # "தெரியுமா?" badge (top-left)
    badge_text = "தெரியுமா?"
    font_badge = get_font_for_text(badge_text, 38, "extrabold")
    bbox = font_badge.getbbox(badge_text)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle([50, 50, 50+bw+40, 50+bh+20], radius=15, fill=(r, g, b, 255))
    draw.text((70, 60), badge_text, fill=(10, 10, 10, 255), font=font_badge)
    
    return canvas


# ══════════════════════════════════════════════════════════════════════════════
# ── LAYOUT C: "SPOTLIGHT FOCUS" ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _layout_spotlight_focus(canvas, draw, title, headline, accent_color, secondary_color, cat_emoji):
    """Single cinematic subject with circular spotlight vignette + glow text."""
    
    # Radial vignette: dark edges, bright center
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    max_r = int(math.sqrt((THUMB_W/2)**2 + (THUMB_H/2)**2))
    for radius in range(max_r, 0, -5):
        alpha = int(200 * (radius / max_r) ** 1.5)
        alpha = min(255, alpha)
        cx, cy = THUMB_W // 2, THUMB_H // 2
        o_draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    
    r, g, b = accent_color
    
    # Category emoji (large, center-top)
    try:
        font_emoji = get_font_for_text(cat_emoji, 100, "bold")
        bbox = font_emoji.getbbox(cat_emoji)
        ew = bbox[2] - bbox[0]
        ex = (THUMB_W - ew) // 2
        draw.text((ex+3, 63), cat_emoji, fill=(0,0,0,150), font=font_emoji)
        draw.text((ex, 60), cat_emoji, fill=(255,255,255,255), font=font_emoji)
    except Exception:
        pass
    
    # 2-line title with glow effect
    hook_lines = [title]
    if len(title) > 18:
        words = title.split()
        mid = len(words) // 2
        hook_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    
    y = THUMB_H // 2 - 20
    for line in hook_lines[:2]:
        font_title = get_font_for_text(line, 62, "extrabold")
        bbox = font_title.getbbox(line)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        lx = (THUMB_W - lw) // 2
        
        # Glow effect: draw text multiple times with slight offsets in accent color
        for ox, oy in [(-3,-3), (3,-3), (-3,3), (3,3), (-2,0), (2,0), (0,-2), (0,2)]:
            draw.text((lx+ox, y+oy), line, fill=(r, g, b, 100), font=font_title)
        # Main text
        draw.text((lx+2, y+2), line, fill=(0, 0, 0, 255), font=font_title)
        draw.text((lx, y), line, fill=(255, 255, 255, 255), font=font_title)
        y += lh + 35
    
    # Bottom accent bar
    draw.rectangle([0, THUMB_H - 18, THUMB_W, THUMB_H], fill=(r, g, b, 255))
    
    # "Simple Tips by VJ" branding (bottom-left)
    try:
        brand_font = get_font_for_text("Simple Tips by VJ", 26, "bold")
        draw.text((42, THUMB_H - 55), "Simple Tips by VJ", fill=(255, 255, 255, 180), font=brand_font)
    except Exception:
        pass
    
    return canvas


# ══════════════════════════════════════════════════════════════════════════════
# ── LAYOUT D: "CLEAN MODERN" ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _layout_clean_modern(canvas, draw, title, headline, accent_color, secondary_color, cat_emoji):
    """Gradient background, large Tamil text, category-colored accent bar. Minimal and premium."""
    
    r, g, b = accent_color
    
    # Smooth gradient overlay from dark-left to accent-tinted-right
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    for x in range(THUMB_W):
        ratio = x / THUMB_W
        # Blend from dark (0,0,0) to slightly accent-tinted
        cr = int(r * ratio * 0.15)
        cg = int(g * ratio * 0.15)
        cb = int(b * ratio * 0.15)
        alpha = int(230 - 80 * ratio)
        o_draw.line([x, 0, x, THUMB_H], fill=(cr, cg, cb, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    
    # Left accent bar (vertical)
    draw.rectangle([0, 0, 12, THUMB_H], fill=(r, g, b, 255))
    
    # Category pill badge (top-left)
    badge_text = f"{cat_emoji} தெரியுமா?"
    font_badge = get_font_for_text(badge_text, 36, "bold")
    bbox = font_badge.getbbox(badge_text)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.rounded_rectangle([40, 50, 40+bw+40, 50+bh+20], radius=18, fill=(r, g, b, 255))
    draw.text((60, 60), badge_text, fill=(10, 10, 10, 255), font=font_badge)
    
    # Large title text (left-aligned)
    hook_lines = [title]
    if len(title) > 16:
        words = title.split()
        if len(words) > 2:
            # Try to split into 2-3 lines
            third = max(1, len(words) // 3)
            hook_lines = []
            for i in range(0, len(words), third):
                hook_lines.append(" ".join(words[i:i+third]))
    
    y = 180
    for line in hook_lines[:3]:
        font_title = get_font_for_text(line, 70, "extrabold")
        bbox = font_title.getbbox(line)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        
        # Drop shadow
        for ox, oy in [(-2,-2), (2,2), (0,3)]:
            draw.text((50+ox, y+oy), line, fill=(0, 0, 0, 255), font=font_title)
        draw.text((50, y), line, fill=(255, 255, 255, 255), font=font_title)
        y += lh + 20
    
    # Bottom accent strip
    draw.rectangle([0, THUMB_H - 10, THUMB_W, THUMB_H], fill=(r, g, b, 255))
    
    # Right-side large emoji (decorative)
    try:
        font_emoji = get_font_for_text(cat_emoji, 200, "bold")
        bbox = font_emoji.getbbox(cat_emoji)
        ew = bbox[2] - bbox[0]
        draw.text((THUMB_W - ew - 40 + 5, THUMB_H // 2 - 120 + 5), cat_emoji, fill=(0,0,0,80), font=font_emoji)
        draw.text((THUMB_W - ew - 40, THUMB_H // 2 - 120), cat_emoji, fill=(255,255,255,120), font=font_emoji)
    except Exception:
        pass
    
    return canvas


# ══════════════════════════════════════════════════════════════════════════════
# ── MAIN THUMBNAIL GENERATOR ─────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

# Layout registry
_LAYOUT_REGISTRY = [
    ("Mystery Box", _layout_mystery_box),
    ("Number Shock", _layout_number_shock),
    ("Spotlight Focus", _layout_spotlight_focus),
    ("Clean Modern", _layout_clean_modern),
]


def generate_thumbnail(script_json):
    """
    Generates a CTR-boosting infotainment thumbnail.
    Randomly selects from 4 layout variants for natural A/B testing.
    Uses category-specific color palettes for brand consistency.
    """
    title = script_json.get("title", "சுவாரசியமான தகவல்")
    headline = script_json.get("original_news_headline", title)
    
    # Resolve category colors
    accent_color, secondary_color, cat_emoji = _get_accent_colors(script_json)
    
    # 1. Fetch Background
    bg = _generate_imagen_background(headline)
    canvas = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    
    # 2. Select layout variant randomly
    layout_name, layout_fn = random.choice(_LAYOUT_REGISTRY)
    print(f"🎨 [thumbnail] Selected layout: {layout_name}")
    
    # 3. Apply the selected layout
    canvas = layout_fn(canvas, draw, title, headline, accent_color, secondary_color, cat_emoji)
    draw = ImageDraw.Draw(canvas)
    
    # 4. Common branding strip on bottom (all layouts)
    r, g, b = accent_color
    draw.rectangle([0, THUMB_H-6, THUMB_W, THUMB_H], fill=(r, g, b, 255))
    
    # Save JPEG
    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"thumbnail_{today_str}.jpg")
    canvas.save(out_path, "JPEG", quality=95)
    print(f"🎉 [thumbnail] Custom thumbnail ({layout_name}) saved to: {out_path}")
    
    return out_path
