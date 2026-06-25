"""
infographic_gen.py — Programmatic motion-graphic infographic cards with bilingual Tamil support.
Supports 8 card types rendered with Pillow and animated with MoviePy:
  - stat, comparison, timeline, definition, ranking, growth, slide, process
"""

import os
import math
import re
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip
from config import ASSETS_DIR

FRAME_W, FRAME_H = 1080, 1920
VISUAL_CENTER_Y = 650  # Center of visual zone for vertical (200-1100)
VISUAL_CENTER_Y_LONGFORM = 540 # True center for 1080p

def get_dimensions(is_longform):
    if is_longform:
        return 1920, 1080, VISUAL_CENTER_Y_LONGFORM
    return 1080, 1920, VISUAL_CENTER_Y

# Font Paths
_FONT_EXTRA_BOLD = os.path.join(ASSETS_DIR, "fonts", "Montserrat-ExtraBold.ttf")
_FONT_BOLD = os.path.join(ASSETS_DIR, "fonts", "Montserrat-Bold.ttf")
_FONT_REGULAR = os.path.join(ASSETS_DIR, "fonts", "Roboto-Regular.ttf")

_FONT_TAMIL_BOLD = os.path.join(ASSETS_DIR, "fonts", "NotoSansTamil-Bold.ttf")
_FONT_TAMIL_REG = os.path.join(ASSETS_DIR, "fonts", "NotoSansTamil-Regular.ttf")

_FALLBACKS = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
    "/System/Library/Fonts/Supplemental/NotoSansTamil-Regular.ttf",
    "/usr/share/fonts/truetype/roboto/Roboto-Bold.ttf",
]

_font_cache = {}

def _load_font(path, size):
    key = (path, size)
    if key not in _font_cache:
        font_obj = None
        for p in [path] + _FALLBACKS:
            if os.path.exists(p):
                try:
                    font_obj = ImageFont.truetype(p, size)
                    try:
                        if hasattr(font_obj, "set_variation_by_name"):
                            basename = os.path.basename(p).lower()
                            if "extrabold" in basename:
                                font_obj.set_variation_by_name(b"ExtraBold")
                            elif "bold" in basename:
                                font_obj.set_variation_by_name(b"Bold")
                            elif "regular" in basename:
                                font_obj.set_variation_by_name(b"Regular")
                    except Exception:
                        pass
                    break
                except Exception:
                    pass
        if font_obj is None:
            font_obj = ImageFont.load_default()
        _font_cache[key] = font_obj
    return _font_cache[key]

def is_emoji(text):
    for char in str(text):
        o = ord(char)
        if (0x1f300 <= o <= 0x1f9ff) or (0x1fa70 <= o <= 0x1faff) or (0x2600 <= o <= 0x27bf) or (0xfe00 <= o <= 0xfe0f):
            return True
    return False

_EMOJI_FONTS = [
    "/System/Library/Fonts/Apple Color Emoji.ttc",
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/emoji/NotoColorEmoji.ttf",
    "/usr/share/fonts/truetype/noto-color-emoji/NotoColorEmoji.ttf",
]

def _load_emoji_font(size):
    for p in _EMOJI_FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return None

def is_char_supported(font, char):
    try:
        missing_mask = list(font.getmask("\ufffd"))
        char_mask = list(font.getmask(char))
        return char_mask != missing_mask
    except Exception:
        return False

def get_text_runs(text):
    runs = []
    current_run = []
    current_is_tamil = None
    
    for char in str(text):
        is_tamil = '\u0b80' <= char <= '\u0bff'
        if char.isspace() or char in ".,!?-:;()\"'0123456789%":
            if current_is_tamil is None:
                current_is_tamil = is_tamil
            is_tamil = current_is_tamil
            
        if current_is_tamil is None:
            current_is_tamil = is_tamil
            current_run.append(char)
        elif is_tamil == current_is_tamil:
            current_run.append(char)
        else:
            runs.append(("".join(current_run), current_is_tamil))
            current_run = [char]
            current_is_tamil = is_tamil
            
    if current_run:
        runs.append(("".join(current_run), current_is_tamil))
    return runs

