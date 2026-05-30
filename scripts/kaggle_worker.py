import os
import subprocess
import shutil
import sys
import json
import time
import re

# 🚀 KAGGLE GPU WORKER FOR Automated Tamil YouTube Shorts (IndicF5 Tamil Voice Cloning)

def run_cmd(cmd, cwd=None, quiet=False):
    if quiet:
        subprocess.run(cmd, cwd=cwd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"Executing: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=cwd, check=True)

def setup_project():
    print("🖥️ Installing System Dependencies (espeak-ng, ffmpeg)...")
    try:
        subprocess.run(["apt-get", "update"], check=False)
        subprocess.run(["apt-get", "install", "-y", "espeak-ng", "ffmpeg"], check=False)
    except Exception as e:
        print(f"⚠️ System dependency warning: {e}")

    print("📦 Installing Python Dependencies...")
    run_cmd(["pip", "install", "-q", "-U", "pip", "setuptools<70", "wheel", "packaging"])
    
    # Install PyTorch, F5-TTS, stable-ts, pydub
    run_cmd(["pip", "install", "-q", "f5-tts", "stable-ts", "pydub", "soundfile", "mutagen", "edge-tts", "elevenlabs"])
    
    print("✅ System dependencies and Python packages installed successfully!")

def _smart_split_sentences(text, max_chars=120):
    import re
    # Split text into natural sentence-boundary chunks under max_chars to prevent clipping
    parts = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""
    for part in parts:
        if len(current + " " + part) < max_chars:
            current = (current + " " + part).strip()
        else:
            if current:
                chunks.append(current.strip())
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
    try:
        from pydub import AudioSegment
        from pydub.effects import normalize, compress_dynamic_range
        
        audio = AudioSegment.from_wav(wav_path)
        
        # High-pass filter at 120Hz to remove low-frequency room rumble
        audio = audio.high_pass_filter(120)
        
        # Three-Band EQ Boost
        lows = audio.low_pass_filter(200).high_pass_filter(100)
        mids = audio.high_pass_filter(200).low_pass_filter(3000)
        highs = audio.high_pass_filter(3000)
        
        lows = lows + 1.5   # Chest warmth
        highs = highs + 3.5 # Crisp presence and air
        
        audio = lows.overlay(mids).overlay(highs)
        
        # Dynamic Range Compression
        audio = compress_dynamic_range(audio, threshold=-15.0, ratio=3.0, attack=5.0, release=50.0)
        
        # Final Normalization to -1dB
        audio = normalize(audio, headroom=1.0)
        audio = audio.fade_in(5).fade_out(5)
        
        audio.export(wav_path, format="wav")
        print(f"   🔊 Audio enhanced: HPF, 3-band presence EQ, compression, normalization applied.")
    except Exception as e:
        print(f"   ⚠️ Audio post-processing warning: {e}")

def process_job():
    print("🎬 Starting Tamil Voice Cloning GPU Job...")
    
    if "JOB_PAYLOAD" in globals():
        job_data = globals()["JOB_PAYLOAD"]
    elif os.path.exists("job_data.json"):
        with open("job_data.json", 'r', encoding='utf-8') as f:
            job_data = json.load(f)
    else:
        print("🚨 Job Data not found. Exiting.")
        return

    script = job_data.get("script")
    print(f"📄 Script to clone:\n{script}")

    # Voice Reference Details
    ref_wav = "vj.wav"
    if not os.path.exists(ref_wav):
        # Check standard location in workspace or dataset
        ref_wav = "/kaggle/working/vj.wav"
        if not os.path.exists(ref_wav):
            ref_wav = "YtDidYouKnowByVJ/assets/vj.wav"
            if not os.path.exists(ref_wav):
                ref_wav = None

    if not ref_wav:
        print("🚨 Reference voice vj.wav not found! Aborting.")
        raise FileNotFoundError("vj.wav missing")

    # English reference text corresponding to vj.wav
    ref_text = "Welcome you are listening to your channel, we bring you the best insights, ideas and stories. Drafted just for you Stay tuned and let's get started."
    
    print(f"🎙️ Using reference audio: {ref_wav}")
    
    # ── STEP 1: IndicF5 / F5-TTS Synthesis ──
    print("⏳ Loading F5-TTS Model...")
    import torch
    from f5_tts.api import F5TTS
    from pydub import AudioSegment

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚡ Device detected: {device}")
    
    f5 = F5TTS(device=device)
    
    chunks = _smart_split_sentences(script, max_chars=120)
    print(f"📝 Split script into {len(chunks)} text chunks for synthesis.")
    
    segment_paths = []
    for i, chunk in enumerate(chunks):
        seg_path = f"seg_{i}.wav"
        print(f"🗣️ Synthesizing chunk {i+1}/{len(chunks)}: {chunk}")
        f5.infer(
            ref_file=ref_wav,
            ref_text=ref_text,
            gen_text=chunk,
            file_wave=seg_path,
            nfe_step=64,
            remove_silence=True,
            speed=1.0
        )
        segment_paths.append(seg_path)

    # Join segments
    CROSSFADE_MS = 30
    combined = AudioSegment.from_wav(segment_paths[0]) if segment_paths else AudioSegment.empty()
    for sp in segment_paths[1:]:
        seg = AudioSegment.from_wav(sp)
        combined = combined.append(seg, crossfade=CROSSFADE_MS)
        
    # Clean up segments
    for sp in segment_paths:
        try: os.remove(sp)
        except: pass

    output_wav = "/kaggle/working/audio.wav"
    combined.export(output_wav, format="wav")
    print(f"✅ Joined segments successfully. Base duration: {len(combined)/1000.0:.2f}s")

    # Post process audio
    _postprocess_voice_audio(output_wav)

    # ── STEP 2: Word timestamps via stable-whisper ──
    print("⏳ Loading stable-whisper for Tamil/Tanglish alignment...")
    import stable_whisper
    
    model = stable_whisper.load_model('tiny', device=device)
    
    # Clean script from any formatting/meta details for Whisper aligner
    clean_script = re.sub(r'\[[^\]]*\]|\([^)]*\)', '', script)
    clean_script = re.sub(r'\s+', ' ', clean_script).strip()
    
    print(f"📖 Aligning clean script: {clean_script}")
    
    # Run alignment using GPU/CPU with Tamil/English mixed detection
    result = model.align(output_wav, clean_script, language='ta')
    
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

    duration = len(combined) / 1000.0
    
    if not word_timestamps:
        print("⚠️ stable-whisper alignment returned empty! Estimating timestamps.")
        words = clean_script.split()
        interval = duration / len(words)
        word_timestamps = [
            {"word": w, "start": round(i * interval, 3), "end": round((i + 1) * interval, 3)}
            for i, w in enumerate(words)
        ]

    print(f"✅ Alignment finished. Extracted {len(word_timestamps)} word timestamps.")

    # ── STEP 3: Save results.json ──
    results = {
        "audio_path": "audio.wav",
        "duration": duration,
        "word_timestamps": word_timestamps
    }
    
    with open("/kaggle/working/results.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
        
    print("🚀 Kaggle job complete! Saved audio.wav and results.json.")

if __name__ == "__main__":
    try:
        print("--- Kaggle Worker Running ---")
        setup_project()
        process_job()
    except Exception as e:
        print(f"🚨 CRITICAL WORKER FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
