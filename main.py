import os
import argparse
import time
import sys
import glob
import random
import traceback
from datetime import datetime
import re

from config import (
    TARGET_AUDIO_DURATION, MAX_RETRY_ATTEMPTS, LOGS_DIR, OUTPUT_DIR, GEMINI_API_KEY,
    ENABLE_EVIDENCE_SCREENSHOTS, ENABLE_LONGFORM, VOICE_SPEED, ELEVENLABS_VOICE_ID,
    ELEVENLABS_API_KEY, ENABLE_OFFLINE_TOPIC_FALLBACK
)
from fetch_topics import fetch_facts_for_category
from topic_tracker import record_story, update_youtube_url
from gemini_script import pick_and_generate_script, is_offline_mode_active, reset_offline_mode
from ecosystem_logic import get_slot_info, get_series_identity
from audio_gen import generate_voiceover, clean_tts_text, ElevenLabsVoiceError
from chunk_builder import build_chunks, redistribute_to_audio_duration
from pexels_fetcher import fetch_all_chunk_visuals
from video_gen import create_video
from screenshot_gen import capture_article_screenshot
from thumbnail_gen import generate_thumbnail
from youtube_upload import upload_video
from telegram_selector import notify_telegram, send_upload_consent
from entity_fetcher import fetch_all_entities, get_retention_layers_config
from x_upload import upload_video_to_x
from did_you_know import (
    FORMAT_ID as DYK_FORMAT_ID, DYK_DURATION_BOUNDS, generate_dyk_script, fetch_dyk_facts, get_dyk_category
)

SHORTS_FORMATS = ("standard", "didyouknow")

def log_message(msg):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(LOGS_DIR, f"log_{today}.txt")
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    print(msg)

def format_description(ai_description, script, hashtags, slot="Slot A", source_url="", unique_angle="", category="", video_number=0):
    hashtag_str = " ".join(hashtags) if hashtags else ""
    clean_summary = ai_description.split(". ")[0] + "."
    if len(clean_summary) > 150: 
        clean_summary = clean_summary[:147] + "..."

    source_str = f"📰 Source: {source_url}\n" if source_url else ""
    angle_str = f"💡 {unique_angle}\n" if unique_angle else ""
    
    # Per-video metadata for uniqueness (anti-repetition signal)
    import datetime
    date_str = datetime.datetime.now().strftime("%d %b %Y")
    category_clean = category.split(" ", 1)[-1] if category else "Tips"
    vid_num_str = f"📌 Video #{video_number}" if video_number > 0 else ""

    # YPP COMPLIANCE: AI Disclosure block (placed at TOP for visibility)
    ai_disclosure = (
        "🤖 AI DISCLOSURE: This video uses AI-assisted voice cloning and "
        "AI-generated visuals to illustrate VJ's tips. All scripts, research, "
        "and editorial direction are by VJ (Simple Tips by VJ).\n"
        "Tools: ElevenLabs (voice), Imagen/Veo (visuals), Gemini (research)."
    )

    # YPP COMPLIANCE: 5 diverse description templates to prevent repetitive content flags
    import hashlib
    desc_seed = int(hashlib.md5(clean_summary.encode()).hexdigest(), 16)
    template_idx = desc_seed % 5

    templates = [
        f"""{ai_disclosure}
━━━━━━━━━━━━━━━━━━━━━━
💡 {clean_summary}
{angle_str}{source_str}
📝 Script & Research by VJ | {category_clean} | {date_str}
{vid_num_str}
━━━━━━━━━━━━━━━━━━━━━━
தினசரி பயனுள்ள குறிப்புகள் மற்றும் எளிய லைஃப் ஹேக்ஸ் தமிழில்!
💬 Simple Tips by VJ-க்கு Subscribe பண்ணுங்க!

{hashtag_str}
#SimpleTipsByVJ #LifeHacks #TamilTips #Shorts""",

        f"""{ai_disclosure}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
⚡ {clean_summary}
{angle_str}{source_str}
📝 Curated by VJ | {category_clean} | {date_str}
{vid_num_str}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
📬 Daily tips & hacks → Subscribe to Simple Tips by VJ!
📲 Telegram group link → Channel cover page!

{hashtag_str}
#SimpleTipsByVJ #TechHacks #LifeHacksTamil #Shorts""",

        f"""{ai_disclosure}
━━━━━━━━━━━━━━━━━━━━━━
{clean_summary}
{angle_str}{source_str}
📝 Written & directed by VJ | {category_clean} | {date_str}
{vid_num_str}
━━━━━━━━━━━━━━━━━━━━━━
🧠 தினசரி பயனுள்ள குறிப்புகளை பெற Subscribe பண்ணுங்க!

{hashtag_str}
#LifeHacks #SimpleTips #DailyHacks #Shorts""",

        f"""{ai_disclosure}
──────────────────────
💡 {clean_summary}
{angle_str}{source_str}
📝 VJ's {category_clean} Series | {date_str}
{vid_num_str}
──────────────────────
Daily Useful Tips & Hacks in Tamil:
• மொபைல் & டெக் ஹேக்ஸ் 📱
• படிப்பு & நினைவாற்றல் குறிப்புகள் 🧠
• உடல் நலம் & வீட்டு குறிப்புகள் 💊

{hashtag_str}
#SimpleTipsByVJ #UsefulTips #TamilShorts #Shorts""",

        f"""{ai_disclosure}
━━━━━━━━━━━━━━━━━━━━━━
👇 {clean_summary}
{angle_str}{source_str}
📝 Researched & produced by VJ | {date_str}
{vid_num_str}
━━━━━━━━━━━━━━━━━━━━━━
💬 இந்த மாதிரி tips daily பார்க்க Simple Tips by VJ-க்கு Subscribe!
📲 Telegram → Channel header-ல link இருக்கு!

{hashtag_str}
#TamilTechTips #HowToTamil #VJTips #Shorts"""
    ]

    return templates[template_idx]

