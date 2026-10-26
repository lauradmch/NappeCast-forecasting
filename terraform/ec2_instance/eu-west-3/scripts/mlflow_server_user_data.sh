#!/bin/bash
yum update -y

fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile swap swap defaults 0 0' >> /etc/fstab

yum install -y docker
systemctl enable docker
systemctl start docker

mkdir -p /usr/local/lib/docker/cli-plugins
curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

BUILDX_URL=$(curl -s https://api.github.com/repos/docker/buildx/releases/latest | grep "browser_download_url.*linux-amd64\"" | cut -d '"' -f 4 | head -n 1)
curl -SL "$BUILDX_URL" -o /usr/local/lib/docker/cli-plugins/docker-buildx
chmod +x /usr/local/lib/docker/cli-plugins/docker-buildx

yum install -y python3-pip
pip3 install boto3
