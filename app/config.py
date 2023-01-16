from pathlib import Path

import yaml


class File:
    _obj = None

    @classmethod
    @property
    def obj(cls):
        if cls._obj is None:
            with open("conf/config.yml") as f:
                cls._obj = yaml.safe_load(f)
        return cls._obj

    @classmethod
    def get(cls, key, default=None):
        return cls.obj.get(key, default)

    @classmethod
    def need(cls, key):
        value = cls.get(key)
        if value is None:
            raise Exception(f"Missing {key} in config.yaml")
        return value


class Config:
    button_title_map = File.get("button_title_map", {})
    mal_to_anilist = File.get("mal_to_anilist", {})
    mal_client_id = File.need("mal_client_id")
    mal_cache_expire_minutes = File.get("mal_cache_expire_minutes", 10)
    anilist_cache_expire_minutes = File.get("mal_cache_expire_minutes", 60)
    app_name = File.get("app_name", "AniBoard")
    default_url = File.get(
        "default_url", "https://nyaa.si/?f=0&c=1_2&q=hevc {title} {episode}"
    )
    cache_dir = Path(File.get("cache_dir", "var/cache"))
    proxy = File.get("proxy")


Config.cache_dir.mkdir(parents=True, exist_ok=True)
