# -*- coding: utf-8 -*-
"""
longform_visuals.py — 16:9 visual resolver + thumbnails for the LONGFORM pipeline.

The shorts resolver (pexels_fetcher.py) is hard-wired to portrait footage and 9:16 prompts, so longform has its own
landscape-first resolver. It reuses the shared building blocks (Pexels dedupe, Imagen / FLUX / Pollinations helpers,
Playwright screenshots) without modifying them.

Per-scene plan → provider chain:
  stock        : Pexels landscape video → AI image → Pexels landscape photo → reuse
  ai_image     : Imagen → Cloudflare FLUX → Pollinations → Pexels video → Pexels photo → reuse
  infographic  : (card is drawn over a darkened background) AI image / stock background chain
  screenshot   : Playwright capture of the cited source → AI image chain
"""

import os
import random
import time

import requests
from PIL import Image, ImageDraw

from config import (
    OUTPUT_DIR, PEXELS_API_KEY, ENABLE_STOCK_FOOTAGE, GEMINI_API_KEY,
    CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID,
)
from longform_niches import LONGFORM_NICHES

TODAY = time.strftime("%Y%m%d_%H%M%S")
_AI_SUFFIX = "16:9 widescreen composition, no text, no captions, no watermarks, no logos, no distorted anatomy."


def _has_pexels():
    return bool(ENABLE_STOCK_FOOTAGE and PEXELS_API_KEY and PEXELS_API_KEY.strip() and "XXX" not in PEXELS_API_KEY)


def _has_gemini():
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and "XXX" not in GEMINI_API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# Providers
# ─────────────────────────────────────────────────────────────────────────────

def fetch_pexels_landscape(query, media_type="video"):
    """Downloads a landscape Pexels video/photo for `query`. Returns a local path or None."""
    if not _has_pexels() or not query:
        return None
    import pexels_fetcher as pf   # reuse its per-run used-asset dedupe

    headers = {"Authorization": PEXELS_API_KEY}
    try:
        if media_type == "video":
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(query)}&per_page=15&orientation=landscape"
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code != 200:
                return None
            videos = r.json().get("videos", [])
            if not videos:
                return None
            video = pf._pick_unused(videos)
            files = [f for f in video.get("video_files", []) if f.get("file_type") == "video/mp4"]
            landscape = [f for f in files if f.get("width", 0) > f.get("height", 0)] or files
            if not landscape:
                return None
            # Prefer crisp HD (1280-1920 wide); otherwise whatever is closest to 1920
            hd = [f for f in landscape if 1280 <= f.get("width", 0) <= 1920]
            chosen = max(hd, key=lambda f: f.get("width", 0)) if hd else min(landscape, key=lambda f: abs(f.get("width", 0) - 1920))
            out = os.path.join(OUTPUT_DIR, f"lf_pexels_video_{TODAY}_{random.randint(1000, 9999)}.mp4")
            print(f"   📥 [pexels] Landscape stock video ({chosen.get('width')}x{chosen.get('height')}) for '{query}'")
            resp = requests.get(chosen["link"], stream=True, timeout=60)
            if resp.status_code != 200:
                return None
            with open(out, "wb") as fh:
                for part in resp.iter_content(chunk_size=1024 * 1024):
                    if part:
                        fh.write(part)
            return out
        url = f"https://api.pexels.com/v1/search?query={requests.utils.quote(query)}&per_page=15&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=12)
        if r.status_code != 200:
            return None
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = pf._pick_unused(photos)
        src = photo.get("src", {}).get("large2x") or photo.get("src", {}).get("large")
        if not src:
            return None
        out = os.path.join(OUTPUT_DIR, f"lf_pexels_photo_{TODAY}_{random.randint(1000, 9999)}.jpg")
        resp = requests.get(src, timeout=30)
        if resp.status_code != 200:
            return None
        with open(out, "wb") as fh:
            fh.write(resp.content)
        return out
    except Exception as e:
        print(f"   ⚠️ [pexels] landscape {media_type} fetch failed for '{query}': {e}")
        return None


def generate_ai_image(prompt, niche, cid):
    """Imagen → Cloudflare FLUX → Pollinations, all 16:9. Returns a local path or None."""
    import nano_scene_gen as ns
    full_prompt = f"{prompt}. {niche['ai_style']}. {_AI_SUFFIX}"
    out = os.path.join(OUTPUT_DIR, f"lf_scene_{cid}_{TODAY}.jpg")
    providers = []
    if _has_gemini():
        providers.append(("Imagen AI", lambda: ns._generate_imagen_image(full_prompt, out, aspect_ratio="16:9")))
    if CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID:
        providers.append(("Cloudflare FLUX", lambda: ns._try_cloudflare_flux(full_prompt, cid, "16:9")))
    providers.append(("Pollinations AI", lambda: ns._generate_pollinations_image(full_prompt, out, aspect_ratio="16:9")))
    for name, fn in providers:
        try:
            path = fn()
            if path and os.path.exists(path) and os.path.getsize(path) > 2000:
                print(f"   ✅ AI image via {name}")
                return path
        except Exception as e:
            print(f"   ❌ {name} failed: {e}")
    return None


def capture_source_screenshot(url, cid):
    try:
        from screenshot_gen import capture_article_screenshot
        path = capture_article_screenshot(url, f"longform_{cid}_{TODAY}.png", desktop=True)
        return path if path and os.path.exists(path) else None
    except Exception as e:
        print(f"   ❌ Screenshot capture failed: {e}")
        return None


