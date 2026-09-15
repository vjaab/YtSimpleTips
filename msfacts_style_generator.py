# -*- coding: utf-8 -*-
"""
MSFACTSTAMIL-Style Visual Shorts Generator
Mimics @MSFACTSTAMIL-t4n/shorts channel style for "Simple Tips by VJ"
- Visual-only (no voiceover needed)
- Fast 1-3 second cuts with stock footage
- Bold Tamil text overlays
- Tanglish facts format
"""

import json
import random
import os
from config import OUTPUT_DIR, ASSETS_DIR
from pexels_fetcher import fetch_pexels_media
from video_gen import create_video

MSFACTS_FACT_TEMPLATES = [
    {
        "id": "brain_facts",
        "topic": "human_body",
        "category": "Science",
        "title": "மூளையின் விசித்திர உண்மைகள்",
        "scenes": [
            {
                "text_tamil": "உங்கள் மூளை [60%] சமையல் எண்ணெய்! 🧠🛢️",
                "visual_query": "brain neural network",
                "duration_sec": 3,
                "sfx": "Deep bass thump"
            },
            {
                "text_tamil": "நீங்க பேசும் போது மூளை [20% மின்சாரம்] உற்பத்தி செய்கிறது! ⚡",
                "visual_query": "brain electricity neurons",
                "duration_sec": 4,
                "sfx": "Electric crackle"
            },
            {
                "text_tamil": "தூங்கும் போது மூளை [குப்பை] தூக்குகிறது! 🗑️😴",
                "visual_query": "brain cleaning sleep glymphatic",
                "duration_sec": 4,
                "sfx": "Water rush"
            },
            {
                "text_tamil": "மேலும் அறிய Follow பண்ணுங்கள்! 🧠🚀",
                "visual_query": "brain follow button",
                "duration_sec": 3,
                "sfx": "Ding bell"
            }
        ]
    },
    {
        "id": "space_facts",
        "topic": "space",
        "category": "Space",
        "title": "விண்வெளியின் ரகசியங்கள்",
        "scenes": [
            {
                "text_tamil": "விண்வெளியில் [சத்தமே இல்லை]! 🤫🌌",
                "visual_query": "space astronaut vacuum",
                "duration_sec": 3,
                "sfx": "Deep space drone"
            },
            {
                "text_tamil": "நீண்ட காலம் உயிர் வarrassாத [Water Bears]! 🐛☄️",
                "visual_query": "tardigrade space",
                "duration_sec": 4,
                "sfx": "Heroic chime"
            },
            {
                "text_tamil": "நெப்டூன்-ல் ஒரு ஆண்டு = [165 பூமி ஆண்டுகள்]! 🪐",
                "visual_query": "neptune planet orbit",
                "duration_sec": 4,
                "sfx": "Time warp whoosh"
            },
            {
                "text_tamil": "மேலும் விண்வெளி டிப்ஸ் Follow பண்ணுங்கள்! 🚀",
                "visual_query": "rocket launch stars",
                "duration_sec": 3,
                "sfx": "Rocket whoosh"
            }
        ]
    },
    {
        "id": "animals_facts",
        "topic": "animals",
        "category": "Nature",
        "title": "மிருகங்களின் அதிசய உண்மைகள்",
        "scenes": [
            {
                "text_tamil": "ஒக்டோபசினு [3 இதயங்கள்] + நீல இரத்தம்! 🐙💙",
                "visual_query": "octopus underwater",
                "duration_sec": 3,
                "sfx": "Heartbeat rhythm"
            },
            {
                "text_tamil": "காஞ்சனா [கண்ணாடி காட்சிகள்] மட்டுமில்லை - UV காணும்! 🦞👁️",
                "visual_query": "mantis shrimp eye",
                "duration_sec": 4,
                "sfx": "Prism shatter"
            },
            {
                "text_tamil": "கூவிகள் [தலையை 270°] திருப்பலாம்! 🦉🔄",
                "visual_query": "owl head rotation",
                "duration_sec": 4,
                "sfx": "Soft bone crack"
            },
            {
                "text_tamil": "மேலும் வைல்ட்லைஃப் Follow பண்ணுங்கள்! 🐾",
                "visual_query": "animal paw print",
                "duration_sec": 3,
                "sfx": "Paw step"
            }
        ]
    },
    {
        "id": "tech_facts",
        "topic": "technology",
        "category": "Technology",
        "title": "தொழில்நுட்பின் மாயை",
        "scenes": [
            {
                "text_tamil": "உங்கள் நரம்பு [CPU-க்கு 100x வேகம்]! 📱⚡",
                "visual_query": "neural network brain computer",
                "duration_sec": 3,
                "sfx": "Digital race whoosh"
            },
            {
                "text_tamil": "First 1GB drive = [500kg] + $40,000! 💾💰",
                "visual_query": "old hard drive computer",
                "duration_sec": 4,
                "sfx": "Heavy thud"
            },
            {
                "text_tamil": "AI இப்போது [தமிழ் கவிதை] எழுதும்! 🤖📜",
                "visual_query": "AI writing code",
                "duration_sec": 4,
                "sfx": "Keyboard typing"
            },
            {
                "text_tamil": "தொழில்நுட்ப டிப்ஸ் Follow பண்ணுங்கள்! 💡",
                "visual_query": "circuit board technology",
                "duration_sec": 3,
                "sfx": "Circuit connect"
            }
        ]
    },
    {
        "id": "psychology_facts",
        "topic": "psychology",
        "category": "Psychology",
        "title": "மனதின் மாயைகள்",
        "scenes": [
            {
                "text_tamil": "நீங்கள் [95%] சிந்திக்கும் விஷயங்கள் மட்டுமே நடக்காது! 🧠💭",
                "visual_query": "brain worry bubbles",
                "duration_sec": 3,
                "sfx": "Bubble pop"
            },
            {
                "text_tamil": "[21 நாட்கள்] பழக்கம் = Automatic behavior! 🔁",
                "visual_query": "neural pathway habit formation",
                "duration_sec": 4,
                "sfx": "Path building"
            },
            {
                "text_tamil": "உங்கள் வேடிக்கை [நேரடி] மாதிரி பரவுகிறது! 😂🦠",
                "visual_query": "laughter contagion brain",
                "duration_sec": 4,
                "sfx": "Contagious laughter"
            },
            {
                "text_tamil": "மனதை கைப்பற்ற Follow பண்ணுங்கள்! 🧩",
                "visual_query": "puzzle pieces brain",
                "duration_sec": 3,
                "sfx": "Satisfying click"
            }
        ]
    },
    {
        "id": "ocean_facts",
        "topic": "ocean",
        "category": "Nature",
        "title": "கடலின் மறைந்த புலமைகள்",
        "scenes": [
            {
                "text_tamil": "கடல் ஆழம் [மேலும் காணப்படாது] - 80% unexplored! 🌊❓",
                "visual_query": "deep ocean Mariana trench",
                "duration_sec": 3,
                "sfx": "Deep pressure drone"
            },
            {
                "text_tamil": "உடர்ப்புக்குள் [கடல் உப்பு] = perfect ratio! 🩸🌊",
                "visual_query": "blood cells seawater",
                "duration_sec": 4,
                "sfx": "Cellular pulse"
            },
            {
                "text_tamil": "ஒரு கேட் [மேதையை ஊக்குகிறது] - Seaweed = Oxygen! 🌿💨",
                "visual_query": "kelp forest oxygen bubbles",
                "duration_sec": 4,
                "sfx": "Bubble stream"
            },
            {
                "text_tamil": "கடல் ரகசியங்கள் Follow என்று சொல்லு! 🐋",
                "visual_query": "whale tail ocean",
                "duration_sec": 3,
                "sfx": "Whale call"
            }
        ]
    },
    {
        "id": "history_facts",
        "topic": "history",
        "category": "History",
        "title": "வரலாற்று ஷாக்கர்கள்",
        "scenes": [
            {
                "text_tamil": "கிளியோபட்ரா [iPhone-க்கு போதும் நெறுக்கம்]! 👑📱",
                "visual_query": "ancient egypt timeline",
                "duration_sec": 3,
                "sfx": "Timeline whoosh"
            },
            {
                "text_tamil": "ரோமன்ஸ் [மூத்திரம்] பயன்படுத்தி தவிட்டு போட்டனர்! 🏛️🧴",
                "visual_query": "ancient roman laundry",
                "duration_sec": 4,
                "sfx": "Chemical fizz"
            },
            {
                "text_tamil": "உலக ammonium போர் = [Sandwich] காரணம்! 🥪⚔️",
                "visual_query": "sandwich invention history",
                "duration_sec": 4,
                "sfx": "Card shuffle"
            },
            {
                "text_tamil": "வரலாறு பிடிக்குமோ? Follow பண்ணுங்கள்! 📜",
                "visual_query": "ancient scroll",
                "duration_sec": 3,
                "sfx": "Scroll unroll"
            }
        ]
    },
    {
        "id": "body_facts",
        "topic": "human_body",
        "category": "Science",
        "title": "உடலின் விசித்திரம்",
        "scenes": [
            {
                "text_tamil": "உங்கள் வயிறு [Second Brain] - 100M neurons! 🧠🍽️",
                "visual_query": "gut brain connection neurons",
                "duration_sec": 3,
                "sfx": "Neural pulse"
            },
            {
                "text_tamil": "நீங்கள் ஆண்டில் [35kg விழுந்த துடுப்பு] பூசுகிறீர்கள்! 🦴🦷",
                "visual_query": "skin cells shedding",
                "duration_sec": 4,
                "sfx": "Dust sparkle"
            },
            {
                "text_tamil": "உங்கள் [நாக்கு] விறப்புணர்வு unique! 👅🔐",
                "visual_query": "tongue print biometric",
                "duration_sec": 4,
                "sfx": "Scanner beep"
            },
            {
                "text_tamil": "உங்கள் உடல் ஒரு கோடி! Follow செய்யுங்கள்! 🫀",
                "visual_query": "heart beating",
                "duration_sec": 3,
                "sfx": "Heartbeat"
            }
        ]
    }
]

