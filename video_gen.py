"""
video_gen.py — 15-Layer Faceless Video Rendering Engine with Bilingual Tamil Captions.
V2: Dual-layer captions, advanced transitions, retention overlays, seamless loop, category colors.
Compiles Ken Burns images, Pexels video clips, Veo AI clips, and infographic cards
with mixed Tamil+English kinetic captions.

Enhanced with: Layout Profile System (YPP Compliance), Entity Overlays, Advanced Transitions
"""

import os
import shutil
import cv2
import numpy as np
import random
import math
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, VideoClip,
    CompositeVideoClip, concatenate_videoclips, afx, vfx
)
from pydub import AudioSegment

from config import (
    ASSETS_DIR, OUTPUT_DIR, LOGS_DIR, BGM_VOLUME, ENABLE_KINETIC_CAPTIONS, ENABLE_WATERMARK,
    ENABLE_FLASH_TRANSITIONS, ENABLE_EMOJI_OVERLAYS,
    ENABLE_DUAL_CAPTIONS, ENABLE_ADVANCED_TRANSITIONS, ENABLE_CATEGORY_COLORS,
    ENABLE_FACT_COUNTER, ENABLE_COUNTDOWN_TIMER, ENABLE_SOUND_ON_INDICATOR,
    ENABLE_SEAMLESS_LOOP, ENABLE_LONGFORM
)
from infographic_gen import build_infographic_clip, get_font_for_text, is_char_supported
from entity_fetcher import fetch_all_entities

FRAME_W, FRAME_H = 1080, 1920  # Default 9:16

# ── DEFAULT COLOR PALETTE (Anime theme - Neon Orange & Electric Blue) ──
_DEFAULT_PALETTE = {
    "primary": (255, 107, 53),           # Neon Orange
    "secondary": (15, 15, 10),
    "caption_highlight": (0, 212, 255),  # Electric Blue
    "progress_bar": (0, 212, 255),
}

# ════════════════════════════════════════════════════════════════════════════════
# ── LAYOUT PROFILE SYSTEM (YPP Compliance) ────────────────────────────────────
# Each video gets a deterministic-but-unique visual layout based on headline hash.
# This breaks the 'template fingerprint' that YouTube's Inauthentic Content policy flags.
# ═════════════════════════════════════════════════════════════════════════════════

def _generate_layout_profile(headline: str) -> dict:
    """
    Generate a deterministic-but-unique visual layout for each video based on its headline hash.
    This breaks the 'template fingerprint' that YouTube's Inauthentic Content policy flags.
    """
    seed = int(hashlib.md5(headline.encode()).hexdigest(), 16)
    rng = random.Random(seed)

    # Gradient
    gradient_height_pct = rng.uniform(0.40, 0.50)          # 40-50-50% (was fixed 45%)
    gradient_position = rng.choice(["bottom", "top"])       # was always bottom

    # Title box
    title_bottom_gap = rng.randint(165, 220)                # was fixed 192px

    # Particles
    particle_style = rng.choice(["bokeh", "digital", "stars", "digital_rain", "lens_dust"])

    # Progress bar
    progress_bar_height = rng.randint(4, 8)                 # was fixed 6px
    progress_bar_position = rng.choice(["bottom", "top"])    # was always bottom

    # Hook transition
    hook_transition_time = rng.uniform(3.5, 5.0)            # was fixed 4.2s

    # Avatar horizontal offset
    avatar_x_offset = rng.randint(-60, 60)                  # was always centered

    # Subtitle Y jitter
    subtitle_y_jitter = rng.randint(-30, 30)                # was fixed 0

    # CTA end card style
    cta_variant = rng.randint(0, 3)                         # 4 CTA styles
    cta_pill_colors = [
        (204, 255, 0),    # Neon green (original)
        (0, 200, 255),    # Cyan
        (255, 100, 100),  # Coral
        (180, 130, 255),  # Lavender
    ]
    cta_pill_color = cta_pill_colors[cta_variant]
    cta_headlines = [
        "Full {topic} guide + source code",
        "Get the complete {topic} breakdown",
        "{topic} implementation playbook",
        "Deep dive: {topic} explained",
    ]
    cta_headline_template = cta_headlines[cta_variant]
    cta_descriptions = [
        "Join the community 🚀",
        "Free access — link in bio 📥",
        "Grab it before it's gone ⚡",
        "Level up your stack 🔧",
    ]
    cta_description = cta_descriptions[cta_variant]

    profile = {
        "gradient_height_pct": gradient_height_pct,
        "gradient_position": gradient_position,
        "title_bottom_gap": title_bottom_gap,
        "particle_style": particle_style,
        "progress_bar_height": progress_bar_height,
        "progress_bar_position": progress_bar_position,
        "hook_transition_time": hook_transition_time,
        "avatar_x_offset": avatar_x_offset,
        "subtitle_y_jitter": subtitle_y_jitter,
        "cta_pill_color": cta_pill_color,
        "cta_headline_template": cta_headline_template,
        "cta_description": cta_description,
    }
    print(f"🎲 Layout Profile: gradient={gradient_position}@{gradient_height_pct:.0%}, "
          f"particles={particle_style}, title_gap={title_bottom_gap}px, "
          f"progress={progress_bar_position}@{progress_bar_height}px, "
          f"avatar_offset={avatar_x_offset}px, cta_variant={cta_variant}")
    return profile


def apply_tech_grade(frame):
    """
    Applies a premium cinematic color grading to the background image:
    1. Contrast enhancement via an S-curve.
    2. Split-toning: cool teal/blue in shadows, warm orange/gold in highlights.
    """
    # Convert to float32 in [0, 1]
    arr = frame.astype(np.float32) / 255.0

    # 1. S-curve contrast boost: f(x) = 3x^2 - 2x^3
    arr = 3 * (arr ** 2) - 2 * (arr ** 3)

    # 2. Split toning based on luminance
    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    lum = np.expand_dims(lum, axis=2) # Shape: (H, W, 1)

    shadow_mask = np.clip(1.0 - lum, 0, 1)
    highlight_mask = np.clip(lum, 0, 1)

    # Cool shadows: slight boost to Blue, minor boost to Green
    arr[:, :, 2] += shadow_mask[:, :, 0] * 0.04  # Blue
    arr[:, :, 1] += shadow_mask[:, :, 0] * 0.01  # Green

    # Warm highlights: slight boost to Red, drop Blue
    arr[:, :, 0] += highlight_mask[:, :, 0] * 0.05  # Red
    arr[:, :, 1] += highlight_mask[:, :, 0] * 0.02  # Green
    arr[:, :, 2] -= highlight_mask[:, :, 0] * 0.02  # Reduce Blue

    return np.clip(arr * 255.0, 0, 255).astype(np.uint8).astype(np.uint8)


# Per-video color grading variation seed (anti-repetition for YPP compliance)
# Each video gets slightly different color parameters so no two look identical
_COLOR_GRADE_SEED = random.Random()
_COLOR_GRADE_SEED.seed()  # Random seed per pipeline run
_CG_SAT_FACTOR = _COLOR_GRADE_SEED.uniform(0.85, 0.95)    # Saturation: 0.85-0.95
_CG_GAMMA = _COLOR_GRADE_SEED.uniform(1.15, 1.25)          # Gamma: 1.15-1.25
_CG_CONTRAST = _COLOR_GRADE_SEED.uniform(1.12, 1.18)       # Contrast: 1.12-1.18

def desaturate_frame(frame, factor=0.85):
    """Reduces saturation of an RGB frame by factor (0.85 = 15% desaturation)."""
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] *= factor
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

# Per-video color grading variation seed (anti-repetition for YPP compliance)
# Each video gets slightly different color parameters so no two look identical
import random as _cg_random
_COLOR_GRADE_SEED = _cg_random.Random()
_COLOR_GRADE_SEED.seed()  # Random seed per pipeline run
_CG_SAT_FACTOR = _COLOR_GRADE_SEED.uniform(0.85, 0.95)    # Saturation: 0.85-0.95
_CG_GAMMA = _COLOR_GRADE_SEED.uniform(1.15, 1.25)          # Gamma: 1.15-1.25
_CG_CONTRAST = _COLOR_GRADE_SEED.uniform(1.12, 1.18)       # Contrast: 1.12-1.18

def apply_cartoon_color_grade(frame):
    """
    Simulates Pixar-style 3D cartoon color grading with per-video randomized variation:
    - Vibrant, warm colors (slightly varied per video)
    - Depth-of-field lighting feel (midtones enhanced)
    - Slightly boosted saturation/vibrancy for a high-quality claymation render
    - Per-video variation prevents YouTube 'repetitive content' flags
    """
    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV).astype(np.float32)
    hsv[:, :, 1] *= _CG_SAT_FACTOR  # Per-video saturation variation
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    frame = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
    
    frame_float = frame.astype(np.float32)
    frame_graded = 255.0 * np.power(frame_float / 255.0, _CG_GAMMA)  # Per-video gamma
    
    mid = 128.0
    frame_graded = mid + _CG_CONTRAST * (frame_graded - mid)  # Per-video contrast
    frame_graded = np.clip(frame_graded, 0, 255).astype(np.uint8)
    
    return frame_graded

