# -*- coding: utf-8 -*-
"""
longform_niches.py — Niche catalogue + weekday rotation for the 2-3 minute LONGFORM pipeline.

Seven niches (one per weekday) built from the viral faceless-Tamil channel types researched online
(mystery/true-crime, Tamil heritage, space & science, psychology, "what if" scenarios) plus the existing
Simple Tips by VJ categories (smart-living tips, nature/food/body science).

Each niche carries everything the script writer, storyboard agent, visual resolver and renderer need:
topic discovery angle, safety rules, hook style, preferred visual mix, AI-image art direction and palette.
"""

import datetime

import pytz

from config import TIMEZONE

# Hard bounds for the finished narration (user spec: 2 to 3 minutes)
LONGFORM_DURATION_BOUNDS = (120, 180)
# Duration the script writer aims for (middle of the window gives room for pacing drift)
LONGFORM_TARGET_SECONDS = 150

LONGFORM_NICHES = {
    "mystery": {
        "label": "🕵️ Mysteries, True Crime & Unexplained",
        "short_label": "Mystery",
        "emoji": "🕵️",
        "accent": (225, 60, 90),
        "angle": (
            "well-documented real mysteries, famous unsolved cases, disappearances, historical enigmas and unexplained "
            "phenomena — world-famous or India/Tamil Nadu cases that are extensively covered by reputable sources"
        ),
        "safety": (
            "NEVER accuse any living private individual. Stick to documented facts from major news / court / encyclopedia "
            "sources. No graphic violence, no gore, be respectful to victims. Clearly say 'theory' when something is a theory."
        ),
        "hook_style": "Open mid-mystery with the single most chilling documented detail, then promise the full story.",
        "visual_mix": {"stock": 35, "ai_image": 45, "infographic": 10, "screenshot": 10},
        "ai_style": (
            "dark cinematic documentary still, moody low-key lighting, volumetric fog, 35mm film grain, "
            "desaturated teal-and-amber grade, photorealistic"
        ),
        "stock_hint": "night street, old building, fog, newspaper, flashlight, empty corridor, ocean at night",
        "hashtags": ["#Mystery", "#TamilMystery", "#UnsolvedMysteries", "#TamilFacts"],
        "tone": "suspenseful, hushed storyteller that builds tension and pays it off",
    },
    "tamil_history": {
        "label": "🏛️ Tamil History & Heritage",
        "short_label": "Tamil History",
        "emoji": "🏛️",
        "accent": (255, 193, 69),
        "angle": (
            "verified history and archaeology of Tamil Nadu and the Tamil people — Chola, Pandya, Pallava, Sangam era, "
            "Keezhadi, temple engineering, ports, trade, inscriptions, forgotten heroes and inventions"
        ),
        "safety": (
            "Cite only claims backed by ASI / university / museum / Britannica / major-news sources. Separate proven fact "
            "from legend. No communal or caste provocation, no political slants."
        ),
        "hook_style": "Open with a jaw-dropping measurable fact (a year, a size, a distance) that makes viewers proud, then ask how.",
        "visual_mix": {"stock": 30, "ai_image": 50, "infographic": 10, "screenshot": 10},
        "ai_style": (
            "cinematic historical documentary frame, golden-hour light, dust motes, ancient South Indian stone temple "
            "architecture, authentic textures, epic wide composition, photorealistic"
        ),
        "stock_hint": "temple tower, stone carving, tamil nadu temple, ancient ruins, river, palm trees, sculpture",
        "hashtags": ["#TamilHistory", "#TamilHeritage", "#Chola", "#TamilFacts"],
        "tone": "proud, authoritative documentary narrator who still talks like a friend",
    },
    "space_science": {
        "label": "🚀 Space, Science & Universe Explained",
        "short_label": "Space & Science",
        "emoji": "🚀",
        "accent": (96, 165, 250),
        "angle": (
            "space, physics, earth science and big-science stories explained simply — ISRO missions, black holes, planets, "
            "stars, deep time, extreme experiments and recent discoveries"
        ),
        "safety": "Use NASA / ISRO / ESA / Nature / university sources. Avoid pseudo-science and unproven claims.",
        "hook_style": "Open with a mind-bending scale or number, then explain it with an everyday Tamil Nadu comparison.",
        "visual_mix": {"stock": 40, "ai_image": 35, "infographic": 20, "screenshot": 5},
        "ai_style": (
            "ultra-detailed space documentary render, deep blue and violet nebula lighting, lens flares, "
            "IMAX cinematic composition, photorealistic"
        ),
        "stock_hint": "galaxy, stars night sky, rocket launch, earth from space, telescope, planet, laboratory",
        "hashtags": ["#Space", "#ISRO", "#ScienceTamil", "#TamilFacts"],
        "tone": "curious, energetic, wonder-filled science explainer",
    },
    "psychology": {
        "label": "🧠 Psychology & Mind Hacks",
        "short_label": "Psychology",
        "emoji": "🧠",
        "accent": (167, 139, 250),
        "angle": (
            "evidence-based psychology, behaviour, habits, memory, sleep, focus and decision-making that Tamil viewers "
            "experience daily — explained with named studies and practical takeaways"
        ),
        "safety": (
            "Use peer-reviewed studies / APA / NIH / major universities. No medical diagnosis or treatment advice, no "
            "'cure' claims; add a gentle 'talk to a professional' note for mental-health topics."
        ),
        "hook_style": "Open by calling out a feeling or habit every viewer has experienced this week, then reveal the hidden reason.",
        "visual_mix": {"stock": 45, "ai_image": 30, "infographic": 20, "screenshot": 5},
        "ai_style": (
            "clean modern editorial illustration-photography blend, soft purple and teal rim light, shallow depth of field, "
            "minimalist composition, photorealistic"
        ),
        "stock_hint": "person thinking, brain scan, crowd walking, sleeping person, office desk, student studying, mobile phone",
        "hashtags": ["#Psychology", "#MindHacks", "#TamilPsychology", "#TamilFacts"],
        "tone": "calm, smart, conversational big-brother who knows the science",
    },
    "what_if": {
        "label": "🤔 What If? Hypothetical Scenarios",
        "short_label": "What If",
        "emoji": "🤔",
        "accent": (255, 138, 76),
        "angle": (
            "science-grounded 'What if…' scenarios — what if the Moon vanished, Earth stopped spinning, humans stopped "
            "sleeping — built step by step from real physics/biology numbers"
        ),
        "safety": (
            "Every step of the scenario must follow from verifiable science; label speculation as 'scientists estimate'. "
            "No fear-mongering, no doomsday predictions presented as fact."
        ),
        "hook_style": "Open with the scenario as a question and the first shocking consequence within 8 seconds.",
        "visual_mix": {"stock": 30, "ai_image": 50, "infographic": 15, "screenshot": 5},
        "ai_style": (
            "surreal cinematic sci-fi concept art made photoreal, dramatic sky, epic scale, high contrast, "
            "orange and cyan grade, photorealistic"
        ),
        "stock_hint": "earth from space, city timelapse, empty street, ocean waves, storm clouds, sunrise, moon",
        "hashtags": ["#WhatIf", "#TamilScience", "#Hypothetical", "#TamilFacts"],
        "tone": "playful, dramatic, 'hold on tight' storyteller that escalates every beat",
    },
    "smart_living": {
        "label": "📱 Digital Safety, Money & Smart Living",
        "short_label": "Smart Living",
        "emoji": "💰",
        "accent": (52, 211, 153),
        "angle": (
            "deep-dive explainers on UPI/online scams, phone privacy, money-saving, bank and credit-card rules, "
            "electricity and consumer rights in India — practical, step-by-step, verified"
        ),
        "safety": (
            "Use RBI / NPCI / TRAI / government / bank / major-news sources. No investment advice or stock tips, no "
            "named-person accusations; give safe, legal actions only."
        ),
        "hook_style": "Open with the exact rupee loss or danger a viewer faces, then promise the 3-step protection.",
        "visual_mix": {"stock": 40, "ai_image": 20, "infographic": 25, "screenshot": 15},
        "ai_style": (
            "modern clean tech photography, soft daylight, realistic Indian urban setting, crisp textures, "
            "shallow depth of field, photorealistic"
        ),
        "stock_hint": "smartphone payment, ATM, wallet money, laptop typing, shopping, bank, mobile screen, credit card",
        "hashtags": ["#DigitalSafety", "#MoneyTips", "#TamilTips", "#UPIScam"],
        "tone": "friendly, protective elder-brother giving practical advice",
    },
    "nature_food_body": {
        "label": "🌿 Nature, Food & Human Body Science",
        "short_label": "Nature & Body",
        "emoji": "🌿",
        "accent": (163, 230, 53),
        "angle": (
            "animal superpowers, nature records, the science of Indian/Tamil foods and spices, and how the human body "
            "works — fascinating, verified, relatable"
        ),
        "safety": (
            "Use Nature / WHO / ICMR / NIH / Britannica / university sources. No diet fads, no medical treatment claims; "
            "add a 'consult a doctor' note for health topics."
        ),
        "hook_style": "Open with a surprising number about an animal, food or body part everyone knows.",
        "visual_mix": {"stock": 55, "ai_image": 25, "infographic": 15, "screenshot": 5},
        "ai_style": (
            "National Geographic style macro and wildlife photography, natural golden light, rich organic colours, "
            "razor-sharp detail, photorealistic"
        ),
        "stock_hint": "wildlife, elephant, bird flying, spices, cooking, kitchen, heart, human body, forest, ocean",
        "hashtags": ["#Nature", "#FoodScience", "#HumanBody", "#TamilFacts"],
        "tone": "warm, amazed, everyday-friendly explainer",
    },
}

# Monday..Sunday rotation (1 longform per day). Order chosen so adjacent days never share a niche.
WEEKDAY_NICHE = {
    "Mon": "mystery",
    "Tue": "tamil_history",
    "Wed": "space_science",
    "Thu": "psychology",
    "Fri": "what_if",
    "Sat": "smart_living",
    "Sun": "nature_food_body",
}


def get_niche_for_today(forced=None):
    """Returns (day_name, niche_id, niche_dict). `forced` may be a niche id or None."""
    ist_now = datetime.datetime.now(pytz.timezone(TIMEZONE))
    day_name = ist_now.strftime("%a")
    niche_id = forced if forced in LONGFORM_NICHES else WEEKDAY_NICHE.get(day_name, "space_science")
    return day_name, niche_id, LONGFORM_NICHES[niche_id]
