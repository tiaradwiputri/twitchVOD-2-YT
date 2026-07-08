# twitchVOD-2-YT

Automatically uploads new Twitch VODs to YouTube (as Unlisted videos). A GitHub
Actions workflow polls for new VODs every 15 minutes, downloads them, and
uploads anything new.

## How it works

- `twitch_api.py` — gets a Twitch app access token and fetches the latest VODs
  for a channel via the Helix API.
- `state.py` — tracks which VOD ids have already been uploaded
  (`state/uploaded_vods.json`), so nothing is re-uploaded.
- `main.py` — orchestrates: fetch latest VODs → skip already-uploaded ones →
  download each new one with `yt-dlp` → upload to YouTube → delete the local
  file → record it as uploaded.
- `youtube_api.py` — builds a YouTube Data API client from a stored OAuth
  refresh token (no interactive login needed) and uploads videos.
- `.github/workflows/upload_vod.yml` — runs `main.py` on a schedule (every 15
  minutes) and commits the updated state file back to the repo.

## One-time setup

### 1. Create a Twitch app

Create an app at https://dev.twitch.tv/console/apps to get a
`TWITCH_CLIENT_ID` and `TWITCH_CLIENT_SECRET`. You'll also need the numeric
`TWITCH_USER_ID` of the channel to monitor (look it up with any
"Twitch user ID lookup" tool, or via the Helix `users` endpoint).

### 2. Create a YouTube OAuth client

You should already have `.secret/client_secret.json` for a YouTube Data API
OAuth client (Desktop app type) from Google Cloud Console, with the YouTube
Data API v3 enabled.

### 3. Get a YouTube refresh token

```
pip install -r requirements.txt
python get_refresh_token.py
```

This opens a browser for a one-time login and prints a refresh token. Save
it — this is `YT_REFRESH_TOKEN` below. You'll also need the `client_id` and
`client_secret` values from `.secret/client_secret.json` as `YT_CLIENT_ID`
and `YT_CLIENT_SECRET`.

### 4. Local testing with `.env`

Copy `.env.example` to `.env` and fill in the six values from steps 1 and 3.
`main.py` loads `.env` automatically (via `python-dotenv`) when run locally;
`.env` is git-ignored and never read in GitHub Actions (secrets are injected
as real env vars there instead).

```
cp .env.example .env
# fill in .env, then:
python main.py
```

### 5. Add GitHub Actions secrets

In the repo's Settings → Secrets and variables → Actions, add:

- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `TWITCH_USER_ID`
- `YT_CLIENT_ID`
- `YT_CLIENT_SECRET`
- `YT_REFRESH_TOKEN`

### 6. Test it

Trigger the workflow manually from the Actions tab ("Run workflow") to
confirm it runs end-to-end before relying on the schedule.

## Notes

- Assumes VODs are public (no sub-only VOD support).
- Very long VODs may approach GitHub-hosted runner disk/time limits.
