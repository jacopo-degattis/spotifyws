import json
import queue
import requests
from spotifyws.ws import WS
from bs4 import BeautifulSoup
from pyee import EventEmitter
from spotifyws.config import *
from pycookiecheat import chrome_cookies
from spotifyws.logger import logger as logging


class SpotifyWs(object):
    debug = None
    queue = None
    device = None
    user_devices = None
    access_token = None
    connection_id = None
    event_emitter = None

    def __init__(self, debug=False, cookie_file=None, device_options={}):
        self.debug = debug
        self.access_token = ''
        self.connection_id = ''
        self.device = DEFAULT_DEVICE
        self.device_options = device_options
        self.user_devices = []

        self.queue = queue.Queue()
        self.s = requests.Session()
        self.s = self._init_session(cookie_file)
        self._get_token_from_html()
        
        self.event_emitter = EventEmitter()
        
        self.ws_socket = WS(self)
        self.ws_socket.start()

        self.init()

    def _add_cookiejar(self, session: requests.Session):
        """Add chrome extracted cookies to session
        
        Extract and decrypt cookies from chrome and add
        them to current 'requests' session.

        Args:
            session: A 'requests.Session' object
        Returns:
            Session updated value with added cookies

        """

        if self.debug:
            logging.debug("Loading cookies from local chrome storage")

        cookies = chrome_cookies(WEB_BASE_URI)

        if not cookies:
            raise Exception(EMPTY_COOKIES_ERROR)

        session.cookies.update(cookies)

        return session

    def _init_session(self, cookie_file=None):
        """Initialize current 'requests' session

        Args: None

        Returns:
            'request' session object

        """

        session = requests.Session()
        
        if not cookie_file:
            session = self._add_cookiejar(session)
            return session

        with open(cookie_file, "r") as cookies:
            session.cookies.update(json.load(cookies))

        return session

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

    def _request(self, uri, method="GET", **kwargs):
        """Make a http request

        Make a HTTP request using the provided values

        Args:
            uri: str
            method: str
            **kwargs: dict
        Returns:
            response object 'requests.models.Response'

        """

        HTTP_METHOD = {
            "POST": self.s.post,
            "GET": self.s.get,
            "PUT": self.s.put,
            "DELETE": self.s.delete
        }
        
        response = HTTP_METHOD[method](uri, **kwargs)
            
        if not response.status_code == 200 and self.debug:
            # NOTE: should this condition throw an exception or just debug a error ?
            logging.error(f"Error while fetching {uri}. Server returned {response.status_code}")
            # raise Exception(f"Error while fetching {uri}. Server returned {response.status_code}")


        return response

    def _get_token_from_html(self):
        """Extract token from plain HTML webpage

        Extract token using web-scraping Beautifoulsoup library

        Args: None
        Returns: void
        
        """

        if self.debug:
            logging.debug("Fetching spotify token from HTML")

        res = self._request(WEB_BASE_URI)
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all('script')

        for script in scripts:
            if len(script.contents) > 0:
                if 'accessToken' in script.contents[0]:
                    data = json.loads(script.contents[0])
                    self.access_token = data['accessToken']
                    self.s.headers.update({"Authorization": f"Bearer {self.access_token}"})

    def _subscribe_to_activity(self):
        """Subscribe to events

        Args: None
        Returns: request response as 'requests.models.Content'
        
        """

        if self.debug:
            logging.debug("Subscribing to activities")
        self.connection_id = self.queue.get(block=True)
        self._request(f"{SUBSCRIBE_ACTIVITY}?connection_id={self.connection_id}", method="PUT")

    def _register_fake_device(self):
        """Register fake device

        Create a new face device to listen for events

        Args: None
        Returns: request response as 'requests.models.Content'
        
        """

        if self.debug:
            logging.debug("Registering fake device to listen to events")

        data = {
            "client_version": "harmony:4.21.0-a4bc573",
            "connection_id": self.connection_id,
            "device": self.device,
            "outro_endcontent_snooping": False,
            "volume": 65535
        }

        res = self._request(
            REGISTER_DEVICE,
            method="POST",
            json=data
        )

        return res

    def _connect_state(self):
        """Connect to spotify state

        Args: None
        Returns: request response as 'requests.models.Content'

        """

        if self.debug:
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

        res = self._request(
            f"{CONNECT_STATE}hobs_{self.device['device_id']}",
            method="PUT",
            json={**default_options, **self.device_options} if self.device_options else default_options,
            headers={"x-spotify-connection-id": self.connection_id}
        )

        for dev_id, dev_info in res.json()["devices"].items():
            self.user_devices.append({
                "id": dev_id,
                "can_play": dev_info.get('can_play', False),
                **dev_info,
            })

        return res

    def _dispatch_command(self, cmd_type, command):
        """Dispatch command base upon its type

        Args:
            cmd_type: playback | volume
            command: object
        Returns:
            HTTP request response
        
        """

        # Playback for audio seek, next, prev, play/pause
        # Volume for volume level control
        if not cmd_type in ["volume", "playback"]:
            raise Exception(f"Command must be either 'volume' or 'playback', {cmd_type} was given")

        URLS = {
            "volume": {
                "uri": SEND_VOL_COMMAND,
                "method": "PUT",
                "json": command
            },
            "playback": {
                "uri": SEND_COMMAND,
                "method": "POST",
                "json": command
            }
        }

        for device in self.user_devices:
            if not device['can_play']:
                break
            URLS[cmd_type]["uri"] = URLS[cmd_type]["uri"].format(self.device['device_id'], device['id'])
            res = self._request(**URLS[cmd_type])

        return res

    def send_command(self, command, *args):

        if command in ["pause", "resume", "skip_next", "skip_prev"]:
            if len(args) != 0:
                raise Exception("This command take no args, ex. ('resume') ")
            self._dispatch_command("playback", { "command": { "endpoint": command }})
            return
        
        if command == "volume":
            if len(args) != 1:
                raise Exception("You must provide an integer value in order to change volume, ex. ('volume', 3000) ")
            self._dispatch_command("volume", {"volume": args[0]})

        if command == "seek_to":
            if len(args) != 1:
                raise Exception("You must provide an integer value in order to seek player position ex. ('seek_to', 5000) ")
            self._dispatch_command("playback", {"command": {"endpoint": "seek_to", "value": args[0]}})

        return

    def init(self):
        """Initialize main library modules

        Args: None
        Returns: void

        """

        self._subscribe_to_activity()
        self._register_fake_device()
        self._connect_state()
