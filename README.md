# Spotify Web Sockets

## Description

This project is inspired by the project https://github.com/EricRabil/sactivity/. Documentation on how to proceed in order to access Spotify WS was taken from his repo.

## Launch flask example

In order to launch flask example you need the following commands:

```bash
$ export FLASK_APP=examples.flask-app.server
$ flask run
```

## Basic library example

Example loading chrome cookies

```python

from spotifyws.spotify import SpotifyWs

client = SpotifyWs()

@client.on('track')
def on_track_change(data):
    print('TRACK CHANGED')

```

Example loading cookies from custom file

```python

from spotifyws.spotify import SpotifyWs

client = SpotifyWs(cookie_file="./cookie_file.json")

@client.on('track')
def on_track_change(data):
    print('TRACK CHANGED')

```

## About authentication

Right now authentication can only be achieved using local cookies and not OAUTH flow.

## Note

This code is intended for learning purposes only.
You must know that bypassing spotify API is against theirs Terms of service therefore I don't invite you to abuse this library.
Thanks

## Author

Jacopo De Gattis
