#!/bin/bash

#send
dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | nc -u 5.161.147.222 5000
#dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | ffmpeg -i pipe: -c:v libx264 -preset superfast -c:a aac -ac 1 -f flv rtmp://5.161.147.222:1935/transcode/king-hd

#receive
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -f flv rtmp://localhost:1935/live/king-hd
#ffmpeg -listen 1 -i tcp://0.0.0.0:5000 -c:v libx264 -preset veryfast -c:a aac -ac 1 -hls_flags delete_segments -f hls /var/www/html/stream/king-hd.m3u8
ffmpeg -err_detect ignore_err -i udp://localhost:5000 -c:v libx264 -preset veryfast -c:a aac -ac 2 -hls_flags delete_segments -hls_start_number_source epoch -hls_list_size 1000 -f hls /var/www/html/stream/tv.m3u8

#transcode
ffmpeg -i rtmp://localhost:1935/transcode/$name -vf "scale=480:320" -c:v libx264 -c:a copy -f flv rtmp://localhost:1935/live/$name

