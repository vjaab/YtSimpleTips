# -*- coding: utf-8 -*-
"""
longform_script.py — Script + storyboard generation for the 2-3 minute LONGFORM pipeline.

Flow (mirrors did_you_know.py, scaled up for chaptered long videos):
  1. discover_topics()   → Gemini Search Grounding finds candidate topics with 6-9 verifiable key facts + sources
  2. fact_check_topic()  → independent grounded verification; unverified facts are dropped, weak topics rejected
  3. write_script()      → chaptered Tanglish script (### markers) sized to the target duration
  4. split_into_scenes() → DETERMINISTIC 8-18 word scenes (guarantees the storyboard covers the whole script)
  5. plan_visuals()      → LLM assigns each scene stock / ai_image / infographic / screenshot visuals
  6. generate_metadata() → title variants, description, hashtags, thumbnail text

generate_longform_script() returns a script_data dict consumed by main_longform.py.
"""

import json
import re

from config import GEMINI_FLASH_MODEL, get_gemini_client
from did_you_know import _grounded_call, _extract_json, _avoid_list
from longform_niches import LONGFORM_NICHES, LONGFORM_TARGET_SECONDS
from topic_tracker import check_story_uniqueness

FORMAT_ID = "longform"

# Default spoken pace (words incl. pauses per second of finished audio). main_longform recalibrates after real TTS.
DEFAULT_WORDS_PER_SEC = 2.35

INFOGRAPHIC_SCHEMAS = """\
- "stat":       {"headline": "WHAT THE NUMBER MEANS (≤5 words)", "subtext": "THE NUMBER e.g. 1,600 YEARS or 40%", "context": "≤10 word explanation"}
- "comparison": {"title": "≤4 words", "item1": "A", "val1": "value", "item2": "B", "val2": "value"}
- "timeline":   {"title": "≤4 words", "events": [{"date": "year/time", "desc": "≤6 words"}, ... 2-3 items]}
- "definition": {"term": "≤3 words", "definition": "≤20 words plain explanation", "example": "≤12 words"}
- "ranking":    {"title": "≤4 words", "items": [{"name": "≤3 words", "val": "≤4 words"}, ... 3 items]}
- "growth":     {"title": "≤4 words", "percent": "+NN%", "subtext": "≤8 words"}"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def word_count(text):
    return len((text or "").split())


def words_range_for_duration(words_per_sec, min_sec, max_sec):
    return int(min_sec * words_per_sec), int(max_sec * words_per_sec)


def _llm_json(prompt, category="", task_type="reasoning"):
    """JSON response from the multi-model pipeline (OpenRouter priority tiers → Gemini)."""
    from gemini_script import call_gemini_api, normalize_llm_json_dict
    res = call_gemini_api(get_gemini_client(), prompt, model=GEMINI_FLASH_MODEL, category=category, task_type=task_type)
    if not res:
        return {}
    if isinstance(res, list):
        return {"scenes": res}
    try:
        return normalize_llm_json_dict(res) or {}
    except Exception:
        return res if isinstance(res, dict) else {}


def _llm_text(prompt, category=""):
    from gemini_script import call_gemini_api
    raw = call_gemini_api(get_gemini_client(), prompt, model=GEMINI_FLASH_MODEL, prefer_fallback=True,
                          category=category, task_type="script_writer", expect_json=False)
    if isinstance(raw, dict):
        raw = raw.get("script") or raw.get("text") or ""
    return str(raw or "").strip()


# ─────────────────────────────────────────────────────────────────────────────
# 1. Topic discovery
# ─────────────────────────────────────────────────────────────────────────────

def discover_topics(niche, failed_topics=None):
    """Finds ~5 candidate longform topics via Search Grounding. Each is source-backed and unique vs. the tracker."""
    avoid = _avoid_list() + list(failed_topics or [])
    avoid_str = "\n".join(f"- {t}" for t in avoid[:60])

    prompt = f"""
Search the web and find 5 topics for a VIRAL 2-3 minute Tamil YouTube explainer video (faceless, voice-over, documentary style).
Audience: Tamil-speaking students, parents, office-goers and elders in Tamil Nadu.

NICHE: {niche['label']}
FOCUS: {niche['angle']}
HOOK STYLE: {niche['hook_style']}
SAFETY RULES: {niche['safety']}

