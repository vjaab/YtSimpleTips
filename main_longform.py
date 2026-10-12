# -*- coding: utf-8 -*-
"""
main_longform.py — 2-3 Minute Widescreen Tamil Explainer Video Pipeline for "Simple Tips by VJ".

Independent pipeline parallel to the Shorts pipeline (main.py):
- 120-180 seconds duration (target: 150s)
- 16:9 1080p landscape format
- 7 viral infotainment niches on a daily rotation (Mystery, Tamil Heritage, Space & Science, Psychology, What If, Smart Living, Nature/Body)
- Chaptered narrative structure (5-6 story beats)
- Mix of stock video b-roll, 16:9 AI visuals, animated data cards, and website evidence screenshots
- Native ElevenLabs cloned voice
- Uploads to YouTube as UNLISTED (or PRIVATE) so you can review in YouTube Studio first
- Telegram notifications with review link
"""

import os
import sys
import glob
import time
import argparse
import traceback
from datetime import datetime
import pytz

from config import (
    LOGS_DIR, OUTPUT_DIR, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    ELEVENLABS_PRESERVE_ORIGINAL_VOICE, VOICE_SPEED, GEMINI_API_KEY,
    TIMEZONE, MAX_RETRY_ATTEMPTS
)
from longform_niches import (
    LONGFORM_NICHES, LONGFORM_DURATION_BOUNDS, LONGFORM_TARGET_SECONDS,
    get_niche_for_today
)
from longform_script import (
    generate_longform_script, words_range_for_duration, DEFAULT_WORDS_PER_SEC
)
from longform_visuals import (
    resolve_longform_visuals, generate_longform_thumbnails
)
from longform_video import create_longform_video
from audio_gen import generate_voiceover, clean_tts_text, ElevenLabsVoiceError
from chunk_builder import build_chunks, redistribute_to_audio_duration
from topic_tracker import record_story, update_youtube_url, check_story_uniqueness
from telegram_selector import notify_telegram
from youtube_upload import upload_video
from ecosystem_logic import generate_youtube_tags, calculate_youtube_tags_length


def log_message(msg):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(LOGS_DIR, f"log_longform_{today}.txt")
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    print(msg)


def format_longform_description(script_data, chapters, source_urls):
    """Formats rich longform description with timestamps, source citations, and AI disclosure."""
    premise = script_data.get("description", "").strip()
    hashtags = " ".join(script_data.get("hashtags", []))
    date_str = datetime.now().strftime("%d %b %Y")
    niche_label = script_data.get("sub_category", "Infotainment")

    # AI Disclosure block (at top for YPP compliance)
    ai_disclosure = (
        "🤖 AI DISCLOSURE: This video uses AI-assisted voice cloning and "
        "AI-generated visuals to illustrate VJ's educational explainer. All scripts, research, "
        "and editorial direction are by VJ (Simple Tips by VJ).\n"
        "Tools: ElevenLabs (voice), Imagen/Veo (visuals), Gemini (grounded research)."
    )

    # Chapters list if timestamps are populated later or chapter titles
    chapter_lines = []
    for idx, ch in enumerate(chapters):
        chapter_lines.append(f"• Part {idx + 1}: {ch.get('title', '')}")
    chapters_str = "\n".join(chapter_lines)

    # Source citations
    source_lines = [f"🔗 {u}" for u in (source_urls or []) if u]
    sources_str = "\n".join(source_lines) if source_lines else "Logged in verification registry."

    desc = f"""{ai_disclosure}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 {premise}

📑 CHAPTERS IN THIS VIDEO:
{chapters_str}

📰 VERIFIED SOURCES & REFERENCES:
{sources_str}

📝 Researched & Narrated by VJ | {niche_label} | {date_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
தினசரி பயனுள்ள ஆழமான குறிப்புகள் மற்றும் மர்மங்கள் தமிழில்!
💬 Simple Tips by VJ சேனலுக்கு Subscribe பண்ணுங்க!

{hashtags}
#SimpleTipsByVJ #TamilExplainer #TamilDocumentary"""
    return desc.strip()