class MultilingualFontWrapper:
    def __init__(self, size, weight="regular"):
        self.size = size
        self.weight = weight
        if weight in ("bold", "extrabold"):
            self.font_tamil = _load_font(_FONT_TAMIL_BOLD, size)
        else:
            self.font_tamil = _load_font(_FONT_TAMIL_REG, size)
            
        if weight == "extrabold":
            self.font_latin = _load_font(_FONT_EXTRA_BOLD, size)
        elif weight == "bold":
            self.font_latin = _load_font(_FONT_BOLD, size)
        else:
            self.font_latin = _load_font(_FONT_REGULAR, size)
            
        try:
            self.path = self.font_latin.path
        except AttributeError:
            self.path = ""

    def get_font_for_run(self, is_tamil):
        return self.font_tamil if is_tamil else self.font_latin

    def getbbox(self, text, *args, **kwargs):
        runs = get_text_runs(text)
        ascent_latin = self.font_latin.getmetrics()[0]
        ascent_tamil = self.font_tamil.getmetrics()[0]
        ascent_max = max(ascent_latin, ascent_tamil)
        
        min_top = 9999
        max_bottom = -9999
        x = 0
        for run_text, is_tamil in runs:
            f = self.get_font_for_run(is_tamil)
            bbox = f.getbbox(run_text, *args, **kwargs)
            y_run = ascent_max - f.getmetrics()[0]
            run_top = y_run + bbox[1]
            run_bottom = y_run + bbox[3]
            run_width = bbox[2] - bbox[0]
            
            if run_top < min_top:
                min_top = run_top
            if run_bottom > max_bottom:
                max_bottom = run_bottom
            x += run_width
            
        return (0, min_top if min_top != 9999 else 0, x, max_bottom if max_bottom != -9999 else 0)

    def getmask(self, text, mode="L", *args, **kwargs):
        bbox = self.getbbox(text, *args, **kwargs)
        w = max(1, bbox[2])
        h = max(1, bbox[3] - bbox[1] + 20)
        
        temp_img = Image.new("L", (w + 20, h), 0)
        temp_draw = ImageDraw.Draw(temp_img)
        
        ascent_latin = self.font_latin.getmetrics()[0]
        ascent_tamil = self.font_tamil.getmetrics()[0]
        ascent_max = max(ascent_latin, ascent_tamil)
        
        y_offset = -bbox[1] if bbox[1] < 0 else 0
        
        x = 0
        runs = get_text_runs(text)
        for run_text, is_tamil in runs:
            f = self.get_font_for_run(is_tamil)
            y_run = ascent_max - f.getmetrics()[0] + y_offset
            temp_draw.text((x, y_run), run_text, font=f, fill=255)
            x += f.getbbox(run_text)[2] - f.getbbox(run_text)[0]
            
        return temp_img.im

    def getmetrics(self):
        return self.font_latin.getmetrics()

def get_font_for_text(text, size, weight="regular"):
    """Detects text language/type and returns the corresponding font/wrapper."""
    text_str = str(text)
    if is_emoji(text_str):
        emoji_f = _load_emoji_font(size)
        if emoji_f:
            return emoji_f
            
    is_tamil = bool(re.search(r'[\u0b80-\u0bff]', text_str))
    if is_tamil:
        return MultilingualFontWrapper(size, weight)
    else:
        if weight == "extrabold":
            return _load_font(_FONT_EXTRA_BOLD, size)
        elif weight == "bold":
            return _load_font(_FONT_BOLD, size)
        else:
            return _load_font(_FONT_REGULAR, size)

def _ts(text, font):
    bb = font.getbbox(text)
    return bb[2] - bb[0], bb[3] - bb[1]

def _center_text(draw, text, font, y, color, card_x, card_w):
    tw, _ = _ts(text, font)
    x = card_x + (card_w - tw) // 2
    draw.text((x, y), text, font=font, fill=color)

