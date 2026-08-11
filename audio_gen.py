# -*- coding: utf-8 -*-
import os
import sys
import json
import re
import asyncio
import shutil
import subprocess
import warnings
from datetime import datetime

# Filter user-facing warnings for clean output
warnings.filterwarnings("ignore")

from config import (
    GEMINI_API_KEY, ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID,
    KAGGLE_USERNAME, KAGGLE_KEY, OUTPUT_DIR, ASSETS_DIR, ENABLE_TTS_FALLBACK, VOICE_SPEED
)
from kaggle_handover import trigger_kaggle_gpu_job

# Global status tracking for voice fallback
VOICE_FALLBACK_USED = False

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
        
        # Strip meta instructions and break tags
        clean_text = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', text)
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
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
            print(f"[audio_gen] stable-ts aligned {len(word_timestamps)} word timestamps.")
            return word_timestamps
    except Exception as e:
        print(f"[audio_gen] stable-ts alignment skipped or failed: {e}")
    return None

def trim_audio_silence(path, word_timestamps):
    """
    Trims only excessive silence from start/end, preserves natural breath pauses.
    """
    from pydub import AudioSegment
    from pydub.silence import detect_leading_silence

    audio = AudioSegment.from_file(path)
    
    # Conservative trimming: -40dBFS instead of -60dBFS, keep more head/tail room
    start_trim = detect_leading_silence(audio, silence_threshold=-40.0)
    reversed_audio = audio.reverse()
    end_trim = detect_leading_silence(reversed_audio, silence_threshold=-40.0)

    duration = len(audio)
    # Keep 200ms silence padding at start/end for natural breath room
    start_trim = max(0, start_trim - 200)
    end_trim = max(0, end_trim - 200)
    
    if duration - start_trim - end_trim > 500:
        trimmed_audio = audio[start_trim:duration-end_trim]
    else:
        trimmed_audio = audio[start_trim:duration-end_trim] if end_trim > 0 else audio[start_trim:]
    
    ext = os.path.splitext(path)[1]
    trimmed_audio.export(path, format=ext[1:])
    
    new_dur = len(trimmed_audio) / 1000.0

    # Recalibrate timestamps
    shift_sec = start_trim / 1000.0
    new_ts = []
    for ws in word_timestamps:
        w_start = max(0.0, round(ws["start"] - shift_sec, 3))
        w_end = max(0.0, round(ws["end"] - shift_sec, 3))
        if w_start < new_dur:
            new_ts.append({
                "word": ws["word"],
                "start": w_start,
                "end": min(w_end, new_dur)
            })
    
    print(f"[audio_gen] Audio trimmed conservatively: -{shift_sec:.2f}s from start. New duration: {new_dur:.2f}s")
    return new_dur, new_ts

def optimize_audio_gaps(audio_path, word_timestamps):
    """
    Returns original duration and word_timestamps without slicing/modifying the audio stream.
    This preserves the original continuous voice quality of the clone, avoiding click/pop artifacts.
    """
    duration = get_audio_duration(audio_path)
    return duration, word_timestamps

def _estimate_timestamps(text, duration):
    # Strip break tags from estimate logic so they aren't counted as words
    text = re.sub(r'<[^>]+>', '', text)
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
        from pydub import AudioSegment
        audio = AudioSegment.from_file(path)
        return len(audio) / 1000.0
    except Exception as e:
        print(f"[audio_gen] get_audio_duration fallback from pydub: {e}")
        try:
            import soundfile as sf
            data, sr = sf.read(path)
            return len(data) / sr
        except Exception:
            return 0

def clean_tts_text(text):
    """Strips AI meta directions and bracket symbols from voice script."""
    return preprocess_script_for_tts(text)

