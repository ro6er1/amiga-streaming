#!/usr/bin/env python3
import subprocess
import os
import time

# Paths
MEDIAMTX_PATH = "/home/pi/mediamtx"
CONFIG_PATH = "/home/pi/mediamtx.yml"

# Kill old processes
subprocess.run(["pkill", "-f", "mediamtx"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["pkill", "-f", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start MediaMTX
mediamtx_process = subprocess.Popen([MEDIAMTX_PATH, CONFIG_PATH])
time.sleep(2)

# FFmpeg command with 48kHz s16 audio for Opus
ffmpeg_command = [
    "ffmpeg",
    # Video input
    "-f", "v4l2",
    "-framerate", "30",
    "-video_size", "640x480",
    "-i", "/dev/video0",
    # Audio input with large buffer
    "-fflags", "+genpts",
    "-thread_queue_size", "4096",
    "-f", "alsa",
    "-ar", "48000",             # 48kHz is safe and ideal for Opus
    "-ac", "2",                 # capture stereo even if source is mono
    "-i", "plughw:2,0",
    # audio filters for stability
    "-filter:a", "aresample=async=1:min_hard_comp=0.100000:first_pts=0,volume=0.8",
    # Video encoding
    "-c:v", "libx264",
    "-preset", "ultrafast",
    "-tune", "zerolatency",
    "-b:v", "1M",
    # encoding
    "-c:a", "libopus",
    "-b:a", "96k",
    "-sample_fmt", "s16",
    # Output
    "-f", "rtsp",
    "-muxdelay", "0.1",  # Improve packet timing
    "rtsp://localhost:8554/mystream"
]


try:
    ffmpeg_process = subprocess.Popen(ffmpeg_command)
    ffmpeg_process.wait()
except KeyboardInterrupt:
    print("\nStopping stream...")
finally:
    if ffmpeg_process and ffmpeg_process.poll() is None:
        ffmpeg_process.terminate()
    if mediamtx_process and mediamtx_process.poll() is None:
        mediamtx_process.terminate()
    print("Stopped cleanly.")

