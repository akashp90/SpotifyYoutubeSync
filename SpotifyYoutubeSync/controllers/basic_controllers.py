from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json
from SpotifyYoutubeSync import app
from ..helpers.helpers import check_enable_sync_button, get_video_names_from_playlist, spotify_search_for_songs, add_tracks_to_spotify_playlist

@app.route("/")
def hello_world():
    return render_template("home.html")

@app.route("/app_home")
def app_home():
    enable_sync_button = check_enable_sync_button()
    return render_template("home.html", enable_sync_button=enable_sync_button)


# TODO: Change this to POST
@app.route("/startSync", methods=["GET"])
def start_sync():
    if not (session.get("youtube_source_playlist_id") and session.get("spotify_destination_playlist_id")):
        return "Not supported yet"

    video_names = get_video_names_from_playlist(session.get("youtube_source_playlist_id"))
    results = spotify_search_for_songs(video_names)
    
    add_tracks_to_spotify_playlist(results, session.get("spotify_destination_playlist_id"))

    return str(json.dumps(results))