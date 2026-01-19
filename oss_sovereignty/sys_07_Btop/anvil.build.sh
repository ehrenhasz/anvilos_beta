#!/bin/bash
# Anvil Build Script for sys_07_Btop
set -e

echo ">> Starting Anvil Build for sys_07_Btop"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/source"
BUILD_DIR="${SCRIPT_DIR}/build"
DIST_DIR="${SCRIPT_DIR}/dist"

mkdir -p "${BUILD_DIR}"
mkdir -p "${DIST_DIR}"

cd "${BUILD_DIR}"
cmake "${SOURCE_DIR}" -DCMAKE_INSTALL_PREFIX="${DIST_DIR}"
make -j$(nproc)
make install

echo ">> Build Complete"
