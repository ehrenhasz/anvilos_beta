#!/bin/bash

# This script is a placeholder for building and installing the recharts component.
# It will call the build.py script

set -e

# Define the location of the build.py script.
BUILD_SCRIPT="oss_sovereignty/ctx_06_recharts/build.py"

# Define the staging directory.
STAGING_DIR="$1"

# Check if the build script exists.
if [ ! -f "$BUILD_SCRIPT" ]; then
  echo "Error: Build script not found: $BUILD_SCRIPT"
  exit 1
fi

# Check if a staging directory argument was supplied
if [ -z "$STAGING_DIR" ]; then
  echo "Error: No staging directory supplied"
  exit 1
fi

# Run the build process.
echo ">> [BUILD] Running build script: $BUILD_SCRIPT"
python3 "$BUILD_SCRIPT"

# Run the install process, passing the staging directory
echo ">> [INSTALL] Running install script: $BUILD_SCRIPT with staging directory: $STAGING_DIR"
python3 "$BUILD_SCRIPT" "$STAGING_DIR"

echo ">> [BUILD] Recharts component build and install complete."
exit 0