def _apply_cartoon_flash_cut(outgoing, incoming, progress):
    """
    Fast cartoon-style flash cut:
    - 2 frames (approx first 25% of transition) white flash.
    - Zoom incoming by 1.05.
    """
    h, w = incoming.shape[:2]
    zoom_scale = 1.0 + 0.05 * progress
    new_w = int(w * zoom_scale)
    new_h = int(h * zoom_scale)
    if new_w > 0 and new_h > 0:
        resized_in = cv2.resize(incoming, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        x1 = (new_w - w) // 2
        y1 = (new_h - h) // 2
        zoomed_in = resized_in[y1:y1+h, x1:x1+w]
    else:
        zoomed_in = incoming

    new_w_out = int(w * (1.0 + 0.02 * progress))
    new_h_out = int(h * (1.0 + 0.02 * progress))
    if new_w_out > 0 and new_h_out > 0:
        resized_out = cv2.resize(outgoing, (new_w_out, new_h_out), interpolation=cv2.INTER_LINEAR)
        x1_out = (new_w_out - w) // 2
        y1_out = (new_h_out - h) // 2
        zoomed_out = resized_out[y1_out:y1_out+h, x1_out:x1_out+w]
    else:
        zoomed_out = outgoing

    if progress < 0.25:
        flash_intensity = progress / 0.25
        flash_frame = np.full_like(zoomed_out, 255)
        blended = cv2.addWeighted(zoomed_out, 1.0 - flash_intensity, flash_frame, flash_intensity, 0)
    else:
        flash_intensity = 1.0 - ((progress - 0.25) / 0.75)
        flash_frame = np.full_like(zoomed_in, 255)
        blended = cv2.addWeighted(zoomed_in, 1.0 - flash_intensity, flash_frame, flash_intensity, 0)

    return blended

def set_resolutions(is_longform=False):
    global FRAME_W, FRAME_H
    if is_longform:
        FRAME_W, FRAME_H = 1920, 1080
    else:
        FRAME_W, FRAME_H = 1080, 1920

def _prepare_evidence_canvas(img, url=None):
    """Draws an obsidian border and floating URL pill around screenshot evidence."""
    canvas = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    
    # Scale image to fit inside 90% of screen width
    target_w = int(FRAME_W * 0.90)
    ratio = target_w / float(img.width)
    target_h = int(img.height * ratio)
    
    # If height is too tall, scale down
    max_h = int(FRAME_H * 0.70)
    if target_h > max_h:
        ratio = max_h / float(img.height)
        target_w = int(img.width * ratio)
        target_h = max_h
        
    scaled_img = img.resize((target_w, target_h), Image.LANCZOS)
    
    cx = (FRAME_W - target_w) // 2
    cy = (FRAME_H - target_h) // 2
    
    draw = ImageDraw.Draw(canvas)
    
    # Shadow
    draw.rounded_rectangle([cx+8, cy+16, cx+target_w+8, cy+target_h+16], radius=24, fill=(0,0,0,140))
    # Border with sleek neon accent
    draw.rounded_rectangle([cx-4, cy-4, cx+target_w+4, cy+target_h+4], radius=24, fill=(204,255,0,255))
    # Inner Image
    canvas.paste(scaled_img, (cx, cy))
    
    # Floating URL banner
    if url:
        url_text = url.replace("https://", "").replace("http://", "").split("/")[0]
        font = get_font_for_text(url_text, 28, "bold")
        tw, th = font.getbbox(url_text)[2] - font.getbbox(url_text)[0], font.getbbox(url_text)[3] - font.getbbox(url_text)[1]
        
        banner_w = tw + 60
        banner_h = th + 24
        bx = (FRAME_W - banner_w) // 2
        by = cy - banner_h - 20
        
        draw.rounded_rectangle([bx, by, bx+banner_w, by+banner_h], radius=15, fill=(15,15,20,240))
        draw.rounded_rectangle([bx, by, bx+banner_w, by+banner_h], radius=15, outline=(204,255,0,255), width=2)
        draw.text((bx + 30, by + 12), url_text, fill=(204,255,0,255), font=font)
        
    return canvas

def prepare_top_panel_screenshot_clip(screenshot_path, duration):
    """Loads screenshot, pads/crops to 1080x864, and returns an ImageClip."""
    if not screenshot_path or not os.path.exists(screenshot_path):
        # Create a fallback blank card or solid color if file not found
        img = Image.new("RGBA", (1080, 864), (15, 15, 20, 255))
        return ImageClip(np.array(img)).with_duration(duration)
        
    img = Image.open(screenshot_path).convert("RGBA")
    
    # Target size is 1080 x 864
    target_w, target_h = 1080, 864
    
    canvas = Image.new("RGBA", (target_w, target_h), (10, 10, 15, 255)) # Dark charcoal/black bg
    
    img_w, img_h = img.size
    aspect = img_w / float(img_h)
    
    # If it is vertical (height > width, e.g. mobile screenshot), we scale to fit height 864 and pad the sides
    if aspect < (target_w / float(target_h)):
        new_h = target_h
        new_w = int(new_h * aspect)
        resized_img = img.resize((new_w, new_h), Image.LANCZOS)
        cx = (target_w - new_w) // 2
        canvas.paste(resized_img, (cx, 0))
    else:
        # Landscape: scale to fit width 1080 and pad the top/bottom
        new_w = target_w
        new_h = int(new_w / aspect)
        resized_img = img.resize((new_w, new_h), Image.LANCZOS)
        cy = (target_h - new_h) // 2
        canvas.paste(resized_img, (0, cy))
        
    return ImageClip(np.array(canvas)).with_duration(duration)
def create_middle_title_banner_clip(title_text, duration, accent_color=(204, 255, 0), style_mode=0):
    """Creates a persistent title/hook banner of size 1080x192 with various visual styles."""
    width, height = 1080, 192
    r, g, b = accent_color
    
    if style_mode == 1:
        # Category accent solid background, dark text
        img = Image.new("RGBA", (width, height), (r, g, b, 255))
        text_fill = (15, 15, 15, 255)
        shadow_fill = (255, 255, 255, 120)
    elif style_mode == 2:
        # Dark translucent / glassmorphic, glowing accent text
        img = Image.new("RGBA", (width, height), (15, 15, 20, 200))
        text_fill = (r, g, b, 255)
        shadow_fill = (0, 0, 0, 180)
    else:
        # Style 0: Solid black background, white text
        img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        text_fill = (255, 255, 255, 255)
        shadow_fill = (10, 10, 15, 200)
        
    draw = ImageDraw.Draw(img)
    
    # Draw border lines or glowing accent lines at top and bottom of the banner
    if style_mode != 1:
        draw.line([(0, 0), (width, 0)], fill=(r, g, b, 255), width=4) # Top border line
        draw.line([(0, height - 4), (width, height - 4)], fill=(r, g, b, 255), width=4) # Bottom border line
    else:
        draw.line([(0, 0), (width, 0)], fill=(255, 255, 255, 255), width=4) # White top border line
        draw.line([(0, height - 4), (width, height - 4)], fill=(255, 255, 255, 255), width=4) # White bottom border line
    
    title_text = "".join(c for c in title_text if ord(c) < 0x2000).strip()
    title_text = title_text.upper().strip()
    
    # We want a bold, high-impact font
    font_size = 48
    font = get_font_for_text(title_text, font_size, "extrabold")
    
    # Adjust font size if text is too long to fit in 760px wide to leave room for countdown timer on the right
    max_text_w = 760
    for fs in range(48, 24, -2):
        font = get_font_for_text(title_text, fs, "extrabold")
        bbox = font.getbbox(title_text)
        tw = bbox[2] - bbox[0]
        if tw <= max_text_w:
            break
            
    bbox = font.getbbox(title_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Center the text in the banner
    tx = (width - tw) // 2
    ty = (height - th) // 2 - bbox[1] # Align vertically
    
    # Draw bold text with drop shadow
    draw.text((tx + 2, ty + 2), title_text, fill=shadow_fill, font=font)
    draw.text((tx, ty), title_text, fill=text_fill, font=font)
    
    return ImageClip(np.array(img)).with_duration(duration)


def build_ken_burns(img_path, duration, zoom_direction=None, target_size=(FRAME_W, FRAME_H)):
    """Builds a smooth Ken Burns effect clip with randomized zoom direction."""
    clip = ImageClip(img_path).with_duration(duration)
    w, h = clip.size
    target_w_val, target_h_val = target_size
    
    # Crop to aspect ratio first
    target_h = int(w * target_h_val / target_w_val)
    if target_h <= h:
        y1 = (h - target_h) // 2
        clip = clip.cropped(x1=0, y1=y1, x2=w, y2=y1 + target_h)
    else:
        target_w = int(h * target_w_val / target_h_val)
        x1 = (w - target_w) // 2
        clip = clip.cropped(x1=x1, y1=0, x2=x1 + target_w, y2=h)
        
    # Resize to match target frame dimensions
    clip = clip.resized(new_size=(target_w_val, target_h_val))
    
    # Guard against zero or extremely small duration to prevent NaN division
    safe_duration = max(0.1, duration) if duration else 1.0
    
    # Randomize zoom direction for visual variety
    if zoom_direction is None:
        zoom_direction = random.choice(["in", "out"])
    
    if zoom_direction == "out":
        # Zoom out: start at 1.10x and settle to 1.0x
        clip = clip.resized(lambda t: 1.10 - 0.10 * (t / safe_duration))
    else:
        # Zoom in: start at 1.0x and grow to 1.10x
        clip = clip.resized(lambda t: 1.0 + 0.10 * (t / safe_duration))
    return clip

def _gradient_overlay(duration):
    """Draws a subtle radial vignette to frame the whiteboard theme and guide the eye."""
    w, h = FRAME_W, FRAME_H
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    
    # Soft dark corners fading into the center
    max_diag = math.sqrt(w**2 + h**2) / 2.0
    for r in range(int(max_diag), 0, -15):
        alpha = int(45 * (r / max_diag)**2) # Cap at 45 (approx 17% opacity)
        cx, cy = w // 2, h // 2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=alpha)
        
    # Clear the top half of the vignette (y < 864) to keep top panel visual completely clean
    draw.rectangle([0, 0, w, 864], fill=0)
    
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vignette = Image.new("RGBA", (w, h), (10, 10, 15, 255))
    img = Image.composite(vignette, img, mask)
    return ImageClip(np.array(img)).with_duration(duration)


# ══════════════════════════════════════════════════════════════════════════════
# ── ADVANCED TRANSITION EFFECTS ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _apply_zoom_burst(outgoing, incoming, progress):
    """Zoom out outgoing frame, zoom in incoming frame, and blend."""
    h, w = incoming.shape[:2]
    # Outgoing: zoom from 1.0 up to 1.15
    scale_out = 1.0 + 0.15 * progress
    new_w_out, new_h_out = int(w * scale_out), int(h * scale_out)
    if new_w_out <= 0 or new_h_out <= 0:
        return incoming
    resized_out = cv2.resize(outgoing, (new_w_out, new_h_out), interpolation=cv2.INTER_LINEAR)
    x1_out = (new_w_out - w) // 2
    y1_out = (new_h_out - h) // 2
    cropped_out = resized_out[y1_out:y1_out+h, x1_out:x1_out+w]

    # Incoming: zoom from 0.85 up to 1.0
    scale_in = 0.85 + 0.15 * progress
    new_w_in, new_h_in = int(w * scale_in), int(h * scale_in)
    if new_w_in <= 0 or new_h_in <= 0:
        return incoming
    resized_in = cv2.resize(incoming, (new_w_in, new_h_in), interpolation=cv2.INTER_LINEAR)
    canvas_in = np.zeros_like(incoming)
    if scale_in < 1.0:
        dy = (h - new_h_in) // 2
        dx = (w - new_w_in) // 2
        canvas_in[dy:dy+new_h_in, dx:dx+new_w_in] = resized_in
    else:
        x1_in = (new_w_in - w) // 2
        y1_in = (new_h_in - h) // 2
        canvas_in = resized_in[y1_in:y1_in+h, x1_in:x1_in+w]

    return cv2.addWeighted(cropped_out, 1.0 - progress, canvas_in, progress, 0)

def _apply_rgb_glitch(outgoing, incoming, progress):
    """Blends frames with horizontal scanlines and channel offsets."""
    blended = cv2.addWeighted(outgoing, 1.0 - progress, incoming, progress, 0)
    h, w = blended.shape[:2]
    intensity = int(12 * math.sin(progress * math.pi))
    if intensity < 1:
        return blended
    result = blended.copy()
    # Shift red channel right, blue channel left
    result[:, intensity:, 0] = blended[:, :-intensity, 0]
    result[:, :-intensity, 2] = blended[:, intensity:, 2]
    # Scanline noise
    for y in range(0, h, 6):
        if random.random() < 0.4:
            shift = random.randint(-intensity, intensity)
            if shift > 0:
                result[y, shift:] = result[y, :-shift]
            elif shift < 0:
                result[y, :shift] = result[y, -shift:]
    return result

def _apply_shake(outgoing, incoming, progress):
    """Blends frames with rapid translational shake."""
    blended = cv2.addWeighted(outgoing, 1.0 - progress, incoming, progress, 0)
    h, w = blended.shape[:2]
    intensity = int(8 * math.sin(progress * math.pi))
    if intensity < 1:
        return blended
    ox = random.randint(-intensity, intensity)
    oy = random.randint(-intensity, intensity)
    M = np.float32([[1, 0, ox], [0, 1, oy]])
    return cv2.warpAffine(blended, M, (w, h), borderMode=cv2.BORDER_REFLECT)

def _apply_flash_fade(outgoing, incoming, progress):
    """Fades outgoing to white flash at peak, then fades to incoming."""
    white = np.full_like(incoming, 255)
    if progress < 0.5:
        p_sub = progress / 0.5
        return cv2.addWeighted(outgoing, 1.0 - p_sub, white, p_sub, 0)
    else:
        p_sub = (progress - 0.5) / 0.5
        return cv2.addWeighted(white, 1.0 - p_sub, incoming, p_sub, 0)

def _apply_cross_dissolve(outgoing, incoming, progress):
    """Blends outgoing frame into incoming frame smoothly."""
    return cv2.addWeighted(outgoing, 1.0 - progress, incoming, progress, 0)

# Transition type mapping from retention_cue effect names
TRANSITION_MAP = {
    "zoom_in": _apply_zoom_burst,
    "zoom_burst": _apply_cartoon_flash_cut,
    "hook_impact": _apply_rgb_glitch,
    "glitch": _apply_rgb_glitch,
    "emphasis": _apply_shake,
    "shake": _apply_shake,
    "flash": _apply_cartoon_flash_cut,
    "dissolve": _apply_cross_dissolve,
}

# Pool of transitions for random selection when no specific cue is given
_TRANSITION_POOL = [
    _apply_cartoon_flash_cut,
    _apply_rgb_glitch,
    _apply_cross_dissolve,
    _apply_shake,
]


# ══════════════════════════════════════════════════════════════════════════════
# ── DUAL-LAYER CAPTION SYSTEM ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def render_subtitle_frame(word_status_list, accent_color=(204, 255, 0), y_shift=0, y_jitter=0):
    """Renders high-impact kinetic subtitle frame with dynamic active-word popping."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    base_size = int(60 * (FRAME_W / 1080.0))

    # Form layout and line-wrap words
    words = [wd["word"] for wd in word_status_list]
    word_widths = []

    for i, wd in enumerate(word_status_list):
        is_active = wd["is_active"]
        weight = "extrabold" if is_active else "bold"
        size = int(base_size * 1.15) if is_active else base_size
        font = get_font_for_text(words[i], size, weight)
        bbox = font.getbbox(words[i])
        word_widths.append(bbox[2] - bbox[0])

    max_w = int(FRAME_W * 0.85)

    # Simple wrap
    lines = []
    current_line = []
    current_w = 0
    space_w = int(18 * (FRAME_W / 1080.0))

    for word, w in zip(words, word_widths):
        if not current_line or (current_w + w <= max_w):
            current_line.append(word)
            current_w += w + space_w
        else:
            lines.append(current_line)
            current_line = [word]
            current_w = w + space_w
    if current_line:
        lines.append(current_line)

    line_h = int(95 * (FRAME_W / 1080.0))
    y_pos = 920 - (len(lines) * line_h // 2) + y_shift + y_jitter
    
    # Obsidian back-plate coordinates calculation
    max_line_w = 0
    temp_idx = 0
    for line in lines:
        line_w = sum(word_widths[temp_idx:temp_idx+len(line)]) + space_w * (len(line)-1)
        max_line_w = max(max_line_w, line_w)
        temp_idx += len(line)
        
    pad_x, pad_y = 40, 20
    bx1 = (FRAME_W - max_line_w) // 2 - pad_x
    bx2 = (FRAME_W + max_line_w) // 2 + pad_x
    by1 = y_pos - pad_y
    by2 = y_pos + len(lines) * line_h - (line_h - base_size) + pad_y
    
    # Use accent color for the border glow
    border_r, border_g, border_b = accent_color
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=15, fill=(10, 10, 15, 230), outline=(border_r, border_g, border_b, 90), width=2)
    
    # Draw word by word
    word_idx = 0
    for i, line in enumerate(lines):
        line_y = y_pos + i * line_h
        line_w = sum(word_widths[word_idx:word_idx+len(line)]) + space_w * (len(line)-1)
        cur_x = (FRAME_W - line_w) // 2
        
        for word_text in line:
            wd = word_status_list[word_idx]
            is_active = wd["is_active"]
            
            if is_active:
                font = get_font_for_text(word_text, int(base_size * 1.15), "extrabold")
                # Cleaner 2px glow behind the active word (reduced from 3px for sharper look)
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        if abs(dx) + abs(dy) > 0:
                            draw.text((cur_x + dx, line_y - 4 + dy), word_text, fill=(0, 212, 255, 90), font=font)
                # Main active text is bold white
                draw.text((cur_x, line_y - 4), word_text, fill=(255, 255, 255, 255), font=font)
            else:
                c_fill = (255, 255, 255, 255)
                font = get_font_for_text(word_text, base_size, "bold")
                draw.text((cur_x+2, line_y+2), word_text, fill=(0,0,0,180), font=font)
                draw.text((cur_x, line_y), word_text, fill=c_fill, font=font)
                
            cur_x += word_widths[word_idx] + space_w
            word_idx += 1
            
    return canvas_to_clip(img)

def render_whiteboard_caption(text, progress=1.0, accent_color=(204, 255, 0)):
    """Renders a high-impact whiteboard-style English keyword/phrase caption with category-colored highlighter."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    text = text.upper().strip()
    if not text:
        return np.array(img)
        
    base_size = int(72 * (FRAME_W / 1080.0))
    font = get_font_for_text(text, base_size, "extrabold")
    
    # Calculate bounds
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    cx = (FRAME_W - tw) // 2
    cy = 1040
    
    # Pop-in animation: scale from 0 → 1.1 → 1.0
    if progress < 0.15:
        # Quick scale up from 0.3 to 1.1
        scale = 0.3 + (0.8 * (progress / 0.15))
    elif progress < 0.3:
        # Settle from 1.1 to 1.0
        settle_progress = (progress - 0.15) / 0.15
        scale = 1.1 - 0.1 * settle_progress
    else:
        # Breathing animation
        scale = 1.0 + 0.03 * math.sin((progress - 0.3) * math.pi * 2)
    
    # Highlight backing pill
    pad_x = int(35 * (FRAME_W / 1080.0))
    pad_y = int(18 * (FRAME_W / 1080.0))
    hx1 = cx - pad_x
    hy1 = cy - pad_y
    hx2 = cx + tw + pad_x
    hy2 = cy + th + pad_y
    
    # Pop animation: scale up highlighter based on scale factor
    if scale != 1.0:
        center_x = (hx1 + hx2) / 2
        center_y = (hy1 + hy2) / 2
        hw = (hx2 - hx1) * scale
        hh = (hy2 - hy1) * scale
        hx1 = int(center_x - hw / 2)
        hx2 = int(center_x + hw / 2)
        hy1 = int(center_y - hh / 2)
        hy2 = int(center_y + hh / 2)
        
        # Scale text size as well
        font = get_font_for_text(text, int(base_size * scale), "extrabold")
        bbox = font.getbbox(text)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        cx = (FRAME_W - tw) // 2
        cy = int(center_y - th / 2)
    
    # Highlighter color: Use category accent color
    r, g, b = accent_color
    draw.rounded_rectangle([hx1, hy1, hx2, hy2], radius=15, fill=(r, g, b, 255))
    
    # Clean black marker text
    draw.text((cx, cy), text, fill=(10, 10, 10, 255), font=font)
    
    return np.array(img)

def canvas_to_clip(pil_img):
    return np.array(pil_img.convert("RGBA"))


# ══════════════════════════════════════════════════════════════════════════════
# ── RETENTION OVERLAY RENDERERS ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _render_fact_counter_badge(draw, fact_number, accent_color):
    """Draws a 'FACT #N' pill badge in the top-left corner."""
    badge_text = f"FACT #{fact_number}"
    font = get_font_for_text(badge_text, 28, "bold")
    bbox = font.getbbox(badge_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    bx, by = 40, 1056 + 140  # Below the watermark area in bottom panel
    pw, ph = tw + 30, th + 16
    
    r, g, b = accent_color
    # Dark pill with accent border
    draw.rounded_rectangle([bx, by, bx+pw, by+ph], radius=12, fill=(10, 10, 15, 220))
    draw.rounded_rectangle([bx, by, bx+pw, by+ph], radius=12, outline=(r, g, b, 200), width=2)
    draw.text((bx + 15, by + 8), badge_text, fill=(r, g, b, 255), font=font)

def _render_countdown_timer(draw, t, total_duration, accent_color):
    """Draws a circular countdown arc in the top-right corner."""
    cx, cy = FRAME_W - 70, 96
    radius = 22
    remaining = max(0, total_duration - t)
    progress = t / total_duration  # 0 → 1 as video plays
    
    r, g, b = accent_color
    
    # Background circle (dark)
    draw.ellipse([cx-radius, cy-radius, cx+radius, cy+radius], fill=(20, 20, 25, 200))
    
    # Draw arc using line segments (Pillow arc)
    start_angle = -90  # Start from top
    end_angle = start_angle + int(360 * (1.0 - progress))
    if end_angle > start_angle:
        draw.arc(
            [cx-radius, cy-radius, cx+radius, cy+radius],
            start=start_angle, end=end_angle,
            fill=(r, g, b, 255), width=4
        )
    
    # Time remaining text
    secs = int(remaining)
    time_text = f"{secs}"
    font = get_font_for_text(time_text, 20, "bold")
    bbox = font.getbbox(time_text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), time_text, fill=(255, 255, 255, 230), font=font)

def _render_sound_on_indicator(draw, t, accent_color):
    """Shows a 'Sound ON' indicator with speaker icon in the first 2.5 seconds."""
    if t > 2.5:
        return
    
    # Fade in (0-0.5s), hold (0.5-1.8s), fade out (1.8-2.5s)
    if t < 0.5:
        alpha = int(255 * (t / 0.5))
    elif t < 1.8:
        alpha = 255
    else:
        alpha = int(255 * (1.0 - (t - 1.8) / 0.7))
    
    alpha = max(0, min(255, alpha))
    
    r, g, b = accent_color
    text = "Sound ON"
    font = get_font_for_text(text, 32, "bold")
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    px = (FRAME_W - tw) // 2
    py = 1056 + int(FRAME_H * 0.12)
    
    # Semi-transparent pill background
    draw.rounded_rectangle(
        [px - 25, py - 10, px + tw + 25, py + th + 10],
        radius=20, fill=(10, 10, 15, int(alpha * 0.85))
    )
    draw.rounded_rectangle(
        [px - 25, py - 10, px + tw + 25, py + th + 10],
        radius=20, outline=(r, g, b, alpha), width=2
    )
    draw.text((px, py), text, fill=(255, 255, 255, alpha), font=font)


# Voice fallback warning removed from video rendering — it was visible to viewers.
# Fallback status is still reported in Telegram consent notification.


# ══════════════════════════════════════════════════════════════════════════════
# ── AUDIO MASTERING ──────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def _mix_and_master_audio(voice_path, bgm_path, output_duration, output_path):
    """Mixes voiceover with background music using dynamic ducking for premium sound."""
    print("🎵 [audio_mastering] Mixing and mastering soundtrack...")
    try:
        # Load audio tracks and standardize formats to 44100Hz, Stereo, 16-bit PCM
        # This prevents any resampling-related glitches or digital stuttering.
        voice = AudioSegment.from_file(voice_path).set_frame_rate(44100).set_channels(2).set_sample_width(2)
        
        if bgm_path and os.path.exists(bgm_path):
            bgm = AudioSegment.from_file(bgm_path).set_frame_rate(44100).set_channels(2).set_sample_width(2)
            
            # Loop BGM if shorter than voice
            while len(bgm) < len(voice):
                bgm += bgm
            bgm = bgm[:len(voice)]
            
            # Convert BGM_VOLUME from config to decibels
            # For BGM_VOLUME = 0.08, bgm_base_db will be ~ -21.9 dB
            bgm_base_db = 20 * math.log10(BGM_VOLUME) if BGM_VOLUME > 0 else -60.0
            
            # Target volumes
            # During voice activity: BGM ducked by an extra 11 dB relative to base (e.g., -33 dB)
            # During silence: BGM rises to base + 2 dB (e.g., -20 dB) to fill the gaps
            ducked_db = bgm_base_db - 11
            unducked_db = bgm_base_db + 2
            
            chunk_ms = 100
            targets = []
            
            # Determine target volume for each 100ms chunk
            for i in range(0, len(voice), chunk_ms):
                voice_chunk = voice[i:i+chunk_ms]
                if voice_chunk.dBFS > -40:  # Voice is active
                    targets.append(ducked_db)
                else:  # Silence
                    targets.append(unducked_db)
            
            # Smooth out volume changes using Exponential Moving Average (EMA).
            # This creates a natural volume envelope and completely removes click artifacts at chunk boundaries.
            smoothed = []
            current_vol = unducked_db
            alpha = 0.7  # Smoothing factor (transition takes ~300-500ms)
            for target in targets:
                current_vol = current_vol * alpha + target * (1 - alpha)
                smoothed.append(current_vol)
                
            # Apply the smoothed gain envelope to the BGM chunks
            ducked_bgm = AudioSegment.empty()
            for idx, i in enumerate(range(0, len(bgm), chunk_ms)):
                bgm_chunk = bgm[i:i+chunk_ms]
                ducked_bgm += bgm_chunk + smoothed[idx]
            
            # Gentle fade-in (300ms) and fade-out (500ms) for high-end polish
            ducked_bgm = ducked_bgm.fade_in(300).fade_out(500)
            
            mastered = ducked_bgm.overlay(voice)
            mastered.export(output_path, format="wav")
            print("✅ [audio_mastering] Soundtrack mixed with smooth EMA-ducked BGM!")
        else:
            print(f"⚠️ [audio_mastering] BGM file not found at '{bgm_path}'. Proceeding with raw voiceover.")
            voice.export(output_path, format="wav")
    except Exception as e:
        print(f"⚠️ [audio_mastering] Audio mixing failed: {e}. Copying raw voice.")
        shutil.copy(voice_path, output_path)

def _generate_lipsync_video(audio_path, face_path=None):
    if face_path is None:
        face_path = os.path.join(ASSETS_DIR, "video", "Firefly_video_final.mp4")
    if not os.path.exists(face_path):
        print(f"{os.path.basename(face_path)} not found in assets. Skipping lip sync.")
        return None

    output_path = os.path.join(OUTPUT_DIR, "temp_lipsync.mp4")
    
    # If Kaggle was enabled but failed to return a lipsync (e.g., crashed), do NOT fall back to local MPS/CPU 
    # to avoid extremely long 30+ min processing times.
    has_kaggle = os.path.exists(os.path.expanduser("~/.kaggle/kaggle.json"))
    use_local_only = os.environ.get("USE_LOCAL_ONLY") == "true"
    
    if has_kaggle and not use_local_only:
        print("⚠️ Kaggle GPU was enabled but no lip-sync received. Skipping slow local fallback.")
        return None

    try:
        from lip_sync import get_available_engine, generate_lip_sync
        engine = get_available_engine()
        print(f"🎭 Lip-sync engine: {engine or 'None available'}")

        result = generate_lip_sync(
            face_path=face_path,
            audio_path=audio_path,
            output_path=output_path,
        )

        if result and os.path.exists(result):
            print(f"🎭 Lip-sync successful: {result}")
            return result
    except Exception as e:
        print(f"🎭 Lip-sync helper import/execution failed: {e}")

    print("🎭 Lip-sync generation failed or unavailable.")
    return None

# ══════════════════════════════════════════════════════════════════════════════
# ── MAIN VIDEO RENDERING ENGINE ──────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def create_video(audio_path, script_json, chunks, output_path=None):
    """Main rendering execution entry point."""
    slot_str = script_json.get("slot", "")
    is_longform = ENABLE_LONGFORM and ("Slot C" in slot_str or "Slot L" in slot_str or script_json.get("is_longform", False))
    set_resolutions(is_longform)
    
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, f"video_{today}.mp4")
        
    print(f"🎬 [video_gen] Initiating video compilation to: {output_path}")
    
    # ── RANDOMIZED TYPOGRAPHY THEME (typography diversity) ──
    title_text = script_json.get("title") or script_json.get("original_news_headline") or "Amazing Fact!"
    import hashlib
    import infographic_gen
    
    font_options = [
        ("Montserrat-ExtraBold.ttf", "Montserrat-Bold.ttf", "Roboto-Regular.ttf"),
        ("Roboto-Bold.ttf", "Roboto-Bold.ttf", "Roboto-Regular.ttf"),
        ("Montserrat-Black.ttf", "Montserrat-Bold.ttf", "Montserrat-Italic.ttf")
    ]
    font_seed = int(hashlib.md5(title_text.encode()).hexdigest(), 16)
    selected_fonts = font_options[font_seed % len(font_options)]
    
    infographic_gen._FONT_EXTRA_BOLD = os.path.join(ASSETS_DIR, "fonts", selected_fonts[0])
    infographic_gen._FONT_BOLD = os.path.join(ASSETS_DIR, "fonts", selected_fonts[1])
    infographic_gen._FONT_REGULAR = os.path.join(ASSETS_DIR, "fonts", selected_fonts[2])
    print(f"🔤 [video_gen] Dynamically selected font theme: {selected_fonts[0]} for typography diversity.")
    
    banner_style_mode = font_seed % 3  # Support Style 0, 1, 2
    
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print(f"🚨 Audio file empty: {audio_path}")
        return None
        
    audio = AudioFileClip(audio_path)
    audio_duration = audio.duration
    
    # ── RESOLVE CATEGORY COLOR PALETTE ──
    palette = dict(_DEFAULT_PALETTE)
    if ENABLE_CATEGORY_COLORS:
        try:
            from ecosystem_logic import get_category_color_palette
            category = script_json.get("sub_category", "")
            if category:
                palette = get_category_color_palette(category)
                print(f"🎨 [video_gen] Using color palette: {palette.get('name', 'default')} for '{category}'")
        except Exception as e:
            print(f"⚠️ [video_gen] Could not load category palette: {e}. Using default.")

    accent_color = palette.get("primary", (204, 255, 0))
    progress_bar_color = palette.get("progress_bar", accent_color)
    caption_highlight = palette.get("caption_highlight", accent_color)

    # ── APPLY LAYOUT PROFILE ──
    TITLE_BOTTOM_GAP = layout_profile.get("title_bottom_gap", 192)
    progress_bar_height = layout_profile.get("progress_bar_height", 6)
    progress_bar_position = layout_profile.get("progress_bar_position", "bottom")
    avatar_x_offset = layout_profile.get("avatar_x_offset", 0)
    subtitle_y_jitter = layout_profile.get("subtitle_y_jitter", 0)
    
    # ── RESOLVE FACT COUNTER ──
    fact_number = 0
    if ENABLE_FACT_COUNTER:
        try:
            from topic_tracker import get_fact_count
            fact_number = get_fact_count() + 1  # +1 because this video hasn't been tracked yet
        except Exception:
            fact_number = 0
    
    # ── SOUNDTRACK MIXING ──
    # YPP COMPLIANCE: BGM must be from YouTube Audio Library or equivalent royalty-free source.
    # Using copyrighted music will trigger Content ID claims and reduce Shorts ad revenue.
    # Current file: assets/music/modern_tech.mp3
    bgm_path = os.path.join(ASSETS_DIR, "music", "modern_tech.mp3")
    if not os.path.exists(bgm_path):
        os.makedirs(os.path.join(ASSETS_DIR, "music"), exist_ok=True)
        # Search for any sound file in reference assets directory
        ref_music_dir = "/Users/vijayakumarjermansraj/Desktop/google_antigravity/yt_did_you_know_by_vj/assets/music"
        if os.path.exists(ref_music_dir):
            files = [f for f in os.listdir(ref_music_dir) if f.endswith((".mp3", ".wav"))]
            if files:
                bgm_path = os.path.join(ref_music_dir, files[0])
                print(f"🎵 Reusing reference BGM: {files[0]}")
    
    if os.path.exists(bgm_path):
        # Check for accompanying license file
        license_file = bgm_path.replace(".mp3", "_license.txt").replace(".wav", "_license.txt")
        if not os.path.exists(license_file):
            print("⚠️ [YPP WARNING] BGM file has no accompanying license file.")
            print("   Ensure this track is from YouTube Audio Library or royalty-free source.")
            print(f"   BGM path: {bgm_path}")
                
    mastered_wav = os.path.join(OUTPUT_DIR, f"master_soundtrack_{today}.wav")
    _mix_and_master_audio(audio_path, bgm_path, audio_duration, mastered_wav)
    final_audio = AudioFileClip(mastered_wav)
    
    # ── VISUAL BACKGROUND LAYER ASSEMBLE ──
    print("🎬 Assembling fullscreen background clips...")

    # ── GENERATE LAYOUT PROFILE (YPP Compliance) ──
    layout_profile = _generate_layout_profile(title_text)

    # ── FETCH ENTITIES FOR OVERLAYS ──
    script_json = fetch_all_entities(script_json)

    background_clips = []
    
    # Track chunk boundaries for transitions
    chunk_boundaries = []
    # Map each boundary to a transition type
    boundary_transitions = {}
    
    # Build retention cue map for transitions
    retention_cues = script_json.get("retention_cues", [])
    cue_effects = {}
    for cue in retention_cues:
        if isinstance(cue, dict):
            cue_effects[round(cue.get("timestamp", -1), 1)] = cue.get("effect", "default")
    
    # Store first chunk visual path for seamless loop
    first_chunk_visual_path = None
    first_chunk_visual_type = None
    
    for i, chunk in enumerate(chunks):
        c_start = chunk["start"]
        c_dur = chunk["duration"]
        vpath = chunk.get("visual_path")
        has_info = chunk.get("has_infographic", False)
        
        # Ensure a small overlap to prevent one-frame rendering gaps between consecutive visual clips
        overlap = 0.1
        safe_dur = c_dur + overlap if (i < len(chunks) - 1) else c_dur
        
        # Store first chunk visual for loop engineering
        if i == 0 and vpath:
            first_chunk_visual_path = vpath
            first_chunk_visual_type = chunk.get("visual_type", "photo")
        
        # Track boundary for transition (skip first chunk)
        if i > 0 and vpath:
            prev_vpath = chunks[i-1].get("visual_path")
            if vpath != prev_vpath or has_info != chunks[i-1].get("has_infographic", False):
                chunk_boundaries.append(c_start)
                # Find matching retention cue or pick random transition
                matched_effect = None
                for cue_t, effect in cue_effects.items():
                    if abs(cue_t - c_start) < 2.0:
                        matched_effect = effect
                        break
                if matched_effect and matched_effect in TRANSITION_MAP:
                    boundary_transitions[c_start] = TRANSITION_MAP[matched_effect]
                else:
                    boundary_transitions[c_start] = random.choice(_TRANSITION_POOL)
        
        # 1. Overlay infographic card if flagged
        if has_info:
            chunk_copy = dict(chunk)
            chunk_copy["duration"] = safe_dur
            card_clip, overlay_clip = build_infographic_clip(chunk_copy, accent_color, is_longform=is_longform)
            if card_clip:
                # Add bottom whiteboard backing clip for the card (cropped to bottom panel)
                bottom_bg = ColorClip(size=(FRAME_W, 864), color=(248, 246, 240), duration=safe_dur).with_start(c_start).with_position((0, 1056))
                background_clips.append(bottom_bg)
                # Crop the centered card clip to fit the bottom panel and position it
                card_clip_cropped = card_clip.cropped(x1=0, y1=528, x2=FRAME_W, y2=1392).with_position((0, 1056))
                background_clips.append(card_clip_cropped)
                
        # 2. Add normal background images / video b-roll
        if vpath and os.path.exists(vpath):
            if vpath.endswith(".png") and "screenshot" in vpath.lower():
                # Full-screen fallback whiteboard bg
                top_bg = ColorClip(size=(FRAME_W, FRAME_H), color=(248, 246, 240), duration=safe_dur).with_start(c_start).with_position((0, 0))
                background_clips.append(top_bg)
                # Render screenshot on the top panel (y=192 to 1056)
                ss_clip = prepare_top_panel_screenshot_clip(vpath, safe_dur).with_start(c_start).with_position((0, 192))
                background_clips.append(ss_clip)
            elif vpath.endswith((".jpg", ".jpeg", ".png")):
                # Ken burns zoom with randomized direction for visual variety (sized to full screen)
                zoom_dir = "in" if i % 2 == 0 else "out"
                c_clip = build_ken_burns(vpath, safe_dur, zoom_direction=zoom_dir, target_size=(FRAME_W, FRAME_H)).with_start(c_start).with_position((0, 0))
                background_clips.append(c_clip)
            elif vpath.endswith(".mp4"):
                # Video clip (Pexels or Veo 3.1)
                c_clip = VideoFileClip(vpath).without_audio().with_start(c_start)
                if c_clip.duration < safe_dur:
                    # Loop video if too short
                    c_clip = c_clip.with_effects([vfx.Loop(duration=safe_dur)])
                else:
                    c_clip = c_clip.subclipped(0, safe_dur)
                    
                # Resize and crop to crop-fill full screen
                w, h = c_clip.size
                panel_h = FRAME_H
                target_h_crop = int(w * panel_h / FRAME_W)
                if target_h_crop <= h:
                    y1 = (h - target_h_crop) // 2
                    c_clip = c_clip.cropped(x1=0, y1=y1, x2=w, y2=y1 + target_h_crop)
                else:
                    target_w_crop = int(h * FRAME_W / panel_h)
                    x1 = (w - target_w_crop) // 2
                    c_clip = c_clip.cropped(x1=x1, y1=0, x2=x1 + target_w_crop, y2=h)
                    
                c_clip = c_clip.resized((FRAME_W, panel_h)).with_position((0, 0))
                background_clips.append(c_clip)
        else:
            # Fallback full screen whiteboard color clip
            c_clip = ColorClip(size=(FRAME_W, FRAME_H), color=(248, 246, 240), duration=safe_dur).with_start(c_start).with_position((0, 0))
            background_clips.append(c_clip)

    # ── BOTTOM PANEL & TITLE BANNER ──
    # Top Banner: Title Hook (at top of shorts, y=0)
    title_text = script_json.get("title") or script_json.get("original_news_headline") or "Amazing Fact!"
    middle_clip = create_middle_title_banner_clip(title_text, audio_duration, accent_color=accent_color, style_mode=banner_style_mode).with_start(0).with_position((0, 0))
    background_clips.append(middle_clip)

    # ── AVATAR VIDEO PIP OVERLAY ──
    skip_avatar = script_json.get("skip_avatar", False)
    if not skip_avatar:
        lipsync_path = script_json.get("kaggle_lipsync_path")
        face_template = script_json.get("lipsync_face_path") or os.path.join(ASSETS_DIR, "video", "Firefly_video_final.mp4")
        if not lipsync_path or not os.path.exists(lipsync_path):
            lipsync_path = _generate_lipsync_video(audio_path, face_template)
            
        avatar_video_path = lipsync_path if lipsync_path else face_template
        if avatar_video_path and os.path.exists(avatar_video_path):
            print(f"Preparing Talking Head Avatar PiP from: {avatar_video_path}")
            try:
                vid_clip = VideoFileClip(avatar_video_path).without_audio()
                if vid_clip.duration < audio_duration:
                    vid_clip = vid_clip.with_effects([vfx.Loop(duration=audio_duration)])
                else:
                    vid_clip = vid_clip.subclipped(0, audio_duration)
                
                w_a, h_a = vid_clip.size
                target_aspect = 9 / 16
                if w_a / h_a > target_aspect:
                    new_w = int(h_a * target_aspect)
                    x1 = (w_a - new_w) // 2
                    vid_clip = vid_clip.cropped(x1=x1, y1=0, x2=x1+new_w, y2=h_a)
                else:
                    new_h = int(w_a / target_aspect)
                    y1 = int((h_a - new_h) * 0.12) if h_a > new_h else 0
                    vid_clip = vid_clip.cropped(x1=0, y1=y1, x2=w_a, y2=y1+new_h)
                w_a, h_a = vid_clip.size
                
                height_pip = int(FRAME_H * 0.40)
                width_pip = int(height_pip * (w_a / h_a))
                avatar_clip = vid_clip.resized((width_pip, height_pip))
                
                # AI Background Removal with rembg
                try:
                    # Default to False to ensure clean deep-learning human segmentation (rembg)
                    # even during local dry-run, unless fast chromakey is explicitly requested.
                    use_fast_chromakey = os.getenv("USE_FAST_CHROMAKEY", "false") == "true"
                    
                    if use_fast_chromakey:
                        print("👤 [video_gen] Fast Chromakey Background Removal enabled for local dry-run...")
                        unmasked_avatar = avatar_clip
                        mask_cache = {}
                        fps = getattr(vid_clip, "fps", 30.0) or 30.0
                        
                        def make_mask_frame(t):
                            frame_idx = int(round(t * fps))
                            if frame_idx in mask_cache:
                                return mask_cache[frame_idx]
                            frame = unmasked_avatar.get_frame(t)
                            
                            # Sample background color from top corners (average of 15x15 regions)
                            bg_color = (frame[0:15, 0:15].mean(axis=(0, 1)) + frame[0:15, -15:].mean(axis=(0, 1))) / 2.0
                            # Calculate distance from background color
                            diff = np.abs(frame.astype(np.float32) - bg_color)
                            # Create binary mask where diff > 30 (tolerance) in any channel
                            mask = np.any(diff > 30, axis=2).astype(np.uint8) * 255
                            
                            # Smooth with morphology
                            kernel = np.ones((5, 5), np.uint8)
                            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                            mask = (mask / 255.0).astype(np.float32)
                            
                            # Watermark erasure: zero out bottom 12%
                            h_mask, w_mask = mask.shape
                            watermark_height = int(h_mask * 0.12)
                            mask[-watermark_height:, :] = 0.0
                            mask_cache[frame_idx] = mask
                            return mask
                            
                    else:
                        from rembg import remove, new_session
                        print("👤 [video_gen] Initializing AI Background Removal (Dynamic u2net_human_seg)...")
                        rembg_session = new_session(model_name="u2net_human_seg")
                        unmasked_avatar = avatar_clip
                        mask_cache = {}
                        fps = getattr(vid_clip, "fps", 30.0) or 30.0
                        
                        def make_mask_frame(t):
                            frame_idx = int(round(t * fps))
                            if frame_idx in mask_cache:
                                return mask_cache[frame_idx]
                            frame = unmasked_avatar.get_frame(t)
                            rgba = remove(
                                frame,
                                session=rembg_session,
                                alpha_matting=False,
                                post_process_mask=True
                            )
                            mask = (rgba[:, :, 3] / 255.0).astype(np.float32)
                            # Watermark erasure: zero out bottom 12%
                            h_mask, w_mask = mask.shape
                            watermark_height = int(h_mask * 0.12)
                            mask[-watermark_height:, :] = 0.0
                            mask_cache[frame_idx] = mask
                            return mask
                        
                    mclip = VideoClip(make_mask_frame, is_mask=True, duration=audio_duration)
                    avatar_clip = avatar_clip.with_mask(mclip)
                    print("   ✅ Background removal applied frame-by-frame.")
                except Exception as re_err:
                    print(f"⚠️ rembg failed: {re_err}. Falling back to Rounded Authority Card.")
                    rad = int(min(width_pip, height_pip) * 0.15)
                    mask = np.ones((height_pip, width_pip), dtype=np.float32)
                    Y, X = np.ogrid[:height_pip, :width_pip]
                    for y, x in [(rad, rad), (rad, width_pip-rad), (height_pip-rad, rad), (height_pip-rad, width_pip-rad)]:
                        dist = np.sqrt((Y-y)**2 + (X-x)**2)
                        corner_mask = (dist > rad) & ( ( (Y<rad) if y==rad else (Y>height_pip-rad) ) & ( (X<rad) if x==rad else (X>width_pip-rad) ) )
                        mask[corner_mask] = 0.0
                    mclip = VideoClip(lambda t: mask, is_mask=True, duration=audio_duration)
                    avatar_clip = avatar_clip.with_mask(mclip)
                
                # "Alive" motion (head-bob and breathing)
                zoom_speed = 0.10 / max(audio_duration, 1.0)
                avatar_clip = avatar_clip.with_effects([
                    vfx.Resize(lambda t: 1.0 + zoom_speed * t + 0.006 * math.sin(t * 1.8)),
                    vfx.Rotate(lambda t: 0.6 * math.sin(t * 1.4 + 0.5))
                ])

                # Position avatar at bottom-center with layout profile offset
                avatar_x_offset = layout_profile.get("avatar_x_offset", 0)

                def pip_position(t):
                    current_scale = 1.0 + zoom_speed * t + 0.006 * math.sin(t * 1.8)
                    scaled_w = int(width_pip * current_scale)
                    scaled_h = int(height_pip * current_scale)
                    base_x = (FRAME_W - scaled_w) // 2 + avatar_x_offset
                    base_y = FRAME_H - scaled_h - 30
                    return (base_x, base_y)

                avatar_pip = avatar_clip.with_position(pip_position).with_start(0)
                background_clips.append(avatar_pip)
                print("✅ [video_gen] Avatar PiP added successfully to composite background layers!")
            except Exception as av_err:
                print(f"❌ [video_gen] Failed to process avatar video clip: {av_err}")

    # ════════════════════════════════════════════════════════════════════════════════════
    # ── ENTITY OVERLAY RENDERERS ─────────────────────────────────────────────────
    # ══════════════════════════════════════════════════════════════════════════════════

    def _render_entity_overlays(draw: ImageDraw.Draw, script_json: dict, t: float, accent_color: tuple):
        """
        Render company logos and person photos as overlays on the video.
        Entities are shown at specific timestamps based on script mentions.
        """
        # Check for company logos
        for company in script_json.get("companies", []):
            if isinstance(company, dict) and company.get("local_logo_path"):
                logo_path = company.get("local_logo_path")
                if os.path.exists(logo_path):
                    try:
                        logo_img = Image.open(logo_path).convert("RGBA")
                        # Resize logo to reasonable size (max 150px)
                        logo_img.thumbnail((150, 150), Image.LANCZOS)
                        # Position: top-right corner with some padding
                        x = FRAME_W - logo_img.width - 30
                        y = 30
                        # Fade in/out animation
                        fade_duration = 1.0
                        alpha = 255
                        # Add subtle pulse
                        pulse = 1.0 + 0.05 * math.sin(t * 2)
                        new_w = int(logo_img.width * pulse)
                        new_h = int(logo_img.height * pulse)
                        logo_img = logo_img.resize((new_w, new_h), Image.LANCZOS)
                        draw.bitmap((x, y), logo_img, fill=(255, 255, 255, alpha))
                    except Exception as e:
                        print(f"⚠️ Failed to render company logo: {e}")

        # Check for person photos
        for person in script_json.get("people", []):
            if isinstance(person, dict) and person.get("local_image_path"):
                photo_path = person.get("local_image_path")
                if os.path.exists(photo_path):
                    try:
                        photo_img = Image.open(photo_path).convert("RGBA")
                        # Resize photo to reasonable size (max 200px)
                        photo_img.thumbnail((200, 200), Image.LANCZOS)
                        # Position: top-left corner
                        x = 30
                        y = 30
                        fade_duration = 1.0
                        alpha = 255
                        pulse = 1.0 + 0.05 * math.sin(t * 2)
                        new_w = int(photo_img.width * pulse)
                        new_h = int(photo_img.height * pulse)
                        photo_img = photo_img.resize((new_w, new_h), Image.LANCZOS)
                        draw.bitmap((x, y), photo_img, fill=(255, 255, 255, alpha))
                    except Exception as e:
                        print(f"⚠️ Failed to render person photo: {e}")

        # Check for key entities
        for entity in script_json.get("key_entities", []):
            if isinstance(entity, dict) and entity.get("local_logo_path"):
                logo_path = entity.get("local_logo_path")
                if os.path.exists(logo_path):
                    try:
                        logo_img = Image.open(logo_path).convert("RGBA")
                        logo_img.thumbnail((150, 150), Image.LANCZOS)
                        # Position: center-top
                        x = (FRAME_W - logo_img.width) // 2
                        y = 30
                        alpha = 255
                        draw.bitmap((x, y), logo_img, fill=(255, 255, 255, alpha))
                    except Exception as e:
                        print(f"⚠️ Failed to render key entity logo: {e}")

    # Compile the base composited backgrounds
    base_comp = CompositeVideoClip(background_clips, size=(FRAME_W, FRAME_H)).with_duration(audio_duration)
    
    # ── PRE-LOAD FIRST FRAME FOR SEAMLESS LOOP ──
    first_frame_data = None
    if ENABLE_SEAMLESS_LOOP and first_chunk_visual_path and os.path.exists(first_chunk_visual_path):
        try:
            if first_chunk_visual_path.endswith((".jpg", ".jpeg", ".png")):
                loop_img = Image.open(first_chunk_visual_path).convert("RGB")
                loop_img = loop_img.resize((FRAME_W, FRAME_H), Image.LANCZOS)
                first_frame_data = np.array(loop_img)
            elif first_chunk_visual_path.endswith(".mp4"):
                loop_clip = VideoFileClip(first_chunk_visual_path)
                first_frame_data = loop_clip.get_frame(0)
                # Resize to match frame dimensions
                first_frame_data = cv2.resize(first_frame_data, (FRAME_W, FRAME_H))
                loop_clip.close()
        except Exception as e:
            print(f"⚠️ [video_gen] Could not pre-load first frame for loop: {e}")
    
    # ── RETENTION OVERLAYS & SUBTITLES ──
    vignette = _gradient_overlay(audio_duration)
    
    # Generate Header bar watermark
    header_clip = None
    if ENABLE_WATERMARK:
        header_img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        header_draw = ImageDraw.Draw(header_img)
        
        header_font = get_font_for_text("Simple Tips by VJ", 38, "bold")
        text_x = 50
        # Draw premium semi-translucent text watermark with dark drop shadow (readable on any background)
        header_draw.text((text_x + 2, 222), "Simple Tips by VJ", fill=(10, 10, 15, 180), font=header_font)
        header_draw.text((text_x, 220), "Simple Tips by VJ", fill=(255, 255, 255, 140), font=header_font)
        
        header_clip = ImageClip(np.array(header_img)).with_duration(audio_duration)
    
    # ── EMOJI OVERLAY CONFIG ──
    emoji_moments = []
    if ENABLE_EMOJI_OVERLAYS:
        emoji_pool_hook = ["🤯", "😱", "⚡"]
        emoji_pool_reveal = ["🧠", "💡", "🔥"]
        emoji_pool_cta = ["💬", "👇", "🚀"]
        emoji_moments = [
            {"start": 0.5, "end": 2.0, "emoji": random.choice(emoji_pool_hook), "x": FRAME_W - 180, "y": 1056 + 200},
            {"start": audio_duration * 0.3, "end": audio_duration * 0.3 + 1.5, "emoji": random.choice(emoji_pool_reveal), "x": 80, "y": 1056 + 250},
            {"start": audio_duration * 0.55, "end": audio_duration * 0.55 + 1.5, "emoji": random.choice(emoji_pool_reveal), "x": FRAME_W - 200, "y": 1056 + 300},
            {"start": audio_duration - 5.0, "end": audio_duration - 3.0, "emoji": random.choice(emoji_pool_cta), "x": FRAME_W - 180, "y": 1056 + 220},
        ]

    # ── TRANSITION DURATION CONFIG ──
    transition_duration = 0.2  # seconds per transition
    
    # Frame Assembly Loop
    def make_final_frame(t):
        frame = base_comp.get_frame(t)
        # ── CARTOON COLOR GRADE & DESATURATION ──
        frame = desaturate_frame(frame, 0.85)
        frame = apply_cartoon_color_grade(frame)
        
        # ── ATTENTION-GRAB SCREEN FLICKER (0:00 - 0:02) — reduced intensity ──
        if t <= 2.0:
            # Fade-out curve so flicker diminishes naturally
            flicker_fade = max(0.0, 1.0 - (t / 2.0))
            flicker_factor = 1.0 + 0.04 * math.sin(t * 50.0) * random.uniform(0.5, 1.0) * flicker_fade
            frame = np.clip(frame.astype(np.float32) * flicker_factor, 0, 255).astype(np.uint8)
        
        # ── HOOK FLASH: Rapid zoom-in + shake in first 0.5s to stop scrolling ──
        if t < 0.5:
            hook_progress = t / 0.5
            # Zoom from 1.2x down to 1.0x
            hook_scale = 1.2 - 0.2 * hook_progress
            h_f, w_f = frame.shape[:2]
            new_w_f, new_h_f = int(w_f * hook_scale), int(h_f * hook_scale)
            if new_w_f > 0 and new_h_f > 0:
                resized_f = cv2.resize(frame, (new_w_f, new_h_f), interpolation=cv2.INTER_LINEAR)
                x1_f = (new_w_f - w_f) // 2
                y1_f = (new_h_f - h_f) // 2
                frame = resized_f[y1_f:y1_f+h_f, x1_f:x1_f+w_f]
            # Subtle camera shake
            if t < 0.3:
                shake_intensity = int(4 * (1.0 - hook_progress))
                if shake_intensity > 0:
                    ox_h = random.randint(-shake_intensity, shake_intensity)
                    oy_h = random.randint(-shake_intensity, shake_intensity)
                    M_h = np.float32([[1, 0, ox_h], [0, 1, oy_h]])
                    frame = cv2.warpAffine(frame, M_h, (frame.shape[1], frame.shape[0]), borderMode=cv2.BORDER_REFLECT)
        
        # ── SEAMLESS LOOP: Cross-dissolve last 2.5s with first frame ──
        if ENABLE_SEAMLESS_LOOP and first_frame_data is not None:
            loop_blend_start = audio_duration - 2.5
            if t > loop_blend_start:
                loop_progress = (t - loop_blend_start) / 2.5
                blend_alpha = loop_progress * 0.50  # Max 50% blend for strong loop signal
                try:
                    first_resized = first_frame_data
                    if first_resized.shape[:2] != frame.shape[:2]:
                        first_resized = cv2.resize(first_frame_data, (frame.shape[1], frame.shape[0]))
                    frame = cv2.addWeighted(frame, 1.0 - blend_alpha, first_resized, blend_alpha, 0)
                except Exception:
                    pass
        
        # ── ADVANCED TRANSITION EFFECTS ──
        if ENABLE_ADVANCED_TRANSITIONS:
            for boundary_t in chunk_boundaries:
                if boundary_t <= t < boundary_t + transition_duration:
                    progress = (t - boundary_t) / transition_duration
                    transition_fn = boundary_transitions.get(boundary_t, _apply_flash_fade)
                    try:
                        outgoing_t = max(0.0, boundary_t - 0.01)
                        outgoing_frame = base_comp.get_frame(outgoing_t)
                        frame = transition_fn(outgoing_frame, frame, progress)
                    except Exception:
                        pass
                    break
        elif ENABLE_FLASH_TRANSITIONS:
            # Legacy flash-only transitions
            flash_duration = 0.066
            for boundary_t in chunk_boundaries:
                if boundary_t <= t < boundary_t + flash_duration:
                    flash_progress = (t - boundary_t) / flash_duration
                    flash_alpha = 1.0 - flash_progress
                    white = np.full_like(frame, 255)
                    frame = np.clip(frame * (1 - flash_alpha) + white * flash_alpha, 0, 255).astype(np.uint8)
                    break
        
        # ── BEAT CUT: Mid-chunk zoom shifts every 3.5s for subtler visual motion ──
        beat_interval = 3.5
        beat_duration = 0.15
        time_in_beat = t % beat_interval
        if time_in_beat < beat_duration and t > 0.5:  # Skip during hook flash
            beat_progress = time_in_beat / beat_duration
            # Subtle zoom pulse: 1.0 → 1.03 → 1.0 (reduced from 1.05)
            beat_scale = 1.0 + 0.03 * math.sin(beat_progress * math.pi)
            h_b, w_b = frame.shape[:2]
            new_w_b, new_h_b = int(w_b * beat_scale), int(h_b * beat_scale)
            if new_w_b > w_b and new_h_b > h_b:
                resized_b = cv2.resize(frame, (new_w_b, new_h_b), interpolation=cv2.INTER_LINEAR)
                x1_b = (new_w_b - w_b) // 2
                y1_b = (new_h_b - h_b) // 2
                frame = resized_b[y1_b:y1_b+h_b, x1_b:x1_b+w_b]
        
        pil_frame = Image.fromarray(frame).convert("RGBA")
        p_draw = ImageDraw.Draw(pil_frame)
        
        # ── RETENTION OVERLAYS ──

        # Fact Counter Badge (top-left)
        if ENABLE_FACT_COUNTER and fact_number > 0:
            _render_fact_counter_badge(p_draw, fact_number, accent_color)

        # Countdown Timer (top-right)
        if ENABLE_COUNTDOWN_TIMER:
            _render_countdown_timer(p_draw, t, audio_duration, accent_color)

        # Sound-On Indicator (first 2.5s)
        if ENABLE_SOUND_ON_INDICATOR:
            _render_sound_on_indicator(p_draw, t, accent_color)

        # Voice Fallback warning removed — only reported via Telegram notification
        # (Previously rendered an orange badge on the video visible to viewers)

        # ── ENTITY OVERLAYS ──
        _render_entity_overlays(p_draw, script_json, t, accent_color)

        # ── DUAL-LAYER CAPTIONS ──
        active_chunk = None
        for chunk in chunks:
            if chunk["start"] <= t <= chunk["end"]:
                active_chunk = chunk
                break
                
        if not active_chunk and chunks and t > chunks[-1]["end"]:
            active_chunk = chunks[-1]
            
        if active_chunk:
            chunk_dur = max(0.1, active_chunk["end"] - active_chunk["start"])
            progress = (t - active_chunk["start"]) / chunk_dur
            
            if ENABLE_DUAL_CAPTIONS:
                # ── LAYER 1: Tanglish word-by-word karaoke subtitles (at ~58% Y) ──
                chunk_words = active_chunk.get("words", [])
                if chunk_words:
                    word_status_list = []
                    for wd in chunk_words:
                        is_active = wd["start"] <= t <= wd["end"]
                        word_status_list.append({"word": wd["word"], "is_active": is_active})
                    
                    sub_arr = render_subtitle_frame(word_status_list, accent_color=caption_highlight)
                    pil_sub = Image.fromarray(sub_arr).convert("RGBA")
                    pil_frame.alpha_composite(pil_sub)
                
                # ── LAYER 2: English keyword pill (at ~76% Y) ──
                eng_caption = active_chunk.get("english_caption", "")
                if eng_caption and eng_caption.strip():
                    cap_arr = render_whiteboard_caption(eng_caption, progress, accent_color=accent_color)
                    pil_cap = Image.fromarray(cap_arr).convert("RGBA")
                    pil_frame.alpha_composite(pil_cap)
            
            elif ENABLE_KINETIC_CAPTIONS:
                # Legacy single-layer caption mode
                chunk_text = active_chunk.get("english_caption", active_chunk.get("text", ""))
                if chunk_text:
                    sub_arr = render_whiteboard_caption(chunk_text, progress, accent_color=accent_color)
                    pil_sub = Image.fromarray(sub_arr).convert("RGBA")
                    pil_frame.alpha_composite(pil_sub)
        
        # ── Emoji reaction overlays ──
        if ENABLE_EMOJI_OVERLAYS:
            for em in emoji_moments:
                if em["start"] <= t <= em["end"]:
                    try:
                        em_progress = (t - em["start"]) / (em["end"] - em["start"])
                        # Pop-in scale: fast grow then settle
                        scale = min(1.0, em_progress * 3.0) if em_progress < 0.33 else 1.0
                        # Fade out in last 30%
                        alpha = 1.0 if em_progress < 0.7 else (1.0 - em_progress) / 0.3
                        
                        emoji_size = int(90 * scale)
                        if emoji_size > 10:
                            em_font = get_font_for_text(em["emoji"], emoji_size, "bold")
                            if is_char_supported(em_font, em["emoji"]):
                                em_draw = ImageDraw.Draw(pil_frame)
                                # Drop shadow
                                em_draw.text((em["x"]+3, em["y"]+3), em["emoji"], fill=(0,0,0,int(180*alpha)), font=em_font)
                                em_draw.text((em["x"], em["y"]), em["emoji"], fill=(255,255,255,int(255*alpha)), font=em_font)
                    except Exception:
                        pass
                
        # ── Premium thin progress bar with rounded leading dot (Layout Profile aware) ──
        progress_ratio = t / audio_duration
        progress_w = int(FRAME_W * progress_ratio)
        if progress_w > 0:
            bar_draw = ImageDraw.Draw(pil_frame)
            pr, pg, pb = progress_bar_color
            # Pulse glow at 40-60% mark (midpoint engagement boost)
            glow_intensity = 0
            if 0.35 < progress_ratio < 0.65:
                glow_phase = (progress_ratio - 0.35) / 0.30
                glow_intensity = int(30 * math.sin(glow_phase * math.pi))
            # Use layout profile for bar height
            bar_height = progress_bar_height + (glow_intensity // 15)
            # Position based on layout profile
            if progress_bar_position == "top":
                bar_y_start = 0
                bar_y_end = bar_height
                dot_y = bar_height // 2
                # Glow layer at top
                if glow_intensity > 0:
                    bar_draw.rectangle([0, 0, progress_w + 2, bar_height + 3], fill=(pr, pg, pb, glow_intensity))
            else:
                bar_y_start = FRAME_H - bar_height
                bar_y_end = FRAME_H
                dot_y = FRAME_H - bar_height // 2
                # Glow layer at bottom
                if glow_intensity > 0:
                    bar_draw.rectangle([0, FRAME_H - bar_height - 3, progress_w + 2, FRAME_H], fill=(pr, pg, pb, glow_intensity))
            # Main bar
            bar_draw.rectangle([0, bar_y_start, progress_w, bar_y_end], fill=(pr, pg, pb, 255))
            # Leading dot (rounded indicator) for premium feel
            dot_radius = bar_height + 2
            dot_x = min(progress_w, FRAME_W - dot_radius)
            bar_draw.ellipse(
                [dot_x - dot_radius, dot_y - dot_radius, dot_x + dot_radius, dot_y + dot_radius],
                fill=(pr, pg, pb, 255)
            )
            
        frame = np.array(pil_frame.convert("RGB"))
        return frame

    final_video = VideoClip(make_final_frame, duration=audio_duration)
    
    # Compose everything
    comp_clips = [final_video, vignette]
    if header_clip:
        comp_clips.append(header_clip)
        
    main_composition = CompositeVideoClip(comp_clips, size=(FRAME_W, FRAME_H)).with_duration(audio_duration)
    final_render = main_composition
        
    final_render = final_render.with_audio(final_audio)
    
    # ── EXPORT ──
    print(f"🎬 [video_gen] Exporting final video: {output_path}...")
    final_render.write_videofile(
        output_path, fps=30, codec="libx264", audio_codec="aac",
        threads=4, preset="medium", ffmpeg_params=["-pix_fmt", "yuv420p", "-b:v", "8M"]
    )
    
    try:
        final_render.close()
        final_audio.close()
    except:
        pass
        
    print("✅ [video_gen] Rendering complete!")
    return output_path

# Helper moviepy ColorClip class fallback
class ColorClip(VideoClip):
    def __init__(self, size, color, duration):
        w, h = size
        r, g, b = color
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :] = [r, g, b]
        super().__init__(lambda t: frame, duration=duration)
