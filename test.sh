#!/bin/bash

#send
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | nc 5.161.147.222 5000

#receive
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -crf 23 -c:a aac -ac 1 -f flv rtmp://localhost:1935/live/king-hd
ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -hls_flags delete_segments -f hls /var/www/king-hd.m3u8
