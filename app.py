from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os 
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.config.from_file("config.json", load=json.load)
app.secret_key = 'some_secret'

@app.route("/spotify/playlists")
def spotify_playlists():
    headers = {
        "Authorization": "Bearer " + session["spotify_credentials"]["access_token"]
    }

    user_response = requests.get(SPOTIFY_BASE_URI + "/v1/me/playlists", headers=headers)
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

        response = requests.get(SPOTIFY_BASE_URI + "/v1/search", headers=headers, params=params)
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
      API_SERVICE_NAME, API_VERSION, credentials=credentials)

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
      API_SERVICE_NAME, API_VERSION, credentials=credentials)
    request = youtube.playlists().list(
        part="contentDetails,id,snippet,status",
        mine=True
    )
    response = request.execute()
    youtube_playlists = response["items"]
    playlists = convert_youtube_playlists_to_playlist(youtube_playlists)


    return render_template("playlists.html", playlists=playlists, service="youtube")


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

@app.route("/spotify_after_login")
def spotify_after_login():
    
    code = request.args['code']

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    g.authorization_code = code

    client_id_secret = CLIENT_ID + ":" + CLIENT_SECRET
    authorization_string = base64.b64encode(client_id_secret.encode("ascii"))

    headers = {
        "Authorization": "Basic "+authorization_string.decode('utf-8')
    }

    response = requests.post(SPOTIFY_ACCOUNTS_BASE_URL + "/api/token", data=payload, headers=headers)
    response_body = json.loads(response.content)
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
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "playlist-modify-private playlist-modify-public"
    }

    #print(SPOTIFY_ACCOUNTS_BASE_URL + urlencode(payload))
    return redirect(SPOTIFY_ACCOUNTS_BASE_URL + "/authorize?" + urlencode(payload))


@app.route("/youtube/login")
def youtube_login():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
      YOUTUBE_CLIENT_SECRETS_FILE, scopes=SCOPES)
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
      YOUTUBE_CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
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


@app.route("/spotify/setSourceOrDestination", methods=["POST"])
def spotify_set_source_or_destination():
    selected_option = request.form['option']
    spotify_playlist_id = request.form["playlist_id"]

    if selected_option == "source":
        session["spotify_source_playlist_id"] = spotify_playlist_id
    elif selected_option == "destination":
        session["spotify_destination_playlist_id"] = spotify_playlist_id 

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


def divide_chunks(l, n): 
    # looping till length l 
    for i in range(0, len(l), n):  
        yield l[i:i + n]

def add_tracks_to_spotify_playlist(track_objects, playlist_id):
    ADD_TRACK_TO_PLAYLIST_URL = SPOTIFY_BASE_URI + "/v1/playlists/" + playlist_id + "/tracks" 
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

    




# TODO: Change this to POST
@app.route("/startSync", methods=["GET"])
def start_sync():
    if not (session.get("youtube_source_playlist_id") and session.get("spotify_destination_playlist_id")):
        return "Not supported yet"

    video_names = get_video_names_from_playlist(session.get("youtube_source_playlist_id"))
    results = spotify_search_for_songs(video_names[:20])
    
    add_tracks_to_spotify_playlist(results, session.get("spotify_destination_playlist_id"))

    return str(json.dumps(results))