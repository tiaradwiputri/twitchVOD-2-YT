import os
import sys

import yt_dlp
from dotenv import load_dotenv

from state import load_uploaded_ids, save_uploaded_ids
from twitch_api import get_app_access_token, get_latest_vods
from youtube_api import get_youtube_client, upload_video

load_dotenv()

DOWNLOAD_DIR = "downloads"


def download_vod(video_id, video_url):
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    output_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    ydl_opts = {
        "outtmpl": output_path,
        "format": "best",
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return output_path


def process_vod(vod, uploaded_ids, youtube):
    """Download and upload a single VOD. Returns True on success. Marks it
    as uploaded (and persists state) only on success, so failures are safe
    to retry."""
    video_id = vod["id"]
    title = vod["title"]
    created_at = vod["created_at"]
    url = vod["url"]

    print(f"Processing VOD {video_id}: {title}")
    file_path = None
    try:
        file_path = download_vod(video_id, url)
        description = f"Originally streamed on Twitch: {url}\nStreamed at: {created_at}"
        youtube_id = upload_video(youtube, file_path, title, description)
        print(f"Uploaded to YouTube: https://youtu.be/{youtube_id}")
        uploaded_ids.add(video_id)
        save_uploaded_ids(uploaded_ids)
        return True
    except Exception as exc:
        print(f"Failed to process VOD {video_id}: {exc}", file=sys.stderr)
        return False
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)


def main():
    twitch_client_id = os.environ["TWITCH_CLIENT_ID"]
    twitch_client_secret = os.environ["TWITCH_CLIENT_SECRET"]
    twitch_user_id = os.environ["TWITCH_USER_ID"]
    yt_client_id = os.environ["YT_CLIENT_ID"]
    yt_client_secret = os.environ["YT_CLIENT_SECRET"]
    yt_refresh_token = os.environ["YT_REFRESH_TOKEN"]

    access_token = get_app_access_token(twitch_client_id, twitch_client_secret)
    vods = get_latest_vods(twitch_user_id, twitch_client_id, access_token)

    uploaded_ids = load_uploaded_ids()
    new_vods = [vod for vod in vods if vod["id"] not in uploaded_ids]
    new_vods.reverse()  # oldest first, so upload order matches stream order

    if not new_vods:
        print("No new VODs.")
        return

    youtube = get_youtube_client(yt_client_id, yt_client_secret, yt_refresh_token)

    for vod in new_vods:
        process_vod(vod, uploaded_ids, youtube)


if __name__ == "__main__":
    main()
