#!/bin/bash

#send
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | nc -u 5.161.147.222 5000

#receive
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -crf 23 -c:a aac -ac 1 -f flv rtmp://localhost:1935/live/king-hd
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -hls_flags delete_segments -f hls /var/www/html/stream/king-hd.m3u8
ffmpeg -err_detect ignore_err -i udp://localhost:5000 -c:v libx264 -preset faster -c:a aac -ac 2 -hls_flags delete_segments -hls_start_number_source epoch -f hls /var/www/html/stream/tv.m3u8
