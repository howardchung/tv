#!/bin/bash

echo '0xxxxxxxxxxxxxx7:KxxxxxxxxxxxxxxxxxQ' > /etc/passwd-s3fs
sudo chmod 640 /etc/passwd-s3fs
sudo mkdir -p ~/backblaze
sudo s3fs watchparty-hls ~/backblaze -o passwd_file=/etc/passwd-s3fs -o url=https://s3.us-east-005.backblazeb2.com
