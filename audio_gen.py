import os
import json
import re
import asyncio
from datetime import datetime
from config import (
    GEMINI_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    KAGGLE_USERNAME, KAGGLE_KEY, OUTPUT_DIR, ASSETS_DIR
)
from kaggle_handover import trigger_kaggle_gpu_job

def _apply_stable_ts(audio_path, text):
    """
    Applies stable-ts locally on CPU/GPU to get word-level timestamps if available.
    """
    try:
        import stable_whisper
        import warnings
        
        warnings.filterwarnings("ignore")
        print("⏳ Running stable-ts locally to extract real word timestamps...")
        model = stable_whisper.load_model('tiny')
        
        # Strip meta instructions
        clean_text = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        result = model.align(audio_path, clean_text, language='ta')
        
        word_timestamps = []
        for segment in result.segments:
            for word in segment.words:
                clean_word = word.word.strip()
                if clean_word:
                    word_timestamps.append({
                        "word": clean_word,
                        "start": round(word.start, 3),
                        "end": round(word.end, 3)
                    })
        if word_timestamps:
            print(f"✅ stable-ts aligned {len(word_timestamps)} word timestamps.")
            return word_timestamps
    except Exception as e:
        print(f"⚠️ stable-ts alignment skipped or failed: {e}")
    return None

def trim_audio_silence(path, word_timestamps):
    """
    Trims silence from the start and end of the audio file 
    and shifts all word timestamps so that the first word starts at 0.0s.
    """
    from pydub import AudioSegment
    from pydub.silence import detect_leading_silence

    audio = AudioSegment.from_file(path)
    
    # Detect start silence (using aggressive -60dBFS threshold)
    start_trim = detect_leading_silence(audio, silence_threshold=-60.0)
    # Detect end silence
    reversed_audio = audio.reverse()
    end_trim = detect_leading_silence(reversed_audio, silence_threshold=-50.0)

    duration = len(audio)
    trimmed_audio = audio[start_trim:duration-end_trim]
    
    # Boost volume by 8 decibels for punchy Shorts sound
    trimmed_audio = trimmed_audio + 8
    
    trimmed_audio.export(path, format="wav" if path.endswith(".wav") else "mp3")
    
    # Recalibrate timestamps
    shift_sec = start_trim / 1000.0
    new_ts = []
    for ws in word_timestamps:
        new_ts.append({
            "word": ws["word"],
            "start": max(0.0, round(ws["start"] - shift_sec, 3)),
            "end": max(0.0, round(ws["end"] - shift_sec, 3))
        })
    
    new_dur = len(trimmed_audio) / 1000.0
    print(f"🔊 Audio trimmed: -{shift_sec:.2f}s from start. New duration: {new_dur:.2f}s")
    return new_dur, new_ts

def optimize_audio_gaps(audio_path, word_timestamps, max_gap_s=0.35, target_gap_s=0.15):
    """
    Detects silent gaps between words and shortens them to keep the pacing
    extremely tight and fast for high-retention Shorts.
    Bypassed to prevent word cutting and choppy/broken speech.
    """
    from pydub import AudioSegment
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0, word_timestamps
    except Exception as e:
        print(f"⚠️ Gap pacing optimization failed: {e}")
        return 0.0, word_timestamps

def _estimate_timestamps(text, duration):
    words = text.split()
    if not words:
        return []
    interval = duration / len(words)
    return [
        {"word": w, "start": round(i * interval, 3), "end": round((i + 1) * interval, 3)}
        for i, w in enumerate(words)
    ]

def get_audio_duration(path):
    try:
        from mutagen.mp3 import MP3
        return MP3(path).info.length
    except Exception:
        try:
            import soundfile as sf
            data, sr = sf.read(path)
            return len(data) / sr
        except Exception:
            return 0

def clean_tts_text(text):
    """Strips AI meta directions and bracket symbols from voice script."""
    cleaned = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# ── FALLBACK 1: ElevenLabs Multilingual (Your Cloned Voice in Tamil) ──
