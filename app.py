from flask import Flask, url_for, redirect, request, g
import requests
from urllib.parse import urlencode
import base64
import json

app = Flask(__name__)
SPOTIFY_ACCOUNTS_BASE_URL = "https://accounts.spotify.com"
SPOTIFY_BASE_URI = "https://api.spotify.com"
REDIRECT_URI = "http://127.0.0.1:5000/spotify_after_login"
CLIENT_ID = "a70e7896202b47d2aef770a2085f46c8"
CLIENT_SECRET = "06e7b4bad080476096789e2777b38159"


access_token = ""
token_type = ""
expires_in = ""
refresh_token = ""
scope = ""



@app.route("/app_home")
def app_home():
    print("Getting User profile")
    global access_token
    print("Access toke: " + access_token)

    headers = {
        "Authorization": "Bearer " + access_token
    }

    user_response = requests.get(SPOTIFY_BASE_URI + "/v1/me/playlists", headers=headers)
    user_body = json.loads(user_response.content)

    #user_id = user_body["id"]


    print("User response")
    print(user_response.content)

    return "App home done"


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
    # g.access_token = response_body['access_token']
    # g.token_type = response_body['token_type']
    # g.expires_in = response_body['expires_in']
    # g.refresh_token = response_body['refresh_token']
    # g.scope = response_body.get('scope')

    global access_token, token_type, expires_in, refresh_token, scope

    access_token = response_body['access_token']
    token_type = response_body['token_type']
    expires_in = response_body['expires_in']
    refresh_token = response_body['refresh_token']
    scope = response_body.get('scope')



    
    return redirect(url_for('app_home'))


@app.route("/login")
def login():
    payload = {
        "response_type" :"code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI
    }

    print(SPOTIFY_ACCOUNTS_BASE_URL + urlencode(payload))
    return redirect(SPOTIFY_ACCOUNTS_BASE_URL + "/authorize?" + urlencode(payload))

@app.route("/")
def hello_world():
    print(url_for("spotify_after_login"))
    return redirect(url_for('login'))