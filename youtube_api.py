from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_URI = "https://oauth2.googleapis.com/token"


def get_youtube_client(client_id, client_secret, refresh_token):
    creds = Credentials(
        None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri=TOKEN_URI,
    )
    return build("youtube", "v3", credentials=creds)


def upload_video(youtube, file_path, title, description, privacy_status="unlisted", category_id="20"):
    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "categoryId": category_id,
        },
        "status": {"privacyStatus": privacy_status},
    }
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        _, response = request.next_chunk()
    return response["id"]
