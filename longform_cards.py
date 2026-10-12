# -*- coding: utf-8 -*-
"""
longform_cards.py — 1920x1080 animated data cards for the LONGFORM pipeline.

infographic_gen.py draws most card types on a fixed 1080x1920 portrait canvas (only slide/process/code/diagram have
landscape support), so longform ships its own widescreen renderer for the six data card types:
stat, comparison, timeline, definition, ranking, growth.

render_card(type, data, accent, progress) → RGBA PIL image (1920x1080, transparent outside the card).
CardAnimator wraps it as cached MoviePy frame/mask functions with fade in/out and count-up animation.
"""

import math
import re

import numpy as np
from PIL import Image, ImageDraw

from infographic_gen import get_font_for_text

W, H = 1920, 1080
CARD_W, CARD_H = 1380, 640
CX0, CY0 = (W - CARD_W) // 2, (H - CARD_H) // 2 - 30
_BODY = (12, 16, 40, 238)


# ─────────────────────────────────────────────────────────────────────────────
# Drawing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _font(text, size, weight="bold"):
    return get_font_for_text(str(text), size, weight)


def _tw(font, text):
    bb = font.getbbox(text)
    return bb[2] - bb[0]


def _center(draw, text, font, y, fill, cx=W // 2):
    draw.text((cx - _tw(font, text) // 2, y), text, font=font, fill=fill)


def _wrap(text, font, max_w, max_lines=4):
    words, lines, cur = str(text).split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if _tw(font, trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines[:max_lines]


def _card_body(draw, accent):
    x, y, w, h = CX0, CY0, CARD_W, CARD_H
    draw.rounded_rectangle([x + 10, y + 18, x + w + 10, y + h + 18], radius=32, fill=(0, 0, 0, 170))
    draw.rounded_rectangle([x - 4, y - 4, x + w + 4, y + h + 4], radius=34, outline=(*accent, 110), width=4)
    draw.rounded_rectangle([x, y, x + w, y + h], radius=30, fill=_BODY)
    # Accent bar on the left edge + subtle corner brackets
    draw.rounded_rectangle([x, y + 40, x + 10, y + h - 40], radius=5, fill=(*accent, 255))
    for (bx, by, sx, sy) in ((x + 24, y + 24, 1, 1), (x + w - 24, y + 24, -1, 1),
                             (x + 24, y + h - 24, 1, -1), (x + w - 24, y + h - 24, -1, -1)):
        draw.line([bx, by, bx + 34 * sx, by], fill=(*accent, 220), width=4)
        draw.line([bx, by, bx, by + 34 * sy], fill=(*accent, 220), width=4)


def _title(draw, text, accent, y=CY0 + 56):
    f = _font(text, 40, "bold")
    t = str(text).upper()
    _center(draw, t, f, y, (190, 198, 225, 255))
    tw = _tw(f, t)
    draw.line([W // 2 - tw // 2, y + 62, W // 2 + tw // 2, y + 62], fill=(*accent, 255), width=3)


def _ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def _animate_number(text, progress):
    """Counts up the leading number inside `text` (e.g. '1,600 YEARS' → '960 YEARS'), keeping suffix/prefix."""
    s = str(text)
    m = re.search(r"(\d[\d,]*\.?\d*)", s)
    if not m or progress >= 1.0:
        return s
    raw = m.group(1)
    try:
        target = float(raw.replace(",", ""))
    except ValueError:
        return s
    cur = target * _ease(progress)
    if "." in raw:
        decimals = len(raw.split(".")[1])
        shown = f"{cur:,.{decimals}f}"
    else:
        shown = f"{int(round(cur)):,}" if "," in raw else str(int(round(cur)))
    return s[:m.start()] + shown + s[m.end():]


# ─────────────────────────────────────────────────────────────────────────────
# Card types
# ─────────────────────────────────────────────────────────────────────────────

def _stat(draw, d, accent, p):
    head = str(d.get("headline", "KEY NUMBER"))
    sub = _animate_number(d.get("subtext", ""), p)
    ctx = str(d.get("context", ""))
    _title(draw, head, accent)
    size = 190 if _tw(_font(sub, 190, "extrabold"), sub) <= CARD_W - 160 else 130
    f_num = _font(sub, size, "extrabold")
    _center(draw, sub, f_num, CY0 + 190, (*accent, 255))
    if ctx:
        for i, line in enumerate(_wrap(ctx, _font(ctx, 42, "regular"), CARD_W - 240, 2)):
            _center(draw, line, _font(line, 42, "regular"), CY0 + 460 + i * 58, (232, 235, 245, 255))


def _comparison(draw, d, accent, p):
    _title(draw, d.get("title", "Comparison"), accent)
    col_w = CARD_W // 2
    for i, (name, val) in enumerate(((d.get("item1", "A"), d.get("val1", "")), (d.get("item2", "B"), d.get("val2", "")))):
        cx = CX0 + col_w * i + col_w // 2
        a = int(255 * _ease(p * 1.4 - i * 0.3))
        color = (255, 255, 255, a) if i == 0 else (*accent, a)
        f_name = _font(name, 70, "extrabold")
        _center(draw, str(name), f_name, CY0 + 210, color, cx)
        for j, line in enumerate(_wrap(val, _font(val, 46, "regular"), col_w - 140, 3)):
            _center(draw, line, _font(line, 46, "regular"), CY0 + 330 + j * 62, (215, 220, 235, a), cx)
    draw.line([W // 2, CY0 + 190, W // 2, CY0 + CARD_H - 70], fill=(70, 78, 110, 255), width=3)
    r = 44
    draw.ellipse([W // 2 - r, CY0 + CARD_H // 2 - r, W // 2 + r, CY0 + CARD_H // 2 + r], fill=(*accent, 255))
    _center(draw, "VS", _font("VS", 36, "extrabold"), CY0 + CARD_H // 2 - 22, (10, 12, 30, 255))


def _timeline(draw, d, accent, p):
    _title(draw, d.get("title", "Timeline"), accent)
    events = [e for e in (d.get("events") or []) if isinstance(e, dict)][:3]
    n = max(1, len(events))
    y_line = CY0 + 300
    x0, x1 = CX0 + 140, CX0 + CARD_W - 140
    draw.line([x0, y_line, x1, y_line], fill=(70, 78, 110, 255), width=6)
    prog_x = x0 + (x1 - x0) * _ease(p)
    draw.line([x0, y_line, prog_x, y_line], fill=(*accent, 255), width=6)
    seg = (x1 - x0) / max(1, n - 1) if n > 1 else 0
    col_w = int((x1 - x0) / n) if n > 1 else CARD_W - 300
    for i, e in enumerate(events):
        x = x0 + seg * i if n > 1 else W // 2
        if x > prog_x + 2:
            continue
        draw.ellipse([x - 20, y_line - 20, x + 20, y_line + 20], fill=(*accent, 255), outline=(255, 255, 255, 255), width=4)
        date = str(e.get("date", ""))
        _center(draw, date, _font(date, 54, "extrabold"), y_line - 110, (*accent, 255), int(x))
        for j, line in enumerate(_wrap(e.get("desc", ""), _font("x", 40, "regular"), min(col_w - 30, 420), 3)):
            _center(draw, line, _font(line, 40, "regular"), y_line + 50 + j * 54, (232, 235, 245, 255), int(x))


def _definition(draw, d, accent, p):
    term = str(d.get("term", "Concept"))
    _center(draw, term, _font(term, 90, "extrabold"), CY0 + 70, (*accent, 255))
    y = CY0 + 215
    f_def = _font(d.get("definition", ""), 46, "regular")
    for line in _wrap(d.get("definition", ""), f_def, CARD_W - 260, 3):
        _center(draw, line, _font(line, 46, "regular"), y, (240, 242, 250, 255))
        y += 64
    ex = str(d.get("example", ""))
    if ex:
        box_y = CY0 + CARD_H - 170
        draw.rounded_rectangle([CX0 + 90, box_y, CX0 + CARD_W - 90, box_y + 110], radius=22, fill=(*accent, 40), outline=(*accent, 200), width=2)
        line = _wrap(ex, _font(ex, 38, "regular"), CARD_W - 280, 1)[0]
        _center(draw, line, _font(line, 38, "regular"), box_y + 33, (225, 230, 245, 255))


def _ranking(draw, d, accent, p):
    _title(draw, d.get("title", "Ranking"), accent)
    items = [i for i in (d.get("items") or []) if isinstance(i, dict)][:3]
    for i, it in enumerate(items):
        a = _ease(p * 1.6 - i * 0.35)
        if a <= 0:
            continue
        y = CY0 + 175 + i * 140
        shift = int((1 - a) * 80)
        al = int(255 * a)
        draw.rounded_rectangle([CX0 + 90 - shift, y, CX0 + CARD_W - 90 - shift, y + 112], radius=24, fill=(255, 255, 255, int(22 * a)))
        draw.ellipse([CX0 + 120 - shift, y + 16, CX0 + 200 - shift, y + 96], fill=(*accent, al))
        _center(draw, str(i + 1), _font("1", 48, "extrabold"), y + 26, (10, 12, 30, al), CX0 + 160 - shift)
        name, val = str(it.get("name", "")), str(it.get("val", ""))
        draw.text((CX0 + 240 - shift, y + 26), name, font=_font(name, 50, "bold"), fill=(255, 255, 255, al))
        f_val = _font(val, 44, "extrabold")
        draw.text((CX0 + CARD_W - 130 - shift - _tw(f_val, val), y + 30), val, font=f_val, fill=(*accent, al))


def _growth(draw, d, accent, p):
    _title(draw, d.get("title", "Growth"), accent)
    percent = str(d.get("percent", "+0%"))
    shown = _animate_number(percent, p)
    green = (52, 211, 153, 255) if "+" in percent else (*accent, 255)
    _center(draw, shown, _font(shown, 210, "extrabold"), CY0 + 175, green)
    sub = str(d.get("subtext", ""))
    if sub:
        line = _wrap(sub, _font(sub, 46, "regular"), CARD_W - 240, 1)[0]
        _center(draw, line, _font(line, 46, "regular"), CY0 + 470, (232, 235, 245, 255))


_RENDERERS = {
    "stat": _stat, "comparison": _comparison, "timeline": _timeline,
    "definition": _definition, "ranking": _ranking, "growth": _growth,
}


def render_card(card_type, data, accent, progress=1.0):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _card_body(draw, accent)
    renderer = _RENDERERS.get(card_type, _stat)
    try:
        renderer(draw, data if isinstance(data, dict) else {}, accent, progress)
    except Exception as e:
        print(f"⚠️ [longform_cards] {card_type} card render failed ({e}); drawing bare card.")
    return img


class CardAnimator:
    """Cached frame/mask providers for a card shown for `duration` seconds."""

    ANIM_SECONDS = 1.3
    FADE_IN, FADE_OUT = 0.35, 0.25

    def __init__(self, card_type, data, accent, duration):
        self.card_type, self.data, self.accent, self.duration = card_type, data, tuple(accent), duration
        self._key, self._arr, self._final = None, None, None

    def _rgba(self, t):
        key = round(min(1.0, t / self.ANIM_SECONDS), 2) if t < self.ANIM_SECONDS else 1.0
        if key == 1.0 and self._final is not None:
            arr = self._final
        elif key == self._key:
            arr = self._arr
        else:
            arr = np.array(render_card(self.card_type, self.data, self.accent, key))
            if key == 1.0:
                self._final = arr
            self._key, self._arr = key, arr
        return arr

    def _alpha_mult(self, t):
        m = 1.0
        if t < self.FADE_IN:
            m = t / self.FADE_IN
        if self.duration - t < self.FADE_OUT:
            m = min(m, max(0.0, (self.duration - t) / self.FADE_OUT))
        return m

    def frame(self, t):
        return self._rgba(t)[:, :, :3]

    def mask(self, t):
        return (self._rgba(t)[:, :, 3].astype(np.float32) / 255.0) * self._alpha_mult(t)