EVERY topic MUST:
1. Be backed by at least ONE reachable, reputable source URL (Wikipedia, Britannica, NASA/ISRO, Nature, WHO, government, major news, ASI, museum, university).
2. Provide 6-9 SPECIFIC, individually verifiable key facts (names, years, numbers, places). No vague claims.
3. Sustain 2-3 minutes with a clear story arc: hook → context → 2-3 escalating reveals → twist/payoff.
4. Be genuinely interesting to Tamil viewers (react: "அட, இது தெரியாதே!"). No overdone textbook basics.
5. Be filmable: concrete subjects for stock footage AND strong AI-image ideas.
6. NOT be a myth, hoax, rumour, conspiracy or unproven claim presented as fact.

DO NOT REPEAT ANY OF THESE ALREADY-COVERED TOPICS:
{avoid_str}

Return ONLY a JSON array (no markdown) of 5 objects:
[
  {{
    "title": "Short English working title",
    "premise": "ONE sentence: what the video is about",
    "key_facts": ["6-9 precise, verifiable one-sentence facts in logical story order"],
    "chapter_beats": ["5 ordered story beats, 3-8 words each"],
    "tamil_connection": "A relatable Tamil Nadu comparison/hook (kitchen, temple, bus, school, village, cinema)",
    "visual_subjects": ["8-10 concrete 1-3 word English stock-video search terms"],
    "ai_image_ideas": ["4-6 one-sentence ideas for AI-generated illustrative images"],
    "source_urls": ["1-3 direct reputable URLs"],
    "source_name": "Main source name",
    "keywords": ["4-6 English SEO keywords"],
    "virality_score": 1-10
  }}
]
"""
    topics = _grounded_call(prompt, temperature=0.8, want="array", label="longform-discover") or []
    if not isinstance(topics, list):
        topics = []

    from fetch_topics import validate_url
    clean = []
    for t in topics:
        if not isinstance(t, dict) or not t.get("title"):
            continue
        facts = [f for f in (t.get("key_facts") or []) if isinstance(f, str) and f.strip()]
        urls = [u for u in (t.get("source_urls") or []) if isinstance(u, str) and u.startswith("http")]
        if len(facts) < 5 or not urls:
            continue
        if failed_topics and any(ft and ft.lower() in t["title"].lower() for ft in failed_topics):
            continue
        ok, reason = check_story_uniqueness(new_title=t["title"], new_url=urls[0])
        if not ok:
            print(f"⏭️ [LONGFORM] Duplicate topic skipped: {t['title']} ({reason})")
            continue
        reachable = [u for u in urls if validate_url(u)]
        if not reachable:
            print(f"⏭️ [LONGFORM] No reachable source for: {t['title']} → {urls}")
            continue
        t["key_facts"] = facts
        t["source_urls"] = reachable
        clean.append(t)

    clean.sort(key=lambda x: float(x.get("virality_score", 0) or 0), reverse=True)
    print(f"✅ [LONGFORM] {len(clean)} unique, source-backed candidate topics for '{niche['short_label']}'.")
    return clean


# ─────────────────────────────────────────────────────────────────────────────
# 2. Fact-check gate
# ─────────────────────────────────────────────────────────────────────────────

def fact_check_topic(topic, niche):
    """
    Independent grounded verification of every key fact.
    Returns (passed, topic_with_only_verified_facts, report). Never publishes unchecked claims.
    """
    numbered = "\n".join(f"{i + 1}. {f}" for i, f in enumerate(topic["key_facts"]))
    hypothetical = (
        "NOTE: the video premise is a hypothetical scenario; verify ONLY the underlying scientific/historical facts.\n"
        if niche is LONGFORM_NICHES["what_if"] else ""
    )
    prompt = f"""
You are a strict fact-checker for an educational YouTube channel. Search the web and verify EACH fact below.
{hypothetical}
TOPIC: {topic.get('title')}
PREMISE: {topic.get('premise')}
CITED SOURCES: {', '.join(topic.get('source_urls', []))}

FACTS:
{numbered}

Rules:
- Check numbers, dates and names precisely. Exaggerated or wrong numbers = WRONG.
- Myths, folklore or unproven theories stated as fact = WRONG (a clearly-labelled theory is acceptable).
- If the core is right but the wording needs a fix, mark CORRECTED and supply the corrected sentence.

