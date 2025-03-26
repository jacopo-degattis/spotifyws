import requests
import time
import pyotp
import hashlib
import hmac

# Credits for this secret and `generate_otp` function: https://github.com/kmille/deezer-downloader/blob/d4aefe23977d79e3f8eb41d731f1f0a37299b0ad/deezer_downloader/spotify.py
SPOTIFY_TOTP_SECRET = bytearray([53, 53, 48, 55, 49, 52, 53, 56, 53, 51, 52, 56, 55, 52, 57, 57, 53, 57, 50, 50, 52, 56, 54, 51, 48, 51, 50, 57, 51, 52, 55])

def generate_totp(
    secret = SPOTIFY_TOTP_SECRET,
    algorithm = hashlib.sha1,
    digits = 6,
    counter_factory = lambda: int(time.time()) // 30,
):
    counter = counter_factory()
    hmac_result = hmac.new(
        secret, counter.to_bytes(8, byteorder="big"), algorithm
    ).digest()

    offset = hmac_result[-1] & 15
    truncated_value = (
        (hmac_result[offset] & 127) << 24
        | (hmac_result[offset + 1] & 255) << 16
        | (hmac_result[offset + 2] & 255) << 8
        | (hmac_result[offset + 3] & 255)
    )
    return (
        str(truncated_value % (10**digits)).zfill(digits),
        counter * 30_000,
    )