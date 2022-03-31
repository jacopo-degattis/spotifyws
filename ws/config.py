import string
import random

EMPTY_COOKIES_ERROR = "Google chrome spotify's cookies are empty. Login or use oauth authentication method !"

WEB_BASE_URI = "https://open.spotify.com"
SUBSCRIBE_ACTIVITY = "https://api.spotify.com/v1/me/notifications/user"
REGISTER_DEVICE = "https://guc-spclient.spotify.com/track-playback/v1/devices"
CONNECT_STATE = "https://guc3-spclient.spotify.com/connect-state/v1/devices/"
SEND_COMMAND = "https://gew1-spclient.spotify.com/connect-state/v1/player/command/from/{}/to/{}"
SEND_VOL_COMMAND = "https://gew1-spclient.spotify.com/connect-state/v1/connect/volume/from/{}/to/{}"
DEALER_WS_URL = "wss://gew1-dealer.spotify.com"
DEFAULT_DEVICE = {
    "brand": "spotify",
    "capabilities": {
        "audio_podcasts": True,
        "change_volume": True,
        "disable_connect": False,
        "enable_play_token": True,
        "manifest_formats": [
            "file_urls_mp3",
            "manifest_ids_video",
            "file_urls_external",
            "file_ids_mp4",
            "file_ids_mp4_dual"
        ],
        "play_token_lost_behavior": "pause",
        "supports_file_media_type": True,
        "video_playback": True
    },
    "device_id": ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(40)),
    "device_type": "computer",
    "metadata": {},
    "model": "web_player",
    "name": "Web Player (Microsoft Edge)",
    "platform_identifier": "web_player osx 11.3.0;microsoft edge 89.0.774.54;desktop"
}