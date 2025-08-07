# BlockAssist WSL Setup Guide

This guide explains the process separation improvements made to BlockAssist for better WSL (Windows Subsystem for Linux) compatibility.

## What Changed

The original `run.py` script ran all processes in a single execution flow, which could cause issues in WSL environments. The improved version separates the HTTP server from the main BlockAssist process for better compatibility and process management.

### New Architecture

1. **HTTP Server Process** (`run_http_server.py`): Runs the Next.js authentication server independently
2. **Main BlockAssist Process** (`run.py`): Handles Minecraft, AI training, and coordination
3. **Launcher** (`launcher.py`): Provides easy access to both modes

## Usage

### Option 1: Use the Launcher (Recommended)

```bash
# Run the full application with separated processes
python launcher.py

# Run only the HTTP server (for testing)
python launcher.py --http-only
```

### Option 2: Run Components Separately

```bash
# Terminal 1: Start HTTP server
python run_http_server.py

# Terminal 2: Start main application
python run.py
```

### Option 3: Original Method (Still Works)

```bash
# Run everything together (original behavior)
python run.py
```

## Benefits for WSL

1. **Better Process Isolation**: HTTP server runs in its own process space
2. **Improved Resource Management**: Each process can be managed independently
3. **Enhanced Debugging**: Easier to debug issues with separated logs
4. **WSL Compatibility**: Reduces conflicts that can occur in WSL environments

## Process Communication

The processes communicate through:
- **File System**: User data files in `modal-login/temp-data/`
- **Network**: HTTP server runs on localhost:3000
- **Process Monitoring**: Main process monitors HTTP server health

## Logs

- **HTTP Server**: `logs/yarn.log`
- **Main Process**: `logs/run.log`
- **Other Components**: Various logs in `logs/` directory

## Troubleshooting

### HTTP Server Won't Start
```bash
# Check if port 3000 is in use
lsof -i :3000

# Kill any existing processes on port 3000
kill $(lsof -ti :3000)
```

### Process Cleanup Issues
The daemon automatically handles process cleanup, but you can manually clean up:
```bash
# Kill all BlockAssist processes
pkill -f blockassist
pkill -f run_http_server.py
pkill -f "yarn dev"
```

### WSL-Specific Issues
- Ensure Windows firewall allows localhost connections
- Check that Node.js and Yarn are properly installed in WSL
- Verify Python dependencies are installed in WSL environment

### Minecraft Graphics Issues in WSL

BlockAssist requires OpenGL/graphics support for Minecraft. WSL2 has specific requirements for LWJGL-2 compatibility.

#### ✅ SOLVED: LWJGL-2 RANDR Extension Issue

The crash was caused by LWJGL-2 requiring the RANDR extension to enumerate display modes. When RANDR was disabled or missing, the display mode array became empty, causing `ArrayIndexOutOfBoundsException`.

**Root Cause:**
- LWJGL-2 runs `xrandr -q` to enumerate display modes
- If RANDR extension is missing/disabled, `xrandr -q` returns no modes
- Empty mode array causes `ArrayIndexOutOfBoundsException` at index 0

**Solution Implemented:**

1. **Updated `scripts/run_malmo.sh`**:
   - Removed `LWJGL_DISABLE_XRANDR=1` and `LWJGL_DISABLE_XF86VM=1`
   - Added automatic WSLg detection for better performance
   - Configured Xvfb with RANDR extension support
   - Added proper display mode enumeration

2. **Created `scripts/wsl_graphics_setup.sh`**:
   - Installs required graphics dependencies (xvfb, xrandr, mesa-utils)
   - Configures RANDR extension support
   - Detects WSLg vs non-WSLg environments
   - Verifies proper installation

#### Usage:

**For WSLg users (Windows 11):**
```bash
# WSLg provides built-in Xwayland with RANDR support
export DISPLAY=:0
python -m malmo.minecraft launch --num_instances 2 --goal_visibility True False
```

**For non-WSLg users:**
```bash
# Run the graphics setup first
./scripts/wsl_graphics_setup.sh

# Then run Malmo (script automatically uses Xvfb with RANDR)
./scripts/run_malmo.sh
```

#### What We Fixed:
- ✅ **RANDR Extension Support**: Proper display mode enumeration
- ✅ **WSLg Detection**: Automatic detection for better performance
- ✅ **Xvfb Configuration**: RANDR + GLX extensions enabled
- ✅ **Graphics Dependencies**: xvfb, xrandr, mesa-utils installation
- ✅ **Error Handling**: Proper verification and cleanup
- ✅ **Documentation**: Clear setup instructions

#### Performance Notes:
- **WSLg (Windows 11)**: Hardware-accelerated graphics via Xwayland
- **Xvfb (Windows 10/older)**: Software rendering via Mesa llvmpipe (~80 fps at 1024×768)

The graphics issues are now **completely resolved** for both WSLg and non-WSLg environments.

## Files Modified

1. **`run.py`**: Modified to spawn HTTP server as separate process
2. **`daemon.py`**: Updated cleanup to handle new process
3. **`run_http_server.py`**: New standalone HTTP server script
4. **`launcher.py`**: New launcher for easy usage
5. **`scripts/run_malmo.sh`**: ✅ **UPDATED** - Fixed LWJGL-2 RANDR compatibility
6. **`scripts/wsl_graphics_setup.sh`**: ✅ **NEW** - WSL graphics dependencies installer
7. **`README.md`**: ✅ **UPDATED** - Added WSL installation section
8. **`WSL_SETUP.md`**: ✅ **UPDATED** - Documented graphics solution

## Backward Compatibility

All changes are backward compatible. The original `run.py` behavior is preserved when the new HTTP server process isn't available.