Return ONLY JSON (no markdown):
{{
  "overall_verdict": "TRUE|MOSTLY_TRUE|MISLEADING|FALSE|UNVERIFIABLE",
  "confidence": 0.0-1.0,
  "facts": [{{"index": 1, "status": "VERIFIED|CORRECTED|WRONG|UNVERIFIABLE", "corrected": "only when CORRECTED"}}],
  "evidence_urls": ["best supporting URLs"],
  "notes": "One short sentence"
}}
"""
    report = _grounded_call(prompt, temperature=0.1, want="object", label="longform-factcheck")
    if not isinstance(report, dict):
        print("⚠️ [LONGFORM] Grounded fact-check unavailable. Using fallback LLM fact-checker...")
        try:
            from gemini_script import call_gemini_api
            report = call_gemini_api(None, prompt, prefer_fallback=True, category=niche["label"], task_type="reasoning")
            if isinstance(report, dict):
                report["checker"] = "fallback_llm"
        except Exception as e:
            print(f"⚠️ [LONGFORM] Fallback fact-checker failed: {e}")
            report = None

    if not isinstance(report, dict) or not report.get("overall_verdict"):
        print("❌ [LONGFORM] No fact-checker available. Rejecting topic (never publish unchecked claims).")
        return False, topic, {"overall_verdict": "UNCHECKED", "confidence": 0.0, "notes": "no checker available"}

    verdict = str(report.get("overall_verdict", "")).upper()
    try:
        confidence = float(report.get("confidence", 0) or 0)
    except (TypeError, ValueError):
        confidence = 0.0

    verified = []
    by_index = {}
    for f in report.get("facts") or []:
        if isinstance(f, dict):
            try:
                by_index[int(f.get("index"))] = f
            except (TypeError, ValueError):
                continue
    for i, fact in enumerate(topic["key_facts"], start=1):
        entry = by_index.get(i)
        if not entry:
            continue
        status = str(entry.get("status", "")).upper()
        if status == "VERIFIED":
            verified.append(fact)
        elif status == "CORRECTED" and entry.get("corrected"):
            verified.append(str(entry["corrected"]).strip())

    passed = verdict in ("TRUE", "MOSTLY_TRUE") and confidence >= 0.75 and len(verified) >= 5
    tag = "✅ PASSED" if passed else "❌ REJECTED"
    print(f"🔎 [LONGFORM] Fact-check {tag}: '{topic.get('title')}' → {verdict} ({confidence:.2f}), "
          f"{len(verified)}/{len(topic['key_facts'])} facts verified. {report.get('notes', '')}")
    if passed:
        topic = dict(topic)
        topic["key_facts"] = verified
        extra = [u for u in (report.get("evidence_urls") or []) if isinstance(u, str) and u.startswith("http")]
        topic["source_urls"] = list(dict.fromkeys(topic.get("source_urls", []) + extra))[:4]
    return passed, topic, report


# ─────────────────────────────────────────────────────────────────────────────
# 3. Chaptered Tanglish script
# ─────────────────────────────────────────────────────────────────────────────

LONGFORM_SCRIPT_PROMPT = """You are VJ, creator of "Simple Tips by VJ" — creating viral, highly engaging 2-3 minute YouTube explainer videos in Universal Conversational Tanglish (like Tech Boss and Madan Gowri).
Write a ~{target_minutes}-minute narration in 100% natural conversational spoken Tamil mixed smoothly with common English loan words.

NICHE: {niche_label}
NARRATOR TONE: {tone}

VERIFIED FACTS (use ONLY these — never invent extra numbers, names, dates or quotes):
{facts}

TOPIC: {title}
PREMISE: {premise}
Tamil-life comparison idea: {tamil_connection}
SAFETY RULES: {safety}

STRUCTURE — write exactly 5 or 6 chapters. Start every chapter with a header line "### <English chapter title, 2-5 words>", then the narration paragraph:
1. HOOK chapter (first ~15 seconds, 35-50 words): {hook_style} NEVER start with "வணக்கம்", "இந்த வீடியோல", "ஒரு விஷயம் தெரியுமா", "Did you know", "Welcome". End with an open loop that makes people stay.
2. CONTEXT chapter: set the scene in simple words.
3. REVEAL chapters (2-3): escalating, each uses the verified facts and ONE everyday Tamil Nadu comparison; re-hook every ~20 seconds ("ஆனா இங்கதான் twist...").
4. TWIST/PAYOFF chapter: the final wow or the most important takeaway.
5. OUTRO chapter (last ~12 seconds): ONE debate/comment question + one short line to subscribe "Simple Tips by VJ". No long goodbye.

