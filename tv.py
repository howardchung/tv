import requests
import subprocess
import time
import os
import signal
import atexit
import json
import sys

stream: subprocess.Popen = None
try:
    adapter = sys.argv[1]
except:
    adapter = "0"
url = "https://backend.watchparty.me/roomData/tender-squirrel-reproduce"
url2 = "https://backend.watchparty.me/roomData/alike-week-recognize"
preset = "veryfast"

def kill():
    global stream
    if stream != None:
        os.killpg(os.getpgid(stream.pid), signal.SIGTERM)
        stream = None

def launch(id):
    global stream
    if not id:
        return
    #-vf scale=-1:720
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -i pipe: -c:v libx264 -preset ' + preset + ' -c:a aac -ac 2 -r 30 -f mpegts - | nc 5.78.115.83 5000', shell=True, preexec_fn=os.setsid)
    # Need to set env var since we're using old drivers (not iHD)
    os.environ["LIBVA_DRIVER_NAME"] = "i965"
    #stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -hwaccel vaapi -vaapi_device /dev/dri/renderD128 -i pipe: -vf \'format=nv12,hwupload\' -c:v h264_vaapi -qp 26 -c:a aac -ac 2 -r 30 -f mp4 -movflags frag_keyframe+empty_moov - | nc 5.78.115.83 5000', shell=True, preexec_fn=os.setsid)

def getChannel():
    #return requests.get(url).json()["video"].split("/")[-1].split(".")[0]
    return requests.get(url2).json()["video"].split("?channel=")[1]
    
atexit.register(kill)
channel = launch(getChannel())
# Repeat every 3 seconds
while True:
    time.sleep(3)
    try:
        new = getChannel()
        # If different from current channel
        # stop the current stream and restart
        if new != channel:
            channel = new
            kill()
            launch(new)
        # If we are supposed to be streaming and process exited, restart
        if new and stream and stream.poll() != None:
            print(stream.poll())
            launch(channel)
    except Exception as e:
        print(e)
