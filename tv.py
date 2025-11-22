import requests
import subprocess
import time
import os
import signal
import atexit
import json
import sys
import io

try:
    adapter = sys.argv[1]
except:
    adapter = "0"

stream: subprocess.Popen = None
basepath = '/var/www/html/'
url = "https://backend.watchparty.me/roomData/alike-week-recognize"
if adapter == "1":
    url = "https://backend.watchparty.me/roomData/supreme-faucet-kneel"

def kill():
    sys.exit()

def launch(id):
    global stream
    if not id:
        return
    #-vf scale=-1:720
    encode1 = '-c:v copy'
    encode2 = '-c:v libx264 -preset veryfast -x264-params "keyint=30:scenecut=0" -crf 26'
    encode3 = '-c:v libx265 -preset veryfast -x265-params "keyint=30"'
    encode4 = '-c:v libsvtav1 -g 150 -preset 9'
    encode5 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 30 -qp 26'
    encode6 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v hevc_vaapi -sei -a53_cc -g 30 -qp 26'
    encode7 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v av1_vaapi -sei -a53_cc -g 30 -qp 26'

    container_hls = '-f hls -hls_time 3 -hls_list_size 7000 -hls_flags delete_segments+append_list' # -hls_segment_type fmp4
    container_dash = '-f dash -seg_duration 3 -window_size 1000' #-tag:v av01 -tag:a mp4a 
    container_flv = '-f flv'
    container_fmp4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    
    outname_hls = basepath + id + '.m3u8'
    outname_dash = basepath + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'

    encode = encode6
    if adapter == "1":
        encode = encode6
    port = str(8080 + int(adapter))
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | node broadcast.js ' + port + ' | ffmpeg -i pipe: ' + encode + ' -c:a aac -ac 2 -r 30 ' + container_hls + ' ' + outname_hls, shell=True, stderr=subprocess.PIPE, text=True)

def getChannel():
    data = requests.get(url).json()["video"]
    if data:
        return data.split(".m3u8")[0].split("/")[-1]
    return ''

def check_and_delete():
   # folder is the name of the folder in which we have to perform the delete operation
   folder = basepath
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
               
curr = getChannel()
launch(curr)
lastTime = time.time()

while True:
    now = time.time()
    if now - lastTime > 3:
        new = getChannel()
        lastTime = now
        # If different from current channel, delete any existing files on the new channel and restart
        if new != curr:
            subprocess.run('rm ' + basepath + new + '*', shell=True)
            #subprocess.run('rm ' + basepath + init.mp4', shell=True)
            kill()
        if stream and stream.poll() != None:
            kill()
    line = stream.stderr.readline()
    print(line)
    if "Non-monotonic DTS" in line:
        kill()
