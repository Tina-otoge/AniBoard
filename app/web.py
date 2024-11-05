import re
import urllib.parse
from datetime import timedelta

import flask
from flask import Flask

from .config import Config
from .main import get_anime_list
from .sonarr import SonarrClient

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SECRET_KEY"] = "yolo it's only for flash messages"


@app.template_global("app")
def inject_app():
    return flask.current_app


@app.template_global("config")
def inject_config():
    return Config


def get_data():
    settings = ["username", "url"]
    return {
        setting: flask.request.args.get(setting)
        or flask.request.cookies.get(setting)
        or ""
        for setting in settings
    }


@app.route("/<username>")
def anime_list_route(username):
    data = get_data()
    ptw = flask.request.args.get("ptw", False)
    anime_list = get_anime_list(username, ptw=ptw)

    def urlize(anime, episode):
        title = Config.button_title_map.get(anime._mal.id, anime.title)
        title = title.lower()
        title = re.sub(r"[^\w\d]", " ", title)
        title = " ".join(
            x
            for x in title.split()
            if x not in ("the", "a", "an", "part", "season")
        )
        return data["url"].format(
            title=urllib.parse.quote(title),
            episode=episode,
        )

    return flask.render_template(
        "index.html", anime_list=anime_list, urlize=urlize, **data
    )


@app.route("/")
def index():
    data = get_data()
    response = None
    if data["username"]:
        response = flask.redirect(
            flask.url_for("anime_list_route", username=data["username"])
        )
    if not data["url"]:
        data["url"] = Config.default_url

    response = response or flask.render_template("index.html", **data)

    for setting, value in data.items():
        if isinstance(response, flask.Response):
            response.set_cookie(setting, value, max_age=timedelta(days=365))

    return response


@app.post("/sonarr")
def sync_to_sonarr():
    data = get_data()
    anime_list = get_anime_list(data["username"])
    body = flask.request.form.to_dict()
    url = body["sonarr_url"].removesuffix("/")
    client = SonarrClient(url=url, api_key=body["sonarr_api_key"])
    for anime in anime_list:
        if not anime.tvdb_id:
            print(f"Skipping {anime.title} because it has no tvdb_id")
            continue
        client.series_import(anime.tvdb_id)
    return flask.redirect(flask.url_for("index"))
