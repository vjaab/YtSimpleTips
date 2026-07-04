"""
settings_ui_gen.py — Programmatically generates realistic settings menu screen recordings.
Simulates dark-mode iOS/Android UI navigation, finger taps, pulsing rings, and highlight borders.
"""

import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from config import ASSETS_DIR, OUTPUT_DIR

# Global font paths
FONT_BOLD = os.path.join(ASSETS_DIR, "fonts", "Montserrat-Bold.ttf")
FONT_REGULAR = os.path.join(ASSETS_DIR, "fonts", "Roboto-Regular.ttf")

def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_device_bezel(draw, px, py, pw, ph, radius=32):
    """Draws a beautiful phone device bezel with a notch/pill."""
    # Outer frame shadow
    draw.rounded_rectangle([px - 4, py - 4, px + pw + 4, py + ph + 4], radius=radius+4, fill=(0, 0, 0, 80))
    # Bezel
    draw.rounded_rectangle([px, py, px + pw, py + ph], radius=radius, outline=(40, 40, 45, 255), width=10, fill=(15, 15, 18, 255))
    # Dynamic notch/pill
    pill_w, pill_h = 110, 20
    pill_x1 = px + (pw - pill_w) // 2
    pill_y1 = py + 12
    draw.rounded_rectangle([pill_x1, pill_y1, pill_x1 + pill_w, pill_y1 + pill_h], radius=10, fill=(5, 5, 8, 255))

def draw_status_bar(draw, px, py, pw, font):
    """Draws a clean top status bar (time, wifi, signal, battery)."""
    # Time
    draw.text((px + 30, py + 15), "9:41", font=font, fill=(255, 255, 255, 220))
    # Wifi/Cell icons mock (just circles/rectangles)
    x_icons = px + pw - 90
    y_icons = py + 16
    # Cell Signal
    for idx in range(4):
        h = 4 + idx * 3
        draw.rectangle([x_icons + idx * 5, y_icons + 10 - h, x_icons + idx * 5 + 3, y_icons + 10], fill=(255, 255, 255, 200))
    # Wifi wave mock
    draw.arc([x_icons + 25, y_icons - 3, x_icons + 41, y_icons + 13], 220, 320, fill=(255, 255, 255, 200), width=2)
    # Battery pill
    draw.rounded_rectangle([x_icons + 48, y_icons, x_icons + 70, y_icons + 11], radius=3, outline=(255, 255, 255, 160), width=1)
    draw.rectangle([x_icons + 50, y_icons + 2, x_icons + 65, y_icons + 9], fill=(57, 255, 20, 200))  # Green full battery
    draw.rectangle([x_icons + 71, y_icons + 3, x_icons + 73, y_icons + 8], fill=(255, 255, 255, 160))

