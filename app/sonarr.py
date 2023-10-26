import requests


def safeify_title(s: str) -> str:
    remove = ("&", "'", '"', ":")
    s = "".join(x for x in s if x not in remove)
    s = " ".join(s.split())
    return s


class SonarrClient:
    def __init__(self, url, api_key):
        self.url = url + "/api/v3"
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-Api-Key": api_key})
        self.root_folder = self.request("/rootFolder").json()[0]

    def request(self, path, method="GET", **kwargs):
        response = self.session.request(method, self.url + path, **kwargs)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            print(response.status_code, response.text)
            with open("error.txt", "w") as f:
                f.write(response.text)
            raise e
        return response

    def series_lookup(self, tvdb_id):
        return self.request(
            "/series/lookup", params={"term": f"tvdb:{tvdb_id}"}
        ).json()[0]

    def series_get(self, tvdb_id):
        return self.request("/series", params={"tvdbId": tvdb_id}).json()

    def series_import(self, tvdb_id):
        if self.series_get(tvdb_id):
            return
        lookup = self.series_lookup(tvdb_id)
        lookup.update(
            {
                "qualityProfileId": 1,
                "languageProfileId": 1,
                "path": (
                    self.root_folder["path"]
                    + "\\"
                    + safeify_title(lookup["title"])
                ),
                "rootFolderPath": self.root_folder["path"],
            }
        )
        return self.request("/series", method="POST", json=lookup)
