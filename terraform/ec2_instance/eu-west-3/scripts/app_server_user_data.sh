#!/bin/bash
yum update -y
yum install -y docker docker-compose-plugin
systemctl enable docker
systemctl start docker
