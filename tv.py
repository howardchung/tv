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
    encode2 = '-c:v libx264 -preset veryfast -x264-params "keyint=150:scenecut=0" -crf 26'
    encode3 = '-c:v libx265 -preset veryfast -x265-params "keyint=150"'
    encode4 = '-c:v libsvtav1 -g 150 -preset 9'
    encode5 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 150 -qp 26'
    encode6 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v hevc_vaapi -sei -a53_cc -g 150 -qp 26'
    encode7 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v av1_vaapi -sei -a53_cc -g 150 -qp 26'

    container_hls = '-f hls -hls_time 5 -hls_list_size 2000 -hls_flags delete_segments+append_list' # -hls_segment_type fmp4
    container_dash = '-f dash -seg_duration 4 -window_size 900' #-tag:v av01 -tag:a mp4a 
    container_flv = '-f flv'
    container_fmp4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    
    outname_hls = '/mnt/watchparty-hls/' + id + '.m3u8'
    outname_dash = '/mnt/watchparty-hls/' + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'

    encode = encode6
    if adapter == "1":
        encode = encode5
    #subprocess.Popen('rm /mnt/watchparty-hls/' + curr + '*', shell=True)
    #subprocess.Popen('rm /mnt/watchparty-hls/init.mp4', shell=True)
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | node broadcast.js 8080 | ffmpeg -i pipe: ' + encode + ' -c:a aac -ac 2 -r 30 -f nut - | ffmpeg -i pipe: -c copy ' + container_hls + ' ' + outname_hls, shell=True, preexec_fn=os.setsid)

def getChannel():
    data = requests.get(url).json()["video"]
    if data:
        return data.split(".m3u8")[0].split("/")[-1]
    return ''

def check_and_delete():
   # folder is the name of the folder in which we have to perform the delete operation
   folder = "/mnt/watchparty-hls"
   # loop to check all files one by one 
   # os.walk returns 3 things: current path, files in the current path, and folders in the current path 
   for (root,dirs,files) in os.walk(folder, topdown=True):
       for f in files:
           # temp variable to store path of the file 
           file_path = os.path.join(root,f)
           # get the timestamp, when the file was modified 
           timestamp_of_file_modified = os.path.getmtime(file_path)
           # convert timestamp to datetime
           modification_date = datetime.datetime.fromtimestamp(timestamp_of_file_modified)
           # find the number of hours when the file was modified
           diff = datetime.datetime.now() - modification_date
           if diff.total_seconds() > 6 * 3600:
               # remove file 
               os.remove(file_path)
               print(f" Delete : {f}")
               
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
        #check_and_delete()
    except Exception as e:
        print(e)
