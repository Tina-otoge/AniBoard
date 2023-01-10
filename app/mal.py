from datetime import timedelta

from requests_cache import CachedSession

from .config import Config


class MALClient:
    client_id = Config.mal_client_id
    url = "https://api.myanimelist.net/v2"
    session = CachedSession(
        Config.cache_dir / "mal",
        expire_after=timedelta(minutes=Config.mal_cache_expire_minutes),
    )

    @classmethod
    def request(cls, endpoint, method="GET", **kwargs):
        response = cls.session.request(
            method,
            f"{cls.url}/{endpoint}",
            headers={"X-MAL-CLIENT-ID": cls.client_id},
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_list(cls, username, status=None):
        return cls.request(
            f"users/{username}/animelist",
            params={
                "status": status or "",
                "fields": "list_status",
                "limit": 1000,
            },
        ).get("data", [])
