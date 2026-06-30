import os
import sys
import numpy as np
from pydub import AudioSegment

# Create dummy audio
audio_path = "scratch/dummy_audio2.wav"
AudioSegment.silent(duration=2000).export(audio_path, format="wav")

# Setup minimal data
script_json = {
    "title": "Test Actual Mask",
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
        "end": 2.0,
        "duration": 2.0,
        "visual_path": "assets/video/C_white.mp4",
        "has_infographic": False,
        "english_caption": "Testing mask values",
        "words": []
    }
]

# Modifying create_video logic slightly to print mask stats during rendering
# We can do this by importing moviepy and creating the clips here to inspect them
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import VideoClip
from rembg import remove, new_session

vid_clip = VideoFileClip("assets/video/C_white.mp4").without_audio().subclipped(0, 2.0)
w_a, h_a = vid_clip.size
height_pip = 360
width_pip = 202
avatar_clip = vid_clip.resized((width_pip, height_pip))

unmasked_avatar = avatar_clip
rembg_session = new_session(model_name="u2net_human_seg")
mask_cache = {}

def make_mask_frame(t):
    frame = unmasked_avatar.get_frame(t)
    rgba = remove(
        frame,
        session=rembg_session,
        alpha_matting=True,
        post_process_mask=True
    )
    mask = (rgba[:, :, 3] / 255.0).astype(np.float32)
    h_mask, w_mask = mask.shape
    watermark_height = int(h_mask * 0.12)
    mask[-watermark_height:, :] = 0.0
    print(f"[t={t:.2f}] Mask stats: min={mask.min():.3f}, max={mask.max():.3f}, mean={mask.mean():.3f}")
    return mask

mclip = VideoClip(make_mask_frame, is_mask=True, duration=2.0)
avatar_clip = avatar_clip.with_mask(mclip)

# Render a single frame of CompositeVideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip

bg = ColorClip(size=(720, 1280), color=(255, 0, 0), duration=2.0)
comp = CompositeVideoClip([bg, avatar_clip.with_position((100, 100))])

print("Getting frame at t=1.0...")
comp_frame = comp.get_frame(1.0)
# Print center pixel of avatar overlay area
print("Center pixel in composite frame:", comp_frame[200, 200])
