#!/bin/bash

#sudo apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio
dvbv5-zap --adapter=0 --input-format=ZAP -c channels.conf -o - king-hd | gst-launch-1.0 -v fdsrc is-live=true ! tsdemux ! mpegvideoparse ! avdec_mpeg2video ! videoconvert ! x264enc ! hlssink2 target-duration=5 max-files=2000 location=/mnt/watchparty-hls
gst-launch-1.0 dvbsrc -e frequency=539000000 delsys="atsc" modulation="8vsb" ! decodebin name=demux ! hlssink2 name=mux target-duration=5 max-files=2000 location=/mnt/watchparty-hls/king-hd%d.ts playlist_location=/mnt/watchparty-hls/king-hd.m3u8 demux. ! videoconvert ! videorate max-rate=30 ! x264enc key-int-max=30 ! mux.video demux. ! audioconvert ! avenc_aac ! mux.audio