def convert_numbers_to_words(text: str) -> str:
    # A simple map for numbers 0 to 100 to English words for clean Tanglish synthesis
    num_map = {
        0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
        16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty",
        30: "thirty", 40: "forty", 50: "fifty", 60: "sixty", 70: "seventy",
        80: "eighty", 90: "ninety", 100: "one hundred"
    }
    
    def get_word(n):
        if n in num_map:
            return num_map[n]
        if 20 < n < 100:
            tens = (n // 10) * 10
            ones = n % 10
            return f"{num_map[tens]}-{num_map[ones]}"
        return str(n)
        
    def repl(match):
        val_str = match.group(0)
        try:
            val = int(val_str)
            if 0 <= val <= 100:
                return get_word(val)
        except ValueError:
            pass
        return val_str
        
    # Replace standalone numbers in range 0-100 with words
    return re.sub(r'\b\d{1,3}\b', repl, text)

def preprocess_script_for_tts(text: str) -> str:
    if not text:
        return ""
    # Strip brackets/parentheses
    text = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', text)
    # Spacing Guard: Ensure proper spaces between English/Latin and Tamil runs
    text = re.sub(r'([a-zA-Z0-9])([\u0b80-\u0bff])', r'\1 \2', text)
    text = re.sub(r'([\u0b80-\u0bff])([a-zA-Z0-9])', r'\1 \2', text)
    # Replace "..." with ", "
    text = text.replace("...", ", ")
    # Replace " - " with ", "
    text = text.replace(" - ", ", ")
    # Replace newlines "\n" with " "
    text = text.replace("\n", " ")
    
    # Deduplicate adjacent duplicate words (e.g., "the the" -> "the", "page page" -> "page")
    text = re.sub(r'\b(\w+)\b\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    # Deduplicate adjacent duplicate 2-word phrases (e.g., "this page this page" or "this page, this page" -> "this page")
    text = re.sub(r'\b(\w+\s+\w+)\b[\s,.]+\1\b', r'\1', text, flags=re.IGNORECASE)
    
    # Replace "%" with " percent"
    text = text.replace("%", " percent")
    
    # Convert digits to words (anti-stutter for ElevenLabs / Edge-TTS)
    text = convert_numbers_to_words(text)
    # Replace numbers > 999 with word form (without commas)
    def replace_num(match):
        raw = match.group(0)
        clean = raw.replace(',', '')
        try:
            val = int(clean)
            if val > 999:
                return clean
        except ValueError:
            pass
        return raw
    text = re.sub(r'\b\d{1,3}(?:,\d{3})+\b|\b\d{4,}\b', replace_num, text)
    
    # Remove all markdown: **, *, #, _, ~
    text = re.sub(r'[*#_~]', '', text)
    # Replace double spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    text = text.strip()
    # Ensure text ends with "."
    if text and not text[-1] in ('.', '!', '?'):
        text += "."
        
    return re.sub(r'\s+', ' ', text).strip()

def split_text_into_chunks(text: str) -> list[str]:
    # Split on sentence-ending punctuation: ".", "!", "?"
    sentences = re.split(r'([.!?]+)', text)
    sentence_list = []
    
    # Reassemble sentences with punctuation
    for i in range(0, len(sentences) - 1, 2):
        s = sentences[i].strip()
        punc = sentences[i+1]
        if s:
            sentence_list.append(s + punc)
    if len(sentences) % 2 == 1:
        s = sentences[-1].strip()
        if s:
            sentence_list.append(s)
            
    chunks = []
    current_chunk = []
    current_word_count = 0
    MAX_WORDS_PER_CHUNK = 80  # Larger chunks = fewer cuts
    
    for sent in sentence_list:
        sent_words = len(sent.split())
        if current_word_count + sent_words > MAX_WORDS_PER_CHUNK and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sent]
            current_word_count = sent_words
        else:
            current_chunk.append(sent)
            current_word_count += sent_words
            
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    # Ensure no chunk is too small (merge tiny trailing chunks)
    merged_chunks = []
    for chunk in chunks:
        if merged_chunks and len(chunk.split()) < 15:
            merged_chunks[-1] += " " + chunk
        else:
            merged_chunks.append(chunk)
    
    return merged_chunks

def inject_break_tags(text: str) -> str:
    """
    Injects SSML-style break tags into preprocessed TTS text for ElevenLabs Multilingual v2.
    - 0.3s pause at sentence-ending punctuation (. ! ?)
    - 0.15s pause at clause/comma punctuation (,)
    """
    # 1. Inject 0.3s break tags at sentence boundaries (. ! ?) followed by space or end of string
    text = re.sub(r'([.!?]+)(?:\s+|$)', r'\1 <break time="0.3s"/> ', text)
    # 2. Inject 0.15s break tags at clause boundaries (commas) followed by space or end of string
    text = re.sub(r'(,)(?:\s+|$)', r'\1 <break time="0.15s"/> ', text)
    # Clean up double spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _synthesize_single_chunk_elevenlabs(text, voice_id, headers, params):
    """Synthesizes a single text chunk via ElevenLabs API. Returns raw MP3 bytes."""
    cleaned_text = preprocess_script_for_tts(text)
    # Inject break tags for ElevenLabs Multilingual v2 pacing control
    cleaned_text = inject_break_tags(cleaned_text)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    data = {
        "text": cleaned_text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            # Tunable settings: Lower stability increases dynamic variation; higher style enhances emotion
            "stability": 0.40,
            "similarity_boost": 0.85,
            "style": 0.45,
            "use_speaker_boost": True
        }
    }
    
    try:
        import requests
        response = requests.post(url, json=data, headers=headers, params=params, stream=True)
        if response.status_code == 200:
            audio_data = b""
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    audio_data += chunk
            return audio_data
        else:
            print(f"   ✗ ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ✗ ElevenLabs chunk synthesis failed: {e}")
        return None
