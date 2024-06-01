from flask import Flask, url_for, redirect, request, g, render_template, session
import requests
from urllib.parse import urlencode
import base64
import json

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask("SpotifyYoutubeSync")
    app.config.from_file("../config.json", load=json.load)
    app.secret_key = os.environ["FLASK_SECRET_KEY"]
    app.debug = 1
    
    return app


app = create_app()

from SpotifyYoutubeSync.controllers import *
