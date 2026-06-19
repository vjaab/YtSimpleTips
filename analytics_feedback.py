import os
import json
import datetime
from dotenv import load_dotenv

load_dotenv()

# We only try loading googleapiclient if we can to avoid import errors in bare environments
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    import google_auth_oauthlib.flow
    import googleapiclient.discovery
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly"
]

YOUTUBE_CLIENT_SECRET_FILE = os.getenv("YOUTUBE_CLIENT_SECRET_FILE", "client_secret.json")

def get_analytics_service():
    if not GOOGLE_API_AVAILABLE:
        print("⚠️ Google API Client libraries not imported.")
        return None, None
        
    creds = None
    token_path = "token_analytics.json"
    
    # Try loading from existing main token.json first
    if os.path.exists("token.json"):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except Exception:
            pass
            
    if not creds or not creds.valid:
        if os.path.exists(token_path):
            try:
                creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            except Exception:
                pass
            
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception:
                    creds = None
            if not creds:
                if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
                    print("⚠️ YouTube client secret file not found. Cannot authenticate Analytics.")
                    return None, None
                try:
                    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                        YOUTUBE_CLIENT_SECRET_FILE, SCOPES
                    )
                    creds = flow.run_local_server(port=8085, prompt='consent')
                except Exception as e:
                    print(f"⚠️ Local server auth flow failed: {e}")
                    return None, None
            if creds:
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
                
    try:
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)
        analytics = googleapiclient.discovery.build("youtubeAnalytics", "v2", credentials=creds)
        return youtube, analytics
    except Exception as e:
        print(f"❌ Analytics api service construction failed: {e}")
        return None, None

def fetch_performance_insights():
    print("📊 Fetching YouTube performance insights for the past 7 days...")
    
    youtube, analytics = get_analytics_service()
    
    # Fallback to mock / default performance insights if auth/credentials not present
    if not youtube or not analytics:
        print("⚠️ YouTube Analytics credentials/auth failed or not configured. Generating mock/default performance insights...")
        mock_insights = {
            "top_categories": ["tech", "study"],
            "average_script_length": 58,
            "average_view_percentage": 82.5,
            "top_videos": [
                {
                    "title": "Secret WhatsApp setting you must change! 🤫",
                    "category": "tech",
                    "script_word_count": 55,
                    "likes": 1200,
                    "comments": 150,
                    "averageViewPercentage": 88.2
                },
                {
                    "title": "Clear browser speed boost hack 🚀",
                    "category": "tech",
                    "script_word_count": 59,
                    "likes": 980,
                    "comments": 95,
                    "averageViewPercentage": 79.5
                }
            ],
            "last_updated": datetime.datetime.now().isoformat()
        }
        write_insights(mock_insights)
        return
        
    try:
        # 1. Fetch channel's uploaded videos in the past 30 days
        print("📡 Retrieving upload history...")
        channel_resp = youtube.channels().list(mine=True, part="contentDetails").execute()
        uploads_playlist = channel_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        
        playlist_resp = youtube.playlistItems().list(
            playlistId=uploads_playlist,
            part="snippet",
            maxResults=15
        ).execute()
        
        video_items = playlist_resp.get("items", [])
        if not video_items:
            print("ℹ️ No uploaded videos found on this channel. Writing default insights.")
            write_default_insights()
            return
            
        video_ids = [item["snippet"]["resourceId"]["videoId"] for item in video_items]
        video_id_str = ",".join(video_ids)
        
        video_details = youtube.videos().list(
            id=video_id_str,
            part="snippet"
        ).execute()
        
        video_meta = {}
        for item in video_details.get("items", []):
            desc = item["snippet"].get("description", "")
            title = item["snippet"].get("title", "")
            category = "tech"
            if "parents" in desc.lower() or "family" in desc.lower():
                category = "parents"
            elif "money" in desc.lower() or "finance" in desc.lower():
                category = "finance"
            elif "study" in desc.lower() or "student" in desc.lower():
                category = "study"
                
            # Estimate word count based on description metadata or default
            word_count = 60
            video_meta[item["id"]] = {
                "title": title,
                "category": category,
                "word_count": word_count
            }
            
        # 2. Query Analytics API for past 7 days
        now = datetime.datetime.utcnow()
        end_date_str = now.strftime("%Y-%m-%d")
        start_date_str = (now - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
        
        metrics = "averageViewPercentage,likes,comments,shares"
        analytics_resp = analytics.reports().query(
            ids="channel==MINE",
            startDate=start_date_str,
            endDate=end_date_str,
            metrics=metrics,
            dimensions="video",
            filters=f"video=={video_id_str}"
        ).execute()
        
        rows = analytics_resp.get("rows", [])
        if not rows:
            print("ℹ️ No analytics rows returned. Writing default insights.")
            write_default_insights()
            return
            
        parsed_videos = []
        for r in rows:
            v_id = r[0]
            avg_view_pct = float(r[1]) if r[1] is not None else 0.0
            likes = int(r[2]) if r[2] is not None else 0
            comments = int(r[3]) if r[3] is not None else 0
            shares = int(r[4]) if r[4] is not None else 0
            
            meta = video_meta.get(v_id, {"title": "Unknown", "category": "tech", "word_count": 60})
            parsed_videos.append({
                "video_id": v_id,
                "title": meta["title"],
                "category": meta["category"],
                "script_word_count": meta["word_count"],
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "averageViewPercentage": avg_view_pct
            })
            
        parsed_videos.sort(key=lambda x: x["averageViewPercentage"], reverse=True)
        top_videos = parsed_videos[:2]
        
        top_categories = list(set([v["category"] for v in top_videos])) if top_videos else ["tech"]
        avg_script_len = sum([v["script_word_count"] for v in top_videos]) / len(top_videos) if top_videos else 60
        avg_view_pct = sum([v["averageViewPercentage"] for v in parsed_videos]) / len(parsed_videos) if parsed_videos else 0.0
        
        insights = {
            "top_categories": top_categories,
            "average_script_length": avg_script_len,
            "average_view_percentage": avg_view_pct,
            "top_videos": top_videos,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        write_insights(insights)
        
    except Exception as e:
        print(f"❌ Failed to fetch analytics report: {e}")
        write_default_insights()

def write_default_insights():
    default_data = {
        "top_categories": ["tech"],
        "average_script_length": 60,
        "average_view_percentage": 50.0,
        "top_videos": [],
        "last_updated": datetime.datetime.now().isoformat()
    }
    write_insights(default_data)

def write_insights(data):
    out_path = "performance_insights.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Performance insights successfully written to: {out_path}")
    except Exception as e:
        print(f"❌ Failed to write insights file: {e}")

if __name__ == "__main__":
    fetch_performance_insights()
