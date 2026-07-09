import requests

TWITCH_OAUTH_URL = "https://id.twitch.tv/oauth2/token"
TWITCH_HELIX_VIDEOS_URL = "https://api.twitch.tv/helix/videos"


def get_app_access_token(client_id, client_secret):
    response = requests.post(
        TWITCH_OAUTH_URL,
        params={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_latest_vods(user_id, client_id, access_token, first=5):
    response = requests.get(
        TWITCH_HELIX_VIDEOS_URL,
        headers={
            "Client-Id": client_id,
            "Authorization": f"Bearer {access_token}",
        },
        params={"user_id": user_id, "type": "archive", "first": first},
    )
    response.raise_for_status()
    return response.json()["data"]


def get_vod_by_id(video_id, client_id, access_token):
    response = requests.get(
        TWITCH_HELIX_VIDEOS_URL,
        headers={
            "Client-Id": client_id,
            "Authorization": f"Bearer {access_token}",
        },
        params={"id": video_id},
    )
    response.raise_for_status()
    data = response.json()["data"]
    if not data:
        raise ValueError(f"No Twitch VOD found with id {video_id}")
    return data[0]
