#!/bin/bash

# Install git
sudo apt update && sudo apt upgrade -y
sudo apt install -y git

cd /home/ubuntu

# Load the full startup script to the instance
git clone https://github.com/jshea1820/dolphin_capture.git

# Signal completion
echo "userdata complete" > signal.txt
