import json
from pathlib import Path

ANIME_MAPPING_PATH = Path("lib/mapping/anime-list-mini.json")
with ANIME_MAPPING_PATH.open() as f:
    ANIME_MAPPING = json.load(f)

MAL_TO_OTHERS = {o["mal_id"]: o for o in ANIME_MAPPING if o.get("mal_id")}
