import threading
from spotifyws import SpotifyWs

current_device_id = None
client = SpotifyWs(
    cookie_file='./cookie_file.json',
)

def listen_for_events():
    @client.on("playback_options")
    def on_playback_options_change(data):
        # print("Options changed => ", data)
        pass

    @client.on("track")
    def on_track_changed(data):
        # print("Track changed with data")
        # print(data)
        pass

    while True: pass

def get_command():
    global current_device_id
    cmd = input("Type a command: [resume, pause, skip_next, skip_prev, volume, seek_to]: ")

    if cmd in ["resume", "pause", "skip_next", "skip_prev"]:
        client.send_command(cmd, current_device_id)
    else:
        command, value = cmd.split(":")
        client.send_command(command, value, current_device_id)

def list_devices():
    global current_device_id
    devices = client.get_available_devices()

    for index, dev in enumerate(devices):
        print(f"{index}). {dev.get('name', 'No Name Available')} with id = {dev.get('id')}")

    cmd = input("Choose a target device: ")
    
    current_device_id = devices[int(cmd)].get("id")

def menu():
    option = int(input(f"Target device id = {current_device_id}\n1). Select a target device\n2). Send commands to device\nYour choice (1-2): "))

    if option == 1:
        list_devices()
    elif option == 2:
        if current_device_id == None:
            print("You must select a target device first!")
            exit(-1)
        get_command()

    menu()

if __name__ == "__main__":
    backround_thread = threading.Thread(target=listen_for_events)
    backround_thread.start()
    client.get_available_devices()
    menu()    
    