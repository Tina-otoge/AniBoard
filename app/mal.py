import urllib.parse
from dataclasses import dataclass
from datetime import timedelta

from requests_cache import CachedSession

from .config import Config


@dataclass
class ListEntry:
    id: int
    title: str
    num_episodes_watched: int
    image: str


class MALClient:
    client_id = Config.mal_client_id
    url = "https://api.myanimelist.net/v2"
    session = CachedSession(
        Config.cache_dir / "mal",
        expire_after=timedelta(minutes=Config.mal_cache_expire_minutes),
    )

    @classmethod
    def request(cls, endpoint, method="GET", **kwargs):
        if endpoint.startswith("/"):
            url = cls.url + endpoint
        else:
            url = endpoint
        response = cls.session.request(
            method,
            url,
            headers={"X-MAL-CLIENT-ID": cls.client_id},
            **kwargs,
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_list_api(cls, username, status=None):
        result = []
        offset = 0
        while True:
            response = cls.request(
                f"/users/{username}/animelist",
                params={
                    "status": status or "",
                    "fields": "list_status",
                    "offset": offset,
                },
            )
            result.extend(response["data"])
            try:
                next_url = response["paging"]["next"]
            except KeyError:
                next_url = None
            if not next_url:
                break
            params = urllib.parse.parse_qs(next_url[next_url.index("?") + 1 :])
            offset = int(params["offset"][0])
        return [
            ListEntry(
                **{
                    "id": entry["node"]["id"],
                    "title": entry["node"]["title"],
                    "num_episodes_watched": entry["list_status"][
                        "num_episodes_watched"
                    ],
                    "image": entry["node"]["main_picture"]["large"],
                }
            )
            for entry in result
        ]

    @classmethod
    def get_list_web(cls, username, status=None):
        status_map = {
            "watching": "1",
            "completed": "2",
            "on_hold": "3",
            "dropped": "4",
            "plan_to_watch": "6",
        }
        # TODO: Implement pagination, currently only returns first 300 entries
        url = f"https://myanimelist.net/animelist/{username}/load.json"

        def web_img_to_api(img):
            id1, id2 = img.split("/")[-2:]
            id2 = id2.split(".")[0]
            return f"https://cdn.myanimelist.net/images/anime/{id1}/{id2}l.jpg"

        return [
            ListEntry(
                **{
                    "id": entry["anime_id"],
                    "title": entry["anime_title"],
                    "num_episodes_watched": entry["num_watched_episodes"],
                    "image": web_img_to_api(entry["anime_image_path"]),
                }
            )
            for entry in cls.request(
                url,
                params={
                    "status": status_map[status] if status else "",
                },
            )
        ]

    @classmethod
    def get_list(cls, username, status=None):
        return cls.get_list_web(username, status)
