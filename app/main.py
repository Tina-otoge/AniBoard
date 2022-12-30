from dataclasses import dataclass

from .anilist import AnilistClient
from .mal import MALClient


@dataclass
class Anime:
    _mal: dict
    _mal_status: dict

    @property
    def _anilist(self):
        return AnilistClient.get_anime(mal_id=self._mal["id"])

    @property
    def title(self):
        return self._mal["title"]

    @property
    def total_episodes(self):
        return self._anilist["episodes"]

    @property
    def watched_episodes(self):
        return self._mal_status["num_episodes_watched"]

    @property
    def aired_episodes(self):
        if self._anilist["nextAiringEpisode"]:
            return self._anilist["nextAiringEpisode"]["episode"] - 1
        return self._anilist["episodes"]

    @property
    def finished_airing(self):
        return self.aired_episodes == self.total_episodes

    @property
    def not_watched_episodes(self):
        return list(range(self.watched_episodes + 1, self.aired_episodes + 1))

    @property
    def up_to_date(self):
        return self.watched_episodes == self.aired_episodes

    @property
    def image(self):
        return self._mal["main_picture"]["large"]


def get_anime_list(mal_username):
    watching = MALClient.get_list(mal_username, status="watching")
    return [
        Anime(_mal=entry["node"], _mal_status=entry["list_status"])
        for entry in watching
    ]
