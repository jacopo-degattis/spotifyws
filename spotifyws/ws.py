
import ssl
import json
import pydash
import threading
import websocket
from pyee.cls import evented
from spotifyws.config import DEALER_WS_URL

@evented
class WS(threading.Thread):

    def __init__(self, spotify):
        self.queue = spotify.queue
        self.previous_payload = dict()
        self.access_token = spotify.access_token
        self.event_emitter = spotify.event_emitter
        threading.Thread.__init__(self, name="websocket", daemon=True)

    def _check_differences(self, keys, new_obj):
        """Check differences between previous and current object

        Given a list of nested keys, check if one of those fields
        has changed and if so keep track of the change 
        
        Args:
            keys: list[str]
            new_obj: dict
        Returns: void

        """

        EVENTS_MAPPING = {
            "is_playing": "is_playing",
            "volume": "volume",
            "options": "playback_options",
            "uri": "track",
        }
        
        for key in keys:
            new_value = pydash.get(new_obj, key)
            
            if pydash.get(self.previous_payload, key) != new_value:
                # TODO: improve this condition
                if key.split('.')[-1] == 'is_paused' and pydash.get(self.previous_payload, key) != new_value:
                    emit_value = 'pause' if new_value else 'resume'
                    self.event_emitter.emit(
                        emit_value,
                    )
                else:
                    self.event_emitter.emit(
                        EVENTS_MAPPING[key.split('.')[-1]],
                        new_value
                    )
                pydash.set_(self.previous_payload, key, new_value)
            
    def _handle_device_state_changed(self, message):
        """Function to handle 'DEVICE_STATE_CHANGED'

        When a 'DEVICE_STATE_CHANGED' event is triggered
        this function take care of checking if any of the listed
        fields has changed

        Args:
            message: dict
        Returns: void

        """

        keys = [
            # TODO: is_playing, when does this event get triggered ?
            "payloads.0.cluster.player_state.is_playing",
            "payloads.0.cluster.player_state.is_paused" ,
            "payloads.0.cluster.player_state.options",
            "payloads.0.cluster.player_state.track.uri"
        ]

        self._check_differences(keys, message)

    def _handle_device_volume_changed(self, message):
        """Function to handle 'DEVICE_VOLUME_CHANGED'

        When a 'DEVICE_VOLUME_CHANGED' event is triggered
        this function take care of checking if any of the listed
        fields has changed

        Args:
            message: dict
        Returns: void
        
        """

        ACTIVE_DEVICE_PATH = "payloads.0.cluster.active_device_id"
        active_device = pydash.get(message, ACTIVE_DEVICE_PATH)

        keys = [
            f"payloads.0.cluster.devices.{active_device}.volume"
        ]

        self._check_differences(keys, message)

    def _handle_message(self, message):
        """Events dispatcher

        Execute a given function base upon his category

        Args:
            message: dict
        Returns:
            callback function

        """

        REASONS = {
            "DEVICES_DISAPPEARED": self._handle_device_volume_changed,
            "DEVICE_STATE_CHANGED": self._handle_device_state_changed,
            "DEVICE_VOLUME_CHANGED": self._handle_device_volume_changed,
            "NEW_DEVICE_APPEARED": lambda x: "TODO"
        }

        payloads = message.get('payloads')

        if not payloads:
            return message

        reason = payloads[0].get('update_reason')

        if not reason:
            return message

        return REASONS[reason](message)  

    def _get_connection_id(self, headers):
        """Extract connection_id field from ws headers

        Args:
            headers: dict
        Returns: void

        """

        connection_id = headers['Spotify-Connection-Id']
        self.connection_id = connection_id
        self.queue.put(connection_id)

    def _on_message(self, ws, message):
        """Triggered whenever socket receives new incoming messages

        Args:
            message: dict
        Returns: void

        """

        msg = json.loads(message)

        headers = msg.get('headers')

        if 'Spotify-Connection-Id' in headers.keys():
            return self._get_connection_id(headers)

        if msg.get('type') == 'message':
            self._handle_message(msg)
        
    def run(self):
        """Thread override method

        Args: None
        Returns: None
        
        """

        # websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            f"{DEALER_WS_URL}?access_token={self.access_token}",
            on_message = self._on_message,
        )

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        