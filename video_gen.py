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
    ENABLE_SEAMLESS_LOOP
)
from infographic_gen import build_infographic_clip, get_font_for_text

FRAME_W, FRAME_H = 1080, 1920  # Default 9:16

# ── DEFAULT COLOR PALETTE (Electric Lime — original brand) ──
_DEFAULT_PALETTE = {
    "primary": (204, 255, 0),
    "secondary": (15, 15, 10),
    "caption_highlight": (204, 255, 0),
    "progress_bar": (204, 255, 0),
}

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
    clip = clip.resized(newsize=(FRAME_W, FRAME_H))
    
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

def _apply_zoom_burst(frame, progress):
    """Quick 1.3x zoom burst that settles back to 1.0x."""
    h, w = frame.shape[:2]
    # Scale: 1.0 → 1.3 → 1.0 over the transition duration
    scale = 1.0 + 0.3 * math.sin(progress * math.pi)
    new_w, new_h = int(w * scale), int(h * scale)
    if new_w <= 0 or new_h <= 0:
        return frame
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    # Crop center back to original size
    x1 = (new_w - w) // 2
    y1 = (new_h - h) // 2
    return resized[y1:y1+h, x1:x1+w]

def _apply_rgb_glitch(frame, progress):
    """Shifts R/G/B channels by random offsets for a digital glitch look."""
    h, w = frame.shape[:2]
    intensity = int(10 * math.sin(progress * math.pi))  # Peak at midpoint
    if intensity < 1:
        return frame
    result = frame.copy()
    # Shift red channel right, blue channel left
    result[:, intensity:, 0] = frame[:, :-intensity, 0]  # R shift right
    result[:, :-intensity, 2] = frame[:, intensity:, 2]   # B shift left
    # Add horizontal scan lines
    for y in range(0, h, 4):
        if random.random() < 0.3 * (1 - progress):
            shift = random.randint(-intensity, intensity)
            if shift > 0:
                result[y, shift:] = result[y, :-shift]
            elif shift < 0:
                result[y, :shift] = result[y, -shift:]
    return result

def _apply_shake(frame, progress):
    """Random X/Y jitter for emphasis."""
    h, w = frame.shape[:2]
    intensity = int(5 * math.sin(progress * math.pi))
    if intensity < 1:
        return frame
    ox = random.randint(-intensity, intensity)
    oy = random.randint(-intensity, intensity)
    M = np.float32([[1, 0, ox], [0, 1, oy]])
    return cv2.warpAffine(frame, M, (w, h), borderMode=cv2.BORDER_REFLECT)

def _apply_flash_fade(frame, progress):
    """White flash that fades from bright to normal (original transition, refined)."""
    flash_alpha = 1.0 - progress
    white = np.full_like(frame, 255)
    return np.clip(frame * (1 - flash_alpha * 0.7) + white * flash_alpha * 0.7, 0, 255).astype(np.uint8)

def _apply_cross_dissolve(frame, progress):
    """Smooth opacity reduction for cross-dissolve effect."""
    # Slight brightness boost during mid-transition
    brightness = 1.0 + 0.15 * math.sin(progress * math.pi)
    return np.clip(frame * brightness, 0, 255).astype(np.uint8)

# Transition type mapping from retention_cue effect names
TRANSITION_MAP = {
    "zoom_in": _apply_zoom_burst,
    "zoom_burst": _apply_zoom_burst,
    "hook_impact": _apply_rgb_glitch,
    "glitch": _apply_rgb_glitch,
    "emphasis": _apply_shake,
    "shake": _apply_shake,
    "flash": _apply_flash_fade,
    "dissolve": _apply_cross_dissolve,
}

# Pool of transitions for random selection when no specific cue is given
_TRANSITION_POOL = [
    _apply_zoom_burst,
    _apply_flash_fade,
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
                c_fill = (*accent_color, 255)  # Category-specific accent color
                font = get_font_for_text(word_text, int(base_size * 1.15), "extrabold")
                # Draw dynamic drop shadow for active word
                draw.text((cur_x+3, line_y-4+3), word_text, fill=(0,0,0,255), font=font)
                draw.text((cur_x, line_y-4), word_text, fill=c_fill, font=font)
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
    is_longform = "Slot C" in slot_str or "Slot L" in slot_str or script_json.get("is_longform", False)
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
        frame = base_comp.get_frame(t)
        
        # ── SEAMLESS LOOP: Cross-dissolve last 3s with first frame ──
        if ENABLE_SEAMLESS_LOOP and first_frame_data is not None:
            loop_blend_start = audio_duration - 3.0
            if t > loop_blend_start:
                loop_progress = (t - loop_blend_start) / 3.0
                blend_alpha = loop_progress * 0.35  # Max 35% blend
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
                        frame = transition_fn(frame, progress)
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
                            em_draw = ImageDraw.Draw(pil_frame)
                            # Drop shadow
                            em_draw.text((em["x"]+3, em["y"]+3), em["emoji"], fill=(0,0,0,int(180*alpha)), font=em_font)
                            em_draw.text((em["x"], em["y"]), em["emoji"], fill=(255,255,255,int(255*alpha)), font=em_font)
                    except Exception:
                        pass
                
        # ── Dynamic glowing progress bar ──
        progress_w = int(FRAME_W * (t / audio_duration))
        if progress_w > 0:
            bar_draw = ImageDraw.Draw(pil_frame)
            pr, pg, pb = progress_bar_color
            bar_draw.rectangle([0, FRAME_H - 12, progress_w, FRAME_H], fill=(pr, pg, pb, 255))
            
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
