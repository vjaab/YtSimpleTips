import os
import argparse
import time
import sys
import glob
import random
import traceback
from datetime import datetime

from config import TARGET_AUDIO_DURATION, MAX_RETRY_ATTEMPTS, LOGS_DIR, OUTPUT_DIR, GEMINI_API_KEY
from fetch_topics import fetch_facts_for_category
from topic_tracker import record_story, update_youtube_url
from gemini_script import pick_and_generate_script
from ecosystem_logic import get_slot_info, get_series_identity
from audio_gen import generate_voiceover, clean_tts_text
from chunk_builder import build_chunks, redistribute_to_audio_duration
from pexels_fetcher import fetch_all_chunk_visuals
from video_gen import create_video
from screenshot_gen import capture_article_screenshot
from thumbnail_gen import generate_thumbnail
from youtube_upload import upload_video
from telegram_selector import notify_telegram, send_upload_consent

def log_message(msg):
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(LOGS_DIR, f"log_{today}.txt")
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(log_path, "a", encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    print(msg)

def format_description(ai_description, script, hashtags, slot="Slot A", source_url=""):
    hashtag_str = " ".join(hashtags) if hashtags else ""
    clean_summary = ai_description.split(". ")[0] + "."
    if len(clean_summary) > 150: 
        clean_summary = clean_summary[:147] + "..."

    source_str = f"📰 SOURCE FACTS: {source_url}\n" if source_url else ""

    # YPP COMPLIANCE: Diverse Description Templates
    import hashlib
    desc_seed = int(hashlib.md5(clean_summary.encode()).hexdigest(), 16)
    template_idx = desc_seed % 3

    templates = [
        f"""தினசரி பயனுள்ள குறிப்புகள் மற்றும் எளிய லைஃப் ஹேக்ஸ் தமிழில்! 💡 சப்ஸ்கிரைப் பண்ணுங்க!
🚀 JOIN TELEGRAM GROUP → Channel Page-ல Link இருக்கு!
━━━━━━━━━━━━━━━━━━━━━━
💡 {clean_summary}
━━━━━━━━━━━━━━━━━━━━━━
{source_str}━━━━━━━━━━━━━━━━━━━━━━
Daily Useful Tips & Hacks:
• மொபைல் & டெக் ஹேக்ஸ் 📱
• படிப்பு & நினைவாற்றல் குறிப்புகள் 🧠
• உடல் நலம் & வீட்டு குறிப்புகள் 💊

Join our community!
💬 Simple Tips by VJ-க்கு சப்ஸ்கிரைப் பண்ணுங்க!

⚠️ DISCLOSURE: This video is a curated tutorial by VJ. Scripting, editing direction, and research are managed by VJ. AI-assisted voice cloning (vj.wav) and visual generation tools are utilized to illustrate VJ's tips.

{hashtag_str}
#SimpleTipsByVJ #LifeHacks #TamilTips #HowTo #UsefulTips #Shorts""",

        f"""⚡ {clean_summary}
{source_str}
▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
📬 பயனுள்ள குறிப்புகள் மற்றும் ஹேக்ஸ் தினமும் பார்க்க சப்ஸ்கிரைப் பண்ணுங்க:
→ Telegram Group-ல சேர channel cover-ல இருக்கற link-ஐ கிளிக் பண்ணுங்க!

⚠️ DISCLOSURE: This video is a curated tutorial by VJ. Scripting, editing direction, and research are managed by VJ. AI-assisted voice cloning (vj.wav) and visual generation tools are utilized to illustrate VJ's tips.

{hashtag_str}
#SimpleTipsByVJ #TechHacks #LifeHacksTamil #HowToTamil #Shorts""",

        f"""இன்னைக்கு ஒரு பயனுள்ள டிப் பார்க்கலாம்! 👇 {clean_summary}
{source_str}
━━━━━━━━━━━━━━━━━━━━━━
🧠 தினசரி பயனுள்ள குறிப்புகளை பெற Simple Tips by VJ-க்கு சப்ஸ்கிரைப் பண்ணுங்க!
📲 Telegram group link profile home page-ல இருக்கு!

⚠️ DISCLOSURE: This video is a curated tutorial by VJ. Scripting, editing direction, and research are managed by VJ. AI-assisted voice cloning (vj.wav) and visual generation tools are utilized to illustrate VJ's tips.

{hashtag_str}
#LifeHacks #SimpleTips #StudyTips #HealthHacks #DailyHacks #Shorts"""
    ]

    return templates[template_idx]

def run_pipeline(forced_category=None):
    log_message("=== STARTING TAMIL SHORTS PIPELINE — SIMPLE TIPS BY VJ ===")

    # ── Clean output folder before starting ──
    if os.path.exists(OUTPUT_DIR):
        for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
            try:
                if os.path.isfile(f):
                    os.remove(f)
            except:
                pass
        log_message(f"Output folder cleaned: {OUTPUT_DIR}")

    # ── STEP 1: Content Ecosystem Check ──
    day_name, slot, category = get_slot_info()
    if forced_category:
        category = forced_category
    log_message(f"STEP 1: Strategy Check -> Day: {day_name}, Slot: {slot}, Category: {category}")
    
    # ── STEP 2: Fetch Trending facts via search grounding ──
    log_message(f"STEP 2: Fetching facts using Search Grounding for '{category}'...")
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

    while attempts < MAX_RETRY_ATTEMPTS:
        log_message(f"STEP 3 (Attempt {attempts+1}/{MAX_RETRY_ATTEMPTS}): Multi-Agent Tanglish Script Generation...")
        
        script_data = pick_and_generate_script(
            articles=facts, extra_instruction="", forced_article=None, topic_type="research", failed_topics=failed_topics
        )

        if not script_data:
            log_message("❌ Script generation failed. Retrying...")
            attempts += 1
            time.sleep(5)
            continue
            
        script_data["slot"] = slot
        title = script_data.get("title") or ""
        if not str(title).strip():
            title = script_data.get("original_news_headline") or "Tamil Fact!"
        # Rebuild script from subtitle_chunks to guarantee 100% word-for-word alignment
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
            rebuilt_script = " ".join(sc.get("text", "").strip() for sc in sub_chunks if sc.get("text"))
            if rebuilt_script:
                log_message("Aligning script text with subtitle chunks...")
                script = rebuilt_script
            else:
                script = script_data.get("script", "")
        else:
            script = script_data.get("script", "")
        fact_headline = script_data.get("original_news_headline")
        fact_url = script_data.get("original_news_url")
        log_message(f"Selected Fact: {fact_headline}")
        log_message(f"Source URL: {fact_url}")

        # ── STEP 3b: Capture Evidence Screenshot (MANDATORY) ──
        log_message("STEP 3b: Capturing evidence screenshot (before audio for fast fail)...")
        screenshot_captured = False
        
        if fact_url:
            screenshot_filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            screenshot_path = capture_article_screenshot(fact_url, screenshot_filename)
            if screenshot_path:
                script_data["screenshot_path"] = screenshot_path
                log_message(f"✅ Screenshot captured: {screenshot_path}")
                screenshot_captured = True
        
        if not screenshot_captured:
            log_message(f"❌ Screenshot failed for: {fact_headline}. Rejecting topic.")
            failed_topics.append(fact_headline)
            script_data = None
            attempts += 1
            continue

        # ── STEP 4: Generate Cloned Voice Audio ──
        log_message("STEP 4: Generating Tamil cloned voiceover...")
        try:
            audio_path, duration, word_timestamps = generate_voiceover(
                script, custom_phonetic_map=script_data.get("phonetic_pronunciation_map", {}), api_key=GEMINI_API_KEY
            )
        except Exception as e:
            log_message(f"❌ Voiceover failed: {e}")
            audio_path = None
            
        if not audio_path:
            log_message("❌ Audio generation failed. Retrying...")
            failed_topics.append(fact_headline)
            attempts += 1
            continue

        if duration < min_dur:
            log_message(f"⚠️ Generated audio too short ({duration:.1f}s < {min_dur}s). Retrying...")
            failed_topics.append(fact_headline)
            attempts += 1
            continue
            
        break  # Success

    if not audio_path or not script_data or duration < min_dur:
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

    # ── STEP 6: Resolve Background Visuals ──
    log_message("STEP 6: Resolving background visual clips...")
    chunks = fetch_all_chunk_visuals(chunks, topic_context=fact_headline, script_data=script_data)

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
    thumbnail_path = generate_thumbnail(script_data)

    # ── STEP 9: Telegram Verification & Consent ──
    log_message("STEP 9: Requesting VJ's upload approval via Telegram...")
    approved = send_upload_consent(thumbnail_path, title, duration)
    
    if not approved:
        log_message("❌ Upload skipped by user rejection or timeout.")
        notify_telegram("❌ YouTube upload skipped. Video saved locally in output/.", "⚠️")
        return True

    # ── STEP 10: YouTube Upload ──
    log_message("STEP 10: Uploading video to VJ Videos YouTube Channel...")
    ai_desc = script_data.get("description", "")
    hashtags = script_data.get("hashtags", ["#தெரியுமா", "#VJVideos"])
    description = format_description(ai_desc, script, hashtags, slot=slot, source_url=fact_url)
    
    tags = list(set(keywords + [t.replace("#", "") for t in hashtags] + ["Shorts", "SimpleTipsByVJ", "TamilTips"]))[:15]
    
    uploaded, result = upload_video(
        video_path, title, description, tags, 
        thumbnail_path=thumbnail_path, comment_hook=script_data.get("comment_hook")
    )
    
    if not uploaded:
        log_message(f"❌ YouTube upload failed: {result}")
        notify_telegram(f"❌ YouTube upload failed: {result}", "🚨")
        return False

    youtube_url = f"https://youtu.be/{result}"
    log_message(f"🎉 YouTube upload SUCCESS: {youtube_url}")
    notify_telegram(f"🚀 Video is now LIVE on VJ Videos!\n\n📌 <b>{title}</b>\n🔗 {youtube_url}", "✅")

    # ── STEP 11: Update URL in tracker ──
    update_youtube_url(fact_headline, youtube_url)

    # ── STEP 12: Cleanup temp files ──
    log_message("STEP 12: Cleaning up output files...")
    cleaned_count = 0
    for f in glob.glob(os.path.join(OUTPUT_DIR, "*")):
        try:
            if os.path.isfile(f):
                os.remove(f)
                cleaned_count += 1
        except Exception as e:
            log_message(f"Failed to delete {f}: {e}")

    log_message("=== PIPELINE COMPLETED SUCCESSFULLY ===")
    return True

def run_local(category=None):
    success = run_pipeline(forced_category=category)
    if not success:
        print("❌ Pipeline failed.")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--now", action="store_true", help="Run pipeline immediately.")
    parser.add_argument("--category", type=str, default=None, help="Force a specific daily category")
    args = parser.parse_args()

    if args.now:
        run_local(category=args.category)
    else:
        print("Usage: python main.py --now")
        print("For scheduled runs: python scheduler.py")
