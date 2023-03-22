import requests
import subprocess
import time
import os
import signal
import atexit
import json

channels = {
    'nbc': '1acf95b4c41cc63f4b34b7fd89e3e84c',
    'abc': '78065103b76684298a77d0b0227e4a1b',
    'cbs': 'c9909ad60ae8c1a4c27728bc2fa2a92b',
    'fox': '77a9546b7a1642fa2da7f5fd2e8939f8',
}

stream: subprocess.Popen = None

def launch(id):
    print(id)
    return subprocess.Popen('ffmpeg -i "http://127.0.0.1:9981/stream/channel/' + id + '?profile=pass" -filter:v fps=fps=30 -c:v libx264 -preset veryfast -x264-params keyint=60 -b:v 2.5M -c:a aac -ar 44100 -ac 1 -drop_pkts_on_overflow 1 -attempt_recovery 1 -recover_any_error 1 -f flv rtmp://5.161.147.222/live/abc', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def kill():
    print('kill group')
    os.killpg(os.getpgid(stream.pid), signal.SIGTERM)

channel = 'abc'
stream = launch(channels[channel])
# Repeat every 3 seconds
# Read the channel from URL
while True:
    time.sleep(3)
    try:
        x = requests.get('https://howardchung.github.io/channel')
        # new = json.loads(x.text)['title']
        new = x.text.strip()
        # If different from current channel
        # stop the current stream and restart
        if new != channel and new in channels:
            channel = new
            if stream != None:
                print('kill process')
                os.system("killall -9 ffmpeg");
            stream = launch(channels[new])
        # If process crashes, restart it
        if stream.poll() != None:
            print(stream.poll())
            stream = launch(channels[channel])
    except:
        print('Exception!')

atexit.register(kill)