def _draw_card_bg(draw, cx, cy, cw, ch, accent_color, border=2, radius=24, fill=(10, 15, 44, 235)):
    # 1. Shadow
    draw.rounded_rectangle(
        [cx + 8, cy + 16, cx + cw + 8, cy + ch + 16],
        radius=radius, fill=(0, 0, 0, 180)
    )
    # 2. Outer glow border (4px, semi-transparent)
    draw.rounded_rectangle(
        [cx - 4, cy - 4, cx + cw + 4, cy + ch + 4],
        radius=radius, outline=(*accent_color, 100), width=4
    )
    # 3. Inner glow border (2px, brighter)
    draw.rounded_rectangle(
        [cx - 2, cy - 2, cx + cw + 2, cy + ch + 2],
        radius=radius, outline=(*accent_color, 200), width=2
    )
    # 4. Card body (dark navy)
    draw.rounded_rectangle(
        [cx, cy, cx + cw, cy + ch],
        radius=radius, fill=fill
    )
    # 5. Corner energy sparkles / HUD crosshairs for anime tech look
    r, g, b = accent_color
    line_len = 15
    # Top-Left corner spark
    draw.line([cx - 10, cy, cx - 10 + line_len, cy], fill=(r, g, b, 255), width=3)
    draw.line([cx, cy - 10, cx, cy - 10 + line_len], fill=(r, g, b, 255), width=3)
    # Top-Right corner spark
    draw.line([cx + cw + 10 - line_len, cy, cx + cw + 10, cy], fill=(r, g, b, 255), width=3)
    draw.line([cx + cw, cy - 10, cx + cw, cy - 10 + line_len], fill=(r, g, b, 255), width=3)
    # Bottom-Left corner spark
    draw.line([cx - 10, cy + ch, cx - 10 + line_len, cy + ch], fill=(r, g, b, 255), width=3)
    draw.line([cx, cy + ch + 10 - line_len, cx, cy + ch + 10], fill=(r, g, b, 255), width=3)
    # Bottom-Right corner spark
    draw.line([cx + cw + 10 - line_len, cy + ch, cx + cw + 10, cy + ch], fill=(r, g, b, 255), width=3)
    draw.line([cx + cw, cy + ch + 10 - line_len, cx + cw, cy + ch + 10], fill=(r, g, b, 255), width=3)

# ── 1. Stat Card ──
def _render_stat_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 900, 600
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    headline = data.get("headline", "STATISTICS")
    subtext = data.get("subtext", "Information")
    context = data.get("context", "")
    
    # Scale animations for numbers
    val_pct = int(progress * 100) if progress < 1.0 else 100
    number_str = f"{val_pct}%" if "%" in subtext else f"{subtext}"
    
    font_head = get_font_for_text(headline, 50, "bold")
    font_num = get_font_for_text(number_str, 120, "extrabold")
    font_ctx = get_font_for_text(context, 40, "regular")
    
    _center_text(draw, headline.upper(), font_head, cy + 60, (180, 180, 180, 255), cx, cw)
    _center_text(draw, number_str, font_num, cy + 180, (*accent_color, 255), cx, cw)
    _center_text(draw, context, font_ctx, cy + 420, (230, 230, 230, 255), cx, cw)
    
    return img

# ── 2. Comparison Card ──
def _render_comparison_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 920, 700
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    title = data.get("title", "COMPARISON")
    item1 = data.get("item1", "A")
    val1 = data.get("val1", "")
    item2 = data.get("item2", "B")
    val2 = data.get("val2", "")
    
    font_title = get_font_for_text(title, 45, "bold")
    font_item = get_font_for_text(item1, 55, "bold")
    font_val = get_font_for_text(val1, 40, "regular")
    
    _center_text(draw, title.upper(), font_title, cy + 60, (200, 200, 200, 255), cx, cw)
    
    # Render left vs right
    col_w = cw // 2
    
    draw.text((cx + 50, cy + 200), item1, font=font_item, fill=(255, 255, 255, 255))
    draw.text((cx + 50, cy + 280), val1, font=font_val, fill=(200, 200, 200, 255))
    
    draw.text((cx + col_w + 50, cy + 200), item2, font=font_item, fill=(*accent_color, 255))
    draw.text((cx + col_w + 50, cy + 280), val2, font=font_val, fill=(200, 200, 200, 255))
    
    # Separator
    draw.line([cx + col_w, cy + 180, cx + col_w, cy + 550], fill=(60, 60, 60, 255), width=3)
    
    return img

# ── 3. Timeline Card ──
def _render_timeline_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 900, 750
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    title = data.get("title", "TIMELINE")
    events = data.get("events", [])
    
    font_title = get_font_for_text(title, 45, "bold")
    _center_text(draw, title.upper(), font_title, cy + 50, (200, 200, 200, 255), cx, cw)
    
    # Draw vertical timeline path
    timeline_x = cx + 150
    draw.line([timeline_x, cy + 160, timeline_x, cy + 620], fill=(60, 60, 60, 255), width=4)
    
    active_count = math.ceil(progress * len(events))
    
    for idx, event in enumerate(events[:3]):  # Limit to 3 items
        if idx >= active_count: break
        
        ey = cy + 190 + idx * 160
        date = event.get("date", "")
        desc = event.get("desc", "")
        
        font_date = get_font_for_text(date, 40, "bold")
        font_desc = get_font_for_text(desc, 32, "regular")
        
        # Node circle
        draw.ellipse([timeline_x - 12, ey + 10, timeline_x + 12, ey + 34], fill=(*accent_color, 255))
        
        # Text
        draw.text((timeline_x - 120, ey), date, font=font_date, fill=(*accent_color, 255))
        draw.text((timeline_x + 40, ey + 6), desc, font=font_desc, fill=(230, 230, 230, 255))
        
    return img

