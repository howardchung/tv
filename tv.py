import requests
import subprocess
import time
import os
import signal
import atexit
import json
import sys

# king-hd (nbc) or komo (abc)
stream: subprocess.Popen = None
adapter = sys.argv[1] or 0
url = 'https://howardchung.github.io/tv/adapter' + adapter + '.html'
preset = "superfast"
crf = "28"

def kill():
    global stream
    if stream != None:
        os.killpg(os.getpgid(stream.pid), signal.SIGTERM)
        stream = None

def launch(id):
    global stream
    if not id:
        return
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -err_detect ignore_err -i pipe: -c:v libx264 -crf ' + crf + ' -preset ' + preset + ' -x264-params keyint=60 -c:a aac -ac 1 -f flv rtmp://5.161.147.222/live/' + adapter, shell=True, preexec_fn=os.setsid)

atexit.register(kill)
x = requests.get(url)
channel = x.text.strip()
launch(channel)
# Repeat every 3 seconds
while True:
    time.sleep(3)
    try:
        x = requests.get(url)
        new = x.text.strip()
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
