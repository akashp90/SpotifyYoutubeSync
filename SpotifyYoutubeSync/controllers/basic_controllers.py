from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json
from SpotifyYoutubeSync import app


@app.route("/")
def hello_world():
    return render_template("home.html")

@app.route("/app_home")
def app_home():
    enable_sync_button = check_enable_sync_button()
    return render_template("home.html", enable_sync_button=enable_sync_button)


def check_enable_sync_button():
    res = False
    if session.get("youtube_source_playlist_id") and session.get("spotify_destination_playlist_id"):
        return True
    if session.get("spotify_source_playlist_id") and session.get("youtube_destination_playlist_id"):
        return True

    return False