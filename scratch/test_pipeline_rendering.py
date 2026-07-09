import os
import sys
import numpy as np
from pydub import AudioSegment
from PIL import Image

os.makedirs("scratch", exist_ok=True)
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# 1. Create a 10-second dummy silent audio file
audio_path = "scratch/dummy_audio_10s.wav"
AudioSegment.silent(duration=10000).export(audio_path, format="wav")

# 2. Create a solid background image for fallback/B-roll
bg_image_path = "scratch/test_bg.jpg"
img = Image.new("RGB", (1080, 1920), (18, 18, 24))
img.save(bg_image_path)

# 3. Setup mock data simulating the Gboard settings video script
script_json = {
    "title": "Gboard-ல ஒரு Hidden AI Hack! Typing Speed 3X Boost! 🚀",
    "sub_category": "🤖 Simple AI Hacks for Everyone",
    "skip_avatar": False,
    "lipsync_face_path": "assets/video/C_white.mp4",
    "kaggle_lipsync_path": None,
    "companies": [],
    "people": [],
    "key_entities": []
}

# Define 3 chunks representing Hook, Body (with Settings UI), and CTA
chunks = [
    {
        "chunk_id": 1,
        "start": 0.0,
        "end": 3.0,
        "duration": 3.0,
        "visual_path": bg_image_path,
        "visual_type": "photo",
        "has_infographic": False,
        "text": "Gboard-la oru hidden AI hack unga typing speed 3X boost panna!",
        "words": [
            {"word": "Gboard-la", "start": 0.0, "end": 0.8},
            {"word": "oru", "start": 0.8, "end": 1.2},
            {"word": "hidden", "start": 1.2, "end": 1.6},
            {"word": "AI", "start": 1.6, "end": 2.0},
            {"word": "hack", "start": 2.0, "end": 2.4},
            {"word": "3X!", "start": 2.4, "end": 3.0}
        ]
    },
    {
        "chunk_id": 2,
        "start": 3.0,
        "end": 7.0,
        "duration": 4.0,
        # visual_path will be resolved to settings simulation by pexels_fetcher.py
        "visual_path": None,
        "visual_type": "video",
        "has_infographic": False,
        "text": "Settings-la Text Correction click panni auto-correction settings double speeds.",
        "words": [
            {"word": "Settings-la", "start": 3.0, "end": 3.8},
            {"word": "Text", "start": 3.8, "end": 4.3},
            {"word": "Correction", "start": 4.3, "end": 4.8},
            {"word": "click", "start": 4.8, "end": 5.2},
            {"word": "panni", "start": 5.2, "end": 5.7},
            {"word": "auto-correction", "start": 5.7, "end": 6.3},
            {"word": "speed!", "start": 6.3, "end": 7.0}
        ]
    },
    {
        "chunk_id": 3,
        "start": 7.0,
        "end": 10.0,
        "duration": 3.0,
        "visual_path": bg_image_path,
        "visual_type": "photo",
        "has_infographic": False,
        "text": "Subscribe to Simple Tips by VJ daily hacks updates.",
        "words": [
            {"word": "Subscribe", "start": 7.0, "end": 7.8},
            {"word": "to", "start": 7.8, "end": 8.2},
            {"word": "Simple", "start": 8.2, "end": 8.6},
            {"word": "Tips", "start": 8.6, "end": 9.0},
            {"word": "by", "start": 9.0, "end": 9.4},
            {"word": "VJ!", "start": 9.4, "end": 10.0}
        ]
    }
]

# 4. Resolve visual_path for the settings chunk using visual engine logic
print("Resolving visuals using fetch_all_chunk_visuals...")
from pexels_fetcher import fetch_all_chunk_visuals
chunks = fetch_all_chunk_visuals(chunks, topic_context="Gboard settings hacks", script_data=script_json, is_longform=False)

# 5. Compile the video
from video_gen import create_video
output_path = "scratch/test_pipeline_output.mp4"
if os.path.exists(output_path):
    os.remove(output_path)

try:
    print("\n🎬 Rendering final test video clip...")
    res = create_video(audio_path, script_json, chunks, output_path=output_path)
    print("🎉 Rendering finished! Output path:", res)
    
    # Extract frames at 1.5s (Hook - full avatar), 5.0s (Body - circular bubble + settings UI), and 8.5s (CTA - full avatar)
    from moviepy.video.io.VideoFileClip import VideoFileClip
    import cv2
    
    clip = VideoFileClip(output_path)
    
    # Save Hook frame (1.5s)
    cv2.imwrite("scratch/frame_hook_1_5s.png", cv2.cvtColor(clip.get_frame(1.5), cv2.COLOR_RGB2BGR))
    # Save Body settings frame (5.0s)
    cv2.imwrite("scratch/frame_body_settings_5_0s.png", cv2.cvtColor(clip.get_frame(5.0), cv2.COLOR_RGB2BGR))
    # Save CTA frame (8.5s)
    cv2.imwrite("scratch/frame_cta_8_5s.png", cv2.cvtColor(clip.get_frame(8.5), cv2.COLOR_RGB2BGR))
    
    clip.close()
    print("📸 Saved test frames in scratch/ to verify layout, avatar, settings UI, and captions.")
except Exception as e:
    import traceback
    print("❌ Render crashed!")
    traceback.print_exc()
