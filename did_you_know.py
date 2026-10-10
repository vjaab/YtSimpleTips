# -*- coding: utf-8 -*-
"""
did_you_know.py — "தெரியுமா? / Did You Know" Shorts format for Simple Tips by VJ.

One deep, verified, number-driven fact per Short (~30-45s), built for Tamil audiences.

Flow:
  1. fetch_dyk_facts()      → Gemini Search Grounding finds candidate facts with a hard number,
                              a Tamil-life connection and filmable stock-footage subjects.
  2. fact_check_claim()     → Independent grounded verification. Only TRUE claims pass;
                              MOSTLY_TRUE claims are replaced with the corrected wording.
  3. generate_dyk_script()  → Number-first Tamil hook → open loop → explanation with a Tamil
                              analogy → bonus twist → comment question. Storyboard is designed
                              for real stock footage (Pexels) with fast 1.5-2.5s cuts.

The returned dict mirrors gemini_script.pick_and_generate_script() so main.py can use it unchanged.
"""

import json
import random
import re

from config import (
    get_gemini_client, is_gemini_disabled, rotate_gemini_api_key,
    GEMINI_API_KEYS, GEMINI_FLASH_MODEL,
)
from topic_tracker import load_tracker, check_story_uniqueness

FORMAT_ID = "did_you_know"

# Script length tuned for 30-45s of spoken Tamil (main.py enforces the audio bounds below)
DYK_WORD_RANGE = (85, 110)
DYK_DURATION_BOUNDS = (25, 55)

TAMIL_INDIA_CATEGORY = "🇮🇳 Tamil Nadu & India Did You Know"

# Money-saving tips are not "facts" — swap that slot for a Tamil/India curiosity slot.
_CATEGORY_REMAP = {
    "💰 Money-Saving & Smart Living Tricks": TAMIL_INDIA_CATEGORY,
}

_CATEGORY_ANGLES = {
    "🧠 Mind-Blowing Science Curiosities": "physics, chemistry, space and earth science facts that sound fake but are proven",
    "🧬 Human Body & Dark Psychology": "human body numbers, brain quirks and everyday psychology everyone has experienced",
    "🍳 Food, Health & Kitchen Science": "surprising science behind Indian/Tamil foods, spices, cooking and kitchen items",
    "🌍 Mysterious History & Culture Secrets": "verified history and archaeology, preferring Tamil Nadu (Keezhadi, Chola, Sangam era) and India",
    "🐾 Nature & Animal Oddities": "animal superpowers and nature records, preferring animals Indians know (crow, elephant, cobra, peacock, mosquito)",
    TAMIL_INDIA_CATEGORY: "verified records and surprising facts about Tamil Nadu, Tamil language, Indian railways, temples, rivers, cities and inventions",
}

_DYK_HASHTAGS = ["#தெரியுமா", "#DidYouKnowTamil", "#TamilFacts", "#Shorts"]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_dyk_category(category):
    """Maps the slot category to a category that suits fact-style Shorts."""
    return _CATEGORY_REMAP.get(category, category)


def _extract_json(raw, want="object"):
    """Pulls the first JSON object/array out of a model response."""
    if not raw:
        return None
    raw = raw.strip()
    if "```" in raw:
        raw = re.sub(r"```(?:json)?", "", raw).strip()
    open_c, close_c = ("[", "]") if want == "array" else ("{", "}")
    start, end = raw.find(open_c), raw.rfind(close_c)
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(raw[start:end + 1])
    except Exception:
        return None


def _grounded_call(prompt, temperature=0.4, want="object", label="grounded"):
    """
    Gemini call with Google Search grounding + API key rotation on 429.
    Returns parsed JSON (dict/list) or None.
    """
    if is_gemini_disabled():
        print(f"⚠️ [DYK:{label}] Gemini disabled — grounded call skipped.")
        return None
    client = get_gemini_client()
    if not client:
        print(f"⚠️ [DYK:{label}] No Gemini client — grounded call skipped.")
        return None

    from google.genai import types
    max_attempts = max(3, len(GEMINI_API_KEYS) + 1)
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_FLASH_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}],
                    temperature=temperature,
                ),
            )
            parsed = _extract_json(response.text or "", want=want)
            if parsed is not None:
                return parsed
            print(f"⚠️ [DYK:{label}] Unparseable response (attempt {attempt}/{max_attempts}).")
        except Exception as e:
            err = str(e).lower()
            print(f"⚠️ [DYK:{label}] Attempt {attempt}/{max_attempts} failed: {e}")
            if ("429" in err or "resource exhausted" in err) and len(GEMINI_API_KEYS) > 1:
                rotate_gemini_api_key()
                client = get_gemini_client()
                continue
            if "prepayment credits" in err:
                from config import disable_gemini
                disable_gemini()
                return None
    return None


