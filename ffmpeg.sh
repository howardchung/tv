#!/bin/bash

# HLS for hls.js players, serve segments with nginx (same for DASH)
# mpegts stream over http for mpegts.js players
# nginx proxies incoming requests on port 80 to broadcast server on 8081
# -c copy -f hls -hls_time 2 -hls_list_size 3000 -hls_start_number_source epoch -hls_flags delete_segments /var/www/hls/tv.m3u8 \
# | node /root/tv/broadcast.js 8081 \

nc -l 5000 \
| node /root/tv/broadcast.js 8080 \
| ffmpeg -err_detect ignore_err -f mpegts -i pipe: -c:v libx264 -preset veryfast -g 60 -keyint_min 60 -c:a aac -ac 2 -c copy -f dash -window_size 3000 -frag_duration 2 -streaming 1 -hls_playlist 1 /var/www/dash/tv.mpd

# As of July 2024 mpegts doesn't support av1 (planned in future)
# apple hls spec says only fmp4 is supported for x265 or av1 content
# subtitles don't work by default with fmp4: -c:s mov_text
# subtitles don't seem to be muxed properly when using av1
# when using DASH subtitles need to be declared in mpd: descriptor=<Accessibility schemeIdUri=\"urn:scte:dash:cc:cea-608:2015\" value=\"CC1=eng\"/>
# output fmp4 stream: -f mp4 -movflags frag_keyframe+empty_moov
# tested working presets for 3 amd cores (cpx series)
#-c:v libx264 -preset fast -g 60 -keyint_min 60
#-c:v libsvtav1 -g 60 -preset 11
#-c:v libx265 -preset veryfast -x265-params "keyint=60:min-keyint=60"
# could also transcode to multiple resolutions and save to separate hls streams
#-vf scale=-1:320
