import os
import sys

# Ensure root directory is in the path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from settings_ui_gen import generate_settings_clip

def test_rendering():
    print("🚀 Running Gboard Settings Simulator Visual Verification...")
    
    test_cases = [
        ("gboard_text_correction", "Go to Text Correction settings and toggle auto-correction to double typing speed.", 4.0),
        ("gboard_glide_typing", "Enable glide typing under keyboard settings for fast swiping.", 3.5),
        ("gboard_dictionary", "Add a custom email shortcut in your dictionary shortcuts settings.", 4.5),
    ]
    
    for filename, text, duration in test_cases:
        out_path = os.path.join(root_dir, "output", f"test_{filename}.mp4")
        print(f"\n🎬 Case: {filename}")
        print(f"   Text: '{text}'")
        print(f"   Duration: {duration}s")
        print(f"   Target: {out_path}")
        
        try:
            generate_settings_clip(text, duration, out_path)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
                print(f"   ✅ Successfully rendered! Size: {os.path.getsize(out_path)} bytes")
            else:
                print(f"   ❌ Render failed or empty output file.")
        except Exception as e:
            print(f"   ❌ Error during generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_rendering()
