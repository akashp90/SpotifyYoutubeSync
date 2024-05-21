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

app = Flask("SpotifyYoutubeSync")
app.config.from_file("../config.json", load=json.load)
app.secret_key = 'some_secret'

from SpotifyYoutubeSync.controllers import *