def generate_msfacts_script(template_id=None):
    """Generate a MSFACTSTAMIL-style visual shorts script."""
    if template_id:
        template = next((t for t in MSFACTS_FACT_TEMPLATES if t["id"] == template_id), None)
        if not template:
            template = random.choice(MSFACTS_FACT_TEMPLATES)
    else:
        template = random.choice(MSFACTS_FACT_TEMPLATES)
    
    scenes = []
    for i, scene in enumerate(template["scenes"]):
        visual_prompt = "Cinematic 4K vertical 9:16 stock footage of " + scene["visual_query"] + ", high quality, dramatic lighting"
        scenes.append({
            "scene": i + 1,
            "duration_sec": scene["duration_sec"],
            "text_tamil": scene["text_tamil"],
            "visual_prompt": visual_prompt,
            "stock_search_query": scene["visual_query"],
            "sfx": scene["sfx"]
        })
    
    total_duration = sum(s["duration_sec"] for s in scenes)
    
    script = {
        "id": template["id"],
        "topic": template["topic"],
        "title": template["title"],
        "format": "visual_only_shorts",
        "language": "tamil",
        "has_voiceover": False,
        "scenes": scenes,
        "total_duration_sec": total_duration,
        "aspect_ratio": "9:16",
        "target_platform": "youtube_shorts"
    }
    
    return script