STYLE (100% NATIVE SPOKEN TAMIL & UNIVERSAL TANGLISH):
- Standard conversational spoken forms: பண்ணுங்க, பாருங்க, தெரியுமா, அப்படி, கொஞ்சம், இல்லையா, ஆகுது / ஆயிடும், இருக்கு.
- BAN textbook / robotic Tamil: செய்கிறது, ஆகும், பாதுகாக்கப்படுகிறது, இதன் மூலம், பயன்படுத்தப்படுகிறது. Use: பண்ணுது, ஆயிடும், காப்பாத்துது, இதனால.
- Smooth English loanwords where natural (Phone, Space, Brain, Secret, Trick, Temple, Scam, Report).
- Write ONLY in Tamil script plus simple English words. NEVER use Hindi/Devanagari or any other script.
- No jargon — explain like a friend over tea.
- Do NOT exaggerate beyond the verified facts. Label theories clearly ("இது ஒரு theory").
- Use commas for natural pauses and "..." before reveals so the voice-over breathes.
- Short punchy sentences (mostly under 12 words). Write numbers as digits.
- STRICT LENGTH: {min_words}-{max_words} words total across all chapters.

OUTPUT: Only the chapter headers ("### Title") and narration text. No brackets, emojis, timestamps, bullet points or extra commentary."""


def parse_chapters(raw):
    """Parses '### Title' + narration blocks into [{'title','text'}]."""
    raw = (raw or "").replace("**", "").replace("__", "")
    chapters, cur = [], None
    for line in raw.splitlines():
        m = re.match(r"^\s*#{2,4}\s*(.+?)\s*$", line)
        if m:
            cur = {"title": m.group(1).strip(" :[]*#"), "lines": []}
            chapters.append(cur)
            continue
        if line.strip():
            if cur is None:
                cur = {"title": "Intro", "lines": []}
                chapters.append(cur)
            cur["lines"].append(line.strip())
    out = []
    for c in chapters:
        text = " ".join(c["lines"]).strip()
        if text:
            out.append({"title": c["title"][:60] or "Chapter", "text": text})
    return out


def write_script(topic, niche, word_range, category=""):
    """Returns a list of chapters or None. Validates language, length and chapter structure; retries with feedback."""
    from gemini_script import sanitize_script_against_ai_cliches
    min_w, max_w = word_range
    facts = "\n".join(f"- {f}" for f in topic["key_facts"])
    prompt = LONGFORM_SCRIPT_PROMPT.format(
        target_minutes=f"{LONGFORM_TARGET_SECONDS / 60:.1f}".rstrip("0").rstrip("."),
        niche_label=niche["label"], tone=niche["tone"], facts=facts,
        title=topic.get("title", ""), premise=topic.get("premise", ""),
        tamil_connection=topic.get("tamil_connection") or "(pick a natural everyday comparison)",
        safety=niche["safety"], hook_style=niche["hook_style"], min_words=min_w, max_words=max_w,
    )
    for attempt in range(3):
        raw = _llm_text(prompt, category=category)
        chapters = parse_chapters(raw)
        for c in chapters:
            c["text"] = sanitize_script_against_ai_cliches(c["text"])
        total = sum(word_count(c["text"]) for c in chapters)
        problem = None
        # Tamil is U+0B80–U+0BFF; anything in the neighbouring Indic blocks (Devanagari, Telugu, Kannada, Malayalam…) is foreign
        if re.search(r"[\u0900-\u0B7F\u0C00-\u0D7F]", "".join(c["text"] for c in chapters)):
            problem = "SCRIPT CONTAINED HINDI/OTHER-SCRIPT CHARACTERS. Use ONLY Tamil script and English."
        if not problem and not (4 <= len(chapters) <= 7):
            problem = f"HAD {len(chapters)} CHAPTERS. It MUST have 5 or 6 chapters, each starting with '### Title'."
        if not problem and not (min_w - 15 <= total <= max_w + 15):
            problem = f"HAD {total} WORDS. It MUST be {min_w}-{max_w} words."
        if not problem and word_count(chapters[0]["text"]) > 70:
            problem = "HOOK CHAPTER WAS TOO LONG. Keep it 35-50 words."
        if not problem:
            return chapters
        print(f"⚠️ [LONGFORM] Script attempt {attempt + 1}/3 rejected: {problem}")
        prompt += f"\n\nPREVIOUS ATTEMPT {problem}"
    return None


# ─────────────────────────────────────────────────────────────────────────────
# 4. Deterministic scene splitting
# ─────────────────────────────────────────────────────────────────────────────

def _split_long_sentence(sentence, min_words, max_words):
    """Splits an over-long sentence at commas (or hard at max_words) into pieces of <= max_words."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]
    pieces, buf = [], []
    for w in words:
        buf.append(w)
        at_comma = w.endswith((",", ";", ":", "…", "-"))
        if (at_comma and len(buf) >= min_words) or len(buf) >= max_words:
            pieces.append(" ".join(buf))
            buf = []
    if buf:
        if pieces and len(buf) < 4:
            pieces[-1] += " " + " ".join(buf)
        else:
            pieces.append(" ".join(buf))
    return pieces


