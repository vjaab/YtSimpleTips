"""
x_upload.py — Robust Auto-Posting Module for X.com (Twitter) for Simple Tips by VJ.

Implements Twitter Media Upload v1.1 API (chunked video upload) + API v2 for Tweeting.
Supports credentials loading, async transcode status polling, and error boundaries.
Adapted for Tamil "Simple Tips by VJ" content with Tamil-specific hashtags.
"""

import os
import time
import requests
from requests_oauthlib import OAuth1
from config import (
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET,
    X_BEARER_TOKEN
)


def _check_credentials() -> bool:
    """Verifies that all required X API credentials are configured."""
    keys = [X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET]
    return all(k and k.strip() for k in keys)


def _generate_tamil_post_text(script_data: dict, youtube_url: str) -> str:
    """
    Generate Tamil-optimized post text for X.com cross-posting.
    Includes Tamil hashtags and engaging format.
    """
    title = script_data.get("title", "Simple Tips by VJ")
    comment_hook = script_data.get("comment_hook", "")
    hashtags = script_data.get("hashtags", ["#தெரியுமா", "#VJVideos", "#SimpleTipsByVJ"])

    # Build Tamil-engaging post
    post_lines = [
        f"🎬 New Tamil Short: {title}",
        "",
        f"🔗 Watch: {youtube_url}",
        "",
    ]

    if comment_hook:
        post_lines.append(f"💬 {comment_hook}")
        post_lines.append("")

    # Add Tamil hashtags (max 3 for X.com)
    tag_str = " ".join(hashtags[:3])
    post_lines.append(tag_str)

    post_text = "\n".join(post_lines)

    # Ensure within X.com 280 character limit
    if len(post_text) > 270:
        post_text = post_text[:267] + "..."

    return post_text


