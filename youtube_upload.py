import os
import time
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
from config import YOUTUBE_CLIENT_SECRET_FILE

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]

# ── Rotating Tamil pinned comment templates (5 variants for anti-repetition) ──
PINNED_COMMENT_TEMPLATES = [
    """💡 இந்த மாதிரி இன்னும் பல பயனுள்ள குறிப்புகள் மற்றும் Life Hacks தெரிஞ்சுக்க நம்ம Telegram group-ல join பண்ணுங்க!

🚀 Daily Useful Tips and Life Hacks in Tamil
💬 Simple Tips by VJ-க்கு மறக்காம Subscribe பண்ணுங்க!
🔗 Telegram Link → channel home page-ல இருக்கு!""",

    """🔥 உங்களுக்கு இந்த simple tip பிடிச்சிருந்தா, உங்க friends-க்கு share பண்ணுங்க!

நம்ம channel-ல daily பயனுள்ள குறிப்புகள் உங்களுக்காக:
→ மொபைல் & டெக் ஹேக்ஸ் 📱
→ படிப்பை எளிதாக்கும் டிப்ஸ் 🧠
→ உடல் நலம் & வீட்டு குறிப்புகள் 💊

📲 Channel profile header-ல இருக்கற Telegram link-ஐ கிளிக் பண்ணி join பண்ணிக்கோங்க!""",

    """⚡ இந்த குறிப்புகள் பத்தின கூடுதல் விவரங்களை நம்ம Telegram group-ல share பண்ணியிருக்கோம்!

ஏன் join பண்ணனும்?
• Daily life hacks & tips in Tamil
• Easy and useful techniques daily

Join immediately! Simple Tips by VJ-க்கு Subscribe பண்ண மறந்துடாதீங்க!""",

    """🎯 இந்த tip உங்களுக்கு useful-ஆ இருந்தா, comment-ல ✅ போடுங்க!

VJ-கிட்ட நேரடியா tips கேக்கணும்னா → Telegram group join பண்ணுங்க!
📲 Link → Channel home page-ல இருக்கு

நன்றி, Happy Learning! 🙏""",

    """📚 தினமும் ஒரு புது tip கத்துக்கலாம்! Simple Tips by VJ

இன்னும் இது மாதிரி useful tips வேணும்னா:
1️⃣ Subscribe + 🔔 Bell icon ON பண்ணுங்க
2️⃣ Telegram group-ல join பண்ணுங்க (link → channel page)
3️⃣ உங்க friends-க்கு share பண்ணுங்க!"""
]

def _get_pinned_comment(title=""):
    import hashlib
    seed = int(hashlib.md5(title.encode()).hexdigest(), 16)
    idx = seed % len(PINNED_COMMENT_TEMPLATES)
    return PINNED_COMMENT_TEMPLATES[idx]

def get_authenticated_service():
    if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
        print("⚠️ YouTube client secret file not found in workspace.")
        return None
        
    creds = None
    token_path = "token.json"
    
    if os.path.exists(token_path):
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    if not creds or not creds.valid:
        from google.auth.transport.requests import Request
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                YOUTUBE_CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=8080, prompt='consent')
            
        with open(token_path, "w") as token:
            token.write(creds.to_json())
            
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        return youtube
    except Exception as e:
        print(f"❌ YouTube auth failed: {e}")
        return None

