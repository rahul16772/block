#!/bin/bash

set -e -u
set -o pipefail

. blockassist-venv/bin/activate

export DISPLAY=:0
export GALLIUM_DRIVER=d3d12
export LIBGL_ALWAYS_INDIRECT=0

unset LWJGL_DISABLE_XRANDR LWJGL_DISABLE_XF86VM

export _JAVA_OPTIONS="-Dorg.lwjgl.opengl.Display.allowSoftwareOpenGL=true -Dorg.lwjgl.opengl.Display.enableHighDPI=false -Djava.awt.headless=false"

export PULSE_SERVER=none
export ALSA_PCM_CARD=-1
export ALSA_PCM_DEVICE=-1
export ALSA_CONFIG_PATH=/dev/null

if [ -n "$WSL_DISTRO_NAME" ] && [ -e "/mnt/wslg/.X11-unix/X0" ]; then
    echo "Detected WSLg - using built-in Xwayland support"
    export DISPLAY=:0
    python -m malmo.minecraft launch --num_instances 2 --goal_visibility True False > 'logs/malmo.log' 2>&1
else
    echo "Using Xvfb with RANDR extension support"
    export DISPLAY=:99
    
    Xvfb :99 -screen 0 1024x768x24 +extension RANDR +extension GLX +render -noreset &
    XVIDEO_PID=$!
    
    sleep 2
    
    if ! xrandr -q >/dev/null 2>&1; then
        echo "Error: RANDR extension not available. Xvfb may not have started properly."
        kill $XVIDEO_PID 2>/dev/null || true
        exit 1
    fi
    
    python -m malmo.minecraft launch --num_instances 2 --goal_visibility True False > 'logs/malmo.log' 2>&1
    
    kill $XVIDEO_PID 2>/dev/null || true
fi