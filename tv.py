import requests
import subprocess
import time
import os
import signal
import atexit
import json

# king-hd (nbc) or komo (abc)
#http://127.0.0.1:9981/play/ticket/stream/channel/98d79ac2602abd0678317916fb2bf044?title=4.1%20%3A%20KOMO
#://127.0.0.1:9981/play/ticket/stream/channel/0fb23aab6bc3f953589495c112fcff37?title=5.1%20%3A%20KING-
stream: subprocess.Popen = None

def launch(id):
    return subprocess.Popen('dvbv5-zap --input-format=ZAP -c channels.conf -o - "' + id + '" | ffmpeg -err_detect ignore_err -i pipe: -c:v libx264 -preset ultrafast -x264-params keyint=60 -b:v 4M -c:a aac -ac 1 -f flv rtmp://5.161.147.222/live/abc', shell=True)

def kill():
    print('kill group')
    os.killpg(os.getpgid(stream.pid), signal.SIGTERM)

atexit.register(kill)

x = requests.get('https://howardchung.github.io/tv/selected.html')
channel = x.text.strip()
stream = launch(channel)
# Repeat every 3 seconds
# Read the channel from URL
while True:
    time.sleep(3)
    try:
        x = requests.get('https://howardchung.github.io/tv/selected.html')
        # new = json.loads(x.text)['title']
        new = x.text.strip()
        # print(new, channel)
        # If different from current channel
        # stop the current stream and restart
        if new != channel:
            channel = new
            if stream != None:
                print('kill process')
                os.system("killall -9 ffmpeg");
                os.system("killall -9 dvbv5-zap");
            stream = launch(new)
        # If process crashes, restart it
        if stream.poll() != None:
            print(stream.poll())
            stream = launch(channel)
    except:
        print('Exception!')
