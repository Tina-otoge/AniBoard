import re
import urllib.parse
from datetime import timedelta

import flask
from flask import Flask

from .config import Config
from .main import get_anime_list

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.template_global("app")
def inject_app():
    return flask.current_app


@app.template_global("app")
def inject_config():
    return Config


@app.route("/")
def index():
    settings = ["username", "url"]
    data = {
        setting: flask.request.args.get(setting)
        or flask.request.cookies.get(setting)
        or ""
        for setting in settings
    }
    if not data["username"]:
        anime_list = []
    else:
        anime_list = get_anime_list(data["username"])
    if not data["url"]:
        data["url"] = Config.default_url

    def urlize(anime, episode):
        title = Config.url_title_map.get(anime.title, anime.title)
        title = anime.title.lower()
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

    html = flask.render_template(
        "index.html", anime_list=anime_list, urlize=urlize, **data
    )
    response = flask.make_response(html)
    for setting, value in data.items():
        if value:
            response.set_cookie(setting, value, max_age=timedelta(days=365))
    return response
