"""
📤 YouTube Uploader — YouTube Data API v3
Handles OAuth authentication and video uploads with full metadata.
Supports: thumbnails, tags, descriptions, scheduled publishing.
"""

import os
import json
import pickle
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
CONFIG_DIR = Path(__file__).parent.parent / "config"


def get_youtube_service():
    """
    Authenticate with YouTube API using OAuth 2.0.
    First run opens browser for authorization, then saves token.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
    except ImportError:
        raise ImportError(
            "❌ Install YouTube upload dependencies:\n"
            "   pip install google-auth google-auth-oauthlib google-api-python-client"
        )
    
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    token_path = CONFIG_DIR / "youtube_token.pickle"
    creds_path = CONFIG_DIR / "youtube_oauth.json"
    
    creds = None
    
    if token_path.exists():
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing YouTube token...")
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"❌ YouTube OAuth file not found: {creds_path}\n"
                    "   1. Go to https://console.cloud.google.com/\n"
                    "   2. Enable YouTube Data API v3\n"
                    "   3. Create OAuth 2.0 credentials (Desktop App)\n"
                    "   4. Download JSON → save as config/youtube_oauth.json"
                )
            
            print("🔐 First-time YouTube authorization — browser will open...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
        print("✅ YouTube token saved!")
    
    return build("youtube", "v3", credentials=creds)


def upload_video(video_path, title, description, tags=None, 
                 thumbnail_path=None, category_id="28", 
                 privacy="public", scheduled_time=None):
    """
    Upload video to YouTube.
    
    Args:
        video_path: Path to video file
        title: Video title (max 100 chars)
        description: Description (max 5000 chars)
        tags: List of tags
        thumbnail_path: Custom thumbnail image
        category_id: YouTube category (28 = Science & Tech)
        privacy: "public", "private", or "unlisted"
        scheduled_time: ISO datetime for scheduled publish
    
    Returns:
        dict with video_id and url
    """
    try:
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        raise ImportError("❌ pip install google-api-python-client")
    
    youtube = get_youtube_service()
    
    print(f"📤 Uploading: {title[:60]}...")
    print(f"🔒 Privacy: {privacy}")
    
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:500],
            "categoryId": category_id,
            "defaultLanguage": "hi",
            "defaultAudioLanguage": "hi"
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "embeddable": True,
            "publicStatsViewable": True
        }
    }
    
    if scheduled_time and privacy == "private":
        body["status"]["publishAt"] = scheduled_time
    
    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=10 * 1024 * 1024
    )
    
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  📊 {int(status.progress() * 100)}% uploaded")
    
    video_id = response["id"]
    video_url = f"https://youtube.com/watch?v={video_id}"
    
    print(f"✅ Uploaded: {video_url}")
    
    # Set thumbnail
    if thumbnail_path and os.path.exists(thumbnail_path):
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(thumbnail_path, mimetype="image/jpeg")
            ).execute()
            print("✅ Thumbnail set!")
        except Exception as e:
            print(f"⚠️ Thumbnail failed (need verified account): {e}")
    
    result = {
        "video_id": video_id,
        "url": video_url,
        "title": title,
        "uploaded_at": datetime.now().isoformat(),
        "privacy": privacy
    }
    
    _log_upload(result)
    return result


def _log_upload(data):
    """Save upload record."""
    log_dir = OUTPUT_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    with open(log_dir / "uploads.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def build_description(script_data, channel_name="YourChannel"):
    """Build professional YouTube description from script data."""
    parts = []
    
    title = script_data.get("title", "")
    parts.append(f"🔥 {title}\n")
    parts.append(
        "Is video me maine dikhaya hai step by step, completely free. "
        "Agar helpful laga toh SUBSCRIBE karo aur bell 🔔 daba do!\n"
    )
    
    # Timestamps for long form
    chapters = script_data.get("chapters", [])
    if chapters:
        parts.append("⏱️ TIMESTAMPS:")
        for ch in chapters:
            parts.append(f"  {ch['time']} - {ch['title']}")
        parts.append("")
    
    # Links
    parts.append("🔗 LINKS & TOOLS:")
    parts.append("  → Tools mentioned in video: [ADD LINK]")
    parts.append("  → Free AI tools playlist: [ADD LINK]")
    parts.append("  → Join Telegram for updates: [ADD LINK]")
    parts.append("")
    
    # Hashtags
    hashtags = script_data.get("hashtags", [])
    if hashtags:
        parts.append(" ".join([f"#{h.replace('#', '')}" for h in hashtags]))
    
    # Footer
    parts.append(f"\n{'═' * 40}")
    parts.append("📱 Follow:")
    parts.append(f"  Instagram: @{channel_name}")
    parts.append(f"  Twitter: @{channel_name}")
    parts.append("\n⚠️ Disclaimer: Educational content. Results may vary.")
    
    return "\n".join(parts)


# ════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="📤 Upload video to YouTube")
    parser.add_argument("--video", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", nargs="+", default=[])
    parser.add_argument("--thumbnail", default=None)
    parser.add_argument("--privacy", choices=["public", "private", "unlisted"], default="public")
    parser.add_argument("--script-json", help="Auto-build description from script")
    
    args = parser.parse_args()
    
    desc = args.description
    if args.script_json:
        with open(args.script_json, "r", encoding="utf-8") as f:
            sd = json.load(f)
        desc = build_description(sd)
        if not args.tags:
            args.tags = sd.get("tags", sd.get("hashtags", []))
    
    result = upload_video(
        video_path=args.video,
        title=args.title,
        description=desc,
        tags=args.tags,
        thumbnail_path=args.thumbnail,
        privacy=args.privacy
    )
    print(f"\n🎉 Watch: {result['url']}")
