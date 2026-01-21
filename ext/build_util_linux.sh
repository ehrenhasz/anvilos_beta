#!/bin/bash
set -e

# Load Toolchain
source "$(pwd)/ext/toolchain/toolchain.sh"

# Paths
VER="2.39.3"
URL="https://mirrors.edge.kernel.org/pub/linux/utils/util-linux/v2.39/util-linux-${VER}.tar.gz"
SRC_DIR="ext/build/util-linux-${VER}"
SYSROOT="$(pwd)/ext/toolchain/x86_64-unknown-linux-musl/sysroot"

echo "Downloading util-linux ${VER}..."
curl -L "${URL}" -o util-linux.tar.gz
tar -xzf util-linux.tar.gz -C ext/build/
rm util-linux.tar.gz

echo "Building util-linux (libs only)..."
cd "${SRC_DIR}"

# Configure for minimal libs
./configure \
    --host=x86_64-unknown-linux-musl \
    --prefix=/usr \
    --disable-all-programs \
    --enable-libuuid \
    --enable-libblkid \
    --disable-bash-completion \
    --disable-use-tty-group \
    --disable-makeinstall-chown \
    --disable-makeinstall-setuid

make -j$(nproc)
make install DESTDIR="${SYSROOT}"

echo "util-linux libs installed to ${SYSROOT}"

