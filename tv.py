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
    global curr
    if stream != None:
        os.killpg(os.getpgid(stream.pid), signal.SIGTERM)
        stream = None

def launch(id):
    global stream
    if not id:
        return
    #-vf scale=-1:720
    encode1 = '-c:v copy'
    encode2 = '-c:v libx264 -preset veryfast -x264-params "keyint=60:scenecut=0" -crf 26'
    encode3 = '-c:v libx265 -preset veryfast -x265-params "keyint=60:min-keyint=60"'
    encode4 = '-c:v libsvtav1 -g 60 -preset 9'
    encode5 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 60 -qp 26'
    encode6 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v hevc_vaapi -sei -a53_cc -g 60 -qp 26'
    encode7 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v av1_vaapi -sei -a53_cc -g 60 -qp 26'

    container_hls = '-f hls -hls_time 4 -hls_list_size 3600 -hls_flags delete_segments+append_list' #-hls_segment_type fmp4
    container_dash = '-f dash -seg_duration 4 -window_size 900' #-tag:v av01 -tag:a mp4a 
    container_flv = '-f flv'
    container_fmp4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    
    outname_hls = '/mnt/watchparty-hls/' + id + '.m3u8'
    outname_dash = '/mnt/watchparty-hls/' + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'

    encode = encode5
    if adapter == "1":
        encode = encode6
    #subprocess.Popen('rm /mnt/watchparty-hls/' + curr + '*', shell=True)
    #subprocess.Popen('rm /mnt/watchparty-hls/init.mp4', shell=True)
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -fflags +igndts -i pipe: ' + encode + ' -c:a aac -ac 2 -r 30 -f nut - | ffmpeg -i pipe: -c copy ' + container_hls + ' ' + outname_hls, shell=True, preexec_fn=os.setsid)

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
            kill()
            curr = new
            launch(curr)
        # If we are supposed to be streaming and process exited, restart
        if new and stream and stream.poll() != None:
            # print(stream.poll())
            launch(new)
    except Exception as e:
        print(e)