def run_longform_pipeline(forced_niche=None, dry_run=False, privacy_status="unlisted"):
    log_message("=== STARTING 2-3 MINUTE TAMIL LONGFORM PIPELINE — SIMPLE TIPS BY VJ ===")
    
    # ── Clean output folder before starting ──
    if os.path.exists(OUTPUT_DIR):
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
            except Exception:
                pass
        log_message(f"Output folder cleaned: {OUTPUT_DIR}")

    # ── ElevenLabs Mandatory Voice Check ──
    if not ELEVENLABS_API_KEY:
        log_message("🚨 [FATAL] ELEVENLABS_API_KEY is not configured in environment or config.")
        log_message("🛑 Aborting longform pipeline immediately. Working ElevenLabs voice cloning is required.")
        return False

    # ── STEP 1: Content Strategy & Niche Selection ──
    day_name, niche_id, niche = get_niche_for_today(forced=forced_niche)
    log_message(f"STEP 1: Niche Selection -> Day: {day_name}, Niche: {niche['label']} ({niche_id})")

    min_dur, max_dur = LONGFORM_DURATION_BOUNDS
    base_wps = DEFAULT_WORDS_PER_SEC
    WORDS_PER_SEC_ESTIMATE = base_wps * (VOICE_SPEED / 1.0)
    word_range = words_range_for_duration(WORDS_PER_SEC_ESTIMATE, min_dur + 5, max_dur - 5)
    log_message(f"ℹ️ Target narration length: {min_dur}s - {max_dur}s (~{word_range[0]}-{word_range[1]} words at {WORDS_PER_SEC_ESTIMATE:.2f} wps)")

    # ── STEP 2: Script Generation & Fact-Check Loop ──
    attempts = 0
    script_data = None
    audio_path = None
    word_timestamps = []
    duration = 0
    failed_topics = []

    while attempts < MAX_RETRY_ATTEMPTS:
        attempts += 1
        log_message(f"STEP 2 (Attempt {attempts}/{MAX_RETRY_ATTEMPTS}): Researching & Generating Chaptered Script...")
        
        script_data = generate_longform_script(niche_id, word_range, failed_topics=failed_topics)
        if not script_data:
            log_message("❌ Script generation or fact-checking failed for this candidate. Retrying with a new topic...")
            time.sleep(3)
            continue

        headline = script_data.get("original_news_headline", "")
        title = script_data.get("title", "")
        source_url = script_data.get("original_news_url", "")

        # ── STEP 2a: Strict Topic Uniqueness Check ──
        is_unique, uniq_reason = check_story_uniqueness(
            new_title=title,
            new_headline=headline,
            new_keywords=script_data.get("keywords"),
            new_url=source_url
        )
        if not is_unique:
            log_message(f"❌ Duplicate topic rejected: '{title}'. Reason: {uniq_reason}")
            failed_topics.append(title)
            if headline:
                failed_topics.append(headline)
            script_data = None
            time.sleep(2)
            continue

        # ── STEP 3: Voiceover Synthesis with ElevenLabs Cloned Voice ──
        log_message(f"STEP 3: Synthesizing ~{LONGFORM_TARGET_SECONDS}s voiceover with ElevenLabs...")
        full_script = script_data.get("script", "").strip()
        word_count = len(full_script.split())
        log_message(f"🎙️ Script word count: {word_count} words")

        target_vid = os.environ.get("ELEVENLABS_VOICE_ID") or ELEVENLABS_VOICE_ID
        try:
            audio_path, duration, word_timestamps = generate_voiceover(
                full_script,
                voice_id=target_vid,
                custom_phonetic_map=script_data.get("phonetic_pronunciation_map", {}),
                api_key=GEMINI_API_KEY
            )
        except ElevenLabsVoiceError as e:
            log_message(f"🚨 [FATAL] ElevenLabs voice generation failed: {e}")
            return False
        except Exception as e:
            log_message(f"🚨 [FATAL] Voiceover generation failed: {e}")
            return False

        if not audio_path or not os.path.exists(audio_path):
            log_message("🚨 [FATAL] ElevenLabs voice output missing.")
            return False

        log_message(f"⏱️ Generated audio duration: {duration:.1f}s (Bounds: [{min_dur}s - {max_dur}s])")

        # Duration validation
        if duration < min_dur or duration > max_dur:
            log_message(f"⚠️ Audio duration ({duration:.1f}s) outside allowed [{min_dur}s - {max_dur}s] range.")
            failed_topics.append(headline or title)
            script_data = None
            continue

        break  # Success

    if not audio_path or not script_data or duration < min_dur or duration > max_dur:
        log_message("🚨 Failed to produce verified script and voiceover after maximum retries.")
        return False

    # ── STEP 4: Reserve Topic in Tracker ──
    log_message("STEP 4: Reserving story in topic tracker...")
    record_story(
        title, headline, script_data.get("sub_category", niche["label"]),
        script_data.get("keywords", []),
        voice_used="VJ_Cloned_Voice_Longform",
        youtube_url="pending_upload",
        source_url=source_url
    )

    # ── STEP 5: Align Word Timestamps to Visual Scenes ──
    log_message("STEP 5: Aligning word timestamps to visual scenes...")
    sub_chunks = script_data.get("subtitle_chunks", [])
    for sc in sub_chunks:
        if "text" in sc:
            sc["text"] = clean_tts_text(sc["text"])

    chunks = build_chunks(word_timestamps, sub_chunks)
    chunks = redistribute_to_audio_duration(chunks, duration)
    log_message(f"✅ Chunks aligned: {len(chunks)} visual scenes spanning {duration:.1f}s")

    # ── STEP 6: Resolve 16:9 Landscape Visuals ──
    log_message("STEP 6: Resolving 16:9 visuals (Pexels video, AI stills, cards, screenshots)...")
    chunks = resolve_longform_visuals(chunks, script_data)

    # ── STEP 7: Render 1920x1080 Widescreen Video ──
    log_message("STEP 7: Invoking 16:9 widescreen video rendering engine...")
    try:
        video_path = create_longform_video(audio_path, script_data, chunks)
        if not video_path or not os.path.exists(video_path):
            raise RuntimeError("Rendered MP4 file missing")
        log_message(f"✅ 16:9 Video rendered successfully: {video_path}")
    except Exception as e:
        traceback.print_exc()
        log_message(f"🚨 Video rendering failed: {e}")
        return False

    # ── STEP 8: Generate Custom 16:9 Thumbnails ──
    log_message("STEP 8: Generating custom 16:9 documentary thumbnails...")
    thumbnail_variants = generate_longform_thumbnails(script_data)
    selected_thumbnail = thumbnail_variants[0] if thumbnail_variants else None

    # ── STEP 9: Title & Metadata Preparation ──
    title_variants = script_data.get("title_variants", [title])
    selected_title = title_variants[0]
    description = format_longform_description(
        script_data, script_data.get("chapters", []), script_data.get("source_urls", [])
    )
    
    tags = generate_youtube_tags(
        title=selected_title,
        keywords=script_data.get("keywords", []),
        hashtags=script_data.get("hashtags", []),
        category=niche["label"],
        max_chars=400
    )
    tag_chars = calculate_youtube_tags_length(tags)
    log_message(f"🏷️ Generated {len(tags)} YouTube tags ({tag_chars}/500 chars)")

    # ── STEP 10: Upload to YouTube (as UNLISTED / PRIVATE for Review) ──
    log_message(f"STEP 10: Uploading 16:9 video to YouTube (Privacy: {privacy_status})...")
    if dry_run:
        log_message("🚀 [DRY-RUN] Simulating YouTube upload (files preserved for inspection)...")
        uploaded, result = True, "dry_run_longform_id"
    else:
        uploaded, result = upload_video(
            video_path,
            selected_title,
            description,
            tags,
            thumbnail_path=selected_thumbnail,
            comment_bait_question=script_data.get("comment_bait_question"),
            is_longform=True,
            privacy_status=privacy_status
        )

    if not uploaded:
        log_message(f"❌ YouTube upload failed: {result}")
        notify_telegram(f"❌ Longform YouTube upload failed: {result}", "🚨")
        return False

    youtube_url = f"https://youtu.be/{result}" if not dry_run else "https://youtu.be/dry_run_longform_id"
    log_message(f"🎉 Longform YouTube upload SUCCESS: {youtube_url} ({privacy_status.upper()})")

    # ── STEP 11: Telegram Notification (Review Prompt) ──
    if not dry_run:
        review_msg = (
            f"🎬 <b>New Longform Video Uploaded ({privacy_status.upper()})</b>\n\n"
            f"📌 <b>{selected_title}</b>\n"
            f"⏱️ Duration: {duration:.1f}s ({duration/60:.2f} mins)\n"
            f"🏷️ Niche: {niche['label']}\n\n"
            f"👀 <b>Review in YouTube Studio:</b>\n🔗 {youtube_url}\n\n"
            f"<i>Uploaded as {privacy_status.upper()} so you can review before setting to Public!</i>"
        )
        notify_telegram(review_msg, "🎬")

    # ── STEP 12: Update URL in Tracker ──
    update_youtube_url(headline or title, youtube_url)

    # ── STEP 13: Cleanup temp files ──
    if not dry_run:
        log_message("STEP 13: Cleaning up temporary render files...")
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
            except Exception:
                pass
    else:
        log_message("ℹ️ [DRY-RUN] Preserving output directory files for verification.")

    log_message("=== LONGFORM PIPELINE COMPLETED SUCCESSFULLY ===")
    return True