def _concat_mp3_chunks(mp3_chunks, crossfade_ms=150):
    """Concatenates MP3 chunks with crossfades (not silence) for seamless flow."""
    from pydub import AudioSegment
    import io
    
    if not mp3_chunks:
        return AudioSegment.empty()
    
    combined = AudioSegment.from_file(io.BytesIO(mp3_chunks[0]), format="mp3")
    
    for mp3_bytes in mp3_chunks[1:]:
        seg = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
        # Crossfade instead of silence gap - eliminates hard cuts
        combined = combined.append(seg, crossfade=crossfade_ms)
    
    return combined
def _generate_elevenlabs(text, output_path):
    print("[audio_gen] Synthesizing with ElevenLabs (Cloned Voice)...")
    if not ELEVENLABS_API_KEY:
        print("   ✗ ElevenLabs API Key missing.")
        return None
        
    voice_id = ELEVENLABS_VOICE_ID or "8Oo4d9mNNwVwK369qOwl"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    # Use mp3_44100_128 format — available on all ElevenLabs tiers (Starter, Creator, Pro)
    # pcm_44100 requires Pro tier and causes 403 errors on lower tiers
    params = {
        "output_format": "mp3_44100_128"
    }
    
    words = text.split()
    mp3_chunks = []
    
    if len(words) > 50:
        print(f"[audio_gen] Long script detected ({len(words)} words). Using chunked synthesis...")
        chunks = split_text_into_chunks(text)
        print(f"👉 Split script into {len(chunks)} chunks.")
        
        for idx, chunk in enumerate(chunks):
            print(f"[audio_gen] Synthesizing chunk {idx+1}/{len(chunks)}...")
            chunk_mp3 = _synthesize_single_chunk_elevenlabs(chunk, voice_id, headers, params)
            if not chunk_mp3:
                print(f"   ✗ Failed to synthesize chunk {idx+1}")
                return None
            mp3_chunks.append(chunk_mp3)
    else:
        print("[audio_gen] Script is short. Synthesizing as a single ElevenLabs chunk...")
        single_mp3 = _synthesize_single_chunk_elevenlabs(text, voice_id, headers, params)
        if not single_mp3:
            return None
        mp3_chunks.append(single_mp3)
            
    try:
        if len(mp3_chunks) == 1:
            # Single chunk — convert directly from MP3 bytes to WAV
            import io
            from pydub import AudioSegment
            audio_seg = AudioSegment.from_file(io.BytesIO(mp3_chunks[0]), format="mp3")
        else:
            # Multiple chunks — concatenate with crossfades
            audio_seg = _concat_mp3_chunks(mp3_chunks, crossfade_ms=150)
        
        # Normalize to 44100Hz mono WAV for downstream processing
        audio_seg = audio_seg.set_frame_rate(44100).set_channels(1).set_sample_width(2)
        audio_seg.export(output_path, format="wav")
        print(f"[audio_gen] ElevenLabs synthesis complete: {output_path}")
        return output_path
    except Exception as e:
        print(f"   ✗ ElevenLabs output conversion failed: {e}")
        return None

