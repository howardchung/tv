while true
do
ffmpeg -i "http://127.0.0.1:9981/stream/channel/78065103b76684298a77d0b0227e4a1b?profile=pass" -filter:v fps=fps=30 -c:v libx264 -preset veryfast -x264-params keyint=60 -b:v 2.5M -c:a aac -ar 44100 -ac 1 -drop_pkts_on_overflow 1 -attempt_recovery 1 -recover_any_error 1 -f flv rtmp://5.161.147.222/live/abc

done