def _generate_elevenlabs(text, output_path):
    print("📡 [audio_gen] Trying Fallback 1: ElevenLabs Turbo v2.5 (Cloned Voice)...")
    if not ELEVENLABS_API_KEY:
        print("   ✗ ElevenLabs API Key missing.")
        return None, 0, []
        
    try:
        import requests
        voice_id = ELEVENLABS_VOICE_ID or "8Oo4d9mNNwVwK369qOwl"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2", # Premium multilingual synthesis
            "voice_settings": {
                "stability": 0.40,
                "similarity_boost": 0.75,
                "style": 0.10,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            duration = get_audio_duration(output_path)
            word_timestamps = _apply_stable_ts(output_path, text)
            if not word_timestamps:
                word_timestamps = _estimate_timestamps(text, duration)
            return output_path, duration, word_timestamps
        else:
            print(f"   ✗ ElevenLabs API error: {response.text}")
            return None, 0, []
    except Exception as e:
        print(f"   ✗ ElevenLabs failed: {e}")
        return None, 0, []

# ── FALLBACK 2: Edge TTS Tamil (Free, cloud-based last resort) ──
async def _async_generate_edge_tts(text, output_path):
    import edge_tts
    # ta-IN-ValluvarNeural is an excellent, warm male Tamil narrator voice
    communicate = edge_tts.Communicate(text, "ta-IN-ValluvarNeural", rate="+8%")
    await communicate.save(output_path)

def _generate_edge_tts(text, output_path):
    print("📡 [audio_gen] Trying Fallback 2: Edge TTS Tamil (ta-IN-ValluvarNeural)...")
    try:
        asyncio.run(_async_generate_edge_tts(text, output_path))
        duration = get_audio_duration(output_path)
        word_timestamps = _apply_stable_ts(output_path, text)
        if not word_timestamps:
            word_timestamps = _estimate_timestamps(text, duration)
        return output_path, duration, word_timestamps
    except Exception as e:
        print(f"   ✗ Edge TTS failed: {e}")
        return None, 0, []

# ── MAIN ENTRY POINT ──
def generate_voiceover(text, custom_phonetic_map=None, api_key=None):
    """
    Generates Tamil/Tanglish voiceover with 3-tier fallback architecture:
    1. Primary: Kaggle GPU offloaded IndicF5 Voice Cloning (Local vj.wav)
    2. Fallback 1: ElevenLabs Multilingual (Cloud vj.wav Voice Clone)
    3. Fallback 2: Edge TTS Tamil (Free cloud narrator)
    """
    clean_text = clean_tts_text(text)
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join(OUTPUT_DIR, f"audio_{today}.wav")
    
    # ── PRIMARY: KAGGLE GPU JOB ──
    if KAGGLE_USERNAME and KAGGLE_KEY:
        print("🎙️ [audio_gen] Running Primary Pipeline: Kaggle GPU IndicF5 Voice Cloning...")
        script_payload = {"script": clean_text}
        
        job_result = trigger_kaggle_gpu_job(script_payload, custom_phonetic_map)
        
        if job_result and "error" not in job_result:
            local_wav = job_result.get("audio_path")
            word_timestamps = job_result.get("word_timestamps", [])
            duration = job_result.get("duration", 0)
            
            # Copy to targeted local wav path
            if local_wav and os.path.exists(local_wav):
                shutil.copy(local_wav, wav_path)
                
                # Apply local post-processing & gap optimization
                if word_timestamps:
                    duration, word_timestamps = trim_audio_silence(wav_path, word_timestamps)
                    duration, word_timestamps = optimize_audio_gaps(wav_path, word_timestamps)
                    
                print(f"⭐ [audio_gen] Successfully generated voiceover using IndicF5 on Kaggle: {wav_path} ({duration:.2f}s)")
                return wav_path, duration, word_timestamps
            else:
                print("⚠️ Kaggle job succeeded but audio file not found. Falling back...")
        else:
            reason = job_result.get("message") if job_result else "Unknown Kaggle error"
            print(f"⚠️ Kaggle GPU voice cloning failed: {reason}. Triggering Fallback...")

    # ── FALLBACK 1: ELEVENLABS CLONED VOICE ──
    path, dur, word_timestamps = _generate_elevenlabs(clean_text, wav_path)
    if path:
        dur, word_timestamps = trim_audio_silence(path, word_timestamps)
        dur, word_timestamps = optimize_audio_gaps(path, word_timestamps)
        print(f"⭐ [audio_gen] ElevenLabs fallback successful: {path}")
        return path, dur, word_timestamps

    # ── FALLBACK 2: EDGE TTS TAMIL ──
    path, dur, word_timestamps = _generate_edge_tts(clean_text, wav_path)
    if path:
        dur, word_timestamps = trim_audio_silence(path, word_timestamps)
        dur, word_timestamps = optimize_audio_gaps(path, word_timestamps)
        print(f"⭐ [audio_gen] Edge TTS fallback successful: {path}")
        return path, dur, word_timestamps

    raise RuntimeError("🚨 ALL audio generation methods failed! Aborting pipeline.")