def _generate_elevenlabs_standard(text, output_path):
    """Generate audio using ElevenLabs with a standard (non-cloned) multilingual voice."""
    print("[audio_gen] Synthesizing with ElevenLabs (Standard Multilingual Voice)...")
    if not ELEVENLABS_API_KEY:
        print("   ✗ ElevenLabs API Key missing.")
        return None
        
    # Use a standard multilingual voice (not cloned)
    # 21m00Tcm4TlvDq8ikWAM = Rachel (multilingual v2)
    # AZnzlk1XvdvUeBnXmlld = Domi (multilingual v2)
    # EXAVITQu4vr4xnSDxMaL = Bella (multilingual v2)
    voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel - standard multilingual voice
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    params = {
        "output_format": "mp3_44100_128"
    }
    
    words = text.split()
    mp3_chunks = []
    
    if len(words) > 50:
        print(f"[audio_gen] Long script detected ({len(words)} words). Using chunked synthesis...")
        chunks = split_text_into_chunks(text)
        print(f"👉 Split script into {len(chunks)} chunks.")
        
        for idx, chunk in enumerate(chunks):
            print(f"[audio_gen] Synthesizing chunk {idx+1}/{len(chunks)}...")
            chunk_mp3 = _synthesize_single_chunk_elevenlabs(chunk, voice_id, headers, params)
            if not chunk_mp3:
                print(f"   ✗ Failed to synthesize chunk {idx+1}")
                return None
            mp3_chunks.append(chunk_mp3)
    else:
        print("[audio_gen] Script is short. Synthesizing as a single ElevenLabs chunk...")
        single_mp3 = _synthesize_single_chunk_elevenlabs(text, voice_id, headers, params)
        if not single_mp3:
            return None
        mp3_chunks.append(single_mp3)
            
    try:
        if len(mp3_chunks) == 1:
            import io
            from pydub import AudioSegment
            audio_seg = AudioSegment.from_file(io.BytesIO(mp3_chunks[0]), format="mp3")
        else:
            audio_seg = _concat_mp3_chunks(mp3_chunks, crossfade_ms=150)
        
        audio_seg = audio_seg.set_frame_rate(44100).set_channels(1).set_sample_width(2)
        audio_seg.export(output_path, format="wav")
        print(f"[audio_gen] ElevenLabs (standard voice) synthesis complete: {output_path}")
        return output_path
    except Exception as e:
        print(f"   ✗ ElevenLabs output conversion failed: {e}")
        return None

async def _async_generate_edge_tts(text, output_path):
    import edge_tts
    # Slower rate (+5% instead of +8%) for more natural pacing
    # Added pitch adjustment for warmer vocal tone
    communicate = edge_tts.Communicate(text, "ta-IN-ValluvarNeural", rate="+5%", pitch="+2Hz")
    await communicate.save(output_path)

def _generate_edge_tts(text, output_path):
    print("[audio_gen] Synthesizing with Edge TTS (ta-IN-ValluvarNeural)...")
    temp_mp3 = output_path + ".temp.mp3"
    try:
        # Edge TTS generates MP3. We save it as temp_mp3, then convert it to a WAV format matching the extension
        asyncio.run(_async_generate_edge_tts(text, temp_mp3))
        if os.path.exists(temp_mp3) and os.path.getsize(temp_mp3) > 0:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(temp_mp3)
            # Normalize to 44100Hz mono WAV
            audio = audio.set_frame_rate(44100).set_channels(1).set_sample_width(2)
            audio.export(output_path, format="wav")
            os.remove(temp_mp3)
            return output_path
    except Exception as e:
        print(f"   ✗ Edge TTS failed: {e}")
        if os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except:
                pass
    return None

def detect_audio_breaks(audio_path: str) -> list[tuple]:
    """
    Detects only EXCESSIVE silence gaps (>1.5s) that indicate TTS artifacts.
    Natural breath pauses (200-800ms) are preserved.
    """
    import librosa
    try:
        y, sr = librosa.load(audio_path, sr=44100, mono=True)
    except Exception as e:
        print(f"[audio_gen] Failed to load audio in librosa: {e}")
        return []
        
    frame_length = 441
    hop_length = 441
    
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)
    rms_values = rms[0]
    num_frames = len(rms_values)
    
    breaks = []
    in_break = False
    break_start_frame = None
    
    for i in range(num_frames):
        is_silent = rms_values[i] < 0.003  # Slightly more sensitive
        if is_silent:
            if not in_break:
                in_break = True
                break_start_frame = i
        else:
            if in_break:
                duration_ms = (i - break_start_frame) * 10.0
                # Only flag breaks > 1.5s (was 600ms) - preserves natural breaths
                if duration_ms > 1500.0:
                    start_time = break_start_frame * 10.0
                    end_time = i * 10.0
                    breaks.append((start_time, end_time))
                in_break = False
                
    if in_break:
        duration_ms = (num_frames - break_start_frame) * 10.0
        if duration_ms > 1500.0:
            start_time = break_start_frame * 10.0
            end_time = num_frames * 10.0
            breaks.append((start_time, end_time))
            
    return breaks