def fetch_visuals_for_script(script):
    """Fetch Pexels stock footage for all scenes in the script."""
    title = script["title"]
    print("🎬 Fetching stock footage for: " + title)
    
    for scene in script["scenes"]:
        query = scene.get("stock_search_query", scene.get("visual_prompt", ""))
        if query:
            print("  🔍 Searching Pexels for: " + query)
            video_path = fetch_pexels_media(query, media_type="video", aspect_ratio="9:16")
            if video_path:
                scene["visual_path"] = video_path
                scene["visual_type"] = "video"
                scene["source"] = "Pexels Video"
                print("  ✅ Downloaded: " + video_path)
            else:
                print("  ⚠️ No video found, trying photo...")
                photo_path = fetch_pexels_media(query, media_type="photo", aspect_ratio="9:16")
                if photo_path:
                    scene["visual_path"] = photo_path
                    scene["visual_type"] = "photo"
                    scene["source"] = "Pexels Photo"
                    print("  ✅ Downloaded photo: " + photo_path)
                else:
                    print("  ❌ No visual found for: " + query)
    
    return script

def build_video_from_script(script, output_name=None):
    """Build final video from the script using stock footage."""
    if not output_name:
        output_name = "msfacts_" + script["id"] + "_" + str(random.randint(1000, 9999)) + ".mp4"
    
    output_path = os.path.join(OUTPUT_DIR, output_name)
    
    # Convert script scenes to chunks format expected by video_gen
    chunks = []
    current_time = 0.0
    for scene in script["scenes"]:
        if scene.get("visual_path") and os.path.exists(scene["visual_path"]):
            chunk_duration = scene["duration_sec"]
            chunks.append({
                "chunk_id": scene["scene"],
                "text": scene["text_tamil"],
                "visual_path": scene["visual_path"],
                "visual_type": scene.get("visual_type", "video"),
                "duration": chunk_duration,
                "start": current_time,
                "end": current_time + chunk_duration,
                "source": scene.get("source", "Stock Footage")
            })
            current_time += chunk_duration
    
    if not chunks:
        print("❌ No valid visuals to build video!")
        return None
    
    print("🎥 Building video with " + str(len(chunks)) + " visual chunks...")
    
    # Create silent audio (since no voiceover)
    from pydub import AudioSegment
    total_duration = sum(c["duration"] for c in chunks) * 1000
    silent_audio = AudioSegment.silent(duration=total_duration)
    audio_path = os.path.join(OUTPUT_DIR, "silent_" + output_name.replace(".mp4", ".wav"))
    silent_audio.export(audio_path, format="wav")
    
    # Build script_json in the format expected by video_gen
    script_json = {
        "title": script["title"],
        "topic": script["topic"],
        "format": script["format"],
        "language": script["language"],
        "has_voiceover": script["has_voiceover"],
        "total_duration_sec": script["total_duration_sec"],
        "aspect_ratio": script["aspect_ratio"],
        "target_platform": script["target_platform"],
        "visual_only": True,
        "skip_avatar": True,
        "visual_shorts_scenes": script["scenes"],
        "subtitle_chunks": chunks
    }
    
    # Generate video
    final_video = create_video(
        audio_path=audio_path,
        script_json=script_json,
        chunks=chunks,
        output_path=output_path
    )
    
    if final_video and os.path.exists(final_video):
        print("✅ Video created: " + final_video)
        return final_video
    
    return None

