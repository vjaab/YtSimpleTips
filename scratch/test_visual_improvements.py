import os
import math
import numpy as np
from PIL import Image

# 1. Test prompt enhancement
from pexels_fetcher import enhance_prompt_for_documentary

prompts = [
    ("Shark swimming in ocean water 3D Pixar/Disney cartoon style clay textures", "🐾 Nature & Animal Oddities"),
    ("Quantum particle tunneling through barrier", "🧠 Mind-Blowing Science Curiosities"),
    ("Hot boiling water with coarse salt crystals", "🍳 Food, Health & Kitchen Science"),
    ("Ancient temple stone architecture", "🌍 Mysterious History & Culture Secrets"),
]

print("=== 1. TESTING DOCUMENTARY PROMPT ENHANCEMENT ===")
for p, cat in prompts:
    enhanced = enhance_prompt_for_documentary(p, category=cat)
    assert "cartoon" not in enhanced.lower()
    assert "clay" not in enhanced.lower()
    assert "8K" in enhanced
    print(f"Original: {p[:40]}...")
    print(f"Enhanced: {enhanced}\n")

# 2. Test cinematic vignette and color grading
from video_gen import apply_cinematic_vignette, apply_cinematic_color_grade, build_ken_burns

print("=== 2. TESTING CINEMATIC VIGNETTE & COLOR GRADE ===")
test_frame = np.full((1920, 1080, 3), 160, dtype=np.uint8)
graded = apply_cinematic_color_grade(test_frame, category="🧠 Mind-Blowing Science Curiosities")
vignetted = apply_cinematic_vignette(graded, intensity=0.30)

assert vignetted.shape == (1920, 1080, 3)
center_val = vignetted[960, 540, 0]
corner_val = vignetted[0, 0, 0]
assert corner_val < center_val, f"Corner ({corner_val}) must be darker than center ({center_val})"
print(f"Frame center luminance: {center_val}, Corner luminance: {corner_val} (Vignette verified!)")

# 3. Test Ken Burns 2.0 multi-axis motion
print("=== 3. TESTING KEN BURNS 2.0 MULTI-AXIS MOTIONS ===")
dummy_img_path = "/tmp/test_kb_dummy.jpg"
Image.new("RGB", (1080, 1920), color=(120, 140, 180)).save(dummy_img_path)

motions = ["dolly_in", "dolly_out", "pan_left", "pan_right", "pedestal_up"]
for m in motions:
    clip = build_ken_burns(dummy_img_path, duration=2.0, zoom_direction=m, target_size=(1080, 1920))
    f0 = clip.get_frame(0.0)
    f1 = clip.get_frame(1.0)
    f2 = clip.get_frame(2.0)
    assert f0.shape == (1920, 1080, 3)
    assert f1.shape == (1920, 1080, 3)
    assert f2.shape == (1920, 1080, 3)
    print(f"  ✅ Camera mode '{m}' rendered smoothly at 1080x1920.")

print("\n🎉 ALL VISUAL IMPROVEMENTS VERIFIED SUCCESSFULLY!")
