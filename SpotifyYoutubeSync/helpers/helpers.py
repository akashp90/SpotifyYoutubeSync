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


def check_enable_sync_button():
    res = False
    if session.get("youtube_source_playlist_id") and session.get("spotify_destination_playlist_id"):
        return True
    if session.get("spotify_source_playlist_id") and session.get("youtube_destination_playlist_id"):
        return True

    return False




def spotify_search_for_songs(video_titles):
    #video_titles = ["Zedd, Elley Duhé - Happy Now (Official Music Video)"]
    headers = {
        "Authorization": "Bearer " + session["spotify_credentials"]["access_token"]
    }

    spotify_tracks = {}

    for video_title in video_titles:
        print("Searching for: " + str(video_title))
        params = {
            "q": video_title,
            "type": "track"
        }

        response = requests.get(app.config['SPOTIFY_BASE_URI'] + "/v1/search", headers=headers, params=params)
        response_body = json.loads(response.content)

        #print("Response: " + str(response_body))
        spotify_tracks[video_title] = convert_spotify_search_response_to_track_object(response_body)

    return spotify_tracks

def convert_spotify_search_response_to_track_object(response_body):
    if not response_body.get("tracks").get("items"):
        print("response_body: " + str(response_body))
        raise Exception("Response is empty: ")

    artist_names = [artist['name'] for artist in response_body.get("tracks").get("items")[0]["artists"]]
    # Combine the names into a single string
    combined_names = ', '.join(artist_names)
    result = {
        "name": response_body.get("tracks").get("items")[0]["name"],
        "spotify_url": response_body.get("tracks").get("items")[0]["external_urls"]["spotify"],
        "id": response_body.get("tracks").get("items")[0]["id"],
        "uri": response_body.get("tracks").get("items")[0]["uri"],
        "artistName": combined_names
    }

    return result



def spotify_response_to_credentials_dict(response_body):
    credentials_dict = {}
    credentials_dict['access_token'] = response_body['access_token']
    credentials_dict['token_type'] = response_body['token_type']
    credentials_dict['expires_in'] = response_body['expires_in']
    credentials_dict['refresh_token'] = response_body['refresh_token']
    credentials_dict['scope'] = response_body.get('scope')

    return credentials_dict


def add_tracks_to_spotify_playlist(track_objects, playlist_id):
    ADD_TRACK_TO_PLAYLIST_URL = app.config['SPOTIFY_BASE_URI'] + "/v1/playlists/" + playlist_id + "/tracks" 
    all_uris = [obj["uri"] for obj in track_objects.values()]
    print("HITTING URL: " + str(ADD_TRACK_TO_PLAYLIST_URL))
    headers = {
        "Authorization": "Bearer " + session["spotify_credentials"]["access_token"],
        "Content-Type": "application/json"
    }

    for uris in divide_chunks(all_uris, 100):
        print("uris: " + str(uris))
        body = {
            "uris": uris
        }
        response = requests.post(ADD_TRACK_TO_PLAYLIST_URL, headers=headers, data=json.dumps(body))
        print("Response: " + str(response))
        response_body = json.loads(response.content)
        print("Response body: " + str(response_body))


def convert_youtube_playlists_to_playlist(youtube_playlists):
    playlists = []

    for youtube_playlist in youtube_playlists:
        youtube_playlist_dict = {
            "name": youtube_playlist["snippet"]["title"],
            "id": youtube_playlist["id"]
        }
        playlists.append(youtube_playlist_dict)

    return playlists


def credentials_to_dict(credentials):
  return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes}


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


def divide_chunks(l, n): 
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n]