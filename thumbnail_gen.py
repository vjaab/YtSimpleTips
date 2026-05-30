"""
thumbnail_gen.py — Premium Faceless Infotainment Thumbnail Generator.
Generates highly click-worthy Tamil thumbnails using Imagen-3 and Noto Sans Tamil.
"""

import os
import random
import time
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from google import genai
from config import GEMINI_API_KEY, OUTPUT_DIR, ASSETS_DIR
from infographic_gen import get_font_for_text

THUMB_W, THUMB_H = 1280, 720  # Standard YouTube 16:9 Thumbnail size

def _generate_imagen_background(prompt_context):
    """Generates an eye-catching background image via Imagen."""
    print(f"🎨 [thumbnail] Generating background for context: {prompt_context[:50]}...")
    client = genai.Client(api_key=GEMINI_API_KEY)
    
    prompt = (
        f"A striking, highly detailed, high-contrast background image related to: {prompt_context}. "
        "Cinematic studio lighting, rich colors, photorealistic, 8k, landscape 16:9 aspect ratio. "
        "No text, no watermarks, no faces."
    )
    
    try:
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
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
            return Image.open(temp_path)
    except Exception as e:
        print(f"⚠️ [thumbnail] Imagen background generation failed: {e}. Reusing default visual.")
        
    # Fallback solid dark canvas
    return Image.new("RGB", (THUMB_W, THUMB_H), (15, 15, 22))

def generate_thumbnail(script_json):
    """
    Generates a CTR-boosting infotainment thumbnail:
    - Background generated via Imagen based on the topic.
    - Large curiosity-gap Tamil title with drop shadow.
    - Glowing "தெரியுமா?" (Did You Know?) badge.
    - Shocked emoji overlay for high clickability.
    """
    title = script_json.get("title", "சுவாரசியமான தகவல்")
    headline = script_json.get("original_news_headline", title)
    
    # 1. Fetch Background
    bg = _generate_imagen_background(headline)
    canvas = bg.resize((THUMB_W, THUMB_H), Image.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    
    # Apply a semi-translucent dark vignette over the background to ensure text pop
    overlay = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    # Gradient from left to right (darker on left for text placement)
    for x in range(0, THUMB_W):
        alpha = int(220 * (1.0 - (x / THUMB_W)))
        o_draw.line([x, 0, x, THUMB_H], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    
    # 2. Draw "தெரியுமா?" (Did You Know?) glowing badge
    badge_text = "தெரியுமா?"
    font_badge = get_font_for_text(badge_text, 45, "extrabold")
    bbox = font_badge.getbbox(badge_text)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    bx, by = 80, 80
    draw.rounded_rectangle([bx-25, by-15, bx+bw+25, by+bh+15], radius=20, fill=(220, 20, 60, 255)) # Crimson red
    draw.rounded_rectangle([bx-25, by-15, bx+bw+25, by+bh+15], radius=20, outline=(255, 215, 0, 255), width=3) # Golden glow border
    draw.text((bx, by-2), badge_text, fill=(255, 255, 255, 255), font=font_badge)
    
    # 3. Draw Tamil Hook Title Text
    # Let's pick a hook or split title to 2 lines
    hook_lines = [title]
    if len(title) > 20:
        # Try splitting at space
        words = title.split()
        mid = len(words) // 2
        hook_lines = [" ".join(words[:mid]), " ".join(words[mid:])]
        
    y = 200
    for line in hook_lines[:2]:
        font_title = get_font_for_text(line, 65, "extrabold")
        
        # Rounded black backing plate for maximum readability
        bbox = font_title.getbbox(line)
        lw, lh = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.rounded_rectangle([60, y-10, 80+lw, y+lh+20], radius=15, fill=(10, 10, 15, 200))
        
        # Multidirectional text shadow
        for ox, oy in [(-2,-2), (2,-2), (-2,2), (2,2), (0,3)]:
            draw.text((80+ox, y+oy), line, fill=(0,0,0,255), font=font_title)
            
        draw.text((80, y), line, fill=(255, 215, 0, 255), font=font_title) # Gold yellow text
        y += lh + 50
        
    # 4. Shocked emoji overlay on bottom right
    try:
        font_emoji = get_font_for_text("😱", 130, "bold")
        ex, ey = THUMB_W - 250, THUMB_H - 220
        # Shadow
        draw.text((ex+5, ey+5), "😱", fill=(0,0,0,180), font=font_emoji)
        draw.text((ex, ey), "😱", fill=(255,255,255,255), font=font_emoji)
    except:
        pass
        
    # 5. Branding strip on bottom
    draw.rectangle([0, THUMB_H-12, THUMB_W, THUMB_H], fill=(255, 215, 0, 255))
    
    # Save JPEG
    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"thumbnail_{today_str}.jpg")
    canvas.save(out_path, "JPEG", quality=95)
    print(f"🎉 [thumbnail] Custom thumbnail saved to: {out_path}")
    
    return out_path
