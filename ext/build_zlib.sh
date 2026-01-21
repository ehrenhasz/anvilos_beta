#!/bin/bash
set -e

# Load Toolchain
source "$(pwd)/ext/toolchain/toolchain.sh"

# Paths
ZLIB_VER="1.3.1"
ZLIB_URL="https://www.zlib.net/zlib-${ZLIB_VER}.tar.gz"
SRC_DIR="ext/build/zlib-${ZLIB_VER}"
SYSROOT="$(pwd)/ext/toolchain/x86_64-unknown-linux-musl/sysroot"

echo "Downloading zlib ${ZLIB_VER}..."
curl -L "${ZLIB_URL}" -o zlib.tar.gz
tar -xzf zlib.tar.gz -C ext/build/
rm zlib.tar.gz

echo "Building zlib..."
cd "${SRC_DIR}"

# Configure for cross-compilation
# zlib's configure doesn't support standard --host, relies on CC/etc env vars
# We must set prefix to /usr so it installs to sysroot/usr
export CC="x86_64-unknown-linux-musl-gcc"
export AR="x86_64-unknown-linux-musl-ar"
export RANLIB="x86_64-unknown-linux-musl-ranlib"

./configure --prefix=/usr --static

make -j$(nproc)
make install DESTDIR="${SYSROOT}"

echo "zlib installed to ${SYSROOT}"
