# Spotify Web Sockets
[![Downloads](https://pepy.tech/badge/spotify-ws)](https://pepy.tech/project/spotify-ws)

## Description

The main purpose of this project is to let the users interact with
spotify web socket events. Right now the project is still in an alpha version therefore is not complete and may have some bugs.
Feel free to contribute is any way.

## Basic library usage

Example using chrome cookies

```python

from spotifyws import SpotifyWs

client = SpotifyWs()

# Triggered on track change
@client.on('track')
def on_track_change(data):
    print('Track changed => ', data)

# Triggered on volume change
@client.on("volume")
def on_volume_change(data):
    print("Volume changed => ", data)

# Triggered on options change, such as shuffle etc.
@client.on("playback_options")
def on_playback_options_change(data):
    print("Options changed => ", data)

# Triggered playback state is resumed
@client.on("resume")
def on_play():
    print("Playback resumed")

# Triggered playback state is paused
@client.on("pause")
def on_pause():
    print("Playback paused")

```

Example using cookies from custom file

```python

from spotifyws import SpotifyWs

client = SpotifyWs(cookie_file="./cookie_file.json")

# Triggered on track change
@client.on('track')
def on_track_change(data):
    print('Track changed => ', data)

# Triggered on volume change
@client.on("volume")
def on_volume_change(data):
    print("Volume changed => ", data)

# Triggered on options change, such as shuffle etc.
@client.on("playback_options")
def on_playback_options_change(data):
    print("Options changed => ", data)

# Triggered playback state is resumed
@client.on("resume")
def on_play():
    print("Playback resumed")

# Triggered playback state is paused
@client.on("pause")
def on_pause():
    print("Playback paused")

```

You can also send playback and volume commands to clients

```python

from spotifyws import SpotifyWs

client = SpotifyWs(cookie_file="./cookie_file.json")

# You can get this using for example `client.get_available_devices()` or the `v1/me/player/devices` endpoint.

target_device_id = 00000000000000

client.send_command("pause", target_device_id)
client.send_command("resume", target_device_id)
client.send_command("skip_next", target_device_id)
client.send_command("skip_prev", target_device_id)
client.send_command("volume", 30000, target_device_id)
client.send_command("seek_to", 5000, target_device_id)

```

## Cookies format

Cookies can be in either two formats

The first format is

`{
    "cookie1": "cookieValue1"
}`

and the scond one is

`[
    {"name": "cookie1", "value": "cookieValue1"}
]`

## About authentication

Right now authentication can only be achieved using local cookies and not through OAUTH flow.

## Note

This code is intended for learning purposes only.
You must know that bypassing spotify API is against theirs Terms of service therefore I don't invite you to abuse this library.
Thanks

## Author

Jacopo De Gattis