def fix_audio_breaks(audio_path: str, breaks: list) -> str:
    """
    Shortens ONLY excessive silences (>1.5s) to a natural 400ms pause.
    Preserves natural breathing room in speech.
    """
    if not breaks:
        return audio_path
        
    from pydub import AudioSegment
    try:
        audio = AudioSegment.from_file(audio_path)
    except Exception as e:
        print(f"[audio_gen] Failed to read audio with pydub: {e}")
        return audio_path
        
    # Process from end to start (reverse order) so timestamps remain valid
    for start_ms, end_ms in reversed(breaks):
        start_ms = int(start_ms)
        end_ms = int(end_ms)
        
        left_part = audio[:start_ms]
        right_part = audio[end_ms:]
        
        # Replace long break with natural 400ms pause (was 200ms - too short)
        silence_gap = AudioSegment.silent(duration=400, frame_rate=audio.frame_rate)
        silence_gap = silence_gap.set_frame_rate(audio.frame_rate).set_sample_width(audio.sample_width).set_channels(audio.channels)
        audio = left_part + silence_gap + right_part
        
    audio.export(audio_path, format="wav")
    return audio_path

def apply_mastering_chain(audio_path: str, is_elevenlabs: bool = True) -> None:
    """
    Applies the exact professional FFmpeg mastering filter chain for vocal clarity.
    Uses t=h (Hz width type) instead of t=o (octave) because widths of 200, 800, 2000
    are Hz values; using octave (t=o) causes coefficient corruption and silence.
    Also appends aresample=44100 to ensure sample rate is exactly 44100 Hz.
    If is_elevenlabs is True, bypasses denoising (afftdn) and harsh EQ to preserve voice clone characteristics.
    """
    temp_path = audio_path + ".mastered.wav"
    if is_elevenlabs:
        # ElevenLabs generates pristine studio-quality audio.
        # Bypass denoising and heavy EQ to prevent watery phase cancellation artifacts
        # and preserve 100% of the original voice match.
        filter_str = (
            "highpass=f=80,"  # removes low-frequency rumble below 80Hz
            "equalizer=f=4000:t=h:w=1000:g=+2.5,"  # presence boost 3kHz-5kHz for vocal clarity
            "acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"  # subtle dynamics compression
            "loudnorm=I=-14:TP=-1.5:LRA=7,"  # standard Shorts loudness target
            "aresample=44100"  # keep consistent sample rate
        )
    else:
        filter_str = (
            "highpass=f=80,"  # removes low-frequency rumble below 80Hz
            "lowpass=f=11000,"  # removes harsh air/TTS artifacts above 11kHz (was 12kHz)
            "afftdn=nf=-25,"  # noise floor reduction at -25dB (gentler than current)
            "equalizer=f=200:t=h:w=200:g=-3,"  # cut muddy low-mids
            "equalizer=f=3500:t=h:w=1000:g=+3,"  # boost vocal presence (clarity range 3kHz-5kHz)
            "equalizer=f=8000:t=h:w=2000:g=+1,"  # subtle air/brightness
            "acompressor=threshold=-18dB:ratio=3:attack=5:release=50,"  # subtle dynamics compression
            "loudnorm=I=-14:TP=-1.5:LRA=7,"  # normalize to YouTube Shorts standard (-14 LUFS)
            "aresample=44100"  # ensure sample rate is exactly 44100 Hz
        )
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-af", filter_str,
        "-ar", "44100",
        temp_path
    ]
    try:
        print(f"[audio_gen] Applying FFmpeg mastering chain to {audio_path}...")
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(temp_path):
            shutil.copy(temp_path, audio_path)
            os.remove(temp_path)
            print("✨ [audio_gen] FFmpeg mastering chain applied successfully.")
    except Exception as e:
        print(f"[audio_gen] FFmpeg mastering chain failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)

def upsample_audio_to_44100(audio_path: str) -> None:
    """
    Upsamples the audio file to 44100 Hz using librosa.resample with res_type='kaiser_best'.
    """
    import librosa
    import soundfile as sf
    print(f"🔄 [audio_gen] Upsampling {audio_path} to 44100 Hz using kaiser_best...")
    try:
        y, sr = librosa.load(audio_path, sr=None)  # Load at original sample rate
        if sr != 44100:
            y_resampled = librosa.resample(y, orig_sr=sr, target_sr=44100, res_type='kaiser_best')
            sf.write(audio_path, y_resampled, 44100)
            print(f"[audio_gen] Upsampled from {sr} Hz to 44100 Hz.")
        else:
            print(f"ℹ️ [audio_gen] Audio is already 44100 Hz.")
    except Exception as e:
        print(f"[audio_gen] Upsampling failed: {e}")

# ── F5-TTS Config ─────────────────────────────────────────────────────────────
VJ_REF_WAV = os.path.join(ASSETS_DIR, "vj.wav")
VJ_REF_TEXT = (
    "Welcome you are listening to your channel, we bring you the best insights, ideas and stories. Drafted just for you Stay tuned and let's get started."
)

_f5_instance = None

def _get_f5_model():
    global _f5_instance
    if _f5_instance is None:
        import torch
        from f5_tts.api import F5TTS

        device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
        print(f"Initialising F5-TTS (Local Voice Cloning) on {device}...")
        _f5_instance = F5TTS(device=device)
    return _f5_instance

def unload_f5_model():
    """Explicitly unload F5-TTS model from GPU to free up memory."""
    global _f5_instance
    if _f5_instance is not None:
        import torch
        import gc
        print("🧹 Unloading F5-TTS model and clearing CUDA cache...")
        _f5_instance = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

def _smart_split_sentences(text, max_chars=120):
    """
    Split text into natural sentence-boundary chunks for F5-TTS.
    Keeps chunks under max_chars to prevent the 12s clipping issue.
    Splits at sentence boundaries (.?!) then at clause boundaries (,;:—) as fallback.
    """
    import re
    # First split into sentences
    parts = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for part in parts:
        if len(current + " " + part) < max_chars:
            current = (current + " " + part).strip()
        else:
            if current:
                chunks.append(current.strip())
            # If a single sentence is still too long, split at clause boundaries
            if len(part) > max_chars:
                clause_parts = re.split(r'(?<=[,;:\—])\s+', part)
                sub_current = ""
                for cp in clause_parts:
                    if len(sub_current + " " + cp) < max_chars:
                        sub_current = (sub_current + " " + cp).strip()
                    else:
                        if sub_current:
                            chunks.append(sub_current.strip())
                        sub_current = cp
                current = sub_current
            else:
                current = part
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c]