def crop_for_instagram(video_path):
    """
    Crops the top 80px watermark header strip using FFmpeg.
    Uses crop=in_w:in_h-80:0:80 to crop the top 80 pixels.
    """
    import subprocess
    base, ext = os.path.splitext(video_path)
    cropped_path = f"{base}_cropped{ext}"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", "crop=in_w:in_h-80:0:80",
        "-c:a", "copy",
        cropped_path
    ]
    print(f"🎬 Running FFmpeg crop for Instagram: {' '.join(cmd)}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return cropped_path

def crosspost_to_instagram(cropped_video_path, caption):
    """
    Cross-posts the cropped video to Instagram Reels using the Meta Graph API.
    """
    import requests
    import os
    
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    public_video_url = os.getenv("PUBLIC_VIDEO_URL", "")
    
    if not access_token or not business_account_id:
        print("⚠️ Instagram credentials (INSTAGRAM_ACCESS_TOKEN/INSTAGRAM_BUSINESS_ACCOUNT_ID) missing. Skipping Instagram cross-posting.")
        return False, "Credentials missing"
        
    if not public_video_url:
        print("⚠️ PUBLIC_VIDEO_URL is missing. Meta Graph API requires a public URL to download the video. Skipping Instagram publish.")
        return False, "PUBLIC_VIDEO_URL missing"
        
    print(f"📡 Initiating Instagram Reels upload container for: {cropped_video_path}...")
    
    url = f"https://graph.facebook.com/v19.0/{business_account_id}/media"
    payload = {
        "media_type": "REELS",
        "video_url": public_video_url,
        "caption": caption,
        "access_token": access_token
    }
    
    try:
        r = requests.post(url, data=payload, timeout=20)
        if r.status_code != 200:
            print(f"❌ Instagram container creation failed: {r.text}")
            return False, r.text
            
        res = r.json()
        container_id = res.get("id")
        print(f"✅ Instagram Reel container created: {container_id}")
        
        poll_url = f"https://graph.facebook.com/v19.0/{container_id}"
        params = {
            "fields": "status_code",
            "access_token": access_token
        }
        
        max_polls = 12
        for attempt in range(max_polls):
            time.sleep(10)
            pr = requests.get(poll_url, params=params, timeout=15)
            if pr.status_code == 200:
                status = pr.json().get("status_code", "").upper()
                print(f"⏳ Reel container status: {status} (attempt {attempt+1}/{max_polls})")
                if status == "FINISHED":
                    break
                elif status == "ERROR":
                    print(f"❌ Instagram processing error: {pr.text}")
                    return False, "Processing error"
            else:
                print(f"⚠️ Instagram container polling failed: {pr.text}")
        else:
            print("⚠️ Reel processing timed out on Meta servers.")
            return False, "Processing timeout"
            
        publish_url = f"https://graph.facebook.com/v19.0/{business_account_id}/media_publish"
        publish_payload = {
            "creation_id": container_id,
            "access_token": access_token
        }
        
        pr = requests.post(publish_url, data=publish_payload, timeout=20)
        if pr.status_code == 200:
            publish_res = pr.json()
            media_id = publish_res.get("id")
            print(f"🎉 Instagram Reel published successfully! Media ID: {media_id}")
            return True, media_id
        else:
            print(f"❌ Instagram Reel publish failed: {pr.text}")
            return False, pr.text
            
    except Exception as e:
        print(f"⚠️ Instagram cross-posting failed with exception: {e}")
        return False, str(e)

def upload_video(video_path, title, description, tags, thumbnail_path=None, category_id="28", comment_hook=None, comment_bait_question=None):
    """Uploads the generated Shorts video to YouTube with Tamil metadata and Altered Content flag."""
    youtube = get_authenticated_service()
    if not youtube:
        return False, "Failed to authenticate with YouTube API"

    # YouTube API does not allow angle brackets '<' and '>' in video titles.
    # Sanitize the title by removing them to prevent 400 Bad Request errors.
    title = title.replace("<", "").replace(">", "").strip()

    # Ensure #Shorts is in the description for algorithm classification
    if "#Shorts" not in description and "#shorts" not in description:
        description = description.rstrip() + "\n\n#Shorts #SimpleTipsByVJ #TamilTips"

    body = {
        "snippet": {
            "title":                title[:40],
            "description":          description[:5000],
            "tags":                 tags[:15],
            "categoryId":           category_id,  # 28 = Science & Tech
            "defaultLanguage":      "ta",
            "defaultAudioLanguage": "ta",
        },
        "status": {
            "privacyStatus":            "public",
            "selfDeclaredMadeForKids":    False,
            # AI disclosure ("Altered Content"): Automatically set via containsSyntheticMedia for YPP compliance.
            "containsSyntheticMedia":     True,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    try:
        response = request.execute()
        video_id = response.get("id")
        print(f"🎉 Video uploaded successfully: https://youtu.be/{video_id}")

        # 1. Upload Thumbnail
        if thumbnail_path and os.path.exists(thumbnail_path):
            try:
                set_thumbnail(youtube, video_id, thumbnail_path)
            except Exception as e:
                print(f"⚠️ Thumbnail upload failed (non-fatal): {e}")

        # 2. Post Pinned Comment
        try:
            pinned_text = _get_pinned_comment(title)
            if comment_bait_question:
                full_comment = f"❓ {comment_bait_question}\n\n{pinned_text}"
            elif comment_hook:
                full_comment = f"{comment_hook}\n\n{pinned_text}"
            else:
                full_comment = pinned_text
            post_and_pin_comment(youtube, video_id, full_comment)
        except Exception as e:
            print(f"⚠️ Pinned comment failed (non-fatal): {e}")

        # 3. Instagram Reels Cross-Post
        try:
            cropped_video = crop_for_instagram(video_path)
            crosspost_to_instagram(cropped_video, f"{title}\n\n{description[:100]}...")
            if cropped_video and os.path.exists(cropped_video):
                os.remove(cropped_video)
        except Exception as ie:
            print(f"⚠️ Instagram cross-posting failed (non-fatal): {ie}")

        return True, video_id
    except googleapiclient.errors.HttpError as e:
        print(f"❌ YouTube upload error {e.resp.status}: {e.content}")
        return False, str(e)

def post_and_pin_comment(youtube, video_id, comment_text):
    comment_response = youtube.commentThreads().insert(
        part="snippet",
        body={
            "snippet": {
                "videoId": video_id,
                "topLevelComment": {
                    "snippet": {
                        "textOriginal": comment_text
                    }
                }
            }
        }
    ).execute()

    comment_id = comment_response["snippet"]["topLevelComment"]["id"]
    print(f"💬 Comment posted: {comment_id}")

    youtube.comments().setModerationStatus(
        id=comment_id,
        moderationStatus="published",
        banAuthor=False
    ).execute()

    print("📌 Comment pinned.")
    return comment_id

def set_thumbnail(youtube, video_id, thumbnail_path):
    print(f"⏳ Waiting 5s for YouTube to index video {video_id} before uploading thumbnail...")
    time.sleep(5) 
    
    print(f"📤 Uploading custom thumbnail: {thumbnail_path}...")
    try:
        request = youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg", resumable=True)
        )
        response = request.execute()
        print("✅ Custom thumbnail uploaded and set!")
        return response
    except Exception as e:
        print(f"⚠️ Custom thumbnail upload failed: {e}")
        raise e
