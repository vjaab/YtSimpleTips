"""
video_gen.py — 15-Layer Faceless Video Rendering Engine with Bilingual Tamil Captions.
V2: Dual-layer captions, advanced transitions, retention overlays, seamless loop, category colors.
Compiles Ken Burns images, Pexels video clips, Veo AI clips, and infographic cards
with mixed Tamil+English kinetic captions.
"""

import os
import shutil
import cv2
import numpy as np
import random
import math
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

FRAME_W, FRAME_H = 1080, 1920  # Default 9:16

# ── DEFAULT COLOR PALETTE (Anime theme - Neon Orange & Electric Blue) ──
_DEFAULT_PALETTE = {
    "primary": (255, 107, 53),           # Neon Orange
    "secondary": (15, 15, 10),
    "caption_highlight": (0, 212, 255),  # Electric Blue
    "progress_bar": (0, 212, 255),
}

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

def apply_anime_color_grade(frame):
    """
    Simulates anime LUT color grading with per-video randomized variation:
    - High contrast (slightly varied per video)
    - Crushed blacks (low pixels pushed down)
    - Slightly boosted saturation/vibrancy for neon midtones
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

def _apply_anime_flash_cut(outgoing, incoming, progress):
    """
    Fast anime-style flash cut:
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

def build_ken_burns(img_path, duration, zoom_direction=None):
    """Builds a smooth Ken Burns effect clip with randomized zoom direction."""
    clip = ImageClip(img_path).with_duration(duration)
    w, h = clip.size
    
    # Crop to aspect ratio first
    target_h = int(w * FRAME_H / FRAME_W)
    if target_h <= h:
        y1 = (h - target_h) // 2
        clip = clip.cropped(x1=0, y1=y1, x2=w, y2=y1 + target_h)
    else:
        target_w = int(h * FRAME_W / FRAME_H)
        x1 = (w - target_w) // 2
        clip = clip.cropped(x1=x1, y1=0, x2=x1 + target_w, y2=h)
        
    # Resize to match target frame dimensions
    clip = clip.resized(new_size=(FRAME_W, FRAME_H))
    
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
    "zoom_burst": _apply_anime_flash_cut,
    "hook_impact": _apply_rgb_glitch,
    "glitch": _apply_rgb_glitch,
    "emphasis": _apply_shake,
    "shake": _apply_shake,
    "flash": _apply_anime_flash_cut,
    "dissolve": _apply_cross_dissolve,
}

# Pool of transitions for random selection when no specific cue is given
_TRANSITION_POOL = [
    _apply_anime_flash_cut,
    _apply_rgb_glitch,
    _apply_cross_dissolve,
    _apply_shake,
]


# ══════════════════════════════════════════════════════════════════════════════
# ── DUAL-LAYER CAPTION SYSTEM ───────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