def run_local(niche=None, dry_run=False, privacy="unlisted"):
    success = run_longform_pipeline(forced_niche=niche, dry_run=dry_run, privacy_status=privacy)
    if not success:
        print("❌ Longform pipeline failed.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2-3 Minute Tamil Longform Explainer Pipeline.")
    parser.add_argument("--now", action="store_true", help="Run longform pipeline immediately.")
    parser.add_argument(
        "--niche", type=str, default=None, choices=list(LONGFORM_NICHES.keys()),
        help=f"Force a specific niche: {list(LONGFORM_NICHES.keys())}"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate without uploading to YouTube.")
    parser.add_argument(
        "--privacy", type=str, choices=["unlisted", "private", "public"],
        default=os.environ.get("LONGFORM_PRIVACY", "unlisted").strip().lower() or "unlisted",
        help="YouTube upload privacy status (default: 'unlisted' for manual review)"
    )
    args = parser.parse_args()

    if args.now:
        run_local(niche=args.niche, dry_run=args.dry_run, privacy=args.privacy)
    else:
        print("Usage: python main_longform.py --now [--niche space_science] [--privacy unlisted] [--dry-run]")
        print("Available niches:")
        for nid, info in LONGFORM_NICHES.items():
            print(f"  • {nid:18}: {info['label']}")
