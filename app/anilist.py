import json
import time

import requests

from .config import Config

API_URL = "https://graphql.anilist.co"
GRAPHQL_ANILIST_FIELDS = """
id, episodes, season, seasonYear, nextAiringEpisode { episode, timeUntilAiring }
"""
CHUNK_SIZE = 60


def _cache_get_path(anilist_id):
    path = Config.cache_dir / "anilist" / f"id{anilist_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cache_get(anilist_id):
    path = _cache_get_path(anilist_id)
    if path.exists():
        with path.open() as f:
            content = json.load(f)
        if (
            content["timestamp"] + Config.anilist_cache_expire_minutes * 60
            > time.time()
        ):
            return content["data"]
        path.unlink()
    return None


def cache_set(anilist_id, data):
    path = _cache_get_path(anilist_id)
    with path.open("w") as f:
        json.dump({"timestamp": time.time(), "data": data}, f)


def _get_anime_multiple(anilist_ids):
    graphql_anilist_query = "{"
    cached_data = {}
    lookup_count = 0
    for anilist_id in anilist_ids:
        data = cache_get(anilist_id)
        if data is not None:
            cached_data[anilist_id] = data
            continue
        graphql_anilist_query += f"id{anilist_id}: Media(id: {anilist_id}) {{{GRAPHQL_ANILIST_FIELDS}}}"
        lookup_count += 1
    graphql_anilist_query += "}"
    if lookup_count == 0:
        return cached_data
    response = requests.post(
        f"{API_URL}/graphql", json={"query": graphql_anilist_query}
    ).json()
    if "errors" in response:
        raise Exception(str(response["errors"]))
    result = {x["id"]: x for x in response["data"].values()}
    for anilist_id, data in result.items():
        cache_set(anilist_id, data)
    for anilist_id, data in cached_data.items():
        result[anilist_id] = data
    return result


def get_anime_multiple(anilist_ids):
    result = {}
    for i in range(0, len(anilist_ids), CHUNK_SIZE):
        start = i
        end = i + CHUNK_SIZE
        result.update(_get_anime_multiple(anilist_ids[start:end]))
    return result
