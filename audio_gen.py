import os
import json
import re
import asyncio
import shutil
import subprocess
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
    Trims silence from the start and end of the audio file,
    applies professional filters (noise reduction, EQ/treble, highpass),
    normalizes volume to avoid clipping,
    and shifts all word timestamps so that the first word starts at 0.0s.
    """
    from pydub import AudioSegment
    from pydub.silence import detect_leading_silence
    from pydub.effects import normalize

    audio = AudioSegment.from_file(path)
    
    # Detect start silence (using aggressive -60dBFS threshold)
    start_trim = detect_leading_silence(audio, silence_threshold=-60.0)
    # Detect end silence
    reversed_audio = audio.reverse()
    end_trim = detect_leading_silence(reversed_audio, silence_threshold=-50.0)

    duration = len(audio)
    trimmed_audio = audio[start_trim:duration-end_trim]
    
    # Save trimmed audio to temp format so we can process it with FFmpeg
    ext = os.path.splitext(path)[1]
    trimmed_audio.export(path, format=ext[1:])
    
    # Apply FFmpeg audio filters for professional voiceover cleaning & mastering:
    # 1. afftdn: FFT denoiser to eliminate background hiss/static
    # 2. highpass=f=80: filter out low-frequency electronic/AC hum
    # 3. equalizer: boost vocal presence/articulation around 3.5kHz by 3dB
    # 4. treble: shelving filter to boost high-end air/clarity above 6kHz by 3dB
    temp_path = path + f".filtered{ext}"
    try:
        filter_str = "afftdn,highpass=f=80,equalizer=f=4000:width_type=h:width=2000:g=4,treble=g=3:f=6000"
        cmd = [
            "ffmpeg", "-y",
            "-i", path,
            "-af", filter_str,
            temp_path
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(temp_path):
            shutil.copy(temp_path, path)
            os.remove(temp_path)
            print("✨ [audio_gen] Applied professional noise reduction, highpass, presence EQ, and treble boost.")
    except Exception as e:
        print(f"⚠️ [audio_gen] FFmpeg voice enhancement failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    # Load the filtered audio and apply peak-normalization to -1.5 dBFS.
    # This maximizes vocal volume without causing any digital clipping.
    try:
        filtered_audio = AudioSegment.from_file(path)
        normalized_audio = normalize(filtered_audio, headroom=1.5)
        normalized_audio.export(path, format=ext[1:])
        trimmed_audio = normalized_audio
    except Exception as e:
        print(f"⚠️ [audio_gen] Audio normalization failed: {e}")
    
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
    print(f"🔊 Audio trimmed & mastered: -{shift_sec:.2f}s from start. New duration: {new_dur:.2f}s")
    return new_dur, new_ts

def optimize_audio_gaps(audio_path, word_timestamps, max_gap_s=0.40, target_gap_s=0.20):
    """
    Detects silent gaps between words and shortens them to keep the pacing
    tight for high-retention Shorts. Uses gentle thresholds to avoid
    cutting words or creating choppy speech.
    """
    from pydub import AudioSegment
    try:
        audio = AudioSegment.from_file(audio_path)
        
        # Find gaps and shorten only those exceeding max_gap_s
        modified = False
        segments = []
        last_end_ms = 0
        
        for i, ws in enumerate(word_timestamps):
            start_ms = int(ws["start"] * 1000)
            end_ms = int(ws["end"] * 1000)
            
            gap_ms = start_ms - last_end_ms
            gap_s = gap_ms / 1000.0
            
            if gap_s > max_gap_s and last_end_ms > 0:
                # Shorten this gap to target_gap_s
                target_gap_ms = int(target_gap_s * 1000)
                # Keep a small portion of the original silence for naturalness
                segments.append(audio[last_end_ms:last_end_ms + target_gap_ms])
                # Adjust timestamps for all subsequent words
                reduction_ms = gap_ms - target_gap_ms
                for j in range(i, len(word_timestamps)):
                    word_timestamps[j]["start"] = max(0, word_timestamps[j]["start"] - reduction_ms / 1000.0)
                    word_timestamps[j]["end"] = max(0, word_timestamps[j]["end"] - reduction_ms / 1000.0)
                modified = True
            else:
                # Keep the gap as-is
                if last_end_ms < start_ms:
                    segments.append(audio[last_end_ms:start_ms])
            
            segments.append(audio[start_ms:end_ms])
            last_end_ms = end_ms
        
        # Add any remaining audio after the last word
        if last_end_ms < len(audio):
            remaining = audio[last_end_ms:]
            # Trim trailing silence to max 0.3s
            if len(remaining) > 300:
                remaining = remaining[:300]
            segments.append(remaining)
        
        if modified and segments:
            combined = segments[0]
            for seg in segments[1:]:
                combined += seg
            combined.export(audio_path, format=os.path.splitext(audio_path)[1][1:])
            new_duration = len(combined) / 1000.0
            print(f"✂️ [audio_gen] Gap optimization: tightened pacing. New duration: {new_duration:.2f}s")
            return new_duration, word_timestamps
        
        duration = len(audio) / 1000.0
        return duration, word_timestamps
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
                "stability": 0.40,      # Lower stability for more expressive, dynamic delivery
                "similarity_boost": 0.75,
                "speed": 1.15           # 15% faster speech for viral Shorts pacing
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
    1. Primary: ElevenLabs Multilingual (Cloud vj.wav Voice Clone)
    2. Fallback 1: Kaggle GPU offloaded IndicF5 Voice Cloning (Local vj.wav)
    3. Fallback 2: Edge TTS Tamil (Free cloud narrator)
    """
    clean_text = clean_tts_text(text)
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join(OUTPUT_DIR, f"audio_{today}.wav")
    
    # ── PRIMARY: ELEVENLABS CLONED VOICE ──
    path, dur, word_timestamps = _generate_elevenlabs(clean_text, wav_path)
    if path:
        dur, word_timestamps = trim_audio_silence(path, word_timestamps)
        dur, word_timestamps = optimize_audio_gaps(path, word_timestamps)
        print(f"⭐ [audio_gen] ElevenLabs primary generation successful: {path}")
        return path, dur, word_timestamps
    else:
        print("⚠️ ElevenLabs primary generation failed. Triggering Fallback 1 (Kaggle GPU)...")

    # ── FALLBACK 1: KAGGLE GPU JOB ──
    if KAGGLE_USERNAME and KAGGLE_KEY:
        print("🎙️ [audio_gen] Running Fallback 1: Kaggle GPU IndicF5 Voice Cloning...")
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
            print(f"⚠️ Kaggle GPU voice cloning failed: {reason}. Triggering Fallback 2...")

    # ── FALLBACK 2: EDGE TTS TAMIL ──
    path, dur, word_timestamps = _generate_edge_tts(clean_text, wav_path)
    if path:
        dur, word_timestamps = trim_audio_silence(path, word_timestamps)
        dur, word_timestamps = optimize_audio_gaps(path, word_timestamps)
        print(f"⭐ [audio_gen] Edge TTS fallback successful: {path}")
        return path, dur, word_timestamps

    raise RuntimeError("🚨 ALL audio generation methods failed! Aborting pipeline.")
