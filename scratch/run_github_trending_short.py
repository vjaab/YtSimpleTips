# -*- coding: utf-8 -*-
import os
import sys
import glob
import shutil
from datetime import datetime

# Set up paths so we can import from the root folder
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Override config setting before importing main components
import config
config.ENABLE_EVIDENCE_SCREENSHOTS = True

from audio_gen import generate_voiceover, clean_tts_text
from chunk_builder import build_chunks, redistribute_to_audio_duration
from pexels_fetcher import fetch_all_chunk_visuals
from video_gen import create_video
from topic_tracker import get_next_avatar

def run():
    print("🚀 Running GitHub Trending PentAGI Short Video Generation...")

    # Copy the captured trending screenshot to have "screenshot" in the filename
    screenshot_src = os.path.join(root_dir, "assets", "screenshots", "github_trending.png")
    screenshot_dst = os.path.join(root_dir, "assets", "screenshots", "screenshot_github_trending.png")
    
    if os.path.exists(screenshot_src):
        shutil.copy(screenshot_src, screenshot_dst)
        print(f"✅ Copied screenshot to: {screenshot_dst}")
    else:
        print("🚨 Error: github_trending.png was not found. Programmatic card will be generated as fallback.")

    # Select intro avatar video
    intro_videos = glob.glob(os.path.join(root_dir, "assets/video/*.mp4"))
    if not intro_videos:
        intro_videos = [os.path.join(root_dir, "assets/video/Firefly_video_final.mp4")]
    selected_avatar = get_next_avatar(intro_videos)
    print(f"Selected avatar face video: {selected_avatar}")

    # Structured script data
    script_data = {
        "title": "GitHub-ல ஒரு Trending AI Hack! PentAGI Security! 🛡️",
        "description": "GitHub Trending page-la innaikku top trending list-la irukku PentAGI. How this autonomous AI hacking agent works explained in Tanglish by VJ. #AITamil #GitHubTrending #SimpleTipsByVJ",
        "use_case_evidence_url": "https://github.com/trending",
        "script": "Chrome matrum WhatsApp-ai vida 10 madangu powerful AI Hack... GitHub-la innaikku enna trending theriyuma? Athu thaan PentAGI. GitHub-la top trending-la irukku intha tool. Ithu oru fully autonomous AI hacking team mathiri work pannum! Metasploit, Nmap, sqlmap mathiri 20 plus top security tools-a ithu automatic-a chain panni absolute security testing pannidum. PostgreSQL knowledge graphs vachu unga code safety pattern-a analyze pannum. Professional security researchers kooda bug find panna intha tool-a thaan top-la use panranga. Intha advanced tech news ungalukku useful-a irundha like pannittu, 'Simple Tips by VJ' channel-a subscribe pannunga!",
        "relevant_links": ["https://github.com/trending"],
        "phonetic_pronunciation_map": {
            "GPay": "jee-pay",
            "PhonePe": "phone-pay",
            "Invisible": "in-vis-i-bl",
            "Guard": "gard",
            "Artificial": "ar-ti-fi-shal",
            "Intelligence": "in-tel-i-gens",
            "AI": "ay-eye",
            "transactions": "tran-sac-shuns",
            "spending": "spen-ding",
            "habits": "ha-bits",
            "alert": "a-lert",
            "block": "blok",
            "PentAGI": "pent-ay-jee",
            "Nmap": "en-map",
            "PostgreSQL": "post-gres-cue-el",
            "Metasploit": "meta-sploit",
            "sqlmap": "sequel-map"
        },
        "hook": "GitHub-la innaikku enna trending theriyuma? 🛡️",
        "summary": "How PentAGI autonomous AI hacking agent works and why it is trending on GitHub.",
        "sub_category": "ai_safety_and_scams",
        "breaking_news_level": 9,
        "keywords": ["GitHub Trending", "PentAGI", "AI Hacking Agent", "Simple Tips by VJ", "Tamil Tech Tips"],
        "hashtags": ["#AITamil", "#TechTamil", "#GitHub", "#PentAGI", "#SimpleTipsByVJ"],
        "comment_bait_question": "Neenga autonomous AI security tools use panni irukingala? Comment-la sollunga!",
        "skip_avatar": False,
        "lipsync_face_path": selected_avatar,
        "kaggle_lipsync_path": None,
        "companies": ["GitHub", "VXControl"],
        "people": [],
        "key_entities": []
    }

    sub_chunks = [
        {
            "chunk_id": 1,
            "text": "Chrome matrum WhatsApp-ai vida",
            "english_caption": "POWERFUL APPS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing grid of modern app icons including WhatsApp and Chrome, digital interfaces, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 2,
            "text": "10 madangu powerful AI Hack...",
            "english_caption": "10X POWER HACK",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing battery icon with green electrical lightning sparks showing 10X power boost, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 3,
            "text": "GitHub-la innaikku enna trending",
            "english_caption": "GITHUB TRENDING",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A close-up of a glowing digital smartphone showing the GitHub logo and trending stars graph, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 4,
            "text": "theriyuma? Athu thaan PentAGI.",
            "english_caption": "PENTAGI REVEALED",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A sleek glowing computer setup displaying cybersecurity agents and matrix code, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 5,
            "text": "GitHub-la top trending-la",
            "english_caption": "NUMBER ONE TREND",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing golden trophy floating above data flow graphs, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 6,
            "text": "irukku intha tool.",
            "english_caption": "POPULAR TOOL",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Digital terminal dashboard with stats and stars rising, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 7,
            "text": "Ithu oru fully autonomous AI",
            "english_caption": "AUTONOMOUS AGENT",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly cute robotic agent typing code on a holographic laptop, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 8,
            "text": "hacking team mathiri work pannum!",
            "english_caption": "HACKING TEAM",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A team of small cute helper robots wearing hacker hoodies working together, glowing screens, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 9,
            "text": "Metasploit, Nmap, sqlmap mathiri",
            "english_caption": "SECURITY TOOLS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A security toolbox filled with glowing digital tools and lock symbols, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 10,
            "text": "20 plus top security tools-a",
            "english_caption": "20+ POWERFUL TOOLS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A grid of 20 glowing metallic lock and shield symbols, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 11,
            "text": "ithu automatic-a chain panni",
            "english_caption": "AUTOMATED CHAINING",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing golden digital chains linking together cyber processes, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 12,
            "text": "absolute security testing pannidum.",
            "english_caption": "SECURED SYSTEM",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A giant glowing green digital lock appearing over a secure server room, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 13,
            "text": "PostgreSQL knowledge graphs vachu",
            "english_caption": "KNOWLEDGE GRAPH",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing network of databases connected by light pathways, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 14,
            "text": "unga code safety pattern-a",
            "english_caption": "CODE PATTERNS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Glowing green lines of source code scanned by a searchlight, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 15,
            "text": "analyze pannum. Professional security",
            "english_caption": "AI ANALYSIS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute robot analyst pointing at security charts on a screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 16,
            "text": "researchers kooda bug find panna",
            "english_caption": "BUG HUNTING",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A magnifying glass highlighting a small glowing bug on a digital leaf made of chips, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 17,
            "text": "intha tool-a thaan top-la use panranga.",
            "english_caption": "TOP CHOICE",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A shiny crown placed on top of a holographic server rack, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 18,
            "text": "Intha advanced tech news ungalukku",
            "english_caption": "USEFUL TECH HACKS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Sparkling news article screen popping out of a phone, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 19,
            "text": "useful-a irundha like pannittu,",
            "english_caption": "LIKE THE VIDEO",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing 'Like' thumbs-up button floating in a warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 20,
            "text": "'Simple Tips by VJ' channel-a",
            "english_caption": "VJ VIDEOS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Channel profile banner with glowing letters, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 21,
            "text": "subscribe pannunga!",
            "english_caption": "SUBSCRIBE",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A large shining red 'Subscribe' button floating with sparkles, 3D Pixar style, vertical 9:16."
        }
    ]

    # Force the trending screenshot for chunks 3, 4, 5, 6
    for i in [2, 3, 4, 5]: # 0-indexed indices for chunk 3, 4, 5, 6
        if i < len(sub_chunks):
            sub_chunks[i]["visual_path"] = screenshot_dst
            sub_chunks[i]["visual_type"] = "photo"

    # Generate Voiceover
    print("🎙️ Generating cloned voiceover...")
    audio_path, duration, word_timestamps = generate_voiceover(
        script_data["script"],
        custom_phonetic_map=script_data["phonetic_pronunciation_map"],
        api_key=config.GEMINI_API_KEY
    )
    print(f"✅ Voiceover generated: {audio_path} (Duration: {duration:.2f}s)")

    # Build Chunks
    print("🧩 Building visual chunks from subtitle timestamps...")
    cleaned_sub_chunks = []
    for sc in sub_chunks:
        sc["text"] = clean_tts_text(sc["text"])
        cleaned_sub_chunks.append(sc)

    chunks = build_chunks(word_timestamps, cleaned_sub_chunks)
    chunks = redistribute_to_audio_duration(chunks, duration)

    # Force visual_path again in the compiled chunks representing indices 2, 3, 4, 5
    print("📌 Injecting screenshot evidence into specific chunk timelines...")
    for idx, c in enumerate(chunks):
        # Map back to matching chunk IDs
        if c.get("chunk_id") in [3, 4, 5, 6]:
            c["visual_path"] = screenshot_dst
            c["visual_type"] = "photo"
            print(f"   Applied screenshot to Chunk {c.get('chunk_id')} [{c.get('start')}s -> {c.get('end')}s]")

    # Resolve remaining visuals (Pexels / etc.)
    print("🎬 Resolving background visuals for other chunks...")
    chunks = fetch_all_chunk_visuals(
        chunks,
        topic_context="GitHub trending repo PentAGI AI cybersecurity penetration testing",
        script_data=script_data,
        is_longform=False
    )

    # Render Final Video
    print("🎥 Rendering video...")
    output_video_path = os.path.join(root_dir, "output", "github_trending_short.mp4")
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    res_path = create_video(audio_path, script_data, chunks, output_path=output_video_path)
    if res_path and os.path.exists(res_path):
        print(f"🎉 SUCCESS! Final video rendered at: {res_path}")
    else:
        print("❌ Video rendering failed.")

if __name__ == "__main__":
    run()