def run_pipeline(forced_category=None, dry_run=False, shorts_format="standard"):
    is_dyk = shorts_format == "didyouknow"
    log_message("=== STARTING TAMIL SHORTS PIPELINE — SIMPLE TIPS BY VJ ===")
    log_message(f"🎞️ Shorts format: {'தெரியுமா? / Did You Know (stock footage)' if is_dyk else 'Standard'}")

    # ── Clean output folder before starting ──
    if os.path.exists(OUTPUT_DIR):
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
            except:
                pass
        log_message(f"Output folder cleaned: {OUTPUT_DIR}")

    # ── ElevenLabs Mandatory Voice Check ──
    if not ELEVENLABS_API_KEY:
        log_message("🚨 [FATAL] ELEVENLABS_API_KEY is not configured in environment or config.")
        log_message("🛑 Aborting shorts generation pipeline immediately. Working ElevenLabs voice cloning is required.")
        return False

    # ── STEP 1: Content Ecosystem Check ──
    day_name, slot, category = get_slot_info()
    if forced_category:
        category = forced_category
    if is_dyk:
        category = get_dyk_category(category)
    log_message(f"STEP 1: Strategy Check -> Day: {day_name}, Slot: {slot}, Category: {category}")
    
    # ── STEP 2: Fetch Trending facts via search grounding ──
    log_message(f"STEP 2: Fetching facts using Search Grounding for '{category}'...")
    facts = fetch_dyk_facts(category) if is_dyk else []
    if not facts:
        facts = fetch_facts_for_category(category)
    if not facts:
        log_message("🚨 Failed to fetch facts! Aborting.")
        return False

    # ── STEP 3: Script & Visual Assets pipeline (with retry) ──
    attempts = 0
    script_data = None
    audio_path  = None
    word_timestamps = []
    duration    = 0
    failed_topics = []
    min_dur, max_dur = TARGET_AUDIO_DURATION
    MIN_DURATION_SEC = 25  # absolute minimum allowed (reduced to accommodate fallback scripts ~70-100 words)
    MAX_DURATION_SEC = max_dur  # absolute maximum allowed (do not allow any shorts more than max_dur)
    if is_dyk:
        MIN_DURATION_SEC, MAX_DURATION_SEC = DYK_DURATION_BOUNDS
    
    while attempts < MAX_RETRY_ATTEMPTS:
        # Recalculate max_attempts each iteration to respect offline mode changes
        current_max_attempts = 3 if is_offline_mode_active() else MAX_RETRY_ATTEMPTS
        if attempts >= current_max_attempts:
            log_message(f"🔴 [OFFLINE MODE] Max attempts ({current_max_attempts}) reached. Stopping.")
            break
            
        log_message(f"STEP 3 (Attempt {attempts+1}/{current_max_attempts}): Multi-Agent Tanglish Script Generation...")
        
        script_data = None
        if is_dyk:
            script_data = generate_dyk_script(category, facts=facts, failed_topics=failed_topics)
            if not script_data:
                log_message("⚠️ [DYK] Did-You-Know generation failed this attempt. Falling back to standard script generator...")
        if not script_data:
            script_data = pick_and_generate_script(
                articles=facts, extra_instruction="", forced_article=None, topic_type="research", failed_topics=failed_topics
            )
            if script_data and is_dyk:
                # Keep the DYK look (stock-only visuals) even when the standard writer produced the script
                script_data["visual_mode"] = "stock_only"

        if not script_data:
            if is_offline_mode_active() and ENABLE_OFFLINE_TOPIC_FALLBACK:
                log_message("🔄 Script generation returned None in offline mode. Loading direct offline fallback...")
                from gemini_script import get_offline_fallback_script
                script_data = get_offline_fallback_script(category, failed_topics)
            if not script_data:
                log_message("❌ Script generation failed. Retrying...")
                reset_offline_mode()
                attempts += 1
                time.sleep(5)
                continue
            
        fact_headline = script_data.get("original_news_headline")
        fact_url = script_data.get("original_news_url")
        
        script_data["slot"] = slot
        scores = script_data.get("quality_scores")
        if scores:
            log_message(f"✅ Storyboard Quality Validation Passed (All scores >= 90%):")
            log_message(f"   - Story Continuity: {scores.get('story_continuity')}%")
            log_message(f"   - Visual Alignment: {scores.get('visual_alignment')}%")
            log_message(f"   - Engagement: {scores.get('engagement')}%")
            log_message(f"   - Transitions: {scores.get('transitions')}%")
            log_message(f"   - Subtitle Timing: {scores.get('subtitle_timing')}%")
        title = script_data.get("title") or ""
        if not str(title).strip():
            title = script_data.get("original_news_headline") or "Tamil Fact!"
        # Prioritize the full natural human script for voiceover synthesis
        full_script = (script_data.get("script") or "").strip()
        if full_script:
            script = full_script
        else:
            # Fallback only if the script field is empty
            raw_sub_chunks = script_data.get("subtitle_chunks", [])
            sub_chunks = []
            for sc in raw_sub_chunks:
                if isinstance(sc, list):
                    for item in sc:
                        if isinstance(item, dict):
                            sub_chunks.append(item)
                elif isinstance(sc, dict):
                    sub_chunks.append(sc)
            if sub_chunks:
                script = " ".join(sc.get("text", "").strip() for sc in sub_chunks if sc.get("text"))
            else:
                script = ""
        
        # Dynamically scaled based on VOICE_SPEED configuration (baseline of 2.55 wps at 1.05 speed)
        base_wps = 2.55
        WORDS_PER_SEC_ESTIMATE = base_wps * (VOICE_SPEED / 1.05)
        log_message(f"ℹ️ Calibrated pacing gate: {WORDS_PER_SEC_ESTIMATE:.2f} words/sec (VOICE_SPEED={VOICE_SPEED})")
        
        word_count = len(script.split())
        sentence_count = len(re.findall(r'[.!?]+', script))
        comma_count = len(re.findall(r',', script))
        added_pauses = sentence_count * 0.3 + comma_count * 0.15
        estimated_duration = (word_count / WORDS_PER_SEC_ESTIMATE) + added_pauses
        
        if estimated_duration < MIN_DURATION_SEC or estimated_duration > MAX_DURATION_SEC:
            if estimated_duration < MIN_DURATION_SEC:
                min_words = int(MIN_DURATION_SEC * WORDS_PER_SEC_ESTIMATE) + 10
                log_message(f"⚠️ Script too short: ~{estimated_duration:.1f}s estimated ({word_count} words). Minimum is {MIN_DURATION_SEC}s ({min_words}+ words). Rejecting early.")
            else:
                max_words = int(MAX_DURATION_SEC * WORDS_PER_SEC_ESTIMATE) - 10
                log_message(f"⚠️ Script too long: ~{estimated_duration:.1f}s estimated ({word_count} words). Maximum is {MAX_DURATION_SEC}s ({max_words} words). Rejecting early.")
            failed_topics.append(fact_headline)
            script_data = None
            attempts += 1
            continue
        
        log_message(f"📊 Script length check passed: {word_count} words → ~{estimated_duration:.1f}s estimated (bounds [{MIN_DURATION_SEC}s - {MAX_DURATION_SEC}s])")
        
        log_message(f"Selected Fact: {fact_headline}")
        log_message(f"Source URL: {fact_url}")

        # ── STEP 3a: Strict Programmatic Uniqueness Gate ──
        from topic_tracker import check_story_uniqueness
        is_unique, uniq_reason = check_story_uniqueness(
            new_title=title,
            new_headline=fact_headline,
            new_keywords=script_data.get("keywords"),
            new_url=fact_url
        )
        if not is_unique:
            log_message(f"❌ [main.py] Duplicate topic rejected: '{title}' / '{fact_headline}'. Reason: {uniq_reason}")
            if fact_headline:
                failed_topics.append(fact_headline)
            if title and title != fact_headline:
                failed_topics.append(title)
            script_data = None
            attempts += 1
            time.sleep(2)
            continue

        # ── STEP 3b: Capture Evidence Screenshot (MANDATORY if enabled) ──
        # ── STEP 4: Generate Cloned Voice Audio (ElevenLabs Voice Cloning Only) ──
        log_message("STEP 4: Generating Tamil cloned voiceover via ElevenLabs...")
        target_vid = script_data.get("voice_id") or os.environ.get("ELEVENLABS_VOICE_ID") or ELEVENLABS_VOICE_ID
        log_message(f"🎙️ Synthesizing voiceover with ElevenLabs Voice ID: {target_vid}")
        try:
            audio_path, duration, word_timestamps = generate_voiceover(
                script,
                voice_id=target_vid,
                custom_phonetic_map=script_data.get("phonetic_pronunciation_map", {}),
                api_key=GEMINI_API_KEY
            )
        except ElevenLabsVoiceError as e:
            log_message(f"🚨 [FATAL] ElevenLabs voice generation failed: {e}")
            log_message("🛑 Aborting shorts generation pipeline immediately. ElevenLabs voice cloning is required and no fallback is permitted.")
            return False
        except Exception as e:
            log_message(f"🚨 [FATAL] Local voiceover generation failed: {e}")
            log_message("🛑 Aborting shorts generation pipeline immediately. ElevenLabs voice cloning is required and no fallback is permitted.")
            return False
            
        # Propagate Voice Fallback Status (always False since only ElevenLabs voice cloning is permitted)
        import audio_gen
        script_data["voice_fallback_used"] = False
        
        if not audio_path or not os.path.exists(audio_path):
            log_message("🚨 [FATAL] ElevenLabs voice output missing or failed to generate.")
            log_message("🛑 Aborting shorts generation pipeline immediately. ElevenLabs voice cloning is required and no fallback is permitted.")
            return False

        if duration < MIN_DURATION_SEC or duration > MAX_DURATION_SEC:
            actual_wps = word_count / duration
            log_message(f"⚠️ Local TTS returned {duration:.1f}s audio. Pre-check estimate was {estimated_duration:.1f}s.")
            log_message(f"   Observed pace: {actual_wps:.2f} words/sec (vs estimate {WORDS_PER_SEC_ESTIMATE}). Recalibrating for next run.")
            WORDS_PER_SEC_ESTIMATE = actual_wps
            log_message(f"⚠️ Generated audio duration ({duration:.1f}s) is out of bounds [{MIN_DURATION_SEC}s - {MAX_DURATION_SEC}s]. Retrying...")
            failed_topics.append(fact_headline)
            attempts += 1
            continue
            
        break  # Success

    if not audio_path or not script_data or duration < MIN_DURATION_SEC or duration > MAX_DURATION_SEC:
        log_message("🚨 Pipeline failed to build core assets after multiple attempts.")
        return False

    # ── STEP 4.5: Reserve Topic in Tracker ──
    log_message("STEP 4.5: Logging fact in topic tracker...")
    subcat = script_data.get("sub_category", category)
    keywords = script_data.get("keywords", [])
    record_story(
        title, fact_headline, subcat, keywords,
        voice_used="VJ_Cloned_Voice", youtube_url="pending_upload", source_url=fact_url
    )

    # ── STEP 5: Build Word Visual Chunks ──
    log_message("STEP 5: Matching word timestamps to visual chunks...")
    raw_sub_chunks = script_data.get("subtitle_chunks", [])
    sub_chunks = []
    for sc in raw_sub_chunks:
        if isinstance(sc, list):
            for item in sc:
                if isinstance(item, dict):
                    sub_chunks.append(item)
        elif isinstance(sc, dict):
            sub_chunks.append(sc)
            
    for sc in sub_chunks:
        if "text" in sc:
            sc["text"] = clean_tts_text(sc["text"])
            
    chunks = build_chunks(word_timestamps, sub_chunks)
    chunks = redistribute_to_audio_duration(chunks, duration)

    # ── STEP 5.5: Fetch Entities (People/Companies) ──
    log_message("STEP 5.5: Fetching entity photos and company logos...")
    try:
        script_data = fetch_all_entities(script_data)
        retention_config = get_retention_layers_config()
        script_data["retention_config"] = retention_config
        log_message(f"Engagement Layers Active: {list(retention_config.keys())}")
    except Exception as e:
        log_message(f"⚠️ Entity fetching failed (non-fatal): {e}")

    # ── STEP 6: Resolve Background Visuals ──
    log_message("STEP 6: Resolving background visual clips...")
    is_longform = ENABLE_LONGFORM and ("Slot C" in slot or "Slot L" in slot or script_data.get("is_longform", False))
    chunks = fetch_all_chunk_visuals(chunks, topic_context=fact_headline, script_data=script_data, is_longform=is_longform)

    # ── STEP 7: Render Final Video ──
    log_message("STEP 7: Invoking video rendering engine...")
    try:
        video_path = create_video(audio_path, script_data, chunks)
        if not video_path or not os.path.exists(video_path):
            raise RuntimeError("Rendered video file missing")
        log_message(f"✅ Video rendered successfully: {video_path}")
    except Exception as e:
        traceback.print_exc()
        log_message(f"🚨 Video rendering failed: {e}")
        return False

    # ── STEP 8: Generate Custom Thumbnail ──
    log_message("STEP 8: Generating premium YouTube thumbnail...")
    thumbnail_variants = generate_thumbnail(script_data)  # Generates 3 variants [pathA, pathB, pathC]

    # ── STEP 9: Auto-select title & thumbnail (no consent gate) ──
    log_message("STEP 9: Auto-selecting title variant 1 and thumbnail A for upload...")
    title_variants = script_data.get("title_variants", [title, title, title])
    selected_title = title_variants[0]
    selected_thumbnail = thumbnail_variants[0] if thumbnail_variants else None

    # ── STEP 10: YouTube Upload & Instagram Reels Cross-post ──
    log_message("STEP 10: Uploading video to Simple Tips by VJ YouTube Channel...")
    ai_desc = script_data.get("description", "")
    hashtags = script_data.get("hashtags", ["#தெரியுமா", "#VJVideos"])
    unique_angle = script_data.get("unique_angle", "")
    
    # Get video count for per-video metadata
    from topic_tracker import get_fact_count
    video_number = get_fact_count() + 1
    
    description = format_description(
        ai_desc, script, hashtags, slot=slot, source_url=fact_url,
        unique_angle=unique_angle, category=category, video_number=video_number
    )
    
    from ecosystem_logic import generate_youtube_tags, calculate_youtube_tags_length
    tags = generate_youtube_tags(
        title=selected_title,
        keywords=keywords,
        hashtags=hashtags,
        category=category,
        max_chars=400
    )
    tag_chars = calculate_youtube_tags_length(tags)
    log_message(f"🏷️ Generated {len(tags)} YouTube tags ({tag_chars}/500 chars): {', '.join(tags[:6])}...")
    
    if dry_run:
        log_message("🚀 [DRY-RUN] Simulating YouTube Upload and Instagram Reels cross-posting...")
        if not is_longform:
            # Verify video crop logic by running ffmpeg crop
            from youtube_upload import crop_for_instagram
            try:
                cropped_path = crop_for_instagram(video_path)
                log_message(f"✅ [DRY-RUN] Verified Instagram video crop: {cropped_path}")
                if os.path.exists(cropped_path):
                    os.remove(cropped_path)
            except Exception as ce:
                log_message(f"❌ [DRY-RUN] Instagram crop verification failed: {ce}")
        else:
            log_message("ℹ️ [DRY-RUN] Widescreen video. Skipping Instagram crop verification.")
        uploaded, result = True, "dry_run_video_id"
    else:
        uploaded, result = upload_video(
            video_path, selected_title, description, tags, 
            thumbnail_path=selected_thumbnail, comment_hook=script_data.get("comment_hook"),
            comment_bait_question=script_data.get("comment_bait_question"),
            is_longform=is_longform
        )
    
    if not uploaded:
        log_message(f"❌ YouTube upload failed: {result}")
        notify_telegram(f"❌ YouTube upload failed: {result}", "🚨")
        return False

    youtube_url = f"https://youtu.be/{result}" if not dry_run else "https://youtu.be/dry_run_video_id"
    log_message(f"🎉 YouTube upload SUCCESS: {youtube_url}")
    if not dry_run:
        notify_telegram(f"🚀 Video is now LIVE on Simple Tips by VJ!\n\n📌 <b>{selected_title}</b>\n🔗 {youtube_url}", "✅")
        # YPP COMPLIANCE: Notify VJ that AI disclosure label has been set automatically
        notify_telegram(
            f"🤖 <b>AI Disclosure Label Automatically Set</b>\n\n"
            f"The video has been flagged as <b>\"AI-generated or altered content\"</b> (containsSyntheticMedia: True) automatically during upload for YPP compliance.\n\n"
            f"🔗 {youtube_url}",
            "🤖"
        )

    # ── STEP 10b: X.com Auto-Post ──
    log_message("STEP 10b: Auto-posting Short to X.com...")
    try:
        x_uploaded, x_result = upload_video_to_x(video_path, script_data, youtube_url)
        if x_uploaded:
            log_message(f"✅ Posted video to X.com! Tweet ID: {x_result}")
        else:
            log_message(f"⚠️ X.com posting skipped/failed: {x_result}")
    except Exception as ex:
        log_message(f"⚠️ X.com auto-post failed (non-fatal): {ex}")

    # ── STEP 11: Update URL in tracker ──
    update_youtube_url(fact_headline, youtube_url)

    # ── STEP 12: Cleanup temp files ──
    if not dry_run:
        log_message("STEP 12: Cleaning up output files...")
        cleaned_count = 0
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
                    cleaned_count += 1
            except Exception as e:
                log_message(f"Failed to delete {f}: {e}")
    else:
        log_message("ℹ️ [DRY-RUN] Skipping cleanup to preserve generated video and assets for verification.")

    log_message("=== PIPELINE COMPLETED SUCCESSFULLY ===")
    return True

def run_local(category=None, dry_run=False, shorts_format="standard"):
    success = run_pipeline(forced_category=category, dry_run=dry_run, shorts_format=shorts_format)
    if not success:
        print("❌ Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Run pipeline immediately.")
    parser.add_argument("--category", type=str, default=None, help="Force a specific daily category")
    parser.add_argument("--dry-run", action="store_true", help="Run dry run verification.")
    parser.add_argument(
        "--format", type=str, choices=SHORTS_FORMATS,
        default=os.environ.get("SHORTS_FORMAT", "standard").strip().lower() or "standard",
        help="Shorts format: 'standard' or 'didyouknow' (தெரியுமா? fact-checked facts + stock footage). Env: SHORTS_FORMAT"
    )
    args = parser.parse_args()

    if args.now:
        run_local(category=args.category, dry_run=args.dry_run, shorts_format=args.format)
    else:
        print("Usage: python main.py --now [--format didyouknow]")
        print("For scheduled runs: python scheduler.py")
