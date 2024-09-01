tv
----
Experiments in streaming TV over the Internet using a closet Linux server

* Hardware is required for this project: A ATSC (US) digital TV Tuner and antenna
* I recommend the Hauppauge WinTV dualHD tuner (works with Linux)
* `w_scan2` is used to generate a local channel list (channels.conf)
* `tv.py` uses the `dvbv5-zap` Linux tool to capture input from the tuner and `nc` to a cloud server for distribution and transcoding
* The currently selected channel is set using a specific WatchParty room's data, if a change is detected, the capture is restarted
* The script also takes care of retries in case of network outages
* Transcoding from mpeg2 video could be done locally before upload, but the capture server is really old and bad at encoding (old Celeron has no QuickSync)
* The cloud server runs a service to collect the input using `nc`, then `ffmpeg` to convert the video to a better output codec for web (h264, av1, h265)
* The output is distributed in multiple containers for testing
* Chained `ffmpeg` commands create HLS/DASH files on the server, and nginx is set up to serve the HLS/DASH files statically
* An HTTP Node.js passthrough server (output stdin to all connected clients and also to stdout to allow further chaining) distributes the mpegts output and the original mpeg2 stream for testing
* The html file provides a web viewer to test viewing the output containers using multiple client playback libraries (mpegts.js, hls.js, dash.js, video.js, shaka)
* Previous iterations of this project used tvheadend, RTMP, and nginx-rtmp but these were eventually replaced