def draw_header_bar(draw, px, py, pw, title, font_title):
    """Draws settings screen title header with a back button."""
    # Back button arrow '<'
    draw.line([px + 30, py + 60, px + 22, py + 68], fill=(57, 255, 20, 255), width=3)
    draw.line([px + 22, py + 68, px + 30, py + 76], fill=(57, 255, 20, 255), width=3)
    # Title centered
    bbox = font_title.getbbox(title)
    t_w = bbox[2] - bbox[0]
    draw.text((px + (pw - t_w) // 2, py + 52), title, font=font_title, fill=(255, 255, 255, 255))
    # Bottom separator line
    draw.line([px + 10, py + 95, px + pw - 10, py + 95], fill=(30, 30, 35, 255), width=1)

def draw_toggle_switch(draw, x, y, is_on=False, transition_progress=1.0):
    """Draws a beautiful iOS-like toggle switch with state transition support."""
    width, height = 55, 30
    radius = height // 2
    
    # State interpolation
    if is_on:
        # Off to On
        bg_color = (int(30 + (57 - 30) * transition_progress),
                    int(30 + (255 - 30) * transition_progress),
                    int(35 + (20 - 35) * transition_progress), 255)
        knob_x = x + 4 + int((width - height) * transition_progress)
    else:
        # On to Off
        bg_color = (int(57 + (30 - 57) * transition_progress),
                    int(255 + (30 - 255) * transition_progress),
                    int(20 + (35 - 20) * transition_progress), 255)
        knob_x = x + 4 + int((width - height) * (1.0 - transition_progress))

    draw.rounded_rectangle([x, y, x + width, y + height], radius=radius, fill=bg_color)
    draw.ellipse([knob_x, y + 3, knob_x + height - 6, y + height - 3], fill=(255, 255, 255, 255))

def draw_setting_row(draw, x, y, w, icon_emoji, title, subtitle, right_type="chevron", toggle_state=False, is_highlighted=False, font_t=None, font_s=None):
    """Draws a single menu row in settings list."""
    row_h = 75
    # Click feedback highlight
    if is_highlighted:
        draw.rounded_rectangle([x + 10, y, x + w - 10, y + row_h], radius=10, fill=(30, 30, 40, 255))
    
    # Icon circle background
    draw.ellipse([x + 25, y + 15, x + 70, y + 60], fill=(25, 25, 30, 255))
    # Icon emoji
    draw.text((x + 36, y + 22), icon_emoji, font=font_s, fill=(255, 255, 255, 255))
    
    # Text Titles
    draw.text((x + 85, y + 17), title, font=font_t, fill=(255, 255, 255, 255))
    if subtitle:
        draw.text((x + 85, y + 43), subtitle, font=font_s, fill=(160, 160, 170, 255))
        
    # Right side element
    if right_type == "chevron":
        # Chevron arrow '>'
        cx = x + w - 40
        cy = y + 37
        draw.line([cx, cy - 6, cx + 5, cy], fill=(120, 120, 130, 255), width=2)
        draw.line([cx + 5, cy, cx, cy + 6], fill=(120, 120, 130, 255), width=2)
    elif right_type == "toggle":
        draw_toggle_switch(draw, x + w - 85, y + 22, is_on=toggle_state)
        
    # Separator
    draw.line([x + 85, y + row_h, x + w - 25, y + row_h], fill=(30, 30, 35, 255), width=1)
    return row_h

def draw_settings_list(draw, px, py, pw, ph, screen_data, active_idx=None, font_t=None, font_s=None):
    """Renders a full list of settings items."""
    cur_y = py + 110
    row_positions = []
    
    for idx, row in enumerate(screen_data.get("rows", [])):
        is_high = (idx == active_idx)
        r_type = row.get("right_type", "chevron")
        t_state = row.get("toggle_state", False)
        
        row_y = cur_y
        row_h = draw_setting_row(
            draw, px, cur_y, pw,
            row.get("icon", "⚙️"), row.get("title", ""), row.get("subtitle", ""),
            right_type=r_type, toggle_state=t_state, is_highlighted=is_high,
            font_t=font_t, font_s=font_s
        )
        row_positions.append((row_y, row_h))
        cur_y += row_h
        
    return row_positions

def draw_dictionary_screen(draw, px, py, pw, word, shortcut, font_t, font_s):
    """Renders the dictionary shortcut editing screen."""
    cur_y = py + 120
    # Input group title
    draw.text((px + 30, cur_y), "Add Shortcut", font=font_t, fill=(57, 255, 20, 255))
    cur_y += 50
    
    # Word Input Card
    draw.rounded_rectangle([px + 20, cur_y, px + pw - 20, cur_y + 90], radius=12, fill=(20, 20, 25, 255), outline=(40, 40, 50, 255), width=1)
    draw.text((px + 40, cur_y + 15), "Type a word (e.g. email)", font=font_s, fill=(150, 150, 160, 255))
    draw.text((px + 40, cur_y + 45), word, font=font_t, fill=(255, 255, 255, 255))
    cur_y += 120
    
    # Shortcut Input Card
    draw.rounded_rectangle([px + 20, cur_y, px + pw - 20, cur_y + 90], radius=12, fill=(20, 20, 25, 255), outline=(40, 40, 50, 255), width=1)
    draw.text((px + 40, cur_y + 15), "Optional shortcut (e.g. em)", font=font_s, fill=(150, 150, 160, 255))
    draw.text((px + 40, cur_y + 45), shortcut, font=font_t, fill=(57, 255, 20, 255))

def generate_settings_clip(chunk_text, duration, output_path):
    """
    Programmatically renders a settings navigation clip based on matching keywords.
    Compiles PIL-rendered frames at 30 fps using MoviePy.
    """
    # 1. Parse keywords to determine screens and actions
    text_lower = chunk_text.lower()
    
    # Initialize Screen Data templates
    screen_main = {
        "title": "Gboard Settings",
        "rows": [
            {"icon": "🌐", "title": "Languages", "subtitle": "English (US), Tamil"},
            {"icon": "⚙️", "title": "Preferences", "subtitle": "Key vibration, sound"},
            {"icon": "🎨", "title": "Theme", "subtitle": "Dark material"},
            {"icon": "📝", "title": "Text Correction", "subtitle": "Auto-correct, Smart replies"},
            {"icon": "✍️", "title": "Glide Typing", "subtitle": "Gesture input"},
            {"icon": "📖", "title": "Dictionary", "subtitle": "Personal shortcuts"}
        ]
    }
    
    screen_correction = {
        "title": "Text Correction",
        "rows": [
            {"icon": "💡", "title": "Show suggestion strip", "right_type": "toggle", "toggle_state": True},
            {"icon": "🔮", "title": "Next-word suggestions", "right_type": "toggle", "toggle_state": True},
            {"icon": "❌", "title": "Auto-correction", "right_type": "toggle", "toggle_state": False},
            {"icon": "🔠", "title": "Auto-capitalization", "right_type": "toggle", "toggle_state": True},
            {"icon": "⚡", "title": "Double-space period", "right_type": "toggle", "toggle_state": True}
        ]
    }
    
    screen_glide = {
        "title": "Glide Typing",
        "rows": [
            {"icon": "✍️", "title": "Enable glide typing", "right_type": "toggle", "toggle_state": False},
            {"icon": "🌈", "title": "Show gesture trail", "right_type": "toggle", "toggle_state": True},
            {"icon": "🔙", "title": "Enable gesture delete", "right_type": "toggle", "toggle_state": True}
        ]
    }
    
    # Set default values for Gboard simulation
    screen_1 = screen_main
    screen_2 = None
    target_idx = 3 # Text Correction by default
    action_type = "navigate"  # "navigate" or "toggle" or "type"
    step_label = "SETTINGS"
    
    # Pick navigation paths based on keywords
    if "text correction" in text_lower or "auto-correct" in text_lower or "correction" in text_lower:
        screen_1 = screen_main
        screen_2 = screen_correction
        target_idx = 3  # Text Correction row in main settings
        action_idx = 2  # Auto-correction toggle in correction sub-screen
        action_type = "toggle"
        step_label = "STEP 1: TEXT CORRECTION"
    elif "glide typing" in text_lower or "glide" in text_lower or "typing speed" in text_lower:
        screen_1 = screen_main
        screen_2 = screen_glide
        target_idx = 4  # Glide Typing row in main settings
        action_idx = 0  # Enable glide typing toggle in glide sub-screen
        action_type = "toggle"
        step_label = "STEP 2: GLIDE TYPING"
    elif "shortcut" in text_lower or "dictionary" in text_lower or "vj.simple.tips" in text_lower or "email" in text_lower:
        screen_1 = screen_main
        screen_2 = "dictionary"
        target_idx = 5  # Dictionary row in main settings
        action_type = "type"
        step_label = "STEP 3: CREATE SHORTCUT"
    elif "settings" in text_lower or "gboard" in text_lower or "preference" in text_lower or "theme" in text_lower:
        screen_1 = screen_main
        screen_2 = None
        target_idx = 3  # Highlight Text Correction
        action_type = "navigate"
        step_label = "GBOARD SETTINGS"
    else:
        # Fallback to generic settings mockup if none matches
        screen_main["title"] = "Phone Settings"
        screen_main["rows"][target_idx] = {"icon": "🤖", "title": "AI & Smart Assistant", "subtitle": "Smart features"}
        step_label = "PHONE SETTINGS"

    # Frame properties
    w, h = 1080, 1920
    fps = 30
    total_frames = int(duration * fps)
    
    # Phone size inside vertical video
    pw, ph = 600, 1060
    px = (w - pw) // 2
    py = 320
    
    # Load fonts
    font_title = _load_font(FONT_BOLD, 30)
    font_row_t = _load_font(FONT_BOLD, 22)
    font_row_s = _load_font(FONT_REGULAR, 17)
    font_label = _load_font(FONT_BOLD, 42)
    font_tap = _load_font(FONT_BOLD, 24)
    
    frames_list = []
    
    # Animate timeline:
    # Phase 1 (0.0s to 1.0s): cursor slides from bottom-right (w, h) to target row on Screen 1
    # Phase 2 (1.0s to 1.3s): pulse tap feedback on Screen 1 target
    # Phase 3 (1.3s to 1.8s): slide transition to Screen 2
    # Phase 4 (1.8s to 2.5s): cursor slides to the toggle/field on Screen 2
    # Phase 5 (2.5s to 2.8s): tap/type action
    # Phase 6 (2.8s to end): display final state with glowing highlight and label
    
    for f_idx in range(total_frames):
        t = f_idx / fps
        
        # Base canvas: dark background with tech grid or subtle gradient
        img = Image.new("RGBA", (w, h), (10, 10, 14, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw background tech grid
        grid_spacing = 60
        for gx in range(0, w, grid_spacing):
            draw.line([gx, 0, gx, h], fill=(20, 20, 30, 255), width=1)
        for gy in range(0, h, grid_spacing):
            draw.line([0, gy, w, gy], fill=(20, 20, 30, 255), width=1)
            
        # Draw bold on-screen label banner
        draw.text((w // 2 - 200, 200), step_label, font=font_label, fill=(204, 255, 0, 255))
        
        # Phone canvas
        phone_img = Image.new("RGBA", (pw, ph), (15, 15, 18, 255))
        p_draw = ImageDraw.Draw(phone_img)
        
        # Render static lists on phone_img
        draw_status_bar(p_draw, 0, 0, pw, font_row_s)
        
        # Calculate cursor/pointer coordinates
        cursor_x, cursor_y = -100, -100
        show_cursor = False
        tap_progress = 0.0
        
        # Active highlight boundaries
        highlight_box = None
        
        # Render screens
        if screen_2 is None:
            # Simple single-screen animation
            draw_header_bar(p_draw, 0, 0, pw, screen_1["title"], font_title)
            row_y_list = draw_settings_list(p_draw, 0, 0, pw, ph, screen_1, font_t=font_row_t, font_s=font_row_s)
            
            # Cursor targets target_idx
            ty = row_y_list[target_idx][0] + row_y_list[target_idx][1] // 2
            tx = pw - 50
            
            if t < 1.0:
                p = t / 1.0
                cursor_x = int(pw + (tx - pw) * p)
                cursor_y = int(ph + (ty - ph) * p)
                show_cursor = True
            elif 1.0 <= t < 1.3:
                cursor_x, cursor_y = tx, ty
                show_cursor = True
                tap_progress = (t - 1.0) / 0.3
            else:
                # Highlight row
                highlight_box = [20, row_y_list[target_idx][0] + 5, pw - 20, row_y_list[target_idx][0] + row_y_list[target_idx][1] - 5]
                
        else:
            # Dual-screen navigation
            if t < 1.3:
                # Screen 1 is active
                draw_header_bar(p_draw, 0, 0, pw, screen_1["title"], font_title)
                row_y_list = draw_settings_list(p_draw, 0, 0, pw, ph, screen_1, font_t=font_row_t, font_s=font_row_s)
                ty = row_y_list[target_idx][0] + row_y_list[target_idx][1] // 2
                tx = pw // 2
                
                if t < 1.0:
                    p = t / 1.0
                    cursor_x = int(pw + (tx - pw) * p)
                    cursor_y = int(ph + (ty - ph) * p)
                    show_cursor = True
                else:
                    cursor_x, cursor_y = tx, ty
                    show_cursor = True
                    tap_progress = (t - 1.0) / 0.3
            elif 1.3 <= t < 1.8:
                # Sliding Transition to Screen 2
                slide_progress = (t - 1.3) / 0.5
                # Screen 1 slides OUT left
                offset_s1 = -int(pw * slide_progress)
                # Screen 2 slides IN right
                offset_s2 = pw - int(pw * slide_progress)
                
                # Render Screen 1 on temporary canvas
                s1_img = Image.new("RGBA", (pw, ph), (15, 15, 18, 0))
                s1_draw = ImageDraw.Draw(s1_img)
                draw_header_bar(s1_draw, 0, 0, pw, screen_1["title"], font_title)
                draw_settings_list(s1_draw, 0, 0, pw, ph, screen_1, font_t=font_row_t, font_s=font_row_s)
                phone_img.alpha_composite(s1_img, (offset_s1, 0))
                
                # Render Screen 2 on temporary canvas
                s2_img = Image.new("RGBA", (pw, ph), (15, 15, 18, 0))
                s2_draw = ImageDraw.Draw(s2_img)
                if screen_2 == "dictionary":
                    draw_header_bar(s2_draw, 0, 0, pw, "English (US)", font_title)
                    draw_dictionary_screen(s2_draw, 0, 0, pw, "", "", font_row_t, font_row_s)
                else:
                    draw_header_bar(s2_draw, 0, 0, pw, screen_2["title"], font_title)
                    draw_settings_list(s2_draw, 0, 0, pw, ph, screen_2, font_t=font_row_t, font_s=font_row_s)
                phone_img.alpha_composite(s2_img, (offset_s2, 0))
                
            else:
                # Screen 2 is active
                if screen_2 == "dictionary":
                    draw_header_bar(p_draw, 0, 0, pw, "English (US)", font_title)
                    # Type animation
                    if t < 2.3:
                        # Typing Word
                        word_p = min(1.0, (t - 1.8) / 0.5)
                        typed_word = "vj.simple.tips@gmail.com"[:int(len("vj.simple.tips@gmail.com") * word_p)]
                        draw_dictionary_screen(p_draw, 0, 0, pw, typed_word, "", font_row_t, font_row_s)
                    else:
                        # Typing Shortcut
                        short_p = min(1.0, (t - 2.3) / 0.5)
                        typed_shortcut = "email"[:int(5 * short_p)]
                        draw_dictionary_screen(p_draw, 0, 0, pw, "vj.simple.tips@gmail.com", typed_shortcut, font_row_t, font_row_s)
                        
                        # Finally highlight the shortcut input field
                        highlight_box = [20, 290, pw - 20, 390]
                else:
                    # Toggle switch animation
                    draw_header_bar(p_draw, 0, 0, pw, screen_2["title"], font_title)
                    # Copy screen_2 to change toggle state dynamically
                    screen_temp = dict(screen_2)
                    screen_temp["rows"] = [dict(r) for r in screen_2["rows"]]
                    
                    ty = py + 110 + action_idx * 75 + 37
                    tx = pw - 60
                    
                    if 1.8 <= t < 2.5:
                        # Move cursor to toggle
                        p = (t - 1.8) / 0.7
                        cursor_x = int(pw // 2 + (tx - pw // 2) * p)
                        cursor_y = int(ph // 2 + (ty - ph // 2) * p)
                        show_cursor = True
                        screen_temp["rows"][action_idx]["toggle_state"] = False
                        draw_settings_list(p_draw, 0, 0, pw, ph, screen_temp, font_t=font_row_t, font_s=font_row_s)
                    elif 2.5 <= t < 2.8:
                        # Tapping
                        cursor_x, cursor_y = tx, ty
                        show_cursor = True
                        tap_progress = (t - 2.5) / 0.3
                        # Animate switch state sliding
                        screen_temp["rows"][action_idx]["toggle_state"] = True
                        draw_settings_list(p_draw, 0, 0, pw, ph, screen_temp, font_t=font_row_t, font_s=font_row_s)
                    else:
                        # Completed toggled state
                        screen_temp["rows"][action_idx]["toggle_state"] = True
                        row_y_list = draw_settings_list(p_draw, 0, 0, pw, ph, screen_temp, font_t=font_row_t, font_s=font_row_s)
                        highlight_box = [20, row_y_list[action_idx][0] + 5, pw - 20, row_y_list[action_idx][0] + row_y_list[action_idx][1] - 5]
                        
        # Draw highlight box around target settings item
        if highlight_box:
            hb = highlight_box
            p_draw.rounded_rectangle([hb[0], hb[1], hb[2], hb[3]], radius=12, outline=(204, 255, 0, 255), width=3)
            
        # Draw pulsing tap circle if active
        if tap_progress > 0.0:
            max_r = 60
            r = int(max_r * tap_progress)
            alpha = int(180 * (1.0 - tap_progress))
            # Translucent pulsing circle on phone screen
            overlay = Image.new("RGBA", (pw, ph), (0,0,0,0))
            o_draw = ImageDraw.Draw(overlay)
            o_draw.ellipse([cursor_x - r, cursor_y - r, cursor_x + r, cursor_y + r], outline=(204, 255, 0, alpha), width=3)
            o_draw.ellipse([cursor_x - r//2, cursor_y - r//2, cursor_x + r//2, cursor_y + r//2], fill=(204, 255, 0, alpha//2))
            phone_img.alpha_composite(overlay)

        # Draw finger cursor pointer emoji
        if show_cursor:
            # Standard emoji overlay (👆)
            cursor_font = _load_font(FONT_BOLD, 38)
            # Offset so pointer points to the coordinate
            p_draw.text((cursor_x - 10, cursor_y - 10), "👆", font=cursor_font, fill=(255, 255, 255, 255))
            
        # Assemble phone screen inside vertical frame
        draw_device_bezel(draw, px, py, pw, ph, radius=35)
        
        # Paste screen contents inside phone bezel boundary
        # Bezel stroke is 10px wide, so offset paste by +10px
        phone_crop = phone_img.crop((10, 10, pw - 10, ph - 10))
        img.paste(phone_crop, (px + 10, py + 10))
        
        # Convert PIL frame to numpy array for MoviePy compatibility
        frame_arr = np.array(img.convert("RGB"))
        frames_list.append(frame_arr)
        
    # Save sequence to MP4 using MoviePy ImageSequenceClip
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    clip = ImageSequenceClip(frames_list, fps=30)
    clip.write_videofile(output_path, codec="libx264", audio=False, logger=None)
    clip.close()
    
    print(f"📱 Programmatic Settings UI video created: {output_path} ({duration:.1f}s)")
    return output_path
