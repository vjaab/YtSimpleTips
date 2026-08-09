# -*- coding: utf-8 -*-
"""
Visual-Only Tamil Shorts Runner
Generates Shorts without voiceover - purely visual + on-screen text + SFX
Usage: python -m scripts.run_visual_shorts [script_id]
"""
import os
import sys
import json
import random

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

from video_gen import create_video

VISUAL_SHORTS_FILE = os.path.join(root_dir, "visual_shorts_scripts.json")


def load_visual_shorts():
    with open(VISUAL_SHORTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def run_visual_short(script_id=None):
    """Generate a visual-only short video from the script data."""
    scripts = load_visual_shorts()
    
    if script_id:
        script_data = next((s for s in scripts if s["id"] == script_id), None)
        if not script_data:
            print(f"❌ Script not found: {script_id}")
            print(f"Available: {[s['id'] for s in scripts]}")
            return False
    else:
        script_data = random.choice(scripts)
        print(f"🎲 Randomly selected: {script_data['id']}")
    
    print(f"🚀 Generating Visual-Only Short: {script_data['title']}")
    print(f"   Topic: {script_data['topic']}")
    print(f"   Scenes: {len(script_data['scenes'])}")
    print(f"   Duration: ~{script_data['total_duration_sec']}s")
    
    # Build script_json compatible with video_gen.py
    # For visual-only: skip avatar, no audio generation needed
    script_json = {
        "title": script_data["title"],
        "script": "",  # No voiceover script
        "subtitle_chunks": [],
        "skip_avatar": True,  # No talking head
        "lipsync_face_path": None,
        "kaggle_lipsync_path": None,
        "has_voiceover": False,
        "visual_only": True,
        "visual_shorts_scenes": script_data["scenes"],
        "total_duration_sec": script_data["total_duration_sec"],
        "aspect_ratio": script_data["aspect_ratio"],
        "target_platform": script_data["target_platform"],
        "companies": [],
        "people": [],
        "key_entities": [],
    }
    
    # Convert scenes to subtitle_chunks format for video_gen compatibility
    for scene in script_data["scenes"]:
        chunk = {
            "chunk_id": scene["scene"],
            "text": scene["text_tamil"],
            "english_caption": scene["text_tamil"],  # Use Tamil as caption
            "start": 0.0,  # Will be calculated by video_gen
            "end": 0.0,
            "has_infographic": False,
            "infographic_type": "none",
            "infographic_data": {},
            "nano_visual_prompt": scene["visual_prompt"],
            "duration_sec": scene["duration_sec"],
            "sfx": scene["sfx"],
        }
        script_json["subtitle_chunks"].append(chunk)
    
    # Generate video - video_gen will need to handle visual_only mode
    # For now, we output the script_json for manual testing
    output_path = os.path.join(root_dir, "output", f"visual_short_{script_data['id']}.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(script_json, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Script JSON saved to: {output_path}")
    print(f"📝 To generate video, run: python -c \"from video_gen import create_video; create_video('{output_path}')\"")
    
    return True


def list_scripts():
    scripts = load_visual_shorts()
    print("\n📋 Available Visual-Only Shorts:")
    print("-" * 60)
    for s in scripts:
        print(f"  {s['id']}")
        print(f"    Topic: {s['topic']} | Scenes: {len(s['scenes'])} | ~{s['total_duration_sec']}s")
        print(f"    Title: {s['title']}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_scripts()
        else:
            run_visual_short(sys.argv[1])
    else:
        run_visual_short()