def _postprocess_voice_audio(wav_path):
    """
    Professional post-processing chain to enhance clarity and presence:
    1. High-pass filter at 120Hz to remove low-end rumble and mud.
    2. Three-Band Presence EQ Crossover Network:
       - Lows (100Hz - 200Hz): warm chest boost (+1.5dB).
       - Mids (200Hz - 3kHz): vocal core.
       - Highs (3kHz - 15kHz): crisp sparkle presence boost (+3.5dB) and high-end air.
    3. Dynamic Range Compression to level out the voice and make it "pop".
    4. Final normalization to -1dB for consistent loudness.
    5. Subtle fade-in/out to prevent clicks.
    """
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize, compress_dynamic_range
        
        audio = AudioSegment.from_wav(wav_path)
        
        # 1. High-pass filter (120Hz) - Removes low-frequency room rumble
        audio = audio.high_pass_filter(120)
        
        # 2. Three-Band Presence EQ Crossover
        lows = audio.low_pass_filter(200).high_pass_filter(100)
        mids = audio.high_pass_filter(200).low_pass_filter(3000)
        highs = audio.high_pass_filter(3000)
        
        # Apply premium boosting gains
        lows = lows + 1.5   # Warmth chest boost
        highs = highs + 3.5 # Sparkle & presence air boost
        
        # Recombine frequency crossover bands
        audio = lows.overlay(mids).overlay(highs)
        
        # 3. Dynamic Compression - Makes the voice sound authoritative and professional
        audio = compress_dynamic_range(audio, threshold=-15.0, ratio=3.0, attack=5.0, release=50.0)
        
        # 4. Final Normalization
        audio = normalize(audio, headroom=1.0)
        
        # 5. Prevent click artifacts
        audio = audio.fade_in(5).fade_out(5)
        
        audio.export(wav_path, format="wav")
        print(f"   [audio_gen] Audio enhanced: 120Hz HPF, 3-band presence EQ, dynamic compression, normalized to -1dB")
    except Exception as e:
        print(f"   ⚠ Audio post-processing skipped: {e}")

