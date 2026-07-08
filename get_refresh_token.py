from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]

flow = InstalledAppFlow.from_client_secrets_file(
    ".secret/client_secret.json",
    SCOPES
)

credentials = flow.run_local_server(port=8080)

print("Refresh token:")
print(credentials.refresh_token)