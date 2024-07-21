dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | ffmpeg -err_detect ignore_err -i pipe: -c:v copy -c:a copy -f flv rtmp://5.161.147.222/live/mpeg
