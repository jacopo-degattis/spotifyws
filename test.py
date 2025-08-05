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

while True: pass