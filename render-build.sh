#!/usr/bin/env bash
set -o errexit

# تثبيت المكتبات
pip install --upgrade pip
pip install -r requirements.txt

# تحميل FFmpeg متوافق مع Railway
mkdir -p bin
curl -L https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz | tar -xJ --strip-components=1 -C bin
