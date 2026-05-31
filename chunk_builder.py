"""
chunk_builder.py — Regroups visual chunks using real audio timestamps and Gemini's subtitle_chunks template.
Bilingual Tamil + English support.
"""

import re

def build_chunks(word_timestamps, subtitle_chunks):
    """
    Groups word timestamps into visual chunks based on the Gemini subtitle_chunks template.
    Overrides Gemini's estimated timestamps with the REAL timestamps from audio.
    """
    if not word_timestamps:
        return []
        
    # Flatten subtitle_chunks to handle nested lists returned by Gemini
    flat_subtitle_chunks = []
    for gc in subtitle_chunks or []:
        if isinstance(gc, list):
            for item in gc:
                if isinstance(item, dict):
                    flat_subtitle_chunks.append(item)
        elif isinstance(gc, dict):
            flat_subtitle_chunks.append(gc)
    subtitle_chunks = flat_subtitle_chunks
    
    if not subtitle_chunks or len(subtitle_chunks) < 3:
        if subtitle_chunks and len(subtitle_chunks) < 3:
            print(f"WARNING: Gemini only produced {len(subtitle_chunks)} subtitle_chunks. Falling back to audio-based chunking.")
        return _fallback_build_chunks(word_timestamps)

    # Allow Tamil characters [0B80 - 0BFF] as alphanumeric tokens so they match correctly!
    def strip_punc(s):
        return re.sub(r'[^a-zA-Z0-9\u0b80-\u0bff]', '', s).lower()

    word_idx = 0
    num_words = len(word_timestamps)
    final_chunks = []

    for gc in subtitle_chunks:
        chunk_text = gc.get("text", "")
        target_len = sum(len(strip_punc(w)) for w in chunk_text.split())
        
        chunk_words = []
        current_len = 0
        
        while word_idx < num_words and current_len < target_len * 0.85:
            wdata = word_timestamps[word_idx]
            chunk_words.append(wdata)
            current_len += len(strip_punc(wdata["word"]))
            word_idx += 1
            
        if not chunk_words:
            continue
            
        final_gc = dict(gc)
        final_gc["words"] = chunk_words
        
        # Override with REAL timestamps, ensuring a minimum duration of 0.1s
        final_gc["start"] = chunk_words[0]["start"]
        final_gc["end"] = max(chunk_words[-1]["end"], final_gc["start"] + 0.1)
        final_gc["duration"] = final_gc["end"] - final_gc["start"]
        
        final_chunks.append(final_gc)

    # Fallback if alignment rate is poor
    if len(final_chunks) < len(subtitle_chunks) * 0.5:
        print(f"WARNING: Subtitle alignment poor ({len(final_chunks)}/{len(subtitle_chunks)}). Falling back to audio-based chunks.")
        return _fallback_build_chunks(word_timestamps)

    # Enforce non-overlap and adjust end times appropriately
    for i in range(len(final_chunks) - 1):
        if final_chunks[i]["end"] > final_chunks[i+1]["start"]:
             final_chunks[i+1]["start"] = final_chunks[i]["end"]
             if final_chunks[i+1]["end"] < final_chunks[i+1]["start"] + 0.1:
                 final_chunks[i+1]["end"] = final_chunks[i+1]["start"] + 0.1
             final_chunks[i+1]["duration"] = final_chunks[i+1]["end"] - final_chunks[i+1]["start"]

    return final_chunks

def _fallback_build_chunks(word_timestamps):
    MIN_DURATION  = 1.0
    MAX_DURATION  = 2.5
    TARGET_WORDS  = 2

    chunks = []
    current_words = []

    for i, word_data in enumerate(word_timestamps):
        current_words.append(word_data)
        word_count = len(current_words)
        current_start = current_words[0]["start"]
        current_end   = word_data["end"]
        current_dur   = current_end - current_start
        is_last_word = (i == len(word_timestamps) - 1)
        should_close = False

        if is_last_word or current_dur >= MAX_DURATION:
            should_close = True
        elif word_count >= TARGET_WORDS and current_dur >= MIN_DURATION:
            if re.search(r'[.!?]$', word_data["word"].strip()) or re.search(r'[,;:\-]$', word_data["word"].strip()) or word_count >= TARGET_WORDS + 2:
                should_close = True

        if should_close:
            safe_end = max(current_end, current_start + 0.1)
            chunks.append({
                "chunk_id": len(chunks) + 1,
                "text":     " ".join(w["word"] for w in current_words),
                "words":    list(current_words),
                "start":    current_start,
                "end":      safe_end,
                "duration": safe_end - current_start,
            })
            current_words = []
            
    return chunks

def redistribute_to_audio_duration(chunks, audio_duration):
    if not chunks:
        return chunks

    # 1. Enforce chronological non-overlap (push starts forward if needed)
    for i in range(len(chunks) - 1):
        if chunks[i]["end"] > chunks[i+1]["start"]:
             chunks[i+1]["start"] = chunks[i]["end"]
             if chunks[i+1]["end"] < chunks[i+1]["start"] + 0.1:
                 chunks[i+1]["end"] = chunks[i+1]["start"] + 0.1
             chunks[i+1]["duration"] = chunks[i+1]["end"] - chunks[i+1]["start"]

    # 2. Force the first chunk to start exactly at 0.0s
    chunks[0]["start"] = 0.0
    chunks[0]["duration"] = chunks[0]["end"] - chunks[0]["start"]

    # 3. Connect all chunks sequentially to eliminate any remaining gaps
    for i in range(len(chunks) - 1):
        chunks[i]["end"] = chunks[i+1]["start"]
        chunks[i]["duration"] = chunks[i]["end"] - chunks[i]["start"]
        chunks[i+1]["duration"] = chunks[i+1]["end"] - chunks[i+1]["start"]

    # 4. Enforce that the last chunk covers the total audio duration
    last_chunk = chunks[-1]
    last_chunk["end"] = max(last_chunk["end"], audio_duration, last_chunk["start"] + 0.1)
    last_chunk["duration"] = last_chunk["end"] - last_chunk["start"]

    return chunks
