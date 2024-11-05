import traceback
from dataclasses import dataclass
from datetime import timedelta

from app import anilist

from .mal import ListEntry, MALClient
from .mapping import MAL_TO_OTHERS


@dataclass
class Anime:
    _mal: ListEntry
    _anilist: dict = None
    tvdb_id: int = None

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
        # left = self.aired_episodes or self.total_episodes
        left = self.aired_episodes
        if not left:
            return []
        watched = self.watched_episodes or 0
        return list(range(watched + 1, left + 1))

    @property
    def up_to_date(self):
        return (
            self.watched_episodes == self.aired_episodes
            and self.aired_episodes > 0
        )

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
        if not self._anilist["season"]:
            return "Unknown"
        return (
            self._anilist["season"].capitalize()
            + " "
            + str(self._anilist["seasonYear"])
        )

    @property
    def date(self):
        if not self._anilist or not self._anilist["season"]:
            return "0"
        season_to_num = {
            "winter": 1,
            "spring": 4,
            "summer": 7,
            "fall": 10,
        }
        season_num = season_to_num[self._anilist["season"].lower()]
        return f"{self._anilist['seasonYear']}-{season_num:02d}"

    @property
    def mal_url(self):
        return f"https://myanimelist.net/anime/{self._mal.id}"

    @property
    def anilist_url(self):
        return f"https://anilist.co/anime/{self._anilist['id']}"

    @property
    def google_url(self):
        return f"https://www.google.com/search?q=anime%20{self.title}"


def get_anime_list(mal_username, ptw=False):
    status = "plan_to_watch" if ptw else "watching"
    mal_entries = {
        x.id: x for x in MALClient.get_list(mal_username, status=status)
    }
    mal_to_anilist_ids = {
        x: MAL_TO_OTHERS.get(x, {}).get("anilist_id")
        for x in mal_entries.keys()
    }
    mal_to_tvdb_ids = {
        x: MAL_TO_OTHERS.get(x, {}).get("thetvdb_id")
        for x in mal_entries.keys()
    }
    anilist_entries = anilist.get_anime_multiple(
        [x for x in mal_to_anilist_ids.values() if x]
    )

    result = [
        Anime(
            _mal=mal_entries[mal_id],
            _anilist=anilist_entries.get(anilist_id),
            tvdb_id=mal_to_tvdb_ids.get(mal_id),
        )
        for mal_id, anilist_id in mal_to_anilist_ids.items()
    ]
    result.sort(key=lambda x: x.date, reverse=True)
    return result