def upload_video_to_x(video_path: str, script_data: dict, youtube_url: str) -> tuple:
    """
    Uploads a video to X.com using OAuth 1.0a User Context and posts it.

    Args:
        video_path (str): Absolute path to the .mp4 video file.
        script_data (dict): The script data containing title, hashtags, etc.
        youtube_url (str): The YouTube URL to reference in the post.

    Returns:
        tuple: (bool success, str result_message_or_id)
    """
    if not _check_credentials():
        return False, "Skipped: X.com credentials not configured in .env"

    if not os.path.exists(video_path):
        return False, f"Error: Video file not found at {video_path}"

    print(f"📡 Initializing chunked video upload to X.com for: {video_path}")
    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    upload_url = "https://upload.twitter.com/1.1/media/upload.json"

    # ── STEP 1: INIT UPLOAD ──
    file_size = os.path.getsize(video_path)
    init_data = {
        "command": "INIT",
        "media_type": "video/mp4",
        "total_bytes": file_size,
        "media_category": "tweet_video"
    }

    try:
        req_init = requests.post(upload_url, data=init_data, auth=auth, timeout=30)
        if req_init.status_code not in (200, 201, 202):
            return False, f"INIT failed (HTTP {req_init.status_code}): {req_init.text}"

        media_id = req_init.json().get("media_id_string")
        if not media_id:
            return False, f"INIT failed: No media_id returned. Response: {req_init.text}"
    except Exception as e:
        return False, f"INIT exception: {e}"

    print(f"✔ INIT complete. Media ID: {media_id}. Starting chunked APPEND...")

    # ── STEP 2: APPEND CHUNKS ──
    chunk_size = 4 * 1024 * 1024  # 4MB chunks
    segment_index = 0

    try:
        with open(video_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                print(f"   Uploading chunk #{segment_index} ({len(chunk)} bytes)...")
                append_data = {
                    "command": "APPEND",
                    "media_id": media_id,
                    "segment_index": segment_index
                }
                files = {"media": chunk}

                req_append = requests.post(upload_url, data=append_data, files=files, auth=auth, timeout=60)
                if req_append.status_code not in (200, 201, 202):
                    return False, f"APPEND chunk #{segment_index} failed: {req_append.text}"

                segment_index += 1
    except Exception as e:
        return False, f"APPEND exception: {e}"

    print("✔ APPEND complete. Finalizing media upload...")

    # ── STEP 3: FINALIZE ──
    finalize_data = {
        "command": "FINALIZE",
        "media_id": media_id
    }

    try:
        req_finalize = requests.post(upload_url, data=finalize_data, auth=auth, timeout=30)
        if req_finalize.status_code not in (200, 201, 202):
            return False, f"FINALIZE failed: {req_finalize.text}"

        finalize_json = req_finalize.json()
    except Exception as e:
        return False, f"FINALIZE exception: {e}"

    # ── STEP 4: STATUS POLLING (Asynchronous Transcode Check) ──
    print("⏳ Waiting for X.com backend to transcode and verify video processing...")
    processing_info = finalize_json.get("processing_info")

    if processing_info:
        state = processing_info.get("state")
        while state in ("pending", "in_progress"):
            check_after = processing_info.get("check_after_secs", 5)
            print(f"   Processing state: {state}. Sleeping for {check_after}s...")
            time.sleep(check_after)

            try:
                status_params = {
                    "command": "STATUS",
                    "media_id": media_id
                }
                req_status = requests.get(upload_url, params=status_params, auth=auth, timeout=20)
                if req_status.status_code == 200:
                    status_json = req_status.json()
                    processing_info = status_json.get("processing_info", {})
                    state = processing_info.get("state")
                else:
                    print(f"⚠️ STATUS check failed (HTTP {req_status.status_code}): {req_status.text}")
            except Exception as e:
                print(f"⚠️ STATUS check exception: {e}")
                time.sleep(5)

        if state == "failed":
            error_msg = processing_info.get("error", {}).get("message", "Unknown transcoding error")
            return False, f"Transcoding failed on X.com: {error_msg}"

    print("✔ Video transcode succeeded! Creating the Tweet...")

    # ── STEP 5: POST TWEET (API v2) ──
    tweet_url = "https://api.twitter.com/2/tweets"
    post_text = _generate_tamil_post_text(script_data, youtube_url)

    tweet_payload = {
        "text": post_text[:280],
        "media": {"media_ids": [media_id]}
    }

    try:
        response = requests.post(tweet_url, json=tweet_payload, auth=auth, timeout=30)
        if response.status_code == 201:
            tweet_id = response.json().get("data", {}).get("id")
            print(f"🎉 Success! Tweet posted to X.com. ID: {tweet_id}")
            return True, tweet_id
        else:
            return False, f"TWEET post failed (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return False, f"TWEET exception: {e}"


def post_text_only_tweet(script_data: dict, youtube_url: str) -> tuple:
    """
    Post a text-only tweet (without video) referencing the YouTube video.
    Useful as fallback when video upload fails or for quick announcements.
    """
    if not _check_credentials():
        return False, "Skipped: X.com credentials not configured"

    auth = OAuth1(X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET)
    tweet_url = "https://api.twitter.com/2/tweets"
    post_text = _generate_tamil_post_text(script_data, youtube_url)

    tweet_payload = {"text": post_text[:280]}

    try:
        response = requests.post(tweet_url, json=tweet_payload, auth=auth, timeout=30)
        if response.status_code == 201:
            tweet_id = response.json().get("data", {}).get("id")
            print(f"🎉 Text-only tweet posted to X.com. ID: {tweet_id}")
            return True, tweet_id
        else:
            return False, f"TWEET post failed (HTTP {response.status_code}): {response.text}"
    except Exception as e:
        return False, f"TWEET exception: {e}"


if __name__ == "__main__":
    print("Testing X.com credentials check...")
    if _check_credentials():
        print("✔ Credentials configured correctly!")
    else:
        print("⚠️ Credentials missing or empty in .env. Auto-posting will be skipped gracefully.")