def make_gradient_background(accent, cid):
    """Last-resort guaranteed visual: a dark vignette gradient tinted with the niche accent."""
    w, h = 1920, 1080
    img = Image.new("RGB", (w, h), (10, 10, 18))
    px = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        px.line([(0, y), (w, y)], fill=(int(12 + accent[0] * 0.18 * (1 - t)),
                                         int(12 + accent[1] * 0.18 * (1 - t)),
                                         int(20 + accent[2] * 0.22 * (1 - t))))
    out = os.path.join(OUTPUT_DIR, f"lf_gradient_{cid}_{TODAY}.png")
    img.save(out)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Resolver
# ─────────────────────────────────────────────────────────────────────────────

def resolve_longform_visuals(chunks, script_data):
    """Fills visual_path / visual_type ('video'|'photo'|'screenshot') / source on every chunk."""
    import pexels_fetcher as pf
    pf._USED_PEXELS_IDS.clear()
    niche = LONGFORM_NICHES[script_data.get("niche")] if script_data.get("niche") in LONGFORM_NICHES else \
        next(iter(LONGFORM_NICHES.values()))
    accent = tuple(script_data.get("accent_color") or niche["accent"])

    print(f"\n🎬 LONGFORM VISUAL RESOLVER: {len(chunks)} scenes (16:9)")
    print(f"  🔑 Providers: Pexels={_has_pexels()} Gemini/Imagen={_has_gemini()} "
          f"Cloudflare={bool(CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID)}")

    last_path, last_type = None, "photo"
    stats = {}
    for i, chunk in enumerate(chunks):
        cid = chunk.get("chunk_id", i + 1)
        plan = chunk.get("plan", "stock")
        query = chunk.get("stock_search_query", "")
        prompt = chunk.get("nano_visual_prompt") or query
        print(f"  [{i + 1}/{len(chunks)}] ({plan}) {chunk.get('text', '')[:42]}… | query='{query}'")

        def stock_video():
            return ("video", fetch_pexels_landscape(query, "video"))

        def stock_photo():
            return ("photo", fetch_pexels_landscape(query, "photo"))

        def ai_image():
            return ("photo", generate_ai_image(prompt, niche, cid))

        def screenshot():
            return ("screenshot", capture_source_screenshot(chunk.get("screenshot_url"), cid))

        if plan == "stock":
            chain = [("Pexels Video", stock_video), ("AI Image", ai_image), ("Pexels Photo", stock_photo)]
        elif plan == "screenshot":
            chain = [("Screenshot", screenshot), ("AI Image", ai_image), ("Pexels Video", stock_video)]
        else:   # ai_image and infographic backgrounds
            chain = [("AI Image", ai_image), ("Pexels Video", stock_video), ("Pexels Photo", stock_photo)]

        visual_path = visual_type = source = None
        for name, fn in chain:
            try:
                vtype, path = fn()
            except Exception as e:
                print(f"     ❌ {name} failed: {e}")
                continue
            if path:
                visual_path, visual_type, source = path, vtype, name
                break
        if not visual_path and last_path:
            visual_path, visual_type, source = last_path, last_type, "Reused Visual"
        if not visual_path:
            visual_path, visual_type, source = make_gradient_background(accent, cid), "photo", "Gradient Fallback"
            print("     🚨 No provider returned a visual — using gradient fallback.")

        chunk["visual_path"], chunk["visual_type"], chunk["source"] = visual_path, visual_type, source
        stats[source] = stats.get(source, 0) + 1
        if source != "Gradient Fallback":
            last_path, last_type = visual_path, visual_type
    print(f"✅ [LONGFORM] Visual sources: {stats}")
    return chunks


# ─────────────────────────────────────────────────────────────────────────────
# Thumbnails (documentary style — the shorts generator uses Pixar-cartoon prompts for 2 of 3 variants)
# ─────────────────────────────────────────────────────────────────────────────

def generate_longform_thumbnails(script_data):
    """Two 1280x720 thumbnail variants [A, B] with documentary backgrounds. Returns a list of paths."""
    import thumbnail_gen as tg

    niche = LONGFORM_NICHES.get(script_data.get("niche"), next(iter(LONGFORM_NICHES.values())))
    accent = tuple(niche["accent"])
    secondary = (15, 15, 22)
    headline = script_data.get("original_news_headline") or script_data.get("title", "")
    text = script_data.get("thumbnail_text") or niche["short_label"].upper()
    stamp = time.strftime("%Y%m%d_%H%M%S")

    variants = [
        (f"{headline}, {niche['ai_style']}", tg._LAYOUT_REGISTRY),
        (f"dramatic close-up of the key subject of: {headline}, {niche['ai_style']}",
         [tg._LAYOUT_REGISTRY[0], tg._LAYOUT_REGISTRY[2]]),   # Mystery Box / Spotlight Focus
    ]
    paths = []
    for idx, (bg_prompt, registry) in enumerate(variants):
        try:
            bg = tg._generate_imagen_background(bg_prompt)
            canvas = bg.convert("RGB").resize((tg.THUMB_W, tg.THUMB_H), Image.LANCZOS)
            draw = ImageDraw.Draw(canvas)
            _, layout_fn = random.choice(registry)
            canvas = layout_fn(canvas, draw, text, headline, accent, secondary, niche["emoji"])
            ImageDraw.Draw(canvas).rectangle([0, tg.THUMB_H - 6, tg.THUMB_W, tg.THUMB_H], fill=accent)
            out = os.path.join(OUTPUT_DIR, f"longform_thumbnail_{stamp}_{'AB'[idx]}.jpg")
            canvas.convert("RGB").save(out, "JPEG", quality=95)
            paths.append(out)
            print(f"✅ [LONGFORM] Thumbnail variant {'AB'[idx]} saved: {out}")
        except Exception as e:
            print(f"⚠️ [LONGFORM] Thumbnail variant {'AB'[idx]} failed: {e}")
    return paths
