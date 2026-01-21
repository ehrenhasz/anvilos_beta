#!/bin/bash
set -e

# Load Toolchain
source "$(pwd)/ext/toolchain/toolchain.sh"

# Paths
ZFS_SRC="$(pwd)/oss_sovereignty/sys_12_ZFS/source"
DEST_DIR="$(pwd)/ext/build/rootfs"

echo "Building ZFS from ${ZFS_SRC}..."
cd "${ZFS_SRC}"

# Configure
./configure \
    --prefix=/ \
    --host=x86_64-unknown-linux-musl \
    --enable-linux-builtin=no \
    --with-config=user \
    --disable-systemd \
    --disable-pyzfs \
    --with-udev-dir=/lib/udev \
    --with-mounthelper-dir=/sbin \
    --disable-dependency-tracking

# Build & Install
make -j$(nproc)
make install DESTDIR="${DEST_DIR}"

echo "ZFS Userspace Tools Installed to ${DEST_DIR}"

