#!/bin/bash

# This script is now a wrapper for the python build script.

# Set environment variables for the python script
export STAGING_DIR="${1:-build/iso_staging}"
export ARTIFACTS_DIR="${2:-artifacts}"
export PROFILE="${3:-runtime}"

python3 oss_sovereignty/ctx_07_vite/build.py
