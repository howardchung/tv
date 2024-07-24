#!/bin/bash

ffmpeg -err_detect ignore_err -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset fast -crf 23 -x264-params keyint=60 -c:a aac -ac 2 -f mpegts - \ 
| ffmpeg -i pipe: \
#HLS for hls.js players, serve segments with nginx
-c copy -f hls -hls_time 2 hls_list_size 2000 -hls_flags delete_segments -hls_start_number_source epoch /tmp/hls/tv.m3u8 \
-c copy -f mpegts - \
#serve stream over http for mpegts.js players
# nginx proxies incoming requests on port 80 to broadcast server on 8081
| node ~/broadcast.js

# As of July 2024 mpegts doesn't support av1 (planned in future)
#-c:v libsvtav1 -g 60 -preset 10 (0 to 13)
#-c:v libx265 -preset fast
#-vf scale=-1:320
# could also transcode to multiple resolutions and save to separate hls streams
