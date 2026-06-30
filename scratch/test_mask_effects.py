import os
import sys
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import VideoClip
from moviepy.video.fx import Resize, Rotate

video_path = "assets/video/C_white.mp4"
clip = VideoFileClip(video_path)

# Create a simple mask of all 0s (fully transparent) to see if it works
mask_data = np.zeros((1280, 720), dtype=np.float32)
mclip = VideoClip(lambda t: mask_data, is_mask=True, duration=3.0)

avatar_clip = clip.resized((360, 640))
print("Before setting mask:")
print("avatar_clip.mask:", avatar_clip.mask)

avatar_clip = avatar_clip.with_mask(mclip)
print("\nAfter setting mask:")
print("avatar_clip.mask:", avatar_clip.mask)

# Apply effects
zoom_speed = 0.10
avatar_clip_effects = avatar_clip.with_effects([
    Resize(lambda t: 1.0 + zoom_speed * t),
    Rotate(lambda t: 0.6 * t)
])
print("\nAfter with_effects:")
print("avatar_clip_effects.mask:", avatar_clip_effects.mask)

# Check if mask is applied to a frame
frame_with_mask = avatar_clip_effects.get_frame(1.0)
print("\nFrame shape with effects:", frame_with_mask.shape)
# If mask is applied, does the frame have an alpha channel?
# Wait, MoviePy's get_frame returns RGB. The mask is applied during blending in CompositeVideoClip.
# Let's check how the clip behaves in CompositeVideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.VideoClip import ColorClip

bg = ColorClip(size=(1080, 1920), color=(255, 0, 0), duration=3.0) # Red background
comp = CompositeVideoClip([bg, avatar_clip_effects.with_position((100, 100))])

# Get a frame of the composition. If the mask (all 0s) is working, the entire frame should be RED
# (or the region where the avatar is placed should be RED, not the avatar itself).
comp_frame = comp.get_frame(1.0)
# Check the region where avatar is placed (100, 100) to (460, 740)
# A pixel in the center of the avatar should be RED [255, 0, 0] if the mask is working.
# If the mask is NOT working, it will show the avatar's pixel colors.
print("Composition frame shape:", comp_frame.shape)
pixel = comp_frame[300, 300]
print("Pixel at (300, 300):", pixel)
if np.array_equal(pixel, [255, 0, 0]):
    print("SUCCESS: Mask is active and blocking the avatar (showing red bg)!")
else:
    print("FAILURE: Mask is ignored (showing avatar pixels)!")
