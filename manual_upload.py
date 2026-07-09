import os
import re
import sys

from dotenv import load_dotenv

from main import process_vod
from state import load_uploaded_ids
from twitch_api import get_app_access_token, get_vod_by_id
from youtube_api import get_youtube_client

load_dotenv()


def extract_video_id(arg):
    match = re.search(r"videos/(\d+)", arg)
    if match:
        return match.group(1)
    if arg.isdigit():
        return arg
    raise ValueError(f"Could not parse a Twitch VOD id from: {arg}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python manual_upload.py <twitch_vod_url_or_id>", file=sys.stderr)
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])

    uploaded_ids = load_uploaded_ids()
    if video_id in uploaded_ids:
        print(f"VOD {video_id} is already marked as uploaded, nothing to do.")
        return

    twitch_client_id = os.environ["TWITCH_CLIENT_ID"]
    twitch_client_secret = os.environ["TWITCH_CLIENT_SECRET"]
    yt_client_id = os.environ["YT_CLIENT_ID"]
    yt_client_secret = os.environ["YT_CLIENT_SECRET"]
    yt_refresh_token = os.environ["YT_REFRESH_TOKEN"]

    access_token = get_app_access_token(twitch_client_id, twitch_client_secret)
    vod = get_vod_by_id(video_id, twitch_client_id, access_token)

    youtube = get_youtube_client(yt_client_id, yt_client_secret, yt_refresh_token)

    if not process_vod(vod, uploaded_ids, youtube):
        sys.exit(1)


if __name__ == "__main__":
    main()
