from dataclasses import dataclass
from datetime import timedelta

from .anilist import AnilistClient
from .mal import ListEntry, MALClient
from .mapping import MAL_TO_ANILIST


@dataclass
class Anime:
    _mal: ListEntry

    def __post_init__(self):
        anilist_id = MAL_TO_ANILIST.get(self._mal.id)
        self._anilist = AnilistClient.get_anime(anilist_id=anilist_id)

    @property
    def title(self):
        return self._mal.title

    @property
    def image(self):
        return self._mal.image

    @property
    def watched_episodes(self):
        return self._mal.num_episodes_watched

    @property
    def total_episodes(self):
        return self._anilist["episodes"]

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
        left = self.aired_episodes or self.total_episodes
        if not left:
            return []
        watched = self.watched_episodes or 0
        return list(range(watched + 1, left + 1))

    @property
    def up_to_date(self):
        return self.watched_episodes == self.aired_episodes

    @property
    def time_until_next_episode(self):
        try:
            return timedelta(
                seconds=self._anilist["nextAiringEpisode"]["timeUntilAiring"]
            )
        except (KeyError, TypeError):
            return None

    @property
    def season(self):
        return (
            self._anilist["season"].capitalize()
            + " "
            + str(self._anilist["seasonYear"])
        )

    @property
    def mal_url(self):
        return f"https://myanimelist.net/anime/{self._mal.id}"

    @property
    def anilist_url(self):
        return f"https://anilist.co/anime/{self._anilist['id']}"

    @property
    def google_url(self):
        return f"https://www.google.com/search?q=anime%20{self.title}"


def get_anime_list(mal_username):
    watching = MALClient.get_list(mal_username, status="watching")
    return [Anime(x) for x in watching]
