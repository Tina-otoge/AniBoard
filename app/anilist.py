import json
import time
from datetime import timedelta

from qlient.http import Fields, GraphQLResponse, HTTPBackend, HTTPClient
from requests_cache import CachedSession

from .config import Config


def _cache_get_path(key):
    path = Config.cache_dir / "anilist" / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def cache_get(key):
    path = _cache_get_path(key)
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


def cache_set(key, data):
    path = _cache_get_path(key)
    with path.open("w") as f:
        json.dump({"timestamp": time.time(), "data": data}, f)


class AnilistClient:
    url = "https://graphql.anilist.co"
    _client = None
    mapping_fix = Config.mal_to_anilist

    @classmethod
    @property
    def client(cls):
        if cls._client is None:
            session = CachedSession(
                Config.cache_dir / "anilist",
                expire_after=timedelta(
                    minutes=Config.anilist_cache_expire_minutes
                ),
            )
            if Config.proxy:
                session.proxies = {"http": Config.proxy, "https": Config.proxy}
            cls._client = HTTPClient(HTTPBackend(cls.url, session=session))
        return cls._client

    @classmethod
    def query(cls, type, *fields, **filters):
        if fields and isinstance(fields[0], Fields):
            fields = fields[0]
        response: GraphQLResponse = getattr(cls.client.query, type)(
            **filters,
            _fields=fields,
        )
        if response.errors:
            raise Exception(response.errors)
        return response.data.get(type)

    @classmethod
    def get_anime(cls, mal_id=None, anilist_id=None):
        if not mal_id and not anilist_id:
            raise Exception("Either MAL ID or Anilist ID is required")
        if anilist_id:
            search = {"id": anilist_id}
        elif mal_id in cls.mapping_fix:
            search = {"id": cls.mapping_fix[mal_id]}
        else:
            search = {"idMal": mal_id}
        key = " ".join(f"{k}{v}" for k, v in search.items())
        # Cached session doesn't work with HTTPBackend apparently so we still
        # use our manual cache
        cache = cache_get(key)
        if cache:
            return cache
        data = cls.query(
            "Media",
            Fields(
                "id",
                "episodes",
                "season",
                "seasonYear",
                nextAiringEpisode=["episode", "timeUntilAiring"],
            ),
            **search,
        )
        cache_set(key, data)
        return data