def split_into_scenes(chapters, min_words=8, max_words=18):
    """
    Splits chapters into consecutive scenes (≈3-7 s of speech each). Concatenating every scene's text
    reproduces the script word-for-word, so chunk_builder alignment can never drop narration.
    """
    scenes = []
    for ci, ch in enumerate(chapters):
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", ch["text"]) if s.strip()]
        pieces = []
        for s in sentences:
            pieces.extend(_split_long_sentence(s, min_words, max_words))
        buf, ch_scenes = [], []
        for p in pieces:
            buf.append(p)
            if word_count(" ".join(buf)) >= min_words:
                ch_scenes.append(" ".join(buf))
                buf = []
        if buf:
            if ch_scenes and word_count(" ".join(buf)) < 4:
                ch_scenes[-1] += " " + " ".join(buf)
            else:
                ch_scenes.append(" ".join(buf))
        for t in ch_scenes:
            scenes.append({"scene_number": len(scenes) + 1, "chapter_index": ci, "chapter_title": ch["title"], "text": t})
    return scenes


# ─────────────────────────────────────────────────────────────────────────────
# 5. Visual planning (stock / AI image / infographic / screenshot)
# ─────────────────────────────────────────────────────────────────────────────

VISUAL_PLAN_PROMPT = """You are the lead video editor of a viral faceless YouTube documentary channel. Plan the visuals for every numbered narration scene below.

NICHE: {niche_label}
AI IMAGE ART DIRECTION: {ai_style}
STOCK FOOTAGE IDEAS: {stock_hint}
TOPIC visual subjects: {visual_subjects}
TOPIC AI image ideas: {ai_ideas}
TARGET VISUAL MIX (approx %): stock={mix_stock} ai_image={mix_ai} infographic={mix_info} screenshot={mix_shot}
VERIFIED FACTS (infographics may ONLY use numbers/dates from here):
{facts}

SCENES:
{scenes}

Choose per scene ONE visual_type:
- "stock": real stock footage — needs a CONCRETE 1-3 word English Pexels query (e.g. 'temple tower', 'night street'). Never abstract words like 'concept', 'idea', 'mystery'.
- "ai_image": AI-generated illustrative still — write "ai_prompt": ONE vivid sentence (subject, setting, mood, camera). No text/logos/watermarks, no real celebrities.
- "infographic": animated data card — ONLY when the scene states a concrete number, comparison, timeline, definition or ranking. Provide "infographic_type" and "infographic_data" matching exactly:
{schemas}
- "screenshot": a capture of the cited source website — use for at most 2 scenes that mention research, official records or proof.

RULES:
- Scene 1 MUST be "stock" or "ai_image" — the most striking hook frame.
- Never two "infographic" or two "screenshot" scenes in a row; never the same stock_query twice in a row.
- For EVERY scene also give "on_screen_text": 1-3 UPPERCASE English words (use the key number when spoken) or "".
- Match visuals to what is being SAID in that scene so viewers instantly connect.

Return ONLY JSON (no markdown):
{{
  "scenes": [
    {{"scene": 1, "visual_type": "stock|ai_image|infographic|screenshot", "stock_query": "...", "ai_prompt": "...",
      "on_screen_text": "...", "infographic_type": "stat", "infographic_data": {{}}}}
  ],
  "phonetic_pronunciation_map": {{"English word used in the script": "Tamil-friendly pronunciation"}}
}}
Include ALL {n_scenes} scenes in order."""


