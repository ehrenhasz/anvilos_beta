#!/bin/bash
# card_fw_001.sh - Fetch Linux Firmware

TARGET_DIR="oss_sovereignty/sys_04_Linux_Firmware"
FIRMWARE_REPO="https://git.kernel.org/pub/scm/linux/kernel/git/firmware/linux-firmware.git"

echo ">> [FIRMWARE] Starting Fetch..."

mkdir -p "$TARGET_DIR"

if [ ! -d "$TARGET_DIR/source/.git" ]; then
    echo ">> [FIRMWARE] Cloning linux-firmware..."
    git clone --depth 1 "$FIRMWARE_REPO" "$TARGET_DIR/source"
else
    echo ">> [FIRMWARE] Repo already exists. Updating..."
    cd "$TARGET_DIR/source" && git pull
fi

# We don't install to rootfs yet as we don't have a mounted rootfs structure defined in this context.
# We just ensure the artifacts are available.
echo ">> [FIRMWARE] Source available at $TARGET_DIR/source"
