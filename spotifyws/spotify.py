import json
import time
import queue
import requests
from .ws import WS
from bs4 import BeautifulSoup
from pyee import EventEmitter
from .config import *
from pycookiecheat import chrome_cookies
from .logger import logger as logging
from .utils import generate_totp

class SpotifyWs(object):
    debug = None
    queue = None
    device = None
    user_devices = None
    access_token = None
    connection_id = None
    event_emitter = None

    def __init__(
        self,
        verbose=False,
        cookie_file=None,
    ):
        self.verbose = verbose
        
        self.connection_id = ''
        self.device = DEFAULT_DEVICE
        self.user_devices = []

        self.queue = queue.Queue()

        self.cookies = self._load_cookies_from_file(cookie_file)
        self.access_token = self.get_access_token()

        self.s = self._init_session()
        self.event_emitter = EventEmitter()
        
        self.ws_socket = WS(self)
        self.ws_socket.start()

        self.init()

    def get_available_devices(self):
        return self.user_devices

    def _load_cookies_from_file(self, cookie_file=None):
        if not cookie_file:
            raise Exception("You must provide a file containing your browser session cookies.")

        # TODO: handle file not existing error
        cookies = open(cookie_file, "r")

        try:
            parsed_cookies = json.load(cookies)
            cookies.close()

            if type(parsed_cookies) == list:
                formatted_cookies = {}
                for cooky in parsed_cookies:
                    formatted_cookies[cooky["name"]] = cooky["value"]
                parsed_cookies = formatted_cookies

            return parsed_cookies
        except:
            logging.error("Invalid JSON file for cookies")
            exit(-1)

    def _init_session(self):
        """Initialize current 'requests' session

        Args: None

        Returns:
            'request' session object

        """
        
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {self.access_token}"
        })

        session.cookies.update(self.cookies)
        
        return session

    def _get_server_time(self):
        response = requests.get(
            GET_SERVER_TIME
        )

        if not response.status_code == 200:
            raise Exception(f"failed while fetching server time with status code {response.status_code} and body {response.content}")

        server_time = response.json()["serverTime"]

        return server_time

    def get_access_token(self):
        server_time = self._get_server_time()
        totp, _ = generate_totp(server_time=server_time)

        response = requests.get(
            GET_SPOTIFY_TOKEN,
            params={
                "reason": 'init',
                "productType": 'web-player',
                "totp": totp,
                "totpVer": 5,
                "ts": int(time.time() * 1000)
            },
            cookies=self.cookies
        )

        return response.json()["accessToken"]

    def on(self, event):
        """Listen for event using a decorator

        Listen for a triggered event using a dectorator
        and execute callback function

        Args:
            event: str
        Returns:
            function provided after the decorator

        """

        def wrapper(method):
            return self.event_emitter.on(event)(method)
        return wrapper

    def add_listener(self, event, method):
        """Listen for event using a listener

        Listen for a triggered event using a listener
        instead of a decorator

        Args:
            event: str
            method: function
        Returns:
            function provided as a callback
        """

        return self.event_emitter.on(event)(method)

    def fetch(self, method, url, retry=True, **kwargs):
        response = self.s.request(method, url, **kwargs)

        if response.status_code == 401:
            self.access_token = self.get_access_token()
            return self.fetch(method, url, retry=False, **kwargs)

        if not response.status_code == 200 and self.verbose:
            logging.error(
                f"Error while fetching {url}. Server returned {response.status_code} status code"
            )

        return response

    def _subscribe_to_activity(self):
        """Subscribe to events

        Args: None
        Returns: request response as 'requests.models.Content'

        """

        if self.verbose:
            logging.debug("Subscribing to activities")
        self.connection_id = self.queue.get(block=True)

        # TODO: it almost seems like it doesn't really matter if response status
        # code is 400 or 200
        
        self.s.put(f"{SUBSCRIBE_ACTIVITY}?connection_id={self.connection_id}", headers={
            "referer": "https://open.spotify.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }, data={})

    def _register_fake_device(self):
        """Register fake device

        Create a new face device to listen for events

        Args: None
        Returns: request response as 'requests.models.Content'
        
        """

        if self.verbose:
            logging.debug("Registering fake device to listen to events")

        data = {
            "client_version": "harmony:4.21.0-a4bc573",
            "connection_id": self.connection_id,
            "device": self.device,
            "outro_endcontent_snooping": False,
            "volume": 65535
        }

        res = self.fetch(
            "POST",
            REGISTER_DEVICE,
            retry=True,
            json=data,
        )

        return res

    # def get_available_devices(self):
    #     res = requests.get("https://api.spotify.com/v1/me/player/devices", headers={
    #         "Authorization": f"Bearer {token}"
    #     })

    #     print(res)
    #     print(res.content)

    def _connect_state(self):
        """Connect to spotify state

        Args: None
        Returns: request response as 'requests.models.Content'

        """

        if self.verbose:
            logging.debug("Connecting device to spotify state")

        default_options = {
            "device": {
                "device_info": {
                    "capabilities": {
                        "can_be_player": False,
                        "hidden": False,
                        "volume_steps": 64,
                        "supported_types": [
                            "audio/track",
                            "audio/episode",
                            "video/episode",
                            "mixed/episode"
                        ],
                        "needs_full_player_state": True,
                        "command_acks": True,
                        "is_controllable": True,
                        "supports_command_request": True,
                        "supports_set_options_command": True,
                    }
                }
            },
            "member_type": "CONNECT_STATE",
        }

        res = self.fetch(
            "PUT",
            f"{CONNECT_STATE}hobs_{self.device['device_id']}",
            json=default_options,
            headers={"x-spotify-connection-id": self.connection_id}
        )

        for dev_id, dev_info in res.json()["devices"].items():
            self.user_devices.append({
                "id": dev_id,
                "can_play": dev_info.get('can_play', False),
                **dev_info,
            })

        return res

    # TODO: maybe add possibility to transfer plyback from one device to another
    def _dispatch_command(self, command_type, command_payload, target_device):
        """Dispatch command base upon its type

        Args:
            command_type: "playback" | "volume"
            command_payload: Dictionary containing the command to dispatch
        Returns:
            HTTP request response
        
        """

        if command_type == "playback":
            cmd_url = "https://gew1-spclient.spotify.com/connect-state/v1/player/command/from/{}/to/{}".format(self.device['device_id'], target_device)
            r = self.fetch("POST", cmd_url, retry=False, json=command_payload)
        elif command_type == "volume":
            cmd_url = "https://gew1-spclient.spotify.com/connect-state/v1/connect/volume/from/{}/to/{}".format(self.device['device_id'], target_device)
            r = self.fetch("PUT", cmd_url, retry=False, json=command_payload)

    def send_command(self, command, target_device, *args):

        if command in ["pause", "resume", "skip_next", "skip_prev"]:
            if len(args) != 0:
                raise Exception("This command take no args, ex. ('resume').")
        else:
            if len(args) != 1:
                raise Exception("You must provide an integer value.")

        if not target_device:
            raise Exception("You must provide a valid target_device to execute a command")

        command_arg = args[0] if len(args) > 0 else None
        command_type = "playback" if command in ["pause", "resume", "skip_next", "skip_prev", "seek_to"] else "volume"
        available_commands = {
            "pause":  {"command": {"endpoint": "pause"}},
            "resume": {"command": {"endpoint": "resume"}},
            "skip_next": {"command": {"endpoint": "skip_next"}},
            "skip_prev": {"command": {"endpoint": "skip_prev"}},
            "seek_to": {"command": {"endpoint": "seek_to", "value": command_arg}},
            "volume": {"volume": command_arg},
        }

        self._dispatch_command(command_type, available_commands[command], target_device)

    def init(self):
        """Initialize main library modules

        Args: None
        Returns: void

        """

        self._subscribe_to_activity()
        self._register_fake_device()
        self._connect_state()
