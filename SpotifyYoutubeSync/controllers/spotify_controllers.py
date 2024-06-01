from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json
from SpotifyYoutubeSync import app
from ..helpers.helpers import spotify_response_to_credentials_dict


@app.route("/spotify/playlists")
def spotify_playlists():
    headers = {
        "Authorization": "Bearer " + session["spotify_credentials"]["access_token"]
    }
    print("Headers: " + str(headers))

    user_response = requests.get(
        app.config["SPOTIFY_BASE_URI"] + "/v1/me/playlists", headers=headers
    )
    print("Playlists response status: " + str(user_response.status_code))
    user_body = json.loads(user_response.content)
    playlists = user_body["items"]

    return render_template("playlists.html", playlists=playlists, service="spotify")


@app.route("/spotify_after_login")
def spotify_after_login():

    code = request.args["code"]

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": app.config["REDIRECT_URI"],
    }

    g.authorization_code = code

    client_id_secret = app.config["CLIENT_ID"] + ":" + app.config["CLIENT_SECRET"]
    authorization_string = base64.b64encode(client_id_secret.encode("ascii"))

    headers = {"Authorization": "Basic " + authorization_string.decode("utf-8")}

    response = requests.post(
        app.config["SPOTIFY_ACCOUNTS_BASE_URL"] + "/api/token",
        data=payload,
        headers=headers,
    )
    response_body = json.loads(response.content)
    print("Spotify login response: " + str(response_body))
    session["spotify_credentials"] = spotify_response_to_credentials_dict(response_body)

    return redirect(url_for("app_home"))


@app.route("/spotify/login")
def spotify_login():
    payload = {
        "response_type": "code",
        "client_id": app.config["CLIENT_ID"],
        "redirect_uri": app.config["REDIRECT_URI"],
        "scope": "playlist-modify-private playlist-modify-public",
    }

    # print(app.config['SPOTIFY_ACCOUNTS_BASE_URL'] + urlencode(payload))
    return redirect(
        app.config["SPOTIFY_ACCOUNTS_BASE_URL"] + "/authorize?" + urlencode(payload)
    )


@app.route("/spotify/setSourceOrDestination", methods=["POST"])
def spotify_set_source_or_destination():
    selected_option = request.form["option"]
    spotify_playlist_id = request.form["playlist_id"]

    if selected_option == "source":
        session["spotify_source_playlist_id"] = spotify_playlist_id
    elif selected_option == "destination":
        session["spotify_destination_playlist_id"] = spotify_playlist_id

    return redirect(url_for("app_home"))
