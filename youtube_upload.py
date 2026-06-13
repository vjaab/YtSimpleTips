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

# ── Rotating Tamil pinned comment templates ──
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

Join immediately! Simple Tips by VJ-க்கு Subscribe பண்ண மறந்துடாதீங்க!"""
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

def upload_video(video_path, title, description, tags, thumbnail_path=None, category_id="28", comment_hook=None):
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
            "categoryId":           category_id,  # 28 = Science & Tech (better for tech tips, higher CPM)
            "defaultLanguage":      "ta",
            "defaultAudioLanguage": "ta",
        },
        "status": {
            "privacyStatus":            "public",
            "selfDeclaredMadeForKids":    False,
            # Mandatory FTC disclosure for synthetic content / voice cloning
            "selfDeclaredAlteredContent": True,
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
            full_comment = f"{title}\n\n{comment_hook}\n\n{pinned_text}" if comment_hook else pinned_text
            post_and_pin_comment(youtube, video_id, full_comment)
        except Exception as e:
            print(f"⚠️ Pinned comment failed (non-fatal): {e}")

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