def _generate_f5_clone(text, output_path):
    print("F5-TTS → Cloning VJ's Voice (High-Quality Pipeline)...")
    
    wav_path = output_path.replace(".mp3", ".wav")
    
    # Smart sentence-boundary splitting (120 chars max per chunk)
    chunks = _smart_split_sentences(text, max_chars=120)
    print(f"   Split into {len(chunks)} voice segments")
    
    # Generate each segment with F5-TTS
    f5 = _get_f5_model()
    segment_paths = []
    for i, chunk in enumerate(chunks):
        seg_path = wav_path.replace(".wav", f"_seg_{i}.wav")
        f5.infer(
            ref_file=VJ_REF_WAV,
            ref_text=VJ_REF_TEXT,
            gen_text=chunk,
            file_wave=seg_path,
            nfe_step=64,      # Increased from 32 for higher audio fidelity and clarity
            remove_silence=True, # Cleanup of chunk edges
            speed=1.0
        )
        segment_paths.append(seg_path)
        
    # Combine segments with 30ms cross-fade for seamless joins
    CROSSFADE_MS = 30
    from pydub import AudioSegment
    combined = AudioSegment.from_wav(segment_paths[0]) if segment_paths else AudioSegment.empty()
    for sp in segment_paths[1:]:
        seg = AudioSegment.from_wav(sp)
        combined = combined.append(seg, crossfade=CROSSFADE_MS)
    
    # Clean up segment files
    for sp in segment_paths:
        try: os.remove(sp)
        except: pass
        
    combined.export(wav_path, format="wav")
    
    # Post-process for professional voice quality
    _postprocess_voice_audio(wav_path)
    
    duration = get_audio_duration(wav_path)
    
    # Word timestamps via stable-ts
    word_timestamps = _apply_stable_ts(wav_path, text)
    if not word_timestamps:
        word_timestamps = _estimate_timestamps(text, duration)
        
    print(f"F5-TTS done: {duration:.2f}s | {len(word_timestamps)} word timestamps")
    return wav_path, duration, word_timestamps

