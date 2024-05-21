from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
from SpotifyYoutubeSync import app

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app.secret_key = 'some_secret'


def convert_youtube_playlists_to_playlist(youtube_playlists):
    playlists = []

    for youtube_playlist in youtube_playlists:
        youtube_playlist_dict = {
            "name": youtube_playlist["snippet"]["title"],
            "id": youtube_playlist["id"]
        }
        playlists.append(youtube_playlist_dict)

    return playlists



def get_video_names_from_playlist(playlist_id):
    credentials = google.oauth2.credentials.Credentials(
          **session['credentials'])

    youtube = googleapiclient.discovery.build(
      app.config["API_SERVICE_NAME"], app.config["API_VERSION"], credentials=credentials)

    pageToken = None
    videos = []
    num_results = 0


    while(1):
        request = youtube.playlistItems().list(
            part="contentDetails,id,snippet,status",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=pageToken
        )
        response = request.execute()
        pageToken = response.get("nextPageToken")

        for video in response["items"]:
            videos.append(video["snippet"]["title"])

        num_results = len(response["items"])

        if not pageToken:
            break

    return videos

@app.route("/youtube/items")
def youtube_playlist_items():
    youtube_playlist_id = request.args.get("playlist_id")
    video_names = get_video_names_from_playlist(youtube_playlist_id)
    #spotify_search_for_songs(video_names[:20])

    return render_template("youtube_video_names.html", video_names=video_names)


@app.route("/youtube/playlists")
def youtube_playlists():
    if 'credentials' not in session:
        return redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
          **session['credentials'])

    youtube = googleapiclient.discovery.build(
      app.config["API_SERVICE_NAME"], app.config["API_VERSION"], credentials=credentials)
    request = youtube.playlists().list(
        part="contentDetails,id,snippet,status",
        mine=True
    )
    response = request.execute()
    youtube_playlists = response["items"]
    playlists = convert_youtube_playlists_to_playlist(youtube_playlists)


    return render_template("playlists.html", playlists=playlists, service="youtube")



@app.route("/youtube/login")
def youtube_login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      app.config["YOUTUBE_CLIENT_SECRETS_FILE"], scopes=app.config["SCOPES"])
    flow.redirect_uri = url_for('youtube_after_login', _external=True)
    authorization_url, state = flow.authorization_url(
      # Enable offline access so that you can refresh an access token without
      # re-prompting the user for permission. Recommended for web server apps.
      access_type='offline',
      # Enable incremental authorization. Recommended as a best practice.
      include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    session['state'] = state

    return redirect(authorization_url)



@app.route("/youtube_after_login")
def youtube_after_login():
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      app.config["YOUTUBE_CLIENT_SECRETS_FILE"], scopes=app.config["SCOPES"], state=state)
    flow.redirect_uri = url_for('youtube_after_login', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)

    print("YouTube credentials: " + str(session['credentials']))

    return redirect(url_for('app_home'))

def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}



@app.route("/youtube/setSourceOrDestination", methods=["POST"])
def youtube_set_source_or_destination():
    selected_option = request.form['option']
    youtube_playlist_id = request.form["playlist_id"]

    if selected_option == "source":
        session["youtube_source_playlist_id"] = youtube_playlist_id
    elif selected_option == "destination":
        session["youtube_destination_playlist_id"] = youtube_playlist_id 

    return redirect(url_for("app_home"))



def get_videos_in_playlist_from_youtube(response_body):
    playlist = response["items"][2]
    num_videos = playlist["contentDetails"]["itemCount"]
    videos = []
    pageToken = None
    num_results = 0
    
    while(num_results < num_videos):
        request = youtube.playlistItems().list(
            part="contentDetails,id,snippet,status",
            playlistId=playlist["id"],
            maxResults=50,
            pageToken=pageToken
        )
        response = request.execute()
        pageToken = response.get("nextPageToken")

        if not pageToken:
            break

        for video in response["items"]:
            videos.append(video["snippet"]["title"])

        num_results = len(response["items"])


    print("Video names: ")

    print(str(videos))