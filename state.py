import json
from pathlib import Path

STATE_PATH = Path(__file__).parent / "state" / "uploaded_vods.json"
MAX_TRACKED = 50


def load_uploaded_ids():
    if not STATE_PATH.exists():
        return set()
    return set(json.loads(STATE_PATH.read_text()).get("uploaded_ids", []))


def save_uploaded_ids(ids):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    trimmed = list(ids)[-MAX_TRACKED:]
    STATE_PATH.write_text(json.dumps({"uploaded_ids": trimmed}, indent=2) + "\n")
