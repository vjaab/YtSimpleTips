import os
import sys
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import VideoClip
from rembg import remove, new_session

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
    return mask

mclip = VideoClip(make_mask_frame, is_mask=True, duration=2.0)
avatar_clip = avatar_clip.with_mask(mclip)

# Now apply the same effects as in video_gen.py:
# vfx.Resize, vfx.Rotate, and then position
from moviepy.video.fx import Resize, Rotate
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip

zoom_speed = 0.10 / 2.0 # duration is 2.0
avatar_clip = avatar_clip.with_effects([
    Resize(lambda t: 1.0 + zoom_speed * t),
    Rotate(lambda t: 0.6 * t)
])

# Background: RED
bg = ColorClip(size=(720, 1280), color=(255, 0, 0), duration=2.0)

# Position: center at x=259 (since FRAME_W=720, scaled_w=202, base_x=(720-202)//2=259), y=800
# Let's use a fixed position for testing
comp = CompositeVideoClip([bg, avatar_clip.with_position((259, 800))])

comp_frame = comp.get_frame(1.0)

# Let's check some pixels in the bounding box of the avatar at t=1.0:
# Bounding box is from x=259 to 259+202 = 461, y=800 to 800+360 = 1160
# Pixel at y=810, x=269 (top-left corner of the avatar overlay)
top_left_pixel = comp_frame[810, 269]
print("Top-left pixel at (810, 269):", top_left_pixel)

# Save the composite frame to verify visually
import cv2
cv2.imwrite("scratch/test_composite_mask_frame.png", cv2.cvtColor(comp_frame, cv2.COLOR_RGB2BGR))
print("Saved test_composite_mask_frame.png to scratch/")
