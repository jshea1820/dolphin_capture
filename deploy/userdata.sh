#!/bin/bash

# Install git
sudo apt update && sudo apt upgrade -y
sudo apt install -y git

# Load the full startup script to the instance
git clone https://github.com/jshea1820/dolphin_capture.git
