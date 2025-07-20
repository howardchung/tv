#!/bin/bash

# echo '0xxxxxxxxxxxxxx7:KxxxxxxxxxxxxxxxxxQ' > /etc/passwd-s3fs
# sudo chmod 640 /etc/passwd-s3fs
# mkdir -p /mnt
# s3fs watchparty-hls /mnt -o passwd_file=/etc/passwd-s3fs -o url=https://s3.us-east-005.backblazeb2.com

#sudo -v ; curl https://rclone.org/install.sh | sudo bash
#rclone config
rclone mount -v --vfs-cache-mode=writes --vfs-write-back=2s backblaze:/ /mnt