# ── 4. Definition Card ──
def _render_definition_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 900, 650
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    term = data.get("term", "CONCEPT")
    definition = data.get("definition", "")
    example = data.get("example", "")
    
    font_term = get_font_for_text(term, 55, "bold")
    font_def = get_font_for_text(definition, 36, "regular")
    font_ex = get_font_for_text(example, 34, "regular")
    
    _center_text(draw, term, font_term, cy + 60, (*accent_color, 255), cx, cw)
    
    # Render definition inside the card with simple word wrap
    def draw_wrapped_text(text, font, start_y, fill_color, max_w=750):
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            tw, _ = _ts(test, font)
            if tw < max_w:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
            
        cur_y = start_y
        for line in lines:
            _center_text(draw, line, font, cur_y, fill_color, cx, cw)
            cur_y += 50
            
    draw_wrapped_text(definition, font_def, cy + 180, (240, 240, 240, 255))
    if example:
        _center_text(draw, "Example:", get_font_for_text("Ex", 36, "bold"), cy + 400, (*accent_color, 255), cx, cw)
        draw_wrapped_text(example, font_ex, cy + 460, (190, 190, 190, 255))
        
    return img

# ── 5. Ranking Card ──
def _render_ranking_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 900, 700
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    title = data.get("title", "TOP LIST")
    items = data.get("items", [])
    
    font_title = get_font_for_text(title, 45, "bold")
    _center_text(draw, title.upper(), font_title, cy + 50, (200, 200, 200, 255), cx, cw)
    
    active_count = math.ceil(progress * len(items))
    
    for idx, item in enumerate(items[:3]):
        if idx >= active_count: break
        
        ry = cy + 180 + idx * 150
        # Draw ranking spot circular badge
        draw.ellipse([cx + 60, ry, cx + 140, ry + 80], fill=(*accent_color, 255))
        _center_text(draw, str(idx+1), get_font_for_text("1", 45, "bold"), ry + 15, (255, 255, 255, 255), cx + 60, 80)
        
        name = item.get("name", "")
        value = item.get("val", "")
        
        font_name = get_font_for_text(name, 42, "bold")
        font_val = get_font_for_text(value, 36, "regular")
        
        draw.text((cx + 180, ry), name, font=font_name, fill=(255, 255, 255, 255))
        draw.text((cx + 180, ry + 45), value, font=font_val, fill=(180, 180, 180, 255))
        
    return img

# ── 6. Growth Card ──
def _render_growth_card(data, accent_color, progress=1.0):
    img = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = 900, 600
    cx = (FRAME_W - cw) // 2
    cy = VISUAL_CENTER_Y - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    title = data.get("title", "GROWTH RATE")
    percent = data.get("percent", "+0%")
    subtext = data.get("subtext", "")
    
    active_percent = f"+{int(progress * int(percent.replace('+', '').replace('%', '')))}%" if '%' in percent else percent
    
    font_title = get_font_for_text(title, 45, "bold")
    font_pct = get_font_for_text(active_percent, 140, "extrabold")
    font_sub = get_font_for_text(subtext, 36, "regular")
    
    _center_text(draw, title.upper(), font_title, cy + 60, (200, 200, 200, 255), cx, cw)
    _center_text(draw, active_percent, font_pct, cy + 180, (46, 204, 113, 255) if '+' in percent else (*accent_color, 255), cx, cw)
    _center_text(draw, subtext, font_sub, cy + 420, (220, 220, 220, 255), cx, cw)
    
    return img

