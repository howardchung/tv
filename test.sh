dvbv5-zap --adapter=1 --input-format=ZAP -c channels.conf -o - "king-hd" | nc -l -p 5000 5.161.147.222
