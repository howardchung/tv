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

url = "https://backend.watchparty.me/roomData/alike-week-recognize"
if adapter == "1":
    url = "https://backend.watchparty.me/roomData/supreme-faucet-kneel"

def kill():
    global stream
    if stream != None:
        os.killpg(os.getpgid(stream.pid), signal.SIGTERM)
        subprocess.Popen('rm /mnt/watchparty-hls/*', shell=True)
        stream = None

def launch(id):
    global stream
    if not id:
        return
    #-vf scale=-1:720
    encode1 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 60 -qp 28'
    encode2 = '-c:v libx264 -preset superfast -x264-params "keyint=60:scenecut=0" -crf 28'
    encode3 = '-c:v libx265 -preset superfast -x265-params "keyint=60:min-keyint=60"'
    encode4 = '-c:v libsvtav1 -g 60 -preset 12'
    encode5 = '-c:v copy'
    
    container_hls = '-f hls -hls_time 6 -hls_list_size 3600 -hls_flags delete_segments'
    container_dash = '-tag:v av01 -tag:a mp4a -f dash -seg_duration 6 -window_size 3600'
    container3 = '-f flv'
    container4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    
    outname_hls = '/mnt/watchparty-hls/' + id + '.m3u8'
    outname_dash = '/mnt/watchparty-hls/' + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'
    # Need to set env var since we're using old drivers (not iHD)
    os.environ["LIBVA_DRIVER_NAME"] = "i965"
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -i pipe: ' + encode2 + ' -c:a aac -ac 2 -r 30 -f nut - | ffmpeg -i pipe: -c copy ' + container_hls + ' ' + outname_hls, shell=True, preexec_fn=os.setsid)

def getChannel():
    data = requests.get(url).json()["video"]
    if data:
        return data.split(".m3u8")[0].split("/")[-1]
    return ''
    
atexit.register(kill)
curr = getChannel()
launch(curr)
# Repeat every 3 seconds
while True:
    time.sleep(3)
    try:
        new = getChannel()
        # If different from current channel
        # stop the current stream and restart
        if new != curr:
            curr = new
            kill()
            launch(curr)
        # If we are supposed to be streaming and process exited, restart
        if new and stream and stream.poll() != None:
            # print(stream.poll())
            launch(new)
    except Exception as e:
        print(e)
