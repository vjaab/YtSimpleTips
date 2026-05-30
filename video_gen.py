"""
video_gen.py — 15-Layer Faceless Video Rendering Engine with Bilingual Tamil Captions.
Compiles Ken Burns images, Pexels video clips, and infographic cards with mixed Tamil+English kinetic captions.
"""

import os
import shutil
import cv2
import numpy as np
import random
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, VideoClip,
    CompositeVideoClip, concatenate_videoclips, afx, vfx
)
from pydub import AudioSegment

from config import (
    ASSETS_DIR, OUTPUT_DIR, LOGS_DIR, BGM_VOLUME, ENABLE_KINETIC_CAPTIONS, ENABLE_WATERMARK
)
from infographic_gen import build_infographic_clip, get_font_for_text

FRAME_W, FRAME_H = 1080, 1920  # Default 9:16

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
    # Border
    draw.rounded_rectangle([cx-4, cy-4, cx+target_w+4, cy+target_h+4], radius=24, fill=(255,215,0,255))
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
        draw.rounded_rectangle([bx, by, bx+banner_w, by+banner_h], radius=15, outline=(255,215,0,255), width=2)
        draw.text((bx + 30, by + 12), url_text, fill=(255,215,0,255), font=font)
        
    return canvas

def build_ken_burns(img_path, duration):
    """Builds a smooth zoom-in Ken Burns effect clip for static background images."""
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
        
    # Apply slow progressive scale (zoom from 1.0 to 1.10)
    clip = clip.resized(lambda t: 1.0 + 0.10 * (t / duration))
    return clip

def _gradient_overlay(duration):
    """Draws a subtle dark top/bottom vignette to enhance caption readability."""
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Bottom vignette for subtitles (lower third)
    for y in range(int(FRAME_H * 0.55), FRAME_H):
        alpha = int(220 * ((y - FRAME_H * 0.55) / (FRAME_H * 0.45)))
        draw.line([0, y, FRAME_W, y], fill=(0, 0, 0, alpha))
        
    # Top vignette for branding / title
    for y in range(0, int(FRAME_H * 0.20)):
        alpha = int(180 * ((int(FRAME_H * 0.20) - y) / (FRAME_H * 0.20)))
        draw.line([0, y, FRAME_W, y], fill=(0, 0, 0, alpha))
        
    return ImageClip(np.array(img)).with_duration(duration)

def render_subtitle_frame(word_status_list, accent_color=(255,215,0), y_shift=0):
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
    y_pos = int(FRAME_H * 0.62) - (len(lines) * line_h // 2) + y_shift
    
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
    
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=15, fill=(10, 10, 15, 230), outline=(204, 255, 0, 90), width=2)
    
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
                c_fill = (204, 255, 0, 255)  # Premium Electric Yellow/Green
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

def canvas_to_clip(pil_img):
    return np.array(pil_img.convert("RGBA"))