def run_msfacts_pipeline(template_id=None, count=1):
    """Run the full MSFACTSTAMIL-style pipeline."""
    print("=" * 60)
    print("🎬 MSFACTSTAMIL-STYLE VISUAL SHORTS PIPELINE")
    print("=" * 60)
    
    videos_created = []
    
    for i in range(count):
        print("\n📹 Generating video " + str(i+1) + "/" + str(count) + "...")
        
        # 1. Generate script
        script = generate_msfacts_script(template_id)
        print("  📝 Script: " + script["title"] + " (" + str(script["total_duration_sec"]) + "s)")
        
        # 2. Fetch stock footage
        script = fetch_visuals_for_script(script)
        
        # 3. Build video
        video_path = build_video_from_script(script)
        if video_path:
            videos_created.append(video_path)
    
    print("\n" + "=" * 60)
    print("✅ Pipeline complete! Created " + str(len(videos_created)) + " videos:")
    for v in videos_created:
        print("  - " + v)
    print("=" * 60)
    
    return videos_created

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MSFACTSTAMIL-style visual shorts generator")
    parser.add_argument("--template", type=str, help="Specific template ID to use")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--list", action="store_true", help="List available templates")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available templates:")
        for t in MSFACTS_FACT_TEMPLATES:
            print("  - " + t["id"] + ": " + t["title"] + " (" + t["category"] + ")")
    else:
        run_msfacts_pipeline(template_id=args.template, count=args.count)