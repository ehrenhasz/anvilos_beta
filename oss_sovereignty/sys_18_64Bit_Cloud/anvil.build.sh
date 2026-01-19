#!/bin/bash
# Anvil Build Script for sys_18_64Bit_Cloud
# 64-Bit Cloud Era Systems Collection

set -e

echo ">> Starting Anvil Build for sys_18_64Bit_Cloud"

# For collections, we just ensure the structure is mirrored to dist
mkdir -p dist
cp metadata.json dist/

echo ">> Build Complete"