_INFO_REQUIRED = {
    "stat": ("headline", "subtext"),
    "comparison": ("item1", "item2"),
    "timeline": ("events",),
    "definition": ("term", "definition"),
    "ranking": ("items",),
    "growth": ("percent",),
}


def _valid_infographic(itype, data):
    if itype not in _INFO_REQUIRED or not isinstance(data, dict):
        return False
    for key in _INFO_REQUIRED[itype]:
        v = data.get(key)
        if not v:
            return False
    if itype == "timeline" and not (isinstance(data["events"], list) and len(data["events"]) >= 2):
        return False
    if itype == "ranking" and not (isinstance(data["items"], list) and len(data["items"]) >= 2):
        return False
    # Reject unfilled LLM placeholders
    blob = json.dumps(data, ensure_ascii=False)
    return not re.search(r"\bX{2,}\b|N/A|\.\.\.|\bTBD\b", blob)


def plan_visuals(scenes, topic, niche, category=""):
    """Returns (chunks, phonetic_map): subtitle_chunk dicts (one per scene) with visual plans attached."""
    scene_lines = "\n".join(f"{s['scene_number']}. [{s['chapter_title']}] {s['text']}" for s in scenes)
    mix = niche["visual_mix"]
    prompt = VISUAL_PLAN_PROMPT.format(
        niche_label=niche["label"], ai_style=niche["ai_style"], stock_hint=niche["stock_hint"],
        visual_subjects=", ".join(topic.get("visual_subjects") or []) or "derive from the script",
        ai_ideas="; ".join(topic.get("ai_image_ideas") or []) or "derive from the script",
        mix_stock=mix["stock"], mix_ai=mix["ai_image"], mix_info=mix["infographic"], mix_shot=mix["screenshot"],
        facts="\n".join(f"- {f}" for f in topic["key_facts"]), scenes=scene_lines,
        schemas=INFOGRAPHIC_SCHEMAS, n_scenes=len(scenes),
    )
    plan, phonetic = {}, {}
    for attempt in range(2):
        res = _llm_json(prompt, category=category)
        items = res.get("scenes") if isinstance(res, dict) else None
        if isinstance(items, list) and len(items) >= 0.6 * len(scenes):
            for it in items:
                if isinstance(it, dict):
                    try:
                        plan[int(it.get("scene"))] = it
                    except (TypeError, ValueError):
                        continue
            phonetic = res.get("phonetic_pronunciation_map") or {}
            break
        print(f"⚠️ [LONGFORM] Visual plan incomplete (attempt {attempt + 1}/2). Retrying...")
        prompt += "\n\nPREVIOUS ATTEMPT WAS INCOMPLETE. Return ALL scenes."

    subjects = [s for s in (topic.get("visual_subjects") or []) if s] or [topic.get("title", "nature")]
    ai_ideas = [s for s in (topic.get("ai_image_ideas") or []) if s]
    source_urls = topic.get("source_urls") or []
    shots_used, prev_type, prev_query = 0, None, None
    chunks = []
    for s in scenes:
        n = s["scene_number"]
        it = plan.get(n, {})
        vtype = str(it.get("visual_type", "")).strip().lower()
        if vtype not in ("stock", "ai_image", "infographic", "screenshot"):
            vtype = "stock" if n % 2 else "ai_image"   # deterministic alternate when the planner skipped a scene
        itype = str(it.get("infographic_type", "")).strip().lower()
        idata = it.get("infographic_data") or {}

        if vtype == "infographic" and (prev_type == "infographic" or not _valid_infographic(itype, idata)):
            vtype = "ai_image"
        if vtype == "screenshot" and (prev_type == "screenshot" or shots_used >= 2 or not source_urls):
            vtype = "ai_image"
        if n == 1 and vtype in ("infographic", "screenshot"):
            vtype = "stock"

        query = str(it.get("stock_query", "")).strip()
        if not query or query.lower() == (prev_query or "").lower():
            query = subjects[(n - 1) % len(subjects)]
        ai_prompt = str(it.get("ai_prompt", "")).strip() or (ai_ideas[(n - 1) % len(ai_ideas)] if ai_ideas else f"{topic.get('title')}, {query}")

        if vtype == "screenshot":
            shots_used += 1
        prev_type, prev_query = vtype, query

        chunks.append({
            "chunk_id": n,
            "text": s["text"],
            "english_caption": str(it.get("on_screen_text", "")).strip()[:30],
            "start": 0.0, "end": 0.0,
            "plan": vtype,
            "has_infographic": vtype == "infographic",
            "infographic_type": itype if vtype == "infographic" else "none",
            "infographic_data": idata if vtype == "infographic" else {},
            "stock_search_query": query,
            "nano_visual_prompt": ai_prompt,
            "screenshot_url": source_urls[(shots_used - 1) % len(source_urls)] if vtype == "screenshot" else "",
            "chapter_index": s["chapter_index"],
            "chapter_title": s["chapter_title"],
        })
    counts = {k: sum(1 for c in chunks if c["plan"] == k) for k in ("stock", "ai_image", "infographic", "screenshot")}
    print(f"🎞️ [LONGFORM] Visual plan for {len(chunks)} scenes: {counts}")
    return chunks, phonetic if isinstance(phonetic, dict) else {}


