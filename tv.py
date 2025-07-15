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
    #-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 60
    #-c:v libx264 -preset veryfast -x264-params "keyint=60:scenecut=0"
    #-c:v libx265 -preset superfast -x265-params "keyint=60:min-keyint=60"
    #-c:v libsvtav1 -g 60 -preset 12
    #-c:v copy
    #-f mpegts
    #-f mp4 -movflags frag_keyframe+empty_moov
    #-f hls -hls_time 10 -hls_list_size 360 -hls_flags delete_segments -hls_segment_type fmp4 /mnt/watchparty-hls/tv.m3u8
    #-tag:a mp4a -f dash -seg_duration 4 -window_size 900  /mnt/watchparty-hls/tv.mpd
    #-f flv rtmp://5.78.115.83:5000
    # Need to set env var since we're using old drivers (not iHD)
    #os.environ["LIBVA_DRIVER_NAME"] = "i965"
    subprocess.Popen('rm /mnt/watchparty-hls/*', shell=True)
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -i pipe: -c:v libsvtav1 -g 60 -preset 13 -c:a aac -ac 2 -r 30 -f nut - | ffmpeg -i pipe: -c copy -tag:a 10 -f dash -seg_duration 4 -window_size 900  /mnt/watchparty-hls/tv.mpd', shell=True, preexec_fn=os.setsid)

def getChannel():
    #return requests.get(url).json()["video"].split("/")[-1].split(".")[0]
    return requests.get(url2).json()["video"].split("channel=")[1]
    
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
