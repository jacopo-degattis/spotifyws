import requests
import time
import pyotp
import hashlib
import hmac

def get_latest_secret_key_version():
    res = requests.get("https://raw.githubusercontent.com/Thereallo1026/spotify-secrets/refs/heads/main/secrets/secrets.json")

    secrets = res.json()

    if not secrets:
        raise ValueError("Secret key list is empty.")

    latest = secrets[-1]
    original_secret = latest["secret"]
    version = latest["version"]

    if not isinstance(original_secret, str):
        raise ValueError("The original secret must be a string.")

    ascii_codes = [ord(c) for c in original_secret]
    transformed = [(val ^ ((i % 33) + 9)) for i, val in enumerate(ascii_codes)]

    transformed_str = ''.join(str(num) for num in transformed)
    return transformed_str, version

def generate_totp(
    server_time,
    algorithm = hashlib.sha1,
    digits = 6,
):
    secret, version = get_latest_secret_key_version()

    counter = server_time // 30
    hmac_result = hmac.new(
        secret.encode(), counter.to_bytes(8, byteorder="big"), algorithm
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