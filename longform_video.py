# -*- coding: utf-8 -*-
"""
longform_video.py — 16:9 (1920x1080) Widescreen Video Rendering Engine for 2-3 minute Longform Videos.

Features:
- Native 1920x1080 landscape resolution
- Dynamic visual compositor:
    * Real Pexels landscape stock video b-roll (scaled & cropped to 1920x1080)
    * AI image stills with 16:9 Ken Burns camera motion (dolly in/out, pan, pedestal)
    * Animated 1920x1080 data cards (longform_cards.py) overlaid on dimmed background
    * Web screenshot evidence panels with verified source URL pill
- Chapter lower-third banner:
    * Animates in at the beginning of each chapter ("CHAPTER 2: ...") for 3.5s
- Clean 16:9 bilingual subtitles:
    * Placed in lower-third safe zone (y ≈ 880) with frosted dark pill for 100% legibility
    * On-screen English punchy keyword badge (e.g. "[1,600 YEARS]")
- Sound design & mastering:
    * EMA dynamic ducking on BGM (YouTube Audio Library royalty-free)
    * Atmospheric sound effects (woosh, pop, glitch) on major visual cuts
"""

import os
import math
import random
import re
from datetime import datetime
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, VideoClip,
    CompositeVideoClip, ColorClip, afx
)

from config import (
    OUTPUT_DIR, ASSETS_DIR, BGM_VOLUME
)
from infographic_gen import get_font_for_text
from video_gen import build_ken_burns, _mix_and_master_audio
from longform_cards import CardAnimator

FRAME_W, FRAME_H = 1920, 1080


def _ts(text, font):
    bb = font.getbbox(str(text))
    return bb[2] - bb[0], bb[3] - bb[1]


# ─────────────────────────────────────────────────────────────────────────────
# Visual background clip preparers (1920x1080)
# ─────────────────────────────────────────────────────────────────────────────

def _prepare_video_clip(video_path, target_duration):
    """Loads video b-roll, loops if too short, crops/scales to 1920x1080 center."""
    try:
        clip = VideoFileClip(video_path)
        # Strip audio track from b-roll video so it doesn't clash with voiceover
        clip = clip.without_audio()
        
        # Loop if needed
        if clip.duration < target_duration:
            loops_needed = math.ceil(target_duration / clip.duration)
            clips = [clip] * loops_needed
            from moviepy import concatenate_videoclips
            clip = concatenate_videoclips(clips)

        clip = clip.subclipped(0, target_duration)
        
        # Scale & center crop to 1920x1080
        vw, vh = clip.size
        target_aspect = FRAME_W / FRAME_H
        clip_aspect = vw / vh

        if clip_aspect > target_aspect:
            # Video is wider than 16:9 -> fit height, crop width
            new_h = FRAME_H
            new_w = int(vh * (vw / vh))
            clip = clip.resized(height=FRAME_H)
            cw, ch = clip.size
            x1 = (cw - FRAME_W) // 2
            clip = clip.cropped(x1=x1, y1=0, x2=x1 + FRAME_W, y2=FRAME_H)
        else:
            # Video is taller than 16:9 -> fit width, crop height
            clip = clip.resized(width=FRAME_W)
            cw, ch = clip.size
            y1 = (ch - FRAME_H) // 2
            clip = clip.cropped(x1=0, y1=y1, x2=FRAME_W, y2=y1 + FRAME_H)
            
        return clip
    except Exception as e:
        print(f"⚠️ [_prepare_video_clip] Error loading video {video_path}: {e}")
        return None


