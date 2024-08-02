#!/bin/bash

# HLS for hls.js players, serve segments with nginx (same for DASH)
# mpegts stream over http for mpegts.js players
# nginx proxies incoming requests on port 80 to broadcast server on 8081
#  \
#  \
#-c copy -f dash -seg_duration 2 -window_size 500  /var/www/dash/tv.mpd \

nc -l 5000 \
| node /root/tv/broadcast.js 8080 \
| ffmpeg -err_detect ignore_err -i pipe: -c:v libx264 -x264-params "keyint=60:scenecut=0" -preset veryfast -c:a aac -ac 2 -c:s mov_text -r 30 -f mp4 -movflags frag_keyframe+empty_moov+dash - \
| ffmpeg -err_detect ignore_err -i pipe: \
-c copy -f hls -hls_time 2 -hls_list_size 4000 -hls_flags delete_segments+append_list -hls_segment_type fmp4 /var/www/hls/tv.m3u8 \
-c copy -f mpegts - \
| node /root/tv/broadcast.js 8081 > /dev/null

# As of July 2024 mpegts doesn't support av1 (planned in future)
# apple hls spec says only fmp4 is supported for x265 or av1 content
# subtitles don't work by default with fmp4: -c:s mov_text
# subtitles don't seem to be muxed properly when using av1
# when using DASH subtitles need to be declared in mpd: descriptor=<Accessibility schemeIdUri=\"urn:scte:dash:cc:cea-608:2015\" value=\"CC1=eng\"/>
# output fmp4 stream: -f mp4 -movflags frag_keyframe+empty_moov
# tested working presets for 3 amd cores (cpx series)
#-c:v libx264 -preset fast -x264-params "keyint=60:scenecut=0"
#-c:v libsvtav1 -g 60 -preset 11
#-c:v libx265 -preset veryfast -x265-params "keyint=60:min-keyint=60"
# could also transcode to multiple resolutions and save to separate hls streams
#-vf scale=-1:320