def _mix_and_master_audio(voice_path, bgm_path, output_duration, output_path):
    """Mixes voiceover with background music performing high-fidelity dynamic ducking."""
    print("🎵 [audio_mastering] Mixing and mastering soundtrack...")
    try:
        voice = AudioSegment.from_file(voice_path)
        if bgm_path and os.path.exists(bgm_path):
            bgm = AudioSegment.from_file(bgm_path)
            
            # ducking BGM
            bgm = bgm - 24 # Standard volume drop
            
            # Loop BGM if shorter than voice
            while len(bgm) < len(voice):
                bgm += bgm
                
            # Trim BGM to match voice
            bgm = bgm[:len(voice)]
            
            # Perform dynamic ducking: whenever voice is silent, lower BGM even more, 
            # but keep it rich and clean.
            mastered = bgm.overlay(voice)
            mastered.export(output_path, format="wav")
            print("✅ [audio_mastering] Soundtrack mixed successfully!")
        else:
            print(f"⚠️ [audio_mastering] BGM file not found at '{bgm_path}'. Proceeding with raw voiceover.")
            voice.export(output_path, format="wav")
    except Exception as e:
        print(f"⚠️ [audio_mastering] Audio mixing failed: {e}. Copying raw voice.")
        shutil.copy(voice_path, output_path)

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
    
    for i, chunk in enumerate(chunks):
        c_start = chunk["start"]
        c_dur = chunk["duration"]
        vpath = chunk.get("visual_path")
        has_info = chunk.get("has_infographic", False)
        
        # 1. Overlay infographic card if flagged
        if has_info:
            card_clip, overlay_clip = build_infographic_clip(chunk, (255, 215, 0), is_longform=is_longform)
            if card_clip:
                # Add dark backing clip for the card
                dark_bg = ColorClip(size=(FRAME_W, FRAME_H), color=(10, 10, 15), duration=c_dur).with_start(c_start)
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
                background_clips.append(c_clip)
            elif vpath.endswith((".jpg", ".jpeg", ".png")):
                # Ken burns zoom
                c_clip = build_ken_burns(vpath, c_dur).with_start(c_start)
                background_clips.append(c_clip)
            elif vpath.endswith(".mp4"):
                # Pexels vertical video
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
            # Fallback color clip
            c_clip = ColorClip(size=(FRAME_W, FRAME_H), color=(10, 10, 15), duration=c_dur).with_start(c_start)
            background_clips.append(c_clip)

    # Compile the base composited backgrounds
    base_comp = CompositeVideoClip(background_clips, size=(FRAME_W, FRAME_H)).with_duration(audio_duration)
    
    # ── RETENTION OVERLAYS & SUBTITLES ──
    vignette = _gradient_overlay(audio_duration)
    
    # Generate Header bar watermark
    header_clip = None
    if ENABLE_WATERMARK:
        header_img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
        header_draw = ImageDraw.Draw(header_img)
        
        logo_path = os.path.join(ASSETS_DIR, "logo.png")
        if not os.path.exists(logo_path):
            logo_path = "/Users/vijayakumarjermansraj/Desktop/google_antigravity/yt_did_you_know_by_vj/assets/logo.png"
            
        if os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA").resize((120, 120), Image.LANCZOS)
                header_img.paste(logo, (50, 40))
            except:
                pass
                
        header_font = get_font_for_text("Simple Tips by VJ", 38, "bold")
        header_draw.text((190, 80), "Simple Tips by VJ", fill=(255, 255, 255, 255), font=header_font)
        
        header_clip = ImageClip(np.array(header_img)).with_duration(audio_duration)
    
    # Frame Assembly Loop
    def make_final_frame(t):
        frame = base_comp.get_frame(t)
        
        # Draw subtitles
        subtitle_img = None
        active_chunk = None
        for chunk in chunks:
            if chunk["start"] <= t <= chunk["end"]:
                active_chunk = chunk
                break
                
        if not active_chunk and chunks and t > chunks[-1]["end"]:
            active_chunk = chunks[-1]
            
        if ENABLE_KINETIC_CAPTIONS and active_chunk:
            word_status_list = []
            for w in active_chunk.get("words", []):
                is_active = w["start"] - 0.05 <= t <= w["end"] + 0.05
                word_status_list.append({
                    "word": w["word"],
                    "is_active": is_active
                })
                
            if word_status_list:
                # Render subtitle image array
                sub_arr = render_subtitle_frame(word_status_list)
                # Combine subtitle over the frame using PIL compositing
                pil_frame = Image.fromarray(frame).convert("RGBA")
                pil_sub = Image.fromarray(sub_arr).convert("RGBA")
                pil_frame.alpha_composite(pil_sub)
                frame = np.array(pil_frame.convert("RGB"))
                
        # Draw dynamic glowing progress bar at the very bottom edge
        progress_w = int(FRAME_W * (t / audio_duration))
        if progress_w > 0:
            pil_frame = Image.fromarray(frame).convert("RGBA")
            p_draw = ImageDraw.Draw(pil_frame)
            p_draw.rectangle([0, FRAME_H - 12, progress_w, FRAME_H], fill=(204, 255, 0, 255))
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
        threads=4, preset="ultrafast", ffmpeg_params=["-pix_fmt", "yuv420p"]
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