def render_subtitle_frame(word_status_list, accent_color=(204, 255, 0), y_shift=0):
    """Renders high-impact kinetic subtitle frame with dynamic active-word popping."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    base_size = int(60 * (FRAME_W / 1080.0))
    
    # Form layout and line-wrap words
    words = [wd["word"] for wd in word_status_list]
    word_widths = []
    
    for i, wd in enumerate(word_status_list):
        font = get_font_for_text(words[i], base_size, "bold")
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
    y_pos = int(FRAME_H * 0.58) - (len(lines) * line_h // 2) + y_shift
    
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
    cy = int(FRAME_H * 0.76)  # Moved down for dual-caption layout
    
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
    
    bx, by = 40, 140  # Below the watermark area
    pw, ph = tw + 30, th + 16
    
    r, g, b = accent_color
    # Dark pill with accent border
    draw.rounded_rectangle([bx, by, bx+pw, by+ph], radius=12, fill=(10, 10, 15, 220))
    draw.rounded_rectangle([bx, by, bx+pw, by+ph], radius=12, outline=(r, g, b, 200), width=2)
    draw.text((bx + 15, by + 8), badge_text, fill=(r, g, b, 255), font=font)

def _render_countdown_timer(draw, t, total_duration, accent_color):
    """Draws a circular countdown arc in the top-right corner."""
    cx, cy = FRAME_W - 70, 160
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
    py = int(FRAME_H * 0.12)
    
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
            # During voice activity: BGM ducked by an extra 6 dB relative to base (e.g., -28 dB)
            # During silence: BGM rises to base + 2 dB (e.g., -20 dB) to fill the gaps
            ducked_db = bgm_base_db - 6
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
            card_clip, overlay_clip = build_infographic_clip(chunk, accent_color, is_longform=is_longform)
            if card_clip:
                # Add whiteboard backing clip for the card
                dark_bg = ColorClip(size=(FRAME_W, FRAME_H), color=(248, 246, 240), duration=c_dur).with_start(c_start)
                background_clips.append(dark_bg)
                background_clips.append(overlay_clip)
                background_clips.append(card_clip)
                continue
                
        # 2. Add normal background images / video b-roll
        if vpath and os.path.exists(vpath):
            if vpath.endswith(".png") and "screenshot" in vpath.lower():
                # Screenshot evidence panel canvas
                img = Image.open(vpath).convert("RGBA")
                canvas = _prepare_evidence_canvas(img, url=chunk.get("source_url"))
                c_clip = ImageClip(np.array(canvas)).with_duration(c_dur).with_start(c_start)
                
                # Gentle Ken Burns scale zoom effect on screenshots
                c_clip = c_clip.resized(lambda t: 1.0 + 0.04 * (t / max(0.1, c_dur)))
                
                # Overlay on off-white whiteboard backing clip
                whiteboard_bg = ColorClip(size=(FRAME_W, FRAME_H), color=(248, 246, 240), duration=c_dur).with_start(c_start)
                background_clips.append(whiteboard_bg)
                background_clips.append(c_clip)
            elif vpath.endswith((".jpg", ".jpeg", ".png")):
                # Ken burns zoom with randomized direction for visual variety
                zoom_dir = "in" if i % 2 == 0 else "out"
                c_clip = build_ken_burns(vpath, c_dur, zoom_direction=zoom_dir).with_start(c_start)
                background_clips.append(c_clip)
            elif vpath.endswith(".mp4"):
                # Video clip (Pexels or Veo 3.1)
                c_clip = VideoFileClip(vpath).without_audio().with_start(c_start)
                if c_clip.duration < c_dur:
                    # Loop video if too short
                    c_clip = c_clip.with_effects([vfx.Loop(duration=c_dur)])
                else:
                    c_clip = c_clip.subclipped(0, c_dur)
                    
                # Resize and crop to crop-fill vertical frame
                w, h = c_clip.size
                target_h = int(w * FRAME_H / FRAME_W)
                if target_h <= h:
                    y1 = (h - target_h) // 2
                    c_clip = c_clip.cropped(x1=0, y1=y1, x2=w, y2=y1 + target_h)
                else:
                    target_w = int(h * FRAME_W / FRAME_H)
                    x1 = (w - target_w) // 2
                    c_clip = c_clip.cropped(x1=x1, y1=0, x2=x1 + target_w, y2=h)
                    
                c_clip = c_clip.resized((FRAME_W, FRAME_H))
                background_clips.append(c_clip)
        else:
            # Fallback whiteboard color clip
            c_clip = ColorClip(size=(FRAME_W, FRAME_H), color=(248, 246, 240), duration=c_dur).with_start(c_start)
            background_clips.append(c_clip)

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
    if audio_duration > 1.5:
        vignette = _gradient_overlay(audio_duration - 1.5).with_start(1.5)
    else:
        vignette = _gradient_overlay(audio_duration)
    
    # Generate Header bar watermark
    header_clip = None
    if ENABLE_WATERMARK:
        header_img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        header_draw = ImageDraw.Draw(header_img)
        
        header_font = get_font_for_text("Simple Tips by VJ", 38, "bold")
        text_x = 50
        # Draw premium semi-translucent text watermark with dark drop shadow (readable on any background)
        header_draw.text((text_x + 2, 82), "Simple Tips by VJ", fill=(10, 10, 15, 180), font=header_font)
        header_draw.text((text_x, 80), "Simple Tips by VJ", fill=(255, 255, 255, 140), font=header_font)
        
        if audio_duration > 1.5:
            header_clip = ImageClip(np.array(header_img)).with_start(1.5).with_duration(audio_duration - 1.5)
        else:
            header_clip = ImageClip(np.array(header_img)).with_duration(audio_duration)
    
    # ── EMOJI OVERLAY CONFIG ──
    emoji_moments = []
    if ENABLE_EMOJI_OVERLAYS:
        emoji_pool_hook = ["🤯", "😱", "⚡"]
        emoji_pool_reveal = ["🧠", "💡", "🔥"]
        emoji_pool_cta = ["💬", "👇", "🚀"]
        emoji_moments = [
            {"start": 0.5, "end": 2.0, "emoji": random.choice(emoji_pool_hook), "x": FRAME_W - 180, "y": 200},
            {"start": audio_duration * 0.3, "end": audio_duration * 0.3 + 1.5, "emoji": random.choice(emoji_pool_reveal), "x": 80, "y": 250},
            {"start": audio_duration * 0.55, "end": audio_duration * 0.55 + 1.5, "emoji": random.choice(emoji_pool_reveal), "x": FRAME_W - 200, "y": 300},
            {"start": audio_duration - 5.0, "end": audio_duration - 3.0, "emoji": random.choice(emoji_pool_cta), "x": FRAME_W - 180, "y": 220},
        ]

    # ── TRANSITION DURATION CONFIG ──
    transition_duration = 0.2  # seconds per transition
    
    # Frame Assembly Loop
    def make_final_frame(t):
        if t < 1.5:
            # Premium gradient hook card with neon glow text
            hook_text = script_json.get("hook", "")
            img = Image.new("RGB", (FRAME_W, FRAME_H), (8, 8, 18))
            draw = ImageDraw.Draw(img)
            
            # Draw vertical gradient: deep navy (top) → dark purple (bottom)
            for y in range(FRAME_H):
                ratio = y / FRAME_H
                r = int(8 + 18 * ratio)
                g = int(8 + 5 * ratio)
                b = int(18 + 22 * ratio)
                draw.line([(0, y), (FRAME_W, y)], fill=(r, g, b))
            
            # Radial center glow (subtle)
            glow_img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_img)
            cx, cy_center = FRAME_W // 2, FRAME_H // 2
            for radius in range(400, 0, -5):
                alpha = int(15 * (1.0 - radius / 400.0))
                ar, ag, ab = accent_color
                glow_draw.ellipse(
                    [cx - radius, cy_center - radius, cx + radius, cy_center + radius],
                    fill=(ar, ag, ab, alpha)
                )
            img.paste(Image.alpha_composite(Image.new("RGBA", (FRAME_W, FRAME_H), (0,0,0,0)), glow_img).convert("RGB"), (0, 0))
            draw = ImageDraw.Draw(img)
            
            # Accent line at top (category color)
            ar, ag, ab = accent_color
            draw.rectangle([0, 0, FRAME_W, 4], fill=(ar, ag, ab))
            
            # Hook text with neon glow effect
            base_size = int(68 * (FRAME_W / 1080.0))
            words = hook_text.split()
            lines = []
            current_line = []
            for w in words:
                current_line.append(w)
                line_str = " ".join(current_line)
                font = get_font_for_text(line_str, base_size, "bold")
                bbox = font.getbbox(line_str)
                lw = bbox[2] - bbox[0]
                if lw > FRAME_W * 0.85 and len(current_line) > 1:
                    current_line.pop()
                    lines.append(" ".join(current_line))
                    current_line = [w]
            if current_line:
                lines.append(" ".join(current_line))
                
            line_h = int(110 * (FRAME_W / 1080.0))
            total_h = len(lines) * line_h
            y_pos = (FRAME_H - total_h) // 2
            
            # Fade-in animation for text (0 → 1.0 over first 0.4s)
            text_alpha = min(255, int(255 * (t / 0.4))) if t < 0.4 else 255
            
            for i, line in enumerate(lines):
                font = get_font_for_text(line, base_size, "bold")
                bbox = font.getbbox(line)
                lw = bbox[2] - bbox[0]
                lx = (FRAME_W - lw) // 2
                # Subtle glow behind text using accent color
                for dx in [-2, -1, 0, 1, 2]:
                    for dy in [-2, -1, 0, 1, 2]:
                        if abs(dx) + abs(dy) > 0:
                            draw.text((lx + dx, y_pos + i * line_h + dy), line, fill=(ar, ag, ab, int(text_alpha * 0.35)), font=font)
                draw.text((lx, y_pos + i * line_h), line, fill=(255, 255, 255, text_alpha), font=font)
            
            # Cross-dissolve into first content frame during last 0.3s of hook
            if t > 1.2:
                dissolve_progress = (t - 1.2) / 0.3
                try:
                    content_frame = base_comp.get_frame(1.5)
                    content_frame = desaturate_frame(content_frame, 0.85)
                    content_frame = apply_anime_color_grade(content_frame)
                    hook_arr = np.array(img)
                    blended = cv2.addWeighted(hook_arr, 1.0 - dissolve_progress, content_frame, dissolve_progress, 0)
                    return blended
                except Exception:
                    pass
            
            return np.array(img)

        frame = base_comp.get_frame(t)
        
        # ── ANIME COLOR GRADE & DESATURATION ──
        frame = desaturate_frame(frame, 0.85)
        frame = apply_anime_color_grade(frame)
        
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
                
        # ── Premium thin progress bar with rounded leading dot ──
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
            bar_height = 6 + (glow_intensity // 15)  # Thinner bar (6px base instead of 12px)
            # Subtle glow layer
            if glow_intensity > 0:
                bar_draw.rectangle([0, FRAME_H - bar_height - 3, progress_w + 2, FRAME_H], fill=(pr, pg, pb, glow_intensity))
            # Main bar
            bar_draw.rectangle([0, FRAME_H - bar_height, progress_w, FRAME_H], fill=(pr, pg, pb, 255))
            # Leading dot (rounded indicator) for premium feel
            dot_radius = bar_height + 2
            dot_x = min(progress_w, FRAME_W - dot_radius)
            dot_y = FRAME_H - bar_height // 2
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
