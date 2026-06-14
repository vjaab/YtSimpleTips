"""
chunk_builder.py — Regroups visual chunks using real audio timestamps and Gemini's subtitle_chunks template.
Bilingual Tamil + English support.
"""

import re

def build_chunks(word_timestamps, subtitle_chunks):
    """
    Groups word timestamps into visual chunks based on the Gemini subtitle_chunks template.
    Overrides Gemini's estimated timestamps with the REAL timestamps from audio.
    Uses a robust lookahead word-by-word sequence alignment algorithm.
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

    # Flatten all words from subtitle chunks to align them
    # flat_chunk_words: list of (chunk_idx, cleaned_word, original_word)
    flat_chunk_words = []
    for c_idx, gc in enumerate(subtitle_chunks):
        words = gc.get("text", "").split()
        for w in words:
            cleaned = strip_punc(w)
            if cleaned:
                flat_chunk_words.append((c_idx, cleaned, w))

    if not flat_chunk_words:
        print("WARNING: No text found in subtitle_chunks. Falling back to audio-based chunking.")
        return _fallback_build_chunks(word_timestamps)

    # Initialize a map from chunk index to list of assigned word timestamps
    chunk_words_map = {i: [] for i in range(len(subtitle_chunks))}
    
    p = 0  # pointer in flat_chunk_words
    num_chunk_words = len(flat_chunk_words)
    
    for w_idx, wdata in enumerate(word_timestamps):
        w_clean = strip_punc(wdata["word"])
        if not w_clean:
            # If the word is empty after cleaning, assign to the current chunk
            chunk_idx = flat_chunk_words[min(p, num_chunk_words - 1)][0]
            chunk_words_map[chunk_idx].append(wdata)
            continue
            
        best_j = -1
        lookahead = 6
        
        # 1. Lookahead for exact match
        for offset in range(lookahead):
            j = p + offset
            if j >= num_chunk_words:
                break
            if flat_chunk_words[j][1] == w_clean:
                best_j = j
                break
                
        # 2. Lookahead for fuzzy/prefix/suffix/contains match
        if best_j == -1:
            for offset in range(lookahead):
                j = p + offset
                if j >= num_chunk_words:
                    break
                c_word = flat_chunk_words[j][1]
                if c_word.startswith(w_clean) or w_clean.startswith(c_word):
                    best_j = j
                    break

        if best_j != -1:
            # Found match at best_j!
            chunk_idx = flat_chunk_words[best_j][0]
            chunk_words_map[chunk_idx].append(wdata)
            p = best_j + 1  # advance pointer past the match
        else:
            # No match in lookahead window, assign to the current pointer's chunk
            chunk_idx = flat_chunk_words[min(p, num_chunk_words - 1)][0]
            chunk_words_map[chunk_idx].append(wdata)

    # Reconstruct chunks with real timestamps
    final_chunks = []
    for c_idx, gc in enumerate(subtitle_chunks):
        c_words = chunk_words_map[c_idx]
        final_gc = dict(gc)
        final_gc["words"] = c_words
        
        if c_words:
            final_gc["start"] = c_words[0]["start"]
            final_gc["end"] = max(c_words[-1]["end"], final_gc["start"] + 0.1)
        else:
            # Interpolate timing if no words were assigned to prevent chunk loss
            if final_chunks:
                final_gc["start"] = final_chunks[-1]["end"]
            else:
                final_gc["start"] = 0.0
            final_gc["end"] = final_gc["start"] + 1.0
            
        final_gc["duration"] = final_gc["end"] - final_gc["start"]
        final_chunks.append(final_gc)

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
