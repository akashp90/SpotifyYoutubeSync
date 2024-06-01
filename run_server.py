from SpotifyYoutubeSync import create_app, app

if __name__ == "__main__":
    app.run()
    print("running")
else:
    gunicorn_app = app
