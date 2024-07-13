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

def kill():
    os.kill(stream.pid, signal.SIGTERM)
    stream = None
atexit.register(kill)

def launch(id):
    if not id:
        return
    stream = subprocess.Popen('dvbv5-zap --adapter=' + adapter + ' --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -err_detect ignore_err -i pipe: -c:v libx264 -preset veryfast -x264-params keyint=60 -b:v 3M -c:a aac -ac 1 -f flv rtmp://5.161.147.222/live/' + adapter, shell=True)

x = requests.get(url)
channel = x.text.strip()
launch(channel)
# Repeat every 3 seconds
while True:
    time.sleep(3)
    try:
        x = requests.get(url)
        new = x.text.strip()
        # print(new, channel)
        # If different from current channel
        # stop the current stream and restart
        if new != channel:
            channel = new
            if stream != None:
                kill()
            launch(new)
        # If process crashes, restart it
        if stream.poll() != None:
            print(stream.poll())
            launch(channel)
    except:
        print('Exception!')