def _prepare_screenshot_canvas(screenshot_path, url, target_duration, accent_color):
    """Embeds screenshot inside an obsidian frame with source badge on 1920x1080."""
    try:
        bg = Image.new("RGB", (FRAME_W, FRAME_H), (10, 12, 20))
        draw = ImageDraw.Draw(bg)
        
        # Ambient subtle grid/gradient
        for y in range(0, FRAME_H, 60):
            draw.line([(0, y), (FRAME_W, y)], fill=(18, 22, 34), width=1)
        for x in range(0, FRAME_W, 60):
            draw.line([(x, 0), (x, FRAME_H)], fill=(18, 22, 34), width=1)

        ss = Image.open(screenshot_path).convert("RGB")
        sw, sh = ss.size
        
        # Fit inside 1500x820 display window
        max_w, max_h = 1480, 780
        scale = min(max_w / sw, max_h / sh)
        new_w, new_h = int(sw * scale), int(sh * scale)
        ss_resized = ss.resize((new_w, new_h), Image.LANCZOS)
        
        px = (FRAME_W - new_w) // 2
        py = (FRAME_H - new_h) // 2 - 30
        
        # Shadow & glowing border
        draw.rounded_rectangle([px + 12, py + 18, px + new_w + 12, py + new_h + 18], radius=24, fill=(0, 0, 0, 180))
        draw.rounded_rectangle([px - 4, py - 4, px + new_w + 4, py + new_h + 4], radius=26, outline=(*accent_color, 200), width=4)
        
        bg.paste(ss_resized, (px, py))
        
        # Source URL badge at the top
        domain = "Official Reference"
        if url:
            m = re.search(r'https?://([^/]+)', url)
            if m:
                domain = m.group(1).replace("www.", "")
        
        badge_text = f"📰 CITED SOURCE: {domain}"
        font_badge = get_font_for_text(badge_text, 36, "bold")
        bw, bh = _ts(badge_text, font_badge)
        bx = (FRAME_W - (bw + 60)) // 2
        by = py - 70 if py >= 90 else py + 15
        
        draw.rounded_rectangle([bx, by, bx + bw + 60, by + bh + 24], radius=16, fill=(15, 18, 30, 240), outline=(*accent_color, 255), width=2)
        draw.text((bx + 30, by + 12), badge_text, font=font_badge, fill=(*accent_color, 255))
        
        return ImageClip(np.array(bg)).with_duration(target_duration)
    except Exception as e:
        print(f"⚠️ [_prepare_screenshot_canvas] Error: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Chapter Lower-Third Banner Clip
# ─────────────────────────────────────────────────────────────────────────────

def build_chapter_banner(chapter_title, chapter_idx, duration=3.5, accent_color=(96, 165, 250)):
    """Creates a broadcast lower-third pill: e.g. 'PART 2: Ancient Architecture'."""
    banner_w, banner_h = 760, 110
    img = Image.new("RGBA", (banner_w, banner_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shadow
    draw.rounded_rectangle([6, 8, banner_w - 6, banner_h - 2], radius=24, fill=(0, 0, 0, 160))
    # Outer stroke
    draw.rounded_rectangle([2, 2, banner_w - 10, banner_h - 10], radius=24, fill=(12, 16, 32, 235), outline=(*accent_color, 220), width=3)
    # Left accent vertical marker
    draw.rounded_rectangle([18, 22, 26, banner_h - 32], radius=4, fill=(*accent_color, 255))

    font_sub = get_font_for_text("PART", 28, "bold")
    draw.text((44, 22), f"CHAPTER {chapter_idx + 1}".upper(), font=font_sub, fill=(*accent_color, 255))

    font_title = get_font_for_text(chapter_title, 38, "bold")
    disp_title = chapter_title[:32] + "..." if len(chapter_title) > 35 else chapter_title
    draw.text((44, 56), disp_title, font=font_title, fill=(255, 255, 255, 255))

    frame_arr = np.array(img)
    
    fade_dur = 0.4
    def make_frame(t):
        return frame_arr[:, :, :3]

    def make_mask(t):
        alpha = frame_arr[:, :, 3].astype(np.float32) / 255.0
        if t < fade_dur:
            alpha = alpha * (t / fade_dur)
        elif t > duration - fade_dur:
            alpha = alpha * max(0.0, (duration - t) / fade_dur)
        return alpha

    banner_clip = VideoClip(make_frame, duration=duration).with_mask(VideoClip(make_mask, is_mask=True, duration=duration))
    # Position on top-left of the 16:9 screen
    return banner_clip.with_position((80, 80))


# ─────────────────────────────────────────────────────────────────────────────
# 16:9 Lower-Third Subtitle Renderer
# ─────────────────────────────────────────────────────────────────────────────

def render_longform_subtitle(chunk, accent_color=(96, 165, 250)):
    """
    Renders 16:9 widescreen subtitles cleanly positioned at lower-third (y ≈ 870px).
    Includes high-contrast frosted pill and on-screen English keyword badge if available.
    """
    text = chunk.get("text", "").strip()
    badge_text = str(chunk.get("english_caption", "")).strip().upper()
    dur = chunk.get("duration", 3.0)
    
    if not text:
        return None

    # Measure text & build wrapping
    base_size = 54
    font_tamil = get_font_for_text(text, base_size, "bold")
    space_w = font_tamil.getbbox(" ")[2]

    words = text.split()
    word_widths = [font_tamil.getbbox(w)[2] - font_tamil.getbbox(w)[0] for w in words]

    max_w = int(FRAME_W * 0.78)  # 1500px max width for comfortable viewing
    lines, current_line, current_w = [], [], 0

    for i, w in enumerate(words):
        w_w = word_widths[i]
        sep = space_w if current_line else 0
        if current_w + sep + w_w > max_w and current_line:
            lines.append(" ".join(current_line))
            current_line = [w]
            current_w = w_w
        else:
            current_line.append(w)
            current_w += sep + w_w
    if current_line:
        lines.append(" ".join(current_line))

    # Keep at most 2 lines per subtitle chunk for fast reading
    lines = lines[:2]
    line_h = 72
    total_text_h = len(lines) * line_h

    # Overall pill dimension
    max_line_w = max(_ts(l, font_tamil)[0] for l in lines) if lines else 0
    pill_w = max(450, max_line_w + 100)
    pill_h = total_text_h + 46
    pill_x = (FRAME_W - pill_w) // 2
    pill_y = FRAME_H - 180 - pill_h // 2  # centered around y=900

    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Frosted background pill with soft shadow
    draw.rounded_rectangle([pill_x + 6, pill_y + 8, pill_x + pill_w + 6, pill_y + pill_h + 8], radius=24, fill=(0, 0, 0, 160))
    draw.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + pill_h], radius=22, fill=(10, 12, 24, 230), outline=(*accent_color, 90), width=2)

    # Draw lines
    cur_y = pill_y + 22
    for l in lines:
        tw, _ = _ts(l, font_tamil)
        tx = pill_x + (pill_w - tw) // 2
        # Drop shadow
        draw.text((tx + 2, cur_y + 2), l, font=font_tamil, fill=(0, 0, 0, 240))
        # Text
        draw.text((tx, cur_y), l, font=font_tamil, fill=(255, 255, 255, 255))
        cur_y += line_h

    # On-screen keyword badge (if present and short) floating above the pill
    if badge_text and len(badge_text) <= 24 and badge_text not in ("N/A", "NONE"):
        font_badge = get_font_for_text(badge_text, 34, "extrabold")
        bw, bh = _ts(badge_text, font_badge)
        bx = (FRAME_W - (bw + 40)) // 2
        by = pill_y - bh - 24
        if by > 80:
            draw.rounded_rectangle([bx + 4, by + 4, bx + bw + 44, by + bh + 16], radius=12, fill=(0, 0, 0, 160))
            draw.rounded_rectangle([bx, by, bx + bw + 40, by + bh + 12], radius=12, fill=(*accent_color, 240))
            draw.text((bx + 20, by + 6), badge_text, font=font_badge, fill=(10, 12, 24, 255))

    frame_arr = np.array(img)
    return ImageClip(frame_arr).with_duration(dur)


# ─────────────────────────────────────────────────────────────────────────────
# Watermark & Channel Identity
# ─────────────────────────────────────────────────────────────────────────────

def create_longform_watermark(duration, brand_name="Simple Tips by VJ"):
    """Subtle top-right channel watermark."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font = get_font_for_text(brand_name, 32, "bold")
    bw, bh = _ts(brand_name, font)
    bx = FRAME_W - bw - 70
    by = 50
    
    # Subtle pill
    draw.rounded_rectangle([bx - 18, by - 8, bx + bw + 18, by + bh + 10], radius=14, fill=(12, 16, 28, 140))
    draw.text((bx, by), brand_name, font=font, fill=(255, 255, 255, 190))
    
    return ImageClip(np.array(img)).with_duration(duration)


# ─────────────────────────────────────────────────────────────────────────────
# Master Video Rendering Function
# ─────────────────────────────────────────────────────────────────────────────

def create_longform_video(audio_path, script_data, chunks, output_path=None):
    """
    Renders the full 16:9 widescreen longform video.
    Returns the path to the rendered MP4 file or None.
    """
    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_path:
        output_path = os.path.join(OUTPUT_DIR, f"longform_{today_str}.mp4")

    print(f"\n🎬 [longform_video] Starting 16:9 widescreen compilation → {output_path}")

    # Validate audio
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print(f"🚨 [longform_video] Audio file missing or empty: {audio_path}")
        return None

    audio = AudioFileClip(audio_path)
    total_audio_duration = audio.duration
    print(f"⏱️ Total narration duration: {total_audio_duration:.2f}s ({total_audio_duration/60:.2f} mins)")

    niche_id = script_data.get("niche", "mystery")
    accent_color = tuple(script_data.get("accent_color") or (96, 165, 250))

    # ── STEP 1: Sound design & BGM mixing ──
    bgm_path = os.path.join(ASSETS_DIR, "music", "modern_tech.mp3")
    mastered_wav = os.path.join(OUTPUT_DIR, f"lf_master_audio_{today_str}.wav")
    
    # Collect cut points for SFX
    sfx_events = []
    last_sfx = -10.0
    for chunk in chunks:
        st = chunk.get("start", 0.0)
        plan = chunk.get("plan", "stock")
        if st - last_sfx >= 4.0 and (plan in ("infographic", "screenshot") or chunk.get("chapter_title")):
            sfx_type = "woosh" if plan == "infographic" else "pop"
            sfx_events.append({"time_ms": int(st * 1000), "type": sfx_type})
            last_sfx = st

    print("🎵 Mixing BGM with dynamic EMA ducking...")
    _mix_and_master_audio(audio_path, bgm_path, total_audio_duration, mastered_wav, sfx_events=sfx_events)
    final_audio = AudioFileClip(mastered_wav)

    # ── STEP 2: Assemble visual clips (Background layer) ──
    print(f"🖼️ Assembling {len(chunks)} scene visual clips...")
    background_clips = []
    card_clips = []
    chapter_banners = []
    subtitle_clips = []

    last_chapter_idx = -1

    for idx, chunk in enumerate(chunks):
        c_start = chunk.get("start", 0.0)
        c_dur = chunk.get("duration", 3.0)
        if c_dur <= 0.1:
            continue

        vpath = chunk.get("visual_path")
        vtype = chunk.get("visual_type", "photo")
        plan = chunk.get("plan", "stock")
        has_info = chunk.get("has_infographic", False)

        # 1. Base visual
        clip = None
        if vpath and os.path.exists(vpath):
            if vtype == "video" or vpath.endswith((".mp4", ".mov", ".webm")):
                clip = _prepare_video_clip(vpath, c_dur)
            elif plan == "screenshot" or "screenshot" in vpath.lower():
                clip = _prepare_screenshot_canvas(vpath, chunk.get("screenshot_url"), c_dur, accent_color)
            else:
                # 16:9 Ken Burns for photos/AI stills
                clip = build_ken_burns(vpath, c_dur, target_size=(FRAME_W, FRAME_H))

        if not clip:
            # Fallback black canvas
            clip = ColorClip(size=(FRAME_W, FRAME_H), color=(10, 12, 20), duration=c_dur)

        clip = clip.with_start(c_start).with_duration(c_dur)
        background_clips.append(clip)

        # 2. Infographic card overlay (if active)
        if has_info:
            itype = chunk.get("infographic_type", "stat")
            idata = chunk.get("infographic_data", {})
            try:
                animator = CardAnimator(itype, idata, accent_color, c_dur)
                card_vclip = VideoClip(animator.frame, duration=c_dur).with_mask(
                    VideoClip(animator.mask, is_mask=True, duration=c_dur)
                ).with_start(c_start)
                card_clips.append(card_vclip)
            except Exception as ce:
                print(f"⚠️ Card build failed: {ce}")

        # 3. Chapter banner (at beginning of each new chapter)
        ch_idx = chunk.get("chapter_index", 0)
        ch_title = chunk.get("chapter_title", "")
        if ch_idx != last_chapter_idx and ch_title:
            banner = build_chapter_banner(ch_title, ch_idx, duration=3.5, accent_color=accent_color)
            banner = banner.with_start(c_start)
            chapter_banners.append(banner)
            last_chapter_idx = ch_idx

        # 4. Lower-third subtitle
        sub_clip = render_longform_subtitle(chunk, accent_color=accent_color)
        if sub_clip:
            sub_clip = sub_clip.with_start(c_start).with_position((0, 0))
            subtitle_clips.append(sub_clip)

    # ── STEP 3: Compose all layers ──
    print("🎬 Compositing video layers...")
    all_layers = []
    all_layers.extend(background_clips)
    all_layers.extend(card_clips)
    all_layers.extend(chapter_banners)
    all_layers.extend(subtitle_clips)

    # Channel watermark
    watermark = create_longform_watermark(total_audio_duration)
    all_layers.append(watermark.with_start(0).with_position((0, 0)))

    final_video = CompositeVideoClip(all_layers, size=(FRAME_W, FRAME_H)).with_duration(total_audio_duration)
    final_video = final_video.with_audio(final_audio)

    # ── STEP 4: Render with FFmpeg ──
    print(f"⚡ Encoding MP4 with libx264/aac (Preset: fast, FPS: 30) to {output_path}...")
    final_video.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="fast",
        threads=4,
        ffmpeg_params=["-crf", "20", "-pix_fmt", "yuv420p"]
    )

    # Close clips to free file descriptors
    try:
        final_video.close()
        final_audio.close()
        audio.close()
    except Exception:
        pass

    if os.path.exists(output_path) and os.path.getsize(output_path) > 100000:
        file_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"🎉 [longform_video] Video rendering COMPLETE: {output_path} ({file_mb:.1f} MB)")
        return output_path
    else:
        print("🚨 [longform_video] Rendered video file is missing or suspiciously small.")
        return None