def _avoid_list():
    tracker = load_tracker()
    items = set((tracker.get("used_titles", []) or []) + (tracker.get("last_7_days_stories", []) or []))
    for h in tracker.get("history", []):
        if isinstance(h, dict):
            for k in ("title", "news_headline"):
                if h.get(k):
                    items.add(h[k])
    return [i for i in items if i]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Fact discovery
# ─────────────────────────────────────────────────────────────────────────────

def fetch_dyk_facts(category, failed_topics=None):
    """
    Finds 6 candidate "Did You Know" facts via Search Grounding.
    Each fact carries a hard number, a Tamil-life hook and filmable stock subjects.
    """
    angle = _CATEGORY_ANGLES.get(category, "verified, surprising general-knowledge facts")
    avoid = _avoid_list() + list(failed_topics or [])
    avoid_str = "\n".join(f"- {t}" for t in avoid[:50])

    prompt = f"""
Search the web and find 6 VIRAL "Did You Know" facts for a Tamil YouTube Shorts audience
(students, parents, office-goers and elders in Tamil Nadu).

CATEGORY: {category}
FOCUS: {angle}

EVERY fact MUST:
1. Be 100% verifiable from a reputable source (Wikipedia, Britannica, NASA, Nature, WHO, government, major news).
2. Contain ONE hard, concrete number or comparison that shocks (e.g. "3 hearts", "1,600 years without rust", "40 minutes").
3. Be counter-intuitive — a Tamil viewer should react "அட, உண்மையாவா?!". NO common school-textbook facts.
4. Be explainable in 35 seconds with ONE clear reason why it happens.
5. Be visually filmable with REAL stock footage (animals, places, objects, nature, food, people doing things).
   Abstract topics with nothing to film are NOT allowed.
6. NOT be a myth. Reject popular myths (e.g. "we use 10% of our brain", "Great Wall visible from space").

DO NOT REPEAT ANY OF THESE ALREADY-COVERED TOPICS:
{avoid_str}

Return ONLY a JSON array (no markdown) of 6 objects:
[
  {{
    "title": "Short English title of the fact",
    "claim": "The fact as ONE precise English sentence including the number",
    "number_hook": "The shocking number/comparison alone (e.g. '3 HEARTS', '1600 YEARS')",
    "why_it_happens": "2-3 sentence plain-English explanation of the reason",
    "bonus_twist": "One extra verified micro-fact about the same subject that adds a final 'wow'",
    "tamil_connection": "A relatable comparison from everyday Tamil Nadu life (kitchen, temple, bus, school, village, cinema)",
    "visual_subjects": ["4-6 concrete 1-3 word English Pexels stock-video search terms, e.g. 'octopus swimming', 'coral reef', 'blue blood'"],
    "source_url": "Direct URL of the reputable source",
    "source_name": "Source name",
    "keywords": ["3-5 English SEO keywords"],
    "wow_score": 1-10
  }}
]
"""
    facts = _grounded_call(prompt, temperature=0.8, want="array", label="discover") or []
    if not isinstance(facts, list):
        facts = []

    from fetch_topics import validate_url
    clean = []
    for f in facts:
        if not isinstance(f, dict) or not f.get("title") or not f.get("claim"):
            continue
        is_unique, reason = check_story_uniqueness(new_title=f["title"], new_url=f.get("source_url", ""))
        if not is_unique:
            print(f"⏭️ [DYK] Duplicate fact skipped: {f['title']} ({reason})")
            continue
        if failed_topics and any(ft and ft.lower() in f["title"].lower() for ft in failed_topics):
            continue
        url = f.get("source_url", "")
        if not url or not validate_url(url):
            print(f"⏭️ [DYK] Unreachable source skipped: {f['title']} → {url}")
            continue
        f["category"] = category
        clean.append(f)

    clean.sort(key=lambda x: float(x.get("wow_score", 0) or 0), reverse=True)
    print(f"✅ [DYK] {len(clean)} unique, source-backed candidate facts for '{category}'.")
    return clean


