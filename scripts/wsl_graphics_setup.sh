#!/bin/bash

set -e -u
set -o pipefail

echo "Setting up WSL graphics and audio dependencies for LWJGL-2 compatibility..."

sudo apt-get update

echo "Installing graphics dependencies..."
sudo apt-get install -y \
    xvfb \
    x11-xserver-utils \
    mesa-utils \
    mesa-utils-extra \
    libgl1-mesa-dri \
    libgl1-mesa-glx \
    libglu1-mesa \
    xauth \
    x11-apps \
    x11-utils

echo "Installing audio dependencies..."
sudo apt-get install -y \
    libasound2 \
    libasound2-dev \
    libopenal1 \
    libopenal-dev

echo "Creating dummy ALSA configuration for WSL compatibility..."
sudo mkdir -p /etc/alsa/conf.d
echo 'pcm.!default { type null }' | sudo tee /etc/alsa/conf.d/99-dummy.conf > /dev/null
echo 'ctl.!default { type null }' | sudo tee -a /etc/alsa/conf.d/99-dummy.conf > /dev/null

echo "Verifying installations..."

if command -v xrandr >/dev/null 2>&1; then
    echo "✅ xrandr is installed"
else
    echo "❌ xrandr is not installed (should be part of x11-xserver-utils)"
    exit 1
fi

if command -v Xvfb >/dev/null 2>&1; then
    echo "✅ Xvfb is installed"
else
    echo "❌ Xvfb is not installed"
    exit 1
fi

if command -v xdpyinfo >/dev/null 2>&1; then
    echo "✅ xdpyinfo is installed"
else
    echo "❌ xdpyinfo is not installed (should be part of x11-utils)"
    exit 1
fi

if command -v glxinfo >/dev/null 2>&1; then
    echo "✅ glxinfo is installed"
else
    echo "❌ glxinfo is not installed (should be part of mesa-utils)"
    exit 1
fi

if [ -f "/usr/lib/x86_64-linux-gnu/libasound.so.2" ] || [ -f "/usr/lib/libasound.so.2" ]; then
    echo "✅ ALSA library is installed"
else
    echo "❌ ALSA library is not installed"
    exit 1
fi

if [ -f "/usr/lib/x86_64-linux-gnu/libopenal.so.1" ] || [ -f "/usr/lib/libopenal.so.1" ]; then
    echo "✅ OpenAL library is installed"
else
    echo "❌ OpenAL library is not installed"
    exit 1
fi

if [ -f "/etc/alsa/conf.d/99-dummy.conf" ]; then
    echo "✅ ALSA dummy configuration is installed"
else
    echo "❌ ALSA dummy configuration is not installed"
    exit 1
fi

if [ -n "$WSL_DISTRO_NAME" ] && [ -e "/mnt/wslg/.X11-unix/X0" ]; then
    echo "✅ WSLg detected - built-in Xwayland support available"
    echo "   You can use DISPLAY=:0 for graphics acceleration"
else
    echo "ℹ️  WSLg not detected - will use Xvfb for graphics"
    echo "   Make sure to use the updated run_malmo.sh script"
fi

