import os
import sys
import numpy as np
from pydub import AudioSegment
from PIL import Image

os.makedirs("scratch", exist_ok=True)

# 1. Create a 3-second dummy audio file
audio_path = "scratch/dummy_audio_green.wav"
AudioSegment.silent(duration=3000).export(audio_path, format="wav")

# 2. Create a solid green background image
green_bg_path = "scratch/green_bg.jpg"
img = Image.new("RGB", (720, 1280), (0, 255, 0)) # pure green
img.save(green_bg_path)

# 3. Setup mock data
script_json = {
    "title": "Test Green Background Removal",
    "sub_category": "Test",
    "skip_avatar": False,
    "lipsync_face_path": "assets/video/C_white.mp4",
    "kaggle_lipsync_path": None,
    "companies": [],
    "people": [],
    "key_entities": []
}

chunks = [
    {
        "start": 0.0,
        "end": 3.0,
        "duration": 3.0,
        "visual_path": green_bg_path, # solid green background image
        "has_infographic": False,
        "english_caption": "Testing background removal",
        "words": []
    }
]

# 4. Import create_video and run it
sys.path.append(os.path.abspath("."))
from video_gen import create_video

output_path = "scratch/test_render_green.mp4"
if os.path.exists(output_path):
    os.remove(output_path)

try:
    print("Running create_video...")
    res = create_video(audio_path, script_json, chunks, output_path=output_path)
    print("create_video finished! Output path:", res)
    
    # Extract frame at 1.5s
    from moviepy.video.io.VideoFileClip import VideoFileClip
    clip = VideoFileClip(output_path)
    frame = clip.get_frame(1.5)
    clip.close()
    
    import cv2
    cv2.imwrite("scratch/frame_green_output.png", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    print("Saved frame_green_output.png to scratch/")
except Exception as e:
    import traceback
    print("create_video crashed!")
    traceback.print_exc()
