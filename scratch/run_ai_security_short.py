# -*- coding: utf-8 -*-
import os
import sys
import glob
from datetime import datetime

# Set up paths so we can import from the root folder
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from config import GEMINI_API_KEY
from audio_gen import generate_voiceover, clean_tts_text
from chunk_builder import build_chunks, redistribute_to_audio_duration
from pexels_fetcher import fetch_all_chunk_visuals
from video_gen import create_video
from topic_tracker import get_next_avatar

def run():
    print("🚀 Running AI Security Short Video Generation (Tanglish Captions)...")

    # Select intro avatar video
    intro_videos = glob.glob(os.path.join(root_dir, "assets/video/*.mp4"))
    if not intro_videos:
        intro_videos = [os.path.join(root_dir, "assets/video/Firefly_video_final.mp4")]
    selected_avatar = get_next_avatar(intro_videos)
    print(f"Selected avatar face video: {selected_avatar}")

    # Structured script data
    script_data = {
        "title": "உங்க GPay பணத்தை திருட முடியாது! AI Security Hack! 🛡️",
        "description": "Ungalukke theriyaama, unga GPay matrum PhonePe panathai 24 mani neramum oru 'Invisible Guard' paadhugaathuttu irukkunnu theriyuma? How AI is protecting your UPI money explained in Tanglish by VJ. #AITamil #GPayTamil #SimpleTipsByVJ",
        "use_case_evidence_url": "https://github.com/vjaab/YtSimpleTips",
        "script": "Ungalukke theriyaama, unga GPay matrum PhonePe panathai 24 mani neramum oru 'Invisible Guard' paadhugaathuttu irukkunnu theriyuma? Adhuthaan Artificial Intelligence (AI). Neenga dhinamum panra transactions vachu intha AI unga spending habits-a padichutte irukkum. Udhaaranathukku, dhinamum tea kadaila 20 roobai anuppura neenga, dhideernu night 2 manikki yaaro oru unknown person-ukku 50000 roobai anuppa try pannaa, AI udane alert aagi andha transaction-a block pannidum! Unga bank manager-a vida intha AI-ku ungala nalla theriyum! Intha information pudhusa irundha like pannittu, 'Simple Tips by VJ' channel-a subscribe pannunga!",
        "relevant_links": ["https://github.com/vjaab/YtSimpleTips"],
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
            "block": "blok"
        },
        "hook": "உங்க GPay பணத்தை திருட முடியாது! Why? 🛡️",
        "summary": "How AI protects GPay and PhonePe 24/7 with invisible security and habit learning.",
        "sub_category": "ai_safety_and_scams",
        "breaking_news_level": 9,
        "keywords": ["GPay AI", "PhonePe Security", "UPI Fraud AI", "Simple Tips by VJ", "Tamil Tech Tips"],
        "hashtags": ["#AITamil", "#TechTamil", "#GPay", "#PhonePe", "#SimpleTipsByVJ"],
        "comment_bait_question": "Unga GPay/PhonePe-la ennikkaavadhu unknown transaction block aagi irukka? Comment-la sollunga!",
        "skip_avatar": False,
        "lipsync_face_path": selected_avatar,
        "kaggle_lipsync_path": None,
        "companies": ["Google", "PhonePe"],
        "people": [],
        "key_entities": []
    }

    sub_chunks = [
        {
            "chunk_id": 1,
            "text": "Ungalukke theriyaama, unga GPay",
            "english_caption": "INVISIBLE SHIELD",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A close-up of a glowing digital smartphone showing GPay and PhonePe app icons, surrounded by a semi-transparent glowing golden security shield, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 2,
            "text": "matrum PhonePe panathai",
            "english_caption": "UPI SECURITY",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Digital data streams forming a secure barrier, glowing holographic lock symbol, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 3,
            "text": "24 mani neramum oru 'Invisible Guard'",
            "english_caption": "24/7 GUARD",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly cute robotic security guard holding a small glowing shield, smiling, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 4,
            "text": "paadhugaathuttu irukkunnu theriyuma?",
            "english_caption": "DID YOU KNOW?",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A South Indian young man scrolling phone looking surprised, phone screen glowing on face, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 5,
            "text": "Adhuthaan Artificial Intelligence (AI).",
            "english_caption": "ARTIFICIAL INTELLIGENCE",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute cartoon representation of a glowing digital brain, pulsing with warm soft blue and purple lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 6,
            "text": "Neenga dhinamum panra",
            "english_caption": "DAILY BASIS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A smartphone interface displaying glowing digital icons of shopping, food, and bills, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 7,
            "text": "transactions vachu intha AI",
            "english_caption": "TRANSACTIONS MONITOR",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A cute 3D cartoon style smartphone screen showing small transaction history logs popping up, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 8,
            "text": "unga spending habits-a",
            "english_caption": "SPENDING HABITS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A digital chart/graph highlighting regular payment blocks, warm volumetric lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 9,
            "text": "padichutte irukkum.",
            "english_caption": "AI LEARNING",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A robotic brain studying a chart/graph of daily habits with a magnifying glass, looking focused, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 10,
            "text": "Udhaaranathukku, dhinamum",
            "english_caption": "FOR EXAMPLE",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A friendly South Indian cartoon tea stall owner pouring hot milk tea, warm sun rays, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 11,
            "text": "tea kadaila 20 roobai",
            "english_caption": "TEA SHOP ₹20",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A charming traditional South Indian tea shop with steam rising from hot tea glass, bright warm volumetric light, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 12,
            "text": "anuppura neenga,",
            "english_caption": "REGULAR PAYMENT",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "Hand holding phone scanning a QR code at a street stall, glowing energy line, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 13,
            "text": "dhideernu night 2 manikki",
            "english_caption": "NIGHT 2:00 AM",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A phone displaying a clock face reading 2:00 AM in a dark room, glowing blue light, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 14,
            "text": "yaaro oru unknown person-ukku",
            "english_caption": "UNKNOWN PERSON",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A mysterious dark hacker silhouette with a hood, looking at a glowing matrix code screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 15,
            "text": "50000 roobai anuppa try pannaa,",
            "english_caption": "SENDING ₹50,000",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A phone in the dark displaying an outgoing transfer screen of ₹50,000 at 2:00 AM, glowing text, dark dramatic lighting, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 16,
            "text": "AI udane alert aagi",
            "english_caption": "AI ALERTS",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A bright red warning alert sign flashing on a mobile screen, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 17,
            "text": "andha transaction-a block pannidum!",
            "english_caption": "TRANSACTION BLOCKED!",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A digital shield blocking a red hacking attempt, secure lock icon, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 18,
            "text": "Unga bank manager-a vida",
            "english_caption": "BANK MANAGER",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A funny scene of a shocked bank manager wearing glasses behind a desk, looking surprised, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 19,
            "text": "intha AI-ku ungala nalla theriyum!",
            "english_caption": "AI KNOWS YOU BETTER",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing smart assistant avatar smiling from a phone screen, warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 20,
            "text": "Intha information pudhusa irundha like pannittu,",
            "english_caption": "LIKE THE VIDEO",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A glowing 'Like' thumbs-up button floating in a warm volumetric background, 3D Pixar style, vertical 9:16."
        },
        {
            "chunk_id": 21,
            "text": "'Simple Tips by VJ' channel-a subscribe pannunga!",
            "english_caption": "SUBSCRIBE TO VJ",
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": "A large shining red 'Subscribe' button floating with sparkles, 3D Pixar style, vertical 9:16."
        }
    ]

    # Generate Voiceover
    print("🎙️ Generating cloned voiceover...")
    audio_path, duration, word_timestamps = generate_voiceover(
        script_data["script"],
        custom_phonetic_map=script_data["phonetic_pronunciation_map"],
        api_key=GEMINI_API_KEY
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

    # Resolve visuals (Pexels / etc.)
    print("🎬 Resolving background visuals...")
    chunks = fetch_all_chunk_visuals(
        chunks,
        topic_context="AI safety and scams with banking UPI",
        script_data=script_data,
        is_longform=False
    )

    # Render Final Video
    print("🎥 Rendering video...")
    output_video_path = os.path.join(root_dir, "output", "ai_security_short.mp4")
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    res_path = create_video(audio_path, script_data, chunks, output_path=output_video_path)
    if res_path and os.path.exists(res_path):
        print(f"🎉 SUCCESS! Final video rendered at: {res_path}")
    else:
        print("❌ Video rendering failed.")

if __name__ == "__main__":
    run()
