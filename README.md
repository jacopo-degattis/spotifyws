# Spotify Web Sockets

## Description

The main purpose of this project is to let the users interact with
spotify web socket events. Right now the project is still in an alpha version therefore is not complete and may have some bugs.
Feel free to contribute is any way.

## Basic library usage

Example using chrome cookies

```python

from spotifyws.spotify import SpotifyWs

client = SpotifyWs()

@client.on('track')
def on_track_change(data):
    print('TRACK CHANGED')

```

Example using cookies from custom file

```python

from spotifyws.spotify import SpotifyWs

client = SpotifyWs(cookie_file="./cookie_file.json")

@client.on('track')
def on_track_change(data):
    print('TRACK CHANGED')

```

## Launch flask example

In order to launch flask example you need the following commands:

```bash
$ export FLASK_APP=examples.flask-app.server
$ flask run
```

## About authentication

Right now authentication can only be achieved using local cookies and not through OAUTH flow.

## Note

This code is intended for learning purposes only.
You must know that bypassing spotify API is against theirs Terms of service therefore I don't invite you to abuse this library.
Thanks

## Author

Jacopo De Gattis
