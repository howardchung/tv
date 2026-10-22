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
    encode2 = '-c:v libx264 -profile:v main -preset veryfast -x264-params "keyint=30:scenecut=0" -crf 26 -g 30'
    encode3 = '-c:v libx265 -preset veryfast -x265-params "keyint=30"'
    encode4 = '-c:v libsvtav1 -g 30 -preset 13' # -preset 9 for decent quality but requires a lot of CPU
    encode5 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v h264_vaapi -sei -a53_cc -g 30 -qp 26'
    encode6 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v hevc_vaapi -sei -a53_cc -g 30 -qp 26'
    encode7 = '-vaapi_device /dev/dri/renderD128 -vf \'format=nv12,hwupload\' -c:v av1_vaapi -sei -a53_cc -g 30 -qp 26'

    container_flv = '-f flv'
    container_fmp4 = '-f mp4 -movflags frag_keyframe+empty_moov'
    outname_hls = basepath + id + '.m3u8'
    outname_dash = basepath + id + '.mpd'
    outname3 = 'rtmp://5.78.115.83:5000'

    # One encode, several outputs, as two piped ffmpeg processes
    # (https://trac.ffmpeg.org/wiki/Creating%20multiple%20outputs): the first ffmpeg encodes once
    # and writes nut to stdout, the second reads that and stream-copies it (-c copy) to every output.
    # nut carries the codec extradata (SPS/PPS/VPS, AAC config) in its header and keeps AAC raw.
    container_hls = [
        '-f', 'hls',
        '-hls_time', '6',
        '-hls_list_size', '4800',
        '-hls_flags', 'delete_segments+append_list',
        '-hls_segment_type', 'fmp4',
        '-hls_fmp4_init_filename', f'{id}_init.mp4',
        outname_hls,
    ]
    container_dash = [
        '-f', 'dash',
        '-seg_duration', '6',
        '-window_size', '100',
        '-extra_window_size', '1',
        '-init_seg_name', f'{id}_init_$RepresentationID$.$ext$',
        '-media_seg_name', f'{id}_chunk_$RepresentationID$-$Number$.$ext$',
        outname_dash,
    ]
    container_ts = ['-f', 'mpegts', 'pipe:1']  # served over HTTP by a second broadcast.js

    encode = encode6
    if adapter == "1":
        encode = encode2

    # Copying out of nut leaves the video with a nut tag that mp4-style muxers (hls fmp4, dash)
    # reject, so set the tag explicitly. hvc1 (rather than hev1) is what Safari wants for HEVC.
    # The muxers get SPS/PPS/VPS from the nut header, so the MPD codec string is complete
    # (e.g. avc1.4d401f). HEVC is only written in full (hvc1.1.6.L93.B0) by a recent ffmpeg,
    # older builds (6.1, 7.0) write a bare "hvc1" whatever the options.
    vtag = []
    if 'hevc' in encode or 'x265' in encode:
        vtag = ['-tag:v', 'hvc1']
    elif '264' in encode:
        vtag = ['-tag:v', 'avc1']
    mp4_opts = [*vtag, '-tag:a', 'mp4a']

    port = str(8080 + int(adapter))
    ts_port = str(8180 + int(adapter))  # HTTP port for the mpegts output

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
    ffmpeg_enc = subprocess.Popen(
        ['ffmpeg', '-i', 'pipe:', *shlex.split(encode), '-c:a', 'aac', '-ac', '2', '-r', '30', '-f', 'nut', 'pipe:1'],
        stdin=node.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    node.stdout.close()  # so node gets SIGPIPE if ffmpeg exits

    ffmpeg_mux = subprocess.Popen(
        ['ffmpeg', '-f', 'nut', '-i', 'pipe:',
         '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy', *mp4_opts, *container_hls,
         '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy', *mp4_opts, *container_dash,
         '-map', '0:v:0', '-map', '0:a:0', '-c', 'copy', *container_ts],
        stdin=ffmpeg_enc.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    ffmpeg_enc.stdout.close()  # so the encoder gets SIGPIPE if the second ffmpeg exits

    # the second ffmpeg's stdout carries the mpegts output, serve it over HTTP
    ts_node = subprocess.Popen(
        ['node', 'broadcast.js', ts_port],
        stdin=ffmpeg_mux.stdout, stdout=subprocess.DEVNULL,
    )
    ffmpeg_mux.stdout.close()  # so the second ffmpeg gets SIGPIPE if the ts server exits

    procs.extend([zap, node, ffmpeg_enc, ffmpeg_mux, ts_node])
    ffmpeg_proc = ffmpeg_enc
    for p in (ffmpeg_enc, ffmpeg_mux):
        threading.Thread(target=read_stderr, args=(p.stderr,), daemon=True).start()


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