def speed_up_audio(audio_path, factor):
    if factor == 1.0:
        return audio_path
    temp_path = audio_path + ".sped.wav"
    cmd = [
        "ffmpeg", "-y",
        "-i", audio_path,
        "-filter:a", f"atempo={factor}",
        temp_path
    ]
    try:
        print(f"[audio_gen] Speeding up audio by {factor}x...")
        import subprocess
        import shutil
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        if os.path.exists(temp_path):
            shutil.copy(temp_path, audio_path)
            os.remove(temp_path)
            print("[audio_gen] Audio speedup applied successfully.")
    except Exception as e:
        print(f"[audio_gen] Audio speedup failed: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return audio_path

def generate_voiceover(text, custom_phonetic_map=None, api_key=None):
    """
    Generates Tamil/Tanglish voiceover using Edge TTS (free, no voice cloning needed).
    Falls back to ElevenLabs with standard multilingual voice if Edge TTS fails.
    """
    global VOICE_FALLBACK_USED
    if custom_phonetic_map:
        for word, phonetic in custom_phonetic_map.items():
            pattern = re.compile(r'\b' + re.escape(word) + r'\b', re.IGNORECASE)
            text = pattern.sub(phonetic, text)
            
    clean_text = preprocess_script_for_tts(text)
    today = datetime.now().strftime("%Y%m%d_%H%M%S")
    wav_path = os.path.join(OUTPUT_DIR, f"audio_{today}.wav")
    
    # Primary: Edge TTS (free, Tamil support, no cloning needed)
    path = _generate_edge_tts(clean_text, wav_path)
    if not path:
        print("⚠️ Edge TTS failed. Falling back to ElevenLabs (standard voice)...")
        # Fallback: ElevenLabs with standard multilingual voice (not cloned)
        path = _generate_elevenlabs_standard(clean_text, wav_path)
        if not path:
            raise RuntimeError("[audio_gen] Both Edge TTS and ElevenLabs voice generation failed!")
        VOICE_FALLBACK_USED = True
    else:
        VOICE_FALLBACK_USED = False
        
    # Speed up audio to match the energetic pacing of reference short
    if VOICE_SPEED != 1.0:
        path = speed_up_audio(path, VOICE_SPEED)
        
    # ── UNIFIED POST-PROCESSING PIPELINE ──
    
    # Step 1: Upsample if F5 was used
    upsample_audio_to_44100(path)
        
    # Step 2: Run break detection and fixing before mastering
    breaks = detect_audio_breaks(path)
    print(f"[audio_gen] Detected {len(breaks)} audio breaks.")
    if breaks:
        path = fix_audio_breaks(path, breaks)
        print(f"[audio_gen] Fixed {len(breaks)} audio breaks.")
        
    # Step 3: Run stable-ts to get real word timestamps (or estimate)
    dur = get_audio_duration(path)
    word_timestamps = _apply_stable_ts(path, clean_text)
    if not word_timestamps:
        word_timestamps = _estimate_timestamps(clean_text, dur)
        
    # Step 4: Apply professional FFmpeg mastering chain
    apply_mastering_chain(path, is_elevenlabs=True)
    
    # Step 5: Trim audio silence and optimize gaps
    dur, word_timestamps = trim_audio_silence(path, word_timestamps)
    dur, word_timestamps = optimize_audio_gaps(path, word_timestamps)
    
    print(f"[audio_gen] Audio generation and processing complete. Path: {path}, Duration: {dur:.2f}s")
    return path, dur, word_timestamps

def measure_loudness_and_peaks(audio_path: str) -> tuple[float, float, int]:
    """
    Measures the Integrated Loudness (LUFS), True Peak (TP), and Sample Rate of the audio.
    Returns (lufs, true_peak, sample_rate).
    """
    import soundfile as sf
    sample_rate = 0
    try:
        info = sf.info(audio_path)
        sample_rate = info.samplerate
    except Exception:
        pass
        
    cmd = [
        "ffmpeg", "-i", audio_path,
        "-filter_complex", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    
    lufs = -99.9
    true_peak = -99.9
    
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stderr = res.stderr
        
        # Split by Summary to get final summary block and avoid matching frame-by-frame stats (e.g. matching initial frame's -70 LUFS)
        if "Summary:" in stderr:
            summary_part = stderr.split("Summary:")[-1]
        else:
            summary_part = stderr
            
        # Parse Integrated loudness (I:)
        i_match = re.search(r'I:\s+([-\d.]+)\s+LUFS', summary_part)
        if i_match:
            lufs = float(i_match.group(1))
            
        # Parse True peak (Peak:)
        tp_match = re.search(r'Peak:\s+([-\d.]+)\s+dBFS', summary_part)
        if tp_match:
            true_peak = float(tp_match.group(1))
            
    except Exception as e:
        print(f"⚠️ Failed to measure audio metrics with FFmpeg: {e}")
        
    return lufs, true_peak, sample_rate

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Audio Generation Module")
    parser.add_argument("--test-audio", action="store_true", help="Run audio mastering dry-run test")
    args = parser.parse_args()
    
    if args.test_audio:
        print("Starting Dry-Run Audio Quality & Mastering Test...")
        test_text = "Vanakkam, ithellam theriyuma? Simple Tips by VJ."
        test_wav = os.path.join(OUTPUT_DIR, "test_output.wav")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print(f"Test text: '{test_text}'")
        
        # 1. Synthesize the text
        clean_text = preprocess_script_for_tts(test_text)
        path = _generate_elevenlabs(clean_text, test_wav)
        if not path:
            print("ElevenLabs failed or not configured, using Edge TTS for dry-run test.")
            path = _generate_edge_tts(clean_text, test_wav)
            
        if not path:
            print("Test failed: Could not generate audio using ElevenLabs or Edge TTS fallback.")
            sys.exit(1)
            
        # 2. Run break detection
        breaks = detect_audio_breaks(path)
        print(f"[Test] Detected breaks count: {len(breaks)}")
        for idx, (start, end) in enumerate(breaks, 1):
            print(f"   Break {idx}: {start:.1f}ms to {end:.1f}ms (duration: {end - start:.1f}ms)")
            
        # Fix breaks if any
        if breaks:
            path = fix_audio_breaks(path, breaks)
            
        # 3. Run mastering chain
        apply_mastering_chain(path)
        
        # 4. Measure and print results
        lufs, tp, sr = measure_loudness_and_peaks(path)
        duration = get_audio_duration(path)
        
        print("--- DRY-RUN AUDIO METRICS ---")
        print(f"Output File: {path}")
        print(f"Duration: {duration:.3f}s")
        print(f"LUFS Level: {lufs} LUFS (Target: -14 LUFS)")
        print(f"True Peak: {tp} dBFS (Target: < -1.0 dBFS)")
        print(f"Sample Rate: {sr} Hz (Target: 44100 Hz)")
        print("---------------------------------\n")
        
        if lufs == -99.9 or tp == -99.9:
            print("Metrics extraction incomplete. Make sure FFmpeg is installed and accessible.")
        else:
            print("Dry-run test completed.")

