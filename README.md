# twitchVOD-2-YT

Automatically uploads new Twitch VODs to YouTube (as Unlisted videos). Zapier
triggers a GitHub Actions workflow after a stream ends, which checks for the
new VOD, downloads it, and uploads it.

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
- `.github/workflows/upload_vod.yml` — runs `main.py` when triggered by Zapier
  (via `repository_dispatch`) or manually, and commits the updated state file
  back to the repo.
- `manual_upload.py` — uploads one specific VOD by URL or id, for streams
  that were missed (see below).

## Uploading a missed stream manually

`main.py` only ever looks at the 5 most recent VODs, so if one falls out of
that window before it gets uploaded, the automated run will never pick it up.
Use `manual_upload.py` instead, locally (with `.env` set up as below):

```
python manual_upload.py https://www.twitch.tv/videos/1234567890
# or just the id:
python manual_upload.py 1234567890
```

It looks up that specific VOD directly (regardless of how old it is),
downloads and uploads it, and records it in `state/uploaded_vods.json` so it
won't be picked up again later. If it's already in that file, it exits
immediately without re-uploading. After running it, commit and push the
updated state file so the automated runs stay in sync.

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

Secrets live in the `TWITCH` environment (Settings → Environments → `TWITCH`
→ Environment secrets — create the environment first if it doesn't exist).
The workflow job declares `environment: TWITCH`, so these must be
**environment** secrets, not repository secrets, and the names must match
exactly:

- `TWITCH_CLIENT_ID`
- `TWITCH_CLIENT_SECRET`
- `TWITCH_USER_ID`
- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

### 6. Test it

Trigger the workflow manually from the Actions tab ("Run workflow") to
confirm it runs end-to-end before wiring up Zapier.

### 7. Wire up Zapier

Create a fine-grained GitHub personal access token
(https://github.com/settings/personal-access-tokens) scoped to just this
repo, with **Contents: Read and write** and **Actions: Read and write**
permissions. Store it in Zapier, not as a GitHub Actions secret.

In Zapier:

1. **Trigger**: whatever signals your stream just ended, followed by a Delay
   step (10–15 min is plenty for a ~1 hour stream to finish processing on
   Twitch's side).
2. **Action**: "Webhooks by Zapier" → POST to
   `https://api.github.com/repos/tiaradwiputri/twitchVOD-2-YT/dispatches`
   - Headers: `Authorization: Bearer <your PAT>`,
     `Accept: application/vnd.github+json`
   - Body: `{"event_type": "vod-ready"}`

You can test this call yourself before wiring up Zapier:

```
curl -X POST \
  -H "Authorization: Bearer <your PAT>" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/tiaradwiputri/twitchVOD-2-YT/dispatches \
  -d '{"event_type":"vod-ready"}'
```

A successful call returns no output (204) and should show up as a new run
in the Actions tab within a few seconds.

## Notes

- Assumes VODs are public (no sub-only VOD support).
- Very long VODs may approach GitHub-hosted runner disk/time limits (not a
  concern at ~1 hour per stream).
- There's no schedule fallback — if the Zapier call never fires, no upload
  happens. Use `workflow_dispatch` to run it manually if needed.