# ─────────────────────────────────────────────────────────────────────────────
# 6. Metadata
# ─────────────────────────────────────────────────────────────────────────────

LONGFORM_METADATA_PROMPT = """You are a YouTube SEO expert for the Tamil channel "Simple Tips by VJ".
Create metadata for a 2-3 minute Tamil explainer video.

NICHE: {niche_label}
TOPIC: {title}
PREMISE: {premise}
HOOK LINE: {hook}

Return ONLY JSON (no markdown):
{{
  "title_variants": ["3 curiosity-driven titles, Tamil/Tanglish + English keywords, 45-70 chars each, no clickbait lies, no < or >"],
  "description": "2-3 sentence Tanglish summary of what viewers will learn (no hashtags)",
  "hashtags": ["4-6 hashtags, mix of Tamil and English, each starting with #"],
  "thumbnail_text": "1-4 word ENGLISH UPPERCASE punchy thumbnail text",
  "comment_bait_question": "ONE Tanglish debate question for the pinned comment",
  "keywords": ["6-10 English + Tamil search keywords"]
}}"""


def generate_metadata(topic, niche, hook, category=""):
    res = _llm_json(LONGFORM_METADATA_PROMPT.format(
        niche_label=niche["label"], title=topic.get("title", ""), premise=topic.get("premise", ""), hook=hook,
    ), category=category, task_type="metadata")
    res = res if isinstance(res, dict) else {}

    titles = [str(t).replace("<", "").replace(">", "").strip() for t in (res.get("title_variants") or []) if str(t).strip()]
    base = topic.get("title", "Simple Tips by VJ")
    fallback_title = f"{base} — முழு கதை! {niche['emoji']}"
    while len(titles) < 3:
        titles.append(titles[0] if titles else fallback_title)
    titles = [t[:100] for t in titles[:3]]

    hashtags = [h if h.startswith("#") else f"#{h}" for h in (res.get("hashtags") or []) if isinstance(h, str) and h.strip()]
    hashtags = list(dict.fromkeys(hashtags + niche["hashtags"] + ["#SimpleTipsByVJ"]))[:8]
    keywords = list(dict.fromkeys([k for k in (res.get("keywords") or []) if isinstance(k, str)] +
                                  (topic.get("keywords") or []) + ["Tamil", "Simple Tips by VJ"]))
    return {
        "title_variants": titles,
        "description": str(res.get("description") or topic.get("premise") or base).strip(),
        "hashtags": hashtags,
        "thumbnail_text": str(res.get("thumbnail_text") or niche["short_label"]).upper()[:30],
        "comment_bait_question": str(res.get("comment_bait_question") or "உங்க கருத்து என்ன? கமெண்ட்ல சொல்லுங்க! 👇").strip(),
        "keywords": keywords,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def generate_longform_script(niche_id, word_range, failed_topics=None, candidates=None):
    """
    Full longform generation for one niche. Returns script_data (or None).
    `failed_topics` is mutated so callers' retries skip rejected topics.
    """
    failed_topics = failed_topics if failed_topics is not None else []
    niche = LONGFORM_NICHES[niche_id]
    category = niche["label"]
    print(f"🎬 [LONGFORM] Generating longform script — niche: {category}")

    from gemini_script import is_offline_mode_active
    if is_offline_mode_active():
        print("🔴 [LONGFORM] Offline mode active — skipping longform generation.")
        return None

    candidates = [c for c in (candidates or discover_topics(niche, failed_topics))
                  if not any(ft and ft.lower() in c["title"].lower() for ft in failed_topics)]
    if not candidates:
        print("❌ [LONGFORM] No candidate topics available.")
        return None

    verified, report = None, None
    for cand in candidates[:3]:
        ok, checked, rep = fact_check_topic(cand, niche)
        if ok:
            verified, report = checked, rep
            break
        failed_topics.append(cand.get("title"))
    if not verified:
        print("❌ [LONGFORM] No candidate passed the fact-check gate.")
        return None

    chapters = write_script(verified, niche, word_range, category=category)
    if not chapters:
        print("❌ [LONGFORM] Script writer failed.")
        failed_topics.append(verified.get("title"))
        return None
    script_text = "\n\n".join(c["text"] for c in chapters)
    print(f"📝 [LONGFORM] Script: {word_count(script_text)} words, {len(chapters)} chapters: "
          f"{[c['title'] for c in chapters]}")

    scenes = split_into_scenes(chapters)
    chunks, phonetic = plan_visuals(scenes, verified, niche, category=category)
    meta = generate_metadata(verified, niche, chapters[0]["text"], category=category)

    title_variants = meta["title_variants"]
    source_urls = verified.get("source_urls", [])
    script_data = {
        "format": FORMAT_ID,
        "is_longform": True,
        "niche": niche_id,
        "title": title_variants[0],
        "title_variants": title_variants,
        "script": script_text,
        "chapters": chapters,
        "hook": chapters[0]["text"],
        "subtitle_chunks": chunks,
        "description": meta["description"],
        "hashtags": meta["hashtags"],
        "keywords": meta["keywords"],
        "thumbnail_text": meta["thumbnail_text"],
        "summary": verified.get("premise", ""),
        "sub_category": category,
        "unique_angle": verified.get("premise", ""),
        "comment_hook": "",
        "comment_bait_question": meta["comment_bait_question"],
        "phonetic_pronunciation_map": phonetic,
        "original_news_headline": verified.get("title"),
        "original_news_url": source_urls[0] if source_urls else "",
        "use_case_evidence_url": source_urls[0] if source_urls else "",
        "source_urls": source_urls,
        "relevant_links": source_urls,
        "visual_subjects": verified.get("visual_subjects", []),
        "key_facts": verified["key_facts"],
        "accent_color": niche["accent"],
        "fact_check": {
            "verdict": (report or {}).get("overall_verdict"),
            "confidence": (report or {}).get("confidence"),
            "notes": (report or {}).get("notes"),
            "verified_fact_count": len(verified["key_facts"]),
        },
    }
    print(f"🎉 [LONGFORM] Ready: '{script_data['title']}' — {len(chunks)} scenes across {len(chapters)} chapters.")
    return script_data


if __name__ == "__main__":
    import argparse
    from longform_niches import get_niche_for_today, LONGFORM_DURATION_BOUNDS

    parser = argparse.ArgumentParser(description="Preview a longform script (no audio/video/upload).")
    parser.add_argument("--niche", type=str, default=None, choices=list(LONGFORM_NICHES))
    args = parser.parse_args()

    _, nid, _ = get_niche_for_today(args.niche)
    wr = words_range_for_duration(DEFAULT_WORDS_PER_SEC, LONGFORM_DURATION_BOUNDS[0] + 10, LONGFORM_DURATION_BOUNDS[1] - 8)
    data = generate_longform_script(nid, wr)
    if data:
        print(json.dumps({
            "title": data["title"], "chapters": data["chapters"], "fact_check": data["fact_check"],
            "sources": data["source_urls"], "hashtags": data["hashtags"],
            "scenes": [(c["plan"], c["text"][:50], c["stock_search_query"]) for c in data["subtitle_chunks"]],
        }, ensure_ascii=False, indent=2))
