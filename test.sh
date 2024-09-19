#!/bin/bash

#send
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | nc 5.78.115.83 5000
# local encode
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | ffmpeg -i pipe: -c:v libsvtav1 -preset 12 -c:a aac -ac 2 -f mpegts - | nc 5.78.115.83 5000
# local hw encode
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | ffmpeg -hwaccel vaapi -vaapi_device /dev/dri/renderD128 -i pipe: -vf 'format=nv12,hwupload' -c:v h264_vaapi -qp 24 -c:a aac -ac 2 -r 30 -f mp4 -movflags frag_keyframe+empty_moov - | nc 5.78.115.83 5000
# local hw encode for modern intel might require h264_qsv instead of vaapi

#receive
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -f flv rtmp://localhost:1935/live/king-hd
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -hls_flags delete_segments -f hls /var/www/html/stream/king-hd.m3u8
ffmpeg -err_detect ignore_err -i tcp://localhost:5000 -c:v libx264 -preset veryfast -c:a aac -ac 2 -hls_flags delete_segments -hls_start_number_source epoch -hls_list_size 1000 -f hls /var/www/html/stream/tv.m3u8

#serve
ffmpeg -err_detect ignore_err -i tcp://localhost:5000 -c:v libx264 -preset veryfast -c:a aac -ac 2 -listen 1 -f mp4 -movflags frag_keyframe+empty_moov http://0.0.0.0:8080

