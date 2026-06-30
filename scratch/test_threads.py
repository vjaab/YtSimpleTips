import os
import sys
import numpy as np
from pydub import AudioSegment
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import VideoClip
from rembg import remove, new_session
from moviepy.video.fx import Resize, Rotate
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip
import cv2

os.makedirs("scratch", exist_ok=True)

# Create 2s audio
audio_path = "scratch/dummy_2s.wav"
AudioSegment.silent(duration=2000).export(audio_path, format="wav")

# Setup clips
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
    try:
        rgba = remove(
            frame,
            session=rembg_session,
            alpha_matting=True,
            post_process_mask=True
        )
        mask = (rgba[:, :, 3] / 255.0).astype(np.float32)
    except Exception as e:
        # If an error happens, return a mask of all ones (so background is NOT removed)
        # and print the error!
        print(f"ERROR in make_mask_frame at t={t}: {e}")
        mask = np.ones((height_pip, width_pip), dtype=np.float32)
        
    h_mask, w_mask = mask.shape
    watermark_height = int(h_mask * 0.12)
    mask[-watermark_height:, :] = 0.0
    return mask

mclip = VideoClip(make_mask_frame, is_mask=True, duration=2.0)
avatar_clip = avatar_clip.with_mask(mclip)

zoom_speed = 0.05
avatar_clip = avatar_clip.with_effects([
    Resize(lambda t: 1.0 + zoom_speed * t),
    Rotate(lambda t: 0.6 * t)
])

bg = ColorClip(size=(720, 1280), color=(255, 0, 0), duration=2.0)
comp = CompositeVideoClip([bg, avatar_clip.with_position((259, 800))])

# 1. Render with threads=1
print("--- Rendering with threads=1 ---")
output_t1 = "scratch/test_t1.mp4"
comp.write_videofile(
    output_t1, fps=30, codec="libx264", audio_codec="aac",
    threads=1, preset="medium", ffmpeg_params=["-pix_fmt", "yuv420p"]
)

# 2. Render with threads=4
print("\n--- Rendering with threads=4 ---")
output_t4 = "scratch/test_t4.mp4"
comp.write_videofile(
    output_t4, fps=30, codec="libx264", audio_codec="aac",
    threads=4, preset="medium", ffmpeg_params=["-pix_fmt", "yuv420p"]
)

# Extract frames at 1.0s to compare
clip1 = VideoFileClip(output_t1)
f1 = clip1.get_frame(1.0)
clip1.close()

clip4 = VideoFileClip(output_t4)
f4 = clip4.get_frame(1.0)
clip4.close()

cv2.imwrite("scratch/frame_t1.png", cv2.cvtColor(f1, cv2.COLOR_RGB2BGR))
cv2.imwrite("scratch/frame_t4.png", cv2.cvtColor(f4, cv2.COLOR_RGB2BGR))
print("\nSaved frame_t1.png and frame_t4.png to scratch/")
