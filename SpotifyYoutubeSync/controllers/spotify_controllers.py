from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json
from SpotifyYoutubeSync import app


@app.route("/spotify/playlists")
def spotify_playlists():
    headers = {
        "Authorization": "Bearer " + session["spotify_credentials"]["access_token"]
    }
    print("Headers: " + str(headers))

    user_response = requests.get(app.config['SPOTIFY_BASE_URI'] + "/v1/me/playlists", headers=headers)
    print("Playlists response status: " + str(user_response.status_code))
    user_body = json.loads(user_response.content)
    playlists=user_body['items']

    return render_template("playlists.html", playlists=playlists, service="spotify")

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



@app.route("/spotify_after_login")
def spotify_after_login():
    
    code = request.args['code']

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": app.config['REDIRECT_URI']
    }

    g.authorization_code = code

    client_id_secret = app.config["CLIENT_ID"] + ":" + app.config["CLIENT_SECRET"]
    authorization_string = base64.b64encode(client_id_secret.encode("ascii"))

    headers = {
        "Authorization": "Basic "+authorization_string.decode('utf-8')
    }

    response = requests.post(app.config['SPOTIFY_ACCOUNTS_BASE_URL'] + "/api/token", data=payload, headers=headers)
    response_body = json.loads(response.content)
    print("Spotify login response: " + str(response_body))
    session['spotify_credentials'] = spotify_response_to_credentials_dict(response_body) 
    
    return redirect(url_for('app_home'))

def spotify_response_to_credentials_dict(response_body):
    credentials_dict = {}
    credentials_dict['access_token'] = response_body['access_token']
    credentials_dict['token_type'] = response_body['token_type']
    credentials_dict['expires_in'] = response_body['expires_in']
    credentials_dict['refresh_token'] = response_body['refresh_token']
    credentials_dict['scope'] = response_body.get('scope')

    return credentials_dict


@app.route("/spotify/login")
def spotify_login():
    payload = {
        "response_type" :"code",
        "client_id": app.config["CLIENT_ID"],
        "redirect_uri": app.config['REDIRECT_URI'],
        "scope": "playlist-modify-private playlist-modify-public"
    }

    #print(app.config['SPOTIFY_ACCOUNTS_BASE_URL'] + urlencode(payload))
    return redirect(app.config['SPOTIFY_ACCOUNTS_BASE_URL'] + "/authorize?" + urlencode(payload))



@app.route("/spotify/setSourceOrDestination", methods=["POST"])
def spotify_set_source_or_destination():
    selected_option = request.form['option']
    spotify_playlist_id = request.form["playlist_id"]

    if selected_option == "source":
        session["spotify_source_playlist_id"] = spotify_playlist_id
    elif selected_option == "destination":
        session["spotify_destination_playlist_id"] = spotify_playlist_id 

    return redirect(url_for("app_home"))

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