def _from_generic_article(article, category):
    """Adapts a fetch_topics article into the DYK fact shape (used as a fallback source)."""
    desc = article.get("description", "")
    return {
        "title": article.get("title", ""),
        "claim": desc.split(". ")[0] if desc else article.get("title", ""),
        "number_hook": "",
        "why_it_happens": desc,
        "bonus_twist": "",
        "tamil_connection": "",
        "visual_subjects": [w for w in article.get("keywords", []) if isinstance(w, str)][:4],
        "source_url": article.get("source_url", ""),
        "source_name": article.get("source_name", ""),
        "keywords": article.get("keywords", []),
        "category": category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fact-check gate
# ─────────────────────────────────────────────────────────────────────────────

def fact_check_claim(fact):
    """
    Independently verifies the claim with Search Grounding.
    Returns (passed: bool, fact: dict (possibly corrected), report: dict).
    """
    prompt = f"""
You are a strict fact-checker for an educational YouTube channel. Search the web and verify this claim.

CLAIM: {fact.get('claim')}
EXPLANATION GIVEN: {fact.get('why_it_happens')}
BONUS DETAIL: {fact.get('bonus_twist')}
CITED SOURCE: {fact.get('source_url')}

Rules:
- Check the NUMBER precisely. A wrong or exaggerated number = MISLEADING.
- Known myths or unproven folklore = FALSE.
- Popular oversimplifications are MISLEADING (e.g. "mantis shrimp see 12x more colours" — studies show
  their colour discrimination is actually worse than humans'). Judge what a viewer will BELIEVE after hearing it.
- If the core claim is right but wording needs a fix, use MOSTLY_TRUE and provide the corrected wording.
- If the bonus detail is wrong, set bonus_ok=false.

Return ONLY JSON (no markdown):
{{
  "verdict": "TRUE|MOSTLY_TRUE|MISLEADING|FALSE|UNVERIFIABLE",
  "confidence": 0.0-1.0,
  "corrected_claim": "Accurate one-sentence claim with the correct number",
  "corrected_number_hook": "Correct shocking number/comparison",
  "bonus_ok": true,
  "evidence_url": "Best supporting URL",
  "notes": "One short sentence"
}}
"""
    report = _grounded_call(prompt, temperature=0.1, want="object", label="factcheck")

    if not isinstance(report, dict):
        # Grounded search unavailable → independent check with the pipeline's fallback LLMs (no auto-accept)
        print("⚠️ [DYK] Grounded fact-check unavailable. Using fallback LLM fact-checker...")
        try:
            from gemini_script import call_gemini_api
            report = call_gemini_api(None, prompt, prefer_fallback=True, category=fact.get("category", ""), task_type="reasoning")
            if isinstance(report, dict):
                report["checker"] = "fallback_llm"
        except Exception as e:
            print(f"⚠️ [DYK] Fallback fact-checker failed: {e}")
            report = None

    if not isinstance(report, dict) or not report.get("verdict"):
        print("❌ [DYK] No fact-checker available. Rejecting fact (never publish unchecked claims).")
        return False, fact, {"verdict": "UNCHECKED", "confidence": 0.0, "notes": "no checker available"}

    verdict = str(report.get("verdict", "")).upper()
    try:
        confidence = float(report.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    passed = (verdict == "TRUE" and confidence >= 0.75) or (verdict == "MOSTLY_TRUE" and confidence >= 0.8)
    if passed:
        fact = dict(fact)
        if verdict == "MOSTLY_TRUE" and report.get("corrected_claim"):
            fact["claim"] = report["corrected_claim"]
            if report.get("corrected_number_hook"):
                fact["number_hook"] = report["corrected_number_hook"]
        if report.get("bonus_ok") is False:
            fact["bonus_twist"] = ""
        if report.get("evidence_url") and not fact.get("source_url"):
            fact["source_url"] = report["evidence_url"]

    status = "✅ PASSED" if passed else "❌ REJECTED"
    print(f"🔎 [DYK] Fact-check {status}: '{fact.get('title')}' → {verdict} ({confidence:.2f}). {report.get('notes', '')}")
    return passed, fact, report


# ─────────────────────────────────────────────────────────────────────────────
# 3. Script + stock-footage storyboard
# ─────────────────────────────────────────────────────────────────────────────

DYK_SCRIPT_PROMPT = """You are VJ, creator of "Simple Tips by VJ" — creating viral, highly engaging YouTube Shorts in Universal Conversational Tanglish (like Tech Boss and Madan Gowri).
Write a 30-45 second "தெரியுமா?" YouTube Short script in 100% natural conversational spoken Tamil mixed smoothly with common English loan words.

VERIFIED FACT (use ONLY these facts — never invent extra numbers, names or dates):
- Claim: {claim}
- Shock number: {number_hook}
- Why it happens: {why}
- Bonus twist: {bonus}
- Tamil-life comparison idea: {tamil_connection}

STRUCTURE (strictly in this order):
1. HOOK (first 3 seconds): Say the shocking number/claim FIRST, end the sentence with "தெரியுமா?".
   Example: "ஒரு Octopus-க்கு மூணு இதயம் இருக்கு... தெரியுமா?"
   NEVER start with "ஒரு விஷயம் தெரியுமா", "இந்த வீடியோல", "வணக்கம்", "Did you know".
2. OPEN LOOP (3-8s): Tease the reason so they keep watching ("ஆனா ஏன்னு தெரிஞ்சா இன்னும் ஷாக் ஆவீங்க...").
3. EXPLAIN (8-28s): The reason in simple words using ONE everyday Tamil Nadu comparison.
4. TWIST (28-38s): The bonus twist as a final "wow" (skip if empty, then deepen the explanation instead).
5. ENDING (last 4s): One short debate/comment question in friendly conversational Tamil ("நீங்க என்ன நினைக்கிறீங்கன்னு கமெண்ட்ல சொல்லுங்க!"). No long subscribe speech.

STYLE (100% NATIVE SPOKEN TAMIL & UNIVERSAL TANGLISH):
- Universal Conversational Tanglish: Always use standard conversational spoken forms: பண்ணுங்க (never பண்ணுங்கோ or செய்யுங்கள்), பாருங்க (never பாருங்கோ or பாருங்கள்), தெரியுமா (never தெர்யுமா), அப்படி (never அப்புடி), கொஞ்சம் (never கொஞ்சூம்), இல்லையா (never இல்லியா), ஆகுது / ஆயிடும் (never ஆகும்), இருக்கு (never உள்ளது).
- BAN ALL TEXTBOOK & ROBOTIC TAMIL: Never use formal/written words like "செய்கிறது", "ஆகும்", "பாதுகாக்கப்படுகிறது", "என்று அழைக்கப்படுகிறது", "இதன் மூலம்", "பயன்படுத்தப்படுகிறது". Use active spoken words: "பண்ணுது", "ஆயிடும்", "காப்பாத்துது", "அப்டின்னு சொல்லுவாங்க", "இதனால".
- Smooth English Technical Loanwords: Phone, Battery, Screen, Settings, Hack, Brain, Heart, Blood, Space, Secret, Trick, Virus, Hack.
- Write ONLY in Tamil script plus simple English words. NEVER use Hindi/Devanagari or any other script.
- No scientific jargon — say it the way you'd explain it to a close friend over tea (e.g. "கண்ணுல இருக்குற color sensor" not "photoreceptor cells").
- Do NOT exaggerate beyond the verified claim.
- Natural breath and speech rhythm: Use commas (,) for natural pauses and ellipses (...) before exciting reveals so the voiceover breathes naturally.
- Short punchy sentences (mostly under 10 words).
- Write numbers as digits (3, 1600, 40%) so subtitles show them clearly.
- STRICT LENGTH: {min_words}-{max_words} words total.

OUTPUT: Only the raw script text. No labels, headings, brackets, emojis or timestamps."""


DYK_STORYBOARD_PROMPT = """You are a viral YouTube Shorts editor who cuts ONLY real stock footage (Pexels).

Split the SCRIPT below into consecutive narration segments of 3-6 words each.
CRITICAL: Concatenating all "narration" fields in order must reproduce the SCRIPT word-for-word.
Do not add, drop, translate or reorder any words.

For each segment choose stock footage that a viewer instantly connects with the spoken words.
Visual subjects available for this fact: {visual_subjects}

SCRIPT:
{script}

Return ONLY JSON (no markdown):
{{
  "storyboard": [
    {{
      "scene_number": 1,
      "narration": "exact words from the script",
      "stock_search_query": "1-3 word CONCRETE English Pexels search term for real footage (e.g. 'octopus swimming', 'temple tower', 'boiling water'). Never abstract words like 'concept', 'idea', 'shock', 'fact'.",
      "visual_prompt": "One sentence describing the exact shot (subject, action, framing)",
      "camera_motion": "Slow zoom|Dolly-in|Pan|Tracking shot|None",
      "transition": "Zoom transition|Swipe|Match cut|Flash",
      "on_screen_text": "1-3 UPPERCASE English words, use the key NUMBER when spoken (e.g. '3 HEARTS')",
      "emotion": "Curiosity|Surprise|Excitement|Focus"
    }}
  ],
  "unique_angle": "One sentence on what makes this Short's explanation different",
  "comment_hook": "Provocative Tanglish question to drive comments",
  "phonetic_pronunciation_map": {{"English word in script": "Tamil-friendly pronunciation"}}
}}

RULES:
- Scene 1 must show the most striking footage of the main subject (the hook frame).
- Never use the same stock_search_query for two consecutive scenes; vary angles (close-up, wide, action).
- Produce between 14 and 30 scenes."""


def _word_count(text):
    return len((text or "").split())


def _write_script(client, fact, category):
    from gemini_script import call_gemini_api, sanitize_script_against_ai_cliches
    min_w, max_w = DYK_WORD_RANGE
    prompt = DYK_SCRIPT_PROMPT.format(
        claim=fact.get("claim", ""),
        number_hook=fact.get("number_hook", "") or "(take it from the claim)",
        why=fact.get("why_it_happens", ""),
        bonus=fact.get("bonus_twist", "") or "(none)",
        tamil_connection=fact.get("tamil_connection", "") or "(pick a natural everyday comparison)",
        min_words=min_w,
        max_words=max_w,
    )
    for attempt in range(2):
        raw = call_gemini_api(client, prompt, model=GEMINI_FLASH_MODEL, prefer_fallback=True,
                              category=category, task_type="script_writer", expect_json=False)
        if isinstance(raw, dict):
            raw = raw.get("script") or raw.get("text") or ""
        text = sanitize_script_against_ai_cliches(str(raw or "").strip())
        words = _word_count(text)
        # Reject non-Tamil Indic scripts (Devanagari, Telugu, Kannada, Malayalam, etc.) leaking into TTS
        foreign = re.findall(r"[\u0900-\u0B7F\u0C00-\u0D7F]", text)
        if foreign:
            print(f"⚠️ [DYK] Script contains non-Tamil Indic characters ({''.join(foreign[:6])}). Retrying...")
            prompt += "\n\nPREVIOUS ATTEMPT CONTAINED HINDI/OTHER SCRIPT CHARACTERS. Use ONLY Tamil script and English."
            continue
        if min_w - 10 <= words <= max_w + 10:
            return text
        print(f"⚠️ [DYK] Script length {words} words outside {min_w}-{max_w}. Retrying...")
        prompt += f"\n\nPREVIOUS ATTEMPT HAD {words} WORDS. It MUST be {min_w}-{max_w} words."
    return None


def _build_storyboard(client, script_text, fact, category):
    from gemini_script import call_gemini_api, normalize_storyboard, normalize_llm_json_dict
    subjects = ", ".join(fact.get("visual_subjects", []) or []) or "choose from the script subject"
    prompt = DYK_STORYBOARD_PROMPT.format(visual_subjects=subjects, script=script_text)

    for attempt in range(2):
        res = call_gemini_api(client, prompt, model=GEMINI_FLASH_MODEL, category=category, task_type="reasoning")
        res = normalize_llm_json_dict(res) if res else {}
        storyboard = normalize_storyboard(res.get("storyboard")) if isinstance(res, dict) else []
        storyboard = [s for s in storyboard if isinstance(s, dict) and s.get("narration", "").strip()]
        sb_words = sum(_word_count(s["narration"]) for s in storyboard)
        script_words = _word_count(script_text)
        if len(storyboard) >= 10 and sb_words >= 0.85 * script_words:
            return res, storyboard
        print(f"⚠️ [DYK] Storyboard incomplete ({len(storyboard)} scenes, {sb_words}/{script_words} words). Retrying...")
        prompt += "\n\nPREVIOUS ATTEMPT DROPPED WORDS OR SCENES. Cover the ENTIRE script word-for-word in 14-30 scenes."
    return None, []


def _fallback_storyboard(script_text, fact):
    """Deterministic split when the storyboard agent fails: 4-word segments cycling visual subjects."""
    words = script_text.split()
    subjects = [s for s in (fact.get("visual_subjects") or []) if s] or [fact.get("title", "nature")]
    scenes = []
    for i in range(0, len(words), 4):
        idx = len(scenes)
        scenes.append({
            "scene_number": idx + 1,
            "narration": " ".join(words[i:i + 4]),
            "stock_search_query": subjects[idx % len(subjects)],
            "visual_prompt": subjects[idx % len(subjects)],
            "camera_motion": "Slow zoom" if idx % 2 == 0 else "Pan",
            "transition": "Zoom transition",
            "on_screen_text": "",
        })
    return scenes


def _scenes_to_chunks(storyboard, fact):
    from gemini_script import sanitize_script_against_ai_cliches
    subjects = [s for s in (fact.get("visual_subjects") or []) if s]
    chunks = []
    prev_query = None
    for i, scene in enumerate(storyboard):
        text = sanitize_script_against_ai_cliches(str(scene.get("narration", ""))) if i == 0 else str(scene.get("narration", "")).strip()
        if not text:
            continue
        query = str(scene.get("stock_search_query", "")).strip()
        if not query or query.lower() == (prev_query or "").lower():
            if subjects:
                query = subjects[i % len(subjects)]
        prev_query = query
        chunks.append({
            "chunk_id": len(chunks) + 1,
            "text": text,
            "english_caption": scene.get("on_screen_text", ""),
            "start": 0.0,
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "stock_search_query": query,
            "nano_visual_prompt": scene.get("visual_prompt", query),
            "visual_type": "video",
            "camera_motion": scene.get("camera_motion", "Slow zoom"),
            "transition": scene.get("transition", "Zoom transition"),
        })
    return chunks


def _metadata(client, fact, script_text, category):
    from gemini_script import call_gemini_api, PIPELINE_PROMPTS
    sentences = [s.strip() for s in re.split(r"[.?!]", script_text) if s.strip()]
    prompt = PIPELINE_PROMPTS["metadata"].format(
        topic=fact.get("title"),
        core_concept=fact.get("claim"),
        first_two_sentences_of_script=" ".join(sentences[:2]),
    )
    prompt += "\nEXTRA RULE: The title MUST contain the shocking number and end with 'தெரியுமா?' or a curiosity gap."
    res = call_gemini_api(client, prompt, prefer_fallback=True, category=category, task_type="metadata")
    return res if isinstance(res, dict) else {}


def generate_dyk_script(category, facts=None, failed_topics=None):
    """
    Full "Did You Know" generation. Returns script_data compatible with main.py, or None.
    `facts` may be DYK facts or generic fetch_topics articles (they are adapted automatically).
    """
    failed_topics = failed_topics if failed_topics is not None else []  # mutated so main.py retries skip rejects
    category = get_dyk_category(category)
    print(f"💡 [DYK] Generating 'தெரியுமா?' Short for category: {category}")

    from gemini_script import apply_cta_rotation, is_offline_mode_active
    if is_offline_mode_active():
        print("🔴 [DYK] Offline mode active — skipping DYK generation.")
        return None

    candidates = []
    for f in facts or []:
        if not isinstance(f, dict):
            continue
        candidates.append(f if f.get("claim") else _from_generic_article(f, category))
    candidates = [c for c in candidates if c.get("title") and not any(
        ft and ft.lower() in c["title"].lower() for ft in failed_topics)]
    if not candidates:
        candidates = fetch_dyk_facts(category, failed_topics)
    if not candidates:
        print("❌ [DYK] No candidate facts available.")
        return None

    # ── Fact-check gate: try up to 3 candidates ──
    verified, report = None, None
    for cand in candidates[:3]:
        ok, checked, rep = fact_check_claim(cand)
        if ok:
            verified, report = checked, rep
            break
        failed_topics.append(cand.get("title"))
    if not verified:
        print("❌ [DYK] No candidate passed the fact-check gate.")
        return None

    client = get_gemini_client()

    script_text = _write_script(client, verified, category)
    if not script_text:
        print("❌ [DYK] Script writer failed.")
        return None
    print(f"📝 [DYK] Script ({_word_count(script_text)} words): {script_text[:120]}...")

    sb_meta, storyboard = _build_storyboard(client, script_text, verified, category)
    if not storyboard:
        print("⚠️ [DYK] Using deterministic storyboard fallback.")
        sb_meta, storyboard = {}, _fallback_storyboard(script_text, verified)

    chunks = _scenes_to_chunks(storyboard, verified)
    meta = _metadata(client, verified, script_text, category)

    title = meta.get("title") or f"{verified.get('number_hook') or verified.get('title')} தெரியுமா? 🤯"
    hashtags = list(dict.fromkeys(_DYK_HASHTAGS + (meta.get("hashtags") or [])))[:6]
    keywords = list(dict.fromkeys((verified.get("keywords") or []) + ["Did You Know", "Tamil Facts", "தெரியுமா"]))

    script_data = {
        "format": FORMAT_ID,
        "visual_mode": "stock_only",
        "title": title,
        "title_variants": [title, f"{title} 🤯", f"{verified.get('number_hook') or 'இது'} உண்மையா?! 😳"],
        "script": script_text,
        "hook": chunks[0]["text"] if chunks else "",
        "storyboard": storyboard,
        "subtitle_chunks": chunks,
        "description": meta.get("description") or verified.get("claim", ""),
        "hashtags": hashtags,
        "keywords": keywords,
        "summary": verified.get("claim", ""),
        "sub_category": category,
        "unique_angle": (sb_meta or {}).get("unique_angle") or f"Fact-checked: {verified.get('claim', '')}",
        "comment_hook": (sb_meta or {}).get("comment_hook") or "இது உங்களுக்கு முன்னாடியே தெரியுமா? 👇",
        "phonetic_pronunciation_map": (sb_meta or {}).get("phonetic_pronunciation_map") or {},
        "original_news_headline": verified.get("title"),
        "original_news_url": verified.get("source_url"),
        "use_case_evidence_url": verified.get("source_url"),
        "relevant_links": [u for u in [verified.get("source_url"), (report or {}).get("evidence_url")] if u],
        "visual_subjects": verified.get("visual_subjects", []),
        "fact_check": {
            "verdict": (report or {}).get("verdict"),
            "confidence": (report or {}).get("confidence"),
            "notes": (report or {}).get("notes"),
            "claim": verified.get("claim"),
        },
    }
    script_data = apply_cta_rotation(script_data)
    if meta.get("thumbnail_text"):
        script_data["thumbnail_text"] = meta["thumbnail_text"]

    print(f"🎉 [DYK] Ready: '{title}' — {len(chunks)} stock-footage scenes.")
    return script_data


if __name__ == "__main__":
    import argparse
    from ecosystem_logic import get_slot_info

    parser = argparse.ArgumentParser(description="Preview a 'Did You Know' script (no audio/video).")
    parser.add_argument("--category", type=str, default=None)
    args = parser.parse_args()

    _, _, slot_category = get_slot_info()
    data = generate_dyk_script(args.category or slot_category)
    if data:
        preview = {k: data[k] for k in ("title", "script", "fact_check", "original_news_url", "hashtags")}
        preview["scenes"] = [(c["text"], c["stock_search_query"]) for c in data["subtitle_chunks"]]
        print(json.dumps(preview, ensure_ascii=False, indent=2))
