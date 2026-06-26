"""
entity_fetcher.py — Entity Logo/Photo Fetcher for Tamil Simple Tips by VJ

Fetches company logos and person photos from Wikipedia/Clearbit for visual overlays
in video generation. Adapted from reference project for Tamil content.
"""

import os
import requests
from io import BytesIO
from PIL import Image
from config import OUTPUT_DIR
from nano_scene_gen import _generate_imagen_image


def _save_image_from_url(url: str, output_path: str, is_logo: bool = False) -> str | None:
    """Download and save an image, ensuring proper formatting."""
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        if r.status_code == 200:
            img = Image.open(BytesIO(r.content)).convert("RGBA")

            if is_logo:
                img.save(output_path, "PNG")
            else:
                img = img.convert("RGB")
                img.save(output_path, "JPEG", quality=90)
            return output_path
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
    return None


def fetch_person_photo(person: dict) -> str | None:
    """
    Fetch a person's photo from Wikipedia.
    Falls back to AI generation if not found.
    """
    name = person.get("name", "")
    wiki_slug = person.get("wikipedia_slug") or name.replace(" ", "_")

    print(f"Fetching photo for person: {name}...")
    output_path = os.path.join(OUTPUT_DIR, f"person_{name.replace(' ', '_')}.jpg")
    if os.path.exists(output_path):
        return output_path

    # PRIORITY 1: Wikipedia API
    try:
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "thumbnail" in data and "source" in data["thumbnail"]:
                img_url = data["thumbnail"]["source"]
                # Try to get larger image
                img_url = img_url.replace(str(data["thumbnail"]["width"]), "400")
                path = _save_image_from_url(img_url, output_path)
                if path:
                    print(f"  -> Found Wikipedia photo for {name}")
                    return path
    except Exception as e:
        print(f"  Wikipedia API fetch failed: {e}")

    # PRIORITY 2: Generative AI fallback
    print(f"  -> Falling back to Generative AI for {name}...")
    prompt = f"Professional portrait photo of {name}, high quality, clean background, 9:16 aspect ratio"
    path = _generate_imagen_image(prompt, output_path)
    if path:
        return path

    print(f"  -> Could not find photo for {name}")
    return None


def fetch_company_logo(company: dict) -> str | None:
    """
    Fetch a company logo from Clearbit or Wikipedia.
    Falls back to AI generation if not found.
    """
    name = company.get("name", "")
    domain = company.get("domain") or company.get("company_domain")
    if not domain:
        domain = f"{name.lower().replace(' ', '')}.com"

    print(f"Fetching logo for company: {name} (domain: {domain})...")
    output_path = os.path.join(OUTPUT_DIR, f"company_{name.replace(' ', '_')}.png")
    if os.path.exists(output_path):
        return output_path

    # PRIORITY 1: Clearbit Logo API (free, no auth)
    try:
        url = f"https://logo.clearbit.com/{domain}?size=600"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            path = _save_image_from_url(url, output_path, is_logo=True)
            if path:
                print(f"  -> Found Clearbit logo for {name}")
                return path
    except Exception as e:
        print(f"  Clearbit fetch failed: {e}")

    # PRIORITY 2: Wikipedia API
    try:
        wiki_slug = name.replace(" ", "_")
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_slug}"
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if "thumbnail" in data and "source" in data["thumbnail"]:
                img_url = data["thumbnail"]["source"]
                img_url = img_url.replace(str(data["thumbnail"]["width"]), "400")
                path = _save_image_from_url(img_url, output_path, is_logo=True)
                if path:
                    print(f"  -> Found Wikipedia logo for {name}")
                    return path
    except Exception as e:
        print(f"  Wikipedia fetch failed: {e}")

    # PRIORITY 3: Generative AI fallback for company office/HQ image
    print(f"  -> Falling back to Generative AI for {name}...")
    imagen_out = os.path.join(OUTPUT_DIR, f"company_{name.replace(' ', '_')}_office.jpg")
    search_query = company.get("hq_pexels_search") or f"{name} office headquarters"
    prompt = f"Professional corporate office headquarters building for {search_query}, modern architecture, clean facade, daylight, 9:16 aspect ratio"
    path = _generate_imagen_image(prompt, imagen_out)
    if path:
        return path

    print(f"  -> Could not find logo/HQ for {name}")
    return None


def fetch_all_entities(script_data: dict) -> dict:
    """
    Download all person photos and company logos referenced in script_data.
    Updates script_data in-place with local paths.
    """
    # Gather all potential entities from various fields
    companies_mentioned = script_data.get("companies_mentioned", [])
    tools_mentioned = script_data.get("tools_mentioned", [])
    key_entities = script_data.get("key_entities", [])
    people = script_data.get("people", [])
    companies = script_data.get("companies", [])

    # Merge companies_mentioned and tools_mentioned into key_entities
    existing_names = {ent.get("name", "").lower() for ent in key_entities if isinstance(ent, dict)}
    for p in people:
        if isinstance(p, dict):
            existing_names.add(p.get("name", "").lower())
    for c in companies:
        if isinstance(c, dict):
            existing_names.add(c.get("name", "").lower())

    for c in companies_mentioned:
        if c and isinstance(c, str) and c.lower() not in existing_names:
            key_entities.append({"name": c, "type": "COMPANY"})
            existing_names.add(c.lower())

    for t in tools_mentioned:
        if t and isinstance(t, str) and t.lower() not in existing_names:
            key_entities.append({"name": t, "type": "TOOL"})
            existing_names.add(t.lower())

    # Fetch for people
    for person in script_data.get("people", []):
        if isinstance(person, dict):
            path = fetch_person_photo(person)
            if path:
                person["local_image_path"] = path

    # Fetch for companies
    for company in script_data.get("companies", []):
        if isinstance(company, dict):
            path = fetch_company_logo(company)
            if path:
                if path.endswith(".png"):
                    company["local_logo_path"] = path
                else:
                    company["local_hq_path"] = path

    # Fetch for key_entities
    for entity in script_data.get("key_entities", []):
        if isinstance(entity, dict):
            path = fetch_company_logo(entity)
            if path:
                if path.endswith(".png"):
                    entity["local_logo_path"] = path
                else:
                    entity["local_hq_path"] = path

    return script_data


def get_retention_layers_config() -> dict:
    """
    Coordination point for kinetic layers and pacing.
    Called by main.py to ensure engagement triggers are active.
    """
    from config import (
        ENABLE_KINETIC_CAPTIONS, ENABLE_AUDIO_DUCKING, ENABLE_PERIODIC_CUTS
    )

    return {
        "kinetic_captions": ENABLE_KINETIC_CAPTIONS,
        "audio_ducking": ENABLE_AUDIO_DUCKING,
        "camera_cuts": ENABLE_PERIODIC_CUTS,
        "pacing_mode": "kinetic_high_energy"
    }