# ── 7. Slide Card (Generic fallback) ──
def _render_slide_card(data, accent_color, progress=1.0, is_longform=False):
    fw, fh, fcy = get_dimensions(is_longform)
    img = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cw, ch = (1400, 600) if is_longform else (900, 600)
    cx = (fw - cw) // 2
    cy = fcy - ch // 2
    
    _draw_card_bg(draw, cx, cy, cw, ch, accent_color)
    
    title = data.get("title", "INFO CARD")
    steps = data.get("steps", [])
    
    font_title = get_font_for_text(title, 45, "bold")
    _center_text(draw, title.upper(), font_title, cy + 50, (200, 200, 200, 255), cx, cw)
    
    active_count = math.ceil(progress * len(steps))
    
    for idx, step in enumerate(steps[:3]):
        if idx >= active_count: break
        
        sy = cy + 180 + idx * 130
        font_step = get_font_for_text(step, 36, "bold")
        _center_text(draw, f"💡 {step}", font_step, sy, (255, 255, 255, 255), cx, cw)
        
    return img

# ── 8. Process Card ──
def _render_process_card(data, accent_color, progress=1.0, is_longform=False):
    return _render_slide_card(data, accent_color, progress, is_longform)

_TYPE_MAP = {
    "stat": _render_stat_card,
    "comparison": _render_comparison_card,
    "timeline": _render_timeline_card,
    "definition": _render_definition_card,
    "ranking": _render_ranking_card,
    "growth": _render_growth_card,
    "slide": _render_slide_card,
    "process": _render_process_card,
}

def render_infographic(infographic_type, infographic_data, accent_color, progress=1.0, is_longform=False):
    """Renders a bilingual infographic card and returns a PIL Image."""
    if isinstance(infographic_data, str):
        try:
            parts = infographic_data.split("|")
            main = parts[0].split(":")
            if infographic_type == "definition":
                infographic_data = {
                    "term": main[0].strip(),
                    "definition": main[1].strip() if len(main)>1 else "",
                    "example": parts[1].strip() if len(parts)>1 else ""
                }
            elif infographic_type == "stat":
                infographic_data = {
                    "headline": main[0].strip(),
                    "subtext": main[1].strip() if len(main)>1 else "",
                    "context": parts[1].strip() if len(parts)>1 else ""
                }
        except Exception:
            pass
            
    renderer = _TYPE_MAP.get(infographic_type, _render_stat_card)
    
    import inspect
    sig = inspect.signature(renderer)
    if "is_longform" in sig.parameters:
        return renderer(infographic_data, accent_color, progress, is_longform=is_longform)
    else:
        return renderer(infographic_data, accent_color, progress)

def build_infographic_clip(chunk, accent_color, is_longform=False):
    """Builds a MoviePy clip for an infographic card with dynamic animations."""
    info = chunk.get("infographic_data", {})
    info_type = chunk.get("infographic_type", "stat")
    dur = chunk.get("duration", 2.0)
    start = chunk.get("start", 0.0)

    if dur < 0.2:
        return None, None

    fw, fh, fcy = get_dimensions(is_longform)
    fade_in = 0.3
    fade_out = 0.2
    count_dur = min(1.5, dur * 0.6)

    def make_frame(t):
        progress = min(1.0, t / count_dur) if count_dur > 0 else 1.0
        img = render_infographic(info_type, info, accent_color, progress, is_longform=is_longform)
        return np.array(img.convert("RGB"))

    def make_mask(t):
        progress = min(1.0, t / count_dur) if count_dur > 0 else 1.0
        img = render_infographic(info_type, info, accent_color, progress, is_longform=is_longform)
        mask_arr = np.array(img.split()[3]).astype(float) / 255.0

        if t < fade_in:
            mask_arr *= t / fade_in
        if dur - t < fade_out:
            mask_arr *= max(0, (dur - t) / fade_out)

        return mask_arr

    card_clip = VideoClip(make_frame, duration=dur)
    card_mask = VideoClip(make_mask, is_mask=True, duration=dur)
    card_clip = card_clip.with_mask(card_mask).with_start(start)

    overlay_arr = np.zeros((fh, fw, 3), dtype=np.uint8)

    def overlay_mask(t):
        base = 0.75
        if t < fade_in:
            return np.full((fh, fw), base * (t / fade_in))
        if dur - t < fade_out:
            return np.full((fh, fw), base * max(0, (dur - t) / fade_out))
        return np.full((fh, fw), base)

    overlay_clip = VideoClip(lambda t: overlay_arr, duration=dur)
    overlay_mask_clip = VideoClip(overlay_mask, is_mask=True, duration=dur)
    overlay_clip = overlay_clip.with_mask(overlay_mask_clip).with_start(start)

    return card_clip, overlay_clip
