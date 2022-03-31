import os
import json
import queue
import base64
import requests
from spotifyws.spotify import SpotifyWs
from flask import Flask, render_template, request, session, redirect
from flask_session import Session
import flask

app = Flask(__name__)
app.secret_key = os.urandom(32)
app.config['SESSION_TYPE'] = 'filesystem'
app.config["SESSION_PERMANENT"] = False
Session(app)
client = SpotifyWs()

# NOTE: redirect uri should be https://localhost:5000/authenticate
CLIENT_ID = "<CLIENT_ID>"
CLIENT_SECRET = "<CLIENT_SECRET>"
SPOTIFY_AUTH_URL = f"https://accounts.spotify.com/authorize?response_type=code&client_id={CLIENT_ID}&scope=user-read-private user-read-email&redirect_uri=http://localhost:5000/authenticate"

# Custom Redis implementation
# Credits: https://github.com/MaxHalford/flask-sse-no-deps
class MessageAnnouncer:

    def __init__(self):
        self.listeners = []

    def listen(self):
        self.listeners.append(queue.Queue(maxsize=5))
        return self.listeners[-1]

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]

announcer = MessageAnnouncer()

def format_sse(data: str, event=None) -> str:
    msg = f"data: {data}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg

@app.route('/ping')
def ping():
    msg = format_sse(data='pong')
    announcer.announce(msg=msg)
    return {}, 200

@app.route('/stream', methods=['GET'])
def listen():

    def stream():
        messages = announcer.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    return flask.Response(stream(), mimetype='text/event-stream')

@client.on('track')
def on_track_change(data):
    msg = format_sse(data=json.dumps({"track": data}))
    announcer.announce(msg=msg)
    return {}, 200

@app.route("/")
def homepage():
    if not session.get('token'):
        return redirect(SPOTIFY_AUTH_URL)
    return render_template('index.html')

@app.route("/track/<id>")
def get_track(id):
    uri = "https://api.spotify.com/v1/tracks/" + id
    res = requests.get(uri, headers={"Authorization": f"Bearer {session['token']}"})
    return res.json(), 200

@app.route("/authenticate")
def authenticate():
    values = request.args

    code = values['code']

    res = requests.post("https://accounts.spotify.com/api/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:5000/authenticate"
    }, headers={
        "Authorization": f"Basic {base64.b64encode('{}:{}'.format(CLIENT_ID, CLIENT_SECRET).encode()).decode()}",
        "Content-Type": "application/x-www-form-urlencoded"
    })

    json_res = res.json()

    session['token'] = json_res['access_token']

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)

