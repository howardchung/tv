import requests
import subprocess
import time
import os
import signal
import atexit
import json
import sys
import io
import re
import shlex
import queue
import threading
from collections import deque

try:
    adapter = sys.argv[1]
except:
    adapter = "0"

# The pipeline: dvbv5-zap | node broadcast.js | ffmpeg
procs = []
ffmpeg_proc: subprocess.Popen = None
basepath = '/var/www/html/'

url = "https://backend.watchparty.me/roomData/alike-week-recognize"
if adapter == "1":
    url = "https://backend.watchparty.me/roomData/supreme-faucet-kneel"

startTime = time.time()

# Only restart on "Non-monotonic DTS" after this many seconds of uptime,
# and only if it's logged DTS_MAX_COUNT times within DTS_WINDOW seconds
DTS_GRACE_PERIOD = 3600
DTS_MAX_COUNT = 5
DTS_WINDOW = 60
dts_times = deque()

# Channel ids come from remote data (WatchParty room) and end up in argv and
# filenames, so only allow a conservative character set. Must start with an
# alphanumeric so it can't be mistaken for a command-line option.
SAFE_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')

# ffmpeg stderr lines, filled by a reader thread so the main loop never blocks on the pipe
line_queue = queue.Queue()


def kill():
    # Stop the whole pipeline (we no longer have a shell to do it for us), then exit.
    # Under systemd, Restart=always brings the script back up.
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    for p in procs:
        try:
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    sys.exit()


def read_stderr(stream):
    for line in iter(stream.readline, ''):
        line_queue.put(line)


def launch(id):
    global ffmpeg_proc
    if not id:
        return
    if not SAFE_ID.match(id):
        print(f"Refusing to launch, unsafe channel id: {id!r}")
        return

    #-vf scale=-1:720
    encode1 = '-c:v copy'
    encode2 = '-c:v libx264 -preset veryfast -x264-params "keyint=30:scenecut=0" -crf 26 -g 30'
    encode3 = '-c:v libx265 -preset veryfast -x265-params "keyint=30"'
    encode4 = '-c:v libsvtav1 -g 30 -preset 13' # -preset 9 for decent quality but requires a lot of CPU
    encode5 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 30 -qp 26'
    encode6 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v hevc_vaapi -sei -a53_cc -g 30 -qp 26'
    encode7 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v av1_vaapi -sei -a53_cc -g 30 -qp 26'

    container_hls = [
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_list_size', '4800',
        '-hls_flags', 'delete_segments+append_list',
        '-hls_segment_type', 'fmp4',
        '-hls_fmp4_init_filename', f'{id}_init.mp4',
    ]
    container_dash = rf'-f dash -seg_duration 6 -window_size 100 -init_seg_name "{id}_init_\$RepresentationID\$.\$ext\$" -media_seg_name "{id}_chunk_\$RepresentationID\$-\$Number\$.\$ext\$"' # -tag:v av01 -tag:v hvc1 -tag:a mp4a
    container_flv = '-f flv'
    container_fmp4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    outname_hls = basepath + id + '.m3u8'
    outname_dash = basepath + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'

    encode = encode6
    if adapter == "1":
        encode = encode2

    port = str(8080 + int(adapter))

    # No shell: every argument is passed as a separate argv entry, so nothing in
    # `id` can be interpreted as shell syntax.
    zap = subprocess.Popen(
        ['dvbv5-zap', f'--adapter={adapter}', '--input-format=ZAP', '-c', 'channels.conf', '-o', '-', id],
        stdout=subprocess.PIPE,
    )
    node = subprocess.Popen(
        ['node', 'broadcast.js', port],
        stdin=zap.stdout, stdout=subprocess.PIPE,
    )
    zap.stdout.close()  # so zap gets SIGPIPE if node exits
    ffmpeg = subprocess.Popen(
        ['ffmpeg', '-i', 'pipe:', *shlex.split(encode), '-c:a', 'aac', '-ac', '2', '-r', '30', *container_hls, outname_hls],
        stdin=node.stdout, stderr=subprocess.PIPE, text=True,
    )
    node.stdout.close()  # so node gets SIGPIPE if ffmpeg exits

    procs.extend([zap, node, ffmpeg])
    ffmpeg_proc = ffmpeg
    threading.Thread(target=read_stderr, args=(ffmpeg.stderr,), daemon=True).start()


def getChannel():
    data = requests.get(url, timeout=5).json()["video"]
    return data.split(".m3u8")[0].split("/")[-1]


def handle_line(line):
    print(line.rstrip())
    if "Non-monotonic DTS" in line and time.time() - startTime > DTS_GRACE_PERIOD:
        now = time.time()
        dts_times.append(now)
        while dts_times and now - dts_times[0] > DTS_WINDOW:
            dts_times.popleft()
        if len(dts_times) >= DTS_MAX_COUNT:
            print(f"{len(dts_times)} Non-monotonic DTS warnings in {DTS_WINDOW}s, restarting")
            kill()


curr = getChannel()
launch(curr)
lastTime = time.time()
while True:
    now = time.time()
    if now - lastTime > 3:
        lastTime = now
        # delete old files periodically
        # deleting * also removes mp4 init segments, so touch them periodically
        subprocess.run(f'touch {basepath}/*.mp4', shell=True)
        subprocess.run(f'find {basepath}/ -name "*" -mmin +1440 -delete', shell=True)
        try:
            new = getChannel()
            if new != curr:
                # New channel, restart
                kill()
        except Exception as e:
            # Catch exceptions here to avoid restarting on HTTP errors, e.g. WatchParty restarts
            print(e)
            print("Exception fetching new channel, continuing")

    # If any stage of the pipeline has exited, the stream is broken, restart
    if any(p.poll() is not None for p in procs):
        kill()

    if ffmpeg_proc:
        # Wait up to 1s for ffmpeg output, then drain whatever else is queued.
        # The timeout means the checks above still run if ffmpeg goes silent.
        try:
            handle_line(line_queue.get(timeout=1))
            while True:
                handle_line(line_queue.get_nowait())
        except queue.Empty:
            pass
    else:
        time.sleep(1)
